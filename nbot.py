"""
Render-ready Telegram bot, Webhook edition using run_webhook.
Based on PTB v22+ examples and agent recommendations.
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,  # Using Application directly is fine, builder pattern also works
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ── 1. CONFIGURATION (Using Agent's suggested variable names) ───────────────────
try:
    BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]  # Using your original name
    PUBLIC_URL: str = os.environ["WEBHOOK_URL"].rstrip("/")  # Using your original name
except KeyError as e:
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical(f"FATAL ERROR: Missing required environment variable: {e}. Bot cannot start.")
    exit(f"Missing environment variable: {e}")

# Optional but recommended: Use the token itself as the secret path segment
WEBHOOK_PATH: str = f"/{BOT_TOKEN}"  # Use the token, start with "/"

# Render provides PORT, default 10000 often works, but PTB defaults might be 80/443/8443
# Using Render's PORT is safer.
PORT: int = int(os.environ.get("PORT", 8443)) # Default to 8443 if PORT not set, Render will override

# Optional: Extra header check for added security
# Set TG_SECRET_TOKEN env var on Render if you use this
SECRET_TOKEN: str | None = os.environ.get("TG_SECRET_TOKEN")

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# --- Constants ---
DEFAULT_SERVICE_URL = "https://shodrop.io"
SUPPORT_CONTACT_INFO = "Для связи с поддержкой напишите @SHODROP_SUPPORT"

# --- DATA ---
SERVICE_DATA = {
    'main_web_dev': {"title": "1️⃣ Разработка веб-сайта", "url": f"{DEFAULT_SERVICE_URL}/web-development"},
    'main_shopify': {"title": "2️⃣ Магазин под ключ на Shopify", "url": f"{DEFAULT_SERVICE_URL}/shopify-store"},
    'main_targeting': {"title": "4️⃣ Настройка таргетированной рекламы", "url": f"{DEFAULT_SERVICE_URL}/targeted-ads"},
    'main_seo': {"title": "5️⃣ SEO-оптимизация сайта", "url": f"{DEFAULT_SERVICE_URL}/seo-optimization"},
    'main_context': {"title": "6️⃣ Контекстная реклама", "url": f"{DEFAULT_SERVICE_URL}/contextual-ads"},
    'main_creative': {"title": "7️⃣ Видео-креативы и карточки товаров", "url": f"{DEFAULT_SERVICE_URL}/creatives"},
    'main_registration': {"title": "8️⃣ Регистрация компании за рубежом", "url": f"{DEFAULT_SERVICE_URL}/company-registration"},
}

# --- MESSAGE TEXTS ---
MAIN_MENU_TEXT = """
Добро пожаловать в SHODROP — Ваше e-Commerce агентство! 🚀
[...] # Your full text
"""
PAYMENT_SYSTEMS_TEXT = "Выберите интересующую платежную систему или опцию:"
SOCIAL_MEDIA_TEXT = "Наши социальные сети:\n- Instagram: @shodrop.io\n- TikTok: @shodrop"

# --- KEYBOARD DEFINITIONS ---
# (All your get_..._keyboard functions remain exactly the same)
def get_main_menu_keyboard():
    # PASTE YOUR ACTUAL KEYBOARD DEFINITION HERE!
    keyboard = [
        [InlineKeyboardButton(SERVICE_DATA['main_web_dev']['title'], callback_data='main_web_dev')],
        [InlineKeyboardButton(SERVICE_DATA['main_shopify']['title'], callback_data='main_shopify')],
        [InlineKeyboardButton("3️⃣ Подключение платежной системы", callback_data='main_payment')],
        [InlineKeyboardButton(SERVICE_DATA['main_targeting']['title'], callback_data='main_targeting')],
        [InlineKeyboardButton(SERVICE_DATA['main_seo']['title'], callback_data='main_seo')],
        [InlineKeyboardButton(SERVICE_DATA['main_context']['title'], callback_data='main_context')],
        [InlineKeyboardButton(SERVICE_DATA['main_creative']['title'], callback_data='main_creative')],
        [InlineKeyboardButton(SERVICE_DATA['main_registration']['title'], callback_data='main_registration')],
        [InlineKeyboardButton("🌐 Наши соц. сети", callback_data='main_social')],
    ]
    return InlineKeyboardMarkup(keyboard)

# ── 2. HANDLERS (Your existing async handlers) ─────────────────────────────────
# (start and button_callback_handler functions remain exactly the same async def ...)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Your existing start handler code...
    user = update.effective_user
    logger.info(f"[Handler /start] User {user.id} initiated.")
    message = update.message or (update.callback_query and update.callback_query.message)
    # ... rest of your logic ...
    if not message: return
    text = MAIN_MENU_TEXT; keyboard = get_main_menu_keyboard()
    try:
        if update.callback_query: await message.edit_text(...) # Your full logic
        elif update.message: await message.reply_text(...) # Your full logic
    except Exception as e: logger.error(...)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Your existing button callback handler code...
    query = update.callback_query
    # ... rest of your logic, including query.answer() and edits ...
    if not query or not query.message: return
    message = query.message; user = query.from_user
    try: await query.answer()
    except Exception as e: logger.warning(...)
    callback_data = query.data
    logger.info(f"[Handler Callback] User {user.id} clicked: {callback_data}.")
    text = ""; keyboard = None
    try:
        # Your routing logic...
        if callback_data == 'back_to_main': await start(update, context); return
        # ... other elif ...
        else: logger.warning(...); return
        # Your edit logic...
        if text and keyboard: await message.edit_text(...)
        elif text: await message.edit_text(...)
    except Exception as e: logger.error(...)

# ── 3. APPLICATION SET-UP ──────────────────────────────────────────────────────
logger.info("Building Telegram Application...")
application = (
    Application.builder()
    .token(BOT_TOKEN)
    .read_timeout(7)    # Adjusted timeouts
    .write_timeout(20)
    .connect_timeout(5)
    .pool_timeout(10)
    .build()
)

# Add your handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback_handler))
# Optional: Add error handler if needed
# application.add_error_handler(...)
logger.info("Handlers registered.")

# ── 4. ENTRY POINT & WEBHOOK START ─────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"Starting webhook server on port {PORT}")
    logger.info(f"Webhook path: {WEBHOOK_PATH}")
    logger.info(f"Registering webhook with Telegram: {PUBLIC_URL}{WEBHOOK_PATH}")

    # run_webhook handles initialization, webhook setting, and shutdown
    application.run_webhook(
        listen="0.0.0.0",                           # Listen on all interfaces for Render
        port=PORT,                                  # Use port from environment variable
        url_path=WEBHOOK_PATH.lstrip("/"),          # The path part (without leading slash)
        webhook_url=f"{PUBLIC_URL}{WEBHOOK_PATH}",  # Full public URL for Telegram
        secret_token=SECRET_TOKEN                   # Pass optional secret token if set
        # drop_pending_updates=True # Consider uncommenting if you have issues with old updates after restarts
    )
    # This line is blocking and will run until the process is stopped
    logger.info("Webhook server stopped.")
