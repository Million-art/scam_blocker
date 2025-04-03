import os
import asyncio
import logging
import json
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from dotenv import load_dotenv
from bot.handler.ban_handler import check_full_name_and_ban, check_user_on_join
import firebase_admin
from firebase_admin import credentials, firestore

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info("Bot is starting...")

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Initialize Firebase
firebase_config = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Create bot instance
bot = AsyncTeleBot(TOKEN)

# # Initialize Firestore if empty
# async def initialize_firestore():
#     try:
#         # Check if config collection exists
#         collections = [coll.id for coll in db.collection('config').get()]
        
#         if 'admins' not in collections:
#             # Add initial admin (the bot owner)
#             initial_admin = int(os.getenv("INITIAL_ADMIN_ID"))  # Add INITIAL_ADMIN_ID to your .env
#             db.collection('config').document('admins').set({'ids': [initial_admin]})
#             logger.info("Created admins document with initial admin")
            
#         if 'restricted_names' not in collections:
#             db.collection('config').document('restricted_names').set({'names': []})
#             logger.info("Created restricted_names document")
            
#     except Exception as e:
#         logger.error(f"Error initializing Firestore: {e}")
#         raise

# # Run initialization
# asyncio.run(initialize_firestore())

async def get_restricted_names():
    doc_ref = db.collection('config').document('restricted_names')
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get('names', [])
    return []

async def get_admin_ids():
    doc_ref = db.collection('config').document('admins')
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get('ids', [])
    return []

async def update_restricted_names(names_list):
    doc_ref = db.collection('config').document('restricted_names')
    doc_ref.set({'names': names_list})

async def update_admin_ids(admin_ids):
    doc_ref = db.collection('config').document('admins')
    doc_ref.set({'ids': admin_ids})

@bot.message_handler(commands=['add_admin'])
async def add_admin(message: types.Message):
    """Add a new admin by replying to their message or providing their ID"""
    admin_ids = await get_admin_ids()
    
    # Check if sender is admin
    if message.from_user.id not in admin_ids:
        await bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        # Check if replying to a user
        if message.reply_to_message:
            new_admin_id = message.reply_to_message.from_user.id
        else:
            # Try to get ID from command arguments
            if len(message.text.split()) < 2:
                await bot.reply_to(message, "Usage: /add_admin [user_id] or reply to user's message")
                return
            new_admin_id = int(message.text.split()[1])
        
        # Check if already admin
        if new_admin_id in admin_ids:
            await bot.reply_to(message, "⚠️ This user is already an admin.")
            return
            
        # Add new admin
        admin_ids.append(new_admin_id)
        await update_admin_ids(admin_ids)
        await bot.reply_to(message, f"✅ Added user {new_admin_id} as admin.")
    except ValueError:
        await bot.reply_to(message, "❌ Invalid user ID. Must be a number.")
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        await bot.reply_to(message, "❌ Failed to add admin.")

@bot.message_handler(commands=['remove_admin'])
async def remove_admin(message: types.Message):
    """Remove an admin by providing their ID"""
    admin_ids = await get_admin_ids()
    
    # Check if sender is admin
    if message.from_user.id not in admin_ids:
        await bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        if len(message.text.split()) < 2:
            await bot.reply_to(message, "Usage: /remove_admin [user_id]")
            return
            
        admin_to_remove = int(message.text.split()[1])
        
        # Check if exists
        if admin_to_remove not in admin_ids:
            await bot.reply_to(message, "⚠️ This user is not an admin.")
            return
            
        # Prevent removing yourself
        if admin_to_remove == message.from_user.id:
            await bot.reply_to(message, "❌ You cannot remove yourself as admin.")
            return
            
        # Remove admin
        admin_ids.remove(admin_to_remove)
        await update_admin_ids(admin_ids)
        await bot.reply_to(message, f"✅ Removed admin privileges from user {admin_to_remove}.")
    except ValueError:
        await bot.reply_to(message, "❌ Invalid user ID. Must be a number.")
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        await bot.reply_to(message, "❌ Failed to remove admin.")

@bot.message_handler(commands=['add_restricted'])
async def add_restricted_name(message: types.Message):
    admin_ids = await get_admin_ids()
    if message.from_user.id not in admin_ids:
        await bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        if len(message.text.split()) < 2:
            await bot.reply_to(message, "Usage: /add_restricted [name]")
            return
            
        name_to_add = ' '.join(message.text.split()[1:]).strip().lower()
        current_names = await get_restricted_names()
        
        if name_to_add in current_names:
            await bot.reply_to(message, f"⚠️ '{name_to_add}' already exists in restricted names.")
            return
            
        current_names.append(name_to_add)
        await update_restricted_names(current_names)
        await bot.reply_to(message, f"✅ Added '{name_to_add}' to restricted names.")
    except Exception as e:
        logger.error(f"Error adding restricted name: {e}")
        await bot.reply_to(message, "❌ Failed to add restricted name.")

@bot.message_handler(commands=['remove_restricted'])
async def remove_restricted_name(message: types.Message):
    admin_ids = await get_admin_ids()
    if message.from_user.id not in admin_ids:
        await bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        if len(message.text.split()) < 2:
            await bot.reply_to(message, "Usage: /remove_restricted [name]")
            return
            
        name_to_remove = ' '.join(message.text.split()[1:]).strip().lower()
        current_names = await get_restricted_names()
        
        if name_to_remove not in current_names:
            await bot.reply_to(message, f"⚠️ '{name_to_remove}' not found in restricted names.")
            return
            
        current_names.remove(name_to_remove)
        await update_restricted_names(current_names)
        await bot.reply_to(message, f"✅ Removed '{name_to_remove}' from restricted names.")
    except Exception as e:
        logger.error(f"Error removing restricted name: {e}")
        await bot.reply_to(message, "❌ Failed to remove restricted name.")

@bot.message_handler(commands=['list_restricted'])
async def list_restricted(message: types.Message):
    admin_ids = await get_admin_ids()
    if message.from_user.id not in admin_ids:
        await bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    current_names = await get_restricted_names()
    if not current_names:
        await bot.reply_to(message, "No restricted names currently set.")
        return
        
    response = "🔒 Restricted Names:\n" + "\n".join(
        f"{i+1}. {name}" for i, name in enumerate(current_names)
    )
    await bot.reply_to(message, response)

@bot.message_handler(commands=['start'])
async def start(message):
    help_text = (
        "Hello! I am a group manager bot.\n\n"
        "Admin commands:\n"
        "/add_admin [id] - Add new admin\n"
        "/remove_admin [id] - Remove admin\n"
        "/add_restricted [name] - Add restricted name\n"
        "/list_restricted - List restricted names\n"
        "/remove_restricted - Remove restricted name"
    )
    await bot.reply_to(message, help_text)

@bot.message_handler(func=lambda message: True)
async def handle_all_messages(message):
    await check_full_name_and_ban(message, bot, db)

@bot.chat_member_handler()
async def on_user_join(update: types.ChatMemberUpdated):
    if update.new_chat_member and update.new_chat_member.status == "member":
        await check_user_on_join(update.new_chat_member.user, update.chat, bot, db)

if __name__ == "__main__":
    logger.info("Starting bot with polling...")
    asyncio.run(bot.polling())