# -*- coding: utf-8 -*-
"""治理地图生成器（第一百九十四批·E2 第一半）——把两科 dev_tools 全量脚本变成可导航清单。

三档语义（定义写死在本文件与根 GOVERNANCE.md，两处须同步改）：
  blocking  check.py 每次全量必跑的门（合入前拦截层）
  nightly   不参与合入拦截、定期或按需重跑的审计/报告器
  ondemand  一次性审计与对拍器（diff_*/audit_*：有对手才跑）
  build     语料/案例构建管道（产物进 data/）
  tool      开发辅助（无守护对象）
未分类不静默：任何不在 curated 表里的 *.py 都进 unclassified 清单并 --strict 判红——
地图烂掉的方式和台账烂掉的一样，都是「新增的东西没人认领」。

本批只出地图与降档候选清单，**不删并不并任何脚本**（§四 验收在删并执行批做）。

    python dev_tools/governance_map.py                 # 两科打印+落 docs/GOVERNANCE-MAP.json
    python dev_tools/governance_map.py --strict        # 未分类即 rc=1（CI 可用）
    python dev_tools/governance_map.py --selftest
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "liuyao" / "scripts"))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
sys.path.insert(0, str(HERE))
from stable_write import write_stable  # noqa: E402  203 批：幂等写，时间戳=内容最后变化

TIERS = ("blocking", "nightly", "ondemand", "build", "tool")

# tier 归属人工初判（194 批）；guards 一句话＝它守什么。按脚本名排序便于 diff。
CURATED = {
    # ---- bazi/dev_tools ----
    "bazi": {
        "check": ("blocking", "两科总闸：全量编排+基线比较"),
        "golden": ("blocking", "40 例结论级指纹（机械+措辞）漂移看门狗"),
        "regression": ("blocking", "5 例手写出生时刻机械断言"),
        "eval_selftest": ("blocking", "评分器九场景校准"),
        "eval_unique_keys": ("ondemand", "考点折叠量尺（207 批更正：从未挂闸，194 批误标 blocking——一致性断言自抓）"),
        "check_case_dupes": ("blocking", "案例考点查重（#39 冗余防线）"),
        "check_case_isolation": ("blocking", "铁律二：解读路径不得触案例库"),
        "check_regex_lists": ("blocking", "正则字符类 list 展平审计（209 批：§二 静默全盲规矩的核对版）"),
        "check_case_pillars": ("blocking", "命例基准自洽（expected 四柱可反算）"),
        "check_cli_encoding": ("blocking", "中文 CLI 编码红线（cp936 行为面）"),
        "check_dayun_cases": ("blocking", "行运见证集回验"),
        "check_determinism": ("blocking", "三 seed 行为一致＋集合 join 静态扫"),
        "check_dim_lock": ("blocking", "维度适用数锁（shensha/dayun 台账双向）"),
        "check_dim_surface": ("blocking", "评测维↔报告面同名同义＋17 小节登记"),
        "check_doc_refs": ("blocking", "文档活引用可达性（死指针判红）"),
        "check_house_conventions": ("blocking", "§三 house 规矩核对版（211 批：版本名/绝对路径/scratch/产物四判据）"),
        "check_feedback": ("blocking", "现实反馈通道 schema/孪生一致"),
        "check_hidden_stems": ("blocking", "藏干独立出处回验"),
        "check_pillar_laws": ("blocking", "排盘入参历法自洽"),
        "check_rule_registry": ("blocking", "规则注册表书源/impl 指针回验"),
        "check_source_readings": ("blocking", "书证引文逐字回验（源L行号）"),
        "corpus_reports": ("blocking", "多盘并集接线闸（[8]；缺件自愈）——207 批更正 tier：实为挂闸门"),
        "corpus_wiring_report": ("blocking", "语料进没进报告的接线读数（挂 [8] 系；207 批更正）"),
        "verdict_audit": ("blocking", "断语外置审计 [16]（207 批更正 tier：实为挂闸门）"),
        "feedback_store": ("tool", "现实反馈落盘通道（在册 0）"),
        "sync_tiaohou_engine": ("blocking", "调候表↔data 同步门（§四.6 --check 挂闸；207 批更正）"),
        "sync_nayin_engine": ("blocking", "纳音表↔data 同步门（§四.6 --check 挂闸；207 批更正）"),
        "diff_tiaohou_vs_head": ("ondemand", "改表前后逐格对拍范式"),
        "baselines": ("ondemand", "八字判断维×常数基线配对对照（187 批 A3 读数器）"),
        "audit_qtbj_batch": ("ondemand", "全局八字批审计一次性器"),
        "audit_tiaohou_gap": ("ondemand", "调候空档审计一次性器"),
        "build_bazili_cases": ("build", "bazili 案例构建"),
        "build_dts_corpus": ("build", "滴天髓语料构建"),
        "build_tiaohou": ("build", "调候语料构建"),
        "build_tiaohou_cases": ("build", "调候案例构建"),
        "__init__": ("tool", "包标记"),
    },
    # ---- liuyao/dev_tools ----
    "liuyao": {
        "check": ("blocking", "两科总闸：全量编排+基线比较"),
        "golden": ("blocking", "288 例指纹（含 193 批扩入的 conclusion 层）"),
        "hexagram_check": ("blocking", "爻序 P0 看门狗（23 断言）"),
        "outcome": ("blocking", "现实回填统计出口（Wilson/n<30 拒判；195 批划界：不写封存）"),
        "feedback_store": ("blocking", "应期反馈记录存储（一键闭环落盘；195 批划界：判卷归 prospective）"),
        "feedback_report": ("blocking", "反馈汇总口径门（check 362 行 import 消费；207 批更正 tier）"),
        "style_check": ("blocking", "CSS 类名有定义（报告面）"),
        "refactor_guard": ("ondemand", "零指纹漂移验收器"),
        "check_bing_yao": ("blocking", "日辰并爻唯一性守卫（[27]）"),
        "check_case_isolation": ("blocking", "铁律二静态扫描"),
        "check_regex_lists": ("blocking", "正则字符类 list 展平审计（209 批：§二 静默全盲规矩的核对版）"),
        "check_case_selfconsistency": ("blocking", "案例日辰/应期自引书文自洽"),
        "check_cli_encoding": ("blocking", "中文 CLI 编码红线"),
        "check_doc_refs": ("blocking", "文档活引用可达"),
        "check_house_conventions": ("blocking", "§三 house 规矩核对版（211 批：版本名/绝对路径/scratch/产物四判据）"),
        "check_fangwei": ("blocking", "方位层还出书自断"),
        "check_fixture_invariants": ("blocking", "fixture 声明干支/卦名可算"),
        "check_rule_registry": ("blocking", "注册表 verified/impl 指针回验"),
        "check_source_readings": ("blocking", "书证逐字回验（含代码注释）"),
        "check_verdict_external": ("blocking", "结构层断语外置审计（210 批：§一.1 核对版 LOCK=0，抓到探针漏网 1 处）"),
        "check_split_ledger": ("blocking", "分片排除理由可字面重跑"),
        "check_verdict_coherence": ("blocking", "判词与得分同档"),
        "check_yingqi_information": ("blocking", "候选池信息量红线（防铺量涨分）"),
        "check_yingqi_scoring": ("blocking", "E 类评分口径双向守卫（[26]）"),
        "prospective": ("blocking", "前瞻封存哈希链判卷通道（[28]，在册 0；195 批划界：唯一封存判卷面）"),
        "harvest_verifications": ("nightly", "古籍自验盘点册构建（观察册）"),
        "graduate_verifications": ("nightly", "自注毕业三态台账（观察册）"),
        "use_god_coverage": ("nightly", "用神来源矩阵"),
        "diff_jingshi_vs_core": ("ondemand", "京氏传↔内核逐格对拍"),
        "diff_shangzhan_vs_core": ("ondemand", "尚占↔内核逐格对拍"),
        "fetch_huozhulin_cases": ("build", "火珠林采集管道（通道活：评分 2<5 未入集/定性 5 在册；196 批 selftest 八件证网无盲）"),
        "fetch_wikisource_cases": ("build", "维基文库案例采集管道"),
        "build_extra_dimensions": ("build", "额外评分维构建"),
        "build_question_use_gods": ("build", "问题→用神词典构建"),
        "build_use_god_rules": ("build", "用神法则表构建"),
        "build_usegod_position": ("build", "用神位置表构建"),
        "build_yingqi_set": ("build", "应期基准集构建"),
        "build_zengshan_dz_cases": ("build", "dz 底本案例构建（八道门）"),
        "ablation": ("ondemand", "规则消融台架（182 批/186 扫掠，配对 McNemar）"),
        "abstain_report": ("ondemand", "弃权分型读数（191 批结案器）"),
        "baselines": ("ondemand", "一行规则基线×引擎对照（读数器）"),
        "build_adjudications": ("nightly", "流派裁决表构建（逐字回验）"),
        "rank_experiment": ("ondemand", "名次键预注册实验（一次性报数器）"),
        "tianhou": ("ondemand", "占天候台架（真实运行待授权）"),
        "triage_partials": ("nightly", "partial 机械预分诊（202 批：B 路与 recheck 词袋同源，15 速裁/8 真分歧并排/5 兜底/35 结案候选，不改判）"),
        "readout_ledger": ("nightly", "读数对账台（200 批：登记值 vs HEAD 重放值逐位核对，×＝分家立案）"),
        "recheck_restorable": ("nightly", "restorable 双解析器共识复核（201 批：10 共识/8 分歧标字段；202 批与分诊 B 路共用词袋=器内口径唯一）"),
        "draft_candidates": ("nightly", "共识→入册候选草稿器（204 批：10 候选含 dup 点名/question 开口，不进册不评分）"),
        "version_collate": ("ondemand", "两抄本源级对拍（185 批冲突率）"),
        "window_report": ("ondemand", "top-k 覆盖曲线读数器"),
        "governance_map": ("tool", "本器：治理地图生成"),
        "stable_write": ("tool", "观察册幂等写共享模块（203 批：时间戳=内容最后变化，杜绝空转脏文件）"),
        "__init__": ("tool", "包标记"),
    },
}


def scan_disc(disc: str, curated: dict, dev_dir: Path, check_py: Path):
    rows, unclassified = [], []
    gate_text = check_py.read_text(encoding="utf-8", errors="replace") if check_py.exists() else ""
    for p in sorted(dev_dir.glob("*.py")):
        stem = p.stem
        src = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'"""[ \t]*\n?(.{0,72})', src)
        desc = (m.group(1).strip() if m else "")[:72]
        # 挂闸两源（207 批）：子进程路径字面量 OR 模块 import——只查其一会把
        # `from feedback_store import ...` 这类真闸门读成未挂（实测漏报两例）。
        in_check = (('dev_tools/%s.py' % stem) in gate_text
                    or re.search(r"\b(?:import|from)\s+%s\b" % re.escape(stem), gate_text) is not None)
        if stem in curated:
            tier, guards = curated[stem]
        else:
            tier, guards = "UNCLASSIFIED", ""
            unclassified.append(p.name)
        rows.append({"script": p.name, "tier": tier, "guards": guards,
                     "run_by_check_py": in_check, "doc": desc})
    ghost = [k for k in curated if not (dev_dir / (k + ".py")).exists()]
    return rows, unclassified, ghost


