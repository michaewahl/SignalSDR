from __future__ import annotations

"""
SignalSDR Main Loop.

The orchestration script that ties together the full pipeline:
  1. Read targets from CSV
  2. Check state (skip recently scanned companies)
  3. Scrape careers pages (Feature A — hiring)
  4. Analyze for hiring signals (Feature A)
  5. Prospect via Brave Search (Feature D — prospect intelligence)
  6. Generate email drafts via LLM (Feature B)
  7. Save to CSV + optional Slack (Feature C)
  8. Update state in db.json

Usage:
    python main.py                          # Run hiring + prospect (if BRAVE_API_KEY set)
    python main.py --targets my_targets.csv # Custom target file
    python main.py --model anthropic/claude-sonnet-4-5  # Use Claude
    python main.py --dry-run                # Scan only, no LLM drafts
    python main.py --prospect-only          # Prospect pipeline only (skip hiring scan)
    python main.py --no-prospect            # Hiring pipeline only (skip prospect)
"""

import argparse
import asyncio
import csv
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from signalsdr.analyzer import analyze_text
from signalsdr.config import MAX_PROSPECT_SIGNALS_PER_COMPANY, SCRAPE_DELAY_SECONDS
from signalsdr.drafter import PROSPECT_SYSTEM_PROMPT, generate_draft
from signalsdr.output import append_to_csv, append_to_markdown, send_email_report, send_slack_notification
from signalsdr.prospector import prospect_company, scrape_news_page
from signalsdr.scraper import fetch_page
from signalsdr.state import record_scan, should_scan


def load_targets(csv_path: str | Path) -> list[dict]:
    """Load target companies from CSV file."""
    targets = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            target = {
                "company": row["company"].strip(),
                "domain": row["domain"].strip(),
                "careers_url": row["careers_url"].strip(),
            }
            # Optional news/blog URL for direct scraping
            news_url = row.get("news_url", "").strip()
            if news_url:
                target["news_url"] = news_url
            targets.append(target)
    return targets


async def run_hiring_pipeline(
    targets: list[dict],
    db: Path,
    output_path: str,
    model: str,
    dry_run: bool,
) -> dict:
    """Run the hiring signal pipeline (scrape careers pages + analyze)."""
    stats = {"scanned": 0, "skipped": 0, "signals": 0, "drafts": 0, "filtered": 0, "errors": 0}

    print(f"\n=== Hiring Pipeline: {len(targets)} targets ===\n")

    for i, target in enumerate(targets):
        company = target["company"]
        domain = target["domain"]
        url = target["careers_url"]

        if not url:
            print(f"[{i+1}/{len(targets)}] SKIP {company} (no careers_url)")
            stats["skipped"] += 1
            continue

        if not should_scan(domain, db, scan_type="hiring"):
            print(f"[{i+1}/{len(targets)}] SKIP {company} (scanned within 24h)")
            stats["skipped"] += 1
            continue

        print(f"[{i+1}/{len(targets)}] SCAN {company} ({url})")
        result = fetch_page(url)

        if not result.success:
            print(f"  ERROR: {result.error}")
            stats["errors"] += 1
            if not dry_run:
                record_scan(domain, company, [], db, scan_type="hiring")
            continue

        stats["scanned"] += 1
        print(f"  Fetched {len(result.text)} chars from '{result.title}'")

        analysis = analyze_text(result.text, url, company)

        if not analysis.has_signals:
            print("  No signals found")
            if not dry_run:
                record_scan(domain, company, [], db, scan_type="hiring")
        else:
            print(f"  {len(analysis.signals)} signal(s) detected:")
            seen_keywords = set()
            unique_signals = []
            for s in analysis.signals:
                if s.keyword not in seen_keywords:
                    seen_keywords.add(s.keyword)
                    unique_signals.append(s)
                    print(f"    [{s.keyword}] {s.matched_text[:80]}")

            stats["signals"] += len(unique_signals)

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
                        append_to_csv(draft, url, output_path)
                        append_to_markdown(draft, url)
                        send_slack_notification(draft)
                    elif draft.success and not draft.is_valid:
                        print(f"    Filtered by LLM (not a real job listing): {signal.keyword}")
                        stats["filtered"] += 1
                    else:
                        print(f"    Draft failed: {draft.error}")
                        stats["errors"] += 1

            if not dry_run:
                signal_dicts = [
                    {"keyword": s.keyword, "matched_text": s.matched_text}
                    for s in unique_signals
                ]
                record_scan(domain, company, signal_dicts, db, scan_type="hiring")

        if i < len(targets) - 1:
            time.sleep(SCRAPE_DELAY_SECONDS)

    return stats


