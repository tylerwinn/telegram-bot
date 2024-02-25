import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv
from paymo import calculate_pay, calculate_average_hours_per_pay_period
from datetime import datetime

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I am finally awake... 1000 years I slumbered... What is your bidding, my liege?")

async def paymo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #if a parameter is passd, it is the previous period
    previous_period = True
    args = context.args
    if len(args) > 0:
        if args[0] == "current":
            previous_period = False
        if args[0] == "average":
            if len(args) > 1:
                if args[1].isdigit():
                    year = int(args[1])
                    average = calculate_average_hours_per_pay_period(year)
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=average)
                    return
            else:
                year = datetime.now().year
                average = calculate_average_hours_per_pay_period(year)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=average)
                return

    
    pay = calculate_pay(previous_period=previous_period, use_est=False)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=pay)

if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    start_handler = CommandHandler('start', start)
    paymo_handler = CommandHandler('paymo', paymo)
    application.add_handler(start_handler)
    application.add_handler(paymo_handler)
    
    application.run_polling()
