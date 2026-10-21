# -*- coding: utf-8 -*-
"""规则消融台架 v0（第一百八十二批）——固定输入/标签/口径，配对 McNemar 测边际贡献。

要回答的问题（GPT 审计 §3.2 / 本仓 176 批后续队列）：某条规则加进推演链之后，
**它自己**贡献了多少？还是只是让输出更丰富？本项目此前只有"改前后各跑一遍总分"
的粗对拍——总分差里混着分母变化、名次漂移与判词措辞。本台架把对照做严：

  - 同一份输入（case_runner 还原时刻与卦面，引擎确定性由门 [23] 三 seed 实证）；
  - 同一套基准标签与同一判卷口径（evaluate.score_case strict 维表，不另建第二套）；
  - 只切换一个模块属性（TOGGLES 注册表，逐条写明书证与作用面）；
  - 逐例二元配对（verdict 满分与否／主应期 top-1 与否），不一致对做 **McNemar 精确检验**。

诚实边界：消融归因的是**古籍吻合面**（与书载判词/应期支的吻合），不是现实效度；
tune/holdout 可用于归因，外部集照旧只报数不设门槛（§四.3）。负探针 rank_reverse
不是规则而是台架自检：若名次排序携带信号，把它倒序必须测出显著退化——测不出，
说明台架是摆设（§四.8 全绿先怀疑）。

    python dev_tools/ablation.py --list
    python dev_tools/ablation.py --toggle day_mod_zero --splits wikisource_holdout tune
    python dev_tools/ablation.py --toggle rank_reverse --splits wikisource_holdout
    python dev_tools/ablation.py --selftest
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from contextlib import redirect_stdout
from datetime import datetime
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
import case_runner  # noqa: E402
import evaluate  # noqa: E402
import step3  # noqa: E402
import step4  # noqa: E402
import classical_enhancements  # noqa: E402
import timing  # noqa: E402

W_V = evaluate.WEIGHTS["verdict"]
W_Y = evaluate.WEIGHTS["yingqi"]


def mcnemar_exact(b: int, c: int) -> float:
    """双侧精确 McNemar：不一致对 n=b+c 下 Bin(n,.5) ≤min(b,c) 尾概率×2（截 1.0）。"""
    n = b + c
    if n == 0:
        return 1.0
    m = min(b, c)
    p = sum(comb(n, k) for k in range(m + 1)) / (2.0 ** n) * 2.0
    return min(1.0, p)


class _CountingEmpty(dict):
    """替代查表的空 dict：每次 .get/in 计一次引用——区分「补丁未接线」
    （0 引用＝死补丁判红）与「规则在本语料面零命中」（引用>0 变化 0＝如实记零贡献）。"""

    def __init__(self, counter, *a):
        super().__init__(*a)
        self._counter = counter

    def get(self, *a, **k):
        self._counter["refs"] = self._counter.get("refs", 0) + 1
        return None

    def __contains__(self, k):
        self._counter["refs"] = self._counter.get("refs", 0) + 1
        return False


# ── TOGGLES 注册表：每个 = (说明, patch(counter)→undo) ────────────────────
def _t_day_mod_zero():
    def patch(counter):
        orig = step3.compute_day_modifier

        def wrapper(*a, **k):
            counter["refs"] = counter.get("refs", 0) + 1
            return (0.0, "消融：日辰修正停用")
        step3.compute_day_modifier = wrapper
        return lambda: setattr(step3, "compute_day_modifier", orig)
    return ("step3.日辰修正档（含并爻唯一性+0.5 与生克泄制）整体归零，带引用计数；"
            "书证层：《黄金策》源L124/L125 并爻条款（门 [27] 锁其正路）——测该修正层对 "
            "verdict/top-1 的边际贡献", patch)


def _t_advance_off():
    def patch(counter):
        o1, o2 = step4.ADVANCE_PAIRS, classical_enhancements.ADVANCE_PAIRS
        step4.ADVANCE_PAIRS = _CountingEmpty(counter)
        classical_enhancements.ADVANCE_PAIRS = _CountingEmpty(counter)

        def undo():
            step4.ADVANCE_PAIRS = o1
            classical_enhancements.ADVANCE_PAIRS = o2
        return undo
    return ("化进神表置空（两处 from-import 命名空间同时打，带引用计数）；书证层：《增删卜易》"
            "源L1120「寅化卯进也」五源同证——测进退神定级对 verdict/top-1 的边际贡献", patch)


def _t_rank_reverse():
    def patch(counter):
        orig = timing._rank_candidates

        def wrapper(*a, **k):
            counter["refs"] = counter.get("refs", 0) + 1
            return list(reversed(orig(*a, **k)))
        timing._rank_candidates = wrapper
        return lambda: setattr(timing, "_rank_candidates", orig)
    return ("【负探针·非规则】名次序整体倒序：若排序携带信号，本消融必须测出显著退化；"
            "测不出＝台架是摆设（§四.8）", patch)


TOGGLES = {
    "day_mod_zero": _t_day_mod_zero,
    "advance_off": _t_advance_off,
    "rank_reverse": _t_rank_reverse,
}


# ── 注册表驱动的全量扫掠（第一百八十六批·A2）─────────────────────────────
IMPL_ANCHOR = re.compile(r"([A-Za-z_]\w*)\.py[:：]([A-Za-z_]\w*)")


def _patch_binding(mod_name: str, fn_name: str, counter: dict):
    """bind-all 补丁（对象同一级）：原函数可能被 N 个模块 from-import——含**异名别名**
    （第一百八十六批开发实证两坑：①只打源模块＝25/33 假「未触发」；②step5 的
    `import predict_timing_core as _predict_timing` 连同名属性扫描都漏——按对象同一收网）。
    返回 (undo, 打了几个绑定)；打不通返回 None。"""
    import importlib
    import types

    def wrapper(*a, **k):
        counter["refs"] = counter.get("refs", 0) + 1
        return None
    try:
        src = importlib.import_module(mod_name)
    except ImportError:
        return None
    src_fn = getattr(src, fn_name, None)
    if src_fn is None or not callable(src_fn):
        return None
    targets = []
    for m in list(sys.modules.values()):
        if not isinstance(m, types.ModuleType):
            continue
        for aname, aobj in list(vars(m).items()):
            if aobj is src_fn:
                targets.append((m, aname))
    if not any(m is src and an == fn_name for m, an in targets):
        targets.append((src, fn_name))
    for m, an in targets:
        setattr(m, an, wrapper)

    def undo():
        for m, an in targets:
            setattr(m, an, src_fn)
    return undo, len(targets)


def parse_impl(impl: str):
    """从 impl 串抽 (module, func) 函数锚点。裸行号锚（step3.py:583/4.3 等）
    与「整文件」指针无法单点切除——不硬造开关，落「不可单切」类显形。"""
    seen = set()
    out = []
    for m in IMPL_ANCHOR.finditer(impl or ""):
        key = (m.group(1), m.group(2))
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def sweep(splits, limit=None, out_path=None) -> dict:
    import importlib
    reg = json.loads((DISC / "data" / "rules" / "rule_registry.json").read_text(encoding="utf-8"))
    rules = reg.get("rules") or []
    if not rules:
        print("× rule_registry 空——先查路径，33 条失踪不会静默")
        return {}
    by_id = {c["id"]: c for c in case_runner.load_cases()}
    # 基线（每 split 一次，确定性由门 [23] 三 seed 实证）
    base_cache = {}
    for split in splits:
        ids = case_runner.load_ids(split)[:limit] if limit else case_runner.load_ids(split)
        if not ids:
            print("× split=%s 0 例——判红不空跑" % split)
            return {}
        bb = {}
        for cid in ids:
            try:
                bb[cid] = _binaries(case_runner.run_case(by_id[cid]), by_id[cid])
            except Exception:
                bb[cid] = (None, None, "ERR")
        base_cache[split] = (ids, bb)
    rows = []
    for r in rules:
        rid = r.get("rule_id", "?")
        anchors = parse_impl(r.get("impl", ""))
        if not anchors:
            rows.append({"rule_id": rid, "class": "不可单切", "note":
                         "impl 为裸行号/整文件/章节锚，无函数落点（不硬造开关）"})
            continue
        per_split = {}
        crashes = fired = changed = 0
        bind_hits = []
        unresolved_mods = []
        for split, (ids, bb) in base_cache.items():
            var = {}
            for cid in ids:
                counter = {"refs": 0}
                undos = []
                try:
                    for mod_name, fn_name in anchors:
                        got = _patch_binding(mod_name, fn_name, counter)
                        if got is None:
                            if mod_name not in unresolved_mods:
                                unresolved_mods.append(mod_name)
                            raise ImportError(mod_name)
                        u, n = got
                        undos.append(u)
                        bind_hits.append(n)
                    eng = case_runner.run_case(by_id[cid])
                    var[cid] = _binaries(eng, by_id[cid])
                except Exception:
                    crashes += 1
                    var[cid] = None
                finally:
                    for u in undos:
                        u()
                fired += 1 if counter["refs"] else 0
                changed += 1 if (var[cid] is not None and var[cid][2] != bb[cid][2]) else 0
            b = c = nsc = 0
            vb = vc = tb = tc = vn = tn = 0
            for cid in ids:
                bv, vy = bb[cid], var.get(cid)
                if vy is None:
                    continue
                if bv[0] is not None and vy[0] is not None:
                    vn += 1
                    if bv[0] == 1 and vy[0] == 0:
                        vb += 1
                    elif bv[0] == 0 and vy[0] == 1:
                        vc += 1
                if bv[1] is not None and vy[1] is not None:
                    tn += 1
                    if bv[1] == 1 and vy[1] == 0:
                        tb += 1
                    elif bv[1] == 0 and vy[1] == 1:
                        tc += 1
            per_split[split] = {"v": [vb, vc, vn], "t": [tb, tc, tn],
                                "p_v": round(mcnemar_exact(vb, vc), 3),
                                "p_t": round(mcnemar_exact(tb, tc), 3)}
        total_cases = sum(len(ids) for ids, _ in base_cache.values())
        if unresolved_mods:
            cls, note = "指针未落地", "模块不可导入：%s" % ",".join(unresolved_mods)
        elif fired == 0:
            cls, note = "全程未触发", "%d 例 refs 全 0——该函数锚点在本语料从未被调用（死接线嫌疑）" % total_cases
        elif crashes >= total_cases:
            cls, note = "结构依赖", "补丁即崩（返回形状被下游强依赖）——不可单切"
        elif changed == 0:
            cls, note = "零贡献", "触发 %d/%d 例而输出观测零变化%s" % (
                fired, total_cases, ("（崩溃 %d——部分例结构依赖）" % crashes) if crashes else "")
        else:
            cls, note = "有影响", "触发 %d｜变化 %d｜崩溃 %d" % (fired, changed, crashes)
        rows.append({"rule_id": rid, "class": cls, "note": note, "fired": fired,
                     "changed": changed, "crashes": crashes, "splits": per_split})
        print("  %-34s %-6s %s" % (rid, cls, note))
    out = {"generated_at": datetime.now().isoformat(timespec="seconds"),
           "splits": list(base_cache), "rows": rows}
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    cnt = Counter(r["class"] for r in rows)
    print("═ 扫掠分类汇总 ═ " + "｜".join("%s %d" % (k, v) for k, v in cnt.most_common()))
    return out


def _binaries(eng: dict, case: dict):
    """(verdict_hit|None, yingqi_top1|None, score_probe) —— 与 evaluate 同一 strict 口径。"""
    if "error" in eng:
        return None, None, ""
    dims = evaluate.score_case(eng, case.get("expected") or {}, "strict", case=case)
    vw, aw, _ = dims.get("verdict", (0, 0, ""))
    vy, ay, _ = dims.get("yingqi", (0, 0, ""))
    v = None if aw == 0 else (1 if vw == W_V else 0)
    y = None if ay == 0 else (1 if vy == W_Y else 0)
    probe = "%s|%s|%.3f|%s" % (eng.get("verdict"), (eng.get("yingqi_branches") or [])[:1],
                               float(eng.get("final_score") or 0.0),
                               ",".join(str(x) for x in (eng.get("yingqi_branches") or [])))
    return v, y, probe


def run_ablation(toggle: str, splits, limit=None):
    if toggle not in TOGGLES:
        print("× 未注册的消融目标：%s（可用：%s）——不许临时造补丁冒充归因" % (toggle, ",".join(TOGGLES)))
        return None
    desc, patch = TOGGLES[toggle]()
    by_id = {c["id"]: c for c in case_runner.load_cases()}
    report = {}
    for split in splits:
        ids = case_runner.load_ids(split)
        if limit:
            ids = ids[:limit]
        if not ids:
            print("× split=%s 解析 0 例——显形，不当 0% 用" % split)
            return None
        base = {}
        counter = {"refs": 0}
        for cid in ids:
            try:
                eng = case_runner.run_case(by_id[cid])
            except Exception as e:  # noqa: BLE001
                eng = {"id": cid, "error": str(e)}
            base[cid] = _binaries(eng, by_id[cid])
        undo = patch(counter)
        var = {}
        try:
            for cid in ids:
                try:
                    eng = case_runner.run_case(by_id[cid])
                except Exception as e:  # noqa: BLE001
                    eng = {"id": cid, "error": str(e)}
                var[cid] = _binaries(eng, by_id[cid])
        finally:
            undo()
        changed = sum(1 for cid in ids if base[cid][2] != var[cid][2])
        if changed == 0 and counter.get("refs", 0) == 0:
            print("× [%s] %s：补丁 0 引用 0 变化——未接线（死补丁，§四.8），中止归因"
                  % (split, toggle))
            return None
        if changed == 0:
            print("  · [%s] %s：规则被引用 %d 次而输出零变化——本语料面**零贡献**，如实记录不判死"
                  % (split, toggle, counter.get("refs", 0)))
        out = {"n": len(ids), "probe_changed_cases": changed,
               "rule_refs": counter.get("refs", 0)}
        for dim, idx in (("verdict", 0), ("yingqi_top1", 1)):
            sc = [cid for cid in ids if base[cid][idx] is not None and var[cid][idx] is not None]
            b = sum(1 for cid in sc if base[cid][idx] == 1 and var[cid][idx] == 0)
            c = sum(1 for cid in sc if base[cid][idx] == 0 and var[cid][idx] == 1)
            rate0 = sum(base[cid][idx] for cid in sc) / len(sc) * 100 if sc else None
            rate1 = sum(var[cid][idx] for cid in sc) / len(sc) * 100 if sc else None
            flipped = [cid for cid in sc if base[cid][idx] != var[cid][idx]][:6]
            out[dim] = {"n_scorable": len(sc), "base": round(rate0, 1) if sc else None,
                        "var": round(rate1, 1) if sc else None, "b": b, "c": c,
                        "p_mcnemar": round(mcnemar_exact(b, c), 4), "flipped": flipped}
        report[split] = out
        for dim in ("verdict", "yingqi_top1"):
            d = out[dim]
            if not d["n_scorable"]:
                print("  %s｜%s：可评 0 例（显形，不充 0%）" % (split, dim))
                continue
            print("  %s｜%s：基线 %.1f%% → 消融 %.1f%%（Δ%+.1fpt）不一致对 b=%d c=%d "
                  "McNemar p=%.4f" % (split, dim, d["base"], d["var"], d["var"] - d["base"],
                                       d["b"], d["c"], d["p_mcnemar"]))
            if d["flipped"]:
                print("      翻转例：%s" % " ".join(d["flipped"]))
    return {"toggle": toggle, "desc": desc, "splits": report}


def cmd_selftest() -> int:
    fails = []
    # 1) 数学自检：mcnemar 精确值对拍（b=0,c=0→1.0；b=1,c=0→0.5；b=5,c=0→1/32*2 截 1→0.0625）
    checks = [((0, 0), 1.0), ((1, 0), 1.0), ((2, 0), 0.5), ((5, 0), 0.0625)]
    for (bc, want) in checks:
        got = mcnemar_exact(*bc)
        if abs(got - want) > 1e-9:
            fails.append("McNemar 对拍错 b=%d c=%d：%s≠%s" % (bc[0], bc[1], got, want))
    # 2) 未知目标 → 拒
    buf = io.StringIO()
    from contextlib import redirect_stdout
    with redirect_stdout(buf):
        r = run_ablation("__no_such__", ["tune"], limit=1)
    if r is not None:
        fails.append("未知消融目标未被注册表拒绝")
    # 3) 死补丁防护：patch 0 引用 0 变化 → 必须判死中止
    saved = dict(TOGGLES)
    def _t_dead():
        def patch(counter):
            return lambda: None
        return ("死补丁夹具（自测专用）", patch)
    TOGGLES["__dead__"] = _t_dead
    with redirect_stdout(buf):
        r2 = run_ablation("__dead__", ["tune"], limit=1)
    TOGGLES.clear()
    TOGGLES.update(saved)
    if r2 is not None:
        fails.append("死补丁（0 引用 0 变化）未被判死，归因会静默空转")
    # 3b) 零贡献≠死补丁：pass-through 包装计数引用而输出无变化 → 必须继续并如实记零贡献
    def _t_passthru():
        def patch(counter):
            orig = step3.compute_day_modifier

            def wrapper(*a, **k):
                counter["refs"] = counter.get("refs", 0) + 1
                return orig(*a, **k)
            step3.compute_day_modifier = wrapper
            return lambda: setattr(step3, "compute_day_modifier", orig)
        return ("引用计数但零变化夹具（自测专用）", patch)
    TOGGLES["__passthru__"] = _t_passthru
    with redirect_stdout(buf):
        r2b = run_ablation("__passthru__", ["tune"], limit=1)
    TOGGLES.pop("__passthru__", None)
    if r2b is None or r2b["splits"]["tune"]["rule_refs"] <= 0:
        fails.append("零贡献面被误判死/引用计数未接线（r=%s）" % (r2b is not None))
    # 5) 可复现：rank_reverse --limit 3 连跑两次，翻转集与 b/c 必须逐一致
    r3 = None
    r4 = None
    with redirect_stdout(buf):
        r3 = run_ablation("rank_reverse", ["tune"], limit=3)
        r4 = run_ablation("rank_reverse", ["tune"], limit=3)
    if not r3 or not r4:
        fails.append("rank_reverse 自检跑不通（可评 0 例？查接线）")
    elif json.dumps(r3["splits"], sort_keys=True) != json.dumps(r4["splits"], sort_keys=True):
        fails.append("同一消融两次结果不一致——引擎确定性或台架隔离有问题")
    # 6) 扫掠锚点解析（第一百八十六批）：函数锚可抽、裸行号不可抽
    a = parse_impl("scripts/effects.py:analyze_repetition(786)/analyze_repetition_deep(914)")
    if a != [("effects", "analyze_repetition")]:
        fails.append("parse_impl 函数锚抽错：%r" % a)
    if parse_impl("scripts/step3.py:583（真空/假空判定）") or parse_impl("scripts/step4.py:4.3/4.3b（贪合忘克）"):
        fails.append("裸行号/小节锚被当成函数锚（会造出假开关）")
    if parse_impl("scripts/step3.py:fn_not_anywhere 与 step2.py:583（裸行号）") != [("step3", "fn_not_anywhere")]:
        fails.append("parse_impl 正则过窄或过宽（假函数锚抽错/裸行号误抽）")
    # 7) mini 扫掠端到端：1 例 tune 跑全注册表不许崩在框架自身
    with redirect_stdout(buf):
        sw = sweep(["tune"], 1, None)
    if not sw or "rows" not in sw:
        fails.append("mini 扫掠框架跑不通")
    if fails:
        print("× selftest：")
        for f in fails:
            print("  · " + f)
        return 1
    print("√ selftest：McNemar 对拍/未注册拒绝/0引用判死/引用而零变化记零贡献/两次一致 全过")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="规则消融台架 v0（配对 McNemar，古籍吻合面归因）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--list", action="store_true", help="列出已注册的消融目标")
    ap.add_argument("--toggle", default=None)
    ap.add_argument("--sweep", action="store_true", help="注册表驱动全量扫掠（第一百八十六批·A2）")
    ap.add_argument("--splits", nargs="*", default=["wikisource_holdout"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=None, help="扫掠报告 JSON 落盘路径（建议 scratch/）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    if args.list:
        for name, fn in TOGGLES.items():
            print("%-14s %s" % (name, fn()[0]))
        return 0
    if args.sweep:
        res = sweep(args.splits, args.limit, args.out)
        print("\n注：分类六档——不可单切（锚点是裸行号）/指针未落地（模块导不进）/"
              "全程未触发（死接线嫌疑）/结构依赖（补丁即崩）/零贡献（触发而输出不变）/"
              "有影响（出 Δ 与 McNemar）。零贡献≠规则无书据，只说在本语料面上不改判卷——"
              "裁决链去留须连书证一起读（§四.3），本表不越权代裁。")
        return 0 if res else 1
    if not args.toggle:
        ap.print_help()
        return 2
    res = run_ablation(args.toggle, args.splits, args.limit)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=1) if res else "{}")
        return 0 if res else 1
    print("\n注：归因对象是古籍吻合面的边际贡献，非现实效度（铁律三）；"
          "外部集只报数不设门槛（§四.3）。")
    return 0 if res else 1


if __name__ == "__main__":
    raise SystemExit(main())
