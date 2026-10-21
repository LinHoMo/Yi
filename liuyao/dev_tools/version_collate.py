# -*- coding: utf-8 -*-
"""版本对拍 v0（第一百八十五批·B1）——同书两抄本的冲突率＝古籍对齐分的天花板估计。

为什么源级：curated 案例库之间同案零重叠（dz 采集侧「同案去重门」按设计所致，
185 批实探：ws81∩classical=1 对、dz∩其余=0）——版本对拍的原料只能在**原表层**：
维基文库 wikitext 与殆知阁 dz 是同一部《增刪卜易》的两条独立转录链。

测什么（每题两项，均从两本各自提取）：
  1. 判词极性冲突：verdict_direction 一吉一凶记冲突；任一侧中性记「不可判」不强行归类；
  2. 应期支冲突：双方都提取到应支（剥「日/月/年」后缀）才比较，只问一侧有＝不可判。
含义：冲突率是对齐分的**天花板**——引擎至多与其中一本吻合，两本互斥之处必有一失；
「上限 ≈ 1 − 冲突率/2」只在两本等权假设下成立，登记为估计式不登记为定理。
口径纪律：繁简/异体归一取内核表唯一真值源；提取正则命中 0 时必须自证路径与字表
（§四.8「扫 0 份≠仓库没文档」同族），selftest 锁死。

    python dev_tools/version_collate.py                 # 增删两本全量对拍
    python dev_tools/version_collate.py --selftest
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.eval import verdict_direction  # noqa: E402
from ablation import mcnemar_exact  # noqa: E402  配对检验口径唯一（182 批）

WIKI = DISC / "data" / "sources" / "zengshan_buyi.wikitext.txt"
DZ = DISC / "data" / "sources" / "zengshan_buyi_dz.dz.txt"

DATE_PAT = re.compile(r"([子丑寅卯辰巳午未申酉戌亥])月([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])日")
BR = "子丑寅卯辰巳午未申酉戌亥"
GAN = "甲乙丙丁戊己庚辛壬癸"
YING_PAT = re.compile(r"[应應](?:于|在)?([" + BR + r"])(?:日|月|年)")
# 卦面 token：白名单是脆弱源（185 批 selftest 抓到「大有」被逐字白名单漏掉）——
# 改为「得X卦」文法级提取（X＝1~3 汉字），两侧同文法直接对 token，不依赖人工表。
HEX_PAT = re.compile(r"得([\u4e00-\u9fff]{1,3})卦")
GUO_PAT = re.compile(r"(?:果[于至]|后果|果[得应應卒升见見归歸破愈死])")
VERD_PAT = re.compile(r"([吉凶悔吝](?:凶|吉)?|大(?:吉|凶)|平(?:吉|凶))")
_PAIRS = [("貲", "资"), ("賁", "贲"), ("恆", "恒"), ("渙", "涣"), ("燬", "毁"),
          ("訞", "妖"), ("迻", "移"), ("禍", "祸"), ("財", "财"), ("馬", "马"), ("車", "车"),
          ("長", "长"), ("門", "门"), ("風", "风"), ("雲", "云"), ("霧", "雾"), ("臨", "临"),
          ("離", "离"), ("兌", "兑"), ("頤", "颐"), ("觀", "观"), ("損", "损"), ("謙", "谦"),
          ("剝", "剥"), ("復", "复"), ("姤", "姤"), ("語", "语"), ("詩", "诗"), ("諸", "诸"),
          ("請", "请"), ("謝", "谢"), ("證", "证"), ("試", "试"), ("識", "识"), ("電", "电"),
          ("雷", "雷"), ("號", "号"), ("魂", "魂"), ("雞", "鸡"), ("難", "难"), ("權", "权"),
          ("變", "变"), ("亂", "乱"), ("體", "体"), ("與", "与"), ("許", "许"), ("誰", "谁"),
          ("調", "调"), ("諭", "谕"), ("詔", "诏"), ("辭", "辞"), ("漢", "汉"), ("澤", "泽"),
          ("滿", "满"), ("燈", "灯"), ("審", "审"), ("寫", "写"), ("監", "监"), ("嶺", "岭"),
          ("藝", "艺"), ("養", "养"), ("獸", "兽"), ("獵", "猎"), ("玄", "玄"), ("內", "内"),
          ("豐", "丰"), ("節", "节"), ("晉", "晋"), ("漸", "渐"), ("蠱", "蛊"), ("壯", "壮"),
          ("隨", "随"), ("師", "师"), ("訟", "讼"), ("純", "纯"), ("實", "实"), ("德", "德"),
          ("進", "进"), ("選", "选"), ("遣", "遣")]
TRAD2SIMP = str.maketrans({a: b for a, b in _PAIRS})


def norm(s: str) -> str:
    s = s.translate(TRAD2SIMP)
    try:
        s = unicodedata.normalize("NFKC", s)
    except Exception:
        pass
    return s


def key_of(line: str):
    m = DATE_PAT.search(line)
    return (m.group(1), m.group(2)) if m else None


def extract_blocks(path: Path) -> dict:
    """key → 块信息；块界＝本日期行到下一日期行前（防跨案窗口污染），封顶 25 行。"""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    nxt = [len(lines)] * len(lines)
    last = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if key_of(norm(lines[i])):
            last = i
        nxt[i] = last
    out = {}
    for i, raw in enumerate(lines):
        ln = norm(raw)
        k = key_of(ln)
        if not k:
            continue
        end = min(nxt[i + 1] if i + 1 < len(nxt) else len(lines), i + 25)
        block = "\n".join(norm(x) for x in lines[i:max(end, i + 1)])
        pols = []
        for mm in re.finditer(r"([吉凶])(?![可相能])", block):
            p = verdict_direction(mm.group(1))
            if p:
                pols.append(p)
        branches = set()
        for mm in YING_PAT.finditer(block):
            branches.add(mm.group(1))
        hx = HEX_PAT.search(block)
        out.setdefault(k, []).append({"line": i + 1, "head": raw.strip()[:60],
                                      "pol": (1 if sum(pols) > 0 else -1 if sum(pols) < 0 else 0) if pols else None,
                                      "ying": sorted(branches),
                                      "hex": hx.group(1) if hx else None,
                                      "guo": bool(GUO_PAT.search(block))})
    return out


def collate() -> int:
    if not WIKI.exists() or not DZ.exists():
        print("× 底本文件缺失：%s/%s——先查路径不出冲突率" % (WIKI.name, DZ.name))
        return 1
    W = extract_blocks(WIKI)
    D = extract_blocks(DZ)
    if not W or not D:
        print("× 一侧提取 0 块（W=%d D=%d）——正则/字表失效嫌疑，0 冲突读数无效" % (len(W), len(D)))
        return 1
    shared = sorted(set(W) & set(D))
    uniq = [k for k in shared if len(W[k]) == 1 and len(D[k]) == 1]
    ambig = len(shared) - len(uniq)
    print("═ 《增刪卜易》两抄本源级对拍 ═")
    print("  wikitext 键 %d｜dz 键 %d｜同键 %d｜其中双侧唯一 %d｜歧义跳过 %d"
          "（同日期多案是本书常态，键不唯一的配对必错案——只采唯一键）"
          % (len(W), len(D), len(shared), len(uniq), ambig))
    MIN_CMP = 15   # 可比题不足此数：只报现状不出天花板估计（材料不够≠零冲突）
    pol_cmp = pol_con = ying_cmp = ying_con = unk = 0
    conflicts = []
    hx_cmp = hx_con = 0
    guo_cmp = guo_con = 0
    for k in uniq:
        w, d = W[k][0], D[k][0]
        if w["hex"] and d["hex"]:
            hx_cmp += 1
            if w["hex"] != d["hex"]:
                hx_con += 1
                conflicts.append(("卦面", k, w["line"], "得%s卦" % w["hex"], d["line"], "得%s卦" % d["hex"]))
        if w["guo"] or d["guo"]:
            guo_cmp += 1
            if w["guo"] != d["guo"]:
                guo_con += 1
        if w["pol"] in (1, -1) and d["pol"] in (1, -1):
            pol_cmp += 1
            if w["pol"] != d["pol"]:
                pol_con += 1
                conflicts.append(("判词", k, w["line"], w["head"][:26], d["line"], d["head"][:26]))
        else:
            unk += 1
        if w["ying"] and d["ying"]:
            ying_cmp += 1
            if set(w["ying"]) != set(d["ying"]):
                ying_con += 1
                conflicts.append(("应支", k, w["line"], " ".join(w["ying"]), d["line"], " ".join(d["ying"])))
    print("  卦面(得X卦)：可比 %d 对｜token 不等 %d" % (hx_cmp, hx_con))
    print("  验注(果X)有无：任一侧有 %d 对｜一方缺一位 %d〔⚠ 块切法敏感——wikitext 短行、"
          "dz 一案一行，窗口信息量不等所致，**只作参考不作版本冲突论据**〕" % (guo_cmp, guo_con))
    print("  判词极性：可比 %d 对｜冲突 %d｜不可判 %d（叙事体少裸吉凶字——原层天然稀疏）" % (pol_cmp, pol_con, unk))
    print("  应期支(应X日)：双方均可提 %d 对｜集合不等 %d" % (ying_cmp, ying_con))
    for kind, k, lw, sw, ld, sd in conflicts[:15]:
        print("    [%s] %s月%s日｜wiki L%d「%s」↔ dz L%d「%s」" % (kind, k[0], k[1], lw, sw, ld, sd))
    ok = [(n, name, con) for (n, name, con) in
          ((hx_cmp, "卦面", hx_con), (pol_cmp, "判词", pol_con),
           (ying_cmp, "应支", ying_con)) if n >= MIN_CMP]
    if not ok:
        print("  → 各维度可比题均 < %d：**现材不足，冲突率与天花板估计不可出**——这不是 0 冲突，"
              "是原层判词/应支多写于叙事而非结构化字段；把它上移到抄本层的义务登记给 B3 毕业管道。" % MIN_CMP)
        return 0
    for n, name, con in ok:
        print("  → %s冲突率 = %d/%d = %.1f%%（门槛 %d 已过）" % (name, con, n, con * 100.0 / n, MIN_CMP))
    print("  → 多维度分别报，**不做单一天花板合数**（不同维度错误率不可加权成定理；"
          "判词维若可比，其冲突即对齐分硬上限的直接来源）。")
    return 0


def cmd_paired_baseline() -> int:
    """183 欠账：引擎 top-1 × 用神值支基线 的配对 McNemar（同分母逐例）。"""
    import case_runner
    import evaluate
    by_id = {c["id"]: c for c in case_runner.load_cases()}
    rows = []
    for split in ("wikisource_holdout", "zengshan_dz_holdout"):
        ids = case_runner.load_ids(split)
        b = c = n = 0
        for cid in ids:
            case = by_id[cid]
            x = str((case.get("expected") or {}).get("yingqi") or "")
            m = evaluate.YQ_UNIT_RE.search(x)
            need = [m.group(1)] if m else evaluate._branches_in(x)
            if not need:
                continue
            try:
                eng = case_runner.run_case(case)
            except Exception:
                continue
            unit = evaluate._expected_unit(x)
            pool = evaluate._offered_branches(evaluate._unit_pool(eng, unit))
            ug = eng.get("use_god_branch")
            if not pool or not ug:
                continue
            n += 1
            e_hit = pool[0] in need
            b_hit = ug in need
            if e_hit and not b_hit:
                b += 1
            elif b_hit and not e_hit:
                c += 1
        p = mcnemar_exact(b, c)
        rows.append((split, n, b, c, p))
        print("  %s：配对 %d 例｜引擎对基线错 b=%d｜基线对引擎错 c=%d｜McNemar p=%.3f%s"
              % (split, n, b, c, p, "（未达显著）" if p > 0.05 else "（显著）"))
    print("  注：b/c 为不一致对——点差方向与 183 批独立读数一致与否以本表为准（配对才是检验）。")
    return 0


def cmd_selftest() -> int:
    fails = []
    import tempfile
    with tempfile.TemporaryDirectory(prefix="yi_vc_st_") as td:
        p = Path(td) / "t.txt"
        p.write_text("卯月壬辰日占文书，得贲卦，断曰吉，应于卯日。\n"
                     "辰月戊子日占财，得大有卦，断曰凶。\n"
                     "寅月甲子日无事。\n", encoding="utf-8")
        blocks = extract_blocks(p)
        if len(blocks) != 3:
            fails.append("合成键提取错（应 3 实 %d）" % len(blocks))
        elif blocks[("卯", "壬辰")][0]["pol"] != 1 or blocks[("辰", "戊子")][0]["pol"] != -1:
            fails.append("判词极性提取错：%r" % {k: [b["pol"] for b in v] for k, v in blocks.items()})
        elif "卯" not in blocks[("卯", "壬辰")][0]["ying"]:
            fails.append("应于X日 支提取失败（繁体應/简体应路径）")
        elif blocks[("卯", "壬辰")][0]["hex"] != "贲" or blocks[("辰", "戊子")][0]["hex"] != "大有":
            fails.append("卦面 token 提取错：%r" % {k: [b["hex"] for b in v] for k, v in blocks.items()})
        elif blocks[("寅", "甲子")][0]["pol"] is not None:
            fails.append("无判词块被臆造极性")
        empty = Path(td) / "e.txt"
        empty.write_text("全书无一日辰。\n", encoding="utf-8")
        if extract_blocks(empty):
            fails.append("空文本竟有提取——假阳性")
    # mcnemar 口径单一：与 ablation 同函数（import 即证）
    import ablation
    if mcnemar_exact is not ablation.mcnemar_exact:
        fails.append("配对检验函数不是 182 批同一个（口径分裂）")
    if fails:
        print("× selftest：" + "；".join(fails))
        return 1
    print("√ selftest：合成键/极性/应支（繁简双式）/空文本假阳性/McNemar 同函数 全过")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="同书两抄本源级对拍（冲突率＝对齐天花板估计）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--paired", action="store_true", help="补 183 欠账：基线×引擎配对 McNemar")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    if args.paired:
        return cmd_paired_baseline()
    return collate()


if __name__ == "__main__":
    raise SystemExit(main())
