import asyncio
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from yt_dlp import YoutubeDL


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class DownloadTooLargeError(Exception):
    """Raised when the downloaded file exceeds Telegram limits."""


load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit(
        "TELEGRAM_BOT_TOKEN is missing. Set it in the environment or .env file."
    )

DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "downloads"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILESIZE_MB = int(os.getenv("MAX_FILESIZE_MB", "45"))
MAX_FILESIZE_BYTES = MAX_FILESIZE_MB * 1024 * 1024

URL_PATTERN = re.compile(r"(https?://\S+)")


@dataclass
class DownloadResult:
    path: Path
    title: str
    source_url: str


def extract_first_url(text: str) -> Optional[str]:
    """Return the first HTTP(S) URL found in the text."""
    if not text:
        return None

    match = URL_PATTERN.search(text.strip())
    if not match:
        return None

    candidate = match.group(1).rstrip(").,")
    parsed = urlparse(candidate)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return candidate

    return None


def build_ydl_opts(download_dir: Path) -> dict:
    """Create yt-dlp configuration."""
    return {
        "outtmpl": str(download_dir / "%(title).80s-%(id)s.%(ext)s"),
        "max_filesize": MAX_FILESIZE_BYTES,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
    }


def _download_sync(url: str) -> DownloadResult:
    """Download media synchronously via yt-dlp; intended for to_thread."""
    ydl_opts = build_ydl_opts(DOWNLOAD_DIR)
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = Path(ydl.prepare_filename(info))

    if not file_path.exists():
        raise FileNotFoundError("yt-dlp reported success but file is missing.")

    if file_path.stat().st_size > MAX_FILESIZE_BYTES:
        file_path.unlink(missing_ok=True)
        raise DownloadTooLargeError(
            f"File is larger than {MAX_FILESIZE_MB} MB, Telegram limit exceeded."
        )

    return DownloadResult(
        path=file_path,
        title=info.get("title") or "Downloaded video",
        source_url=url,
    )


async def download_media(url: str) -> DownloadResult:
    """Wrapper to keep yt-dlp off the main event loop."""
    return await asyncio.to_thread(_download_sync, url)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hey! Send me any public video URL (YouTube, TikTok, Instagram, Twitter/X, etc.) "
        "and I will download it and send it back as long as it's under Telegram's size limits."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "1. Copy the share link of the video/reel/story.\n"
        "2. Send the link to this chat.\n"
        "3. Wait while I fetch and upload the file (up to "
        f"{MAX_FILESIZE_MB} MB).\n\n"
        "If the platform requires authentication or the file is too large, the download may fail."
    )


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.text:
        return

    url = extract_first_url(message.text)
    if not url:
        await message.reply_text("Please send a valid HTTP/HTTPS URL.")
        return

    status_message = await message.reply_text("Downloading your video, please wait…")
    result: Optional[DownloadResult] = None

    try:
        await context.bot.send_chat_action(
            chat_id=message.chat_id, action=ChatAction.UPLOAD_DOCUMENT
        )
        result = await download_media(url)

        await context.bot.send_chat_action(
            chat_id=message.chat_id, action=ChatAction.UPLOAD_VIDEO
        )

        with result.path.open("rb") as fp:
            caption = f"{result.title}\n\nSource: {result.source_url}"
            await message.reply_document(
                document=fp,
                filename=result.path.name,
                caption=caption[:1024],
            )

        await status_message.edit_text("Done ✅")
    except DownloadTooLargeError as exc:
        logger.warning("File too large: %s", exc)
        await status_message.edit_text(
            f"Download succeeded but the file is bigger than {MAX_FILESIZE_MB} MB, "
            "so Telegram refuses it. Try a shorter clip."
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to download or send media: %s", exc)
        user_message = (
            "Sorry, I couldn't download that link. "
            "Make sure it's public and try again."
        )
        if isinstance(exc, TelegramError):
            user_message = "Telegram rejected the upload. Please try another video."

        await status_message.edit_text(user_message)
    finally:
        if "result" in locals():
            try:
                result.path.unlink(missing_ok=True)
            except OSError as unlink_error:
                logger.warning("Failed to delete %s: %s", result.path, unlink_error)


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link)
    )

    logger.info("Bot is running…")
    application.run_polling()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
