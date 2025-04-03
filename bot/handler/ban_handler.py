from telebot import types
import re

async def check_full_name_and_ban(message: types.Message, bot, db):
    chat = message.chat
    user = message.from_user

    if not chat or not user:
        return

    # Get restricted names from Firestore
    restricted_names = await get_restricted_names(db)

    # Get user's name parts
    name_parts = [
        user.first_name or '',
        user.last_name or '',
        user.username or ''
    ]
    full_name = " ".join(name_parts).strip().lower()

    # Check if user's name matches any restricted name
    if any(restricted_name in full_name for restricted_name in restricted_names):
        try:
            # Check if the user is an admin or owner
            chat_member = await bot.get_chat_member(chat.id, user.id)
            if chat_member.status in ["administrator", "creator"]:
                return

            # First delete the offending message
            try:
                await bot.delete_message(chat.id, message.message_id)
            except Exception as delete_error:
                print(f"Could not delete message: {delete_error}")

            # Then ban the user
            await bot.ban_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                revoke_messages=True  
            )

            # Notify the group
            await bot.send_message(
                chat_id=chat.id,
                text="🚨 Security Alert: A user was banned for violating group naming policies. Their messages have been purged."
            )

        except Exception as e:
            print(f"Error in ban process: {e}")

async def check_user_on_join(user: types.User, chat: types.Chat, bot, db):
    if not chat or not user:
        return
    
    # Get restricted names from Firestore
    restricted_names = await get_restricted_names(db)
    
    # Get user's name parts
    name_parts = [
        user.first_name or '',
        user.last_name or '',
        user.username or ''
    ]
    full_name = " ".join(name_parts).strip().lower()

    # Check if user's name matches any restricted name
    if any(restricted_name in full_name for restricted_name in restricted_names):
        try:
            # Check if the user is an admin or owner
            chat_member = await bot.get_chat_member(chat.id, user.id)
            if chat_member.status in ["administrator", "creator"]:
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
                text=f"🚨 User {user.first_name} was banned for violating group naming policies."
            )

        except Exception as e:
            print(f"Error banning user {user.id}: {e}")

async def get_restricted_names(db):
    """Helper function to get restricted names from Firestore"""
    doc_ref = db.collection('config').document('restricted_names')
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get('names', [])
    return []