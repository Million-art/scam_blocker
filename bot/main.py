import os
import asyncio
import logging
import json
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler
from bot.handler.ban_handler import check_full_name_and_ban, check_user_on_join

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

# Load initial configuration
def load_config():
    with open('config.json') as config_file:
        return json.load(config_file)

config = load_config()
ADMIN_IDS = config['admin_ids']

# Start command handler
@bot.message_handler(commands=['start'])
async def start(message):
    logger.debug(f"Received /start command from user {message.from_user.id}")
    await bot.reply_to(message, "Hello! I am a group manager bot.")

# Command to add restricted names
@bot.message_handler(commands=['add_restricted_name'])
async def add_restricted_name(message):
    user = message.from_user
    logger.debug(f"Received /add_restricted_name command from user {user.id}")
    if user.id not in ADMIN_IDS:
        await bot.reply_to(message, "You do not have permission to use this command.")
        return

    args = message.text.split(None, 1)
    if len(args) < 2:
        await bot.reply_to(message, "Usage: /add_restricted_name <name>")
        return

    new_name = args[1].strip().lower()
    config = load_config()
    if new_name in config['restricted_names']:
        await bot.reply_to(message, "This name is already restricted.")
        return

    config['restricted_names'].append(new_name)
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)

    await bot.reply_to(message, f"Restricted name '{new_name}' added successfully.")

# Message handler
@bot.message_handler(func=lambda message: True)
async def handle_all_messages(message: types.Message):
    logger.debug(f"Received message from user {message.from_user.id}: {message.text}")
    await check_full_name_and_ban(message, bot)

    # Log the message
    log_message(message)

def log_message(message: types.Message):
    # Get user's name parts
    name_parts = [
        message.from_user.first_name or '',
        message.from_user.last_name or '',
        message.from_user.username or ''
    ]
    full_name = " ".join(name_parts).strip()

    # Log the message with user details
    logger.info(f"Message from {full_name} ({message.from_user.id}): {message.text}")
# New user join handler
@bot.chat_member_handler()
async def on_user_join(update: types.ChatMemberUpdated):
    logger.debug(f"Received new user join update: {update}")
    if update.new_chat_member and update.new_chat_member.status == "member":
        await check_user_on_join(update.new_chat_member.user, update.chat, bot)

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
 