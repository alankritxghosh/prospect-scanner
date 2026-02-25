"""
Apify-based scanners for Reddit, Twitter, LinkedIn, and Product Hunt.
Uses Apify's free tier (~$5/month of free compute).

To use: Set APIFY_TOKEN in your .env file.
Get a free token at: https://console.apify.com/account#/integrations
"""

import os
import time
import requests
from config import SEARCH_KEYWORDS, SUBREDDITS


APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
APIFY_BASE = "https://api.apify.com/v2"


def _run_actor(actor_id: str, run_input: dict, timeout: int = 120) -> list[dict]:
    """Run an Apify actor and return the results."""
    if not APIFY_TOKEN:
        print(f"    ⚠️ APIFY_TOKEN not set — skipping {actor_id}")
        return []

    try:
        # Start the actor run
        actor_path = actor_id.replace("/", "~")
        resp = requests.post(
            f"{APIFY_BASE}/acts/{actor_path}/runs",
            params={"token": APIFY_TOKEN},
            json=run_input,
            timeout=30,
        )
        if resp.status_code != 201:
            print(f"    ⚠️ Failed to start {actor_id}: {resp.status_code} {resp.text[:200]}")
            return []

        run_data = resp.json().get("data", {})
        run_id = run_data.get("id")
        if not run_id:
            return []

        # Poll for completion
        for _ in range(timeout // 5):
            time.sleep(5)
            status_resp = requests.get(
                f"{APIFY_BASE}/actor-runs/{run_id}",
                params={"token": APIFY_TOKEN},
                timeout=10,
            )
            if status_resp.status_code == 200:
                status = status_resp.json().get("data", {}).get("status")
                if status == "SUCCEEDED":
                    break
                elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                    print(f"    ⚠️ Actor {actor_id} {status}")
                    return []

        # Fetch results from the default dataset
        dataset_id = run_data.get("defaultDatasetId")
        if not dataset_id:
            return []

        results_resp = requests.get(
            f"{APIFY_BASE}/datasets/{dataset_id}/items",
            params={"token": APIFY_TOKEN, "limit": 100},
            timeout=30,
        )
        if results_resp.status_code == 200:
            return results_resp.json()

    except requests.RequestException as e:
        print(f"    ⚠️ Error running {actor_id}: {e}")

    return []


def scan_reddit() -> list[dict]:
    """Scan Reddit subreddits for opportunity posts using Apify."""
    print("  📡 Scanning Reddit via Apify...")
    opportunities = []

    # Build search queries
    search_terms = [
        "need a developer",
        "looking for technical cofounder",
        "build my MVP",
        "need someone to build",
        "hiring developer freelance",
    ]

    for term in search_terms[:3]:  # Limit to save Apify credits
        results = _run_actor("trudax/reddit-scraper-lite", {
            "searches": [term],
            "sort": "new",
            "time": "week",
            "maxItems": 15,
        })

        for post in results:
            title = post.get("title", "")
            text = post.get("body") or post.get("selftext") or post.get("text", "")
            subreddit = post.get("subreddit") or post.get("communityName", "")

            opportunities.append({
                "platform": "Reddit",
                "type": f"r/{subreddit}",
                "title": title,
                "text": (text or title)[:500],
                "url": post.get("url") or post.get("permalink", ""),
                "author": post.get("author") or post.get("username", "unknown"),
                "keywords_matched": [term],
                "posted": post.get("createdAt") or post.get("created", "unknown"),
                "score": post.get("score") or post.get("upVotes", 0),
            })

    print(f"  ✅ Found {len(opportunities)} Reddit opportunities")
    return opportunities


def scan_twitter() -> list[dict]:
    """Scan Twitter/X for people looking for developers/builders."""
    print("  📡 Scanning Twitter/X via Apify...")
    opportunities = []

    search_queries = [
        "need a developer to build",
        "looking for technical cofounder",
        "hiring freelance developer",
        "who can build my MVP",
        "need someone to build my app",
    ]

    for query in search_queries[:3]:  # Limit to save credits
        results = _run_actor("apidojo/tweet-scraper", {
            "searchTerms": [query],
            "maxTweets": 15,
            "sort": "Latest",
        })

        for tweet in results:
            text = tweet.get("full_text") or tweet.get("text", "")
            user = tweet.get("user", {})

            opportunities.append({
                "platform": "Twitter/X",
                "type": "Tweet",
                "title": text[:100],
                "text": text[:500],
                "url": tweet.get("url") or f"https://twitter.com/{user.get('screen_name', '')}/status/{tweet.get('id_str', '')}",
                "author": user.get("screen_name") or tweet.get("username", "unknown"),
                "author_name": user.get("name") or tweet.get("name", ""),
                "author_bio": user.get("description") or tweet.get("bio", ""),
                "keywords_matched": [query],
                "posted": tweet.get("created_at", "unknown"),
                "followers": user.get("followers_count", 0),
            })

    print(f"  ✅ Found {len(opportunities)} Twitter opportunities")
    return opportunities


def scan_linkedin() -> list[dict]:
    """Scan LinkedIn for founders posting about needing technical help."""
    print("  📡 Scanning LinkedIn via Apify...")
    opportunities = []

    results = _run_actor("apify/google-search-scraper", {
        "queries": "site:linkedin.com/posts \"looking for developer to build MVP\" OR \"need technical cofounder startup\" OR \"hiring freelance developer AI\"",
        "resultsPerPage": 20,
    })

    if results and len(results) > 0 and "organicResults" in results[0]:
        for post in results[0]["organicResults"]:
            text = post.get("description", "")
            title = post.get("title", "")
            
            # Very basic author extraction from title "Post | John Doe | LinkedIn"
            author_name = "unknown"
            if "|" in title:
                parts = [p.strip() for p in title.split("|")]
                if len(parts) >= 2: author_name = parts[-2]

            opportunities.append({
                "platform": "LinkedIn",
                "type": "Post",
                "title": title[:100],
                "text": text[:500],
                "url": post.get("url", ""),
                "author": author_name,
                "author_title": "",
                "keywords_matched": ["linkedin search"],
                "posted": "unknown",
            })

    print(f"  ✅ Found {len(opportunities)} LinkedIn opportunities")
    return opportunities


def scan_producthunt() -> list[dict]:
    """Scan Product Hunt for recent launches by non-technical founders."""
    print("  📡 Scanning Product Hunt via Apify...")
    opportunities = []

    results = _run_actor("apify/google-search-scraper", {
        "queries": "site:producthunt.com/products \"I built\" OR \"we built\" OR \"just launched\" \"seeking\" OR \"feedback\"",
        "resultsPerPage": 20,
    })

    if results and len(results) > 0 and "organicResults" in results[0]:
        for product in results[0]["organicResults"]:
            title = product.get("title", "")
            description = product.get("description", "")

            opportunities.append({
                "platform": "Product Hunt",
                "type": "Launch",
                "title": title[:100],
                "text": description[:500],
                "url": product.get("url", ""),
                "author": "unknown",
                "keywords_matched": ["ph search"],
                "posted": "unknown",
                "votes": 0,
            })

    print(f"  ✅ Found {len(opportunities)} Product Hunt launches")
    return opportunities
