## Telegram Media Downloader Bot

This bot lives inside Telegram and works like a “send me a link, I’ll send you the file” assistant. It uses `yt-dlp`, so anything listed in their [supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) will usually work (YouTube, TikTok, Instagram reels/stories, Facebook, Twitter/X, Reddit, etc.). The bot downloads the clip to a temporary folder, trims the caption, and uploads the file back to you as long as it fits under Telegram’s ~50 MB limit.

---

### What you need up front

1. **Python 3.10+** (3.11/3.12 work great).  
2. **A Telegram bot token** from [@BotFather](https://t.me/BotFather). It takes ~30 seconds: `/start → /newbot → follow prompts → copy the HTTP API token`.

---

### Quick start (local machine)

```bash
# 1) Get into the project directory and create a virtual environment
python -m venv .venv
source .venv/bin/activate  # on Windows PowerShell: .venv\Scripts\Activate.ps1

# 2) Install everything the bot needs
pip install -r requirements.txt

# 3) Copy env template and fill in your token
cp .env.example .env
```

Open `.env`, paste the token after `TELEGRAM_BOT_TOKEN=` and (optionally) tweak:
- `DOWNLOAD_DIR` – folder where temporary files go (default `downloads`).
- `MAX_FILESIZE_MB` – cap before Telegram refuses uploads (stick to ≤48).

Finally, launch:

```bash
python bot.py
```

You should see `Bot is running…` in the console. Talk to your bot in Telegram and send a link to test.

---

### How the bot behaves

- `/start` or `/help` prints short instructions.
- Any message containing the first `http(s)` link gets processed. If the platform is supported and public, the bot downloads the best available quality under your size limit and reuploads it as a document.
- Files are deleted right after they’re sent so disk space stays clean.

Common reasons a download fails:
- The link needs you to be logged in (private/age-restricted content).
- The final file is bigger than `MAX_FILESIZE_MB`.
- The provider rate-limited `yt-dlp` (try again later or use a different host/IP).

---

### Want it online 24/7 for free?

- **Railway.app**: connect your GitHub repo, add env vars, command `python bot.py`. Free tier gives ~500 hours/month.
- **Render.com**: create a “Background Worker”, point to the repo, enter env vars, command `python bot.py`. One worker on the free tier runs continuously.
- **Fly.io / Docker host**: wrap the bot in a small Docker image, deploy to Fly’s free VM or a cheap VPS. Set secrets/environment variables via their CLI.

Stick with long polling (no webhook needed) unless you have a custom HTTPS endpoint. Most hosts above restart the service automatically if it crashes.

---

### Troubleshooting checklist

- `python bot.py` immediately crashes with `ModuleNotFoundError`: activate your virtual environment and re-run `pip install -r requirements.txt`.
- `RuntimeError: event loop is already running`: ensure the bottom of `bot.py` matches the latest version—`main()` should call `application.run_polling()` directly (no `asyncio.run`).
- Download works but Telegram rejects upload: lower `MAX_FILESIZE_MB`, or force `yt-dlp` to grab a lower-quality format.
- Logs are empty: set `logging.basicConfig(level=logging.DEBUG)` temporarily if you need more noise.

That’s it! Drop new features into `bot.py` (extra commands, quality selectors, etc.) and redeploy. Enjoy your all-in-one media fetcher. ***
