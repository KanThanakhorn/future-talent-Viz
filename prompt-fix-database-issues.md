# Prompt สำหรับ AI Agent: แก้ไขปัญหาข้อมูลใน future_ready_talent.db

## บริบท (Context)
ตรวจสอบ SQL dump (`future_ready_talent_full_dump.sql`) เทียบกับเอกสารต้นฉบับ (WEF Future of Jobs Report 2025, In-depth Research on Youth NEET in Thailand, และบทความ TDRI/UNICEF ที่ fetch จากเว็บ) แล้วพบว่า**ตัวเลขทุกจุดที่ตรวจสอบถูกต้องตรงกับต้นฉบับ 100%** (skill_change, macrotrends, technology trends, job_demand aggregate, neet_provinces, neet_groups) ปัญหาที่พบเป็นเรื่อง**โครงสร้างข้อมูลและความสมบูรณ์** ไม่ใช่ตัวเลขผิด งานนี้คือการแก้ 4 จุดต่อไปนี้ ห้ามแก้ตัวเลขที่ verify แล้วว่าถูกต้อง

---

## ปัญหาที่ 1: เอกสารซ้ำในตาราง `documents`

**อาการ:** id=1 กับ id=7 เป็นเอกสาร "In-depth Research on Youth NEET in Thailand" เอกสารเดียวกัน (142 หน้าเท่ากัน), id=2 กับ id=8 เป็น "Future of Jobs Report 2025" เอกสารเดียวกัน (290 หน้าเท่ากัน) ผลคือ `analytics_metrics` มี 74 แถว ซึ่งเท่ากับ 37 แถวจริง × 2 (ซ้ำสนิท), `chunks` และ `chunk_embeddings_v2` ก็ซ้ำเช่นกัน (165+165, 374+374)

**สิ่งที่ต้องทำ:**
1. เขียน migration script ที่:
   - เก็บ document_id คู่ไหนไว้อันเดียว (แนะนำเก็บ id ที่น้อยกว่า คือ 1 และ 2) แล้ว re-point foreign key ทั้งหมด (`analytics_metrics.source_document_id`, `chunks.document_id`, `document_pages.document_id`, `job_demand.source_document_id` ถ้ามี) ไปยัง id ที่เก็บไว้
   - ลบแถวที่ซ้ำสนิท (duplicate rows) ใน `analytics_metrics`, `chunks`, `chunk_embeddings_v2`, `document_pages` หลัง re-point แล้ว โดยเทียบ content ให้ตรงกันทุก field ก่อนลบ (กัน false positive)
   - ลบ document id 7 และ 8 ออกจากตาราง `documents`
2. เพิ่ม `UNIQUE` constraint หรือ application-level check บน `(title, source)` ใน `documents` เพื่อป้องกัน ingest pipeline สร้างเอกสารซ้ำอีกในอนาคต (root cause: ingest.py น่าจะถูกรันซ้ำโดยไม่ได้เช็คว่าเอกสารมีอยู่แล้ว)
3. หลังทำเสร็จ ตรวจว่า `SELECT COUNT(*) FROM analytics_metrics` = 37 (ไม่ใช่ 74)

---

## ปัญหาที่ 2: `skill_requirements` ว่างเปล่า (0 แถว) — บล็อก gap chart

**อาการ:** ตารางนี้ควรเชื่อม `job_demand` กับ `skills` (พร้อม `importance_level`) แต่ไม่มีข้อมูลเลย ทำให้ทำ gap chart (เทียบ skill demand ระดับโลกกับความพร้อมเยาวชนไทย) ไม่ได้

**สิ่งที่ต้องทำ:**
1. กลับไปอ่านเนื้อหา WEF report ในส่วนที่เชื่อมโยง skill กับ job role/industry (เช่น Figure 3.5 "industry-specific variations in skills" ที่กล่าวถึงในหน้า 38 เป็นต้นไป) และส่วนที่พูดถึง top fastest-growing/declining jobs พร้อม skill ที่เกี่ยวข้อง
2. Populate `skill_requirements` โดย insert แถวที่เชื่อม `job_demand.id` กับ `skills.id` พร้อมระบุ `importance_level` (เช่น high/medium/low หรือ 1-5) ตาม evidence จากรายงาน — **ห้ามเดา ทุกแถวต้องมี source_page อ้างอิงได้** (ถ้า schema ยังไม่มีคอลัมน์ source_page ในตารางนี้ ให้เพิ่ม)
3. ถ้าข้อมูลใน job_demand ปัจจุบัน (มีแค่ 3 แถว: created/displaced/net global aggregate) ไม่ละเอียดพอที่จะ map กับ skill ได้จริง ให้แก้ปัญหาที่ 3 ก่อน (เพิ่ม job_demand ระดับ industry) แล้วค่อยกลับมาทำข้อนี้

