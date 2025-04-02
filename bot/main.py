# bot/main.py
import os
import asyncio
import logging
import json
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv
from bot.handler.ban_handler import check_full_name_and_ban, check_user_on_join

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

bot = AsyncTeleBot(TOKEN)

# Cached configuration
_config = None
def load_config():
    global _config
    if _config is None:
        with open('bot/config.json') as config_file:
            _config = json.load(config_file)
    return _config

# Bot handlers
@bot.message_handler(commands=['start'])
async def start(message):
    try:
        await bot.reply_to(message, "🚀 Bot is operational!")
    except Exception as e:
        logger.error(f"Start command error: {e}")

@bot.message_handler(commands=['add_restricted_name'])
async def add_restricted_name(message):
    try:
        user = message.from_user
        config = load_config()
        
        if user.id not in config['admin_ids']:
            await bot.reply_to(message, "❌ Admin access required")
            return

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await bot.reply_to(message, "📝 Usage: /add_restricted_name <name>")
            return

        new_name = args[1].strip().lower()
        if new_name in config['restricted_names']:
            await bot.reply_to(message, "⚠️ Name already restricted")
            return

        config['restricted_names'].append(new_name)
        with open('bot/config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        await bot.reply_to(message, f"✅ Added: {new_name}")
    except Exception as e:
        logger.error(f"Add name error: {e}")

@bot.message_handler(func=lambda message: True)
async def handle_messages(message):
    try:
        await check_full_name_and_ban(message, bot)
    except Exception as e:
        logger.error(f"Message handling error: {e}")

@bot.chat_member_handler()
async def handle_new_members(update):
    try:
        if update.new_chat_member.status == "member":
            await check_user_on_join(update.new_chat_member.user, update.chat, bot)
    except Exception as e:
        logger.error(f"Member update error: {e}")

# Vercel handler
async def handler(request):
    if request.method == 'GET':
        return {'statusCode': 200, 'body': 'Bot active'}
    
    try:
        body = request.body
        update = types.Update.de_json(json.loads(body))
        await bot.process_new_updates([update])
        return {'statusCode': 200, 'body': 'Update processed'}
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {'statusCode': 500, 'body': str(e)}

# Local development
if __name__ == "__main__":
    logger.info("Starting in polling mode...")
    asyncio.run(bot.polling())