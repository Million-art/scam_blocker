import os
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Construct the path to config.json relative to the current script
current_script_path = Path(__file__)
config_path = current_script_path.parent.parent / "config.json"
logger.debug(f"Current working directory: {os.getcwd()}")
logger.debug(f"Config path: {config_path}")

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    logger.debug("Config loaded successfully")
except FileNotFoundError:
    logger.error(f"Config file not found at {config_path}")
    config = {}
except json.JSONDecodeError as e:
    logger.error(f"Error decoding JSON: {e}")
    config = {}

# Export config values
RESTRICTED_NAMES = config.get("restricted_names", [])
ADMIN_IDS = config.get("admin_ids", [])