from telebot import types
import re
import json
import logging
def load_config():
    with open('config.json') as config_file:
        return json.load(config_file)
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def check_full_name_and_ban(message: types.Message, bot):
    config = load_config()
    RESTRICTED_NAMES = config['restricted_names']
    ADMIN_IDS = config['admin_ids']

    chat = message.chat
    user = message.from_user

    if not chat or not user:
        logger.error("Invalid chat or user")
        return

    # Get user's name parts
    name_parts = [
        user.first_name or '',
        user.last_name or '',
        user.username or ''
    ]
    full_name = " ".join(name_parts).strip().lower()
    logger.debug(f"User full name: {full_name}")

    # Check if user's name matches any restricted name
    if any(restricted_name in full_name for restricted_name in RESTRICTED_NAMES):
        logger.info(f"Restricted name detected: {full_name}")
        try:
            # Check if the user is an admin or owner
            chat_member = await bot.get_chat_member(chat.id, user.id)
            if chat_member.status in ["administrator", "creator"] or user.id in ADMIN_IDS:
                logger.info(f"User {user.id} is an admin or owner, skipping ban")
                return

            # First delete the offending message
            try:
                await bot.delete_message(chat.id, message.message_id)
                logger.info(f"Deleted message from user {user.id}")
            except Exception as delete_error:
                logger.error(f"Could not delete message: {delete_error}")

            # Then ban the user
            await bot.ban_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                revoke_messages=True  
            )
            logger.info(f"Banned user {user.id}")

            # Notify the group
            await bot.send_message(
                chat_id=chat.id,
                text=f"🚨 Security Alert: User @{user.username} was banned for violating group naming policies. Their messages have been purged."
            )
            logger.info(f"Notified group about banned user {user.id}")

        except Exception as e:
            logger.error(f"Error in ban process: {e}")
# Function to check if a user's name matches any restricted name and ban them
async def check_user_on_join(user: types.User, chat: types.Chat, bot):
    config = load_config()
    RESTRICTED_NAMES = config['restricted_names']
    ADMIN_IDS = config['admin_ids']

    if not chat or not user:
        return
    
    # Get user's name parts
    name_parts = [
        user.first_name or '',
        user.last_name or '',
        user.username or ''
    ]
    full_name = " ".join(name_parts).strip().lower()

    # Check if user's name matches any restricted name
    if any(restricted_name in full_name for restricted_name in RESTRICTED_NAMES):
        try:
            # Check if the user is an admin or owner
            chat_member = await bot.get_chat_member(chat.id, user.id)
            if chat_member.status in ["administrator", "creator"] or user.id in ADMIN_IDS:
                return

            # Ban the user
            await bot.ban_chat_member(
                chat_id=chat.id, 
                user_id=user.id, 
                revoke_messages=True
            )

            # Notify the group
            await bot.send_message(
                chat_id=chat.id,
                text=f"🚨 User @{user.username} was banned for violating group naming policies."
            )

        except Exception as e:
            print(f"Error banning user {user.id}: {e}")