import os
import asyncio
import logging
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from bot.handler.ban_handler import check_full_name_and_ban

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info("Bot is starting...")

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Create bot instance (global for webhook)
bot = AsyncTeleBot(TOKEN)

# Start command handler
@bot.message_handler(commands=['start'])
async def start(message):
    await bot.reply_to(message, "Hello! I am a group manager bot.")

# Message handler
@bot.message_handler(func=lambda message: True)
async def handle_all_messages(message):
    await check_full_name_and_ban(message, bot)

# For local testing with polling
async def run_polling():
    logger.info("Starting bot with polling...")
    await bot.polling()

if __name__ == "__main__":
    asyncio.run(run_polling())