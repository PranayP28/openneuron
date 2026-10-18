from typing import List, Tuple
from services.api.app.config.settings import settings

class SafetyService:
    """Enforces non-negotiable legal constraints."""

    def validate_response(self, response: str) -> Tuple[bool, str]:
        """
        Checks if the response contains forbidden legal verdicts.
        Returns (is_safe, error_message).
        """
        forbidden_terms = [
            "enforceable", "illegal", "you will win", "should sign",
            "legal advice", "binding", "lawsuit", "court will"
        ]

        for term in forbidden_terms:
            if term.lower() in response.lower():
                return False, f"Response contains forbidden legal verdict: '{term}'"

        return True, ""

safety_service = SafetyService()