def build(strict=False) -> int:
    out = {"schema": "yi-governance-map/1", "tiers": list(TIERS),
           "_policy": "三档定义见根 GOVERNANCE.md；blocking→ondemand 降档须连续一季 0 判红且负例仍可跑，逐批执行；新门仍按 §四.8 负例自证。",
           "disciplines": {}}
    rc = 0
    for disc in ("bazi", "liuyao"):
        dev = ROOT / disc / "dev_tools"
        rows, unc, ghost = scan_disc(disc, CURATED[disc], dev, ROOT / disc / "dev_tools" / "check.py")
        # 一致性断言（第两百零七批）：tier 定义的机器化。分两级是诚实的分层：
        # 硬断言 blocking⇒被 check 引用（漏引用＝假闸门，--strict 判红）；
        # 软清单 引用⇏blocking（被 required 存在性清单提及但未执行属合法形态——
        # bazi diff_tiaohou_vs_head 实例——但清单内容入账，冒出没见过的条目账台即红）。
        bnl = [r["script"] for r in rows if r["tier"] == "blocking" and not r["run_by_check_py"]]
        lnb = sorted(r["script"] for r in rows if r["run_by_check_py"] and r["tier"] != "blocking")
        from collections import Counter
        tc = Counter(r["tier"] for r in rows)
        out["disciplines"][disc] = {"count": len(rows), "by_tier": dict(tc),
                                    "unclassified": unc, "curated_but_missing": ghost,
                                    "tier_link_violations": {"blocking_not_referenced": bnl,
                                                            "referenced_not_blocking": lnb},
                                    "rows": rows}
        dst = ROOT / disc / "docs" / "GOVERNANCE-MAP.json"
        write_stable(dst, out["disciplines"][disc])
        print("%s：%d 脚本｜blocking %s｜nightly %s｜ondemand %s｜build %s｜tool %s"
              % (disc, len(rows), tc.get("blocking", 0), tc.get("nightly", 0),
                 tc.get("ondemand", 0), tc.get("build", 0), tc.get("tool", 0)))
        if unc or ghost:
            print("  × 未分类 %r｜表中有序实无 %r" % (unc, ghost))
            rc = 1 if strict else rc
        if bnl:
            print("  × %s blocking 未挂闸（假闸门）：%r" % (disc, bnl))
            rc = 1 if strict else rc
        if lnb:
            print("  · %s 被引用但非 blocking（存在性引用合法，清单已入账）：%r" % (disc, lnb))
    print("（本批只出地图，不删并不；降档候选＝nightly/ondemand 中连续一季零判红者，逐批走 §四）")
    return rc


