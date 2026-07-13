# Retrieval evaluation

ชุดทดสอบ 18 ข้อครอบคลุม WEF และ NEET ทั้งภาษาไทยและอังกฤษ แต่ละข้อระบุชื่อเอกสารและหน้าที่คาดหวังไว้ล่วงหน้า metric คือ `hit@3` โดยผลลัพธ์ต้องตรงทั้งเอกสารและช่วงหน้า

```bash
PYTHONPATH=.:.python-deps python3 -m app.reindex_embeddings
PYTHONPATH=.:.python-deps python3 evaluation/run_retrieval_eval.py
```

`retrieval_report.json` เปรียบเทียบ legacy feature hashing กับ BM25 + multilingual vector ผ่าน RRF และ cross-encoder reranking ผลลัพธ์ขึ้นกับ active embedding index ที่ผ่าน verification ในฐานข้อมูล
