PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    source_uri TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    published_date TEXT,
    topic TEXT NOT NULL,
    document_type TEXT NOT NULL CHECK (document_type IN ('pdf', 'web')),
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ready',
    page_count INTEGER,
    raw_path TEXT,
    ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_pages (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER,
    section TEXT,
    content TEXT NOT NULL,
    extraction_method TEXT NOT NULL,
    confidence REAL,
    needs_review INTEGER NOT NULL DEFAULT 0,
    UNIQUE(document_id, page_number)
);

CREATE TABLE IF NOT EXISTS extraction_logs (
    id INTEGER PRIMARY KEY,
    source_uri TEXT NOT NULL,
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    page_number INTEGER,
    level TEXT NOT NULL,
    stage TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS industries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    source_document_id INTEGER REFERENCES documents(id),
    source_page INTEGER
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    source_document_id INTEGER REFERENCES documents(id),
    source_page INTEGER
);

CREATE TABLE IF NOT EXISTS job_demand (
    id INTEGER PRIMARY KEY,
    industry_id INTEGER NOT NULL REFERENCES industries(id),
    job_role TEXT NOT NULL,
    headcount_needed INTEGER,
    demand_value REAL,
    demand_unit TEXT,
    year_start INTEGER NOT NULL,
    year_end INTEGER NOT NULL,
    metric_type TEXT NOT NULL DEFAULT 'demand',
    source_document_id INTEGER NOT NULL REFERENCES documents(id),
    source_page INTEGER,
    note TEXT,
    UNIQUE(industry_id, job_role, year_start, year_end, source_document_id)
);

CREATE TABLE IF NOT EXISTS skill_requirements (
    job_demand_id INTEGER NOT NULL REFERENCES job_demand(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id),
    importance_level REAL NOT NULL CHECK (importance_level BETWEEN 0 AND 100),
    source_document_id INTEGER NOT NULL REFERENCES documents(id),
    source_page INTEGER NOT NULL,
    evidence_scope TEXT NOT NULL DEFAULT 'industry',
    PRIMARY KEY(job_demand_id, skill_id)
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_start INTEGER,
    page_end INTEGER,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding TEXT NOT NULL,
    embedding_model TEXT NOT NULL DEFAULT 'local-hash-v1',
    source_type TEXT NOT NULL DEFAULT 'narrative' CHECK (source_type IN ('narrative', 'chart_ocr')),
    UNIQUE(document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS embedding_indexes (
    model TEXT PRIMARY KEY,
    dimension INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('building', 'ready', 'failed')),
    chunk_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activated_at TEXT
);

CREATE TABLE IF NOT EXISTS chunk_embeddings_v2 (
    chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    model TEXT NOT NULL REFERENCES embedding_indexes(model) ON DELETE CASCADE,
    embedding TEXT NOT NULL,
    PRIMARY KEY(chunk_id, model)
);

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_metrics (
    id INTEGER PRIMARY KEY,
    chart_key TEXT NOT NULL,
    series TEXT NOT NULL,
    label TEXT NOT NULL,
    value REAL,
    unit TEXT NOT NULL,
    period TEXT,
    scope TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    source_document_id INTEGER NOT NULL REFERENCES documents(id),
    source_page INTEGER NOT NULL,
    note TEXT,
    UNIQUE(chart_key, series, label, period, source_document_id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
    content,
    content='chunks',
    content_rowid='id',
    tokenize='unicode61'
);

CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunk_fts(rowid, content) VALUES (new.id, new.content);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunk_fts(chunk_fts, rowid, content) VALUES ('delete', old.id, old.content);
END;
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunk_fts(chunk_fts, rowid, content) VALUES ('delete', old.id, old.content);
    INSERT INTO chunk_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE INDEX IF NOT EXISTS idx_pages_document ON document_pages(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON chunk_embeddings_v2(model);
CREATE INDEX IF NOT EXISTS idx_analytics_chart ON analytics_metrics(chart_key, sort_order);
CREATE INDEX IF NOT EXISTS idx_job_demand_year ON job_demand(year_start, year_end);
CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_title_source ON documents(title, source);