---

## ปัญหาที่ 3: `industries` มีแค่ 1 แถว, `job_demand` มีแค่ 3 แถว (global aggregate เท่านั้น)

**อาการ:** WEF report มีข้อมูลแยกตาม 22 industry clusters แต่ฐานข้อมูลตอนนี้มีแค่ industry เดียวคือ "Global labour market" และ job_demand มีแค่ 3 แถวรวมระดับโลก ไม่สะท้อนความละเอียดที่มีในต้นฉบับ

**สิ่งที่ต้องทำ:**
1. อ่าน WEF report ส่วน industry-specific breakdown (มักอยู่ในบท "Industry outlook" หรือ Chapter 4 ของรายงาน — ให้ agent เปิดหาส่วนที่มีตาราง/กราฟแยกตาม industry cluster)
2. Insert แถวใหม่ใน `industries` ตาม industry cluster ที่รายงานระบุจริง (ไม่ใช่สร้างหมวดเอาเอง)
3. Insert `job_demand` แยกตาม industry_id ที่เพิ่มใหม่ พร้อม `source_page` อ้างอิงทุกแถว
4. เก็บ industry "Global labour market" (id=1) ไว้เป็น aggregate level เดิม ไม่ต้องลบ แค่เพิ่มระดับ industry-specific เข้ามาเสริม

---

## ปัญหาที่ 4: เนื้อหาจากเว็บ TDRI (document id 3, 4, 5) มี HTML boilerplate ปนอยู่

**อาการ:** chunk ของเอกสาร TDRI มีเนื้อหาปนกับเมนูเว็บไซต์, ลิงก์ "อ่านเพิ่มเติม" ของบทความอื่น, ข้อความ cookie notice ซึ่งเป็น noise ที่ไม่เกี่ยวกับเนื้อหาจริง

**สิ่งที่ต้องทำ:**
1. แก้ส่วน HTML parsing ใน `app/ingest.py` (จุดที่ fetch เนื้อหาจาก URL reference) ให้ใช้ selector ที่เจาะจงเฉพาะ article body (เช่น class/id ของ content container ของเว็บ tdri.or.th) แทนการดึงทั้งหน้า
2. ตัดส่วนที่เป็น pattern ซ้ำๆ ออกอย่างชัดเจน เช่น "อ่านเพิ่มเติม", รายการบทความแนะนำท้ายหน้า, ข้อความเกี่ยวกับ cookie — เขียนเป็น cleanup rule ที่ apply กับทุกเอกสารจาก domain เดียวกัน ไม่ hardcode เฉพาะบทความเดียว
3. Re-fetch และ re-chunk เอกสาร id 3, 4, 5 (และเอกสารอื่นที่มาจาก URL fetch ในอนาคต) ด้วย parser ใหม่
4. ตรวจสอบว่า chunk size หลัง clean แล้วยังใกล้เคียง spec เดิม (~400 คำ ซ้อน 60 คำ) — ตอนนี้ doc 3/4/5 มีแค่ chunk เดียวต่อเอกสาร (700+ คำ) ซึ่งไม่ตรง spec ถ้า clean แล้วเนื้อหาสั้นลงจนพอดี 1 chunk ก็รับได้ แต่ถ้ายังยาวควรแบ่งตาม spec

---

## ลำดับการทำงาน (แนะนำ)
1. แก้ปัญหา 1 ก่อน (dedupe) เพราะกระทบทุกตารางที่เหลือ
2. แก้ปัญหา 4 (clean HTML) เพราะทำแยกอิสระได้ และควรทำก่อน re-index สำหรับ RAG
3. แก้ปัญหา 3 (industries/job_demand แยกตาม cluster) เพราะปัญหา 2 ต้องพึ่งข้อมูลนี้
4. แก้ปัญหา 2 (skill_requirements) เป็นลำดับสุดท้าย

## ข้อกำหนดร่วม
- ทุกแถวข้อมูลใหม่ที่ insert ต้องมี `source_document_id` และ `source_page` ที่ตรวจสอบย้อนกลับไปยัง PDF/เว็บต้นฉบับได้จริง ห้ามสร้างตัวเลขหรือ mapping ที่ไม่มีหลักฐานรองรับ
- หลังแก้แต่ละข้อ ให้รัน sanity check query (เช่น `SELECT COUNT(*)`, เช็ค foreign key ไม่ orphan) แล้วรายงานผลก่อน/หลัง
- backup ไฟล์ dump เดิมไว้ก่อนรัน migration ทุกครั้ง
