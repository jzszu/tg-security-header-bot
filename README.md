# 🛡️ TG Security Header Auditor Bot

Telegram-бот для проведения первичного аудита заголовков безопасности (Security Headers) веб-сайтов на соответствие стандартам OWASP.

## 🚀 Функционал
- **Аудит безопасности:** Проверка наличия заголовков `Strict-Transport-Security`, `X-Frame-Options` и `Content-Security-Policy`.
- **База данных:** Сохранение истории проверок пользователей в SQLite (`aiosqlite`).
- **Защита от спама:** Rate Limiting (ограничение частоты запросов).
- **Админ-панель:** Ограниченный доступ к статистике бота (`/admin`) по `ADMIN_ID`.
- **Логирование:** Автоматическая запись событий в `bot_access.log`.

## 🛠 Технологии
- **Language:** Python 3.12
- **Framework:** aiogram 3.x
- **HTTP Client:** httpx
- **Database:** SQLite (`aiosqlite`)
- **Environment:** Linux (Ubuntu) / WSL 2

## ⚙️ Быстрый запуск

1. Клонировать репозиторий:
   ```bash
   git clone [https://github.com/jzszu/tg-security-header-bot.git](https://github.com/jzszu/tg-security-header-bot.git)
   cd tg-security-header-bot