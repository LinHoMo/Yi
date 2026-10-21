# -*- coding: utf-8 -*-
"""自注毕业管道 v0（第一百八十九批·B3）——把 179 批盘点册升成「可复原性三态」台账。

开发前置事实（本批第一读数是打脸自己）：盘点册的「可联盘候选」判据是命中行 ±3 行内有
卦/占线索＋时间词——**同线同时含日期键与卦面式者仅 6/193**（179 批状态标签过度承诺，
按 §六.2 本批回头改登记）。毕业管道因此不信任原状态，从命中行向**案块边界**重展开：
  块界＝向上找最近「X月Y日」日期行（≤40 行），块内找卦面式（得X之Y卦／得X卦變Y／…）。

三态输出（data/cases/verifications_graduation.json，观察册——不入 splits、不碰评分面）：
  restorable          日期键＋可解析卦名（hex2yao 表内可落）且验支在块内——可升正式配对案例
  partial_needs_human 块内有日期或卦面但缺一（跨案断线/卦名异写）——留人工，不硬修
  unrestorable        块扩到 40 行仍凑不齐——按 §六.5 结案式登记，不假装能救

卦名解析＝繁简归一后对内核 64 卦短名做唯一后缀匹配（山火贲→贲、风水涣→涣；歧义即弃）。
验支＝书载「应X日/果于X日」支——expected 只抄书载明写，§三.4 合法来源。

    python dev_tools/graduate_verifications.py             # 重建三态台账
    python dev_tools/graduate_verifications.py --verify    # 复核在册台账逐字书证
    python dev_tools/graduate_verifications.py --selftest  # 负例
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from stable_write import write_stable  # noqa: E402  203 批：幂等写，时间戳=内容最后变化
import case_runner  # noqa: E402
from version_collate import norm  # noqa: E402  繁简归一＝185 批同一函数（科内口径唯一）
from yishu_core.symbols import HEXAGRAM_TRIGRAMS  # noqa: E402  64 卦名唯一真值源＝内核表键

SRC_DIR = DISC / "data" / "sources"
LEDGER = DISC / "data" / "cases" / "verifications.json"
OUT = DISC / "data" / "cases" / "verifications_graduation.json"

DATE_PAT = re.compile(r"([子丑寅卯辰巳午未申酉戌亥])月([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])日")
HEX_FORMS = re.compile(
    r"得([\u4e00-\u9fff]{1,4})(?:之|变|變)([\u4e00-\u9fff]{1,4})卦|得([\u4e00-\u9fff]{1,4})卦")
YING_PAT = re.compile(
    r"[应應](?:于|在)?([子丑寅卯辰巳午未申酉戌亥])(?:日|月|年)"
    r"|果于([子丑寅卯辰巳午未申酉戌亥])日"
    r"|至([子丑寅卯辰巳午未申酉戌亥])日(?:而|方)?[应應]"
    r"|[应應]在([子丑寅卯辰巳午未申酉戌亥])日")
MAX_BACK = 40


def resolve_hex(raw: str):
    """异写卦名→内核表短名：表内直配失败则按后缀试（山火贲→贲）。歧义/不在表 → None。"""
    s = norm(raw)
    if s.endswith("卦") and len(s) > 2:      # 捕获尾「卦」剥离：得X卦变Y卦 的组内残留
        s = s[:-1]
    if s in HEXAGRAM_TRIGRAMS:
        return s
    if "为" in s:                       # 八纯卦「兑为泽」式：取上卦字对表（泽→兊不行则直取首字）
        head = s.split("为")[0]
        if head in HEXAGRAM_TRIGRAMS:
            return head
    cands = [k for k in HEXAGRAM_TRIGRAMS if s.endswith(k)]
    return cands[0] if len(cands) == 1 else None


def classify(rec, lines):
    hit = rec["line"] - 1
    block_start = hit
    date_key = None
    for j in range(hit, max(-1, hit - MAX_BACK), -1):
        m = DATE_PAT.search(norm(lines[j]))
        if m:
            block_start, date_key = j, (m.group(1), m.group(2))
            break
    block = "\n".join(norm(lines[j]) for j in range(block_start, min(len(lines), hit + 2)))
    if not date_key:
        return "unrestorable", "块内（回溯 %d 行）无「X月Y日」日期键" % MAX_BACK, {}
    hm = HEX_FORMS.search(block)
    if not hm:
        return "unrestorable", "有日期键但块内无「得X卦/得X之Y卦」卦面式", {"date": date_key}
    if hm.group(1):
        o, ch = resolve_hex(hm.group(1)), resolve_hex(hm.group(2))
    else:
        o, ch = resolve_hex(hm.group(3)), None
    if not o or (hm.group(2) and not ch):
        return "partial_needs_human", "卦名异写不可唯一落表：%r" % (hm.groups(),), {"date": date_key}
    ym = YING_PAT.search(block)
    ybranch = next((g for g in (ym.groups() if ym else ()) if g), None)
    if not ybranch:
        return "partial_needs_human", "卦面齐但书载验支不可提（块内无应X日/果于X日）", \
            {"date": date_key, "original": o, "changed": ch}
    try:
        yao = case_runner.hex2yao(o, ch)
        built = yao is not None
    except Exception:
        built = False
    if not built:
        return "partial_needs_human", "卦面对（%s→%s）但 hex2yao 装配失败——异写或表缺" % (o, ch), \
            {"date": date_key, "original": o, "changed": ch}
    return "restorable", "", {"date": "%s月%s日" % date_key, "original": o, "changed": ch,
                              "yingqi_branch": ybranch}


def build() -> int:
    if not LEDGER.exists():
        print("× 盘点册不存在——先跑 179 批 harvest")
        return 1
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    src_cache = {}
    rows, cnt = [], {"restorable": 0, "partial_needs_human": 0, "unrestorable": 0}
    for rec in led["records"]:
        f = rec["file"]
        if f not in src_cache:
            p = SRC_DIR / f
            src_cache[f] = p.read_text(encoding="utf-8", errors="replace").splitlines() if p.exists() else []
        if not src_cache[f]:
            cnt["unrestorable"] += 1
            rows.append({"source_id": rec["id"], "status": "unrestorable", "why": "底本文件缺失"})
            continue
        st, why, info = classify(rec, src_cache[f])
        cnt[st] += 1
        rows.append({"source_id": rec["id"], "book": rec["book"], "file": f, "line": rec["line"],
                     "quote": rec["quote"], "status": st, "why": why, **({"hex": info} if st else {})})
    # 装配后逐字回验：quote 必须仍是对应行子串（照录义）
    bad = 0
    for r in rows:
        if "quote" not in r:
            continue
        ln = src_cache.get(r["file"], [])
        if not (0 < r["line"] <= len(ln) and norm(r["quote"]) in norm(ln[r["line"] - 1])):
            bad += 1
    if bad:
        print("× %d 条引文回验未过——不落盘" % bad)
        return 1
    doc = {"schema": "yi-liuyao-verifications-graduation/1", "built_at": datetime.now().isoformat(timespec="seconds"),
           "_comment": "观察册：不入 case_splits、不参与评分与调参；restorable 项待人工逐案确认后"
                       "另批入册（§三.4：expected 只抄书载明写的验支）。179 批「可联盘候选 193」系"
                       "±3 行线索判据过度承诺，本册按块界重判为准（§六.2 回头改登记）。",
           "summary": cnt, "rows": rows}
    write_stable(OUT, doc)
    print("√ 毕业台账落成 %s｜restorable %d｜partial %d｜unrestorable %d｜共 %d"
          % (OUT.name, cnt["restorable"], cnt["partial_needs_human"], cnt["unrestorable"], len(rows)))
    by_book = {}
    for r in rows:
        if r["status"] == "restorable":
            by_book[r["book"]] = by_book.get(r["book"], 0) + 1
    print("  可复原按书分布：%s" % (by_book or "无"))
    return 0


def cmd_verify() -> int:
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    bad = []
    cache = {}
    for r in doc["rows"]:
        if "quote" not in r:
            continue
        f = r["file"]
        if f not in cache:
            cache[f] = (SRC_DIR / f).read_text(encoding="utf-8", errors="replace").splitlines()
        ln = cache[f]
        if not (0 < r["line"] <= len(ln) and norm(r["quote"]) in norm(ln[r["line"] - 1])):
            bad.append(r["source_id"])
    print(("× 回验未过 %d 条：%s" % (len(bad), bad[:5])) if bad
          else "√ 在册 %d 条引文全部可回指原书行" % len(doc["rows"]))
    return 1 if bad else 0


def cmd_selftest() -> int:
    fails = []
    if resolve_hex("山火贲") != "贲" or resolve_hex("风水涣") != "涣":
        fails.append("异写后缀解析错：%r/%r" % (resolve_hex("山火贲"), resolve_hex("风水涣")))
    if resolve_hex("不存在卦") is not None:
        fails.append("表外卦名被臆造解析")
    fake = ["别的行。", "卯月壬辰日占文书，得山火贲卦，应卯日。", "又一行。"]
    st, why, info = classify({"line": 2, "file": "x", "quote": "卯月壬辰日占文书，得山火贲卦，应卯日。"}, fake)
    if st != "restorable" or info.get("yingqi_branch") != "卯":
        fails.append("合成块判态错：%s/%r" % (st, info))
    st2, _, _ = classify({"line": 2, "file": "x", "quote": "x"}, ["无日期行。", "得乾卦。", ""])
    if st2 != "unrestorable":
        fails.append("缺日期键未判 unrestorable")
    if fails:
        print("× selftest：" + "；".join(fails))
        return 1
    print("√ selftest：异写解析/表外拒绝/合成块三态 全过")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="自注毕业管道 v0（观察册，不入评分面）")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    if args.verify:
        return cmd_verify()
    return build()


if __name__ == "__main__":
    raise SystemExit(main())
