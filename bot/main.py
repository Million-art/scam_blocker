import os
import asyncio
import logging
import json
from pathlib import Path
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv
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

def is_name_exist(name: str) -> bool:
    """Check for exact match (case-insensitive)"""
    name_lower = name.lower()
    return any(existing.lower() == name_lower for existing in RESTRICTED_NAMES)

def update_config():
    """Save current RESTRICTED_NAMES to config.json"""
    config_path = Path(__file__).parent.parent / "config.json"
    try:
        with open(config_path, 'r+', encoding='utf-8') as f:
            config = json.load(f)
            config["restricted_names"] = RESTRICTED_NAMES
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()
        return True
    except Exception as e:
        logger.error(f"Error updating config: {e}")
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
        
        if is_name_exist(name_to_add):
            await bot.reply_to(message, f"⚠️ '{name_to_add}' already exists in restricted names.")
            return
            
        RESTRICTED_NAMES.append(name_to_add)
        if update_config():
            await bot.reply_to(message, f"✅ Added '{name_to_add}' to restricted names.")
        else:
            RESTRICTED_NAMES.remove(name_to_add)  # Revert if save fails
            await bot.reply_to(message, "❌ Failed to save configuration.")
    except Exception as e:
        logger.error(f"Error adding restricted name: {e}")
        await bot.reply_to(message, "❌ Failed to add restricted name.")

@bot.message_handler(commands=['remove_restricted'])
async def remove_restricted_name(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        if len(message.text.split()) < 2:
            await bot.reply_to(message, "Usage: /remove_restricted [name]")
            return
            
        name_to_remove = ' '.join(message.text.split()[1:]).strip()
        
        # Find case-insensitive match
        found_name = next(
            (name for name in RESTRICTED_NAMES if name.lower() == name_to_remove.lower()),
            None
        )
        
        if not found_name:
            await bot.reply_to(message, f"⚠️ '{name_to_remove}' not found in restricted names.")
            return
            
        RESTRICTED_NAMES.remove(found_name)
        if update_config():
            await bot.reply_to(message, f"✅ Removed '{found_name}' from restricted names.")
        else:
            RESTRICTED_NAMES.append(found_name)  # Revert if save fails
            await bot.reply_to(message, "❌ Failed to save configuration.")
    except Exception as e:
        logger.error(f"Error removing restricted name: {e}")
        await bot.reply_to(message, "❌ Failed to remove restricted name.")

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

# Start command handler
@bot.message_handler(commands=['start'])
async def start(message):
    help_text = (
        "Hello! I am a group manager bot.\n\n"
        "Admin commands:\n"
        "/add_restricted [name] - Add a restricted name\n"
        "/list_restricted - Show current restricted names\n"
        "/remove_restricted - remove current restricted names"
    )
    await bot.reply_to(message, help_text)

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