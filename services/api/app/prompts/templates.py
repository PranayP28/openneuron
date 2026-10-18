from collections import defaultdict
from typing import Optional

# Versioned prompt templates. Each template includes few-shot examples as per requirements.
PROMPT_VERSION = "2"

_ANALYSIS_SYSTEM = (
    "You are a legal document triage assistant running fully offline. You do NOT provide legal advice "
    "or verdicts. You explain only what the document excerpts say, quoting or closely paraphrasing them. "
    "If the excerpts are silent on a point, say 'document is silent'. Be concise: at most 5 short bullet points, "
    "with no introduction or closing remarks."
)

PROMPTS = {
    "clause_analysis": {
        "template": (
            "Explain the clauses in the document excerpts that relate to the user question, in plain language. "
            "Separate explicit statements from interpretations.\n\n"
            "User question: {question}\n\nDocument excerpts:\n{text}\n\nClause analysis:"
        ),
        "system": _ANALYSIS_SYSTEM,
        "few_shot": [
            {"input": "Tenant shall pay rent on the 1st of each month.", "output": "Explicit: Rent is due on the 1st. Interpretation: The tenant is responsible for timely payment to avoid late fees."},
            {"input": "The parties may agree to modify this in writing.", "output": "Explicit: Modifications must be written. Interpretation: Verbal changes to terms are likely not accepted."},
        ],
    },
    "risk_detection": {
        "template": (
            "Identify any 'red flag' language or unfavorable terms in the document excerpts that relate to the "
            "user question. Be objective.\n\n"
            "User question: {question}\n\nDocument excerpts:\n{text}\n\nRisks:"
        ),
        "system": _ANALYSIS_SYSTEM + " Identify unfavorable terms without giving legal verdicts.",
        "few_shot": [
            {"input": "Landlord may enter premises at any time without notice.", "output": "Red Flag: Lack of notice for entry may conflict with privacy expectations."},
            {"input": "This agreement is governed by the laws of the Galactic Empire.", "output": "Risk: Unfamiliar or non-standard jurisdiction."},
        ],
    },
    "obligation_extraction": {
        "template": (
            "List the obligations (who must do what) stated in the document excerpts that relate to the user "
            "question.\n\n"
            "User question: {question}\n\nDocument excerpts:\n{text}\n\nObligations:"
        ),
        "system": _ANALYSIS_SYSTEM,
        "few_shot": [
            {"input": "Tenant shall keep the premises clean and notify Landlord of any damage.", "output": "- Tenant: keep the premises clean.\n- Tenant: notify Landlord of any damage."},
        ],
    },
    "deadline_extraction": {
        "template": (
            "List every date, deadline, notice period or duration stated in the document excerpts that relates "
            "to the user question.\n\n"
            "User question: {question}\n\nDocument excerpts:\n{text}\n\nDeadlines:"
        ),
        "system": _ANALYSIS_SYSTEM,
        "few_shot": [
            {"input": "Either party may terminate with 30 days written notice. The term ends on 31 December 2025.", "output": "- Termination notice: 30 days, in writing.\n- Term end: 31 December 2025."},
        ],
    },
    "classify_label": {
        "template": (
            "Classify the following document into one of these categories: "
            "[rental, employment, legal_notice, service_agreement, non_legal].\n\n"
            "Document text: {text}\n\nCategory:"
        ),
        "system": "You are a document classifier. Only output the category label.",
        "few_shot": [
            {"input": "This lease agreement is between...", "output": "rental"},
            {"input": "I am writing to notify you that your employment...", "output": "employment"},
            {"input": "The weather is nice today.", "output": "non_legal"},
        ],
    },
}

LEGAL_CATEGORIES = ("rental", "employment", "legal_notice", "service_agreement")
NON_LEGAL_CATEGORY = "non_legal"


def _format_few_shot(key: str) -> str:
    examples = PROMPTS.get(key, {}).get("few_shot", [])
    if not examples:
        return ""
    lines = ["Examples:"]
    for ex in examples:
        lines.append(f"Input: {ex['input']}\nOutput: {ex['output']}")
    return "\n".join(lines) + "\n\n"


def get_prompt(key: str, **kwargs) -> str:
    template = PROMPTS.get(key, {}).get("template", "")
    return _format_few_shot(key) + template.format_map(defaultdict(str, kwargs))


def get_system_prompt(key: str) -> str:
    return PROMPTS.get(key, {}).get("system", "")


def parse_category(raw: Optional[str]) -> str:
    """Normalizes free-form model output (e.g. 'Category: Rental.') to a known label."""
    text = (raw or "").strip().lower().replace("-", "_").replace(" ", "_")
    if "non_legal" in text or "not_legal" in text:
        return NON_LEGAL_CATEGORY
    for label in LEGAL_CATEGORIES:
        if label in text:
            return label
    return "other_legal" if text else NON_LEGAL_CATEGORY
