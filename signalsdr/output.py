from __future__ import annotations

"""
SignalSDR Output Module (Feature C from spec).

Writes results to drafts_output.csv and optionally sends
Slack notifications via webhook. The agent never sends emails
directly - it only writes drafts for human review.
"""

import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

from signalsdr.drafter import EmailDraft


OUTPUT_CSV_HEADERS = [
    "timestamp",
    "company",
    "role_detected",
    "draft_subject",
    "draft_body",
    "status",
    "model",
    "url",
]


def append_to_csv(
    draft: EmailDraft,
    url: str,
    output_path: str | Path = "drafts_output.csv",
) -> None:
    """
    Append a draft result as a row to the output CSV.

    Creates the file with headers if it doesn't exist yet.

    Args:
        draft: The generated email draft.
        url: The source careers page URL.
        output_path: Path to the output CSV file.
    """
    output_path = Path(output_path)
    file_exists = output_path.exists()

    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_CSV_HEADERS)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "company": draft.company,
            "role_detected": draft.role,
            "draft_subject": draft.subject_line or "",
            "draft_body": draft.body or "",
            "status": "PENDING_REVIEW" if draft.is_valid else "DRAFT_FAILED",
            "model": draft.model,
            "url": url,
        })


def append_to_markdown(
    draft: EmailDraft,
    url: str,
    output_path: str | Path = "drafts_output.md",
) -> None:
    """Append a draft as a readable markdown section."""
    output_path = Path(output_path)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    is_new = not output_path.exists()

    with open(output_path, "a", encoding="utf-8") as f:
        if is_new:
            f.write("# SignalSDR Drafts\n\n")

        f.write(f"## {draft.company} — {draft.role}\n")
        f.write(f"**Subject:** {draft.subject_line}\n\n")
        f.write(f"{draft.body}\n\n")
        f.write(f"*{ts} | {draft.model} | [source]({url})*\n\n")
        f.write("---\n\n")


def send_slack_notification(
    draft: EmailDraft,
    webhook_url: str | None = None,
) -> bool:
    """
    Send a Slack notification about a detected signal.

    Args:
        draft: The generated email draft.
        webhook_url: Slack webhook URL (falls back to SLACK_WEBHOOK_URL env var).

    Returns:
        True if the notification was sent successfully.
    """
    webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return False

    text = (
        f"Signal Detected: {draft.company} is hiring a {draft.role}.\n"
        f"Subject: {draft.subject_line}\n"
        f"Status: {'Draft Created' if draft.is_valid else 'Draft Failed'}"
    )

    try:
        resp = requests.post(
            webhook_url,
            json={"text": text},
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException:
        return False
