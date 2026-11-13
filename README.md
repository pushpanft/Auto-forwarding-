# Telegram Affiliate Deal Auto-Forward Bot (for Pushpa)

Auto-forwards deal messages and adds platform tags: #Amazon #Flipkart #Shop

## What it does
- Listens in SOURCE_CHAT (your deal source group)
- Detects Amazon / Flipkart / Shop links
- Posts to DEST_CHAT (your public channel/group) with tag on top
- Adds your affiliate tag to links if configured

## Setup (10 minutes, no coding)

1. Open Telegram, message @BotFather
   Send `/newbot`, follow steps, copy the `BOT_TOKEN`

2. Create folder, copy files:
   ```
   cp telegram_deal_bot.py ~/deal-bot/
   cp .env.example ~/deal-bot/.env
   cd ~/deal-bot
   nano .env   # paste BOT_TOKEN
   ```

3. Add bot to:
   - Source group (where deals come from)
   - Destination channel (where you want deals posted)
   Make bot ADMIN in both (or at least "Post messages" + "Read messages").

4. First run to get IDs:
   ```
   pip install python-telegram-bot
   python3 telegram_deal_bot.py
   ```
   In Telegram, send any message in the source group.
   Terminal will print `[seen] chat_id=-100xxx...` for each chat.
   Source ID = where deals live, Dest ID = where you want them posted.

5. Fill `.env` with SOURCE_CHAT_ID, DEST_CHAT_ID, and your affiliate tags:
   - Amazon: from Amazon Associates (tag like `abc-21`)
   - Flipkart: from Flipkart affiliate dashboard
   - Shop/Shopify: if you have one

6. Run again: `python3 telegram_deal_bot.py`
   Post a test deal link in the source group. It appears in destination with #Amazon / #Flipkart / #Shop.

To run 24/7: use `python3 telegram_deal_bot.py &` or `tmux`, or deploy on a free VPS / Replit / Railway.

## Important limit (read once)
This uses official Telegram Bot API. A bot can only forward messages it can SEE.
- If deals are in a group you own -> works after adding bot as admin.
- If deals are in someone else's channel/bot and you can't add your bot -> Telegram blocks this. Then you need a user-account (Telethon) version. Tell me and I will build that instead, it needs your phone login (not recommended for public use).

## Files
- `telegram_deal_bot.py` - main bot
- `.env.example` - config template
