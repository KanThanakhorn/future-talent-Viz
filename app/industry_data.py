"""Evidence-backed WEF 2025 industry outlook data.

Industry names are listed on report page 98. Role growth is from each two-page
industry profile (first page). Skill percentages are Figure 3.5, pages 39–40.
"""
from __future__ import annotations

import sqlite3


INDUSTRIES = [
    ("Accommodation, Food, and Leisure", 240, "AI and Machine Learning Specialists", 64),
    ("Advanced Manufacturing", 242, "AI and Machine Learning Specialists", 82),
    ("Agriculture, Forestry, and Fishing", 244, "AI and Machine Learning Specialists", 42),
    ("Automotive and Aerospace", 246, "Robotics Engineers", 65),
    ("Chemical and Advanced Materials", 248, "AI and Machine Learning Specialists", 52),
    ("Education and Training", 250, "AI and Machine Learning Specialists", 42),
    ("Electronics", 252, "AI and Machine Learning Specialists", 81),
    ("Energy Technology and Utilities", 254, "AI and Machine Learning Specialists", 46),
    ("Financial Services and Capital Markets", 256, "AI and Machine Learning Specialists", 228),
    ("Government and Public Sector", 258, "AI and Machine Learning Specialists", 179),
    ("Information and Technology Services", 260, "Software and Applications Developers", 132),
    ("Infrastructure", 262, "AI and Machine Learning Specialists", 50),
    ("Insurance and Pensions Management", 264, "AI and Machine Learning Specialists", 40),
    ("Medical and Healthcare Services", 266, "Data Analysts and Scientists", 50),
    ("Mining and Metals", 268, "AI and Machine Learning Specialists", 43),
    ("Oil and Gas", 270, "AI and Machine Learning Specialists", 81),
    ("Production of Consumer Goods", 272, "Business Development Professionals", 26),
    ("Professional Services", 274, "AI and Machine Learning Specialists", 61),
    ("Real Estate", 276, "AI and Machine Learning Specialists", 75),
    ("Retail and Wholesale of Consumer Goods", 278, "AI and Machine Learning Specialists", 44),
    ("Supply Chain and Transportation", 280, "Autonomous and Electric Vehicle Specialists", 53),
    ("Telecommunications", 282, "AI and Machine Learning Specialists", 65),
]

# Figure 3.5 reports the share of surveyed employers in an industry expecting
# increasing use of the skill by 2030. Short aliases keep the transcription
# readable; they are expanded to the official industry names below.
SKILL_EVIDENCE = {
    "AI and big data": (39, {"Automotive":100,"Telecommunications":100,"Professional":98,"IT":97,"Insurance":97,"Financial":95,"Supply":94,"Medical":92,"Energy":90,"Government":90}),
    "Networks and cybersecurity": (39, {"Financial":82,"Insurance":81,"Energy":79,"Medical":78,"Automotive":78,"Government":78,"Supply":76,"Telecommunications":75,"Advanced":74,"IT":74}),
    "Technological literacy": (39, {"Automotive":84,"Financial":84,"Medical":81,"Insurance":81,"Supply":77,"Education":76,"Oil":76,"Professional":75,"Advanced":73,"Consumer":72}),
    "Creative thinking": (39, {"Insurance":86,"Education":79,"Medical":76,"Advanced":76,"Telecommunications":75,"IT":75,"Real":73,"Professional":69,"Supply":69,"Consumer":69}),
    "Resilience, flexibility and agility": (39, {"Agriculture":83,"Telecommunications":79,"IT":78,"Consumer":73,"Insurance":72,"Automotive":71,"Advanced":71,"Retail":69,"Financial":68,"Electronics":68}),
    "Curiosity and lifelong learning": (39, {"Education":79,"Insurance":77,"Telecommunications":75,"Real":68,"IT":68,"Automotive":68,"Energy":67,"Retail":67,"Oil":64,"Medical":64}),
    "Leadership and social influence": (40, {"Automotive":71,"Telecommunications":69,"Education":68,"IT":67,"Medical":66,"Electronics":64,"Chemical":63,"Accommodation":63,"Energy":62,"Consumer":61}),
    "Talent management": (40, {"Infrastructure":70,"Automotive":68,"Mining":68,"Chemical":67,"Supply":65,"Telecommunications":64,"Consumer":63,"Oil":62,"Education":60,"Real":59}),
    "Analytical thinking": (40, {"Education":70,"Supply":70,"Automotive":68,"Telecommunications":67,"Consumer":65,"Insurance":61,"Advanced":61,"Financial":60,"Infrastructure":59,"Real":59}),
    "Environmental stewardship": (40, {"Oil":80,"Chemical":75,"Agriculture":71,"Automotive":70,"Mining":68,"Supply":68,"Infrastructure":67,"Consumer":66,"Professional":63,"Energy":60}),
}

