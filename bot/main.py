import os
import asyncio
import logging
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info("Bot is starting...")

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Create bot instance
bot = AsyncTeleBot(TOKEN)

# Only start command handler remains
@bot.message_handler(commands=['start'])
async def start(message):
    await bot.reply_to(message, "Hello! I am a simple bot that only responds to /start commands.")

# For local testing with polling
async def run_polling():
    logger.info("Starting bot with polling...")
    await bot.polling()

if __name__ == "__main__":
    asyncio.run(run_polling())