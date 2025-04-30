import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Configuration ---
TELEGRAM_BOT_TOKEN = "7593178773:AAEKhP2sioAJk-yKUwSxXh34WoLDv9ILnB4"  # Replace with your actual bot token
DEFAULT_SERVICE_URL = "https://shodrop.io" # Fallback/Example URL
SUPPORT_CONTACT_INFO = "Для связи с поддержкой напишите @SHODROP_SUPPORT" # Your support info

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Service Data (Title and URL mapping) ---
# Store service info for easy access
SERVICE_DATA = {
    'main_web_dev': {"title": "1️⃣ Разработка веб-сайта", "url": f"{DEFAULT_SERVICE_URL}/web-dev"}, # Replace with actual URLs
    'main_shopify': {"title": "2️⃣ Магазин под ключ на Shopify", "url": f"{DEFAULT_SERVICE_URL}/shopify"},
    # 'main_payment' is handled separately as it has its own menu
    'main_targeting': {"title": "4️⃣ Настройка таргетированной рекламы", "url": f"{DEFAULT_SERVICE_URL}/targeting"},
    'main_seo': {"title": "5️⃣ SEO-оптимизация сайта", "url": f"{DEFAULT_SERVICE_URL}/seo"},
    'main_context': {"title": "6️⃣ Контекстная реклама", "url": f"{DEFAULT_SERVICE_URL}/context"},
    'main_creative': {"title": "7️⃣ Видео-креативы и карточки товаров", "url": f"{DEFAULT_SERVICE_URL}/creative"},
    'main_registration': {"title": "8️⃣ Регистрация компании за рубежом", "url": f"{DEFAULT_SERVICE_URL}/registration"},
}


# --- Keyboard Definitions ---

