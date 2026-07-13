# Future Ready Talent Knowledge Platform

แพลตฟอร์มข้อมูลแรงงานที่นำ PDF และ URL reference เข้าแบบ idempotent, เก็บข้อมูลที่ตรวจสอบย้อนกลับได้ใน SQL, ทำ hybrid retrieval และแสดง dashboard/chat ผ่านเว็บไซต์เดียวกัน

## เริ่มใช้งาน

ต้องมี Python 3.11+, `pdftotext` และ `pdftoppm` (แพ็กเกจ poppler-utils)

### Ubuntu/Debian ที่เปิด PEP 668

วิธีนี้ติดตั้ง dependency ไว้ใน `.python-deps` ภายในโปรเจกต์ ไม่แก้ system Python และไม่ต้องใช้ `--break-system-packages`:

```bash
./scripts/setup-local.sh
python3 -m app.ingest
./scripts/run-local.sh
```

### เครื่องที่สร้าง virtual environment ได้

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.ingest
uvicorn app.main:app --reload
```

ถ้า `python -m venv` แจ้งว่าไม่มี `ensurepip` สามารถใช้วิธี `.python-deps` ด้านบนได้ทันที หรือเลือกติดตั้งแพ็กเกจระบบ `python3-venv` ภายหลัง

เปิด `http://localhost:8000` และ API docs ที่ `http://localhost:8000/docs` หรือใช้ Docker:

```bash
docker compose build
docker compose run --rm app python -m app.ingest
docker compose up
```

การ ingest รอบถัดไปจะข้ามเอกสารที่ hash ไม่เปลี่ยน URL ที่ fetch ไม่สำเร็จหรือได้ข้อความสั้นผิดปกติจะถูก log และไม่สร้าง document ว่าง

## OCR และ RAG

Pipeline ใช้ text layer ก่อนและ flag หน้าที่ข้อความน้อยให้ review ใน `extraction_logs` หากติดตั้ง Tesseract พร้อมภาษาไทย/อังกฤษแล้วให้รัน:

```bash
python -m app.ocr
# จำกัดงานเพื่อ review ทีละชุด
python -m app.ocr --limit 20
```

OCR จะไม่ทับข้อความเดิม แต่ต่อเป็น supplement และ rebuild index เฉพาะเอกสารที่เปลี่ยน Retrieval ใช้ embedding แบบ feature hashing 256 มิติที่เก็บใน SQLite ร่วมกับ metadata ระดับหน้า จึงทำงาน offline ได้ หากตั้ง `OPENAI_API_KEY` chat จะให้โมเดลสังเคราะห์คำตอบจาก context ที่ค้นได้; ถ้าไม่ตั้ง ระบบคืน grounded extract โดยตรง

ตัวเลขบน dashboard query จาก `job_demand` ใน SQL เท่านั้น ไม่ผ่าน RAG ข้อมูล seed ที่ยืนยันแล้วระบุ `source_document_id` และ `source_page` ทุกแถว

## API หลัก

- `GET /api/dashboard` — ตัวเลขและทักษะจาก SQL
- `GET /api/documents` — แหล่งข้อมูลและสถานะ OCR review
- `GET /api/search?q=...` — retrieved chunks พร้อมหน้าและ score
- `POST /api/chat` — คำตอบพร้อม citations
- `GET /api/documents/{id}/pages/{page}` — หลักฐานระดับหน้า
- `GET /api/documents/{id}/source` — เปิด PDF ต้นฉบับที่นำเข้า
- `GET /api/health` — จำนวน documents/chunks

## Architecture

```mermaid
flowchart LR
    A[PDF files] --> B[Text layer extraction]
    U[TXT URL reference] --> V[Fetch + validate HTML]
    V --> C[Clean article text]
    B --> D{Low text density?}
    D -- yes --> O[OCR review queue]
    O --> T[Tesseract supplement]
    D -- no --> P[Page records]
    T --> P
    C --> P
    P --> S[(SQLite knowledge DB)]
    P --> K[300–500 word chunks]
    K --> E[Local vector embeddings]
    E --> S
    S --> Q[Hybrid retrieval]
    Q --> R[RAG answer + citations]
    S --> N[Numeric SQL queries]
    R --> W[FastAPI + Web UI]
    N --> W
```

รายละเอียด schema อยู่ใน `app/schema.sql`: `documents`, `document_pages`, `industries`, `skills`, `job_demand`, `skill_requirements`, `chunks`, `chunk_fts` และ `extraction_logs` SQLite เหมาะกับ demo/deployment ขนาดเล็ก; สำหรับหลาย worker สามารถย้าย repository layer ไป PostgreSQL + pgvector โดยคง provenance model เดิม

## ตรวจสอบ

```bash
python -m unittest discover -s tests -v
python -m compileall -q app
```
