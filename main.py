# main.py
import os
import requests
from flask import Flask, request
import telebot

# ---------------- Environment Variables ----------------
TOKEN = os.environ.get("BOT_TOKEN")  # Sizning bot tokeningiz
ADMIN_ID = int(os.environ.get("ADMIN_ID"))  # Admin Telegram ID
# OPTIONAL: Kanal va guruhlar bo‘lsa
CHANNELS = os.environ.get("CHANNELS", "").split(",")  # masalan: "kanal1,kanal2"
GROUPS = os.environ.get("GROUPS", "").split(",")      # masalan: "guruh1,guruh2"
API_KEY = os.environ.get("API_KEY")  # Uzbek-seen.uz API key

# ---------------- Bot va Flask server ----------------
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# ---------------- Foydalanuvchilar va buyurtmalar ----------------
users = {}  # foydalanuvchilar ma'lumotlari

# ---------------- Funksiyalar ----------------
def get_services():
    url = "https://uzbek-seen.uz/api/v2"
    params = {"key": API_KEY, "action": "services"}
    r = requests.get(url, params=params)
    return r.json()

def add_order(service_id, link, quantity):
    url = "https://uzbek-seen.uz/api/v2"
    params = {
        "key": API_KEY,
        "action": "add",
        "service": service_id,
        "link": link,
        "quantity": quantity
    }
    r = requests.get(url, params=params)
    return r.json()

def get_balance():
    url = "https://uzbek-seen.uz/api/v2"
    params = {"key": API_KEY, "action": "balance"}
    r = requests.get(url, params=params)
    return r.json()

# Kanal va guruh obuna tekshirish
def is_subscribed(chat_id):
    try:
        for channel in CHANNELS:
            member = bot.get_chat_member(channel, chat_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        for group in GROUPS:
            member = bot.get_chat_member(group, chat_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        return True
    except:
        return False

# ---------------- Bot komandalar ----------------
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.chat.id
    if not is_subscribed(user_id):
        bot.send_message(user_id, "❌ Xizmatdan foydalanish uchun kanal va guruhga obuna bo‘ling!")
        return
    users[user_id] = {"id": user_id}
    bot.send_message(user_id, "✅ Xush kelibsiz! /services orqali xizmatlarni ko‘rishingiz mumkin.")

@bot.message_handler(commands=["services"])
def services_handler(message):
    services = get_services()
    text = "📋 Xizmatlar:\n\n"
    for s in services:
        text += f"{s['service']}: {s['name']} ({s['rate']} UZS)\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["balance"])
def balance_handler(message):
    balance = get_balance()
    bot.send_message(message.chat.id, f"💰 Sizning balans: {balance['balance']} {balance['currency']}")

# Buyurtma qo‘shish
@bot.message_handler(commands=["order"])
def order_handler(message):
    try:
        args = message.text.split()
        if len(args) < 4:
            bot.send_message(message.chat.id, "❌ Foydalanish: /order <service_id> <link> <quantity>")
            return
        service_id = args[1]
        link = args[2]
        quantity = args[3]
        result = add_order(service_id, link, quantity)
        bot.send_message(message.chat.id, f"✅ Buyurtma qo‘shildi:\n{result}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xato: {e}")

# ---------------- Flask webhook ----------------
@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    return "✅ SMM Bot ishlayapti!", 200

# ---------------- Main ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
