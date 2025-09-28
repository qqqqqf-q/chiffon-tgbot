"""Daily fortune command."""
from __future__ import annotations

import random
from datetime import date
from hashlib import sha256

from telegram import Update
from telegram.ext import CallbackContext

FORTUNES = [
    "今天是个幸运的一天，保持微笑！",
    "小心谨慎，慢慢来会有惊喜。",
    "努力就会有收获，坚持住！",
    "适合思考与计划的一天。",
    "放松身心，享受生活的小确幸吧。",
]


def _seed_from_user(user_id: int) -> int:
    payload = f"{user_id}:{date.today().isoformat()}".encode("utf-8")
    digest = sha256(payload).hexdigest()
    return int(digest[:8], 16)


def fortune(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    message = update.effective_message
    if message is None or user is None:
        return
    random.seed(_seed_from_user(user.id))
    message.reply_text(random.choice(FORTUNES))
