import os
import requests
from flask import Flask, request
import telebot

# ================= Environment Variables =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")       # Masalan: 8467603767:AAGURwyZ9D1GcTfYp3EU2yC0AnuHLynZy60
ADMIN_ID = int(os.environ.get("ADMIN_ID"))    # Telegram ID raqam sifatida
SMM_API_KEY = os.environ.get("SMM_API_KEY")  # SMM API key (uzbek-seen.uz)
PORT = int(os.environ.get("PORT", 5000))     # Render port

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ================= Admin boshqaruvi =================
channels = []  # Admin qo‘shgan kanallar
groups = []    # Admin qo‘shgan guruhlar

# ================= Inline menyu =================
def inline_menu():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔄 Buyurtmalar", callback_data="orders"))
    markup.add(telebot.types.InlineKeyboardButton("➕ Kanal qo'shish", callback_data="add_channel"))
    markup.add(telebot.types.InlineKeyboardButton("➖ Kanal o'chirish", callback_data="remove_channel"))
    markup.add(telebot.types.InlineKeyboardButton("➕ Guruh qo'shish", callback_data="add_group"))
    markup.add(telebot.types.InlineKeyboardButton("➖ Guruh o'chirish", callback_data="remove_group"))
    return markup

# ================= /start komandasi =================
@bot.message_handler(commands=["start"])
def start_handler(message):
    bot.send_message(message.chat.id, "Salom! SMM bot ishga tushdi.", reply_markup=inline_menu())

# ================= Callback tugmalar =================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Faqat admin ishlata oladi!")
        return

    if call.data == "orders":
        # Buyurtmalarni olish
        url = "https://uzbek-seen.uz/api/v2"
        payload = {"key": SMM_API_KEY, "action": "services"}
        res = requests.post(url, data=payload).json()
        text = "SMM xizmatlar:\n\n"
        for s in res:
            text += f"{s['service']} - {s['name']} ({s['rate']} UZS)\n"
        bot.send_message(call.message.chat.id, text)

    elif call.data == "add_channel":
        bot.send_message(call.message.chat.id, "Kanal username (@username) ni yuboring:")
        bot.register_next_step_handler(call.message, add_channel)

    elif call.data == "remove_channel":
        bot.send_message(call.message.chat.id, "O'chirmoqchi bo'lgan kanalni yuboring (@username):")
        bot.register_next_step_handler(call.message, remove_channel)

    elif call.data == "add_group":
        bot.send_message(call.message.chat.id, "Guruh username (@username) ni yuboring:")
        bot.register_next_step_handler(call.message, add_group)

    elif call.data == "remove_group":
        bot.send_message(call.message.chat.id, "O'chirmoqchi bo'lgan guruhni yuboring (@username):")
        bot.register_next_step_handler(call.message, remove_group)

# ================= Admin funksiyalar =================
def add_channel(message):
    username = message.text.strip()
    if username not in channels:
        channels.append(username)
        bot.send_message(message.chat.id, f"Kanal qo‘shildi: {username}")
    else:
        bot.send_message(message.chat.id, f"Kanal allaqachon mavjud: {username}")

def remove_channel(message):
    username = message.text.strip()
    if username in channels:
        channels.remove(username)
        bot.send_message(message.chat.id, f"Kanal o‘chirildi: {username}")
    else:
        bot.send_message(message.chat.id, f"Kanal topilmadi: {username}")

def add_group(message):
    username = message.text.strip()
    if username not in groups:
        groups.append(username)
        bot.send_message(message.chat.id, f"Guruh qo‘shildi: {username}")
    else:
        bot.send_message(message.chat.id, f"Guruh allaqachon mavjud: {username}")

def remove_group(message):
    username = message.text.strip()
    if username in groups:
        groups.remove(username)
        bot.send_message(message.chat.id, f"Guruh o‘chirildi: {username}")
    else:
        bot.send_message(message.chat.id, f"Guruh topilmadi: {username}")

# ================= Flask webhook =================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_json()
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return {"ok": True}

@app.route("/")
def index():
    return "SMM bot ishlayapti ✅", 200

# ================= Run Flask =================
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://YOUR_RENDER_URL/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=PORT)
