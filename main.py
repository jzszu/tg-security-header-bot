import asyncio
import logging
import os
import time
from datetime import datetime

import httpx
from aiogram import Bot, Dispatcher, F, html
from aiogram.filters import Command, CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from dotenv import load_dotenv

from database import add_check, get_global_stats, get_user_history, init_db

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

dp = Dispatcher()

# Простой словарь для защиты от спама (Rate Limiting)
# Хранит {user_id: timestamp_последнего_запроса}
user_cooldowns = {}

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📜 Моя история"), KeyboardButton(text="ℹ️ Инструкция")]
    ],
    resize_keyboard=True
)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    text = (
        f"Привет, {html.bold(message.from_user.full_name)}!\n\n"
        "Я **Security Header Auditor Bot**.\n"
        "Отправь мне URL сайта (например, `https://github.com`), и я проверю его статус "
        "и базовые заголовки безопасности."
    )
    await message.answer(text, reply_markup=main_kb, parse_mode="HTML")


@dp.message(F.text == "ℹ️ Инструкция")
async def info_handler(message: Message) -> None:
    await message.answer("Просто отправь мне URL-адрес сайта, начиная с http:// или https://")


# Команда для админа: доступна только по ADMIN_ID
@dp.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        # Отклоняем доступ незарегистрированным пользователям (ИБ-принцип Least Privilege)
        await message.answer("⛔ У вас нет прав для выполнения этой команды.")
        return

    total_checks, unique_users = await get_global_stats()
    admin_text = (
        f"📊 {html.bold('Панель администратора')}\n\n"
        f"👥 Всего пользователей: {html.bold(unique_users)}\n"
        f"🔍 Всего проверок сделано: {html.bold(total_checks)}"
    )
    await message.answer(admin_text, parse_mode="HTML")


@dp.message(F.text == "📜 Моя история")
async def history_handler(message: Message) -> None:
    history = await get_user_history(message.from_user.id)
    if not history:
        await message.answer("У тебя пока нет сохраненных проверок.")
        return

    text = "📜 **Твои последние проверки:**\n\n"
    for url, status, time_str in history:
        text += f"🔹 `{url}` — Статус: {status} ({time_str})\n"

    await message.answer(text, parse_mode="HTML")


# Аудит сайта с защитой от флуда
@dp.message(F.text.startswith("http://") | F.text.startswith("https://"))
async def check_url_handler(message: Message) -> None:
    user_id = message.from_user.id
    current_time = time.time()

    # Защита от спама: не чаще 1 запроса в 5 секунд
    if user_id in user_cooldowns:
        elapsed = current_time - user_cooldowns[user_id]
        if elapsed < 5.0:
            wait_time = int(5.0 - elapsed) + 1
            await message.answer(f"⏳ Слишком часто! Подожди {wait_time} сек. перед следующей проверкой.")
            return

    # Обновляем время последнего запроса
    user_cooldowns[user_id] = current_time

    url = message.text.strip()
    await message.answer("🔍 Провожу экспресс-аудит сайта...")

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            response = await client.get(url)
            status_code = response.status_code
            headers = response.headers

            await add_check(user_id, url, status_code)

            hsts = "✅ Настроен" if "Strict-Transport-Security" in headers else "❌ Отсутствует (MitM риск)"
            x_frame = "✅ Настроен" if "X-Frame-Options" in headers else "⚠️ Отсутствует (Clickjacking риск)"
            csp = "✅ Настроен" if "Content-Security-Policy" in headers else "⚠️ Отсутствует (XSS риск)"

            result_text = (
                f"🌐 {html.bold('Результат аудита:')}\n"
                f"🔗 URL: `{url}`\n"
                f"📊 Код ответа: {html.bold(status_code)}\n\n"
                f"🛡 {html.bold('Заголовки безопасности:')}\n"
                f"• HSTS: {hsts}\n"
                f"• X-Frame-Options: {x_frame}\n"
                f"• CSP: {csp}\n"
            )
            await message.answer(result_text, parse_mode="HTML")

    except httpx.RequestError as e:
        await message.answer(f"❌ Ошибка подключения: `{e}`", parse_mode="HTML")


async def main() -> None:
    await init_db()
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())