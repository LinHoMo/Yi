# -*- coding: utf-8 -*-
"""六爻应期（YP）：候选支收集 + 法则方法 + 择优排序 + 窗口计算。

应期四诀／九法书源对拍表（2026-10-07 补注记，落 OPT-yiin_dz-03 / OPT-huangjince_dz-06）
════════════════════════════════════════════════════════════════════════════
本表只做**出处对照与缺口登记**，不改任何判定值、不新增 Rule。
列义：书源方法 → 引擎落点（函数:行）→ 覆盖状态（已实现／口径不一致／缺失）。
逐字引文可回指 `源L<行>`，行号即 data/sources/<书>.dz.txt 的物理行号。

【甲】《易隐》应期四诀（书源：`data/sources/yiin_dz.dz.txt`，OPT-yiin_dz-03）
────────────────────────────────────────────────────────────────────────
1. 动合日／静冲日／伏值日／休生旺日
   源L1556 逐字：「用动，则以六合之日为期也。用静，则以冲动之日为期也。
   用伏藏旺相，则以用爻值日为期。用出现休囚，则以生旺之日为期也。」
   引擎：`_build_timing_methods` 出 timing_methods 四条
   （逢值/逢冲/待旺时/出空）+ `_rank_candidates` 的
   「发动值日」「用神值日」「动逢合日」「静逢冲日」。
   状态：**已实现**（四态齐备；六合日/三合日按 _he()/_collect_key_branches 合支并入）。

2. 行人归期：三合日／六合日／静取冲动月日／旺生月日／衰取旺日／旺取墓日
   《易隐》源L2051 逐字：「凡用爻应爻动者，三合日到，或六合日到也。静取冲动月日起程，
   旺生月日到也。衰取旺日到，旺取墓日到也。」
   引擎：合日→`_collect_key_branches` 推 _he 支；静冲月日→日/月/年级
   三档各有一条「静逢冲日」；衰取旺日→use_weak_wait_prosper 排 PEAK_BRANCH；
   旺取墓日→use_tomb_chong_tomb／_month／_year 三档。
   状态：**已实现**（月日级；「三合日」按三合局支并入 key_branches）。

3. 尹逢头断法四句（应期总纲，最紧凑的四条）
   《易隐》源L2168 逐字：「用旺还须墓日定，用休生旺日当成，用伏但看用值日，
   动逢合住待冲辰。」
   引擎：用旺墓日定→use_tomb_chong_tomb；用休生旺日当成→
   use_weak_wait_prosper；用伏但看用值日→「伏神值日」；
   动逢合住待冲辰→bound_by 分支「用神被X合住，冲开之日」。
   状态：**已实现**（四句逐句有落点；「合住待冲」为 bound_by 分支）。

4. 迟速四段（动速静迟／旺相出现速／囚死伏藏迟／爻位与宫位迟速）
   《易隐》源L2168 逐字：「动速静迟，旺相出现速，囚死伏藏迟。…初二爻动速，三四爻动，
   犹豫迟疑。五动迟，六动更迟。」
   引擎：`_build_timing_methods`(387-395) 只出 speed 三档
   （极旺/旺→应速；中和→应期适中；其余→应迟），**不分爻位、不分宫位**。
   状态：**口径不一致（登记不采）**——爻位/宫位迟速为《易隐》一家专论，
   与增删《应期直读法》体系不同；贸然细分会动排序与读数，
   按 SKILL.md 不在补注记轮次改判定值，只登记分歧。
   现有 speed 标签已能表达「动/静 + 旺衰」的粗分速调。

【乙】《黄金策·千金赋》期日九法（OPT-huangjince_dz-06）
────────────────────────────────────────────────────────────────────────
源L264「用爻旺相不动，以冲动月日断」 夹注逐字（九法原文照录，不删不改）：
  「用爻旺相不动，以冲动月日断；用爻有气发动，以合日断，或以本日断；
    用爻受制，以制杀月日断；用爻得时旺动，又遇生扶，此为太旺，应以墓库月日断；
    用爻无气发动而遇生扶，即以生扶之月日断；用爻入墓，则以破墓月日断；
    用爻空亡，以冲动月日断；用爻旺空，或空而逢冲、逢并、逢动者，以过旬断；
    若占散事，应以用爻死墓绝日断等等。」
《黄金策》源L263 逐字：「若遇休囚，必生旺而成事。」／源L265 逐字：「速则动而克世，缓则静而生身。」

  #  方法（《黄金策》源L264「此谈期日之法」）      引擎落点                                状态
  1 旺相不动→冲动月日      YINGQI_TXT[use_quiet_chong_day] 静逢冲   已实现
  2 有气发动→合日/本日      use_moving_he_day 动逢合日＋dufa_value_day 独发值日 已实现
  3 受制→制杀月日           use_god_restrained_zhi_sha_日/月（窄化谓词，见下） 已实现(156)
  4 太旺（旺动逢生扶）→墓库 重叠_taiwang_tomb_日/月（主语＝临日月之重叠爻） 已实现(78)
  5 无气发动逢生扶→生扶月日 use_weak_wait_prosper 待旺／"待旺时"法  已实现
  6 入墓→破墓月日            YINGQI_TXT[use_tomb_chong_tomb] 冲墓    已实现
  7 空亡→冲动月日            empty_chong_real／chronic_empty_wait_chong 已实现
  8 旺空/空逢冲并动→过旬     _rank_candidates 出旬之日支（全局，第 2 位）  已覆盖
  9 散事→用爻死墓绝日        ——                                        缺失
  ＋ 休囚→生旺（《黄金策》源L263「若遇休囚，必生旺而成事」）      use_weak_wait_prosper（PEAK_BRANCH）      已实现
  ＋ 速则动而克世/缓则静而生身
    （《黄金策》源L265「速则动而克世，缓则静而生身」）                ——（speed 只按旺衰分档，未按动克世/静生身） 部分

  缺口处置（截至第一百五十六批的现状：第 3/4 法已实现（第 3 法第一百五十六批、第 4 法第七十八批），
  第 9 法仍不补，各条理由见下；
  「本轮不补」这一旧措辞已按实改为具名现状，避免读者把它当悬空的待办）：
  - 第4法「太旺→墓库月日」：**第七十八批已按书接上**（落点见 `_rank_candidates` 内
    「期日第4法」块）。历史上的坑不是"没有谓词"，而是**谓词挂错了主语**——
    《黄金策》源L264 夹注字面写「用爻得时旺动」，第六十八批就照字面挂在用神上建了三条件合取，
  · 第六十八批实做过又**实测后还原**（不是没试）：按夹注三条件合取（用神旺相＋用神自身发动＋日月或动爻生扶）
    建「太旺」谓词，候选＝值墓库支，日月两级各排一处，另加「已入墓则归第6法冲墓」的避让守卫。
    实测：[2] 36、[3] 11、[4] 18、tune 97.3／64.7／1.53、holdout 90.2／50／1.6 全不动；但只读外部集
    wikisource_holdout 66.2→66.0（名次 2.29→2.25 反更好）、suigui_holdout 98.5→97.5（名次 1.5→2.0 变差），
    288 例机械 52f36e9d→a535d2ed；加守卫后仍是 66.0／97.5（机械 ed345ce9）——假设被自己的实验否掉，
    且无法把这次下跌归因到具体盘（130 例经典案例里该谓词一例都不触发，可观测信号只剩 eval 集 46 盘）。
    故按「解释不了就不留」整条还原，第4法**仍记缺失**。
    下一次动手的前置：先取得一条书上明写「太旺→应墓库月日」的全要素真例（照 reg_19 四步：取要素→
    derived_hexagrams 验卦名→ganzhi_of 反算干支→expected 只取书判），让这条法有可判落点再谈排序。
  · 第六十九批：前置真例**已找到**（就在本章）。《增删卜易》源L1673 逐字「如午月戊午日占何日雨得地风升变恒卦」，    爻行源L1674-L1679（初妻财丑土″应／二父母亥水′／三官鬼酉金′／四妻财丑土″世**动**化子孙午火′／五父母亥水″／    上官鬼酉金″），断语源L1680 逐字「午火子孙临日月旺之极矣，乃为用爻重叠，逢墓库以收藏，故知戌必雨。果于戌日申时雨」。    机器核对：`derived_hexagrams([8,7,7,6,8,8]) == ('升','恒')`、`ganzhi_of(2024-06-23)` 实算 午月戊午日、    `TOMB_MAP[火] == 戌`（与书上应期同支）。
    **关键更正**：书上这条的落点不是「用神太旺」，而是**临日月而重叠之爻（此处化出之子孙午火）取该五行之墓库日**——    用神是父母亥水。第六十八批那次还原的实现正是把谓词挂在用神上（前提错），这解释了它为何只动外部集而不修好任何一例。    重做要以「哪个爻临日月且重叠」为主语，且必须有可判真例在前。
  · 第七十八批：按第六十九批更正后的主语落地——谓词＝**月建与日辰同支、卦中（本爻或化出）
    再见该支**之重叠爻，候选＝该支五行之墓库支（日/月两级各排一处）；两条避让：重叠支＝用神支
    不排（用神太旺入墓于书无据、且与第6法相抵），重叠支旬空不排。真例复算：`升之恒`（午月戊午日）
    主应期由「亥日（用神值日）」改为**「戌日（重叠之爻临日月太旺，逢墓库之日收藏）」**，
    与《增删卜易》源L1680「故知戌必雨。果于戌日申时雨」同支（壬戌＝戊午后第四日，实算合）。
    实测（同批 rc=0 运行）：288 例金标准机械 52f36e9d6760d4c4／措辞 7200af9a70d2df8f **零漂移**；
    tune 97.3／64.7／1.53、holdout 90.2／50／1.6、外部 87.9／67.4／72.4／98.5 全不变；
    [2] 36、[3] 11、[4] 18、[14] 493 指针／460 可验／457 逐字命中／0 判红／10 NOTE。
    逐集实查本法命中数：tune 0、holdout 0、wikisource_holdout 0、suigui 0、huozhulin 0、
    yingqi_holdout 0、wikisource_direction 2（该集应期为 N/A，只评方向，故方向分不动）。
    ⇒ 与第六十八批的分水岭：那次挂在用神上，谓词在 130 例经典案例里一例不触发、
    只晃外部集（66.2→66.0、98.5→97.5）；这次挂在重叠爻上，在**书上那条真例上触发并把主应期
    改成书上的支**，而在所有已评分集上零命中、零读数漂移——即"补上缺口"而非"调出分数"。
    仍**不进 tune**：本集里没有任何一张盘满足该条件，所以这条法目前只有一个可判落点（书例本身），
    扩大验证的路径是给 fixture 增例（见 reg_19 的四步做法），不是给排序加权重。
  - 第3法「制杀月日」：**第一百五十六批已按书接上**（落点见 `_rank_candidates` 内
    「期日第3法」块；日级置于病药块内、用神值日之前，月级对称置于月梯之首）。
    书据：《黄金策》源L264 夹注逐字「用爻受制，以制杀月日断」＋《增删卜易》源L643
    逢伤章逐字「爻值月建乃为旺矣，或被他爻所克，即谓之逢伤……待至冲去伤爻之日则不
    受其伤矣，病者必愈、事必成」＋源L594「忌神宜克不宜生」。候选＝冲克神之支。
    **谓词窄化**（广义版实测回归，已整条还原，逐例反例登记在 CHANGELOG 第一百五十六批）：
    回头克＋任一动爻本支克（无门）→ holdout top-1 50%→37.5%、wikisource 22.7%→18.2%
    （HO008/WS018 回头克但用神不临月建、WS017 的「克者」实为解神、WS023 用神月破、
    ZD102 书答辰父发动值日、ZD065 书答忌神值月而非制杀）。现行两道门：
    ① 回头克（化出支克本支）＋用神临月建＝L643「逢伤」原文形，真例 ZD015（子日）；
    ② 动爻本支克用神＋用神静＋该动爻化进神（ADVANCE_PAIRS，忌神得势而进），真例
    ZD160（申金动克卯木财、化酉进神，书答寅月冲申）／ZD125（申月）。
    实测（同批 rc=0 运行）：tune 97.3／64.7／1.53、holdout 90.2／50.0／1.6、
    wikisource 62.9／22.7／2.27、suigui 98.5／50.0／1.5、yingqi_holdout 87.9
    全部逐位不变；zengshan_dz（外部集）47.7→54.1、top-1 13.6→27.3（22 例时点）；
    288 例金标准机械层 33 例漂移（化空月梯，下条）已具名登记 digest drift_log。
  ＋ 化空月级梯（与日级 change_branch_empty_fill 对称，真例 ZD151「世化官空，
    八九月必见，果于八月丁艰」＝酉月）：变卦化出之支逢空 → 该支出空填实之月，
    与日级同置月阶梯之首。日级原有（病药块之首）、月级缺失，本批补对称；
    除 ZD151 外各已评分集零触发、零读数漂移。
  - 第8法「过旬」：已补全局口径（2026-10-10）——旬空案例把**出旬之日**（旬首支+10）
    排入候选第 2 位（值空支之后）。为什么不排第 1：本块只在**用神旬空**时触发，
    可检因此只剩 4 例（日级、基准应支落在当日旬空两支之内）——ZS017 用神即出旬支
    （池内已有，去重跳过）、ZS006 用神为另一空支而书上答出旬日（卯木财空、
    癸丑日次晨即甲寅，《增删卜易》源L1573「又因卯木财空，次日出空而退灾」，新候选唯一能赢的一例）、
    ZS002 酉／ZS004 亥 书上就是值空支填实
    （提到第 1 会反伤这两例），故取第 2。实跑读数 tune 97.2→97.3，其余三套不变。
  - 第9法「散事死墓绝日」：散事域未进本学科门类（见 OPT-zengshan_buyi_dz-08
    「登记不动」同类处置），故不排。
  - 《黄金策》源L265「速则动而克世，缓则静而生身」：属**迟速速调**而非定应期日，现 speed 标签
    粒度较粗；补则改 output speed 字段，须同上走门槛。
  三项均属「新增判定」而非「补注记」，按本轮范围（补对源/补注记类，
  不改判定值）只登记不实施，见两 doc 的 OPT 行状态说明。
"""
from __future__ import annotations

