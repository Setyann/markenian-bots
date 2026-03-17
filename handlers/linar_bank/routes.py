
import os
import random
import string
import hashlib
import asyncio
from io import BytesIO
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.linar_bank.keyboards import (
    get_language_keyboard,
    get_main_menu_keyboard,
    get_back_keyboard,
    inline_keyboard,
    get_confirm_keyboard,
    get_card_action_keyboard,
    LABELS,
    LANGS,
)
from handlers.linar_bank import db
from handlers import registry


load_dotenv()
router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID") or "0")

ROLE_CLIENT = "client"
ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_RISK = "risk"

USER_ACTIVE = "active"
USER_BLOCKED = "blocked"
USER_FROZEN = "frozen"

PIN_MAX_ATTEMPTS = 3
OTP_MAX_ATTEMPTS = 3
OTP_TTL_SEC = 300

FEE_INTERNAL = 0.0
FEE_EXTERNAL = 0.01
FEE_PAYMENT = 0.01

user_languages: dict[int, str] = {}

TEXTS = {
    "start": {
        "en": "Welcome to Linar Bank. Use the menu below.",
        "ru": "Добро пожаловать в Linar Bank. Используйте меню ниже.",
        "hy": "Welcome to Linar Bank. Use the menu below.",
    },
    "help": {
        "en": "Use the main menu. Financial operations require PIN + OTP.",
        "ru": "Используйте меню. Финансовые операции требуют PIN + OTP.",
        "hy": "Use the main menu. Financial operations require PIN + OTP.",
    },
    "lang_select": {
        "en": "Select language:",
        "ru": "Выберите язык:",
        "hy": "Select language:",
    },
    "lang_changed": {
        "en": "Language updated.",
        "ru": "Язык изменён.",
        "hy": "Language updated.",
    },
    "not_registered": {
        "en": "You are not registered in the bank system.",
        "ru": "Вы не зарегистрированы в системе банка.",
        "hy": "You are not registered in the bank system.",
    },
    "access_denied": {
        "en": "Access denied.",
        "ru": "Доступ запрещён.",
        "hy": "Access denied.",
    },
    "main_menu": {
        "en": "Main Menu",
        "ru": "Главное меню",
        "hy": "Main Menu",
    },
    "profile": {
        "en": "Profile: {name}\nRole: {role}\nStatus: {status}\nPhone: {phone}",
        "ru": "Профиль: {name}\nРоль: {role}\nСтатус: {status}\nТелефон: {phone}",
        "hy": "Profile: {name}\nRole: {role}\nStatus: {status}\nPhone: {phone}",
    },
    "accounts": {
        "en": "Your accounts:\n{list}",
        "ru": "Ваши счета:\n{list}",
        "hy": "Your accounts:\n{list}",
    },
    "no_accounts": {
        "en": "No active accounts.",
        "ru": "Нет активных счетов.",
        "hy": "No active accounts.",
    },
    "history": {
        "en": "Recent transactions:\n{list}",
        "ru": "Последние операции:\n{list}",
        "hy": "Recent transactions:\n{list}",
    },
    "no_history": {
        "en": "No transactions yet.",
        "ru": "Операций пока нет.",
        "hy": "No transactions yet.",
    },
    "transfer_type": {
        "en": "Select transfer type:",
        "ru": "Выберите тип перевода:",
        "hy": "Select transfer type:",
    },
    "choose_from": {
        "en": "Select source account:",
        "ru": "Выберите счет списания:",
        "hy": "Select source account:",
    },
    "choose_to": {
        "en": "Select destination account:",
        "ru": "Выберите счет зачисления:",
        "hy": "Select destination account:",
    },
    "enter_phone": {
        "en": "Enter phone number:",
        "ru": "Введите телефон:",
        "hy": "Enter phone number:",
    },
    "reg_enter_fullname": {
        "en": "Registration: enter full name:",
        "ru": "Регистрация: введите ФИО:",
        "hy": "Registration: enter full name:",
    },
    "reg_enter_phone": {
        "en": "Registration: enter phone number:",
        "ru": "Регистрация: введите телефон:",
        "hy": "Registration: enter phone number:",
    },
    "reg_success": {
        "en": "Registration completed.",
        "ru": "Регистрация завершена.",
        "hy": "Registration completed.",
    },
    "already_registered": {
        "en": "You are already registered.",
        "ru": "Вы уже зарегистрированы.",
        "hy": "You are already registered.",
    },
    "phone_required": {
        "en": "Phone number is required to use this feature. Complete registration.",
        "ru": "Нужен номер телефона. Завершите регистрацию.",
        "hy": "Phone number is required to use this feature. Complete registration.",
    },
    "phone_in_use": {
        "en": "Phone number is already in use.",
        "ru": "Телефон уже используется.",
        "hy": "Phone number is already in use.",
    },
    "enter_fullname_search": {
        "en": "Enter full name (or part of it):",
        "ru": "Введите ФИО (можно часть):",
        "hy": "Enter full name (or part of it):",
    },
    "multiple_users": {
        "en": "Multiple matches:\n{list}\nPlease уточните ФИО.",
        "ru": "Найдено несколько:\n{list}\nУточните ФИО.",
        "hy": "Multiple matches:\n{list}\nPlease уточните ФИО.",
    },
    "enter_card_number": {
        "en": "Enter recipient card number:",
        "ru": "Введите номер карты получателя:",
        "hy": "Enter recipient card number:",
    },
    "card_not_found": {
        "en": "Card not found.",
        "ru": "Карта не найдена.",
        "hy": "Card not found.",
    },
    "card_recipient_blocked": {
        "en": "Recipient card is blocked.",
        "ru": "Карта получателя заблокирована.",
        "hy": "Recipient card is blocked.",
    },
    "card_number_invalid": {
        "en": "Invalid card number.",
        "ru": "Некорректный номер карты.",
        "hy": "Invalid card number.",
    },
    "enter_amount": {
        "en": "Enter amount:",
        "ru": "Введите сумму:",
        "hy": "Enter amount:",
    },
    "enter_description": {
        "en": "Enter payment description:",
        "ru": "Введите описание платежа:",
        "hy": "Enter payment description:",
    },
    "insufficient_funds": {
        "en": "Insufficient funds.",
        "ru": "Недостаточно средств.",
        "hy": "Insufficient funds.",
    },
    "account_frozen": {
        "en": "Account is frozen.",
        "ru": "Счет заморожен.",
        "hy": "Account is frozen.",
    },
    "limit_exceeded": {
        "en": "Limit exceeded. Daily: {daily}, per tx: {tx}.",
        "ru": "Лимит превышен. Дневной: {daily}, за операцию: {tx}.",
        "hy": "Limit exceeded. Daily: {daily}, per tx: {tx}.",
    },
    "confirm_transfer": {
        "en": "Confirm transfer:\nFrom: {from_acc}\nTo: {to_acc}\nAmount: {amount} MRK\nFee: {fee}",
        "ru": "Подтвердите перевод:\nСчет: {from_acc}\nПолучатель: {to_acc}\nСумма: {amount} MRK\nКомиссия: {fee}",
        "hy": "Confirm transfer:\nFrom: {from_acc}\nTo: {to_acc}\nAmount: {amount} MRK\nFee: {fee}",
    },
    "confirm_payment": {
        "en": "Confirm payment:\nFrom: {from_acc}\nAmount: {amount} MRK\nFee: {fee}\nDesc: {desc}",
        "ru": "Подтвердите платеж:\nСчет: {from_acc}\nСумма: {amount} MRK\nКомиссия: {fee}\nОписание: {desc}",
        "hy": "Confirm payment:\nFrom: {from_acc}\nAmount: {amount} MRK\nFee: {fee}\nDesc: {desc}",
    },
    "enter_pin": {
        "en": "Enter PIN:",
        "ru": "Введите PIN:",
        "hy": "Enter PIN:",
    },
    "pin_set": {
        "en": "PIN set successfully.",
        "ru": "PIN установлен.",
        "hy": "PIN set successfully.",
    },
    "pin_required": {
        "en": "Set a PIN first.",
        "ru": "Сначала установите PIN.",
        "hy": "Set a PIN first.",
    },
    "pin_invalid": {
        "en": "Invalid PIN.",
        "ru": "Неверный PIN.",
        "hy": "Invalid PIN.",
    },
    "pin_blocked": {
        "en": "Account blocked due to PIN attempts.",
        "ru": "Аккаунт заблокирован из-за неверных PIN.",
        "hy": "Account blocked due to PIN attempts.",
    },
    "otp_sent": {
        "en": "OTP sent. Enter code:",
        "ru": "OTP отправлен. Введите код:",
        "hy": "OTP sent. Enter code:",
    },
    "otp_invalid": {
        "en": "Invalid OTP.",
        "ru": "Неверный OTP.",
        "hy": "Invalid OTP.",
    },
    "otp_expired": {
        "en": "OTP expired.",
        "ru": "OTP истек.",
        "hy": "OTP expired.",
    },
    "transfer_done": {
        "en": "Transfer completed.",
        "ru": "Перевод выполнен.",
        "hy": "Transfer completed.",
    },
    "payment_done": {
        "en": "Payment completed.",
        "ru": "Платеж выполнен.",
        "hy": "Payment completed.",
    },
    "card_info": {
        "en": "Card: {number}\nStatus: {status}",
        "ru": "Карта: {number}\nСтатус: {status}",
        "hy": "Card: {number}\nStatus: {status}",
    },
    "card_issued": {
        "en": "Virtual card issued: {number}",
        "ru": "Виртуальная карта выпущена: {number}",
        "hy": "Virtual card issued: {number}",
    },
    "card_blocked": {
        "en": "Card blocked.",
        "ru": "Карта заблокирована.",
        "hy": "Card blocked.",
    },
    "card_unblocked": {
        "en": "Card unblocked.",
        "ru": "Карта разблокирована.",
        "hy": "Card unblocked.",
    },
    "loan_amount": {
        "en": "Enter loan amount:",
        "ru": "Введите сумму кредита:",
        "hy": "Enter loan amount:",
    },
    "loan_term": {
        "en": "Enter term in months:",
        "ru": "Введите срок (мес.):",
        "hy": "Enter term in months:",
    },
    "loan_submitted": {
        "en": "Loan application submitted.",
        "ru": "Заявка отправлена.",
        "hy": "Loan application submitted.",
    },
    "support_prompt": {
        "en": "Describe your issue:",
        "ru": "Опишите проблему:",
        "hy": "Describe your issue:",
    },
    "support_received": {
        "en": "Ticket created. Operator will respond soon.",
        "ru": "Обращение создано. Оператор ответит скоро.",
        "hy": "Ticket created. Operator will respond soon.",
    },
    "user_not_found": {
        "en": "User not found.",
        "ru": "Пользователь не найден.",
        "hy": "User not found.",
    },
    "limits_updated": {
        "en": "Limits updated.",
        "ru": "Лимиты обновлены.",
        "hy": "Limits updated.",
    },
    "freeze_done": {
        "en": "Accounts frozen.",
        "ru": "Счета заморожены.",
        "hy": "Accounts frozen.",
    },
    "credit_pending_empty": {
        "en": "No pending applications.",
        "ru": "Нет заявок на рассмотрении.",
        "hy": "No pending applications.",
    },
    "credit_decided": {
        "en": "Decision recorded.",
        "ru": "Решение сохранено.",
        "hy": "Decision recorded.",
    },
    "ticket_empty": {
        "en": "No open tickets.",
        "ru": "Нет открытых обращений.",
        "hy": "No open tickets.",
    },
    "ticket_responded": {
        "en": "Response sent.",
        "ru": "Ответ отправлен.",
        "hy": "Response sent.",
    },
    "select_action": {
        "en": "Select action:",
        "ru": "Выберите действие:",
        "hy": "Select action:",
    },
    "enter_tg_id": {
        "en": "Enter tg_id:",
        "ru": "Введите tg_id:",
        "hy": "Enter tg_id:",
    },
    "enter_fullname": {
        "en": "Enter full name:",
        "ru": "Введите полное имя:",
        "hy": "Enter full name:",
    },
    "enter_role": {
        "en": "Enter role (client/admin/operator/risk):",
        "ru": "Введите роль (client/admin/operator/risk):",
        "hy": "Enter role (client/admin/operator/risk):",
    },
    "user_blocked": {
        "en": "User blocked.",
        "ru": "Пользователь заблокирован.",
        "hy": "User blocked.",
    },
    "user_created": {
        "en": "User created.",
        "ru": "Пользователь создан.",
        "hy": "User created.",
    },
    "user_exists": {
        "en": "User already exists.",
        "ru": "Пользователь уже существует.",
        "hy": "User already exists.",
    },
    "role_updated": {
        "en": "Role updated.",
        "ru": "Роль обновлена.",
        "hy": "Role updated.",
    },
    "enter_daily_limit": {
        "en": "Enter daily limit:",
        "ru": "Введите дневной лимит:",
        "hy": "Enter daily limit:",
    },
    "enter_tx_limit": {
        "en": "Enter per-tx limit:",
        "ru": "Введите разовый лимит:",
        "hy": "Enter per-tx limit:",
    },
    "select_account": {
        "en": "Select account:",
        "ru": "Выберите счет:",
        "hy": "Select account:",
    },
    "enter_amount_signed": {
        "en": "Enter amount (+/-):",
        "ru": "Введите сумму (+/-):",
        "hy": "Enter amount (+/-):",
    },
    "balance_updated": {
        "en": "Balance updated.",
        "ru": "Баланс обновлен.",
        "hy": "Balance updated.",
    },
    "enter_response": {
        "en": "Enter response:",
        "ru": "Введите ответ:",
        "hy": "Enter response:",
    },
    "reply": {
        "en": "Reply",
        "ru": "Ответить",
        "hy": "Reply",
    },
    "approve": {
        "en": "Approve",
        "ru": "Одобрить",
        "hy": "Approve",
    },
    "deny": {
        "en": "Deny",
        "ru": "Отклонить",
        "hy": "Deny",
    },
    "create_user": {
        "en": "Create",
        "ru": "Создать",
        "hy": "Create",
    },
    "block_user": {
        "en": "Block",
        "ru": "Заблокировать",
        "hy": "Block",
    },
    "change_role": {
        "en": "Change Role",
        "ru": "Изменить роль",
        "hy": "Change Role",
    },
    "issue": {
        "en": "Issue",
        "ru": "Выпустить",
        "hy": "Issue",
    },
    "block": {
        "en": "Block",
        "ru": "Заблокировать",
        "hy": "Block",
    },
    "unblock": {
        "en": "Unblock",
        "ru": "Разблокировать",
        "hy": "Unblock",
    },
    "decision_approved": {
        "en": "approved",
        "ru": "одобрено",
        "hy": "approved",
    },
    "decision_denied": {
        "en": "denied",
        "ru": "отклонено",
        "hy": "denied",
    },
    "notify_card_issue": {
        "en": "New card issued for {name} ({phone}). Card: {card}",
        "ru": "Новая карта для {name} ({phone}). Карта: {card}",
        "hy": "New card issued for {name} ({phone}). Card: {card}",
    },
    "notify_loan_apply": {
        "en": "New loan application #{app_id} from {name} ({phone}). Amount: {amount:.2f} MRK, term: {term}m.",
        "ru": "Новая заявка на кредит #{app_id} от {name} ({phone}). Сумма: {amount:.2f} MRK, срок: {term}м.",
        "hy": "New loan application #{app_id} from {name} ({phone}). Amount: {amount:.2f} MRK, term: {term}m.",
    },
    "notify_credit_decision": {
        "en": "Credit application #{app_id} {decision} by {officer}.",
        "ru": "Заявка на кредит #{app_id} {decision}. Решение: {officer}.",
        "hy": "Credit application #{app_id} {decision} by {officer}.",
    },
    "report_summary": {
        "en": "Report:\nTurnover: {turnover}\nActive loans: {loans}\nFrozen users: {frozen}",
        "ru": "Отчет:\nОборот: {turnover}\nАктивные кредиты: {loans}\nЗамороженных: {frozen}",
        "hy": "Report:\nTurnover: {turnover}\nActive loans: {loans}\nFrozen users: {frozen}",
    },
    "logs_header": {
        "en": "Latest logs:\n{list}",
        "ru": "Последние логи:\n{list}",
        "hy": "Latest logs:\n{list}",
    },
    "unknown": {
        "en": "Unknown command. Use the menu.",
        "ru": "Неизвестная команда. Используйте меню.",
        "hy": "Unknown command. Use the menu.",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    if lang not in LANGS:
        lang = "en"
    block = TEXTS.get(key, {})
    text = block.get(lang) or block.get("en") or key
    return text.format(**kwargs) if kwargs else text


def detect_lang(message: Message) -> str:
    if message.from_user.id in user_languages:
        return user_languages[message.from_user.id]
    tg_lang = message.from_user.language_code
    if tg_lang:
        tg_lang = tg_lang.split("-")[0]
        if tg_lang in LANGS:
            return tg_lang
    return "en"


def hash_pin(pin: str, tg_id: int) -> str:
    payload = f"{tg_id}:{pin}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def luhn_check_digit(number: str) -> str:
    total = 0
    for index, digit in enumerate(reversed(number)):
        n = int(digit)
        if index % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return str((10 - (total % 10)) % 10)


def generate_card_number(prefix: str = "57297094") -> str:
    base = prefix + "".join(random.choice(string.digits) for _ in range(7))
    return base + luhn_check_digit(base)


def format_card(number: str) -> str:
    return " ".join(number[i:i + 4] for i in range(0, len(number), 4))


def generate_otp() -> str:
    return "".join(random.choice(string.digits) for _ in range(6))


def normalize_card_number(text: str) -> str:
    return "".join(ch for ch in text if ch.isdigit())


def normalize_phone(text: str) -> str:
    return "".join(ch for ch in (text or "") if ch.isdigit())


def render_card_balance_image(balance: float) -> bytes | None:
    image_path = Path(__file__).resolve().parents[2] / "Linar Bank.png"
    if not image_path.exists():
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except Exception:
        return None
    try:
        with Image.open(image_path).convert("RGBA") as img:
            draw = ImageDraw.Draw(img)
            text = f"Balance: {balance:.2f}"
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = max(10, img.width - text_w - 20)
            y = max(10, img.height - text_h - 20)
            draw.rectangle([x - 8, y - 6, x + text_w + 8, y + text_h + 6], fill=(0, 0, 0, 160))
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
            buf = BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
    except Exception:
        return None


async def ensure_user(tg_id: int, fullname: str):
    return await db.get_user_by_tg(tg_id)


async def require_any_role(message: Message, roles: list[str]):
    user = await db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer(t(detect_lang(message), "not_registered"))
        return None
    if user["status"] != USER_ACTIVE:
        await message.answer(t(detect_lang(message), "pin_blocked"))
        return None
    if user["role"] not in roles and user["role"] != ROLE_ADMIN:
        await message.answer(t(detect_lang(message), "access_denied"))
        return None
    return user


async def require_any_role_callback(callback: CallbackQuery, roles: list[str]):
    user = await db.get_user_by_tg(callback.from_user.id)
    if not user:
        await callback.message.answer(t(detect_lang(callback.message), "not_registered"))
        return None
    if user["status"] != USER_ACTIVE:
        await callback.message.answer(t(detect_lang(callback.message), "pin_blocked"))
        return None
    if user["role"] not in roles and user["role"] != ROLE_ADMIN:
        await callback.message.answer(t(detect_lang(callback.message), "access_denied"))
        return None
    return user


async def require_phone(message: Message, user, state: FSMContext | None = None) -> bool:
    if user and user.get("phone"):
        return True
    lang = detect_lang(message)
    await message.answer(t(lang, "phone_required"))
    if state and user:
        await state.update_data(user_id=user["id"], fullname=user.get("fullname") or message.from_user.full_name)
        await state.set_state(RegisterStates.enter_phone)
        await message.answer(t(lang, "reg_enter_phone"))
    return False


async def require_phone_callback(callback: CallbackQuery, user, state: FSMContext | None = None) -> bool:
    if user and user.get("phone"):
        return True
    lang = detect_lang(callback.message)
    await callback.message.answer(t(lang, "phone_required"))
    if state and user:
        await state.update_data(user_id=user["id"], fullname=user.get("fullname") or callback.from_user.full_name)
        await state.set_state(RegisterStates.enter_phone)
        await callback.message.answer(t(lang, "reg_enter_phone"))
    return False


async def notify_admin(bot, text: str, actor_tg_id: int | None = None):
    if not ADMIN_ID:
        return
    try:
        await bot.send_message(ADMIN_ID, text)
    except Exception:
        return


async def get_today_spent(user_id: int) -> float:
    today = datetime.utcnow().date().isoformat()
    txs = await db.list_transactions(user_id, limit=None)
    total = 0.0
    for tx in txs:
        if tx.get("status") == "completed" and str(tx.get("created_at", ""))[:10] == today:
            total += float(tx.get("amount", 0.0)) + float(tx.get("fee", 0.0))
    return total


def is_menu_button(text: str, key: str) -> bool:
    if not text:
        return False
    return text in {
        LABELS[key]["en"],
        LABELS[key]["ru"],
        LABELS[key]["hy"],
    }


class TransferStates(StatesGroup):
    choose_type = State()
    choose_from = State()
    choose_to = State()
    enter_card = State()
    enter_amount = State()
    enter_pin = State()
    enter_otp = State()


class PaymentStates(StatesGroup):
    choose_from = State()
    enter_amount = State()
    enter_desc = State()
    enter_pin = State()
    enter_otp = State()


class PinStates(StatesGroup):
    enter_pin = State()


class RegisterStates(StatesGroup):
    enter_fullname = State()
    enter_phone = State()


class LoanStates(StatesGroup):
    enter_amount = State()
    enter_term = State()


class SupportStates(StatesGroup):
    enter_message = State()


class AdminUserStates(StatesGroup):
    choose_action = State()
    enter_tg_id = State()
    enter_fullname = State()
    enter_phone = State()
    enter_role = State()


class LimitsStates(StatesGroup):
    enter_phone = State()
    enter_daily = State()
    enter_tx = State()


class AdjustStates(StatesGroup):
    enter_phone = State()
    choose_account = State()
    enter_amount = State()


class TicketStates(StatesGroup):
    enter_response = State()


class ProfileStates(StatesGroup):
    enter_name = State()


class FreezeStates(StatesGroup):
    enter_phone = State()


class OperatorHistoryStates(StatesGroup):
    enter_name = State()


class AdminCardStates(StatesGroup):
    enter_phone = State()


async def send_main_menu(message: Message, user, lang: str):
    await message.answer(
        t(lang, "main_menu"),
        reply_markup=get_main_menu_keyboard(user["role"], lang),
    )


# --- HANDLERS BELOW ---
@router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = lang
    await callback.answer()
    await callback.message.edit_text(t(lang, "lang_changed"))


@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await db.init_db()
    user = await ensure_user(message.from_user.id, message.from_user.full_name)
    lang = detect_lang(message)
    if not user:
        await state.set_state(RegisterStates.enter_fullname)
        await message.answer(t(lang, "reg_enter_fullname"))
        return
    if not user.get("phone"):
        await state.update_data(user_id=user["id"], fullname=user.get("fullname") or message.from_user.full_name)
        await state.set_state(RegisterStates.enter_phone)
        await message.answer(t(lang, "reg_enter_phone"))
        return
    await send_main_menu(message, user, lang)


@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(t(detect_lang(message), "help"), reply_markup=get_back_keyboard(detect_lang(message)))


@router.message(Command("register"))
async def register_cmd(message: Message, state: FSMContext):
    await db.init_db()
    lang = detect_lang(message)
    user = await db.get_user_by_tg(message.from_user.id)
    if user and user.get("phone"):
        await message.answer(t(lang, "already_registered"))
        return
    if not user:
        await state.set_state(RegisterStates.enter_fullname)
        await message.answer(t(lang, "reg_enter_fullname"))
        return
    await state.update_data(user_id=user["id"], fullname=user.get("fullname") or message.from_user.full_name)
    await state.set_state(RegisterStates.enter_phone)
    await message.answer(t(lang, "reg_enter_phone"))


@router.message(Command("lang"))
async def lang_cmd(message: Message):
    lang = detect_lang(message)
    await message.answer(t(lang, "lang_select"), reply_markup=get_language_keyboard())


@router.message(Command("menu"))
async def menu_cmd(message: Message):
    user = await db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer(t(detect_lang(message), "not_registered"))
        return
    await send_main_menu(message, user, detect_lang(message))


@router.message(RegisterStates.enter_fullname)
async def register_fullname(message: Message, state: FSMContext):
    lang = detect_lang(message)
    fullname = message.text.strip()
    if len(fullname) < 2:
        await message.answer(t(lang, "reg_enter_fullname"))
        return
    await state.update_data(fullname=fullname)
    await state.set_state(RegisterStates.enter_phone)
    await message.answer(t(lang, "reg_enter_phone"))


@router.message(RegisterStates.enter_phone)
async def register_phone(message: Message, state: FSMContext):
    lang = detect_lang(message)
    phone_raw = message.text.strip()
    phone_norm = normalize_phone(phone_raw)
    if len(phone_norm) < 8 or len(phone_norm) > 15:
        await message.answer(t(lang, "reg_enter_phone"))
        return
    data = await state.get_data()
    existing_phone_user = await db.get_user_by_phone(phone_raw)
    if existing_phone_user and data.get("user_id") != existing_phone_user.get("id"):
        await message.answer(t(lang, "phone_in_use"))
        return
    if data.get("user_id"):
        await db.update_user_profile(data["user_id"], fullname=data.get("fullname"), phone=phone_raw)
        user = await db.get_user_by_id(data["user_id"])
    else:
        role = ROLE_ADMIN if ADMIN_ID and message.from_user.id == ADMIN_ID else ROLE_CLIENT
        user = await db.create_user(message.from_user.id, data.get("fullname") or message.from_user.full_name, phone_raw, role)
        if user:
            await db.create_account(user["id"], "Main", "MRK", 0.0)
            await db.ensure_limits(user["id"])
    if user:
        await registry.sync_user_from_linar(user)
    await message.answer(t(lang, "reg_success"))
    if user:
        await send_main_menu(message, user, lang)
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "main_menu"))
async def main_menu_button(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer(t(detect_lang(message), "not_registered"))
        return
    await send_main_menu(message, user, detect_lang(message))


@router.message(lambda m: is_menu_button(m.text, "accounts"))
async def accounts_menu(message: Message):
    user = await require_any_role(message, [ROLE_CLIENT])
    if not user:
        return
    accounts = await db.get_accounts(user["id"])
    if not accounts:
        await message.answer(t(detect_lang(message), "no_accounts"), reply_markup=get_back_keyboard(detect_lang(message)))
        return
    lines = []
    for acc in accounts:
        lines.append(f"#{acc['id']} {acc['name']} {acc['currency']} — {acc['balance']:.2f} ({acc['status']})")
    await message.answer(
        t(detect_lang(message), "accounts", list="\n".join(lines)),
        reply_markup=get_back_keyboard(detect_lang(message)),
    )


@router.message(lambda m: is_menu_button(m.text, "history"))
async def history_menu(message: Message, state: FSMContext):
    user = await db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer(t(detect_lang(message), "not_registered"))
        return
    if user["role"] in [ROLE_OPERATOR, ROLE_ADMIN, ROLE_RISK]:
        await state.set_state(OperatorHistoryStates.enter_name)
        await message.answer(t(detect_lang(message), "enter_fullname_search"))
        return
    txs = await db.list_transactions(user["id"], 10)
    if not txs:
        await message.answer(t(detect_lang(message), "no_history"), reply_markup=get_back_keyboard(detect_lang(message)))
        return
    lines = [f"#{tx['id']} {tx['type']} {tx['amount']:.2f} MRK ({tx['status']})" for tx in txs]
    await message.answer(
        t(detect_lang(message), "history", list="\n".join(lines)),
        reply_markup=get_back_keyboard(detect_lang(message)),
    )


@router.message(OperatorHistoryStates.enter_name)
async def operator_history_tg(message: Message, state: FSMContext):
    operator = await require_any_role(message, [ROLE_OPERATOR, ROLE_ADMIN, ROLE_RISK])
    if not operator:
        await state.clear()
        return
    query = message.text.strip()
    matches = await db.search_users_by_fullname(query)
    if not matches:
        await message.answer(t(detect_lang(message), "user_not_found"))
        return
    if len(matches) > 1:
        lines = [f"#{u['id']} {u['fullname']} ({u['phone'] or '-'})" for u in matches]
        await message.answer(t(detect_lang(message), "multiple_users", list="\n".join(lines)))
        return
    target = matches[0]
    txs = await db.list_transactions(target["id"], 10)
    if not txs:
        await message.answer(t(detect_lang(message), "no_history"), reply_markup=get_back_keyboard(detect_lang(message)))
        await state.clear()
        return
    lines = [f"#{tx['id']} {tx['type']} {tx['amount']:.2f} MRK ({tx['status']})" for tx in txs]
    await message.answer(
        t(detect_lang(message), "history", list="\n".join(lines)),
        reply_markup=get_back_keyboard(detect_lang(message)),
    )
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "transfer"))
async def transfer_menu(message: Message, state: FSMContext):
    user = await require_any_role(message, [ROLE_CLIENT])
    if not user:
        return
    if not await require_phone(message, user, state):
        return
    lang = detect_lang(message)
    actions = [
        ("Between my accounts", "transfer:type:own"),
        ("To another client", "transfer:type:external"),
    ]
    await state.set_state(TransferStates.choose_type)
    await message.answer(t(lang, "transfer_type"), reply_markup=inline_keyboard(actions, row_size=1))


