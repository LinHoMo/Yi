# -*- coding: utf-8 -*-
"""命·金标准指纹：44 样例的逐字段快照（机械层覆盖 conclusion **全部字段**）。

   python dev_tools/golden.py verify            # 默认；漂移退出码 1
   python dev_tools/golden.py capture "理由"    # 有意漂移后落基线（必须给理由）

为什么从 6 例扩到 44 例，并且改哈希面（2026-10-12 第一百二十九批）：
1. **旧机械层只取 6 个字段**（strength/strength_score/pattern/useful_gods/dayun 首行
   ＋pillars），而 `analyze()` 的 conclusion 实测有 **28 个顶层键**——`pattern_cheng_bai`
   `tong_guan` `tian_ke_di_chong` `san_hui` `pillar_relations` `ten_god_combos`
   `nayin_xiangge` `timing` `verdicts` `female_fu_zi` `taboo_gods` … 行为变了，
   机械层**一概看不见**，只能靠措辞层偶然发现，且发现不了"改了字段没改措辞"这一类。
   现在额外记 `conclusion_sha`＝整个 conclusion 的规范化哈希，金标准壳把它归入机械层
   （`golden_kit` 的口径：除 `narrate_*` 之外全字段入机械 blob），于是一次改任何一
   个字段都必漂移。
2. **6 例全是手写日期**，覆盖面按人想象而非按引擎输出分层。现在 38 例从语料按
   `pattern × strength` 分层取层首（27 组全覆盖，按 id 序先到先得，不挑样例）
   ＋从格例 3（ZC001-3）＋外部独立集 4（QTBJ001/003/005/007，原 8 例里 002/004/006/008
   是同考点异盘冗余、第一百六十批随 #39 清出考卷而移出样例），再保留原手写 6 例。现共 40 例。
   选例**冻结进代码**而不是每次现算：否则改一次语料就挪动看门狗的覆盖面，
   基线会因为与行为无关的原因漂移。要换样例必须显式改这张表并 capture 记理由。
3. **女命在语料里是 0 例**（实测：670 例带 datetime／四柱者中 `gender=="女"` 者 0）——
   行运方向"女"这一侧眼下只有手写样例 2 例覆盖。已如实登记，不冒充语料有覆盖。
4. 13 例走 `chart_from_pillars`（书上只给四柱、无公历），与 `chart()` 是两条入参路径，
   旧 6 例全走 datetime，那条路径过去完全不在指纹里。
"""
from __future__ import annotations


# 控制台编码守卫：GBK/cp936 控制台下本器的中文输出会退化成乱码字节（rc 仍为 0，只有这条管得住）。
# 位置在 __future__ 之后、其余语句之前；import 期解释器告警仍需调用方 PYTHONUTF8=1 才能全拦（见 check.py 编码不变式）。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import hashlib
import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[1] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

OUT = DISC / "scratch" / "golden_ming_before.json"
DIGEST = DISC / "data" / "golden" / "digest.json"

# 手写样例：身旺/身弱/中和 × 不同月令格，且是**仅有**的女命覆盖（语料女命 0 例）
HAND = [
    {"sample": "mid_jianlu", "datetime": "1984-02-10 10:00", "gender": "男"},
    {"sample": "strong_jianlu", "datetime": "1996-11-11 22:00", "gender": "男"},
    {"sample": "weak_shangguan", "datetime": "1990-05-20 10:30", "gender": "男"},
    {"sample": "weak_zhengguan", "datetime": "1984-12-08 08:00", "gender": "女"},
    {"sample": "weak_zhengguan2", "datetime": "2000-08-15 14:00", "gender": "男"},
    {"sample": "mid_zhengyin", "datetime": "1955-04-20 04:00", "gender": "女"},
]

