# --- IMPORTS ---
import logging
import os
# No 'import asyncio' needed here anymore
from flask import Flask, request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical("FATAL ERROR: TELEGRAM_BOT_TOKEN environment variable not set.")
    exit("Bot token not found. Exiting.")

WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
if not WEBHOOK_URL:
    logging.warning("WARNING: WEBHOOK_URL environment variable not set. Webhook setup must be done manually or via other means.")

SECRET_PATH = TELEGRAM_BOT_TOKEN
PORT = int(os.environ.get('PORT', 8080))

# --- Constants ---
DEFAULT_SERVICE_URL = "https://shodrop.io"
SUPPORT_CONTACT_INFO = "Для связи с поддержкой напишите @SHODROP_SUPPORT"

# --- LOGGING SETUP ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

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
# (All get_..._keyboard functions remain exactly the same as before)
def get_main_menu_keyboard():
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
    keyboard = [
        [InlineKeyboardButton("Stripe 💳", callback_data='payment_stripe')],
        [InlineKeyboardButton("Shopify Payments 💳", callback_data='payment_shopify')],
        [InlineKeyboardButton("Отзывы ✅", callback_data='payment_reviews')],
        [InlineKeyboardButton("💬 Есть вопрос? Связаться с поддержкой", callback_data='support_payment')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_service_detail_keyboard(service_key):
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
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')]]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_payments_keyboard():
    keyboard = [[InlineKeyboardButton("◀️ Назад к платежным системам", callback_data='main_payment')]]
    return InlineKeyboardMarkup(keyboard)

# --- TELEGRAM BOT HANDLERS (async def functions) ---
# (start and button_callback_handler functions remain exactly the same as before)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"[Handler /start] User {user.id} ({user.username or 'NoUsername'}) initiated.")
    message = update.message or (update.callback_query and update.callback_query.message)
    if not message:
        logger.warning("Start command received without a message context.")
        return
    text = MAIN_MENU_TEXT
    keyboard = get_main_menu_keyboard()
    try:
        if update.callback_query:
            logger.info(f"Editing message {message.message_id} for user {user.id} to main menu.")
            await message.edit_text(text=text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)
        elif update.message:
             logger.info(f"Replying to message {message.message_id} for user {user.id} with main menu.")
             await message.reply_text(text=text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in start handler for user {user.id}: {e}", exc_info=True)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.message:
        logger.warning("Callback query received without query or message object.")
        return
    message = query.message
    user = query.from_user
    try:
        # Still attempt to answer, but be prepared for potential loop issues if they persist
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query {query.id} for user {user.id}: {e}") # Log warning instead of error now

    callback_data = query.data
    logger.info(f"[Handler Callback] User {user.id} ({user.username or 'NoUsername'}) clicked: {callback_data}. Message ID: {message.message_id}")
    text = ""
    keyboard = None
    try:
        # --- Routing ---
        if callback_data == 'back_to_main': await start(update, context); return
        elif callback_data == 'main_payment': text = PAYMENT_SYSTEMS_TEXT; keyboard = get_payment_systems_keyboard()
        elif callback_data == 'main_social': text = SOCIAL_MEDIA_TEXT; keyboard = get_back_to_main_keyboard()
        elif callback_data in SERVICE_DATA:
            service_info = SERVICE_DATA[callback_data]
            clean_title = service_info['title'].split(' ', 1)[-1] if ' ' in service_info['title'] else service_info['title']
            text = f"Услуга: {clean_title}"; keyboard = get_service_detail_keyboard(callback_data)
        elif callback_data.startswith('support_'):
            text = SUPPORT_CONTACT_INFO
            keyboard = get_back_to_payments_keyboard() if callback_data == 'support_payment' else get_back_to_main_keyboard()
        elif callback_data == 'payment_stripe': text = "Подключение Stripe..."; keyboard = InlineKeyboardMarkup([ ... ]) # Fill details
        elif callback_data == 'payment_shopify': text = "Shopify Payments..."; keyboard = InlineKeyboardMarkup([ ... ]) # Fill details
        elif callback_data == 'payment_reviews': text = "Отзывы..."; keyboard = InlineKeyboardMarkup([ ... ]) # Fill details
        else: logger.warning(f"Unhandled callback_data '{callback_data}' from user {user.id}"); return
        # --- Edit ---
        if text and keyboard:
             logger.info(f"Editing message {message.message_id} for user {user.id}. New text: '{text[:30]}...'")
             await message.edit_text(text=text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)
        elif text:
            logger.info(f"Editing message {message.message_id} for user {user.id} (text only). New text: '{text[:30]}...'")
            await message.edit_text(text=text, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error processing callback data '{callback_data}' for user {user.id}: {e}", exc_info=True)
        try: await query.edit_message_text("Произошла ошибка.", reply_markup=get_back_to_main_keyboard())
        except Exception as inner_e: logger.error(f"Failed to send error msg after callback error: {inner_e}")

# --- SETUP BOT APPLICATION ---
logger.info("Initializing Telegram Application builder...")
application = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .read_timeout(7)
    .write_timeout(20)
    .connect_timeout(5)
    .pool_timeout(10)
    .build()
)

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback_handler))
logger.info("Telegram handlers registered.")

# NO explicit application.initialize() call here anymore

# --- FLASK APP ---
app = Flask(__name__)

@app.route('/')
def index():
    logger.debug("Flask index route '/' accessed.")
    return "Flask server running for Telegram bot!"

@app.route(f'/{SECRET_PATH}', methods=['POST'])
async def telegram_webhook():
    if request.is_json:
        update = None # Initialize update to None
        try:
            json_data = request.get_json(force=True)
            update = Update.de_json(json_data, application.bot)
            logger.info(f"Received update via webhook: ID {update.update_id}")
            await application.process_update(update)
            return Response(status=200)
        except Exception as e:
            update_id_str = update.update_id if update else 'unknown'
            logger.error(f"Error processing update {update_id_str} from webhook: {e}", exc_info=True)
            return Response(f"Error processing update: {e}", status=500)
    else:
        logger.warning("Received non-JSON request on webhook endpoint.")
        return Response("Bad Request: Expected JSON", status=400)

# --- MAIN EXECUTION (for Gunicorn) ---
logger.info("Flask app 'app' instance is ready for Gunicorn.")

if __name__ == '__main__':
    # For local testing ONLY. Not used by Gunicorn on Render.
    logger.warning("Running Flask development server (for local testing only)...")
    app.run(host='0.0.0.0', port=PORT, debug=False)
