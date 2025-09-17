import os
import telebot
from flask import Flask, request
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
API_KEY = os.getenv("API_KEY")
WEBHOOK_URL = f"https://smm-4.onrender.com/{BOT_TOKEN}"  # Render URL bilan almashtiring

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Kanal va guruhlar ro'yxati ---
channels = {}  # {channel_id: {"name": "Kanal nomi"}}
groups = {}    # {group_id: {"name": "Guruh nomi"}}

# --- Flask route webhook ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# --- Start va admin menu ---
@bot.message_handler(commands=["start"])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Admin panelga xush kelibsiz!\n"
                                          "/add_channel - Kanal qo'shish\n"
                                          "/del_channel - Kanal o'chirish\n"
                                          "/add_group - Guruh qo'shish\n"
                                          "/del_group - Guruh o'chirish\n"
                                          "/services - Xizmatlarni ko'rish\n"
                                          "/order - Buyurtma qo'shish")
    else:
        bot.send_message(message.chat.id, "Salom! Xizmatdan foydalanish uchun kanal va guruhlarga obuna bo'ling.")

# --- Kanal qo'shish ---
@bot.message_handler(commands=["add_channel"])
def add_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "Kanal ID yoki username kiriting:")
    bot.register_next_step_handler(msg, save_channel)

def save_channel(message):
    channel_id = message.text
    channels[channel_id] = {"name": channel_id}
    bot.send_message(message.chat.id, f"Kanal qo'shildi: {channel_id}")

# --- Kanal o'chirish ---
@bot.message_handler(commands=["del_channel"])
def del_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "O'chirish uchun kanal ID yoki username kiriting:")
    bot.register_next_step_handler(msg, remove_channel)

def remove_channel(message):
    channel_id = message.text
    if channel_id in channels:
        channels.pop(channel_id)
        bot.send_message(message.chat.id, f"Kanal o'chirildi: {channel_id}")
    else:
        bot.send_message(message.chat.id, "Kanal topilmadi!")

# --- Guruh qo'shish ---
@bot.message_handler(commands=["add_group"])
def add_group(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "Guruh ID yoki username kiriting:")
    bot.register_next_step_handler(msg, save_group)

def save_group(message):
    group_id = message.text
    groups[group_id] = {"name": group_id}
    bot.send_message(message.chat.id, f"Guruh qo'shildi: {group_id}")

# --- Guruh o'chirish ---
@bot.message_handler(commands=["del_group"])
def del_group(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "O'chirish uchun guruh ID yoki username kiriting:")
    bot.register_next_step_handler(msg, remove_group)

def remove_group(message):
    group_id = message.text
    if group_id in groups:
        groups.pop(group_id)
        bot.send_message(message.chat.id, f"Guruh o'chirildi: {group_id}")
    else:
        bot.send_message(message.chat.id, "Guruh topilmadi!")

# --- Xizmatlarni ko'rish ---
@bot.message_handler(commands=["services"])
def services(message):
    url = "https://uzbek-seen.uz/api/v2"
    params = {"key": API_KEY, "action": "services"}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        text = ""
        for s in data:
            text += f"{s['service']}. {s['name']} ({s['min']}-{s['max']}) - {s['rate']} UZS\n"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "Xizmatlarni olishda xato!")

# --- Buyurtma qo'shish ---
@bot.message_handler(commands=["order"])
def add_order(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "Buyurtma: service_id link quantity (misol: 1 https://t.me/username 100)")
    bot.register_next_step_handler(msg, create_order)

def create_order(message):
    try:
        service, link, quantity = message.text.split()
        url = "https://uzbek-seen.uz/api/v2"
        params = {
            "key": API_KEY,
            "action": "add",
            "service": service,
            "link": link,
            "quantity": quantity
        }
        r = requests.post(url, data=params)
        if r.status_code == 200:
            bot.send_message(message.chat.id, f"Buyurtma qo'shildi: {r.json().get('order')}")
        else:
            bot.send_message(message.chat.id, "Buyurtma qo'shishda xato!")
    except:
        bot.send_message(message.chat.id, "Format xato! Misol: 1 https://t.me/username 100")

# --- Bot Flask serverini ishga tushurish ---
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
