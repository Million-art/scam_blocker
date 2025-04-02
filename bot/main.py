import os
import asyncio
import logging
import json
from pathlib import Path
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv
from bot.handler.ban_handler import check_full_name_and_ban, check_user_on_join

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info("Bot is starting...")

# Load config from root folder
CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# Initialize config
config = load_config()
RESTRICTED_NAMES = config.get("restricted_names", [])
ADMIN_IDS = config.get("admin_ids", [])

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Create bot instance
bot = AsyncTeleBot(TOKEN)

def is_name_restricted(name: str) -> bool:
    """Check if name is similar to any restricted names (case-insensitive)"""
    name_lower = name.lower()
    return any(restricted.lower() == name_lower for restricted in RESTRICTED_NAMES)

def name_exists_in_restricted(name: str) -> bool:
    """Check for partial matches (used before adding new names)"""
    name_lower = name.lower()
    return any(name_lower in restricted.lower() or restricted.lower() in name_lower 
              for restricted in RESTRICTED_NAMES)

def update_restricted_names(new_name: str) -> bool:
    """Update both config.json and in-memory RESTRICTED_NAMES"""
    try:
        if name_exists_in_restricted(new_name):
            return False
            
        with open(CONFIG_PATH, 'r+', encoding='utf-8') as f:
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
        if len(message.text.split()) < 2:
            await bot.reply_to(message, "Usage: /add_restricted [name]")
            return
            
        name_to_add = ' '.join(message.text.split()[1:]).strip()
        
        if update_restricted_names(name_to_add):
            await bot.reply_to(message, f"✅ Added '{name_to_add}' to restricted names.")
        else:
            await bot.reply_to(message, f"⚠️ '{name_to_add}' conflicts with existing restricted name.")
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

@bot.message_handler(commands=['start'])
async def start(message):
    await bot.reply_to(message, "Hello! I am a group manager bot.")

@bot.message_handler(func=lambda message: True)
async def handle_all_messages(message):
    await check_full_name_and_ban(message, bot)

@bot.chat_member_handler()
async def on_user_join(update: types.ChatMemberUpdated):
    if update.new_chat_member and update.new_chat_member.status == "member":
        await check_user_on_join(update.new_chat_member.user, update.chat, bot)

if __name__ == "__main__":
    logger.info("Starting bot with polling...")
    asyncio.run(bot.polling())