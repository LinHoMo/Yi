# -*- coding: utf-8 -*-
"""大六壬·课目机械识别（判据全部为结构条件；条数与分组以 IMPLEMENTED 为准）。

判据源：data/kemu.json（六壬大全 卷一「课目」歌诀诀文 + 卷七~卷十
「课经集」释义 + rules 参数），诀文/释义/参数一律外置，本模块只留算法。
课目表条数不在此写死：由 data/kemu.json 实算，门 dev_tools/check.py [1c] 与
书源卷一「课目」段逐条对齐后报出。

识别只报**结构命中**，不报吉凶——诀文里的旺相/神煞/吉将附加条件未落地者，
在 hit 的 `partial` 字段显式声明，不得当作完整判据输出（AGENTS.md 铁律一/三）。

判据分组：
  甲组·门类（10）：元首/重审/知一/涉害/遥克/昴星/别责/八专/伏吟/返吟
    —— 构型由 jiuzongmen 九宗门判据树给出（men + ke_name），本组只做映射。
  乙组·结构（10）：铸印/斲轮/斩关/联珠/全局/元胎/六纯/盘珠/励德/无禄/度厄
    —— 三传、四课、天将布法上的纯结构条件。
  丙组·旬奇（3）：三奇/六仪/闭口
    —— 旬首支由 core 旬空表推得（不另立表），奇支映射外置在 kemu.json.rules。
  另有 轩盖/引从/亨通/三交/乱首/赘胥/冲破 —— 前三批评据；九丑/天网/游子（第四批）
  与 淫泆/芜淫/侵害/刑伤/死奇/鬼墓/殃咎/龙战（第五批）同属结构判据，一并计入 IMPLEMENTED。
  未落判据者（旺相/神煞/年月/年命依赖，如需节气的天祸、二烦、天寇）只登记诀文与
  课经释义，不写占位识别。
"""
from __future__ import annotations

import json as _json
from pathlib import Path as _Path

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES as _BR
from yishu_core.liuren_tables import JI_GONG, tianjiang_layout
from yishu_core.symbols import (
    BRANCH_ELEMENTS,
    CHONG_PAIRS,
    HARM_PAIRS,
    HE_PAIRS,
    KE_CYCLE,
    SAN_HE_GROUPS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
    TWELVE_GROWTH,
    sanxing_hits,
    wangxiangxiuqiusi,
    xunkong_of,
)

from jiuzongmen import MENG, four_courses

# 已落机械判据的课目名——**唯一真值源**（dev_tools/check.py 的守门断言、
# dev_tools/build_kemu_notes.py 写 kemu.json 的 implemented 旗标都读它）。
IMPLEMENTED: tuple[str, ...] = (
    # 甲组·门类
    "元首", "重审", "知一", "涉害", "遥克", "昴星", "别责", "八专", "伏吟", "返吟",
    # 乙组·结构
    "铸印", "斲轮", "斩关", "联珠", "全局", "玄胎", "六纯", "盘珠", "励德",
    "无禄", "度厄",
    # 丙组·旬奇
    "三奇", "六仪", "闭口",
    # 前三批
    "轩盖", "引从", "亨通", "三交", "乱首", "赘胥", "冲破",
    # 第四批·结构（10-01r；不倚赖旺相/神煞/年命）
    "九丑", "天网", "游子",
    # 第五批·结构（10-01s；仍只倚赖日柱/三传/四课/时支/天将布法）
    "淫泆", "芜淫", "侵害", "刑伤", "死奇", "鬼墓", "殃咎", "龙战",
    # 第六批·结构（10-06g；只倚赖日柱/四课，六合表取 core HE_PAIRS）
    "和美",
    # 第七批·结构（10-07a；OPT-liuren_zhinan_dz-03，旺相依赖已解耦为「月支判囚死」）
    "天狱",
    # 第八批·结构（10-07b；OPT-liuren_zhinan_dz-04，日辰加临六课，只倚赖四课位置）
    "自在", "俸就", "历虚", "归宠", "培植", "脱骨", "无涉",
    # 第九批·结构（OPT-liuren_cuiyan_dz-01；L159 十二盘，分支步长判据，书源《六壬萃言》L112-124）
    "进茹", "退茹", "进间", "退间",
    # 第十批·结构（OPT-liuren_cuiyan_dz-07；L159 十二盘，集合条件，书源《六壬粹言》L147/L151）
    "关格", "稼穑",
)

