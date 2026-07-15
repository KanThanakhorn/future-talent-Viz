from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import ROOT, settings
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
        active = conn.execute(
            """SELECT i.model,i.dimension,i.chunk_count,i.status
               FROM embedding_indexes i JOIN system_settings s ON s.value=i.model
               WHERE s.key='active_embedding_model'"""
        ).fetchone()
    index = dict(active) if active else {"model": "local-hash-v1", "dimension": 256, "chunk_count": chunk_count, "status": "fallback"}
    return {"status": "ok", "documents": document_count, "chunks": chunk_count, "embedding_index": index}


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
                      i.name AS industry,d.title AS source_title,d.id AS document_id,
                      d.document_type,d.source_uri
               FROM job_demand j JOIN industries i ON i.id=j.industry_id
               JOIN documents d ON d.id=j.source_document_id
               WHERE j.headcount_needed IS NOT NULL ORDER BY j.headcount_needed DESC"""
        )]
        skills = [dict(row) for row in conn.execute(
            """SELECT s.name,s.category,s.source_page,d.title AS source_title,d.id AS document_id,
                      d.document_type,d.source_uri
               FROM skills s JOIN documents d ON d.id=s.source_document_id ORDER BY s.id LIMIT 10"""
        )]
        totals = dict(conn.execute(
            """SELECT COUNT(*) AS documents,
                      COALESCE(SUM(page_count),0) AS pages,
                      (SELECT COUNT(*) FROM chunks) AS chunks,
                      (SELECT COUNT(*) FROM document_pages WHERE needs_review=1) AS review_pages
               FROM documents WHERE status='ready'"""
        ).fetchone())
        chart_rows = [dict(row) for row in conn.execute(
            """SELECT a.chart_key,a.series,a.label,a.value,a.unit,a.period,a.scope,a.note,a.source_page,
                      d.id AS document_id,d.title AS source_title,d.document_type,d.source_uri
               FROM analytics_metrics a JOIN documents d ON d.id=a.source_document_id
               ORDER BY a.chart_key,a.sort_order"""
        )]
    charts: dict[str, list[dict]] = {}
    for row in chart_rows:
        charts.setdefault(row.pop("chart_key"), []).append(row)
    charts["jobs_transition"] = demand
    gap_ready = bool(charts.get("readiness_gap"))
    charts["demand_readiness_gap"] = {
        "status": "partial" if gap_ready else "data_required",
        "global_demand": charts.get("skill_change", [])[:5],
        "thai_readiness": charts.get("readiness_gap", []),
        "curriculum_coverage": [],
        "message": (
            "ยังไม่มีข้อมูลความพร้อมรายทักษะของเยาวชนไทย และไม่มีตัวเลข curriculum coverage "
            "จากเอกสาร STEM จึงไม่คำนวณช่องว่างรายทักษะ"
        ),
    }
    return {"totals": totals, "job_demand": demand, "skills": skills, "charts": charts}


@app.get("/api/documents/highlights")
def document_highlights() -> list[dict]:
    """Return six document cards and up to two high-impact, cited SQL facts."""
    with connect() as conn:
        rows = conn.execute(
            """SELECT d.id,d.title,d.source,d.published_date,d.topic,d.page_count,
                      d.document_type,d.source_uri,
                      COUNT(DISTINCT a.id) AS metric_count,
                      COUNT(DISTINCT j.id) AS demand_count,
                      COUNT(DISTINCT sr.job_demand_id || '-' || sr.skill_id) AS skill_evidence_count
               FROM documents d
               LEFT JOIN analytics_metrics a ON a.source_document_id=d.id
               LEFT JOIN job_demand j ON j.source_document_id=d.id
               LEFT JOIN skill_requirements sr ON sr.source_document_id=d.id
               WHERE d.status='ready' AND d.id BETWEEN 1 AND 6
               GROUP BY d.id
               ORDER BY CASE
                 WHEN d.title='Future of Jobs Report 2025' THEN 1
                 WHEN d.title='In-depth Research on Youth NEET in Thailand' THEN 2
                 WHEN d.title LIKE 'การพัฒนาทุนมนุษย์%' THEN 3
                 WHEN d.title LIKE 'การพัฒนาการศึกษาและกำลังคน%' THEN 4
                 WHEN d.title LIKE 'แนวโน้มความต้องการแรงงาน%' THEN 5
                 ELSE 6 END"""
        ).fetchall()
        result = []
        for raw in rows:
            row = dict(raw)
            metrics = [dict(item) for item in conn.execute(
                """SELECT label,value,unit,period,source_page,note,'analytics_metric' AS evidence_type
                   FROM analytics_metrics WHERE source_document_id=?
                   ORDER BY CASE chart_key
                     WHEN 'neet_press_release' THEN sort_order
                     WHEN 'neet_provinces' THEN value * -1
                     WHEN 'human_capital_training' THEN value * -1
                     WHEN 'stem_career_alignment' THEN value * -1
                     ELSE sort_order END LIMIT 2""",
                (row["id"],),
            )]
            if row["id"] == 2:
                metrics = [dict(item) for item in conn.execute(
                    """SELECT job_role AS label,headcount_needed AS value,'jobs' AS unit,
                              year_start || '–' || year_end AS period,source_page,note,
                              'job_demand' AS evidence_type
                       FROM job_demand WHERE source_document_id=? AND headcount_needed IS NOT NULL
                       ORDER BY CASE metric_type WHEN 'creation' THEN 1 WHEN 'net-growth' THEN 2 ELSE 3 END LIMIT 2""",
                    (row["id"],),
                )]
            row["highlights"] = metrics
            result.append(row)
    return result


@app.get("/api/reports")
def reports() -> list[dict]:
    """Backward-compatible report listing."""
    return document_highlights()


@app.get("/api/documents/{document_id}/full-data")
def document_full_data(document_id: int) -> dict:
    """All structured, page-level evidence belonging to one document."""
    with connect() as conn:
        document = conn.execute(
            """SELECT id,title,source,published_date,topic,page_count,document_type,source_uri
               FROM documents WHERE id=? AND status='ready'""",
            (document_id,),
        ).fetchone()
        if not document:
            raise HTTPException(404, "Report not found")
        metric_rows = [dict(row) for row in conn.execute(
            """SELECT chart_key,series,label,value,unit,period,scope,sort_order,source_page,note
               FROM analytics_metrics WHERE source_document_id=?
               ORDER BY chart_key,sort_order,id""",
            (document_id,),
        )]
        demand = [dict(row) for row in conn.execute(
            """SELECT j.id,j.job_role,j.headcount_needed,j.demand_value,j.demand_unit,
                      j.year_start,j.year_end,j.metric_type,j.source_page,j.note,i.name AS industry
               FROM job_demand j JOIN industries i ON i.id=j.industry_id
               WHERE j.source_document_id=? ORDER BY j.metric_type,i.name,j.demand_value DESC""",
            (document_id,),
        )]
        requirements = [dict(row) for row in conn.execute(
            """SELECT i.name AS industry,s.name AS skill,s.category,sr.importance_level,
                      sr.source_page,sr.evidence_scope
               FROM skill_requirements sr
               JOIN job_demand j ON j.id=sr.job_demand_id
               JOIN industries i ON i.id=j.industry_id
               JOIN skills s ON s.id=sr.skill_id
               WHERE sr.source_document_id=?
               ORDER BY s.name,sr.importance_level DESC,i.name""",
            (document_id,),
        )]
        evidence_pages = [dict(row) for row in conn.execute(
            """SELECT page_number,section,extraction_method,needs_review,
                      LENGTH(TRIM(content)) AS text_length
               FROM document_pages WHERE document_id=?
               ORDER BY page_number""",
            (document_id,),
        )]
    charts: dict[str, list[dict]] = {}
    for row in metric_rows:
        charts.setdefault(row.pop("chart_key"), []).append(row)
    return {
        "document": dict(document),
        "charts": charts,
        "job_demand": demand,
        "skill_requirements": requirements,
        "evidence_pages": evidence_pages,
    }


@app.get("/api/reports/{document_id}")
def report(document_id: int) -> dict:
    """Backward-compatible alias for the document data endpoint."""
    return document_full_data(document_id)


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
            "document_type": item["document_type"],
            "page_start": item["page_start"],
            "page_end": item["page_end"],
            "score": round(item["score"], 4),
            "source_type": item.get("source_type", "narrative"),
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
        row = conn.execute(
            "SELECT raw_path,source_uri,document_type,title FROM documents WHERE id=?", (document_id,)
        ).fetchone()
    if not row or row["document_type"] != "pdf":
        raise HTTPException(404, "Local source file not found")
    path = Path(row["raw_path"]).resolve() if row["raw_path"] else Path()
    if not path.is_file():
        # raw_path can contain the host path while the same database is mounted
        # in Docker. Resolve the stable dataset URI against this runtime.
        filename = Path(row["source_uri"].removeprefix("dataset://")).name
        path = (settings.dataset_path / filename).resolve()
    if not path.is_file():
        raise HTTPException(404, "Local source file not found")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.name,
        content_disposition_type="inline",
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/documents/{document_id}", include_in_schema=False)
def report_page(document_id: int) -> FileResponse:
    return FileResponse(STATIC / "report.html")


@app.get("/reports/{document_id}", include_in_schema=False)
def legacy_report_page(document_id: int) -> FileResponse:
    return FileResponse(STATIC / "report.html")
