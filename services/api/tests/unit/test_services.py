import unittest

from services.api.app.orchestrator.policy import SafetyService
from services.api.app.prompts.templates import get_prompt, parse_category
from services.api.app.services.chunking import ChunkingService
from services.api.app.services.classification import reconcile_category
from services.api.app.services.verification import VerificationService


class TestChunking(unittest.TestCase):
    def test_prefers_sentence_boundaries(self):
        text = ("Sentence number one is here. " * 60).strip()
        chunks = ChunkingService().chunk_text(text, chunk_size=200, overlap=20)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks[:-1]:
            self.assertTrue(chunk.endswith("."))

    def test_overlap_not_less_than_size_terminates(self):
        chunks = ChunkingService().chunk_text("A" * 50, chunk_size=10, overlap=10)
        self.assertGreater(len(chunks), 1)

    def test_empty(self):
        self.assertEqual(ChunkingService().chunk_text(""), [])


class TestVerification(unittest.TestCase):
    def setUp(self):
        self.svc = VerificationService()
        self.context = "Tenant shall pay rent of $1000 monthly. Landlord must repair the roof within 14 days."

    def test_grounded_multi_sentence(self):
        claim = "The tenant pays rent of $1000 monthly. The landlord must repair the roof within 14 days."
        grounded, evidence = self.svc.verify_claim(claim, self.context)
        self.assertTrue(grounded)
        self.assertEqual(len(evidence), 2)

    def test_hallucination(self):
        grounded, _ = self.svc.verify_claim("The moon is made of green cheese entirely.", self.context)
        self.assertFalse(grounded)


class TestSafetyAndPrompts(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(SafetyService().validate_response("This clause is ILLEGAL.")[0])
        self.assertTrue(SafetyService().validate_response("Rent is due monthly.")[0])

    def test_parse_category(self):
        self.assertEqual(parse_category("Category: Rental."), "rental")
        self.assertEqual(parse_category("non-legal"), "non_legal")
        self.assertEqual(parse_category("Service Agreement"), "service_agreement")
        self.assertEqual(parse_category(""), "non_legal")

    def test_prompt_includes_question(self):
        prompt = get_prompt("risk_detection", question="Can they evict me?", text="ctx")
        self.assertIn("Can they evict me?", prompt)
        self.assertIn("Examples:", prompt)


class TestClassification(unittest.TestCase):
    LEASE = (
        "RESIDENTIAL LEASE. The Landlord leases the premises to the Tenant for 12 months. "
        "Rent is $1,200 per month. A security deposit of $1,200 is due at signing. "
        "Either party may terminate with 60 days written notice."
    )
    RECIPE = "Banana smoothie: blend two bananas, a cup of milk and honey for one minute. Serve cold."

    def test_lease_overrides_wrong_model_label(self):
        self.assertEqual(reconcile_category("legal_notice", self.LEASE), "rental")

    def test_non_legal_text_is_blocked_even_if_model_says_legal(self):
        self.assertEqual(reconcile_category("service_agreement", self.RECIPE), "non_legal")

    def test_model_label_kept_when_keywords_agree_or_are_weak(self):
        self.assertEqual(reconcile_category("rental", self.LEASE), "rental")
        nda = "This Agreement is between the parties. Each party shall keep information confidential."
        self.assertEqual(reconcile_category("other_legal", nda), "other_legal")


if __name__ == "__main__":
    unittest.main()
