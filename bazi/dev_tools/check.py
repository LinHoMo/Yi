# -*- coding: utf-8 -*-
"""命·质量门：契约完整性 + 四段冒烟 + 金标准 + **对齐分下限** + **表同步门**。

    python dev_tools/check.py            # 全部检查（含 [7] 分数下限门）
    python dev_tools/check.py --raise    # 把本次实测对齐分登记为新基线（确认改进后才用）
    python dev_tools/check.py --fast     # 跳过 [7] 案例评测（省时；**不作为合入依据**）

⚠ `--fast` 下 **[7] 分数下限门不生效**（照六爻同参数口径）。合入前必须跑一次**不带 --fast**
  的本门，否则 tune/holdout 回退无人拦（SKILL.md）。跳过时本门会在输出里显式写明
  「未生效」，不假装通过。
  （2026-10-13 更正：此处原写「根门 `dev_tools/check.py --full` 才会不带 --fast 跑一遍」，
   而根 `tools/check.py` 已随扁平化删除、本器也从未接受过 `--full`——推荐的是一个不存在
   的命令。同一错误提示还在两处注释里，已一并按实改掉，见 docs/CHANGELOG.md 第一百六十八批。）

分数口径（SKILL.md 铁律三，务必连同分数一起读）：
  [7] 的分数是**古籍案例对齐分**——引擎输出与《穷通宝鉴》《子平真诠》《滴天髓》等
  案例要点的加权一致性（strict 计分模型），用于回归审计，**衡量不了现实命中率**。
  tune n=60、holdout n=278（2026-10-13 按 `scripts/evaluate.py --split … --save` 实跑更正；
  原记「tune n=138、holdout n=532」系 #39 清出 342 例冗余**前**的口径，新旧不可比——
  见 docs/EVAL-PLAN.md §1.1 与 §四.4）。holdout 集合未参与本轮判据调参。

门槛设计（SKILL.md）：
  · 基线取**实测值**，只准前进不准后退：低于 BASELINE 即判红（范式照六爻
    `liuyao/dev_tools/check.py`）。抬基线走 `--raise`，且必须在
    `docs/CHANGELOG.md` 登记理由；**下调**基线只能改本文件里的字面量（进 git diff、
    进评审），本地 `check_baseline.json` 覆盖文件一律**不得放宽**（见 `_effective_baseline`）。
  · §四.2「tune 均分无故跌破 95 即视为回归」落在**加权均分**口径上（当前 tune 100.0 /
    holdout 99.5（308 批实测，原登记 97.6），均 ≥95，AGENTS_TUNE_FLOOR 有机械断言兜着）。
  · ⚠ tune 已 **100.0% 满分饱和**（60/60，min=max）。按 AGENTS.md §三.4 自引口径，
    该集**已丧失区分能力**，只能当回归哨兵，不得作为能力证据引用（308 批标注）。
  · 维度层不用百分比当门槛，改用**绝对命中数**（`DIM_HITS`）：当前 holdout 的
    pattern 100.0%（308 批实测 36/36，原 80.6%）／cong_ge 86.7% 是「满分例数/适用例数」的维度内比值（n=36／n=15，
    另有 242／263 例 N/A——本集合 n=278，Applicable+NA 必须等于 278），不是 §四.2 说的「均分」；
    把它当 95 分线是口径错配。
    而百分比本身不能当回归门槛——新增案例只涨分母、必然压低百分比，拿它设线等于
    逼人调阈值或拒绝扩样。命中数则单调：引擎回归必压低它，扩案例不会。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[1] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.gate_kit import eval_metrics, run_step  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

BASELINE_FILE = DISC / "dev_tools" / "check_baseline.json"   # 本地覆盖（gitignore）
CASES_FILE = DISC / "data" / "cases" / "bazi_classical_cases.json"

# 古籍案例对齐分（加权均分 %，strict）——2026-10-09 实测登记，非预测命中率
BASELINE = {
    "tune": 100.0,        # n=60（2026-10-13 按 #39 清冗余后的实测例数更正，原注 n=30）
    # 308 批只准前进：96.6 → 99.5（实测；抬基线即收紧门，与 AGENTS.md §四.2 同口径）。
    "holdout": 99.5,      # n=278（未参与本轮调参；原 96.6 系 2026-10-10 从格判据改正后登记，
                          #  原注 n=246 系语料扩容前快照；308 批按实测抬到 99.5，只准前进）
}
AGENTS_TUNE_FLOOR = 95.0  # SKILL.md 的均分硬下限；BASELINE 必须严于它

# 维度绝对命中数下限（= evaluate.py 明细里的「满分例数」；n/a 例不进分母故不影响本数）
DIM_HITS = {
    "tune": {"tiaohou": 60, "ten_gods": 1, "hidden_stems": 1},
    "holdout": {"pillars": 213, "tiaohou": 51, "pattern": 36, "cong_ge": 13,
                "ten_gods": 213, "hidden_stems": 213, "shensha": 5},
}
# tiaohou 下限原为 tune 30／holdout 19（扁平化提交 e2c77ad 带入，此后语料扩样但
# 该两格从未回头改）——实测满分数已是 60／51，即**下限只压着实测的 50%／37%**：
# 该维静默丢掉一半（holdout 丢 32/53）也不会判红，正是本门要防的静默盲区。
# 其余各维下限均与实测齐平（pillars 213/213、pattern 36/36（308 批由 29 抬上）、cong_ge 13/13、
# ten_gods 213/213、hidden_stems 213/213），唯 tiaohou 松弛，故判定为陈旧字面量而非有意留量。
# 按 AGENTS.md §四.2「基线只准前进」上调至实测值，与其余各维同口径（下限=实测满分数）。
# ten_gods／hidden_stems 的下限是**回填存活线**（2026-10-13 第一百六十八批补）：
# 这两维由书载四柱机械派生回填（AGENTS.md §三.4 定义式例外），214 例带键。曾经
# 语料被回填**后**的版本在一次 git 还原中静默丢失、回到回填前版本，而本门全程绿——
# 因为均分 97.578（无此两维）与 97.638（有）都四舍五入成 97.6，两维的 N/A 不进分母，
# 于是一次「少 214 例 × 24 权重」的静默盲区在分数上完全不可见。命中数是绝对量：
# 键丢了 → applicable=0 → full=0 < 下限 → 判红。这才是「回填有没有活着」的机械证据。
# shensha／dayun 的空档原先只有「不设假下限」一句注（第一百六十九批前的原话），
# 该批起改为：shensha 由**书证回填 5 例**（全库 338 例以引擎神煞基名 19 项机械抽自
# core/yishu_core/shensha.py、扫 source_quote+note，命中者全部回填：MT521 书作「羊刃」
# 《穷通宝鉴》论庚·八月「且见羊刃…名为羊刃驾杀」；ZP006/ZP007/ZP031/MT550 书作异名
# 「阳刃」＝阳干之刃，按同义存引擎名「羊刃」，逐例书证见 scratch/_inject_shensha.py
# 与本批 CHANGELOG；其余 333 例书文 0 处提及神煞名 ⇒ 维持空档）。
# 故 holdout 加 `shensha: 5` 作**回填存活线**——键在 git 还原里静默丢失
# ⇒ applicable 归 0、full 归 0 < 下限 5 → 判红。dayun 仍无可回填（书文明写顺逆／起运
# 实测 0/338），不设假下限；两维的**带期望例数**由 [25] 维度适用数锁双向锁死
# （多了＝未登记回填判红，少了＝回填丢失判红）。

# 接线门比对的最小叶子长度。原取 12（只想比整句引文），代价是 nayin_quxiang.json
# 这类「性质名短语库」（227 条叶子全 <12 字、最长 8 字）被 `if not leaves: continue`
# 整份跳过——死语料反而看不见。取 4：四字名相（「从革之金」）已足够特异，不会撞进干支串里；
# 真出现「短串偶合」的假绿，宁可显式登记在 UNWIRED_CORPORA 也不靠拉长阈值来遮。
MIN_LEAF_LEN = 4


ENC_WITNESS: list[str] = []


def run(cmd: list[str]) -> tuple[int, str]:
    """本门口径：cwd=学科根、60s 超时、argv 前补解释器（实现在内核 gate_kit）。"""
    _rc, _out = run_step(cmd, cwd=DISC, timeout=60, python=True)
    witness = None
    try:
        import importlib.util as _iu
        _path = str(DISC / "dev_tools" / "check_cli_encoding.py")
        _sp = _iu.spec_from_file_location("enc_witness", _path)
        if _sp is None or _sp.loader is None:
            raise RuntimeError("载不进门：『" + _path + "』")
        _mod = _iu.module_from_spec(_sp)
        _sp.loader.exec_module(_mod)
        witness = _mod.witness
    except Exception as _e:
        ENC_WITNESS.append("编码证人自身没跑成：" + type(_e).__name__ + ": " + str(_e)[:90])
    if witness is not None:
        _nm = next((a for a in cmd if str(a).endswith(".py")), str(cmd[-1]))
        _w = witness(_nm, _out or "")
        if _w:
            ENC_WITNESS.append(_w)
    return _rc, _out


def _effective_baseline() -> dict:
    """BASELINE 与本地覆盖文件合并——**覆盖文件只准抬，不准降**（防"调绿"）。"""
    merged = dict(BASELINE)
    if not BASELINE_FILE.exists():
        return merged
    local = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    for key, value in local.items():
        floor = BASELINE.get(key)
        if isinstance(floor, (int, float)) and isinstance(value, (int, float)) \
                and value < floor:
            raise SystemExit(
                f"× {BASELINE_FILE.name} 把 {key} 基线从登记值 {floor} 降到 {value}——"
                f"本地覆盖文件不得放宽门槛。要下调基线：改本文件字面量（进 git diff）"
                f"并在 docs/CHANGELOG.md 登记理由。")
        merged[key] = value
    return merged


def _leaf_strings(obj) -> list[str]:
    """语料 JSON → 全部叶子字符串（跳过 _meta：元信息本就不进报告）。"""
    if isinstance(obj, dict):
        return [s for k, v in obj.items() if k != "_meta" for s in _leaf_strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _leaf_strings(v)]
    return [obj] if isinstance(obj, str) else []


# 已知「数据已入库、叙述层未接线」的语料：如实登记而不是静默跳过（SKILL.md
# 「任何 0 结果都要先确认不是路径解析错了」的反面——0 命中必须有名有姓地说出来）。
# 列在这里的文件一旦真的接上（命中 >0），本门**反而判红**并要求把它从表里摘掉，
# 于是这张表不会烂成「永久豁免清单」。
# ⚠️ 2026-10-09f 更新：nayin_quxiang.json 已在 narrate.py 接线（只作旁证展示、不计格不评分），
# 从 UNWIRED_CORPORA 摘除——若本门 [8] 再报它 0 命中，说明接线回归，必须立刻修。
UNWIRED_CORPORA = {
    # 当前无未接线语料（nayin_quxiang.json 已落地 2026-10-09f）。
    # 新缺口登记格式："文件名": "接线方案出处 / 待办事项",
}


def _alignment_floor(baseline: dict, fails: list[str], measured: dict,
                     fast: bool = False) -> None:
    """[7] 对齐分下限：加权均分 + 维度绝对命中数，两条各判一次（口径见模块 docstring）。"""
    print("\n[7] 古籍案例对齐分下限（strict 加权均分 + 维度命中数；非现实预测命中率）")
    if fast:
        # 不静默跳过：跳过必须写成「未生效」，否则 --fast 的门长得像全绿的门。
        print("  × 本次带 --fast：**分数下限未跑**，[7] 未生效——"
              "合入前请重跑不带 --fast 的 python dev_tools/check.py")
        return
    splits_ids: dict = {}
    if CASES_FILE.is_file():
        splits_ids = json.loads(CASES_FILE.read_text(encoding="utf-8")).get("splits") or {}
    for split in ("tune", "holdout"):
        ids = splits_ids.get(split) or []
        if not ids:
            # 空集合没有分数，也就无从证明「不低于基线」——如实判红而不是跳过：
            # 否则「删案例来凑绿」这条最省力的路永远是绿的。
            fails.append(f"{split} 分集合为空（n=0）：无分数可与基线比对，"
                         f"禁止用清空案例集的方式过门")
            print(f"  × {split} n=0 → 无法比对基线")
            continue
        eval_file = DISC / "data" / "cases" / f"eval_{split}.json"
        m = eval_metrics(split, eval_file=eval_file, cwd=DISC, model_key=None)
        if m.get("error"):
            fails.append(f"{split} 评测未跑成：{str(m['error'])[:200]}")
            print(f"  × {split} 评测失败：{str(m['error'])[:120]}")
            continue
        avg, n = m.get("avg"), m.get("n")
        floor = baseline[split]
        measured[split] = avg
        ok = avg is not None and avg >= floor - 1e-9
        print(f"  {'√' if ok else '×'} {split} 加权均分 {avg}%（n={n}，基线 ≥{floor:g}）")
        if not ok:
            fails.append(f"{split} 对齐分均分 {avg} 低于基线 {floor}（n={n}；"
                         f"分数是古籍案例对齐分，非预测率——铁律三）")
            continue
        dims = (json.loads(eval_file.read_text(encoding="utf-8")).get("results")
                or {}).get("dims") or {}
        want = DIM_HITS.get(split) or {}
        seen = {k for k, v in dims.items() if v.get("applicable")}
        for dim in sorted(set(want) | seen):
            cell = dims.get(dim) or {}
            full, applicable, rate = cell.get("full"), cell.get("applicable", 0), cell.get("rate")
            if dim in want:
                need = want[dim]
                hit_ok = full is not None and full >= need
                print(f"      · {dim:<13s} 满分 {full}/{applicable}（{rate}%）"
                      f"下限 ≥{need} {'√' if hit_ok else '×'}")
                if not hit_ok:
                    fails.append(f"{split}/{dim} 绝对命中数 {full} 低于下限 {need}"
                                 f"（适用 {applicable} 例）")
            else:
                print(f"      · {dim:<13s} 满分 {full}/{applicable}（{rate}%）"
                      f"—— 本次未设下限；扩样后请把实测命中数登记进 DIM_HITS")

def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="八字科质量门")
    ap.add_argument("--raise", dest="raise_baseline", action="store_true",
                    help="把本次实测 tune/holdout 均分写入本地基线文件（仅在确认改进后使用；"
                         "维度命中数下限 DIM_HITS 不在 --raise 范围内，改它要走代码字面量 + CHANGELOG 登记）")
    ap.add_argument("--fast", action="store_true",
                    help="跳过 [7] 案例评测——**跳过即分数下限不生效**，"
                         "输出里会显式写明「未生效」，不假装通过")
    args = ap.parse_args()
    fails: list[str] = []
    measured: dict[str, float] = {}

    # SKILL.md 的均分硬下限是「登记基线不得被调到 95 以下」的机械兜底：
    # 有人把 BASELINE["tune"] 改小凑绿时，这里先红，不用等分数跑出来。
    if BASELINE["tune"] < AGENTS_TUNE_FLOOR:
        fails.append(f"BASELINE['tune']={BASELINE['tune']} 低于 SKILL.md "
                     f"的 tune 均分硬下限 {AGENTS_TUNE_FLOOR}")

    required = [
        "SKILL.md",
        "scripts/chart.py",
        "scripts/analyze.py",
        "scripts/narrate.py",
        "scripts/render.py",
        "data/verdicts.json",
        "data/tiaohou_quotes.json",
        "data/ditian_sui.json",
        "dev_tools/check.py",
        "dev_tools/golden.py",
        "dev_tools/sync_tiaohou_engine.py",
        "dev_tools/diff_tiaohou_vs_head.py",
        "data/rules/rule_registry.json",
    ]
    for rel in required:
        if not (DISC / rel).exists():
            fails.append(f"缺 {rel}")
    print("[0] 契约文件", "√" if not fails else "×")

    code, out = run(["scripts/chart.py", "--datetime", "1990-05-20 10:30", "--gender", "男", "-o", "scratch/chart.json"])
    if code != 0:
        fails.append("chart 冒烟失败")
        print(out)
    else:
        print("[1] chart 冒烟 √")

    code, out = run(["scripts/analyze.py", "scratch/chart.json", "-o", "scratch/analyze.json"])
    if code != 0:
        fails.append("analyze 冒烟失败")
        print(out)
    else:
        a = json.loads((DISC / "scratch" / "analyze.json").read_text(encoding="utf-8"))
        con = a.get("conclusion") or {}
        # 机械标签允许；禁止「命运吉凶」总断
        if con.get("方向"):
            fails.append("analyze 不应给出命运方向总断")
        for v in con.get("verdicts") or []:
            if not isinstance(v, dict) or not v.get("basis"):
                fails.append("verdicts 须带 basis")
                break
        if not con.get("strength") or not con.get("pattern"):
            fails.append("缺 strength/pattern 机械推演")
        if not con.get("dayun"):
            fails.append("缺 dayun 大运表")
        print("[2] analyze 机械推演 √" if not any("analyze" in f or "verdicts" in f or "strength" in f or "dayun" in f or "方向" in f for f in fails) else "[2] analyze ×")

    code, out = run(["scripts/narrate.py", "scratch/analyze.json"])
    if code != 0 or "不是命运断言" not in out:
        fails.append("narrate 应声明非命运断言")
        print(out)
    else:
        print("[3] narrate 口径声明 √")

    code, out = run(["dev_tools/golden.py", "verify"])
    if code != 0:
        fails.append("金标准指纹漂移")
        print(out)
    else:
        # 空跑必须判红：壳退 0 但没交出「用例 N 条／机械 <16hex>／措辞 <16hex>」三件，
        # 或 N=0，都不算通过——否则"看门狗没跑到"与"跑过且一致"在报表上长得一模一样。
        m_n = re.search(r"用例 (\d+) 条", out)
        m_mech = re.search(r"机械 ([0-9a-f]{16})", out)
        m_word = re.search(r"措辞 ([0-9a-f]{16})", out)
        if not (m_n and m_mech and m_word):
            fails.append("金标准壳输出形状不完整（rc=0 但缺 用例/机械/措辞 行）＝不当作通过")
            print(out)
        elif int(m_n.group(1)) == 0:
            fails.append("金标准跑了 0 例＝空跑，不判通过")
            print(out)
        else:
            print(f"[4] 金标准 √ 用例 {m_n.group(1)} 条／机械 {m_mech.group(1)}／措辞 {m_word.group(1)}")

    code, out = run(["dev_tools/regression.py"])
    if code != 0:
        fails.append("机械因子回归失败")
        print(out)
    else:
        print("[5] 机械回归 √", out.strip().splitlines()[-1] if out.strip() else "")

    # 评测器存在性 + 框架自检（八字科评测是新立的尺子，必须校准）；分数下限见 [7]
    if not (DISC / "scripts" / "evaluate.py").is_file():
        fails.append("缺 scripts/evaluate.py（八字科评测器）")
        print("[6] 评测器 ×")
    else:
        code, out = run(["dev_tools/eval_selftest.py"])
        if code != 0:
            fails.append("评测框架自检失败")
            print(out)
        else:
            print("[6] 评测框架自检 √", out.strip().splitlines()[-2]
                  if len(out.strip().splitlines()) > 1 else "")
        # tune / holdout：分数下限门（只准前进不准后退；口径见模块 docstring）
        _alignment_floor(_effective_baseline(), fails, measured, fast=args.fast)

    # [8] 语料接线：data/*.json 每个语料文件都必须真的被报告消费（否则是死语料）。
    # 叶子长度阈值曾取 12——nayin_quxiang.json 全库叶子 <12 字，整份文件被
    # `if not leaves: continue` 静默跳过，「死语料必判红」的门对它完全无感（2026-10-09 修）。
    # 现在：非空即判、0 命中即红，唯一例外是 UNWIRED_CORPORA 里**点名登记**的缺口，
    # 且登记表里的文件一旦接上反而判红（防豁免清单烂掉）。
    # 第一百一十七批口径变更（§四.4 已登记）：接线判定的比对面从「一盘 narrate 输出」
    # 改为「eval_all 全部盘的 narrate 并集」。旧口径读数（单盘）：ditian_sui 17/136、
    # liushen_image 7/35、nayin_quxiang 12/182、shi_shen_actions 14/29、tiaohou_quotes 2/302、
    # verdicts 13/90 —— 这些数的分母接近单盘天花板，**与新读数不可比**，历史条目里的旧数不改写。
    code, out = run(["dev_tools/corpus_reports.py"])
    cpath = DISC / "scratch" / "corpus_reports.txt"
    corpus = cpath.read_text(encoding="utf-8") if (code == 0 and cpath.exists()) else ""
    if not corpus:
        fails.append("多盘并集未生成（dev_tools/corpus_reports.py 跑不通）——接线门不许退回单盘口径")
        print("[8] 语料接线 ×")
        out = ""
    else:
        out = corpus
    if code != 0 or not corpus:
        pass
    else:
        bad = []
        for path in sorted((DISC / "data").glob("*.json")):
            obj = json.loads(path.read_text(encoding="utf-8"))
            leaves = [s for s in _leaf_strings(obj) if len(s) >= MIN_LEAF_LEN]
            if not leaves:
                fails.append(f"{path.name}：过滤后 0 条叶子串（MIN_LEAF_LEN={MIN_LEAF_LEN} "
                             f"或整份是非文本表）——接线门看不见它，必须显式处理")
                print(f"[8] 语料接线 × {path.name}：无可比对叶子串")
                continue
            # 接线判定看「这条语料的内容有没有进报告」，不是看字节是否完全相同：
            # tiaohou_quotes 的引文是按句切下来的片段，741 条里 82 条以「，」起头，
            # narrate 表示层会 lstrip 掉切片残留（语料本身逐字不动，生成器有重算比对）。
            # 早先只比字节，于是那次纯粹的显示修复把读数从 2/302 报成 1/302——
            # 量的是"没接线"，实际是"接了但首字标点被规范化"。
            hit = sum(1 for s in leaves
                      if s in out or s.lstrip("，、。；：") in out)
            declared = UNWIRED_CORPORA.get(path.name)
            if declared:
                if hit:
                    fails.append(f"{path.name}：已进报告 {hit}/{len(leaves)} 条，"
                                 f"却仍挂在 UNWIRED_CORPORA 豁免表里——请摘掉（登记理由：{declared}）")
                    print(f"[8] 语料接线 × {path.name}：豁免表条目已过期")
                else:
                    print(f"[8] 语料接线 · {path.name}：0/{len(leaves)} 条进报告"
                          f"——已登记缺口，不判红（{declared}）")
                continue
            if hit == 0:
                bad.append(f"{path.name}：{len(leaves)} 条语料一条未进 276 盘报告并集（接线缺失）")
            else:
                print(f"[8] 语料接线 √ {path.name}：{hit}/{len(leaves)} 条进入多盘报告并集")
        code2, out2 = run(["dev_tools/corpus_wiring_report.py"])
        for line in out2.splitlines():          # 归类只作明细，不改变判定：判定仍看「0 命中即红」
            if line.strip():
                print("  " + line.strip())
        if bad:
            fails.extend(bad)
            for b in bad:
                print(f"[8] 语料接线 × {b}")

    # [9] 静态表 ↔ data 层同步（SKILL.md：不同源就必须有挂线的同步门，不靠自觉）
    code, out = run(["dev_tools/sync_tiaohou_engine.py", "--check"])
    if code != 0:
        fails.append("TIAO_HOU 引擎表与 data/tiaohou_quotes.json 不同源"
                     f"（跑 dev_tools/sync_tiaohou_engine.py 同步，不要手改表）：{out.strip()[:200]}")
        print("[9] 调候表同步 ×")
        print(out.strip()[-800:])
    else:
        print("[9] 调候表同步 √", out.strip())

    # [10] 参考文档「源L 行号 + 逐字引文」回验。
    # 此前 references/*.md 写着「可经 python tools/check_source_readings.py 回验」，
    # 而 tools/ 与 docs/source-readings/ 已随扁平化删除——声明指向不存在的能力，
    # 且这些行号引文此后再没有任何东西校验过。首轮实跑抓出两处真错并已修：
    #   · bazi_yue_shi_ge.md 标「源L263 逐字」却把底本第二、三从句调换顺序；
    #   · 同文标「源L307」的《考原》段实际在 L305（L307 是另一个算例）。
    print("\n[10] 书证行号逐字回验")
    code, out = run(["dev_tools/check_source_readings.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("参考文档的「源L 逐字」声明与底本不符（或回验器负例失效）")

    # [11]-[13] 引用完整性 / 书源指针 / 案例库隔离（本轮清出的活断链全靠人读出来，
    # 写进散文的门等于没跑，故一律接进本门）。
    for title, script in (
            ("[11] 文档活引用可达性（指向不存在文件的指针）", "dev_tools/check_doc_refs.py"),
            ("[12] 规则注册表书源指针回验（verified 不许自说自话）", "dev_tools/check_rule_registry.py"),
            ("[13] 案例库隔离（解读路径不得触达 data/cases）", "dev_tools/check_case_isolation.py")):
        print(f"\n{title}")
        code, out = run([script, "--selftest"])
        for line in out.splitlines():
            if line.strip():
                print("  " + line.strip())
        if code != 0:
            fails.append(f"{title} 未通过")

    print("\n[14] 纳音取象表 data↔内核同步")
    code, out = run(["dev_tools/sync_nayin_engine.py", "--check", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("NAYIN_XIANGGE 与 data/nayin_quxiang.json 不同源"
                     "（同步方向 data→代码：跑 dev_tools/sync_nayin_engine.py --emit 取字面量，"
                     "不要手改 data 迁就读数）")

    print("\n[15] 评测维度 ↔ 报告面同名同义（EVAL-PLAN §六 / 步 7）")
    code, out = run(["dev_tools/check_dim_surface.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("计分维度与报告章节两侧不一致（维度没落点，或小节既没评又没登记理由）")

    # [16] 断语外置（重建历史上 tools/verdict_audit.py 的等价物；登记于 docs/CHANGELOG.md 第三/五批）
    code, out = run(["dev_tools/verdict_audit.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("报告出现无外置出处的判断措辞（或本器负例失效／一行都没检视）")
    else:
        print("[16] 断语外置 √")

    # [17] 命例基准自洽：书载四柱（note/pillars_raw）必须等于内核按 datetime 反算的四柱
    code, out = run(["dev_tools/check_case_pillars.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("命例基准不自洽（书载四柱与内核反算不符，或本器负例失效／一例都没对账）")
    else:
        print("[17] 命例基准自洽 √")

    # [18] 行运见证集回验：逐字回底本＋五虎遁自洽＋运序连续＋方向唯一（#31③ 的书据材料）
    code, out = run(["dev_tools/check_dayun_cases.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("行运见证集不自洽（引文不在源行／月柱不符五虎遁／运序不连续／顺逆不唯一，"
                     "或本器负例失效、一例都没检视）")
    else:
        print("[18] 行运见证集回验 √")

    # [19] 藏干独立出处（#14(1)）：书中所写藏干须逐条见于内核表，可核支数 <4 即判红（防空跑）
    code, out = run(["dev_tools/check_hidden_stems.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("藏干出处不自洽（书有而表无＝按书改表或登记分歧；或可核支数不足、负例失效）")
    else:
        print("[19] 藏干独立出处回验 √")

    # [20] 排盘入参历法自洽（#14(3)）：五虎遁·五鼠遁**不看日期**，只给结构化四柱的 116 例从此有账
    code, out = run(["dev_tools/check_pillar_laws.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("排盘入参历法不自洽（新违律未登记／可检 0 例＝空跑／负例失效／豁免条目失效未删）")
    else:
        print("[20] 排盘入参历法自洽 √")

    # [21] 现实反馈通道（#32）：内核登记与孪生副本一致／负例有牙齿／在册记录合 canonical／空库须说空话
    code, out = run(["dev_tools/check_feedback.py"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("现实反馈通道回验未过（内核未登记／两副本漂移／负例失效／在册记录不合 schema）")
    else:
        print("[21] 现实反馈通道回验 √")

    # [22] 案例考点查重（#39）：台账在册的历史重复不判红，台账之外点名到 id 判红——
    # 同一考点被计两次以上时，考卷分母与权重都不再是"多少条规则"。
    code, out = run(["dev_tools/check_case_dupes.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("案例考点查重未过（台账之外有重复／台账缺失＝无从分辨新旧／负例失效／空跑）")
    else:
        print("[22] 案例考点查重 √")

    # [23] 输出确定性（#40）：三个 hash seed 下金标准 digest 必须全同＋静态层无集合直接 join
    # ——这类缺陷的特征是单次运行永远自洽，只在换进程时才变。
    code, out = run(["dev_tools/check_determinism.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("输出确定性未过（跨进程 digest 分歧／静态层命中／夹具 0 文件＝没扫／金标准没交形状）")
    else:
        print("[23] 输出确定性 √")

    # [24] CLI 编码红线：以 cp936 起子进程跑各 argparse 中文入口的 --help，
    # 产物字节必须可按 UTF-8 读出中文——守卫写了但位置不对（早于 import sys）也照样被抓。
    code, out = run(["dev_tools/check_cli_encoding.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("CLI 编码红线未过（产物出现 GBK 字节／入口跑挂／零入口可扫＝没跑）")
    else:
        print("[24] CLI 编码红线 √")

    # [25] 维度适用数锁：受控空档维度（shensha/dayun）的「带期望例数」必须与登记逐格相等。
    # 双向判红：多了＝§三.4 禁止的引擎反推回填（读数当场自证），少了＝回填静默丢失
    # （第一百六十八批：214 例回填丢失而均分四舍五入后不动）。解锁唯一通道 =
    # 改 check_dim_lock.py 的 LOCK 字面量（进 git diff）+ docs/CHANGELOG.md 登记书证。
    code, out = run(["dev_tools/check_dim_lock.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("维度适用数锁未过（登记外回填／回填静默丢失／LOCK 维度名拼错）")
    else:
        print("[25] 维度适用数锁 √")

    # [26] 正则字符类 list 展平审计（AGENTS §二 硬规矩核对版，第两百零九批）：
    # 内核 HEAVENLY_STEMS/EARTHLY_BRANCHES 是 list，`[%s] % 列表` 静默全盲无报错。
    code, out = run(["dev_tools/check_regex_lists.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("正则字符类 list 展平审计未过（负例无牙／本科存在直插违规）")
    else:
        print("[26] 正则字符类 list 展平审计 √")

    # [27] §三 house 规矩核对版（第两百一十一批）：版本号文件名/绝对用户路径/scratch/产物四判据，
    # tracked 口径；selftest 含注入负例与门不自咬（本器反例串豁免自身）。
    code, out = run(["dev_tools/check_house_conventions.py", "--selftest"])
    for line in out.splitlines():
        if line.strip():
            print("  " + line.strip())
    if code != 0:
        fails.append("§三 house 规矩核对未过")
    else:
        print("[27] §三 house 规矩核对 √")

    if ENC_WITNESS:
        fails.extend("产物编码退化：" + w for w in ENC_WITNESS)
    if fails:
        print("失败：", *fails, sep="\n  ")
        return 1

    if args.raise_baseline:
        if measured:
            # 241 批修：合并基取 _effective_baseline()（含盘上抬过的覆盖）非字面默认——
            # 旧形在 --fast 部分跑时把未测键的覆盖整段丢弃（读守卫防"写低"防不了"删键"）。
            new = dict(_effective_baseline())
            new.update(measured)
            BASELINE_FILE.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n",
                                     encoding="utf-8")
            print(f"基线已登记 → {BASELINE_FILE}")
            print(json.dumps(new, ensure_ascii=False))
            print("注：维度命中数下限（DIM_HITS）不在 --raise 范围，改它要走代码字面量 + "
                  "docs/CHANGELOG.md 登记（§四.4 口径变更必须写明）。")
        else:
            print("× 本次未取到任何对齐分，拒绝登记基线")
            return 1

    print("八字科质量门通过。")
    print("分数含义：与古籍案例要点的一致性，不代表现实预测命中率（SKILL.md 铁律三）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