# 课目**别名**登记（OPT-liuren_zhinan_dz-05）：书源一课多名者，在此登记别名 →
# 本仓课名的映射；引擎**只认 IMPLEMENTED 里的课名**，别名仅作显示与检索，
# **不另立课目**（同「赘婿／赘胥」的处理：书源多作赘婿，本仓课名取卷一歌诀的「赘胥」，
# 别名走 `aliases` 而非新增条目）。
# 别名数据源唯一真值源：data/kemu.json#aliases（消费方 dev_tools/check.py [1e] 校验）。
KE_NAME_VARIANTS: dict[str, str] = {
    "无依": "井栏射",   # 指南 L28「乃名无依（无亲、井栏）」——返吟无克六日
    "无亲": "井栏射",   # 同上，指南括注
    "赘婿": "赘胥",     # 指南／课经集多作赘婿，卷一歌诀作赘胥
    "曲直": "全局",     # OPT-liuren_cuiyan_dz-05：三合四局指向全局课目；ju_name 区分
    "炎上": "全局",     # 同上
    "从革": "全局",     # 同上
    "润下": "全局",     # 同上
    "顺关隔": "关格",   # L159 十二盘（关格＝四仲三传＝子午卯酉；顺逆别名，不另立课目）
    "逆关隔": "关格",   # 同上
    "顺稼穑": "稼穑",   # L159 十二盘（稼穑＝四季土三传＝辰戌丑未；顺逆别名，不另立课目）
    "逆稼穑": "稼穑",   # 同上
}

# 课名/诀文/释义/判据参数唯一真值源（AGENTS.md §三）：data/kemu.json
_KEMU = _json.loads(
    (_Path(__file__).resolve().parent.parent / "data" / "kemu.json")
    .read_text(encoding="utf-8"))
_KEMU_DATA = {e["name"]: e for e in _KEMU["entries"]}
_RULES = _KEMU.get("rules") or {}

CHONG_OF: dict[str, str] = {}
for _a, _b in CHONG_PAIRS:
    CHONG_OF[_a] = _b
    CHONG_OF[_b] = _a

_MENG = MENG                                          # 四孟取用：与九宗门共用一份（元胎：孟神发用传皆四孟）
_YANG = frozenset(_BR[::2])                           # 阳支（六纯判据）：由 core 地支序推出，不另立表
_TU = frozenset({"辰", "戌", "丑", "未"})             # 四季土支（游子「三传皆土」判据 + 稼穑「传皆季神」）
_SI_ZHONG = frozenset({"子", "卯", "午", "酉"})      # 四仲支（关格「三传皆四仲」判据）

# 九丑日（卷一「课目」诀注逐字：「凡戊子、戊午、壬子、壬午、乙卯、乙酉、己卯、
# 己酉、辛卯、辛酉十日，为九丑日」）——子午卯酉配乙戊己辛壬十日之列，照录不增删。
_JIUGUI_DAYS = frozenset({
    "戊子", "戊午", "壬子", "壬午", "乙卯", "乙酉", "己卯", "己酉", "辛卯", "辛酉",
})


def _elem(x: str) -> str:
    return BRANCH_ELEMENTS.get(x) or STEM_ELEMENTS.get(x) or ""


def _ke(a: str, b: str) -> bool:
    """a 克 b。"""
    ea, eb = _elem(a), _elem(b)
    return bool(ea and eb) and KE_CYCLE[ea] == eb


def _sheng(a: str, b: str) -> bool:
    """a 生 b。"""
    ea, eb = _elem(a), _elem(b)
    return bool(ea and eb) and SHENG_CYCLE[ea] == eb


def _neighbors(target: str, a: str, b: str) -> bool:
    """a、b 恰为 target 在支环上的前后两位（引从）。"""
    i = _BR.index(target)
    prev, nxt = _BR[(i - 1) % 12], _BR[(i + 1) % 12]
    return {a, b} == {prev, nxt}


def _xun_head(day_ganzhi: str) -> str:
    """旬首支。读 core 旬空表反解：空亡两支为「旬首前二位、前一位」。

    甲子旬空戌亥 → 旬首子。**不另立旬首表**（唯一真值源在 core，AGENTS.md §二）。
    """
    kong = xunkong_of(day_ganzhi)
    if len(kong) != 2:
        return ""
    return _BR[(_BR.index(kong[1]) + 1) % 12]