def selftest() -> int:
    fails = []
    with tempfile.TemporaryDirectory(prefix="yi_gov_st_") as td:
        tdp = Path(td)
        dev = tdp / "dev_tools"
        dev.mkdir()
        (dev / "known.py").write_text('"""已知器。"""\n', encoding="utf-8")
        (dev / "lonely_gate.py").write_text('"""声称挂了闸其实没有。"""\n', encoding="utf-8")
        (dev / "brand_new_thing.py").write_text('"""新来的没人认领。"""\n', encoding="utf-8")
        check = tdp / "runner_check.py"          # 编排器不放进被扫描目录，否则自己变未分类
        # 运行时拼出完整字面量写入临时文件：本 .py 源码任何处（含注释）都不出现
        # 「dev_tools/known 加后缀」的全文——[11] 把带斜杠串当路径声明，194 批首跑即抓，
        # 夹具与产品同规矩。
        token = "dev_tools/known" + ".py"
        check.write_text("x = %r\nimport lonely_gate\n" % token, encoding="utf-8")
        rows, unc, ghost = scan_disc("t", {"known": ("blocking", "x"),
                                           "lonely_gate": ("ondemand", "y"),
                                           "vanished": ("tool", "z")}, dev, check)
        if unc != ["brand_new_thing.py"]:
            fails.append("未分类显形错：%r" % unc)
        if ghost != ["vanished"]:
            fails.append("幽灵条目（表里有实无）显形错：%r" % ghost)
        if not any(r["script"] == "known.py" and r["run_by_check_py"] for r in rows):
            fails.append("run_by_check 关联失效（子进程字面量源）")
        if not any(r["script"] == "lonely_gate.py" and r["run_by_check_py"] for r in rows):
            fails.append("import 源关联失效（模块 import 也须算挂闸，207 批）")
        # 一致性断言的负例：blocking 却没被任何一种源抓到
        fake = [dict(r) for r in rows]
        # 把 known 的关联关掉——blocking 且无关联必须显形
        for r in fake:
            if r["script"] == "known.py":
                r["run_by_check_py"] = False
        bnl = [r["script"] for r in fake if r["tier"] == "blocking" and not r["run_by_check_py"]]
        if bnl != ["known.py"]:
            fails.append("blocking未挂闸负例未显形：%r" % bnl)
    real_rc = build(strict=True)
    if fails:
        print("× selftest：" + "；".join(fails))
        return 1
    print("√ selftest：未分类/幽灵/双源关联/挂闸硬断言 负例全过；真实扫描 strict rc=%s" % real_rc
          if not fails else "× " + "；".join(fails))
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="治理地图生成器（E2 第一半）")
    ap.add_argument("--strict", action="store_true", help="未分类/幽灵条目即 rc=1")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return build(args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
