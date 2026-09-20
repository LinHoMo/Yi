# -*- coding: utf-8 -*-
import json
from pathlib import Path
p = Path(r"C:\Users\Lin\Desktop\skills\liu-yao\.worktrees\liuyao-optimize\data\cases\classical_cases.json")
data = json.loads(p.read_text(encoding="utf-8"))
fixes = {
    "HO008": {
        "use_god": "官鬼", "use_god_branch": "亥", "verdict": "吉",
        "key_points": ["用神多现", "旬空", "长生", "暗动"],
        "detail": "离宫官鬼在亥（库文巳支有误）；鼎之既济多爻动、原神有动，综合可断吉，防旺极",
        "yingqi": "亥日",
    },
    "HO009": {
        "use_god": "世爻", "use_god_branch": "子", "verdict": "大凶",
        "key_points": ["久病", "回头克", "六合", "六冲", "旬空"],
        "detail": "久病以世为用，回头克+合处变冲，逢冲日危",
        "yingqi": "午日",
    },
    "HO010": {
        "use_god": "官鬼", "use_god_branch": "亥", "verdict": "凶",
        "key_points": ["暗动", "化退神", "月破", "六合", "旬空"],
        "detail": "官司以官鬼为官方；官鬼克世/文书有缺主不利（库文申金与离宫纳甲不符，取亥）",
        "yingqi": "申日",
    },
    "HO011": {
        "use_god": "父母", "use_god_branch": "丑", "verdict": "平吉",
        "key_points": ["用神多现", "旬空", "兄弟持世"],
        "detail": "科举以父母为文书用神，可中而名次不显",
        "yingqi": "年内",
    },
    "HO012": {
        "use_god": "子孙", "use_god_branch": "未", "verdict": "吉",
        "key_points": ["长生", "帝旺", "旬空"],
        "detail": "胎孕以子孙为用，旺相主胎安",
        "yingqi": "月余",
    },
}
for c in data["cases"]:
    if c["id"] in fixes:
        f = fixes[c["id"]]
        exp = c.setdefault("expected", {})
        for k in ("use_god", "use_god_branch", "verdict", "detail", "yingqi"):
            if k in f:
                exp[k] = f[k]
        exp["key_points"] = f["key_points"]
        c["benchmark_fix"] = f["detail"]
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("expected fixed", list(fixes))
