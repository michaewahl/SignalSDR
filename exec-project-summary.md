# SignalSDR — Executive Project Summary

## What I Did

Built **SignalSDR**, an automated sales intelligence agent that monitors 25 OEM target companies daily for two types of business signals:

1. **Hiring Signals** — Scrapes careers pages to detect when targets are hiring roles relevant to our services (technical writers, documentation managers, service information leads, etc.)
2. **Prospect Intelligence** — Uses Brave Search API to scan for business news across **five categories**: product launches, EV/electrification moves, regulatory/compliance events, service/technician challenges, and **AI/ML adoption** (new as of Feb 21, 2026).

For every signal detected, the agent generates a personalized cold outreach email draft via LLM (GPT-4o), tailored to connect the signal to our specific products and services. Drafts are written to CSV/Markdown for human review and emailed as a daily digest.

### Architecture Decision: Nanobot Framework

Forked [HKUDS/nanobot](https://github.com/HKUDS/nanobot), a lightweight AI agent framework (~4,000 lines of Python), as the foundation. Nanobot provides:

- **Agent loop** with tool registration and execution
- **Multi-provider LLM support** (OpenAI, Anthropic, local models)
- **Skill system** for injecting domain context into every agent interaction
- **Channel support** (CLI, API) for flexible deployment

This gave us a production-ready agent skeleton without building from scratch or taking on a heavy framework like LangChain.

### What We Built On Top

All custom business logic lives in the `signalsdr/` package:

| Module | Purpose |
|--------|---------|
| `scraper.py` | BeautifulSoup page fetcher for careers sites |
| `analyzer.py` | Keyword-based signal detection with word-boundary regex |
| `prospector.py` | Brave Search API integration + news page scraping |
| `drafter.py` | LLM email drafting via litellm (hiring + prospect prompts) |
| `output.py` | CSV/Markdown writer + Slack webhook + Gmail SMTP reports |
| `state.py` | JSON-based state management with independent 24h cooldowns |
| `config.py` | Keywords, exclusions, prospect categories, rate limits |

Plus two **nanobot tools** (`career_scanner.py`, `prospect_scanner.py`) and a **nanobot skill** (`SKILL.md`) that gives the agent full context about our company, products, and how to use both scanners conversationally.

**`main.py`** orchestrates the dual pipeline with CLI flags (`--prospect-only`, `--no-prospect`, `--dry-run`) and runs daily at 6am via macOS launchd.

---

## Why It Matters

### Before SignalSDR
- SDRs manually checked careers pages and Google News for each target — time-consuming, inconsistent, and easy to miss signals
- No systematic way to track which companies were scanned and when
- Cold outreach was generic, not tied to real-time business triggers

### After SignalSDR
- **25 companies monitored automatically every day** across hiring + 4 prospect signal categories
- **LLM-generated drafts** connect each signal to our specific products (documentation, parts catalogs, diagnostics, eLearning)
- **False-positive filtering** built into the LLM prompts — the model returns null for irrelevant results instead of hallucinating
- **Daily email digest** delivered to inbox with all new drafts for human review before sending
- **State tracking** prevents duplicate scans and respects API rate limits

### Key Numbers (Live Run — Feb 10, 2026)
- 14 careers pages scanned → 3 hiring signals → 2 valid drafts
- 25 companies prospect-scanned → 125 prospect signals → 123 valid drafts
- Full pipeline completes in ~10 minutes
- Brave Search: free tier, 2,000 queries/month (currently using ~125/run with 5 categories)

### Key Numbers (Live Run — Feb 21, 2026 — first run with ai_adoption category)
- New `ai_adoption` signals detected across: Smartcar (connected vehicle), Thermoking, Waymo (world model), Toyota (humanoid robots), Hyundai (industrial AI), Audi (AI in production logistics)
- Draft language shifted: "Scale AI Adoption Across [Company] with Tweddle Group" vs old "Enhance X with Tweddle Group's Expertise"

---

## What It Improves

### 1. Speed to Signal
Signals that would take an SDR hours to find manually are detected and drafted overnight. By 6am, actionable outreach drafts are in your inbox.

### 2. Signal Quality
Word-boundary keyword matching eliminates false positives (e.g., "AI" no longer matches "Français"). LLM filtering catches non-job content like diversity statements and footer text. Prospect signals are capped at 5 per company with category diversity to avoid noise.

### 3. Outreach Relevance
Every draft is tied to a specific, real-time trigger — a job posting, a product launch, a regulatory change. This is fundamentally different from batch cold email.

### 4. Operational Reliability
- **launchd** (not cron) ensures the daily run fires even if the Mac was asleep at 6am — missed jobs queue and run on wake
- **OneDrive isolation** — Python venv lives on local disk to avoid filesystem lock hangs from cloud sync
- **Independent cooldowns** — hiring and prospect scans track separate timestamps so one pipeline doesn't block the other
- **Dry-run mode** is fully side-effect-free (no state updates, no emails)

### 5. Extensibility
Adding a new signal category is a config change + search query template. The nanobot skill means the agent can also be used conversationally — ask it to scan a specific company or explain a signal in natural language.

---

## Updates — Feb 21, 2026

### 1. New Signal Category: `ai_adoption`
Added a fifth prospect category that detects when target companies are deploying AI, building software-defined vehicles, adding connected vehicle features, or pushing over-the-air updates. This is driven by the reality that every AI feature deployment requires service network training, technical content, and change management documentation — exactly what we provide.

**What it catches:** AI platform deployments, machine learning integration announcements, digital transformation initiatives, connected vehicle partnerships, generative AI feature launches.

**Example signals from first run:**
- Smartcar + Volvo Cars partner to unlock connected vehicle experiences
- Waymo publishes world model paper redefining autonomous driving
- Toyota exploring humanoid robot integration in production
- Hyundai makes bold bet on industrial AI robots
- Audi expands AI deployment in production and logistics

### 2. Upgraded Email Draft Prompts
Rewrote both the hiring and prospect email prompts to align with current B2B sales messaging best practices:

**Old approach:** Generic "we can enhance/support your [function]" framing.

**New approach:** Org-wide multiplier framing — we don't just help one team, we help the whole org execute at scale. Every draft now:
- Opens by connecting the signal to an organizational shift happening at the target
- Frames us as the partner that multiplies capability across the whole org, not just one team
- Ends with a direct ask tied to business impact (faster model launch, lower recall cost, org-wide compliance)
- Uses active verbs: build, deploy, scale, ship, create
- Bans vague phrases: "enhance," "streamline," "leverage"

**Signal-specific framing:**
- `ai_adoption` → "If you're deploying AI features, your service network needs to understand them before your customers do. We build the technical content and training that scales AI adoption across your org."
- `ev_transition` → "Electrification is a content rebuild from scratch. We build it out so your whole org can execute, not just pilot."
- `service_challenge` → "Don't just fill the gap — multiply your best techs across the network."

### 3. launchd Reliability Fix
Identified root cause of intermittent daily run failures: `source activate` in launchd's non-interactive bash shell can trigger a Python site-module deadlock (`OSError: [Errno 11] Resource deadlock avoided`). Fixed by replacing venv activation with a direct path to the venv's Python binary — simpler and more reliable.

**Before:** `source "$HOME/.signalsdr-venv/bin/activate" && python main.py`
**After:** `"$HOME/.signalsdr-venv/bin/python" main.py`

### 4. CSV Parser Hardening
Fixed a crash when targets.csv rows have missing columns (e.g., a row with only 3 of 4 expected columns). Python's `csv.DictReader` returns `None` (not an empty string) for missing columns, which causes `AttributeError` on `.strip()` calls. Fixed all field accesses to use `(row.get("field") or "").strip()`.

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.13 |
| Agent Framework | Nanobot (forked) |
| LLM | GPT-4o via litellm |
| Web Search | Brave Search API (free tier) |
| Web Scraping | BeautifulSoup + requests |
| Scheduling | macOS launchd (`StartCalendarInterval`) |
| State | JSON file (`data/db.json`) |
| Output | CSV + Markdown + Gmail SMTP + Slack webhook |
| Build | hatchling via pyproject.toml |

---

## MVP Status: Complete + Enhanced

All planned features are implemented and running in production:

- [x] Hiring signal scanner (scraper + analyzer)
- [x] Prospect intelligence (Brave Search + news scraping, 5 categories)
- [x] LLM email drafting (hiring + prospect prompts with org-multiplier framing)
- [x] Output to CSV/Markdown + Slack + Gmail
- [x] State management with independent cooldowns
- [x] Nanobot tools + skill for conversational use
- [x] 25 OEM targets configured
- [x] Daily automation via launchd (using direct venv Python path)
- [x] Dry-run mode for safe testing
- [x] Company identity externalized (company.json)
- [x] `ai_adoption` signal category (Feb 21, 2026)
- [x] Upgraded draft prompts with B2B org-multiplier framing (Feb 21, 2026)
- [x] launchd site-module deadlock fix (Feb 21, 2026)
- [x] CSV parser hardened for missing columns (Feb 21, 2026)