import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)

from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    ADVANCE_PAIRS,
    BRANCH_ELEMENTS,
    CHONG_PAIRS,
    EARTHLY_BRANCHES,
    HE_PAIRS,
    KE_CYCLE,
    RETREAT_PAIRS,
    SAN_HE_GROUPS,
    SHENG_CYCLE,
    TOMB_MAP,
    chu_xun_branch,
)
from narrative_utils import safe_get  # noqa: E402
from narrative_utils import STEP5_YINGQI as YINGQI_TXT  # noqa: E402

import json as _json  # noqa: E402
from pathlib import Path as _P  # noqa: E402
from datetime import datetime  # noqa: E402
import re  # noqa: E402

_YD = _json.loads((_P(__file__).resolve().parents[1] / 'data' / 'narrative_templates.json').read_text(encoding='utf-8')).get('yingqi_descriptions', {})

# 原闭包内本地常量；提升为模块常量供 _push / _rank 复用。
# 地支序列唯一真值源在 core（此前是第二份手写串）
BRANCH_ORDER = EARTHLY_BRANCHES


# ────────────────────────────────────────────────────────────────
# 应期窗口工具（原 yingqi_windows.py）
# ────────────────────────────────────────────────────────────────

REL_RULES = [
    # (关键词, 天数窗下限, 上限, 标签)
    (("当日", "当天"), 0, 0, "当日"),
    (("次日",), 1, 1, "次日"),
    (("月余", "旺相之月"), 20, 50, "月余窗"),
    (("年内", "经年"), 1, 365, "年内窗"),
]


def resolve_case_anchor(exp_input: dict, case: dict) -> datetime | None:
    """从案例 input.date / 顶层 year-month-day 解析锚日。"""
    y = case.get("year")
    m = case.get("month")
    d = case.get("day")
    if y and m and d:
        try:
            return datetime(int(y), int(m), int(d))
        except ValueError:
            return None
    text = str((exp_input or {}).get("date") or "")
    # 尽力抽公历 YYYY-M-D
    m2 = re.search(r"(20\d{2})-(\d{1,2})-(\d{1,2})", text)
    if m2:
        try:
            return datetime(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)))
        except ValueError:
            return None
    return None


def relative_window(x_yq: str) -> tuple[int, int, str] | None:
    for keys, lo, hi, label in REL_RULES:
        if any(k in x_yq for k in keys):
            return lo, hi, label
    return None


def date_in_window(anchor: datetime, date_str: str, lo: int, hi: int) -> bool:
    try:
        dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
    except ValueError:
        return False
    delta = (dt - anchor).days
    return lo <= delta <= hi


# ────────────────────────────────────────────────────────────────
# 原闭包内 5 个辅助：提升为模块级纯函数（不再捕获外层作用域）。
# ────────────────────────────────────────────────────────────────

def _pair_partner(pairs, b: str) -> str:
    """配对表是单向列出的（每对只写一次），必须双向查。"""
    for a, c in pairs:
        if b == a:
            return c
        if b == c:
            return a
    return ""


def _chong(b: str) -> str:
    return _pair_partner(CHONG_PAIRS, b)


def _he(b: str) -> str:
    return _pair_partner(HE_PAIRS, b)


def _push(key_branches: list, b: str, suffix: str = "日") -> None:
    if not b or b not in BRANCH_ORDER:
        return
    token = f"{b}{suffix}"
    if token not in key_branches:
        key_branches.append(token)


def _rank(ranked: list, b: str, rule: str, suffix: str = "日") -> None:
    if not b or b not in BRANCH_ORDER:
        return
    token = f"{b}{suffix}"
    if token not in [t for t, _ in ranked]:
        ranked.append((token, rule))


# ────────────────────────────────────────────────────────────────
# 职责一：收集候选地支（原 103–247 收集段）
# ────────────────────────────────────────────────────────────────

