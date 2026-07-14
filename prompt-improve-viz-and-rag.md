# Prompt สำหรับ AI Agent: ปรับปรุง Visualization + RAG Retrieval

## บริบท (Context)
โปรเจกต์นี้มีระบบทำงานอยู่แล้ว (app/ingest.py, app/retrieval.py, app/rag.py) เก็บข้อมูลใน SQLite พร้อม schema ที่เตรียม FTS5 ไว้แต่ยังไม่ได้ใช้งานจริง และมี vector search แบบ local feature hashing 256 มิติ งานนี้คือการ "ปรับปรุงของเดิม" ไม่ใช่สร้างใหม่ ห้ามรื้อโครงสร้างเดิมที่ทำงานถูกต้องอยู่แล้ว (citation flow, การแยก numeric ออกจาก RAG, extractive/generative dual mode)

เอกสารต้นฉบับในระบบมี 2 กลุ่ม scope ต่างกัน:
- **WEF Future of Jobs Report 2025** — ข้อมูลระดับโลก ภาษาอังกฤษ
- **NEET Thailand (UNICEF)** — ข้อมูลเฉพาะไทย ภาษาอังกฤษ/ไทยปน
- ผู้ใช้ระบบถามเป็น**ภาษาไทย** เป็นหลัก

---

## หัวข้อที่ 1: เพิ่ม Visualization

### เป้าหมาย
สร้าง dashboard ที่เล่าเรื่อง "**demand vs readiness**" — เปรียบเทียบทักษะที่โลกต้องการ (จาก WEF) กับความพร้อมของเยาวชนไทย (จาก NEET) ไม่ใช่แค่โชว์กราฟแยกกันโดยไม่เชื่อมโยง

### รายการกราฟที่ต้องทำ

**A. จาก WEF Future of Jobs Report (global demand)**
1. Bar chart: Top fastest-growing vs fastest-declining skills (ดึงจาก section skills outlook)
2. Bar/waterfall chart: jobs created vs jobs displaced (มีตัวเลขในรายงาน เช่น structural transformation ~22% ของงานทั้งหมด, displacement จาก slower growth)
3. Heatmap หรือ horizontal bar: % ของ employer ที่บอกว่าแต่ละ macrotrend (AI, climate, cost of living ฯลฯ) จะ transform ธุรกิจของตนภายในปี 2030

**B. จาก NEET Thailand Research (local readiness)**
4. Map หรือ bar chart: NEET rate แยกตามภูมิภาค/จังหวัด (อ้างอิง chapter 2.2.3 Geographical location)
5. Stacked bar หรือ donut: สัดส่วนเยาวชน NEET แบ่งเป็น 4 กลุ่ม (อยากพัฒนาทักษะ+พร้อมทำงาน / อยากพัฒนาแต่ไม่พร้อม / ไม่อยากพัฒนาแต่พร้อม / ไม่อยากทั้งคู่)
6. Bar chart: NEET แยกตาม gender, age group, และ educational attainment

**C. กราฟเชื่อมสองฝั่ง (ไฮไลต์ของโปรเจกต์)**
7. Gap chart: เทียบทักษะที่ WEF ระบุว่าเป็นที่ต้องการสูง กับสัดส่วนเยาวชนไทยกลุ่มที่ "พร้อมพัฒนาทักษะ" (NEET group 1-2) — ถ้ามีข้อมูล curriculum/skills ที่สอนในระบบการศึกษาไทยเพิ่มเติม (เช่นจากเอกสาร STEM education) ให้ใส่เป็นชั้นเปรียบเทียบที่ 3 ด้วย

### ข้อกำหนดทางเทคนิค
- ทุกกราฟต้อง query ตัวเลขจากตาราง SQL โดยตรง (ไม่ผ่าน RAG/LLM) เพื่อป้องกันตัวเลขผิดเพี้ยน — คงหลักการเดิมของระบบไว้
- กราฟทุกอันต้องมีปุ่ม/tooltip ที่กดแล้วเห็นแหล่งอ้างอิง (document title + page number) ย้อนกลับไปยังต้นฉบับ
- Gap chart (ข้อ 7) ต้องระบุ label ชัดเจนว่าฝั่งไหนเป็นข้อมูล global (WEF) ฝั่งไหนเป็นข้อมูลไทย (NEET) ห้ามให้ผู้ดูเข้าใจผิดว่าเป็น dataset เดียวกัน
- ถ้าข้อมูลสำหรับกราฟ 7 ยังไม่ครบ (เช่นยังไม่ได้ fetch เอกสาร STEM education) ให้ทำ placeholder พร้อม comment ว่าต้องการ data source อะไรเพิ่ม แทนที่จะสร้างตัวเลขสมมุติขึ้นมาเอง

---

## หัวข้อที่ 2: ปรับปรุง RAG Retrieval

