import asyncio
import sqlite3
import aiohttp
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получение переменных окружения
API_TOKEN = os.getenv("BOT_TOKEN")  # Токен Telegram-бота
ASF_API_URL = os.getenv("ASF_API_URL", "http://localhost:1242/ASF")  # URL ASF IPC
ASF_API_KEY = os.getenv("ASF_API_KEY")  # API ключ ASF

# Проверка обязательных переменных
if not API_TOKEN or not ASF_API_KEY:
    raise ValueError("TELEGRAM_BOT_TOKEN и ASF_API_KEY должны быть заданы в переменных окружения")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            steam_id TEXT,
            farming BOOLEAN,
            selected_games TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Создание клавиатуры
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("/start_farm"))
    keyboard.add(KeyboardButton("/stop_farm"))
    keyboard.add(KeyboardButton("/select_games"))
    keyboard.add(KeyboardButton("/status"))
    return keyboard

# Функция для отправки запроса к ASF API
async def asf_request(endpoint, method="GET", data=None):
    headers = {"Authentication": ASF_API_KEY, "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        try:
            if method == "POST":
                async with session.post(f"{ASF_API_URL}/{endpoint}", json=data, headers=headers) as resp:
                    return await resp.json()
            async with session.get(f"{ASF_API_URL}/{endpoint}", headers=headers) as resp:
                return await resp.json()
        except Exception as e:
            logging.error(f"ASF API error: {e}")
            return None

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для фарма часов в Steam. Используй команды:\n"
        "/start_farm - Начать фарм\n"
        "/stop_farm - Остановить фарм\n"
        "/select_games - Выбрать игры\n"
        "/status - Проверить статус",
        reply_markup=get_main_menu()
    )

# Обработчик команды /start_farm
@dp.message(Command("start_farm"))
async def cmd_start_farm(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT steam_id, selected_games FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        await message.answer("Пожалуйста, укажи свой Steam ID (например, 76561198000000000):")
        dp.register_message_handler(process_steam_id, user_id=user_id)
        conn.close()
        return

    steam_id, selected_games = user
    if not selected_games:
        await message.answer("Сначала выбери игры для фарма с помощью /select_games!")
        conn.close()
        return

    # Проверяем статус фарма
    cursor.execute("SELECT farming FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone()[0]:
        await message.answer("Фарм уже запущен!")
        conn.close()
        return

    # Запускаем фарм через ASF
    data = {
        "Command": f"!start {steam_id} {selected_games}"
    }
    result = await asf_request("Command", method="POST", data=data)
    if result and result.get("Success"):
        cursor.execute("UPDATE users SET farming = ? WHERE user_id = ?", (True, user_id))
        conn.commit()
        await message.answer(f"Фарм начат для Steam ID {steam_id} с играми: {selected_games}!")
    else:
        await message.answer("Ошибка при запуске фарма. Проверь настройки ASF.")
    conn.close()

# Обработчик ввода Steam ID
async def process_steam_id(message: types.Message):
    user_id = message.from_user.id
    steam_id = message.text.strip()

    # Проверка формата Steam ID
    if not steam_id.isdigit() or len(steam_id) != 17:
        await message.answer("Неверный формат Steam ID. Попробуй еще раз (17 цифр):")
        return

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, steam_id, farming, selected_games) VALUES (?, ?, ?, ?)",
        (user_id, steam_id, False, "")
    )
    conn.commit()
    conn.close()
    await message.answer(f"Steam ID сохранен: {steam_id}. Теперь выбери игры с помощью /select_games!")
    dp.message_handlers.unregister(process_steam_id)

# Обработчик команды /stop_farm
@dp.message(Command("stop_farm"))
async def cmd_stop_farm(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT steam_id, farming FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user or not user[1]:
        await message.answer("Фарм не запущен!")
        conn.close()
        return

    steam_id = user[0]
    # Останавливаем фарм через ASF
    data = {
        "Command": f"!stop {steam_id}"
    }
    result = await asf_request("Command", method="POST", data=data)
    if result and result.get("Success"):
        cursor.execute("UPDATE users SET farming = ? WHERE user_id = ?", (False, user_id))
        conn.commit()
        await message.answer("Фарм остановлен!")
    else:
        await message.answer("Ошибка при остановке фарма. Проверь настройки ASF.")
    conn.close()

# Обработчик команды /select_games
@dp.message(Command("select_games"))
async def cmd_select_games(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT steam_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        await message.answer("Сначала укажи Steam ID с помощью /start_farm!")
        conn.close()
        return

    steam_id = user[0]
    # Получаем список доступных игр через ASF
    result = await asf_request(f"Bot/{steam_id}/Games")
    if not result or not result.get("Success"):
        await message.answer("Не удалось получить список игр. Проверь ASF.")
        conn.close()
        return

    games = result.get("Result", {}).get("Games", {})
    if not games:
        await message.answer("Нет доступных игр для фарма.")
        conn.close()
        return

    # Формируем список игр (AppID)
    game_list = [f"{app_id}" for app_id in games.keys()]
    await message.answer(
        f"Доступные игры (AppID): {', '.join(game_list)}\n"
        "Введи AppID игр для фарма через запятую (например, 730,440):"
    )
    dp.register_message_handler(process_games_selection, user_id=user_id)
    conn.close()

# Обработчик выбора игр
async def process_games_selection(message: types.Message):
    user_id = message.from_user.id
    games = message.text.strip().split(",")
    games = [game.strip() for game in games if game.strip().isdigit()]

    if not games:
        await message.answer("Неверный формат. Введи AppID игр через запятую.")
        return

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET selected_games = ? WHERE user_id = ?", (",".join(games), user_id))
    conn.commit()
    conn.close()
    await message.answer(f"Игры выбраны: {', '.join(games)}. Теперь используй /start_farm!")
    dp.message_handlers.unregister(process_games_selection)

# Обработчик команды /status
@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT steam_id, farming, selected_games FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        await message.answer("Ты еще не начинал фарм. Используй /start_farm!")
        return

    steam_id, farming, selected_games = user
    status = "активен" if farming else "остановлен"
    games = selected_games or "не выбраны"
    await message.answer(f"Статус фарма: {status}\nSteam ID: {steam_id}\nИгры: {games}")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
