import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler
from bot.main import bot
from telebot import types
from pathlib import Path

async def process_update(update_dict):
    try:
        update = types.Update.de_json(update_dict)
        if update:
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
        current_script_path = Path(__file__)
        config_path = current_script_path.parent.parent / "config.json"
        config_status = "found" if config_path.exists() else "missing"
        writable = os.access(os.getcwd(), os.W_OK)
        
        self._set_headers(200)
        self.wfile.write(json.dumps({
            "status": "ready",
            "service": "Telegram Bot Webhook",
            "config_path": str(config_path),
            "config_status": config_status,
            "environment": "production",
            "writable": writable
        }).encode())

handler = Handler