def _collect_key_branches(r: dict, use_god_branch: str, day_branch: str):
    """遍历卦爻/日月/用神/伏神/旬空，按规则把应期候选支推入 key_branches。

    返回 (key_branches, month_branch, step2_d, pd)：
      - key_branches 是会被下游「法则应期」段继续追加的可变列表；
      - month_branch / step2_d / pd 是收集段顺手算出的派生量，下游排序与组装都要用。
    """
    key_branches: list[str] = []

    # 收集卦中地支
    yao_lines = ((r.get("original_hexagram") or {}).get("yao_lines")) or []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if y.get("is_moving"):
            _push(key_branches, br)
            chg = y.get("changed_earthly_branch") or y.get("changed_branch") or ""
            if not chg:
                # 尝试从 changed_hexagram 对应位取
                pass
            if chg:
                _push(key_branches, chg)
        if y.get("six_relation") and use_god_branch and br == use_god_branch:
            _push(key_branches, br)

    # 变卦地支
    ch_hex = r.get("changed_hexagram") or {}
    for y in (ch_hex.get("yao_lines") or []):
        if isinstance(y, dict) and y.get("is_moving"):
            _push(key_branches, y.get("earthly_branch") or "")
        # 动爻变出支通常在 original 的 moving 标记里，双保险
        if isinstance(y, dict) and y.get("changed_earthly_branch"):
            _push(key_branches, y.get("changed_earthly_branch"))

    # 原始动爻若带 changed_branch 字段
    for y in yao_lines:
        if isinstance(y, dict):
            for k in ("changed_earthly_branch", "changed_branch", "transform_branch"):
                if y.get(k):
                    _push(key_branches, y.get(k))

    # 日月
    if day_branch:
        _push(key_branches, day_branch)
    month_branch = ""
    mdt = r.get("divination_time") or {}
    if isinstance(mdt, dict):
        msb = mdt.get("month_stem_branch") or mdt.get("month_branch") or ""
        month_branch = msb[-1] if msb else ""
        if month_branch:
            _push(key_branches, month_branch, "月")

    # 用神及其冲合
    if use_god_branch:
        _push(key_branches, use_god_branch)
        _push(key_branches, _chong(use_god_branch))
        _push(key_branches, _he(use_god_branch))

    # 原神旺日
    step2_d = safe_get(r, "_step2_data", default={}) or {}
    yuan_elem = (step2_d.get("yuan_shen") or {}).get("element", "")
    peak_days = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}
    pd = peak_days.get(yuan_elem, "")
    for ch in pd:
        _push(key_branches, ch)
    for pos in ((step2_d.get("yuan_shen") or {}).get("positions") or []):
        if isinstance(pos, dict):
            _push(key_branches, pos.get("earthly_branch") or "")

    # 伏神地支
    fu = step2_d.get("fu_cang_detail") or {}
    if isinstance(fu, dict):
        for res in fu.get("results") or []:
            if isinstance(res, dict):
                _push(key_branches, ((res.get("fu_shen") or {}).get("branch")) or "")
                _push(key_branches, ((res.get("fei_shen") or {}).get("branch")) or "")

    # 旬空地支（出空应期）
    for e in (r.get("empty_branches") or []):
        _push(key_branches, e)

    # 合局/贪合 → 冲开之支（冲开合局方应）
    # （原 step4_all 本地变量已废弃：从未被读取，删除不影响任何输出）
    # 冲用神、合用神之支
    if use_god_branch:
        _push(key_branches, _chong(use_god_branch))
        _push(key_branches, _he(use_god_branch))
    # 卦中地支：动爻候合、静爻候冲；并冲开六合之支
    he_branches = []
    for y in yao_lines:
        if not isinstance(y, dict):
            continue
        br = y.get("earthly_branch") or ""
        if not br:
            continue
        if y.get("is_moving"):
            _push(key_branches, _he(br))
            _push(key_branches, _chong(br))
        else:
            _push(key_branches, _chong(br))
        for a, b in HE_PAIRS:
            if br == a:
                he_branches.append(b)
            elif br == b:
                he_branches.append(a)
    for hb in he_branches:
        _push(key_branches, _chong(hb))  # 冲开合局
        _push(key_branches, hb)
    # 日月与卦爻成合：冲开该合
    if day_branch:
        for a, b in HE_PAIRS:
            if day_branch == a:
                _push(key_branches, _chong(b)); _push(key_branches, b)
            elif day_branch == b:
                _push(key_branches, _chong(a)); _push(key_branches, a)
    if month_branch:
        for a, b in HE_PAIRS:
            if month_branch == a:
                _push(key_branches, _chong(b)); _push(key_branches, b)
            elif month_branch == b:
                _push(key_branches, _chong(a)); _push(key_branches, a)
    # 伏神得出：伏支值日 + 冲飞之日
    fu_d = safe_get(r, "_step2_data", default={}) or {}
    fu_detail = fu_d.get("fu_cang_detail") or {}
    if isinstance(fu_detail, dict):
        for res in fu_detail.get("results") or []:
            if not isinstance(res, dict):
                continue
            fu_br = ((res.get("fu_shen") or {}).get("branch")) or ""
            fei_br = ((res.get("fei_shen") or {}).get("branch")) or ""
            if fu_br:
                _push(key_branches, fu_br)
            if fei_br:
                _push(key_branches, _chong(fei_br))
    # 用神临月建：该五行旺月/日
    if use_god_branch and month_branch:
        if use_god_branch == month_branch or (
            BRANCH_ELEMENTS.get(use_god_branch) == BRANCH_ELEMENTS.get(month_branch)
        ):
            elem = BRANCH_ELEMENTS.get(use_god_branch, "")
            peak = {"木": "寅卯", "火": "巳午", "土": "辰戌丑未", "金": "申酉", "水": "亥子"}.get(elem, "")
            for ch in peak:
                _push(key_branches, ch)
    # 原神旺月支
    if pd:
        for ch in pd:
            _push(key_branches, ch)
    # 世爻之冲（世应应期）
    for y in yao_lines:
        if isinstance(y, dict) and y.get("is_world"):
            _push(key_branches, _chong(y.get("earthly_branch") or ""))
            break

    return key_branches, month_branch, step2_d, pd


# ────────────────────────────────────────────────────────────────
# 职责二：组装「法则应期」方法与速迟基调（原 249–342 段）
# ────────────────────────────────────────────────────────────────

def _build_timing_methods(r: dict, step3_data: dict, use_god_branch: str, use_god_element: str,
                          strength_level: str, is_empty, is_month_break,
                          day_branch: str, step2_d: dict, step4_data: dict,
                          key_branches: list, pd: str):
    """按旺衰/空亡/月破/暗动/伏藏等通则生成 timing_methods，并定 speed 基调。

    注意：本段仍会向 key_branches 追加支（逢冲之支、空亡支、贪合冲日支），
    须在执行完本段之后、排序之前再对 key_branches 做 candidates_all 快照。
    """
    timing_methods = []

    # 旺衰规则
    if strength_level in ("极旺", "旺"):
        timing_methods.append({
            "method": "逢值",
            "description": _YD["value_day"].format(use_god_branch=use_god_branch),
            "type": "速应",
        })
        cb = _chong(use_god_branch)
        if cb:
            timing_methods.append({
                "method": "逢冲",
                "description": _YD["clash_day"].format(use_god_branch=use_god_branch, cb=cb),
                "type": "速应",
            })
            _push(key_branches, cb)
    elif strength_level in ("偏弱", "弱", "极弱"):
        element_peak_months = {
            "木": "寅卯月（春）",
            "火": "巳午月（夏）",
            "土": "辰戌丑未月（季月）",
            "金": "申酉月（秋）",
            "水": "亥子月（冬）",
        }
        peak = element_peak_months.get(use_god_element, "")
        timing_methods.append({
            "method": "待旺时",
            "description": _YD["peak_month"].format(use_god_branch=use_god_branch, peak=peak),
            "type": "迟应",
        })
        timing_methods.append({
            "method": "逢生",
            "description": (_YD["yuan_peak"].format(pd0=pd[0] if pd else "", pd1=pd[1] if len(pd) > 1 else "") if pd else _YD["yuan_peak_short"]),
            "type": "迟应",
        })
    else:
        if use_god_branch:
            timing_methods.append({
                "method": "中和取用",
                "description": _YD["neutral"].format(use_god_branch=use_god_branch),
                "type": "适中",
            })

    if is_empty:
        timing_methods.append({
            "method": "出空",
            "description": _YD["out_void"].format(use_god_branch=use_god_branch),
            "type": "空亡应期",
        })
        # 常见出空应期支：待用神值日或填实之支
        if use_god_branch:
            _push(key_branches, use_god_branch)
        for e in (r.get("empty_branches") or []):
            _push(key_branches, e)

    if is_month_break:
        timing_methods.append({
            "method": "填实",
            "description": _YD["month_break"].format(use_god_branch=use_god_branch),
            "type": "填实应期",
        })

    if step4_data.get("tan_he_wan_sheng_ke"):
        timing_methods.append({
            "method": "冲合",
            "description": _YD["he_clash"],
            "type": "化合应期",
        })
        if day_branch:
            _push(key_branches, _chong(day_branch))

    # 暗动：应在冲动之日
    if (step3_data.get("an_dong_modifier") or 1.0) < 1.0 and day_branch:
        timing_methods.append({
            "method": "暗动应期",
            "description": _YD["an_dong"].format(day_branch=day_branch),
            "type": "暗动",
        })

    # 伏藏：飞神冲去或伏神值日
    if step2_d.get("has_fu_cang") or step2_d.get("fu_cang_detail"):
        timing_methods.append({
            "method": "伏神应期",
            "description": _YD["fu_hidden"],
            "type": "伏藏应期",
        })

    if strength_level in ("极旺", "旺"):
        speed = "应速"
    elif strength_level in ("中和",):
        speed = "应期适中"
    else:
        speed = "应迟"

    return timing_methods, speed


