import logging
import os
import asyncio
from aiohttp import web

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================================================
# КОНФИГУРАЦИЯ
# =========================================================

TOKEN = os.environ.get("BOT_TOKEN", "8873232031:AAFu5RAgsCa0YvrNxUuQlZniatQ2_d71NeI")
PORT = int(os.environ.get("PORT", 8080))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================================================
# ССЫЛКИ (URL)
# =========================================================

URL_PROJECTS_CHANNEL = "https://t.me/rrnftstore"
URL_PROJECTS_BOT = "https://t.me/RRnftStoreBot"

URL_CONTACT_NAZA = "https://t.me/wmixz"
URL_CONTACT_MANAGER = "https://t.me/RrManag"
URL_CONTACT_GARANT = "https://t.me/GARANTwmixz"

URL_REVIEWS = "https://t.me/RrNazaReviews"

URL_ADS_CONTACT = "https://t.me/wmixz"

# =========================================================
# ПОДПИСИ КНОПОК И ТЕКСТЫ
# =========================================================

BTN_ABOUT = "👤 Обо мне"
BTN_PROJECTS = "📁 Проекты"
BTN_CONTACTS = "✉️ Контакты"
BTN_REVIEWS = "⭐️ Отзывы"
BTN_ADS = "📢 Реклама"

BTN_PROJECTS_CHANNEL = "📢 RR STORE | NFT"
BTN_PROJECTS_BOT = "🤖 RR | STORE | BOT"

BTN_CONTACT_NAZA = "👤 RR | Naza"
BTN_CONTACT_MANAGER = "👨‍💻 RR | Manager"
BTN_CONTACT_GARANT = "🛡 RR | Garant"

BTN_REVIEWS_LINK = "⭐️ Смотреть отзывы"
BTN_ADS_LINK = "📩 Предложить"

BTN_BACK = "⬅️ Назад"
CALLBACK_BACK = "back_to_main"

WELCOME_TEXT = "Добро пожаловать! 👋\n\nВыберите интересующий раздел с помощью кнопок меню ниже 👇"
BACK_TO_MAIN_TEXT = "🏠 Главное меню\n\nВыберите раздел с помощью кнопок меню ниже 👇"

TEXT_ABOUT = (
    "<b>Приветствую, ребята!</b>\n\n"
    "Думаю, все, кто сюда зашёл, уже в курсе, <b>кто я и чем занимаюсь,</b> "
    "так что не будем вдаваться в подробности.\n\n"
    "Здесь собрал всё самое основное: <b>мои проекты, контакты команды, "
    "отзывы и информацию по рекламе.</b>"
)

TEXT_PROJECTS = (
    "<b>RR STORE | NFT — наш Telegram-канал,</b> где публикуем "
    "<b>все новости, новые поступления</b> и проводим различные <b>розыгрыши!</b>\n\n"
    "<b>RR | STORE | BOT — удобный бот-каталог, в котором можно посмотреть "
    "и приобрести наши товары: Stars, Premium, NFT-подарки</b> и многое другое."
)

TEXT_CONTACTS = (
    "<b>RR | Naza — владелец проектов.</b> Первый, к кому вы можете "
    "обратиться, если хотите что-то <b>приобрести,</b> предложить "
    "<b>сотрудничество</b> или просто что-то узнать.\n\n"
    "<b>RR | Manager — менеджер и мой помощник.</b> Если я не могу "
    "ответить, можете обратиться к нему — поможет с покупкой и другими вопросами.\n\n"
    "<b>RR | Garant — гарант ваших сделок на сумму до 3000 грн.</b>\n"
    "Стоимость услуги — <b>5% от суммы сделки.</b>\n"
    "Если сумма сделки до <b>500 грн</b> — фиксировано <b>25 грн.</b>\n\n"
    "По всем остальным вопросам также можете обращаться к <b>нашей команде</b> — постараемся помочь!"
)

TEXT_REVIEWS = (
    "Здесь собраны <b>отзывы наших клиентов</b> о покупках и работе с <b>RR | STORE.</b>\n\n"
    "Нам важно не просто продать товар, а сделать так, чтобы <b>клиент остался довольный и вернулся снова.</b>\n\n"
    "Уже собрали <b>1000+ отзывов и продолжаем двигаться дальше.</b>\n\n"
    "<b>Спасибо каждому, кто выбирает RR | STORE!</b>"
)

TEXT_ADS = (
    "По вопросам <b>рекламы, взаимопиара и коммерческого сотрудничества</b> "
    "обращайтесь <b>строго ко мне</b> в личные сообщения.\n\n"
    "Рассматриваю разные варианты сотрудничества:\n\n"
    "<b>— рекламные посты</b>\n"
    "<b>— размещение в каналах</b>\n"
    "<b>— взаимопиар</b>\n"
    "<b>— долгосрочное сотрудничество</b>\n"
    "<b>— индивидуальные предложения</b>\n\n"
    "Есть идея или предложение? <b>Пишите — обсудим.</b>"
)