ALIASES = {
    "Accommodation":"Accommodation, Food, and Leisure", "Advanced":"Advanced Manufacturing",
    "Agriculture":"Agriculture, Forestry, and Fishing", "Automotive":"Automotive and Aerospace",
    "Chemical":"Chemical and Advanced Materials", "Education":"Education and Training",
    "Electronics":"Electronics", "Energy":"Energy Technology and Utilities",
    "Financial":"Financial Services and Capital Markets", "Government":"Government and Public Sector",
    "IT":"Information and Technology Services", "Infrastructure":"Infrastructure",
    "Insurance":"Insurance and Pensions Management", "Medical":"Medical and Healthcare Services",
    "Mining":"Mining and Metals", "Oil":"Oil and Gas", "Consumer":"Production of Consumer Goods",
    "Professional":"Professional Services", "Real":"Real Estate",
    "Retail":"Retail and Wholesale of Consumer Goods", "Supply":"Supply Chain and Transportation",
    "Telecommunications":"Telecommunications",
}


def seed_industry_data(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT MIN(id) id FROM documents WHERE title='Future of Jobs Report 2025'").fetchone()
    if not row or row["id"] is None:
        return
    doc = int(row["id"])
    industry_ids: dict[str, int] = {}
    for name, page, role, growth in INDUSTRIES:
        conn.execute(
            """INSERT INTO industries(name,description,source_document_id,source_page) VALUES(?,?,?,98)
               ON CONFLICT(name) DO UPDATE SET description=excluded.description,
               source_document_id=excluded.source_document_id,source_page=excluded.source_page""",
            (name, "WEF Future of Jobs Report 2025 industry cluster", doc),
        )
        iid = int(conn.execute("SELECT id FROM industries WHERE name=?", (name,)).fetchone()["id"])
        industry_ids[name] = iid
        conn.execute(
            """INSERT INTO job_demand(industry_id,job_role,headcount_needed,demand_value,demand_unit,
               year_start,year_end,metric_type,source_document_id,source_page,note)
               VALUES(?,?,NULL,?,? ,2025,2030,'net-growth-percent',?,?,?)
               ON CONFLICT(industry_id,job_role,year_start,year_end,source_document_id) DO UPDATE SET
               demand_value=excluded.demand_value,demand_unit=excluded.demand_unit,
               source_page=excluded.source_page,note=excluded.note""",
            (iid, role, growth, "% net role growth", doc, page, "Industry profile jobs outlook"),
        )

    skills = {r["name"]: int(r["id"]) for r in conn.execute("SELECT id,name FROM skills")}
    for skill, (page, evidence) in SKILL_EVIDENCE.items():
        skill_id = skills.get(skill)
        if not skill_id:
            continue
        for alias, percent in evidence.items():
            name = ALIASES[alias]
            iid = industry_ids[name]
            context_role = "Industry workforce skill outlook"
            conn.execute(
                """INSERT INTO job_demand(industry_id,job_role,headcount_needed,demand_value,demand_unit,
                   year_start,year_end,metric_type,source_document_id,source_page,note)
                   VALUES(?,?,NULL,NULL,'% employers reporting increasing use',2025,2030,
                   'industry-skill-context',?,?,?) ON CONFLICT DO NOTHING""",
                (iid, context_role, doc, page, "Aggregate industry context for WEF Figure 3.5"),
            )
            job_id = int(conn.execute(
                "SELECT id FROM job_demand WHERE industry_id=? AND job_role=? AND source_document_id=?",
                (iid, context_role, doc),
            ).fetchone()["id"])
            conn.execute(
                """INSERT INTO skill_requirements(job_demand_id,skill_id,importance_level,
                   source_document_id,source_page,evidence_scope) VALUES(?,?,?,?,?,'industry')
                   ON CONFLICT(job_demand_id,skill_id) DO UPDATE SET importance_level=excluded.importance_level,
                   source_document_id=excluded.source_document_id,source_page=excluded.source_page,
                   evidence_scope=excluded.evidence_scope""",
                (job_id, skill_id, percent, doc, page),
            )
