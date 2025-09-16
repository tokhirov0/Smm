import os
from flask import Flask, request
import telebot
from telebot import types
import requests

# Environment Variables
TOKEN = os.environ.get("TOKEN")
OWNER_ID = int(os.environ.get("OWNER"))
OWNER_USERNAME = os.environ.get("OWNER_USERNAME")
GROUP = os.environ.get("GROUP")
CHANNEL = os.environ.get("CHANNEL")
API_KEY = os.environ.get("API_KEY")

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Inline menu foydalanuvchiga
def inline_menu():
    menu = types.InlineKeyboardMarkup()
    menu.add(types.InlineKeyboardButton("📋 Xizmatlar ro'yxati", callback_data="services"))
    menu.add(types.InlineKeyboardButton("💰 Balansni tekshirish", callback_data="balance"))
    menu.add(
        types.InlineKeyboardButton("🔵 Admin", url=f"https://t.me/{OWNER_USERNAME}"),
        types.InlineKeyboardButton("👥 Guruh", url=f"https://t.me/{GROUP}"),
        types.InlineKeyboardButton("📣 Kanal", url=f"https://t.me/{CHANNEL}")
    )
    return menu

# Admin menyusi
def admin_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add("➕ Kanal qo'shish", "➖ Kanal o'chirish")
    menu.add("➕ Guruh qo'shish", "➖ Guruh o'chirish")
    menu.add("📋 Buyurtmalar", "💰 Balans")
    return menu

# /start
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.chat.id
    if user_id == OWNER_ID:
        bot.send_message(user_id, "👑 Admin panelga xush kelibsiz", reply_markup=admin_menu())
    else:
        bot.send_message(user_id, "👋 Salom! SMM xizmat botiga xush kelibsiz.", reply_markup=inline_menu())

# Inline tugmalar
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    try:
        if call.data == "services":
            response = requests.get(
                "https://uzbek-seen.uz/api/v2",
                params={"key": API_KEY, "action": "services"}
            )
            data = response.json()
            msg = "📋 Mavjud xizmatlar:\n\n"
            for item in data:
                msg += f"{item['service']}. {item['name']} ({item['rate']} UZS) [Min: {item['min']}, Max: {item['max']}]\n"
            bot.send_message(user_id, msg)

        elif call.data == "balance":
            response = requests.get(
                "https://uzbek-seen.uz/api/v2",
                params={"key": API_KEY, "action": "balance"}
            )
            data = response.json()
            bot.send_message(user_id, f"💰 Sizning balansingiz: {data['balance']} {data['currency']}")
    except Exception as e:
        bot.send_message(user_id, f"❌ Xatolik yuz berdi: {e}")

# Admin buyruqlari
@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID)
def admin_handler(message):
    text = message.text
    if text == "➕ Kanal qo'shish":
        bot.send_message(OWNER_ID, "Kanal username-ni kiriting (masalan: anketaa_uz)")
    elif text.startswith("@") or text.isalnum():
        global CHANNEL
        CHANNEL = text.replace("@", "")
        bot.send_message(OWNER_ID, f"📣 Kanal o‘rnatildi: {CHANNEL}")
    elif text == "➖ Kanal o'chirish":
        CHANNEL = ""
        bot.send_message(OWNER_ID, "📣 Kanal o‘chirildi!")
    elif text == "➕ Guruh qo'shish":
        bot.send_message(OWNER_ID, "Guruh username-ni kiriting (masalan: anonimchat15)")
    elif text.startswith("#") or text.isalnum():
        global GROUP
        GROUP = text.replace("@", "")
        bot.send_message(OWNER_ID, f"👥 Guruh o‘rnatildi: {GROUP}")
    elif text == "➖ Guruh o'chirish":
        GROUP = ""
        bot.send_message(OWNER_ID, "👥 Guruh o‘chirildi!")
    elif text == "📋 Buyurtmalar":
        bot.send_message(OWNER_ID, "Buyurtmalar funksiyasi hozircha tayyor emas.")
    elif text == "💰 Balans":
        try:
            response = requests.get(
                "https://uzbek-seen.uz/api/v2",
                params={"key": API_KEY, "action": "balance"}
            )
            data = response.json()
            bot.send_message(OWNER_ID, f"💰 Balans: {data['balance']} {data['currency']}")
        except Exception as e:
            bot.send_message(OWNER_ID, f"❌ Xatolik: {e}")

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
