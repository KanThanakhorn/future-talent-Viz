from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import ROOT
from .db import connect, init_db
from .rag import answer
from .retrieval import retrieve

app = FastAPI(title="Future Ready Talent API", version="0.1.0")
STATIC = ROOT / "frontend"
app.mount("/assets", StaticFiles(directory=STATIC), name="assets")


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    limit: int = Field(default=6, ge=1, le=12)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    with connect() as conn:
        document_count = conn.execute("SELECT COUNT(*) FROM documents WHERE status='ready'").fetchone()[0]
        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    return {"status": "ok", "documents": document_count, "chunks": chunk_count}


@app.get("/api/documents")
def documents() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT d.id,d.title,d.source,d.published_date,d.topic,d.document_type,d.source_uri,d.page_count,
                      COUNT(DISTINCT CASE WHEN p.needs_review=1 THEN p.id END) AS review_pages
               FROM documents d LEFT JOIN document_pages p ON p.document_id=d.id
               WHERE d.status='ready' GROUP BY d.id ORDER BY d.published_date DESC"""
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/dashboard")
def dashboard() -> dict:
    with connect() as conn:
        demand = [dict(row) for row in conn.execute(
            """SELECT j.job_role,j.headcount_needed,j.year_start,j.year_end,j.metric_type,j.source_page,
                      i.name AS industry,d.title AS source_title,d.id AS document_id
               FROM job_demand j JOIN industries i ON i.id=j.industry_id
               JOIN documents d ON d.id=j.source_document_id
               WHERE j.headcount_needed IS NOT NULL ORDER BY j.headcount_needed DESC"""
        )]
        skills = [dict(row) for row in conn.execute(
            """SELECT s.name,s.category,s.source_page,d.title AS source_title,d.id AS document_id
               FROM skills s JOIN documents d ON d.id=s.source_document_id ORDER BY s.id LIMIT 10"""
        )]
        totals = dict(conn.execute(
            """SELECT COUNT(*) AS documents,
                      COALESCE(SUM(page_count),0) AS pages,
                      (SELECT COUNT(*) FROM chunks) AS chunks,
                      (SELECT COUNT(*) FROM document_pages WHERE needs_review=1) AS review_pages
               FROM documents WHERE status='ready'"""
        ).fetchone())
    return {"totals": totals, "job_demand": demand, "skills": skills}


@app.get("/api/search")
def search(q: str = Query(min_length=2, max_length=1000), limit: int = Query(6, ge=1, le=12)) -> list[dict]:
    return retrieve(q, limit)


@app.post("/api/chat")
def chat(body: ChatRequest) -> dict:
    contexts = retrieve(body.question, body.limit)
    response, model = answer(body.question, contexts)
    citations = [
        {
            "index": index,
            "document_id": item["document_id"],
            "title": item["title"],
            "source": item["source"],
            "source_uri": item["source_uri"],
            "page_start": item["page_start"],
            "page_end": item["page_end"],
            "score": round(item["score"], 4),
        }
        for index, item in enumerate(contexts, 1)
    ]
    return {"answer": response, "mode": model, "citations": citations}


@app.get("/api/documents/{document_id}/pages/{page_number}")
def document_page(document_id: int, page_number: int) -> dict:
    with connect() as conn:
        row = conn.execute(
            """SELECT p.page_number,p.content,p.extraction_method,p.needs_review,d.title,d.source_uri
               FROM document_pages p JOIN documents d ON d.id=p.document_id
               WHERE p.document_id=? AND p.page_number=?""",
            (document_id, page_number),
        ).fetchone()
    if not row:
        raise HTTPException(404, "Page not found")
    return dict(row)


@app.get("/api/documents/{document_id}/source", include_in_schema=False)
def document_source(document_id: int) -> FileResponse:
    with connect() as conn:
        row = conn.execute("SELECT raw_path,document_type,title FROM documents WHERE id=?", (document_id,)).fetchone()
    if not row or row["document_type"] != "pdf" or not row["raw_path"]:
        raise HTTPException(404, "Local source file not found")
    path = Path(row["raw_path"]).resolve()
    if not path.is_file():
        raise HTTPException(404, "Local source file not found")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
