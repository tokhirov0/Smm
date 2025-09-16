import os
import requests
from flask import Flask, request
import telebot
from telebot import types

# Environment Variables
TOKEN = os.environ.get("TOKEN")
OWNER = os.environ.get("OWNER")  # Admin username
SMM_API_KEY = os.environ.get("SMM_API_KEY")  # API kalit
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Admin qo‘shadigan kanal va guruhlar
CHANNELS = []  # Admin qo‘shadi
GROUPS = []    # Admin qo‘shadi

# Inline menu yaratish
def inline_menu():
    menu = types.InlineKeyboardMarkup()
    menu.add(types.InlineKeyboardButton("🔵 Admin", url=f"https://t.me/{OWNER}"))
    for ch in CHANNELS:
        menu.add(types.InlineKeyboardButton(f"📣 Kanal: {ch}", url=f"https://t.me/{ch}"))
    for gr in GROUPS:
        menu.add(types.InlineKeyboardButton(f"👥 Guruh: {gr}", url=f"https://t.me/{gr}"))
    return menu

# Kanalga majburiy obuna tekshiruvi
def check_subscription(user_id):
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return ch
        except Exception:
            return ch
    return None

# /start komandasi
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    not_sub = check_subscription(user_id)
    if not_sub:
        bot.send_message(user_id, f"❌ Xizmatdan foydalanish uchun @{not_sub} kanaliga obuna bo‘ling.")
        return
    bot.send_message(user_id, "👋 Salom! SMM botiga xush kelibsiz.", reply_markup=inline_menu())

# SMM API funksiyalari
API_URL = "https://uzbek-seen.uz/api/v2"

def get_services():
    data = {"key": SMM_API_KEY, "action": "services"}
    res = requests.post(API_URL, data=data).json()
    return res

def add_order(service_id, link, quantity):
    data = {"key": SMM_API_KEY, "action": "add", "service": service_id, "link": link, "quantity": quantity}
    res = requests.post(API_URL, data=data).json()
    return res

def get_balance():
    data = {"key": SMM_API_KEY, "action": "balance"}
    res = requests.post(API_URL, data=data).json()
    return res

def get_order_status(order_id):
    data = {"key": SMM_API_KEY, "action": "status", "order": order_id}
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

@bot.message_handler(commands=["add_order"])
def add_order_handler(message):
    try:
        user_id = message.chat.id
        args = message.text.split()
        if len(args) != 4:
            bot.send_message(user_id, "❌ Format: /add_order <service_id> <link> <quantity>")
            return
        service_id, link, quantity = int(args[1]), args[2], int(args[3])
        res = add_order(service_id, link, quantity)
        if "order" in res:
            bot.send_message(user_id, f"✅ Buyurtma qo‘shildi. ID: {res['order']}")
        else:
            bot.send_message(user_id, f"❌ Xato: {res}")
    except Exception as e:
        bot.send_message(user_id, f"❌ Xato: {str(e)}")

@bot.message_handler(commands=["status"])
def status_order(message):
    try:
        user_id = message.chat.id
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(user_id, "❌ Format: /status <order_id>")
            return
        order_id = args[1]
        res = get_order_status(order_id)
        bot.send_message(user_id, f"📊 Order status:\n{res}")
    except Exception as e:
        bot.send_message(user_id, f"❌ Xato: {str(e)}")

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
