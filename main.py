import os
import requests
from flask import Flask, request
import telebot
from telebot import types

TOKEN = os.environ.get("TOKEN")
OWNER = os.environ.get("OWNER")
GROUP = os.environ.get("GROUP")
CHANNEL = os.environ.get("CHANNEL")
API_KEY = os.environ.get("API_KEY")

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Inline va Reply tugmalar
def inline_menu():
    menu = types.InlineKeyboardMarkup()
    menu.add(types.InlineKeyboardButton("💬 Yangi buyurtma", callback_data="NewOrder"))
    menu.add(
        types.InlineKeyboardButton("🔵 Admin", url=f"https://t.me/{OWNER}"),
        types.InlineKeyboardButton("👥 Guruh", url=f"https://t.me/{GROUP}"),
        types.InlineKeyboardButton("📣 Kanal", url=f"https://t.me/{CHANNEL}")
    )
    return menu

def generate_services_markup(services):
    markup = types.InlineKeyboardMarkup()
    for s in services:
        markup.add(types.InlineKeyboardButton(f"{s['name']} ({s['rate']} UZS)", callback_data=f"service_{s['service']}"))
    return markup

# Foydalanuvchi obuna tekshiruvi
def check_subscription(user_id):
    try:
        status = bot.get_chat_member(CHANNEL, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

# Admin kanal/guruh o'rnatish
@bot.message_handler(commands=["setchannel"])
def set_channel(message):
    if str(message.from_user.username) != OWNER:
        return
    args = message.text.split()
    if len(args) == 2:
        new_channel = args[1].replace("@","")
        os.environ["CHANNEL"] = new_channel
        global CHANNEL
        CHANNEL = new_channel
        bot.send_message(message.chat.id, f"✅ Kanal yangilandi: @{new_channel}")
    else:
        bot.send_message(message.chat.id, "❌ Foydalanish: /setchannel kanal_username")

@bot.message_handler(commands=["setgroup"])
def set_group(message):
    if str(message.from_user.username) != OWNER:
        return
    args = message.text.split()
    if len(args) == 2:
        new_group = args[1].replace("@","")
        os.environ["GROUP"] = new_group
        global GROUP
        GROUP = new_group
        bot.send_message(message.chat.id, f"✅ Guruh yangilandi: @{new_group}")
    else:
        bot.send_message(message.chat.id, "❌ Foydalanish: /setgroup guruh_username")

# /start
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.chat.id
    if not check_subscription(user_id):
        bot.send_message(user_id, f"❌ Iltimos, xizmatdan foydalanish uchun @{CHANNEL} kanaliga obuna bo'ling.", reply_markup=inline_menu())
        return
    bot.send_message(user_id, "👋 Salom! Xizmatdan foydalanishingiz mumkin.", reply_markup=inline_menu())

# API xizmatlarini olish
def get_services():
    url = "https://uzbek-seen.uz/api/v2"
    params = {"key": API_KEY, "action": "services"}
    res = requests.get(url, params=params).json()
    return res

# Buyurtma qo‘yish
def add_order(service_id, link, quantity):
    url = "https://uzbek-seen.uz/api/v2"
    params = {
        "key": API_KEY,
        "action": "add",
        "service": service_id,
        "link": link,
        "quantity": quantity
    }
    res = requests.post(url, data=params).json()
    return res

# Buyurtma statusi
def order_status(order_id):
    url = "https://uzbek-seen.uz/api/v2"
    params = {"key": API_KEY, "action": "status", "order": order_id}
    res = requests.get(url, params=params).json()
    return res

# Balans
def get_balance():
    url = "https://uzbek-seen.uz/api/v2"
    params = {"key": API_KEY, "action": "balance"}
    res = requests.get(url, params=params).json()
    return res.get("balance", "0")

# Inline tugmalar
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "NewOrder":
        services = get_services()
        bot.send_message(call.message.chat.id, "💠 Xizmatlar ro‘yxati:", reply_markup=generate_services_markup(services))
    elif call.data.startswith("service_"):
        service_id = int(call.data.split("_")[1])
        bot.send_message(call.message.chat.id, f"✅ Siz {service_id} xizmatini tanladingiz.\nLink va miqdorni yuboring (misol: link quantity)")

# Foydalanuvchi buyurtma ma’lumotini yuborsa
@bot.message_handler(func=lambda m: True)
def handle_order(message):
    try:
        service_id, link, quantity = map(str, message.text.split())
        quantity = int(quantity)
        res = add_order(service_id, link, quantity)
        bot.send_message(message.chat.id, f"✅ Buyurtma qabul qilindi!\nOrder ID: {res.get('order')}")
    except:
        bot.send_message(message.chat.id, "❌ Format xato. Misol: 1 https://t.me/channel 100")

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
