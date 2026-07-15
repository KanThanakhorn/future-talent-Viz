# Prompt สำหรับ AI Agent: ปรับโครงสร้างเว็บเป็น Landing Page + หน้าเอกสารรายไฟล์

## บริบท (Context)
ระบบปัจจุบันมี dashboard เดียวรวม 7 กราฟจากทุกเอกสารปนกัน งานนี้คือ**ปรับโครงสร้างใหม่** ให้เป็น 2 ระดับ:
1. **Landing page** — รวม highlight เด่นจากทั้ง 6 เอกสาร
2. **หน้าเอกสารรายไฟล์ (6 หน้า)** — แต่ละหน้าแสดง viz ของ**ข้อมูลทั้งหมด**ที่มีอยู่ในเอกสารนั้น พร้อม sidebar สารบัญด้านซ้าย

ห้ามรื้อ backend/API เดิม (`/api/dashboard`, SQL schema, RAG pipeline) งานนี้เป็นการจัด layout/routing ฝั่ง frontend ใหม่ และอาจต้องเพิ่ม API endpoint ที่ query แยกตาม `document_id` เท่านั้น

---

## โครงสร้างเว็บใหม่

### 1. Landing Page (`/`)
แสดง **6 การ์ด** (1 การ์ด = 1 เอกสาร):
- Future of Jobs Report 2025 (WEF)
- In-depth Research on Youth NEET in Thailand (UNICEF)
- การพัฒนาทุนมนุษย์ในประเทศไทย (TDRI)
- การพัฒนาการศึกษาและกำลังคนด้าน STEM (TDRI)
- แนวโน้มความต้องการแรงงานในอุตสาหกรรมต่างๆ (TDRI)
- ข่าว NEET motivation (UNICEF press release)

แต่ละการ์ดแสดง:
- ชื่อเอกสาร + แหล่งที่มา
- **ตัวเลข/สถิติที่น่าสนใจที่สุด 1-2 จุดจากเอกสารนั้น** (ไม่ใช่ทุกตัวเลข — เลือกที่ impact สูงสุดหรือน่าตกใจที่สุด เช่น WEF → "170 ล้านตำแหน่งงานใหม่ภายในปี 2030", NEET → "จังหวัด Nong Bua Lam Phu มี NEET rate สูงสุด 33.5%")
- ปุ่ม/คลิกทั้งการ์ด → ไปหน้าเอกสารเต็มของไฟล์นั้น

**กติกาเลือก highlight:** ต้องดึงจากตัวเลขที่มีอยู่จริงใน `analytics_metrics`/`job_demand` ของเอกสารนั้นเท่านั้น ห้ามสร้างตัวเลขใหม่ ถ้าเอกสารไหนมีตัวเลขเชิงปริมาณน้อย (เช่นเอกสาร TDRI/UNICEF ที่เป็นบทความเชิงบรรยาย) ให้เลือก stat ที่มีอยู่จริงแม้จะเป็นแค่ 1 จุด ดีกว่าใส่ placeholder

### 2. หน้าเอกสารรายไฟล์ (`/documents/{document_id}`)
6 หน้า (1 หน้าต่อเอกสาร) โครงสร้างแต่ละหน้า:

**Layout:** sidebar ซ้าย (fixed/sticky) + เนื้อหาหลักฝั่งขวาเป็น single scrolling page (ไม่แบ่ง tab)

**Sidebar ซ้าย:**
- List หัวข้อย่อยของ viz ทั้งหมดในหน้านั้น (table of contents) เช่นสำหรับหน้า WEF: "Skills Growth", "Jobs Created/Displaced", "Macrotrends", "Technology Adoption", "Industry Breakdown", "Top Roles by Industry"
- แต่ละรายการเป็น anchor link กดแล้ว smooth-scroll ไปยัง section นั้นในหน้าเดียวกัน
- Highlight รายการที่กำลัง active ตามตำแหน่ง scroll ปัจจุบัน (scrollspy)

**เนื้อหาหลัก:** ต้องครอบคลุม**ข้อมูลทั้งหมด**ที่มีอยู่ในฐานข้อมูลของเอกสารนั้น แบ่งตามเอกสารดังนี้:

