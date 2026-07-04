from models import Department
import json

# 症状同义词/口语表：把用户的口语说法归一到症状词库里的标准词。
# key 是标准词（需与 init_db.py 科室 symptoms 中的词一致），value 是常见口语/别名。
SYMPTOM_SYNONYMS = {
    "头痛": ["头疼", "脑袋疼", "脑袋痛", "头部疼痛", "偏头痛"],
    "头晕": ["晕", "犯晕", "头昏", "眩晕", "天旋地转"],
    "发烧": ["发热", "低烧", "高烧", "体温高", "发高烧"],
    "咳嗽": ["咳", "干咳", "老咳", "咳个不停"],
    "咳痰": ["有痰", "痰多"],
    "腹泻": ["拉肚子", "拉稀", "泻肚", "大便次数多", "腹泄"],
    "腹痛": ["肚子疼", "肚子痛", "小肚子疼", "腹部疼痛"],
    "胃痛": ["胃疼", "胃部疼痛", "上腹痛"],
    "恶心": ["想吐", "反胃", "犯恶心"],
    "呕吐": ["吐了", "干呕"],
    "便秘": ["便不出", "拉不出", "大便干燥", "排便困难"],
    "胸痛": ["胸口疼", "胸口痛", "心口疼", "胸部疼痛"],
    "胸闷": ["胸口闷", "喘不上气", "憋气", "气闷"],
    "心慌": ["心里发慌", "心跳乱", "心悸"],
    "气短": ["喘不过气", "呼吸急促", "上气不接下气"],
    "呼吸困难": ["喘不上来气", "呼吸费劲", "透不过气"],
    "失眠": ["睡不着", "睡不好", "入睡困难", "整夜睡不着"],
    "手脚麻木": ["手麻", "脚麻", "手脚发麻", "肢体麻木"],
    "皮肤痒": ["皮肤瘙痒", "身上痒", "浑身痒", "发痒"],
    "皮疹": ["起疹子", "长疹子", "红疹", "出疹"],
    "痘痘": ["痤疮", "长痘", "青春痘"],
    "眼痛": ["眼睛疼", "眼睛痛"],
    "视力模糊": ["看不清", "视物模糊", "眼花", "视力下降"],
    "耳鸣": ["耳朵响", "耳朵嗡嗡"],
    "耳痛": ["耳朵疼", "耳朵痛"],
    "鼻塞": ["鼻子不通", "鼻子堵", "堵鼻子"],
    "流涕": ["流鼻涕", "流清涕", "流鼻水"],
    "咽痛": ["嗓子疼", "喉咙痛", "喉咙疼", "咽喉痛"],
    "腰痛": ["腰疼", "腰部疼痛", "腰酸"],
    "关节痛": ["关节疼", "关节酸痛"],
    "膝盖痛": ["膝盖疼", "膝关节痛"],
    "痛经": ["例假肚子疼", "月经疼", "来大姨妈肚子疼"],
    "月经不调": ["例假不规律", "大姨妈紊乱", "月经紊乱"],
    "食欲不振": ["没胃口", "不想吃饭", "吃不下", "胃口差"],
}


def normalize_symptoms(symptom_text):
    """把用户文本里的口语同义词补充为症状词库中的标准词。

    遇到任一别名就把对应标准词追加到文本末尾（保留原文，只做增量），
    这样后续的关键词匹配就能命中标准词库，提升口语描述的召回率。

    Returns:
        (normalized_text, hits) —— 归一化后的文本，以及命中的标准词集合
    """
    text = symptom_text or ""
    hits = set()
    for standard, aliases in SYMPTOM_SYNONYMS.items():
        if standard in text or any(alias in text for alias in aliases):
            hits.add(standard)
    if hits:
        text = text + " " + " ".join(hits)
    return text, hits


def recommend_departments(symptom_text, top_n=3):
    """Recommend departments based on symptom text using keyword matching.

    Args:
        symptom_text: Combined text of all user-described symptoms
        top_n: Number of top departments to return

    Returns:
        List of (Department, score) tuples, sorted by score descending
    """
    # 先做同义词归一化，提升口语描述的召回率
    symptom_text, _ = normalize_symptoms(symptom_text)

    all_departments = Department.query.all()
    total_depts = max(1, len(all_departments))

    # ---- Build IDF weights ----
    # Rare symptoms (appearing in few depts) get higher weight — they are more
    # diagnostic.  Common symptoms (e.g. "发烧" appears in many depts) get lower
    # weight.  This fixes the old problem where depts with many keywords were
    # penalised with low match_percentage.
    from math import log
    keyword_dept_count = {}
    for dept in all_departments:
        for kw in dept.get_symptoms():
            keyword_dept_count[kw] = keyword_dept_count.get(kw, 0) + 1

    keyword_idf = {}
    for kw, count in keyword_dept_count.items():
        keyword_idf[kw] = log(total_depts / count) + 1  # +1 floors the weight at ~1

    # ---- Weighted scoring ----
    # Each matched keyword contributes [1 × IDF_weight] instead of a flat 1.
    scored = []
    for dept in all_departments:
        weighted = 0.0
        matched_keys = []
        for kw in dept.get_symptoms():
            if kw in symptom_text:
                w = keyword_idf.get(kw, 1.0)
                weighted += w
                matched_keys.append(kw)

        if weighted > 0:
            scored.append((dept, weighted, matched_keys))

    scored.sort(key=lambda x: x[1], reverse=True)

    # ---- Normalise percentage ----
    # Percentage is relative to the *top* scorer, so the first result is always
    # ~95% and others scale down proportionally.  This makes the number mean
    # "relevance relative to the best match", not "coverage of one dept's word
    # list" — so large depts are no longer penalised.
    top_weight = scored[0][1] if scored else 1.0

    results = []
    for dept, weight, matched_keys in scored[:top_n]:
        # Scale so the best match is ~95, others proportionally lower
        pct = int(round(weight / top_weight * 95))
        results.append({
            "department": dept.to_dict(),
            "match_score": round(weight, 1),
            "match_percentage": max(5, min(100, pct)),
            "matched_keywords": matched_keys,
        })

    return results


def extract_symptoms_from_conversation(messages):
    """Extract symptoms mentioned across a consultation conversation.

    Args:
        messages: List of message dicts [{"role":"user","content":"..."}, ...]

    Returns:
        Combined symptom description string
    """
    user_messages = [m["content"] for m in messages if m.get("role") == "user"]
    return " ".join(user_messages)
