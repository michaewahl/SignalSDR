SignalSDR: Headless MVP Specification
1. Project Overview
Name: SignalSDR (MVP) Type: Headless Automation / Sidecar Agent Goal: Automate the detection of "Hiring Signals" on target company websites and generate personalized cold email drafts for SDRs. Philosophy: Adaptable Systems. The agent only acts when a specific event (hiring) changes the state of the prospect.

2. Architecture: The "Time-Event-State-Loop"
We are building a headless loop that runs a specific workflow.

Time: The script is triggered manually (CLI) or via a simple Cron (e.g., daily).

Event (Trigger): A "Hiring Signal" is detected (e.g., keywords "Head of Sales", "VP Engineering" found on a careers page).

State (Memory): A local JSON file (db.json) or Google Sheet that tracks which companies have been scanned and what signals were found.

Loop (Action):

Read target list.

Scrape/Scan for signal.

If signal == True, generate Email Draft via LLM.

Save Draft to Output (Slack/CSV).

3. Tech Stack & Tools
Language: Python 3.9+

Scraping: requests, BeautifulSoup4 (or ZenRows/Firecrawl if JS rendering is needed).

LLM: openai (GPT-4o) or google-generativeai (Gemini Pro).

Database (MVP): tinydb (local JSON) or pandas (CSV/Excel).

Notifications: slack_sdk (Webhooks) or simply append to CSV.

4. Data Structure (db.json Schema)
The agent needs a simple memory to avoid re-scanning the same company every hour.

JSON
{
  "companies": [
    {
      "id": "c_001",
      "name": "Acme Corp",
      "domain": "acme.com",
      "careers_url": "https://acme.com/careers",
      "last_scan": "2026-02-07T09:00:00Z",
      "status": "active",
      "signals": [
        {
          "date": "2026-02-07",
          "type": "hiring",
          "details": "Found role: Director of Security"
        }
      ]
    }
  ]
}
5. Core Features & Logic
Feature A: The Scanner (Event Detection)
Input: A list of target URLs (e.g., targets.csv).

Logic:

Fetch HTML content of careers_url.

Filter text for specific "high-value" keywords defined in a config list: ["VP", "Director", "Head of", "Security", "AI"].

Constraint: Ignore generic roles like "Intern" or "Associate".

Feature B: The Drafter (LLM Integration)
System Prompt:

"You are an expert SDR. Your goal is to write a short, 3-sentence cold email. Context: We sell AI Security software. Trigger: The company is hiring for [Role Found]. Task: Connect the hiring of this role to the value of securing their new AI initiatives. Tone: Professional, direct, no fluff."

Input: The detected role (e.g., "VP of AI").

Output: A JSON object containing { "subject_line": "...", "body": "..." }.

Feature C: The Output (Headless Reporting)
Action:

If a draft is generated, append a row to results.csv:

Company, Role Detected, Draft Subject, Draft Body, Status: PENDING_REVIEW

(Optional) Send a message to a Slack channel via Webhook:

"🚨 Signal Detected: Acme Corp is hiring a VP of AI. [Draft Created]"

6. Safety Guardrails (Crucial)
Read-Only Output: The agent never sends emails. It only writes to a CSV/Log.

Rate Limiting: Add a time.sleep(2) between scrapes to avoid IP bans.

Hallucination Check: The LLM prompt must include: "If no relevant role is found, return NULL. Do not invent a role."

7. MVP Implementation Steps (For the AI Assistant)
Setup: Create a virtual env and install requests, beautifulsoup4, openai, python-dotenv.

Config: Create a .env file for API keys.

Scraper: Write scraper.py to fetch a URL and return text.

Analyzer: Write analyzer.py to detect keywords in that text.

Generator: Write agent.py to send the detected signal to the LLM and get a draft.

Main Loop: Create main.py that iterates through targets.csv and runs the flow.

Output: Save valid results to drafts_output.csv.

Our Spec (SignalSDR)Nanobot ImplementationWhy this mattersTime (Events)Smart Daily Routine ManagerIt has built-in cron/schedule handling (schedule_tasks). You don't need to write the loop; you just define the schedule.State (Context)Personal Knowledge AssistantIt uses a lightweight local memory (likely RAG/JSON) to store user context, just like our db.json idea.Events (Triggers)Integrations (Discord/Slack)It listens for messages. For SignalSDR, we just swap "Discord Message" for "Hiring Signal."Loop (Action)Providers (OpenAI/DeepSeek)It abstracts the LLM call. You just plug in vllm or openai and it handles the prompt plumbing.

Since Nanobot already exists, we should fork it rather than writing scraper.py from scratch. It solves the "boring" parts of the infrastructure for us.

Instead of writing a new main.py, we can write a "Skill" for Nanobot.

How to build SignalSDR inside Nanobot:
1. The "Signal" becomes a Custom Tool Nanobot likely has a tools/ directory. We add hiring_scanner.py there.

Python
# tools/hiring_scanner.py
def check_careers_page(url: str):
    """Scrapes a URL for 'Head of Sales' roles."""
    # ... (Our BeautifulSoup logic from before) ...
    return found_roles
2. The "Routine" becomes a Config Nanobot uses a config file (probably config.json or YAML). We just tell it to run our tool every morning.

JSON
"scheduled_tasks": [
  {
    "time": "08:00",
    "prompt": "Run the 'check_careers_page' tool for all domains in 'targets.csv'. If you find a role, draft an email."
  }
]
3. The "State" is Free Nanobot already manages conversation history. If the agent drafted an email yesterday, it (theoretically) remembers it today, so we don't need to build a complex db.json from scratch.

3. The Security Upgrade (Crucial)
You noticed the "Security Nightmare" article earlier. Nanobot explicitly addresses this in its README:

Sandbox Mode: It mentions "restrictToWorkspace": true. This forces the agent to only read/write files in a specific folder.

Why this saves us: If our SignalSDR agent goes rogue (hallucinates), it can't delete your hard drive. It can only mess up files in its sandbox folder.