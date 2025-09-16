import os
import requests
from flask import Flask, request
import telebot
from telebot import types
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()

TOKEN = os.environ.get("TOKEN")
ADMIN = os.environ.get("ADMIN")            # Telegram username
CHANNEL = os.environ.get("CHANNEL")        # Majburiy kanal (admin qo‘shadi)
GROUP = os.environ.get("GROUP")            # Majburiy guruh (admin qo‘shadi)
API_KEY = os.environ.get("API_KEY")        # SMM API key
PORT = int(os.environ.get("PORT", 5000))

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Inline tugmalar
def admin_menu():
    menu = types.InlineKeyboardMarkup()
    menu.add(
        types.InlineKeyboardButton("➕ Kanal qo‘shish", callback_data="add_channel"),
        types.InlineKeyboardButton("➖ Kanal o‘chirish", callback_data="remove_channel")
    )
    menu.add(
        types.InlineKeyboardButton("➕ Guruh qo‘shish", callback_data="add_group"),
        types.InlineKeyboardButton("➖ Guruh o‘chirish", callback_data="remove_group")
    )
    menu.add(
        types.InlineKeyboardButton("💰 Balans", callback_data="balance"),
        types.InlineKeyboardButton("📦 Buyurtmalar", callback_data="orders")
    )
    return menu

def user_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add("📦 Buyurtma qo‘yish", "💰 Balansni tekshirish")
    return menu

# Admin faqat o‘z username orqali ishlaydi
def is_admin(username):
    return username == ADMIN

# SMM API bilan ishlash
SMM_API_URL = "https://uzbek-seen.uz/api/v2"

def get_services():
    resp = requests.post(SMM_API_URL, data={"key": API_KEY, "action": "services"})
    if resp.ok:
        return resp.json()
    return []

def add_order(service_id, link, quantity):
    resp = requests.post(SMM_API_URL, data={
        "key": API_KEY,
        "action": "add",
        "service": service_id,
        "link": link,
        "quantity": quantity
    })
    if resp.ok:
        return resp.json()
    return {}

def get_balance():
    resp = requests.post(SMM_API_URL, data={"key": API_KEY, "action": "balance"})
    if resp.ok:
        return resp.json()
    return {}

def get_orders():
    resp = requests.post(SMM_API_URL, data={"key": API_KEY, "action": "orders"})
    if resp.ok:
        return resp.json()
    return []

# /start
@bot.message_handler(commands=["start"])
def start(message):
    if is_admin(message.from_user.username):
        bot.send_message(message.chat.id, "Salom Admin! Botga xush kelibsiz.", reply_markup=admin_menu())
    else:
        bot.send_message(message.chat.id, "Salom! SMM xizmatlar botiga xush kelibsiz.", reply_markup=user_menu())

# Inline tugmalar
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    username = call.from_user.username

    if not is_admin(username):
        bot.answer_callback_query(call.id, "Bu tugma faqat admin uchun!")
        return

    if call.data == "add_channel":
        bot.send_message(chat_id, "Majburiy kanal username sini yuboring (misol: @kanal):")
        bot.register_next_step_handler_by_chat_id(chat_id, add_channel)
    elif call.data == "remove_channel":
        global CHANNEL
        CHANNEL = None
        bot.send_message(chat_id, "Kanal o‘chirildi!")
    elif call.data == "add_group":
        bot.send_message(chat_id, "Majburiy guruh username sini yuboring (misol: @guruh):")
        bot.register_next_step_handler_by_chat_id(chat_id, add_group)
    elif call.data == "remove_group":
        global GROUP
        GROUP = None
        bot.send_message(chat_id, "Guruh o‘chirildi!")
    elif call.data == "balance":
        bal = get_balance()
        bot.send_message(chat_id, f"💰 Balans: {bal.get('balance','0')} {bal.get('currency','UZS')}")
    elif call.data == "orders":
        orders = get_orders()
        if orders:
            text = "📦 Buyurtmalar:\n\n"
            for o in orders:
                text += f"ID: {o['order']}, Xizmat: {o['service']}, Status: {o['status']}\n"
            bot.send_message(chat_id, text)
        else:
            bot.send_message(chat_id, "📦 Buyurtma topilmadi.")

def add_channel(message):
    global CHANNEL
    CHANNEL = message.text
    bot.send_message(message.chat.id, f"Kanal qo‘shildi: {CHANNEL}")

def add_group(message):
    global GROUP
    GROUP = message.text
    bot.send_message(message.chat.id, f"Guruh qo‘shildi: {GROUP}")

# Foydalanuvchi tugmalar
@bot.message_handler(func=lambda message: message.text in ["📦 Buyurtma qo‘yish","💰 Balansni tekshirish"])
def user_actions(message):
    chat_id = message.chat.id
    if message.text == "📦 Buyurtma qo‘yish":
        services = get_services()
        text = "Xizmatlar:\n\n"
        for s in services:
            text += f"ID: {s['service']}, {s['name']}, Narx: {s['rate']} UZS\n"
        bot.send_message(chat_id, text + "\nBuyurtma uchun: XizmatID Link Quantity")
        bot.register_next_step_handler(message, create_order)
    elif message.text == "💰 Balansni tekshirish":
        bal = get_balance()
        bot.send_message(chat_id, f"💰 Balans: {bal.get('balance','0')} {bal.get('currency','UZS')}")

def create_order(message):
    try:
        service_id, link, quantity = message.text.split()
        order = add_order(service_id, link, quantity)
        if "order" in order:
            bot.send_message(message.chat.id, f"✅ Buyurtma qabul qilindi! Order ID: {order['order']}")
        else:
            bot.send_message(message.chat.id, f"❌ Xatolik yuz berdi: {order}")
    except:
        bot.send_message(message.chat.id, "❌ Format xato! Misol: 1 https://t.me/username 100")

# Flask Webhook
@server.route(f"/{TOKEN}", methods=["POST"])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    return "SMM Bot ishlayapti! ✅", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=PORT)
