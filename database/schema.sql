-- Competition-specific optional structured data. Existing app tables remain authoritative.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT,
    organization TEXT,
    source_document_id INTEGER,
    source_page INTEGER
);

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    source_document_id INTEGER,
    source_page INTEGER
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    company_id INTEGER REFERENCES companies(id),
    budget REAL,
    currency TEXT,
    source_document_id INTEGER,
    source_page INTEGER
);

CREATE INDEX IF NOT EXISTS idx_people_name ON people(name);
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
