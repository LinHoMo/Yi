#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""八字象层：宫位象 / 六亲象 / 五行脏腑象（第三百六十二批）。

本模块补的是八字侧**此前完全没有**的一条线——宫位与六亲。此前 analyze 面
有十神、有藏干、有纳音取象，却没有「哪一柱是哪一门亲眷／哪一段人生」的
宫位定位，也没有「十神落在六亲上是谁」的取象；正文里这两项实测为零。

纪律（CONTRACT §五-bis，违反即门红）：
  1. 象层**只呈现素材**：不进 strength / pattern / verdict 评分，不改结论。
  2. 不借道叙述层私表：narrate 的 liushen_image.json／十神行事表（铁律一）
     不在本模块读取范围；本模块只读本批新建的 data/xiang_layer.json。
  3. 脏腑象是**象意提示**，不是医学诊断——交付面必须带此声明。
  4. 素材不齐或装配失败即整块不产，不塞空壳冒充覆盖。
"""

from __future__ import annotations

# 控制台编码守卫：须在 import sys 之后——早于 sys 导入时 NameError 会被 except 咽掉、静默失效
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import json  # noqa: E402
from pathlib import Path  # noqa: E402

CORE = Path(__file__).resolve().parents[1] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.relations import LIUQIN_TO_SHISHEN  # noqa: E402  五类六亲唯一真源

_XIANG_PATH = Path(__file__).resolve().parents[1] / "data" / "xiang_layer.json"

# 十神 → 五类六亲（父/母/兄弟/子孙/妻财/官鬼）：由内核 LIUQIN_TO_SHISHEN 反查，
# 不在本模块另存一份映射（AGENTS §二 单向依赖：学科只读内核，不抄内核的表）。
_SHEN_TO_LIUQIN5 = {
    shen: liuqin
    for liuqin, shens in LIUQIN_TO_SHISHEN.items()
    for shen in shens
}

_WUXING = ("木", "火", "土", "金", "水")
_PILLARS = (("年", "year"), ("月", "month"), ("日", "day"), ("时", "hour"))


def _load() -> dict:
    try:
        return json.loads(_XIANG_PATH.read_text(encoding="utf-8"))
    except OSError:
        return {}


_RULES = _load()
_GONGWEI = _RULES.get("gongwei") or {}
_LIUGIN = _RULES.get("liugin_by_ten_god") or {}
_ZANGFU = _RULES.get("zangfu_by_element") or {}
_BASIS = _RULES.get("basis") or {}
_RENDER = _RULES.get("render") or {}


# =============================================================================
# 一、宫位象
# =============================================================================

def build_gongwei(a: dict) -> dict:
    """四柱宫位：年为根、月为苗、日为花、时为果，各柱带上本柱十神。

    宫位回答的是「哪一段人生／哪一门亲眷」，不回答吉凶。
    """
    pillars = a.get("pillars") or {}
    factors = a.get("factors") or {}
    out = {}
    for cn, en in _PILLARS:
        p = pillars.get(en) or {}
        g = _GONGWEI.get(cn) or {}
        if not p or not g:
            continue
        out[cn] = {
            "ganzhi": p.get("ganzhi", ""),
            "nayin": p.get("nayin", ""),
            "stem_ten_god": (factors.get(en) or {}).get("stem_ten_god") or p.get("ten_god", ""),
            "宫位": g.get("宫位", ""),
            "位次": g.get("位次", ""),
            "时限": g.get("时限", ""),
            "身位": g.get("身位", ""),
            "物象": g.get("物象", ""),
        }
    if not out:
        return {}
    out["basis"] = _BASIS.get("gongwei", "")
    return out


# =============================================================================
# 二、六亲象
# =============================================================================

def build_liugin(a: dict) -> dict:
    """十神 → 六亲，两层：

    · 五类（父母/兄弟/子孙/妻财/官鬼）：反查内核 `LIUQIN_TO_SHISHEN`，
      内核是唯一真源，本模块不抄表。
    · 子平分野（母/父/妻/夫/子女…）：读本批新建的 data/xiang_layer.json，
      男命以正财为妻、女命以正官为夫；传统本身有歧异的只登记两说不裁决。

    只取四柱天干十神（柱面定位）；藏干是「柱内含什么」，不在此取象。
    """
    gender = (a.get("birth") or {}).get("gender") or ""
    key = "男" if gender == "男" else ("女" if gender == "女" else "通用")
    factors = a.get("factors") or {}
    out = {}
    for cn, en in _PILLARS:
        tg = (factors.get(en) or {}).get("stem_ten_god") or ""
        if not tg:
            continue
        m = _LIUGIN.get(tg) or {}
        out.setdefault(cn, {
            "ten_god": tg,
            "五类": _SHEN_TO_LIUQIN5.get(tg, ""),
            "六亲": m.get(key) or m.get("通用", ""),
            "象意": m.get("通用", ""),
        })
    if not out:
        return {}
    out["gender_basis"] = (
        "男命以正财为妻、女命以正官为夫（通行分野）" if key in ("男", "女")
        else "性别未给，取通用口径（不按男命/女命分野）")
    out["gender"] = gender or "（未给）"
    out["basis"] = _BASIS.get("liugin", "")
    out["basis_wulei"] = "kernel/yishu_core/relations.py#LIUQIN_TO_SHISHEN（五类六亲唯一真源）"
    return out


# =============================================================================
# 三、五行脏腑象
# =============================================================================

def build_zangfu(a: dict) -> dict:
    """五行计数 → 脏腑象意提示（偏盛/偏弱/缺失）。

    计数取 bing_yao.element_counts（病药同源），缺项补 0——不因缺而省。
    只描述「该象偏盛/偏弱」，不写病症、不给医嘱。
    """
    counts = ((a.get("bing_yao") or {}).get("element_counts") or {})
    if not isinstance(counts, dict) or not counts:
        return {}
    full = {e: int(counts.get(e, 0) or 0) for e in _WUXING}
    present = {e: n for e, n in full.items() if n > 0}
    if not present:
        return {}
    heaviest = max(present, key=lambda e: present[e])
    absent = [e for e in _WUXING if full[e] == 0]

    def _image(e: str, tone: str) -> dict:
        z = _ZANGFU.get(e) or {}
        return {
            "五行": e,
            "见数": full[e],
            "脏腑": z.get("脏腑", ""),
            "身体": z.get("身体", ""),
            "象": z.get(tone, ""),
        }

    out = {
        "counts": full,
        "偏盛": _image(heaviest, "偏盛"),
    }
    if absent:
        out["缺"] = [{"五行": e, "脏腑": (_ZANGFU.get(e) or {}).get("脏腑", ""),
                      "象": (_ZANGFU.get(e) or {}).get("偏弱", "")} for e in absent]
    elif len(present) > 1:
        lightest = min(present, key=lambda e: present[e])
        out["偏弱"] = _image(lightest, "偏弱")
    out["note"] = _RENDER.get("medical_note", "")
    out["basis"] = _BASIS.get("zangfu", "")
    return out


# =============================================================================
# 四、装配
# =============================================================================

def build_xiang(a: dict) -> dict:
    """八字象层总装。分项取不到素材就不写该键。"""
    xiang = {}
    gw = build_gongwei(a)
    if gw:
        xiang["gongwei"] = gw
    lg = build_liugin(a)
    if lg:
        xiang["liugin"] = lg
    zf = build_zangfu(a)
    if zf:
        xiang["zangfu"] = zf
    if not xiang:
        return {}
    xiang["basis"] = {
        "registry": _BASIS.get("registry", ""),
        "note": "象层不进评分、不参与 verdict（CONTRACT §五-bis）；脏腑为象意提示非医学诊断",
    }
    return xiang


# =============================================================================
# 五、正文【象】段
# =============================================================================

def format_xiang_text(xiang: dict) -> str:
    """象层 → 正文一段。只读素材、不下判词；无素材返回空串。"""
    if not xiang:
        return ""
    lead = _RENDER.get("lead") or "**象上看**："
    sep = _RENDER.get("separator") or "；"
    parts = []

    gw = xiang.get("gongwei") or {}
    gw_txt = []
    for cn in ("年", "月", "日", "时"):
        v = gw.get(cn) or {}
        if v.get("ganzhi"):
            gw_txt.append(f"{cn}柱{v['ganzhi']}为{v.get('宫位','')}（{v.get('时限','')}）")
    if gw_txt:
        parts.append("宫位：" + sep.join(gw_txt))

    lg = xiang.get("liugin") or {}
    lg_txt = []
    for cn in ("年", "月", "日", "时"):
        v = lg.get(cn) or {}
        if v.get("ten_god"):
            _w = f"（{v['五类']}类）" if v.get("五类") else ""
            lg_txt.append(f"{cn}柱{v['ten_god']}应{v.get('六亲','')}{_w}")
    if lg_txt:
        parts.append(f"六亲（{lg.get('gender','')}命口径，{lg.get('gender_basis','')}）：" + sep.join(lg_txt))

    zf = xiang.get("zangfu") or {}
    h = zf.get("偏盛") or {}
    if h.get("五行"):
        s = f"五行{h['五行']}最重（{h.get('见数')}见）——{h.get('脏腑','')}之象偏盛"
        if (zf.get("偏弱") or {}).get("五行"):
            w = zf["偏弱"]
            s += f"，{w['五行']}最轻（{w.get('见数')}见）——{w.get('脏腑','')}之象偏弱"
        if zf.get("缺"):
            s += "，局中不见" + "、".join(x["五行"] for x in zf["缺"])
        parts.append(s + "。" + (zf.get("note") or ""))

    if not parts:
        return ""
    return lead + sep.join(parts)


# =============================================================================
# CLI 自测
# =============================================================================

if __name__ == "__main__":
    from chart import chart as _chart
    from analyze import analyze as _analyze
    _dt = sys.argv[1] if len(sys.argv) > 1 else "1990-05-15 10:30"
    _g = sys.argv[2] if len(sys.argv) > 2 else "男"
    _a = _analyze(_chart(datetime_str=_dt, gender=_g))
    _x = build_xiang(_a)
    print(json.dumps(_x, ensure_ascii=False, indent=2))
    print()
    print(format_xiang_text(_x))
