"""
SignalSDR State Management.

Tracks which companies have been scanned and what signals
were found, using a local db.json file. Prevents re-scanning
the same company within a configurable cooldown window.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DB_PATH = Path("data/db.json")
RESCAN_COOLDOWN_HOURS = 24


def _load_db(db_path: Path) -> dict:
    """Load the state database from disk."""
    if not db_path.exists():
        return {"companies": []}
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_db(db: dict, db_path: Path) -> None:
    """Write the state database to disk."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def should_scan(
    domain: str,
    db_path: Path = DEFAULT_DB_PATH,
    scan_type: str = "hiring",
) -> bool:
    """
    Check if a company should be scanned based on cooldown.

    Returns True if the company hasn't been scanned, or if
    the last scan was more than RESCAN_COOLDOWN_HOURS ago.

    Args:
        domain: Company domain (unique key).
        db_path: Path to db.json.
        scan_type: "hiring" or "prospect" — tracked independently.
    """
    db = _load_db(db_path)
    ts_key = "last_scan" if scan_type == "hiring" else "last_prospect_scan"

    for company in db["companies"]:
        if company.get("domain") == domain:
            last_scan = company.get(ts_key)
            if not last_scan:
                return True
            last_dt = datetime.fromisoformat(last_scan)
            now = datetime.now(timezone.utc)
            hours_since = (now - last_dt).total_seconds() / 3600
            return hours_since >= RESCAN_COOLDOWN_HOURS

    return True


def record_scan(
    domain: str,
    company_name: str,
    signals: list[dict],
    db_path: Path = DEFAULT_DB_PATH,
    scan_type: str = "hiring",
) -> None:
    """
    Record a completed scan in the state database.

    Updates existing entry or creates a new one.

    Args:
        domain: Company domain (unique key).
        company_name: Human-readable company name.
        signals: List of signal dicts (keyword, matched_text).
        db_path: Path to db.json.
        scan_type: "hiring" or "prospect" — stored separately.
    """
    db = _load_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    ts_key = "last_scan" if scan_type == "hiring" else "last_prospect_scan"

    # Find existing entry or create new
    existing = None
    for company in db["companies"]:
        if company.get("domain") == domain:
            existing = company
            break

    if scan_type == "prospect":
        signal_records = [
            {
                "date": now[:10],
                "type": f"prospect_{s.get('category', 'unknown')}",
                "details": s.get("headline", s.get("snippet", "unknown")),
            }
            for s in signals
        ]
    else:
        signal_records = [
            {
                "date": now[:10],
                "type": "hiring",
                "details": f"Found role: {s.get('matched_text', s.get('keyword', 'unknown'))}",
            }
            for s in signals
        ]

    if existing:
        existing[ts_key] = now
        existing["status"] = "signal_found" if signals else "no_signal"
        if signals:
            existing.setdefault("signals", []).extend(signal_records)
    else:
        entry = {
            "id": f"c_{len(db['companies']) + 1:03d}",
            "name": company_name,
            "domain": domain,
            ts_key: now,
            "status": "signal_found" if signals else "no_signal",
            "signals": signal_records,
        }
        db["companies"].append(entry)

    _save_db(db, db_path)
