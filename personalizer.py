"""
Gemini Personalizer — generates hyper-personalized outreach messages
using Google's Gemini API (free tier).
"""

import os
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

THE OPPORTUNITY:
Platform: {platform}
Their post/message: "{title} — {text}"
About them: {author_context}

RULES:
1. Reference something SPECIFIC from their post — not generic
2. Connect it to something the sender has actually built
3. Keep it under 5 lines for DMs, 8 lines for email
4. End with a low-friction CTA (15-min call, feedback, question)
5. Do NOT say "I came across your profile" or "I'm excited to"
6. Do NOT mention pricing
7. Sound like a real human, not a sales bot
8. Match the platform's tone: {'casual' if platform in ['Reddit', 'Twitter/X'] else 'professional but warm'}

Generate TWO things:
1. MAIN MESSAGE: The initial outreach message
2. FOLLOW-UP: A shorter follow-up to send if no reply in 5 days

Format:
MAIN:
[message]

FOLLOW_UP:
[follow-up message]
"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Parse the response
        main_msg = result_text
        follow_up = ""

        if "FOLLOW_UP:" in result_text:
            parts = result_text.split("FOLLOW_UP:")
            main_msg = parts[0].replace("MAIN:", "").strip()
            follow_up = parts[1].strip()
        elif "FOLLOW-UP:" in result_text:
            parts = result_text.split("FOLLOW-UP:")
            main_msg = parts[0].replace("MAIN:", "").strip()
            follow_up = parts[1].strip()

        opportunity["draft_message"] = main_msg
        opportunity["draft_follow_up"] = follow_up

    except Exception as e:
        opportunity["draft_message"] = f"[⚠️ Gemini error: {e}]"
        opportunity["draft_follow_up"] = ""

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
