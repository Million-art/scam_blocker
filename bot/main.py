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

# Load config from root folder (go up one level from bot/ folder)
CONFIG_PATH = Path(__file__).parent.parent / "config.json"

def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found at {CONFIG_PATH}")
        # Create default config if doesn't exist
        default_config = {
            "restricted_names": [],
            "admin_ids": []
        }
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    except json.JSONDecodeError:
        logger.error("Invalid JSON in config file")
        raise
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise

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
    """Check for exact match (case-insensitive)"""
    name_lower = name.lower()
    return any(restricted.lower() == name_lower for restricted in RESTRICTED_NAMES)

def name_conflicts(name: str) -> bool:
    """Check for partial matches before adding new names"""
    name_lower = name.lower()
    return any(name_lower in restricted.lower() or restricted.lower() in name_lower
              for restricted in RESTRICTED_NAMES)

def update_restricted_names(new_name: str) -> bool:
    """Update config.json and in-memory list"""
    try:
        if name_conflicts(new_name):
            return False
            
        # Update in-memory list first
        global RESTRICTED_NAMES
        RESTRICTED_NAMES.append(new_name)
        
        # Update config file
        config["restricted_names"] = RESTRICTED_NAMES
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
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

# ... [rest of your handlers] ...

if __name__ == "__main__":
    logger.info("Starting bot with polling...")
    asyncio.run(bot.polling())