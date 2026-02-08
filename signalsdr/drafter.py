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
You are an expert SDR (Sales Development Representative).
Your goal is to write a short, 3-sentence cold email.

Context: We sell AI Security software.
Trigger: The company is hiring for {role} at {company}.
Task: Connect the hiring of this role to the value of securing their new AI initiatives.
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

    @property
    def is_valid(self) -> bool:
        return self.success and self.subject_line is not None and self.body is not None


async def generate_draft(
    company: str,
    role: str,
    model: str = "openai/gpt-4o",
    temperature: float = 0.7,
    api_key: str | None = None,
) -> EmailDraft:
    """
    Generate a cold email draft for a detected hiring signal.

    Uses litellm to call whichever LLM provider is configured.
    The system prompt constrains the LLM to output JSON with
    subject_line and body fields.

    Args:
        company: The company name (e.g. "Acme Corp").
        role: The detected role (e.g. "VP of AI").
        model: litellm model string (e.g. "openai/gpt-4o", "anthropic/claude-sonnet-4-5").
        temperature: LLM sampling temperature.
        api_key: Optional API key override (otherwise uses env vars).

    Returns:
        EmailDraft with the generated subject line and body.
    """
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
        )
