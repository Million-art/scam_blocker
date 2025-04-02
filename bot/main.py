import os
import logging
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handler.ban_handler import check_full_name_and_ban
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from vercel_fastapi import VercelFastAPI  # ✅ Import Vercel adapter

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot.main")

logger.info("Bot is starting...")

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Create bot application (async)
application = Application.builder().token(TOKEN).build()

# ✅ Wrap FastAPI with VercelFastAPI
app = FastAPI()
app = VercelFastAPI(app)  # ✅ Fix for Vercel deployment

# Command: /start
async def start(update: Update, context):
    await update.message.reply_text("Hello! I am a group manager bot.")

# Handlers
application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_full_name_and_ban))
application.add_handler(CommandHandler("start", start))

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    """Handles incoming Telegram webhook updates."""
    try:
        update_dict = await request.json()
        update = Update.de_json(update_dict, application.bot)
        await application.process_update(update)
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
