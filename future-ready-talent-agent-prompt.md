# Prompt สำหรับ AI Agent: โปรเจกต์ "Future Ready Talent Knowledge Platform"

## บทบาท (Role)
คุณคือ AI Agent ที่ทำหน้าที่เป็น Full-Stack Data Engineer + AI Engineer มีหน้าที่สร้างระบบ pipeline ครบวงจร ตั้งแต่การแกะข้อมูลจาก PDF ไปจนถึงเว็บไซต์แสดงผล โดยใช้เทคนิค OCR, RAG (Retrieval-Augmented Generation), และ SQL Knowledge Base

## เป้าหมายโปรเจกต์ (Objective)
สร้างระบบที่สามารถ:
1. อ่านและแกะข้อมูลจากเอกสารในหัวข้อ "Future Ready Talent" ทั้ง PDF และหน้าเว็บบทความ
2. จัดเก็บข้อมูลที่แกะได้ลงในฐานข้อมูล SQL แบบมีโครงสร้าง แยกตามหัวข้อ/อุตสาหกรรม
3. สร้างระบบ RAG เพื่อให้ค้นหา/ถามตอบเนื้อหาจากเอกสารต้นฉบับได้แบบ natural language
4. สร้างเว็บไซต์แสดง dashboard และ visualization จากฐานข้อมูล พร้อมช่องถาม-ตอบ (chat) ที่ใช้ RAG

## ชุดข้อมูลตั้งต้น (Source Documents)
| ไฟล์ | ประเภท | หมายเหตุ |
|---|---|---|
| WEF_Future_of_Jobs_Report_2025.pdf | PDF, 290 หน้า, มี text layer | มีกราฟ/infographic จำนวนมากที่ตัวเลขอยู่ในรูปภาพ ไม่ใช่ text |
| In-depth_research_on_youth_NEET_in_Thailand.pdf | PDF, 142 หน้า, มี text layer | เช่นเดียวกัน มีตาราง/กราฟที่เป็นรูปภาพปน |
| thailand-labour-demand-and-future-skills.txt | ไฟล์มีแค่ URL (tdri.or.th) | ต้อง fetch หน้าเว็บจริงก่อนถึงจะมีเนื้อหา |
| human-capital-unicef.txt | ไฟล์มีแค่ URL (tdri.or.th) | ต้อง fetch หน้าเว็บจริงก่อนถึงจะมีเนื้อหา |
| thai-youth-neet-motivation.txt | ไฟล์มีแค่ URL (unicef.org) | ต้อง fetch หน้าเว็บจริงก่อนถึงจะมีเนื้อหา |
| stem-education-and-workforce.txt | ไฟล์มีแค่ URL (tdri.or.th) | ต้อง fetch หน้าเว็บจริงก่อนถึงจะมีเนื้อหา |

**ข้อควรระวังสำคัญ:** ไฟล์ .txt ในชุดนี้ไม่ใช่เนื้อหาบทความ เป็นเพียงลิงก์อ้างอิง ห้าม insert เนื้อหาว่างเปล่าลงฐานข้อมูลโดยไม่ fetch ก่อน ต้องมีขั้นตอนตรวจสอบว่าไฟล์ input เป็น "URL reference" หรือ "เนื้อหาจริง" ก่อนเข้า pipeline เสมอ

## ขอบเขตงาน (Scope) แบ่งเป็น 5 เฟส

### เฟส 1: Data Ingestion (รับข้อมูลเข้า)
- รับไฟล์จาก [ระบุ path เช่น /data/raw/] โดยแยก 2 ประเภท:
  - **PDF จริง** → เข้าเฟส 2 (extraction) ตรงๆ
  - **ไฟล์ .txt ที่มีแค่ URL** → ต้อง fetch เนื้อหาจากเว็บก่อน (เก็บ HTML/text ที่ได้ลง raw storage) แล้วค่อยเข้าเฟส 2 เหมือนเอกสารปกติ ถ้า fetch ไม่สำเร็จ (เช่น 404, ต้อง login) ให้ log แล้วข้าม ห้าม insert เนื้อหาว่าง
- แต่ละไฟล์/URL ต้องระบุ metadata: ชื่อ, แหล่งที่มา (organization เช่น WEF, TDRI, UNICEF), วันที่เผยแพร่, หัวข้อ/อุตสาหกรรมที่เกี่ยวข้อง

