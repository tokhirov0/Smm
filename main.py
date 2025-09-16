import os
import requests
from telebot import TeleBot, types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNELS = os.getenv("CHANNELS").split(",")
GROUPS = os.getenv("GROUPS").split(",")

bot = TeleBot(BOT_TOKEN)

BASE_URL = "https://uzbek-seen.uz/api/v2"

# ================== API FUNKSIYALARI ==================
def get_services():
    params = {"key": API_KEY, "action": "services"}
    res = requests.get(BASE_URL, params=params)
    return res.json()

def add_order(service_id, link, quantity):
    data = {"key": API_KEY, "action": "add", "service": service_id, "link": link, "quantity": quantity}
    res = requests.post(BASE_URL, data=data)
    return res.json()

def order_status(order_id):
    data = {"key": API_KEY, "action": "status", "order": order_id}
    res = requests.get(BASE_URL, params=data)
    return res.json()

def user_balance():
    data = {"key": API_KEY, "action": "balance"}
    res = requests.get(BASE_URL, params=data)
    return res.json()

# ================== ADMIN FUNKSIYALARI ==================
def is_admin(user_id):
    return user_id == ADMIN_ID

# ================== OBUNA TEKSHIRISH ==================
def check_subscribe(user_id):
    for ch in CHANNELS + GROUPS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ================== BOT HANDLERLARI ==================
@bot.message_handler(commands=["start"])
def start(message):
    if not check_subscribe(message.from_user.id):
        text = "❌ Iltimos, buyurtmalarni ishlatish uchun kanal va guruhga obuna bo‘ling."
        bot.send_message(message.chat.id, text)
        return
    text = "✅ Salom! SMM botga xush kelibsiz."
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["services"])
def services(message):
    services = get_services()
    text = "📋 Xizmatlar ro'yxati:\n"
    for s in services:
        text += f"{s['service']}. {s['name']} — Narxi: {s['rate']} UZS\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["order"])
def order(message):
    try:
        _, service_id, link, quantity = message.text.split()
        res = add_order(service_id, link, quantity)
        bot.send_message(message.chat.id, f"Buyurtma qo‘shildi: {res}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")

@bot.message_handler(commands=["status"])
def status(message):
    try:
        _, order_id = message.text.split()
        res = order_status(order_id)
        bot.send_message(message.chat.id, f"Buyurtma holati: {res}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")

@bot.message_handler(commands=["balance"])
def balance(message):
    res = user_balance()
    bot.send_message(message.chat.id, f"Balans: {res['balance']} {res['currency']}")

# ================== ADMIN KANAL/GURUH QO‘SHISH/OLISH ==================
@bot.message_handler(commands=["addchannel"])
def add_channel(message):
    if not is_admin(message.from_user.id):
        return
    try:
        _, ch = message.text.split()
        CHANNELS.append(ch)
        bot.send_message(message.chat.id, f"Kanal qo‘shildi: {ch}")
    except:
        bot.send_message(message.chat.id, "Xato!")

@bot.message_handler(commands=["removechannel"])
def remove_channel(message):
    if not is_admin(message.from_user.id):
        return
    try:
        _, ch = message.text.split()
        if ch in CHANNELS:
            CHANNELS.remove(ch)
            bot.send_message(message.chat.id, f"Kanal o‘chirildi: {ch}")
    except:
        bot.send_message(message.chat.id, "Xato!")

@bot.message_handler(commands=["addgroup"])
def add_group(message):
    if not is_admin(message.from_user.id):
        return
    try:
        _, gr = message.text.split()
        GROUPS.append(gr)
        bot.send_message(message.chat.id, f"Guruh qo‘shildi: {gr}")
    except:
        bot.send_message(message.chat.id, "Xato!")

@bot.message_handler(commands=["removegroup"])
def remove_group(message):
    if not is_admin(message.from_user.id):
        return
    try:
        _, gr = message.text.split()
        if gr in GROUPS:
            GROUPS.remove(gr)
            bot.send_message(message.chat.id, f"Guruh o‘chirildi: {gr}")
    except:
        bot.send_message(message.chat.id, "Xato!")

# ================== RUN BOT ==================
bot.infinity_polling()