| เอกสาร (document_id) | Section ที่ต้องมี |
|---|---|
| WEF Future of Jobs (id=2) | Skills growing/declining, Jobs created/displaced/net, Macrotrends impact, Technology adoption, Industry-by-industry job outlook (จากตาราง job_demand ทั้ง 23 industries), Top roles per industry (จาก skill_requirements/job_demand ที่ผูกกับ industry) |
| NEET Thailand (id=1) | NEET rate by province/region, NEET 4 groups breakdown, NEET by gender/age/education attainment |
| TDRI human capital (id=3) | ทุก stat ที่ดึงได้จากเอกสาร (เช่น productivity potential %) แสดงเป็น stat card ถ้าไม่มีข้อมูลตารางเพียงพอสำหรับกราฟเชิงเปรียบเทียบ |
| TDRI STEM education (id=4) | ทุก stat ที่ดึงได้ แสดงเป็น stat card หรือกราฟตามความเหมาะสมของข้อมูล |
| TDRI labour demand (id=5) | ทุก stat ที่ดึงได้ แสดงเป็น stat card หรือกราฟตามความเหมาะสมของข้อมูล |
| UNICEF press release (id=6) | stat ที่ดึงได้ (เช่นสัดส่วนเยาวชนที่ขาดแรงจูงใจ) |

**สำคัญ:** เอกสาร id=3,4,5,6 เป็นบทความเชิงบรรยาย ไม่ใช่ตารางข้อมูล ถ้า agent ตรวจสอบแล้วพบว่ามีตัวเลขเชิงปริมาณน้อยหรือไม่มีเลย **ห้ามสร้างกราฟจากตัวเลขที่ไม่มีอยู่จริง** ให้แสดงเป็น text summary/quote card พร้อม citation แทน และระบุในหน้านั้นตรงๆ ว่า "เอกสารนี้เป็นเชิงคุณภาพ ข้อมูลเชิงปริมาณมีจำกัด" ความซื่อสัตย์กับข้อมูลสำคัญกว่าการมีกราฟให้ครบ

**ทุก viz/stat card ต้องมี:**
- ปุ่ม/tooltip อ้างอิงกลับ page number ของเอกสารต้นฉบับ (เชื่อมกับ `GET /api/documents/{id}/pages/{page}` ที่มีอยู่แล้ว)
- Query ตัวเลขจาก SQL โดยตรง ไม่ผ่าน RAG/LLM

---

## งานฝั่ง Backend ที่ต้องเพิ่ม (ถ้ายังไม่มี)
- Endpoint ใหม่ เช่น `GET /api/documents/{id}/full-data` ที่ join ข้อมูลทั้งหมดที่เกี่ยวกับ `document_id` นั้น (จาก `analytics_metrics`, `job_demand`, `skill_requirements` ที่ผูกกับ `source_document_id`) ส่งกลับเป็น JSON ก้อนเดียวให้หน้าเอกสารนั้นเรียกใช้ครั้งเดียว ไม่ต้องยิงหลาย request
- Endpoint สำหรับ landing page เช่น `GET /api/documents/highlights` ที่ส่งเฉพาะ top-N stat ต่อเอกสาร (กำหนด logic เลือก highlight ในโค้ด backend ไม่ hardcode ใน frontend เพื่อให้ปรับได้ง่าย)

## งานฝั่ง Frontend
- Route: `/` (landing) และ `/documents/:id` (6 หน้า)
- Sidebar component แบบ sticky + scrollspy (ใช้ Intersection Observer จับ section ที่มองเห็นอยู่)
- Responsive: บนจอเล็ก sidebar ควรยุบเป็นเมนู dropdown/hamburger แทนแสดงตลอด

## เกณฑ์ตรวจรับงาน (Acceptance Criteria)
1. Landing page มี 6 การ์ด ครบทุกเอกสาร แต่ละการ์ดมี highlight ที่ตรวจสอบย้อนกลับไปหลักฐานได้
2. แต่ละหน้าเอกสาร (6 หน้า) มี sidebar สารบัญที่ list section ครบตามตารางด้านบน และกดแล้ว scroll ไปถูกจุดจริง
3. ไม่มีตัวเลขใดในเว็บที่ไม่มี `source_document_id` + `source_page` อ้างอิงได้
4. เอกสารที่มีข้อมูลเชิงปริมาณน้อย (id 3,4,5,6) ต้องแสดงตามจริง ไม่ยัดกราฟที่ไม่มีข้อมูลรองรับ
