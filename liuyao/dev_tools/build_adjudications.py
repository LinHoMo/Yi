# -*- coding: utf-8 -*-
"""流派裁决表 v0（第一百八十八批·B2）——四书互驳处，引擎采谁、凭什么、状态如何，一次说清。

背景：全仓所有「与古书吻合」的声称此前都含混指四本书的合成体；但库里明文存在互驳
（觉子曰辟诸书之谬在《增删》是逐章体例，被《黄金策》旧注与《易冒》夹击）。本表把
**每一个已知分歧点**登记为：各方立场（逐字书证＋行号）→ 引擎立场 → 锚点 → 状态。
状态只有三种，不许含糊：
  settled_by_source  引擎照所据书文执行（书内自记例外也逐字在册）
  frozen_by_user     用户裁定冻结（引批次号）
  open_conflict      未决——引擎与语料自证相左，不得称已裁（#33 系此类的正式户口）

本表不改引擎、不进评分面、不挂门（第一百七十六批冻结守台账类新增）；它是「与古书吻合」
这句话的**展开定义**——今后任何报告引用吻合率，须能指回本表的哪几行。

    python dev_tools/build_adjudications.py            # 构建＋落盘（先逐字回验）
    python dev_tools/build_adjudications.py --verify   # 复核在册文件每条书证
    python dev_tools/build_adjudications.py --selftest # 负例：篡改书证必须拒写
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
sys.path.insert(0, str(HERE))
from stable_write import write_stable  # noqa: E402  203 批：幂等写，时间戳=内容最后变化

SRC = DISC / "data" / "sources" / "zengshan_buyi_dz.dz.txt"
OUT = DISC / "data" / "rules" / "adjudications.json"

Z = "《增刪卜易》（zengshan_buyi_dz.dz.txt）"

ENTRIES = [
    {
        "id": "liuyao.xunkong_variants",
        "dispute": "旬空判法：诸书列十一类空（真空/假空/动空/冲空…）vs 野鹤一句「旺不为空」的从简",
        "parties": [
            {"who": "诸书（转述）", "quote": "旬空之法，诸书论太烦，有真空、假空、动空、冲空、填空、无故自空、有散而空、墓空、绝空、害空、安空、破空", "source": Z, "line": 893},
            {"who": "野鹤/觉子", "quote": "非比休囚之真空到底而为空也", "source": Z, "line": 643},
        ],
        "engine_position": "采《增删》简化：真空/假空互斥判定（宁缺勿滥），不采十一类名目",
        "engine_anchor": "rule_registry: liuyao.xunkong_zhenjia → scripts/step3.py:583",
        "status": "settled_by_source",
    },
    {
        "id": "liuyao.clash_scatter_weight",
        "dispute": "冲散权重：《黄金策》空亡重而冲散轻 vs 《易冒》最重冲散 vs 野鹤「旺相冲之愈强，散百中一二」",
        "parties": [
            {"who": "黄金策（转述）", "quote": "黄金策以空亡为重，冲散为轻", "source": Z, "line": 852},
            {"who": "易冒（转述）", "quote": "易冒最重冲散", "source": Z, "line": 852},
            {"who": "野鹤/觉子", "quote": "旺相者冲之愈强", "source": Z, "line": 692},
        ],
        "engine_position": "从《增删》：用神旺相冲不破、休囚始论散；六合/六冲只出结构标签不覆写旺衰",
        "engine_anchor": "rule_registry: liuyao.liuhe_liuchong → scripts/effects.py:analyze_clash_harmony",
        "status": "settled_by_source",
    },
    {
        "id": "liuyao.sanhe_empty_break",
        "dispute": "三合局内一空一破是否破局：「破则不成局」派 vs 《增删》「待填满之日月成之」派",
        "parties": [
            {"who": "《增删》", "quote": "三合局中若有一空破者，待填满之日月成之", "source": Z, "line": 767},
        ],
        "engine_position": "三合/三会成立不以空破即废（待填/待冲结构标签在册；三会成立不再按三合破局论——第一百六十九批 registry 注）",
        "engine_anchor": "rule_registry: liuyao.sanhe → scripts/classical_enhancements.py:analyze_triple_combo；liuyao.sanhui impl 注",
        "status": "settled_by_source",
    },
    {
        "id": "liuyao.month_break_day_stem",
        "dispute": "月破是否永破：「破而不破（临日建/有生扶）」vs 一律论破；例外＝忌神发动伤用（寡不敌众，破亦为破）",
        "parties": [
            {"who": "《增删》例文", "quote": "亥为月破，临日建而不破", "source": Z, "line": 708},
            {"who": "《增删》总论", "quote": "逢月破而不破", "source": Z, "line": 692},
            {"who": "野鹤总论", "quote": "惟而不动又无日辰动爻生助者则到底而破矣", "source": Z, "line": 991},
            {"who": "《增删》实案例外", "quote": "卯木子孙，临月破，又动出申金伤克，虽值日辰，难过酉月卯日", "source": Z, "line": 1911},
        ],
        "engine_position": "月破层存在且救法集条件化（第两百八十批）：临日建1.0/日合0.5/日辰生扶0.5，例外＝卦中忌神类动爻克伤用神时救法不给（L692 寡不敌众；L1911 临日辰仍凶）；第一百五十九批唤醒 is_month_break 死键后外部 top-1 22.7→27.3 为该立场的读数侧写",
        "engine_anchor": "rule_registry: liuyao.yuepo → scripts/classical_enhancements.py:analyze_monthly_break；step3.compute_month_break_modifier（280 批条件化）",
        "status": "settled_by_source",
    },
    {
        "id": "liuyao.tianshi_frost_claims",
        "dispute": "占天时：旧注「冬天以子孙为霜雪」vs 野鹤「占天时不论旺衰，亦未有以子孙为霜雪」",
        "parties": [
            {"who": "旧注（转述）", "quote": "旧注有云，冬天以子孙为霜雪", "source": Z, "line": 1963},
            {"who": "野鹤/觉子", "quote": "所以占天时，不论旺衰，亦未有以子孙为霜雪也", "source": Z, "line": 1971},
        ],
        "engine_position": "占天候台架从《增删》：只看发动六亲（子孙/财=晴、父母=雨），不论旺衰、不设季节变体",
        "engine_anchor": "dev_tools/tianhou.py 裁决表（第一百八十批）；未入引擎用神层（入层须另批带书证两集出分）",
        "status": "settled_by_source",
    },
    {
        "id": "liuyao.moving_line_yingqi_priority",
        "dispute": "应期取支主位：「神兆机于动，先重动爻」总注法 vs 现行应期以用神取支为纲",
        "parties": [
            {"who": "《增删》断例", "quote": "神兆机于动，余从来不言散", "source": Z, "line": 550},
        ],
        "engine_position": "应期阶梯以用神为主（七条规则），克神/变爻/元神取支仅部分入池——与本书自证存在已登记分歧",
        "engine_anchor": "step5.calculate_yingqi 七条阶梯；#33 档案（失败形态 B 类 30%＝对支在池不在首）",
        "status": "open_conflict",
        "note": "本项是引擎与所据书的已知偏差，不是裁决完成；#33 结案判据（是否改双主位）留用户裁，不许由实现侧代劳（§四.3）。",
    },
    {
        "id": "liuyao.usegod_two_present",
        "dispute": "用神两现取舍：古法序（旺/动/不破/不空）vs 书内自记例外（应验偏在空破之爻）vs《易冒》有伤无伤键",
        "parties": [
            {"who": "古法（《增删》述）", "quote": "舍其休囚，用其旺相，舍其静爻，而用动爻，舍其月破，而用不破，舍其旬空，用其不空，舍其被伤，用其不伤。此古法也", "source": Z, "line": 1396},
            {"who": "《增删》例外自记", "quote": "得其验者，应乎旬空月破，舍其不空，而用旬空，舍其不破，而用月破", "source": Z, "line": 1396},
        ],
        "engine_position": "A 古法序为第一键并冻结（第一百七十二批：B 易冒键书注样本 4/7 反书注、C 与 A 同分无增益）；例外条款在册不实现——n=6 不足以普适（该批自注），强判反违书",
        "engine_anchor": "step2._use_god_rules；门 [26]/取舍序冻结登记见 CHANGELOG 第一百七十二批",
        "status": "frozen_by_user",
    },
]


def verify_entries(entries) -> list[str]:
    lines = SRC.read_text(encoding="utf-8").splitlines()
    bad = []
    for e in entries:
        for q in e["parties"]:
            ln = lines[q["line"] - 1] if 0 < q["line"] <= len(lines) else ""
            if q["quote"] not in ln:
                bad.append("%s: 书证非该 L%d 行逐字子串（%s…）" % (e["id"], q["line"], q["quote"][:24]))
    return bad


def cmd_build() -> int:
    bad = verify_entries(ENTRIES)
    if bad:
        print("× 书证逐字回验未过，拒绝落盘：")
        for b in bad:
            print("  · " + b)
        return 1
    doc = {"schema": "yi-liuyao-adjudications/1", "discipline": "liuyao",
           "built_at": datetime.now().isoformat(timespec="seconds"),
           "_comment": "流派裁决表：「与古书吻合」的展开定义。引用任何吻合率须能指回本表行。"
                       "不改引擎不进评分面不挂门（§176 冻结声明）。状态三值见 builder docstring。",
           "count": len(ENTRIES),
           "entries": ENTRIES}
    write_stable(OUT, doc)
    print("√ 裁决表落成 %s｜%d 项分歧点（settled %d／frozen %d／open %d），书证 %d 条全部逐字回验过"
          % (OUT.name, len(ENTRIES),
             sum(1 for e in ENTRIES if e["status"] == "settled_by_source"),
             sum(1 for e in ENTRIES if e["status"] == "frozen_by_user"),
             sum(1 for e in ENTRIES if e["status"] == "open_conflict"),
             sum(len(e["parties"]) for e in ENTRIES)))
    return 0


def cmd_verify() -> int:
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    bad = verify_entries(doc["entries"])
    for b in bad:
        print("  · " + b)
    print("√ 在册裁决表 %d 项书证全部可回指原书行" % len(doc["entries"]) if not bad
          else "× 回验未过 %d 条" % len(bad))
    return 0 if not bad else 1


def cmd_selftest() -> int:
    fails = []
    n = len(verify_entries(ENTRIES))
    if n:
        fails.append("正书证回验本应全过，实报 %d 条问题" % n)
    tampered = [dict(ENTRIES[0], parties=[dict(ENTRIES[0]["parties"][0], quote="旬空之法诸书不论")] )]
    if not verify_entries(tampered):
        fails.append("篡改书证未被识破（回验是摆设）")
    shift = [dict(ENTRIES[1], parties=[dict(ENTRIES[1]["parties"][0], line=1)])]
    if not verify_entries(shift):
        fails.append("行号挪移未被识破")
    ids = [e["id"] for e in ENTRIES]
    if len(ids) != len(set(ids)):
        fails.append("裁决项 id 重复")
    if not any(e["status"] == "open_conflict" for e in ENTRIES):
        fails.append("open_conflict 被清零——不许把未决粉饰为已裁")
    print("√ selftest：正验全过/篡改拒/行号挪移拒/id 唯一/未决项保留 全过" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="流派裁决表构建器（B2，逐字书证回验后落盘）")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    if args.verify:
        return cmd_verify()
    return cmd_build()


if __name__ == "__main__":
    raise SystemExit(main())