@router.callback_query(F.data.startswith("transfer:type:"))
async def transfer_type(callback: CallbackQuery, state: FSMContext):
    lang = detect_lang(callback.message)
    transfer_type = callback.data.split(":")[2]
    await state.update_data(transfer_type=transfer_type)
    await callback.answer()
    user = await db.get_user_by_tg(callback.from_user.id)
    accounts = await db.get_accounts(user["id"])
    actions = [(f"#{a['id']} {a['name']} {a['currency']}", f"transfer:from:{a['id']}") for a in accounts]
    await state.set_state(TransferStates.choose_from)
    await callback.message.answer(t(lang, "choose_from"), reply_markup=inline_keyboard(actions, row_size=1))


@router.callback_query(F.data.startswith("transfer:from:"))
async def transfer_from(callback: CallbackQuery, state: FSMContext):
    lang = detect_lang(callback.message)
    account_id = int(callback.data.split(":")[2])
    await state.update_data(from_account_id=account_id)
    data = await state.get_data()
    transfer_type = data.get("transfer_type")
    await callback.answer()
    if transfer_type == "own":
        user = await db.get_user_by_tg(callback.from_user.id)
        accounts = await db.get_accounts(user["id"])
        actions = [(f"#{a['id']} {a['name']} {a['currency']}", f"transfer:to:{a['id']}") for a in accounts if a["id"] != account_id]
        await state.set_state(TransferStates.choose_to)
        await callback.message.answer(t(lang, "choose_to"), reply_markup=inline_keyboard(actions, row_size=1))
    else:
        await state.set_state(TransferStates.enter_card)
        await callback.message.answer(t(lang, "enter_card_number"))


