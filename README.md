## Telegram Video Downloader Bot

Python Telegram bot that downloads public videos/reels/stories from any source supported by `yt-dlp` (YouTube, TikTok, Instagram, Twitter/X, Facebook, etc.) and sends the file back to the user, respecting Telegram's upload limits.

### Prerequisites

- Python 3.10 or newer
- Telegram Bot token from [@BotFather](https://t.me/BotFather)

### Setup

1. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Configure environment:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `TELEGRAM_BOT_TOKEN`. Optional overrides:
   - `DOWNLOAD_DIR` – where temporary downloads are stored (default `downloads`).
   - `MAX_FILESIZE_MB` – upper bound for uploads (default 45 MB; Telegram hard limit is 50 MB).
3. Run the bot:
   ```bash
   python bot.py
   ```

### Usage

- `/start` or `/help`: show instructions.
- Send any direct or share URL for a public video/reel/story. The bot downloads the media with `yt-dlp` and replies with the file if it is smaller than `MAX_FILESIZE_MB`.

### Notes

- Private or login-protected links cannot be downloaded.
- If the video is larger than the configured limit, Telegram rejects the upload. Trim the content or choose a lower-quality format.
- `yt-dlp` supports a large set of platforms. Check the [supported sites list](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) for details.
