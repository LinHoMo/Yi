# -*- coding: utf-8 -*-
"""古书源获取器：把公版古籍正文取回本地，**留下可复核的出处痕迹**。

    python tools/fetch_source.py --list                     # 看清单与本地缓存状态
    python tools/fetch_source.py --show liu-ren-da-quan     # 看某书解析出的子页
    python tools/fetch_source.py --fetch liu-ren-da-quan    # 抓取（含全部子页）
    python tools/fetch_source.py --fetch --all              # 抓清单里全部可用的书

为什么必须有这个工具（而不是各自写个小脚本）：
  1. **限流是要尊重的**。维基文库会对高频请求返回 HTTP 429。第一次探测候选门类时，
     我连打请求被限流，于是"取不到"与"没有这本书"在输出里长得一模一样——
     差点得出"《遁甲演义》不存在"的错误结论。本工具把限流**当成显式状态**重试，
     绝不把 429 静默降级成"缺失"。
  2. **出处要留痕**。每本书落盘时同时写 `*.provenance.json`：来源站点、页面标题、
     修订号、抓取时刻、sha256、字节数、子页清单。谁都可以据此复核"这段话真是书上的"。
     这与 `AGENTS.md` 铁律二（案例库隔离）配套：正文进 `data/sources/`，只做只读原料。
  3. **子页要能展开**。不少书在维基文库是"总页 + 卷次子页"（如《六壬大全》/1、/2…）。
     只抓总页会拿到空骨架——这是"书源看起来存在其实没内容"的常见坑。

设计纪律：
  * 只读公版古籍，不抓现代点校本、不抓带版权声明的站点；
  * 只做**字符级**保存，不做任何"模型转写"（转写会造出自洽性失败的假文本）；
  * 抓取与解析分离：`--fetch` 落原文，解析交给各门类自己的 parser；
  * 落盘位置默认 `data/sources/`；生成的 JSON 与 txt 是否入库由维护者按体量决定。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources"
CST = timezone(timedelta(hours=8))

API = "https://zh.wikisource.org/w/api.php"
USER_AGENT = "Yi-research/0.1 (classical text acquisition; https://github.com/)"

# 请求节流：维基媒体对匿名高频请求会 429。默认每次请求之间歇 1.5 秒，
# 429 时按 5/15/30/60 秒退避重试，最多 4 次；绝不把限流当"缺失"。
SLEEP_BETWEEN = 1.5
BACKOFF = (5, 15, 30, 60)

# 候选门类 → 古书清单。`pages` 为空表示按总页自动展开子页。
# status 字段是**实测**结果，不是推测：
#   ok        = 已实测取到正文（记下字节数）
#   skeleton  = 实测只取到目录骨架（正文尚未数字化）
#   missing   = 实测 missingtitle
#   unverified= 未实测（多为触发限流后主动停手，需后续复核）
CATALOG = (
    # ── 大六壬（推荐第一科：判据树最清晰，书源已实测可用）──
    {"key": "liu-ren-da-quan", "kind": "大六壬", "title": "六壬大全",
     "pages": ["六壬大全/1", "六壬大全/2"],
     "status": "ok",
     "note": "已抓 129817 字节。卷一含《入手法》：十干寄宫诀 + 九宗门逐条判决"
             "（贼克/比用/涉害/遥克…），三传/四课/天将/月将/寄宫全部命中"},
    {"key": "liu-ren-da-quan-juan3", "kind": "大六壬", "title": "六壬大全/3",
     "pages": [], "status": "ok", "note": "已抓 72209 字节（344 行 / 干支对 62）"},
    {"key": "mei-hua-yi-shu", "kind": "梅花易数", "title": "梅花易數",
     "pages": [], "status": "ok",
     "note": "2026-09-30j 实测存在（繁体，正文 11201 字节）。三科外部独立集的书源前置："
             "抓取后从中提取卷二/卷三占验例建 external_cases（永不调参 split）"},
    {"key": "ling-qi-jing", "kind": "灵棋经", "title": "靈棋經",
     "pages": [], "status": "ok",
     "note": "2026-09-30l 实测存在（繁体，正文 36912 字节）。第二门类（备选一）书源："
             "查表即断（上中下三部掷数 → 课名/卦象/断语），core 零增补"},
    {"key": "da-liu-ren-zhi-nan", "kind": "大六壬", "title": "大六壬指南",
     "pages": [], "status": "missing", "note": "实测 missingtitle"},
    {"key": "liu-ren-bi-fa-fu", "kind": "大六壬", "title": "六壬毕法赋",
     "pages": [], "status": "missing", "note": "实测 missingtitle"},
    # ── 奇门遁甲（**降级**：主源不存在，"古书自带算例"无法兑现）──
    {"key": "dun-jia-yan-yi", "kind": "奇门遁甲", "title": "遁甲演义",
     "pages": ["遁甲演义/1"], "status": "missing",
     "note": "**实测 missingtitle**（两次复核）。此前立项文档据「检索旁证」称其"
             "「已联网核实、自带五组带日期算例」，该说法不成立——奇门的推荐理由随之降级"},
    {"key": "yan-bo-diao-sou-ge", "kind": "奇门遁甲", "title": "煙波釣叟歌",
     "pages": [], "status": "ok", "note": "已抓 5970 字节（第三轮重试成功）。实测复核：有机制纲诀"
             "（阴阳遁分界/三元五日/阳遁顺仪奇逆布/值符值使），**无 24 节气×三元定局表与算例**"},
    {"key": "yu-ding-qi-men-bao-jian", "kind": "奇门遁甲", "title": "御定奇门宝鉴",
     "pages": [], "status": "unverified", "note": "未实测"},
    # ── 八字（调候 / 格局；命科深度改造的判据与命例来源）──
    {"key": "qiong-tong-bao-jian", "kind": "八字·调候", "title": "穷通宝鉴",
     "pages": [], "status": "ok",
     "note": "已抓 100030 字节：56 个标题（论X木/三春甲木…=调候判据正文）"
             "+ 70 个表格（四柱命例 + 断语如「状元」「词林」）=可建案例集"},
    {"key": "lan-jiang-wang", "kind": "八字·调候", "title": "欄江網",
     "pages": [], "status": "missing",
     "note": "实测 missingtitle；《穷通宝鉴》异名在维基文库无独立页"},
    {"key": "zi-ping-zhen-quan", "kind": "八字·格局", "title": "子平真诠",
     "pages": [], "status": "missing",
     "note": "实测 missingtitle（简繁两式均无）。格局成败救应的判据来源需另找"},
    {"key": "di-tian-sui", "kind": "八字·用神", "title": "滴天髓",
     "pages": [], "status": "ok",
     "note": "2026-10-01 重抓实测 60578 字节（含任注從化論：『從得真者只論從』逐字在库），此前 skeleton 判定过期"},
    {"key": "yuan-hai-zi-ping", "kind": "八字·总纲", "title": "渊海子平",
     "pages": [], "status": "missing", "note": "实测 missingtitle"},
    # ── 备选与旁证 ──
    {"key": "ling-qi-jing", "kind": "灵棋经", "title": "灵棋经 (四库全书本)",
     "pages": [], "status": "unverified", "note": "备选门类；124 课查表即断"},
    {"key": "tai-yi-jin-jing", "kind": "太乙", "title": "太乙金镜式经",
     "pages": [], "status": "unverified", "note": "论证中列为不推荐（占域以分野/治乱为纲）"},
    {"key": "xie-ji-bian-fang", "kind": "择吉", "title": "协纪辨方书",
     "pages": [], "status": "unverified", "note": "择吉科的口径旁证"},
    {"key": "zi-wei-dou-shu-quan-shu", "kind": "紫微斗数", "title": "紫微斗數全書",
     "pages": [], "status": "ok",
     "note": "已抓 214512 字节（卷一/二/三，93 标题）：卷一诸星问答论十四主星性情段 + "
             "太微赋/形性赋，可校 verdicts 主星格释义"},
    {"key": "zeng-shan-bu-yi", "kind": "六爻", "title": "增刪卜易",
     "pages": [], "status": "ok",
     "note": "已有专用 parser：disciplines/liuyao/dev_tools/fetch_wikisource_cases.py"})


# ── HTTP ────────────────────────────────────────────────────────────────────

class RateLimited(RuntimeError):
    """明确的限流状态。绝不与「页面不存在」混为一谈。"""


def _get(params: dict, *, retries: int = 4) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            time.sleep(SLEEP_BETWEEN)
            return data
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code == 429:
                wait = BACKOFF[min(attempt, len(BACKOFF) - 1)]
                print(f"    · 限流 429，等待 {wait}s 后重试（第 {attempt + 1} 次）")
                time.sleep(wait)
                continue
            if exc.code == 404:
                return {"error": {"code": "missingtitle"}}
            raise
        except Exception as exc:  # 网络抖动
            last = exc
            time.sleep(BACKOFF[min(attempt, len(BACKOFF) - 1)])
    raise RateLimited(f"重试 {retries} 次仍失败：{last!r}")


def page_wikitext(title: str) -> tuple[str, dict]:
    """取单页 wikitext。返回 (正文, 元信息)；页面不存在返回 ("", {...})。"""
    data = _get({"action": "parse", "format": "json", "formatversion": "2",
                 "prop": "wikitext|revid", "page": title, "redirects": "1"})
    if "error" in data:
        return "", {"title": title, "error": data["error"].get("code", "error")}
    parse = data.get("parse") or {}
    text = ((parse.get("wikitext")) or "")
    if isinstance(text, dict):  # 老式 formatversion=1 结构
        text = text.get("*", "")
    return text, {"title": parse.get("title") or title,
                  "revid": parse.get("revid"),
                  "pageid": parse.get("pageid")}


def subpages(title: str) -> list[str]:
    """列出某页的全部子页（如《六壬大全》的卷次页）。"""
    data = _get({"action": "query", "format": "json", "formatversion": "2",
                 "list": "allpages", "apprefix": title + "/", "aplimit": "200"})
    if "error" in data:
        return []
    pages = ((data.get("query") or {}).get("allpages")) or []
    return [p.get("title", "") for p in pages if p.get("title")]


def page_exists(title: str) -> bool:
    data = _get({"action": "query", "format": "json", "formatversion": "2",
                 "titles": title, "redirects": "1"})
    if "error" in data:
        return False
    pages = ((data.get("query") or {}).get("pages")) or []
    return bool(pages) and not pages[0].get("missing")


# ── 落盘与留痕 ──────────────────────────────────────────────────────────────

def _slug(entry: dict) -> str:
    return entry["key"]


def raw_path(entry: dict) -> Path:
    return SOURCES / f"{_slug(entry)}.wikitext.txt"


def prov_path(entry: dict) -> Path:
    return SOURCES / f"{_slug(entry)}.provenance.json"


def load_prov(entry: dict) -> dict | None:
    p = prov_path(entry)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def stat_text(text: str) -> dict:
    """正文字面统计：给"这本书里到底有没有可编程结构"一个客观读数。"""
    ganzhi = re.findall(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]", text)
    tables = len(re.findall(r"\{\|", text))
    headings = len(re.findall(r"^=+[^=\n]+=+", text, re.M))
    lines = [l for l in text.splitlines() if l.strip()]
    return {"bytes": len(text.encode("utf-8")), "chars": len(text),
            "lines": len(lines), "ganzhi_pairs": len(ganzhi),
            "tables": tables, "headings": headings}


def fetch(entry: dict, *, force: bool = False) -> dict:
    """抓取一本书（含子页），落原文 + 出处。返回出处 dict。"""
    key = entry["key"]
    if raw_path(entry).is_file() and not force:
        prov = load_prov(entry) or {}
        print(f"  = {key}：已有缓存（{prov.get('stats', {}).get('bytes', '?')} 字节），"
              f"加 --force 可重抓")
        return prov

    print(f"  → {key}（{entry['title']}）")
    titles = list(entry.get("pages") or [])
    if not titles:
        # 总页 + 自动展开的子页
        main_text, meta = page_wikitext(entry["title"])
        if meta.get("error"):
            print(f"    × 总页不可用：{meta['error']}")
            return {"key": key, "status": meta["error"], "pages": []}
        print(f"    · 总页 {meta['title']} 取到 {len(main_text)} 字符，展开子页…")
        subs = subpages(meta.get("title") or entry["title"])
        titles = [meta.get("title") or entry["title"]] + subs
        print(f"    · 子页 {len(subs)} 个")
        texts = {meta.get("title") or entry["title"]: main_text}
    else:
        texts = {}

    order: list[str] = []
    for t in titles:
        if t in texts:
            order.append(t)
            continue
        text, meta = page_wikitext(t)
        if meta.get("error"):
            print(f"    · 跳过 {t}（{meta['error']}）")
            continue
        texts[t] = text
        order.append(t)

    if not order:
        return {"key": key, "status": "empty", "pages": []}

    body = "\n\n".join(
        f"<!-- ==== {t} ==== -->\n{texts[t]}" for t in order if texts.get(t))
    st = stat_text(body)
    SOURCES.mkdir(parents=True, exist_ok=True)
    raw_path(entry).write_text(body, encoding="utf-8")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    prov = {
        "key": key, "kind": entry["kind"], "title": entry["title"],
        "site": "zh.wikisource.org", "api": API,
        "pages": order, "page_count": len(order),
        "fetched": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S%z"),
        "sha256": digest, "stats": st,
        "source_file": raw_path(entry).relative_to(ROOT).as_posix(),
        "note": ("公版古籍原文的字符级转存，未做任何改写或模型转写；"
                 "子页以 <!-- ==== 标题 ==== --> 分隔。"),
    }
    prov_path(entry).write_text(json.dumps(prov, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    print(f"    √ 落盘 {st['bytes']} 字节 / {st['lines']} 行 / "
          f"干支对 {st['ganzhi_pairs']} / 表格 {st['tables']} / 标题 {st['headings']}")
    print(f"      出处 → {prov_path(entry).relative_to(ROOT).as_posix()}")
    return prov


def by_key(key: str) -> dict | None:
    for e in CATALOG:
        if e["key"] == key:
            return e
    return None


def cmd_list() -> int:
    print("%-24s %-10s %-22s %-10s %s" % ("key", "门类", "书名", "状态", "本地缓存"))
    print("-" * 92)
    for e in CATALOG:
        prov = load_prov(e)
        cached = (f"{prov['stats']['bytes']}B/{prov['page_count']}页"
                  if prov else "—")
        print("%-24s %-10s %-22s %-10s %s" % (
            e["key"], e["kind"], e["title"], e["status"], cached))
        if e.get("note"):
            print("%-24s %s" % ("", "└ " + e["note"]))
    print("\n状态口径：ok=实测取到正文；skeleton=只有目录骨架；missing=实测不存在；"
          "unverified=未实测（多为限流后主动停手，需复核）。")
    return 0


def cmd_show(key: str) -> int:
    e = by_key(key)
    if not e:
        print(f"× 清单里没有 {key}（用 --list 查看）")
        return 2
    print(f"《{e['title']}》（{e['kind']}）status={e['status']}")
    if e.get("note"):
        print("  实测备注：" + e["note"])
    if e.get("pages"):
        print("  清单内写定的子页：")
        for p in e["pages"]:
            print("    · " + p)
    print("  探测子页（可能触发限流，会明确重试）…")
    subs = subpages(e["title"])
    if not subs:
        print("    （无子页，或该总页不存在）")
    for p in subs:
        print("    · " + p)
    prov = load_prov(e)
    if prov:
        print("  本地缓存：" + json.dumps(prov.get("stats"), ensure_ascii=False))
    return 0


def cmd_check(titles: list[str]) -> int:
    """逐标题实测存在性并报正文字节数。

    用途：**解决"这本书到底有没有"的争执**。同一个书名，有人凭检索结果说"有"，
    有人抓取失败说"无"——两种说法都不算数，只有 `action=query` 的 missing 字段算数。
    本命令对每个标题分别报：存在 / 不存在 / 被限流（**不等于不存在**）。
    """
    rc = 0
    for title in titles:
        try:
            data = _get({"action": "query", "format": "json", "formatversion": "2",
                         "titles": title, "redirects": "1",
                         "prop": "info"})
        except RateLimited as exc:
            print("  ? %-30s 被限流，无法判定（**不是**不存在）：%s" % (title, exc))
            rc = 1
            continue
        if "error" in data:
            print("  ? %-30s 查询出错：%s" % (title, data["error"].get("code")))
            rc = 1
            continue
        pages = ((data.get("query") or {}).get("pages")) or []
        if not pages:
            print("  ? %-30s 无返回" % title)
            rc = 1
            continue
        page = pages[0]
        if page.get("missing"):
            print("  × %-30s 不存在（missingtitle）" % title)
            rc = 1
            continue
        real = page.get("title") or title
        text, meta = page_wikitext(real)
        st = stat_text(text)
        if st["bytes"] < 500:
            verdict = "存在但正文过短（可能是总页/骨架）"
        else:
            verdict = f"存在，正文 {st['bytes']} 字节 / 干支对 {st['ganzhi_pairs']}"
        print("  √ %-30s %s%s" % (title, verdict,
                                  f"（重定向→{real}）" if real != title else ""))
    return rc


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(
        description="古书源获取器（维基文库；限流显式重试、出处留痕、子页展开）")
    ap.add_argument("--list", action="store_true", help="列出清单与缓存状态")
    ap.add_argument("--show", metavar="KEY", help="看某书的子页与缓存")
    ap.add_argument("--check", nargs="*", metavar="TITLE",
                    help="直接核查书名/页面标题是否存在（判定『有没有这本书』的唯一依据）")
    ap.add_argument("--fetch", nargs="*", metavar="KEY", help="抓取指定书（可多个）")
    ap.add_argument("--all", action="store_true", help="配合 --fetch：抓清单里 status=ok 的全部")
    ap.add_argument("--force", action="store_true", help="已有缓存也重抓")
    args = ap.parse_args()

    if args.check:
        print("逐标题实测（结论只认 API 的 missing 字段；限流≠不存在）：")
        return cmd_check(args.check)
    if args.list or not (args.fetch or args.show):
        return cmd_list()
    if args.show:
        return cmd_show(args.show)
    keys = list(args.fetch or [])
    if args.all:
        keys += [e["key"] for e in CATALOG if e["status"] == "ok"]
    if not keys:
        print("× 没给要抓的书（--fetch KEY...，或 --all 抓 status=ok 的全部）")
        return 2

    ok = 0
    for key in dict.fromkeys(keys):
        e = by_key(key)
        if not e:
            print(f"  × 清单里没有 {key}")
            continue
        try:
            prov = fetch(e, force=args.force)
        except RateLimited as exc:
            print(f"  × {key}：被限流且重试未过 —— {exc}")
            print("     这是「取不到」，**不是**「这本书不存在」；稍后重试。")
            continue
        if prov.get("sha256"):
            ok += 1
        elif prov.get("status"):
            # 如实区分三类结果，绝不把"取不到"说成"不存在"
            kind = {"missingtitle": "维基文库上没有这个页面",
                    "empty": "页面存在但没有正文",
                    "skeleton": "只有目录骨架"}.get(prov["status"], prov["status"])
            print(f"  ! {key}：{kind}")
    print(f"\n完成 {ok}/{len(set(keys))} 本。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
