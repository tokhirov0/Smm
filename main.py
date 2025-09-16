import os
import requests
from flask import Flask, request
import telebot
from telebot import types

# =================== CONFIG ===================
TOKEN = os.environ.get("TOKEN")  # Admin o'zi Render Environment Variables orqali qo'yadi
OWNER = os.environ.get("OWNER")  # Telegram username
API_KEY = os.environ.get("API_KEY")  # Uzbek-seen API key

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Bot data
bot_data = {"channel": "", "group": ""}

# =================== MESSAGES ===================
m_start = "👋 Salom! SMM botga xush kelibsiz. Kanalga obuna bo'ling va xizmatlardan foydalaning."
m_no_sub = "⚠️ Siz kanalga obuna bo'lishingiz kerak: @{channel}"
m_only_admin = "❌ Bu faqat admin uchun."

# =================== INLINE BUTTONS ===================
def inline_menu():
    menu = types.InlineKeyboardMarkup()
    menu.add(
        types.InlineKeyboardButton("📜 Xizmatlar ro'yxati", callback_data="services"),
        types.InlineKeyboardButton("💰 Balans", callback_data="balance")
    )
    menu.add(
        types.InlineKeyboardButton("🛒 Buyurtma qo'shish", callback_data="add_order")
    )
    return menu

# =================== ADMIN COMMANDS ===================
@bot.message_handler(commands=["setchannel"])
def set_channel(msg):
    if msg.from_user.username != OWNER:
        bot.send_message(msg.chat.id, m_only_admin)
        return
    try:
        _, channel_name = msg.text.split()
        bot_data["channel"] = channel_name
        bot.send_message(msg.chat.id, f"✅ Kanal o'rnatildi: @{channel_name}")
    except:
        bot.send_message(msg.chat.id, "❌ Format: /setchannel kanal_nomi")

@bot.message_handler(commands=["setgroup"])
def set_group(msg):
    if msg.from_user.username != OWNER:
        bot.send_message(msg.chat.id, m_only_admin)
        return
    try:
        _, group_name = msg.text.split()
        bot_data["group"] = group_name
        bot.send_message(msg.chat.id, f"✅ Guruh o'rnatildi: @{group_name}")
    except:
        bot.send_message(msg.chat.id, "❌ Format: /setgroup guruh_nomi")

# =================== SUBSCRIBE CHECK ===================
def check_subscribe(user_id):
    channel = bot_data.get("channel")
    if not channel:
        return True  # Kanal o'rnatilmagan bo'lsa, tekshiruv o'tkazilmaydi
    try:
        member = bot.get_chat_member(f"@{channel}", user_id)
        if member.status in ["left", "kicked"]:
            return False
        return True
    except:
        return False

# =================== START COMMAND ===================
@bot.message_handler(commands=["start"])
def start(msg):
    user_id = msg.chat.id
    if not check_subscribe(user_id):
        bot.send_message(user_id, m_no_sub.format(channel=bot_data.get("channel")))
        return
    bot.send_message(user_id, m_start, reply_markup=inline_menu())

# =================== INLINE CALLBACKS ===================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id

    # Balans
    if call.data == "balance":
        res = requests.post(
            "https://uzbek-seen.uz/api/v2",
            data={"key": API_KEY, "action": "balance"}
        ).json()
        balance = res.get("balance", "0")
        currency = res.get("currency", "UZS")
        bot.send_message(user_id, f"💰 Balans: {balance} {currency}")

    # Xizmatlar
    elif call.data == "services":
        res = requests.post(
            "https://uzbek-seen.uz/api/v2",
            data={"key": API_KEY, "action": "services"}
        ).json()
        text = "📜 Xizmatlar ro'yxati:\n\n"
        for s in res:
            text += f"{s['service']}. {s['name']} | Min: {s['min']} | Max: {s['max']} | Narx: {s['rate']}\n"
        bot.send_message(user_id, text)

    # Buyurtma qo'shish (oddiy misol)
    elif call.data == "add_order":
        bot.send_message(user_id, "💡 Buyurtma qo'shish uchun:\nFormat: service_id link quantity")
        bot.register_next_step_handler_by_chat_id(user_id, process_order)

def process_order(msg):
    user_id = msg.chat.id
    try:
        service, link, quantity = msg.text.split()
        res = requests.post(
            "https://uzbek-seen.uz/api/v2",
            data={
                "key": API_KEY,
                "action": "add",
                "service": service,
                "link": link,
                "quantity": quantity
            }
        ).json()
        order_id = res.get("order")
        if order_id:
            bot.send_message(user_id, f"✅ Buyurtma qo'shildi. ID: {order_id}")
        else:
            bot.send_message(user_id, "❌ Buyurtma qo'shilmadi. Ma'lumotni tekshiring.")
    except:
        bot.send_message(user_id, "❌ Format noto'g'ri. Misol: 15 https://t.me/username 100")

# =================== FLASK WEBHOOK ===================
@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    return "Bot ishlayapti! ✅", 200

# =================== RUN ===================
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
