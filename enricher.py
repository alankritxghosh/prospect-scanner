import re
import requests
import json
import google.generativeai as genai
import os

from config import YOUR_PROFILE

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def _get_model():
    """Initialize and return Gemini model."""
    if not GEMINI_API_KEY:
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-2.0-flash")

def _fetch_hn_user_bio(username: str) -> str:
    """Fetch user bio from Hacker News to look for emails/links."""
    if not username or username == "unknown":
        return ""
        
    try:
        url = f"https://hacker-news.firebaseio.com/v0/user/{username}.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data and "about" in data:
                return data["about"]
    except Exception:
        pass
    return ""

def _extract_emails_from_text(text: str) -> list[str]:
    """Basic regex to find emails in text."""
    if not text:
        return []
    # Basic email regex
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return list(set(emails))

def enrich_opportunity(opp: dict) -> dict:
    """
    Finds the person's email and LinkedIn URL.
    Checks HN bio first (if applicable), then uses Gemini to extract/guess
    from the post content.
    """
    platform = opp.get("platform", "")
    author = opp.get("author", "unknown")
    text = opp.get("text", "")
    title = opp.get("title", "")
    url = opp.get("url", "")
    
    found_emails = []
    author_bio = ""

    # 1. If Hacker News, fetch their profile
    if platform == "Hacker News" and author != "unknown":
        author_bio = _fetch_hn_user_bio(author)
        if author_bio:
            # Add bio to opp for later use by personalizer
            opp["author_bio"] = author_bio
            found_emails.extend(_extract_emails_from_text(author_bio))

    # 2. Extract emails from post text itself
    found_emails.extend(_extract_emails_from_text(text))
    
    # Clean and deduplicate emails
    found_emails = list(set([e.lower() for e in found_emails]))
    
    # 3. Use Gemini to do deep extraction for LinkedIn URL and guess email if missing
    model = _get_model()
    if not model:
        opp["email"] = found_emails[0] if found_emails else ""
        opp["linkedin_url"] = ""
        return opp
        
    prompt = f"""You are a data enrichment bot. Your job is to find the Email Address and construct the LinkedIn Profile URL for a person who posted an opportunity.

PERSON POSTED THIS:
Platform: {platform}
Author Username: {author}
Author Bio: {author_bio}
Post Link: {url}
Post Title: {title}
Post Content: {text}

INSTRUCTIONS:
1. EMAIL: If an email is explicitly mentioned in the text, title, or bio, use it. If a domain is mentioned (e.g. "We are AcmeCorp"), you can guess the email (e.g. founder@acmecorp.com or username@acmecorp.com) but ONLY if you are highly confident. If you have no idea, return "".
2. LINKEDIN: If a LinkedIn URL is explicitly in the bio/text, use it. Otherwise, guess their LinkedIn URL based on their username or company (e.g. "https://linkedin.com/in/username" or "https://linkedin.com/company/startupname"). If you have no idea, return a Google Search Query instead (e.g. 'site:linkedin.com "username" "startupname"').

Respond ONLY with a valid JSON object. Do not include markdown formatting like ```json.
{{
  "email": "extracted or highly confident guessed email, or empty string",
  "linkedin_url": "explicit url, guessed url, or search query"
}}
"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Clean markdown
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        elif result_text.startswith("```"):
            result_text = result_text.replace("```", "").strip()
            
        data = json.loads(result_text)
        
        # If Gemini didn't find an email, but our regex did, use regex
        final_email = data.get("email", "").strip()
        if not final_email and found_emails:
            final_email = found_emails[0]
            
        opp["email"] = final_email
        opp["linkedin_url"] = data.get("linkedin_url", "").strip()
        
    except Exception as e:
        print(f"    ⚠️ Enrichment AI error for {author}: {e}")
        opp["email"] = found_emails[0] if found_emails else ""
        opp["linkedin_url"] = ""

    return opp

def enrich_batch(opportunities: list[dict]) -> list[dict]:
    """Enrich a batch of leads with emails and linkedin URLs."""
    import time
    print(f"  🔍 Enriching {len(opportunities)} leads (finding emails & linkedin)...")
    
    for i, opp in enumerate(opportunities):
        opportunities[i] = enrich_opportunity(opp)
        
        # Rate limit protection (Gemini free tier)
        if i < len(opportunities) - 1:
            time.sleep(4)
            
    print("  ✅ Enrichment complete")
    return opportunities
