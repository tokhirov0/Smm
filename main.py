import os
import requests
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
API_KEY = os.getenv("API_KEY")
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

SMM_API = "https://uzbek-seen.uz/api/v2"

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def get_services():
    params = {"key": API_KEY, "action": "services"}
    r = requests.get(SMM_API, params=params)
    return r.json()

def add_order(service_id, link, quantity):
    params = {"key": API_KEY, "action": "add", "service": service_id, "link": link, "quantity": quantity}
    r = requests.post(SMM_API, data=params)
    return r.json()

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        bot.send_message(user_id, f"Botdan foydalanish uchun kanalimizga obuna bo‘ling: {REQUIRED_CHANNEL}")
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Xizmatlar ro‘yxati", callback_data="services"))
    bot.send_message(user_id, "Xush kelibsiz! Xizmatni tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    if call.data == "services":
        services = get_services()
        text = "Xizmatlar:\n"
        for s in services:
            text += f"{s['service']}: {s['name']} | Narxi: {s['rate']} UZS | Min: {s['min']} | Max: {s['max']}\n"
        bot.send_message(user_id, text)

# Admin komandasi orqali kanal qo‘shish / o‘chirish
@bot.message_handler(commands=["addchannel"])
def add_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
    global REQUIRED_CHANNEL
    REQUIRED_CHANNEL = message.text.split()[1]
    bot.send_message(message.chat.id, f"Kanal yangilandi: {REQUIRED_CHANNEL}")

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://smm-4.onrender.com/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
