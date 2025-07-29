import asyncio
import threading
from flask import Flask, render_template_string, render_template, abort
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

API_TOKEN = '7750224184:AAGyfpkoXwmW1PDps-grZ0E5LU3ImP3Mbi4'

# --- SQLAlchemy setup ---
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    userid = Column(Integer, primary_key=True)
    username = Column(String)
    credit = Column(Integer)

engine = create_engine('sqlite:///tgbot.db', echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

# --- Aiogram setup ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Игры", callback_data="games")],
    [InlineKeyboardButton(text="Приложения", callback_data="apps")],
    [InlineKeyboardButton(text="Новости", callback_data="news")],
    [InlineKeyboardButton(text="Личный кабинет", callback_data="profile")],
])

back_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Назад в Меню", callback_data="menu")]
])

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    def db_check_and_add():
        with SessionLocal() as session:
            user = session.get(User, user_id)
            if not user:
                user = User(userid=user_id, username=username, credit=100)
                session.add(user)
                session.commit()

    await asyncio.get_event_loop().run_in_executor(None, db_check_and_add)

    await message.answer(
        "Привет! Я твой ИИ агент. Нажми кнопку ниже, чтобы открыть меню.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def process_menu(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text(
        "Вы открыли меню. Выберите пункт:",
        reply_markup=menu_kb
    )

@dp.callback_query(lambda c: c.data == "games")
async def on_games(callback_query: types.CallbackQuery):
    await callback_query.answer("Вы выбрали 'Игры'")
    await callback_query.message.edit_text(
        "Раздел 'Игры' — здесь будет контент.",
        reply_markup=back_kb
    )

@dp.callback_query(lambda c: c.data == "apps")
async def on_apps(callback_query: types.CallbackQuery):
    await callback_query.answer("Вы выбрали 'Приложения'")
    await callback_query.message.edit_text(
        "Раздел 'Приложения' — здесь будет контент.",
        reply_markup=back_kb
    )

@dp.callback_query(lambda c: c.data == "news")
async def on_news(callback_query: types.CallbackQuery):
    await callback_query.answer("Вы выбрали 'Новости'")
    await callback_query.message.edit_text(
        "Раздел 'Новости' — здесь будет контент.",
        reply_markup=back_kb
    )

@dp.callback_query(lambda c: c.data == "profile")
async def on_profile(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    def db_get_user():
        with SessionLocal() as session:
            return session.get(User, user_id)

    user = await asyncio.get_event_loop().run_in_executor(None, db_get_user)

    if user:
        text = f"Личный кабинет:\nID: {user.userid}\nБаланс: {user.credit}₽"
    else:
        text = "Пользователь не найден в базе данных."

    await callback_query.answer("Вы выбрали 'Личный кабинет'")
    await callback_query.message.edit_text(
        text,
        reply_markup=back_kb
    )

async def start_bot():
    await dp.start_polling(bot)

# --- Flask setup ---
app = Flask(__name__)

# Простой HTML шаблон для отображения пользователя
html_template = """
<!doctype html>
<title>Профиль пользователя</title>
<h2>Профиль пользователя</h2>
{% if user %}
    <p><b>ID Telegram:</b> {{ user.userid }}</p>
    <p><b>Username:</b> {{ user.username }}</p>
    <p><b>Баланс:</b> {{ user.credit }} ₽</p>
{% else %}
    <p>Пользователь не найден</p>
{% endif %}
"""

@app.route("/user/<int:userid>")
def user_profile(userid):
    with SessionLocal() as session:
        user = session.get(User, userid)
        if not user:
            abort(404)
        return render_template_string(html_template, user=user)

@app.route("/flappy")
def flappy():
    return render_template("flappy.html")

def run_flask():
    # Flask запускается в отдельном потоке
    app.run(host="0.0.0.0", port=5000, debug=False)  # debug=True по желанию

if __name__ == '__main__':
    # Запускаем Flask в потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Запускаем бота aiogram в asyncio loop
    asyncio.run(start_bot())
                   
