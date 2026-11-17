import logging
import os
import re
import asyncio
from pathlib import Path
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

# Токен берётся только из переменной окружения BOT_TOKEN (Render → Environment)
TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
# httpx пишет в журнал полный URL запроса вместе с токеном — оставляем только предупреждения
logging.getLogger("httpx").setLevel(logging.WARNING)

IMG = Path(__file__).parent / "img"

# =========================================================
# ССЫЛКИ (URL)
# =========================================================

URL_PROJECTS_CHANNEL = "https://t.me/coolshop"
URL_PROJECTS_TALK = "https://t.me/BullXTalk"

URL_CONTACT_NAZA = "https://t.me/wmixz"
URL_CONTACT_MANAGER = "https://t.me/BullXHelper"
URL_CONTACT_GARANT = "https://t.me/BullXDeal"

URL_REVIEWS = "https://t.me/BullXRate"

URL_ADS_CONTACT = "https://t.me/wmixz"

# =========================================================
# ПРЕМИУМ-ЭМОДЗИ (работают, пока у владельца бота есть Telegram Premium)
# =========================================================

E_WAVE = "5994750571041525522"      # 👋
E_HEART = "5429553830033401743"     # ❤️ (Обо мне)
E_HEART2 = "5429618099924016128"    # ❤️ (приветствие)
E_WARN = "5870527021485919704"      # ❗️
E_DOWN = "5807557921843715576"      # ⬇️
E_BACK = "5805509901048356965"      # ⬅️
E_HUB = "5771695636411847302"       # 📢
E_TALK = "6019151079114021083"      # 💬
E_NAZA = "5229027828527309057"      # 👑
E_HELPER = "6021659039367173797"    # ➕
E_DEAL = "6019328362479097179"      # 🛡
E_REVIEWS = "6019320644422867543"   # 💬 (отзывы)
E_INFO = "5879785854284599288"      # ℹ️ (реклама)
E_OFFER = "5967280668885913944"     # ✉️ (Предложить)
E_CONTACTS = "5942877472163892475"  # 👥 (кнопка Контакты)


def pe(emoji_id: str, fallback: str) -> str:
    """премиум-эмодзи в HTML-тексте"""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def url_button(text: str, url: str, emoji_id: str | None = None) -> InlineKeyboardButton:
    """инлайн-кнопка-ссылка с премиум-иконкой слева от текста"""
    extra = {"icon_custom_emoji_id": emoji_id} if emoji_id else None
    return InlineKeyboardButton(text, url=url, api_kwargs=extra)


# =========================================================
# ПОДПИСИ КНОПОК И ТЕКСТЫ
# =========================================================

BTN_ABOUT = "Обо мне"
BTN_PROJECTS = "Проекты"
BTN_CONTACTS = "Контакты"
BTN_REVIEWS = "Отзывы"
BTN_ADS = "Реклама"

BTN_PROJECTS_CHANNEL = "BullXHub"
BTN_PROJECTS_TALK = "BullXTalk"

BTN_CONTACT_NAZA = "RR | Naza"
BTN_CONTACT_MANAGER = "BullXHelper"
BTN_CONTACT_GARANT = "BullXDeal"

BTN_REVIEWS_LINK = "Смотреть отзывы"
BTN_ADS_LINK = "Предложить"

BTN_BACK = "Назад"
CALLBACK_BACK = "back_to_main"

WELCOME_TEXT = (
    f"{pe(E_HEART2, '❤️')}<b>Добро пожаловать в BullX Info!</b>\n\n"
    "Здесь всё самое важное о <b>BullX:</b> проекты, контакты, отзывы и реклама.\n\n"
    f"Выбери раздел в меню ниже{pe(E_DOWN, '⬇️')}"
)

TEXT_ABOUT = (
    f"{pe(E_WAVE, '👋')}<b>Приветствую, ребята!</b>\n\n"
    "Думаю, все, кто сюда зашёл, уже знают, <b>кто я и чем занимаюсь</b> — "
    f"я владелец проектов <b>BullX</b>{pe(E_HEART, '❤️')}\n\n"
    f"{pe(E_WARN, '❗️')}Здесь собрал всё самое основное: <b>проекты, контакты команды, отзывы и рекламу.</b>"
)

