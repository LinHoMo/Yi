# -*- coding: utf-8 -*-
"""古籍自验子集收割 v0（第一百七十九批）——只产「盘点册」，不产 expected、不碰评分面。

背景（176 批后续队列·三重对照的历史通道）：现实判卷样本=0 是预测效度的最大瓶颈；
十六部底本里存在一批**书内自注配对**——「断曰…果于丑日起床」这类「预测→后验」句式，
是唯一不需等待现实就能取得的 outcome-level 材料。v0 只做三件事：
  1. 按保守模式族扫描 data/sources/*.txt 的自注句式，逐条落「逐字引文 + 行号 + 状态」；
  2. 状态三分：可联盘候选（有上下文卦/占线索＋时间词）／仅验语／待人工；
  3. 产出盘点册 `data/cases/verifications.json` 与逐书计数，供下一步**人工**构建配对案例。

诚实边界（§三.4/§六.5）：自注只记验不记失（幸存者偏差），本册**不得**直接当命中率证据；
构建正式案例时须按「全录/仅录验」两假设给上下界。本工具不写 expected、不进任何评分集。

    python dev_tools/harvest_verifications.py                 # 收割并落盘
    python dev_tools/harvest_verifications.py --verify        # 复核在册盘点册逐字引文
    python dev_tools/harvest_verifications.py --book zengshan # 只扫某书
    python dev_tools/harvest_verifications.py --selftest      # 负例自证（§四.8）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

SOURCES = DISC / "data" / "sources"
OUT_DEFAULT = DISC / "data" / "cases" / "verifications.json"

BOOK_NAMES = {
    "zengshan_buyi": "增刪卜易", "zengshan_buyi_dz": "增刪卜易(dz)",
    "bushi_zhengzong": "卜筮正宗", "bushi_zhengzong_dz": "卜筮正宗(dz)",
    "bushi_quanshu_dz": "卜筮全書(dz)", "huangjin_ce": "黃金策",
    "huangjince_dz": "黄金策(dz)", "huozhulin": "火珠林", "huozhulin_dz": "火珠林(dz)",
    "jingshi_yizhuan_dz": "京氏易傳(dz)", "duanyi_tianji_dz": "斷易天機(dz)",
    "yiin_dz": "易隱(dz)", "yilin_buyi_dz": "易林補遺(dz)", "yimao_dz": "易冒(dz)",
    "wenwang_jinqianke_dz": "文王金課(dz)", "zhouyi_shangzhan_dz": "周易尚佔(dz)",
}

# 保守模式族：P1 果+时间；P2 后果+述；P3 时间词后有限字内见果；P4 果+验字动词。
# 已知陷阱（合成负例覆盖）：人名「张果元」、议论「若果能」不得入册。
PATTERNS = (
    re.compile(r"果[于至][^，。；！？]{0,6}?(日|月|年|时|旬|载|旦|夕)|果[于至]"),
    re.compile(r"后果[^，。；]{2,20}"),
    re.compile(r"(次日|翌日|旦日|后[一二三四五六七八九十旬百零两0-9]+[日时月年载])[^，。；]{0,10}果"),
    re.compile(r"果[得应卒升见归破愈死]"),
)
EXCLUDE = re.compile(r"果元|花果|仙果|若果|如果|果能")
TIME_RE = re.compile(r"([^，。；！？]{0,2}(?:次日|翌日|旦日|旬日|[一二三四五六七八九十百零两0-9]+|"
                     r"[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]+)[日时月年载])")
GUA_RE = re.compile(r"卦|占|断曰|断日|应爻|用神")


def _book_of(fname: str) -> str:
    return BOOK_NAMES.get(fname.split(".")[0], fname.split(".")[0])


def scan_line(line: str):
    """返回首个合法命中的 (片段, 模式号)；无则 None。"""
    for k, pat in enumerate(PATTERNS):
        for m in pat.finditer(line):
            if EXCLUDE.search(m.group(0)):
                continue
            pos = m.start()
            if line[pos - 1:pos] == "若" or "张果" in line[max(0, pos - 2):pos]:
                continue  # 紧邻前字构成「若果/张果」——非验语
            return m.group(0), k
    return None


def harvest(files):
    records = []
    for f in sorted(files):
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for i, ln in enumerate(lines, 1):
            hit = scan_line(ln)
            if hit is None:
                continue
            m, _k = hit
            pos = ln.find(m)
            win = ln[max(0, pos - 40):pos + len(m) + 60]
            tim = TIME_RE.search(win)
            ctx = "\n".join(lines[max(0, i - 3):min(len(lines), i + 2)])
            gua = bool(GUA_RE.search(ctx))
            status = "可联盘候选" if (tim and gua) else ("仅验语" if (tim or gua) else "待人工")
            records.append({
                "id": "VER-%s-L%d" % (f.stem.replace(".", "_"), i),
                "book": _book_of(f.name), "file": f.name, "line": i,
                "match": m, "time_expr": (tim.group(1) if tim else ""),
                "quote": win, "status": status,
            })
    return records


def check_quotes(records, files):
    """负例有牙：每条 quote 必须是对应文件该行（或跨行拼接域）的逐字子串——照录义 §二。"""
    by_name = {f.name: f for f in files}
    bad = []
    cache = {}
    for r in records:
        f = by_name.get(r["file"])
        if f is None:
            bad.append("%s: 文件不在底本集" % r["id"])
            continue
        if f.name not in cache:
            cache[f.name] = f.read_text(encoding="utf-8", errors="replace").splitlines()
        lines = cache[f.name]
        if not (1 <= r["line"] <= len(lines)) or r["quote"] not in lines[r["line"] - 1]:
            bad.append("%s: 引文非该行逐字子串（篡改？）" % r["id"])
    return bad


def _summary(records):
    by_book, by_status = {}, {}
    for r in records:
        by_book[r["book"]] = by_book.get(r["book"], 0) + 1
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    return {"total": len(records), "by_book": by_book, "by_status": by_status}


def cmd_run(sources_dir: Path, out_path: Path, book_filter) -> int:
    files = [p for p in sources_dir.glob("*.txt") if "provenance" not in p.name]
    if book_filter:
        files = [f for f in files if book_filter in f.name]
    if not files:
        # §四.8：0 文件先自证不是路径解析错——直接判红，不静默出空册
        print("× 底本目录解析后 0 文件（%s）——先查路径，再谈 0 命中" % sources_dir)
        return 1
    records = harvest(files)
    bad = check_quotes(records, files)
    if bad:
        print("× 引文逐字校验未过 %d 条：%s" % (len(bad), bad[:3]))
        return 1
    doc = {"generated_at": datetime.now().isoformat(timespec="seconds"),
           "tool": "harvest_verifications.py",
           "note": "盘点册：不产 expected、不进评分集；自注有幸存者偏差，不得当命中率证据",
           "summary": _summary(records), "records": records}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    s = doc["summary"]
    print("√ 盘点册落成 %s｜总命中 %d 条（可联盘候选是其中 %d 条）"
          % (out_path.name, s["total"], s["by_status"].get("可联盘候选", 0)))
    for b, n in sorted(s["by_book"].items(), key=lambda kv: -kv[1]):
        print("    %-18s %d" % (b, n))
    return 0


def cmd_verify(out_path: Path, sources_dir: Path) -> int:
    if not out_path.exists():
        print("× 盘点册不存在（%s）——先跑收割" % out_path)
        return 1
    doc = json.loads(out_path.read_text(encoding="utf-8"))
    files = [p for p in sources_dir.glob("*.txt") if "provenance" not in p.name]
    bad = check_quotes(doc["records"], files)
    if bad:
        for b in bad[:10]:
            print("  · " + b)
        print("× 引文回验未过 %d 条" % len(bad))
        return 2
    print("√ 在册盘点册 %d 条引文全部可回指原文" % len(doc["records"]))
    return 0


def cmd_selftest() -> int:
    fails = []
    with tempfile.TemporaryDirectory(prefix="yi_hv_st_") as td:
        d = Path(td)
        (d / "fake_book.txt").write_text(
            "断曰：用神安静逢冲之日。果于丑日起床，家人相庆。\n"
            "予因张果元不论父友子友皆以应为用神。\n"
            "若果能诚，则占卜灵验。\n", encoding="utf-8")
        files = [d / "fake_book.txt"]
        recs = harvest(files)
        if len(recs) != 1:
            fails.append("合成底本应恰中 1 条，实得 %d（人名/若果混入或漏收）" % len(recs))
        elif recs[0]["status"] != "可联盘候选" or not recs[0]["time_expr"]:
            fails.append("命中状态/时间词判错：%r" % recs[0])
        if not check_quotes([dict(recs[0], quote="果于寅日起床")], files):
            fails.append("篡改引文未被回验抓出（判据是摆设）")
        empty = cmd_run(d / "no_such", d / "o.json", None)
        if empty == 0:
            fails.append("0 文件目录未判红（静默空册）")
        real = [p for p in SOURCES.glob("*.txt") if "provenance" not in p.name]
        n = len(harvest(real))
        if not real or n == 0:
            fails.append("真实底本 %d 文件却 0 命中——正则静默全盲嫌疑（§四.8 案族）" % len(real))
    if fails:
        print("× selftest：")
        for f in fails:
            print("  · " + f)
        return 1
    print("√ selftest：合成恰中/人名与若果排除/篡改回验/0 文件判红/真实盘非零 全过")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="古籍自验子集收割 v0（盘点册，不碰评分面）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--verify", action="store_true", help="复核在册盘点册逐字引文")
    ap.add_argument("--book", default=None, help="文件名子串过滤")
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    if args.verify:
        return cmd_verify(Path(args.out), SOURCES)
    return cmd_run(SOURCES, Path(args.out), args.book)


if __name__ == "__main__":
    raise SystemExit(main())
