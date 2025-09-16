import json
import aiohttp
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv
import os

# ENV yuklash
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

CHANNELS_FILE = "channels.json"
API_URL = "https://uzbek-seen.uz/api/v2"

# 📌 Kanal ro'yxatini yuklash
def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        return []
    with open(CHANNELS_FILE, "r") as f:
        return json.load(f)

# 📌 Kanal ro'yxatini saqlash
def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f, indent=4)

# 📌 Foydalanuvchi obuna bo'lganini tekshirish
async def check_subscription(user_id):
    channels = load_channels()
    not_subscribed = []
    for channel in channels:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_subscribed.append(channel)
        except TelegramBadRequest:
            continue
    return not_subscribed

# 📌 Start komandasi
@dp.message(Command("start"))
async def start_handler(message: Message):
    not_subscribed = await check_subscription(message.from_user.id)
    if not_subscribed:
        kb = InlineKeyboardBuilder()
        for ch in not_subscribed:
            kb.button(text=f"👉 {ch}", url=f"https://t.me/{ch[1:]}")
        kb.button(text="✅ Obuna bo‘ldim", callback_data="check_subs")
        await message.answer(
            "❗ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:",
            reply_markup=kb.as_markup()
        )
    else:
        await message.answer("👋 Xush kelibsiz! /services buyrug‘i orqali xizmatlarni ko‘rishingiz mumkin.")

# 📌 Obuna tekshirish tugmasi
@dp.callback_query(F.data == "check_subs")
async def check_subs_callback(call: CallbackQuery):
    not_subscribed = await check_subscription(call.from_user.id)
    if not_subscribed:
        kb = InlineKeyboardBuilder()
        for ch in not_subscribed:
            kb.button(text=f"👉 {ch}", url=f"https://t.me/{ch[1:]}")
        kb.button(text="✅ Obuna bo‘ldim", callback_data="check_subs")
        await call.message.edit_text(
            "❗ Hali hammasiga obuna bo‘lmadingiz!",
            reply_markup=kb.as_markup()
        )
    else:
        await call.message.edit_text("✅ Obuna tasdiqlandi! Endi xizmatlardan foydalanishingiz mumkin.")

# 📌 Xizmatlar ro'yxati
@dp.message(Command("services"))
async def services_handler(message: Message):
    not_subscribed = await check_subscription(message.from_user.id)
    if not_subscribed:
        await start_handler(message)
        return

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, data={"key": API_KEY, "action": "services"}) as resp:
            data = await resp.json()

    text = "📋 <b>Xizmatlar ro‘yxati:</b>\n\n"
    for srv in data[:10]:  # faqat 10 ta xizmat ko‘rsatamiz
        text += f"🔹 ID: <b>{srv['service']}</b>\n📌 Nomi: {srv['name']}\n💰 Narx: {srv['rate']} UZS\n➖➕ {srv['min']} - {srv['max']}\n\n"

    await message.answer(text)

# 📌 Admin kanal qo‘shishi
@dp.message(Command("add_channel"))
async def add_channel_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❗ Foydalanish: /add_channel @kanal")
        return
    channel = args[1]
    channels = load_channels()
    if channel not in channels:
        channels.append(channel)
        save_channels(channels)
        await message.answer(f"✅ Kanal qo‘shildi: {channel}")
    else:
        await message.answer("❗ Bu kanal allaqachon ro‘yxatda bor.")

# 📌 Admin kanal o‘chirish
@dp.message(Command("del_channel"))
async def del_channel_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❗ Foydalanish: /del_channel @kanal")
        return
    channel = args[1]
    channels = load_channels()
    if channel in channels:
        channels.remove(channel)
        save_channels(channels)
        await message.answer(f"🗑 Kanal o‘chirildi: {channel}")
    else:
        await message.answer("❗ Bu kanal topilmadi.")

# 📌 Admin kanallarni ko‘rishi
@dp.message(Command("channels"))
async def list_channels(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    channels = load_channels()
    if not channels:
        await message.answer("📂 Hech qanday kanal qo‘shilmagan.")
    else:
        text = "📌 Majburiy kanallar:\n" + "\n".join([f"👉 {ch}" for ch in channels])
        await message.answer(text)

# Run
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