# ────────────────────────────────────────────────────────────────
# 职责三：应期择优排序（原 344–491 段）
# ────────────────────────────────────────────────────────────────

def _rank_candidates(r: dict, use_god_branch: str, use_god_element: str, strength_level: str,
                     is_empty, is_month_break, day_branch: str, month_branch: str,
                     step2_d: dict, speed: str) -> list:
    """法则驱动的主/次应期排序：日/月/年分列、各自封顶（避免单位互相饿死）。"""
    ranked: list[tuple[str, str]] = []

    yao_lines = ((r.get("original_hexagram") or {}).get("yao_lines")) or []
    ug_moving = any(isinstance(y, dict) and y.get("earthly_branch") == use_god_branch
                    and y.get("is_moving") for y in yao_lines)
    changed_pairs = [(y.get("earthly_branch") or "",
                      y.get("changed_earthly_branch") or y.get("changed_branch") or "")
                     for y in yao_lines
                     if isinstance(y, dict) and y.get("is_moving")]
    changed_pairs = [(b, c) for b, c in changed_pairs if c]
    # 动而化回头生：古籍以"生我之日"为应，且此则先于旬空——动爻得生则不作空论
    hui_tou_sheng = [c for b, c in changed_pairs
                     if SHENG_CYCLE.get(BRANCH_ELEMENTS.get(c, "")) == use_god_element]
    fu_detail = step2_d.get("fu_cang_detail") or {}
    fu_res = (fu_detail.get("results") or [{}])[0] if isinstance(fu_detail, dict) else {}
    fu_shen = fu_res.get("fu_shen") or {}
    fei_shen = fu_res.get("fei_shen") or {}
    fu_branch = fu_shen.get("branch") or ""
    fei_branch = fei_shen.get("branch") or ""
    # 飞/伏五行读结构值（缺陷 B 修复，2026-10-09）：旧代码对
    # `str(fu_cang_detail)+str(fu_cang_summary)` 做子串嗅探判「飞克伏/伏生飞」，
    # 而 fu_cang_summary 全仓无生产者、fu_cang_detail 的 repr 只有 element/
    # six_relation 等英文键——两支恒不成立，伏藏应期永远落通用「伏神值日」。
    # 现用内核 KE_CYCLE/SHENG_CYCLE 直接比较飞伏五行（出处：《增删卜易·飞伏神章》
    # 源L1055「伏神得遇日月动爻冲克飞神者五也」、源L1535「飞不冲开亦枉然…
    # 须宜月建日辰冲开飞神」；《卜筮正宗》源L433「土克水谓之飞来克伏」）。
    fu_elem = fu_shen.get("element") or BRANCH_ELEMENTS.get(fu_branch, "")
    fei_elem = fei_shen.get("element") or BRANCH_ELEMENTS.get(fei_branch, "")
    tomb_branch = TOMB_MAP.get(use_god_element or "", "")
    bound_by = day_branch if _he(use_god_branch) == day_branch else \
               (month_branch if _he(use_god_branch) == month_branch else "")
    PEAK_BRANCH = {"木": "寅", "火": "巳", "土": "辰", "金": "申", "水": "亥"}

    # ── 病药解除优先（《增删卜易》空则实之、破则补之、墓则冲之）──
    _empty_list = list(r.get("empty_branches") or [])
    _chong_ug = _chong(use_god_branch)
    # 问事归类读取用神层（step2）产出的结构枚举 question_class（缺陷 D 修复，
    # 2026-10-09）：旧代码用 "病/疾/半年/久病" 子串嗅探自由文本，改写措辞/换简繁
    # 即静默变向；question_class 由 data/rules/question_classes.json 映射表经
    # normalize_question_text 归一后单点产出（关键词族逐字继承旧表，判类属启发式）。
    _qclass = str(step2_d.get("question_class") or "")
    _is_illness_q = _qclass in ("疾病·近病", "疾病·久病")
    _is_chronic = _qclass == "疾病·久病"
    # 取哪一条化出之支：旧写法 `changed_pairs[0][1]` 是按爻位顺序拿第一条动爻的化支，
    # 与书上口径无关。《增删卜易》源L3322「应亥月者父母化出之爻也」指的是**用神自身**
    # 所化之支，故优先取用神动爻的化出支；用神不动时才退回原顺序第一条。
    # 【灰区·如实记】同书并非一律取化出支：源L3008「内卦寅木父母旺而化出子水之官，
    # 许寅年仍以原品起用」答的是**本爻值年**；源L1353「寅木一爻独发，化出丑父」「寅木一爻独发，化出丑父，
    # 乃应正月得见父灵」答的又是化出之父。本条只做"选哪一条化出支"的修正，
    # 不据此断言化出支一定优于本爻值——那需要按门类再分。
    _chg_ug = next((c for (b0, c) in changed_pairs
                    if b0 == use_god_branch and c), "")
    _chg0 = _chg_ug or (changed_pairs[0][1] if changed_pairs else "")
    # 化空 / 回头生优先；动而化回头生则不作空论（ZS005/007/013）
    for _b, _c in changed_pairs:
        if _c and _c in _empty_list:
            _rank(ranked, _c, YINGQI_TXT["change_branch_empty_fill"]["text"])
    if hui_tou_sheng and is_empty:
        _rank(ranked, hui_tou_sheng[0], YINGQI_TXT["change_hui_tou_sheng_empty"]["text"])
    elif hui_tou_sheng:
        pass  # 回头生的化出支在下面"其余化出之支"那一档排（《增删卜易》源L1361「此世化申金回头生，
              # 亦应申月」）——此前该处被 `not hui_tou_sheng` 挡死，这句注释是假的
    if is_empty and not hui_tou_sheng:
        if day_branch and day_branch == _chong_ug:
            _rank(ranked, day_branch, YINGQI_TXT["use_empty_day_chong"]["text"])
        elif _is_chronic and _chong_ug:
            # 久病逢空多应冲空之日（《增删卜易》久病之忌）
            _rank(ranked, _chong_ug, YINGQI_TXT["chronic_empty_wait_chong"]["text"])
            _rank(ranked, use_god_branch, YINGQI_TXT["empty_fill"]["text"])
        elif _is_illness_q:
            # 近病逢空即愈：出空填实为应
            _rank(ranked, use_god_branch, YINGQI_TXT["acute_empty_fill"]["text"])
            _rank(ranked, _chong_ug or use_god_branch, "冲空则实")
        else:
            _rank(ranked, use_god_branch, YINGQI_TXT["empty_fill"]["text"])
            _rank(ranked, _chong_ug or use_god_branch, YINGQI_TXT["empty_chong_real"]["text"])
        # ── 出旬之日（此前整个池子都没有这一支）──
        # 《增删卜易·各门类应期总注章》源L964「旬空最爱填冲」只给填/冲两条落点，
        # 《卜筮正宗·旬空论第十》源L1066 另补一条：「此等旬空到底有用，不过待其出旬」，
        # 《增删卜易》源L643「待至出空之日则不空也」、源L894「卦吉者许之出旬」同此口径。
        # 本块只在**用神旬空**时触发，所以可比案例不是「基准应支落在
        # 旬空两支之内」的 12 例，而是其中**用神恰为空支**的 4 例：
        #   ZS017（壬辰日空午未，用神午=出旬支）——池内已有，下面的去重会跳过；
        #   ZS006（癸丑日空寅卯，用神卯）——书上答「次日出空」（源L1573「又因卯木财空，
        #     次日出空而退灾」），癸丑是甲辰旬末日、次晨即出旬日甲寅，新候选唯一能赢的一例；
        #   ZS002（酉）/ZS004（亥）——书上写的就是值空支填实，提到第 1 会反伤它们。
        # 故取第 2 位。旧实现在此只排了 `empty_fill`（值空支**填实**）却把它标成
        # 「出旬填实」，名实不符；出旬日本身从未进池
        # （本文件开头缺口处置清单早就登记过：「全局过旬口径缺失」）。
        _dgz = str(safe_get(r, "divination_time", "day_stem_branch", default="") or "")
        _cx = chu_xun_branch(_dgz)
        # ranked 里存的是**带单位的 token**（"寅日"），比较与定位都必须用同一口径；
        # 拿裸支去比会得到恒不相等 + next() 抛 StopIteration，把整例打挂在评测之外。
        _tok = f"{_cx}日"
        if _cx and all(_tok != t for t, _ in ranked):
            _rank(ranked, _cx, YINGQI_TXT["chu_xun_day"]["text"])
            _i = next((i for i, (t, _) in enumerate(ranked) if t == _tok), None)
            if _i is not None and _i > 1:
                # 值空支（填实）之后、泛化候选（原神旺日/比和日等）之前
                ranked.insert(1, ranked.pop(_i))
    if is_month_break:
        _rank(ranked, use_god_branch, YINGQI_TXT["month_break_fill"]["text"])
        _rank(ranked, _he(use_god_branch), YINGQI_TXT["month_break_he"]["text"])
    # 化空出空 / 回头生：先于合住冲开与伏藏（ZS005/007/013）
    if step2_d.get("has_fu_cang") and (fu_branch or fei_branch):
        fei_empty = fei_branch in _empty_list if fei_branch else False
        # 飞伏生克判据＝五行结构比较（缺陷 B 修复；旧文本嗅探两支恒假，见上文注记）
        _fei_ke_fu = bool(fei_elem and fu_elem and KE_CYCLE.get(fei_elem) == fu_elem)
        _fu_sheng_fei = bool(fu_elem and fei_elem and SHENG_CYCLE.get(fu_elem) == fei_elem)
        if _fei_ke_fu and fei_branch:
            _rank(ranked, _chong(fei_branch) or fu_branch, YINGQI_TXT["fu_fei_ke_chong_fei"]["text"])
            if fu_branch:
                _rank(ranked, fu_branch, "伏神值日")
        elif fei_empty and fu_branch:
            _rank(ranked, fu_branch, YINGQI_TXT["fu_fei_empty_wait_fu_day"]["text"])
        elif fu_branch:
            _rank(ranked, fu_branch, YINGQI_TXT["fu_out_wait_fu_day"]["text"])
            if fei_branch and _fu_sheng_fei:
                _rank(ranked, _chong(fei_branch) or fei_branch, YINGQI_TXT["fu_sheng_fei_chong"]["text"])
            elif fei_branch:
                _rank(ranked, _chong(fei_branch) or fu_branch, "冲飞神得出")
        if fu_branch and fu_branch != use_god_branch:
            _rank(ranked, fu_branch, "伏神值日")
    if tomb_branch and tomb_branch in (day_branch, month_branch):
        _rank(ranked, _chong(tomb_branch), YINGQI_TXT["use_tomb_chong_tomb"]["text"])
    if bound_by:
        _rank(ranked, _chong(bound_by), f"用神被{bound_by}合住，冲开之日")
    # ── 期日第4法：太旺者逢墓库收藏（九法之四，逐字书据见下面三行）──
    # 主语是**月建与日辰同支、卦中（本爻或化出）再见**之"重叠之爻"，不是用神。
    # 《黄金策》源L264 逐字「用爻得时旺动，又遇生扶，此为太旺，应以墓库月日断」；
    # 全要素真例《增删卜易》源L1673 逐字「如午月戊午日占何日雨得地风升变恒卦」
    # 合断语《增删卜易》源L1680 逐字「午火子孙临日月旺之极矣，乃为用爻重叠，
    # 逢墓库以收藏，故知戌必雨」——此例用神是父母亥水，书取的墓库属火（化出午火→戌），
    # 故谓词挂在重叠之爻上；第六十八批挂在用神上，实测不动任何一例而只晃外部集。
    # 避让两条：重叠支＝用神支时不排（用神太旺入墓于书无据，且与第6法「入墓→冲墓」相抵）；
    # 重叠支旬空时不排（空则不作旺之极论，另由出空填实一支接手）。
    _die = sorted({b for b in ({(y.get("earthly_branch") or "") for y in yao_lines
                                if isinstance(y, dict)}
                               | {c for _b0, c in changed_pairs})
                   if b and b == day_branch == month_branch
                   and b != use_god_branch and b not in _empty_list})
    for _db in _die:
        _tomb_die = TOMB_MAP.get(BRANCH_ELEMENTS.get(_db, ""), "")
        if _tomb_die:
            _rank(ranked, _tomb_die, YINGQI_TXT["overlap_taiwang_tomb_day"]["text"])
    # ── 期日第3法：用爻受制，以制杀月日断（九法之三，第一百五十六批补）──
    # 书据：《黄金策》源L264 夹注逐字「用爻受制，以制杀月日断」；
    # 《增删卜易》源L594 逐字「忌神者以克少生多为凶，所以忌神宜克不宜生也」；
    # 《增删卜易》源L643 逐字「爻值月建乃为旺矣，或被他爻所克，即谓之逢伤，占病者
    # 目下不愈，占事者目下不成，待至冲去伤爻之日则不受其伤矣，病者必愈、事必成。
    # 故曰：逢伤亦伤却有待时之用」。
    # 谓词分两支，各有书例与实测反例（**不含日月克用神**——日辰司权场景另论）：
    #  ① 回头克＋用神临月建＝源L643「爻值月建乃为旺矣，或被他爻所克」的原文形。
    #    真例 ZD015 蛊之蒙：世官鬼酉临月建，动化午火回头克，书「须待子日冲去午火
    #    方得拜谒，果得见于丙子日」——断语末句「故曰：逢伤亦伤却有待时之用」即源L643 原句。
    #    反例（广义形实测会打掉，故加临月建门）：HO008 鼎之既济（用神亥动化丑回头克，
    #    不临月建，书答亥日＝用神值日）、WS018 小畜之蛊（用神子动化丑，书答子日）。
    #  ② 动爻本支克用神＋用神静＋该动爻化进神（忌神得势而进）。
    #    真例 ZD160 归妹之兑（申金动化进神克卯木财，书「待寅月冲去申金，其价必涨…
    #    此乃财爻被克待冲去克神之月」）、ZD125 益之睽（寅木临月建化进神克辰土世，
    #    书「六七月衰墓之时」应申月——申冲寅，亦木之绝月，两读同支）。
    #    反例（三道门各挡一批，全部实测）：动用神不触发——HO008/WS017 比之咸/WS018
    #    （三例用神均动，书答都是用神值日）；不化进不触发——WS023 既济之革（申动化亥，
    #    书答实破卯日）、ZD102 临之蒙（巳动化寅，书答辰父发动值日）、ZD065 恒之升
    #    （午动化丑，书答午月＝忌神值月而非制杀，已连同测量登记 CHANGELOG）。
    # 候选＝冲克神之支（制杀）。日级置于病药块内、用神值日之前（与空/破/墓/合同级
    # 「病药解除优先」）；月级对称置于月阶梯用神值月之前。
    # 注：G6a（日级末位「化出X克用，冲去之支」）与本条同源，保留不动——本条前置后
    # 同名 token 由 _rank 去重，G6a 只在更早的则都不触发时补位。
    _ke_shen: list[str] = []
    _ug_lin_yue = bool(use_god_branch) and use_god_branch == month_branch
    if _ug_lin_yue:
        for _b, _c in changed_pairs:
            if _b == use_god_branch and _c and KE_CYCLE.get(BRANCH_ELEMENTS.get(_c, "")) == use_god_element:
                _ke_shen.append(_c)                    # ① 回头克（逢伤形）
    if use_god_branch and not ug_moving:
        for _y in yao_lines:
            if isinstance(_y, dict) and _y.get("is_moving"):
                _b0 = _y.get("earthly_branch") or ""
                _c0 = _y.get("changed_earthly_branch") or _y.get("changed_branch") or ""
                if (_b0 and _b0 != use_god_branch
                        and KE_CYCLE.get(BRANCH_ELEMENTS.get(_b0, "")) == use_god_element
                        and _c0 and ADVANCE_PAIRS.get(_b0) == _c0):
                    _ke_shen.append(_b0)               # ② 动爻本支克（化进形）
    #  ③ 动爻本支克用神＋用神静＋动爻化退神（第两百八十五批补，与②对称的退形）。
    #    书据：《增删卜易》源L1174 逐字「戌土子孙孙虽动幸化退神，不克官也，辰年冲去
    #    戌土，是以许之，果于辰年得选岂可谓之动空化日月而不退也」（WS004 占功名，
    #    用神官鬼亥静，忌神戌动化未退神——化退已减其克，冲去忌神之年彻底除患）；
    #    同书源L2050「子孙爻动化回头克，或被动爻克，须待冲去克神之日始晴」、
    #    源L2058「应丑日者，冲去未土合起父母」（占天时同构实案）。
    #    准入门：用神必须静（动用神书答值日，HO008/WS017/WS018 实测反例同②）；
    #    须化退（WS023 申动化亥书答实破、ZD065 午动化丑书答忌神值月，均非退形）；
    #    用神发动的不触发（ZD102 巳动化寅退神，书答辰父**发动**值日，由 ug_moving
    #    门挡下）。
    if use_god_branch and not ug_moving:
        for _y in yao_lines:
            if isinstance(_y, dict) and _y.get("is_moving"):
                _b0 = _y.get("earthly_branch") or ""
                _c0 = _y.get("changed_earthly_branch") or _y.get("changed_branch") or ""
                if (_b0 and _b0 != use_god_branch
                        and KE_CYCLE.get(BRANCH_ELEMENTS.get(_b0, "")) == use_god_element
                        and _c0 and RETREAT_PAIRS.get(_b0) == _c0):
                    _ke_shen.append(_b0)               # ③ 动忌化退克用（冲去忌神）
                # ④ 忌神动化回头生（得源）克用＋用神静→冲去化出之源（第两百八十六批）。
                #    书据：《增删卜易》源L2570 逐字「果终于本年冬至日，应子日者冲去午火
                #    而未土以克亥水」（WS035 占父寿，忌神未土动化午火回头生——冲去生
                #    忌之源则忌失其生）；同书源L1206「至丑月土旺…且化退神，正以绝其源，
                #    源绝危险」反证「源」于应期的分量（源绝则事败，源旺则待除）。
                elif (_b0 and _b0 != use_god_branch
                        and KE_CYCLE.get(BRANCH_ELEMENTS.get(_b0, "")) == use_god_element
                        and _c0 and SHENG_CYCLE.get(BRANCH_ELEMENTS.get(_c0, "")) == BRANCH_ELEMENTS.get(_b0, "")):
                    _ke_shen.append(_c0)               # ④ 动忌化回头生得源（冲去生源）
    # ⑤ 通用主支：动忌克用＋用神静＋用神月令旺相（有根）→冲去忌神本支（第两百一十五批补）。
    #    书据：《增删卜易》源L3099 应期总纲逐字「被克者冲去克神之秋」；
    #    源L3107 实案逐字「此乃财爻被克待冲去克神之月」（ZD160 同案，前文「财有根蒂」）；
    #    源L651 逐字「须待子日冲去午火方得拜谒」（回头克形）；源L1140 逐字「必待午日冲去子水」。
    #    准入门：用神静（同②③④）；月令旺相=有根（L3107「财有根蒂」；L780 用神失陷虽冲
    #    不破反证失陷者不在此轨；WS023 用神月破不触发）；本支为任意动忌（化进/退/生/克
    #    皆可）的兜底，与①—④经 dict.fromkeys 去重后并入。
    if use_god_branch and not ug_moving and strength_level in ("极旺", "旺", "相"):
        for _y in yao_lines:
            if isinstance(_y, dict) and _y.get("is_moving"):
                _b0 = _y.get("earthly_branch") or ""
                if (_b0 and _b0 != use_god_branch
                        and KE_CYCLE.get(BRANCH_ELEMENTS.get(_b0, "")) == use_god_element):
                    _ke_shen.append(_b0)               # ⑤ 动忌克用（通用主支，冲去忌神）
    for _ks in dict.fromkeys(_ke_shen):
        _zs = _chong(_ks)
        if _zs:
            _rank(ranked, _zs, YINGQI_TXT["use_god_restrained_zhi_sha_day"]["text"].format(ks=_ks))
    # 用神不空时，本气值日优先于其他空亡出空
    if use_god_branch and not is_empty:
        if ug_moving:
            _rank(ranked, use_god_branch, "发动值日")
            _rank(ranked, _he(use_god_branch), YINGQI_TXT["use_moving_he_day"]["text"])
        else:
            _rank(ranked, use_god_branch, "用神值日")
            _rank(ranked, _chong_ug, YINGQI_TXT["use_quiet_chong_day"]["text"])
    # 其余化出之支
    if changed_pairs and _chg0 and _chg0 not in _empty_list:
        _rank(ranked, _chg0,
              YINGQI_TXT["hui_tou_sheng_change_branch"]["text"] if hui_tou_sheng
              else "化出之支值日")
    # 同五行之空亡支
    ug_el = use_god_element or ""
    for e in _empty_list:
        if e and e != use_god_branch and ug_el and BRANCH_ELEMENTS.get(e) == ug_el:
            _rank(ranked, e, YINGQI_TXT["empty_same_element_fill"]["text"])
    for e in _empty_list:
        if e and e != use_god_branch:
            _rank(ranked, e, "空亡之支出空填实")
    if use_god_branch and is_empty:
        _rank(ranked, use_god_branch, "以用神为主")
    if strength_level in ("休囚", "囚", "死", "偏弱", "衰") or speed == "应迟":
        _rank(ranked, PEAK_BRANCH.get(use_god_element or "", ""), YINGQI_TXT["use_weak_wait_prosper"]["text"])
    # 独发之爻值日：《增删卜易·应期总注》源L958「动而逢合逢值：如主事爻临子水发动，
    # 后遇丑日子日而应之」＋《易冒》独发章源L438「然后以独发独静之爻定其时，则每有验」、
    # 源L439「独发独静可以定时日」。只在**仅一爻动**（独发，主事爻可机械判定）且该爻
    # 不是用神时补这一支；多爻动时「主事爻」无法机械认定，宁缺不铺。
    _moving_b = [y.get("earthly_branch") for y in yao_lines
                 if isinstance(y, dict) and y.get("is_moving") and y.get("earthly_branch")]
    if len(_moving_b) == 1 and _moving_b[0] != use_god_branch:
        _rank(ranked, _moving_b[0], YINGQI_TXT["dufa_value_day"]["text"])
    _rank(ranked, use_god_branch, "以用神为主")
    _rank(ranked, day_branch, "日辰值事")
    # ── 日级末位补充（追加于既有序列之后，只补空槽不挤既有候选）──
    # G4 世爻发动逢合：《增删卜易》「應辰日者，世動逢合之日也」；天时章
    # 「動者逢值逢合之日」——用神动逢合已有，世爻动亦同此理；
    # 世持用神时与用神动规则同 token，由 _rank 去重。
    _world_yao = next((y for y in yao_lines
                       if isinstance(y, dict) and y.get("is_world")), None)
    if _world_yao is not None and _world_yao.get("is_moving"):
        _wb = _world_yao.get("earthly_branch") or ""
        if _wb:
            _rank(ranked, _he(_wb), "世爻发动，逢合之日（世動逢合）")
    # G6a 化出之支回头克用神，冲去该支：《增删卜易》天时章「父母子水動被未土回頭克，
    # 丑日而雨。應丑日者，沖去未土合起父母」＋觉子按语「合住爻沖開之日時必晴」。
    for _b, _c in changed_pairs:
        _c_el = BRANCH_ELEMENTS.get(_c or "", "")
        if _c_el and use_god_element and KE_CYCLE.get(_c_el) == use_god_element:
            _rank(ranked, _chong(_c), f"化出{_c}克用，冲去之支（冲去{_c}）")

    # 月级阶梯：《增刪卜易》「遠則應月﹐近則應日」（norm@79289）——同一套"解除障碍之期"
    # 在月单位上另排一遍。
    peak = PEAK_BRANCH.get(use_god_element or "", "")
    # 化空之月：日级 change_branch_empty_fill（病药块之首）的月级对称，同置月阶梯之首。
    # 真例 ZD151 颐之噬嗑：世妻财戌动化官鬼酉，酉值旬空，书「世化官空，八九月必见，
    # 果于八月丁艰」＝酉月——日级早有「酉日」（排日池第 1），月级却因 G2 的
    # `_chg0 not in _empty_list` 守卫一支俱无，书答月级候选池里找不到酉。
    for _b, _c in changed_pairs:
        if _c and _c in _empty_list:
            _rank(ranked, _c, YINGQI_TXT["change_branch_empty_fill_month"]["text"], "月")
    if is_empty:
        _rank(ranked, use_god_branch, YINGQI_TXT["use_empty_fill_month"]["text"], "月")
        _rank(ranked, _chong(use_god_branch) or use_god_branch, YINGQI_TXT["use_empty_chong_month"]["text"], "月")
    if is_month_break:
        _rank(ranked, use_god_branch, YINGQI_TXT["month_break_real_month"]["text"], "月")
    if tomb_branch and tomb_branch in (day_branch, month_branch):
        _rank(ranked, _chong(tomb_branch), YINGQI_TXT["use_tomb_chong_month"]["text"], "月")
    if bound_by:
        _rank(ranked, _chong(bound_by), f"用神被{bound_by}合住，冲开之月", "月")
    if step2_d.get("has_fu_cang") and (fu_branch or fei_branch):
        _rank(ranked, _chong(fei_branch) or fu_branch, YINGQI_TXT["fu_hidden_chong_fei_month"]["text"], "月")
    for _db in _die:
        _tomb_die = TOMB_MAP.get(BRANCH_ELEMENTS.get(_db, ""), "")
        if _tomb_die:
            _rank(ranked, _tomb_die, YINGQI_TXT["overlap_taiwang_tomb_month"]["text"], "月")
    # 期日第3法（月级）：与日级同谓词、同候选（冲克神之支），置于用神值月之前。
    for _ks in dict.fromkeys(_ke_shen):
        _zs = _chong(_ks)
        if _zs:
            _rank(ranked, _zs, YINGQI_TXT["use_god_restrained_zhi_sha_month"]["text"].format(ks=_ks), "月")
    if use_god_branch:
        if ug_moving:
            _rank(ranked, _he(use_god_branch), YINGQI_TXT["use_moving_he_month"]["text"], "月")
        else:
            _rank(ranked, _chong(use_god_branch), YINGQI_TXT["use_quiet_chong_month"]["text"], "月")
        _rank(ranked, use_god_branch, "用神值月", "月")
    if strength_level in ("休囚", "囚", "死", "偏弱", "衰") or speed == "应迟":
        _rank(ranked, peak, YINGQI_TXT["use_weak_prosper_month"]["text"], "月")
    _rank(ranked, use_god_branch, "以用神为主", "月")
    # 月级末位补充（排在既有序列之后，只补空槽不挤既有候选——月序本身是调优资产）：
    # G2 化出之支值月：《增删卜易》行人例「應亥月者父母化出之爻也」。
    if changed_pairs and _chg0 and _chg0 not in _empty_list:
        _rank(ranked, _chg0,
              YINGQI_TXT["hui_tou_sheng_change_branch"]["text"] + "（月）" if hui_tou_sheng
              else YINGQI_TXT["change_branch_value_month"]["text"], "月")
    # G3 三合虚一待用：《增删卜易》升遷例「欲成三合，因少卯字，明年卯月必升，此乃
    # 虛一待用」——卦中日月已具两支、独缺一支者，应于所缺之支之月（书例只给月级）。
    # 三合组的锚是「卦中日月爻已具两支」的组本身，而非用神所属之组：
    # 书例 WS016 用神巳火，三合缺支却在亥卯未组（月建亥+动爻未，缺卯）——
    # 若按用神组查会误入寅午戌组。故扫描四组、取「已具两支且缺一支」者补缺。
    # 三合成局的两支须来自动爻或日月（静爻不成局）；缺的一支待其值日月时补齐。
    _active = {(y.get("earthly_branch") or "") for y in yao_lines
               if isinstance(y, dict) and y.get("is_moving")}
    _active |= {day_branch or "", month_branch or ""}
    # 静爻被日辰所冲=暗动（《增删易》重动轻静），暗动之支亦可成局之形：
    # 书例 WS016 亥爻被巳日冲动、与动爻未欲成亥卯未三合（L1523 逐字）。
    _day_chong = _chong(day_branch) if day_branch else ""
    for y in yao_lines:
        if isinstance(y, dict) and not y.get("is_moving"):
            _b = y.get("earthly_branch") or ""
            if _b and _b == _day_chong:
                _active.add(_b)
    for _combo in SAN_HE_GROUPS.values():
        _ins = [b for b in _combo if b and b in _active]
        _miss = [b for b in _combo if b and b not in _active]
        if len(_ins) == 2 and len(_miss) == 1:
            _rank(ranked, _miss[0], YINGQI_TXT["sanhe_lack_branch_month"]["text"], "月")

    # 年级阶梯（G1）：《增删卜易》「近應日遠應年月」（月破章总纲）；世爻章
    # 「靜者逢沖逢值之年月……動者應在丑年月亦有應子年，餘仿此」「世空者沖空實空之年，
    # 世破者實破之年」「惟動空及動而破者，不妨定破實空之年月也」——
    # 同一套解除障碍之期在年单位上再排一遍（远应年月之年半边）。
    # 制杀之年（年级对称，第两百三十四批）：书据《增删卜易》源L1174 逐字「辰年冲去戌土，是以许之，果于辰年得选」（WS004/WS021 同案，年单位实案）；书序源L3099 总纲「被克者冲去克神之秋」属解障组，置于解障组之首实测（A/B 见 324 批 CHANGELOG）。
    for _ks_y in dict.fromkeys(_ke_shen):
        _zs_y = _chong(_ks_y)
        if _zs_y:
            _rank(ranked, _zs_y, YINGQI_TXT["use_god_restrained_zhi_sha_year"]["text"].format(ks=_ks_y), "年")
    if is_empty:
        _rank(ranked, use_god_branch, YINGQI_TXT["use_empty_fill_year"]["text"], "年")
        _rank(ranked, _chong_ug or use_god_branch, YINGQI_TXT["use_empty_chong_year"]["text"], "年")
    if is_month_break:
        _rank(ranked, use_god_branch, YINGQI_TXT["month_break_real_year"]["text"], "年")
    if tomb_branch and tomb_branch in (day_branch, month_branch):
        _rank(ranked, _chong(tomb_branch), YINGQI_TXT["use_tomb_chong_year"]["text"], "年")
    if bound_by:
        _rank(ranked, _chong(bound_by), f"用神被{bound_by}合住，冲开之年", "年")
    if step2_d.get("has_fu_cang") and (fu_branch or fei_branch):
        _rank(ranked, _chong(fei_branch) or fu_branch, YINGQI_TXT["fu_hidden_chong_fei_year"]["text"], "年")
    if use_god_branch:
        if ug_moving:
            _rank(ranked, _he(use_god_branch), YINGQI_TXT["use_moving_he_year"]["text"], "年")
        else:
            _rank(ranked, _chong_ug, YINGQI_TXT["use_quiet_chong_year"]["text"], "年")
        _rank(ranked, use_god_branch, YINGQI_TXT["use_value_year"]["text"], "年")
        # ⑧ 动用神逢冲之年（第两百四十六批；324 批曾试限「世动」回退——年窗 3 后
        #   WS049 酉年可入第 3 槽）。书据：《增删卜易》源L3634 逐字「应酉年者，谓之再冲之年」
        #   （WS049 占地，世爻卯动临月建，应爻酉冲克动世，四年之内二男一女相继而亡）；
        #   六冲章注源L1705「动逢冲而事散」——占吉事散、占凶事应，冲应之年。
        if _chong_ug:
            _rank(ranked, _chong_ug, YINGQI_TXT["use_moving_chong_year"]["text"], "年")
    # （第一百一十七批实验记录，未落库）各门类应期总注章的「问有应于变爻动爻…有戌日应者，有酉日应者」
    # 与「大象吉而受克，须待克神受克…后逢申酉日冲克克神」两条曾被作为年级候选试补：
    # 在 年=2 槽下**完全不生效**（被既有阶梯截断），提到 3 槽则"在池升而 top-1 不升、随机期望反涨"。
    # 若要取第一百一十六批测得的年 top-1 9.1%→27.3%，须把这两条**前置**，
    # 而总注章把它们列在末位——**那是拿外部集调参，已拒绝**；候选的排序依据见 #33（「神兆机于动，先重动爻」）。
    if strength_level in ("休囚", "囚", "死", "偏弱", "衰") or speed == "应迟":
        _rank(ranked, peak, YINGQI_TXT["use_weak_prosper_year"]["text"], "年")
    return ranked


