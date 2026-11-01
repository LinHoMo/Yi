#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""八字象层门（362 批）：宫位/六亲/脏腑三象须齐、须带出处、且不得倒灌评分。

为什么需要它：八字侧此前有十神、有藏干、有纳音取象，正文里却**没有宫位也没有
六亲**——「哪一柱是哪一门亲眷／哪一段人生」这条线整条缺，实测正文命中数为 0。
素材在（四柱、十神、五行计数全有），能力不在；原有门一条都拦不住（键面合规、
评分未变、指纹不动）。

三条判据：
  ① 三象齐备且带出处：宫位（四柱俱在）、六亲（按性别分野）、脏腑（五行计数
     含中医声明），每块 `basis` 非空。
  ② 六亲性别分野真生效：同一盘男命月干正财应「妻」、女命时干正官应「夫」——
     只验"能取到六亲"会把不分性别的恒通用口径判成过。
  ③ 禁评分：评分侧（pattern.py / bazi_factors/*）不得读 `xiang`；
     `xiang` 不得成为 evaluate.WEIGHTS 的维度。

`--selftest`：挖 basis／抹掉性别分野／评分侧偷读 xiang，三处各须被抓。
454 批：`--selftest` 通过后**继续跑真实数据面**——此前 `return selftest()` 提前返回，
而 check.py 只以 `--selftest` 调本门，③ 禁评分与男女两份真实象层在全量流程里未执行。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "core"))

# 定盘：日干甲（阳木）→ 月干己（阴土，我克异性）为正财；时干辛（阴金，克我异性）为正官
PILLARS = {"year": "甲辰", "month": "己巳", "day": "甲子", "hour": "辛未"}

# 评分侧：象层一旦被这里读到，象就变成了分数——CONTRACT §五-bis 禁边
SCORING_DIRS = ("bazi_factors",)
SCORING_FILES = ("pattern.py", "chart.py")


def _xiang_of(gender: str) -> dict:
    from chart import chart_from_pillars
    from analyze import analyze as _analyze
    from xiang import build_xiang
    a = _analyze(chart_from_pillars(PILLARS, gender=gender, question="象层门"))
    return build_xiang({**a, "bing_yao": a.get("bing_yao")})


def shape_problems(x: dict, label: str) -> list[str]:
    """① 三象齐备 + 出处非空。"""
    problems: list[str] = []
    if not x:
        return [f"象层整块缺失（{label}）——素材在盘面里，analyze 没装配出来"]

    gw = x.get("gongwei") or {}
    for cn in ("年", "月", "日", "时"):
        if not (gw.get(cn) or {}).get("ganzhi"):
            problems.append(f"宫位缺 {cn} 柱（{label}）")
    if not str(gw.get("basis") or "").strip():
        problems.append(f"宫位象缺 basis（{label}）——无出处的象目不得产出")

    lg = x.get("liugin") or {}
    if not any((lg.get(cn) or {}).get("六亲") for cn in ("年", "月", "日", "时")):
        problems.append(f"六亲象四柱皆空（{label}）")
    if not str(lg.get("basis") or "").strip():
        problems.append(f"六亲象缺 basis（{label}）")
    if not str(lg.get("basis_wulei") or "").strip():
        problems.append(f"六亲五类未标内核真源（{label}）")

    zf = x.get("zangfu") or {}
    if len(zf.get("counts") or {}) != 5:
        problems.append(f"五行计数不是五维齐全（{label}）：{zf.get('counts')}")
    if not str(zf.get("basis") or "").strip():
        problems.append(f"脏腑象缺 basis（{label}）")
    if "医学诊断" not in str(zf.get("note") or ""):
        problems.append(f"脏腑象缺「非医学诊断」声明（{label}）")
    if not str((x.get("basis") or {}).get("note") or "").strip():
        problems.append(f"象层缺总登记 note（{label}）")
    return problems


def gender_problems(male: dict, female: dict) -> list[str]:
    """② 六亲性别分野真生效（男：正财→妻；女：正官→夫）。"""
    problems: list[str] = []
    m_yue = ((male.get("liugin") or {}).get("月") or {}).get("六亲") or ""
    f_shi = ((female.get("liugin") or {}).get("时") or {}).get("六亲") or ""
    if m_yue != "妻":
        problems.append(f"男命月干正财应「妻」，实得「{m_yue}」——性别分野未生效")
    if f_shi != "夫":
        problems.append(f"女命时干正官应「夫」，实得「{f_shi}」——性别分野未生效")
    return problems


def no_scoring_problems() -> list[str]:
    """③ 禁评分。"""
    problems: list[str] = []
    targets: list[Path] = []
    for d in SCORING_DIRS:
        targets += [p for p in (ROOT / "scripts" / d).glob("*.py")]
    targets += [ROOT / "scripts" / f for f in SCORING_FILES if (ROOT / "scripts" / f).exists()]
    for p in targets:
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("#"):
                continue
            if "xiang" in s and ("import" in s or '"xiang"' in s or "'xiang'" in s):
                problems.append(f"评分侧 {p.name} 读象：{s[:90]}——象不得倒灌评分（CONTRACT §五-bis）")
                break
    try:
        from evaluate import WEIGHTS
        if "xiang" in WEIGHTS:
            problems.append("evaluate.WEIGHTS 含 xiang 维度——象层不进评分")
    except Exception:  # noqa: BLE001
        pass
    return problems


def selftest() -> int:
    problems: list[str] = []
    good = _xiang_of("男")
    if shape_problems(good, "男"):
        problems.append("自证失败：合规象层被误判（先确认正跑是否真的绿）")
    bad = {"gongwei": {"年": {"ganzhi": "甲辰"}, "月": {"ganzhi": "己巳"},
                       "日": {"ganzhi": "甲子"}, "时": {"ganzhi": "辛未"}}}
    if not shape_problems(bad, "坏"):
        problems.append("自证失败：缺 basis／缺六亲脏腑的象层没被抓到")
    if not shape_problems({}, "空"):
        problems.append("自证失败：象层整块缺失没被抓到")
    if not gender_problems({"liugin": {"月": {"六亲": "嫂／弟媳"}}},
                           {"liugin": {"时": {"六亲": "夫"}}}):
        problems.append("自证失败：男命正财未按男命口径（恒通用）没被抓到")
    if gender_problems(good, _xiang_of("女")):
        problems.append("自证失败：合规性别分野被误判（先确认正跑是否真的绿）")
    if problems:
        print("FAIL：负例自证未通过")
        for p in problems:
            print("  " + p)
        return 1
    print("selftest：三类负例（缺出处／缺性别分野／整块缺失）全部抓到；合规输入放行")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="八字象层门：三象／六亲分野／禁评分")
    ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = ap.parse_args()
    if args.selftest:
        st = selftest()
        if st != 0:
            return st
        # 454 批：负例通过后继续跑真实数据面（不提前 return；check.py 只以 --selftest 调本门）

    male = _xiang_of("男")
    female = _xiang_of("女")
    problems: list[str] = []
    problems.extend(shape_problems(male, "男"))
    problems.extend(shape_problems(female, "女"))
    problems.extend(gender_problems(male, female))
    problems.extend(no_scoring_problems())

    print(f"象层门：定盘 {PILLARS} 男/女各一；"
          f"宫位 {len([k for k in (male.get('gongwei') or {}) if k in ('年','月','日','时')])}/4；"
          f"脏腑五行 {len((male.get('zangfu') or {}).get('counts') or {})}/5")
    if problems:
        print(f"FAIL：{len(problems)} 项")
        for p in problems:
            print("  " + p)
        return 1
    print("校验不过项: 无（三象齐备有出处、六亲按性别分野、象层未倒灌评分）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