def recognize(chart_out: dict) -> list[dict]:
    """chart 段输出 → 命中课目列表 [{name, basis, partial, verse, note, note_src}]。"""
    need = ("moment", "san_chuan", "tianpan", "men", "ke_name")
    missing = [k for k in need if k not in chart_out]
    if missing:
        raise KeyError(f"kemu.recognize 缺 chart 字段 {missing}（不静默降级）")
    san = chart_out.get("san_chuan") or []
    if len(san) != 3:
        return []
    chu, zhong, mo = san
    day_gz = chart_out["moment"]["day_ganzhi"]
    day_stem, day_branch = day_gz[0], day_gz[1]
    hour_branch = (chart_out.get("moment") or {}).get("hour_branch") or ""
    jigong = JI_GONG[day_stem]
    tianpan = chart_out.get("tianpan") or {}
    men = chart_out.get("men") or ""
    ke_name = chart_out.get("ke_name") or ""
    courses = four_courses(day_stem, day_branch, tianpan)
    hits: list[dict] = []

    def hit(name: str, basis: str, partial: str = "") -> None:
        entry = _KEMU_DATA.get(name) or {}
        hits.append({"name": name, "basis": basis, "partial": partial,
                     "verse": entry.get("verse") or "",
                     "note": entry.get("note") or "",
                     "note_src": entry.get("note_src") or ""})

    # ── 甲组·门类（men/ke_name 由 jiuzongmen 判据树机械给出，此处只映射） ──
    if men == "贼克" and ke_name == "元首":
        hit("元首", "一上克下，余课无克，为元首课")
    elif men == "贼克" and ke_name == "重审":
        hit("重审", "一下贼上，余课无克，为重审课")
    elif men == "比用":
        hit("知一", "二上克下或二下克上，择课之阴阳与今日比者为用")
    elif men == "涉害":
        hit("涉害", "俱比俱不比，各涉归本家数其受克深浅，取深者为用")
    elif men == "遥克":
        hit("遥克", f"四课无克，取日干与四课上神相克者为用（{ke_name}）")
    elif men == "昴星":
        hit("昴星", f"四课上下无相克，又无遥克，取从魁上下神为用（{ke_name}）")
    elif men == "别责":
        hit("别责", "三课无克，别取一神为用")
    elif men == "八专":
        hit("八专", "干支同位无克，取阳顺阴逆三神为用")
    elif men == "伏吟":
        hit("伏吟", "月将加时十二神各居本宫，取神克日为用")
    elif men == "返吟":
        hit("返吟", "十二神各居冲位，取相克为用")

    # ── 乙组·结构（三传/四课/天将布法上的纯结构条件） ──
    # 斩关：魁罡（辰戌）加日干寄宫或日支而发用
    for _t, _label in ((jigong, "日干寄宫"), (day_branch, "日支")):
        if tianpan.get(_t) in ("辰", "戌") and tianpan.get(_t) == chu:
            hit("斩关", f"魁罡加{_label}发用（{chu}临{_t}）")
            break
    # 铸印：戌加巳而居三传之中
    if zhong == "戌" and tianpan.get("巳") == "戌":
        hit("铸印", "戌加巳中传（戌为印，巳为炉）")
    # 斲轮：卯加庚（庚寄申）或加辛（辛寄戌）为用
    if chu == "卯" and (tianpan.get("申") == "卯" or tianpan.get("戌") == "卯"):
        hit("斲轮", "卯加庚或加辛为用（卯为车轮，庚辛为刀斧）",
            "诀又须遁干庚/乙庚，未并入判据")
    # 全局：三传成三合局（三合表唯一真值源在 core）
    for _e, _grp in SAN_HE_GROUPS.items():
        if set(san) == set(_grp):
            hit("全局", f"三合俱在传（{_e}局）")
            break
    # 联珠：三传相连作中末——「连茹兼进退，间传顺逆此中论」（卷一歌诀六四条）
    _i0, _i1, _i2 = (_BR.index(b) for b in san)
    _step = ((_i1 - _i0) % 12, (_i2 - _i1) % 12)
    _named = {(1, 1): "顺连茹", (11, 11): "逆连茹",
              (2, 2): "顺间传", (10, 10): "逆间传"}
    if _step in _named:
        hit("联珠", f"三传相连作中末（{_named[_step]}）",
            "卷十「连珠课/间传课」分立两目，本判据依卷一歌诀条目并收四式")
        # 十二地盘变体名（L159，《六壬粹言》L112-124 逐字）
        if _step == (1, 1):
            hit("进茹", "三传之神俱在一方，顺行而进（支序+1相连）",
                "《六壬粹言》L112 逐字；诀又须神将吉方入课，未并入判据")
        elif _step == (11, 11):
            hit("退茹", "三传之神，俱在一方，逆行而退（支序-1相连）",
                "《六壬粹言》L116 逐字")
        elif _step == (2, 2):
            hit("进间", "凡课得间一位作三传，顺行而进（支序+2）",
                "《六壬粹言》L120 逐字")
        elif _step == (10, 10):
            hit("退间", "谓课得间一位作三传，逆行而退（支序-2）",
                "《六壬粹言》L124 逐字")
    # 关格／稼穑：十二地盘两课（L159，《六壬粹言》L147/L151 逐字；纯集合条件，不涉及顺逆序）
    if set(san) <= _SI_ZHONG:
        hit("关格", "三传皆四仲（子午卯酉），为关格课",
            "《六壬粹言》L147 逐字；顺逆序未并入判据（步长已由联珠分支覆盖）")
    if set(san) <= _TU:
        hit("稼穑", "三传皆季神（辰戌丑未），为稼穑课",
            "《六壬粹言》L151 逐字")
    # 玄胎：孟神发用，传皆四孟（卷十作「元胎课」，卷一名「玄胎」）
    if all(b in _MENG for b in san):
        hit("玄胎", "孟神发用，传皆四孟", "课经集作「元胎课」，名从卷一歌诀「玄胎」")
    # 六纯：四课上下与三传俱阳 / 俱阴
    _all_b = [c["xia"] for c in courses] + [c["shang"] for c in courses] + list(san)
    if all(b in _YANG for b in _all_b):
        hit("六纯", "四课三传俱阳，为六阳课")
    elif all(b not in _YANG for b in _all_b):
        hit("六纯", "四课三传俱阴，为六阴课")
    # 盘珠：三传皆在四课之上（回还格）
    if set(san) <= {c["shang"] for c in courses}:
        hit("盘珠", "三传皆在四课之上，为回还格",
            "天心格（太岁/月建并入四课）条件未落地，只报回还一格")
    # 励德：天乙立卯酉（天将布法由 core 机械给出）
    layout = tianjiang_layout(day_stem, chart_out["moment"]["hour_branch"], tianpan)
    if any(j == "贵人" and p in ("卯", "酉") for p, j in layout.items()):
        hit("励德", "天乙立卯酉")
    # 无禄：四课四上俱克下；度厄：三上克下或三下贼上
    _up = sum(_ke(c["shang"], c["xia"]) for c in courses)
    _down = sum(_ke(c["xia"], c["shang"]) for c in courses)
    if _up == 4:
        hit("无禄", "四课四上俱克下")
    elif _down == 4:
        hit("无禄", "四课四下俱贼上")
    if _up == 4 or _down == 4:
        hits[-1]["partial"] = "卷一歌诀作「无禄四下贼乎上」，卷九定义作「四上俱克下」，两读并收"
    if _up == 3:
        hit("度厄", "四课内三上克下")
    elif _down == 3:
        hit("度厄", "四课内三下贼上")

    # ── 丙组·旬奇（旬首支由 core 旬空表反解；奇支映射外置 kemu.json.rules） ──
    xun_head = _xun_head(day_gz)
    if xun_head:
        _qi = {_RULES.get("xun_qi", {}).get(xun_head),
               _RULES.get("stem_qi", {}).get(day_stem)} - {None}
        _hit_qi = [q for q in sorted(_qi) if q in san]
        if _hit_qi:
            hit("三奇", f"旬日之奇发用或入传（{'、'.join(_hit_qi)}）")
        if xun_head in san:
            hit("六仪", f"旬首之仪发用或入传（{xun_head}）", "支仪十二课未并入判据")
        xun_tail = _BR[(_BR.index(xun_head) + 9) % 12]
        if tianpan.get(xun_head) == xun_tail:
            hit("闭口", "旬尾加旬首为用",
                "「旬首乘元武」「旬首位上神乘元武」二式未并入判据")

    # ── 前三批评据 ──
    if san == ["午", "卯", "子"]:
        hit("轩盖", "三传午卯子", "诀又须正/七两月，月支条件未并入判据")
    for target, label in ((jigong, "日干寄宫"), (day_branch, "日支")):
        if _neighbors(target, chu, mo):
            hit("引从", f"初传末传引从{label}（{chu}…{mo}）")
            break
    if _sheng(chu, zhong) and _sheng(zhong, mo) and _sheng(mo, day_stem):
        hit("亨通", "三传递生日干（天生一式）", "「地生」一式未实现")
    if all(b in ("子", "午", "卯", "酉") for b in san):
        hit("三交", "三传皆四仲", "诀又须阴不备/合逢，未并入判据")
    if tianpan.get(jigong) == day_branch and _ke(day_branch, day_stem):
        hit("乱首", "支加干上而克干")
    if tianpan.get(jigong) == day_branch and _ke(day_stem, day_branch):
        hit("赘胥", "支临干上而被干克")
    elif tianpan.get(day_branch) == jigong and _ke(jigong, day_branch):
        hit("赘胥", "干加支上而克支")
    # ── 结构补充批三（10-07 OPT-liuren_zhinan_dz-04）：日辰加临六课（乱首/赘胥之外六课） ──
    # 乱首＝支加干上克干，赘胥＝支临干上被克或干加支上克支（已在上面）；本批余六：
    #   · 支加干上生干→自在；支干相加而生干者                   L374「辰临日而生日」
    #   · 干支相加干支上神相脱→历虚                           L378「日临辰而生辰」
    #   · 干支相加干被支生→俸就                               L376「日临辰而受生」
    #   · 支加干上干来生支→归宠                               L380「辰临日而受生」
    #   · 干支比和相加→培植                                   L382「同类相加培植和合」
    #   · 干支上神互盗其气→脱骨                               L383「日辰交生名为脱骨」
    #   · 干支上神互战并伤→无涉                               L384「日辰交克号曰无涉」
    # 互斥保证(相同天盘干支位置)：乱首/赘胥/自在/俸就/历虚/归宠/培植 七者由上下位不同
    # 与生克方向唯一锁定；脱骨/无涉 补充覆盖上神生盗与上神交克。书源《六壬指南》L371-386。
    _tinggan = tianpan.get(jigong) == day_branch      # 支加干上（辰临日）
    _tingzhi = tianpan.get(day_branch) == jigong      # 干加支上（日临辰）
    if _tinggan and _ke(day_branch, day_stem):
        pass    # 乱首已报支加干上克干
    elif _tinggan and _sheng(day_branch, day_stem):
        hit("自在", "支支相临，支来生干（辰临日而生日——恢宏之志）")
    elif _tinggan and _sheng(day_stem, day_branch):
        hit("归宠", "支干从上，干来生支（辰临日而受生——福履之来崇）")
    elif _tingzhi and _ke(jigong, day_branch):
        pass    # 赘胥已报干加支上而克支
    elif _tingzhi and _sheng(day_branch, day_stem):
        hit("俸就", "干来加支上，支生干（日临辰而受生——荣显之机）")
    elif _tingzhi and _sheng(day_stem, day_branch):
        hit("历虚", "干来加支上，干生辰（日临辰而生辰——脱气之征）")
    if STEM_ELEMENTS.get(day_stem, "") and STEM_ELEMENTS[day_stem] == BRANCH_ELEMENTS.get(day_branch, ""):
        hit("培植", "干支比和，同类相加（五行相等——培植和合）")
    _shanggan = tianpan.get(jigong) or ""
    _shangzhi = tianpan.get(day_branch) or ""
    # 脱骨 = 干支上神相盗其气：生我者为父母，我生者为子孙——上神见子孙盗气
    if _shanggan and _shangzhi and _sheng(_shanggan, _shangzhi):
        hit("脱骨", f"干上神{_shanggan}盗支上神{_shangzhi}之气（日辰交生——彼我舒情）")
    if _shanggan and _shangzhi and _ke(_shangzhi, _shanggan):
        hit("无涉", f"支上神{_shangzhi}伤干上神{_shanggan}（日辰交克——内外疑忌）")
    if chu in (CHONG_OF.get(jigong), CHONG_OF.get(day_branch)):
        hit("冲破", f"初传{chu}冲日辰", "诀又须岁月破神并，未并入判据")

    # ── 结构补充批（10-01r）：判据只倚赖**日柱/三传/四课/时支**等结构，不涉旺相/神煞/年命 ──
    # 九丑：日柱属书源所列十日（十日之日支恰为子午卯酉四仲），而丑发用（初传为丑）
    # 诀注作「如四仲时占，丑临日加四仲上发用，为九丑课」——「丑临日加四仲上」传抄有异读
    # （或读作四仲时、或读作四仲日），本判据取「十日 + 初传丑」一面，故标 partial。
    if day_gz in _JIUGUI_DAYS and chu == "丑":
        hit("九丑", f"九丑日{day_gz}而丑发用（初传丑）",
            "诀注「如四仲时占，丑临日加四仲上发用」有传抄异读（时/日），本判据取「十日+初传丑」一面")
    # 天网：占时与用神俱克日干（诀「时用俱克日」）
    if _ke(hour_branch, day_stem) and _ke(chu, day_stem):
        hit("天网", f"占时{hour_branch}与用神{chu}俱克日干{day_stem}")
    # 游子：三传皆土（辰戌丑未）
    # 诀作「三传皆土，遇旬丁天马为用」——本判据只取「三传皆土」一面（结构特征），
    # 旬丁/天马附加条件未并入，故标 partial（同铸印/斲轮对「诀又须…」的处理）。
    if san and all(b in _TU for b in san):
        hit("游子", f"三传皆土（{'、'.join(san)}）",
            "诀又须「遇旬丁天马为用」，本判据只取三传皆土一面")

    # ── 结构补充批二（10-01s）：判据仍只倚赖**日柱/三传/四课/时支/天将布法** ──
    _he_pairs = {frozenset(p) for p in HARM_PAIRS}
    _tomb_day = TOMB_MAP.get(STEM_ELEMENTS.get(day_stem, ""))
    _tomb_zhi = TOMB_MAP.get(BRANCH_ELEMENTS.get(day_branch, ""))
    _gan_shang, _zhi_shang = tianpan.get(jigong), tianpan.get(day_branch)

    # 淫泆：初传卯酉为用，将乘后合（卯酉为阴私之门，后合为淫欲之神）
    _pos_chu = next((p for p, s in tianpan.items() if s == chu), None)
    _jiang_chu = layout.get(_pos_chu) if _pos_chu else ""
    if chu in ("卯", "酉") and _jiang_chu in ("六合", "天后"):
        hit("淫泆", f"初传{chu}为用而乘{_jiang_chu}",
            "诀又分「狡童格」（用起六合终于天后）与「泆女格」，本判据未分立二格")
    # 侵害：日辰六害相加（干上神与支上神相害）
    if frozenset((_gan_shang, _zhi_shang)) in _he_pairs:
        hit("侵害", f"日辰六害相加（干上神{_gan_shang}与支上神{_zhi_shang}相害）",
            "书注诸例（子加未、丑加午…）为单课上下相害之式，本判据取「日辰上神相加」一面；"
            "「并行年为用」未并入判据")
    # 刑伤：三传递见三刑
    _tri = sanxing_hits(list(san))
    if _tri:
        hit("刑伤", f"三传递见三刑（{'、'.join(_tri)}）",
            "诀又须「并行年为刑」，「本命与年命」条件未并入判据")
    # 死奇：斗罡（辰）加日辰阴阳而发用（初传为辰，且辰为四课之上神）
    if chu == "辰" and any(c["shang"] == "辰" for c in courses):
        hit("死奇", "斗罡（辰）加日辰阴阳而发用",
            "诀又须「月缠天罡…丘墓岁伏殃灾随」的年月神煞条件，未并入判据")
    # 芜淫：四课不备（有一课重复）而课有克
    if len({(c["xia"], c["shang"]) for c in courses}) < 4 and (_up + _down) > 0:
        hit("芜淫", "四课不备（有一课重复）而四课有克",
            "书注又列「日辰交互相克」一面，本判据未并入（该面另覆盖近半课式，与「不备」并列会使判据失焦）")
    # 鬼墓：日辰之墓神或日鬼发用
    if chu in (_tomb_day, _tomb_zhi) or _ke(chu, day_stem):
        if chu == _tomb_day:
            _gm_why = f"初传{chu}为日干{day_stem}之墓"
        elif chu == _tomb_zhi:
            _gm_why = f"初传{chu}为日支{day_branch}之墓"
        else:
            _gm_why = f"初传{chu}克日干{day_stem}（日鬼发用）"
        hit("鬼墓", _gm_why,
            "书源并列「日辰墓神」「日鬼发用」两面，本判据取其一即报；"
            "用起四墓/自坐四墓/干支乘墓诸格未逐格分列")
    # 殃咎：三传递克日干，或干支乘墓
    _di_ke = ((_ke(chu, zhong) and _ke(zhong, mo) and _ke(mo, day_stem))
              or (_ke(mo, zhong) and _ke(zhong, chu) and _ke(chu, day_stem)))
    if _di_ke:
        hit("殃咎", "三传递克日干（初中末递克，终于克日）",
            "「神将克战」一面需将神五行表，未并入判据")
    elif _gan_shang == _tomb_day and _zhi_shang == _tomb_zhi:
        hit("殃咎", "干支乘墓（干上神为干墓、支上神为支墓）",
            "「神将克战」一面需将神五行表，未并入判据")
    # 龙战：卯酉日占而卯酉发用
    if day_branch in ("卯", "酉") and chu in ("卯", "酉"):
        hit("龙战", f"{day_branch}日占而{chu}发用",
            "诀又须「人年立卯酉」，行年条件未并入判据")
    # 第六批·和美：干支六合相加（六合表唯一真值源 core HE_PAIRS）
    #   课经释义两面同构：①干上神与支上神作六合（戊辰日干上丑支上子、辛酉日干上未
    #   支上午）②干上神与日支作六合（乙丑日干上子、丙寅日干上亥）。
    #   「甲申日干上亥支上巳俱合」一例与六合定义相悖（亥巳为六冲），疑传抄讹误，
    #   不为凑例改判据。三传三合/上下递互诸式未并入。
    _he6 = {frozenset(p) for p in HE_PAIRS}
    if frozenset((_gan_shang, _zhi_shang)) in _he6:
        hit("和美", f"干支上神作六合（干上{_gan_shang}与支上{_zhi_shang}相合）",
            "诀兼「三传三合」「上下递互作合」诸式，本判据取「干支上神六合」一面")
    elif frozenset((_gan_shang, day_branch)) in _he6:
        hit("和美", f"干上神{_gan_shang}与日支{day_branch}作六合",
            "诀兼「三传三合」「上下递互作合」诸式，本判据取「干支上下作六合」一面")

    # ── 天狱（OPT-liuren_zhinan_dz-03）：解除「需旺相依赖」的阻塞 ──
    # 源《六壬指南》L178 逐字：`○凡用神囚死更天罡加日本之上曰天狱卦，主官非口舌、刑罚及身。`
    #   条件只取前半：**用神落囚／死 ＋ 天罡（辰）加日本**；末句「主官非口舌、刑罚及身」
    #   是断语，**不入结构层**（大六壬骨架层铁律）。
    # 「日本」定义取《六壬大全》卷九课经集注逐字：「日本者，亥为甲乙之本，寅为丙丁之本，
    #   申为戊己壬癸之本，巳为庚辛之本」——即日干长生位，故**不另立日本表**，
    #   由 core 十二长生（`TWELVE_GROWTH`，唯一真值源）反解长生支。
    # 旺相依赖已解耦：囚／死由 core `wangxiangxiuqiusi` 按**月支**判，
    #   本条判据只倚赖月支／日柱／三传／天地盘，**不引神煞、不引年命**。
    _month_branch = (chart_out.get("moment") or {}).get("month_branch") or ""
    if _month_branch:
        _chu_state = wangxiangxiuqiusi(_month_branch, _elem(chu))
        if _chu_state in ("囚", "死"):
            _riben_branch = next(
                (b for b, st in TWELVE_GROWTH.get(STEM_ELEMENTS.get(day_stem, ""), {}).items()
                 if st == "长生"), "")
            if _riben_branch and tianpan.get(_riben_branch) == "辰":
                hit("天狱", f"用神{chu}落{_chu_state}而天罡（辰）加日本"
                            f"（{day_stem}长生在{_riben_branch}）",
                    "《六壬大全》卷一诀另含「墓」一面（天狱墓死作囚用），"
                    "本判据据指南 L178 只取「囚死」一面，未并入「墓」与「四八大过」")
    return hits
