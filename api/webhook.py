import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from bot.main import bot
from telebot import types
from config import CONFIG_PATH, IS_VERCEL

# Configure paths for production vs development
def get_config_path():
    """Determine the correct config path based on environment"""
    if os.getenv('VERCEL'):
        return Path('/tmp/config.json')  # Vercel uses /tmp for writable storage
    elif os.getenv('DOCKER'):
        return Path('/app/config.json')  # Docker convention
    else:
        return Path(__file__).parent.parent / 'config.json'  # Local development

CONFIG_PATH = get_config_path()

async def process_update(update_dict):
    try:
        # Debug: Print received update
        print(f"Received update: {json.dumps(update_dict, indent=2)}")
        
        update = types.Update.de_json(update_dict)
        if update:
            # Reload config fresh for each request in production
            if os.getenv('PRODUCTION'):
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
            
            # Debug: Print config path being used
            print(f"Using config from: {CONFIG_PATH}")
            print(f"Config exists: {CONFIG_PATH.exists()}")
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(process_update(update_dict))
            loop.close()
            
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
        self._set_headers(200)
        self.wfile.write(json.dumps({
            "status": "ready",
            "service": "Telegram Bot Webhook",
            "config_path": str(CONFIG_PATH),
            "config_exists": CONFIG_PATH.exists(),
            "environment": "production" if os.getenv('PRODUCTION') else "development"
        }).encode())

handler = Handler