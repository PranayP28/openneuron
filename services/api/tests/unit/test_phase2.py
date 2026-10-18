import unittest
from services.api.app.services.ingestion import IngestionService
from services.api.app.services.chunking import ChunkingService
from services.api.app.services.inference import MockInferenceClient

class TestPhase2(unittest.TestCase):
    def setUp(self):
        self.ingestion = IngestionService()
        self.chunking = ChunkingService()
        self.inference = MockInferenceClient()

    def test_txt_ingestion(self):
        # Create temp file
        with open("test_doc.txt", "w") as f:
            f.write("This is a sample legal document.")

        text = self.ingestion.extract_text("test_doc.txt")
        self.assertEqual(text, "This is a sample legal document.")

    def test_chunking(self):
        text = "A" * 1500 # Larger than default 1000
        chunks = self.chunking.chunk_text(text)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(len(chunks[0]), 1000)

    def test_mock_inference(self):
        res = self.inference.generate("Hello")
        self.assertIn("MOCK_RESPONSE", res)

if __name__ == "__main__":
    unittest.main()
