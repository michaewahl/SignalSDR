from __future__ import annotations

"""
SignalSDR Drafter Module (Feature B from spec).

Takes a detected hiring signal and generates a personalized cold
email draft via LLM (litellm for multi-provider support).
This is the "brain" of the agent.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from litellm import acompletion


# ---------------------------------------------------------------------------
# Load company identity from company.json (gitignored).
# Falls back to Acme Corp defaults if the file is missing.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_COMPANY_JSON = _PROJECT_ROOT / "company.json"

_DEFAULT_COMPANY = {
    "name": "Acme Corp",
    "url": "www.acmecorp.com",
    "products": [
        "Technical documentation & service information (repair manuals, owner guides)",
        "Electronic parts catalogs & wiring diagrams",
        "Diagnostic tools & guided diagnostics",
        "Interactive training & eLearning for technicians",
        "Content management systems & service portals",
    ],
    "industries": "automotive, EV, heavy equipment, aerospace, defense, powersports, RVs",
}


def _load_company() -> dict:
    if _COMPANY_JSON.exists():
        with open(_COMPANY_JSON) as f:
            return json.load(f)
    return _DEFAULT_COMPANY


COMPANY = _load_company()
_CO = COMPANY["name"]
_URL = COMPANY["url"]
_PRODUCTS = "\n".join(f"- {p}" for p in COMPANY["products"])
_INDUSTRIES = COMPANY["industries"]


SYSTEM_PROMPT = f"""\
You are an expert SDR (Sales Development Representative) for {_CO} \
({_URL}), a leader in product information and technical documentation.

{_CO} helps OEMs and manufacturers build and deploy:
{_PRODUCTS}

Industries: {_INDUSTRIES}.

Trigger: {{company}} is hiring for {{role}}.
Task: Write a short 3-sentence cold email that:
1. Opens by connecting this specific hire to an organizational shift happening at {{company}}
2. Frames {_CO} as the partner that lets that capability scale across their whole org — not just support one team
3. Ends with a direct, low-friction ask tied to business impact (faster launch, lower recall cost, org-wide compliance)

Use active verbs: build, deploy, scale, ship, create. Avoid vague phrases like "enhance" or "streamline."
Tone: Confident, specific, no fluff.

CRITICAL RULE: Analyze the "Hiring Signal" text carefully.
If the text is NOT a real job listing — for example, it is a diversity statement, \
footer text, generic marketing copy, a "Board of Directors" page, a fraud warning, \
or any other non-hiring content — you MUST return: {{{{"subject_line": null, "body": null}}}}
Do not hallucinate a job opening. Do not invent a role.
Only draft an email when the signal clearly indicates an open position being hired for.

You MUST respond with valid JSON only, no markdown, no explanation:
{{{{"subject_line": "...", "body": "..."}}}}
"""

PROSPECT_SYSTEM_PROMPT = f"""\
You are an expert SDR (Sales Development Representative) for {_CO} \
({_URL}), a leader in product information and technical documentation.

{_CO} helps OEMs and manufacturers build and deploy:
{_PRODUCTS}

Industries: {_INDUSTRIES}.

Signal type: {{category}}
Trigger: {{role}}
Company: {{company}}

Task: Write a compelling 3-sentence outreach email that:
1. Opens by naming the specific signal and what it signals about {{company}}'s direction
2. Frames {_CO} as what multiplies that capability across their whole org — not a one-off engagement
3. Ends with a direct ask tied to business impact: faster launch, top-line growth, org-wide compliance, or reduced recall cost

Use active verbs: build, deploy, scale, ship, create. Frame value as org-wide, not individual productivity.
Signal framing by type:
- new_model → "Every new model needs docs, parts catalogs, and technician training built before day one — we deploy all three at OEM scale so your teams can ship."
- service_challenge → "Don't just fill the gap — multiply your best techs across the network. Our AI-assisted diagnostics and eLearning let your existing team do the work of a larger one."
- ev_transition → "Electrification is a content rebuild from scratch. New service docs, wiring diagrams, training curricula — we build it out so your whole org can execute, not just pilot."
- regulatory → "Compliance can't live in one team's inbox. We build the documentation infrastructure that gets your entire org audit-ready as standards evolve."
- ai_adoption → "If you're deploying AI features, your service network needs to understand them before your customers do. We build the technical content and training that scales AI adoption across your org."

Tone: Confident, specific, reference the exact signal. No generic phrases like "enhance" or "streamline."

CRITICAL RULE: Analyze the signal carefully.
If the headline/snippet is clearly irrelevant (unrelated company, spam, \
generic news aggregation) — return: {{{{"subject_line": null, "body": null}}}}
Only draft when the signal is genuinely about {{company}}.

You MUST respond with valid JSON only, no markdown, no explanation:
{{{{"subject_line": "...", "body": "..."}}}}
"""


@dataclass
class EmailDraft:
    """A generated email draft."""

    company: str
    role: str
    subject_line: str | None
    body: str | None
    model: str
    success: bool
    error: str = ""
    signal_type: str = "hiring"

    @property
    def is_valid(self) -> bool:
        return self.success and self.subject_line is not None and self.body is not None


async def generate_draft(
    company: str,
    role: str,
    model: str = "openai/gpt-4o",
    temperature: float = 0.7,
    api_key: str | None = None,
    system_prompt: str | None = None,
    signal_type: str = "hiring",
) -> EmailDraft:
    """
    Generate a cold email draft for a detected signal.

    Uses litellm to call whichever LLM provider is configured.
    The system prompt constrains the LLM to output JSON with
    subject_line and body fields.

    Args:
        company: The company name (e.g. "Acme Corp").
        role: The detected role or signal headline.
        model: litellm model string (e.g. "openai/gpt-4o", "anthropic/claude-sonnet-4-5").
        temperature: LLM sampling temperature.
        api_key: Optional API key override (otherwise uses env vars).
        system_prompt: Custom system prompt (uses SYSTEM_PROMPT if None).
        signal_type: "hiring" or "prospect" — stored on the draft.

    Returns:
        EmailDraft with the generated subject line and body.
    """
    if system_prompt:
        system_msg = system_prompt
    else:
        system_msg = SYSTEM_PROMPT.format(company=company, role=role)

    user_msg = (
        f"Company: {company}\n"
        f"Detected Role: {role}\n\n"
        f"Write the cold email draft as JSON."
    )

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 512,
        "temperature": temperature,
    }
    if api_key:
        kwargs["api_key"] = api_key

    try:
        response = await acompletion(**kwargs)
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if the LLM wraps its JSON
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        draft_data = json.loads(raw)

        return EmailDraft(
            company=company,
            role=role,
            subject_line=draft_data.get("subject_line"),
            body=draft_data.get("body"),
            model=model,
            success=True,
            signal_type=signal_type,
        )

    except json.JSONDecodeError as e:
        return EmailDraft(
            company=company,
            role=role,
            subject_line=None,
            body=None,
            model=model,
            success=False,
            error=f"LLM returned invalid JSON: {e}",
            signal_type=signal_type,
        )
    except Exception as e:
        return EmailDraft(
            company=company,
            role=role,
            subject_line=None,
            body=None,
            model=model,
            success=False,
            error=str(e),
            signal_type=signal_type,
        )
