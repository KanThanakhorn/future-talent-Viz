from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import re
import shutil
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

from .config import ROOT, settings
from .db import init_db, transaction
from .retrieval import embed

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOG = logging.getLogger("ingestion")

METADATA = {
    "WEF_Future_of_Jobs_Report_2025.pdf": ("Future of Jobs Report 2025", "World Economic Forum", "2025-01-01", "Future of work"),
    "In-depth research on youth NEET in Thailand.pdf": ("In-depth Research on Youth NEET in Thailand", "UNICEF Thailand", "2023-01-01", "Youth NEET"),
    "thailand-labour-demand-and-future-skills.txt": ("Thailand Labour Demand and Future Skills", "TDRI", "2024-06-01", "Labour demand and future skills"),
    "stem-education-and-workforce.txt": ("STEM Education and Workforce in Thailand", "TDRI", "2025-07-01", "STEM workforce"),
    "thai-youth-neet-motivation.txt": ("Thai Youth NEET Motivation", "UNICEF Thailand", "2023-03-01", "Youth NEET"),
    "human-capital-unicef.txt": ("Human Capital Development in Thailand", "TDRI", "2026-01-29", "Human capital"),
}


@dataclass
class Extracted:
    source_uri: str
    title: str
    source: str
    published_date: str | None
    topic: str
    document_type: str
    raw_path: str
    pages: list[str]
    methods: list[str]
    review_pages: set[int]


class ArticleParser(HTMLParser):
    SKIP = {"script", "style", "svg", "noscript", "nav", "footer", "header", "form"}

    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.article_depth = 0
        self.skip_depth = 0
        self.parts: list[str] = []
        self.fallback: list[str] = []
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP:
            self.skip_depth += 1
        if tag in {"article", "main"}:
            self.article_depth += 1
        if tag == "title":
            self.in_title = True
        if tag in {"p", "h1", "h2", "h3", "li", "br"}:
            self.parts.append("\n")
            self.fallback.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1
        if tag in {"article", "main"} and self.article_depth:
            self.article_depth -= 1
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data
        if self.skip_depth or not data.strip():
            return
        self.fallback.append(data)
        if self.article_depth:
            self.parts.append(data)

    def text(self) -> str:
        chosen = self.parts if len(" ".join(self.parts)) > 500 else self.fallback
        value = html.unescape(" ".join(chosen))
        return re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", value)).strip()


def _meta(path: Path) -> tuple[str, str, str | None, str]:
    return METADATA.get(path.name, (path.stem.replace("_", " "), "Unknown", None, "Future ready talent"))


def extract_pdf(path: Path) -> Extracted:
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext is required for PDF extraction")
    with tempfile.NamedTemporaryFile(suffix=".txt") as output:
        subprocess.run(["pdftotext", "-layout", str(path), output.name], check=True, capture_output=True)
        pages = Path(output.name).read_text(encoding="utf-8", errors="replace").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    pages = [re.sub(r"[ \t]+", " ", page).strip() for page in pages]
    review_pages = {i for i, text in enumerate(pages, 1) if len(text) < 250}
    # pdfimages gives a cheap signal for full-page charts/infographics. Queue only
    # image-heavy pages whose text layer is also sparse enough to miss labels.
    if shutil.which("pdfimages"):
        listing = subprocess.run(["pdfimages", "-list", str(path)], check=True, capture_output=True, text=True).stdout
        for line in listing.splitlines():
            columns = line.split()
            if len(columns) < 6 or not columns[0].isdigit() or not columns[3].isdigit() or not columns[4].isdigit():
                continue
            page_number, width, height = int(columns[0]), int(columns[3]), int(columns[4])
            if width * height >= 1_000_000 and page_number <= len(pages) and len(pages[page_number - 1]) < 1500:
                review_pages.add(page_number)
    methods = ["text-layer" for _ in pages]
    title, source, published, topic = _meta(path)
    return Extracted(str(path.resolve()), title, source, published, topic, "pdf", str(path), pages, methods, review_pages)