# ────────────────────────────────────────────────────────────────
# 职责四：分级预算 + 组装输出（原 493–554 段）
# ────────────────────────────────────────────────────────────────

def _assemble_timing(ranked: list, timing_methods: list, speed: str,
                     special_pattern, step4_data: dict, use_god_branch: str,
                     candidates_all: list) -> dict:
    # 分级预算：单位不同不可同窗排序，否则加一个"生旺之月"就把正确的日支挤出窗口。
    # 月窗口 3→4：三合虚一待用（L1507「虚一待用，待后时之月日可以填之」）等
    # 月级通用轨曾被 3 槽截断（WS016 卯月排第 4 进不了输出）；A/B 全 split 无退化。
    UNIT_BUDGET = (("日", 5), ("月", 4), ("年", 3))
    by_unit = {u: [] for u, _ in UNIT_BUDGET}
    for token, rule in ranked:
        unit = token[-1]
        if unit in by_unit and len(by_unit[unit]) < dict(UNIT_BUDGET)[unit]:
            by_unit[unit].append((token, rule))
    yingqi_days = [t for t, _ in by_unit["日"]]
    yingqi_months = [t for t, _ in by_unit["月"]]
    yingqi_years = [t for t, _ in by_unit["年"]]
    ranked_top = by_unit["日"] or ranked

    key_branches = yingqi_days
    timing_rules = [{"token": t, "rule": r, "unit": t[-1]} for t, r in ranked]

    key_text = "、".join(key_branches) if key_branches else YINGQI_TXT["wait_strength"]["text"]
    main_text = f"{ranked_top[0][0]}（{ranked_top[0][1]}）" if ranked_top else "—"
    month_text = "、".join(yingqi_months) if yingqi_months else ""
    year_text = "、".join(yingqi_years) if yingqi_years else ""
    detail = ("、".join(t["description"] for t in timing_methods)
              if timing_methods else YINGQI_TXT["hard_to_single_yingqi"]["text"])

    sp_blob = ""
    if isinstance(special_pattern, dict):
        sp_blob = str(special_pattern.get("pattern") or "") + str(special_pattern.get("description") or "")
    elif special_pattern:
        sp_blob = str(special_pattern)
    if any(k in sp_blob for k in ("近病逢空", "近病逢合", "近病")):
        speed = "应速"
    if any("合" in str(t.get("method") or "") or "合" in str(t.get("description") or "") for t in timing_methods):
        speed_plain_extra = YINGQI_TXT["he_wait_chong"]["text"]
    else:
        speed_plain_extra = ""
    speed_plain = {
        "应速": YINGQI_TXT["speed_fast"]["text"],
        "应期适中": YINGQI_TXT["speed_medium"]["text"],
        "应迟": YINGQI_TXT["speed_slow"]["text"],
    }.get(speed, speed)
    sp_text = sp_blob
    if step4_data.get("tan_he_wan_sheng_ke") or "合处逢冲" in sp_text or "冲中逢合" in sp_text:
        speed_plain += YINGQI_TXT["repeat_uneasy"]["text"]

    summary_text = (f"重点应期：{key_text}。主应期 {main_text}。{speed_plain}。{speed_plain_extra}"
                    + (f"若事应迟，则看月级：{month_text}。" if month_text else "")
                    + (f"久案应于年：{year_text}。" if year_text else "")
                    + (f"依据：{detail}。" if detail else ""))
    timing_reasons = [summary_text]  # 本地列表，不进返回字典

    return {
        "timing_methods": timing_methods,
        "timing_rules": timing_rules,
        "speed": speed,
        "key_branches": key_branches,
        "yingqi_days": yingqi_days,
        "yingqi_months": yingqi_months,
        "yingqi_years": yingqi_years,
        "candidates_all": candidates_all,
        "summary_text": summary_text,
        "plain_text": (f"事情应验的时间，主看{main_text}，备选{'、'.join(key_branches[1:]) or '无'}。"
                       + (f"若拖得久，月级看{month_text}。" if month_text else "")
                       + f"{speed_plain}。"),
    }


