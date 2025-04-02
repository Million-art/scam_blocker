# bot/handlers/ban_handler.py
from telegram import Update
from telegram.ext import ContextTypes
import re

async def check_full_name_and_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not chat or not user:
        return

    # Get the group name (remove special characters for better matching)
    group_name = re.sub(r'[^\w\s]', '', chat.title).strip().lower() if chat.title else ""

    # Get user's name parts (first, last, username)
    name_parts = [
        user.first_name or '',
        user.last_name or '',
        user.username or ''
    ]
    full_name = " ".join(name_parts).strip().lower()

    # Check if user's name matches group name (flexible matching)
    if group_name and (
        # Exact match (e.g., "My Group" vs "my group")
        full_name == group_name or
        # Partial match (e.g., "My Group Admin" contains "my group")
        group_name in full_name or
        # Initials match (e.g., "MG" vs "My Group")
        "".join(word[0] for word in group_name.split()) in full_name
    ):
        try:
            # 1. Ban the user and delete their messages
            await context.bot.ban_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                revoke_messages=True
            )

            # 2. Delete the triggering message
            if message:
                await message.delete()

            # 3. Notify the group anonymously
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"🚨 A user was banned for impersonating this group's name.",
                parse_mode='Markdown'
            )

        except Exception as e:
            context.logger.error(f"Error banning user: {e}")