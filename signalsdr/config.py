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
]

# Rate limiting: seconds to wait between scrapes
SCRAPE_DELAY_SECONDS = 2

# HTTP request settings
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