# ────────────────────────────────────────────────────────────────
# 编排入口（原 _predict_timing 巨石本体，签名不变以兼容再导出）
# ────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────
# Rule 8：静爻旺相逢冲即发（《增删卜易》）
# ────────────────────────────────────────────────────────────────
def _apply_rule8_static_movement(r: dict, key_branches: list, day_branch: str,
                                 use_god_branch: str, strength_level: str,
                                 is_empty: bool) -> list[dict]:
    """静爻旺相逢冲即发 — 用神/原神静爻得旺相之气，日辰冲之即应。

    《增删卜易》原文：「静爻旺相，冲之即发；静爻休囚，冲之即破。」

    书源行号（2026-10-07 补注记，OPT-huangjince_dz-06／OPT-yiin_dz-03 对拍表）：
      data/sources/zengshan_buyi_dz.dz.txt 源L957「静而逢值逢冲」＝本条书源锚点
      data/sources/huangjince_dz.dz.txt 源L264 夹注「用爻旺相不动，以冲动月日断」
        ——千金赋期日九法之首法，与本条同向（旺相静爻候冲日），互为佐证
      data/sources/yiin_dz.dz.txt 源L1556「用静，则以冲动之日为期也。」
        ——《易隐》应期四诀之一，同向
    三源口径一致（旺相静爻→冲日），故本条不构成口径分歧。

    与 Rule 6（用神值日逢冲 / 非空静爻候冲）的区别：
      Rule 6 把所有"不空静爻"一律排"用神值日 + 冲日"两档，不分旺衰；
      本条专门识别「旺相静爻被冲即发」——旺相之静爻逢冲，
      不是「候冲填实」，而是「逢冲即动」，应期比 Rule 6 的候冲更速。

    命中条件：
      1) 用神不空（空则出空为先，不适用本条）
      2) 用神静爻（非动爻）且旺相
      3) 日辰冲用神之支
    """
    factors: list[dict] = []
    yao_lines = ((r.get("original_hexagram") or {}).get("yao_lines")) or []

    if is_empty or not day_branch or not use_god_branch:
        return factors

    # 用神是否旺相
    if strength_level not in ("极旺", "旺"):
        return factors

    # 日辰是否冲用神
    if _chong(use_god_branch) != day_branch:
        return factors

    # 用神必须在卦中且为静爻（有发动则归 Rule 6）
    ug_static = [y for y in yao_lines
                 if isinstance(y, dict)
                 and y.get("earthly_branch") == use_god_branch
                 and not y.get("is_moving")]
    if not ug_static:
        return factors

    # 命中：日辰冲用神之支即为应期，推入 key_branches
    if day_branch and day_branch in BRANCH_ORDER:
        token = f"{day_branch}日"
        if token not in key_branches:
            key_branches.append(token)
    factors.append({
        "rule": "r8_static_wang_chong",
        "basis": "静爻旺相逢冲即发",
        "source": "增删卜易",
        "weight": "high",
        "condition": f"用神{use_god_branch}旺相静爻，日辰{day_branch}冲之",
    })
    return factors


