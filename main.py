import os
import requests
from flask import Flask, request
import telebot
from telebot import types

# Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("SMM_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNELS = os.getenv("CHANNELS", "").split(",")  # Majburiy kanallar
GROUPS = os.getenv("GROUPS", "").split(",")      # Majburiy guruhlar

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Inline menu
def inline_menu():
    menu = types.InlineKeyboardMarkup()
    menu.add(types.InlineKeyboardButton("📜 Xizmatlar", callback_data="services"))
    menu.add(types.InlineKeyboardButton("💰 Balans", callback_data="balance"))
    menu.add(types.InlineKeyboardButton("➕ Buyurtma berish", callback_data="order"))
    menu.add(types.InlineKeyboardButton("⚙ Admin panel", callback_data="admin_panel"))
    return menu

# Kanal/guruh obuna tekshiruvi
def check_subscriptions(user_id):
    for ch in CHANNELS + GROUPS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# API funksiya: xizmatlar
def get_services():
    r = requests.get("https://uzbek-seen.uz/api/v2", params={"key": API_KEY, "action": "services"})
    return r.json()

# API funksiya: balans
def get_balance():
    r = requests.get("https://uzbek-seen.uz/api/v2", params={"key": API_KEY, "action": "balance"})
    return r.json()

# API funksiya: buyurtma
def create_order(service_id, link, quantity):
    r = requests.post("https://uzbek-seen.uz/api/v2", data={
        "key": API_KEY,
        "action": "add",
        "service": service_id,
        "link": link,
        "quantity": quantity
    })
    return r.json()

# Start komandasi
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.chat.id
    if not check_subscriptions(user_id):
        text = "❌ Xizmatdan foydalanish uchun barcha kanallar va guruhlarga obuna bo‘ling:"
        for ch in CHANNELS + GROUPS:
            text += f"\n🔗 @{ch}"
        bot.send_message(user_id, text)
        return
    bot.send_message(user_id, "👋 SMM botiga xush kelibsiz!", reply_markup=inline_menu())

# Callback tugmalar
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    if not check_subscriptions(user_id):
        bot.answer_callback_query(call.id, "❌ Kanal yoki guruhga obuna bo‘ling!")
        return

    if call.data == "services":
        services = get_services()
        text = "🌐 Xizmatlar ro'yxati:\n\n"
        for s in services:
            text += f"{s['service']}. {s['name']} ({s['rate']} UZS)\nMin: {s['min']} Max: {s['max']}\n\n"
        bot.send_message(user_id, text)

    elif call.data == "balance":
        balance = get_balance()
        bot.send_message(user_id, f"💰 Balans: {balance['balance']} {balance['currency']}")

    elif call.data == "order":
        bot.send_message(user_id, "Buyurtma berish formatida yozing:\n/service_id link quantity\nMasalan:\n/23501 https://t.me/example 50")

    elif call.data == "admin_panel":
        if user_id != ADMIN_ID:
            bot.send_message(user_id, "❌ Faqat admin foydalanishi mumkin.")
        else:
            bot.send_message(user_id, "⚙ Admin panel")

# Buyurtma komandasi
@bot.message_handler(commands=["order"])
def order_command(message):
    user_id = message.chat.id
    if not check_subscriptions(user_id):
        bot.send_message(user_id, "❌ Kanal yoki guruhga obuna bo‘ling!")
        return

    try:
        parts = message.text.split()
        if len(parts) < 4:
            bot.send_message(user_id, "Foydalanish: /order <service_id> <link> <quantity>")
            return
        service_id = parts[1]
        link = parts[2]
        quantity = parts[3]
        result = create_order(service_id, link, quantity)
        bot.send_message(user_id, f"✅ Buyurtma: {result}")
    except Exception as e:
        bot.send_message(user_id, f"Xatolik yuz berdi: {e}")

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
