# -*- coding: utf-8 -*-
"""《易林補遺》L1279 候选池同源复验（第 542 批，只读）。

为什么需要：本批把一段 617 字的古籍里 7 个真案逐字签成候选池。这类内容有两个
静默退化面——① 引文被手抄改字（不转简／不改字是 AGENTS.md §二 引文条的硬要求，
「涣之垢」的「垢」尤其容易被"顺手 corrected"）；② 候选池被误并进评分集，
于是「永不参与调参」变成一句空话，而现有 [38]/[43] 门都是白名单制、扫不到它。

本器仿 519 批构建器 `--check` 的只读复验范式，逐条对拍：底本 sha256 三方一致、
每条引文是 L1279 行的逐字子串、候选 ID 只进授权 holdout（yilin_buyi_holdout，
泄漏进其他分片判红）、整池无 expected／verdict 映射（防反推）、7 案顺序与覆盖完整、
预注册在册。548 批起本池已按 §四 入册授权正式转建为 `yilin_buyi_holdout`，
故「ID 只进授权 holdout」替代原「零泄漏」语义（防二次误用仍守住）。
**不写任何文件**；`--selftest` 全部在内存里注入负例，不写真盘（526 批教训）。

    python dev_tools/verify_yilin_candidates.py
    python dev_tools/verify_yilin_candidates.py --selftest
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
POOL = DISC / "data" / "cases" / "yilin_buyi_candidates.json"
SPLITS = DISC / "data" / "cases" / "case_splits.json"

SOURCE_LINE = 1279
EXPECTED_N = 7
# 548 批 §四 入册授权：本候选池已正式转建为评分集 `yilin_buyi_holdout`（Form C 单独授权）。
# 「永不参与调参」的语义由「池本身零 expected／verdict」守住；候选 ID 经授权的 holdout 键
# 进 case_splits 是入册的必然结果，不再算泄漏——但泄漏进**其他**分片（tune/holdout 等）
# 仍须判红（防二次误用）。
ENROLLED_SPLIT = "yilin_buyi_holdout"
# 617 是 L1279 行「且如子占父病」到「凡占父母及家主尊长之类」之间的案例段字数，
# 由 542 批切分实测；七案 quote 长度合计须与之相等（防漏案／防重复切）。
EXPECTED_QUOTE_CHARS = 617


def load_pool() -> dict:
    return json.loads(POOL.read_text(encoding="utf-8"))


def line_text(source_rel: str) -> str:
    raw = (DISC / source_rel).read_text(encoding="utf-8")
    lines = raw.splitlines()
    if len(lines) < SOURCE_LINE:
        raise ValueError(f"底本不足 {SOURCE_LINE} 行")
    return lines[SOURCE_LINE - 1]


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


def verify(pool: dict, line: str, membership: dict[str, set[str]],
           enrolled_split: str | None = None,
           source_sha: str | None = None, provenance_sha: str | None = None) -> list[str]:
    """纯判据：不读盘、不写盘。返回问题列表（空＝同源）。

    `membership` 为 id→出现分片键集合；`enrolled_split` 为授权入册的 holdout 键。
    候选 ID 出现在 enrolled_split 不算泄漏，出现在其他分片才算泄漏。
    """
    bad: list[str] = []
    src = pool.get("source") or {}
    if src.get("line") != SOURCE_LINE:
        bad.append(f"source.line 应为 {SOURCE_LINE}，实为 {src.get('line')}")
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
    if any(not str(i).startswith("YLB") for i in ids):
        bad.append("存在非 YLB 前缀的 ID")

    total_chars = 0
    prev_pos = -1
    for c in cases:
        cid = c.get("id") or "?"
        quote = c.get("source_quote") or ""
        if not quote:
            bad.append(f"{cid}：source_quote 为空")
            continue
        total_chars += len(quote)
        pos = line.find(quote)
        if pos < 0:
            bad.append(f"{cid}：引文不是 L1279 行的逐字子串（被改字／转简／补标点？）")
        elif pos <= prev_pos:
            bad.append(f"{cid}：引文在原文中的顺序不对（重排或重复切）")
        else:
            prev_pos = pos
        if c.get("source_line") != SOURCE_LINE:
            bad.append(f"{cid}：source_line 不是 {SOURCE_LINE}")
        # 防反推：整池不许出现 expected 块、吉凶映射或卦理派生字段
        if "expected" in c:
            bad.append(f"{cid}：出现 expected 块（§三.4 禁反推）")
        if c.get("verdict") is not None:
            bad.append(f"{cid}：verdict 非 null（散文断语映射吉凶属解读，按 425 批 yiin 口径）")
        for forbidden in ("use_god", "use_god_branch", "yingqi_branches", "direction"):
            if forbidden in c:
                bad.append(f"{cid}：出现派生字段 {forbidden}（本池只登记逐字文本）")
    if total_chars != EXPECTED_QUOTE_CHARS:
        bad.append(f"七案引文合计 {total_chars} 字，应为 {EXPECTED_QUOTE_CHARS} 字（覆盖不完整）")

    leaked = []
    for cid in ids:
        hit = (membership.get(cid, set()) - {enrolled_split}) if enrolled_split else membership.get(cid, set())
        if hit:
            leaked.append(cid)
    if leaked:
        bad.append(f"候选 ID 泄漏进 case_splits 非授权分片 {sorted(hit)}：{sorted(leaked)}（永不参与调参被破坏）")

    pre = pool.get("preregistration") or {}
    if not pre.get("hypothesis") or not pre.get("decision_rule"):
        bad.append("预注册缺假设或判卷规则（§四）")
    # 543 批：允许「已开卷一次」；548 批：允许「已入册」——状态与开卷记录须成对出现。
    allowed_status = ("未开卷·不入册·不出分", "已开卷一次·逐例红绿·无率值",
                     "已入册·yilin_buyi_holdout")
    if pre.get("status") not in allowed_status:
        bad.append("预注册状态非法（只允许未开卷／已开卷一次／已入册·yilin_buyi_holdout）")
    if pre.get("status") in (allowed_status[1], allowed_status[2]):
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
    return verify(pool, line_text(src_rel), split_membership(splits),
                  enrolled_split=ENROLLED_SPLIT,
                  source_sha=source_sha, provenance_sha=prov.get("sha256"))


def selftest() -> int:
    """内存负例：不写真盘。每类损坏都必须被 verify() 抓到，健康副本必须放行。"""
    pool = load_pool()
    src_rel = pool["source"]["file"]
    line = line_text(src_rel)
    raw_bytes = (DISC / src_rel).read_bytes()
    sha = hashlib.sha256(raw_bytes).hexdigest()
    prov = json.loads((DISC / pool["source"]["provenance"]).read_text(encoding="utf-8"))
    membership = split_membership(json.loads(SPLITS.read_text(encoding="utf-8")))

    def v(p, m=None, sha_override=None):
        return verify(p, line, membership if m is None else m,
                      enrolled_split=ENROLLED_SPLIT,
                      source_sha=sha_override or sha, provenance_sha=prov.get("sha256"))

    import copy
    probes = []
    healthy = v(pool)
    probes.append(("健康副本放行", not healthy, healthy))

    p = copy.deepcopy(pool)
    p["cases"][0]["source_quote"] = p["cases"][0]["source_quote"].replace("观之益", "观之益卦", 1)
    probes.append(("引文改字被抓", bool(v(p)), ""))

    p = copy.deepcopy(pool)
    p["cases"][0]["verdict"] = "凶"
    probes.append(("吉凶映射被抓", bool(v(p)), ""))

    p = copy.deepcopy(pool)
    p["cases"][0]["expected"] = {"verdict": "凶"}
    probes.append(("反推 expected 被抓", bool(v(p)), ""))

    p = copy.deepcopy(pool)
    p["cases"] = p["cases"][:6]
    probes.append(("漏案被抓", bool(v(p)), ""))

    # 泄漏只准进授权 holdout；把候选 ID 塞进非授权分片（tune）必须判红
    p = copy.deepcopy(pool)
    leaky = {cid: set(v) for cid, v in membership.items()}
    # 把 YLB001 额外塞进 tune（非授权分片）
    leaky["YLB001"] = (leaky.get("YLB001", set()) | {"tune"})
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

    fails = [f"{name}{'：' + str(detail) if detail else ''}"
             for name, caught, detail in probes if not caught]
    if fails:
        for f in fails:
            print("  × selftest：" + f)
        return 1
    print(f"  √ selftest：{len(probes)} 类负例全部抓到；健康副本放行（全程内存，真盘零写入）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="易林補遺 L1279 候选池同源复验（只读）")
    ap.add_argument("--selftest", action="store_true", help="内存负例自证")
    args = ap.parse_args()
    if args.selftest:
        if selftest() != 0:
            return 1
        # 负例过了不等于真仓干净（527 批假绿教训）：再跑一次真盘
        bad = run_real()
        for b in bad:
            print("  × " + b)
        if bad:
            return 1
        print("  √ 真盘候选池同源：7 案逐字、零泄漏、无反推、开卷状态合法")
        return 0
    bad = run_real()
    for b in bad:
        print("  × " + b)
    if bad:
        return 1
    state = (json.loads(POOL.read_text(encoding="utf-8"))
             .get("preregistration", {}).get("status", "?"))
    print(f"  √ 候选池同源：7 案引文逐字命中 L1279，ID 只进授权 holdout（yilin_buyi_holdout），预注册状态＝{state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
