# -*- coding: utf-8 -*-
"""liuren 引文逐字订正 + `verbatim_policy` 登记块刷新（默认 dry-run，--write 落盘）。

背景：独立验证指出 men.昴星/伏吟/返吟 三条 basis 去掉了书源夹注与书名号，
「逐字」声明比实际严。本脚本把这三条**还原为书源原样形态**（含夹注、「《玉厯》」），
使全部外置引文成为书源去空白后的逐字子串。

两件事，各自幂等：
  1) 三条 basis 的还原 —— 新值**直接从书源行取出**（不手敲），不手敲、不改语义字段；
  2) `verbatim_policy` 登记块刷新 —— 口径文案的唯一真值源即本文件 POLICY，
     数据里的块与之不符就重写（防「数据里的口径」与「门里断言的覆盖」漂移）。

落盘前自检全量逐字（条数由 dev_tools/check.py::verbatim_inventory 实算，本文件不写条数）；
dry-run 默认，`--write` 落盘；无关字节不变（保持原换行风格）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DISC = ROOT / "disciplines" / "liuren"
SRC = ROOT / "data" / "sources" / "liu-ren-da-quan.wikitext.txt"
VD = DISC / "data" / "verdicts.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))     # 与门共用同一计算处
from check import verbatim_inventory  # noqa: E402

# 书源行号 → data 里的键（1-based 行号，取自 data/sources/liu-ren-da-quan.wikitext.txt 卷一）
# 三条 basis 的「行号→键」定义**只此一份**：数据里的 verbatim_policy 只声明规则、不列清单。
FIXES = {
    ("men", "昴星", "basis"): 32,
    ("men", "伏吟", "basis"): 44,
    ("men", "返吟", "basis"): 48,
}

NEW_COMMENT = (
    "引文全部逐字取自 data/sources/liu-ren-da-quan.wikitext.txt 卷一「入手法」（四库本）："
    "men[*].basis 与 tianjiang[*].verse 均为书源去空白后的**逐字子串**，"
    "含书源夹注（如「论初传也」）与书名号（如「《玉厯》」），异体字照录不作归一。"
    "如将来对某条作归化（去夹注/去书名号/正字），必须登记在 verbatim_policy.normalized，否则门 [1d] 判败。"
    "引文条数不在此写死——见门 dev_tools/check.py [1d] 的运行时实算。"
)

POLICY = {
    "what": "引文逐字口径与归化登记（门 dev_tools/check.py [1d] 机械断言）。",
    "scope": "verdicts：men[*].basis + tianjiang[*].verse；kemu：课目 verse + 课目 note。"
             "条数与逐字清单由 dev_tools/check.py::verbatim_inventory 运行时实算，"
             "本块不写条数（防语料增长后多处数字互相说谎）。",
    "rule": "每条必须是六壬书源（data/sources/liu-ren-da-quan*.wikitext.txt）去空白后的连续子串；"
            "字符级保留标点与书名号，含书源小字夹注、异体字照录不归一。",
    "normalized": [],
    "checked_by": "dev_tools/check.py::check_verbatim（[1d] 引文逐字门，清单由 verbatim_inventory 实算）",
}


def _strip(s: str) -> str:
    return "".join(s.split())


def _policy_block(nl: str) -> str:
    """生成与文件缩进一致的登记块文本（含尾随逗号，供插在 preamble 之前）。"""
    body = json.dumps({"verbatim_policy": POLICY}, ensure_ascii=False,
                      indent=1).split("\n")[1:-1]
    return nl.join(body) + ","


def main() -> int:
    ap = argparse.ArgumentParser(description="liuren 引文逐字订正（默认 dry-run）")
    ap.add_argument("--write", action="store_true", help="落盘 data/verdicts.json")
    args = ap.parse_args()

    src_text = SRC.read_text(encoding="utf-8")
    src_lines = src_text.splitlines()
    src_flat = _strip(src_text)
    raw = VD.read_text(encoding="utf-8", newline="")
    data = json.loads(raw)
    nl = "\r\n" if "\r\n" in raw else "\n"      # 保持文件原有换行风格，不整文件 diff
    patched = raw

    # ---- 1) 三条 basis 还原 ----
    changed_vals = []
    for key, ln in FIXES.items():
        section, name, field = key
        val = src_lines[ln - 1].strip()
        assert _strip(val) in src_flat, f"书源第 {ln} 行不在书源内？"
        old = data[section][name][field]
        if old == val:
            continue
        changed_vals.append(key)
        needle, repl = (json.dumps(old, ensure_ascii=False),
                        json.dumps(val, ensure_ascii=False))
        assert patched.count(needle) == 1, f"旧值在原文中不唯一：{needle[:40]}"
        patched = patched.replace(needle, repl)
        print(f"[{section}.{name}.{field}] （书源第 {ln} 行）")
        print(f"  旧: {old}")
        print(f"  新: {val}")
    print(f"{len(FIXES)} 条 basis："
          + ("已是书源原样形态，无需订正" if not changed_vals
             else f"已还原 {len(changed_vals)} 条：{'、'.join('.'.join(k) for k in changed_vals)}"))

    # ---- 2) _comment 口径说明 ----
    old_c = json.dumps(data["_comment"][1], ensure_ascii=False)
    if data["_comment"][1] != NEW_COMMENT:
        assert patched.count(old_c) == 1, "旧 _comment[1] 不唯一"
        patched = patched.replace(old_c, json.dumps(NEW_COMMENT, ensure_ascii=False))
        print("_comment 口径说明：已改写")

    # ---- 3) verbatim_policy 登记块 ----
    block = _policy_block(nl)
    lines = patched.split(nl)
    idx = [i for i, l in enumerate(lines) if l.lstrip().startswith('"verbatim_policy"')]
    if idx:
        i = idx[0]
        j = next(k for k in range(i, len(lines)) if lines[k].rstrip() in (" },", " }"))
        old_block = nl.join(lines[i:j + 1])
        lines[i:j + 1] = block.split(nl)
        patched = nl.join(lines)
        print("verbatim_policy：" + ("与口径真值源一致，无需刷新" if old_block == block
                                     else "已按口径真值源刷新"))
    else:
        anchor = ("键变更须过断语键一致性检查。\"" + nl + " ]," + nl + " \"preamble\":")
        assert patched.count(anchor) == 1, "锚点（_comment 数组尾）不唯一"
        patched = patched.replace(
            anchor, "键变更须过断语键一致性检查。\"" + nl + " ]," + nl
            + block + nl + " \"preamble\":")
        print("verbatim_policy：新插入登记块")

    # ---- 4) 落盘前全量逐字自检（与门 [1d] 共用 verbatim_inventory，条数实算）----
    after = json.loads(patched)
    assert after["_comment"][1] == NEW_COMMENT
    assert after["verbatim_policy"] == POLICY, "登记块与口径真值源不一致"
    inv = verbatim_inventory(after)
    print(f"落盘前自检：{len(inv['items'])} 条引文"
          f"（verdicts {inv['n_verdicts']} + 课目 {inv['n_kemu']}）"
          f"；非逐字={inv['non_verbatim']}；登记={sorted(inv['registered'])}")
    assert not inv["non_verbatim"], f"仍有非逐字条目，拒绝写盘：{inv['non_verbatim']}"
    assert not inv["stale"], f"归化登记与实测不符（陈旧登记）：{inv['stale']}"

    if patched == raw:
        print("\n文件无需改动（幂等），退出 0。")
        return 0
    if args.write:
        VD.write_text(patched, encoding="utf-8", newline="")
        print(f"\n已写入 {VD}")
    else:
        print("\ndry-run（未写盘）；加 --write 落盘。")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
