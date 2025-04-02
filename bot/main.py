from dotenv import load_dotenv
import os
from telegram.ext import Application
from bot.handler.ban_handler import check_full_name_and_ban
from telegram.ext import MessageHandler, filters
from http.server import BaseHTTPRequestHandler
import json
import asyncio

def main():
    # Load environment variables
    load_dotenv()
    token = os.getenv('BOT_TOKEN')
    
    if not token:
        raise ValueError("No BOT_TOKEN found in environment variables")
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Add message handler
    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, check_full_name_and_ban)
    )
    
# Command to start the bot
@bot.message_handler(commands=['start'])
async def start(message: types.Message):
    await bot.reply_to(message, "Hello! i am group manager bot.")

# HTTP handler for Vercel
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update_dict = json.loads(post_data.decode('utf-8'))

        asyncio.run(self.process_update(update_dict))

        self.send_response(200)
        self.end_headers()

    async def process_update(self, update_dict):
        update = types.Update.de_json(update_dict)
        await bot.process_new_updates([update])

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('Hello, BOT is running!'.encode('utf-8'))
  