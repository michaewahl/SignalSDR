# SignalSDR: Full Specification

## 1. Project Overview

**Name:** SignalSDR
**Type:** Headless Automation / Sidecar Agent
**Owner:** Configurable (see `signalsdr/drafter.py` and `nanobot/skills/signalsdr/SKILL.md`)
**Goal:** Automate the detection of business signals (hiring, new models, EV transitions, service challenges, regulatory changes) on target OEM/manufacturer websites and generate personalized cold email drafts for BD/sales teams.

**Philosophy:** Adaptable Systems. The agent only acts when a specific event changes the state of a prospect.

**What your company sells (example: Acme Corp):**
- Technical documentation & service information (repair manuals, owner guides)
- Electronic parts catalogs & wiring diagrams
- Diagnostic tools & guided diagnostics
- Interactive training & eLearning for technicians
- Content management systems & service portals

**Industries (example):** Automotive, EV, heavy equipment, aerospace, defense, powersports, RVs.

## 2. Architecture: The "Time-Event-State-Loop"

**Time:** Triggered via CLI (`python main.py`) or daily cron (`run_daily.sh`).

**Event (Triggers):**
- **Hiring Signal:** High-value keywords detected on a company's careers page (VP, Director, Head of, CISO, CTO, AI, etc.)
- **Prospect Signal:** Business opportunity detected via web search or news page scraping (new model launch, EV transition, service challenge, regulatory change)

**State (Memory):** `data/db.json` tracks per-company scan history with independent 24h cooldowns for hiring and prospect scans.

**Loop (Action):**
1. Read target list from `targets.csv`
2. Check state (skip recently scanned companies)
3. **Hiring pipeline:** Scrape careers pages, analyze for hiring keywords
4. **Prospect pipeline:** Search Brave API + scrape company newsrooms for business signals
5. Generate email drafts via LLM (with false-positive filtering)
6. Save drafts to CSV + markdown, send Slack notifications
7. Email daily report via Gmail
8. Update state in `db.json`

## 3. Tech Stack

- **Language:** Python 3.13 (requires >=3.11), venv at `.venv/`
- **Build:** hatchling via `pyproject.toml`, installed editable
- **Scraping:** `requests`, `BeautifulSoup4`
- **Web Search:** Brave Search API (optional, for prospect intelligence)
- **LLM:** `litellm` (multi-provider: OpenAI, Anthropic, Gemini, etc.)
- **State:** Local JSON (`data/db.json`)
- **Notifications:** Slack webhooks (optional), Gmail SMTP (optional)
- **Agent Framework:** Forked from HKUDS/nanobot (~4k lines)

## 4. Project Structure

```
SignalSDR/
├── main.py                          # CLI orchestration (hiring + prospect pipelines)
├── company.json                     # Your company identity — gitignored (copy company.example.json)
├── company.example.json             # Acme Corp placeholder (committed)
├── targets.csv                      # Target companies — gitignored (copy targets.example.csv)
├── targets.example.csv              # Example targets file (committed)
├── run_daily.sh                     # Cron wrapper script
├── data/
│   ├── db.json                      # State tracking — gitignored (copy db.example.json)
│   └── db.example.json              # Empty state template (committed)
├── drafts_output.csv                # Output: email drafts for review (gitignored)
├── drafts_output.md                 # Output: readable markdown (gitignored)
├── signalsdr/                       # Business logic package
│   ├── config.py                    # Keywords, categories, rate limits
│   ├── scraper.py                   # BeautifulSoup page fetcher
│   ├── analyzer.py                  # Keyword signal detection (hiring)
│   ├── prospector.py                # Brave Search + news page scraping (prospect)
│   ├── drafter.py                   # LLM email drafter (loads company.json)
│   ├── output.py                    # CSV/markdown writer, Slack, Gmail
│   └── state.py                     # db.json state management (24h cooldown)
├── nanobot/                         # Forked nanobot framework
│   ├── agent/
│   │   ├── loop.py                  # Agent loop (registers tools)
│   │   └── tools/
│   │       ├── career_scanner.py    # Nanobot tool: hiring signal scanner
│   │       └── prospect_scanner.py  # Nanobot tool: prospect signal scanner
│   └── skills/
│       └── signalsdr/
│           ├── SKILL.md             # Nanobot skill — gitignored (copy SKILL.example.md)
│           └── SKILL.example.md     # Acme Corp placeholder skill (committed)
├── .env                             # API keys (gitignored, copy .env.example)
└── .env.example                     # Placeholder API keys (committed)
```

