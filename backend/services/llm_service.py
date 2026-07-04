import json
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

_openai_available = True
try:
    from openai import OpenAI
except Exception:
    _openai_available = False


def _get_client(config=None):
    """Get an OpenAI client, preferring user config over env defaults.

    Args:
        config: Optional dict with {api_key, base_url, model} from user settings

    Returns:
        (client, model_name) tuple, or (None, None) if no API key available
    """
    api_key = ''
    base_url = LLM_BASE_URL
    model = LLM_MODEL

    # User config takes priority
    if config:
        api_key = config.get('api_key', api_key)
        base_url = config.get('base_url', base_url)
        model = config.get('model', model)

    # Fall back to env
    if not api_key:
        api_key = LLM_API_KEY

    if not api_key:
        return None, None

    if not _openai_available:
        return None, None

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        return client, model
    except Exception:
        return None, None

SYSTEM_PROMPT = """你是一位专业的AI医疗导诊助手。你的任务是：
1. 通过多轮对话采集患者的症状信息，包括：主要症状、持续时间、严重程度、伴随症状、既往病史、过敏史、用药情况。
2. 每次回复要简洁专业，追问1-2个关键问题，不要一次性问太多。
3. 如果用户描述的症状包含急危重症迹象（如剧烈胸痛、严重呼吸困难、大出血等），请立即建议前往急诊。
4. 在对话结尾（采集到足够信息后），请总结已采集的症状信息，格式为：
【症状总结】
- 主要症状：xxx
- 持续时间：xxx
- 严重程度：xxx
- 伴随症状：xxx
- 既往病史：xxx
- 过敏史：xxx

重要提示：你提供的是导诊参考建议，不能替代专业医生的诊断。"""

MOCK_RESPONSES = [
    "您好！我是AI医疗导诊助手。为了更好地帮助您，请告诉我您目前最主要的不适症状是什么？持续了多长时间？",
    "感谢您的描述。能否再详细说明一下：症状的严重程度如何？（轻微/中等/严重）是否还有其他伴随症状？",
    "了解了。请问您是否有相关的既往病史？比如高血压、糖尿病等慢性病？另外，您对什么药物或食物过敏吗？",
    "您最近是否服用过什么药物？症状在什么情况下会加重或缓解？",
    "好的，我已经收集到了足够的信息。\n\n【症状总结】\n- 主要症状：根据您的描述总结\n- 持续时间：已记录\n- 严重程度：已记录\n- 伴随症状：已记录\n- 既往病史：已记录\n- 过敏史：已记录\n\n基于以上信息，建议您前往相关科室就诊。您可以在系统中查看科室推荐结果。\n\n⚠️ 温馨提示：以上导诊建议仅供参考，如有不适请及时就医，急重症请立即前往急诊科。"
]

def chat(user_message, history=None, config=None):
    """Send a message to the LLM and get a response.

    Args:
        user_message: The user's message text
        history: List of previous messages [{"role":"user","content":"..."}, ...]
        config: Optional dict with {api_key, base_url, model} from user settings

    Returns:
        Assistant's response text
    """
    client, model = _get_client(config)

    if client is None:
        return _mock_chat(user_message, history)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM API error: {e}")
        return _mock_chat(user_message, history)


def chat_stream(user_message, history=None, config=None):
    """Streaming version: yields response chunks (str) from LLM or mock.

    Usage:
        for chunk in chat_stream(msg, hist):
            yield chunk  # forward to SSE client

    Yields:
        str chunks of the assistant response (one "word" at a time for mock,
        raw delta.content tokens for real API).
    """
    import time

    client, model = _get_client(config)

    # ---- Mock streaming: chunk the mock response ----
    if client is None:
        full = _mock_chat(user_message, history)
        # Simulate typing — yield 3-8 characters per chunk with ~30ms delay
        pos = 0
        while pos < len(full):
            chunk_size = 5 + (pos * 7) % 4  # 5-8 chars, deterministic variance
            chunk = full[pos:pos + chunk_size]
            pos += chunk_size
            yield chunk
            time.sleep(0.03)
        return

    # ---- Real API streaming ----
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
    except Exception as e:
        print(f"LLM stream error: {e}")
        # Fallback to mock on error
        full = _mock_chat(user_message, history)
        pos = 0
        while pos < len(full):
            chunk_size = 5 + (pos * 7) % 4
            chunk = full[pos:pos + chunk_size]
            pos += chunk_size
            yield chunk
            time.sleep(0.03)


