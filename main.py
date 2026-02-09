from __future__ import annotations

"""
SignalSDR Main Loop.

The orchestration script that ties together the full pipeline:
  1. Read targets from CSV
  2. Check state (skip recently scanned companies)
  3. Scrape careers pages (Feature A)
  4. Analyze for hiring signals (Feature A)
  5. Generate email drafts via LLM (Feature B)
  6. Save to CSV + optional Slack (Feature C)
  7. Update state in db.json

Usage:
    python main.py                          # Run with defaults
    python main.py --targets my_targets.csv # Custom target file
    python main.py --model anthropic/claude-sonnet-4-5  # Use Claude
    python main.py --dry-run                # Scan only, no LLM drafts
"""

import argparse
import asyncio
import csv
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from signalsdr.analyzer import analyze_text
from signalsdr.config import SCRAPE_DELAY_SECONDS
from signalsdr.drafter import generate_draft
from signalsdr.output import append_to_csv, append_to_markdown, send_slack_notification
from signalsdr.scraper import fetch_page
from signalsdr.state import record_scan, should_scan


def load_targets(csv_path: str | Path) -> list[dict]:
    """Load target companies from CSV file."""
    targets = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            targets.append({
                "company": row["company"].strip(),
                "domain": row["domain"].strip(),
                "careers_url": row["careers_url"].strip(),
            })
    return targets


async def run_pipeline(
    targets_path: str = "targets.csv",
    output_path: str = "drafts_output.csv",
    db_path: str = "data/db.json",
    model: str = "openai/gpt-4o",
    dry_run: bool = False,
) -> dict:
    """
    Run the full SignalSDR pipeline.

    Returns a summary dict with counts of scanned, signals, drafts.
    """
    targets = load_targets(targets_path)
    db = Path(db_path)

    stats = {"scanned": 0, "skipped": 0, "signals": 0, "drafts": 0, "filtered": 0, "errors": 0}

    print(f"SignalSDR: Processing {len(targets)} targets")
    print(f"  Model: {model}")
    print(f"  Output: {output_path}")
    print(f"  Dry run: {dry_run}")
    print()

    for i, target in enumerate(targets):
        company = target["company"]
        domain = target["domain"]
        url = target["careers_url"]

        # --- State check: skip if recently scanned ---
        if not should_scan(domain, db):
            print(f"[{i+1}/{len(targets)}] SKIP {company} (scanned within 24h)")
            stats["skipped"] += 1
            continue

        # --- Feature A: Scrape ---
        print(f"[{i+1}/{len(targets)}] SCAN {company} ({url})")
        result = fetch_page(url)

        if not result.success:
            print(f"  ERROR: {result.error}")
            stats["errors"] += 1
            record_scan(domain, company, [], db)
            continue

        stats["scanned"] += 1
        print(f"  Fetched {len(result.text)} chars from '{result.title}'")

        # --- Feature A: Analyze ---
        analysis = analyze_text(result.text, url, company)

        if not analysis.has_signals:
            print("  No signals found")
            record_scan(domain, company, [], db)
        else:
            print(f"  {len(analysis.signals)} signal(s) detected:")
            # Deduplicate signals by keyword
            seen_keywords = set()
            unique_signals = []
            for s in analysis.signals:
                if s.keyword not in seen_keywords:
                    seen_keywords.add(s.keyword)
                    unique_signals.append(s)
                    print(f"    [{s.keyword}] {s.matched_text[:80]}")

            stats["signals"] += len(unique_signals)

            # --- Feature B: Draft (one per unique keyword) ---
            if not dry_run:
                for signal in unique_signals:
                    draft = await generate_draft(
                        company=company,
                        role=signal.matched_text[:100],
                        model=model,
                    )

                    if draft.is_valid:
                        print(f"    Draft: \"{draft.subject_line}\"")
                        stats["drafts"] += 1

                        # --- Feature C: Output ---
                        append_to_csv(draft, url, output_path)
                        append_to_markdown(draft, url)
                        send_slack_notification(draft)
                    elif draft.success and not draft.is_valid:
                        # LLM intentionally returned null = false positive filtered
                        print(f"    Filtered by LLM (not a real job listing): {signal.keyword}")
                        stats["filtered"] += 1
                    else:
                        print(f"    Draft failed: {draft.error}")
                        stats["errors"] += 1

            # Record scan with signals
            signal_dicts = [
                {"keyword": s.keyword, "matched_text": s.matched_text}
                for s in unique_signals
            ]
            record_scan(domain, company, signal_dicts, db)

        # Rate limit between targets
        if i < len(targets) - 1:
            time.sleep(SCRAPE_DELAY_SECONDS)

    # --- Summary ---
    print()
    print("--- SignalSDR Run Complete ---")
    print(f"  Scanned: {stats['scanned']}")
    print(f"  Skipped: {stats['skipped']} (recently scanned)")
    print(f"  Signals: {stats['signals']}")
    print(f"  Drafts:  {stats['drafts']}")
    print(f"  Filtered: {stats['filtered']} (false positives caught by LLM)")
    print(f"  Errors:  {stats['errors']}")

    return stats


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="SignalSDR: Hiring Signal Detection Agent")
    parser.add_argument("--targets", default="targets.csv", help="Path to targets CSV")
    parser.add_argument("--output", default="drafts_output.csv", help="Path to output CSV")
    parser.add_argument("--db", default="data/db.json", help="Path to state database")
    parser.add_argument("--model", default="openai/gpt-4o", help="LLM model (litellm format)")
    parser.add_argument("--dry-run", action="store_true", help="Scan only, skip LLM drafting")
    args = parser.parse_args()

    asyncio.run(run_pipeline(
        targets_path=args.targets,
        output_path=args.output,
        db_path=args.db,
        model=args.model,
        dry_run=args.dry_run,
    ))


if __name__ == "__main__":
    main()
