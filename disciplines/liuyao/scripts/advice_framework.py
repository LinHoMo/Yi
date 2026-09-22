# -*- coding: utf-8 -*-
"""
趋避建议 — 从一开始就说人话，分类按问题关键词，不靠默认「事业」。
"""


ADVICE_RULES = {
    "投资": {
        "auspicious": [
            "可以顺着现在的势头推进，不必反复观望错过窗口",
            "投入节奏跟关键节点走，比一把梭更稳",
            "合作对象若与原神所主五行相近，往往更顺手",
        ],
        "neutral": [
            "先看清楚再进，急着下单容易接盘",
            "设好止损线，到线就执行，不靠感觉加仓",
            "小仓试水比满仓赌方向划算",
        ],
        "inauspicious": [
            "眼下不是加仓的时候，能不进就不进",
            "别碰自己看不懂、也和忌神所主方向纠缠太深的标的",
            "若已经持有，优先减风险而不是幻想翻盘",
        ],
    },
    "事业": {
        "auspicious": [
            "该争取的可以开口，顺推进比原地等更有用",
            "关键节点挑在用神得力的日子，成功率更高",
            "方向上可偏向原神所主的领域或城市",
        ],
        "neutral": [
            "先把本职做扎实，升迁调动再等一等",
            "人和比蛮干更要紧，少卷入口舌",
            "有想法先小步验证，别一上来就摊牌",
        ],
        "inauspicious": [
            "宜静不宜动，辞职跳槽这类大动作先缓",
            "提防小人与暗处的阻力，重要决定多留书面记录",
            "退一步有时比硬顶更保实力",
        ],
    },
    "婚姻": {
        "auspicious": [
            "缘分有推进空间，真诚表达比试探更好",
            "谈婚论嫁可挑双方都轻松、用神得力的时段",
            "日常多经营关系，别只在节点上用力",
        ],
        "neutral": [
            "好事多磨，给彼此一点时间反而更稳",
            "重要决定放到局势更明朗时再说",
            "有话当面讲清楚，少让猜忌发酵",
        ],
        "inauspicious": [
            "当下成算不高，硬定容易后面翻车",
            "若有长辈或现实阻力，先理清再谈感情",
            "双方都空有愿望却落不了地时，不如先冷静",
        ],
    },
    "出行": {
        "auspicious": [
            "出行整体顺，按计划走即可",
            "择用神得力的日子启程更省心",
            "行程留点弹性，顺的时候也别赶太死",
        ],
        "neutral": [
            "能走，但路上可能有小折腾，证件时间多核对",
            "结伴或告知行程更稳妥",
            "恶劣天气与疲劳驾驶能避则避",
        ],
        "inauspicious": [
            "今日或当下不宜远行，改期更合适",
            "若必须出行，安全冗余加倍，勿赶夜路逞强",
            "有些行程取消，反而少一场麻烦",
        ],
    },
    "疾病": {
        "auspicious": [
            "卦象偏松，仍要按医嘱治疗，不要自行停药",
            "静养与规范治疗比四处求偏方更重要",
            "可关注用神得力的那几日是否症状减轻",
        ],
        "neutral": [
            "病情平稳期，调护与复查不能省",
            "留意反复的诱因，作息饮食先稳住",
            "有变化及时复诊，别拖",
        ],
        "inauspicious": [
            "身体的事不能扛，尽快正规就医",
            "卦象偏紧时更要遵医嘱，勿讳疾忌医",
            "家人多分担，别让求测者独扛压力",
        ],
    },
    "失物": {
        "auspicious": [
            "有找回的可能，方向可偏向原神所主方位",
            "沿最近动过的路线、抽屉、包袋再细找一遍",
            "若涉及他人，可在对双方都方便时开口询问",
        ],
        "neutral": [
            "别急着定论「丢了」，再系统找一轮",
            "时间拖长变数增加，尽早动手",
            "贵重物品建议同步做好挂失或备案",
        ],
        "inauspicious": [
            "找回难度大，可同步准备补办或止损",
            "若疑被盗或遗失在公共场所，及时报警备案",
            "情绪上先接受「可能回不来」，反而省心",
        ],
    },
    "诉讼": {
        "auspicious": [
            "形势相对有利，但仍应以律师策略为准",
            "证据与时间线整理清楚，比情绪输出有用",
            "能调解结案的窗口值得认真评估",
        ],
        "neutral": [
            "宜和解或稳步推进，避免缠讼消耗",
            "程序节点记清楚，文书别延误",
            "对结果预期放现实一点",
        ],
        "inauspicious": [
            "形势不利，切勿硬扛，优先听专业律师意见",
            "避免激化矛盾，防止损失扩大",
            "能止损的方案，往往比「争一口气」更划算",
        ],
    },
    "胎产": {
        "auspicious": [
            "卦象偏安，仍按时产检，遵医嘱",
            "情绪稳定、休息充足对母婴都重要",
            "临产准备按医院流程来，不必额外焦虑",
        ],
        "neutral": [
            "孕期平稳，注意调护与产检节奏",
            "有异常症状立即联系医院",
            "家人多陪伴，减少劳顿",
        ],
        "inauspicious": [
            "以医院检查与医生判断为唯一依据",
            "卦象不能替代产检，切勿延误就医",
            "出现腹痛出血等情况立刻急诊",
        ],
    },
    "学业": {
        "auspicious": [
            "按计划复习应考，状态在线",
            "重要考试挑状态好的时段冲刺",
            "文书材料多检查一遍细节",
        ],
        "neutral": [
            "实力尚可，差的是节奏与心态",
            "薄弱环节优先补，别平均用力",
            "作息稳住，比熬夜刷题有效",
        ],
        "inauspicious": [
            "若准备不足，宜调整目标或延期再战",
            "临场易慌，先把可控项（睡眠、证件）管好",
            "一次失利不是终点，复盘比自责有用",
        ],
    },
}

