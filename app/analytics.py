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


def seed_analytics(conn: sqlite3.Connection) -> None:
    sources = {
        row["title"]: int(row["id"])
        for row in conn.execute(
            "SELECT MIN(id) AS id,title FROM documents WHERE title IN (?,?) GROUP BY title",
            ("Future of Jobs Report 2025", "In-depth Research on Youth NEET in Thailand"),
        )
    }
    source_sets = [
        ("Future of Jobs Report 2025", WEF_METRICS),
        ("In-depth Research on Youth NEET in Thailand", NEET_METRICS),
    ]
    for title, metrics in source_sets:
        document_id = sources.get(title)
        if not document_id:
            continue
        for metric in metrics:
            conn.execute(
                """INSERT INTO analytics_metrics(
                       chart_key,series,label,value,unit,period,scope,sort_order,source_document_id,source_page,note
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(chart_key,series,label,period,source_document_id) DO UPDATE SET
                       value=excluded.value,unit=excluded.unit,scope=excluded.scope,
                       sort_order=excluded.sort_order,source_page=excluded.source_page,note=excluded.note""",
                (*metric[:8], document_id, *metric[8:]),
            )
