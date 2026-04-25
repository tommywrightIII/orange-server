import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ChatMemberStatus

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get('BOT_TOKEN', 'ВАШ_ТОКЕН')
MINI_APP_URL = "https://tommywrightiii.github.io/Orange-Market/index.html"
ADMIN_ID = int(os.environ.get('ADMIN_ID', '123456789'))
CHANNEL = "@orangeshopz"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED, ChatMemberStatus.BANNED]
    except:
        return False


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/orangeshopz")],
            [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")]
        ])
        await message.answer(
            "👋 Привет!\n\nЧтобы пользоваться магазином, подпишись на наш канал 👇",
            reply_markup=kb
        )
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🛍 Открыть каталог",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]])
    await message.answer(
        "👋 Привет! Добро пожаловать в Orange Market.\n\nЖми кнопку ниже чтобы посмотреть каталог 👇",
        reply_markup=kb
    )


@dp.callback_query(lambda c: c.data == "check_sub")
async def check_sub(callback: types.CallbackQuery):
    if not await is_subscribed(callback.from_user.id):
        await callback.answer("❌ Ты ещё не подписался на канал!", show_alert=True)
        return

    await callback.message.delete()
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🛍 Открыть каталог",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]])
    await callback.message.answer(
        "✅ Отлично! Добро пожаловать в Orange Market.\n\nЖми кнопку ниже чтобы посмотреть каталог 👇",
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
