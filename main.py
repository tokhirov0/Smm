import os
import requests
from flask import Flask, request
import telebot
from telebot import types

# Environment Variables
TOKEN = os.environ.get("TOKEN")
OWNER = os.environ.get("OWNER")  # Admin username
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Kanal va Guruhlar (Admin o‘zi qo‘shadi)
CHANNELS = []  # ['@kanal_nomi']
GROUPS = []    # ['@guruh_nomi']

# Inline menu yaratish
def inline_menu():
    menu = types.InlineKeyboardMarkup()
    menu.add(
        types.InlineKeyboardButton("🔵 Admin", url=f"https://t.me/{OWNER}")
    )
    for ch in CHANNELS:
        menu.add(types.InlineKeyboardButton(f"📣 Kanal: {ch}", url=f"https://t.me/{ch}"))
    for gr in GROUPS:
        menu.add(types.InlineKeyboardButton(f"👥 Guruh: {gr}", url=f"https://t.me/{gr}"))
    return menu

# /start komandasi
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    bot.send_message(user_id, "👋 Salom! SMM botiga xush kelibsiz.", reply_markup=inline_menu())

# SMM API funksiyalari
API_KEY = os.environ.get("SMM_API_KEY")  # Masalan: '37c5efb953b0fb08f32f5dbba666cc68'
API_URL = "https://uzbek-seen.uz/api/v2"

def get_services():
    data = {"key": API_KEY, "action": "services"}
    res = requests.post(API_URL, data=data).json()
    return res

def add_order(service_id, link, quantity):
    data = {"key": API_KEY, "action": "add", "service": service_id, "link": link, "quantity": quantity}
    res = requests.post(API_URL, data=data).json()
    return res

def get_balance():
    data = {"key": API_KEY, "action": "balance"}
    res = requests.post(API_URL, data=data).json()
    return res

# Inline tugmalar orqali SMM buyurtmalar
@bot.message_handler(commands=["services"])
def services(message):
    user_id = message.chat.id
    services_list = get_services()
    text = "📜 Xizmatlar ro'yxati:\n\n"
    for s in services_list:
        text += f"{s['service']}. {s['name']} | Narx: {s['rate']} | Min: {s['min']} | Max: {s['max']}\n"
    bot.send_message(user_id, text)

@bot.message_handler(commands=["balance"])
def balance(message):
    user_id = message.chat.id
    bal = get_balance()
    bot.send_message(user_id, f"💰 Sizning balansingiz: {bal['balance']} {bal['currency']}")

# Webhook Flask
@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    return "Bot ishlayapti! ✅", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
