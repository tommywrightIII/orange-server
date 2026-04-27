import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get('BOT_TOKEN', 'ВАШ_ТОКЕН')
MINI_APP_URL = "https://tommywrightiii.github.io/Orange-Market/index.html"
ADMIN_ID = int(os.environ.get('ADMIN_ID', '123456789'))
CHANNEL = "@orangeshopz"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Буфер для сбора фото из альбома
photo_buffer = {}
photo_timers = {}


async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status not in ['left', 'kicked', 'banned']
    except:
        return False


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться на канал", url="https://t.me/orangeshopz")],
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
        " 👋 Wuzzzuuuppp! Welcome to Orange Market, тут продаются шмотки по адекватным ценам.\n\nЖми кнопку ниже чтобы посмотреть каталог 👇",
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
    await message.answer(
        "Админ-панель 👇\n\n📸 Чтобы получить ссылки на фото — отправь одно или несколько фото",
        reply_markup=kb
    )


async def send_photo_links(chat_id: int, photos: list):
    lines = ["📸 Ссылки на фото:\n"]
    for i, url in enumerate(photos, 1):
        lines.append(f"<b>Фото {i}:</b>\n<code>{url}</code>\n")
    await bot.send_message(chat_id, "\n".join(lines), parse_mode="HTML")


@dp.message(F.photo)
async def handle_photo(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"

    media_group_id = message.media_group_id
    chat_id = message.chat.id

    if media_group_id:
        # Альбом — собираем все фото
        if media_group_id not in photo_buffer:
            photo_buffer[media_group_id] = []

        photo_buffer[media_group_id].append(file_url)

        # Отменяем предыдущий таймер если есть
        if media_group_id in photo_timers:
            photo_timers[media_group_id].cancel()

        # Ставим таймер на отправку через 1.5 сек
        async def delayed_send():
            await asyncio.sleep(1.5)
            urls = photo_buffer.pop(media_group_id, [])
            photo_timers.pop(media_group_id, None)
            if urls:
                await send_photo_links(chat_id, urls)

        task = asyncio.create_task(delayed_send())
        photo_timers[media_group_id] = task
    else:
        # Одиночное фото
        await send_photo_links(chat_id, [file_url])


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
