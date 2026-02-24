# 🔍 Prospect Scanner

Multi-platform opportunity finder that scans Reddit, Twitter/X, LinkedIn, Product Hunt, and Hacker News for people looking for developers/builders. Generates hyper-personalized outreach messages using Gemini AI.

Built by [@alankritxghosh](https://github.com/alankritxghosh)

## How It Works

```
Scan 5 platforms → Find people who need a builder → Generate personalized messages → Daily markdown digest
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up API keys in .env
cp .env.example .env
# Add your Gemini API key (free: aistudio.google.com)
# Add your Apify token (free: console.apify.com)

# 3. Run it
python main.py              # Scan all platforms
python main.py --hn-only    # Hacker News only (no Apify needed)
python main.py --no-personalize  # Scan without AI messages
```

## Platforms Scanned

| Platform | Method | Cost | What It Finds |
|---|---|---|---|
| Hacker News | HN Algolia API | Free | "Who is Hiring" threads, Ask HN posts |
| Reddit | Apify | Free tier | Posts in r/SaaS, r/startups, r/cofounder |
| Twitter/X | Apify | Free tier | Tweets asking for developers |
| LinkedIn | Apify | Free tier | founder posts seeking technical help |
| Product Hunt | Apify | Free tier | New launches by non-technical founders |

## Output

Daily markdown digest saved to `output/digest_YYYY-MM-DD.md` with:
- Every opportunity found across all platforms
- AI-personalized draft messages (via Gemini)
- Follow-up messages for no-reply scenarios
- Direct links to each opportunity

## API Keys

| Key | Where to Get | Cost |
|---|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | Free |
| `APIFY_TOKEN` | [console.apify.com](https://console.apify.com/account#/integrations) | Free tier (~$5/month compute) |

## Project Structure

```
prospect-scanner/
├── main.py              # Entry point — orchestrates everything
├── config.py            # Keywords, subreddits, your profile
├── personalizer.py      # Gemini API — generates personalized messages
├── scanners/
│   ├── hackernews.py    # HN Algolia API (free, no auth)
│   └── apify_scanners.py  # Reddit, Twitter, LinkedIn, PH via Apify
├── output/              # Daily digest files
├── .env                 # Your API keys (gitignored)
└── requirements.txt
```

## License

MIT
