# --- IMPORTS ---
import logging
import os
import asyncio # <--- Required for application initialization
from flask import Flask, request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    # TypeHandler # Not strictly needed for this setup, but good for advanced use
)

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    # Use basic logging before full setup if token is missing
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical("FATAL ERROR: TELEGRAM_BOT_TOKEN environment variable not set.")
    exit("Bot token not found. Exiting.")

# The public URL assigned by Render (set as an environment variable)
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
if not WEBHOOK_URL:
    # Log warning but allow startup for potential local testing or alternative webhook setup
    logging.warning("WARNING: WEBHOOK_URL environment variable not set. Webhook setup must be done manually or via other means.")

# Secret path segment to ensure requests come from Telegram (using token is common)
SECRET_PATH = TELEGRAM_BOT_TOKEN

# Render provides the PORT environment variable for Web Services
PORT = int(os.environ.get('PORT', 8080)) # Default for local runs

# --- Constants ---
DEFAULT_SERVICE_URL = "https://shodrop.io" # Replace with your main site or a fallback
SUPPORT_CONTACT_INFO = "Для связи с поддержкой напишите @SHODROP_SUPPORT" # Replace with actual support contact/link

# --- LOGGING SETUP ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Reduce noise from underlying HTTP library
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# --- DATA ---
# Store service info (callback_data -> {title, url})
SERVICE_DATA = {
    'main_web_dev': {"title": "1️⃣ Разработка веб-сайта", "url": f"{DEFAULT_SERVICE_URL}/web-development"}, # Example URL
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
SOCIAL_MEDIA_TEXT = "Наши социальные сети:\n- Instagram: @shodrop.io\n- TikTok: @shodrop" # Add actual links/handles

# --- KEYBOARD DEFINITIONS ---

def get_main_menu_keyboard():
    """Generates the main menu inline keyboard."""
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
    keyboard = [
        [InlineKeyboardButton("Подробнее 🔥", url=service_url)],
        [InlineKeyboardButton("💬 Есть вопрос? Связаться с поддержкой", callback_data=support_callback)],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_keyboard():
    """Generates a simple keyboard with only a 'Back to Main Menu' button."""
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')]]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_payments_keyboard():
    """Generates a simple keyboard with only a 'Back to Payment Systems' button."""
    keyboard = [[InlineKeyboardButton("◀️ Назад к платежным системам", callback_data='main_payment')]]
    return InlineKeyboardMarkup(keyboard)


# --- TELEGRAM BOT HANDLERS (Must be async) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends or edits the message to show the main menu."""
    user = update.effective_user
    logger.info(f"[Handler /start] User {user.id} ({user.username or 'NoUsername'}) initiated.")
    message = update.message or (update.callback_query and update.callback_query.message)
    if not message:
        logger.warning("Start command received without a message context.")
        return

    text = MAIN_MENU_TEXT
    keyboard = get_main_menu_keyboard()
    try:
        if update.callback_query: # Came from a button press (like 'Back')
            logger.info(f"Editing message {message.message_id} for user {user.id} to main menu.")
            await message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        elif update.message: # Came from /start command
             logger.info(f"Replying to message {message.message_id} for user {user.id} with main menu.")
             await message.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"Error in start handler for user {user.id}: {e}", exc_info=True)


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message."""
    query = update.callback_query
    if not query or not query.message:
        logger.warning("Callback query received without query or message object.")
        return

    message = query.message
    user = query.from_user

    # Always answer the callback query immediately
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query {query.id} for user {user.id}: {e}")

    callback_data = query.data
    logger.info(f"[Handler Callback] User {user.id} ({user.username or 'NoUsername'}) clicked: {callback_data}. Message ID: {message.message_id}")

    text = ""
    keyboard = None

    try:
        # --- Routing based on callback_data ---
        if callback_data == 'back_to_main':
            # Re-use the start logic to show the main menu
            await start(update, context)
            return # Stop further processing here

        elif callback_data == 'main_payment':
            text = PAYMENT_SYSTEMS_TEXT
            keyboard = get_payment_systems_keyboard()

        elif callback_data == 'main_social':
            text = SOCIAL_MEDIA_TEXT
            keyboard = get_back_to_main_keyboard()

        # Handle clicks on specific service buttons from the main menu
        elif callback_data in SERVICE_DATA:
            service_info = SERVICE_DATA[callback_data]
            clean_title = service_info['title'].split(' ', 1)[-1] if ' ' in service_info['title'] else service_info['title']
            text = f"Услуга: {clean_title}"
            keyboard = get_service_detail_keyboard(callback_data)

        # Handle clicks on "Contact Support"
        elif callback_data.startswith('support_'):
            text = SUPPORT_CONTACT_INFO
            if callback_data == 'support_payment':
                keyboard = get_back_to_payments_keyboard()
            else: # Support from a general service page
                keyboard = get_back_to_main_keyboard()

        # --- Payment Systems Sub-menu Logic ---
        elif callback_data == 'payment_stripe':
            text = "Подключение Stripe: Помощь в настройке для приема платежей."
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
            # Optionally notify user or just ignore
            # await query.edit_message_text("Неизвестная команда.", reply_markup=get_back_to_main_keyboard())
            return

        # --- Edit the message ---
        if text and keyboard:
             logger.info(f"Editing message {message.message_id} for user {user.id}. New text: '{text[:30]}...'")
             await message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        elif text: # Handle cases where only text might change
            logger.info(f"Editing message {message.message_id} for user {user.id} (text only). New text: '{text[:30]}...'")
            await message.edit_text(
                text=text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        # else: If 'start' was called (handled above) or unhandled callback

    except Exception as e:
        logger.error(f"Error processing callback data '{callback_data}' for user {user.id}: {e}", exc_info=True)
        # Attempt to inform the user about the error
        try:
            await query.edit_message_text("Произошла ошибка при обработке вашего запроса. Попробуйте вернуться в главное меню.", reply_markup=get_back_to_main_keyboard())
        except Exception as inner_e:
            logger.error(f"Failed to send error message to user {user.id} after callback error: {inner_e}")


# --- SETUP BOT APPLICATION ---
logger.info("Initializing Telegram Application builder...")
# Note: Set pool_timeout to avoid issues on platforms like Render that might reuse connections
application = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .read_timeout(7)   # Shorter timeout for read
    .write_timeout(20) # Longer for potential processing/edits
    .connect_timeout(5)
    .pool_timeout(10)  # Timeout for getting connection from pool
    .build()
)

# Register handlers BEFORE initializing
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback_handler))
# Optional: Add an error handler for uncaught exceptions within PTB
# async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
#    logger.error(msg="PTB Exception while handling an update:", exc_info=context.error)
# application.add_error_handler(error_handler)

logger.info("Telegram handlers registered.")

# --- Initialize Application ---
# This is CRUCIAL for webhook mode when not using run_polling/run_webhook.
# It performs necessary async setup for the application object.
try:
    logger.info("Running Application.initialize()...")
    # Use asyncio.run to execute the async initialize function
    asyncio.run(application.initialize()) # <--- THE CRITICAL INITIALIZATION STEP
    logger.info("Application initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize Telegram Application: {e}", exc_info=True)
    # If initialization fails, the bot cannot function correctly.
    exit("Failed application initialization. Check logs.")


# --- FLASK APP ---
app = Flask(__name__)

@app.route('/')
def index():
    """ Basic route for platform health checks. """
    logger.debug("Flask index route '/' accessed.")
    return "Flask server running for Telegram bot!"

# Define the webhook route - MUST accept POST requests
@app.route(f'/{SECRET_PATH}', methods=['POST'])
async def telegram_webhook():
    """ Endpoint to receive updates from Telegram. """
    if request.is_json:
        try:
            json_data = request.get_json(force=True)
            update = Update.de_json(json_data, application.bot)
            logger.info(f"Received update via webhook: ID {update.update_id}")

            # Process the update using the initialized Application object's handlers
            await application.process_update(update)

            # Return 200 OK to Telegram immediately after starting processing
            return Response(status=200)

        except Exception as e:
            logger.error(f"Error processing update {update.update_id if 'update' in locals() else 'unknown'} from webhook: {e}", exc_info=True)
            # Return an error status to Telegram
            return Response(f"Error processing update: {e}", status=500)
    else:
        logger.warning("Received non-JSON request on webhook endpoint.")
        return Response("Bad Request: Expected JSON", status=400)

# Optional: Route to manually set webhook (remove or secure in production)
# Use environment variable for safety if keeping this route
# ENABLE_SET_WEBHOOK = os.environ.get('ENABLE_SET_WEBHOOK', 'false').lower() == 'true'
# if ENABLE_SET_WEBHOOK:
#     @app.route('/set_webhook', methods=['GET'])
#     async def setup_webhook_route():
#         if not WEBHOOK_URL:
#             return "WEBHOOK_URL environment variable not set.", 500
#         try:
#             webhook_full_url = f"{WEBHOOK_URL}/{SECRET_PATH}"
#             logger.info(f"Attempting to set webhook via route to: {webhook_full_url}")
#             # Initialize required components before setting webhook
#             await application.bot.initialize()
#             await application.updater.initialize()
#             # Set the webhook
#             await application.updater.bot.set_webhook(url=webhook_full_url, allowed_updates=Update.ALL_TYPES)
#             logger.info(f"Webhook set successfully via route to: {webhook_full_url}")
#             # Shutdown components after setting webhook
#             await application.updater.shutdown()
#             await application.bot.shutdown()
#             return f"Webhook set to {webhook_full_url}", 200
#         except Exception as e:
#             logger.error(f"Failed to set webhook via route: {e}", exc_info=True)
#             return f"Failed to set webhook: {e}", 500


# --- MAIN EXECUTION (for Gunicorn) ---
# Gunicorn looks for the 'app' variable (the Flask instance).
# It runs the Flask app, handling incoming webhook requests via the defined routes.
logger.info("Flask app 'app' instance is ready for Gunicorn.")

if __name__ == '__main__':
    # This block is NOT executed when running with Gunicorn on Render.
    # It's useful for local development testing ONLY.
    logger.warning("Running Flask development server (for local testing only)...")
    # Note: Flask's dev server doesn't fully replicate Gunicorn's async handling,
    # but it's useful for basic testing. Use 'debug=False' for closer parity.
    app.run(host='0.0.0.0', port=PORT, debug=False)
