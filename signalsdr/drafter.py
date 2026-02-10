from __future__ import annotations

"""
SignalSDR Drafter Module (Feature B from spec).

Takes a detected hiring signal and generates a personalized cold
email draft via LLM (litellm for multi-provider support).
This is the "brain" of the agent.
"""

import json
from dataclasses import dataclass

from litellm import acompletion


SYSTEM_PROMPT = """\
You are an expert SDR (Sales Development Representative) for Acme Corp \
(www.acmecorp.com), a leader in product information and technical documentation.

Acme Corp helps OEMs and manufacturers with:
- Technical documentation & service information (repair manuals, owner guides)
- Electronic parts catalogs & wiring diagrams
- Diagnostic tools & guided diagnostics
- Interactive training & eLearning for technicians
- Content management systems & service portals

Industries: automotive, EV, heavy equipment, aerospace, defense, powersports, RVs.

Trigger: {company} is hiring for {role}.
Task: Write a short 3-sentence cold email connecting this hire to how Acme Corp \
can support their documentation, service, or training needs. Be specific to the role.
Tone: Professional, direct, no fluff.

CRITICAL RULE: Analyze the "Hiring Signal" text carefully.
If the text is NOT a real job listing — for example, it is a diversity statement, \
footer text, generic marketing copy, a "Board of Directors" page, a fraud warning, \
or any other non-hiring content — you MUST return: {{"subject_line": null, "body": null}}
Do not hallucinate a job opening. Do not invent a role.
Only draft an email when the signal clearly indicates an open position being hired for.

You MUST respond with valid JSON only, no markdown, no explanation:
{{"subject_line": "...", "body": "..."}}
"""

PROSPECT_SYSTEM_PROMPT = """\
You are an expert SDR (Sales Development Representative) for Acme Corp \
(www.acmecorp.com), a leader in product information and technical documentation.

Acme Corp helps OEMs and manufacturers with:
- Technical documentation & service information (repair manuals, owner guides)
- Electronic parts catalogs & wiring diagrams
- Diagnostic tools & guided diagnostics
- Interactive training & eLearning for technicians
- Content management systems & service portals

Industries: automotive, EV, heavy equipment, aerospace, defense, powersports, RVs.

Signal type: {category}
Trigger: {role}
Company: {company}

Task: Write a compelling 3-sentence outreach email that connects this business signal \
to how Acme Corp can help. For example:
- New model/product launch → "Every new model needs documentation, parts catalogs, \
and technician training — Acme Corp delivers all three."
- Service/technician challenges → "With the technician shortage growing, our diagnostic \
tools and eLearning platforms help your existing team do more."
- EV transition → "Electrification means entirely new service documentation, wiring \
diagrams, and training curricula — we specialize in exactly that."
- Regulatory/compliance → "New safety and emissions standards require updated \
documentation across your entire fleet — we can get you compliant fast."

Tone: Professional, direct, reference the specific signal. No fluff.

CRITICAL RULE: Analyze the signal carefully.
If the headline/snippet is clearly irrelevant (unrelated company, spam, \
generic news aggregation) — return: {{"subject_line": null, "body": null}}
Only draft when the signal is genuinely about {company}.

You MUST respond with valid JSON only, no markdown, no explanation:
{{"subject_line": "...", "body": "..."}}
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
