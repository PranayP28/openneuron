import re
from typing import List, Tuple

_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "and", "or", "of", "in", "on",
    "to", "for", "with", "by", "as", "at", "it", "its", "this", "that", "these", "those", "which",
    "from", "not", "no", "any", "all", "may", "can", "will", "shall", "must", "should", "if",
    "document", "text", "clause", "says", "states", "explicit", "interpretation", "means",
}
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD = re.compile(r"\w+")
_MIN_KEYWORDS = 3
_SENTENCE_OVERLAP = 0.3
_SUPPORTED_FRACTION = 0.5


def _keywords(text: str) -> set:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP_WORDS}


class VerificationService:
    """Ensures AI claims are grounded in the actual document text."""

    def verify_claim(self, claim: str, context: str) -> Tuple[bool, List[str]]:
        """
        Checks if a claim is supported by the provided context using sentence-level
        keyword overlap. A claim is grounded when at least half of its checkable
        sentences overlap (>30% of keywords) with some sentence of the context.
        Returns (is_grounded, evidence_sentences).
        """
        if not context or not claim:
            return False, []

        context_sentences = [s.strip() for s in _SENTENCE_SPLIT.split(context) if s.strip()]
        context_keywords = [(s, _keywords(s)) for s in context_sentences]

        claim_sentences = [s for s in _SENTENCE_SPLIT.split(claim) if s.strip()]
        checkable = [kw for kw in (_keywords(s) for s in claim_sentences) if len(kw) >= _MIN_KEYWORDS]
        if not checkable:
            whole = _keywords(claim)
            checkable = [whole] if whole else []
        if not checkable:
            return False, []

        evidence: List[str] = []
        supported = 0
        for keywords in checkable:
            best_sentence, best_ratio = None, 0.0
            for sentence, sent_keywords in context_keywords:
                ratio = len(keywords & sent_keywords) / len(keywords)
                if ratio > best_ratio:
                    best_sentence, best_ratio = sentence, ratio
            if best_sentence is not None and best_ratio > _SENTENCE_OVERLAP:
                supported += 1
                if best_sentence not in evidence:
                    evidence.append(best_sentence)

        is_grounded = supported / len(checkable) >= _SUPPORTED_FRACTION
        return is_grounded, evidence


verification_service = VerificationService()
