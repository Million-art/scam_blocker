from telebot import types
from config import RESTRICTED_NAMES, ADMIN_IDS
import re
async def check_full_name_and_ban(message: types.Message, bot):
    chat = message.chat
    user = message.from_user

    if not chat or not user:
        return

    # Skip if user is admin
    if user.id in ADMIN_IDS:
        return

    # Get user's name parts
    name_parts = [
        user.first_name or '',
        user.last_name or '',
        user.username or ''
    ]
    full_name = " ".join(name_parts).strip().lower()

    # Check if user's name matches any restricted name
    if any(re.search(rf'\b{re.escape(restricted_name.lower())}\b', full_name) 
           for restricted_name in RESTRICTED_NAMES):
        try:
            # First delete the message
            try:
                await bot.delete_message(chat.id, message.message_id)
            except Exception as delete_error:
                print(f"Could not delete message: {delete_error}")

            # Ban the user
            await bot.ban_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                revoke_messages=True  
            )

            # Notify the group
            await bot.send_message(
                chat_id=chat.id,
                text="🚨 Security Alert: User banned for violating naming policies. Messages purged."
            )

        except Exception as e:
            print(f"Error in ban process: {e}")

async def check_user_on_join(user: types.User, chat: types.Chat, bot):
    if not chat or not user:
        return
    
    # Skip if user is admin
    if user.id in ADMIN_IDS:
        return

    # Get user's name parts
    name_parts = [
        user.first_name or '',
        user.last_name or '',
        user.username or ''
    ]
    full_name = " ".join(name_parts).strip().lower()

    # Check if user's name matches any restricted name
    if any(re.search(rf'\b{re.escape(restricted_name.lower())}\b', full_name) 
           for restricted_name in RESTRICTED_NAMES):
        try:
            # Ban the user
            await bot.ban_chat_member(
                chat_id=chat.id, 
                user_id=user.id, 
                revoke_messages=True
            )

            # Notify the group
            await bot.send_message(
                chat_id=chat.id,
                text=f"🚨 User {user.first_name} was banned for violating naming policies."
            )

        except Exception as e:
            print(f"Error banning user {user.id}: {e}")