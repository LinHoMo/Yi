# -*- coding: utf-8 -*-
"""批次号体检器（第两百三十批）——229 批一次性探针的常设化（"随月巡可重放"须有可放之物）。

判据（两科 CHANGELOG 的 `^## <日期> 第X批` 标题行）：
  U 唯一性：同一标题号不得出现两次（正文提及不算——^## 锚是判据的一半）；
  M 单调性：176 批后（现代史）新科标题号须随文件位置严格降序（newest-first 契约）；
  字符类必须含「两」（229 批首版漏之致 200+ 全漏检——假零重复，教训铸成 fixture）。
本器是**审计工具不是门**（176 冻结条款：不新增守台账类拦截）——月巡第④步调用，异常显名报告。

    python dev_tools/batchnum_audit.py            # 两科体检
    python dev_tools/batchnum_audit.py --selftest # fixture：漏「两」必假阴、带锚版必抓真重复
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
ROOT = DISC.parent

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CN = {"〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
      "六": 6, "七": 7, "八": 8, "九": 9}
HEAD_RE = re.compile(r"^## \d{4}-\d{2}-\d{2} 第([零〇一二两三四五六七八九十百千]+)批", re.M)
MODERN = 176


def parse_cn(s: str) -> int:
    tot = num = 0
    for ch in s:
        if ch in CN:
            num = num * 10 + CN[ch]
        elif ch == "十":
            tot += (num or 1) * 10; num = 0
        elif ch == "百":
            tot += (num or 1) * 100; num = 0
        elif ch == "千":
            tot += (num or 1) * 1000; num = 0
    return tot + num


def audit(text: str):
    heads = [parse_cn(x) for x in HEAD_RE.findall(text)]
    heads = [h for h in heads if h > 0]
    dup = sorted({h for h in heads if heads.count(h) > 1})
    mod = [h for h in heads if h >= MODERN]
    disorder = [f"{mod[i]}在{mod[i+1]}之前(文件序)" for i in range(len(mod) - 1) if mod[i] < mod[i+1]]
    return heads, dup, disorder


def selftest() -> int:
    fails = []
    with tempfile.TemporaryDirectory(prefix="yi_bn_st_") as td:
        f = Path(td) / "log.md"
        f.write_text(
            "# CH\n\n"
            "## 2026-10-21 第两百零一批（两科）：新批\n\n"
            "## 2026-10-21 第两百批：新批\n\n"
            "正文里也提一句 第两百零一批 以证锚有效。\n\n"
            "## 2026-10-21 第一百九十九批：旧批\n", encoding="utf-8")
        heads, dup, dis = audit(f.read_text(encoding="utf-8"))
        if heads != [201, 200, 199]:
            fails.append("字符类/锚失效：%r（『两』或正文提及未正确处置）" % heads)
        if dup or dis:
            fails.append("干净样本误报：dup=%r dis=%r" % (dup, dis))
        f.write_text(f.read_text(encoding="utf-8").replace(
            "第两百批：新批", "第两百零一批：重复者"), encoding="utf-8")
        heads2, dup2, _ = audit(f.read_text(encoding="utf-8"))
        if dup2 != [201]:
            fails.append("真重复未抓：%r" % dup2)
        f.write_text("# C\n\n## 2026-10-21 第两百零一批\n\n## 2026-10-21 第两百二十批\n\n",
                     encoding="utf-8")
        _, _, dis3 = audit(f.read_text(encoding="utf-8"))
        if not dis3:
            fails.append("乱序（201 在 220 前）未报——单调判据无牙")
    print("√ selftest：锚+字符类/正文提及免疫/真重复必抓/乱序必报 全过" if not fails
          else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="批次号标题级体检（唯一+单调；审计工具非门）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    bad = 0
    for d in ("liuyao", "bazi"):
        t = (ROOT / d / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
        heads, dup, dis = audit(t)
        mod = [h for h in heads if h >= MODERN]
        ok = not dup and not dis
        print("%s%s：标题 %d 个，现代史 %d 个（%d→%d）｜重复 %r｜乱序 %r"
              % ("√ " if ok else "× ", d, len(heads), len(mod),
                 max(mod) if mod else 0, min(mod) if mod else 0, dup, dis))
        bad += 0 if ok else 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
