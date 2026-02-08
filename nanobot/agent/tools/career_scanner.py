"""Career scanner tool: nanobot wrapper around SignalSDR scraper + analyzer."""

import json
from typing import Any

from nanobot.agent.tools.base import Tool


class CareerScannerTool(Tool):
    """Scan a company careers page for high-value hiring signals."""

    name = "career_scanner"
    description = (
        "Scrape a company careers page URL and detect hiring signals "
        "(VP, Director, Head of, CISO, etc.). Returns matched roles or "
        "an empty list if no signals found."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The careers page URL to scan",
            },
            "company": {
                "type": "string",
                "description": "Company name for tracking",
            },
        },
        "required": ["url", "company"],
    }

    async def execute(self, url: str, company: str, **kwargs: Any) -> str:
        from signalsdr.analyzer import analyze_text
        from signalsdr.scraper import fetch_page

        result = fetch_page(url)
        if not result.success:
            return json.dumps({"error": result.error, "url": url, "company": company})

        analysis = analyze_text(
            text=result.text,
            url=url,
            company=company,
        )

        signals = [
            {"keyword": s.keyword, "matched_text": s.matched_text}
            for s in analysis.signals
        ]

        return json.dumps({
            "url": url,
            "company": company,
            "page_title": result.title,
            "signal_count": len(signals),
            "signals": signals,
        })
