"""
Quick setup helper — gets your Telegram chat ID and tests the connection.

Usage:
1. First, send /start to @alankrit_prospects_bot on Telegram
2. Then run: python3 setup_telegram.py
"""

import os
import sys
import time
import requests
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ[key.strip()] = value.strip().strip('"').strip("'")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not set in .env")
    sys.exit(1)


def get_chat_id():
    """Get chat ID from the most recent message to the bot."""
    print("⏳ Waiting for you to message the bot on Telegram...")
    print("   → Open Telegram, search @alankrit_prospects_bot, send /start")
    print()

    for attempt in range(60):  # Wait up to 5 minutes
        resp = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
            timeout=10,
        )
        if resp.status_code == 200:
            results = resp.json().get("result", [])
            if results:
                chat_id = results[-1].get("message", {}).get("chat", {}).get("id")
                if chat_id:
                    return str(chat_id)

        if attempt % 6 == 0 and attempt > 0:
            print(f"   Still waiting... ({attempt * 5}s elapsed)")

        time.sleep(5)

    return None


def update_env(chat_id: str):
    """Update the .env file with the chat ID."""
    env_content = env_path.read_text()
    env_content = env_content.replace("TELEGRAM_CHAT_ID=", f"TELEGRAM_CHAT_ID={chat_id}")
    env_path.write_text(env_content)
    os.environ["TELEGRAM_CHAT_ID"] = chat_id


def test_message(chat_id: str):
    """Send a test message."""
    resp = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "✅ *Prospect Scanner connected!*\n\nYou'll receive daily lead digests here every morning at 9 AM.\n\nRun `python main.py --notify` to test a full scan.",
            "parse_mode": "Markdown",
        },
        timeout=10,
    )
    return resp.status_code == 200


if __name__ == "__main__":
    chat_id = get_chat_id()

    if chat_id:
        print(f"\n✅ Found your chat ID: {chat_id}")
        update_env(chat_id)
        print("✅ Updated .env with your chat ID")

        if test_message(chat_id):
            print("✅ Test message sent to Telegram!")
            print("\n🎉 Setup complete! Run: python main.py --notify")
        else:
            print("❌ Failed to send test message. Check bot permissions.")
    else:
        print("\n❌ Timed out. Make sure you sent /start to @alankrit_prospects_bot")
