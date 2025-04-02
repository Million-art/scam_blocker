from telebot import types
import re

async def check_full_name_and_ban(message: types.Message, bot):
    chat = message.chat
    user = message.from_user

    if not chat or not user:
        return

    # Get the group name (remove special characters)
    group_name = re.sub(r'[^\w\s]', '', chat.title).strip().lower() if chat.title else ""

    # Get user's name parts
    name_parts = [
        user.first_name or '',
        user.last_name or '',
        user.username or ''
    ]
    full_name = " ".join(name_parts).strip().lower()

    # Check if user's name matches group name
    if group_name and (
        full_name == group_name or
        group_name in full_name or
        "".join(word[0] for word in group_name.split()) in full_name
    ):
        try:
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
                text="🚨 Security Alert: A user was banned for violating group naming policies. Their messages have been purged.")

        except Exception as e:
            print(f"Error in ban process: {e}")