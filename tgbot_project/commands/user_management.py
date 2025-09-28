"""User management commands."""
from __future__ import annotations

from typing import Dict, List

from telegram import Update
from telegram.ext import CallbackContext

from ..database.db import (
    add_or_update_user,
    list_users,
    remove_user,
    set_user_role,
    user_has_role,
)
from ..logger.logger import get_logger

logger = get_logger("commands.user_management")

HELP_TEXT = (
    "用法: /manage_user <register|setrole|remove|list> ...\n"
    "示例:\n"
    "  /manage_user register\n"
    "  /manage_user setrole <telegram_id> <member|admin>\n"
    "  /manage_user remove <telegram_id>\n"
    "  /manage_user list"
)

ADMIN_ROLES = {"admin"}
VALID_ROLES = {"member", "admin"}


def _require_message(update: Update):
    if update.effective_message is None:
        raise ValueError("Command must be triggered from a message context")
    return update.effective_message


def manage_user(update: Update, context: CallbackContext) -> None:
    message = _require_message(update)
    user = update.effective_user
    args: List[str] = context.args or []

    if user is None:
        message.reply_text("无法识别用户信息。")
        return

    if not args:
        message.reply_text(HELP_TEXT)
        return

    subcommand = args[0].lower()

    if subcommand == "register":
        existing = list_users()
        has_admin = any(item.get("role") == "admin" for item in existing)
        default_role = "admin" if not has_admin else "member"
        record = add_or_update_user(
            user.id,
            user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            role=default_role,
        )
        suffix = "（首位注册用户自动成为管理员）" if default_role == "admin" else ""
        message.reply_text(
            f"用户 {record['telegram_id']} 注册成功，角色: {record['role']}{suffix}"
        )
        logger.info("Registered user %s with role %s", record["telegram_id"], record["role"])
        return

    is_admin = user_has_role(user.id, *ADMIN_ROLES)
    if subcommand != "register" and not is_admin:
        message.reply_text("只有管理员可以执行该命令，请先 /manage_user register 并联系管理员授权。")
        logger.warning("User %s tried admin command %s", user.id, subcommand)
        return

    if subcommand == "setrole":
        if len(args) < 3:
            message.reply_text("用法: /manage_user setrole <telegram_id> <member|admin>")
            return
        target_id, role = args[1], args[2].lower()
        if role not in VALID_ROLES:
            message.reply_text(f"角色 {role} 不合法，可选: {', '.join(VALID_ROLES)}")
            return
        try:
            target_id_int = int(target_id)
        except ValueError:
            message.reply_text("telegram_id 必须是数字")
            return
        record = set_user_role(target_id_int, role)
        if not record:
            message.reply_text("未找到该用户，请提醒对方先执行 /manage_user register 或加入群组。")
            return
        message.reply_text(f"已将用户 {record['telegram_id']} 设置为 {record['role']}")
        logger.info("User %s set role of %s to %s", user.id, record["telegram_id"], role)
        return

    if subcommand == "remove":
        if len(args) < 2:
            message.reply_text("用法: /manage_user remove <telegram_id>")
            return
        try:
            target_id_int = int(args[1])
        except ValueError:
            message.reply_text("telegram_id 必须是数字")
            return
        if remove_user(target_id_int):
            message.reply_text(f"已移除用户 {target_id_int}")
            logger.info("User %s removed %s", user.id, target_id_int)
        else:
            message.reply_text("未找到该用户")
        return

    if subcommand == "list":
        users: List[Dict[str, str]] = list_users()
        if not users:
            message.reply_text("暂无注册用户")
            return
        lines = [
            f"{item['telegram_id']} - {item.get('username') or '未知'} - {item['role']} - "
            f"{'活跃' if item.get('is_active') else '已退出'}"
            for item in users
        ]
        message.reply_text("用户列表:\n" + "\n".join(lines))
        return

    message.reply_text(HELP_TEXT)

