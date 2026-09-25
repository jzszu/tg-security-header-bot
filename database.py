import aiosqlite

DB_NAME = "bot_history.db"

# Создаем таблицу, если ее еще нет
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT,
                status_code INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# Сохраняем проверку в БД
async def add_check(user_id: int, url: str, status_code: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO checks (user_id, url, status_code) VALUES (?, ?, ?)",
            (user_id, url, status_code)
        )
        await db.commit()

# Получаем последние 5 проверок пользователя
async def get_user_history(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT url, status_code, timestamp FROM checks WHERE user_id = ? ORDER BY id DESC LIMIT 5",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()
# Функция для админ-панели: считает общее число проверок и уникальных пользователей
async def get_global_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*), COUNT(DISTINCT user_id) FROM checks") as cursor:
            total_checks, unique_users = await cursor.fetchone()
            return total_checks, unique_users