@router.callback_query(F.data.startswith("transfer:to:"))
async def transfer_to(callback: CallbackQuery, state: FSMContext):
    account_id = int(callback.data.split(":")[2])
    await state.update_data(to_account_id=account_id)
    await state.set_state(TransferStates.enter_amount)
    await callback.answer()
    await callback.message.answer(t(detect_lang(callback.message), "enter_amount"))


@router.message(TransferStates.enter_card)
async def transfer_enter_card(message: Message, state: FSMContext):
    lang = detect_lang(message)
    card_number = normalize_card_number(message.text.strip())
    if len(card_number) != 16:
        await message.answer(t(lang, "card_number_invalid"))
        return
    card = await db.get_card_by_number(card_number)
    if not card:
        await message.answer(t(lang, "card_not_found"))
        return
    if card["status"] != "active":
        await message.answer(t(lang, "card_recipient_blocked"))
        return
    accounts = await db.get_accounts(card["user_id"])
    if not accounts:
        await message.answer(t(lang, "user_not_found"))
        return
    to_account = next((acc for acc in accounts if acc["status"] == USER_ACTIVE), accounts[0])
    await state.update_data(
        recipient_user_id=card["user_id"],
        to_account_id=to_account["id"],
        to_label=f"Card {format_card(card_number)}",
    )
    await state.set_state(TransferStates.enter_amount)
    await message.answer(t(lang, "enter_amount"))


