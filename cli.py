from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.application import result_as_dict
from core.config import load_config
from core.factory import build_answer_service
from core.logging import configure_logging
from database.seed import seed
from rag.chunker import WordChunker
from rag.factory import build_components
from rag.indexer import DocumentIndexer
from rag.loader import PdfTextLoader


def index_documents(paths: list[str] | None = None) -> int:
    config = load_config()
    embeddings, store = build_components(config)
    loader = PdfTextLoader(WordChunker(config.rag.chunk_size, config.rag.chunk_overlap))
    indexer = DocumentIndexer(loader, embeddings, store)
    selected_paths = paths or list(config.rag.pdf_paths)
    count = indexer.index(selected_paths)
    print(f"Indexed {count} chunks from {len(loader.discover(selected_paths))} PDF(s).")
    return count


def print_answer(question: str, *, as_json: bool = False, model: str | None = None) -> None:
    result = build_answer_service().answer(question, model=model)
    if as_json:
        print(json.dumps(result_as_dict(result), ensure_ascii=False, indent=2))
        return
    print("\nAnswer:")
    print(result.answer)
    print("\nEvidence:")
    for item in result.evidence:
        print(f"- {item}")
    print("\nSource PDF:")
    for source in sorted({item.chunk.metadata.source_filename for item in result.chunks}):
        pages = sorted({
            item.chunk.metadata.page_number for item in result.chunks
            if item.chunk.metadata.source_filename == source and item.chunk.metadata.page_number is not None
        })
        print(f"- {source}; page(s) {', '.join(map(str, pages))}")
    print("\nRetrieved chunk ids:")
    print(", ".join(item.chunk.chunk_id for item in result.chunks))
    print(f"\nExecution time: {result.execution_time:.2f} sec")


def interactive() -> None:
    print("Future Talent RAG + MCP CLI. Type 'exit' to quit.")
    while True:
        try:
            question = input("\nAsk: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if question.lower() in {"exit", "quit", "q"}:
            return
        if not question:
            continue
        try:
            print_answer(question)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Future Talent RAG + MCP")
    subparsers = parser.add_subparsers(dest="command")
    ask_parser = subparsers.add_parser("ask", help="Ask one question")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--json", action="store_true")
    ask_parser.add_argument("--model")
    index_parser = subparsers.add_parser("index", help="Index configured PDFs")
    index_parser.add_argument("paths", nargs="*")
    subparsers.add_parser("seed-db", help="Create optional structured tables")
    args = parser.parse_args()

    config = load_config()
    configure_logging(config.log_level, config.json_logs)
    if args.command == "ask":
        print_answer(args.question, as_json=args.json, model=args.model)
    elif args.command == "index":
        index_documents(args.paths or None)
    elif args.command == "seed-db":
        seed()
        print(f"Database schema initialized: {config.sql.connection}")
    else:
        interactive()


if __name__ == "__main__":
    main()
