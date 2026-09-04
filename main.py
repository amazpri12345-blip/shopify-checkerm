import os
import re
import tempfile
import aiohttp

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
URL_REGEX = re.compile(r"https?://\S+")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Send me a video link.\n\n"
        "I will process the link and return the video when a supported "
        "direct video source is available."
    )


async def process_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = URL_REGEX.search(text)

    if not match:
        await update.message.reply_text("❌ Please send a valid video URL.")
        return

    url = match.group(0)
    status = await update.message.reply_text("⏳ Processing your video...")

    if not url.lower().split("?")[0].endswith((".mp4", ".mov", ".mkv", ".webm")):
        await status.edit_text(
            "⚠️ This link is not a direct video file.\n\n"
            "A documented Flezen API/endpoint is required to automatically "
            "resolve a normal Flezen page into a video."
        )
        return

    filename = tempfile.mktemp(suffix=".mp4")

    try:
        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                with open(filename, "wb") as f:
                    while True:
                        chunk = await response.content.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

        await status.edit_text("📤 Uploading video to Telegram...")
        with open(filename, "rb") as video:
            await update.message.reply_video(video=video, caption="🎬 Video ready")

        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ Could not process the video.\n\n{str(e)[:300]}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_url))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