## 5. Data Structures

### targets.csv
```csv
company,domain,careers_url,news_url
Ford,ford.com,https://ford.com/careers/,https://media.ford.com/
Toyota,toyota.com,https://toyota.com/careers/,https://pressroom.toyota.com/
```

### db.json
```json
{
  "companies": [
    {
      "id": "c_001",
      "name": "Ford",
      "domain": "ford.com",
      "last_scan": "2026-02-09T20:00:00+00:00",
      "last_prospect_scan": "2026-02-09T20:05:00+00:00",
      "status": "signal_found",
      "signals": [
        {"date": "2026-02-09", "type": "hiring", "details": "Found role: VP of Engineering"},
        {"date": "2026-02-09", "type": "prospect_ev_transition", "details": "Ford announces new EV platform"}
      ]
    }
  ]
}
```

## 6. Feature Details

### Feature A: Hiring Scanner
- **Input:** `careers_url` from targets.csv
- **Logic:** Fetch HTML via `requests` + `BeautifulSoup`, extract text, match against `SIGNAL_KEYWORDS` (VP, Director, Head of, CISO, CTO, AI, etc.) using word-boundary regex to avoid false positives, filter out `EXCLUDE_KEYWORDS` (Intern, Associate, Junior, Social Security)
- **Output:** List of `Signal` objects with keyword + matched text

### Feature B: Prospect Intelligence
Two signal sources:
1. **Brave Search API** (if `BRAVE_API_KEY` set): Queries 4 categories per company with freshness filter (past week)
2. **News page scraping** (if `news_url` configured): Fetches company blog/newsroom, matches against `NEWS_PAGE_KEYWORDS` mapped to categories. Quality filters skip tag lists, WLTP/emissions disclaimers, and generic site chrome.

**Prospect categories (configurable in `signalsdr/config.py`):**
- `new_model` — new vehicle/product/equipment launches
- `service_challenge` — technician shortages, recalls, warranty, parts supply
- `ev_transition` — electrification, battery, hybrid transitions
- `regulatory` — safety standards, emissions, right-to-repair
- `ai_adoption` — AI/ML deployment, software-defined vehicles, connected vehicle, over-the-air updates, digital transformation

**Signal cap:** Max 5 signals per company (`MAX_PROSPECT_SIGNALS_PER_COMPANY`). When a company has more signals (e.g., a large newsroom archive), the pipeline prioritizes category diversity — taking the first signal from each category before filling remaining slots.

### Feature C: LLM Email Drafter
- **Provider:** `litellm` (supports OpenAI, Anthropic, Gemini via `--model` flag)
- **Hiring prompt:** Frames each hire as an organizational shift. Pitches your company as the partner that lets the new capability scale across the whole org — not just support one team. Requires active verbs (build, deploy, scale, ship, create). Bans vague phrases like "enhance" or "streamline."
- **Prospect prompt:** Signal-specific framing per category — new models need documentation + parts catalogs built before day one; service challenges call for multiplying existing technicians with AI-assisted diagnostics; AI adoption signals prompt content + training that scales AI rollout org-wide. All pitches anchor to top-line business impact.
- **False-positive filter:** LLM returns `{subject_line: null, body: null}` for irrelevant signals (diversity statements, tag lines, spam)

### Feature D: Output & Reporting
- `drafts_output.csv` — structured output with signal_type, company, role, draft, status
- `drafts_output.md` — readable markdown with category badges (reset per run)
- Slack webhook notifications (optional)
- Gmail email report after each run with emoji subject line and draft/signal counts

## 7. CLI Usage

```bash
python main.py                          # Run hiring + prospect
python main.py --prospect-only          # Prospect pipeline only
python main.py --no-prospect            # Hiring pipeline only
python main.py --dry-run                # Scan only, no LLM drafts
python main.py --model anthropic/claude-sonnet-4-5  # Use Claude
python main.py --no-email               # Skip email report
python main.py --targets custom.csv     # Custom target file
```

