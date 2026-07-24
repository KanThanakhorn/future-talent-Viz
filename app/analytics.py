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


def _rows(chart, series, labels, values, unit, period, scope, page, note=None):
    """Build page-cited metric tuples from a transcribed figure or table."""
    return [(chart, series, label, value, unit, period, scope, order, page, note)
            for order, (label, value) in enumerate(zip(labels, values), 1)]


STEM_METRICS += (
    _rows("stem_pisa_2018", "คณิตศาสตร์", ["ไทย", "OECD"], [419, 489], "score", "2018", "International", 80)
    + _rows("stem_pisa_2018", "วิทยาศาสตร์", ["ไทย", "OECD"], [426, 489], "score", "2018", "International", 80)
    + _rows("stem_school_leavers", "ม.3", ["2561", "2562", "2563", "2564"], [491069, 497975, 478565, 485737], "students", None, "OBEC", 179)
    + _rows("stem_school_leavers", "ม.6", ["2561", "2562", "2563", "2564"], [274135, 277854, 278821, 286831], "students", None, "OBEC", 179)
    + _rows("stem_vocational_students", "ปวช.", ["อุตสาหกรรม", "พาณิชยกรรม/บริหารธุรกิจ", "ท่องเที่ยว", "เกษตรกรรม", "คหกรรม", "ศิลปกรรม", "ICT", "ประมง", "พาณิชยนาวี", "สิ่งทอ", "บันเทิงและดนตรี"], [340132, 218865, 24374, 23094, 14323, 15402, 11941, 361, 0, 163, 159], "students", "2565", "Thailand", 196)
    + _rows("stem_vocational_students", "ปวส.", ["อุตสาหกรรม", "พาณิชยกรรม/บริหารธุรกิจ", "ท่องเที่ยว", "เกษตรกรรม", "คหกรรม", "ศิลปกรรม", "ICT", "ประมง", "พาณิชยนาวี", "สิ่งทอ", "บันเทิงและดนตรี"], [167490, 139194, 8682, 8623, 7033, 4042, 7286, 1230, 494, 59, 44], "students", "2565", "Thailand", 196)
    + _rows("stem_vocational_budget", "งบ สอศ.", ["2561", "2562", "2563", "2564", "2565"], [26464790300, 26907041800, 25944008100, 24737086200, 23082395900], "baht", None, "Thailand", 211)
)

HUMAN_CAPITAL_METRICS = [
    ("human_capital_training", "ได้รับการฝึกอบรม", "ประชากรอายุ 15–59 ปี", 2.26, "% population", "2021 Q1", "Thailand", 1, 38, None),
    ("human_capital_training", "ได้รับการฝึกอบรม", "กำลังแรงงาน", 2.66, "% workforce", "2021 Q1", "Thailand", 2, 38, None),
    ("human_capital_training", "ต้องการการฝึกอบรม", "ประชากรอายุ 15–59 ปี", 11.21, "% population", "2021 Q1", "Thailand", 3, 38, None),
    ("human_capital_training", "ต้องการการฝึกอบรม", "กำลังแรงงาน", 11.65, "% workforce", "2021 Q1", "Thailand", 4, 38, None),
]

