from __future__ import annotations

"""
SignalSDR Analyzer Module (Feature A - keyword detection from spec).

Takes raw text from the scraper and detects "hiring signals" by
matching against configurable keyword lists. Filters out noise
(intern/junior roles) to surface only high-value signals.
"""

import re
from dataclasses import dataclass, field

from signalsdr.config import EXCLUDE_KEYWORDS, SIGNAL_KEYWORDS


@dataclass
class Signal:
    """A single detected hiring signal."""

    keyword: str
    matched_text: str
    line_number: int


@dataclass
class AnalysisResult:
    """Result of analyzing a page's text for hiring signals."""

    url: str
    company: str
    signals: list[Signal] = field(default_factory=list)

    @property
    def has_signals(self) -> bool:
        return len(self.signals) > 0


def _is_excluded(line: str) -> bool:
    """Check if a line matches any exclusion keyword."""
    line_lower = line.lower()
    return any(kw.lower() in line_lower for kw in EXCLUDE_KEYWORDS)


def analyze_text(
    text: str,
    url: str,
    company: str,
    keywords: list[str] | None = None,
) -> AnalysisResult:
    """
    Scan text for hiring signal keywords.

    For each line of text, checks if any keyword from the signal list
    appears (case-insensitive). Lines matching exclusion keywords are
    skipped.

    Args:
        text: The scraped page text to analyze.
        url: Source URL (for tracking).
        company: Company name (for tracking).
        keywords: Override keyword list (defaults to SIGNAL_KEYWORDS).

    Returns:
        AnalysisResult containing any detected signals.
    """
    keywords = keywords or SIGNAL_KEYWORDS
    result = AnalysisResult(url=url, company=company)

    for line_num, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue

        # Skip lines that match exclusion patterns
        if _is_excluded(line):
            continue

        for keyword in keywords:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            if pattern.search(line):
                result.signals.append(
                    Signal(
                        keyword=keyword,
                        matched_text=line.strip()[:200],  # cap at 200 chars
                        line_number=line_num,
                    )
                )

    return result
