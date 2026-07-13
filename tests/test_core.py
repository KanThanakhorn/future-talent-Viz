import math
import tempfile
import unittest
from pathlib import Path

from app.analytics import seed_analytics
from app.db import connect, init_db
from app.ingest import _is_url_reference, chunks_from_pages
from app.retrieval import _fts_tokens, cosine, embed


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

    def test_fts_terms_drop_question_stopwords(self):
        self.assertEqual(_fts_tokens("What skills are growing fastest?"), ["skills", "growing", "fastest"])

    def test_schema_migration_and_analytics_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.db"
            init_db(path)
            with connect(path) as conn:
                columns = {row[1] for row in conn.execute("PRAGMA table_info(chunks)")}
                self.assertIn("source_type", columns)
                for source_uri, title in [
                    ("file:///wef.pdf", "Future of Jobs Report 2025"),
                    ("file:///neet.pdf", "In-depth Research on Youth NEET in Thailand"),
                ]:
                    conn.execute(
                        """INSERT INTO documents(source_uri,title,source,topic,document_type,content_hash)
                           VALUES(?,?,?,'test','pdf','hash')""",
                        (source_uri, title, "test"),
                    )
                seed_analytics(conn)
                count = conn.execute("SELECT COUNT(*) FROM analytics_metrics").fetchone()[0]
                untraced = conn.execute("SELECT COUNT(*) FROM analytics_metrics WHERE source_page IS NULL").fetchone()[0]
                self.assertGreaterEqual(count, 30)
                self.assertEqual(untraced, 0)


if __name__ == "__main__":
    unittest.main()