# Values embedded in figures are included only where the PDF text layer keeps
# an unambiguous label/value pairing. PDF page numbers are used for citations.
HUMAN_CAPITAL_METRICS += (
    _rows("hc_stunting_trend", "ภาวะเตี้ยแคระแกร็น", [str(y) for y in range(2559, 2568)], [10.91, 8.91, 10.95, 10.26, 10.75, 10.89, 12.55, 12.64, 12.86], "% children 0–5", None, "Thailand", 12)
    + _rows("hc_wasting_trend", "ภาวะผอมแห้ง", [str(y) for y in range(2559, 2568)], [6.2, 5.64, 6.02, 6.73, 5.83, 5.73, 6.76, 7.36, 6.18], "% children 0–5", None, "Thailand", 12)
    + _rows("hc_overweight_trend", "ภาวะน้ำหนักเกิน", [str(y) for y in range(2559, 2568)], [3.54, 3.18, 9.17, 11.45, 9.5, 9.05, 10.24, 9.12, 9.29], "% children 0–5", None, "Thailand", 13)
    + _rows("hc_ecdi", "เพศ", ["รวม", "ชาย", "หญิง"], [77.8, 75.2, 81.0], "% children 24–59 months", "MICS 2022", "Thailand", 14)
    + _rows("hc_ecdi", "ภูมิภาค", ["กรุงเทพมหานคร", "ภาคกลาง", "ภาคเหนือ", "ภาคตะวันออกเฉียงเหนือ", "ภาคใต้"], [85.3, 80.4, 73.3, 74.2, 81.9], "% children 24–59 months", "MICS 2022", "Thailand", 14)
    + _rows("hc_ecdi", "ควินไทล์ฐานะ", ["Q1", "Q2", "Q3", "Q4", "Q5"], [72.0, 75.4, 79.2, 80.7, 83.5], "% children 24–59 months", "MICS 2022", "Thailand", 14)
    + _rows("hc_ecdi", "เข้าเรียนปฐมวัย", ["เข้าเรียน", "ไม่เข้าเรียน"], [81.0, 66.7], "% children 24–59 months", "MICS 2022", "Thailand", 14)
    + _rows("hc_ecdi", "การศึกษามารดา", ["ก่อนประถม", "ประถม", "ม.ต้น", "ม.ปลาย", "อุดมศึกษา"], [54.2, 74.7, 77.6, 79.0, 84.2], "% children 24–59 months", "MICS 2022", "Thailand", 14)
    + _rows("hc_ecdi", "ภาษาในครัวเรือน", ["ภาษาไทย", "ภาษาอื่น"], [78.0, 76.4], "% children 24–59 months", "MICS 2022", "Thailand", 14)
    + _rows("hc_foundational_skills", "อ่าน", ["นอกระบบ", "ป.1", "ป.2", "ป.3", "ป.4", "ป.5", "ป.6", "ม.1", "ม.2", "ม.3"], [62.5, 16.0, 41.8, 60.3, 73.8, 80.8, 81.2, 88.3, 91.2, 91.2], "% children", "MICS 2022", "Thailand", 18)
    + _rows("hc_foundational_skills", "คำนวณ", ["นอกระบบ", "ป.1", "ป.2", "ป.3", "ป.4", "ป.5", "ป.6", "ม.1", "ม.2", "ม.3"], [70.2, 22.9, 41.7, 56.7, 62.2, 70.7, 75.1, 88.2, 89.2, 85.2], "% children", "MICS 2022", "Thailand", 18)
    + _rows("hc_reading_equity", "อ่าน", ["รวม", "หญิง", "ชาย", "กรุงเทพฯ", "ภาคกลาง", "ภาคเหนือ", "อีสาน", "ภาคใต้", "Q1", "Q2", "Q3", "Q4", "Q5", "ภาษาอื่น", "ภาษาไทย", "ชนบท", "เมือง"], [71.3, 74.6, 68.1, 80.5, 75.3, 73.9, 68.4, 63.0, 59.9, 69.6, 73.3, 76.7, 78.7, 52.3, 72.9, 69.2, 74.1], "% children", "MICS 2022", "Thailand", 18)
    + _rows("hc_numeracy_equity", "คำนวณ", ["รวม", "หญิง", "ชาย", "กรุงเทพฯ", "ภาคกลาง", "ภาคเหนือ", "อีสาน", "ภาคใต้", "Q1", "Q2", "Q3", "Q4", "Q5", "ภาษาอื่น", "ภาษาไทย", "ชนบท", "เมือง"], [65.0, 66.3, 63.6, 74.8, 73.7, 61.3, 61.5, 56.0, 54.44, 60.0, 68.0, 69.8, 74.8, 40.9, 67.0, 62.9, 67.7], "% children", "MICS 2022", "Thailand", 19)
    + _rows("hc_pisa_country", "OECD 2565", ["วิทยาศาสตร์", "อ่าน", "คณิตศาสตร์"], [485, 476, 472], "score", "2565", "OECD", 20)
    + _rows("hc_pisa_country", "ไทย 2565", ["วิทยาศาสตร์", "อ่าน", "คณิตศาสตร์"], [409, 379, 394], "score", "2565", "Thailand", 20)
    + _rows("hc_pisa_country", "OECD 2561", ["วิทยาศาสตร์", "อ่าน", "คณิตศาสตร์"], [489, 487, 489], "score", "2561", "OECD", 20)
    + _rows("hc_pisa_country", "ไทย 2561", ["วิทยาศาสตร์", "อ่าน", "คณิตศาสตร์"], [426, 393, 419], "score", "2561", "Thailand", 20)
    + sum((_rows("hc_pisa_school_quartile", subject, ["Q1", "Q2", "Q3", "Q4"], values, "score", "2022", "Thailand", 20) for subject, values in [("คณิตศาสตร์", [368.53, 377.71, 403.65, 486.32]), ("อ่าน", [347.0, 364.8, 395.48, 466.36]), ("วิทยาศาสตร์", [377.82, 394.57, 424.8, 501.52])]), [])
    + _rows("hc_upper_secondary_completion", "เปรียบเทียบ", ["ไทย", "เฉลี่ย OECD"], [59.4, 86.2], "% age 25–34", None, "International", 24)
)

