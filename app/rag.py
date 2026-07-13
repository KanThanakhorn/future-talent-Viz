from __future__ import annotations

import json
import urllib.request

from .config import settings


def _extractive_answer(question: str, contexts: list[dict]) -> str:
    if not contexts or contexts[0]["score"] <= 0:
        return "ไม่พบข้อมูลที่เกี่ยวข้องเพียงพอในเอกสารที่นำเข้าระบบ"
    excerpts = []
    for item in contexts[:3]:
        content = item["content"].strip()
        excerpts.append(content[:700] + ("…" if len(content) > 700 else ""))
    return "ข้อมูลที่เกี่ยวข้องจากเอกสาร:\n\n" + "\n\n".join(excerpts)


def answer(question: str, contexts: list[dict]) -> tuple[str, str]:
    if not settings.openai_api_key:
        return _extractive_answer(question, contexts), "extractive"
    source_blocks = []
    for index, item in enumerate(contexts, 1):
        page = item["page_start"]
        source_blocks.append(f"[{index}] {item['title']} หน้า {page}\n{item['content']}")
    prompt = f"""ตอบคำถามด้วยภาษาเดียวกับผู้ใช้ โดยใช้เฉพาะหลักฐานด้านล่างเท่านั้น
ใส่อ้างอิง [1], [2] หลังข้อความที่หลักฐานรองรับ หากหลักฐานไม่พอให้บอกตรงๆ
ห้ามคำนวณหรือแต่งตัวเลขใหม่; ตัวเลขต้องคงตามต้นฉบับ

คำถาม: {question}

หลักฐาน:
{chr(10).join(source_blocks)}"""
    payload = json.dumps({"model": settings.openai_model, "input": prompt}).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read())
        if result.get("output_text"):
            return result["output_text"], settings.openai_model
        parts = [part.get("text", "") for output in result.get("output", []) for part in output.get("content", [])]
        return "".join(parts).strip(), settings.openai_model
    except Exception:
        return _extractive_answer(question, contexts), "extractive-fallback"
