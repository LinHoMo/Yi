# -*- coding: utf-8 -*-
"""prose 通道吉凶书证门（[41]，第四百二十二批新增）。

守什么：dz 散文通道（`zengshan_dz_prose_cases.json`）的**每一个非空吉凶**都必须有
本案断语段里的逐字书证；书证册（`zengshan_dz_prose_readings.json`）与案例、分片册三方同源。

为什么需要它：421 批把吉凶收进逐字书证册，但建器只校验 `quote in 整个底本`——
L2334（ZDP012）的「后竟纳之，名败身丧」实际长在 L2911（ZDP024）的断语段里，
全库命中即放行，于是别案的结论被记到本案名下。同一事故族的另一种形态是
**人工改数据**：直接改书证册或案例的 verdict／quote，建器不跑就无人发现。
（`fetch_zengshan_dz_cases.py --selftest` 只证逻辑，不证当前盘上数据。）

本门守五条：
  A. 非空吉凶必须有 `provenance.verdict_quote`，且引文落在**本案头行→下一占例头行**的段内；
  B. 书证册每个键必须对应在册案例；verdict 取值 ∈ {吉, 凶, 空}；
  C. 册与案例的 verdict 必须一致；非空 verdict 的 quote 必须与案例所记逐字相同；
  D. 存活线：案例数／书证册条数／非空吉凶数不低于登记下限（422 批：38／28／23）；
  E. 分片册 `zengshan_dz_prose_holdout`／`_direction` 必须能由当前数据机械重算（逐 id 相同）。

    python dev_tools/check_prose_readings.py            # 对拍真实数据
    python dev_tools/check_prose_readings.py --selftest # 负例自证：每类破坏都必须判红

口径：这是**书证归属**门，不是吉凶判读门——书上的结果句是否该判吉／凶仍由人工逐条读，
本门只保证「写进来的吉凶指得回本案原文」。
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402  [20] CLI 编码红线

import fetch_zengshan_dz_cases as B  # noqa: E402  断语段止界与建器同一口径

SRC = DISC / "data" / "sources" / "zengshan_buyi_dz.dz.txt"
CASES = DISC / "data" / "cases" / "zengshan_dz_prose_cases.json"
READINGS = DISC / "data" / "cases" / "zengshan_dz_prose_readings.json"
SPLITS = DISC / "data" / "cases" / "case_splits.json"

ALLOWED_VERDICTS = ("", "吉", "凶")
# 422 批登记下限：解锁＝同批改这里与 docs/CHANGELOG.md（§四.4／§六.2）。
MIN_CASES = 38       # 案例数
MIN_READINGS = 28    # 书证册条数（含 N/A 的“无结果句”证据）
MIN_VERDICT = 23     # 非空吉凶数
MIN_DIRECTION = 19   # 仅方向分片（无应期但有吉凶）
MIN_HOLDOUT = 4      # 有应期分片


def window_of(lines: list[str], src: str) -> str:
    """本案断语段：头行 → 下一占例头行（与建器 `case_windows` 同口径）。"""
    m = re.search(r"L(\d+)$", str(src or ""))
    if not m:
        return ""
    i = int(m.group(1)) - 1
    stop = B.next_case_head(lines, i + 1)
    return "".join(lines[i:stop if stop is not None else len(lines)])


def audit(cases: list[dict], readings: dict, splits: dict, lines: list[str]) -> list[str]:
    problems: list[str] = []
    by_src: dict[str, dict] = {}
    for c in cases:
        src = str(c.get("_src") or "")
        by_src[src] = c
        cid = str(c.get("id") or src)
        e = c.get("expected") or {}
        pv = c.get("provenance") or {}
        v = str(e.get("verdict") or "")
        q = str(pv.get("verdict_quote") or "")
        if v not in ALLOWED_VERDICTS:
            problems.append(f"{cid} 吉凶取值未登记：{v!r}")
        if v and not q:
            problems.append(f"{cid} 非空吉凶缺逐字书证")
        if q and q not in window_of(lines, src):
            problems.append(f"{cid} 书证不在本案断语段：{q!r}")
        if q and src not in readings:
            problems.append(f"{cid} 有逐字书证但书证册无对应条目（册是唯一登记面）")

    if len(cases) < MIN_CASES:
        problems.append(f"案例数 {len(cases)} < 登记下限 {MIN_CASES}")
    n_verdict = sum(1 for c in cases if str((c.get("expected") or {}).get("verdict") or ""))
    if n_verdict < MIN_VERDICT:
        problems.append(f"非空吉凶 {n_verdict} < 登记下限 {MIN_VERDICT}")

    if len(readings) < MIN_READINGS:
        problems.append(f"书证册 {len(readings)} 条 < 登记下限 {MIN_READINGS}")
    for key, r in readings.items():
        c = by_src.get(key)
        v = str(r.get("verdict") or "")
        q = str(r.get("quote") or "")
        if v not in ALLOWED_VERDICTS:
            problems.append(f"书证册 {key} 取值未登记：{v!r}")
        if v and not q:
            problems.append(f"书证册 {key} 非空吉凶缺引文")
        if q and q not in window_of(lines, key):
            problems.append(f"书证册 {key} 引文不在本案断语段：{q!r}")
        if c is None:
            problems.append(f"书证册键不对应案例：{key}")
            continue
        cv = str((c.get("expected") or {}).get("verdict") or "")
        cq = str((c.get("provenance") or {}).get("verdict_quote") or "")
        if cv != v:
            problems.append(f"书证册 {key} verdict={v!r} ≠ 案例 {cv!r}")
        if (q or cq) and cq != q:
            problems.append(f"书证册 {key} 引文与案例 provenance 不一致")

    hold = [c["id"] for c in cases
            if str((c.get("expected") or {}).get("yingqi") or "")]
    direction = [c["id"] for c in cases
                 if not str((c.get("expected") or {}).get("yingqi") or "")
                 and str((c.get("expected") or {}).get("verdict") or "")]
    if hold != splits.get("zengshan_dz_prose_holdout"):
        problems.append("分片 zengshan_dz_prose_holdout 与当前数据重算不一致（须重跑建器）")
    if direction != splits.get("zengshan_dz_prose_direction"):
        problems.append("分片 zengshan_dz_prose_direction 与当前数据重算不一致（须重跑建器）")
    if len(hold) < MIN_HOLDOUT or len(direction) < MIN_DIRECTION:
        problems.append(f"分片缩水：holdout {len(hold)}/{MIN_HOLDOUT}、direction {len(direction)}/{MIN_DIRECTION}")
    return problems


def load() -> tuple[list[dict], dict, dict, list[str]]:
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    readings = json.loads(READINGS.read_text(encoding="utf-8"))["readings"]
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    lines = SRC.read_text(encoding="utf-8", errors="replace").split("\n")
    return cases, readings, splits, lines


def selftest(cases: list[dict], readings: dict, splits: dict, lines: list[str]) -> list[str]:
    fails: list[str] = []

    def must_catch(label: str, mutate) -> None:
        cs, rd, sp = copy.deepcopy(cases), copy.deepcopy(readings), copy.deepcopy(splits)
        mutate(cs, rd, sp)
        if not audit(cs, rd, sp, lines):
            fails.append(f"负例未抓到：{label}")

    if audit(cases, readings, splits, lines):
        fails.append("完好数据被误伤——本门自身口径有误")
        return fails

    quoted = next(c for c in cases
                  if str((c.get("expected") or {}).get("verdict") or "")
                  and str((c.get("provenance") or {}).get("verdict_quote") or ""))
    other = next(c for c in cases
                 if c is not quoted
                 and str((c.get("expected") or {}).get("verdict") or "")
                 and str((c.get("provenance") or {}).get("verdict_quote") or ""))

    def blank_quote(cs, rd, sp):
        cs[cases.index(quoted)]["provenance"]["verdict_quote"] = ""

    must_catch("非空吉凶清空书证", blank_quote)

    def fake_quote(cs, rd, sp):
        cs[cases.index(quoted)]["provenance"]["verdict_quote"] = "本书没有这句话"

    must_catch("书证引文不在底本", fake_quote)

    def cross_case_quote(cs, rd, sp):
        # 421 批的真实形态：引文在全库另一案段命中，但不在本案段
        i = cases.index(quoted)
        cs[i]["provenance"]["verdict_quote"] = other["provenance"]["verdict_quote"]

    must_catch("跨案引文（全库有、本案段无）", cross_case_quote)

    key = str(quoted.get("_src"))
    bare = next(c for c in cases
                if not str((c.get("provenance") or {}).get("verdict_quote") or ""))
    bare_src = str(bare.get("_src"))

    def case_quote_without_reading(cs, rd, sp):
        c = next(x for x in cs if str(x.get("_src")) == bare_src)
        c.setdefault("provenance", {})["verdict_quote"] = window_of(lines, bare_src)[:20]

    must_catch("案例有书证但册无条目", case_quote_without_reading)

    def reading_mismatch(cs, rd, sp):
        v = rd[key]["verdict"]
        rd[key]["verdict"] = "凶" if v == "吉" else "吉"

    must_catch("册与案例 verdict 不一致", reading_mismatch)

    def reading_bad_value(cs, rd, sp):
        rd[key]["verdict"] = "平"

    must_catch("册吉凶取值未登记", reading_bad_value)

    def reading_orphan(cs, rd, sp):
        rd["zengshan_buyi_dz.dz.txt L99999"] = {"verdict": "吉", "quote": "无"}

    must_catch("册键不对应案例", reading_orphan)

    def drop_case(cs, rd, sp):
        cs.pop()

    must_catch("删掉一例", drop_case)

    def drop_reading(cs, rd, sp):
        rd.pop(next(iter(rd)))

    must_catch("删掉一条书证", drop_reading)

    def drift_splits(cs, rd, sp):
        sp["zengshan_dz_prose_direction"] = sp["zengshan_dz_prose_direction"][:-1]

    must_catch("分片与数据分家", drift_splits)
    return fails


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="prose 通道吉凶书证门（[41]）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    cases, readings, splits, lines = load()
    problems = audit(cases, readings, splits, lines)
    n_verdict = sum(1 for c in cases if str((c.get("expected") or {}).get("verdict") or ""))
    n_quote = sum(1 for c in cases
                  if str((c.get("provenance") or {}).get("verdict_quote") or ""))
    print("prose 吉凶书证对拍：")
    print(f"  · 案例 {len(cases)}｜非空吉凶 {n_verdict}｜带逐字书证 {n_quote}"
          f"｜书证册 {len(readings)} 条")
    for p in problems:
        print("  ×", p)
    if not problems:
        print("  √ 非空吉凶全部指回本案断语段；册↔案例↔分片三方同源")

    st_fail: list[str] = []
    if args.selftest:
        st_fail = selftest(cases, readings, splits, lines)
        print(f"  [selftest] 负例{'全部抓到' if not st_fail else '失效'}"
              "（10 类：清空/伪造/跨案引文、案例有证册无条目、册不一致/坏取值/孤儿键、删例/删证/分片漂移）")
        for p in st_fail:
            print("  ×", p)

    if problems or st_fail:
        return 1
    print("prose 吉凶书证门通过。解锁＝同批改本案登记下限与 docs/CHANGELOG.md。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