@router.message(TransferStates.enter_amount)
async def transfer_enter_amount(message: Message, state: FSMContext):
    lang = detect_lang(message)
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(t(lang, "enter_amount"))
        return
    if amount <= 0:
        await message.answer(t(lang, "enter_amount"))
        return
    user = await db.get_user_by_tg(message.from_user.id)
    limits = await db.get_limits(user["id"])
    spent = await get_today_spent(user["id"])
    if limits and (amount > limits["tx_limit"] or spent + amount > limits["daily_limit"]):
        await message.answer(t(lang, "limit_exceeded", daily=limits["daily_limit"], tx=limits["tx_limit"]))
        await state.clear()
        return
    data = await state.get_data()
    from_account = await db.get_account(data["from_account_id"])
    if not from_account or from_account["status"] != USER_ACTIVE:
        await message.answer(t(lang, "account_frozen"))
        await state.clear()
        return
    transfer_type = data.get("transfer_type")
    fee_rate = FEE_INTERNAL if transfer_type == "own" else FEE_EXTERNAL
    fee = amount * fee_rate
    total = amount + fee
    if from_account["balance"] < total:
        await message.answer(t(lang, "insufficient_funds"))
        await state.clear()
        return
    to_account = await db.get_account(data["to_account_id"])
    to_label = data.get("to_label")
    if not to_label and to_account:
        to_label = f"{to_account['name']} #{to_account['id']}"
    await state.update_data(amount=amount, fee=fee)
    await message.answer(
        t(
            lang,
            "confirm_transfer",
            from_acc=f"{from_account['name']} #{from_account['id']}",
            to_acc=to_label or "—",
            amount=f"{amount:.2f} MRK",
            fee=f"{fee:.2f}",
        ),
        reply_markup=get_confirm_keyboard("transfer:confirm", "transfer:cancel", lang),
    )