def _is_url_reference(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return len(lines) == 1 and bool(re.fullmatch(r"https?://\S+", lines[0]))


def extract_text_reference(path: Path) -> Extracted:
    raw = path.read_text(encoding="utf-8").strip()
    if not _is_url_reference(raw):
        raise ValueError(f"{path.name} is not a single URL reference")
    request = urllib.request.Request(raw, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/136 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "th,en-US;q=0.8,en;q=0.7",
    })
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
    except Exception:
        # Some publisher CDNs reject urllib's TLS fingerprint even with normal
        # browser headers. curl is a deterministic fallback, never a source of
        # synthetic content; validation below still rejects empty/error pages.
        if not shutil.which("curl"):
            raise
        result = subprocess.run(
            ["curl", "-L", "--fail", "--max-time", "45", "-A", request.headers["User-agent"], "-H", "Accept: text/html,application/xhtml+xml", raw],
            check=True, capture_output=True,
        )
        body = result.stdout
        charset = "utf-8"
    parser = ArticleParser()
    parser.feed(body.decode(charset, errors="replace"))
    content = parser.text()
    if len(content) < 300:
        raise ValueError(f"Fetched page contains too little usable content ({len(content)} chars)")
    raw_dir = ROOT / "data" / "raw-web"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{path.stem}.html"
    raw_path.write_bytes(body)
    title, source, published, topic = _meta(path)
    if parser.title.strip():
        title = re.sub(r"\s+", " ", parser.title).strip().split(" | ")[0].split(" - TDRI")[0]
    return Extracted(raw, title, source, published, topic, "web", str(raw_path), [content], ["html-parser"], set())


def chunks_from_pages(pages: list[str]) -> list[tuple[int, int, str]]:
    chunks: list[tuple[int, int, str]] = []
    buffer: list[tuple[str, int]] = []
    for page_number, page in enumerate(pages, 1):
        for word in page.split():
            buffer.append((word, page_number))
            if len(buffer) >= settings.chunk_words:
                content = " ".join(word for word, _ in buffer)
                chunks.append((buffer[0][1], buffer[-1][1], content))
                buffer = buffer[-settings.chunk_overlap :]
    if len(buffer) >= 30 or not chunks:
        chunks.append((buffer[0][1] if buffer else 1, buffer[-1][1] if buffer else 1, " ".join(w for w, _ in buffer)))
    return chunks


def save_document(item: Extracted, force: bool = False) -> tuple[int, bool]:
    full_text = "\n\f\n".join(item.pages)
    digest = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
    if not full_text.strip():
        raise ValueError("Refusing to insert empty document")
    with transaction() as conn:
        old = conn.execute("SELECT id, content_hash FROM documents WHERE source_uri = ?", (item.source_uri,)).fetchone()
        if old and old["content_hash"] == digest and not force:
            return int(old["id"]), False
        conn.execute(
            """INSERT INTO documents(source_uri,title,source,published_date,topic,document_type,content_hash,status,page_count,raw_path)
               VALUES(?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(source_uri) DO UPDATE SET title=excluded.title, source=excluded.source,
               published_date=excluded.published_date, topic=excluded.topic, content_hash=excluded.content_hash,
               status='ready', page_count=excluded.page_count, raw_path=excluded.raw_path, updated_at=CURRENT_TIMESTAMP""",
            (item.source_uri, item.title, item.source, item.published_date, item.topic, item.document_type, digest, "ready", len(item.pages), item.raw_path),
        )
        document_id = int(conn.execute("SELECT id FROM documents WHERE source_uri=?", (item.source_uri,)).fetchone()["id"])
        conn.execute("DELETE FROM document_pages WHERE document_id=?", (document_id,))
        conn.execute("DELETE FROM chunks WHERE document_id=?", (document_id,))
        for page_number, (content, method) in enumerate(zip(item.pages, item.methods), 1):
            conn.execute(
                "INSERT INTO document_pages(document_id,page_number,content,extraction_method,confidence,needs_review) VALUES(?,?,?,?,?,?)",
                (document_id, page_number, content, method, 1.0 if method == "text-layer" else 0.95, page_number in item.review_pages),
            )
        for index, (start, end, content) in enumerate(chunks_from_pages(item.pages)):
            chunk_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            conn.execute(
                """INSERT INTO chunks(document_id,page_start,page_end,chunk_index,content,content_hash,embedding,source_type)
                   VALUES(?,?,?,?,?,?,?,'narrative')""",
                (document_id, start, end, index, content, chunk_hash, json.dumps(embed(content), separators=(",", ":"))),
            )
        for page in sorted(item.review_pages):
            conn.execute(
                "INSERT INTO extraction_logs(source_uri,document_id,page_number,level,stage,message) VALUES(?,?,?,?,?,?)",
                (item.source_uri, document_id, page, "warning", "ocr-review", "Low text density; review image/table and run OCR if needed"),
            )
    return document_id, True


