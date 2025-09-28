"""Entry point for the Telegram bot."""
from __future__ import annotations

import sys
from typing import Optional

from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from .commands import file_management, fortune, twitter_sync, user_management
from .config import config_secret
from .database.db import add_or_update_user, init_db, mark_user_inactive, record_membership_event
from .logger.logger import get_logger

logger = get_logger("bot")


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    message = update.effective_message
    if user:
        add_or_update_user(
            user.id,
            user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
    if message:
        message.reply_text("你好！欢迎使用 Chiffon Telegram Bot。发送 /help 查看支持的命令。")
    logger.info("User %s triggered /start", user.id if user else "unknown")


def help_command(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    if not message:
        return
    message.reply_text(
        "可用命令:\n"
        "/start - 初始化机器人\n"
        "/help - 查看帮助\n"
        "/fortune - 今日运势\n"
        "/upload - 上传文件或图片\n"
        "/manage_user - 用户和权限管理\n"
        "/sync_twitter - 同步 Twitter 推文"
    )


def handle_new_members(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None or not message.new_chat_members:
        return

    for member in message.new_chat_members:
        if member.is_bot:
            continue
        add_or_update_user(
            member.id,
            member.username,
            first_name=member.first_name,
            last_name=member.last_name,
        )
        record_membership_event(
            telegram_id=member.id,
            chat_id=chat.id,
            chat_title=chat.title,
            username=member.username,
            event="join",
        )
        logger.info("Member %s joined chat %s", member.id, chat.id)


def handle_member_left(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None or not message.left_chat_member:
        return

    member = message.left_chat_member
    if member.is_bot:
        return

    mark_user_inactive(member.id)
    record_membership_event(
        telegram_id=member.id,
        chat_id=chat.id,
        chat_title=chat.title,
        username=member.username,
        event="leave",
    )
    logger.info("Member %s left chat %s", member.id, chat.id)


def error_handler(update: Optional[Update], context: CallbackContext) -> None:
    logger.exception("Update %s caused error", update, exc_info=context.error)


def main() -> None:
    token = getattr(config_secret, "TELEGRAM_API_TOKEN", None)
    if not token:
        logger.error("Telegram token missing. Set TELEGRAM_API_TOKEN in config_secret.yaml or environment.")
        sys.exit(1)

    init_db()

    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("fortune", fortune.fortune))
    dispatcher.add_handler(CommandHandler("upload", file_management.upload))
    dispatcher.add_handler(CommandHandler("manage_user", user_management.manage_user))
    dispatcher.add_handler(CommandHandler("sync_twitter", twitter_sync.sync_twitter, pass_args=True))

    dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo, file_management.upload))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, handle_new_members))
    dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member, handle_member_left))

    dispatcher.add_error_handler(error_handler)

    logger.info("Bot starting. Listening for updates...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
