# Prospect Scanner Configuration

# --- Keywords to search for across platforms ---
SEARCH_KEYWORDS = [
    "need a developer",
    "looking for developer",
    "looking for technical cofounder",
    "need technical cofounder",
    "need someone to build",
    "build my MVP",
    "build my app",
    "MVP help",
    "looking for a builder",
    "hire a developer",
    "freelance developer needed",
    "need a full stack developer",
    "looking for someone to build",
    "cofounder technical",
    "need help building",
    "who can build",
    "YC founder looking",
    "startup looking for founding engineer",
]

# --- Reddit subreddits to scan ---
SUBREDDITS = [
    "SaaS",
    "startups",
    "EntrepreneurRideAlong",
    "cofounder",
    "indiehackers",
    "sideproject",
    "webdev",
    "reactjs",
    "nextjs",
    "artificial",
]

# --- Apify actor IDs ---
APIFY_ACTORS = {
    "reddit": "trudax/reddit-scraper-lite",
    "twitter": "apidojo/tweet-scraper",
    "linkedin": "apify/google-search-scraper",
    "producthunt": "apify/google-search-scraper",
}

# --- Your profile (used for personalization) ---
YOUR_PROFILE = {
    "name": "Alankrit Ghosh",
    "title": "AI-native product builder",
    "skills": "Next.js, TypeScript, SwiftUI, Supabase, AI/LLM integration",
    "speed": "Ship MVPs in 3-10 days",
    "portfolio": "https://alankritdev.vercel.app",
    "github": "https://github.com/alankritxghosh",
    "products": [
        "Signal — macOS Gmail automation app",
        "william.ai — Anti-slop AI ghostwriting tool",
        "LeadFlow Lab — Revenue infrastructure for B2B",
    ],
    "goals": "Open to landing a founding engineer or product engineer role in a YC backed company. Looking for a young, hungry startup team where I can work closely with the founders.",
}
