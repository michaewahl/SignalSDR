"""Prospect scanner tool: nanobot wrapper around SignalSDR prospector."""

import json
from typing import Any

from nanobot.agent.tools.base import Tool


class ProspectScannerTool(Tool):
    """Search for business signals about a company via Brave Search."""

    name = "prospect_scanner"
    description = (
        "Search the web for business signals about a company — funding rounds, "
        "product launches, leadership changes, and regulatory/compliance news. "
        "Returns recent news headlines and snippets from the past week."
    )
    parameters = {
        "type": "object",
        "properties": {
            "company": {
                "type": "string",
                "description": "Company name to search for",
            },
            "domain": {
                "type": "string",
                "description": "Company domain (e.g. cloudflare.com) for filtering self-links",
            },
            "categories": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Signal categories to search (funding, product_launch, "
                    "leadership, compliance). Defaults to all."
                ),
            },
        },
        "required": ["company", "domain"],
    }

    async def execute(
        self,
        company: str,
        domain: str,
        categories: list[str] | None = None,
        **kwargs: Any,
    ) -> str:
        from signalsdr.prospector import prospect_company

        result = prospect_company(company, domain, categories=categories)

        if not result.success:
            return json.dumps({"error": result.error, "company": company})

        signals = [
            {
                "category": s.category,
                "headline": s.headline,
                "snippet": s.snippet,
                "source_url": s.source_url,
            }
            for s in result.signals
        ]

        return json.dumps({
            "company": company,
            "domain": domain,
            "signal_count": len(signals),
            "signals": signals,
        })