# ────────────────────────────────────────────────────────────────
# Rule 9：世应位置迟速调节（《增删卜易》）
# ────────────────────────────────────────────────────────────────
def _apply_rule9_shi_ying_modulation(r: dict, base_window: int = 0) -> list[dict]:
    """世应生克调节应期窗口宽度 — 不直接定应期，只修正宽松度。

    《增删卜易》原文：「世应相克，往来冲合，迟速有别；世应相生，逢值即应。」

    书源行号（2026-10-07 补注记，OPT-yiin_dz-03 对拍表）：
      data/sources/zengshan_buyi_dz.dz.txt 源L969「化退神、忌值忌冲：如酉化申，乃为退神，为凶为吉」段末
        「速则动而克世爻缓则静而生身」——**只此一处**把「动而克世→速 /
        静而生身→缓」写成通则；本条 Rule 9 是其**世应位置的同向实现**
        （世应相生收窄＝速／相克放宽＝迟），但**不覆盖「动克世/静生身」本身**
        （那一支只在 speed 粗档，未按动克世细判），故记为部分覆盖、登记不采。
      data/sources/huangjince_dz.dz.txt 源L265 逐字「速则动而克世，缓则静而生身。」
        ——与上同书源同向，《黄金策》亦作通则，可与增删互校。
      data/sources/yiin_dz.dz.txt 源L2168「动速静迟，旺相出现速，囚死伏藏迟。」
        ——《易隐》同向但按**爻位/宫位**细分，本条不采其细分（见模块 docstring 甲.4）。

    条件：
      - 世应相生 → 窗口收窄（速应，±0 日）
      - 世应相克 → 窗口放宽（迟应，±N 日）

    本条仅输出调节参数与因子记录，不影响 ranked 排序，
    不自动命中 strict 评分，但会影响 loose 评分。
    """
    factors: list[dict] = []
    yao_lines = ((r.get("original_hexagram") or {}).get("yao_lines")) or []

    shi_yao = next((y for y in yao_lines
                    if isinstance(y, dict) and y.get("is_world")), None)
    ying_yao = next((y for y in yao_lines
                     if isinstance(y, dict) and y.get("is_response")), None)
    if not shi_yao or not ying_yao:
        return factors

    shi_branch = shi_yao.get("earthly_branch") or ""
    ying_branch = ying_yao.get("earthly_branch") or ""
    if not shi_branch or not ying_branch:
        return factors

    shi_el = BRANCH_ELEMENTS.get(shi_branch, "")
    ying_el = BRANCH_ELEMENTS.get(ying_branch, "")
    if not shi_el or not ying_el:
        return factors

    if SHENG_CYCLE.get(shi_el) == ying_el or SHENG_CYCLE.get(ying_el) == shi_el:
        factors.append({
            "rule": "r9_shi_ying_modulation",
            "basis": "世应相生，逢值即应",
            "source": "增删卜易",
            "weight": "medium",
            "modulation": {
                "type": "narrow",
                "delta_days": 0,
                "description": f"世{shi_branch}({shi_el})与应{ying_branch}({ying_el})相生，应速",
            },
        })
    elif KE_CYCLE.get(shi_el) == ying_el or KE_CYCLE.get(ying_el) == shi_el:
        factors.append({
            "rule": "r9_shi_ying_modulation",
            "basis": "世应相克，往来冲合，迟速有别",
            "source": "增删卜易",
            "weight": "medium",
            "modulation": {
                "type": "widen",
                "delta_days": 3,
                "description": f"世{shi_branch}({shi_el})与应{ying_branch}({ying_el})相克，应迟",
            },
        })
    return factors