async def run_prospect_pipeline(
    targets: list[dict],
    db: Path,
    output_path: str,
    model: str,
    dry_run: bool,
) -> dict:
    """Run the prospect intelligence pipeline (Brave Search + news page scraping)."""
    stats = {"scanned": 0, "skipped": 0, "signals": 0, "drafts": 0, "filtered": 0, "errors": 0}
    has_brave = bool(os.environ.get("BRAVE_API_KEY"))

    print(f"\n=== Prospect Pipeline: {len(targets)} targets ===")
    print(f"  Sources: {'Brave Search + ' if has_brave else ''}News page scraping\n")

    for i, target in enumerate(targets):
        company = target["company"]
        domain = target["domain"]
        news_url = target.get("news_url")

        if not should_scan(domain, db, scan_type="prospect"):
            print(f"[{i+1}/{len(targets)}] SKIP {company} (prospect-scanned within 24h)")
            stats["skipped"] += 1
            continue

        print(f"[{i+1}/{len(targets)}] PROSPECT {company} ({domain})")

        # Collect signals from all sources
        all_signals = []

        # Source 1: Brave Search (if API key available)
        if has_brave:
            brave_result = prospect_company(company, domain)
            if brave_result.success:
                all_signals.extend(brave_result.signals)
                print(f"  Brave Search: {len(brave_result.signals)} result(s)")
            else:
                print(f"  Brave Search error: {brave_result.error}")

        # Source 2: News page scraping (if news_url configured)
        if news_url:
            news_result = scrape_news_page(company, domain, news_url)
            if news_result.success:
                all_signals.extend(news_result.signals)
                print(f"  News page: {len(news_result.signals)} signal(s) from {news_url}")
            else:
                print(f"  News page error: {news_result.error}")

        if not has_brave and not news_url:
            print("  No sources available (no BRAVE_API_KEY and no news_url)")
            stats["errors"] += 1
            if not dry_run:
                record_scan(domain, company, [], db, scan_type="prospect")
            continue

        stats["scanned"] += 1

        if not all_signals:
            print("  No prospect signals found")
            if not dry_run:
                record_scan(domain, company, [], db, scan_type="prospect")
        else:
            # Deduplicate by headline
            seen = set()
            deduped = []
            for s in all_signals:
                if s.headline not in seen:
                    seen.add(s.headline)
                    deduped.append(s)

            # Cap signals per company with category diversity:
            # take first signal from each category, then fill remaining slots
            if len(deduped) > MAX_PROSPECT_SIGNALS_PER_COMPANY:
                seen_cats: set[str] = set()
                diverse: list = []
                remaining: list = []
                for s in deduped:
                    if s.category not in seen_cats:
                        seen_cats.add(s.category)
                        diverse.append(s)
                    else:
                        remaining.append(s)
                unique = (diverse + remaining)[:MAX_PROSPECT_SIGNALS_PER_COMPANY]
                print(f"  {len(deduped)} signals found, capped to {len(unique)} (category-diverse):")
            else:
                unique = deduped
                print(f"  {len(unique)} unique prospect signal(s):")

            for s in unique:
                print(f"    [{s.category}] {s.headline[:80]}")

            stats["signals"] += len(unique)

            if not dry_run:
                for signal in unique:
                    prompt = PROSPECT_SYSTEM_PROMPT.format(
                        category=signal.category,
                        role=f"{signal.headline}: {signal.snippet[:150]}",
                        company=company,
                    )

                    draft = await generate_draft(
                        company=company,
                        role=signal.headline[:100],
                        model=model,
                        system_prompt=prompt,
                        signal_type=f"prospect_{signal.category}",
                    )

                    if draft.is_valid:
                        print(f"    Draft: \"{draft.subject_line}\"")
                        stats["drafts"] += 1
                        append_to_csv(draft, signal.source_url, output_path)
                        append_to_markdown(draft, signal.source_url)
                        send_slack_notification(draft)
                    elif draft.success and not draft.is_valid:
                        print(f"    Filtered by LLM (irrelevant): {signal.headline[:60]}")
                        stats["filtered"] += 1
                    else:
                        print(f"    Draft failed: {draft.error}")
                        stats["errors"] += 1

            if not dry_run:
                signal_dicts = [
                    {"category": s.category, "headline": s.headline, "snippet": s.snippet}
                    for s in unique
                ]
                record_scan(domain, company, signal_dicts, db, scan_type="prospect")

        if i < len(targets) - 1:
            time.sleep(SCRAPE_DELAY_SECONDS)

    return stats


