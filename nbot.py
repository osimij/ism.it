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
    # Using your original environment variable names
    BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
    PUBLIC_URL: str = os.environ["WEBHOOK_URL"].rstrip("/")
except KeyError as e:
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical(f"FATAL ERROR: Missing required environment variable: {e}. Bot cannot start.")
    exit(f"Missing environment variable: {e}")

# Use the token itself as the secret path segment
WEBHOOK_PATH: str = f"/{BOT_TOKEN}"

# Port provided by Render (defaults to 10000 on free tier usually)
PORT: int = int(os.environ.get("PORT", 10000))

# Optional: Extra header check for added security
SECRET_TOKEN: str | None = os.environ.get("TG_SECRET_TOKEN") # Set this env var on Render if used

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

Мы здесь, чтобы помочь вашему онлайн-бизнесу расти и развиваться!

💡 Что вы найдете в этом боте?
- Список наших услуг с переходом на сайт
- Отзывы клиентов
- AI-EcomMentor (скоро!)
- Ответы на ваши вопросы
- Возможность связаться с нашей командой

🌐 Узнайте больше: shodrop.io
💬 Чат поддержки: @SHODROP_SUPPORT (или другая ссылка/контакт)
"""
PAYMENT_SYSTEMS_TEXT = "Выберите интересующую платежную систему или опцию:"
SOCIAL_MEDIA_TEXT = "Наши социальные сети:\n- Instagram: @shodrop.io\n- TikTok: @shodrop"

# --- KEYBOARD DEFINITIONS ---

def get_main_menu_keyboard():
    """Generates the main menu inline keyboard."""
    # --- PASTE ACTUAL KEYBOARD DEFINITION ---
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

def get_payment_systems_keyboard():
    """Generates the payment systems submenu keyboard."""
    # --- PASTE ACTUAL KEYBOARD DEFINITION ---
    keyboard = [
        [InlineKeyboardButton("Stripe 💳", callback_data='payment_stripe')],
        [InlineKeyboardButton("Shopify Payments 💳", callback_data='payment_shopify')],
        [InlineKeyboardButton("Отзывы ✅", callback_data='payment_reviews')],
        [InlineKeyboardButton("💬 Есть вопрос? Связаться с поддержкой", callback_data='support_payment')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_service_detail_keyboard(service_key):
    """Generates the 3-button keyboard for a specific service detail view."""
    service_info = SERVICE_DATA.get(service_key)
    service_url = service_info.get('url', DEFAULT_SERVICE_URL) if service_info else DEFAULT_SERVICE_URL
    support_callback = f"support_{service_key.split('_', 1)[-1]}" if '_' in service_key else f"support_{service_key}"
    # --- PASTE ACTUAL KEYBOARD DEFINITION ---
    keyboard = [
        [InlineKeyboardButton("Подробнее 🔥", url=service_url)],
        [InlineKeyboardButton("💬 Есть вопрос? Связаться с поддержкой", callback_data=support_callback)],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_keyboard():
    """Generates a simple keyboard with only a 'Back to Main Menu' button."""
    # --- PASTE ACTUAL KEYBOARD DEFINITION ---
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')]]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_payments_keyboard():
    """Generates a simple keyboard with only a 'Back to Payment Systems' button."""
     # --- PASTE ACTUAL KEYBOARD DEFINITION ---
    keyboard = [[InlineKeyboardButton("◀️ Назад к платежным системам", callback_data='main_payment')]]
    return InlineKeyboardMarkup(keyboard)

# --- TELEGRAM BOT HANDLERS (async def functions) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends or edits the message to show the main menu."""
    user = update.effective_user
    logger.info(f"[Handler /start] User {user.id} ({user.username or 'NoUsername'}) initiated.")
    message = update.message or (update.callback_query and update.callback_query.message)
    if not message:
        logger.warning("Start command received without a message context.")
        return

    text = MAIN_MENU_TEXT
    # Error handling specifically for keyboard generation added
    try:
        keyboard = get_main_menu_keyboard()
    except Exception as e:
         logger.error(f"Error generating main menu keyboard: {e}", exc_info=True)
         # Send a message without keyboard if generation fails
         if update.message:
             await message.reply_text("Произошла ошибка при загрузке меню. Попробуйте позже.")
         return # Stop processing if keyboard fails

    try:
        if update.callback_query:
            logger.info(f"Editing message {message.message_id} for user {user.id} to main menu.")
            await message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        elif update.message:
             logger.info(f"Replying to message {message.message_id} for user {user.id} with main menu.")
             await message.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"Error sending/editing message in start handler for user {user.id}: {e}", exc_info=True)


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message."""
    query = update.callback_query
    if not query or not query.message:
        logger.warning("Callback query received without query or message object.")
        # Try to answer even if message context is missing, might clear loading state
        if query:
            try: await query.answer("Processing...")
            except Exception: pass
        return

    message = query.message
    user = query.from_user

    # Always answer the callback query immediately
    try:
        await query.answer()
    except Exception as e:
        # Log as warning, bot might still be able to process
        logger.warning(f"Failed to answer callback query {query.id} for user {user.id}: {e}")

    callback_data = query.data
    logger.info(f"[Handler Callback] User {user.id} ({user.username or 'NoUsername'}) clicked: {callback_data}. Message ID: {message.message_id}")

    text = ""
    keyboard = None
    keyboard_func = None

    try:
        # --- Routing based on callback_data ---
        if callback_data == 'back_to_main':
            # Re-use the start logic to show the main menu
            await start(update, context)
            return

        elif callback_data == 'main_payment':
            text = PAYMENT_SYSTEMS_TEXT
            keyboard_func = get_payment_systems_keyboard
        elif callback_data == 'main_social':
            text = SOCIAL_MEDIA_TEXT
            keyboard_func = get_back_to_main_keyboard
        elif callback_data in SERVICE_DATA:
            service_info = SERVICE_DATA[callback_data]
            clean_title = service_info['title'].split(' ', 1)[-1] if ' ' in service_info['title'] else service_info['title']
            text = f"Услуга: {clean_title}"
            # Pass service_key to the function correctly
            keyboard = get_service_detail_keyboard(callback_data) # Directly get keyboard here
        elif callback_data.startswith('support_'):
            text = SUPPORT_CONTACT_INFO
            keyboard_func = get_back_to_payments_keyboard if callback_data == 'support_payment' else get_back_to_main_keyboard
        elif callback_data == 'payment_stripe':
            text = "Подключение Stripe: Помощь в настройке для приема платежей."
            # Define keyboard directly or ensure function returns valid structure
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Подробнее о Stripe 🔥", url=f"{DEFAULT_SERVICE_URL}/stripe-integration")],
                [InlineKeyboardButton("◀️ Назад к платежным системам", callback_data='main_payment')]
            ])
        elif callback_data == 'payment_shopify':
            text = "Shopify Payments: Настройка и верификация интегрированной системы."
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Подробнее о Shopify Payments 🔥", url=f"{DEFAULT_SERVICE_URL}/shopify-payments")],
                [InlineKeyboardButton("◀️ Назад к платежным системам", callback_data='main_payment')]
            ])
        elif callback_data == 'payment_reviews':
            text = "Отзывы наших клиентов о настройке платежных систем..."
            keyboard = InlineKeyboardMarkup([
                # [InlineKeyboardButton("Читать отзывы", url=f"{DEFAULT_SERVICE_URL}/reviews")],
                [InlineKeyboardButton("◀️ Назад к платежным системам", callback_data='main_payment')]
            ])
        else:
            logger.warning(f"Unhandled callback_data '{callback_data}' received from user {user.id}")
            await query.edit_message_text("Неизвестная команда.", reply_markup=get_back_to_main_keyboard())
            return

        # Generate keyboard if a function was assigned
        if keyboard_func:
             try:
                 keyboard = keyboard_func()
             except Exception as e:
                 logger.error(f"Error generating keyboard for callback {callback_data}: {e}", exc_info=True)
                 await query.edit_message_text("Ошибка отображения кнопок.", reply_markup=get_back_to_main_keyboard())
                 return

        # --- Edit the message ---
        # Ensure keyboard is generated if text is set
        if text and keyboard:
             logger.info(f"Editing message {message.message_id} for user {user.id}. Action: {callback_data}")
             await message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        elif text: # Handle cases where only text might change (e.g., error message with standard back button)
            logger.info(f"Editing message {message.message_id} for user {user.id} (text only). Action: {callback_data}")
            await message.edit_text(
                text=text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        # else: Action resulted in calling start() or was unhandled

    except Exception as e:
        logger.error(f"Error processing callback data '{callback_data}' for user {user.id}: {e}", exc_info=True)
        # Attempt to inform the user about the error with a safe keyboard
        try:
            await query.edit_message_text("Произошла ошибка при обработке вашего запроса. Попробуйте вернуться в главное меню.", reply_markup=get_back_to_main_keyboard())
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
    # run_webhook handles initialization, webhook setting, and shutdown
    logger.info(f"Starting webhook server on port {PORT}")
    logger.info(f"Webhook path: {WEBHOOK_PATH}")
    logger.info(f"Registering webhook with Telegram: {PUBLIC_URL}{WEBHOOK_PATH}")

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH.lstrip("/"), # PTB expects path without leading '/' here
        webhook_url=f"{PUBLIC_URL}{WEBHOOK_PATH}",
        secret_token=SECRET_TOKEN
    )
