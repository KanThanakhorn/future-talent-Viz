import math
import tempfile
import unittest
from pathlib import Path

from app.analytics import seed_analytics
from app.db import connect, init_db
from app.ingest import ArticleParser, _is_url_reference, chunks_from_pages
from app.retrieval import _fts_tokens, cosine, embed
from app.main import report_page


class CoreTests(unittest.TestCase):
    def test_report_page_route_exists(self):
        response = report_page(1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Path(response.path).name, "report.html")

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

    def test_tdri_parser_keeps_article_body_and_drops_noise(self):
        parser = ArticleParser(tdri=True)
        parser.feed("""
          <nav>site menu</nav>
          <div id="content_body_post" class="et_pb_post_content">
            <h1>Evidence title</h1><p>""" + "evidence " * 80 + """</p>
          </div>
          <div class="related-posts">อ่านเพิ่มเติม noisy recommendation</div>
        """)
        text = parser.text()
        self.assertIn("Evidence title", text)
        self.assertNotIn("site menu", text)
        self.assertNotIn("recommendation", text)

    def test_fts_terms_drop_question_stopwords(self):
        self.assertEqual(_fts_tokens("What skills are growing fastest?"), ["skills", "growing", "fastest"])

    def test_schema_migration_and_analytics_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.db"
            init_db(path)
            with connect(path) as conn:
                columns = {row[1] for row in conn.execute("PRAGMA table_info(chunks)")}
                self.assertIn("source_type", columns)
                requirement_columns = {row[1] for row in conn.execute("PRAGMA table_info(skill_requirements)")}
                self.assertTrue({"source_document_id", "source_page", "evidence_scope"} <= requirement_columns)
                note_columns = {row[1] for row in conn.execute("PRAGMA table_info(editorial_notes)")}
                self.assertTrue({"section_key", "note_type", "body", "source_document_id", "source_page"} <= note_columns)
                for source_uri, title in [
                    ("file:///wef.pdf", "Future of Jobs Report 2025"),
                    ("file:///neet.pdf", "In-depth Research on Youth NEET in Thailand"),
                    ("file:///stem.pdf", "การพัฒนาการศึกษาและกำลังคนด้านวิทยาศาสตร์ เทคโนโลยี วิศวกรรมศาสตร์ และคณิตศาสตร์ ของประเทศไทย"),
                ]:
                    conn.execute(
                        """INSERT INTO documents(source_uri,title,source,topic,document_type,content_hash)
                           VALUES(?,?,?,'test','pdf','hash')""",
                        (source_uri, title, "test"),
                    )
                seed_analytics(conn)
                seed_analytics(conn)
                count = conn.execute("SELECT COUNT(*) FROM analytics_metrics").fetchone()[0]
                untraced = conn.execute("SELECT COUNT(*) FROM analytics_metrics WHERE source_page IS NULL").fetchone()[0]
                self.assertGreaterEqual(count, 30)
                self.assertEqual(untraced, 0)
                stem_count = conn.execute(
                    "SELECT COUNT(*) FROM analytics_metrics WHERE chart_key='stem_career_alignment'"
                ).fetchone()[0]
                self.assertEqual(stem_count, 4)


if __name__ == "__main__":
    unittest.main()
