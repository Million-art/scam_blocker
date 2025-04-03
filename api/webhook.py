import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from bot.main import bot
from telebot import types

def get_config_path():
    """Determine the correct config path based on environment"""
    if os.getenv('DOCKER'):
        return Path('/app/config.json')  # Docker convention
    elif os.getenv('VERCEL'):
        return Path('/vercel/path/to/config.json')  # Adjust this path if /tmp is not available
    else:
        return Path(__file__).parent.parent / 'config.json'  # Local development

CONFIG_PATH = get_config_path()

def initialize_config():
    """Ensure config file exists with proper structure"""
    if not CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump({
                    "restricted_names": [],
                    "admin_ids": []
                }, f, indent=4)
            print(f"Created new config at {CONFIG_PATH}")
        except Exception as e:
            print(f"Failed to create config: {e}")
            raise

async def process_update(update_dict):
    try:
        # Ensure config exists before processing
        initialize_config()
        
        # Debug: Print received update
        print(f"Received update: {json.dumps(update_dict, indent=2)}")
        
        update = types.Update.de_json(update_dict)
        if update:
            # Reload fresh config for each request in production
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                bot.restricted_names = config.get('restricted_names', [])
                bot.admin_ids = config.get('admin_ids', [])
            
            await bot.process_new_updates([update])
        return True
    except Exception as e:
        print(f"Error processing update: {e}")
        return False

class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Empty request"}).encode())
            return

        post_data = self.rfile.read(content_length)
        try:
            update_dict = json.loads(post_data.decode('utf-8'))
            
            # Debug info
            print(f"Using config from: {CONFIG_PATH}")
            print(f"Config exists: {CONFIG_PATH.exists()}")
            print(f"Config writable: {os.access(str(CONFIG_PATH.parent), os.W_OK)}")
            
            # Run async function in sync context
            loop = asyncio.get_event_loop()
            success = loop.run_until_complete(process_update(update_dict))
            
            if success:
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "ok"}).encode())
            else:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": "Update processing failed"}).encode())
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        try:
            config_exists = CONFIG_PATH.exists()
            config_status = "exists" if config_exists else "missing"
            
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "status": "ready",
                "service": "Telegram Bot Webhook",
                "config_path": str(CONFIG_PATH),
                "config_status": config_status,
                "environment": "production" if os.getenv('VERCEL') else "development",
                "writable": os.access(str(CONFIG_PATH.parent), os.W_OK)
            }).encode())
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

handler = Handler