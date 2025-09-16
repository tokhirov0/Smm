import os
import requests
from flask import Flask, request
import telebot
from telebot import types

# Environment Variables
TOKEN = os.environ.get("TOKEN")
OWNER_ID = int(os.environ.get("OWNER"))

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Global kanal
CHANNEL = None

# SMM API
API_URL = "https://uzbek-seen.uz/api/v2"
API_KEY = os.environ.get("API_KEY")  # .env faylga qo'yish kerak

# Menyular
def main_menu():
    menu = types.InlineKeyboardMarkup()
    menu.add(types.InlineKeyboardButton("📃 Xizmatlar", callback_data="services"))
    menu.add(types.InlineKeyboardButton("💰 Balans", callback_data="balance"))
    return menu

# Admin kanal qo‘shish
@bot.message_handler(commands=["setchannel"])
def set_channel(message):
    global CHANNEL
    if message.chat.id == OWNER_ID:
        args = message.text.split()
        if len(args) == 2:
            CHANNEL = args[1]
            bot.reply_to(message, f"Kanal majburiy qilindi: {CHANNEL}")
        else:
            bot.reply_to(message, "Iltimos, kanal nomini yozing: /setchannel @kanalnomi")

@bot.message_handler(commands=["removechannel"])
def remove_channel(message):
    global CHANNEL
    if message.chat.id == OWNER_ID:
        CHANNEL = None
        bot.reply_to(message, "Majburiy kanal olib tashlandi.")

# Kanalga obuna tekshirish
def check_subscription(user_id):
    if not CHANNEL:
        return True
    try:
        status = bot.get_chat_member(CHANNEL, user_id).status
        if status in ["creator", "administrator", "member"]:
            return True
        return False
    except:
        return False

# API: Xizmatlar
def get_services():
    data = {"key": API_KEY, "action": "services"}
    return requests.post(API_URL, data=data).json()

# API: Buyurtma qo‘yish
def add_order(service_id, link, quantity):
    data = {"key": API_KEY, "action": "add", "service": service_id, "link": link, "quantity": quantity}
    return requests.post(API_URL, data=data).json()

# API: Buyurtma statusi
def order_status(order_id):
    data = {"key": API_KEY, "action": "status", "order": order_id}
    return requests.post(API_URL, data=data).json()

# API: Balans
def get_balance():
    data = {"key": API_KEY, "action": "balance"}
    return requests.post(API_URL, data=data).json()

# /start
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.chat.id
    if not check_subscription(user_id):
        bot.send_message(user_id, f"⚠️ Kanalga obuna bo‘ling: {CHANNEL}")
        return
    bot.send_message(user_id, "👋 Assalomu alaykum!\nXizmatlar va balansni ko‘rish uchun menyudan tanlang.", reply_markup=main_menu())

# Inline tugmalar
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data == "services":
        services = get_services()
        text = "📃 Xizmatlar:\n\n"
        for s in services:
            text += f"{s['service']}. {s['name']} - Narxi: {s['rate']} UZS\n"
        bot.send_message(chat_id, text)
    elif call.data == "balance":
        balance = get_balance()
        bot.send_message(chat_id, f"💰 Sizning balansingiz: {balance['balance']} {balance['currency']}")

# Flask webhook
@server.route(f"/{TOKEN}", methods=["POST"])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    return "Bot ishlayapti! ✅", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
