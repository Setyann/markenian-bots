from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

LANGS = ("en", "ru", "hy")

LABELS = {
    "main_menu": {
        "en": "🏠 Main Menu",
        "ru": "🏠 Главное меню",
        "hy": "🏠 Main Menu",
    },
    "accounts": {
        "en": "🏦 Accounts",
        "ru": "🏦 Счета",
        "hy": "🏦 Accounts",
    },
    "history": {
        "en": "📜 History",
        "ru": "📜 История",
        "hy": "📜 History",
    },
    "transfer": {
        "en": "🔁 Transfer",
        "ru": "🔁 Перевод",
        "hy": "🔁 Transfer",
    },
    "payments": {
        "en": "🧾 Payments",
        "ru": "🧾 Платежи",
        "hy": "🧾 Payments",
    },
    "card": {
        "en": "💳 Card",
        "ru": "💳 Карта",
        "hy": "💳 Card",
    },
    "loans": {
        "en": "💼 Loans",
        "ru": "💼 Кредиты",
        "hy": "💼 Loans",
    },
    "support": {
        "en": "💬 Support",
        "ru": "💬 Поддержка",
        "hy": "💬 Support",
    },
    "set_pin": {
        "en": "🔐 Set PIN",
        "ru": "🔐 Установить PIN",
        "hy": "🔐 Set PIN",
    },
    "users": {
        "en": "👥 Users",
        "ru": "👥 Пользователи",
        "hy": "👥 Users",
    },
    "adjust": {
        "en": "💰 Adjust Balance",
        "ru": "💰 Начисления/списания",
        "hy": "💰 Adjust Balance",
    },
    "cards_admin": {
        "en": "💳 Cards",
        "ru": "💳 Карты",
        "hy": "💳 Cards",
    },
    "limits": {
        "en": "🧭 Limits",
        "ru": "🧭 Лимиты",
        "hy": "🧭 Limits",
    },
    "reports": {
        "en": "📊 Reports",
        "ru": "📊 Отчеты",
        "hy": "📊 Reports",
    },
    "logs": {
        "en": "📜 Logs",
        "ru": "📜 Логи",
        "hy": "📜 Logs",
    },
    "tickets": {
        "en": "💬 Tickets",
        "ru": "💬 Обращения",
        "hy": "💬 Tickets",
    },
    "profile": {
        "en": "👤 Profile Lookup",
        "ru": "👤 Поиск профиля",
        "hy": "👤 Profile Lookup",
    },
    "freeze": {
        "en": "🚫 Freeze Accounts",
        "ru": "🚫 Заморозка счетов",
        "hy": "🚫 Freeze Accounts",
    },
    "credit_decisions": {
        "en": "✅/❌ Credit Decisions",
        "ru": "✅/❌ Решения по кредитам",
        "hy": "✅/❌ Credit Decisions",
    },
    "confirm": {
        "en": "✅ Confirm",
        "ru": "✅ Подтвердить",
        "hy": "✅ Confirm",
    },
    "cancel": {
        "en": "❌ Cancel",
        "ru": "❌ Отмена",
        "hy": "❌ Cancel",
    },
    "issue_card": {
        "en": "💳 Issue Card",
        "ru": "💳 Выпустить карту",
        "hy": "💳 Issue Card",
    },
    "block_card": {
        "en": "🚫 Block Card",
        "ru": "🚫 Заблокировать карту",
        "hy": "🚫 Block Card",
    },
    "unblock_card": {
        "en": "✅ Unblock Card",
        "ru": "✅ Разблокировать карту",
        "hy": "✅ Unblock Card",
    },
}

ROLE_MENU = {
    "client": [
        ["accounts", "history"],
        ["transfer", "payments"],
        ["card", "loans"],
        ["support", "set_pin"],
    ],
    "admin": [
        ["users", "adjust"],
        ["cards_admin", "limits"],
        ["reports", "logs"],
        ["accounts", "history"],
        ["transfer", "payments"],
        ["card", "loans"],
        ["set_pin"],
    ],
    "operator": [
        ["tickets", "profile"],
        ["history"],
    ],
    "risk": [
        ["freeze", "credit_decisions"],
        ["limits", "logs"],
    ],
}


def _label(key: str, lang: str) -> str:
    if lang not in LANGS:
        lang = "en"
    return LABELS.get(key, {}).get(lang, LABELS.get(key, {}).get("en", key))


def get_language_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="English 🇺🇸", callback_data="lang_en")],
            [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton(text="Հայերեն 🇦🇲", callback_data="lang_hy")],
        ]
    )


def get_main_menu_keyboard(role: str, lang: str = "en"):
    layout = ROLE_MENU.get(role, ROLE_MENU["client"])
    keyboard = []
    for row in layout:
        keyboard.append([KeyboardButton(text=_label(btn, lang)) for btn in row])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_back_keyboard(lang: str = "en"):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=_label("main_menu", lang))]],
        resize_keyboard=True,
    )


def inline_keyboard(actions: list[tuple[str, str]], row_size: int = 2):
    rows = []
    row = []
    for text, data in actions:
        row.append(InlineKeyboardButton(text=text, callback_data=data))
        if len(row) == row_size:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_confirm_keyboard(confirm_data: str, cancel_data: str, lang: str = "en"):
    return inline_keyboard(
        [
            (_label("confirm", lang), confirm_data),
            (_label("cancel", lang), cancel_data),
        ],
        row_size=2,
    )


def get_card_action_keyboard(has_card: bool, is_blocked: bool, lang: str = "en"):
    actions = []
    if not has_card:
        actions.append((_label("issue_card", lang), "card:issue"))
    else:
        if is_blocked:
            actions.append((_label("unblock_card", lang), "card:unblock"))
        else:
            actions.append((_label("block_card", lang), "card:block"))
    return inline_keyboard(actions, row_size=1)