def predict_timing_core(r: dict, step3_data: dict, step1_data: dict, day_branch: str, special_pattern=None) -> dict:
    """
    应期判断 — v9：前置「重点应期」地支词，兼顾古籍规则与人话可读性。
    （原 491 行巨石已按职责切分为 _collect_key_branches / _build_timing_methods /
    _rank_candidates / _assemble_timing，见本模块。）

    新增 Rule 8（静爻旺相逢冲即发）与 Rule 9（世应迟速调节），
    在 Rule 1–7 之后追加检测，输出增加 timing_factors 字段。
    """
    use_god_branch = safe_get(step3_data, "use_god_branch", default="") or ""
    use_god_element = safe_get(step3_data, "use_god_element", default="")
    strength_level = safe_get(step3_data, "strength_level", default="中和")
    is_empty = safe_get(step3_data, "is_empty", default=False)
    is_month_break = safe_get(step3_data, "is_month_break", default=False)

    step4_data = safe_get(r, "_step4_data", default={}) or {}

    key_branches, month_branch, step2_d, pd = _collect_key_branches(r, use_god_branch, day_branch)
    timing_methods, speed = _build_timing_methods(
        r, step3_data, use_god_branch, use_god_element, strength_level,
        is_empty, is_month_break, day_branch, step2_d, step4_data, key_branches, pd)
    # candidates_all 必须在「法则应期」段追加支之后、排序之前快照
    candidates_all = list(key_branches)
    ranked = _rank_candidates(
        r, use_god_branch, use_god_element, strength_level, is_empty,
        is_month_break, day_branch, month_branch, step2_d, speed)
    timing_result = _assemble_timing(
        ranked, timing_methods, speed, special_pattern, step4_data,
        use_god_branch, candidates_all)

    # ── Rule 8: 静爻旺相逢冲即发 ──
    factors = _apply_rule8_static_movement(
        r, timing_result.get("key_branches", []), day_branch,
        use_god_branch, strength_level, is_empty)

    # ── Rule 9: 世应位置迟速调节 ──
    factors.extend(_apply_rule9_shi_ying_modulation(r))

    # 追加 timing_factors 字段（向后兼容：只新增，不改旧字段）
    timing_result["timing_factors"] = factors
    return timing_result


# 再导出入口（兼容 chain_step5.py 的 from chain_step5_yp import _predict_timing）
_predict_timing = predict_timing_core
