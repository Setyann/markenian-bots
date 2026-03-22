from aiogram import Router, F
from dotenv import load_dotenv
from os import getenv
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from handlers.tax_authority.keyboards import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from handlers.tax_authority import db

router = Router()

load_dotenv()
ADMIN_ID = getenv("ADMIN_ID")

user_languages = {}
TEXTS = {
    "start": {
        "en": "👋 Hello, {name}! I'm Tax Authority of Markenia 🏛.\nUse /help to see available commands, /pay_fine to pay your tax penalties or /view_penalties to view all your penalties.",
        "ru": "👋 Здравствуйте, {name}! Я Налоговая служба Маркении 🏛.\nИспользуйте /help, чтобы увидеть доступные команды, /pay_fines, чтобы оплатить штрафы или /view_penalties, чтобы посмотреть все свои штрафы.",
        "hy": "👋 Բարև, {name}! Ես Մարկենիայի Հարկային Ծառայություն եմ 🏛։\nՕգտագործեք /help՝ հասանելի հրամանները տեսնելու համար, /pay_fines՝ տուգանքները վճարելու համար կամ /view_penalties՝ տուգանքները դիտելու համար։"
    },
    "start_admin": {
        "en": "👋 Hello, Admin! I'm Tax Authority of Markenia 🏛.\nUse /help to see available commands or use the keyboard below to manage tax penalties.",
        "ru": "👋 Здравствуйте, Админ! Я Налоговая служба Маркении 🏛.\nИспользуйте /help, чтобы увидеть доступные команды или используйте клавиатуру ниже для управления штрафами.",
        "hy": "👋 Բարև, Admin! Ես Մարկենիայի Հարկային Ծառայություն եմ 🏛։\nՕգտագործեք /help՝ հասանելի հրամանները տեսնելու համար կամ օգտագործեք ստորև ներկայացված ստեղնաշարը՝ տուգանքները կառավարելու համար։"
    },
    "restart_bot": {
        "en": "🔄 Bot has been restarted. Use /start to begin again.",
        "ru": "🔄 Бот перезапущен. Используйте /start, чтобы начать заново.",
        "hy": "🔄 Բոտը վերագործարկվել է։ Օգտագործեք /start՝ նորից սկսելու համար։"
    },
    "help": {
        "en": "Commands available:\n/start - Restart the bot\n/help - Show this help message\n/pay_fine - Pay tax penalties\n/view_penalties - View all your penalties\n/info - Show information about the tax authority\n/lang - Change language",
        "ru": "Доступные команды:\n/start - Перезапустить бота\n/help - Показать это сообщение помощи\n/pay_fine - Оплатить штрафы\n/view_penalties - Просмотреть все свои штрафы\n/info - Показать информацию о налоговой службе\n/lang - Изменить язык",
        "hy": "Հասանելի հրամաններ:\n/start - Վերագործարկել բոտը\n/help - Ցույց տալ այս օգնության տեքստը\n/pay_fine - Վճարել տուգանքները\n/view_penalties - Դիտել ձեր բոլոր տուգանքները\n/info - Ցույց տալ հարկային ծառայության տեղեկությունը՝\n/lang - Փոխել լեզուն",
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
    "pay_fine": {
        "en": "To pay your tax penalties, enter your name, phone number and tax penalty ID:",
        "ru": "Чтобы оплатить штрафы, введите ваше имя, номер телефона и ID штрафа:",
        "hy": "Ձեր տուգանքները վճարելու համար, մուտքագրեք ձեր անունը, հեռախոսահամարը և տուգանքի ID-ն։",
    },
    "info": {
        "en": "*🏛 Tax Service of Markenia*\n\n"
            "The Tax Service of Markenia is a state authority responsible for *tax collection*, *financial oversight*, and *enforcement of tax legislation* within Markenia; it was officially established on *January 28, 2026*, and all taxpayers without exception are required to pay a *uniform tax of 9%*, ensuring stable *budget revenues and the financial sustainability* of the state.\n\n"
            "*💼 Responsibilities*\n"
            "- 💰 Collection of taxes and mandatory payments  \n"
            "- 📑 Registration of taxpayers  \n"
            "- 🔍 Monitoring and auditing of tax reports  \n"
            "- ⚖️ Prevention of tax violations  \n"
            "- 🤝 Consultations for citizens and businesses  \n\n"
            "*👤 Who pays taxes*\n"
            "- Individuals  \n"
            "- Individual entrepreneurs  \n"
            "- Legal entities and organizations  \n\n"
            "*🧮 Main taxes*\n"
            "- Personal income tax  \n"
            "- Corporate income tax  \n"
            "- Property tax  \n"
            "- VAT  \n"
            "- Government fees  \n\n"
            "*⏱ Responsibility*\n"
            "Taxes must be paid *on time*.  \n"
            "Violations result in *fines and legal sanctions* under the laws of Markenia.\n\n"
            "_Paying taxes means supporting the stability and development of the state._",
        "ru": "*🏛 Налоговая служба Маркении*\n\n"
            "Налоговая служба Маркении — государственный орган, отвечающий за *сбор налогов*, *контроль финансовой деятельности* и *соблюдение налогового законодательства* на территории Маркении; служба была официально учреждена *28 января 2026 года*, а все налогоплательщики без исключения обязаны уплачивать *единый налог в размере 9%*, обеспечивая стабильное наполнение бюджета и финансовую устойчивость государства.\n\n"
            "*💼 Что делает служба*\n"
            "- 💰 Сбор налогов и обязательных платежей  \n"
            "- 📑 Учёт налогоплательщиков  \n"
            "- 🔍 Контроль и проверки отчётности  \n"
            "- ⚖️ Пресечение налоговых нарушений  \n"
            "- 🤝 Консультации для граждан и бизнеса  \n\n"
            "*👤 Кто платит налоги*\n"
            "- Физические лица  \n"
            "- Индивидуальные предприниматели  \n"
            "- Юридические лица и организации  \n\n"
            "*🧮 Основные налоги*\n"
            "- Подоходный налог  \n"
            "- Налог на прибыль  \n"
            "- Налог на имущество  \n"
            "- НДС  \n"
            "- Государственные сборы  \n\n"
            "*⏱ Ответственность*\n"
            "Налоги должны уплачиваться *в срок*.  \n"
            "Нарушения влекут *штрафы и санкции* по закону Маркении.\n\n"
            "_Платить налоги — значит поддерживать стабильность и развитие государства._",
        "hy": "*🏛 Մարկենիայի հարկային ծառայություն*\n\n"
            "Մարկենիայի հարկային ծառայությունը պետական մարմին է, որը պատասխանատու է *հարկերի հավաքագրման*, *ֆինանսական վերահսկողության* և *հարկային օրենսդրության պահպանման համար* Մարկենիայի տարածքում․ ծառայությունը պաշտոնապես *հիմնադրվել է 2026 թվականի հունվարի 28-ին*, և բոլոր հարկատուները առանց բացառության պարտավոր են վճարել *9% չափով միասնական հարկ*, ապահովելով պետական *բյուջեի կայուն համալրումը և երկրի ֆինանսական կայունությունը*։\n\n"
            "*💼 Ծառայության գործառույթները*\n"
            "- 💰 Հարկերի և պարտադիր վճարների հավաքագրում  \n"
            "- 📑 Հարկ վճարողների հաշվառում  \n"
            "- 🔍 Հաշվետվությունների վերահսկում և ստուգում  \n"
            "- ⚖️ Հարկային խախտումների կանխարգելում  \n"
            "- 🤝 Քաղաքացիների և բիզնեսի խորհրդատվություն  \n\n"
            "*👤 Ովքեր են վճարում հարկեր*\n"
            "- Ֆիզիկական անձինք  \n"
            "- Անհատ ձեռնարկատերեր  \n"
            "- Իրավաբանական անձինք և կազմակերպություններ  \n\n"
            "*🧮 Հիմնական հարկերը*\n"
            "- Եկամտահարկ  \n"
            "- Շահութահարկ  \n"
            "- Գույքահարկ  \n"
            "- ԱԱՀ  \n"
            "- Պետական տուրքեր  \n\n"
            "*⏱ Պատասխանատվություն*\n"
            "Հարկերը պետք է վճարվեն *ժամանակին*։  \n"
            "Խախտումները ենթադրում են *տուգանքներ և իրավական պատժամիջոցներ* Մարկենիայի օրենքների համաձայն։\n\n"
            "_Հարկերի վճարումը նպաստում է պետության կայուն զարգացմանը։_",
    },
    "admin_info": {
        "en": "*🏛 Tax Service of Markenia - Admin Info*\n\n"
            "As an admin of the Tax Authority bot, you have access to special commands to manage tax penalties and view taxpayer information. Use the keyboard below to issue tax penalties or view all taxpayers in the database.\n\n"
            "_Ensure proper management of tax penalties to maintain compliance with Markenia's tax laws._",
        "ru": "*🏛 Налоговая служба Маркении - Информация для админа*\n\n"
            "Как администратор бота Налоговой службы, у вас есть доступ к специальным командам для управления штрафами и просмотра информации о налогоплательщиках. Используйте клавиатуру ниже, чтобы выдавать штрафы или просматривать всех налогоплательщиков в базе данных.\n\n"
            "_Обеспечьте правильное управление штрафами для соблюдения налогового законодательства Маркении._",
        "hy": "*🏛 Մարկենիայի հարկային ծառայություն - Տեղեկություններ ադմինիստրատորի համար*\n\n"
            "Որպես Հարկային ծառայության բոտի ադմինիստրատոր՝ դուք ունեք հատուկ հրամանների հասանելիություն՝ տուգանքները կառավարելու և հարկատուների տեղեկությունները դիտելու համար։ Օգտագործեք ստորև ներկայացված ստեղնաշարը՝ հարկային տուգանքներ նշանակելու կամ տվյալների բազայում բոլոր հարկատուներին դիտելու համար։\n\n"
            "_Համոզվեք, որ ճիշտ եք կառավարում հարկային տուգանքները՝ ապահովելու Մարկենիայի հարկային օրենքների պահպանումը։_"
    },
    "issue_tax_penalty_start": {
        "en": "Enter the name of the taxpayer:",
        "ru": "Введите имя налогооблагаемого лица:",
        "hy": "Մուտքագրեք հարկատուի անունը։",
    },
    "enter_amount": {
        "en": "Enter the penalty amount:",
        "ru": "Введите сумму штрафа:",
        "hy": "Մուտքագրեք տուգանքի գումարը։"
    },
    "enter_reason": {
        "en": "Enter the reason for the penalty:",
        "ru": "Введите причину штрафа:",
        "hy": "Մուտքագրեք տուգանքի պատճառը։"
    },
    "confirm_penalty": {
        "en": "Confirm issuing the penalty:\nName: {name}\nAmount: {amount}\nReason: {reason}\nType 'Yes' to confirm or 'No' to cancel.",
        "ru": "Подтвердите выдачу штрафа:\nИмя: {name}\nСумма: {amount}\nПричина: {reason}\nНапишите 'Да' для подтверждения или 'Нет' для отмены.",
        "hy": "Հաստատեք տուգանքը:\nԱնունը: {name}\nԳումարը: {amount}\nՊատճառը: {reason}\nՄուտքագրեք 'Այո' հաստատելու համար կամ 'Ոչ' չեղարկելու համար։"
    },
    "taxpayer_not_found": {
        "en": "❌ Taxpayer not found in the database.",
        "ru": "❌ Налогоплательщик не найден в базе.",
        "hy": "❌ Հարկատուն չի գտնվել տվյալների բազայում։"
    },
    "penalty_issued": {
        "en": "✅ Tax penalty issued successfully.",
        "ru": "✅ Штраф успешно выдан.",
        "hy": "✅ Տուգանքը հաջողությամբ նշանակվել է։"
    },
    "penalty_canceled": {
        "en": "❌ Tax penalty issuance canceled.",
        "ru": "❌ Выдача штрафа отменена.",
        "hy": "❌ Տուգանքի նշանակումը չեղարկվել է։"
    },
    "add_taxpayer_name": {
        "en": "Enter taxpayer full name. You can also cancel adding by /cancel_adding_taxpayer:",
        "ru": "Введите полное имя налогоплательщика. Вы также можете отменить добавление налогоплательщика командой /cancel_adding_taxpayer:",
        "hy": "Enter taxpayer full name. You can also cancel adding by /cancel_adding_taxpayer:",
    },
    "add_taxpayer_phone": {
        "en": "Enter taxpayer phone number:",
        "ru": "Введите номер телефона налогоплательщика:",
        "hy": "Enter taxpayer phone number:",
    },
    "taxpayer_added": {
        "en": "✅ Taxpayer added.",
        "ru": "✅ Налогоплательщик добавлен.",
        "hy": "✅ Taxpayer added.",
    },
    "remove_taxpayer_prompt": {
        "en": "Enter taxpayer name or phone number to remove. You can also cancel removing by /cancel_removing_taxpayer:",
        "ru": "Введите имя или телефон налогоплательщика для удаления. Вы также можете отменить удаление налогоплательщика командой /cancel_removing_taxpayer:",
        "hy": "Enter taxpayer name or phone number to remove. You can also cancel removing by /cancel_removing_taxpayer:",
    },
    "taxpayer_removed": {
        "en": "✅ Taxpayer removed.",
        "ru": "✅ Налогоплательщик удален.",
        "hy": "✅ Taxpayer removed.",
    },
    "taxpayer_remove_not_found": {
        "en": "❌ Taxpayer not found in the database.",
        "ru": "❌ Налогоплательщик не найден в базе.",
        "hy": "❌ Taxpayer not found in the database.",
    },
    "view_all_taxpayers": {
        "en": "{id}. {name}, {phone_number}\n",
        "ru": "{id}. {name}, {phone_number}\n",
        "hy": "{id}. {name}, {phone_number}\n"
    },
    "no_taxpayers": {
        "en": "No taxpayers found in the database.",
        "ru": "Налогоплательщики не найдены в базе данных.",
        "hy": "Տվյալների բազայում հարկատուներ չեն գտնվել։"
    },
    "view_all_penalties": {
        "en": "{id}. Name: {name}\nAmount: {amount} MRK\nReason: {reason}\n",
        "ru": "{id}. Имя: {name}\nСумма: {amount} MRK\nПричина: {reason}\n",
        "hy": "{id}. Անունը: {name}\nԳումարը: {amount} MRK\nՊատճառը: {reason}\n"
    },
    "no_penalties_admin": {
        "en": "No penalties found in the database.",
        "ru": "Штрафы не найдены в базе данных.",
        "hy": "Տվյալների բազայում տուգանքներ չեն գտնվել։"
    },
    "view_penalties": {
        "en": "Viewing your penalties:",
        "ru": "Просмотр ваших штрафов:",
        "hy": "Ձեր տուգանքները դիտելու համար՝"
    },
    "no_penalties": {
        "en": "You have no penalties.",
        "ru": "У вас нет штрафов.",
        "hy": "Դուք չունեք տուգանքներ։"
    },
    "main_menu": {
        "en": "🏠 Main Menu",
        "ru": "🏠 Главное меню",
        "hy": "🏠 Գլխավոր մենյու"
    },
    "cancel_adding_taxpayer": {
        "en": "❌ Taxpayer add cancelled",
        "ru": "❌ Добавление налогоплательщика отменено",
        "hy": "❌ Taxpayer add cancelled"
    },
    "cancel_removing_taxpayer": {
        "en": "❌ Taxpayer removing cancelled",
        "ru": "❌ Удаление налогоплательщика отменено",
        "hy": "❌ Taxpayer removing cancelled"
    },
    "unknown_command": {
        "en": "Unrecognized command. Use /help to see available commands.",
        "ru": "Неизвестная команда. Используйте /help, чтобы увидеть доступные команды.",
        "hy": "Չճանաչված հրաման։ Օգտագործեք /help՝ հասանելի հրամանները տեսնելու համար։"
    }
}

@router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = lang

    await callback.answer()
    await callback.message.edit_text(
        TEXTS["lang_changed"][lang],
        reply_markup=get_menu_keyboard()
    )

# --- Определяем состояния FSM для выдачи штрафа ---
class TaxPenaltyStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_amount = State()
    waiting_for_reason = State()
    confirmation = State()


class AdminUserStates(StatesGroup):
    add_fullname = State()
    add_phone = State()
    remove_query = State()

# --- Проверка наличия налогоплательщика ---
async def taxpayer_exists(name: str) -> bool:
    return await db.has_taxpayer(name)

# --- Сохранение штрафа ---
async def save_penalty(name: str, amount: float, reason: str, created_by: int | None = None):
    await db.create_penalty(name, amount, reason, created_by)

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

@router.message(F.text.contains("🔄 Restart Bot"))
async def restart_bot(message: Message):
    if str(message.from_user.id) != ADMIN_ID:
        return  # Только для админа
    lang = detect_lang(message)
    user_languages.pop(message.from_user.id, None)
    await message.answer(TEXTS["restart_bot"][lang])

@router.message(Command("start"))
async def start(message: Message):
    await db.init_db()
    lang = detect_lang(message)
    user_languages.setdefault(message.from_user.id, lang)
    if str(message.from_user.id) == ADMIN_ID:
        await message.answer(
            TEXTS["start_admin"][lang].format(name=message.from_user.full_name),
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            TEXTS["start"][lang].format(name=message.from_user.full_name),
            reply_markup=get_user_menu_keyboard()
        )

@router.message(F.text.contains("🏠 Go to Main Menu"))
async def main_menu(message: Message):
    if str(message.from_user.id) != ADMIN_ID:
        return  # Только для админа
    lang = detect_lang(message)
    await message.answer(
        TEXTS["main_menu"][lang],
        reply_markup=get_admin_keyboard()
    )

@router.message(Command("help"))
async def help(message: Message):
    lang = detect_lang(message)
    if str(message.from_user.id) != ADMIN_ID:
        await message.answer(TEXTS["help"][lang])
    else:
        await message.answer(
            TEXTS["help"][lang] + "\n\nAdmin Commands:\n📜 Issue Tax Penalty\n📄 View All Taxpayers\n➕ Add User\n➖ Remove User\n📋 View All Penalties",
            reply_markup=get_admin_keyboard()
        )

@router.message(F.text.contains("💳 Pay Tax Penalties"))
@router.message(Command("pay_fine"))
async def pay_fine(message: Message):
    lang = detect_lang(message)
    await message.answer(TEXTS["pay_fine"][lang])

@router.message(Command("info"))
async def info(message: Message):
    lang = detect_lang(message)
    if str(message.from_user.id) != ADMIN_ID:
        await message.answer(TEXTS["info"][lang], parse_mode="Markdown", reply_markup=get_user_menu_keyboard())
    else:
        await message.answer(
            TEXTS["admin_info"][lang] + "\n\n" + TEXTS["info"][lang],
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown"
        )
@router.message(Command("lang"))
async def lang(message: Message):
    lang = detect_lang(message)
    await message.answer(
        TEXTS["lang_select"][lang],
        reply_markup=get_language_keyboard()
    )

# --- Старт выдачи штрафа ---
@router.message(F.text.contains("📜 Issue Tax Penalty"))
async def issue_tax_penalty_start(message: Message, state: FSMContext):
    if str(message.from_user.id) != ADMIN_ID:
        return  # Только для админа
    lang = detect_lang(message)
    
    await message.answer(
        TEXTS["issue_tax_penalty_start"][lang],
        reply_markup=ReplyKeyboardRemove()
    )
    
    await state.set_state(TaxPenaltyStates.waiting_for_name)
    await state.update_data(penalty={})
    
@router.message(Command("cancel"))
async def cancel_penalty(message: Message, state: FSMContext):
    await state.clear()
    lang = detect_lang(message)
    await message.answer(TEXTS["penalty_canceled"][lang], reply_markup=get_menu_keyboard())

# --- Ввод имени налогоплательщика ---
@router.message(TaxPenaltyStates.waiting_for_name)
async def penalty_name(message: Message, state: FSMContext):
    lang = detect_lang(message)
    name = message.text.strip()

    if not await taxpayer_exists(name):
        await message.answer(TEXTS["taxpayer_not_found"][lang])
        await state.clear()
        return

    data = await state.get_data()
    data['penalty']['name'] = name
    await state.update_data(data)

    await message.answer(TEXTS["enter_amount"][lang])
    await state.set_state(TaxPenaltyStates.waiting_for_amount)
    
# --- Ввод суммы штрафа ---
@router.message(TaxPenaltyStates.waiting_for_amount)
async def penalty_amount(message: Message, state: FSMContext):
    lang = detect_lang(message)
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer(TEXTS["enter_amount"][lang])
        return

    data = await state.get_data()
    data['penalty']['amount'] = amount
    await state.update_data(data)

    await message.answer(TEXTS["enter_reason"][lang])
    await state.set_state(TaxPenaltyStates.waiting_for_reason)
    
# --- Ввод причины штрафа ---
@router.message(TaxPenaltyStates.waiting_for_reason)
async def penalty_reason(message: Message, state: FSMContext):
    lang = detect_lang(message)
    reason = message.text.strip()

    data = await state.get_data()
    data['penalty']['reason'] = reason
    await state.update_data(data)

    penalty = data['penalty']
    await message.answer(
        TEXTS["confirm_penalty"][lang].format(
            name=penalty['name'],
            amount=penalty['amount'],
            reason=penalty['reason']
        )
    )
    await state.set_state(TaxPenaltyStates.confirmation)
    
# --- Подтверждение ---
@router.message(TaxPenaltyStates.confirmation)
async def penalty_confirmation(message: Message, state: FSMContext):
    lang = detect_lang(message) 
    text = message.text.lower() # Приводим к нижнему регистру для сравнения
    data = await state.get_data() 
    penalty = data['penalty'] 

    if text in ["yes", "да", "այո"]:
        await save_penalty(penalty['name'], penalty['amount'], penalty['reason'], message.from_user.id)
        await message.answer(TEXTS["penalty_issued"][lang], reply_markup=get_menu_keyboard())
    else:
        await message.answer(TEXTS["penalty_canceled"][lang], reply_markup=get_menu_keyboard())

    await state.clear()

@router.message(F.text.contains("📄 View All Taxpayers"))
async def view_all_taxpayers(message: Message, state: FSMContext):
    if str(message.from_user.id) != ADMIN_ID:
        return  # Только для админа
    lang = detect_lang(message)
    
    taxpayers = await db.list_taxpayers()
    if not taxpayers:
        await message.answer(TEXTS["no_taxpayers"][lang], reply_markup=get_user_keyboard())
        return

    # Формируем текст для всех налогоплательщиков
    users_text = ""
    for idx, taxpayer in enumerate(taxpayers, start=1):
        users_text += TEXTS["view_all_taxpayers"][lang].format(
            id=taxpayer.get("id", idx),
            name=taxpayer.get("fullname", "N/A"),
            phone_number=taxpayer.get("phone") or "N/A"
        )

    await message.answer(users_text, reply_markup=get_user_keyboard())

@router.message(F.text.contains("📋 View All Penalties"))
async def view_all_penalties(message: Message, state: FSMContext):
    if str(message.from_user.id) != ADMIN_ID:
        return  # Только для админа
    lang = detect_lang(message)
    
    penalties = await db.list_penalties()
    if not penalties:
        await message.answer(TEXTS["no_penalties"][lang], reply_markup=get_menu_keyboard())
        return

    # Формируем текст для всех штрафов
    penalties_text = ""
    for idx, penalty in enumerate(penalties, start=1):
        penalties_text += TEXTS["view_all_penalties"][lang].format(
            id=penalty.get("id", idx),
            name=penalty.get("name", "N/A"),
            amount=penalty.get("amount", 0),
            reason=penalty.get("reason", "")
        )

    await message.answer(penalties_text, reply_markup=get_menu_keyboard())
    
@router.message(F.text.contains("📋 View My Penalties"))
@router.message(Command("view_penalties"))
async def view_penalties(message: Message):
    lang = detect_lang(message)
    user_penalties = await db.list_penalties_by_name(message.from_user.full_name)
    if not user_penalties:
        await message.answer(TEXTS["no_penalties"][lang])
        return
    penalties_text = TEXTS["view_penalties"][lang] + "\n"
    for idx, penalty in enumerate(user_penalties, start=1):
        penalties_text += TEXTS["view_all_penalties"][lang].format(
            id=penalty.get("id", idx),
            name=penalty.get("name", "N/A"),
            amount=penalty.get("amount", 0),
            reason=penalty.get("reason", "")
        )  
    await message.answer(penalties_text)

@router.message(F.text.contains("➕ Add User"))
async def add_user(message: Message, state: FSMContext):
    if str(message.from_user.id) != ADMIN_ID:
        return  # Только для админа
    lang = detect_lang(message)
    await state.clear()
    await state.set_state(AdminUserStates.add_fullname)
    await message.answer(TEXTS["add_taxpayer_name"][lang], reply_markup=ReplyKeyboardRemove())

@router.message(Command("cancel_adding_taxpayer"))
async def cancel_adding_taxpayer(message: Message):
    lang = detect_lang(message)
    await state.clear()
    await message.answer(
        TEXTS["cancel_adding_taxpayer"][lang],
        reply_markup=get_menu_keyboard()
    )

@router.message(AdminUserStates.add_fullname)
async def add_user_fullname(message: Message, state: FSMContext):
    lang = detect_lang(message)
    fullname = message.text.strip()
    if len(fullname) < 2:
        await message.answer(TEXTS["add_taxpayer_name"][lang])
        return
    await state.update_data(fullname=fullname)
    await state.set_state(AdminUserStates.add_phone)
    await message.answer(TEXTS["add_taxpayer_phone"][lang])


@router.message(AdminUserStates.add_phone)
async def add_user_phone(message: Message, state: FSMContext):
    lang = detect_lang(message)
    phone_raw = message.text.strip()
    phone_norm = "".join(ch for ch in phone_raw if ch.isdigit())
    if len(phone_norm) < 8 or len(phone_norm) > 15:
        await message.answer(TEXTS["add_taxpayer_phone"][lang])
        return
    data = await state.get_data()
    await db.upsert_taxpayer(
        tg_id=None,
        fullname=data.get("fullname", ""),
        phone=phone_raw,
        source="manual_admin",
        linar_user_id=None,
    )
    await message.answer(TEXTS["taxpayer_added"][lang], reply_markup=get_admin_keyboard())
    await state.clear()


@router.message(F.text.contains("➖ Remove User"))
async def remove_user(message: Message, state: FSMContext):
    if str(message.from_user.id) != ADMIN_ID:
        return  # Только для админа
    lang = detect_lang(message)
    await state.clear()
    await state.set_state(AdminUserStates.remove_query)
    await message.answer(TEXTS["remove_taxpayer_prompt"][lang], reply_markup=ReplyKeyboardRemove())

@router.message(Command("cancel_removing_taxpayer"))
async def cancel_removing_taxpayer(message: Message):
    lang = detect_lang(message)
    await state.clear()
    await message.answer(
        TEXTS["cancel_removing_taxpayer"][lang],
        reply_markup=get_menu_keyboard()
    )

@router.message(AdminUserStates.remove_query)
async def remove_user_query(message: Message, state: FSMContext):
    lang = detect_lang(message)
    query = message.text.strip()
    if not query:
        await message.answer(TEXTS["remove_taxpayer_prompt"][lang])
        return
    removed = await db.delete_taxpayer(query)
    if not removed:
        await message.answer(TEXTS["taxpayer_remove_not_found"][lang], reply_markup=get_admin_keyboard())
        await state.clear()
        return
    await message.answer(TEXTS["taxpayer_removed"][lang], reply_markup=get_admin_keyboard())
    await state.clear()

@router.message()
async def unknown_command(message: Message):
    lang = detect_lang(message)
    await message.answer(
        TEXTS["unknown_command"][lang]
    )
