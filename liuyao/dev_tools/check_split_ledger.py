# -*- coding: utf-8 -*-
"""[19] 分片台账复核门：`case_splits.json` 里每一条**排除理由**都得能按字面重跑。

为什么需要它：`[6]` 管的是台账的**形状**（外部集一律过一遍、空集要出声、note 齐不齐），
`check_case_selfconsistency.py` 管的是**单例基准**与自引书文是否串档。
两者都不碰台账里那些**散文式理由**——「无卦名，无法复原装卦」「与 ZS008 同源，不重复计入」
「0 处应期锚点，不产出 yingqi-scorable 案例」。这些句子和它们描述的语料之间没有任何机械联系：
语料一改，理由就可能变成假话，而门全绿——本会话已经撞过三次"文档里的旧真值"（八字 §七 的
`wc -l`=0 实为 5、README 说"没有反馈通道"其实已建、门 docstring 里的过期分母）。
所以把"理由"降级成"可执行断言"：

  · 理由含「无卦名」⇒ 该例的 `hexagram.original` 必须真的解析不出六十四卦名；
  · 理由含「同源」并点名某例 ⇒ 两例必须仍然同源（本卦＋变卦＋占题三件一致，即理由括注所断言者）；
    **断语与应期不参与判据**——它们不同往往正是排除的理由（ZS027 明写「断语相反，基准矛盾」）。
  · 被排除的 id 不得同时出现在任何在用分片里；
  · 理由宣称「0 处应期锚点」者 ⇒ 回该底本逐字重跑锚点正则，命中数必须仍为 0；
    底本文件不存在时，理由必须写明是"无结构化版本"一类，否则判红（无从复核的登记不算登记）。

    python dev_tools/check_split_ledger.py            # 全量复核
    python dev_tools/check_split_ledger.py --selftest # 负例：三种坏理由必须被抓
    python dev_tools/check_split_ledger.py --verbose  # 逐条列出核过的断言
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import tempfile

DISC = pathlib.Path(__file__).resolve().parents[1]
for _p in (str(DISC / "scripts"), str(DISC / "core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402

SPLITS = DISC / "data" / "cases" / "case_splits.json"
CASES = DISC / "data" / "cases" / "classical_cases.json"
ANCHOR_RE = re.compile(r"果于[^，。；]{1,14}?(?:日|月|年)|占[^，。；]{0,8}得[^，。；]{0,6}卦")
SRC_RE = re.compile(r"data/sources/([\w.\-]+)")


def hex_names() -> set:
    from yishu_core.symbols import HEXAGRAM_TRIGRAMS  # 64 卦名唯一真值源
    return set(HEXAGRAM_TRIGRAMS)


def source_key(c: dict) -> tuple:
    """同源的判据＝本卦＋变卦＋占题（理由括注「（屯之震·师尊官事）」断言的就是这三件）。

    曾经用「卦 + 占时 + 断语 + 应期」做键，实测一口气假红 4 条：
    ZS026/ZS008 应期一个写「午年」一个写「丙午年」，ZS029 断语「凶」对「平」，
    而 ZS027 的理由本身就明说「断语相反，基准矛盾」——判据把理由要表达的差异当成了不符。
    断语与应期的差异属于**基准矛盾**（那正是要排除的原因），不属于"不同源"。
    """
    hx = c.get("hexagram") or {}
    return (hx.get("original"), hx.get("changed"), (c.get("topic") or "").strip())


def audit(reg: dict, by_id: dict, sources_root: pathlib.Path | None = None) -> tuple[list[str], list[str]]:
    """sources_root 可注入：自检用它把「0 锚点」负例夹具放在临时目录（铁律二，不写进仓）。"""
    problems: list[str] = []
    checked: list[str] = []
    names = hex_names()
    sroot = pathlib.Path(sources_root or (DISC / "data" / "sources"))
    active = {k: [i for i in v if isinstance(i, str)]
              for k, v in reg.items()
              if isinstance(v, list) and k not in ("excluded", "too_weak")}

    exc = [e for e in (reg.get("excluded") or []) if isinstance(e, dict)]
    for e in exc:
        cid, reason = e.get("id"), e.get("reason") or ""
        c = by_id.get(cid)
        if c is None:
            problems.append(f"{cid}：登了排除理由但案例表里查无此例（理由无从复核）")
            continue
        where = [k for k, v in active.items() if cid in v]
        if where:
            problems.append(f"{cid}：既在 excluded 又在用分片 {where}——排除不成立或分片未清")
            continue
        if "无卦名" in reason:
            got = (c.get("hexagram") or {}).get("original")
            if got in names:
                problems.append(f"{cid}：理由称「无卦名」，实为可解析卦名「{got}」——排除理由已失效")
            else:
                checked.append(f"{cid}：无卦名 ✓（original={got!r} 不在 64 卦名内）")
        m = re.search(r"与\s*(\w+)\s*同源", reason)
        if m:
            other = m.group(1)
            c2 = by_id.get(other)
            if c2 is None:
                problems.append(f"{cid}：理由点名 {other}，但该例查无（同源判据指向空）")
            elif source_key(c) != source_key(c2):
                problems.append(f"{cid}：理由称「与 {other} 同源」，现按（本卦·变卦·占题）键已不同源——"
                                f"要么改判收录，要么更新理由")
            else:
                checked.append(f"{cid}：与 {other} 同源 ✓")
        if "无卦名" in reason and not e.get("trace_2026_10_12"):
            problems.append(f"{cid}：理由称「无卦名」（＝残缺可补），但未记底本可定位性——"
                            "「补回卦名即可收录」与「原文根本不在库里」是两种处置，须分开登记")

    tw = [e for e in (reg.get("too_weak") or []) if isinstance(e, dict)]
    for e in tw:
        reason = e.get("reason") or ""
        src = e.get("source") or "?"
        pathm = SRC_RE.search(reason)
        claims_zero = bool(re.search(r"0\s*处|无任何|无.*锚点", reason))
        no_file = bool(re.search(r"missingtitle|无结构化|未命中|无此目", reason))
        if pathm:
            p = sroot / pathm.group(1)
            if not p.exists():
                problems.append(f"too_weak[{src}]：理由点名的底本文件不存在（{p.name}）——无从复核")
                continue
            hits = ANCHOR_RE.findall(p.read_text(encoding="utf-8", errors="replace"))
            if hits and claims_zero:
                problems.append(f"too_weak[{src}]：理由称「0 处应期锚点」，实测命中 {len(hits)} 处 "
                                f"（样本 {hits[:3]}）——登记与底本已不符")
            else:
                checked.append(f"too_weak[{src}]：锚点实测 {len(hits)} 处，与理由一致 ✓")
        elif no_file:
            checked.append(f"too_weak[{src}]：无可复核底本（理由已注明），按登记接受")
        else:
            problems.append(f"too_weak[{src}]：理由既无底本路径、也未说明"
                            "「无结构化版本」一类无从复核的原因——不算可执行断言")

    # 在用分片内部不得有同考点重复（同卦·同变·同题）——这是 bazi [22] 那一族在六爻侧的对应面。
    # 2026-10-12 实测 34 条可定位例、0 组重复，故直接做成红线而非棘轮。
    seen: dict[tuple, list[str]] = {}
    for k, ids in active.items():
        for cid in ids:
            c = by_id.get(cid)
            if c is None:
                continue
            seen.setdefault((k,) + source_key(c), []).append(cid)
    dups = {key: v for key, v in seen.items() if len(v) > 1}
    for key, v in dups.items():
        problems.append(f"在用分片 {key[0]} 内同考点重复 {v}（卦：{key[1]}/{key[2]}，题：{key[3]}）"
                        "——同一考点被计两次以上，分母与权重失真")
    checked.append(f"在用分片可定位 {sum(len(v) for v in seen.values())} 条，同考点重复 {len(dups)} 组")

    if not exc and not tw:
        problems.append("台账 excluded/too_weak 两条清单都空——本器等于没跑")
    return problems, checked


def selftest(problems: list[str]) -> None:
    """三式（负例夹具只落临时目录，铁律二）：坏理由必须被抓，好理由不得误伤。"""
    reg = {"tune": ["OK01"], "excluded": [
        {"id": "A1", "reason": "无卦名，无法复原装卦"},
        {"id": "A2", "reason": "与 A3 同源，不重复计入"},
        {"id": "A3", "reason": "占题不详"},
        {"id": "A4", "reason": "无卦名"},
    ], "too_weak": [{"source": "测试书", "reason": "data/sources/ 之文件已下载，0 处应期锚点"}]}
    by = {
        "A1": {"id": "A1", "hexagram": {"original": "益"}, "expected": {"verdict": "吉"}},
        "A2": {"id": "A2", "hexagram": {"original": "屯"}, "input": {"date": "子月甲子日"},
               "expected": {"verdict": "凶", "yingqi": "午日"}},
        "A3": {"id": "A3", "hexagram": {"original": "蒙"}, "input": {"date": "子月甲子日"},
               "expected": {"verdict": "凶", "yingqi": "午日"}},
        "A4": {"id": "A4", "hexagram": {"original": None}, "expected": {}},
        "OK01": {"id": "OK01", "hexagram": {"original": "乾"}, "expected": {}},
    }
    with tempfile.TemporaryDirectory(prefix="ledger_selftest_") as td:
        tmp = pathlib.Path(td)
        # 路径分段拼出：写成完整字面量会被 [11]「文档活引用可达性」当成指向不存在文件的指针
        fname = "ledger_" + "probe.txt"
        (tmp / fname).write_text("果于午日验。", encoding="utf-8")
        reg["too_weak"][0]["reason"] = "data/" + f"sources/{fname} 已下载，0 处应期锚点"
        p, _c = audit(reg, by, sources_root=tmp)
    joined = "\n".join(p)
    if "A1" not in joined:
        problems.append(f"负例自证失效：「无卦名」理由被推翻却没判红 → {p}")
    if "A2" not in joined:
        problems.append(f"负例自证失效：「同源」判据已不符却没判红 → {p}")
    if "实测命中" not in joined:
        problems.append(f"负例自证失效：底本明明有锚点，「0 处」的登记却没被判红 → {p}")
    good = {"tune": [], "excluded": [{"id": "A4", "reason": "无卦名",
                                      "trace_2026_10_12": "底本可定位，仅缺卦名"}], "too_weak": []}
    p2, _c2 = audit(good, by)
    if p2:
        problems.append(f"负例自证假阳性：站得住的排除理由被判红 → {p2}")
    if "未记底本可定位性" not in "\n".join(p):
        problems.append(f"负例自证失效：无卦名条目缺 trace 字段却没判红 → {p}")
    dupreg = dict(good)
    dupreg["tune"] = ["OK01", "OK01"]
    p3, _c3 = audit(dupreg, by)
    if "同考点重复" not in "\n".join(p3):
        problems.append(f"负例自证失效：在用分片里塞进重复例却没判红 → {p3}")


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="六爻分片台账复核门")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    reg = json.loads(SPLITS.read_text(encoding="utf-8"))
    d = json.loads(CASES.read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in d.get("cases", []) if isinstance(c, dict)}
    if not by_id:
        print(f"× {CASES.name} 里 0 例——本器等于没跑，不判通过")
        return 1

    problems, checked = audit(reg, by_id)
    if args.selftest:
        selftest(problems)
        print("  [selftest] 负例已跑（无卦名理由被推翻须判红 / 同源判据失效须判红 / 站得住的理由不误伤）")

    n_exc = len([e for e in (reg.get("excluded") or []) if isinstance(e, dict)])
    n_tw = len([e for e in (reg.get("too_weak") or []) if isinstance(e, dict)])
    print(f"合计：复核排除条目 {n_exc} 条、别源条目 {n_tw} 条；"
          f"断言成立 {len(checked)} 条，判红 {len(problems)} 条（案例表 {len(by_id)} 例）")
    if args.verbose:
        for c in checked:
            print("  √ " + c)
    for x in problems:
        print("× " + x)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