### เป้าหมาย
แก้จุดอ่อน 2 อย่างของระบบปัจจุบัน: (1) semantic understanding อ่อนเพราะใช้ feature hashing แทน embedding จริง (2) ค้นข้ามภาษาไม่ได้ (คำถามไทย vs เอกสารอังกฤษ)

### งานที่ต้องทำ เรียงตามลำดับความสำคัญ

**2.1 Hybrid retrieval: เปิดใช้ FTS5 (BM25) ร่วมกับ vector search**
- Schema มี FTS5 เตรียมไว้แล้วแต่ยังไม่ได้เชื่อมกับ scoring จริง ใน `app/retrieval.py` — ให้เพิ่ม BM25 query จาก FTS5 คู่กับ cosine similarity ที่มีอยู่
- รวมคะแนนสองฝั่งด้วย Reciprocal Rank Fusion (RRF) แทนการถ่วงน้ำหนัก manual เพราะ robust กว่าและไม่ต้อง tune ค่าคงที่บ่อย
- คงน้ำหนักพิเศษสำหรับเนื้อหาส่วนรายงานหลักเหนือ appendix ที่มีอยู่เดิมไว้

**2.2 เปลี่ยนจาก feature hashing → local multilingual embedding model**
- แทนที่ 256-dim feature hashing ด้วย embedding model ที่รันได้แบบ offline (เช่นตระกูล multilingual e5-small แบบ ONNX) เพื่อให้:
  - เข้าใจ semantic ได้จริง ไม่ใช่แค่ตรงคำ
  - ค้นข้ามภาษาได้ (คำถามไทย → เจอ chunk ภาษาอังกฤษที่ตรงความหมาย)
- ต้องคง constraint เดิมไว้: ระบบต้องทำงาน offline ได้เมื่อไม่มี OPENAI_API_KEY (extractive mode) — embedding model ที่เลือกต้อง run local ได้จริง ไม่ใช่เรียก API ภายนอก
- Re-index เอกสารเดิมทั้งหมดด้วย embedding ใหม่ (migration script แยก ไม่ทับ table เดิมจนกว่าจะ verify ผลลัพธ์)

**2.3 Re-ranking**
- หลังได้ top-k จาก hybrid search (ข้อ 2.1) เพิ่มขั้นตอน re-rank ด้วย cross-encoder ขนาดเล็กก่อนส่งเข้า `app/rag.py`
- เป้าหมาย: เพิ่มความแม่นยำของ chunk อันดับ 1-3 ที่จะถูกใช้สร้างคำตอบ/แสดง citation

**2.4 แยกประเภท chunk: narrative vs chart-derived data**
- ใน `app/ingest.py` ตอนบันทึก chunk ให้เพิ่ม field `source_type` แยก `narrative` (ข้อความปกติ) กับ `chart_ocr` (ตัวเลข/ข้อมูลที่มาจาก OCR กราฟ/infographic)
- ป้องกันไม่ให้ retrieval สับสนระหว่างข้อความบรรยายกับตัวเลขจากภาพ และทำให้ citation ชัดเจนขึ้นว่าเลขมาจากไหน

**2.5 สร้าง evaluation set**
- สร้างชุดคำถาม-คำตอบ+หน้าอ้างอิงที่รู้คำตอบล่วงหน้า 15-20 ข้อ คละจากทั้ง WEF และ NEET report (รวมคำถามภาษาไทยที่ต้องข้ามไปหาคำตอบในเอกสารอังกฤษ)
- ใช้วัด retrieval hit-rate ก่อน/หลังทำข้อ 2.1-2.4 เพื่อยืนยันว่าปรับปรุงจริง ไม่ใช่แค่คาดเดา
- เก็บผลไว้เป็นไฟล์ report สั้นๆ (ก่อน/หลัง) เพื่อใช้ประกอบการนำเสนอในงานแข่ง

### ข้อจำกัดที่ต้องรักษาไว้ (ห้ามเปลี่ยน)
- ตัวเลขในกราฟยังคง query จากตาราง SQL โดยตรง ไม่ผ่าน RAG
- โหมด extractive (ไม่มี OPENAI_API_KEY) ต้องทำงานได้เหมือนเดิม
- Citation format เดิม (title, page_start, page_end, score) ต้องคงไว้ แต่ปรับปรุงคุณภาพ score ให้สะท้อนความเกี่ยวข้องจริงมากขึ้น

## Deliverables
1. `app/retrieval.py` ที่มี hybrid (BM25 + vector) + RRF fusion + re-ranking
2. Embedding model ใหม่ + migration/re-index script
3. `app/ingest.py` ที่แยก `source_type`
4. Dashboard 7 กราฟตามหัวข้อที่ 1 พร้อม query ตรงจาก SQL
5. ไฟล์ evaluation set + ผลเปรียบเทียบก่อน/หลัง
