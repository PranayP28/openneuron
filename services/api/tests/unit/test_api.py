import json
import time
import unittest

from fastapi.testclient import TestClient

import services.api.app.orchestrator.nodes as nodes_module
from services.api.app.orchestrator.graph import legal_graph
from services.api.app.services.inference import MockInferenceClient
from services.api.main import app

LEASE = (
    b"This rental agreement is between Landlord and Tenant. "
    b"Tenant shall pay rent of $1000 on the first day of each month. "
    b"Either party may terminate this lease with 30 days written notice."
)


class TestApi(unittest.TestCase):
    def setUp(self):
        nodes_module.inference_client = MockInferenceClient()
        self.client = TestClient(app)

    def _upload(self, content=LEASE, name="lease.txt"):
        return self.client.post("/upload", files={"file": (name, content, "text/plain")})

    def test_upload_classifies_and_indexes(self):
        res = self._upload()
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["category"], "rental")
        self.assertTrue(data["is_legal"])
        self.assertGreater(data["num_chunks"], 0)

    def test_upload_rejects_unsupported_type(self):
        res = self._upload(b"hello", "notes.docx")
        self.assertEqual(res.status_code, 400)

    def test_upload_rejects_empty_text(self):
        res = self._upload(b"   ", "empty.txt")
        self.assertEqual(res.status_code, 422)

    def test_chat_returns_sections(self):
        doc_id = self._upload().json()["doc_id"]
        res = self.client.post("/chat", data={"doc_id": doc_id, "query": "How much is the rent?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("MOCK_RESPONSE", data["response"])
        self.assertEqual([s["category"] for s in data["sections"]], ["clause", "risk", "obligation", "deadline"])

    def test_chat_non_legal(self):
        doc_id = self._upload(b"I love eating apples. Apples are red.", "apples.txt").json()["doc_id"]
        res = self.client.post("/chat", data={"doc_id": doc_id, "query": "What color?"})
        self.assertIn("does not appear to be a legal document", res.json()["response"])

    def test_chat_unknown_and_invalid_doc(self):
        self.assertEqual(self.client.post("/chat", data={"doc_id": "../etc/passwd", "query": "x"}).status_code, 400)
        missing = "00000000-0000-0000-0000-000000000000"
        self.assertEqual(self.client.post("/chat", data={"doc_id": missing, "query": "x"}).status_code, 404)

    def test_chat_rejects_empty_query(self):
        doc_id = self._upload().json()["doc_id"]
        res = self.client.post("/chat", data={"doc_id": doc_id, "query": "   "})
        self.assertEqual(res.status_code, 400)

    def test_chat_stream_emits_sections_then_final(self):
        doc_id = self._upload().json()["doc_id"]
        res = self.client.post("/chat/stream", data={"doc_id": doc_id, "query": "When can I terminate?"})
        self.assertEqual(res.status_code, 200)
        events = [json.loads(line) for line in res.text.splitlines() if line]
        sections = [e for e in events if e["type"] == "section"]
        self.assertEqual(len(sections), 4)
        self.assertEqual(events[-1]["type"], "final")
        self.assertIn("MOCK_RESPONSE", events[-1]["response"])


class TestParallelAnalysis(unittest.TestCase):
    def test_analyses_run_concurrently(self):
        delay = 0.3

        class SlowMock(MockInferenceClient):
            def generate(self, prompt, system=None):
                if "Category:" not in prompt:
                    time.sleep(delay)
                return super().generate(prompt, system)

        nodes_module.inference_client = SlowMock()
        with open("parallel.txt", "w") as f:
            f.write(LEASE.decode())

        start = time.perf_counter()
        result = legal_graph.invoke({"doc_id": "parallel.txt", "user_query": "rent?", "is_legal_doc": False})
        elapsed = time.perf_counter() - start

        self.assertTrue(result["is_legal_doc"])
        # Sequential execution would take >= 4 * delay.
        self.assertLess(elapsed, 3 * delay)


if __name__ == "__main__":
    unittest.main()
