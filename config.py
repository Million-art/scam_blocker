import json
from pathlib import Path

# Load config from root folder
CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()
RESTRICTED_NAMES = config.get("restricted_names", [])
ADMIN_IDS = config.get("admin_ids", [])