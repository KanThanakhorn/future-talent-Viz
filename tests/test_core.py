import math
import unittest

from app.ingest import _is_url_reference, chunks_from_pages
from app.retrieval import cosine, embed


class CoreTests(unittest.TestCase):
    def test_url_reference_detection_rejects_content(self):
        self.assertTrue(_is_url_reference("https://example.org/article\n"))
        self.assertFalse(_is_url_reference("https://example.org\narticle body"))
        self.assertFalse(_is_url_reference(""))

    def test_embeddings_are_normalized_and_deterministic(self):
        first = embed("AI and big data skills")
        second = embed("AI and big data skills")
        self.assertEqual(first, second)
        self.assertAlmostEqual(math.sqrt(cosine(first, first)), 1.0, places=4)
        self.assertGreater(cosine(first, embed("AI data technology skills")), cosine(first, embed("banana recipe ocean")))

    def test_chunk_page_provenance(self):
        pages = [" ".join(f"a{i}" for i in range(300)), " ".join(f"b{i}" for i in range(300))]
        chunks = chunks_from_pages(pages)
        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(chunks[0][0], 1)
        self.assertEqual(chunks[-1][1], 2)


if __name__ == "__main__":
    unittest.main()
