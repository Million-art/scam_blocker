from dotenv import load_dotenv
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers.ban_handler import check_full_name_and_ban
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
    
    # Add command handler
    application.add_handler(CommandHandler('start', start))
    
    # Start the bot
    application.run_polling()

async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I am group manager bot.")

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
  