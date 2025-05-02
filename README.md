# Dengify

Dengify is a **Kurdish** Telegram bot that converts YouTube video links into MP3 audio files. It automatically embeds:

* **Metadata**: Title, Artist (uploader), Album (channel name)
* **Cover Art**: YouTube video thumbnail

Built with `python-telegram-bot`, `yt-dlp`, `FFmpeg`, and `Mutagen` for fast, reliable audio delivery.

---

## Features

* 🚀 Send a YouTube link and receive an MP3 file
* 🏷️ Automatic embedding of title, artist, album metadata
* 🎨 Embedded cover art for better music app compatibility
* 🔄 Robust download with retries and support for slow connections

---

## Prerequisites

* **Python 3.8+**
* **FFmpeg** installed and available in your system `PATH`
* A **Telegram Bot Token** (obtain via [BotFather](https://t.me/BotFather))

---

## Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/AlandNawzad/Dengify.git
   cd Dengify
   ```

2. **Create & activate a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # on Windows use `.venv\\Scripts\\activate`
   ```

3. **Install dependencies**

   ```bash
   pip install python-telegram-bot yt-dlp mutagen python-dotenv
   ```

4. **Set up environment variables**

   Create a file named `.env` in the project root:

   ```bash
   DENGIFY_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
   ```

5. **(Optional)** Add to `.gitignore`:

   ```gitignore
   .env
   .venv/
   ```

---

## Usage

Run the bot:

```bash
python main.py
```

* Open the bot in Telegram (`@YourBotUsername`)
* Send `/start` to see instructions
* Send any YouTube link to get the MP3

---

## Commands

* `/start` - Display greeting and usage instructions

---

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
