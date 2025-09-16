import os
import requests
from flask import Flask, request
import telebot
from telebot import types

TOKEN = os.environ.get("TOKEN")
API_KEY = os.environ.get("API_KEY")  # uzbek-seen.uz API kaliti
CHANNEL = os.environ.get("CHANNEL")  # majburiy obuna kanali

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Inline menyu
def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📃 Xizmatlar ro'yxati", callback_data="services"))
    markup.add(types.InlineKeyboardButton("💰 Balansni tekshirish", callback_data="balance"))
    markup.add(types.InlineKeyboardButton("🛒 Buyurtma berish", callback_data="order"))
    return markup

# Kanalga obuna tekshirish
def check_channel(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except:
        return False

# /start komandasi
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.chat.id
    if not check_channel(user_id):
        bot.send_message(user_id, f"📢 Botdan foydalanish uchun kanalimizga obuna bo'ling: @{CHANNEL}")
        return
    bot.send_message(user_id, "Salom! SMM xizmatlar botiga xush kelibsiz.", reply_markup=main_menu())

# Inline tugmalar
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id

    if not check_channel(user_id):
        bot.send_message(user_id, f"📢 Xizmatlardan foydalanish uchun kanalga obuna bo'ling: @{CHANNEL}")
        return

    if call.data == "services":
        r = requests.post("https://uzbek-seen.uz/api/v2", data={"key": API_KEY, "action": "services"}).json()
        msg = "📃 Xizmatlar ro'yxati:\n\n"
        for s in r:
            msg += f"{s['service']}. {s['name']} ({s['min']}-{s['max']})\n"
        bot.send_message(user_id, msg)

    elif call.data == "balance":
        r = requests.post("https://uzbek-seen.uz/api/v2", data={"key": API_KEY, "action": "balance"}).json()
        bot.send_message(user_id, f"💰 Sizning balansingiz: {r['balance']} {r['currency']}")

    elif call.data == "order":
        bot.send_message(user_id, "🛒 Buyurtma berish uchun quyidagi formatda yuboring:\nservice_id|link|quantity\nMasalan:\n1|https://t.me/username|100")

# Buyurtma berish
@bot.message_handler(func=lambda m: "|" in m.text)
def order_handler(message):
    user_id = message.chat.id
    try:
        service_id, link, quantity = message.text.split("|")
        r = requests.post("https://uzbek-seen.uz/api/v2", data={
            "key": API_KEY,
            "action": "add",
            "service": service_id.strip(),
            "link": link.strip(),
            "quantity": quantity.strip()
        }).json()
        if "order" in r:
            bot.send_message(user_id, f"✅ Buyurtma qabul qilindi. Order ID: {r['order']}")
        else:
            bot.send_message(user_id, f"❌ Xatolik yuz berdi: {r}")
    except Exception as e:
        bot.send_message(user_id, f"❌ Format xatolik: {e}")

# Webhook Flask
@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    return "Bot ishlayapti ✅", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
