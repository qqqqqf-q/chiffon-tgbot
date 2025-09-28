"""File management commands."""
from __future__ import annotations

from pathlib import Path

from telegram import Update
from telegram.ext import CallbackContext

from ..logger.logger import get_logger

logger = get_logger("commands.file_management")

FILES_DIR = Path(__file__).resolve().parent.parent / "files"
FILES_DIR.mkdir(parents=True, exist_ok=True)


def upload(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    if message is None:
        logger.warning("Received upload command without message context")
        return

    if message.document:
        telegram_file = message.document.get_file()
        target_path = FILES_DIR / message.document.file_name
        telegram_file.download(custom_path=str(target_path))
        message.reply_text(f"文件 {message.document.file_name} 上传成功！")
        logger.info("Stored file %s", target_path)
        return

    if message.photo:
        # Save highest resolution photo when sent as picture
        telegram_file = message.photo[-1].get_file()
        target_path = FILES_DIR / f"photo_{telegram_file.file_unique_id}.jpg"
        telegram_file.download(custom_path=str(target_path))
        message.reply_text("图片上传成功！")
        logger.info("Stored photo %s", target_path)
        return

    message.reply_text("请上传一个文件或图片！")
    logger.warning("User %s triggered upload without file", update.effective_user.id if update.effective_user else "unknown")

