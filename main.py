import os
import requests
from flask import Flask, request
from telebot import TeleBot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY   = os.getenv("API_KEY")
ADMIN_ID  = int(os.getenv("ADMIN_ID"))
CHANNELS  = os.getenv("CHANNELS")  # @kanal
GROUPS    = os.getenv("GROUPS")    # @guruh

bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Kanal va guruhga obuna tekshirish
def check_subscription(user_id):
    # Telegram API orqali tekshirish qo'shiladi
    return True

# Xizmatlar ro'yxatini olish
def get_services():
    url = "https://uzbek-seen.uz/api/v2"
    params = {"key": API_KEY, "action": "services"}
    r = requests.get(url, params=params)
    return r.json()

# Buyurtma qo'shish
def add_order(service_id, link, quantity):
    url = "https://uzbek-seen.uz/api/v2"
    params = {
        "key": API_KEY,
        "action": "add",
        "service": service_id,
        "link": link,
        "quantity": quantity
    }
    r = requests.post(url, data=params)
    return r.json()

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_json()
    bot.process_new_updates([json_data])
    return {"ok": True}

@app.route("/")
def index():
    return "Bot ishlayapti!"

# Start handler
@bot.message_handler(commands=["start"])
def start_message(message):
    if not check_subscription(message.from_user.id):
        bot.send_message(message.chat.id, f"Iltimos kanalga obuna bo'ling: {CHANNELS}")
        return
    bot.send_message(message.chat.id, "Salom! SMM xizmatlar botiga xush kelibsiz.")
    services = get_services()
    text = "Xizmatlar ro'yxati:\n\n"
    for s in services:
        text += f"{s['service']}. {s['name']} ({s['rate']} UZS)\n"
    bot.send_message(message.chat.id, text)

# Buyurtmalar handler
@bot.message_handler(commands=["order"])
def order_message(message):
    try:
        if not check_subscription(message.from_user.id):
            bot.send_message(message.chat.id, f"Iltimos kanalga obuna bo'ling: {CHANNELS}")
            return
        order_resp = add_order(service_id=1, link="https://t.me/username", quantity=100)
        bot.send_message(message.chat.id, f"Buyurtma qo'shildi: {order_resp}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