TEXT_PROJECTS = (
    f"{pe(E_HUB, '📢')}<b>BullXHub — наш Telegram-канал,</b> где публикуем "
    "<b>все новости, новые поступления, ежедневный рынок NFT</b> и проводим <b>розыгрыши!</b>\n\n"
    f"{pe(E_TALK, '💬')}<b>BullXTalk — наш чат,</b> где можно "
    "<b>покупать, продавать и обменивать NFT и не только</b> — напрямую с другими людьми."
)

TEXT_CONTACTS = (
    f"{pe(E_NAZA, '👑')}<b>RR | Naza — владелец BullX.</b> Первый, к кому можно обратиться, "
    "если хотите что-то <b>приобрести,</b> предложить <b>сотрудничество</b> или просто что-то узнать.\n\n"
    f"{pe(E_HELPER, '➕')}<b>BullXHelper — менеджер и мой помощник.</b> Если я не могу ответить, "
    "пишите ему — поможет <b>с покупкой и другими вопросами.</b>\n\n"
    f"{pe(E_DEAL, '🛡')}<b>BullXDeal — </b>гарант ваших сделок на сумму<b> до 3000 грн</b>.\n"
    "<blockquote>Стоимость услуги — <b>5% от суммы сделки.</b>\n"
    "Если сумма сделки до <b>500 грн</b> — фиксировано <b>25 грн.</b></blockquote>\n\n"
    "По всем остальным вопросам обращайтесь к <b>нашей команде</b> — постараемся помочь!"
)

TEXT_REVIEWS = (
    "Здесь собраны <b>отзывы наших клиентов</b> о покупках и работе с <b>BullX.</b>\n\n"
    "Нам важно не просто продать товар, а сделать так, чтобы "
    "<b>клиент остался довольным и вернулся снова.</b>\n\n"
    f"{pe(E_REVIEWS, '💬')}Уже собрали <b>1500+ отзывов</b> и <b>продолжаем двигаться дальше.</b>\n"
    "<b>Спасибо каждому, кто выбирает BullX!</b>"
)

TEXT_ADS = (
    f"{pe(E_INFO, 'ℹ️')}По вопросам <b>рекламы, взаимопиара и коммерческого сотрудничества</b> "
    "обращайтесь <b>строго ко мне</b> в личные сообщения.\n\n"
    "<b>Рассматриваю разные варианты сотрудничества:</b>\n"
    "— <b>рекламные посты</b>\n"
    "— <b>размещение в каналах</b>\n"
    "— <b>взаимопиар</b>\n"
    "— <b>долгосрочное сотрудничество</b>\n"
    "— <b>индивидуальные предложения</b>\n\n"
    "Есть идея или предложение? <b>Пишите — обсудим.</b>"
)

# =========================================================
# КЛАВИАТУРЫ
# =========================================================

def menu_button(text: str, emoji_id: str) -> KeyboardButton:
    """кнопка нижнего меню с премиум-иконкой слева"""
    return KeyboardButton(text, api_kwargs={"icon_custom_emoji_id": emoji_id})

def main_reply_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [menu_button(BTN_ABOUT, E_NAZA), menu_button(BTN_PROJECTS, E_HUB)],
        [menu_button(BTN_CONTACTS, E_CONTACTS), menu_button(BTN_REVIEWS, E_REVIEWS)],
        [menu_button(BTN_ADS, E_INFO)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def back_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(BTN_BACK, callback_data=CALLBACK_BACK, api_kwargs={"icon_custom_emoji_id": E_BACK})

def about_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[back_button()]])

def projects_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [url_button(BTN_PROJECTS_CHANNEL, URL_PROJECTS_CHANNEL, E_HUB)],
        [url_button(BTN_PROJECTS_TALK, URL_PROJECTS_TALK, E_TALK)],
        [back_button()],
    ]
    return InlineKeyboardMarkup(keyboard)

def contacts_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [url_button(BTN_CONTACT_NAZA, URL_CONTACT_NAZA, E_NAZA)],
        [url_button(BTN_CONTACT_MANAGER, URL_CONTACT_MANAGER, E_HELPER)],
        [url_button(BTN_CONTACT_GARANT, URL_CONTACT_GARANT, E_DEAL)],
        [back_button()],
    ]
    return InlineKeyboardMarkup(keyboard)

def reviews_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [url_button(BTN_REVIEWS_LINK, URL_REVIEWS, E_REVIEWS)],
        [back_button()],
    ]
    return InlineKeyboardMarkup(keyboard)