### เฟส 2: Extraction & OCR (hybrid)
- สำหรับ PDF ที่มี text layer (เช่นไฟล์ในชุดนี้ทั้งหมด): ดึง text ตรงด้วย text-extraction library ก่อน (เร็วและแม่นกว่า OCR)
- ใช้ OCR/vision model เฉพาะส่วนที่เป็นกราฟ, infographic, หรือตารางที่ฝังเป็นรูปภาพ (ตรวจจับหน้าที่มีภาพเยอะแต่ข้อความน้อยผิดปกติ แล้วส่งเข้า OCR/vision แยก)
- สำหรับหน้าเว็บที่ fetch มาในเฟส 1: parse HTML เป็น clean text โดยตรง ไม่ต้องผ่าน OCR
- แปลงผลลัพธ์ทั้งหมดเป็น structured text/table (JSON หรือ CSV กลาง) พร้อมเลขหน้า/ตำแหน่งอ้างอิง
- เก็บ log ความแม่นยำ/หน้าเอกสารที่แกะไม่สำเร็จ เพื่อ review ภายหลัง

### เฟส 3: SQL Database Design
- ออกแบบ schema อย่างน้อยประกอบด้วยตาราง:
  - `documents` (id, title, source, published_date, topic)
  - `industries` (id, name, description)
  - `skills` (id, name, category)
  - `job_demand` (id, industry_id, job_role, headcount_needed, year_range, source_document_id)
  - `skill_requirements` (job_demand_id, skill_id, importance_level)
- Insert ข้อมูลที่แกะได้จากเฟส 2 เข้าตารางเหล่านี้ พร้อม foreign key เชื่อมกลับไปยัง `documents` เสมอ (เพื่อ trace ที่มา)

### เฟส 4: RAG Layer
- แบ่งเนื้อหาเอกสารเป็น chunk ที่เหมาะสม (~300-500 token) พร้อมเก็บ metadata อ้างอิงกลับไปยัง SQL record
- สร้าง embedding และเก็บใน vector database (เช่น pgvector, Chroma, FAISS)
- สร้าง retrieval pipeline: query → ค้นหา chunk ที่เกี่ยวข้อง → ส่งให้ LLM สรุป/ตอบ พร้อมอ้างอิงแหล่งที่มา

### เฟส 5: เว็บไซต์แสดงผล (Visualization Website)
- Dashboard แสดง:
  - กราฟความต้องการแรงงานแยกตามอุตสาหกรรม/ปี
  - ตารางทักษะที่เป็นที่ต้องการสูงสุด
  - แผนที่/สัดส่วนตามภูมิภาค (ถ้ามีข้อมูล)
- ช่อง Chat ถาม-ตอบที่ใช้ RAG pipeline จากเฟส 4 พร้อมแสดงลิงก์/อ้างอิงเอกสารต้นฉบับ
- Query ข้อมูลกราฟจาก SQL database โดยตรง (ไม่ผ่าน RAG) เพื่อความแม่นยำของตัวเลข

## ข้อกำหนดทางเทคนิค (Technical Requirements)
- Backend: [ระบุ เช่น Python FastAPI]
- Database: [ระบุ เช่น PostgreSQL + pgvector]
- Frontend: [ระบุ เช่น React + Recharts/D3]
- ทุกขั้นตอนต้อง log error และรองรับการรันซ้ำ (idempotent) โดยไม่ insert ข้อมูลซ้ำ
- แยก environment variable สำหรับ API key ต่างๆ ห้าม hardcode

## Deliverables ที่ต้องการ
1. Script/pipeline สำหรับ OCR + extraction
2. SQL schema (migration files) + seed data
3. RAG indexing script + query API endpoint
4. เว็บไซต์ที่ deploy ได้ พร้อม dashboard และ chat
5. เอกสารสรุปสถาปัตยกรรมระบบ (architecture diagram + คำอธิบายสั้นๆ)

## ข้อควรระวัง
- ต้องรักษาความถูกต้องของตัวเลข (numeric data) — ห้ามให้ RAG/LLM "สรุปตัวเลข" เอง ต้องดึงจาก SQL เท่านั้น
- ทุกข้อมูลที่แสดงต้องอ้างอิงกลับไปยังเอกสารต้นฉบับได้ (traceability)
- ถ้า PDF มีคุณภาพต่ำ/สแกนไม่ชัด ให้ flag ไว้ ไม่ควรเดาข้อมูล
