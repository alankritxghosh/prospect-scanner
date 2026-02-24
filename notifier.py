"""
Telegram Notifier — sends prospect digest to your Telegram.

Setup:
1. Search @BotFather on Telegram → /newbot → name it "ProspectScanner"
2. Copy the bot token to .env as TELEGRAM_BOT_TOKEN
3. Search @userinfobot on Telegram → it replies with your chat ID
4. Copy your chat ID to .env as TELEGRAM_CHAT_ID
5. IMPORTANT: Send any message to your bot first (e.g. /start) so it can message you back
"""

import os
import requests


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_API = "https://api.telegram.org/bot{token}"


def _send_telegram(text: str, parse_mode: str = "Markdown") -> bool:
    """Send a message via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    url = f"{TELEGRAM_API.format(token=TELEGRAM_BOT_TOKEN)}/sendMessage"

    try:
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }, timeout=15)

        if resp.status_code == 200:
            return True
        else:
            # Retry without parse_mode if markdown fails
            resp2 = requests.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "disable_web_page_preview": True,
            }, timeout=15)
            return resp2.status_code == 200

    except requests.RequestException as e:
        print(f"  ⚠️ Telegram error: {e}")
        return False


def _truncate(text: str, max_len: int = 200) -> str:
    """Truncate text to max length."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _escape_md(text: str) -> str:
    """Escape special markdown characters for Telegram."""
    for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(char, f'\\{char}')
    return text


def send_digest_summary(opportunities: list[dict]) -> bool:
    """
    Send a summary of today's opportunities to Telegram.
    Groups by platform, shows top opportunities with draft messages.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ⚠️ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping notifications")
        print("  💡 Set them up in .env (see notifier.py for instructions)")
        return False

    # Build summary header
    platforms = {}
    for opp in opportunities:
        p = opp.get("platform", "Unknown")
        if p not in platforms:
            platforms[p] = []
        platforms[p].append(opp)

    total = len(opportunities)
    header = f"🔍 *Prospect Scanner — Daily Digest*\n📊 *{total} opportunities found*\n\n"

    for platform, opps in platforms.items():
        header += f"• {platform}: {len(opps)} leads\n"

    _send_telegram(header)

    # Send top opportunities (max 10 to avoid spam)
    high_value = [o for o in opportunities if o.get("draft_message") and o["draft_message"].strip()]
    count = min(len(high_value), 10)

    for i, opp in enumerate(high_value[:count]):
        platform = opp.get("platform", "")
        author = opp.get("author", "unknown")
        title = _truncate(opp.get("title", ""), 100)
        url = opp.get("url", "")
        draft = opp.get("draft_message", "")

        # Clean up draft message (remove "Option 1/2" boilerplate from Gemini)
        draft_lines = draft.split("\n")
        clean_draft = []
        for line in draft_lines:
            line = line.strip()
            if line and not line.startswith("**OPTION") and not line.startswith("**Option") and not line.startswith("Here are") and not line.startswith("Okay,") and line != "****" and line != "**":
                clean_draft.append(line)
        draft = "\n".join(clean_draft[:8])  # Max 8 lines

        msg = (
            f"📌 *Lead {i+1}/{count}* — {platform}\n"
            f"👤 {author}\n"
            f"📝 {title}\n"
        )
        if url:
            msg += f"🔗 {url}\n"

        msg += f"\n💬 *Draft message:*\n{draft}\n"

        _send_telegram(msg)

    # Final summary
    _send_telegram(f"✅ Scan complete. {count} personalized leads sent. Full digest saved locally.")
    return True


def send_test_message() -> bool:
    """Send a test message to verify Telegram setup."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env first")
        print("   See notifier.py header for setup instructions")
        return False

    success = _send_telegram("✅ Prospect Scanner connected! You'll receive daily lead digests here.")
    if success:
        print("✅ Test message sent to Telegram!")
    else:
        print("❌ Failed to send. Check your bot token and chat ID.")
    return success


if __name__ == "__main__":
    send_test_message()
