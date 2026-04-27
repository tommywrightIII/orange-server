import asyncio
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get('BOT_TOKEN', 'ВАШ_ТОКЕН')
MINI_APP_URL = "https://tommywrightiii.github.io/Orange-Market/index.html"
ADMIN_ID = int(os.environ.get('ADMIN_ID', '123456789'))
CHANNEL = "@orangeshopz"
DATABASE_URL = os.environ.get('DATABASE_URL')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

photo_buffer = {}
photo_timers = {}


def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()


def save_user(user: types.User):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (id, username, first_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        ''', (user.id, user.username, user.first_name))
        conn.commit()
        cur.close()
        conn.close()
    except:
        pass


def get_all_users():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id FROM users')
        users = [row['id'] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return users
    except:
        return []


init_db()


async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status not in ['left', 'kicked', 'banned']
    except:
        return False


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user)

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
    save_user(callback.from_user)

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
    users = get_all_users()
    await message.answer(
        f"Админ-панель 👇\n\n📸 Отправь фото — получишь ссылку\n📢 /broadcast текст — рассылка всем пользователям\n👥 Пользователей в базе: {len(users)}",
        reply_markup=kb
    )


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа.")
        return

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("❌ Напиши текст после команды.\n\nПример:\n/broadcast Новый товар в каталоге! 🔥")
        return

    users = get_all_users()
    if not users:
        await message.answer("❌ Нет пользователей в базе.")
        return

    await message.answer(f"📢 Начинаю рассылку {len(users)} пользователям...")

    sent = 0
    failed = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1

    await message.answer(f"✅ Рассылка завершена!\n✉️ Отправлено: {sent}\n❌ Не доставлено: {failed}")


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
        if media_group_id not in photo_buffer:
            photo_buffer[media_group_id] = []
        photo_buffer[media_group_id].append(file_url)

        if media_group_id in photo_timers:
            photo_timers[media_group_id].cancel()

        async def delayed_send():
            await asyncio.sleep(1.5)
            urls = photo_buffer.pop(media_group_id, [])
            photo_timers.pop(media_group_id, None)
            if urls:
                await send_photo_links(chat_id, urls)

        task = asyncio.create_task(delayed_send())
        photo_timers[media_group_id] = task
    else:
        await send_photo_links(chat_id, [file_url])


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
