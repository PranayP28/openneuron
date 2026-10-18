from typing import Tuple

FORBIDDEN_TERMS = (
    "enforceable", "illegal", "you will win", "should sign",
    "legal advice", "binding", "lawsuit", "court will",
)


class SafetyService:
    """Enforces non-negotiable legal constraints."""

    def validate_response(self, response: str) -> Tuple[bool, str]:
        """
        Checks if the response contains forbidden legal verdicts.
        Returns (is_safe, error_message).
        """
        lowered = response.lower()
        for term in FORBIDDEN_TERMS:
            if term in lowered:
                return False, f"Response contains forbidden legal verdict: '{term}'"
        return True, ""


safety_service = SafetyService()
