# --- IMPORTS ---
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# --- CONFIGURATION ---
try:
    BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
    PUBLIC_URL: str = os.environ["WEBHOOK_URL"].rstrip("/")
except KeyError as e:
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical(f"FATAL ERROR: Missing required environment variable: {e}. Bot cannot start.")
    exit(f"Missing environment variable: {e}")

WEBHOOK_PATH: str = f"/{BOT_TOKEN}"
PORT: int = int(os.environ.get("PORT", 10000))
SECRET_TOKEN: str | None = os.environ.get("TG_SECRET_TOKEN")

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Constants ---
SUPPORT_CONTACT_INFO = "Для связи с поддержкой напишите @SHODROP_SUPPORT"
PLACEHOLDER_URL = "https://google.com"

# --- DATA STRUCTURE ---
SERVICE_CATEGORIES = {
    "main_web_dev": {
        "title": "1️⃣ Веб-разработка",
        "sub_items": [
            "Интернет-магазин",
            "Лендинг",
            "Сайт-визитка",
            "Wordpress",
            "Shopify",
            "Cайт под ваш вкус",
        ],
        "message_title": "Веб-разработка",
    },
    "main_apps": {
        "title": "2️⃣ Приложения",
        "sub_items": [
            "iOS",
            "Android",
            "Мини-приложения для Telegram",
        ],
        "message_title": "Приложения",
     },
    "main_bots": {
        "title": "3️⃣ Разработка ботов",
        "sub_items": [
            "Для Telegram",
            "Для Веб-сайтов",
        ],
        "message_title": "Разработка ботов",
     },
    "main_targeting": {
        "title": "4️⃣ Настройка таргетированной рекламы",
        "sub_items": [
            "Google",
            "Facebook",
            "Instagram",
            "Pinterest",
            "Yandex",
            "Tiktok",
        ],
        "message_title": "Настройка таргетированной рекламы",
     },
    "main_seo": {
        "title": "6️⃣ SEO - оптимизация",
        "sub_items": [
            "Комплексное SEO-продвижение",
        ],
        "message_title": "SEO - оптимизация",
     },
    "main_support": {
        "title": "7️⃣ Техподдержка",
        "sub_items": [
            "Напиши нам свою проблему",
            "Решаем проблемы до звонка клиенту",
        ],
        "message_title": "Техподдержка",
     },
    "main_ai": {
        "title": "8️⃣ AI-интеграция",
        "sub_items": [
            "Чат-ассистенты",
        ],
        "message_title": "AI-интеграция",
     },
}

# --- MESSAGE TEXTS ---
MAIN_MENU_TEXT = """
Добро пожаловать в SHODROP — Ваше e-Commerce агентство! 🚀

Мы здесь, чтобы помочь вашему онлайн-бизнесу расти и развиваться!

Выберите интересующую вас категорию услуг:
"""

# --- KEYBOARD DEFINITIONS ---
def get_main_menu_keyboard():
    """Generates the main menu inline keyboard from SERVICE_CATEGORIES."""
    keyboard = []
    for key, data in SERVICE_CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(data["title"], callback_data=key)])
    return InlineKeyboardMarkup(keyboard)

def get_category_detail_keyboard(category_key):
    """Generates keyboard with clickable sub-items, Support, and Back."""
    category_info = SERVICE_CATEGORIES.get(category_key)
    if not category_info:
        logger.error(f"Category key '{category_key}' not found in SERVICE_CATEGORIES.")
        return get_back_to_main_keyboard()

    keyboard = []
    # Add button for each sub-item, linking to the placeholder URL
    for item_label in category_info["sub_items"]:
        keyboard.append([InlineKeyboardButton(item_label, url=PLACEHOLDER_URL)])

    # Add Support button
    support_callback = f"support_{category_key.split('_', 1)[-1]}"
    keyboard.append([InlineKeyboardButton("📩 Есть вопрос? Связаться с поддержкой", callback_data=support_callback)])

    # Add Back button
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')])

    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_keyboard():
    """Generates a simple keyboard with only a 'Back to Main Menu' button."""
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')]]
    return InlineKeyboardMarkup(keyboard)

