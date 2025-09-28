"""Sync Twitter timeline to Telegram."""
from __future__ import annotations

from typing import Optional

import tweepy
from telegram import Update
from telegram.ext import CallbackContext

from ..config import config_secret
from ..logger.logger import get_logger

logger = get_logger("commands.twitter_sync")


def _build_twitter_client() -> Optional[tweepy.API]:
    twitter_conf = getattr(config_secret, "TWITTER", None)
    if twitter_conf is None:
        logger.error("TWITTER configuration missing in config_secret.yaml")
        return None

    required = [
        twitter_conf.consumer_key,
        twitter_conf.consumer_secret,
        twitter_conf.access_token,
        twitter_conf.access_token_secret,
    ]
    if not all(required):
        logger.warning("Twitter credentials not fully configured; skipping client creation")
        return None

    auth = tweepy.OAuth1UserHandler(
        twitter_conf.consumer_key,
        twitter_conf.consumer_secret,
        twitter_conf.access_token,
        twitter_conf.access_token_secret,
    )
    return tweepy.API(auth)


_TWITTER_CLIENT = None
try:
    _TWITTER_CLIENT = _build_twitter_client()
except Exception as exc:  # pragma: no cover - defensive
    logger.exception("Failed to initialise Twitter client: %s", exc)


def sync_twitter(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    if message is None:
        return

    if _TWITTER_CLIENT is None:
        message.reply_text("Twitter 功能尚未配置，请先在 config_secret.yaml 中填写凭证。")
        return

    twitter_conf = getattr(config_secret, "TWITTER", None)
    handle = context.args[0] if context.args else getattr(twitter_conf, "target_handle", None)
    if not handle:
        message.reply_text("请提供 Twitter 用户名，例如 /sync_twitter TwitterDev")
        return

    try:
        tweets = _TWITTER_CLIENT.user_timeline(screen_name=handle, count=5, tweet_mode="extended")
    except tweepy.TweepyException as exc:  # type: ignore[attr-defined]
        logger.exception("Failed to fetch tweets: %s", exc)
        message.reply_text("同步推特时出现错误，请稍后再试。")
        return

    if not tweets:
        message.reply_text(f"未找到 {handle} 的推文。")
        return

    for tweet in tweets:
        text = tweet.full_text if hasattr(tweet, "full_text") else tweet.text
        message.reply_text(f"{tweet.user.name}: {text}")

    logger.info("Synced %d tweets for handle %s", len(tweets), handle)

