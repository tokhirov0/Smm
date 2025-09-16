import os
import requests
from flask import Flask, request
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
API_KEY = os.getenv("API_KEY")

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Kanallar va guruhlar
channels = {}
groups = {}

# Inline menu
def inline_menu():
    menu = types.InlineKeyboardMarkup()
    menu.add(types.InlineKeyboardButton("💬 Xizmatlar", callback_data="services"))
    if ADMIN_ID:
        menu.add(types.InlineKeyboardButton("⚙️ Admin panel", callback_data="admin_panel"))
    return menu

# Start komandasi
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    bot.send_message(user_id, "👋 Salom! SMM botga xush kelibsiz.", reply_markup=inline_menu())

# Inline tugmalar
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id

    # Xizmatlar
    if call.data == "services":
        # Kanal va guruh tekshiruvi
        missing = []
        for ch in channels.values():
            member = bot.get_chat_member(ch, user_id)
            if member.status == "left":
                missing.append(ch)
        for gr in groups.values():
            member = bot.get_chat_member(gr, user_id)
            if member.status == "left":
                missing.append(gr)
        if missing:
            bot.send_message(user_id, "❌ Buyurtma berishdan oldin kanal/guruhga obuna bo'ling!")
            return
        # SMM xizmatlarini olish
        res = requests.get("https://uzbek-seen.uz/api/v2", params={"key": API_KEY, "action": "services"}).json()
        msg = "🌐 Xizmatlar:\n"
        for s in res:
            msg += f"{s['service']}: {s['name']} ({s['rate']} UZS)\n"
        bot.send_message(user_id, msg)

    # Admin panel
    elif call.data == "admin_panel" and user_id == ADMIN_ID:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ Kanal qo‘shish", callback_data="add_channel"))
        kb.add(types.InlineKeyboardButton("➖ Kanal o‘chirish", callback_data="del_channel"))
        kb.add(types.InlineKeyboardButton("➕ Guruh qo‘shish", callback_data="add_group"))
        kb.add(types.InlineKeyboardButton("➖ Guruh o‘chirish", callback_data="del_group"))
        bot.send_message(user_id, "⚙️ Admin panel:", reply_markup=kb)

    # Kanal/Guruh qo‘shish va o‘chirish (oddiy misol)
    elif call.data.startswith("add_channel") and user_id == ADMIN_ID:
        # Keyingi xabarni kutib, kanal ID qabul qiladigan kod yozish mumkin
        bot.send_message(user_id, "Kanal ID ni jo'nating:")
        bot.register_next_step_handler_by_chat_id(user_id, add_channel)

    elif call.data.startswith("del_channel") and user_id == ADMIN_ID:
        bot.send_message(user_id, "O‘chirish uchun kanal ID ni jo'nating:")
        bot.register_next_step_handler_by_chat_id(user_id, del_channel)

    elif call.data.startswith("add_group") and user_id == ADMIN_ID:
        bot.send_message(user_id, "Guruh ID ni jo'nating:")
        bot.register_next_step_handler_by_chat_id(user_id, add_group)

    elif call.data.startswith("del_group") and user_id == ADMIN_ID:
        bot.send_message(user_id, "O‘chirish uchun guruh ID ni jo'nating:")
        bot.register_next_step_handler_by_chat_id(user_id, del_group)

# Admin funksiyalari
def add_channel(message):
    channels[message.text] = int(message.text)
    bot.send_message(ADMIN_ID, f"Kanal qo‘shildi: {message.text}")

def del_channel(message):
    channels.pop(message.text, None)
    bot.send_message(ADMIN_ID, f"Kanal o‘chirildi: {message.text}")

def add_group(message):
    groups[message.text] = int(message.text)
    bot.send_message(ADMIN_ID, f"Guruh qo‘shildi: {message.text}")

def del_group(message):
    groups.pop(message.text, None)
    bot.send_message(ADMIN_ID, f"Guruh o‘chirildi: {message.text}")

# Flask webhook
@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def home():
    return "Bot ishlayapti! ✅", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
