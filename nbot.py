# --- IMPORTS ---
import logging
import os
import asyncio # Needed for async operations within Flask routes
from flask import Flask, request, Response # Added request and Response
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, TypeHandler
# --- Keyboard Imports ---
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical("FATAL ERROR: TELEGRAM_BOT_TOKEN environment variable not set.")
    exit("Bot token not found. Exiting.")

# The public URL assigned by Render (set as an environment variable)
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
if not WEBHOOK_URL:
    logging.warning("WARNING: WEBHOOK_URL environment variable not set. Webhook setup will fail.")
    # You might want to exit here in production if the webhook URL is essential at startup
    # exit("WEBHOOK_URL not found. Exiting.")

# Secret path segment to ensure requests come from Telegram (optional but recommended)
# Should be hard to guess, like the bot token itself or a UUID
SECRET_PATH = TELEGRAM_BOT_TOKEN # Using the token as the path is common practice

# Render provides the PORT environment variable
PORT = int(os.environ.get('PORT', 8080)) # Default if run locally

# --- Constants ---
DEFAULT_SERVICE_URL = "https://shodrop.io"
SUPPORT_CONTACT_INFO = "Для связи с поддержкой напишите @SHODROP_SUPPORT"

# --- LOGGING SETUP ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- DATA / TEXTS / KEYBOARDS ---
# (Keep all your SERVICE_DATA, message texts, and keyboard functions exactly the same)
SERVICE_DATA = {
    'main_web_dev': {"title": "1️⃣ Разработка веб-сайта", "url": f"{DEFAULT_SERVICE_URL}/web-development"},
    'main_shopify': {"title": "2️⃣ Магазин под ключ на Shopify", "url": f"{DEFAULT_SERVICE_URL}/shopify-store"},
    'main_targeting': {"title": "4️⃣ Настройка таргетированной рекламы", "url": f"{DEFAULT_SERVICE_URL}/targeted-ads"},
    # ... etc
}
MAIN_MENU_TEXT = """..."""
PAYMENT_SYSTEMS_TEXT = "..."
SOCIAL_MEDIA_TEXT = "..."
def get_main_menu_keyboard():
    # ... (same as before)
    keyboard = [ ... ]
    return InlineKeyboardMarkup(keyboard)
def get_payment_systems_keyboard():
    # ... (same as before)
    keyboard = [ ... ]
    return InlineKeyboardMarkup(keyboard)
# ... other keyboard functions ...


# --- TELEGRAM BOT HANDLERS ---
# (Keep your start() and button_callback_handler() async functions exactly the same)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (same logic as before)
    user = update.effective_user
    logger.info(f"[Webhook] User {user.id} ({user.username}) started.")
    message = update.message or (update.callback_query and update.callback_query.message)
    # ... rest of start logic ...

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (same logic as before)
    query = update.callback_query
    user = query.from_user
    logger.info(f"[Webhook] User {user.id} ({user.username}) clicked: {query.data}")
    # ... rest of button_callback_handler logic ...


# --- SETUP BOT APPLICATION (without polling/webhook setup here) ---
# We initialize the application first, then set up handlers.
# The webhook connection happens via the Flask route.
logger.info("Initializing Telegram Application...")
application = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .read_timeout(30) # Optional: Adjust timeouts if needed
    .write_timeout(30)
    .build()
)

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback_handler))
# Optional: Add an error handler
# async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
#    logger.error(msg="Exception while handling an update:", exc_info=context.error)
# application.add_error_handler(error_handler)

logger.info("Telegram handlers registered.")


# --- FLASK APP ---
app = Flask(__name__)

@app.route('/')
def index():
    """ Basic route for health checks. """
    logger.info("Flask index route accessed.")
    return "Flask server is running for Telegram Bot!"

# Define the webhook route - MUST accept POST requests
@app.route(f'/{SECRET_PATH}', methods=['POST'])
async def telegram_webhook():
    """ Endpoint to receive updates from Telegram. """
    if request.is_json:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        logger.debug(f"Received update via webhook: ID {update.update_id}")
        try:
            # Process the update using the Application object's handlers
            await application.process_update(update)
            # Return 200 OK to Telegram to acknowledge receipt
            return Response(status=200)
        except Exception as e:
            logger.error(f"Error processing update {update.update_id}: {e}", exc_info=True)
            # Return an error status to Telegram if processing fails
            return Response(f"Error processing update: {e}", status=500)
    else:
        logger.warning("Received non-JSON request on webhook endpoint.")
        return Response("Bad Request: Expected JSON", status=400)

# Optional: Route to manually trigger webhook setup (USE WITH CAUTION)
# @app.route('/set_webhook', methods=['GET'])
# async def setup_webhook_route():
#     if not WEBHOOK_URL:
#         return "WEBHOOK_URL environment variable not set.", 500
#     try:
#         webhook_full_url = f"{WEBHOOK_URL}/{SECRET_PATH}"
#         await application.bot.set_webhook(url=webhook_full_url, allowed_updates=Update.ALL_TYPES)
#         logger.info(f"Webhook set successfully to: {webhook_full_url}")
#         return f"Webhook set to {webhook_full_url}", 200
#     except Exception as e:
#         logger.error(f"Failed to set webhook: {e}", exc_info=True)
#         return f"Failed to set webhook: {e}", 500

# --- MAIN EXECUTION (for Gunicorn) ---
# Gunicorn looks for the 'app' variable (the Flask instance).
# It will run the Flask app, which handles incoming webhook requests.
# No need for threads or explicit polling calls here.
logger.info("Flask app 'app' created and configured.")
if __name__ == '__main__':
    # This block is mainly for local testing, Gunicorn won't run it directly.
    # You would run Flask's development server locally:
    # logger.info(f"Starting Flask development server on port {PORT}...")
    # app.run(host='0.0.0.0', port=PORT, debug=True) # debug=True for local dev
    pass # Gunicorn handles running the 'app' instance in production