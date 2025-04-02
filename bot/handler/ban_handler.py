from telebot import types
from pathlib import Path
import json
import logging
import re
from config import RESTRICTED_NAMES, ADMIN_IDS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def load_config():
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


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
    try:
        # 1. First debug point - confirm handler is being called
        logger.debug("\n" + "="*40)
        logger.debug("NEW USER JOIN HANDLER TRIGGERED")
        
        if not user:
            logger.error("No user object provided!")
            return
        if not chat:
            logger.error("No chat object provided!")
            return

        # 2. Print all available user information
        logger.debug(f"User ID: {user.id}")
        logger.debug(f"First Name: {user.first_name}")
        logger.debug(f"Last Name: {user.last_name}")
        logger.debug(f"Username: @{user.username}")
        logger.debug(f"Is Bot: {user.is_bot}")
        logger.debug(f"Chat: {chat.title} (ID: {chat.id})")
        logger.debug(f"Chat Type: {chat.type}")

        # 3. Load and verify config
        config_path = Path(__file__).parent.parent / "config.json"
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            restricted_names = [n.lower() for n in config.get("restricted_names", [])]
            admin_ids = config.get("admin_ids", [])
            logger.debug(f"Loaded restricted names: {restricted_names}")
            logger.debug(f"Admin IDs: {admin_ids}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return

        # 4. Check admin status
        if user.id in admin_ids:
            logger.debug("User is admin, skipping ban check")
            return

        # 5. Prepare name combinations to check
        first = (user.first_name or "").lower().strip()
        last = (user.last_name or "").lower().strip()
        username = (user.username or "").lower().strip()
        
        combinations = [
            first,
            last,
            username,
            f"{first}{last}",    # "ab" + "i" = "abi"
            f"{first} {last}",   # "ab i"
            f"{last}{first}",    # "iab"
            f"{last} {first}"    # "i ab"
        ]
        
        logger.debug(f"Checking combinations: {combinations}")

        # 6. Check against restricted names
        for name in combinations:
            if name in restricted_names:
                logger.debug(f"MATCH FOUND: '{name}' in restricted names")
                try:
                    await bot.ban_chat_member(
                        chat_id=chat.id,
                        user_id=user.id,
                        revoke_messages=True
                    )
                    logger.debug(f"Successfully banned user {user.id}")
                    await bot.send_message(
                        chat_id=chat.id,
                        text=f"🚨 Banned user {user.first_name} {user.last_name} (matched: '{name}')"
                    )
                    return
                except Exception as e:
                    logger.error(f"Failed to ban user: {e}")
                    return

        logger.debug("No name matches found")
        
    except Exception as e:
        logger.error(f"Unexpected error in check_user_on_join: {e}")

    if not chat or not user:
        logger.debug("No chat or user provided")
        return
    
    config = load_config()
    admin_ids = config.get("admin_ids", [])
    restricted_names = [name.lower() for name in config.get("restricted_names", [])]

    # Debug print user info
    logger.debug(f"New user joined: {user.first_name} {user.last_name} (@{user.username}) ID: {user.id}")
    logger.debug(f"Admin IDs: {admin_ids}")
    logger.debug(f"Restricted names: {restricted_names}")

    # Skip if user is admin
    if user.id in admin_ids:
        logger.debug(f"Skipping admin user: {user.id}")
        return

    # Get name components
    first = (user.first_name or '').lower().strip()
    last = (user.last_name or '').lower().strip()
    username = (user.username or '').lower().strip()

    # Debug print name components
    logger.debug(f"Name components - First: '{first}', Last: '{last}', Username: '@{username}'")

    # Check all possible combinations
    combinations = {
        'first': first,
        'last': last,
        'username': username,
        'first_last': f"{first}{last}",
        'first_space_last': f"{first} {last}",
        'last_first': f"{last}{first}",
        'last_space_first': f"{last} {first}"
    }

    # Debug print all combinations
    logger.debug("Checking combinations:")
    for name_type, combo in combinations.items():
        logger.debug(f"{name_type}: '{combo}'")
        if combo in restricted_names:
            logger.debug(f"MATCH FOUND! {name_type}='{combo}' matches restricted names")
            try:
                await bot.ban_chat_member(
                    chat_id=chat.id, 
                    user_id=user.id,
                    revoke_messages=True
                )
                await bot.send_message(
                    chat_id=chat.id,
                    text=f"🚨 Banned user {user.first_name} {user.last_name} - matched restricted pattern: {combo}"
                )
                logger.debug(f"Successfully banned user {user.id}")
                return
            except Exception as e:
                logger.error(f"Failed to ban user {user.id}: {str(e)}")
                return

    logger.debug("No name combinations matched restricted names")
    if not chat or not user:
        return
    
    config = load_config()
    admin_ids = config.get("admin_ids", [])
    restricted_names = [name.lower() for name in config.get("restricted_names", [])]

    # Skip if user is admin
    if user.id in admin_ids:
        return

    # Create all possible name combinations
    first_name = (user.first_name or '').lower()
    last_name = (user.last_name or '').lower()
    username = (user.username or '').lower()
    
    # Check all possible combinations
    name_combinations = [
        first_name,
        last_name,
        username,
        f"{first_name}{last_name}",  # "ab" + "i" = "abi"
        f"{first_name} {last_name}", # "ab i"
        f"{last_name}{first_name}",  # "iab"
        f"{last_name} {first_name}"  # "i ab"
    ]

    # Check if any combination matches restricted names
    for name in name_combinations:
        if name in restricted_names:
            try:
                await bot.ban_chat_member(
                    chat_id=chat.id, 
                    user_id=user.id,
                    revoke_messages=True
                )
                await bot.send_message(
                    chat_id=chat.id,
                    text=f"🚨 Banned user {user.first_name} {user.last_name} for matching restricted name: {name}"
                )
                return
            except Exception as e:
                print(f"Error banning user {user.id}: {e}")
                return
    if not chat or not user:
        return
    
    config = load_config()
    admin_ids = config.get("admin_ids", [])
    restricted_names = config.get("restricted_names", [])

    # Skip if user is admin
    if user.id in admin_ids:
        return

    # Get user's name parts
    name_parts = [
        user.first_name or '',
        user.last_name or '',
        user.username or ''
    ]
    full_name = " ".join(name_parts).strip().lower()

    # Check if user's name exactly matches any restricted name (case-insensitive)
    if any(restricted.lower() == full_name for restricted in restricted_names):
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
                text=f"🚨 Banned user {user.first_name} for having a restricted name."
            )

        except Exception as e:
            print(f"Error banning user {user.id}: {e}")