# 语料分层样例（src＝案例 id；datetime 走 chart()，pillars 走 chart_from_pillars()）
CORPUS = [
    {"src": "MP116", "datetime": "2010-01-16 03:30", "gender": "男"},
    {"src": "MP076", "datetime": "2082-07-27 07:30", "gender": "男"},
    {"src": "ZP013", "pillars": "己卯/丁丑/丙寅/庚寅", "gender": "男"},
    {"src": "MP056", "datetime": "2031-02-05 17:30", "gender": "男"},
    {"src": "MP342", "datetime": "1998-08-13 03:30", "gender": "男"},
    {"src": "MP052", "datetime": "1966-02-16 03:30", "gender": "男"},
    {"src": "MP214", "datetime": "2023-03-12 11:30", "gender": "男"},
    {"src": "MP098", "datetime": "1944-11-18 03:30", "gender": "男"},
    {"src": "MT478", "datetime": "1984-04-08 10:00", "gender": "男"},
    {"src": "MP242", "datetime": "2001-02-16 19:30", "gender": "男"},
    {"src": "MP082", "datetime": "2042-08-26 07:30", "gender": "男"},
    {"src": "MP064", "datetime": "1977-05-19 00:30", "gender": "男"},
    {"src": "ZP024", "pillars": "戊辰/癸亥/壬午/丙午", "gender": "男"},
    {"src": "MP066", "datetime": "2075-05-15 11:30", "gender": "男"},
    {"src": "MP072", "datetime": "2078-06-28 01:30", "gender": "男"},
    {"src": "MP222", "datetime": "1972-04-18 15:30", "gender": "男"},
    {"src": "MP070", "datetime": "1950-06-20 21:30", "gender": "男"},
    {"src": "MP060", "datetime": "1995-03-06 21:30", "gender": "男"},
    {"src": "MP230", "datetime": "2016-05-17 21:30", "gender": "男"},
    {"src": "MP118", "datetime": "2060-02-04 03:30", "gender": "男"},
    {"src": "MP104", "datetime": "1911-12-22 03:30", "gender": "男"},
    {"src": "MP106", "datetime": "1961-12-09 09:30", "gender": "男"},
    {"src": "MP212", "datetime": "2059-01-01 11:30", "gender": "男"},
    {"src": "MP086", "datetime": "1936-09-21 17:30", "gender": "男"},
    {"src": "MP142", "datetime": "1927-07-12 11:30", "gender": "男"},
    {"src": "MP092", "datetime": "1959-10-21 00:30", "gender": "男"},
    {"src": "MP370", "datetime": "2080-03-16 15:30", "gender": "男"},
    {"src": "ZC001", "pillars": "戊戌/丙辰/乙未/丙戌", "gender": "男"},
    {"src": "ZC002", "pillars": "壬寅/壬寅/庚寅/戊寅", "gender": "男"},
    {"src": "ZC003", "pillars": "丙寅/庚寅/壬午/乙巳", "gender": "男"},
    {"src": "QTBJ001", "pillars": "丙午/庚寅/丙午/庚寅", "gender": "男"},
    {"src": "QTBJ003", "pillars": "乙亥/己卯/丙申/己亥", "gender": "男"},
    {"src": "QTBJ005", "pillars": "丁巳/乙巳/丙子/戊子", "gender": "男"},
    {"src": "QTBJ007", "pillars": "庚寅/壬午/丙戌/己亥", "gender": "男"},
]


def _conclusion_sha(con: dict) -> str:
    """整个 conclusion 的规范化哈希——28 个顶层键任何一处行为变化都必漂移。"""
    blob = json.dumps(con, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def fingerprint() -> list[dict]:
    from chart import chart, chart_from_pillars
    from analyze import analyze
    from narrate import narrate as _narrate

    out = []
    for s in HAND + [{"sample": f"corpus_{d['src']}", **d} for d in CORPUS]:
        if s.get("datetime"):
            c = chart(s["sample"], datetime_str=s["datetime"], gender=s["gender"])
        else:
            y, m, d2, h = s["pillars"].split("/")
            c = chart_from_pillars({"year": y, "month": m, "day": d2, "hour": h},
                                   gender=s["gender"], question=s["sample"])
        a = analyze(c)
        con = a.get("conclusion") or {}
        row = {
            "sample": s["sample"],
            "src": s.get("src", ""),
            "datetime": s.get("datetime") or c.get("birth", {}).get("datetime", ""),
            "given": s.get("pillars") or "",
            "pillars": {k: (v or {}).get("ganzhi") for k, v in (c.get("pillars") or {}).items()},
            # 逐字段可读行（保留旧形状，便于漂移报告直接指出是哪个字段）
            "strength": con.get("strength"),
            "strength_score": con.get("strength_score"),
            "pattern": con.get("pattern"),
            "pattern_cheng_bai": con.get("pattern_cheng_bai"),
            "useful_gods": con.get("useful_gods"),
            "taboo_gods": con.get("taboo_gods"),
            "tiaohou_pattern_conflict": con.get("tiaohou_pattern_conflict"),
            "dayun_head": (con.get("dayun") or [{}])[0] if con.get("dayun") else None,
            "dayun_len": len(con.get("dayun") or []),
            "direction": con.get("方向"),
            # 全字段兜底哈希：conclusion 28 个顶层键里任何一处行为变化都必漂移。
            # 第一百二十九批曾因**引擎跨进程非确定**（#40：detail 由 `set & set` 拼串，
            # 序随 PYTHONHASHSEED 随机）而摘出；conflict_resolution.py 已改按格局喜用原序取交集，
            # 三个 hash seed 下 44 样例合并哈希同为 404e00cf00860dbb，故纳回。
            "conclusion_sha": _conclusion_sha(con),
            # 全字段兜底哈希暂不入（见上因由 #40）：引擎确定性修好后再加回
            "narrate_sha": hashlib.sha256(str(_narrate(a)).encode("utf-8")).hexdigest()[:12],
        }
        out.append(row)
    return out


def main() -> int:
    from yishu_core.golden_kit import run
    return run(
        "八字科（四柱）",
        what="八字科金标准指纹基线（conclusion 全字段哈希＋逐字段快照＋大运方向）",
        how='改动引擎行为后跑 python dev_tools/golden.py capture "理由"；'
            "机械层漂移=行为变化（含 conclusion_sha，任何字段都算），"
            "措辞层漂移=narrate 断语变化（两层分列归因）",
        fingerprint=fingerprint, out=OUT, digest_path=DIGEST)


if __name__ == "__main__":
    raise SystemExit(main())