# =========================================================
# КЛАВИАТУРЫ
# =========================================================

def main_reply_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(BTN_ABOUT), KeyboardButton(BTN_PROJECTS)],
        [KeyboardButton(BTN_CONTACTS), KeyboardButton(BTN_REVIEWS)],
        [KeyboardButton(BTN_ADS)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def projects_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(BTN_PROJECTS_CHANNEL, url=URL_PROJECTS_CHANNEL)],
        [InlineKeyboardButton(BTN_PROJECTS_BOT, url=URL_PROJECTS_BOT)],
        [InlineKeyboardButton(BTN_BACK, callback_data=CALLBACK_BACK)],
    ]
    return InlineKeyboardMarkup(keyboard)

def contacts_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(BTN_CONTACT_NAZA, url=URL_CONTACT_NAZA)],
        [InlineKeyboardButton(BTN_CONTACT_MANAGER, url=URL_CONTACT_MANAGER)],
        [InlineKeyboardButton(BTN_CONTACT_GARANT, url=URL_CONTACT_GARANT)],
        [InlineKeyboardButton(BTN_BACK, callback_data=CALLBACK_BACK)],
    ]
    return InlineKeyboardMarkup(keyboard)

def reviews_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(BTN_REVIEWS_LINK, url=URL_REVIEWS)],
        [InlineKeyboardButton(BTN_BACK, callback_data=CALLBACK_BACK)],
    ]
    return InlineKeyboardMarkup(keyboard)

def ads_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(BTN_ADS_LINK, url=URL_ADS_CONTACT)],
        [InlineKeyboardButton(BTN_BACK, callback_data=CALLBACK_BACK)],
    ]
    return InlineKeyboardMarkup(keyboard)

# =========================================================
# ОБРАБОТЧИКИ БОТА
# =========================================================

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text(
            WELCOME_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=main_reply_keyboard(),
        )
    except TelegramError as exc:
        logger.error("Ошибка при отправке приветствия: %s", exc)

async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text(TEXT_ABOUT, parse_mode=ParseMode.HTML)
    except TelegramError as exc:
        logger.error("Ошибка в разделе 'Обо мне': %s", exc)

async def projects_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text(
            TEXT_PROJECTS,
            parse_mode=ParseMode.HTML,
            reply_markup=projects_inline_keyboard(),
        )
    except TelegramError as exc:
        logger.error("Ошибка в разделе 'Проекты': %s", exc)

async def contacts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text(
            TEXT_CONTACTS,
            parse_mode=ParseMode.HTML,
            reply_markup=contacts_inline_keyboard(),
        )
    except TelegramError as exc:
        logger.error("Ошибка в разделе 'Контакты': %s", exc)

async def reviews_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text(
            TEXT_REVIEWS,
            parse_mode=ParseMode.HTML,
            reply_markup=reviews_inline_keyboard(),
        )
    except TelegramError as exc:
        logger.error("Ошибка в разделе 'Отзывы': %s", exc)

async def ads_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text(
            TEXT_ADS,
            parse_mode=ParseMode.HTML,
            reply_markup=ads_inline_keyboard(),
        )
    except TelegramError as exc:
        logger.error("Ошибка в разделе 'Реклама': %s", exc)

async def back_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    try:
        await query.answer()
    except TelegramError as exc:
        logger.warning("Ошибка при answer callback_query: %s", exc)

    try:
        await query.edit_message_text(
            BACK_TO_MAIN_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=None,
        )
    except TelegramError as exc:
        logger.warning("Ошибка при возврате в главное меню: %s", exc)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Исключение при обработке апдейта: %s", context.error)

# =========================================================
# ВЕБ-СЕРВЕР ДЛЯ RENDER / UPTIMEROBOT
# =========================================================

async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info("Веб-сервер запущен на порту %s", PORT)

# =========================================================
# ЗАПУСК ВСЕГО ПРИЛОЖЕНИЯ
# =========================================================

async def main_async():
    if not TOKEN or TOKEN == "PUT_YOUR_TOKEN_HERE":
        raise RuntimeError("Не задан токен бота.")

    # Запускаем веб-сервер для Render
    await start_web_server()

    # Настраиваем и запускаем Telegram бота
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(MessageHandler(filters.Regex(f"^{BTN_ABOUT}$"), about_handler))
    application.add_handler(MessageHandler(filters.Regex(f"^{BTN_PROJECTS}$"), projects_handler))
    application.add_handler(MessageHandler(filters.Regex(f"^{BTN_CONTACTS}$"), contacts_handler))
    application.add_handler(MessageHandler(filters.Regex(f"^{BTN_REVIEWS}$"), reviews_handler))
    application.add_handler(MessageHandler(filters.Regex(f"^{BTN_ADS}$"), ads_handler))
    application.add_handler(CallbackQueryHandler(back_callback_handler, pattern=f"^{CALLBACK_BACK}$"))
    application.add_error_handler(error_handler)

    logger.info("Бот запущен...")
    
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        # Ожидаем бесконечно, пока работает процесс
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main_async())