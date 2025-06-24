import os
import re
import subprocess
import asyncio
import tempfile

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
from PIL import Image, ImageFilter


# Load bot token
load_dotenv()
BOT_TOKEN = os.getenv("DENGIFY_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("DENGIFY_TOKEN is not set in .env")

# Metadata embedder
def embed_metadata(mp3_path: str, title: str, artist: str, album: str):
    audio = MP3(mp3_path, ID3=EasyID3)
    audio["title"] = title
    audio["artist"] = artist
    audio["album"] = album
    audio.save()

# Pad image to square (only if needed)
def pad_to_square(image_path: str, output_path: str):
    with Image.open(image_path) as img:
        width, height = img.size

        if width == height:
            img.save(output_path, format="JPEG")
            return

        # Create blurred background
        max_dim = max(width, height)
        blurred_bg = img.resize((max_dim, max_dim)).filter(ImageFilter.GaussianBlur(15))


        # Create output canvas
        result = Image.new("RGB", (max_dim, max_dim))
        result.paste(blurred_bg, (0, 0))

        # Center paste the original image
        x = (max_dim - width) // 2
        y = (max_dim - height) // 2
        result.paste(img, (x, y))

        result.save(output_path, format="JPEG")


# Download YouTube MP3 and thumbnail
def download_mp3_with_art(youtube_url: str, workdir: str):
    song_template = os.path.join(workdir, "song.%(ext)s")
    mp3_path = os.path.join(workdir, "song.mp3")
    raw_cover_path = os.path.join(workdir, "raw_cover.jpg")
    square_cover_path = os.path.join(workdir, "cover.jpg")
    final_path = os.path.join(workdir, "final.mp3")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": song_template,
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

    subprocess.run(["curl", "-L", thumbnail, "-o", raw_cover_path], check=True)
    pad_to_square(raw_cover_path, square_cover_path)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", mp3_path,
        "-i", square_cover_path,
        "-map", "0:a",
        "-map", "1:v",
        "-c:a", "copy",
        "-c:v", "mjpeg",
        "-id3v2_version", "3",
        "-metadata:s:v", 'title="Album cover"',
        "-metadata:s:v", 'comment="Cover (front)"',
        "-disposition:v", "attached_pic",
        final_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    embed_metadata(final_path, title, artist, album)
    return title, artist, final_path, square_cover_path

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سڵاو\n"
        "سوپاس بۆ بەکارهێنانی بۆتی دەنگیفای \n"
        "هیوادارم سودی لێ ببینن!\n\n"
        "❗ تکایە لینکی گۆرانی یوتیوبەکەت بنێرە"
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    m = re.search(r"(https?://(?:youtu\.be/|youtube\.com/watch\?v=)[^&\s]+)", text)
    if not m:
        return await update.message.reply_text("❌ تکایە تەنها لینکی یوتیوب بنێرە")

    url = m.group(1)
    chat_id = update.effective_chat.id

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text("🎵 تکایە جاوەڕوان بە تاوەکو گۆرانیەکەت ئامادە دەکرێت…")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            title, artist, final_path, cover_path = await asyncio.to_thread(
                download_mp3_with_art, url, tmpdir
            )

            await context.bot.send_chat_action(chat_id, ChatAction.UPLOAD_DOCUMENT)
            with open(final_path, "rb") as audio_f, open(cover_path, "rb") as thumb_f:
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

# Entrypoint
if __name__ == "__main__":
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(5)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 DengifyBot is running…")
    app.run_polling()
