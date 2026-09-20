# -*- coding: utf-8 -*-
"""optimize: 追加 holdout 真例 HO008–HO012 并更新 case_splits。"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "data" / "cases" / "classical_cases.json"
sp = ROOT / "data" / "cases" / "case_splits.json"
data = json.loads(p.read_text(encoding="utf-8"))
splits = json.loads(sp.read_text(encoding="utf-8"))

new_cases = [
    {
        "id": "HO008",
        "source": "《黄金策·功名章》/case_library 案例二",
        "topic": "事业",
        "question": "午月甲午日占升迁能否升职，鼎之既济",
        "hexagram": {"original": "鼎", "changed": "既济"},
        "input": {
            "date": "午月甲午日辰巳旬空",
            "question": "升官能否升职",
            "hexagram_name": "鼎",
            "changed_name": "既济",
            "notes": "官鬼旺于日月但原神妻财不动作；原神失位，旺极无源",
        },
        "expected": {
            "verdict": "凶",
            "use_god": "官鬼",
            "use_god_branch": "巳",
            "key_points": ["用神多现", "旬空", "原神", "月破", "暗动"],
            "yingqi": "年内",
            "detail": "官旺无源，升官无望反有丢官之虞；不久降职",
        },
        "scoring": {"verdict_match": 0.35, "use_god_correct": 0.25, "key_pattern_identified": 0.25, "yingqi_correct": 0.15},
        "benchmark_note": "核心法则：原神失位，用神虽旺亦凶",
    },
    {
        "id": "HO009",
        "source": "《黄金策·疾病章》/case_library 案例四",
        "topic": "疾病",
        "question": "未月癸亥日占久病半年吉凶，小畜之乾",
        "hexagram": {"original": "小畜", "changed": "乾"},
        "input": {
            "date": "未月癸亥日子丑旬空",
            "question": "久病半年日益沉重吉凶",
            "hexagram_name": "小畜",
            "changed_name": "乾",
            "notes": "久病以世为用；用神回头克；六合变六冲；久病逢冲即死",
        },
        "expected": {
            "verdict": "大凶",
            "use_god": "世爻",
            "use_god_branch": "子",
            "key_points": ["久病", "回头克", "六合", "六冲", "旬空", "月破"],
            "yingqi": "午日",
            "detail": "久病逢冲危笃，果于午日病故",
        },
        "scoring": {"verdict_match": 0.4, "use_god_correct": 0.2, "key_pattern_identified": 0.25, "yingqi_correct": 0.15},
        "benchmark_note": "对照近病逢冲即愈：久病逢冲为凶",
    },
    {
        "id": "HO010",
        "source": "《增删卜易·官非章》/case_library 案例十一",
        "topic": "官司",
        "question": "辰月甲寅日占被诬告官司，讼之否",
        "hexagram": {"original": "讼", "changed": "否"},
        "input": {
            "date": "辰月甲寅日子丑旬空",
            "question": "被人诬告官司吉凶",
            "hexagram_name": "讼",
            "changed_name": "否",
            "notes": "官鬼暗动；子孙化退抗官力弱；父母文书月破",
        },
        "expected": {
            "verdict": "凶",
            "use_god": "官鬼",
            "use_god_branch": "申",
            "key_points": ["暗动", "化退神", "月破", "六合", "旬空", "世爻"],
            "yingqi": "申日",
            "detail": "官司不利，官方已行动，申日被判罚",
        },
        "scoring": {"verdict_match": 0.3, "use_god_correct": 0.3, "key_pattern_identified": 0.25, "yingqi_correct": 0.15},
    },
    {
        "id": "HO011",
        "source": "《黄金策·功名章》/case_library 案例十五",
        "topic": "学业",
        "question": "戌月癸卯日占科举能否中第，晋之剥",
        "hexagram": {"original": "晋", "changed": "剥"},
        "input": {
            "date": "戌月癸卯日辰巳旬空",
            "question": "科举考试能否中第",
            "hexagram_name": "晋",
            "changed_name": "剥",
            "notes": "父母官鬼双用神；父母旺；原神动生官；世持兄弟竞争",
        },
        "expected": {
            "verdict": "平吉",
            "use_god": "父母",
            "use_god_branch": "丑",
            "key_points": ["用神多现", "旬空", "兄弟持世", "长生", "帝旺"],
            "yingqi": "年内",
            "detail": "功名可中但非前茅；中举名次靠后",
        },
        "scoring": {"verdict_match": 0.3, "use_god_correct": 0.25, "key_pattern_identified": 0.25, "yingqi_correct": 0.2},
        "benchmark_note": "双用神：父母文书 + 官鬼功名",
    },
    {
        "id": "HO012",
        "source": "《卜筮正宗·胎孕论》/case_library 案例十八",
        "topic": "胎产",
        "question": "丑月丙子日占妻胎安否，观之比",
        "hexagram": {"original": "观", "changed": "比"},
        "input": {
            "date": "丑月丙子日申酉旬空",
            "question": "妻怀孕安否男女",
            "hexagram_name": "观",
            "changed_name": "比",
            "notes": "子孙为胎；子孙未土丑月旺；原神生子孙",
        },
        "expected": {
            "verdict": "吉",
            "use_god": "子孙",
            "use_god_branch": "未",
            "key_points": ["长生", "帝旺", "旬空", "暗动"],
            "yingqi": "月余",
            "detail": "胎安女胎顺产，母女平安",
        },
        "scoring": {"verdict_match": 0.3, "use_god_correct": 0.3, "key_pattern_identified": 0.25, "yingqi_correct": 0.15},
    },
]

by = {c["id"]: c for c in data["cases"]}
for c in new_cases:
    by[c["id"]] = c
# keep order: original + new
order = [c["id"] for c in data["cases"] if c["id"] not in {x["id"] for x in new_cases}]
order += [c["id"] for c in new_cases]
data["cases"] = [by[i] for i in order]
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

ho = splits.get("holdout") or []
for c in new_cases:
    if c["id"] not in ho:
        ho.append(c["id"])
splits["holdout"] = ho
splits["holdout_policy"] = "禁止为单例新增仅对其命中的私有格局别名；通用古籍术语允许；原神失位/久病逢冲为通用法则"
sp.write_text(json.dumps(splits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("holdout now", ho, "total cases", len(data["cases"]))
