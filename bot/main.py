import os
import asyncio
import json
import logging
from pathlib import Path
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler
from bot.handler.ban_handler import check_full_name_and_ban, check_user_on_join
from config import RESTRICTED_NAMES, ADMIN_IDS

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

def update_restricted_names(new_name: str):
    """Update both config.json and in-memory RESTRICTED_NAMES"""
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, 'r+', encoding='utf-8') as f:
            config = json.load(f)
            if new_name.lower() not in [n.lower() for n in config["restricted_names"]]:
                config["restricted_names"].append(new_name)
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()
                # Update in-memory list
                global RESTRICTED_NAMES
                RESTRICTED_NAMES = config["restricted_names"]
                return True
        return False
    except Exception as e:
        logger.error(f"Error updating restricted names: {e}")
        return False

# Admin command to add restricted names
@bot.message_handler(commands=['add_restricted'])
async def add_restricted_name(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        name_to_add = message.text.split(' ', 1)[1].strip()
        if not name_to_add:
            await bot.reply_to(message, "Usage: /add_restricted [name]")
            return

        if update_restricted_names(name_to_add):
            await bot.reply_to(message, f"✅ Added '{name_to_add}' to restricted names.")
        else:
            await bot.reply_to(message, f"⚠️ '{name_to_add}' is already restricted.")
    except IndexError:
        await bot.reply_to(message, "Usage: /add_restricted [name]")
    except Exception as e:
        logger.error(f"Error adding restricted name: {e}")
        await bot.reply_to(message, "❌ Failed to add restricted name.")

# Start command handler
@bot.message_handler(commands=['start'])
async def start(message):
    help_text = (
        "Hello! I am a group manager bot.\n\n"
        "Admin commands:\n"
        "/add_restricted [name] - Add a restricted name\n"
        "/list_restricted - Show current restricted names"
    )
    await bot.reply_to(message, help_text)

# List restricted names command
@bot.message_handler(commands=['list_restricted'])
async def list_restricted(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    names_list = "\n".join(RESTRICTED_NAMES) or "No restricted names set"
    await bot.reply_to(message, f"🔒 Restricted Names:\n{names_list}")

# Message handler
@bot.message_handler(func=lambda message: True)
async def handle_all_messages(message):
    await check_full_name_and_ban(message, bot)

# New user join handler
@bot.chat_member_handler()
async def on_user_join(update: types.ChatMemberUpdated):
    if update.new_chat_member and update.new_chat_member.status == "member":
        await check_user_on_join(update.new_chat_member.user, update.chat, bot)

 
# Start bot in polling mode if running locally
if __name__ == "__main__":
    logger.info("Starting bot with polling...")
    asyncio.run(bot.polling())