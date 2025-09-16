import os
import requests
from flask import Flask, request
import telebot
from telebot import types

# ---------------- CONFIG ----------------
TOKEN = "BOT_TOKENINGIZ"       # Admin tomonidan o‘rnatilgan token
ADMIN = "admin_username"       # Admin Telegram username
CHANNELS = []                  # Admin istagicha qo‘shadi
GROUPS = []                    # Admin istagicha qo‘shadi
SMM_API_KEY = "SMM_API_KEY"    # Uzbek-seen.uz API key
PORT = int(os.environ.get("PORT", 5000))
# --------------------------------------

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Inline menu yaratish
def inline_menu():
    menu = types.InlineKeyboardMarkup()
    menu.add(types.InlineKeyboardButton("📣 Kanal qo‘shish", callback_data="add_channel"))
    menu.add(types.InlineKeyboardButton("➖ Kanal o‘chirish", callback_data="del_channel"))
    menu.add(types.InlineKeyboardButton("👥 Guruh qo‘shish", callback_data="add_group"))
    menu.add(types.InlineKeyboardButton("➖ Guruh o‘chirish", callback_data="del_group"))
    menu.add(types.InlineKeyboardButton("💰 Buyurtmalar", callback_data="orders"))
    return menu

# Start komandasi
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.chat.id
    bot.send_message(user_id, "👋 Salom! SMM botga xush kelibsiz.", reply_markup=inline_menu())

# Inline tugmalarni boshqarish
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    if call.data == "add_channel":
        if user_id != ADMIN_ID:  # Admin tekshirish
            bot.send_message(user_id, "❌ Faqat admin bajarishi mumkin")
            return
        bot.send_message(user_id, "Kanal username (@username) ni yuboring:")
        bot.register_next_step_handler_by_chat_id(user_id, add_channel_step)
    elif call.data == "del_channel":
        if user_id != ADMIN_ID:
            bot.send_message(user_id, "❌ Faqat admin bajarishi mumkin")
            return
        bot.send_message(user_id, "O‘chirmoqchi bo‘lgan kanalni yuboring (@username):")
        bot.register_next_step_handler_by_chat_id(user_id, del_channel_step)
    elif call.data == "add_group":
        if user_id != ADMIN_ID:
            bot.send_message(user_id, "❌ Faqat admin bajarishi mumkin")
            return
        bot.send_message(user_id, "Guruh username (@username) ni yuboring:")
        bot.register_next_step_handler_by_chat_id(user_id, add_group_step)
    elif call.data == "del_group":
        if user_id != ADMIN_ID:
            bot.send_message(user_id, "❌ Faqat admin bajarishi mumkin")
            return
        bot.send_message(user_id, "O‘chirmoqchi bo‘lgan guruhni yuboring (@username):")
        bot.register_next_step_handler_by_chat_id(user_id, del_group_step)
    elif call.data == "orders":
        show_orders(user_id)

# Kanal qo‘shish
def add_channel_step(message):
    CHANNELS.append(message.text)
    bot.send_message(message.chat.id, f"✅ Kanal qo‘shildi: {message.text}")

# Kanal o‘chirish
def del_channel_step(message):
    if message.text in CHANNELS:
        CHANNELS.remove(message.text)
        bot.send_message(message.chat.id, f"✅ Kanal o‘chirildi: {message.text}")
    else:
        bot.send_message(message.chat.id, "❌ Kanal topilmadi")

# Guruh qo‘shish
def add_group_step(message):
    GROUPS.append(message.text)
    bot.send_message(message.chat.id, f"✅ Guruh qo‘shildi: {message.text}")

# Guruh o‘chirish
def del_group_step(message):
    if message.text in GROUPS:
        GROUPS.remove(message.text)
        bot.send_message(message.chat.id, f"✅ Guruh o‘chirildi: {message.text}")
    else:
        bot.send_message(message.chat.id, "❌ Guruh topilmadi")

# Buyurtmalarni ko‘rsatish (API bilan)
def show_orders(user_id):
    url = "https://uzbek-seen.uz/api/v2"
    params = {"key": SMM_API_KEY, "action": "orders"}
    try:
        resp = requests.post(url, data=params).json()
        if resp:
            msg = "📄 Buyurtmalar:\n"
            for order in resp:
                msg += f"Order: {order['order']}, Service: {order['service']}, Status: {order['status']}\n"
            bot.send_message(user_id, msg)
        else:
            bot.send_message(user_id, "❌ Buyurtmalar topilmadi")
    except Exception as e:
        bot.send_message(user_id, f"❌ Xato: {e}")

# Flask webhook
@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    return "SMM Bot ishlayapti! ✅", 200

# Botni ishga tushurish
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=PORT)
