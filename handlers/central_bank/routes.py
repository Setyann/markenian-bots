import os
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv

from handlers.central_bank.db import (
    get_latest_mrk_usd_rate,
    get_mrk_usd_rate_for_today,
    set_mrk_usd_rate,
)
from handlers.central_bank.keyboards import get_language_keyboard, get_conversion_keyboard
from handlers.central_bank.rates_provider import RatesProviderError, get_usd_rates

router = Router()

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID") or "0")

user_languages = {}
pending_conversion = {}
TEXTS = {
    "start": {
        "en": "👋 Hello, {name}! I'm Central Bank of Markenia 🏦.\nUse /help to see available commands.",
        "ru": "👋 Здравствуйте, {name}! Я Центральный банк Маркении 🏦.\nИспользуйте /help, чтобы увидеть доступные команды.",
        "hy": "👋 Բարև, {name}! Ես Մարկենիայի Կենտրոնական բանկն եմ 🏦.\nՕգտագործեք /help՝ հասանելի հրամանները տեսնելու համար."
    },
    "help": {
        "en": "Commands available:\n/start - Restart the bot\n/help - Show this help message\n/rates - Get current exchange rates\n/convert - Convert currency\n/lang - Change language",
        "ru": "Доступные команды:\n/start - Перезапустить бота\n/help - Показать это сообщение помощи\n/rates - Получить текущие курсы валют\n/convert - Конвертировать валюту\n/lang - Изменить язык",
        "hy": "Հասանելի հրամաններ:\n/start - Վերագործարկել բոտը\n/help - Ցույց տալ այս օգնության տեքստը\n/rates - Ստանալ ընթացիկ փոխարժեքի գները\n/convert - Փոխարկել արժույթը\n/lang - Փոխել լեզուն",
    },
    "lang_select": {
        "en": "Select your preferred language:",
        "ru": "Выберите язык:",
        "hy": "Ընտրեք լեզուն:",
    },
    "lang_changed": {
        "en": "Language has been changed.",
        "ru": "Язык изменён.",
        "hy": "Լեզուն փոխված է։",
    },
    "conversion_error": {
        "en": "Please enter a valid numeric amount.",
        "ru": "Пожалуйста, введите корректное числовое значение.",
        "hy": "Խնդրում ենք մուտքագրել ճիշտ թվային արժեք։"
    },
    "unknown_command": {
        "en": "Unrecognized command. Use /help to see available commands.",
        "ru": "Неизвестная команда. Используйте /help, чтобы увидеть доступные команды.",
        "hy": "Չճանաչված հրաման։ Օգտագործեք /help՝ հասանելի հրամանները տեսնելու համար։"
    },
    "rates_header": {
        "en": "Current exchange rates:\n\n",
        "ru": "Текущие курсы валют:\n\n",
        "hy": "Ընթացիկ փոխարժեքի գները՝\n\n"
    },
    "rates_footer": {
        "en": "\n_Data provided by the Central Bank of Markenia. You can also enter an amount in MRK to 💱convert it to all available currencies, and vice versa. But this feature is under development._",
        "ru": "\n_Данные предоставлены Центральным банком Маркении. Вы также можете ввести сумму в MRK для 💱конвертации во все доступные валюты и наоборот. Но эта функция находится в разработке._",
        "hy": "\n_Տվյալները տրամադրված են Մարկենիայի Կենտրոնական բանկի կողմից։ Դուք նույնպես կարող եք մուտքագրել գումար MRK-ում՝ այն 💱փոխարկելու բոլոր հասանելի արժույթների և հակառակը։ Բայց այս ֆունկցիան մշակման փուլում է._"
    },
    "conversion_prompt": {
        "en": "Select the currency to convert to. You can see rates in /rates:",
        "ru": "Выберите валюту для конвертации. Вы можете увидеть курсы в /rates:",
        "hy": "Ընտրեք արժույթը փոխարկելու համար: /rates-ում կարող եք տեսնել փոխարժեքները:"
    },
    "conversion_result": {
        "en": "💱 {amount} MRK is approximately:\n\n{results}",
        "ru": "💱 {amount} MRK примерно равно:\n\n{results}",
        "hy": "💱 {amount} MRK-ը մոտավորապես հավասար է՝\n\n{results}"
    },
    "rates_base": {
        "en": "Base rate: 1 MRK = {mrk_usd_rate} USD (date {date}).\n\n",
        "ru": "Базовый курс: 1 MRK = {mrk_usd_rate} USD (дата {date}).\n\n",
        "hy": "Base rate: 1 MRK = {mrk_usd_rate} USD (date {date}).\n\n"
    },
    "enter_amount": {
        "en": "Enter amount in MRK:",
        "ru": "Введите сумму в MRK:",
        "hy": "Enter amount in MRK:"
    },
    "admin_only": {
        "en": "This command is available only for the admin.",
        "ru": "Эта команда доступна только администратору.",
        "hy": "This command is available only for the admin."
    },
    "setrate_usage": {
        "en": "Usage: /setrate <MRK_to_USD_rate>. Example: /setrate 0.25",
        "ru": "Использование: /setrate <курс MRK к USD>. Пример: /setrate 0.25",
        "hy": "Usage: /setrate <MRK_to_USD_rate>. Example: /setrate 0.25"
    },
    "rate_set": {
        "en": "Rate saved: 1 MRK = {rate} USD for {date}.",
        "ru": "Курс сохранён: 1 MRK = {rate} USD на дату {date}.",
        "hy": "Rate saved: 1 MRK = {rate} USD for {date}."
    },
    "rate_missing": {
        "en": "Today's MRK/USD rate is not set. Please ask the admin to set it with /setrate.",
        "ru": "Курс MRK/USD на сегодня не установлен. Попросите администратора установить его командой /setrate.",
        "hy": "Today's MRK/USD rate is not set. Please ask the admin to set it with /setrate."
    },
    "rate_missing_last": {
        "en": "\nLast known rate: {rate} (date {date}).",
        "ru": "\nПоследний установленный курс: {rate} (дата {date}).",
        "hy": "\nLast known rate: {rate} (date {date})."
    },
    "help_admin": {
        "en": "\n\nAdmin:\n/setrate - Set today's MRK/USD rate",
        "ru": "\n\nАдмин:\n/setrate - Установить курс MRK/USD на сегодня",
        "hy": "\n\nAdmin:\n/setrate - Set today's MRK/USD rate"
    },
    "processing": {
        "en": "Processing data, please wait...",
        "ru": "Идёт обработка данных, просьба ожидать...",
        "hy": "Processing data, please wait..."
    },
    "rates_api_missing": {
        "en": "Exchange-rate API key is not configured. Ask the admin to set it.",
        "ru": "API-ключ для курсов валют не задан. Попросите администратора настроить его.",
        "hy": "Exchange-rate API key is not configured. Ask the admin to set it."
    },
    "rates_unavailable": {
        "en": "Failed to fetch USD rates. Please try again later.",
        "ru": "Не удалось получить курсы USD. Попробуйте позже.",
        "hy": "Failed to fetch USD rates. Please try again later."
    }
}


