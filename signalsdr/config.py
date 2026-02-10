"""SignalSDR configuration: keywords, exclusions, and defaults."""

# High-value hiring keywords to detect on careers pages
SIGNAL_KEYWORDS = [
    "VP",
    "Vice President",
    "Director",
    "Head of",
    "Chief",
    "CISO",
    "CTO",
    "CIO",
    "Security",
    "AI",
    "Machine Learning",
    "Series B",
    "Series C",
]

# Risk/news keywords for second-pass analysis (v0.2)
RISK_KEYWORDS = [
    "Data Breach",
    "Ransomware",
    "Compliance Violation",
    "GDPR Fine",
    "Series B",
    "Series C",
    "Acquisition",
    "IPO",
]

# Roles to ignore (noise reduction)
EXCLUDE_KEYWORDS = [
    "Intern",
    "Associate",
    "Junior",
    "Entry Level",
    "Part-time",
    "Part time",
    "Social Security",
]

# Prospect signal categories tailored to your company's market
# (technical documentation, diagnostics, parts catalogs, training for OEMs)
# {company} is replaced at runtime
PROSPECT_CATEGORIES = {
    "new_model": '"{company}" new model OR new vehicle OR new product launch OR new equipment announced',
    "service_challenge": '"{company}" service operations OR technician shortage OR parts supply OR recall OR warranty',
    "ev_transition": '"{company}" electric vehicle OR EV OR electrification OR battery OR hybrid transition',
    "regulatory": '"{company}" regulation OR compliance OR safety standard OR emissions OR right to repair',
}

# Keywords for scanning company news/blog pages directly (maps keyword → category)
NEWS_PAGE_KEYWORDS = {
    # new_model
    "new model": "new_model",
    "new vehicle": "new_model",
    "new product": "new_model",
    "product launch": "new_model",
    "all-new": "new_model",
    "next-generation": "new_model",
    "unveils": "new_model",
    "introduces": "new_model",
    "autonomous": "new_model",
    # service_challenge
    "recall": "service_challenge",
    "warranty": "service_challenge",
    "technician": "service_challenge",
    "service network": "service_challenge",
    "parts supply": "service_challenge",
    "service center": "service_challenge",
    # ev_transition
    "electric vehicle": "ev_transition",
    "electrification": "ev_transition",
    "battery": "ev_transition",
    "EV platform": "ev_transition",
    "zero emission": "ev_transition",
    "hybrid": "ev_transition",
    "charging": "ev_transition",
    # regulatory
    "regulation": "regulatory",
    "compliance": "regulatory",
    "safety standard": "regulatory",
    "emissions": "regulatory",
    "right to repair": "regulatory",
    "NHTSA": "regulatory",
}

# Brave Search freshness filter: "pd" = past day, "pw" = past week, "pm" = past month
PROSPECT_FRESHNESS = "pw"

# Max search results per category per company
PROSPECT_MAX_RESULTS = 5

# Max prospect signals per company (after dedup, before LLM drafting)
# Prioritizes category diversity: takes 1 from each category first, then fills remaining
MAX_PROSPECT_SIGNALS_PER_COMPANY = 5

# Rate limiting: seconds to wait between scrapes
SCRAPE_DELAY_SECONDS = 2

# HTTP request settings
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
