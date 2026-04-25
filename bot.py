import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

logging.basicConfig(level=logging.INFO)

# ==============================
# НАСТРОЙ ЭТИ ЗНАЧЕНИЯ:
BOT_TOKEN = "8778887103:AAGxnPbwjpwzCPk2nhaC6eN26BLiTJ33zX8"         # токен от @BotFather
MINI_APP_URL = "https://tommywrightiii.github.io/Orange-Market/index.html"  # URL где хостится Mini App
ADMIN_ID = 943609196                    # твой Telegram user_id
# ==============================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🛍 Открыть каталог",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]])
    await message.answer(
        "👋 Привет! Здесь продаются крутые б/у вещи по адекватным ценам.\n\n"
        "Жми кнопку ниже чтобы посмотреть каталог 👇",
        reply_markup=kb
    )


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа.")
        return

    admin_url = MINI_APP_URL + "?admin=1"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="⚙️ Открыть админ-панель",
            web_app=WebAppInfo(url=admin_url)
        )
    ]])
    await message.answer("Админ-панель 👇", reply_markup=kb)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