# Курсы USD -> валюта (fallback)
USD_RATES_FALLBACK = {
    "USD": 1.0,
    "JPY": 384.682948246,
    "GBP": 2.05132488545,
    "EUR": 2.34158924747,
    "RUB": 200.057356449,
    "CNY": 17.8562452642,
    "AUD": 3.85025203547,
    "CAD": 3.46047384593,
    "INR": 212.628462934,
}

SUPPORTED_CURRENCIES = list(USD_RATES_FALLBACK.keys())

# Флаги
currency_flags = {
    "USD": "🇺🇸",
    "JPY": "🇯🇵",
    "GBP": "🇬🇧",
    "EUR": "🇪🇺",
    "RUB": "🇷🇺",
    "CNY": "🇨🇳",
    "AUD": "🇦🇺",
    "CAD": "🇨🇦",
    "INR": "🇮🇳"
}


@router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = lang

    await callback.answer()
    await callback.message.edit_text(
        TEXTS["lang_changed"][lang]
    )
    
def detect_lang(message: Message) -> str:
    # 1. если пользователь уже выбирал язык вручную
    if message.from_user.id in user_languages:
        return user_languages[message.from_user.id]

    # 2. язык Telegram
    tg_lang = message.from_user.language_code
    if tg_lang:
        tg_lang = tg_lang.split("-")[0]
        if tg_lang in ("en", "ru", "hy"):
            return tg_lang

    # 3. fallback
    return "en"


def _today_str() -> str:
    return datetime.now().date().isoformat()
    

@router.message(Command("start"))
async def start(message: Message):
    lang = detect_lang(message)
    user_languages.setdefault(message.from_user.id, lang)
    await message.answer(
        TEXTS["start"][lang].format(name=message.from_user.full_name)
    )
    
@router.message(Command("help"))
async def help(message: Message):
    lang = detect_lang(message)
    text = TEXTS["help"][lang]
    if ADMIN_ID and message.from_user.id == ADMIN_ID:
        text += TEXTS["help_admin"][lang]
    await message.answer(text)


@router.message(Command("setrate"))
async def setrate(message: Message):
    lang = detect_lang(message)
    if not ADMIN_ID or message.from_user.id != ADMIN_ID:
        await message.answer(TEXTS["admin_only"][lang])
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(TEXTS["setrate_usage"][lang])
        return
    raw = parts[1].strip().replace(",", ".")
    try:
        rate = float(raw)
    except ValueError:
        await message.answer(TEXTS["setrate_usage"][lang])
        return
    if rate <= 0:
        await message.answer(TEXTS["setrate_usage"][lang])
        return
    today = _today_str()
    await set_mrk_usd_rate(rate, today, message.from_user.id)
    await message.answer(
        TEXTS["rate_set"][lang].format(rate=rate, date=today)
    )
    
