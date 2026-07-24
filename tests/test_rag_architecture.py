from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from core.application import AnswerService
from core.llm import ExtractiveProvider
from core.llm import OpenAIResponsesProvider
from core.models import Route
from core.router import KeywordQuestionRouter
from mcp.client import InProcessMCPClient
from mcp.server import SQLMCPServer
from mcp.tools import ReadOnlySQLiteTools
from rag.chunker import WordChunker
from rag.embeddings import HashEmbeddingProvider
from rag.retriever import VectorRetriever
from rag.vector_store import SQLiteVectorStore


class ArchitectureTests(unittest.TestCase):
    def test_gpt5_responses_payload_omits_temperature(self):
        self.assertFalse(OpenAIResponsesProvider._supports_temperature("gpt-5.3-chat-latest"))
        self.assertTrue(OpenAIResponsesProvider._supports_temperature("gpt-4o"))

    def test_chunk_metadata_and_overlap(self):
        chunks = WordChunker(5, 2).split("doc-1", [(7, "Heading\none two three four five six seven")], "a.pdf")
        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(chunks[0].metadata.page_number, 7)
        self.assertEqual(chunks[0].metadata.document_id, "doc-1")
        self.assertEqual(chunks[0].metadata.source_filename, "a.pdf")
        self.assertTrue(chunks[0].chunk_id)

    def test_vector_store_roundtrip_and_grounded_service(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            embeddings = HashEmbeddingProvider(64)
            store = SQLiteVectorStore(root / "vectors.db", embeddings.dimension)
            chunks = WordChunker(10, 2).split(
                "doc", [(1, "Budget sponsor organization pays for talent platform")], "source.pdf"
            )
            store.upsert(chunks, embeddings.embed_documents([chunk.text for chunk in chunks]))
            database = root / "data.db"
            with sqlite3.connect(database) as conn:
                conn.executescript(
                    "CREATE TABLE analytics_metrics(label TEXT,value REAL,unit TEXT,period TEXT,"
                    "scope TEXT,source_page INTEGER,note TEXT,chart_key TEXT,source_document_id INTEGER);"
                    "CREATE TABLE documents(id INTEGER,title TEXT);"
                )
            service = AnswerService(
                VectorRetriever(embeddings, store, 2),
                ExtractiveProvider(),
                InProcessMCPClient(ReadOnlySQLiteTools(database)),
            )
            result = service.answer("Which organization is the sponsor?")
            self.assertEqual(result.route, Route.SQL)
            self.assertTrue(result.chunks)
            self.assertIn("source.pdf", result.evidence[0])

    def test_readonly_sql_rejects_writes_and_multiple_statements(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "data.db"
            with sqlite3.connect(database) as conn:
                conn.execute("CREATE TABLE values_table(value TEXT)")
                conn.execute("INSERT INTO values_table VALUES('safe')")
            tools = ReadOnlySQLiteTools(database)
            result = tools.execute_readonly_sql("SELECT * FROM values_table")
            self.assertEqual(result.rows[0]["value"], "safe")
            with self.assertRaises(ValueError):
                tools.execute_readonly_sql("DELETE FROM values_table")
            with self.assertRaises(ValueError):
                tools.execute_readonly_sql("SELECT 1; SELECT 2")

    def test_mcp_protocol_lists_and_calls_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "data.db"
            with sqlite3.connect(database) as conn:
                conn.execute("CREATE TABLE people(id INTEGER,name TEXT)")
                conn.execute("INSERT INTO people VALUES(1,'Ada')")
            server = SQLMCPServer(ReadOnlySQLiteTools(database))
            listed = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
            self.assertIn("execute_readonly_sql", {tool["name"] for tool in listed["result"]["tools"]})
            called = server.handle({
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "search_people", "arguments": {"query": "Ada"}},
            })
            content = called["result"]["structuredContent"]
            self.assertEqual(content["rows"][0]["name"], "Ada")

    def test_router_supports_hybrid(self):
        self.assertEqual(KeywordQuestionRouter().route("Explain the budget statistics"), Route.HYBRID)


if __name__ == "__main__":
    unittest.main()
