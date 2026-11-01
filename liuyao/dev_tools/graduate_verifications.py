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

BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
# dz 转录本把日干「己」写作「已」（与《增删》建器同一混淆）；不认「已」就会
# 把本案日期回退到上一案（399 批实测：L2424「寅月已酉日」被读成上一案辰月乙卯日）。
STEMS_SRC = "甲乙丙丁戊己庚辛壬癸已"
DATE_PAT = re.compile(r"([%s])月([%s])([%s])日" % (BRANCHES, STEMS_SRC, BRANCHES))
HEX_FORMS = re.compile(
    r"得([\u4e00-\u9fff]{1,4})(?:之|变|變)([\u4e00-\u9fff]{1,4})卦|得([\u4e00-\u9fff]{1,4})卦")
# 400 批：旧 YING_PAT 只认「应X日/果于X日/至X日应」，漏掉书里大量实录写法
# （果得於甲午日／果卒於申日／果至卯年／后至辛卯日／果于次年三月／果于七月）。
# 新式以**结果标记**（果/竟/卒/后）起头，12 字内取支＋日/月/年，或月序（三月→辰）。
# 只认结果标记，不认纯预测句；跨句以「．」等句读为界（L1165「果得长子．甲戌年」
# 的甲戌是下一句，不能算本条验支）。
MONTH_ORDER_BRANCH = {"正": "寅", "一": "寅", "二": "卯", "三": "辰", "四": "巳",
                      "五": "午", "六": "未", "七": "申", "八": "酉", "九": "戌",
                      "十": "亥", "冬": "子", "腊": "丑"}
YING_PAT = re.compile(
    r"[应應](?:于|在)?([%s])(?:日|月|年)"
    r"|[应應]在([%s])日"
    r"|[果竟卒后][^。；\n．.]{0,12}?([%s])(日|月|年)"
    r"|[果竟卒后][^。；\n．.]{0,12}?([正一二三四五六七八九十冬腊])月"
    r"|至([%s])日(?:而|方)?[应應]" % (BRANCHES, BRANCHES, BRANCHES, BRANCHES))
MAX_BACK = 40


def _norm_day_stem(s: str) -> str:
    """转录讹字「已」→「己」；其余干原样。"""
    return "己" if s == "已" else s


def _ying_branch(m: re.Match | None) -> str | None:
    """从 YING_PAT 的任一分组取支；月序组（三/七/八…）按标准月建映射。

    分组顺序：应X／应在X／果-支／果-月序／至X应。单位组（日/月/年）不在支表、
    也不在月序表，自然跳过。
    """
    if not m:
        return None
    for g in m.groups():
        if not g:
            continue
        if g in BRANCHES:
            return g
        if g in MONTH_ORDER_BRANCH:
            return MONTH_ORDER_BRANCH[g]
    return None


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
            # DATE_PAT 三段：月支／日干／日支；日干「已」归一为「己」后与日支拼回日柱
            block_start, date_key = j, (m.group(1), _norm_day_stem(m.group(2)) + m.group(3))
            break
    block = "\n".join(norm(lines[j]) for j in range(block_start, min(len(lines), hit + 2)))
    if not date_key:
        return "unrestorable", "块内（回溯 %d 行）无「X月Y日」日期键" % MAX_BACK, {}
    hm = HEX_FORMS.search(block)
    if not hm:
        return "unrestorable", "有日期键但块内无「得X卦/得X之Y卦」卦面式", {"date": list(date_key)}
    if hm.group(1):
        o, ch = resolve_hex(hm.group(1)), resolve_hex(hm.group(2))
    else:
        o, ch = resolve_hex(hm.group(3)), None
    if not o or (hm.group(2) and not ch):
        return "partial_needs_human", "卦名异写不可唯一落表：%r" % (hm.groups(),), {"date": list(date_key)}
    ym = YING_PAT.search(block)
    ybranch = _ying_branch(ym)
    if not ybranch:
        return "partial_needs_human", "卦面齐但书载验支不可提（块内无结果标记＋日期令牌）", \
            {"date": list(date_key), "original": o, "changed": ch}
    try:
        yao = case_runner.hex2yao(o, ch)
        built = yao is not None
    except Exception:
        built = False
    if not built:
        return "partial_needs_human", "卦面对（%s→%s）但 hex2yao 装配失败——异写或表缺" % (o, ch), \
            {"date": list(date_key), "original": o, "changed": ch}
    return "restorable", "", {"date": "%s月%s日" % date_key, "original": o, "changed": ch,
                              "yingqi_branch": ybranch}


def build(report_only: bool = False) -> int:
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
    if report_only:
        old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"rows": []}
        old_status = {r.get("source_id"): r.get("status") for r in old.get("rows", [])}
        new_status = {r.get("source_id"): r.get("status") for r in rows}
        old_rest = {sid for sid, st in old_status.items() if st == "restorable"}
        new_rest = [r for r in rows if r["status"] == "restorable"]
        new_ids = {r["source_id"] for r in new_rest}
        added = [r for r in new_rest if r["source_id"] not in old_rest]
        lost = sorted(old_rest - new_ids)
        print("√ 报告模式（**未写盘**）：restorable %d｜partial %d｜unrestorable %d｜共 %d"
              % (cnt["restorable"], cnt["partial_needs_human"], cnt["unrestorable"], len(rows)))
        print("  旧册 restorable %d → 新 %d｜新增 %d｜减少 %d"
              % (len(old_rest), len(new_rest), len(added), len(lost)))
        for r in added:
            hx = r.get("hex") or {}
            print("  + %-42s %s｜%s→%s｜应%s"
                  % (r["source_id"], hx.get("date") or "?", hx.get("original") or "?",
                     hx.get("changed") or "—", hx.get("yingqi_branch") or "?"))
        for sid in lost:
            print("  - %s（旧册 restorable → 新判 %s）" % (sid, new_status.get(sid)))
        print("  （这是工具盲区复核的实测差；应用差集＝另批重建观察册，本批只报数）")
        return 0
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
    # 400 批：已/己 转录混淆与实录式盲区
    dm = DATE_PAT.search("寅月已酉日")
    if not dm or _norm_day_stem(dm.group(2)) + dm.group(3) != "己酉":
        fails.append("「已酉日」未按己酉归一：%r" % (dm.groups() if dm else None))
    cases = {
        "果得於甲午日": "午", "果卒於申日": "申", "果至卯年": "卯",
        "后至辛卯日": "卯", "果于次年三月": "辰", "果于七月": "申",
    }
    for text, want in cases.items():
        got = _ying_branch(YING_PAT.search(text))
        if got != want:
            fails.append("实录式漏取：%r→%r（应 %s）" % (text, got, want))
    for text in ("果于本日酉时", "果于次日大晴", "果得长子.甲戌年", "果得长子．甲戌年"):
        if _ying_branch(YING_PAT.search(text)) is not None:
            fails.append("非验支被误取：%r→%r" % (text, _ying_branch(YING_PAT.search(text))))
    if fails:
        print("× selftest：" + "；".join(fails))
        return 1
    print("√ selftest：异写解析/表外拒绝/合成块三态/已己归一/实录式正负例 全过")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="自注毕业管道 v0（观察册，不入评分面）")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true",
                    help="只按当前分类器重算并打印与在册册的差集，**不写盘**")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    if args.verify:
        return cmd_verify()
    return build(report_only=args.report)


if __name__ == "__main__":
    raise SystemExit(main())