def seed_verified_data() -> None:
    with transaction() as conn:
        wef = conn.execute("SELECT id FROM documents WHERE title='Future of Jobs Report 2025'").fetchone()
        if not wef:
            return
        document_id = int(wef["id"])
        conn.execute("INSERT OR IGNORE INTO industries(name,description) VALUES(?,?)", ("Global labour market", "WEF employer survey extrapolation"))
        industry_id = int(conn.execute("SELECT id FROM industries WHERE name='Global labour market'").fetchone()["id"])
        metrics = [
            ("Jobs created", 170_000_000, "creation", "14% of current employment"),
            ("Jobs displaced", 92_000_000, "displacement", "8% of current employment"),
            ("Net job growth", 78_000_000, "net-growth", "7% of current employment"),
        ]
        for role, headcount, metric, note in metrics:
            conn.execute(
                """INSERT OR IGNORE INTO job_demand(industry_id,job_role,headcount_needed,year_start,year_end,metric_type,source_document_id,source_page,note)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (industry_id, role, headcount, 2025, 2030, metric, document_id, 5, note),
            )
        skills = [
            ("AI and big data", "technology"), ("Networks and cybersecurity", "technology"),
            ("Technological literacy", "technology"), ("Creative thinking", "cognitive"),
            ("Resilience, flexibility and agility", "self-efficacy"),
            ("Curiosity and lifelong learning", "self-efficacy"),
            ("Leadership and social influence", "interpersonal"),
            ("Talent management", "management"), ("Analytical thinking", "cognitive"),
            ("Environmental stewardship", "sustainability"),
        ]
        for rank, (name, category) in enumerate(skills, 1):
            conn.execute(
                "INSERT OR IGNORE INTO skills(name,category,source_document_id,source_page) VALUES(?,?,?,?)",
                (name, category, document_id, 35),
            )
        from .analytics import seed_analytics

        seed_analytics(conn)


def log_failure(source_uri: str, message: str) -> None:
    with transaction() as conn:
        conn.execute(
            "INSERT INTO extraction_logs(source_uri,level,stage,message) VALUES(?,?,?,?)",
            (source_uri, "error", "ingestion", message[:2000]),
        )


def run(dataset: Path, force: bool = False) -> int:
    init_db()
    successes = 0
    for path in sorted(dataset.iterdir()):
        if path.suffix.lower() not in {".pdf", ".txt"}:
            continue
        try:
            extracted = extract_pdf(path) if path.suffix.lower() == ".pdf" else extract_text_reference(path)
            document_id, changed = save_document(extracted, force)
            successes += 1
            LOG.info("%s document %s (%s)", "Indexed" if changed else "Unchanged", document_id, path.name)
        except Exception as exc:
            LOG.error("Skipped %s: %s", path.name, exc)
            log_failure(str(path.resolve()), str(exc))
    seed_verified_data()
    return successes


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Future Ready Talent source documents")
    parser.add_argument("--dataset", type=Path, default=settings.dataset_path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    count = run(args.dataset, args.force)
    LOG.info("Finished: %s source(s) available", count)


if __name__ == "__main__":
    main()
