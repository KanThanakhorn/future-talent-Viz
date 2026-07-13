from __future__ import annotations

import sqlite3

# Every value below was transcribed from the cited report page and is inserted
# only when that source document exists. Missing evidence stays missing.
WEF_METRICS = [
    ("skill_change", "Growing", "AI and big data", 87, "% net increase", "2025–2030", "Global", 1, 37, None),
    ("skill_change", "Growing", "Networks and cybersecurity", 70, "% net increase", "2025–2030", "Global", 2, 37, None),
    ("skill_change", "Growing", "Technological literacy", 68, "% net increase", "2025–2030", "Global", 3, 37, None),
    ("skill_change", "Growing", "Creative thinking", 66, "% net increase", "2025–2030", "Global", 4, 37, None),
    ("skill_change", "Growing", "Resilience, flexibility and agility", 66, "% net increase", "2025–2030", "Global", 5, 37, None),
    ("skill_change", "Declining", "Reading, writing and mathematics", -4, "% net increase", "2025–2030", "Global", 6, 37, None),
    ("skill_change", "Declining", "Manual dexterity, endurance and precision", -24, "% net increase", "2025–2030", "Global", 7, 37, None),
    ("macrotrends", "Macrotrend", "Broadening digital access", 60, "% employers", "by 2030", "Global", 1, 10, None),
    ("macrotrends", "Macrotrend", "Rising cost of living / inflation", 50, "% employers", "by 2030", "Global", 2, 10, None),
    ("macrotrends", "Macrotrend", "Reduce carbon emissions", 47, "% employers", "by 2030", "Global", 3, 10, None),
    ("macrotrends", "Macrotrend", "Labour and social issues", 46, "% employers", "by 2030", "Global", 4, 10, None),
    ("macrotrends", "Macrotrend", "Slower economic growth", 42, "% employers", "by 2030", "Global", 5, 10, None),
    ("macrotrends", "Macrotrend", "Adapt to climate change", 41, "% employers", "by 2030", "Global", 6, 10, None),
    ("macrotrends", "Technology", "AI and information processing", 86, "% employers", "2025–2030", "Global", 7, 11, None),
    ("macrotrends", "Technology", "Robots and autonomous systems", 58, "% employers", "2025–2030", "Global", 8, 11, None),
    ("macrotrends", "Technology", "Energy generation and storage", 41, "% employers", "2025–2030", "Global", 9, 11, None),
]

NEET_METRICS = [
    ("neet_provinces", "Northern", "Phetchabun", 18.8, "% youth NEET", "2020", "Thailand", 1, 41, None),
    ("neet_provinces", "Northern", "Uthai Thani", 18.6, "% youth NEET", "2020", "Thailand", 2, 41, None),
    ("neet_provinces", "Central", "Chainat", 20.9, "% youth NEET", "2020", "Thailand", 3, 41, None),
    ("neet_provinces", "Eastern", "Sa Kaeo", 21.5, "% youth NEET", "2020", "Thailand", 4, 41, None),
    ("neet_provinces", "Northeastern", "Nong Bua Lam Phu", 33.5, "% youth NEET", "2020", "Thailand", 5, 41, None),
    ("neet_provinces", "Northeastern", "Amnat Charoen", 25.9, "% youth NEET", "2020", "Thailand", 6, 41, None),
    ("neet_provinces", "Southern", "Narathiwat", 26.2, "% youth NEET", "2020", "Thailand", 7, 41, None),
    ("neet_provinces", "Southern", "Ranong", 21.7, "% youth NEET", "2020", "Thailand", 8, 41, None),
    ("neet_provinces", "Bangkok", "Bangkok", 8.1, "% youth NEET", "2020", "Thailand", 9, 41, None),
    ("neet_groups", "Want skills", "Group 1: want skills + ready", 6.9, "% classified NEET", "2021", "Thailand", 1, 45, "N=1,287,962; excludes temporary NEETs"),
    ("neet_groups", "Want skills", "Group 2: want skills + not ready", 11.9, "% classified NEET", "2021", "Thailand", 2, 45, "N=1,287,962; excludes temporary NEETs"),
    ("neet_groups", "Do not want skills", "Group 3: no skills + ready", 12.9, "% classified NEET", "2021", "Thailand", 3, 45, "N=1,287,962; excludes temporary NEETs"),
    ("neet_groups", "Do not want skills", "Group 4: no skills + not ready", 68.2, "% classified NEET", "2021", "Thailand", 4, 45, "Table cells sum to 99.9% due to rounding; narrative reports 69.2%, while table reports 68.2%"),
    ("neet_demographics", "Gender", "Male total", 11.8, "% youth NEET", "2020", "Thailand", 1, 38, None),
    ("neet_demographics", "Gender", "Female total", 18.5, "% youth NEET", "2020", "Thailand", 2, 39, None),
    ("neet_demographics", "Age", "Age 15–19", 9.2, "% youth NEET", "2020", "Thailand", 3, 38, None),
    ("neet_demographics", "Age", "Age 20–24", 20.5, "% youth NEET", "2020", "Thailand", 4, 38, None),
    ("neet_demographics", "Education", "Primary education", 19.9, "% youth NEET", "2021", "Thailand", 5, 43, None),
    ("neet_demographics", "Education", "Lower secondary", 32.1, "% youth NEET", "2021", "Thailand", 6, 43, None),
    ("neet_demographics", "Education", "Upper secondary (academic)", 20.9, "% youth NEET", "2021", "Thailand", 7, 43, None),
    ("readiness_gap", "Thai readiness", "NEET youth who want to develop skills", 18.9, "% classified NEET", "2021", "Thailand", 1, 45, "Aggregate readiness, not measured per skill"),
]

