from dotenv import load_dotenv
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handler.ban_handler import check_full_name_and_ban
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import asyncio
from telegram import Update
import logging

# Load environment variables
load_dotenv()
token = os.getenv('BOT_TOKEN')

if not token:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Create the Application
application = Application.builder().token(token).build()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the start function
async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I am group manager bot.")

# Add message handler
application.add_handler(
    MessageHandler(filters.ALL & ~filters.COMMAND, check_full_name_and_ban)
)

# Add command handler
application.add_handler(CommandHandler('start', start))

# HTTP handler for incoming webhook requests
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update_dict = json.loads(post_data.decode('utf-8'))

        asyncio.run(self.process_update(update_dict))

        self.send_response(200)
        self.end_headers()

    async def process_update(self, update_dict):
        update = Update.de_json(update_dict, application.bot)
        await application.process_update(update)

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello, BOT is running!')

def run_server(server_class=HTTPServer, handler_class=handler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logger.info(f"Starting httpd server on port {port}")
    httpd.serve_forever()

def main():
    # Start the HTTP server to handle incoming webhook requests
    run_server()

if __name__ == "__main__":
    main()