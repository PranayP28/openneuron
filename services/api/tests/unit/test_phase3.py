import unittest
from services.api.app.orchestrator.graph import legal_graph
from services.api.app.services.inference import MockInferenceClient
import services.api.app.services.inference as inference_module
import os

class TestPhase3(unittest.TestCase):
    def setUp(self):
        # Force the mock client into the module where nodes import it
        inference_module.inference_client = MockInferenceClient()
        # Also patch it in the nodes module specifically if it was imported directly
        import services.api.app.orchestrator.nodes
        services.api.app.orchestrator.nodes.inference_client = MockInferenceClient()

    def test_full_pipeline_legal(self):
        doc_path = "test_legal.txt"
        with open(doc_path, "w") as f:
            f.write("This is a rental agreement. Tenant shall pay $1000 per month.")

        inputs = {
            "doc_id": doc_path,
            "user_query": "How much is the rent?",
            "is_legal_doc": False
        }

        result = legal_graph.invoke(inputs)

        self.assertTrue(result["is_legal_doc"])
        self.assertIsNotNone(result["final_response"])
        self.assertIn("MOCK_RESPONSE", result["final_response"])

    def test_full_pipeline_non_legal(self):
        doc_path = "test_non_legal.txt"
        with open(doc_path, "w") as f:
            f.write("I love eating apples. Apples are red.")

        inputs = {
            "doc_id": doc_path,
            "user_query": "What color are apples?",
            "is_legal_doc": False
        }

        result = legal_graph.invoke(inputs)

        self.assertFalse(result["is_legal_doc"])
        # Instead of assertIsNone, check if key exists or is None
        self.assertTrue(result.get("final_response") is None)


if __name__ == "__main__":
    unittest.main()
