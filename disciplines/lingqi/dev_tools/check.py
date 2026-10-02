# -*- coding: utf-8 -*-
"""灵棋经·质量门：契约文件 + 课表完整性 + 四段冒烟 + 金标准。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = DISC.parents[1] / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from yishu_core.gate_kit import run_step as _run_step  # noqa: E402


def run(cmd: list[str]) -> tuple[int, str]:
    """本门口径：cwd=学科根、120s 超时、argv 前补解释器（实现在内核 gate_kit）。"""
    return _run_step(cmd, cwd=DISC, timeout=120, python=True)


def main() -> int:
    fails: list[str] = []

    required = ["SKILL.md", "scripts/chart.py", "scripts/analyze.py",
                "scripts/narrate.py", "scripts/render.py",
                "data/ketables.json", "dev_tools/check.py", "dev_tools/golden.py"]
    missing = [r for r in required if not (DISC / r).exists()]
    if missing:
        fails.append(f"缺 {missing}")
    print("[0] 契约文件", "√" if not missing else "×")

    # [1] 课表完整性：124 课、键集合 = 全部非零三部组合、课名齐全唯一
    table = json.loads((DISC / "data" / "ketables.json").read_text(encoding="utf-8"))
    courses = table.get("courses") or {}
    expect_keys = {f"{u}-{m}-{d}" for u in range(5) for m in range(5)
                   for d in range(5) if (u, m, d) != (0, 0, 0)}
    keys = set(courses)
    if len(courses) != 124 or keys != expect_keys:
        fails.append(f"课表键数 {len(courses)} ≠ 124 或键集合不匹配 "
                     f"(缺 {len(expect_keys - keys)}，多 {len(keys - expect_keys)})")
    noname = [k for k, v in courses.items() if not v.get("name")]
    if noname:
        fails.append(f"缺课名: {noname[:5]}")
    names = [v["name"] for v in courses.values()]
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        fails.append(f"课名重复: {dup[:5]}")
    if table.get("problems"):
        fails.append(f"构建器报告问题: {table['problems']}")
    # 字段不变式（SYS-REVIEW #9）：每课 name/xiang/zhu/gong 非空、标注组至少一组——
    # 查表直录科的结构恒定，防某课静默缺字段
    # 标注组可少（书源个别课本无詩曰，如 4-1-3 益友卦只有象曰+許曰），忠实录不造句
    gongs = sorted({v.get("gong", "") for v in courses.values()})
    gong8 = sorted({g[0] for g in gongs if g})
    bad_fields = [k for k, v in courses.items()
                  if not v.get("name") or not v.get("xiang") or not v.get("zhu")
                  or not v.get("gong") or not v.get("notes")]
    if bad_fields:
        fails.append(f"课条目缺字段（name/xiang/zhu/gong/notes）: {bad_fields[:5]}")
    if len(gong8) != 8:
        fails.append(f"卦宫八卦 {len(gong8)} 种 ≠ 8：{gong8}")
    print(f"[1] 课表完整性 √ 124 课" if not any("课表" in f or "课名" in f or "缺字段" in f
                                              or "卦宫" in f for f in fails)
          else "[1] 课表完整性 ×")

    # [1c] 逐字回指门（铁律三）：入库文本去空白后必须是书源连续子串；
    # 另校验标注组结构（每课恰一组「象曰」）与非课标题章节已进 appendix（不静默并入）
    src = (DISC.parents[1] / "data" / "sources" / "ling-qi-jing.wikitext.txt")
    flat = re.sub(r"\s+", "", src.read_text(encoding="utf-8")) if src.exists() else ""
    bad = []
    if not flat:
        bad.append("书源缺失，无法做回指")
    for k, v in courses.items():
        for fld in ("name", "xiang", "zhu"):
            if re.sub(r"\s+", "", v.get(fld) or "") not in flat:
                bad.append(f"{k}.{fld} 不可回指")
        notes = v.get("notes") or []
        marks = [g.get("mark") for g in notes]
        if marks.count("象曰") != 1:
            bad.append(f"{k}：象曰组数 {marks.count('象曰')} ≠ 1（{marks}）")
        for gi, g in enumerate(notes):
            if not g.get("lines"):
                bad.append(f"{k}.notes[{gi}]({g.get('mark')}) 空组")
            for li, line in enumerate(g.get("lines") or []):
                if re.sub(r"\s+", "", line) not in flat:
                    bad.append(f"{k}.notes[{gi}][{li}] 不可回指")
    appendix = table.get("appendix") or []
    if not appendix:
        bad.append("书源非课标题章节（如「純陰饅」）未登记 appendix——不得静默并入相邻课")
    for a in appendix:
        for gi, g in enumerate(a.get("notes") or []):
            for li, line in enumerate(g.get("lines") or []):
                if re.sub(r"\s+", "", line) not in flat:
                    bad.append(f"appendix[{a.get('title')}][{gi}][{li}] 不可回指")
    if bad:
        fails.extend(bad[:5])
        print("[1c] 引文可回指 ×", *bad[:5], sep="\n    ")
    else:
        groups = sum(len(v.get("notes") or []) for v in courses.values())
        print(f"[1c] 引文可回指 √ 124 课｜标注组 {groups} 组｜卦宫 9 串（八宫齐）"
              f"｜附录 {len(appendix)} 条：{'、'.join(a.get('title', '') for a in appendix)}")

    # [2] 全 124 课逐一走 chart（机械查表无异常）
    sys.path.insert(0, str(DISC / "scripts"))
    from chart import chart as chart_fn  # noqa: E402
    bad = []
    for key in sorted(keys):
        u, m, d = (int(x) for x in key.split("-"))
        try:
            c = chart_fn(u, m, d)
            if c["men"] != courses[key]["name"]:
                bad.append(f"{key} 课名不匹配")
        except Exception as exc:  # noqa: BLE001
            bad.append(f"{key}: {type(exc).__name__}: {exc}")
    if bad:
        fails.extend(bad[:5])
        print("[2] 全课查表 ×", *bad[:5], sep="\n    ")
    else:
        print("[2] 全课查表 √ 124/124")

    code, out = run(["scripts/chart.py", "--up", "4", "--mid", "3", "--down", "2",
                     "--question", "占谋事", "-o", "scratch/chart.json"])
    if code != 0:
        fails.append("chart 冒烟失败")
        print(out[-600:])
    else:
        print("[3] chart 冒烟 √")

    code, out = run(["scripts/analyze.py", "scratch/chart.json", "-o", "scratch/analyze.json"])
    if code != 0:
        fails.append("analyze 冒烟失败")
        print(out[-600:])
    else:
        print("[4] analyze 冒烟 √")

    code, out = run(["scripts/narrate.py", "scratch/analyze.json"])
    if code != 0 or "不是现实预测" not in out:
        fails.append("narrate 应声明非现实预测")
        print(out[-600:])
    else:
        print("[5] narrate 口径声明 √")

    code, out = run(["scripts/render.py", "scratch/analyze.json", "-o", "scratch/report.md"])
    if code != 0 or not (DISC / "scratch" / "report.md").exists():
        fails.append("render 冒烟失败")
        print(out[-600:])
    else:
        print("[6] render 冒烟 √")

    code, out = run(["dev_tools/golden.py", "verify"])
    if code != 0:
        fails.append("金标准指纹漂移")
        print(out[-600:])
    else:
        print("[7] 金标准 √", out.strip())

    if fails:
        print("\n质量门未通过：", *fails, sep="\n  · ")
        return 1
    print("\n灵棋经质量门全部通过。")
    print("口径：查表直录《靈棋經》原文断语，非本仓推断，不是现实预测命中率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
