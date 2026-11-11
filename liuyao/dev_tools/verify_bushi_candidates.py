# -*- coding: utf-8 -*-
"""《卜筮全书》候选池同源复验（第 546 批，只读）。

为什么需要：本批把《卜筮全书》主段 L5408–L5566 与 L5706 段的真案逐字签成候选池。
与 542 批《易林補遺》候选池同型，有两个静默退化面——① 引文被手抄改字（不转简／不改字是
AGENTS.md §二 引文条的硬要求）；② 候选池被误并进评分集，于是「永不参与调参」变空话，
而现有 [38]/[43] 门都是白名单制、扫不到它。另加一条：去重漏判会导致《黄金策》承袭同案
被当新案入册（545 批已确证本书与增删／正宗同源）。

本器仿 519 批构建器 `--check` 只读复验范式，逐条对拍：底本 sha256 三方一致、每条引文是
对应底本行的逐字子串、ID 零泄漏进 case_splits、整池无 expected／verdict 映射（防反推）、
8 案顺序与覆盖完整、excluded 五项均带承袭同案证据、预注册在册（547 批已按 §四 一次性开卷：
状态＝已开卷一次·逐例红绿·无率值，与 open_result 成对出现，n<30 不出率值）。
**不写任何文件**；`--selftest` 全部在内存里注入负例，不写真盘（526 批教训）。

    python dev_tools/verify_bushi_candidates.py
    python dev_tools/verify_bushi_candidates.py --selftest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
POOL = DISC / "data" / "cases" / "bushi_quanshu_candidates.json"
SPLITS = DISC / "data" / "cases" / "case_splits.json"

EXPECTED_N = 8
EXPECTED_EXCLUDED = 5
ID_PREFIX = "BQS"
# 548 批 §四 入册授权：本候选池可还原案已正式转建为 `bushi_quanshu_holdout`
# （BQS001/003/004/005/006；BQS002/007/008 缺月支不入册）。候选 ID 经授权 holdout 键
# 进 case_splits 是入册结果，不算泄漏；泄漏进其他分片仍须判红。
ENROLLED_SPLIT = "bushi_quanshu_holdout"
ALLOWED_STATUS = ("未开卷·不入册·不出分", "已开卷一次·逐例红绿·无率值",
                  "已入册·bushi_quanshu_holdout")


def load_pool() -> dict:
    return json.loads(POOL.read_text(encoding="utf-8"))


def load_lines(source_rel: str) -> list[str]:
    return (DISC / source_rel).read_text(encoding="utf-8").splitlines()


def split_membership(splits: dict) -> dict[str, set[str]]:
    """id → 它出现的分片键集合（用于「只准进授权 holdout」判定）。"""
    out: dict[str, set[str]] = {}
    for key, val in splits.items():
        if isinstance(val, list):
            for x in val:
                cid = x if isinstance(x, str) else str((x.get("id") if isinstance(x, dict) else x) or "")
                if cid:
                    out.setdefault(cid, set()).add(key)
    return out


def verify(pool: dict, lines: list[str], membership: dict[str, set[str]],
           enrolled_split: str | None = None,
           source_sha: str | None = None, provenance_sha: str | None = None) -> list[str]:
    """纯判据：不读盘、不写盘。返回问题列表（空＝同源）。

    `membership` 为 id→出现分片键集合；`enrolled_split` 为授权入册的 holdout 键。
    候选 ID 出现在 enrolled_split 不算泄漏，出现在其他分片才算；excluded ID 出现在
    任何分片都算泄漏（承袭同案不应入册）。
    """
    bad: list[str] = []
    src = pool.get("source") or {}
    if source_sha and src.get("sha256") != source_sha:
        bad.append("池登记的 sha256 与底本实盘不符")
    if provenance_sha and provenance_sha != source_sha:
        bad.append("provenance 登记的 sha256 与底本实盘不符")

    cases = pool.get("cases") or []
    if len(cases) != EXPECTED_N:
        bad.append(f"候选应为 {EXPECTED_N} 案，实为 {len(cases)}（漏案或并入未登记的案）")
    ids = [c.get("id") for c in cases]
    if len(set(ids)) != len(ids):
        bad.append("ID 重复")
    if any(not str(i).startswith(ID_PREFIX) for i in ids):
        bad.append(f"存在非 {ID_PREFIX} 前缀的 ID")

    prev_line = -1
    prev_pos = -1
    for c in cases:
        cid = c.get("id") or "?"
        quote = c.get("source_quote") or ""
        if not quote:
            bad.append(f"{cid}：source_quote 为空")
            continue
        sl = c.get("source_line")
        if sl is None or sl < 1 or sl > len(lines):
            bad.append(f"{cid}：source_line 越界 {sl}")
            continue
        line = lines[sl - 1]
        pos = line.find(quote)
        if pos < 0:
            bad.append(f"{cid}：引文不是底本 L{sl} 行的逐字子串（被改字／转简／补标点？）")
        else:
            # 跨行按顺序递增：同行的按 pos 递增，换行的按行号递增
            if sl == prev_line and pos <= prev_pos:
                bad.append(f"{cid}：引文在原文中的顺序不对（重排或重复切）")
            elif sl < prev_line:
                bad.append(f"{cid}：source_line 顺序倒退（{sl}<{prev_line}）")
            prev_line, prev_pos = sl, pos
        # 防反推：整池不许出现 expected 块、吉凶映射或卦理派生字段
        if "expected" in c:
            bad.append(f"{cid}：出现 expected 块（§三.4 禁反推）")
        if c.get("verdict") is not None:
            bad.append(f"{cid}：verdict 非 null（散文断语映射吉凶属解读，按 425 批 yiin 口径）")
        for forbidden in ("use_god", "use_god_branch", "yingqi_branches", "direction"):
            if forbidden in c:
                bad.append(f"{cid}：出现派生字段 {forbidden}（本池只登记逐字文本）")

    # excluded 审计：每项须有引文子串证据、理由、且不泄漏进分片
    excl = pool.get("excluded") or []
    if len(excl) != EXPECTED_EXCLUDED:
        bad.append(f"excluded 应为 {EXPECTED_EXCLUDED} 项，实为 {len(excl)}")
    excl_ids = set()
    for e in excl:
        eid = e.get("id") or "?"
        excl_ids.add(eid)
        q = e.get("source_quote") or ""
        sl = e.get("source_line")
        if not q or sl is None or sl < 1 or sl > len(lines) or lines[sl - 1].find(q) < 0:
            bad.append(f"{eid}：excluded 引文非底本 L{sl} 逐字子串或缺失")
        if not e.get("reason"):
            bad.append(f"{eid}：excluded 缺承袭同案理由")
    # 候选 ID 只准进授权 holdout；excluded ID 不准进任何分片
    cand_leaked = []
    for cid in ids:
        hit = (membership.get(cid, set()) - {enrolled_split}) if enrolled_split else membership.get(cid, set())
        if hit:
            cand_leaked.append(cid)
    if cand_leaked:
        bad.append(f"候选 ID 泄漏进 case_splits 非授权分片 {sorted(hit)}：{sorted(cand_leaked)}（永不参与调参被破坏）")
    excl_leaked = sorted(excl_ids & set().union(*membership.values()) if membership else set())
    if excl_leaked:
        bad.append(f"excluded ID 泄漏进 case_splits：{excl_leaked}（承袭同案不应入册）")

    pre = pool.get("preregistration") or {}
    if not pre.get("hypothesis") or not pre.get("decision_rule"):
        bad.append("预注册缺假设或判卷规则（§四）")
    # 547/548 批：允许「已开卷一次」／「已入册」，但状态与开卷记录须成对出现。
    if pre.get("status") not in ALLOWED_STATUS:
        bad.append("预注册状态非法（只允许未开卷／已开卷一次／已入册·bushi_quanshu_holdout）")
    if pre.get("status") in (ALLOWED_STATUS[1], ALLOWED_STATUS[2]):
        op = pool.get("open_result") or {}
        if not op:
            bad.append("状态为已开卷/已入册却缺 open_result")
        elif op.get("aggregate") is not None or op.get("open_count") != 1:
            bad.append("开卷记录含率值或不止一次开封（n<30 只报逐例红绿）")
    elif pool.get("open_result"):
        bad.append("未开卷状态却带 open_result")
    return bad


def run_real() -> list[str]:
    pool = load_pool()
    src_rel = pool["source"]["file"]
    raw_bytes = (DISC / src_rel).read_bytes()
    source_sha = hashlib.sha256(raw_bytes).hexdigest()
    prov = json.loads((DISC / pool["source"]["provenance"]).read_text(encoding="utf-8"))
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    return verify(pool, load_lines(src_rel), split_membership(splits),
                  enrolled_split=ENROLLED_SPLIT,
                  source_sha=source_sha, provenance_sha=prov.get("sha256"))


def selftest() -> int:
    """内存负例：不写真盘。每类损坏都必须被 verify() 抓到，健康副本必须放行。"""
    import copy
    pool = load_pool()
    src_rel = pool["source"]["file"]
    lines = load_lines(src_rel)
    raw_bytes = (DISC / src_rel).read_bytes()
    sha = hashlib.sha256(raw_bytes).hexdigest()
    prov = json.loads((DISC / pool["source"]["provenance"]).read_text(encoding="utf-8"))
    membership = split_membership(json.loads(SPLITS.read_text(encoding="utf-8")))

    def v(p, m=None, sha_override=None):
        return verify(p, lines, membership if m is None else m,
                      enrolled_split=ENROLLED_SPLIT,
                      source_sha=sha_override or sha, provenance_sha=prov.get("sha256"))

    probes = []
    healthy = v(pool)
    probes.append(("健康副本放行", not healthy, healthy))

    p = copy.deepcopy(pool)
    p["cases"][0]["source_quote"] = p["cases"][0]["source_quote"].replace("同人之无妄", "同人之无妄卦", 1)
    probes.append(("引文改字被抓", bool(v(p)), ""))

    p = copy.deepcopy(pool)
    p["cases"][0]["verdict"] = "凶"
    probes.append(("吉凶映射被抓", bool(v(p)), ""))

    p = copy.deepcopy(pool)
    p["cases"][0]["expected"] = {"verdict": "凶"}
    probes.append(("反推 expected 被抓", bool(v(p)), ""))

    p = copy.deepcopy(pool)
    p["cases"] = p["cases"][:7]
    probes.append(("漏案被抓", bool(v(p)), ""))

    # 泄漏只准进授权 holdout；把候选 ID 塞进非授权分片（tune）必须判红
    p = copy.deepcopy(pool)
    leaky = {cid: set(vv) for cid, vv in membership.items()}
    leaky["BQS001"] = (leaky.get("BQS001", set()) | {"tune"})
    probes.append(("ID 泄漏进非授权分片被抓", bool(v(p, m=leaky)), ""))

    p = copy.deepcopy(pool)
    p["source"]["sha256"] = "0" * 64
    probes.append(("底本哈希漂移被抓", bool(v(p, sha_override="0" * 64)), ""))

    p = copy.deepcopy(pool)
    p["preregistration"]["status"] = "已开卷·已出分"
    probes.append(("预注册状态被改被抓", bool(v(p)), ""))

    p = copy.deepcopy(pool)
    p.pop("open_result", None)
    probes.append(("已开卷却缺判卷记录被抓", bool(v(p)), ""))

    p = copy.deepcopy(pool)
    p["open_result"]["aggregate"] = 66.7
    probes.append(("开卷出率值被抓", bool(v(p)), ""))

    p = copy.deepcopy(pool)
    p["preregistration"]["hypothesis"] = ""
    probes.append(("预注册缺假设被抓", bool(v(p)), ""))

    p = copy.deepcopy(pool)
    p["excluded"][0]["source_quote"] = "被篡改的引文"
    probes.append(("excluded 引文非子串被抓", bool(v(p)), ""))

    p = copy.deepcopy(pool)
    p["excluded"][0]["reason"] = ""
    probes.append(("excluded 缺理由被抓", bool(v(p)), ""))

    fails = [f"{name}{('：' + str(detail)) if detail else ''}"
             for name, caught, detail in probes if not caught]
    if fails:
        for f in fails:
            print("  × selftest：" + f)
        return 1
    print(f"  √ selftest：{len(probes)} 类负例全部抓到；健康副本放行（全程内存，真盘零写入）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="卜筮全书候选池同源复验（只读）")
    ap.add_argument("--selftest", action="store_true", help="内存负例自证")
    args = ap.parse_args()
    if args.selftest:
        if selftest() != 0:
            return 1
        bad = run_real()
        for b in bad:
            print("  × " + b)
        if bad:
            return 1
        print("  √ 真盘候选池同源：8 案逐字、5 项 excluded 带承袭证据、零泄漏、无反推、已开卷一次·逐例红绿·无率值")
        return 0
    bad = run_real()
    for b in bad:
        print("  × " + b)
    if bad:
        return 1
    state = (json.loads(POOL.read_text(encoding="utf-8"))
             .get("preregistration", {}).get("status", "?"))
    print(f"  √ 候选池同源：8 案引文逐字命中底本，ID 零泄漏进评分集，预注册状态＝{state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
