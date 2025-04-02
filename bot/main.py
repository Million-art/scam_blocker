import os
import asyncio
import logging
import json
import re
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler

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

# Function to check if a user's name matches the group name and ban them
async def check_user_on_join(user: types.User, chat: types.Chat):
    if not chat or not user:
        return
    
    # Get the group name (remove special characters)
    group_name = re.sub(r'[^\w\s]', '', chat.title).strip().lower() if chat.title else ""

    # Get user's name parts
    name_parts = [
        user.first_name or '',
        user.last_name or '',
        user.username or ''
    ]
    full_name = " ".join(name_parts).strip().lower()

    # Check if user's name matches group name
    if group_name and (
        full_name == group_name or
        group_name in full_name or
        "".join(word[0] for word in group_name.split()) in full_name
    ):
        try:
            # Ban the user
            await bot.ban_chat_member(chat.id, user.id, revoke_messages=True)

            # Notify the group
            await bot.send_message(
                chat.id,
                f"🚨 User {user.first_name} was banned for violating group naming policies."
            )

        except Exception as e:
            logger.error(f"Error banning user {user.id}: {e}")

# Handle new members joining
@bot.message_handler(content_types=['new_chat_members'])
async def handle_new_members(message):
    for user in message.new_chat_members:
        await check_user_on_join(user, message.chat)

# Start command handler
@bot.message_handler(commands=['start'])
async def start(message):
    await bot.reply_to(message, "Hello! I am a group manager bot.")

# Handle messages (for normal messages)
@bot.message_handler(func=lambda message: True)
async def handle_all_messages(message):
    await check_user_on_join(message.from_user, message.chat)

# Run the bot with polling
if __name__ == "__main__":
    logger.info("Starting bot with polling...")
    asyncio.run(bot.polling())

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
