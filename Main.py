import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Apple Pay BIN database
apple_pay_bins = {
    "471630": {"status": "Apple Pay Friendly", "type": "Non(Auto)-VBV", "bank": "U.S. Bank"},
    "554860": {"status": "Apple Pay Friendly", "type": "Non-VBV", "bank": "Citibank, N.A. (Peru)"},
    "542000": {"status": "Apple Pay Friendly", "type": "Non-VBV", "bank": "HSBC Bank PLC (UK)"},
    "411845": {"status": "Apple Pay Friendly", "type": "Non-VBV", "bank": "Doral Bank Puerto Rico"},
    "479126": {"status": "Apple Pay Friendly", "type": "Non-VBV", "bank": "ESL F.C.U."},
    "426588": {"status": "Apple Pay Friendly", "type": "AUTO-VBV", "bank": "United Overseas Bank (Singapore)"},
    "552000": {"status": "Apple Pay Friendly", "type": "AUTO-VBV", "bank": "Citibank (Taiwan)"},
    "400261": {"status": "Apple Pay Friendly", "type": "Non-VBV", "bank": "Financiera el Comercio (Paraguay)"},
    "462730": {"status": "Apple Pay Friendly", "type": "Non-VBV", "bank": "ZAO RAIFFEISENBANK (Russia)"},
    "428258": {"status": "Apple Pay Friendly", "type": "Non-VBV", "bank": "LANDESBANK BERLIN AG"},
    "525615": {"status": "Apple Pay Friendly", "type": "Non-VBV", "bank": "VERBAND DER SPARDA BANKEN (Germany)"},
    "546812": {"status": "Apple Pay Friendly", "type": "Non-VBV", "bank": "SANTANDER CONSUMER BANK AG (Germany)"},
    "523236": {"status": "Apple Pay Friendly", "type": "Non-VBV", "bank": "SANTANDER CONSUMER BANK AG (Germany)"},
}

# BIN Database API endpoint
BIN_API_URL = "https://lookup.binlist.net/"

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        'Welcome to the BIN Checker Bot!\n\n'
        'Send me a 6-digit BIN number and I\'ll check:\n'
        '• VBV status (VBV/non-VBV/AUTO-VBV)\n'
        '• Apple Wallet compatibility\n\n'
        'Example: 471630'
    )

def check_bin(update: Update, context: CallbackContext) -> None:
    """Check the BIN number and return its VBV status and Apple Wallet compatibility."""
    bin_number = update.message.text.strip()
    
    # Validate BIN input (should be 6 digits)
    if not bin_number.isdigit() or len(bin_number) != 6:
        update.message.reply_text('Please provide a valid 6-digit BIN number.')
        return
    
    try:
        # Call the BIN API
        response = requests.get(f"{BIN_API_URL}{bin_number}")
        response.raise_for_status()
        
        bin_data = response.json()
        
        # Extract bank and card information
        bank = bin_data.get('bank', {}).get('name', 'Unknown')
        country = bin_data.get('country', {}).get('name', 'Unknown')
        card_type = bin_data.get('type', 'Unknown')
        card_brand = bin_data.get('brand', 'Unknown')
        
        # Determine VBV status based on card type and brand patterns
        vbv_status = "UNKNOWN"
        
        if card_brand.lower() in ['visa']:
            vbv_status = "AUTO-VBV"
            if "debit" in card_type.lower():
                vbv_status = "VBV"
        elif card_brand.lower() in ['mastercard']:
            vbv_status = "AUTO-VBV"
            if "credit" in card_type.lower():
                vbv_status = "NON-VBV"
        elif card_brand.lower() in ['american express']:
            vbv_status = "NON-VBV"
        
        # Check Apple Wallet compatibility
        apple_pay_status = "⚠️ Unknown - Try adding manually"
        if bin_number in apple_pay_bins:
            apple_pay_status = f"✅ Yes - {apple_pay_bins[bin_number]['type']} - Works without additional verification"
        
        # Check card brand compatibility with Apple Pay
        brand_compatible = card_brand.lower() in ['visa', 'mastercard', 'american express', 'discover']
        
        # Create the response message
        result_message = (
            f"BIN: {bin_number}\n"
            f"Bank: {bank}\n"
            f"Card Type: {card_type}\n"
            f"Brand: {card_brand}\n"
            f"Country: {country}\n"
            f"VBV Status: {vbv_status}\n"
            f"Apple Wallet: {apple_pay_status}"
        )
        
        # Add additional notes about Apple Wallet
        if bin_number not in apple_pay_bins and brand_compatible:
            result_message += (
                "\n\nℹ️ This BIN is not in our verified list, but "
                f"{card_brand} cards are generally supported by Apple Wallet. "
                "Verification requirements vary by bank."
            )
        
        update.message.reply_text(result_message)
        
    except Exception as e:
        logger.error(f"Error checking BIN: {e}")
        update.message.reply_text(f"Sorry, couldn't check this BIN. Error: {str(e)}")

def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    """Start the bot."""
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("No BOT_TOKEN provided!")
        return
    
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    
    # on message - check BIN
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, check_bin))
    
    # log all errors
    dispatcher.add_error_handler(error)
    
    # Start the Bot
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C or the process stops
    updater.idle()

if __name__ == '__main__':
    main()