# --- TELEGRAM BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends or edits the message to show the main menu."""
    user = update.effective_user
    logger.info(f"[Handler /start] User {user.id} ({user.username or 'NoUsername'}) initiated.")
    message = update.message or (update.callback_query and update.callback_query.message)
    if not message:
        logger.warning("Start command received without a message context.")
        return

    text = MAIN_MENU_TEXT
    try:
        keyboard = get_main_menu_keyboard()
    except Exception as e:
         logger.error(f"Error generating main menu keyboard: {e}", exc_info=True)
         if update.message:
             await message.reply_text("Ошибка загрузки меню.")
         return

    try:
        if update.callback_query:
            logger.info(f"Editing message {message.message_id} for user {user.id} to main menu.")
            await message.edit_text(text=text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)
        elif update.message:
             logger.info(f"Replying to message {message.message_id} for user {user.id} with main menu.")
             await message.reply_text(text=text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error sending/editing message in start handler for user {user.id}: {e}", exc_info=True)


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message."""
    query = update.callback_query
    if not query: # Check query exists first
        logger.warning("Callback query received without query object.")
        return # Cannot proceed without a query

    # Attempt to answer the query first thing
    try:
        await query.answer()
    except Exception as e:
        # Log as warning, bot might still be able to process the rest
        logger.warning(f"Failed to answer callback query {query.id}: {e}")

    # Check if message context exists *after* answering
    if not query.message:
        logger.warning(f"Callback query {query.id} received without message object.")
        return # Cannot edit a message if it doesn't exist

    # Now we know query and query.message exist
    message = query.message
    user = query.from_user
    callback_data = query.data
    logger.info(f"[Handler Callback] User {user.id} ({user.username or 'NoUsername'}) clicked: {callback_data}. Message ID: {message.message_id}")

    text = ""
    keyboard = None
    try:
        # --- Routing ---
        if callback_data == 'back_to_main':
            await start(update, context)
            return
        elif callback_data in SERVICE_CATEGORIES:
            category_info = SERVICE_CATEGORIES[callback_data]
            text = category_info["message_title"]
            keyboard = get_category_detail_keyboard(callback_data)
        elif callback_data.startswith('support_'):
            text = SUPPORT_CONTACT_INFO
            # Using get_back_to_main_keyboard, assuming support message doesn't need specific back context
            keyboard = get_back_to_main_keyboard()
        else:
            logger.warning(f"Unhandled callback_data '{callback_data}' from user {user.id}")
            await query.edit_message_text("Неизвестная команда.", reply_markup=get_back_to_main_keyboard())
            return

        # --- Edit ---
        if text and keyboard:
             logger.info(f"Editing message {message.message_id} for user {user.id}. Action: {callback_data}")
             await message.edit_text(
                 text=text,
                 reply_markup=keyboard,
                 parse_mode=None, # Set to 'HTML' or 'Markdown' if title needs formatting
                 disable_web_page_preview=True
            )
        elif text: # Fallback if only text needs changing (e.g., support message without buttons)
             logger.info(f"Editing message {message.message_id} for user {user.id} (text only). Action: {callback_data}")
             await message.edit_text(
                 text=text,
                 parse_mode=None,
                 disable_web_page_preview=True
             )

    except Exception as e:
        logger.error(f"Error processing callback data '{callback_data}' for user {user.id}: {e}", exc_info=True)
        try:
            await query.edit_message_text("Произошла ошибка при обработке вашего запроса.", reply_markup=get_back_to_main_keyboard())
        except Exception as inner_e:
            logger.error(f"Failed to send error message to user {user.id} after callback error: {inner_e}")

# --- APPLICATION SETUP ---
logger.info("Building Telegram Application...")
application = (
    Application.builder()
    .token(BOT_TOKEN)
    .read_timeout(7)
    .write_timeout(20)
    .connect_timeout(5)
    .pool_timeout(10)
    .build()
)

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback_handler))
logger.info("Handlers registered.")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    logger.info(f"Starting webhook server on port {PORT}")
    logger.info(f"Webhook path: {WEBHOOK_PATH}")
    logger.info(f"Attempting to set webhook via run_webhook: {PUBLIC_URL}{WEBHOOK_PATH}")

    # run_webhook handles initialization, webhook setting, and the web server loop
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH.lstrip("/"), # Expects path without leading slash
        webhook_url=f"{PUBLIC_URL}{WEBHOOK_PATH}", # Full URL for Telegram
        secret_token=SECRET_TOKEN # Pass optional secret token if set
    )
