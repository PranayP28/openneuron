import re
from typing import Dict

from services.api.app.prompts.templates import LEGAL_CATEGORIES, NON_LEGAL_CATEGORY

# Deterministic keyword signals used to sanity-check the (small, local) model's classification.
CATEGORY_KEYWORDS: Dict[str, tuple] = {
    "rental": (
        "lease", "landlord", "tenant", "rent", "premises", "security deposit", "lessee", "lessor",
        "tenancy", "sublet", "rental",
    ),
    "employment": (
        "employee", "employer", "employment", "salary", "wage", "probation", "severance",
        "job title", "working hours", "payroll",
    ),
    "legal_notice": (
        "hereby notified", "notice is hereby", "cease and desist", "legal notice", "summons",
        "plaintiff", "defendant", "demand notice", "show cause",
    ),
    "service_agreement": (
        "service provider", "statement of work", "scope of work", "deliverable", "contractor",
        "service level", "client", "invoice",
    ),
}
GENERIC_LEGAL_KEYWORDS = (
    "agreement", "contract", "party", "parties", "shall", "hereby", "herein", "hereinafter",
    "liability", "indemnify", "indemnification", "governing law", "terminate", "termination",
    "breach", "jurisdiction", "clause", "effective date", "notice", "obligation", "signature",
)

# Below this many distinct legal terms the document is treated as non-legal, whatever the model says.
MIN_LEGAL_TERMS = 2
# A keyword category needs at least this many distinct hits to override the model.
MIN_OVERRIDE_HITS = 2


def _pattern(term: str) -> re.Pattern:
    return re.compile(r"\b" + re.escape(term).replace(r"\ ", r"\s+") + r"s?\b", re.IGNORECASE)


_CATEGORY_PATTERNS = {c: [_pattern(t) for t in terms] for c, terms in CATEGORY_KEYWORDS.items()}
_GENERIC_PATTERNS = [_pattern(t) for t in GENERIC_LEGAL_KEYWORDS]


def keyword_scores(text: str) -> Dict[str, int]:
    """Counts distinct keyword hits per category (plus a 'generic' bucket)."""
    scores = {c: sum(1 for p in patterns if p.search(text)) for c, patterns in _CATEGORY_PATTERNS.items()}
    scores["generic"] = sum(1 for p in _GENERIC_PATTERNS if p.search(text))
    return scores


def reconcile_category(model_category: str, text: str) -> str:
    """Combines the model label with keyword evidence so obvious misclassifications are corrected."""
    scores = keyword_scores(text)
    legal_terms = sum(scores.values())
    if legal_terms < MIN_LEGAL_TERMS:
        return NON_LEGAL_CATEGORY

    best = max(LEGAL_CATEGORIES, key=lambda c: scores[c])
    if scores[best] >= MIN_OVERRIDE_HITS and scores[best] > scores.get(model_category, 0):
        return best
    return model_category