# 问题关键词 → 建议类目（长词优先）
_CATEGORY_KEYWORDS = {
    "疾病": ["病", "疾", "愈", "康复", "医", "健康", "身弱", "症"],
    "婚姻": ["婚姻", "姻", "嫁", "娶", "感情", "恋爱", "缘", "合婚"],
    "失物": ["失物", "失银", "丢失", "找回", "遗失", "失", "盗"],
    "诉讼": ["官司", "讼", "诉讼", "法律", "官非", "师尊官"],
    "胎产": ["胎", "产", "孕", "怀孕", "生产"],
    "学业": ["考试", "学业", "文书", "领", "成绩", "升学"],
    "出行": ["出行", "出外", "旅行", "归", "回", "行人", "仆"],
    "投资": ["投资", "股", "生意", "买卖", "贸易", "经营", "融资", "价格", "价", "贵贱", "桑叶"],
    "事业": ["事业", "工作", "升职", "求官", "官职", "面试", "求职"],
}


def match_advice_category(question: str, fallback: str = "事业") -> str:
    q = str(question or "")
    if not q.strip():
        return fallback
    best_key = None
    best_len = 0
    for key, kws in _CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in q and len(kw) > best_len:
                best_key = key
                best_len = len(kw)
    if best_key:
        return best_key
    # 兜底：原始字典粗匹配
    for key in ADVICE_RULES:
        if key in q:
            return key
    if "财" in q:
        return "投资"
    if "婚" in q:
        return "婚姻"
    return fallback


def _bucket_of(verdict: str) -> str:
    v = str(verdict or "")
    if "凶" in v or "跌" in v:
        return "inauspicious"
    if "吉" in v and "凶" not in v:
        return "auspicious"
    return "neutral"


def generate_advice(verdict: str, category: str, result: dict) -> list:
    """按问题类型与断语，返回 3–4 条已经说人话的建议。"""
    bucket = _bucket_of(verdict)
    matched = match_advice_category(category)
    advice_list = list(ADVICE_RULES.get(matched, {}).get(bucket) or ADVICE_RULES["事业"][bucket])

    # 应期补一句，也用人话
    tc = result.get("thinking_chain", {}) if isinstance(result, dict) else {}
    s5 = tc.get("step5_synthesis", {}) if isinstance(tc, dict) else {}
    timing = s5.get("timing") or {}
    keys = []
    if isinstance(timing, dict):
        keys = timing.get("key_branches") or []
        plain = timing.get("plain_text") or timing.get("summary_text") or ""
    else:
        plain = ""
    if keys:
        advice_list = advice_list + [f"时机上可多留意 {'、'.join(keys[:4])} 这几日"]
    elif plain:
        short = str(plain)
        if len(short) > 40:
            short = short[:40] + "…"
        advice_list = advice_list + [short]

    return advice_list[:4]
