from __future__ import annotations

"""
SignalSDR Prospector Module.

Two signal sources:
  1. Brave Search API — searches the web for business signals
  2. News page scraping — fetches company blogs/newsrooms directly
"""

import os
import re
import time
from dataclasses import dataclass, field

import requests

from signalsdr.config import (
    NEWS_PAGE_KEYWORDS,
    PROSPECT_CATEGORIES,
    PROSPECT_FRESHNESS,
    PROSPECT_MAX_RESULTS,
    REQUEST_TIMEOUT_SECONDS,
)


@dataclass
class ProspectSignal:
    """A single prospect signal."""

    category: str  # new_model, service_challenge, ev_transition, regulatory
    headline: str
    snippet: str
    source_url: str


@dataclass
class ProspectResult:
    """Aggregated prospect signals for one company."""

    company: str
    domain: str
    signals: list[ProspectSignal] = field(default_factory=list)
    success: bool = True
    error: str = ""

    @property
    def has_signals(self) -> bool:
        return len(self.signals) > 0


def search_brave(
    query: str,
    api_key: str,
    freshness: str = PROSPECT_FRESHNESS,
    count: int = PROSPECT_MAX_RESULTS,
) -> list[dict]:
    """
    Query the Brave Search API and return raw result items.

    Args:
        query: The search query string.
        api_key: Brave Search API key.
        freshness: Time filter (pd=past day, pw=past week, pm=past month).
        count: Maximum number of results.

    Returns:
        List of result dicts with 'title', 'description', 'url' keys.
    """
    resp = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        },
        params={
            "q": query,
            "freshness": freshness,
            "count": count,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "url": item.get("url", ""),
        })
    return results


def prospect_company(
    company: str,
    domain: str,
    categories: list[str] | None = None,
    api_key: str | None = None,
) -> ProspectResult:
    """
    Search for prospect signals about a company via Brave Search.

    Args:
        company: Company name (e.g. "Ford").
        domain: Company domain (e.g. "ford.com").
        categories: List of category keys to search (defaults to all).
        api_key: Brave API key (falls back to BRAVE_API_KEY env var).

    Returns:
        ProspectResult with any signals found.
    """
    api_key = api_key or os.environ.get("BRAVE_API_KEY")
    if not api_key:
        return ProspectResult(
            company=company,
            domain=domain,
            success=False,
            error="BRAVE_API_KEY not set",
        )

    cats = categories or list(PROSPECT_CATEGORIES.keys())
    signals: list[ProspectSignal] = []

    for idx, cat in enumerate(cats):
        template = PROSPECT_CATEGORIES.get(cat)
        if not template:
            continue

        # Rate-limit Brave Search requests (free tier: ~1 req/sec)
        if idx > 0:
            time.sleep(1.1)

        query = template.replace("{company}", company)

        try:
            results = search_brave(query, api_key)
        except requests.RequestException as e:
            print(f"  Brave Search error for {cat}: {e}")
            continue

        for item in results:
            # Skip results from the company's own domain (self-promotional)
            if domain in item["url"]:
                continue

            signals.append(ProspectSignal(
                category=cat,
                headline=item["title"],
                snippet=item["description"][:300],
                source_url=item["url"],
            ))

    return ProspectResult(
        company=company,
        domain=domain,
        signals=signals,
    )


def scrape_news_page(
    company: str,
    domain: str,
    news_url: str,
) -> ProspectResult:
    """
    Fetch a company's blog/newsroom page and scan for prospect keywords.

    Uses the existing scraper to fetch the page, then matches lines
    against NEWS_PAGE_KEYWORDS to detect business signals.

    Args:
        company: Company name.
        domain: Company domain.
        news_url: URL of the company's news/blog page.

    Returns:
        ProspectResult with signals found on the page.
    """
    from signalsdr.scraper import fetch_page

    result = fetch_page(news_url)
    if not result.success:
        return ProspectResult(
            company=company,
            domain=domain,
            success=False,
            error=f"Failed to fetch news page: {result.error}",
        )

    signals: list[ProspectSignal] = []
    seen: set[str] = set()

    for line in result.text.splitlines():
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 25:
            continue

        # Skip comma-separated tag lists (e.g., "Electrification,Sustainability,Podcast")
        if "," in line_stripped:
            segments = [s.strip() for s in line_stripped.split(",")]
            if len(segments) >= 2 and all(len(s) <= 30 for s in segments):
                continue

        # Skip WLTP / emissions disclaimers (e.g., "WLTP combined: Energy consumption...")
        if re.search(r"kWh/100\s?km|g/km|CO₂|WLTP|NEDC", line_stripped):
            continue

        # Skip generic site chrome / image captions
        lower = line_stripped.lower()
        if any(phrase in lower for phrase in (
            "browse below", "download the right", "cookie", "privacy policy",
            "terms of use", "all rights reserved", "subscribe to",
        )):
            continue

        for keyword, category in NEWS_PAGE_KEYWORDS.items():
            if re.search(re.escape(keyword), line_stripped, re.IGNORECASE):
                # Use the matched line as the headline, deduplicate
                headline = line_stripped[:150]
                if headline in seen:
                    continue
                seen.add(headline)

                signals.append(ProspectSignal(
                    category=category,
                    headline=headline,
                    snippet=line_stripped[:300],
                    source_url=news_url,
                ))
                break  # One match per line is enough

    return ProspectResult(
        company=company,
        domain=domain,
        signals=signals,
    )
