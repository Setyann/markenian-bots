from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_language_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="English 🇺🇸", callback_data="lang_en")],
            [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton(text="Հայերեն 🇦🇲", callback_data="lang_hy")]
        ]
    )
    return keyboard

def get_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📜 Issue Tax Penalty"), KeyboardButton(text="📄 View All Taxpayers")],
            [KeyboardButton(text="📋 View All Penalties"), KeyboardButton(text="🔄 Restart Bot")],
        ],
        resize_keyboard=True
    )
    return keyboard

def get_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Go to Main Menu")],
        ],
        resize_keyboard=True
    )
    return keyboard

def get_user_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Pay Tax Penalties"), KeyboardButton(text="📋 View My Penalties")],
        ],
        resize_keyboard=True
    )
    return keyboard

def get_user_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Add User"), KeyboardButton(text="➖ Remove User")],
            [KeyboardButton(text="🏠 Go to Main Menu")],
        ],
        resize_keyboard=True
    )
    return keyboard