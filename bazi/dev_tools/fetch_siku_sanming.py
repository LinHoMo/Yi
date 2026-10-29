# -*- coding: utf-8 -*-
"""抓取维基文库《四庫全書本·三命通會》卷一–卷十二原文，落盘为新底本。

    python dev_tools/fetch_siku_sanming.py [--check]

为什么抓它（第三百二十七批）：在库底本 `data/sources/sanming_tonghui_dz.dz.txt`
开头即「钦定四库全书　子部七　三命通会　术数类五」＋四库提要＋「乾隆四十四年九月恭校」——
**它本身就是四库全书本**，只是经殆知阁渠道转录。维基文库把同一底本按卷切成 12 个页面
（`三命通會 (四庫全書本)/卷01`…`/卷12`）逐卷数字化，于是同一本书有了**两条转录渠道**。
两条渠道的差异不是「版本差异」，是**转录脱漏**——这正是校勘要找的东西：哪一段在某一渠道里掉了字。

**本底本无标点**（四库扫描版原文如此，页首自注「加標點請另外建立頁面」），与在库 dz 本同。

落盘约定（**刻意避开 `_source_titles()` 的映射**）：
- 底本文件 `sanming_tonghui_siku.wikitext.txt`；
- 元数据 `sanming_tonghui_siku.meta.json`（**不叫 `*.provenance.json`**）。
  原因：八字科 `dev_tools/check_source_readings.py` 的 `_source_titles()` 硬编码
  「`*.provenance.json` → 同名 `*.dz.txt`」，任何 `*.provenance.json` 都会被登记成
  书名 → 底本文件名。本底本不是 `.dz.txt`，若登记成 provenance 会指向一个不存在的
  `.dz.txt` 文件，污染既有回验的书名映射。故元数据另起名，台账信息写在这里。

只做字符级保存：原文一字不改、不加标点、不转简体、不补缺。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DISC = Path(__file__).resolve().parents[1]
OUT = DISC / "data" / "sources" / "sanming_tonghui_siku.wikitext.txt"
META = DISC / "data" / "sources" / "sanming_tonghui_siku.meta.json"

API = "https://zh.wikisource.org/w/api.php"
UA = "Yi-corpus-audit/1.0 (siku-edition Sanming Tonghui transcription audit)"
VOLUMES = list(range(1, 13))
PAGE = "三命通會 (四庫全書本)/卷{:02d}"
# 卷首自带的模板/包装，字符级保留（与既有 wikitext 底本同构），只把卷次写成可 grep 的标记
VOL_MARK = re.compile(r"^<!-- ==== 三命通會 卷([0-9]{2}) ==== -->$", re.M)


def fetch(title: str) -> str:
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "revisions",
        "rvslots": "*", "rvprop": "content", "titles": title, "redirects": "1",
    })
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as resp:
        d = json.loads(resp.read().decode("utf-8"))
    pages = d.get("query", {}).get("pages", {})
    for _pid, pg in pages.items():
        if "missing" in pg:
            raise SystemExit(f"页面不存在（missing）：{title}")
        rev = pg.get("revisions") or []
        if not rev:
            raise SystemExit(f"页面无 revisions：{title}")
        return rev[0]["slots"]["main"]["*"]
    raise SystemExit(f"页面返回异常：{title}")


def build() -> tuple[str, list[dict]]:
    parts, per = [], []
    for n in VOLUMES:
        title = PAGE.format(n)
        text = fetch(title)
        per.append({
            "volume": n, "page": title, "chars": len(text),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        })
        parts.append(f"<!-- ==== 三命通會 卷{n:02d} ==== -->\n{text}")
        print(f"  卷{n:02d} {len(text):7d} 字  {title}")
        time.sleep(0.6)          # 对公共 API 保持礼貌
    return "\n".join(parts), per


def main() -> int:
    ap = argparse.ArgumentParser(description="抓取四库本《三命通会》卷一至卷十二")
    ap.add_argument("--check", action="store_true", help="只比对落盘文件与元数据，不联网")
    args = ap.parse_args()

    if args.check:
        meta = json.loads(META.read_text(encoding="utf-8"))
        raw = OUT.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        ok = sha == meta.get("sha256")
        print(f"底本 {OUT.name}：{len(raw)} bytes  sha256={sha[:16]}…  与元数据一致={ok}")
        return 0 if ok else 1

    print("抓取《四庫全書本·三命通會》卷一–卷十二：")
    text, per = build()
    OUT.write_text(text, encoding="utf-8", newline="\n")
    raw = OUT.read_bytes()

    meta = {
        "key": "sanming_tonghui_siku",
        "kind": "八字",
        "title": "三命通會（四庫全書本·維基文庫轉錄）",
        "work": "《三命通会》明·万民英撰（四库全书本）",
        "site": "zh.wikisource.org",
        "api": API,
        "retrieved": "2026-10-29",
        "license": "原作明代，公有领域；转录本依维基文库授权条款",
        "source_file": "data/sources/sanming_tonghui_siku.wikitext.txt",
        "chars": len(text),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "sha256_convention": "对落盘字节取哈希（与在盘文件一致）",
        "eol_on_disk": "LF",
        "punctuation": "无标点（四库扫描版原文如此，页首自注「加標點請另外建立頁面」）",
        "volumes": per,
        "relation_to_dz": (
            "与在库 `sanming_tonghui_dz.dz.txt`（殆知阁转录）是**同一四库底本的两条转录渠道**，"
            "不是两个版本；两者差异即转录脱漏，可逐段对拍。"
        ),
        "note": (
            "本文件**不是** `*.provenance.json`：八字科 `_source_titles()` 硬编码"
            "「`*.provenance.json` → 同名 `*.dz.txt`」，登记成 provenance 会指向不存在的 `.dz.txt`，"
            "污染既有回验的书名映射，故元数据另起 `*.meta.json`。"
        ),
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n写出 {OUT.relative_to(DISC)}（{len(text)} 字 / {len(raw)} 字节）")
    print(f"写出 {META.relative_to(DISC)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