@router.message(Command("rates"))
async def rates(message: Message):
    lang = detect_lang(message)
    status = await message.answer(TEXTS["processing"][lang])

    today = _today_str()
    mrk_usd_rate = await get_mrk_usd_rate_for_today(today)
    if mrk_usd_rate is None:
        text = TEXTS["rate_missing"][lang]
        last_rate, last_date = await get_latest_mrk_usd_rate()
        if last_rate is not None and last_date:
            text += TEXTS["rate_missing_last"][lang].format(
                rate=last_rate,
                date=last_date
            )
        await status.edit_text(text)
        return

    try:
        usd_rates = await get_usd_rates(SUPPORTED_CURRENCIES)
    except RatesProviderError as exc:
        if exc.code == "missing_api_key":
            await status.edit_text(TEXTS["rates_api_missing"][lang])
        else:
            await status.edit_text(TEXTS["rates_unavailable"][lang])
        return

    # Build rates text
    rates_text = TEXTS["rates_header"][lang]
    rates_text += TEXTS["rates_base"][lang].format(
        mrk_usd_rate=mrk_usd_rate,
        date=today
    )
    for code in SUPPORTED_CURRENCIES:
        usd_rate = usd_rates.get(code)
        if usd_rate is None:
            continue
        flag = currency_flags.get(code, "")
        mrk_rate = mrk_usd_rate * usd_rate
        rates_text += f"{flag} 1 MRK = {mrk_rate} {code}\n"

    rates_text += TEXTS.get("rates_footer", {}).get(lang, "")

    await status.edit_text(rates_text, parse_mode="Markdown")

@router.message(Command("lang"))
async def lang(message: Message):
    lang = detect_lang(message)
    await message.answer(
        TEXTS["lang_select"][lang],
        reply_markup=get_language_keyboard()
    )

@router.message(F.text.regexp(r'^\d+(\.\d+)?$'))
async def amount_entered(message: Message):
    lang = detect_lang(message)
    amount = float(message.text)

    pending_conversion[message.from_user.id] = amount

    await message.answer(
        TEXTS["conversion_prompt"][lang],
        reply_markup=get_conversion_keyboard()
    )

@router.message(Command("convert"))
async def convert_command(message: Message):
    lang = detect_lang(message)
    user_id = message.from_user.id
    if user_id not in pending_conversion:
        await message.answer(TEXTS["enter_amount"][lang])
        return
    await message.answer(
        TEXTS["conversion_prompt"][lang],
        reply_markup=get_conversion_keyboard()
    )


@router.callback_query(F.data.startswith("convert_"))
async def convert_currency(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, "en")

    if user_id not in pending_conversion:
        await callback.answer(TEXTS["enter_amount"][lang], show_alert=True)
        return

    if not callback.message:
        await callback.answer(TEXTS["processing"][lang], show_alert=True)
        return

    await callback.message.edit_text(TEXTS["processing"][lang])
    await callback.answer()

    today = _today_str()
    mrk_usd_rate = await get_mrk_usd_rate_for_today(today)
    if mrk_usd_rate is None:
        text = TEXTS["rate_missing"][lang]
        last_rate, last_date = await get_latest_mrk_usd_rate()
        if last_rate is not None and last_date:
            text += TEXTS["rate_missing_last"][lang].format(
                rate=last_rate,
                date=last_date
            )
        await callback.message.edit_text(text)
        return

    try:
        usd_rates = await get_usd_rates(SUPPORTED_CURRENCIES)
    except RatesProviderError as exc:
        if exc.code == "missing_api_key":
            await callback.message.edit_text(TEXTS["rates_api_missing"][lang])
        else:
            await callback.message.edit_text(TEXTS["rates_unavailable"][lang])
        return

    amount = pending_conversion[user_id]

    # Determine currency from callback data
    parts = callback.data.split("_")
    currency = parts[1].upper()

    usd_rate = usd_rates.get(currency)
    if not usd_rate:
        await callback.message.edit_text("Unknown currency.")
        return

    result = amount * mrk_usd_rate * usd_rate
    flag = currency_flags.get(currency, "")

    await callback.message.edit_text(
        TEXTS["conversion_result"][lang].format(
            amount=amount,
            results=f"{flag} {currency}: {result:.2f}"
        )
    )

    pending_conversion.pop(user_id, None)

@router.message()
async def unknown_command(message: Message):
    lang = detect_lang(message)
    await message.answer(
        TEXTS["unknown_command"][lang]
    )
