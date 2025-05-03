import os
import re
import subprocess
import asyncio
import time

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import yt_dlp
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from dotenv import load_dotenv

# Load your bot token from .env
load_dotenv()
BOT_TOKEN = os.getenv("DENGIFY_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("DENGIFY_TOKEN is not set in .env")

# Embed title, artist, and album info into MP3
def embed_metadata(mp3_path, title, artist, album):
    audio = MP3(mp3_path, ID3=EasyID3)
    audio["title"] = title
    audio["artist"] = artist
    audio["album"] = album
    audio.save()

# Download YouTube audio, convert to MP3, embed cover and metadata
def download_mp3_with_art(youtube_url: str, output_filename: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "song.%(ext)s",
        "retries": 10,
        "socket_timeout": 10,
        "extractor_retries": 3,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)

    title = info.get("title", "Unknown Title")
    artist = info.get("uploader", "Unknown Artist")
    album = info.get("channel", artist)
    thumbnail = info.get("thumbnail")

    # Download thumbnail image
    subprocess.run(["curl", "-L", thumbnail, "-o", "cover.jpg"], check=True)

    # Embed cover into MP3
    subprocess.run([
        "ffmpeg", "-y",
        "-i", "song.mp3",
        "-i", "cover.jpg",
        "-map", "0:a", "-map", "1:v",
        "-c:a", "copy",
        "-c:v", "mjpeg",
        "-id3v2_version", "3",
        "-metadata:s:v", 'title="Album cover"',
        "-metadata:s:v", 'comment="Cover (front)"',
        "-disposition:v", "attached_pic",
        output_filename
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    embed_metadata(output_filename, title, artist, album)
    return title, artist

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سڵاو\n"
        "سوپاس بۆ بەکارهێنانی بۆتی دەنگیفای \n"
        "هیوادارم سودی لێ ببینن!\n\n"
        "❗ تکایە لینکی گۆرانی یوتیوبەکەت بنێرە"
    )

# Message handler for YouTube links
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    m = re.search(r"(https?://(?:youtu\.be/|youtube\.com/watch\?v=)[^&\s]+)", text)
    if not m:
        return await update.message.reply_text("❌ تکایە تەنها لینکی یوتیوب بنێرە")

    url = m.group(1)
    chat_id = update.effective_chat.id

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text("🎵 تکایە جاوەڕوانبە تا گۆرانیەکەت داونلۆد دەکرێت…")

    try:
        output_file = "final.mp3"
        title, artist = download_mp3_with_art(url, output_file)

        await context.bot.send_chat_action(chat_id, ChatAction.UPLOAD_DOCUMENT)
        with open(output_file, "rb") as audio_f, open("cover.jpg", "rb") as thumb_f:
            send_coro = context.bot.send_audio(
                chat_id=chat_id,
                audio=audio_f,
                thumbnail=thumb_f,
                filename=f"{title}.mp3",
                title=title,
                performer=artist
            )
            await asyncio.wait_for(send_coro, timeout=120)

        await update.message.reply_text("✅ گۆرانی بەسەرکەوتووی داونلۆد کرا")

    except Exception as e:
        await update.message.reply_text(f"❌ هەڵە: {e}")

    finally:
        for fn in ("song.mp3", "cover.jpg", "final.mp3"):
            if os.path.exists(fn):
                os.remove(fn)

# Start the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 DengifyBot is running…")
    while True:
        try:
            app.run_polling()
        except Exception as err:
            print(f"⚠️ Bot crashed: {err}\nRestarting in 5s…")
            time.sleep(5)