THAI_LABOUR_METRICS = [
    ("thai_job_postings", "Q1 2024", "Professional Sales", 14163, "positions", "2024 Q1", "Thailand online job postings", 1, 8, "TDRI-JPA; 15 job boards; not representative of all Thai hiring"),
    ("thai_job_postings", "Q1 2024", "Administrative Support", 12558, "positions", "2024 Q1", "Thailand online job postings", 2, 8, None),
    ("thai_job_postings", "Q1 2024", "Information Support and Services", 7013, "positions", "2024 Q1", "Thailand online job postings", 3, 8, None),
    ("thai_job_postings", "Q1 2024", "Engineering and Technology", 6858, "positions", "2024 Q1", "Thailand online job postings", 4, 8, None),
    ("thai_job_postings", "Q1 2024", "Marketing Management", 6154, "positions", "2024 Q1", "Thailand online job postings", 5, 8, None),
    ("thai_job_postings", "Q1 2024", "Operations Management", 5331, "positions", "2024 Q1", "Thailand online job postings", 6, 8, None),
]

STEM_METRICS = [
    ("stem_career_alignment", "STEM occupation", "ปวช.", 6, "% graduates", None, "Thailand", 1, 11, "Share of STEM graduates working in STEM occupations"),
    ("stem_career_alignment", "STEM occupation", "ปวส.", 9, "% graduates", None, "Thailand", 2, 11, None),
    ("stem_career_alignment", "STEM occupation", "ปริญญาตรี", 41, "% graduates", None, "Thailand", 3, 11, None),
    ("stem_career_alignment", "STEM occupation", "ปริญญาโทขึ้นไป", 62, "% graduates", None, "Thailand", 4, 11, None),
]

HUMAN_CAPITAL_METRICS = [
    ("human_capital_training", "ได้รับการฝึกอบรม", "ประชากรอายุ 15–59 ปี", 2.26, "% population", "2021 Q1", "Thailand", 1, 38, None),
    ("human_capital_training", "ได้รับการฝึกอบรม", "กำลังแรงงาน", 2.66, "% workforce", "2021 Q1", "Thailand", 2, 38, None),
    ("human_capital_training", "ต้องการการฝึกอบรม", "ประชากรอายุ 15–59 ปี", 11.21, "% population", "2021 Q1", "Thailand", 3, 38, None),
    ("human_capital_training", "ต้องการการฝึกอบรม", "กำลังแรงงาน", 11.65, "% workforce", "2021 Q1", "Thailand", 4, 38, None),
]


def seed_analytics(conn: sqlite3.Connection) -> None:
    titles = (
        "Future of Jobs Report 2025",
        "In-depth Research on Youth NEET in Thailand",
        "แนวโน้มความต้องการแรงงานในอุตสาหกรรมต่างๆ และทักษะอาชีพที่แรงงานไทยควรต้องมี",
        "การพัฒนาการศึกษาและกำลังคนด้านวิทยาศาสตร์ เทคโนโลยี วิศวกรรมศาสตร์ และคณิตศาสตร์ ของประเทศไทย",
        "การพัฒนาทุนมนุษย์ในประเทศไทย : การศึกษาช่องว่าง อุปสรรค และทางเลือกเชิงนโยบาย",
    )
    sources = {
        row["title"]: int(row["id"])
        for row in conn.execute(
            f"SELECT MIN(id) AS id,title FROM documents WHERE title IN ({','.join('?' for _ in titles)}) GROUP BY title",
            titles,
        )
    }
    source_sets = [
        ("Future of Jobs Report 2025", WEF_METRICS),
        ("In-depth Research on Youth NEET in Thailand", NEET_METRICS),
        (titles[2], THAI_LABOUR_METRICS),
        (titles[3], STEM_METRICS),
        (titles[4], HUMAN_CAPITAL_METRICS),
    ]
    for title, metrics in source_sets:
        document_id = sources.get(title)
        if not document_id:
            continue
        for metric in metrics:
            chart_key, series, label, value, unit, period, scope, sort_order, source_page, note = metric
            matches = conn.execute(
                """SELECT id FROM analytics_metrics WHERE chart_key=? AND series=? AND label=?
                   AND period IS ? AND source_document_id=? ORDER BY id""",
                (chart_key, series, label, period, document_id),
            ).fetchall()
            if matches:
                keep = int(matches[0]["id"])
                conn.execute(
                    """UPDATE analytics_metrics SET value=?,unit=?,scope=?,sort_order=?,source_page=?,note=?
                       WHERE id=?""",
                    (value, unit, scope, sort_order, source_page, note, keep),
                )
                if len(matches) > 1:
                    conn.executemany("DELETE FROM analytics_metrics WHERE id=?", [(row["id"],) for row in matches[1:]])
            else:
                conn.execute(
                    """INSERT INTO analytics_metrics(
                           chart_key,series,label,value,unit,period,scope,sort_order,
                           source_document_id,source_page,note
                       ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (chart_key, series, label, value, unit, period, scope, sort_order,
                     document_id, source_page, note),
                )
