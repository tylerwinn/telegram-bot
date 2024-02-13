import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv
from paymo import calculate_pay

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I am finally awake... 1000 years I slumbered... What is your bidding, my liege?")

async def paymo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pay = calculate_pay()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=pay)

if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    start_handler = CommandHandler('start', start)
    paymo_handler = CommandHandler('paymo', paymo)
    application.add_handler(start_handler)
    application.add_handler(paymo_handler)
    
    application.run_polling()