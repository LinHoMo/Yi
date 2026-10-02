# -*- coding: utf-8 -*-
"""紫微斗数排盘引擎（chart 段）—— 纯机械，无解读（CONTRACT §A）。

输入出生公历时刻 + 性别，输出派盘 JSON。
年干支（立春界）与月支/日柱复用 core.ganzhi_calendar；
**安星所据的月与日取农历**（书源《紫微斗數全書》卷二安星诀一律作「正月…十二月」
「初一…三十」，如「如是正月初一生者是火局，酉宫起初一日」），
农历换算复用 core.lunar（唯一真值源）。
紫微定位 / 星系排布 / 余曜安星 / 十二宫逆布 / 四化——全部机械，LLM 零参与。
规则表的唯一真值源在 core.yishu_core.ziwei_tables，本文件只做历法转写与装配。
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

from yishu_core.ganzhi_calendar import ganzhi_of, TIGER_MONTH_STEM  # noqa: E402
from yishu_core.lunar import solar_to_lunar  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.ziwei_tables import (  # noqa: E402
    AUXILIARY_STARS,
    PALACES,
    JU_TO_WUXING,
    SIHUA_TABLE,
    SIHUA_DIRECTION,
    MAIN_STAR_ORDER,
    ziwei_position,
    tianfu_position,
    ziwei_group_positions,
    tianfu_group_positions,
    ju_from_ming_gong,
    ming_gong_pos,
    shen_gong_pos,
    zuo_you_positions,
    chang_qu_positions,
    kui_yue_positions_by_stem,
    lu_cun_pos,
    qing_yang_tuo_luo_pos,
    tian_ma_pos,
    huoling_pos,
    di_kong_jie_pos,
    tian_xing_yao_pos,
    tian_ku_xu_pos,
    long_chi_feng_ge_pos,
    san_tai_ba_zuo_pos,
    tai_fu_feng_gao_pos,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
)


class PaiPanError(ValueError):
    """排盘异常：所依古籍明文缺格或历法超出可算范围时抛出，不得手动替代。"""


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

    # 农历月日（安星依据）。书源 1665：「又若闰月正月生者要在二月内起安身命，
    # 凡有闰月具要依此为例」→ 闰月作下一月论。
    lunar = solar_to_lunar(dt.date())
    if lunar is None:
        raise PaiPanError(
            f"农历表范围 1900-2049，{dt.date()} 超出，无法排盘（紫微安星依农历月日）"
        )
    lunar_month = lunar["month"] % 12 + 1 if lunar["leap"] else lunar["month"]
    lunar_day = lunar["day"]

    # 月支按「正月=寅」：正月(1) → 寅(2)，十二月(12) → 丑(1)
    month_branch = (lunar_month + 1) % 12
    hour_branch = _branch_idx(hour_gz[1])
    year_branch = _branch_idx(year_gz[1])
    year_stem = _stem_idx(year_gz[0])

    # 命宫 / 身宫（书源 1662-1664「安身命例」）
    mg_pos = ming_gong_pos(month_branch, hour_branch)
    sg_pos = shen_gong_pos(month_branch, hour_branch)

    # 五行局：由命宫干支的纳音定（书源 1665-1666）
    ju = ju_from_ming_gong(year_gz[0], EARTHLY_BRANCHES[mg_pos])
    if ju is None:
        raise PaiPanError(f"年干 {year_gz[0]} / 命宫 {EARTHLY_BRANCHES[mg_pos]} 无法定五行局")

    # 紫微定位（书源五张安紫微图，按局数 + 农历日查表）
    ziwei_pos = ziwei_position(ju, lunar_day)
    if ziwei_pos < 0:
        raise PaiPanError(
            f"{JU_TO_WUXING[ju]}{ju}局 农历{lunar_day}日：书源安紫微图该格残缺，无从定紫微"
        )
    tf_pos = tianfu_position(ziwei_pos)

    # 紫微星系（逆布）、天府星系（顺布）
    zw_positions = ziwei_group_positions(ziwei_pos)
    tf_positions = tianfu_group_positions(tf_pos)

    # 余曜（各星所论见 ziwei_tables 对应函数的书源引文）
    zuo_pos, you_pos = zuo_you_positions(month_branch)
    chang_pos, qu_pos = chang_qu_positions(hour_branch)
    kui_pos, yue_pos = kui_yue_positions_by_stem(year_stem)
    lu_pos = lu_cun_pos(year_stem)
    yang_pos, tuo_pos = qing_yang_tuo_luo_pos(lu_pos)
    ma_pos = tian_ma_pos(year_branch)
    huo_pos, ling_pos = huoling_pos(year_branch, hour_branch)
    kong_pos, jie_pos = di_kong_jie_pos(hour_branch)
    xing_pos, yao_pos = tian_xing_yao_pos(month_branch)
    ku_pos, xu_pos = tian_ku_xu_pos(year_branch)
    chi_pos, ge_pos = long_chi_feng_ge_pos(year_branch)
    tai_pos, zuo8_pos = san_tai_ba_zuo_pos(zuo_pos, you_pos, lunar_day)
    fu_pos, gao_pos = tai_fu_feng_gao_pos(hour_branch)

    aux_positions: dict[str, int] = {
        "左辅": zuo_pos, "右弼": you_pos,
        "文昌": chang_pos, "文曲": qu_pos,
        "天魁": kui_pos, "天钺": yue_pos,
        "禄存": lu_pos, "擎羊": yang_pos, "陀罗": tuo_pos,
        "火星": huo_pos, "铃星": ling_pos, "天马": ma_pos,
        "地空": kong_pos, "地劫": jie_pos,
        "天刑": xing_pos, "天姚": yao_pos,
        "天哭": ku_pos, "天虚": xu_pos,
        "龙池": chi_pos, "凤阁": ge_pos,
        "三台": tai_pos, "八座": zuo8_pos,
        "台辅": fu_pos, "封诰": gao_pos,
    }

    # 各宫星曜装配：宫位idx → {主星: [...], 辅星: [...], 四化: [...]}
    # 十二宫逆布（书源 1669「男女俱从逆转」）：命宫起，依次兄弟、夫妻…
    star_positions_all = {**zw_positions, **tf_positions}
    palaces_data: dict[str, dict] = {}
    for i in range(12):
        palace_branch_idx = (mg_pos - i) % 12
        palace_name = PALACES[i]
        # 主星按 MAIN_STAR_ORDER 归一序（紫微系在前、天府系在后）——
        # 与 ziwei_tables.DUAL_PATTERNS 的键序一致，格局名不受装配顺序影响
        main_stars = [s for s in MAIN_STAR_ORDER
                      if star_positions_all.get(s) == palace_branch_idx]
        aux_stars = [s for s in AUXILIARY_STARS
                     if aux_positions.get(s) == palace_branch_idx]
        palaces_data[palace_name] = {
            "branch": EARTHLY_BRANCHES[palace_branch_idx],
            "branch_idx": palace_branch_idx,
            "main_stars": main_stars,
            "aux_stars": aux_stars,
            "sihua": [],
        }

    # 四化星（年干→星→定位→入何宫）。化科/化忌之星可为文昌文曲左辅右弼，
    # 故余曜亦须在查找范围内，否则静默丢项。
    sihua = SIHUA_TABLE.get(year_gz[0], {})
    si_list = []
    for dtype, star in sihua.items():
        star_pos = star_positions_all.get(star, aux_positions.get(star))
        if star_pos is None:
            continue
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

    # 命宫干支：五虎遁配干（唯一真值源在 ganzhi_calendar.TIGER_MONTH_STEM）
    mg_stem = HEAVENLY_STEMS[(TIGER_MONTH_STEM[year_gz[0]] + (mg_pos - 2) % 12) % 10]
    ming_gong_ganzhi = mg_stem + EARTHLY_BRANCHES[mg_pos]

    return {
        "discipline": "ziwei",
        "birth": {
            "datetime": dt.strftime("%Y-%m-%d %H:%M"),
            "gender": gender,
            "longitude": longitude,
        },
        "lunar": {
            "year": lunar["year"],
            "month": lunar["month"],
            "day": lunar["day"],
            "leap": lunar["leap"],
            "month_used": lunar_month,
        },
        "pillars": {
            "year": year_gz,
            "month": month_gz,
            "day": day_gz,
            "hour": hour_gz,
        },
        "wuxing_ju": ju,
        "ju_name": f"{JU_TO_WUXING[ju]}{ju}局",
        "ming_gong": {
            "palace_idx": mg_pos,
            "branch": EARTHLY_BRANCHES[mg_pos],
            "ganzhi": ming_gong_ganzhi,
        },
        "shen_gong": {
            "palace_idx": sg_pos,
            "branch": EARTHLY_BRANCHES[sg_pos],
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
        "calendar_policy": {
            "year_boundary": "立春（core.ganzhi_calendar）",
            "month_day": "农历朔望月（安星依据；闰月顺延一月）",
            "zi_hour": "same-day",
            "ju_basis": "命宫干支纳音",
        },
    }


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="紫微斗数排盘（chart 段，纯机械）")
    ap.add_argument("--datetime", help='出生公历 "YYYY-MM-DD HH:MM"')
    ap.add_argument("--gender", choices=["男", "女"], default=None)
    ap.add_argument("--longitude", type=float, default=None)
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    try:
        out = ziwei_chart(
            datetime_str=args.datetime,
            gender=args.gender,
            longitude=args.longitude,
        )
    except PaiPanError as exc:
        print(f"排盘异常：{exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"排盘异常：{exc}", file=sys.stderr)
        return 2

    text = json.dumps(out, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