def _mock_chat(user_message, history=None):
    """Mock LLM responses for demo without API key."""
    import random

    # Count conversation turns
    turn = len(history) if history else 0

    # Detect if the message contains emergency symptoms
    emergency_keywords = ["剧烈胸痛", "呼吸困难", "大出血", "昏迷", "严重外伤", "中风", "心脏病", "心梗"]
    is_emergency = any(kw in user_message for kw in emergency_keywords)

    if is_emergency:
        return ("⚠️ 根据您的描述，可能存在急危重症情况！请立即前往医院急诊科就诊，或拨打120急救电话！\n\n"
                "在等待急救期间，请保持镇定，尽量平卧休息。\n\n"
                "【症状总结】\n- 紧急症状：已识别急危重症信号\n- 建议：立即急诊")

    # Return appropriate mock response based on conversation stage
    if turn < 2:
        return MOCK_RESPONSES[turn] if turn < len(MOCK_RESPONSES) else MOCK_RESPONSES[1]
    elif turn < 5:
        # Summarize with user's input keywords
        return ("好的，我已经收集到了足够的信息。\n\n"
                "【症状总结】\n"
                f"- 主要症状：{user_message[:30]}...\n"
                "- 持续时间：已记录\n"
                "- 严重程度：已记录\n"
                "- 伴随症状：已记录\n"
                "- 既往病史：已记录\n"
                "- 过敏史：已记录\n\n"
                "基于以上信息，建议您前往相关科室就诊。请点击下方「科室推荐」查看推荐结果。\n\n"
                "⚠️ 温馨提示：以上导诊建议仅供参考，如有不适请及时就医，急重症请立即前往急诊科。")
    else:
        return ("问诊已基本完成。如果您还有其他症状需要补充，请告诉我；否则可以查看科室推荐结果。\n\n"
                "⚠️ 温馨提示：以上导诊建议仅供参考，如有不适请及时就医。")


def interpret_report(report_text, indicators=None, config=None):
    """Interpret a medical report using LLM.

    Args:
        report_text: Raw text extracted from the report
        indicators: List of indicator dicts
        config: Optional dict with {api_key, base_url, model}

    Returns:
        (interpretation_text, advice_text, indicators)
    """
    client, model = _get_client(config)

    if client is None:
        return _mock_interpret(report_text, indicators)

    prompt = f"""请对以下医疗检查报告进行专业解读：

报告内容：
{report_text}

请完成以下任务：
1. 对异常指标进行标注和解释（标注偏高/偏低及可能原因）
2. 给出综合健康评估
3. 提供就医和生活方式建议

请用通俗易懂的语言回复，格式如下：
【报告解读】
（各项指标分析）

【综合评估】
（整体健康评估）

【建议】
（就医建议和生活建议）

⚠️ 重要提示：本解读仅供参考，具体诊断请咨询专业医生。"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000
        )
        content = response.choices[0].message.content
        # Split interpretation and advice
        if "【建议】" in content:
            parts = content.split("【建议】")
            interpretation = parts[0].strip()
            advice = "【建议】" + parts[1].strip() if len(parts) > 1 else ""
            return interpretation, advice
        return content, ""
    except Exception as e:
        print(f"LLM API error: {e}")
        return _mock_interpret(report_text, indicators)


def _mock_interpret(report_text, indicators=None):
    """Mock report interpretation for demo."""
    if indicators is None:
        # Simulate parsing common indicators
        indicators = [
            {"name": "白细胞(WBC)", "value": "6.5", "unit": "10⁹/L", "range": "3.5-9.5", "status": "正常"},
            {"name": "红细胞(RBC)", "value": "4.8", "unit": "10¹²/L", "range": "4.3-5.8", "status": "正常"},
            {"name": "血红蛋白(Hb)", "value": "145", "unit": "g/L", "range": "130-175", "status": "正常"},
            {"name": "血小板(PLT)", "value": "180", "unit": "10⁹/L", "range": "125-350", "status": "正常"},
            {"name": "血糖(GLU)", "value": "6.8", "unit": "mmol/L", "range": "3.9-6.1", "status": "偏高"},
            {"name": "总胆固醇(TC)", "value": "5.6", "unit": "mmol/L", "range": "3.1-5.2", "status": "偏高"},
        ]

    # Build interpretation
    interpretation_parts = ["【报告解读】"]
    for ind in indicators:
        status_tag = ""
        if ind.get("status") == "偏高":
            status_tag = " ⚠️ 偏高"
        elif ind.get("status") == "偏低":
            status_tag = " ⚠️ 偏低"
        else:
            status_tag = " ✓ 正常"
        interpretation_parts.append(
            f"- {ind['name']}：{ind['value']} {ind.get('unit','')} "
            f"（参考范围：{ind.get('range','')}）{status_tag}"
        )

    interpretation = "\n".join(interpretation_parts)

    advice = (
        "【综合评估】\n"
        "根据报告数据显示，血糖和总胆固醇指标略高于正常参考范围，其他指标均在正常范围内。"
        "这可能与近期饮食、生活作息相关，建议引起重视但不必过度担心。\n\n"
        "【建议】\n"
        "1. 建议进一步检查糖化血红蛋白(HbA1c)以评估近期血糖控制情况\n"
        "2. 控制饮食：减少高糖、高脂肪食物摄入，增加蔬菜水果比例\n"
        "3. 加强运动：每周进行至少150分钟中等强度有氧运动\n"
        "4. 定期复查：1-3个月后复查血糖和血脂\n"
        "5. 若复查结果持续异常，建议咨询内分泌科医生\n\n"
        "⚠️ 重要提示：本解读仅供参考，具体诊断和治疗方案请咨询专业医生。"
    )

    return interpretation, advice, indicators
