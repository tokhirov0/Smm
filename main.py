import os
import requests
from flask import Flask, request
import telebot
from telebot import types

# =======================
# Environment Variables
# =======================
BOT_TOKEN = os.environ.get("BOT_TOKEN")          # Telegram bot token
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))    # Admin telegram ID
SMM_API_KEY = os.environ.get("SMM_API_KEY")      # uzbek-seen.uz API key
bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

# =======================
# Admin managed channels/groups
# =======================
CHANNELS = []  # Admin qo‘shadi, bot avtomatik tekshiradi

# =======================
# Helper Functions
# =======================
def get_services():
    url = "https://uzbek-seen.uz/api/v2"
    data = {"key": SMM_API_KEY, "action": "services"}
    r = requests.post(url, data=data)
    return r.json()

def add_order(service_id, link, quantity):
    url = "https://uzbek-seen.uz/api/v2"
    data = {"key": SMM_API_KEY, "action": "add", "service": service_id, "link": link, "quantity": quantity}
    r = requests.post(url, data=data)
    return r.json()

def order_status(order_id):
    url = "https://uzbek-seen.uz/api/v2"
    data = {"key": SMM_API_KEY, "action": "status", "order": order_id}
    r = requests.post(url, data=data)
    return r.json()

def user_balance():
    url = "https://uzbek-seen.uz/api/v2"
    data = {"key": SMM_API_KEY, "action": "balance"}
    r = requests.post(url, data=data)
    return r.json()

def admin_only(func):
    def wrapper(message, *args, **kwargs):
        if message.from_user.id != ADMIN_ID:
            bot.send_message(message.chat.id, "❌ Siz admin emassiz!")
            return
        return func(message, *args, **kwargs)
    return wrapper

# =======================
# Bot Commands
# =======================
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Xizmatlar", "💰 Balans")
    bot.send_message(message.chat.id, "👋 Salom! SMM botiga xush kelibsiz.", reply_markup=markup)

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Kanal qo‘shish", "➖ Kanal o‘chirish", "📦 Buyurtmalar", "📊 Statistika")
    bot.send_message(message.chat.id, "🛠 Admin panel", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📋 Xizmatlar")
def services(message):
    try:
        services = get_services()
        text = "📋 Xizmatlar:\n\n"
        for s in services:
            text += f"{s['service']}. {s['name']} - {s['rate']} UZS\n"
        bot.send_message(message.chat.id, text)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

@bot.message_handler(func=lambda m: m.text == "💰 Balans")
def balance(message):
    try:
        bal = user_balance()
        bot.send_message(message.chat.id, f"💰 Sizning balans: {bal['balance']} {bal['currency']}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

# =======================
# Admin channel/group management
# =======================
@bot.message_handler(func=lambda m: m.text in ["➕ Kanal qo‘shish", "➖ Kanal o‘chirish"])
@admin_only
def manage_channels(message):
    if message.text == "➕ Kanal qo‘shish":
        msg = bot.send_message(message.chat.id, "Kanal yoki guruh username (@username) ni yuboring:")
        bot.register_next_step_handler(msg, add_channel)
    else:
        msg = bot.send_message(message.chat.id, "O‘chirish uchun username yuboring:")
        bot.register_next_step_handler(msg, remove_channel)

def add_channel(message):
    CHANNELS.append(message.text)
    bot.send_message(message.chat.id, f"✅ {message.text} qo‘shildi!")

def remove_channel(message):
    if message.text in CHANNELS:
        CHANNELS.remove(message.text)
        bot.send_message(message.chat.id, f"✅ {message.text} o‘chirildi!")
    else:
        bot.send_message(message.chat.id, "❌ Bu kanal topilmadi.")

# =======================
# Flask Webhook
# =======================
@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    return "Bot ishlayapti ✅", 200

# =======================
# Run Flask server
# =======================
if __name__ == "__main__":
    # Set webhook
    WEBHOOK_URL = f"https://smm-3.onrender.com/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