def get_main_menu_keyboard():
    keyboard = [
        # Use titles directly from SERVICE_DATA for consistency
        [InlineKeyboardButton(SERVICE_DATA['main_web_dev']['title'], callback_data='main_web_dev')],
        [InlineKeyboardButton(SERVICE_DATA['main_shopify']['title'], callback_data='main_shopify')],
        [InlineKeyboardButton("3️⃣ Подключение платежной системы", callback_data='main_payment')], # Keep payment separate
        [InlineKeyboardButton(SERVICE_DATA['main_targeting']['title'], callback_data='main_targeting')],
        [InlineKeyboardButton(SERVICE_DATA['main_seo']['title'], callback_data='main_seo')],
        [InlineKeyboardButton(SERVICE_DATA['main_context']['title'], callback_data='main_context')],
        [InlineKeyboardButton(SERVICE_DATA['main_creative']['title'], callback_data='main_creative')],
        [InlineKeyboardButton(SERVICE_DATA['main_registration']['title'], callback_data='main_registration')],
        [InlineKeyboardButton("🌐 Наши соц. сети", callback_data='main_social')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_systems_keyboard():
    # (Keep this as defined in the previous example)
    keyboard = [
        [InlineKeyboardButton("Stripe 💳", callback_data='payment_stripe')],
        [InlineKeyboardButton("Shopify Payments 💳", callback_data='payment_shopify')],
        [InlineKeyboardButton("Отзывы ✅", callback_data='payment_reviews')],
        [InlineKeyboardButton("💬 Есть вопрос? Связаться с поддержкой", callback_data='support_payment')], # Specific support CB
        [InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_service_detail_keyboard(service_key):
    """Generates the 3-button keyboard for a specific service."""
    service_info = SERVICE_DATA.get(service_key)
    if not service_info:
        # Fallback if key not found (shouldn't happen with proper routing)
        logger.warning(f"Service key {service_key} not found in SERVICE_DATA")
        service_url = DEFAULT_SERVICE_URL
    else:
        service_url = service_info.get('url', DEFAULT_SERVICE_URL)

    # Create a specific support callback for this service
    support_callback = f"support_{service_key.split('_')[-1]}" # e.g., support_shopify

    keyboard = [
        [InlineKeyboardButton("Подробнее 🔥", url=service_url)],
        [InlineKeyboardButton("💬 Есть вопрос? Связаться с поддержкой", callback_data=support_callback)],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_keyboard():
    """Simple keyboard with only a 'Back to Main Menu' button."""
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')]]
    return InlineKeyboardMarkup(keyboard)

# --- Message Texts ---

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

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the welcome message with the main menu."""
    # Check if message exists to edit, otherwise send new
    if update.message:
         await update.message.reply_text(
            text=MAIN_MENU_TEXT,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )
    # If called from a callback query (like 'back_to_main'), edit the message
    elif update.callback_query and update.callback_query.message:
         await update.callback_query.edit_message_text(
            text=MAIN_MENU_TEXT,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )


# --- Callback Query Handler ---

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    callback_data = query.data
    text = ""
    keyboard = None

    # --- Routing ---
    if callback_data == 'back_to_main':
        # Use the start function logic to show the main menu again
        await start(update, context)
        return # Stop further processing in this handler

    elif callback_data == 'main_payment':
        text = PAYMENT_SYSTEMS_TEXT
        keyboard = get_payment_systems_keyboard()

    elif callback_data == 'main_social':
        text = SOCIAL_MEDIA_TEXT
        keyboard = get_back_to_main_keyboard() # Only Back button needed

    # Handle clicks on specific service buttons from the main menu
    elif callback_data in SERVICE_DATA:
        service_info = SERVICE_DATA[callback_data]
        # Use cleaner title without the number emoji for the detail view
        text = service_info['title'].split(' ', 1)[1] if ' ' in service_info['title'] else service_info['title']
        keyboard = get_service_detail_keyboard(callback_data)

    # Handle clicks on "Contact Support" from a service detail view
    elif callback_data.startswith('support_'):
        text = SUPPORT_CONTACT_INFO
        keyboard = get_back_to_main_keyboard() # Back to main menu after support info

    # --- Payment Systems Sub-menu Logic (Example) ---
    elif callback_data == 'payment_stripe':
        text = "Информация о подключении Stripe..." # Replace with actual info
        # You might want a different keyboard here, maybe linking to stripe details and back to payment menu
        keyboard = InlineKeyboardMarkup([
             [InlineKeyboardButton("Подробнее 🔥", url=f"{DEFAULT_SERVICE_URL}/stripe")], # Example URL
             [InlineKeyboardButton("◀️ Назад к платежным системам", callback_data='main_payment')]
        ])
    elif callback_data == 'payment_shopify':
        text = "Информация о Shopify Payments..." # Replace with actual info
        keyboard = InlineKeyboardMarkup([
             [InlineKeyboardButton("Подробнее 🔥", url=f"{DEFAULT_SERVICE_URL}/shopify-payments")], # Example URL
             [InlineKeyboardButton("◀️ Назад к платежным системам", callback_data='main_payment')]
        ])
    elif callback_data == 'payment_reviews':
        text = "Здесь будут отзывы о нашей работе с платежными системами..." # Replace
        keyboard = InlineKeyboardMarkup([
             # [InlineKeyboardButton("Посмотреть Отзывы", url=f"{DEFAULT_SERVICE_URL}/reviews")], # Example URL
             [InlineKeyboardButton("◀️ Назад к платежным системам", callback_data='main_payment')]
        ])
    # Support specifically for payment section
    elif callback_data == 'support_payment':
         text = SUPPORT_CONTACT_INFO
         keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад к платежным системам", callback_data='main_payment')]])


    # --- Edit the message ---
    if text and keyboard:
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML' # Optional
        )
    elif text: # Handle cases where only text might change
         await query.edit_message_text(text=text, parse_mode='HTML')
    else:
        logger.warning(f"No action defined for callback_data: {callback_data}")


# --- Main Bot Execution ---

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback_handler))

    print("Bot starting...")
    application.run_polling()
    print("Bot stopped.")

if __name__ == "__main__":
    main()