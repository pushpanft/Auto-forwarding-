#!/usr/bin/env python3
"""
Telegram Affiliate Deal Auto-Forward Bot
For Pushpa - auto-forwards deal messages with platform tags:
  Amazon, Shop, Flipkart

How it works:
- Bot listens in SOURCE_CHAT (group/channel where deals are posted)
- Detects platform from links in the message
- Forwards / posts to DEST_CHAT (your public deal channel) with tag on top

Privacy note: Bot can only forward messages it can SEE.
- If source is a private group, add bot as member + admin (to read messages).
- If source is another bot / private channel you don't own, Telegram will NOT
  let this bot see or forward those messages. In that case you need a
  user-account (Telethon) solution - this bot uses official Bot API only.

Setup (5 min):
1. Talk to @BotFather on Telegram -> /newbot -> copy BOT_TOKEN
2. Add bot to source group + destination channel, make it admin in both
3. Send /start in source group, get chat ids from logs (first run prints them)
4. Fill .env and run: python3 telegram_deal_bot.py
"""

import os
import re
import asyncio
from pathlib import Path

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# ---------- config (from .env or environment) ----------
def load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SOURCE_CHAT_ID = os.getenv("SOURCE_CHAT_ID", "").strip()
DEST_CHAT_ID = os.getenv("DEST_CHAT_ID", "").strip()
AFFILIATE_TAG_AMAZON = os.getenv("AFFILIATE_TAG_AMAZON", "").strip()   # e.g. yourtag-21
AFFILIATE_TAG_FLIPKART = os.getenv("AFFILIATE_TAG_FLIPKART", "").strip() # e.g. youraffid
AFFILIATE_TAG_SHOP = os.getenv("AFFILIATE_TAG_SHOP", "").strip()       # optional
ADD_TAG = os.getenv("ADD_TAG", "true").lower() == "true"
SKIP_NO_LINK = os.getenv("SKIP_NO_LINK", "true").lower() == "true"

# ---------- platform detection ----------
PLATFORMS = [
    ("Amazon",   r"(amazon\.in|amazon\.com|amzn\.to|amzn\.in)", "#Amazon"),
    ("Flipkart", r"(flipkart\.com|fkrt\.it|flipkart\.in)", "#Flipkart"),
    ("Shop",     r"(shop\.app|shopify\.com|shop\.amazon|myntra\.com|ajio\.com|meesho\.com)", "#Shop"),
]
COMPILED = [(name, re.compile(pat, re.I), tag) for name, pat, tag in PLATFORMS]

URL_RE = re.compile(r"https?://[^\s]+")

def detect_platform(text: str) -> tuple[str, str] | None:
    for name, rx, tag in COMPILED:
        if rx.search(text or ""):
            return name, tag
    return None

def add_affiliate_tag(url: str, platform: str) -> str:
    tag = {"Amazon": AFFILIATE_TAG_AMAZON, "Flipkart": AFFILIATE_TAG_FLIPKART, "Shop": AFFILIATE_TAG_SHOP}.get(platform, "")
    if not tag:
        return url
    sep = "&" if "?" in url else "?"
    if platform == "Amazon":
        return f"{url}{sep}tag={tag}"
    if platform == "Flipkart":
        return f"{url}{sep}affid={tag}"
    return url

# ---------- handlers ----------
async def forward_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or msg.from_user is None:
        return

    chat_id = str(msg.chat_id)
    # First-run helper: print ids so you can fill .env
    print(f"[seen] chat_id={chat_id} title={msg.chat.title if msg.chat else ''} from={msg.from_user.first_name}")

    # Only forward from source (empty SOURCE = listen everywhere in first setup run)
    if SOURCE_CHAT_ID and chat_id != SOURCE_CHAT_ID:
        return
    if not DEST_CHAT_ID:
        if SOURCE_CHAT_ID:
            print("[warn] DEST_CHAT_ID not set in .env, skipping forward")
        return

    text = msg.text or msg.caption or ""
    links = URL_RE.findall(text)
    if SKIP_NO_LINK and not links:
        return

    found = detect_platform(text)
    if not found:
        # No known platform link -> forward as-is with generic tag unless disabled
        if not links:
            return
        header = "#Deal"
    else:
        name, tag = found
        header = f"{tag} #Deal" if ADD_TAG else f"{name} deal:"

    # Rewrite links with affiliate tag
    new_text = text
    if found:
        name = found[0]
        new_text = URL_RE.sub(lambda m: add_affiliate_tag(m.group(0).rstrip(")"), name), new_text)
        if new_text and not new_text.startswith(header):
            new_text = f"{header}\n{new_text}"

    # Forward: text / photo with caption / other media
    try:
        if msg.text:
            await context.bot.send_message(chat_id=int(DEST_CHAT_ID) if DEST_CHAT_ID.lstrip("-").isdigit() else DEST_CHAT_ID, text=new_text, disable_web_page_preview=False)
        elif msg.photo:
            await context.bot.send_photo(chat_id=DEST_CHAT_ID, photo=msg.photo[-1].file_id, caption=new_text[:1024] if new_text else None)
        elif msg.video:
            await context.bot.send_video(chat_id=DEST_CHAT_ID, video=msg.video.file_id, caption=new_text[:1024] if new_text else None)
        elif msg.document:
            await context.bot.send_document(chat_id=DEST_CHAT_ID, document=msg.document.file_id, caption=new_text[:1024] if new_text else None)
        else:
            # Fallback: copy_message (forwards almost any type)
            await context.bot.copy_message(chat_id=DEST_CHAT_ID, from_chat_id=chat_id, message_id=msg.message_id)
        print(f"[forwarded] {header} -> {DEST_CHAT_ID}")
    except Exception as e:
        print(f"[error] forward failed: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Deal bot is running. Send a deal link here (with amazon/flipkart link) and it will tag + forward.\n"
        f"Source: {SOURCE_CHAT_ID or '(not set)'}\nDest: {DEST_CHAT_ID or '(not set - fill .env)'}"
    )

def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set. Create .env from .env.example and fill BOT_TOKEN from @BotFather")
        raise SystemExit(1)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_deal))
    print("Bot started. Add bot as admin to source group + dest channel, then post a deal link to test.")
    if not SOURCE_CHAT_ID or not DEST_CHAT_ID:
        print("Tip: SOURCE_CHAT_ID / DEST_CHAT_ID empty -> check logs for chat_id after you send a message in the group, then fill .env and restart.")
    app.run_polling()

if __name__ == "__main__":
    main()
