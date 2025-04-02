import os
import asyncio
import logging
import json
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler
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

# Create bot instance
bot = AsyncTeleBot(TOKEN)

# Start command handler
@bot.message_handler(commands=['start'])
async def start(message):
    await bot.reply_to(message, "Hello! I am a group manager bot.")

# Message handler
@bot.message_handler(func=lambda message: True)
async def handle_all_messages(message):
    # You'll need to implement or import your check_full_name_and_ban function
    await check_full_name_and_ban(message,bot)

# # Run the bot with polling
# if __name__ == "__main__":
#     logger.info("Starting bot with polling...")
#     asyncio.run(bot.polling())

# HTTP handler for Vercel
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update_dict = json.loads(post_data.decode('utf-8'))

        asyncio.run(self.process_update(update_dict))

        self.send_response(200)
        self.end_headers()

    async def process_update(self, update_dict):
        update = types.Update.de_json(update_dict)
        await bot.process_new_updates([update])

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('Hello, BOT is running!'.encode('utf-8'))