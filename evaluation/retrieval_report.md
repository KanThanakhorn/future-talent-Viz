# Retrieval evaluation report

Evaluation วันที่ 13 กรกฎาคม 2026 ใช้คำถามที่กำหนดคำตอบล่วงหน้า 18 ข้อจาก WEF Future of Jobs Report 2025 และ In-depth Research on Youth NEET in Thailand มีทั้งภาษาไทยและอังกฤษ

| Retrieval pipeline | Hit@3 | Hit rate |
|---|---:|---:|
| Before: local feature hashing | 5/18 | 27.78% |
| After: BM25 + multilingual vector + RRF + cross-encoder/RRF | 10/18 | 55.56% |

เกณฑ์ hit เข้มกว่าการตรงเอกสารอย่างเดียว: ผล top-3 ต้องตรงทั้งชื่อเอกสารและมีช่วงหน้าครอบคลุมหน้าที่กำหนดไว้ ค่า hit rate เพิ่มขึ้น 27.78 percentage points หรือ 2 เท่าจาก baseline

## Configuration

- Dense model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, ONNX, 384 dimensions
- Lexical retrieval: SQLite FTS5 BM25
- Fusion: Reciprocal Rank Fusion, `k=60`
- Reranker: `Xenova/ms-marco-MiniLM-L-6-v2`; รวมอันดับกับ RRF รอบสองเพื่อไม่ให้ English-only reranker ลบ multilingual recall
- Corpus: 545 chunks จากเอกสาร 6 แหล่ง

ผลรายข้อและหน้า top-3 อยู่ใน `retrieval_report.json` ชุดทดสอบยังชี้ว่าคำถามภาษาไทยเกี่ยวกับ WEF บางข้อไม่พบหน้าสรุปที่กำหนด จึงควรปรับ chunking ตาม section และเพิ่ม multilingual reranker ในรอบถัดไป โดยไม่เปลี่ยน expected pages เพื่อไล่ตามผลลัพธ์
