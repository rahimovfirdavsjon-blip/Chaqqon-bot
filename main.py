# main.py - Простая версия для Render
import os
import telebot
from telebot import types
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

print("=" * 60)
print("🚀 CHAQQON CARGO BOT - Render.com Version")
print("=" * 60)

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.getenv('BOT_TOKEN', '8304765608:AAFKm7FoUghkXZ2sPUA25cQuzVoybjC74V4')
ADMIN_IDS = os.getenv('ADMIN_IDS', '123456789').split(',')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '1JFqNX3HBfPO2CDNekkvUDO3qwF6ZgDa-MJtJN2vmHcE')
PORT = int(os.getenv('PORT', 10000))

print(f"🤖 Бот: {'✅' if BOT_TOKEN else '❌'}")
print(f"👑 Админы: {ADMIN_IDS}")
print(f"📊 Google Sheet ID: {GOOGLE_SHEET_ID}")
print(f"🚪 Порт: {PORT}")
print("=" * 60)

bot = telebot.TeleBot(BOT_TOKEN)

# ========== GOOGLE SHEETS ==========
def connect_to_google_sheets():
    """Подключение к Google Sheets"""
    try:
        google_creds = os.getenv('GOOGLE_CREDENTIALS')
        if not google_creds:
            print("❌ GOOGLE_CREDENTIALS не найдены")
            return None
        
        creds_dict = json.loads(google_creds)
        scope = ['https://spreadsheets.google.com/feeds', 
                'https://www.googleapis.com/auth/drive']
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = spreadsheet.sheet1
        
        print(f"✅ Подключено к Google Sheets: {spreadsheet.title}")
        return worksheet
        
    except Exception as e:
        print(f"❌ Ошибка Google Sheets: {e}")
        return None

# ========== ПОИСК ПОСЫЛКИ ==========
def search_package(track_code):
    """Поиск посылки"""
    track_code = str(track_code).strip().upper()
    
    # Пробуем найти в Google Sheets
    worksheet = connect_to_google_sheets()
    if worksheet:
        try:
            all_data = worksheet.get_all_values()
            for row in all_data[1:]:  # Пропускаем заголовок
                if row and row[0].upper() == track_code:
                    return {
                        'track': track_code,
                        'status': row[1] if len(row) > 1 else 'Не указано',
                        'date': row[2] if len(row) > 2 else 'Не указано',
                        'note': row[3] if len(row) > 3 else 'Нет примечаний'
                    }
        except Exception as e:
            print(f"Ошибка поиска: {e}")
    
    # Тестовые данные если Google Sheets не работает
    test_data = {
        "CCTEST001": {"status": "В пути", "date": "16.01.2024", "note": "Тестовая посылка"},
        "CC123456": {"status": "Доставлено", "date": "15.01.2024", "note": "Получено клиентом"},
    }
    
    if track_code in test_data:
        return test_data[track_code]
    
    return None

# ========== КОМАНДЫ БОТА ==========
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔍 Проверить трек-код"))
    markup.add(types.KeyboardButton("ℹ️ Помощь"))
    
    text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "🚚 *CHAQQON Cargo Online Tracking*\n\n"
        "📦 Отслеживайте статус посылок мгновенно!\n\n"
        "💡 *Пример трек-кода:*\n"
        "`CCTEST001`, `CC123456`"
    )
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔍 Проверить трек-код")
def ask_track(message):
    bot.send_message(message.chat.id, 
                    "🔎 *Введите трек-код:*\n\nПример: `CCTEST001`",
                    parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "ℹ️ Помощь")
def help_message(message):
    bot.send_message(message.chat.id,
                    "📋 *Помощь*\n\n"
                    "1. Нажмите '🔍 Проверить трек-код'\n"
                    "2. Введите трек-код\n"
                    "3. Получите статус\n\n"
                    "📞 Поддержка: @chaqqon_support",
                    parse_mode="Markdown")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text in ["🔍 Проверить трек-код", "ℹ️ Помощь"]:
        return
    
    track_code = message.text.upper()
    print(f"🔍 Поиск: {track_code}")
    
    package = search_package(track_code)
    
    if package:
        response = (
            f"📦 *Посылка найдена!*\n\n"
            f"🔢 *Трек-код:* `{track_code}`\n"
            f"📍 *Статус:* {package['status']}\n"
            f"📅 *Дата:* {package['date']}\n"
            f"📝 *Примечание:* {package['note']}\n\n"
            f"💫 *CHAQQON Cargo*"
        )
    else:
        response = (
            f"❌ *Трек-код не найден:* `{track_code}`\n\n"
            "💡 Проверьте правильность кода\n"
            "📞 Обратитесь в офис CHAQQON Cargo"
        )
    
    bot.send_message(message.chat.id, response, parse_mode="Markdown")

# ========== ЗАПУСК ==========
def start_bot():
    print("🤖 Запускаем бота...")
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")
        print("🔄 Перезапуск через 10 секунд...")
        import time
        time.sleep(10)
        start_bot()

if __name__ == "__main__":
    # Запускаем web сервер для Render health checks
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"CHAQQON CARGO BOT is running!")
    
    # Запускаем web сервер в отдельном потоке
    def run_web():
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        print(f"🌐 Web сервер запущен на порту {PORT}")
        server.serve_forever()
    
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    # Запускаем бота
    start_bot()