# Intentionally not seeded from the summary PDF: target lines in figures 2.1–
# 2.3, the complete 39-country ranking in 4.1, dropout/mismatch series in
# chapters 4–5, training outcome series in 6.4, and NEET breakdowns in chapter
# 7. Their values are drawn as image glyphs or overlap in the text layer, so an
# automated transcription cannot pair every number with its category safely.
# The UI therefore omits those requested charts instead of guessing values.
# Likewise, the STEM curriculum/ISCED/quality-assurance tables are definitions,
# not quantitative observations, and are intentionally not charted.

UNICEF_PRESS_METRICS = [
    ("neet_press_release", "Motivation", "Youth NEET who lack motivation to develop skills or work", 68, "% youth NEET", "2023", "Thailand", 1, 1, "UNICEF press release, 22 March 2023"),
    ("neet_press_release", "Scale", "Youth aged 15–24 who are NEET", 15, "% youth", "2023", "Thailand", 2, 1, "Approximately 1.4 million young people"),
    ("neet_press_release", "Gender", "Youth NEET who are female", 70, "% youth NEET", "2023", "Thailand", 3, 1, "Reported as about 70 per cent"),
]

# Static editorial copy: rendered directly from SQL, never generated by RAG.
# Tuple: document title, section key, type, title, body, order, PDF page.
EDITORIAL_NOTES = [
    ("Future of Jobs Report 2025", "section-industries", "context", "ขอบเขตของข้อมูล", "เป็นมุมมองของนายจ้างทั่วโลกต่อการเปลี่ยนแปลงช่วงปี 2025–2030 ไม่ใช่ประมาณการตลาดแรงงานไทย", 1, 98),
    ("Future of Jobs Report 2025", "section-roles", "caution", "อ่านค่า role และ skill แยกกัน", "อาชีพที่เติบโตเร็วที่สุดไม่จำเป็นต้องสร้างตำแหน่งงานใหม่มากที่สุด และสัญญาณทักษะในตารางนี้วัดในระดับอุตสาหกรรม ไม่ได้ผูกกับตำแหน่งงานโดยตรง", 1, 39),
    ("Future of Jobs Report 2025", "section-skill_change", "definition", "ความหมายของ net increase", "ค่าบวกและค่าลบสะท้อนสัดส่วนนายจ้างที่คาดว่าการใช้ทักษะจะเพิ่มหรือลด ไม่ใช่คะแนนความสามารถของแรงงาน", 1, 37),
    ("In-depth Research on Youth NEET in Thailand", "section-neet_groups", "definition", "NEET 4 กลุ่ม", "รายงานจำแนกเยาวชนตามความต้องการพัฒนาทักษะและความพร้อมเข้าสู่กิจกรรมการศึกษา การฝึกอบรม หรือการทำงาน โดยไม่รวม NEET ชั่วคราวในฐานคำนวณนี้", 1, 45),
    ("In-depth Research on Youth NEET in Thailand", "section-neet_groups", "caution", "ค่าที่รายงานไม่ตรงกัน", "เซลล์ในตารางรวมได้ 99.9% จากการปัดเศษ และกลุ่มที่ 4 ระบุ 68.2% ขณะที่ข้อความบรรยายระบุ 69.2% หน้านี้จึงยึดค่าจากตาราง", 2, 45),
    ("In-depth Research on Youth NEET in Thailand", "section-neet_demographics", "context", "เหตุผลที่ต้องอ่านร่วมกับบริบท", "ภาระดูแลครอบครัว การแต่งงานและมีบุตรตั้งแต่อายุน้อย เป็นปัจจัยสำคัญที่รายงานใช้ประกอบการอธิบายความแตกต่างระหว่างเพศ", 1, 39),
    ("In-depth Research on Youth NEET in Thailand", "section-neet_provinces", "caution", "ค่าระดับจังหวัด", "การเปรียบเทียบจังหวัดควรคำนึงถึงขนาดตัวอย่างและความไม่แน่นอน ไม่ควรตีความอันดับเป็นความแตกต่างเชิงสาเหตุ", 1, 41),
    ("การพัฒนาทุนมนุษย์ในประเทศไทย : การศึกษาช่องว่าง อุปสรรค และทางเลือกเชิงนโยบาย", "section-hc_stunting_trend", "context", "ภาวะทุพโภชนาการมีหลายรูปแบบ", "รายงานพบ stunting 12.86%, wasting 6.18% และ overweight 9.29% ในข้อมูลล่าสุด โดยรูปแบบความเสี่ยงแตกต่างตามรายได้และภูมิภาค", 1, 11),
    ("การพัฒนาทุนมนุษย์ในประเทศไทย : การศึกษาช่องว่าง อุปสรรค และทางเลือกเชิงนโยบาย", "section-hc_ecdi", "definition", "ECDI 2030 คืออะไร", "ดัชนีประเมินเด็กอายุ 24–59 เดือนด้านสุขภาพ การเรียนรู้ และสุขภาวะทางจิตสังคม ความแตกต่างระหว่างกลุ่มเป็นความสัมพันธ์ ไม่ใช่ข้อพิสูจน์เชิงสาเหตุ", 1, 13),
    ("การพัฒนาทุนมนุษย์ในประเทศไทย : การศึกษาช่องว่าง อุปสรรค และทางเลือกเชิงนโยบาย", "section-hc_foundational_skills", "definition", "ฐานการประเมิน", "ทักษะการอ่านและคำนวณในกราฟประเมินตามความคาดหวังระดับชั้นประถมศึกษาปีที่ 2 ในกลุ่มเด็กอายุ 7–14 ปี", 1, 18),
    ("การพัฒนาทุนมนุษย์ในประเทศไทย : การศึกษาช่องว่าง อุปสรรค และทางเลือกเชิงนโยบาย", "section-hc_reading_equity", "finding", "ช่องว่างที่เด่นชัด", "เด็กจากครัวเรือนยากจนที่สุด เด็กที่ใช้ภาษาอื่นในครัวเรือน และเด็กในชนบทมีสัดส่วนทักษะอ่านพื้นฐานต่ำกว่ากลุ่มเปรียบเทียบ", 1, 18),
    ("การพัฒนาทุนมนุษย์ในประเทศไทย : การศึกษาช่องว่าง อุปสรรค และทางเลือกเชิงนโยบาย", "section-hc_numeracy_equity", "finding", "ภาษาในครัวเรือน", "กลุ่มที่ใช้ภาษาอื่นในครัวเรือนมีทักษะคำนวณพื้นฐาน 40.9% เทียบกับ 67.0% ในกลุ่มที่ใช้ภาษาไทย", 1, 19),
    ("การพัฒนาทุนมนุษย์ในประเทศไทย : การศึกษาช่องว่าง อุปสรรค และทางเลือกเชิงนโยบาย", "section-hc_pisa_country", "definition", "PISA วัดใคร", "PISA ประเมินสมรรถนะของนักเรียนอายุ 15 ปี ค่าที่แสดงจึงไม่ใช่ผลสัมฤทธิ์ของนักเรียนทุกระดับชั้น", 1, 20),
    ("การพัฒนาทุนมนุษย์ในประเทศไทย : การศึกษาช่องว่าง อุปสรรค และทางเลือกเชิงนโยบาย", "section-hc_pisa_school_quartile", "caution", "Q1–Q4 เป็นระดับโรงเรียน", "ควอร์ไทล์ในกราฟเป็นสถานะทางเศรษฐกิจและสังคมของโรงเรียนที่เข้าร่วม ไม่ใช่ควอร์ไทล์รายได้ของครอบครัวโดยตรง", 1, 20),
    ("การพัฒนาทุนมนุษย์ในประเทศไทย : การศึกษาช่องว่าง อุปสรรค และทางเลือกเชิงนโยบาย", "section-hc_upper_secondary_completion", "context", "ช่วงเปลี่ยนผ่านที่สำคัญ", "รายงานชี้ว่าเด็กหลุดจากระบบมากเป็นพิเศษในช่วง ม.ต้นไป ม.ปลาย และจาก ม.ปลายไปอุดมศึกษาหรือเทียบเท่า", 1, 24),
    ("การพัฒนาทุนมนุษย์ในประเทศไทย : การศึกษาช่องว่าง อุปสรรค และทางเลือกเชิงนโยบาย", "section-human_capital_training", "finding", "ความต้องการสูงกว่าการเข้าถึง", "สัดส่วนผู้ต้องการฝึกอบรมสูงกว่าสัดส่วนผู้ได้รับการฝึกอบรมหลายเท่า โดยข้อจำกัดสำคัญคือเวลา ต้นทุนค่าเสียโอกาส และแรงจูงใจ", 1, 38),
    ("การพัฒนาทุนมนุษย์ในประเทศไทย : การศึกษาช่องว่าง อุปสรรค และทางเลือกเชิงนโยบาย", "section-human_capital_training", "context", "วิกฤตทักษะพื้นฐาน", "ASAT 2565 พบผู้มีทักษะการอ่านต่ำกว่าเกณฑ์ 64.7% ทักษะดิจิทัลต่ำกว่าเกณฑ์ 74.1% และทักษะสังคมและอารมณ์ต่ำกว่าเกณฑ์ 30.3%", 2, 40),
    ("การพัฒนาการศึกษาและกำลังคนด้านวิทยาศาสตร์ เทคโนโลยี วิศวกรรมศาสตร์ และคณิตศาสตร์ ของประเทศไทย", "section-stem_pisa_2018", "context", "ชุดประเทศเปรียบเทียบ", "รายงานเลือกประเทศจากกลุ่มที่มีอันดับความสามารถในการแข่งขันสูง การเปรียบเทียบจึงไม่ใช่ตัวอย่างประเทศแบบสุ่ม", 1, 80),
    ("การพัฒนาการศึกษาและกำลังคนด้านวิทยาศาสตร์ เทคโนโลยี วิศวกรรมศาสตร์ และคณิตศาสตร์ ของประเทศไทย", "section-stem_school_leavers", "context", "เส้นทางหลังจบการศึกษา", "ข้อมูลต้นฉบับยังแยกผู้เรียนต่อสายสามัญ อาชีวศึกษา สถาบันอื่น ผู้ไปทำงาน และผู้ไม่เรียนต่อหรือทำงาน จึงไม่ควรอ่านจำนวนผู้จบเป็นจำนวนผู้เข้าสู่ตลาดแรงงาน", 1, 179),
    ("การพัฒนาการศึกษาและกำลังคนด้านวิทยาศาสตร์ เทคโนโลยี วิศวกรรมศาสตร์ และคณิตศาสตร์ ของประเทศไทย", "section-stem_vocational_students", "finding", "ผู้เรียนกระจุกตัวสองประเภทวิชา", "ประมาณ 87% ของนักเรียนอาชีวศึกษาอยู่ในประเภทอุตสาหกรรมและพาณิชยกรรม/บริหารธุรกิจ", 1, 196),
    ("การพัฒนาการศึกษาและกำลังคนด้านวิทยาศาสตร์ เทคโนโลยี วิศวกรรมศาสตร์ และคณิตศาสตร์ ของประเทศไทย", "section-stem_vocational_budget", "caution", "งบประมาณยังไม่ปรับเงินเฟ้อ", "ค่าที่แสดงเป็นเงินบาทตามราคาของแต่ละปี การลดลงเชิงตัวเงินจึงยังไม่สะท้อนการเปลี่ยนแปลงกำลังซื้อที่แท้จริง", 1, 211),
    ("แนวโน้มความต้องการแรงงานในอุตสาหกรรมต่างๆ และทักษะอาชีพที่แรงงานไทยควรต้องมี", "section-thai_job_postings", "caution", "ประกาศงานออนไลน์ไม่ใช่ตลาดแรงงานทั้งหมด", "JPA รวบรวมจาก 15 เว็บไซต์ งานนอกระบบ การรับสมัครผ่านเครือข่ายส่วนตัว และประกาศที่ซ้ำอาจไม่ถูกสะท้อนอย่างสมบูรณ์", 1, 8),
    ("Nearly 7 in 10 out-of-school or unemployed youth in Thailand lack the motivation to develop skills or seek work, a new UNICEF study finds", "section-neet_press_release", "definition", "เกือบ 7 ใน 10 หมายถึงใคร", "สถิตินี้กล่าวถึงเยาวชนที่อยู่ในสถานะ NEET ไม่ใช่เยาวชนไทยทั้งหมด บทความยังรายงานว่า NEET คิดเป็นราว 15% หรือประมาณ 1.4 ล้านคน และราว 70% เป็นหญิง", 1, 1),
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
    press = conn.execute(
        "SELECT MIN(id) AS id,title FROM documents WHERE title LIKE 'Nearly 7 in 10%'"
    ).fetchone()
    if press and press["id"] is not None:
        source_sets.append((press["title"], UNICEF_PRESS_METRICS))
        sources[press["title"]] = int(press["id"])
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
    for title, section_key, note_type, heading, body, order, page in EDITORIAL_NOTES:
        document_id = sources.get(title)
        if not document_id:
            row = conn.execute("SELECT MIN(id) id FROM documents WHERE title=?", (title,)).fetchone()
            document_id = int(row["id"]) if row and row["id"] is not None else None
        if document_id:
            conn.execute(
                """INSERT INTO editorial_notes(section_key,note_type,title,body,sort_order,source_document_id,source_page)
                   VALUES(?,?,?,?,?,?,?) ON CONFLICT(section_key,note_type,title,source_document_id)
                   DO UPDATE SET body=excluded.body,sort_order=excluded.sort_order,source_page=excluded.source_page""",
                (section_key, note_type, heading, body, order, document_id, page),
            )
