import asyncio
import json
from http.server import BaseHTTPRequestHandler
from bot.main import bot
from telebot import types

async def process_update(update_dict):
    update = types.Update.de_json(update_dict)
    await bot.process_new_updates([update])

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update_dict = json.loads(post_data.decode('utf-8'))
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_update(update_dict))
        loop.close()
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Webhook is ready')