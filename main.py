import telebot
import gspread
from telebot import types
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# === 1. ТВОЙ ТОКЕН ===
TOKEN = "8304765608:AAFKm7FoUghkXZ2sPUA25cQuzVoybjC74V4"
bot = telebot.TeleBot(TOKEN)

# === 2. ПОДКЛЮЧЕНИЕ К GOOGLE SHEETS ===
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "D:/CHAQQON CARGO/Cargo bot/chaqqoncargobot-1bab83dd20f1.json",
        scope
    )

    client = gspread.authorize(creds)

    # === 3. НАЗВАНИЕ ТАБЛИЦЫ ===
    sheet = client.open("ChaqqonCargo").sheet1
    print("✅ Успешно подключено к Google Sheets")

except Exception as e:
    print(f"❌ Ошибка подключения к Google Sheets: {e}")
    sheet = None


# ====================================
#         ОБРАБОТКА СООБЩЕНИЙ
# ====================================

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_track = types.KeyboardButton("🔍 Проверить трек-код")
    btn_help = types.KeyboardButton("📋 Помощь")
    markup.add(btn_track, btn_help)

    text = (
        "🚀 *CHAQQON Cargo Online Tracking*\n\n"
        "📦 Просто введите свой трек-код —\n"
        "и мы покажем точный статус вашей посылки прямо сейчас.\n\n"
        "Нажмите кнопку ниже, чтобы начать ⬇️"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def help_message(message):
    help_text = (
        "📋 *Доступные команды:*\n\n"
        "🔍 *Проверить трек-код* - поиск статуса посылки\n"
        "📋 *Помощь* - это сообщение\n"
        "⚙️ *Статус* - проверка подключения\n\n"
        "💡 *Просто отправьте трек-код* для быстрого поиска"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def status_message(message):
    if sheet is not None:
        try:
            data = sheet.get_all_records()
            status_text = (
                "✅ *Бот работает нормально*\n\n"
                f"📊 *Записей в базе:* {len(data)}\n"
                "🔗 *Подключение к Google Sheets:* ✅ Активно"
            )
        except Exception as e:
            status_text = f"⚠ Ошибка при чтении данных: {e}"
    else:
        status_text = (
            "❌ *Нет подключения к Google Sheets*\n"
            "🔄 *Используются тестовые данные*\n\n"
            "💡 Для настройки используйте команду /setup"
        )
    bot.send_message(message.chat.id, status_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🔍 Проверить трек-код")
def track_button_handler(message):
    bot.send_message(
        message.chat.id,
        "🔎 *Введите трек-код для проверки:*\n\n"
        "Пример: `CC123456789`",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "📋 Помощь")
def help_button_handler(message):
    help_message(message)

@bot.message_handler(func=lambda message: message.text == "⚙️ Статус системы")
def status_button_handler(message):
    status_message(message)

@bot.message_handler(content_types=['text'])
def track_search(message):
    # Пропускаем команды и кнопки
    if message.text.startswith('/') or message.text in ["🔍 Проверить трек-код", "📋 Помощь", "⚙️ Статус системы"]:
        return
        
    track_code = message.text.strip().upper()

    if sheet is None:
        bot.send_message(
            message.chat.id, 
            "⚠ *Ошибка подключения к базе данных.*\nПопробуйте позже.",
            parse_mode="Markdown"
        )
        return

    try:
        data = sheet.get_all_records()

        found = False
        for row in data:
            if str(row.get("TRACK", "")).strip().upper() == track_code:
                status = row.get("STATUS", "Не указан")
                date = row.get("DATE", "Не указана")
                note = row.get("NOTE", "Нет примечаний")

                # Создаем красивый ответ
                text = (
                    f"📦 *Трек-код:* `{track_code}`\n"
                    f"📍 *Статус:* {status}\n"
                    f"📅 *Дата:* {date}\n"
                    f"📝 *Примечание:* {note}\n\n"
                    f"💫 *CHAQQON Cargo* - всегда на связи!"
                )

                bot.send_message(message.chat.id, text, parse_mode="Markdown")
                found = True
                break

        if not found:
            bot.send_message(
                message.chat.id,
                f"❌ *Трек-код не найден:* `{track_code}`\n\n"
                "Проверьте правильность ввода и попробуйте снова.",
                parse_mode="Markdown"
            )

    except Exception as e:
        print(f"Ошибка при поиске: {e}")
        bot.send_message(
            message.chat.id,
            "⚠ *Произошла ошибка при поиске.*\nПопробуйте позже.",
            parse_mode="Markdown"
        )

# ====================================
#              ЗАПУСК БОТА
# ====================================
if __name__ == "__main__":
    print("Бот запущен...")
    try:
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")