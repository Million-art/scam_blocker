import json
from pathlib import Path

# Load config from JSON file
config_path = Path(__file__).parent / "config.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Export config values
RESTRICTED_NAMES = config.get("restricted_names", [])
ADMIN_IDS = config.get("admin_ids", [])