@router.callback_query(F.data.in_(["transfer:confirm", "transfer:cancel"]))
async def transfer_confirm(callback: CallbackQuery, state: FSMContext):
    lang = detect_lang(callback.message)
    if callback.data.endswith("cancel"):
        await state.clear()
        await callback.answer()
        await callback.message.answer(t(lang, "unknown"), reply_markup=get_back_keyboard(lang))
        return
    await callback.answer()
    user = await db.get_user_by_tg(callback.from_user.id)
    if not user or not user["pin_hash"]:
        await callback.message.answer(t(lang, "pin_required"))
        await state.clear()
        return
    await state.set_state(TransferStates.enter_pin)
    await callback.message.answer(t(lang, "enter_pin"))


@router.message(TransferStates.enter_pin)
async def transfer_pin(message: Message, state: FSMContext):
    lang = detect_lang(message)
    user = await db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer(t(lang, "not_registered"))
        await state.clear()
        return
    if user["pin_hash"] != hash_pin(message.text.strip(), user["tg_id"]):
        await db.increment_pin_attempts(user["id"])
        if user["pin_attempts"] + 1 >= PIN_MAX_ATTEMPTS:
            await db.set_user_status(user["id"], USER_BLOCKED)
            await db.set_account_status(user["id"], USER_FROZEN)
            await message.answer(t(lang, "pin_blocked"))
            await state.clear()
            return
        await message.answer(t(lang, "pin_invalid"))
        return
    await db.reset_pin_attempts(user["id"])
    data = await state.get_data()
    tx_id = await db.create_transaction(
        user["id"],
        data["from_account_id"],
        data["to_account_id"],
        data["amount"],
        data["fee"],
        "transfer",
        "pending",
        "transfer",
    )
    code = generate_otp()
    expires_at = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat(timespec="seconds")
    otp_id = await db.create_otp(user["id"], tx_id, code, expires_at)
    await state.update_data(otp_id=otp_id, tx_id=tx_id)
    await state.set_state(TransferStates.enter_otp)
    await message.answer(f"{t(lang, 'otp_sent')} {code}")


@router.message(TransferStates.enter_otp)
async def transfer_otp(message: Message, state: FSMContext):
    lang = detect_lang(message)
    data = await state.get_data()
    otp = await db.get_otp(data["otp_id"])
    if not otp or otp["status"] != "active":
        await message.answer(t(lang, "otp_invalid"))
        await state.clear()
        return
    if datetime.fromisoformat(otp["expires_at"]) < datetime.utcnow():
        await db.set_otp_status(otp["id"], "expired")
        await message.answer(t(lang, "otp_expired"))
        await state.clear()
        return
    if otp["code"] != message.text.strip():
        await db.increment_otp_attempts(otp["id"])
        if otp["attempts"] + 1 >= OTP_MAX_ATTEMPTS:
            await db.set_otp_status(otp["id"], "blocked")
            await db.update_transaction_status(data["tx_id"], "rejected")
            await db.set_user_status(otp["user_id"], USER_BLOCKED)
            await db.set_account_status(otp["user_id"], USER_FROZEN)
            await message.answer(t(lang, "otp_invalid"))
            await state.clear()
            return
        await message.answer(t(lang, "otp_invalid"))
        return
    await db.set_otp_status(otp["id"], "used")
    await db.update_balance(data["from_account_id"], -(data["amount"] + data["fee"]))
    await db.update_balance(data["to_account_id"], data["amount"])
    await db.update_transaction_status(data["tx_id"], "completed")
    await db.log_action(otp["user_id"], "transfer_completed", f"tx_id={data['tx_id']}")
    await message.answer(t(lang, "transfer_done"), reply_markup=get_back_keyboard(lang))
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "payments"))
async def payment_menu(message: Message, state: FSMContext):
    user = await require_any_role(message, [ROLE_CLIENT])
    if not user:
        return
    if not await require_phone(message, user, state):
        return
    accounts = await db.get_accounts(user["id"])
    actions = [(f"#{a['id']} {a['name']} {a['currency']}", f"payment:from:{a['id']}") for a in accounts]
    await state.set_state(PaymentStates.choose_from)
    await message.answer(t(detect_lang(message), "choose_from"), reply_markup=inline_keyboard(actions, row_size=1))


@router.callback_query(F.data.startswith("payment:from:"))
async def payment_from(callback: CallbackQuery, state: FSMContext):
    account_id = int(callback.data.split(":")[2])
    await state.update_data(from_account_id=account_id)
    await state.set_state(PaymentStates.enter_amount)
    await callback.answer()
    await callback.message.answer(t(detect_lang(callback.message), "enter_amount"))


@router.message(PaymentStates.enter_amount)
async def payment_amount(message: Message, state: FSMContext):
    lang = detect_lang(message)
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(t(lang, "enter_amount"))
        return
    if amount <= 0:
        await message.answer(t(lang, "enter_amount"))
        return
    await state.update_data(amount=amount)
    await state.set_state(PaymentStates.enter_desc)
    await message.answer(t(lang, "enter_description"))


@router.message(PaymentStates.enter_desc)
async def payment_desc(message: Message, state: FSMContext):
    lang = detect_lang(message)
    desc = message.text.strip()
    data = await state.get_data()
    fee = data["amount"] * FEE_PAYMENT
    from_account = await db.get_account(data["from_account_id"])
    if not from_account or from_account["status"] != USER_ACTIVE:
        await message.answer(t(lang, "account_frozen"))
        await state.clear()
        return
    if from_account["balance"] < data["amount"] + fee:
        await message.answer(t(lang, "insufficient_funds"))
        await state.clear()
        return
    await state.update_data(desc=desc, fee=fee)
    await message.answer(
        t(
            lang,
            "confirm_payment",
            from_acc=f"{from_account['name']} #{from_account['id']}",
            amount=f"{data['amount']:.2f} MRK",
            fee=f"{fee:.2f}",
            desc=desc,
        ),
        reply_markup=get_confirm_keyboard("payment:confirm", "payment:cancel", lang),
    )


@router.callback_query(F.data.in_(["payment:confirm", "payment:cancel"]))
async def payment_confirm(callback: CallbackQuery, state: FSMContext):
    lang = detect_lang(callback.message)
    if callback.data.endswith("cancel"):
        await state.clear()
        await callback.answer()
        await callback.message.answer(t(lang, "unknown"), reply_markup=get_back_keyboard(lang))
        return
    await callback.answer()
    user = await db.get_user_by_tg(callback.from_user.id)
    if not user or not user["pin_hash"]:
        await callback.message.answer(t(lang, "pin_required"))
        await state.clear()
        return
    await state.set_state(PaymentStates.enter_pin)
    await callback.message.answer(t(lang, "enter_pin"))


@router.message(PaymentStates.enter_pin)
async def payment_pin(message: Message, state: FSMContext):
    lang = detect_lang(message)
    user = await db.get_user_by_tg(message.from_user.id)
    if user["pin_hash"] != hash_pin(message.text.strip(), user["tg_id"]):
        await db.increment_pin_attempts(user["id"])
        if user["pin_attempts"] + 1 >= PIN_MAX_ATTEMPTS:
            await db.set_user_status(user["id"], USER_BLOCKED)
            await db.set_account_status(user["id"], USER_FROZEN)
            await message.answer(t(lang, "pin_blocked"))
            await state.clear()
            return
        await message.answer(t(lang, "pin_invalid"))
        return
    await db.reset_pin_attempts(user["id"])
    data = await state.get_data()
    tx_id = await db.create_transaction(
        user["id"],
        data["from_account_id"],
        None,
        data["amount"],
        data["fee"],
        "payment",
        "pending",
        data["desc"],
    )
    code = generate_otp()
    expires_at = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat(timespec="seconds")
    otp_id = await db.create_otp(user["id"], tx_id, code, expires_at)
    await state.update_data(otp_id=otp_id, tx_id=tx_id)
    await state.set_state(PaymentStates.enter_otp)
    await message.answer(f"{t(lang, 'otp_sent')} {code}")


