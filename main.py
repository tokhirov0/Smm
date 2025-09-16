import os
from flask import Flask, request
import telebot
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
API_KEY = os.getenv("API_KEY")

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Foydalanuvchilar va kanal/guruh ro'yxati
users = {}
channels = {}
groups = {}

# Xabarlar
START_MSG = "👋 Salom! SMM xizmat botiga xush kelibsiz."

# Inline menu
def inline_menu():
    from telebot import types
    menu = types.InlineKeyboardMarkup()
    menu.add(types.InlineKeyboardButton("💬 Buyurtmalar", callback_data="order"))
    menu.add(types.InlineKeyboardButton("📊 Balans", callback_data="balance"))
    return menu

# /start komandasi
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.chat.id
    users[user_id] = {"id": user_id}
    bot.send_message(user_id, START_MSG, reply_markup=inline_menu())

# Buyurtmalar funksiyasi
def get_services():
    url = "https://uzbek-seen.uz/api/v2"
    params = {"key": API_KEY, "action": "services"}
    res = requests.get(url, params=params)
    return res.json()

def add_order(service_id, link, quantity):
    url = "https://uzbek-seen.uz/api/v2"
    params = {"key": API_KEY, "action": "add", "service": service_id, "link": link, "quantity": quantity}
    res = requests.post(url, data=params)
    return res.json()

# Inline tugmalar
@bot.callback_query_handler(func=lambda c: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if call.data == "order":
        services = get_services()
        msg = "💼 Xizmatlar:\n"
        for s in services:
            msg += f"{s['service']}. {s['name']} - Narx: {s['rate']} UZS\n"
        bot.send_message(user_id, msg)
    elif call.data == "balance":
        url = "https://uzbek-seen.uz/api/v2"
        params = {"key": API_KEY, "action": "balance"}
        res = requests.get(url, params=params).json()
        bot.send_message(user_id, f"💰 Balans: {res['balance']} {res['currency']}")

# Webhook route
@server.route(f"/{TOKEN}", methods=["POST", "GET"])
def webhook():
    if request.method == "POST":
        json_str = request.get_data().decode("UTF-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "!", 200
    else:
        return "✅ Bot ishlayapti!", 200

# Root
@server.route("/")
def index():
    return "SMM Bot ishlayapti! ✅", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
