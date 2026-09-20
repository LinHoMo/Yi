# -*- coding: utf-8 -*-
"""T2: case_splits.json + 校正 classical_cases topic + 写入 HO holdout 真例。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
cases_path = ROOT / "data" / "cases" / "classical_cases.json"
splits_path = ROOT / "data" / "cases" / "case_splits.json"

data = json.loads(cases_path.read_text(encoding="utf-8"))
cases = data["cases"]
by_id = {c["id"]: c for c in cases}

# topic corrections for any remaining non-excluded that we keep in file for history
topic_fix = {
    "ZS012": "婚姻",
    "ZS003": "寻人",
    "ZS027": "寻人",
    "ZS028": "寻物",
    "ZS029": "婚姻",
}
for cid, topic in topic_fix.items():
    if cid in by_id:
        by_id[cid]["topic"] = topic

# Holdout 真例：来自 references/case_library.md，卦名/干支/断语以文档为准
holdout_cases = [
    {
        "id": "HO001",
        "source": "《黄金策·疾病章》/case_library 案例一",
        "topic": "疾病",
        "question": "辰月戊申日占父近病，乾为天之小畜",
        "hexagram": {"original": "乾", "changed": "小畜"},
        "input": {
            "date": "辰月戊申日寅卯旬空",
            "question": "父亲近病吉凶",
            "hexagram_name": "乾",
            "changed_name": "小畜",
            "notes": "用神父母多现取辰土临月建；忌神寅木冲空暗动克用；原神贪合待冲开",
        },
        "expected": {
            "verdict": "吉",
            "use_god": "父母",
            "use_god_branch": "辰",
            "key_points": ["用神多现", "忌神暗动", "旬空", "冲空", "原神", "冲中逢合"],
            "yingqi": "丑日",
            "detail": "病重但可愈，须待丑日冲开合局，果于丑日病愈",
        },
        "scoring": {"verdict_match": 0.3, "use_god_correct": 0.3, "key_pattern_identified": 0.25, "yingqi_correct": 0.15},
    },
    {
        "id": "HO002",
        "source": "《增删卜易·求财章》/case_library 案例五",
        "topic": "求财",
        "question": "寅月丙子日占投资经营求财，屯之节",
        "hexagram": {"original": "屯", "changed": "节"},
        "input": {
            "date": "寅月丙子日申酉旬空",
            "question": "投资经营财之得失",
            "hexagram_name": "屯",
            "changed_name": "节",
            "notes": "妻财伏藏，日辰冲飞神得出；兄弟持世；子孙化退",
        },
        "expected": {
            "verdict": "平吉",
            "use_god": "妻财",
            "use_god_branch": "巳",
            "key_points": ["伏藏", "伏神得出", "飞空得出", "兄弟持世", "旬空"],
            "yingqi": "戌月",
            "detail": "财可得但不多，防破耗；应期在冲开世爻之月",
        },
        "scoring": {"verdict_match": 0.3, "use_god_correct": 0.3, "key_pattern_identified": 0.25, "yingqi_correct": 0.15},
    },
    {
        "id": "HO003",
        "source": "《黄金策·出行章》/case_library 案例九",
        "topic": "行人",
        "question": "子月丙寅日占父出行何日归，解之豫",
        "hexagram": {"original": "解", "changed": "豫"},
        "input": {
            "date": "子月丙寅日戌亥旬空",
            "question": "父亲在外何日归来",
            "hexagram_name": "解",
            "changed_name": "豫",
            "notes": "父母两现取子水临月建；用神生世主迟归",
        },
        "expected": {
            "verdict": "吉",
            "use_god": "父母",
            "use_god_branch": "子",
            "key_points": ["用神生世", "迟归", "旬空"],
            "yingqi": "子日",
            "detail": "行人迟归，果于子日回",
        },
        "scoring": {"verdict_match": 0.3, "use_god_correct": 0.3, "key_pattern_identified": 0.25, "yingqi_correct": 0.15},
    },
    {
        "id": "HO004",
        "source": "《黄金策·婚姻章》/case_library 案例十（男测）",
        "topic": "婚姻",
        "question": "卯月丁亥日男占求婚，咸之萃",
        "hexagram": {"original": "咸", "changed": "萃"},
        "input": {
            "date": "卯月丁亥日午未旬空",
            "question": "男测婚姻成否",
            "hexagram_name": "咸",
            "changed_name": "萃",
            "notes": "妻财卯木临月建生世；世爻旬空；应爻兄弟主对方家阻力",
        },
        "expected": {
            "verdict": "吉",
            "use_god": "妻财",
            "use_god_branch": "卯",
            "key_points": ["用神临月建", "世爻旬空", "出空", "世应"],
            "yingqi": "巳午月",
            "detail": "可成，须待世爻出空",
        },
        "scoring": {"verdict_match": 0.3, "use_god_correct": 0.3, "key_pattern_identified": 0.25, "yingqi_correct": 0.15},
    },
    {
        "id": "HO005",
        "source": "《增删卜易·失物章》/case_library 案例十二",
        "topic": "失物",
        "question": "酉月丁丑日占失银能否找回，师之蒙",
        "hexagram": {"original": "师", "changed": "蒙"},
        "input": {
            "date": "酉月丁丑日申酉旬空",
            "question": "丢失银两能否找回",
            "hexagram_name": "师",
            "changed_name": "蒙",
            "notes": "妻财持世在内卦；用神休囚；世持财主自失非盗",
        },
        "expected": {
            "verdict": "吉",
            "use_god": "妻财",
            "use_god_branch": "午",
            "key_points": ["世持财", "内卦", "伏藏", "旬空"],
            "yingqi": "未日",
            "detail": "物未失在家内，未日厨下寻得",
        },
        "scoring": {"verdict_match": 0.3, "use_god_correct": 0.3, "key_pattern_identified": 0.25, "yingqi_correct": 0.15},
    },
    {
        "id": "HO006",
        "source": "《增删卜易·求财章》/case_library 案例十六",
        "topic": "求财",
        "question": "亥月甲寅日占投资经营，益之小畜",
        "hexagram": {"original": "益", "changed": "小畜"},
        "input": {
            "date": "亥月甲寅日子丑旬空",
            "question": "投资经营求财得失",
            "hexagram_name": "益",
            "changed_name": "小畜",
            "notes": "妻财子水旺；世持兄弟克财；子孙动而化退",
        },
        "expected": {
            "verdict": "平/不利",
            "use_god": "妻财",
            "use_god_branch": "子",
            "key_points": ["兄弟持世", "六合", "旬空", "化退神"],
            "yingqi": "年内",
            "detail": "求财辛苦多耗，经营三月所得甚微",
        },
        "scoring": {"verdict_match": 0.35, "use_god_correct": 0.25, "key_pattern_identified": 0.25, "yingqi_correct": 0.15},
    },
    {
        "id": "HO007",
        "source": "《黄金策·出行章》/case_library 案例十七",
        "topic": "出行",
        "question": "申月辛卯日占出国远行，泰之明夷",
        "hexagram": {"original": "泰", "changed": "明夷"},
        "input": {
            "date": "申月辛卯日午未旬空",
            "question": "出国出行吉凶顺否",
            "hexagram_name": "泰",
            "changed_name": "明夷",
            "notes": "世爻休囚日克；六合主动缓；变卦明夷有险",
        },
        "expected": {
            "verdict": "平吉",
            "use_god": "世爻",
            "use_god_branch": "辰",
            "key_points": ["六合", "世爻", "旬空", "月破"],
            "yingqi": "月余",
            "detail": "出行受阻延迟，最终可成，因故延迟月余",
        },
        "scoring": {"verdict_match": 0.3, "use_god_correct": 0.3, "key_pattern_identified": 0.25, "yingqi_correct": 0.15},
    },
]

# merge: avoid duplicate ids
existing_ids = {c["id"] for c in cases}
merged = []
for c in cases:
    merged.append(c)
for hc in holdout_cases:
    if hc["id"] in existing_ids:
        # replace
        for i, c in enumerate(merged):
            if c["id"] == hc["id"]:
                merged[i] = hc
                break
    else:
        merged.append(hc)

data["cases"] = merged
cases_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

splits = {
    "version": 1,
    "note": "tune=ZS001-020 调参集；holdout=未参与词典调参的古籍真例；excluded=残缺或与tune重复，不计入均分",
    "tune": [f"ZS{i:03d}" for i in range(1, 21)],
    "holdout": [c["id"] for c in holdout_cases],
    "excluded": [
        {"id": "ZS021", "reason": "无卦名，无法复原装卦"},
        {"id": "ZS022", "reason": "无卦名；topic 与 question 不符（近病）"},
        {"id": "ZS023", "reason": "无卦名；topic 与 question 不符（功名）"},
        {"id": "ZS024", "reason": "无卦名；topic 与 question 不符（赌钱）"},
        {"id": "ZS025", "reason": "无卦名；topic 与 question 不符（生意）"},
        {"id": "ZS026", "reason": "与 ZS008 同源（屯之震·师尊官事），不重复计入 holdout"},
        {"id": "ZS027", "reason": "与 ZS003 同源（革·仆归）但断语相反，基准矛盾，excluded"},
        {"id": "ZS028", "reason": "与 ZS011 同源（巽之讼·失银）"},
        {"id": "ZS029", "reason": "与 ZS012 同源（否·婚姻合处逢冲）"},
        {"id": "ZS030", "reason": "与 ZS014 同源（蹇·逃仆伏神）"},
    ],
    "holdout_policy": "禁止为单例新增仅对其命中的私有格局别名；通用古籍术语允许",
}

splits_path.write_text(json.dumps(splits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("cases", len(merged), "holdout", splits["holdout"])
print("wrote", cases_path)
print("wrote", splits_path)