@router.message(PaymentStates.enter_otp)
async def payment_otp(message: Message, state: FSMContext):
    lang = detect_lang(message)
    data = await state.get_data()
    otp = await db.get_otp(data["otp_id"])
    if not otp or otp["status"] != "active":
        await message.answer(t(lang, "otp_invalid"))
        await state.clear()
        return
    if datetime.fromisoformat(otp["expires_at"]) < datetime.utcnow():
        await db.set_otp_status(otp["id"], "expired")
        await message.answer(t(lang, "otp_expired"))
        await state.clear()
        return
    if otp["code"] != message.text.strip():
        await db.increment_otp_attempts(otp["id"])
        if otp["attempts"] + 1 >= OTP_MAX_ATTEMPTS:
            await db.set_otp_status(otp["id"], "blocked")
            await db.update_transaction_status(data["tx_id"], "rejected")
            await db.set_user_status(otp["user_id"], USER_BLOCKED)
            await db.set_account_status(otp["user_id"], USER_FROZEN)
            await message.answer(t(lang, "otp_invalid"))
            await state.clear()
            return
        await message.answer(t(lang, "otp_invalid"))
        return
    await db.set_otp_status(otp["id"], "used")
    await db.update_balance(data["from_account_id"], -(data["amount"] + data["fee"]))
    await db.update_transaction_status(data["tx_id"], "completed")
    await db.log_action(otp["user_id"], "payment_completed", f"tx_id={data['tx_id']}")
    await message.answer(t(lang, "payment_done"), reply_markup=get_back_keyboard(lang))
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "card"))
async def card_menu(message: Message, state: FSMContext):
    user = await require_any_role(message, [ROLE_CLIENT])
    if not user:
        return
    if not await require_phone(message, user, state):
        return
    lang = detect_lang(message)
    card = await db.get_card_by_user(user["id"])
    if not card:
        await message.answer(
            t(lang, "card_info", number="—", status="none"),
            reply_markup=get_card_action_keyboard(False, False, lang),
        )
        return
    accounts = await db.get_accounts(user["id"])
    main_account = None
    for acc in accounts:
        if str(acc.get("name", "")).lower() == "main":
            main_account = acc
            break
    if not main_account and accounts:
        main_account = accounts[0]
    balance = float(main_account.get("balance", 0.0)) if main_account else 0.0
    rendered = render_card_balance_image(balance)
    if rendered:
        await message.answer_photo(BufferedInputFile(rendered, filename="card.png"))
    else:
        image_path = Path(__file__).resolve().parents[2] / "Linar Bank.png"
        if image_path.exists():
            await message.answer_photo(FSInputFile(image_path))
    await message.answer(   
        t(lang, "card_info", number=format_card(card["card_number"]), status=card["status"]),
        reply_markup=get_card_action_keyboard(True, card["status"] == "blocked", lang),
    )


@router.callback_query(F.data.in_(["card:issue", "card:block", "card:unblock"]))
async def card_action(callback: CallbackQuery, state: FSMContext):
    lang = detect_lang(callback.message)
    user = await db.get_user_by_tg(callback.from_user.id)
    if not user:
        await callback.message.answer(t(lang, "not_registered"))
        return
    if not await require_phone_callback(callback, user, state):
        return
    card = await db.get_card_by_user(user["id"])
    if callback.data == "card:issue":
        if not card:
            number = generate_card_number()
            await db.create_card(user["id"], number)
            await db.log_action(user["id"], "card_issue", f"card={number}")
            await callback.message.answer(t(lang, "card_issued", number=format_card(number)))
            await notify_admin(
                callback.message.bot,
                t(
                    lang,
                    "notify_card_issue",
                    name=user["fullname"],
                    phone=user["phone"] or "-",
                    card=format_card(number),
                ),
                callback.from_user.id,
            )
        else:
            await callback.message.answer(t(lang, "card_info", number=format_card(card["card_number"]), status=card["status"]))
    elif callback.data == "card:block" and card:
        await db.update_card_status(card["id"], "blocked", "user_request")
        await db.log_action(user["id"], "card_block", f"card_id={card['id']}")
        await callback.message.answer(t(lang, "card_blocked"))
    elif callback.data == "card:unblock" and card:
        await db.update_card_status(card["id"], "active", None)
        await db.log_action(user["id"], "card_unblock", f"card_id={card['id']}")
        await callback.message.answer(t(lang, "card_unblocked"))
    await callback.answer()


@router.message(lambda m: is_menu_button(m.text, "loans"))
async def loan_menu(message: Message, state: FSMContext):
    user = await require_any_role(message, [ROLE_CLIENT])
    if not user:
        return
    if not await require_phone(message, user, state):
        return
    await state.set_state(LoanStates.enter_amount)
    await message.answer(t(detect_lang(message), "loan_amount"))


@router.message(LoanStates.enter_amount)
async def loan_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(t(detect_lang(message), "loan_amount"))
        return
    await state.update_data(amount=amount)
    await state.set_state(LoanStates.enter_term)
    await message.answer(t(detect_lang(message), "loan_term"))


@router.message(LoanStates.enter_term)
async def loan_term(message: Message, state: FSMContext):
    try:
        term = int(message.text.strip())
    except ValueError:
        await message.answer(t(detect_lang(message), "loan_term"))
        return
    data = await state.get_data()
    user = await db.get_user_by_tg(message.from_user.id)
    app_id = await db.create_credit_application(user["id"], data["amount"], term)
    await db.log_action(user["id"], "loan_apply", f"amount={data['amount']} term={term}")
    lang = detect_lang(message)
    await message.answer(t(lang, "loan_submitted"), reply_markup=get_back_keyboard(lang))
    await notify_admin(
        message.bot,
        t(
            lang,
            "notify_loan_apply",
            app_id=app_id,
            name=user["fullname"],
            phone=user["phone"] or "-",
            amount=data["amount"],
            term=term,
        ),
        message.from_user.id,
    )
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "support"))
async def support_menu(message: Message, state: FSMContext):
    user = await require_any_role(message, [ROLE_CLIENT])
    if not user:
        return
    await state.set_state(SupportStates.enter_message)
    await message.answer(t(detect_lang(message), "support_prompt"))


@router.message(SupportStates.enter_message)
async def support_message(message: Message, state: FSMContext):
    user = await db.get_user_by_tg(message.from_user.id)
    await db.create_support_ticket(user["id"], message.text.strip())
    await message.answer(t(detect_lang(message), "support_received"), reply_markup=get_back_keyboard(detect_lang(message)))
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "set_pin"))
async def pin_menu(message: Message, state: FSMContext):
    await state.set_state(PinStates.enter_pin)
    await message.answer(t(detect_lang(message), "enter_pin"))


@router.message(PinStates.enter_pin)
async def pin_set(message: Message, state: FSMContext):
    pin = message.text.strip()
    if not pin.isdigit() or len(pin) < 4 or len(pin) > 6:
        await message.answer(t(detect_lang(message), "enter_pin"))
        return
    user = await db.get_user_by_tg(message.from_user.id)
    await db.set_user_pin(user["id"], hash_pin(pin, user["tg_id"]))
    await message.answer(t(detect_lang(message), "pin_set"), reply_markup=get_back_keyboard(detect_lang(message)))
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "users"))
async def admin_users(message: Message, state: FSMContext):
    user = await require_any_role(message, [ROLE_ADMIN])
    if not user:
        return
    lang = detect_lang(message)
    actions = [
        (t(lang, "create_user"), "admin:user:create"),
        (t(lang, "block_user"), "admin:user:block"),
        (t(lang, "change_role"), "admin:user:role"),
    ]
    await state.set_state(AdminUserStates.choose_action)
    await message.answer(t(lang, "select_action"), reply_markup=inline_keyboard(actions, row_size=1))


@router.callback_query(F.data.startswith("admin:user:"))
async def admin_user_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[2]
    await state.update_data(action=action)
    await callback.answer()
    if action == "create":
        await state.set_state(AdminUserStates.enter_tg_id)
        await callback.message.answer(t(detect_lang(callback.message), "enter_tg_id"))
    else:
        await state.set_state(AdminUserStates.enter_phone)
        await callback.message.answer(t(detect_lang(callback.message), "enter_phone"))


@router.message(AdminUserStates.enter_tg_id)
async def admin_user_tg_id(message: Message, state: FSMContext):
    try:
        tg_id = int(message.text.strip())
    except ValueError:
        await message.answer(t(detect_lang(message), "enter_tg_id"))
        return
    await state.update_data(tg_id=tg_id)
    await state.set_state(AdminUserStates.enter_fullname)
    await message.answer(t(detect_lang(message), "enter_fullname"))


