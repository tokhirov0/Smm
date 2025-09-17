import os
import requests
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Siz Renderda envga kiritasiz
API_KEY = os.getenv("API_KEY")      # uzbek-seen.uz API key
ADMIN_ID = int(os.getenv("ADMIN_ID"))
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")  # Bo'sh qoldirilsa kanal tekshirmaydi

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Kanal obuna tekshirish
def is_subscribed(user_id):
    if not REQUIRED_CHANNEL:
        return True  # Kanal bo'sh bo'lsa hammasiga ruxsat
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status not in ['left', 'kicked']
    except:
        return False

# Start komanda
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id):
        bot.send_message(
            user_id,
            f"Bot xizmatlaridan foydalanish uchun kanalga obuna bo'ling: @{REQUIRED_CHANNEL}"
        )
        return
    bot.send_message(user_id, "Salom! SMM xizmatlaridan foydalanishingiz mumkin.")

# Admin: kanal/guruh qo'shish
@bot.message_handler(commands=["add_channel"])
def add_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Foydalanish: /add_channel @channelusername")
        return
    global REQUIRED_CHANNEL
    REQUIRED_CHANNEL = args[1]
    bot.reply_to(message, f"Kanal qo‘shildi: {REQUIRED_CHANNEL}")

# Admin: kanal o'chirish
@bot.message_handler(commands=["remove_channel"])
def remove_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
    global REQUIRED_CHANNEL
    REQUIRED_CHANNEL = ""
    bot.reply_to(message, "Majburiy kanal o‘chirildi.")

# SMM API xizmatlar
@bot.message_handler(commands=["services"])
def services(message):
    url = "https://uzbek-seen.uz/api/v2"
    params = {"key": API_KEY, "action": "services"}
    try:
        res = requests.get(url, params=params).json()
        text = "Xizmatlar:\n"
        for s in res:
            text += f"{s['service']}. {s['name']} - {s['rate']} UZS\n"
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, "Xizmatlarni olishda xatolik yuz berdi.")

# Flask webhook
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

@app.route("/")
def index():
    return "Bot ishga tushdi!"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://YOUR_RENDER_URL/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
