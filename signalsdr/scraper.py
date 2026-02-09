from __future__ import annotations

"""
SignalSDR Scraper Module (Feature A from spec).

Fetches HTML content from career pages and extracts readable text
using requests + BeautifulSoup. This is the "eyes" of the agent.
"""

import time

import requests
from bs4 import BeautifulSoup

from signalsdr.config import (
    REQUEST_TIMEOUT_SECONDS,
    SCRAPE_DELAY_SECONDS,
    USER_AGENT,
)


class ScraperResult:
    """Container for a scrape result."""

    def __init__(self, url: str, text: str, title: str, success: bool, error: str = ""):
        self.url = url
        self.text = text
        self.title = title
        self.success = success
        self.error = error

    def __repr__(self) -> str:
        status = "OK" if self.success else f"FAIL: {self.error}"
        return f"ScraperResult(url={self.url!r}, status={status}, chars={len(self.text)})"


def fetch_page(url: str) -> ScraperResult:
    """
    Fetch a single URL and return its visible text content.

    Uses requests for HTTP and BeautifulSoup to strip HTML down to
    readable text. Removes script/style/nav/footer noise so the
    analyzer only sees meaningful content.

    Args:
        url: The careers page URL to fetch.

    Returns:
        ScraperResult with extracted text or error details.
    """
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return ScraperResult(url=url, text="", title="", success=False, error="Request timed out")
    except requests.exceptions.ConnectionError:
        return ScraperResult(url=url, text="", title="", success=False, error="Connection failed")
    except requests.exceptions.HTTPError as e:
        return ScraperResult(
            url=url, text="", title="", success=False, error=f"HTTP {e.response.status_code}"
        )
    except requests.exceptions.RequestException as e:
        return ScraperResult(url=url, text="", title="", success=False, error=str(e))

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract page title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Remove noise elements that don't contain job listings
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
        tag.decompose()

    # Get visible text, collapse whitespace
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    return ScraperResult(url=url, text=text, title=title, success=True)


def fetch_pages(urls: list[str]) -> list[ScraperResult]:
    """
    Fetch multiple URLs with rate limiting between requests.

    Respects SCRAPE_DELAY_SECONDS from config to avoid IP bans.

    Args:
        urls: List of career page URLs to scrape.

    Returns:
        List of ScraperResult objects (one per URL).
    """
    results = []
    for i, url in enumerate(urls):
        result = fetch_page(url)
        results.append(result)

        # Rate limit: sleep between requests (skip after last one)
        if i < len(urls) - 1:
            time.sleep(SCRAPE_DELAY_SECONDS)

    return results
