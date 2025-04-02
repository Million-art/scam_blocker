import os
import asyncio
import logging
import json
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

def is_name_restricted(name: str) -> bool:
    """Check if name is similar to any restricted names (case-insensitive and partial match)"""
    name_lower = name.lower()
    return any(restricted.lower() in name_lower for restricted in RESTRICTED_NAMES)

def update_restricted_names(new_name: str) -> bool:
    """Update both config.json and in-memory RESTRICTED_NAMES"""
    config_path = Path(__file__).parent / "config.json"
    try:
        # Check if name already exists (case-insensitive)
        if is_name_restricted(new_name):
            return False
            
        with open(config_path, 'r+', encoding='utf-8') as f:
            config = json.load(f)
            config["restricted_names"].append(new_name)
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()
            # Update in-memory list
            global RESTRICTED_NAMES
            RESTRICTED_NAMES = config["restricted_names"]
            return True
    except Exception as e:
        logger.error(f"Error updating restricted names: {e}")
        return False

@bot.message_handler(commands=['add_restricted'])
async def add_restricted_name(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        # Extract name from command
        if len(message.text.split()) < 2:
            await bot.reply_to(message, "Usage: /add_restricted [name]")
            return
            
        name_to_add = ' '.join(message.text.split()[1:]).strip()
        
        if update_restricted_names(name_to_add):
            await bot.reply_to(message, f"✅ Added '{name_to_add}' to restricted names.")
        else:
            await bot.reply_to(message, f"⚠️ '{name_to_add}' matches an existing restricted name.")
    except Exception as e:
        logger.error(f"Error adding restricted name: {e}")
        await bot.reply_to(message, "❌ Failed to add restricted name.")

@bot.message_handler(commands=['list_restricted'])
async def list_restricted(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    if not RESTRICTED_NAMES:
        await bot.reply_to(message, "No restricted names currently set.")
        return
        
    response = "🔒 Restricted Names:\n" + "\n".join(
        f"{i+1}. {name}" for i, name in enumerate(RESTRICTED_NAMES)
    )
    await bot.reply_to(message, response)

# ... [rest of your existing handlers and server code] ...
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