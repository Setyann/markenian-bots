from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_language_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="English 🇺🇸", callback_data="lang_en")],
            [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton(text="Հայերեն 🇦🇲", callback_data="lang_hy")]
        ]
    )
    return keyboard

def get_conversion_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇸 USD", callback_data="convert_usd_mkm"), InlineKeyboardButton(text="🇯🇵 JPY", callback_data="convert_jpy_mkm")],
            [InlineKeyboardButton(text="🇬🇧 GBP", callback_data="convert_gbp_mkm"), InlineKeyboardButton(text="🇪🇺 EUR", callback_data="convert_eur_mkm")],
            [InlineKeyboardButton(text="🇷🇺 RUB", callback_data="convert_rub_mkm"), InlineKeyboardButton(text="🇨🇳 CNY", callback_data="convert_cny_mkm")],
            [InlineKeyboardButton(text="🇦🇺 AUD", callback_data="convert_aud_mkm"), InlineKeyboardButton(text="🇨🇦 CAD", callback_data="convert_cad_mkm")],
            [InlineKeyboardButton(text="🇮🇳 INR", callback_data="convert_inr_mkm")]
        ]
    )
    return keyboard