## 8. Environment Variables (.env)

```
OPENAI_API_KEY=sk-...              # Required: LLM provider
BRAVE_API_KEY=...                  # Optional: prospect web search
SLACK_WEBHOOK_URL=...              # Optional: Slack notifications
GMAIL_ADDRESS=you@gmail.com        # Optional: email reports
GMAIL_APP_PASSWORD=xxxx xxxx xxxx  # Optional: Gmail App Password
GMAIL_RECIPIENT=team@company.com   # Optional: defaults to GMAIL_ADDRESS
```

## 9. Safety Guardrails

- **Read-only output:** The agent never sends outreach emails. It only writes drafts for human review.
- **Rate limiting:** `time.sleep(2)` between scrapes to avoid IP bans. Brave Search queries are spaced 1.1s apart to stay within the free tier rate limit (~1 req/sec).
- **24h cooldown:** Independent per-company cooldowns for hiring and prospect scans prevent redundant scanning.
- **Dry-run isolation:** `--dry-run` mode scans pages and detects signals but does not call the LLM or update state in `db.json`, so cooldowns are not consumed.
- **Word-boundary matching:** Hiring keyword regex uses `\b` word boundaries to prevent false positives (e.g., "AI" matching inside "Français" or "paid").
- **Signal cap:** Prospect pipeline limits to 5 signals per company with category-diverse selection, preventing runaway LLM costs from large newsroom archives.
- **Newsroom quality filters:** Skips comma-separated tag lists (e.g., "Electrification,Sustainability"), WLTP/emissions disclaimers (kWh/100km, g/km, CO2), generic site chrome (cookie banners, privacy policies), and lines under 25 characters.
- **LLM hallucination check:** Prompts include explicit instructions to return null for non-genuine signals.
- **Sandbox mode:** Nanobot's `restrictToWorkspace: true` limits file access to the project directory.
- **No secrets in git:** `.env` is gitignored; `.env.example` has placeholder values only.

## 10. Nanobot Integration

### Tools
- `career_scanner(url, company)` — wraps scraper + analyzer for interactive use
- `prospect_scanner(company, domain, categories?)` — wraps Brave Search + news scraping

### Skill (SKILL.md)
- `always: true` — loaded into every agent context
- Documents both tools with examples and workflow instructions
- Includes company context and email drafting rules
- Workflow: Signal Detection → Context Gathering (Deep Dive) → Drafting → Summary

## 11. Daily Automation (macOS launchd)

SignalSDR runs daily at 6am via **launchd** (not cron). launchd is preferred over cron on macOS because it retries missed jobs after sleep/wake.

**LaunchAgent plist** at `~/Library/LaunchAgents/com.signalsdr.daily.plist`:

```xml
<key>ProgramArguments</key>
<array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>cd "$HOME/.../SignalSDR" &amp;&amp; sleep 5 &amp;&amp; echo "=== SignalSDR run: $(date) ===" >> data/signalsdr.log &amp;&amp; "$HOME/.signalsdr-venv/bin/python" main.py >> data/signalsdr.log 2&gt;&amp;1</string>
</array>
```

**Key design decisions:**
- Uses `~/.signalsdr-venv/bin/python` directly — avoids `source activate` which can cause Python site-module deadlocks in launchd's non-interactive shell
- Logs to `data/signalsdr.log` (within project) + `/tmp/signalsdr-launchd.log` (launchd stdout/stderr)
- `sleep 5` lets OneDrive sync finish before scanning starts
- `StartCalendarInterval` fires at 6:00am; missed runs execute on next wake

**Install/reinstall:**
```bash
launchctl unload ~/Library/LaunchAgents/com.signalsdr.daily.plist
launchctl load ~/Library/LaunchAgents/com.signalsdr.daily.plist
launchctl list | grep signalsdr  # exit code should be 0
```

**Important:** The Python venv must be on local disk (not OneDrive) to avoid filesystem lock hangs. Default location: `~/.signalsdr-venv`. Symlink into project: `ln -s ~/.signalsdr-venv .venv`.
