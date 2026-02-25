"""
Gemini Personalizer — generates hyper-personalized outreach messages
using Google's Gemini API (free tier).
"""

import os
import json
import google.generativeai as genai
from config import YOUR_PROFILE


# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def _get_model():
    """Initialize and return Gemini model."""
    if not GEMINI_API_KEY:
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-2.0-flash")


def personalize_opportunity(opportunity: dict) -> dict:
    """
    Takes a raw opportunity and generates a personalized draft reply/message.
    Returns the opportunity dict with added 'draft_message' and 'draft_follow_up' fields.
    """
    model = _get_model()
    if not model:
        opportunity["draft_message"] = "[⚠️ GEMINI_API_KEY not set — no personalization]"
        opportunity["draft_follow_up"] = ""
        return opportunity

    platform = opportunity.get("platform", "")
    author = opportunity.get("author", "someone")
    author_name = opportunity.get("author_name", author)
    author_bio = opportunity.get("author_bio", "")
    author_title = opportunity.get("author_title", "")
    text = opportunity.get("text", "")
    title = opportunity.get("title", "")

    # Build context about the author
    author_context = f"Name: {author_name}"
    if author_bio:
        author_context += f"\nBio: {author_bio}"
    if author_title:
        author_context += f"\nTitle: {author_title}"

    prompt = f"""You are writing a personalized outreach message for {YOUR_PROFILE['name']}, 
an {YOUR_PROFILE['title']} who {YOUR_PROFILE['speed']}.

ABOUT THE SENDER:
- Skills: {YOUR_PROFILE['skills']}
- Products built: {', '.join(YOUR_PROFILE['products'])}
- Portfolio: {YOUR_PROFILE['portfolio']}
- Goals: {YOUR_PROFILE.get('goals', '')}

THE OPPORTUNITY:
Platform: {platform}
Their post/message: "{title} — {text}"
About them: {author_context}

RULES:
1. Reference something SPECIFIC from their post — not generic
2. Connect it to something the sender has actually built
3. Cold Email: Keep it under 8 lines, professional but warm, and end with a low-friction CTA.
4. LinkedIn Connection Note: MUST BE STRICTLY UNDER 300 CHARACTERS. Be punchy and direct. Not a hard sell.
5. Do NOT mention pricing. Do NOT say "I came across your profile".

Generate TWO things:
1. COLD EMAIL
2. LINKEDIN NOTE

Format:
EMAIL:
[cold email body]

LINKEDIN:
[linkedin note body]
"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Parse the response
        email = ""
        linkedin = ""
        search = ""

        if "EMAIL:" in result_text:
            parts = result_text.split("LINKEDIN:")
            email = parts[0].replace("EMAIL:", "").strip()
            if len(parts) > 1:
                linkedin = parts[1].strip()

        opportunity["cold_email"] = email or result_text
        opportunity["linkedin_note"] = linkedin

    except Exception as e:
        opportunity["cold_email"] = f"[⚠️ Gemini error: {e}]"
        opportunity["linkedin_note"] = ""

    return opportunity


def personalize_batch(opportunities: list[dict], max_personalize: int = 20) -> list[dict]:
    """
    Personalize a batch of opportunities. Limits to max_personalize to stay within
    Gemini free tier rate limits (15 RPM).
    """
    import time

    model = _get_model()
    if not model:
        print("  ⚠️ GEMINI_API_KEY not set — skipping personalization")
        for opp in opportunities:
            opp["draft_message"] = "[Set GEMINI_API_KEY to enable personalization]"
            opp["draft_follow_up"] = ""
        return opportunities

    print(f"  ✍️ Personalizing {min(len(opportunities), max_personalize)} messages...")

    for i, opp in enumerate(opportunities[:max_personalize]):
        opp = personalize_opportunity(opp)
        opportunities[i] = opp

        # Rate limit: 15 RPM on free tier = 1 every 4 seconds
        if i < max_personalize - 1:
            time.sleep(4)

        if (i + 1) % 5 == 0:
            print(f"    ✅ Personalized {i + 1}/{min(len(opportunities), max_personalize)}")

    print(f"  ✅ Personalization complete")
    return opportunities


def filter_and_rank_opportunities(opportunities: list[dict], top_k: int = 10) -> list[dict]:
    """
    Uses Gemini to evaluate all opportunities against the user's profile and returns the top 10.
    """
    if not opportunities:
        return []

    model = _get_model()
    if not model:
        print("  ⚠️ GEMINI_API_KEY not set — skipping ranking and returning top 10 natively")
        return opportunities[:top_k]

    print(f"  🧠 AI is ranking {len(opportunities)} opportunities to find the top {top_k}...")

    # Prepare catalog
    catalog = ""
    for i, opp in enumerate(opportunities):
        catalog += f"ID: {i}\n"
        catalog += f"Platform: {opp.get('platform')}\n"
        catalog += f"Title: {opp.get('title')}\n"
        catalog += f"Text: {opp.get('text', '')[:300]}\n"
        catalog += "---\n"

    prompt = f"""You are an elite lead generation assistant for {YOUR_PROFILE['name']}.
Your goal is to evaluate a list of leads (project opportunities) and select the absolute BEST {top_k} fits.

ABOUT {YOUR_PROFILE['name']}:
- Title: {YOUR_PROFILE['title']}
- Speed: {YOUR_PROFILE['speed']}
- Skills: {YOUR_PROFILE['skills']}
- Portfolio/Products: {', '.join(YOUR_PROFILE['products'])}
- Goals: {YOUR_PROFILE.get('goals', '')}

INSTRUCTIONS:
1. Review the provided catalog of {len(opportunities)} leads.
2. Select the top {top_k} IDs that are the highest quality matches for the sender's skills, speed, and specifically their goals (e.g. prioritize YC-backed companies, young hungry teams, or founding engineer roles).
3. Return ONLY a valid JSON array of integers representing the chosen IDs. No markdown formatting, no explanations, just the JSON array.
Example output: [5, 12, 45, 2, 99, 102, 34, 1, 88, 7]

CATALOG:
{catalog}
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()
            
        top_ids = json.loads(text)
        
        # Ensure we only get valid indices
        valid_ids = [i for i in top_ids if isinstance(i, int) and 0 <= i < len(opportunities)]
        
        top_opportunities = [opportunities[i] for i in valid_ids[:top_k]]
        
        # Fallback if Gemini didn't return enough 
        if not top_opportunities:
            print("  ⚠️ AI ranking returned empty, falling back to recent ones.")
            return opportunities[:top_k]

        print(f"  ✅ AI successfully selected top {len(top_opportunities)} leads")
        return top_opportunities

    except Exception as e:
        print(f"  ⚠️ Error during AI ranking: {e}. Falling back to default top {top_k}.")
        return opportunities[:top_k]