async def run_pipeline(
    targets_path: str = "targets.csv",
    output_path: str = "drafts_output.csv",
    db_path: str = "data/db.json",
    model: str = "openai/gpt-4o",
    dry_run: bool = False,
    send_email: bool = True,
    run_hiring: bool = True,
    run_prospect: bool = True,
) -> dict:
    """
    Run the full SignalSDR pipeline (hiring + prospect).

    Returns a combined summary dict.
    """
    targets = load_targets(targets_path)
    db = Path(db_path)

    # Reset markdown output so each run's email only contains fresh drafts
    md_path = Path("drafts_output.md")
    if md_path.exists():
        md_path.unlink()

    print(f"SignalSDR: Processing {len(targets)} targets")
    print(f"  Model: {model}")
    print(f"  Output: {output_path}")
    print(f"  Dry run: {dry_run}")
    print(f"  Hiring: {'yes' if run_hiring else 'skip'}")
    print(f"  Prospect: {'yes' if run_prospect else 'skip'}")

    combined = {
        "scanned": 0, "skipped": 0, "signals": 0, "drafts": 0,
        "filtered": 0, "errors": 0,
        "prospect_scanned": 0, "prospect_skipped": 0,
        "prospect_signals": 0, "prospect_drafts": 0,
        "prospect_filtered": 0, "prospect_errors": 0,
    }

    # --- Hiring pipeline ---
    if run_hiring:
        h = await run_hiring_pipeline(targets, db, output_path, model, dry_run)
        combined["scanned"] = h["scanned"]
        combined["skipped"] = h["skipped"]
        combined["signals"] = h["signals"]
        combined["drafts"] = h["drafts"]
        combined["filtered"] = h["filtered"]
        combined["errors"] = h["errors"]

    # --- Prospect pipeline ---
    if run_prospect:
        # Runs with Brave Search, news page scraping, or both
        has_brave = bool(os.environ.get("BRAVE_API_KEY"))
        has_news_urls = any(t.get("news_url") for t in targets)
        if not has_brave and not has_news_urls:
            print("\n  Prospect pipeline skipped (no BRAVE_API_KEY and no news_url in targets)")
        else:
            p = await run_prospect_pipeline(targets, db, output_path, model, dry_run)
            combined["prospect_scanned"] = p["scanned"]
            combined["prospect_skipped"] = p["skipped"]
            combined["prospect_signals"] = p["signals"]
            combined["prospect_drafts"] = p["drafts"]
            combined["prospect_filtered"] = p["filtered"]
            combined["prospect_errors"] = p["errors"]

    # --- Summary ---
    print()
    print("--- SignalSDR Run Complete ---")
    if run_hiring:
        print(f"  [Hiring]   Scanned: {combined['scanned']}  Skipped: {combined['skipped']}  "
              f"Signals: {combined['signals']}  Drafts: {combined['drafts']}  "
              f"Filtered: {combined['filtered']}  Errors: {combined['errors']}")
    if run_prospect and combined["prospect_scanned"] > 0:
        print(f"  [Prospect] Scanned: {combined['prospect_scanned']}  Skipped: {combined['prospect_skipped']}  "
              f"Signals: {combined['prospect_signals']}  Drafts: {combined['prospect_drafts']}  "
              f"Filtered: {combined['prospect_filtered']}  Errors: {combined['prospect_errors']}")

    # --- Email report ---
    if send_email and not dry_run:
        if send_email_report(combined):
            print("  Email report sent")
        else:
            import os
            if not os.environ.get("GMAIL_ADDRESS") or not os.environ.get("GMAIL_APP_PASSWORD"):
                print("  Email report skipped (GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set)")
            else:
                print("  Email report skipped (no new drafts to report)")

    return combined


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="SignalSDR: Hiring & Prospect Signal Detection Agent")
    parser.add_argument("--targets", default="targets.csv", help="Path to targets CSV")
    parser.add_argument("--output", default="drafts_output.csv", help="Path to output CSV")
    parser.add_argument("--db", default="data/db.json", help="Path to state database")
    parser.add_argument("--model", default="openai/gpt-4o", help="LLM model (litellm format)")
    parser.add_argument("--dry-run", action="store_true", help="Scan only, skip LLM drafting")
    parser.add_argument("--no-email", action="store_true", help="Skip email report after run")
    parser.add_argument("--prospect-only", action="store_true", help="Run prospect pipeline only (skip hiring)")
    parser.add_argument("--no-prospect", action="store_true", help="Skip prospect pipeline")
    args = parser.parse_args()

    run_hiring = not args.prospect_only
    run_prospect = not args.no_prospect

    asyncio.run(run_pipeline(
        targets_path=args.targets,
        output_path=args.output,
        db_path=args.db,
        model=args.model,
        dry_run=args.dry_run,
        send_email=not args.no_email,
        run_hiring=run_hiring,
        run_prospect=run_prospect,
    ))


if __name__ == "__main__":
    main()
