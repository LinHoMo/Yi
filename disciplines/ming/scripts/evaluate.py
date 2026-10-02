# -*- coding: utf-8 -*-
"""命科八字 · 古籍案例对齐评分（tune / holdout 分列出分，禁止混分）。

    python scripts/evaluate.py --split tune
    python scripts/evaluate.py --split holdout --verbose
    python scripts/evaluate.py --split all --save

口径（务必连同分数一起阅读，AGENTS.md 铁律三；方法学见 disciplines/ming/docs/EVAL-PLAN.md）：
  本脚本衡量的是**引擎输出与古籍案例要点的一致性**，不是现实世界预言命中率。

三条硬规则（方法论层面的自保，违反则分数没有意义）：
  1. **只评书上明写的量**。案例 `expected` 里不出现的键 = 该维度 N/A，
     **整项从分母剔除**（不是算错也不是算对）。
  2. **不评无客观标的的东西**：富贵层次、寿夭、六亲克应、具体吉凶年份一律不计分；
     这类内容可以原文抄进 `qualitative` 案例的 `notes`，但**不进分母**。
  3. **禁止用引擎输出反推 expected**。每例的 expected 都必须能指回 `book` + `location`
     的原文（`source_quote`）。不能指回的案例不入库。

维度与权重（单一真值源，总和 100；只计条目实际存在的维度）：
  四柱 24（每柱 6）/ 十神 16（每位 4）/ 藏干 8（每支 2）/ 调候 16（主 10 + 佐 6）/
  格局 12（名 8 + 成破救应 4）/ 从格 4 / 神煞 8 / 大运 12（顺逆 8 + 起运 4）

  权重刻意选成**能整除各自子项数**：否则"四柱对三柱"会算出 18.75 这种分量，
  取整后显示 72% 或 76%，与"四分之三"的直觉不符，也掩盖了真实误差。
  框架自检（`tools/scratch` 之外的一次性脚本）抓到过这个歧义。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.eval import run_eval, report  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

import analyze as analyze_mod  # noqa: E402
import chart as chart_mod  # noqa: E402

CASES_PATH = DISC / "data" / "cases" / "ming_classical_cases.json"
OUT_DIR = DISC / "data" / "cases"

WEIGHTS = {
    "pillars": 24,      # 四柱，每柱 6
    "ten_gods": 16,     # 十神，每位 4
    "hidden_stems": 8,  # 藏干本气，每支 2
    "tiaohou": 16,      # 调候主神 10 + 佐神 6
    "pattern": 12,      # 格局名 8 + 成破救应 4
    "cong_ge": 4,       # 从格布尔
    "shensha": 8,       # 神煞集合
    "dayun": 12,        # 顺逆 8 + 起运 4
}
assert sum(WEIGHTS.values()) == 100, "维度权重之和必须是 100"

MODEL = "strict"

PILLAR_KEYS = ("year", "month", "day", "hour")


# ── 案例装载 ────────────────────────────────────────────────────────────────

def load_store() -> dict:
    if not CASES_PATH.is_file():
        return {"schema": "yi-ming-cases/1", "splits": {"tune": [], "holdout": []},
                "cases": []}
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def load_ids(split: str) -> list[str]:
    store = load_store()
    if split == "all":
        return [c["id"] for c in store.get("cases", [])]
    return list((store.get("splits") or {}).get(split) or [])


def load_cases() -> list[dict]:
    return list(load_store().get("cases", []))


# ── 跑引擎 ──────────────────────────────────────────────────────────────────

def _pillars_to_datetime(pillars: dict) -> str | None:
    """案例若给了公历 `datetime` 就用它；只给四柱的案例无法反推公历，返回 None。"""
    return pillars.get("datetime")


def run_ids(ids: list[str], gender_default: str = "") -> dict:
    """逐例跑 chart→analyze，收集引擎输出。

    案例给公历 datetime → chart（干支历换算）；只给四柱 → chart_from_pillars
    （直填，birth.datetime 置空、不猜公历；大运起运岁数按近似）。
    """
    by_id = {c["id"]: c for c in load_cases()}
    out: dict = {"cases": [], "errors": []}
    for cid in ids:
        case = by_id.get(cid)
        if case is None:
            out["errors"].append({"id": cid, "error": "案例不存在"})
            continue
        dt = _pillars_to_datetime(case.get("pillars") or {})
        gender = case.get("gender") or gender_default or "男"
        try:
            if dt:
                ch = chart_mod.chart(datetime_str=dt, gender=gender)
            else:
                gz = {k: (case.get("pillars") or {}).get(k) for k in ("year", "month", "day", "hour")}
                missing = [k for k, v in gz.items() if not v]
                if missing:
                    out["errors"].append({"id": cid,
                                          "error": f"案例无公历 datetime 且四柱不全（缺 {'/'.join(missing)}）；无法起盘（不猜）"})
                    out["cases"].append({
                        "id": cid,
                        "error": f"案例无公历 datetime 且四柱不全（缺 {'/'.join(missing)}）",
                        "expected_available": bool(case.get("expected")),
                    })
                    continue
                ch = chart_mod.chart_from_pillars(gz, gender=gender)
            an = dict(analyze_mod.analyze(ch))
            an["id"] = cid
            # 大运顺逆：analyze 未把它提到顶层，这里按同一内核口径补上（不新造判据）
            if not an.get("dayun_direction"):
                from yishu_core.ming_tables import dayun_direction
                year_stem = (ch.get("pillars") or {}).get("year", {}).get("stem") or ""
                if year_stem and gender:
                    an["dayun_direction"] = dayun_direction(year_stem, gender)
            out["cases"].append(an)
        except Exception as exc:  # 引擎异常如实登记，不吞
            out["errors"].append({"id": cid, "error": f"{type(exc).__name__}: {exc}"})
            out["cases"].append({"id": cid, "error": f"{type(exc).__name__}: {exc}"})
    return out


# ── 打分 ────────────────────────────────────────────────────────────────────

def _na(value) -> bool:
    return value in (None, "", "?", [], {})


def _eng_pillars(eng: dict) -> dict:
    return {k: (eng.get("pillars") or {}).get(k, {}).get("ganzhi") for k in PILLAR_KEYS}


def _eng_ten_gods(eng: dict) -> dict:
    return {k: (eng.get("pillars") or {}).get(k, {}).get("ten_god") for k in PILLAR_KEYS}


def _set_ratio(offered, needed) -> tuple[float, str]:
    """集合命中比例（不给"多列即多中"的骑墙分）。"""
    needed = [str(x) for x in needed]
    if not needed:
        return 0.0, ""
    got = set(str(x) for x in offered)
    hit = len([x for x in needed if x in got])
    return hit / len(needed), f"{hit}/{len(needed)}"


def score_case(eng: dict, exp: dict, model: str) -> dict:
    """单例打分。返回 {dim: (earned, applicable_weight, note)}。

    **只处理 exp 里出现的维度**：没出现的键整个不进 dims —— 于是它既不进分子
    也不进分母（`yishu_core.eval.pct` 只对 dims 求和）。这是"只评书上明写的量"
    在代码层的落实。
    """
    dims: dict[str, tuple[int, int, str]] = {}

    # 1) 四柱（历法真值：错就是错）
    w = WEIGHTS["pillars"]
    x_p = exp.get("pillars")
    if not _na(x_p):
        want = {k: x_p.get(k) for k in PILLAR_KEYS if x_p.get(k)}
        got = _eng_pillars(eng)
        if want:
            hit = sum(1 for k, v in want.items() if got.get(k) == v)
            # 权重 24 能被 4 整除 → 每柱 6 分，"对三柱"恰好 18/24 = 75%，
            # 不出现 18.75 这种分量（否则取整会让读数在 72%~76% 之间抖）。
            earned = w * hit // len(want)
            dims["pillars"] = (earned, w,
                               f"{hit}/{len(want)} " + "/".join(
                                   f"{k}:{got.get(k)}" for k in want))

    # 2) 十神
    w = WEIGHTS["ten_gods"]
    x_g = exp.get("ten_gods")
    if not _na(x_g):
        want = {k: v for k, v in x_g.items() if v}
        got = _eng_ten_gods(eng)
        if want:
            hit = sum(1 for k, v in want.items() if got.get(k) == v)
            dims["ten_gods"] = (w * hit // len(want), w, f"{hit}/{len(want)}")

    # 3) 藏干（按支比对"本气是否命中"）
    w = WEIGHTS["hidden_stems"]
    x_h = exp.get("hidden_stems")
    if not _na(x_h):
        factors = eng.get("factors") or {}
        hit = tot = 0
        notes = []
        for pos, want_stems in x_h.items():
            if not want_stems:
                continue
            tot += 1
            got = list((factors.get(pos) or {}).get("hidden_stems") or [])
            main_ok = bool(got) and got[0] == want_stems[0]
            hit += 1 if main_ok else 0
            notes.append(f"{pos}{'√' if main_ok else '×'}")
        if tot:
            dims["hidden_stems"] = (w * hit // tot, w, f"{hit}/{tot} " + " ".join(notes))

    # 4) 调候（《穷通宝鉴》表对表：主神 10 分 + 佐神 6 分）
    w = WEIGHTS["tiaohou"]
    x_t = exp.get("tiaohou")
    if not _na(x_t):
        got = (eng.get("tiaohou") or {})
        main_ok = bool(got.get("main")) and got.get("main") == x_t.get("main")
        note = (f"引擎 {got.get('main') or '—'}/{got.get('assist') or '—'}"
                f" vs 书 {x_t.get('main')}/{x_t.get('assist') or '—'}")
        if x_t.get("assist"):
            assist_ok = bool(got.get("assist")) and got.get("assist") == x_t.get("assist")
            earned = (10 if main_ok else 0) + (6 if assist_ok else 0)
            dims["tiaohou"] = (min(earned, w), w, note)
        else:
            # 书只给主神：佐神「书上没写」= 不适用 → 适用权重只算主神 10，
            # 从分母剔除（规则1：没写的量既不进分子也不进分母），而不是拿 16
            # 当分母把没写的佐神记成扣分
            dims["tiaohou"] = (10 if main_ok else 0, 10, note)

    # 5) 格局（名 8 分 + 成破救应 4 分）
    # 适用权重 = 实际出现的子项权重之和：只记成败 → w=4；只记格名 → w=8；
    # 都记 → w=12。
    name_na = _na(exp.get("pattern"))
    cb_na = _na(exp.get("pattern_cheng_bai"))
    if not (name_na and cb_na):
        w_app = (0 if name_na else 8) + (0 if cb_na else 4)
        strength = eng.get("strength") or {}
        earned, bits = 0, []
        if not name_na:
            ok = strength.get("pattern") == exp.get("pattern")
            earned += 8 if ok else 0
            bits.append(f"格{'√' if ok else '×'}")
        if not cb_na:
            got_cb = strength.get("pattern_cheng_bai")
            ok = got_cb is not None and got_cb == exp.get("pattern_cheng_bai")
            earned += 4 if ok else 0
            bits.append(f"成败{'√' if ok else '×'}")
        dims["pattern"] = (min(earned, w_app), w_app, " ".join(bits))

    # 6) 从格（布尔 2 + 种类 1 + 真/假 1；书没写的子项从分母剔除）
    # 口径：可判级（《滴天髓》从象/假从章
    # 真从=绝无一毫生扶，假从=中有比劫暗生；kind 大类 从财/从官杀/从儿/
    # 从旺/从强/从势/从气）。判据缺口（三合化气/财生杀/透干印比无根边界）
    # 见 docs/CHANGELOG.md。
    w = WEIGHTS["cong_ge"]
    x_bool = exp.get("cong_ge")
    x_kind = exp.get("from_kind")
    x_type = exp.get("from_type")
    if not (_na(x_bool) and _na(x_kind) and _na(x_type)):
        strength = eng.get("strength") or {}
        w_app = 0
        earned = 0
        bits = []
        if not _na(x_bool):
            w_app += 2
            eng_cong = bool(strength.get("from_kind"))
            ok = eng_cong == bool(x_bool)
            earned += 2 if ok else 0
            bits.append(f"从{'√' if ok else '×'}")
        if not _na(x_kind):
            w_app += 1
            ok = (strength.get("from_kind") or "") == x_kind
            earned += 1 if ok else 0
            bits.append(f"类{'√' if ok else '×'}({strength.get('from_kind') or '—'})")
        if not _na(x_type):
            w_app += 1
            ok = (strength.get("from_type") or "") == x_type
            earned += 1 if ok else 0
            bits.append(f"真/假{'√' if ok else '×'}({strength.get('from_type') or '—'})")
        dims["cong_ge"] = (min(earned, w_app), w_app, " ".join(bits))

    # 7) 神煞（期望集合的命中比例；多出不算错——神煞流派差异大）
    w = WEIGHTS["shensha"]
    x_s = exp.get("shensha")
    if not _na(x_s):
        offered = [s.get("name") for s in (eng.get("shensha") or [])]
        ratio, note = _set_ratio(offered, x_s)
        dims["shensha"] = (int(w * ratio), w, note)

    # 8) 大运（顺逆一致 8 分；首运起运岁数误差 ≤1 岁再得 4 分）
    w = WEIGHTS["dayun"]
    if not _na(exp.get("dayun_direction")) or not _na(exp.get("dayun_start_age")):
        dayun = eng.get("dayun") or []
        earned, bits = 0, []
        if not _na(exp.get("dayun_direction")):
            got = eng.get("dayun_direction")
            ok = got is not None and got == exp.get("dayun_direction")
            earned += 8 if ok else 0
            bits.append(f"顺逆{'√' if ok else '×'}({got})")
        if not _na(exp.get("dayun_start_age")):
            if dayun and dayun[0].get("start_age") is not None:
                delta = abs(float(dayun[0]["start_age"]) - float(exp["dayun_start_age"]))
                ok = delta <= 1.0
                earned += 4 if ok else 0
                bits.append(f"起运{'√' if ok else f'×Δ{delta:.1f}'}")
            else:
                bits.append("起运×缺")
        dims["dayun"] = (min(earned, w), w, " ".join(bits))

    return dims


# ── 报告与防骑墙 ────────────────────────────────────────────────────────────

# 各维度的随机期望基线（"多选一"维度的骑墙警戒线）。
# 只报命中率而不报基线 = 骑墙；这里把基线连同读数一起打出来。
RANDOM_BASELINE = {
    "pillars": 1.0 / 60,        # 单柱干支 60 甲子中取一
    "ten_gods": 1.0 / 10,       # 十神中取一
    "hidden_stems": 1.0 / 10,   # 天干十中取一
    "tiaohou": 1.0 / 10,        # 调候主神十干取一
    "pattern": 1.0 / 12,        # 正格十二名取一
    "cong_ge": 0.5,             # 布尔 2/4；种类 1/8、真/假 1/2 另计（见维度明细）
    "shensha": 1.0 / 30,        # 神煞表约 30 项
    "dayun": 0.5,               # 顺逆布尔
}

MIN_N_FOR_PCT = 20          # 集合 n 低于此值不报"百分比式"结论
MIN_APPLICABLE_FOR_PCT = 5  # 单维度 applicable 低于此值只报命中数


def print_dim_detail(res: dict) -> None:
    """三列明细。**「命中」= 该例在该维度拿满该维度权重**（不是子项计数）。

    口径要统一：`yishu_core.eval` 的数就是"满分例数"，子项计数只在 note 里出现。
    两者混在一张表里会让人把"四柱对三柱"读成 0 命中（框架自检抓到过这个歧义）。
    """
    print("\n维度明细（满分例数 / 适用例数 / N/A 例数｜该维度的判据痕迹）：")
    notes = {}
    for row in (res.get("rows") or []):
        for k, v in (row.get("dims") or {}).items():
            if len(v) > 2 and v[2]:
                notes.setdefault(k, []).append(v[2])
    for k, v in (res.get("dims") or {}).items():
        base = RANDOM_BASELINE.get(k)
        base_s = f"  随机基线≈{base * 100:.1f}%" if base else ""
        if v["applicable"] == 0:
            rate = f"—（本集合无适用案例，n/a={v['na']}）"
        elif v["applicable"] < MIN_APPLICABLE_FOR_PCT:
            rate = f"满分 {v['full']}/{v['applicable']}（适用数 <{MIN_APPLICABLE_FOR_PCT}，不报百分比）"
        else:
            rate = f"{v['rate']}%{base_s}"
        print(f"  {k:<14s} {v['full']:>3d}/{v['applicable']:<3d}  n/a={v['na']:<3d} {rate}")
        for note in notes.get(k, [])[:3]:
            print(f"      · {note}")


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(
        description="命科八字古籍案例对齐评分（非现实预测命中率；方法学见 docs/EVAL-PLAN.md）")
    ap.add_argument("--split", choices=["tune", "holdout", "all"], default="all")
    ap.add_argument("--ids", nargs="*", help="指定案例 ID，优先于 --split")
    ap.add_argument("--stage", choices=["run", "score", "all"], default="all")
    ap.add_argument("--engine-file", type=Path, help="已有的引擎输出（配合 --stage score）")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--save", action="store_true", help="写出 JSON 明细到 data/cases/")
    args = ap.parse_args()

    if args.ids:
        ids, label = args.ids, "custom"
    else:
        ids, label = load_ids(args.split), args.split

    store = load_store()
    if not ids:
        print(f"=== 命科 [{label}] 尚无案例（n=0）===")
        print("  cases 文件：" + str(CASES_PATH.relative_to(DISC.parent.parent)))
        print("  这不是「无结果」，是「还没有尺子」。建集规范见 disciplines/ming/docs/EVAL-PLAN.md 第三节。")
        print("  口径提醒：只评书上明写的量；未记录的维度记 N/A 并从分母剔除。")
        n_cases = len(store.get("cases") or [])
        if n_cases:
            print(f"  注：cases 里已有 {n_cases} 条案例，但 splits 未把它们分配进来。")
        return 0

    if args.stage == "score" and args.engine_file:
        loaded = json.loads(Path(args.engine_file).read_text(encoding="utf-8"))
        engine_out = loaded.get("engine_output", loaded)
        label = f"{label}(cached)"
    else:
        print(f"运行 {len(ids)} 例（{label}）…")
        engine_out = run_ids(ids)

    base = {c["id"]: c for c in load_cases()}
    res = run_eval(engine_out, base, ids, WEIGHTS, score_case, MODEL, label, args.verbose)

    # N/A 计数：run_eval 只统计 score_case **返回过**的维度，于是"基准未记"
    # （维度整个没进 dims）与"该维度不存在"在表里长得一样。这里按"进入打分的行"
    # 逐例比对补记 N/A —— 三列（命中/适用/N/A）必须自解释，否则读者会把
    # "书上没写"误读成"引擎没算"。
    scored_rows = [r for r in res.get("rows", []) if "dims" in r]
    for row in scored_rows:
        for k in WEIGHTS:
            if k not in row["dims"]:
                res["dims"][k]["na"] += 1

    report(res)

    # 不可跑的案例要**单独点名并说明原因**（典型：案例只给四柱没给公历）。
    # 放在"无可用结果"提前返回**之前**——否则最需要解释的那种情况（全部不可跑）
    # 恰好什么都不说。
    unrunnable = [c for c in engine_out.get("cases", []) if "error" in c]
    if unrunnable:
        print(f"\n不可跑 {len(unrunnable)} 例（不计分，如实登记）：")
        for c in unrunnable:
            print(f"  · {c.get('id')}: {c.get('error')}")

    if res["avg"] is None:
        print("无可用结果（案例未给公历 datetime，或全部引擎报错）")
        return 1

    print_dim_detail(res)

    if res["n"] < MIN_N_FOR_PCT:
        print(f"\n⚠ 集合 n={res['n']} < {MIN_N_FOR_PCT}：以上均分**不足以**支撑任何"
              f"「准确率式」结论，只作回归审计用。报分时请连 n 一起写。")
    print("提示：本分数衡量的是与古籍案例要点的一致性，不代表现实预测命中率；"
          "富贵层次/寿夭/六亲克应等无客观标的者一律不计分（EVAL-PLAN §2.2）。")

    errored = [e["id"] for e in engine_out.get("errors", [])]
    if errored:
        print(f"\n引擎报错 {len(errored)} 例：{', '.join(errored)}")

    if args.save:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUT_DIR / f"eval_{label}.json"
        out.write_text(json.dumps({"results": res, "engine_output": engine_out},
                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("明细 →", out)
    return 1 if errored else 0


if __name__ == "__main__":
    raise SystemExit(main())
