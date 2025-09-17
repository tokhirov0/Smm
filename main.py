import os
import telebot
from flask import Flask, request
import requests
from dotenv import load_dotenv
import json

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
API_KEY = os.getenv("API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

# Kanallar va guruhlar (admin bot orqali qo‘shadi)
channels = []
groups = []

# Funksiya: kanal qo‘shish
@bot.message_handler(commands=['addchannel'])
def add_channel(message):
    if message.from_user.id == ADMIN_ID:
        try:
            channel_link = message.text.split()[1]
            channels.append(channel_link)
            bot.reply_to(message, f"✅ Kanal qo‘shildi: {channel_link}")
        except IndexError:
            bot.reply_to(message, "❌ Kanal linkini yozing.")

# Funksiya: kanal o‘chirish
@bot.message_handler(commands=['delchannel'])
def del_channel(message):
    if message.from_user.id == ADMIN_ID:
        try:
            channel_link = message.text.split()[1]
            if channel_link in channels:
                channels.remove(channel_link)
                bot.reply_to(message, f"✅ Kanal o‘chirildi: {channel_link}")
            else:
                bot.reply_to(message, "❌ Kanal topilmadi.")
        except IndexError:
            bot.reply_to(message, "❌ Kanal linkini yozing.")

# Funksiya: guruh qo‘shish
@bot.message_handler(commands=['addgroup'])
def add_group(message):
    if message.from_user.id == ADMIN_ID:
        try:
            group_link = message.text.split()[1]
            groups.append(group_link)
            bot.reply_to(message, f"✅ Guruh qo‘shildi: {group_link}")
        except IndexError:
            bot.reply_to(message, "❌ Guruh linkini yozing.")

# Funksiya: guruh o‘chirish
@bot.message_handler(commands=['delgroup'])
def del_group(message):
    if message.from_user.id == ADMIN_ID:
        try:
            group_link = message.text.split()[1]
            if group_link in groups:
                groups.remove(group_link)
                bot.reply_to(message, f"✅ Guruh o‘chirildi: {group_link}")
            else:
                bot.reply_to(message, "❌ Guruh topilmadi.")
        except IndexError:
            bot.reply_to(message, "❌ Guruh linkini yozing.")

# Foydalanuvchi buyurtma qo‘shish
@bot.message_handler(commands=['order'])
def add_order(message):
    try:
        parts = message.text.split()
        service_id = parts[1]
        link = parts[2]
        quantity = parts[3]

        url = "https://uzbek-seen.uz/api/v2"
        data = {
            "key": API_KEY,
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity
        }
        response = requests.post(url, data=data).json()
        bot.reply_to(message, f"✅ Buyurtma qo‘shildi: {response}")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

# Foydalanuvchi balansni tekshirish
@bot.message_handler(commands=['balance'])
def get_balance(message):
    try:
        url = "https://uzbek-seen.uz/api/v2"
        data = {
            "key": API_KEY,
            "action": "balance"
        }
        response = requests.post(url, data=data).json()
        bot.reply_to(message, f"💰 Balans: {response['balance']} {response['currency']}")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

# Kanalga obuna tekshirish
def check_subscription(user_id):
    for ch in channels:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# Start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    if not check_subscription(message.from_user.id):
        bot.send_message(message.chat.id, "❗ Xizmatdan foydalanish uchun kanallarga obuna bo‘ling.")
    else:
        bot.send_message(message.chat.id, "✅ Xush kelibsiz! Buyurtmalarni qo‘shishingiz mumkin.")

# Flask webhook
@server.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    return "Bot ishlayapti!", 200

# Botni webhook bilan ishga tushurish
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://YOUR_RENDER_URL/{BOT_TOKEN}")
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
