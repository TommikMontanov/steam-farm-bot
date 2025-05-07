import asyncio
import sqlite3
import aiohttp
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Получение переменных окружения
API_TOKEN = os.getenv("BOT_TOKEN")
ASF_API_URL = os.getenv("ASF_API_URL", "http://localhost:1242/ASF")
ASF_API_KEY = os.getenv("ASF_API_KEY")

# Проверка обязательных переменных
if not API_TOKEN or not ASF_API_KEY:
    raise ValueError("TELEGRAM_BOT_TOKEN и ASF_API_KEY должны быть заданы")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Временное хранилище для регистрации
registration_data = {}

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            steam_id TEXT,
            farming BOOLEAN,
            selected_games TEXT,
            bot_name TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Создание клавиатуры
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/register")],
            [KeyboardButton(text="/start_farm")],
            [KeyboardButton(text="/stop_farm")],
            [KeyboardButton(text="/select_games")],
            [KeyboardButton(text="/status")]
        ],
        resize_keyboard=True
    )
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
    logging.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(
        "Привет! Я бот для фарма часов в Steam. Используй команды:\n"
        "/register - Зарегистрировать Steam-аккаунт\n"
        "/start_farm - Начать фарм\n"
        "/stop_farm - Остановить фарм\n"
        "/select_games - Выбрать игры\n"
        "/status - Проверить статус",
        reply_markup=get_main_menu()
    )

# Обработчик команды /register
@dp.message(Command("register"))
async def cmd_register(message: types.Message):
    user_id = message.from_user.id
    logging.info(f"Начало регистрации для пользователя {user_id}")
    registration_data[user_id] = {"step": "login"}
    await message.answer("Введи свой Steam логин:")

# Обработчик текстовых сообщений для регистрации
@dp.message()
async def process_registration(message: types.Message):
    if not message.text:
        return  # Игнорируем сообщения без текста

    user_id = message.from_user.id
    logging.info(f"Получено сообщение от пользователя {user_id}: {message.text}")
    
    if user_id not in registration_data:
        logging.warning(f"Пользователь {user_id} не в процессе регистрации")
        await message.answer("Начни регистрацию с /register!")
        return

    step = registration_data[user_id]["step"]
    logging.info(f"Текущий шаг регистрации для {user_id}: {step}")

    if step == "login":
        registration_data[user_id]["login"] = message.text.strip()
        registration_data[user_id]["step"] = "password"
        await message.answer("Введи свой Steam пароль:")
    elif step == "password":
        registration_data[user_id]["password"] = message.text.strip()
        registration_data[user_id]["step"] = "steamguard"
        await message.answer(
            "Если у тебя включен Steam Guard, введи код из письма или мобильного приложения. "
            "Если Steam Guard отключен, напиши 'нет':"
        )
    elif step == "steamguard":
        steamguard_code = message.text.strip()
        login = registration_data[user_id]["login"]
        password = registration_data[user_id]["password"]
        bot_name = f"Bot_{user_id}"

        logging.info(f"Отправка конфигурации ASF для бота {bot_name}")
        # Создаем конфигурацию для ASF
        bot_config = {
            "Enabled": True,
            "SteamLogin": login,
            "SteamPassword": password,
            "SteamUserPermissions": {},
            "FarmingPreferences": 0,
            "IsBotAccount": True,
            "OnlineStatus": 1
        }
        if steamguard_code.lower() != "нет":
            bot_config["TwoFactorCode"] = steamguard_code

        # Отправляем конфигурацию в ASF
        data = {
            "Command": f"!addbot {bot_name}",
            "Config": bot_config
        }
        result = await asf_request("Bot", method="POST", data=data)
        if result and result.get("Success"):
            # Получаем Steam ID после успешной регистрации
            bot_info = await asf_request(f"Bot/{bot_name}")
            if bot_info and bot_info.get("Success"):
                steam_id = bot_info.get("Result", {}).get("SteamID")
                if steam_id:
                    conn = sqlite3.connect("users.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT OR REPLACE INTO users (user_id, steam_id, farming, selected_games, bot_name) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (user_id, steam_id, False, "", bot_name)
                    )
                    conn.commit()
                    conn.close()
                    await message.answer(f"Регистрация успешна! Steam ID: {steam_id}. Теперь выбери игры с помощью /select_games!")
                else:
                    logging.error(f"Не удалось получить Steam ID для {bot_name}")
                    await message.answer("Не удалось получить Steam ID. Проверь настройки ASF.")
            else:
                logging.error(f"Ошибка получения данных бота {bot_name}")
                await message.answer("Ошибка при получении данных бота. Проверь ASF.")
        else:
            error_msg = result.get("Message", "Неизвестная ошибка") if result else "Ошибка связи с ASF"
            logging.error(f"Ошибка регистрации для {user_id}: {error_msg}")
            await message.answer(f"Ошибка регистрации: {error_msg}. Попробуй снова или проверь Steam Guard.")
            if "Steam Guard" in error_msg:
                registration_data[user_id]["step"] = "steamguard"
                await message.answer("Введи новый код Steam Guard:")
                return

        # Очищаем временные данные
        del registration_data[user_id]
        logging.info(f"Регистрация завершена для пользователя {user_id}")

# Обработчик команды /start_farm
@dp.message(Command("start_farm"))
async def cmd_start_farm(message: types.Message):
    user_id = message.from_user.id
    logging.info(f"Команда /start_farm от пользователя {user_id}")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT steam_id, selected_games, bot_name FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        await message.answer("Сначала зарегистрируйся с помощью /register!")
        conn.close()
        return

    steam_id, selected_games, bot_name = user
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
        "Command": f"!start {bot_name} {selected_games}"
    }
    result = await asf_request("Command", method="POST", data=data)
    if result and result.get("Success"):
        cursor.execute("UPDATE users SET farming = ? WHERE user_id = ?", (True, user_id))
        conn.commit()
        await message.answer(f"Фарм начат для Steam ID {steam_id}!")
    else:
        await message.answer("Ошибка при запуске фарма. Проверь настройки ASF.")
    conn.close()

# Запуск бота
async def main():
    logging.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
