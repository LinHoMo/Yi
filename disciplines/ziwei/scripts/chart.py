# -*- coding: utf-8 -*-
"""紫微斗数排盘引擎（chart 段）—— 纯机械，无解读（CONTRACT §A）。

输入出生公历时刻 + 性别，输出派盘 JSON。
年界立春、月界节气、日柱儒略日——复用 core.ganzhi_calendar。
紫微定位 / 星系排布 / 余曜安星 / 十二宫逆布 / 四化——全部机械，LLM 零参与。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.ganzhi_calendar import ganzhi_of  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.ziwei_tables import (  # noqa: E402
    STARS,
    AUXILIARY_STARS,
    PALACES,
    WUXING_TO_JU,
    JU_TO_WUXING,
    SIHUA_TABLE,
    SIHUA_DIRECTION,
    ZIWEI_GROUP_ORDER,
    TIANFU_GROUP_ORDER,
    ziwei_position,
    tianfu_position,
    ziwei_group_positions,
    tianfu_group_positions,
    ming_gong_pos,
    zuo_you_positions,
    chang_qu_positions,
    kui_yue_positions_by_stem,
    huoling_pos,
    di_kong_jie_pos,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
)
from yishu_core.symbols import nayin_of, NAYIN_TO_ELEMENT  # noqa: E402


def _branch_idx(branch: str) -> int:
    try:
        return EARTHLY_BRANCHES.index(branch)
    except ValueError:
        return -1


def _stem_idx(stem: str) -> int:
    try:
        return HEAVENLY_STEMS.index(stem)
    except ValueError:
        return -1


def ziwei_chart(
    *,
    datetime_str: str | None = None,
    gender: str | None = None,
    longitude: float | None = None,
) -> dict:
    """出生时刻 → 紫微斗数盘 JSON（机械因子）。"""
    if datetime_str:
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    else:
        dt = datetime.now()

    moment = ganzhi_of(dt, boundary="day")
    year_gz = moment.year_ganzhi
    month_gz = moment.month_ganzhi
    day_gz = moment.day_ganzhi
    hour_gz = moment.hour_ganzhi

    # 年纳音 → 五行局数
    nayin = nayin_of(year_gz)
    element = NAYIN_TO_ELEMENT.get(nayin or "") if nayin else ""
    ju = WUXING_TO_JU.get(element, 5)

    # 分支索引
    month_branch = _branch_idx(month_gz[1])
    hour_branch = _branch_idx(hour_gz[1])
    year_branch = _branch_idx(year_gz[1])
    year_stem = _stem_idx(year_gz[0])
    day_stem = _stem_idx(day_gz[0])

    # 命宫（寅起逆月顺时）
    mg_pos = ming_gong_pos(month_branch, hour_branch)

    # 紫微定位
    ziwei_pos = ziwei_position(ju, dt.day)
    tf_pos = tianfu_position(ziwei_pos)

    # 紫微星系（逆布）
    zw_positions = ziwei_group_positions(ziwei_pos)
    # 天府星系（顺布）
    tf_positions = tianfu_group_positions(tf_pos)

    # 余曜
    zuo_pos, you_pos = zuo_you_positions(month_branch)
    chang_pos, qu_pos = chang_qu_positions(hour_branch)
    kui_pos, yue_pos = kui_yue_positions_by_stem(year_stem)
    huo_pos, ling_pos = huoling_pos(year_branch, hour_branch)
    dk_pos, dj_pos = di_kong_jie_pos(year_branch)

    aux_positions: dict[str, int] = {
        "左辅": zuo_pos, "右弼": you_pos,
        "文昌": chang_pos, "文曲": qu_pos,
        "天魁": kui_pos, "天钺": yue_pos,
        "火星": huo_pos, "铃星": ling_pos,
        "地空": dk_pos, "地劫": dj_pos,
    }

    # 各宫星曜装配：宫位idx → {主星: [...], 辅星: [...], 四化: [...]}
    # 十二宫逆时针排列：命宫起（位置idx=mg_pos），依次为兄弟、夫妻...
    palaces_data: dict[str, dict] = {}
    for i in range(12):
        # 宫位索引：命宫(i=0) 在 mg_pos，兄弟(i=1) 在 mg_pos-1，...
        palace_branch_idx = (mg_pos - i) % 12
        palace_name = PALACES[i]
        main_stars = []
        aux_stars = []
        sihua_here = []
        # 主星：在 palace_branch_idx 的主星
        for star, pos in zw_positions.items():
            if pos == palace_branch_idx:
                main_stars.append(star)
        for star, pos in tf_positions.items():
            if pos == palace_branch_idx:
                main_stars.append(star)
        # 余曜
        for star, pos in aux_positions.items():
            if pos == palace_branch_idx:
                aux_stars.append(star)
        palaces_data[palace_name] = {
            "branch": EARTHLY_BRANCHES[palace_branch_idx],
            "branch_idx": palace_branch_idx,
            "main_stars": main_stars,
            "aux_stars": aux_stars,
            "sihua": sihua_here,
        }

    # 四化星（年干→星→定位→入何宫）
    sihua = SIHUA_TABLE.get(year_gz[0], {})
    si_list = []
    for dtype, star in sihua.items():
        star_pos = zw_positions.get(star)
        if star_pos is None:
            star_pos = tf_positions.get(star)
        if star_pos is None:
            continue
        # 找到该宫
        target_palace = None
        for pname, pdata in palaces_data.items():
            if pdata["branch_idx"] == star_pos:
                target_palace = pname
                pdata["sihua"].append(f"{star}{dtype}")
                break
        si_list.append({
            "type": dtype,
            "star": star,
            "direction": SIHUA_DIRECTION.get(dtype, "平"),
            "palace": target_palace,
            "palace_idx": star_pos,
        })

    return {
        "discipline": "ziwei",
        "birth": {
            "datetime": dt.strftime("%Y-%m-%d %H:%M"),
            "gender": gender,
            "longitude": longitude,
        },
        "pillars": {
            "year": year_gz,
            "month": month_gz,
            "day": day_gz,
            "hour": hour_gz,
        },
        "nayin": nayin,
        "wuxing_ju": ju,
        "ju_name": f"{JU_TO_WUXING[ju]}{ju}局",
        "ming_gong": {
            "palace_idx": mg_pos,
            "branch": EARTHLY_BRANCHES[mg_pos],
        },
        "ziwei": {
            "pos": ziwei_pos,
            "branch": EARTHLY_BRANCHES[ziwei_pos],
        },
        "tianfu": {
            "pos": tf_pos,
            "branch": EARTHLY_BRANCHES[tf_pos],
        },
        "palaces": palaces_data,
        "sihua": sihua,
        "sihua_list": si_list,
        "star_positions": {
            **{s: {"idx": p, "branch": EARTHLY_BRANCHES[p]} for s, p in zw_positions.items()},
            **{s: {"idx": p, "branch": EARTHLY_BRANCHES[p]} for s, p in tf_positions.items()},
            **{s: {"idx": p, "branch": EARTHLY_BRANCHES[p]} for s, p in aux_positions.items()},
        },
        "calendar_policy": {"boundary": "day", "zi_hour": "same-day"},
    }


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="紫微斗数排盘（chart 段，纯机械）")
    ap.add_argument("--datetime", help='出生公历 "YYYY-MM-DD HH:MM"')
    ap.add_argument("--gender", choices=["男", "女"], default=None)
    ap.add_argument("--longitude", type=float, default=None)
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    out = ziwei_chart(
        datetime_str=args.datetime,
        gender=args.gender,
        longitude=args.longitude,
    )
    text = json.dumps(out, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