def ads_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [url_button(BTN_ADS_LINK, URL_ADS_CONTACT, E_OFFER)],
        [back_button()],
    ]
    return InlineKeyboardMarkup(keyboard)

# =========================================================
# ОТПРАВКА: баннер + текст подписью одним сообщением
# =========================================================

async def send_section(chat, banner: str, text: str, reply_markup, where: str) -> None:
    """баннер img/<banner>.jpg с текстом-подписью; если картинки нет — просто текст"""
    path = IMG / f"{banner}.jpg"
    try:
        if path.exists():
            with path.open("rb") as photo:
                await chat.send_photo(photo, caption=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            await chat.send_message(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except TelegramError as exc:
        # если Telegram не принял премиум-эмодзи (например, закончился Premium) — шлём обычными
        logger.error("Ошибка в разделе '%s': %s — отправляю без премиум-эмодзи", where, exc)
        plain = re.sub(r'<tg-emoji emoji-id="\d+">(.*?)</tg-emoji>', r"\1", text)
        markup = strip_icons(reply_markup)
        try:
            if path.exists():
                with path.open("rb") as photo:
                    await chat.send_photo(photo, caption=plain, parse_mode=ParseMode.HTML, reply_markup=markup)
            else:
                await chat.send_message(plain, parse_mode=ParseMode.HTML, reply_markup=markup)
        except TelegramError as exc2:
            logger.error("Повторная ошибка в разделе '%s': %s", where, exc2)


def strip_icons(markup):
    """та же инлайн-клавиатура, но без премиум-иконок на кнопках"""
    if isinstance(markup, ReplyKeyboardMarkup):
        return ReplyKeyboardMarkup([[KeyboardButton(b.text) for b in row] for row in markup.keyboard],
                                   resize_keyboard=True, is_persistent=True)
    if not isinstance(markup, InlineKeyboardMarkup):
        return markup
    rows = []
    for row in markup.inline_keyboard:
        rows.append([
            InlineKeyboardButton(b.text, url=b.url) if b.url else InlineKeyboardButton(b.text, callback_data=b.callback_data)
            for b in row
        ])
    return InlineKeyboardMarkup(rows)

# =========================================================
# ОБРАБОТЧИКИ БОТА
# =========================================================

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_section(update.effective_chat, "info", WELCOME_TEXT, main_reply_keyboard(), "Приветствие")

async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_section(update.effective_chat, "about", TEXT_ABOUT, about_inline_keyboard(), "Обо мне")

async def projects_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_section(update.effective_chat, "projects", TEXT_PROJECTS, projects_inline_keyboard(), "Проекты")

async def contacts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_section(update.effective_chat, "contacts", TEXT_CONTACTS, contacts_inline_keyboard(), "Контакты")

async def reviews_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_section(update.effective_chat, "reviews", TEXT_REVIEWS, reviews_inline_keyboard(), "Отзывы")

async def ads_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_section(update.effective_chat, "ads", TEXT_ADS, ads_inline_keyboard(), "Реклама")

async def back_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """«Назад»: убираем кнопки у раздела и присылаем главное меню (приветствие с баннером)"""
    query = update.callback_query
    try:
        await query.answer()
    except TelegramError as exc:
        logger.warning("Ошибка при answer callback_query: %s", exc)
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except TelegramError as exc:
        logger.warning("Не удалось убрать кнопки: %s", exc)
    await send_section(update.effective_chat, "info", WELCOME_TEXT, main_reply_keyboard(), "Главное меню")

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
    if not TOKEN:
        raise RuntimeError("Не задан токен бота: добавь BOT_TOKEN в Render → Environment.")

    # Запускаем веб-сервер для Render
    await start_web_server()

    # Настраиваем и запускаем Telegram бота
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(MessageHandler(filters.Regex(f"{BTN_ABOUT}$"), about_handler))
    application.add_handler(MessageHandler(filters.Regex(f"{BTN_PROJECTS}$"), projects_handler))
    application.add_handler(MessageHandler(filters.Regex(f"{BTN_CONTACTS}$"), contacts_handler))
    application.add_handler(MessageHandler(filters.Regex(f"{BTN_REVIEWS}$"), reviews_handler))
    application.add_handler(MessageHandler(filters.Regex(f"{BTN_ADS}$"), ads_handler))
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
