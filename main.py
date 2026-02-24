"""
Prospect Scanner — Multi-platform opportunity finder.

Scans Reddit, Twitter/X, LinkedIn, Product Hunt, and Hacker News
for people looking for developers/builders. Generates personalized
outreach messages using Gemini API.

Usage:
    python main.py                  # Scan all platforms
    python main.py --hn-only        # Scan Hacker News only (no Apify needed)
    python main.py --no-personalize # Scan without generating messages

Output: Markdown digest saved to output/digest_YYYY-MM-DD.md
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Load .env file manually (no external dependency)
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ[key.strip()] = value.strip().strip('"').strip("'")

from scanners.hackernews import scan_who_is_hiring
from scanners.apify_scanners import scan_reddit, scan_twitter, scan_linkedin, scan_producthunt
from personalizer import personalize_batch


def generate_digest(opportunities: list[dict]) -> str:
    """Generate a markdown digest from opportunities."""
    today = datetime.now().strftime("%B %d, %Y")
    lines = [
        f"# 🔍 Prospect Scanner — Daily Digest",
        f"**Date**: {today}",
        f"**Total Opportunities Found**: {len(opportunities)}",
        "",
    ]

    # Sort by platform
    platforms = {}
    for opp in opportunities:
        platform = opp.get("platform", "Unknown")
        if platform not in platforms:
            platforms[platform] = []
        platforms[platform].append(opp)

    # Priority emoji
    priority_emoji = {
        "Reddit": "🟠",
        "Twitter/X": "🔵",
        "Hacker News": "🟡",
        "LinkedIn": "🔷",
        "Product Hunt": "🟣",
    }

    for platform, opps in platforms.items():
        emoji = priority_emoji.get(platform, "⚪")
        lines.append(f"---")
        lines.append(f"## {emoji} {platform} ({len(opps)} opportunities)")
        lines.append("")

        for i, opp in enumerate(opps, 1):
            lines.append(f"### {i}. {opp.get('title', 'Untitled')[:80]}")
            lines.append(f"- **Author**: {opp.get('author', 'unknown')}")
            lines.append(f"- **Posted**: {opp.get('posted', 'unknown')}")
            lines.append(f"- **Type**: {opp.get('type', '')}")

            if opp.get("url"):
                lines.append(f"- **Link**: {opp['url']}")

            if opp.get("score"):
                lines.append(f"- **Score/Votes**: {opp['score']}")

            if opp.get("followers"):
                lines.append(f"- **Followers**: {opp['followers']}")

            lines.append("")
            lines.append(f"> {opp.get('text', '')[:300]}")
            lines.append("")

            if opp.get("draft_message"):
                lines.append(f"**📝 Draft Message:**")
                lines.append(f"```")
                lines.append(opp["draft_message"])
                lines.append(f"```")
                lines.append("")

            if opp.get("draft_follow_up"):
                lines.append(f"**🔄 Follow-up (if no reply in 5 days):**")
                lines.append(f"```")
                lines.append(opp["draft_follow_up"])
                lines.append(f"```")
                lines.append("")

    # Summary stats
    lines.append("---")
    lines.append("## 📊 Summary")
    for platform, opps in platforms.items():
        lines.append(f"- **{platform}**: {len(opps)} opportunities")
    lines.append("")
    lines.append(f"*Generated at {datetime.now().strftime('%H:%M:%S')} by Prospect Scanner*")

    return "\n".join(lines)


def main():
    hn_only = "--hn-only" in sys.argv
    no_personalize = "--no-personalize" in sys.argv

    print("🔍 Prospect Scanner — Starting scan...")
    print(f"   Mode: {'HN only' if hn_only else 'All platforms'}")
    print(f"   Personalization: {'OFF' if no_personalize else 'ON'}")
    print()

    all_opportunities = []

    # Always scan Hacker News (free, no API key needed)
    hn_results = scan_who_is_hiring()
    all_opportunities.extend(hn_results)

    # Scan other platforms via Apify (unless --hn-only)
    if not hn_only:
        apify_token = os.getenv("APIFY_TOKEN", "")
        if apify_token:
            reddit_results = scan_reddit()
            all_opportunities.extend(reddit_results)

            twitter_results = scan_twitter()
            all_opportunities.extend(twitter_results)

            linkedin_results = scan_linkedin()
            all_opportunities.extend(linkedin_results)

            ph_results = scan_producthunt()
            all_opportunities.extend(ph_results)
        else:
            print("  ⚠️ APIFY_TOKEN not set — skipping Reddit, Twitter, LinkedIn, Product Hunt")
            print("  💡 Get a free token at: https://console.apify.com/account#/integrations")
            print()

    print(f"\n📋 Total opportunities found: {len(all_opportunities)}")

    # Personalize messages with Gemini
    if not no_personalize and all_opportunities:
        all_opportunities = personalize_batch(all_opportunities)

    # Generate and save digest
    digest = generate_digest(all_opportunities)

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"digest_{datetime.now().strftime('%Y-%m-%d')}.md"
    output_file.write_text(digest)

    print(f"\n✅ Digest saved to: {output_file}")
    print(f"   Open it: cat {output_file}")

    return all_opportunities


if __name__ == "__main__":
    main()
