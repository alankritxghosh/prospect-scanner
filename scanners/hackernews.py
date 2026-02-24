"""
Hacker News Scanner — scans HN for hiring posts and project opportunities.
Uses the free HN API (no auth needed).
"""

import requests
from datetime import datetime, timedelta


HN_API_BASE = "https://hacker-news.firebaseio.com/v0"

# Keywords that signal someone needs a builder
OPPORTUNITY_KEYWORDS = [
    "looking for", "need a developer", "hiring", "cofounder",
    "technical cofounder", "build", "MVP", "freelance", "contract",
    "part-time", "remote developer", "full-stack", "frontend", "backend",
    "next.js", "react", "typescript", "supabase", "ai", "automation",
    "seeking developer", "help building",
]


def fetch_item(item_id: int) -> dict | None:
    """Fetch a single HN item by ID."""
    try:
        resp = requests.get(f"{HN_API_BASE}/item/{item_id}.json", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return None


def is_recent(item: dict, hours: int = 72) -> bool:
    """Check if an item was posted within the last N hours."""
    if not item or "time" not in item:
        return False
    item_time = datetime.fromtimestamp(item["time"])
    return datetime.now() - item_time < timedelta(hours=hours)


def matches_keywords(text: str) -> list[str]:
    """Check if text contains any opportunity keywords. Returns matched keywords."""
    if not text:
        return []
    text_lower = text.lower()
    return [kw for kw in OPPORTUNITY_KEYWORDS if kw in text_lower]


def scan_who_is_hiring() -> list[dict]:
    """
    Scan the most recent 'Who is Hiring' and 'Freelancer? Seeking Freelancer?' threads.
    """
    print("  📡 Scanning Hacker News...")
    opportunities = []

    # Search for recent hiring threads via HN search API
    search_queries = [
        "Ask HN: Who is hiring",
        "Ask HN: Freelancer? Seeking freelancer",
        "Ask HN: Who wants to be hired",
    ]

    for query in search_queries:
        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search",
                params={
                    "query": query,
                    "tags": "story",
                    "numericFilters": f"created_at_i>{int((datetime.now() - timedelta(days=60)).timestamp())}",
                    "hitsPerPage": 3,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                continue

            hits = resp.json().get("hits", [])
            for story in hits:
                story_id = story.get("objectID")
                if not story_id:
                    continue

                # Fetch story to get comment IDs
                story_data = fetch_item(int(story_id))
                if not story_data or "kids" not in story_data:
                    continue

                # Scan top 50 comments (these are individual job postings)
                for comment_id in story_data["kids"][:50]:
                    comment = fetch_item(comment_id)
                    if not comment or comment.get("deleted") or comment.get("dead"):
                        continue

                    text = comment.get("text", "")
                    matched = matches_keywords(text)

                    if matched:
                        opportunities.append({
                            "platform": "Hacker News",
                            "type": "Who is Hiring",
                            "title": story.get("title", "HN Thread"),
                            "text": text[:500],  # Truncate
                            "url": f"https://news.ycombinator.com/item?id={comment_id}",
                            "author": comment.get("by", "unknown"),
                            "keywords_matched": matched,
                            "posted": datetime.fromtimestamp(comment.get("time", 0)).strftime("%Y-%m-%d %H:%M"),
                        })

        except requests.RequestException as e:
            print(f"    ⚠️ Error searching HN for '{query}': {e}")

    # Also scan recent "Show HN" and "Ask HN" for non-technical founders
    try:
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": "need developer OR looking for cofounder OR build MVP",
                "tags": "(story,comment)",
                "numericFilters": f"created_at_i>{int((datetime.now() - timedelta(days=7)).timestamp())}",
                "hitsPerPage": 20,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            for hit in resp.json().get("hits", []):
                text = hit.get("comment_text") or hit.get("title") or ""
                matched = matches_keywords(text)
                if matched:
                    item_id = hit.get("objectID", "")
                    opportunities.append({
                        "platform": "Hacker News",
                        "type": "Comment/Story",
                        "title": hit.get("story_title") or hit.get("title", ""),
                        "text": text[:500],
                        "url": f"https://news.ycombinator.com/item?id={item_id}",
                        "author": hit.get("author", "unknown"),
                        "keywords_matched": matched,
                        "posted": hit.get("created_at", "unknown"),
                    })
    except requests.RequestException as e:
        print(f"    ⚠️ Error searching HN stories: {e}")

    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for opp in opportunities:
        if opp["url"] not in seen_urls:
            seen_urls.add(opp["url"])
            unique.append(opp)

    print(f"  ✅ Found {len(unique)} HN opportunities")
    return unique