@router.message(AdminUserStates.enter_fullname)
async def admin_user_fullname(message: Message, state: FSMContext):
    await state.update_data(fullname=message.text.strip())
    await state.set_state(AdminUserStates.enter_phone)
    await message.answer(t(detect_lang(message), "enter_phone"))


@router.message(AdminUserStates.enter_phone)
async def admin_user_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(phone=phone)
    data = await state.get_data()
    if data.get("action") == "create":
        await state.set_state(AdminUserStates.enter_role)
        await message.answer(t(detect_lang(message), "enter_role"))
        return
    target = await db.get_user_by_phone(phone)
    if not target:
        await message.answer(t(detect_lang(message), "user_not_found"))
        await state.clear()
        return
    if data.get("action") == "block":
        await db.set_user_status(target["id"], USER_BLOCKED)
        await db.set_account_status(target["id"], USER_FROZEN)
        await db.log_action(message.from_user.id, "admin_block", f"user_id={target['id']}")
        await message.answer(t(detect_lang(message), "user_blocked"), reply_markup=get_back_keyboard(detect_lang(message)))
        await state.clear()
        return
    if data.get("action") == "role":
        await state.update_data(target_user_id=target["id"])
        await state.set_state(AdminUserStates.enter_role)
        await message.answer(t(detect_lang(message), "enter_role"))


@router.message(AdminUserStates.enter_role)
async def admin_user_role(message: Message, state: FSMContext):
    lang = detect_lang(message)
    role = message.text.strip().lower()
    if role not in [ROLE_CLIENT, ROLE_ADMIN, ROLE_OPERATOR, ROLE_RISK]:
        await message.answer(t(lang, "enter_role"))
        return
    data = await state.get_data()
    if data.get("action") == "create":
        existing = await db.get_user_by_tg(data["tg_id"])
        if existing:
            await message.answer(t(lang, "user_exists"), reply_markup=get_back_keyboard(lang))
            await state.clear()
            return
        await db.create_user(data["tg_id"], data["fullname"], data["phone"], role)
        user = await db.get_user_by_tg(data["tg_id"])
        await db.create_account(user["id"], "Main", "MRK", 0.0)
        await db.ensure_limits(user["id"])
        if user:
            await registry.sync_user_from_linar(user)
        await db.log_action(message.from_user.id, "admin_create_user", f"user_id={user['id']}")
        await message.answer(t(lang, "user_created"), reply_markup=get_back_keyboard(lang))
    else:
        await db.set_user_role(data["target_user_id"], role)
        await db.log_action(message.from_user.id, "admin_role_change", f"user_id={data['target_user_id']} role={role}")
        await message.answer(t(lang, "role_updated"), reply_markup=get_back_keyboard(lang))
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "cards_admin"))
async def admin_cards_menu(message: Message, state: FSMContext):
    user = await require_any_role(message, [ROLE_ADMIN])
    if not user:
        return
    await state.set_state(AdminCardStates.enter_phone)
    await message.answer(t(detect_lang(message), "enter_phone"))


@router.message(AdminCardStates.enter_phone)
async def admin_cards_phone(message: Message, state: FSMContext):
    target = await db.get_user_by_phone(message.text.strip())
    if not target:
        await message.answer(t(detect_lang(message), "user_not_found"))
        await state.clear()
        return
    lang = detect_lang(message)
    card = await db.get_card_by_user(target["id"])
    if not card:
        actions = [(t(lang, "issue"), f"admincard:issue:{target['id']}")]
        await message.answer(
            t(lang, "card_info", number="—", status="none"),
            reply_markup=inline_keyboard(actions, row_size=1),
        )
    else:
        actions = []
        if card["status"] == "blocked":
            actions.append((t(lang, "unblock"), f"admincard:unblock:{card['id']}"))
        else:
            actions.append((t(lang, "block"), f"admincard:block:{card['id']}"))
        await message.answer(
            t(lang, "card_info", number=format_card(card["card_number"]), status=card["status"]),
            reply_markup=inline_keyboard(actions, row_size=1),
        )
    await state.clear()


@router.callback_query(F.data.startswith("admincard:"))
async def admin_card_action(callback: CallbackQuery):
    parts = callback.data.split(":")
    action = parts[1]
    if action == "issue":
        user_id = int(parts[2])
        number = generate_card_number()
        await db.create_card(user_id, number)
        await db.log_action(callback.from_user.id, "admin_card_issue", f"user_id={user_id}")
        lang = detect_lang(callback.message)
        await callback.message.answer(t(lang, "card_issued", number=format_card(number)))
        target = await db.get_user_by_id(user_id)
        await notify_admin(
            callback.message.bot,
            t(
                lang,
                "notify_card_issue",
                name=target["fullname"] if target else f"user_id={user_id}",
                phone=target["phone"] if target else "-",
                card=format_card(number),
            ),
            callback.from_user.id,
        )
    else:
        card_id = int(parts[2])
        if action == "block":
            await db.update_card_status(card_id, "blocked", "admin")
            await db.log_action(callback.from_user.id, "admin_card_block", f"card_id={card_id}")
            await callback.message.answer(t(detect_lang(callback.message), "card_blocked"))
        if action == "unblock":
            await db.update_card_status(card_id, "active", None)
            await db.log_action(callback.from_user.id, "admin_card_unblock", f"card_id={card_id}")
            await callback.message.answer(t(detect_lang(callback.message), "card_unblocked"))
    await callback.answer()


@router.message(lambda m: is_menu_button(m.text, "limits"))
async def limits_menu(message: Message, state: FSMContext):
    user = await require_any_role(message, [ROLE_ADMIN, ROLE_RISK])
    if not user:
        return
    await state.set_state(LimitsStates.enter_phone)
    await message.answer(t(detect_lang(message), "enter_phone"))


@router.message(LimitsStates.enter_phone)
async def limits_phone(message: Message, state: FSMContext):
    target = await db.get_user_by_phone(message.text.strip())
    if not target:
        await message.answer(t(detect_lang(message), "user_not_found"))
        await state.clear()
        return
    await state.update_data(target_user_id=target["id"])
    await state.set_state(LimitsStates.enter_daily)
    await message.answer(t(detect_lang(message), "enter_daily_limit"))


@router.message(LimitsStates.enter_daily)
async def limits_daily(message: Message, state: FSMContext):
    try:
        daily = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(t(detect_lang(message), "enter_daily_limit"))
        return
    await state.update_data(daily=daily)
    await state.set_state(LimitsStates.enter_tx)
    await message.answer(t(detect_lang(message), "enter_tx_limit"))


@router.message(LimitsStates.enter_tx)
async def limits_tx(message: Message, state: FSMContext):
    try:
        tx_limit = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(t(detect_lang(message), "enter_tx_limit"))
        return
    data = await state.get_data()
    await db.set_limits(data["target_user_id"], data["daily"], tx_limit)
    await db.log_action(message.from_user.id, "limits_update", f"user_id={data['target_user_id']}")
    await message.answer(t(detect_lang(message), "limits_updated"), reply_markup=get_back_keyboard(detect_lang(message)))
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "adjust"))
async def adjust_menu(message: Message, state: FSMContext):
    user = await require_any_role(message, [ROLE_ADMIN])
    if not user:
        return
    await state.set_state(AdjustStates.enter_phone)
    await message.answer(t(detect_lang(message), "enter_phone"))


@router.message(AdjustStates.enter_phone)
async def adjust_phone(message: Message, state: FSMContext):
    target = await db.get_user_by_phone(message.text.strip())
    if not target:
        await message.answer(t(detect_lang(message), "user_not_found"))
        await state.clear()
        return
    accounts = await db.get_accounts(target["id"])
    actions = [(f"#{a['id']} {a['name']}", f"adjust:acc:{a['id']}") for a in accounts]
    await state.set_state(AdjustStates.choose_account)
    await message.answer(t(detect_lang(message), "select_account"), reply_markup=inline_keyboard(actions, row_size=1))


@router.callback_query(F.data.startswith("adjust:acc:"))
async def adjust_choose_account(callback: CallbackQuery, state: FSMContext):
    acc_id = int(callback.data.split(":")[2])
    await state.update_data(account_id=acc_id)
    await state.set_state(AdjustStates.enter_amount)
    await callback.answer()
    await callback.message.answer(t(detect_lang(callback.message), "enter_amount_signed"))


@router.message(AdjustStates.enter_amount)
async def adjust_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(t(detect_lang(message), "enter_amount_signed"))
        return
    data = await state.get_data()
    admin = await db.get_user_by_tg(message.from_user.id)
    actor_id = admin["id"] if admin else message.from_user.id
    account = await db.get_account(data["account_id"])
    target_user_id = account["user_id"] if account else actor_id
    await db.update_balance(data["account_id"], amount)
    await db.create_transaction(
        target_user_id,
        None,
        data["account_id"],
        abs(amount),
        0.0,
        "adjustment",
        "completed",
        "admin_adjust",
    )
    await db.log_action(actor_id, "admin_adjust", f"account_id={data['account_id']} amount={amount}")
    await message.answer(t(detect_lang(message), "balance_updated"), reply_markup=get_back_keyboard(detect_lang(message)))
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "reports"))
async def reports_menu(message: Message):
    user = await require_any_role(message, [ROLE_ADMIN])
    if not user:
        return
    transactions = await db.list_all_transactions()
    turnover = 0.0
    for tx in transactions:
        if tx.get("status") == "completed":
            turnover += float(tx.get("amount", 0.0)) + float(tx.get("fee", 0.0))
    loans = len(await db.list_credit_applications(status="approved"))
    frozen = len(await db.list_users(status="frozen"))
    await message.answer(
        t(detect_lang(message), "report_summary", turnover=turnover, loans=loans, frozen=frozen),
        reply_markup=get_back_keyboard(detect_lang(message)),
    )


@router.message(lambda m: is_menu_button(m.text, "logs"))
async def logs_menu(message: Message):
    user = await require_any_role(message, [ROLE_ADMIN, ROLE_RISK])
    if not user:
        return
    logs = await db.list_logs(20)
    lines = [f"#{row['id']} {row['action']} {row['details']}" for row in logs]
    await message.answer(t(detect_lang(message), "logs_header", list="\n".join(lines)), reply_markup=get_back_keyboard(detect_lang(message)))


@router.message(lambda m: is_menu_button(m.text, "tickets"))
async def tickets_menu(message: Message, state: FSMContext):
    operator = await require_any_role(message, [ROLE_OPERATOR, ROLE_ADMIN])
    if not operator:
        return
    await state.clear()
    lang = detect_lang(message)
    tickets = await db.list_open_tickets()
    if not tickets:
        await message.answer(t(lang, "ticket_empty"), reply_markup=get_back_keyboard(lang))
        return
    for ticket in tickets:
        user = await db.get_user_by_id(ticket["user_id"])
        if user:
            user_label = f"{user['fullname']} ({user['phone']})"
        else:
            user_label = f"user_id={ticket['user_id']}"
        text = f"#{ticket['id']} {user_label}\n{ticket['message']}"
        actions = [(t(lang, "reply"), f"ticket:reply:{ticket['id']}")]
        await message.answer(text, reply_markup=inline_keyboard(actions, row_size=1))


@router.callback_query(F.data.startswith("ticket:reply:"))
async def ticket_reply(callback: CallbackQuery, state: FSMContext):
    operator = await require_any_role_callback(callback, [ROLE_OPERATOR, ROLE_ADMIN])
    await callback.answer()
    if not operator:
        return
    ticket_id = int(callback.data.split(":")[2])
    await state.update_data(ticket_id=ticket_id)
    await state.set_state(TicketStates.enter_response)
    await callback.message.answer(t(detect_lang(callback.message), "enter_response"))


@router.message(TicketStates.enter_response)
async def ticket_response(message: Message, state: FSMContext):
    operator = await require_any_role(message, [ROLE_OPERATOR, ROLE_ADMIN])
    if not operator:
        await state.clear()
        return
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    if not ticket_id:
        await state.clear()
        await message.answer(t(detect_lang(message), "ticket_empty"), reply_markup=get_back_keyboard(detect_lang(message)))
        return
    await db.respond_ticket(ticket_id, operator["id"], message.text.strip())
    await db.log_action(operator["id"], "ticket_response", f"ticket_id={ticket_id}")
    await message.answer(t(detect_lang(message), "ticket_responded"), reply_markup=get_back_keyboard(detect_lang(message)))
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "profile"))
async def profile_menu(message: Message, state: FSMContext):
    operator = await require_any_role(message, [ROLE_OPERATOR, ROLE_ADMIN])
    if not operator:
        return
    await state.set_state(ProfileStates.enter_name)
    await message.answer(t(detect_lang(message), "enter_fullname_search"))


@router.message(ProfileStates.enter_name)
async def profile_phone(message: Message, state: FSMContext):
    operator = await require_any_role(message, [ROLE_OPERATOR, ROLE_ADMIN])
    if not operator:
        await state.clear()
        return
    query = message.text.strip()
    matches = await db.search_users_by_fullname(query)
    if not matches:
        await message.answer(t(detect_lang(message), "user_not_found"))
        return
    if len(matches) > 1:
        lines = [f"#{u['id']} {u['fullname']} ({u['phone'] or '-'})" for u in matches]
        await message.answer(t(detect_lang(message), "multiple_users", list="\n".join(lines)))
        return
    target = matches[0]
    phone = target["phone"] or "-"
    text = t(
        detect_lang(message),
        "profile",
        name=target["fullname"],
        role=target["role"],
        status=target["status"],
        phone=phone,
    )
    await message.answer(text, reply_markup=get_back_keyboard(detect_lang(message)))
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "freeze"))
async def freeze_menu(message: Message, state: FSMContext):
    officer = await require_any_role(message, [ROLE_RISK])
    if not officer:
        return
    await state.set_state(FreezeStates.enter_phone)
    await message.answer(t(detect_lang(message), "enter_phone"))


@router.message(FreezeStates.enter_phone)
async def freeze_phone(message: Message, state: FSMContext):
    officer = await require_any_role(message, [ROLE_RISK])
    if not officer:
        await state.clear()
        return
    target = await db.get_user_by_phone(message.text.strip())
    if not target:
        await message.answer(t(detect_lang(message), "user_not_found"))
        await state.clear()
        return
    await db.set_user_status(target["id"], USER_FROZEN)
    await db.set_account_status(target["id"], USER_FROZEN)
    await db.log_action(officer["id"], "risk_freeze", f"user_id={target['id']}")
    await message.answer(t(detect_lang(message), "freeze_done"), reply_markup=get_back_keyboard(detect_lang(message)))
    await state.clear()


@router.message(lambda m: is_menu_button(m.text, "credit_decisions"))
async def credit_decisions_menu(message: Message):
    officer = await require_any_role(message, [ROLE_RISK])
    if not officer:
        return
    lang = detect_lang(message)
    apps = await db.list_pending_credit_applications()
    if not apps:
        await message.answer(t(lang, "credit_pending_empty"), reply_markup=get_back_keyboard(lang))
        return
    for app in apps:
        user = await db.get_user_by_id(app["user_id"])
        if user:
            user_label = f"{user['fullname']} ({user['phone']})"
        else:
            user_label = f"user_id={app['user_id']}"
        text = (
            f"#{app['id']} {user_label}\n"
            f"Amount: {app['amount']:.2f} MRK\n"
            f"Term: {app['term_months']} months"
        )
        actions = [
            (t(lang, "approve"), f"credit:approve:{app['id']}"),
            (t(lang, "deny"), f"credit:deny:{app['id']}"),
        ]
        await message.answer(text, reply_markup=inline_keyboard(actions, row_size=2))


@router.callback_query(F.data.startswith("credit:"))
async def credit_decision(callback: CallbackQuery):
    officer = await require_any_role_callback(callback, [ROLE_RISK])
    await callback.answer()
    if not officer:
        return
    parts = callback.data.split(":")
    if len(parts) < 3:
        return
    action = parts[1]
    app_id = int(parts[2])
    status = "approved" if action == "approve" else "denied"
    await db.decide_credit_application(app_id, status, officer["id"], None)
    await db.log_action(officer["id"], f"credit_{status}", f"app_id={app_id}")
    lang = detect_lang(callback.message)
    await callback.message.answer(t(lang, "credit_decided"))
    decision_text = t(lang, "decision_approved") if status == "approved" else t(lang, "decision_denied")
    officer_name = officer["fullname"] or str(officer["tg_id"] or officer["id"])
    await notify_admin(
        callback.message.bot,
        t(
            lang,
            "notify_credit_decision",
            app_id=app_id,
            decision=decision_text,
            officer=officer_name,
        ),
        callback.from_user.id,
    )


@router.message()
async def unknown_message(message: Message, state: FSMContext):
    if await state.get_state():
        return
    await message.answer(
        t(detect_lang(message), "unknown"),
        reply_markup=get_back_keyboard(detect_lang(message)),
    )
