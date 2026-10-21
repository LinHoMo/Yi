# -*- coding: utf-8 -*-
"""读数对账台（第两百批·防御性维护）——登记值 vs 当前 HEAD 重放值，逐位核对。

176→199 批把二十余个关键读数写散在 CHANGELOG/README/CAPABILITY 里。凡散落的数字，
终有一天和产生它的代码分家（§六.3 的时延版）。本器把**每个对外声称的读数**做成可重放
断言：expected 逐字来自登记文本（注明批次），actual 由当前 HEAD 现场重跑取回。

    python dev_tools/readout_ledger.py --quick   # 快组（纯文本/装配/小扫描，秒级~2min）
    python dev_tools/readout_ledger.py           # 全量（含两科评测与外部集，十分钟级）
    python dev_tools/readout_ledger.py --selftest

对账失败＝读数已与代码分家：要么改代码前偷动了读数（缺陷），要么登记文本过期（§六.2）——
两种都必须立案，不许静默刷新基线。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
ROOT = DISC.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402


def sh(args, cwd=None):
    r = subprocess.run([sys.executable, "-X", "utf8"] + args,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(cwd or DISC))
    return (r.stdout or "") + (r.stderr or "")


def grab(text, pat, group=1):
    m = re.search(pat, text)
    return m.group(group) if m else None


# ── 读数账目：id -> (登记出处, 取数函数, 比对) ──────────────────────────────
def checks():
    out = []

    def add(cid, src, fn, expect):
        out.append((cid, src, fn, expect))

    # --- 六爻内部集 ---
    def c_tune(t):
        s = sh(["scripts/evaluate.py", "--split", "tune"])
        return (grab(s, r"平均分 = ([0-9.]+)%.*n=20"),
                grab(s, r"strict top-1 命中 ([0-9.]+)%"),
                grab(s, r"平均排在第 ([0-9.]+) 位"))
    add("liuyao.tune(97.9/64.7/1.53)", "README 表/172批", c_tune,
        ("97.9", "64.7", "1.53"))

    def c_holdout(t):
        s = sh(["scripts/evaluate.py", "--split", "holdout"])
        return (grab(s, r"平均分 = ([0-9.]+)%"),
                grab(s, r"strict top-1 命中 ([0-9.]+)%"),
                grab(s, r"平均排在第 ([0-9.]+) 位"))
    add("liuyao.holdout(90.2/50.0/1.6)", "README 表", c_holdout,
        ("90.2", "50.0", "1.6"))

    # --- 外部集 ---
    def c_wiki(t):
        s = sh(["scripts/evaluate.py", "--split", "wikisource_holdout"])
        return (grab(s, r"平均分 = ([0-9.]+)%"), grab(s, r"strict top-1 命中 ([0-9.]+)%"),
                grab(s, r"平均排在第 ([0-9.]+) 位"))
    add("liuyao.wikisource(62.4/27.3/2.19)", "README 表/181批", c_wiki,
        ("62.4", "27.3", "2.19"))

    def c_dz(t):
        s = sh(["scripts/evaluate.py", "--split", "zengshan_dz_holdout"])
        return (grab(s, r"平均分 = ([0-9.]+)%"), grab(s, r"strict top-1 命中 ([0-9.]+)%"))
    add("liuyao.zengshan_dz(53.4/33.3)", "README 表", c_dz, ("53.4", "33.3"))

    def c_window2(t):
        s = sh(["dev_tools/window_report.py"])
        blk = s.split("═ zengshan_dz_holdout")[0]
        # 实际格式是编号行「  1   12/44 =  27.3%」（200 批立案教训：模式抄实样非凭印象）
        t1 = re.search(r"^\s+1\s+(\d+)/(\d+) =\s*([\d.]+)%", blk, re.M)
        t3 = re.search(r"^\s+3\s+(\d+)/(\d+) =\s*([\d.]+)%", blk, re.M)
        return ((t1.group(3), t3.group(3)) if t1 and t3 else (None, None))
    add("liuyao.wiki top1/top3(27.3/52.3)", "181/199批", c_window2, ("27.3", "52.3"))

    def c_baselines(t):
        s = sh(["dev_tools/baselines.py"])
        yong = re.search(r"用神值支\s+(\d+)/\s*\d+ =\s*([\d.]+)%", s)
        day = re.search(r"日辰即答\s+(\d+)/\s*\d+ =\s*([\d.]+)%", s)
        return ((yong.group(2), day.group(2)) if yong and day else (None, None))
    add("liuyao.baselines 用神18.2/日辰4.5", "183批", c_baselines, ("18.2", "4.5"))

    # --- 版本对拍/毕业/分诊（JSON 直读 + 现场重生成核对） ---
    add("liuyao.collate(卦面0/47 判词1/37)", "185批", lambda t: _collate_now(), ("0/47", "1/37"))
    add("liuyao.graduation(18/63/161)", "189批", lambda t: _json_counts(
        "data/cases/verifications_graduation.json", "summary",
        ("restorable", "partial_needs_human", "unrestorable")), ("18", "63", "161"))
    add("liuyao.triage(15/35/B兜底5/真分歧8)", "199批（202 批 B 路细分，附理由改期望）", lambda t: _json_counts(
        "data/cases/verifications_triage.json", None,
        ("A_有验支候选", "A_无验支结案候选", "B_异写候选", "B_真分歧需人"), key="buckets"),
        ("15", "35", "5", "8"))
    add("liuyao.restorable_recheck(共识10/分歧8)", "201批", lambda t: _json_counts(
        "data/cases/restorable_recheck.json", None, ("consensus", "needs_human")), ("10", "8"))
    add("liuyao.draft_candidates(10含dup4)", "204批", lambda t: _draft_counts(), ("10", "4"))

    # --- 裁决表/治理图/指纹 ---
    add("liuyao.adjudications(7=5+1+1)", "188批", lambda t: _adjud_counts(), ("7", "5", "1", "1"))
    add("liuyao.golden(b716/a46f)", "193批", lambda t: _golden("liuyao"),
        ("b7162bfc99e2cce8", "a46f7374276a17a6"))
    add("bazi.golden(2a4c/1a0f)", "176批前", lambda t: _golden("bazi"),
        ("2a4c9258d6c1e4cb", "1a0f165ebfa7b6da"))
    add("governance(57/36, blk 24/25)", "194批（244 批更新：六爻加 raise 回归守卫；230 批曾加体检器 55→56）", lambda t: _gov_counts(), ("57", "36", "24", "25"))

    # 案例分母（234 批）：账台钉率也钉分母——删/添一例而率恰不动时，分母行会红。
    def c_case_denoms(t):
        sp = json.loads((DISC / "data" / "cases" / "case_splits.json").read_text(encoding="utf-8"))
        cl = json.loads((DISC / "data" / "cases" / "classical_cases.json").read_text(encoding="utf-8"))
        n_cl = cl.get("cases") if isinstance(cl, dict) else cl
        return tuple(map(str, (len(n_cl if n_cl else cl),
                                len(sp["tune"]), len(sp["holdout"]),
                                len(sp["wikisource_holdout"]), len(sp["wikisource_direction"]),
                                len(sp["zengshan_dz_holdout"]))))
    add("六爻案例分母(44/20/12/50/31/21)", "234批（率与分母并钉）", c_case_denoms,
        ("44", "20", "12", "50", "31", "21"))

    def c_bazi_denoms(t):
        cc = json.loads((ROOT / "bazi" / "data" / "cases" / "bazi_classical_cases.json")
                        .read_text(encoding="utf-8"))["cases"]
        ex = json.loads((ROOT / "bazi" / "data" / "cases" / "bazi_external_cases.json")
                        .read_text(encoding="utf-8"))
        from collections import Counter
        c = Counter(x.get("split") for x in cc)
        return (str(c["tune"]), str(c["holdout"]), str(len(ex.get("cases") or ex)))
    add("八字案例分母(60/278/53)", "234批", c_bazi_denoms, ("60", "278", "53"))

    # 头牌值在位性（235 批）：现状文档（README×2/CAPABILITY/GOVERNANCE）必须各含每个
    # 主读数**至少一处**——文档被改回旧值（176 批 97.3 事故族）时现值消失即红。
    # 不查"旧值不得出现"：更正记录合法引用旧值，absence 判据在该域机械不可分（235 探针实证）。
    def c_headline_present(t):
        docs = [(ROOT / x).read_text(encoding="utf-8") for x in
                ("liuyao/README.md", "bazi/README.md", "CAPABILITY.md", "GOVERNANCE.md")]
        heads = ("97.9", "90.2", "62.4", "27.3", "33.3", "52.3", "97.6", "96.2", "80.6")
        gone = [h for h in heads if not any(h in d for d in docs)]
        return f"{len(heads) - len(gone)}/{len(heads)}" + ("" if not gone else " 缺:" + ",".join(gone))
    add("头牌值在位(9/9)", "235批（176 事故族的正向断言）", c_headline_present, ("9/9",))

    # tracked×ignore 漂移（237 批）：任何已跟踪文件不得再命中 ignore 规则（产物规矩的存量面）。
    def c_ignore_drift(t):
        import subprocess as sp
        r = sp.run(["git", "-C", str(ROOT), "ls-files", "-i", "-c", "--exclude-standard"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
        rows = [x for x in (r.stdout or "").splitlines() if x.strip()]
        return str(len(rows))
    add("tracked×ignore 漂移(0)", "237批（236 一次性杂检的常设化）", c_ignore_drift, ("0",))

    # tracked 完整性（238 批）：全库可 UTF-8 解码＋全 tracked JSON 可解析——
    # 各门只读自己那几个文件，从未有全量口径；破损会在最意外的运行时现形。
    def c_tracked_integrity(t):
        import subprocess as sp
        files = sp.run(["git", "-C", str(ROOT), "ls-files", "-z"],
                       capture_output=True).stdout.split(b"\0")
        bd = bj = 0
        for f in filter(None, files):
            p = ROOT / f.decode("utf-8", errors="replace")
            if not p.exists():
                continue
            b = p.read_bytes()
            try:
                b.decode("utf-8")
            except UnicodeDecodeError:
                bd += 1
            if p.suffix == ".json":
                try:
                    json.loads(b.decode("utf-8", errors="replace"))
                except Exception:
                    bj += 1
        return (str(bd), str(bj))
    add("tracked 完整性(解码0/JSON0)", "238批（353 文件 89 JSON 全量口径首立）", c_tracked_integrity, ("0", "0"))

    # 零耦合铁律（§二）的机器化（243 批）——AGENTS「两科禁止任何相互 import」五十批无门。
    # 判据只收 import 图（机械可分）；路径字符串启发式已废——实测唯一命中是 docstring
    # 说明文里的科名（243 探针记录，字符串级误报形态留此供后人不再重蹈）。
    def c_no_cross_import(t):
        import ast as _ast
        n = 0
        for d, other in (("bazi", "liuyao"), ("liuyao", "bazi")):
            for p in (ROOT / d).rglob("*.py"):
                if "__pycache__" in str(p):
                    continue
                try:
                    tree = _ast.parse(p.read_text(encoding="utf-8", errors="replace"))
                except SyntaxError:
                    continue
                for nd in _ast.walk(tree):
                    mods = ([a.name for a in nd.names] if isinstance(nd, _ast.Import)
                            else [nd.module] if isinstance(nd, _ast.ImportFrom) and nd.module else [])
                    n += sum(1 for m in mods if m == other or m.startswith(other + "."))
        return str(n)
    add("两科零耦合 import(0)", "243批（§二铁律五十三批后获断言版）", c_no_cross_import, ("0",))

    # --raise 合并基回归（244 批）：241 病的常设齿（静态双钉＋六爻功能探针，bytes 级自恢复）。
    def c_raise_guard(t):
        r = sh(["dev_tools/check_raise_regression.py"])
        return "PASS" if "全净" in r else (r.strip().splitlines() or ["?"])[-1][:40]
    add("raise 回归守卫(PASS)", "244批（修过的病必须带齿常驻）", c_raise_guard, ("PASS",))

    # 嵌入式 --only 声称的键真实性（249 批）：报错文案/注释里让用户去跑
    # `check.py --only X` 的每一处 X 必须是该科 want 真值源里的真键——
    # 249 全库首扫抓 1 处坏键（fetch_huozhulin 的 selfconsistency，已修 case_selfconsistency）。
    def c_embedded_only_keys(t):
        import re as _re

        def keys_of(dname: str) -> set:
            ck = (ROOT / dname / "dev_tools" / "check.py").read_text(encoding="utf-8")
            return (set(_re.findall(r'want\("([a-z_0-9]+)"\)', ck))
                    | set(_re.findall(r'\("([a-z_0-9]+)",\s*"\[', ck)))
        K = {d: keys_of(d) for d in ("liuyao", "bazi")}
        bad = 0
        for d in ("liuyao", "bazi"):
            for p in (ROOT / d).rglob("*.py"):
                if "__pycache__" in str(p) or p.name == "check.py":
                    continue
                s = p.read_text(encoding="utf-8", errors="replace")
                for m in _re.finditer(r"check\.py[^\n\"']*--only\s+([a-z_0-9,\s]+)", s):
                    for tok in _re.split(r"[,\s]+", m.group(1).strip()):
                        if tok and tok not in K[d]:
                            bad += 1
        return str(bad)
    add("嵌入式 --only 坏键(0)", "249批（报错文案是 Agent 的行动指令，它自己先得可执行）", c_embedded_only_keys, ("0",))

    # 登记×提交在册（254 批·253 事故的结构性反应）：现代史（≥176）每个 changelog
    # 标题批号必须被至少一条提交信息（全信息体、中文或阿拉伯数字形）提及——
    # 防"写了条目没提交"的半个虚构面（72 型虚构若落在 changelog 上，下轮 quick 即红）。
    # 已知具名历史孤儿：221（误编号案：实体在 8275cef 而信息写 212，勘误文本未入任何信息体）。
    def c_registration_orphans(t):
        import re as _re
        import subprocess as _sp
        cn = {"〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9}

        def parse(s):
            tot = num = 0
            for ch in s:
                if ch in cn:
                    num = num * 10 + cn[ch]
                elif ch == "十":
                    tot += (num or 1) * 10; num = 0
                elif ch == "百":
                    tot += (num or 1) * 100; num = 0
                elif ch == "千":
                    tot += (num or 1) * 1000; num = 0
            return tot + num
        heads = set()
        for d in ("liuyao", "bazi"):
            # 读 HEAD 版本而非工作树：巡逻语义＝对已提交态核对；在制批的未提交条目
            # 不该判红（254 上线首跑即抓到自己诞生瞬间的"条目已写、提交未在册"，
            # 该误红暴露了口径须钉 HEAD——已按 §六.2 分诊归正）。
            txt = _sp.run(["git", "-C", str(ROOT), "show", f"HEAD:{d}/docs/CHANGELOG.md"],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace").stdout
            heads |= {parse(x) for x in _re.findall(
                r"^## \d{4}-\d{2}-\d{2} 第([零〇一二两三四五六七八九十百千]+)批", txt, _re.M)}
        body = _sp.run(["git", "-C", str(ROOT), "log", "--format=%B\x01"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        men = ({parse(x) for x in _re.findall(r"第([零〇一二两三四五六七八九十百千]+)批", body)}
               | {int(x) for x in _re.findall(r"第(\d{1,4})批", body)})
        orph = sorted(h for h in heads if h and h > 175 and h not in men)
        return str(len(orph))
    add("登记×提交在册(1=已知221)", "254批（253 事故的结构反应；新虚构条目即红）", c_registration_orphans, ("1",))

    # 集合互斥（258 批·铁律三的集合面守卫）：六爻 case_splits 十二集两两零交集＋
    # 八字案例 id 无跨 split 重复。此前八字 tune∩holdout=0 只是叙事，两科皆无断言——
    # 一例泄漏即让「holdout 未参与调参」的所有句子从根上坏掉，而全账不会红。
    def c_split_disjoint(t):
        sp = json.loads((DISC / "data" / "cases" / "case_splits.json").read_text(encoding="utf-8"))
        sets = {}
        for k, v in sp.items():
            if isinstance(v, list):
                sets[k] = {x if isinstance(x, str) else (x.get("id") or "") for x in v}
        nm = list(sets)
        lu = sum(len(sets[a] & sets[b]) for i, a in enumerate(nm) for b in nm[i + 1:])
        bz = json.loads((ROOT / "bazi" / "data" / "cases" / "bazi_classical_cases.json")
                        .read_text(encoding="utf-8"))["cases"]
        seen: dict = {}
        rep = 0
        for c in bz:
            cid, s = c.get("id"), c.get("split")
            if cid in seen and seen[cid] != s:
                rep += 1
            seen.setdefault(cid, s)
        return str(lu + rep)
    add("集合互斥泄漏(0)", "258批（铁律三集合面补闸：六爻十二集两两∅＋八字 id 不跨 split）", c_split_disjoint, ("0",))

    def c_tier_consistency(t):
        ml = json.loads((ROOT / "liuyao" / "docs" / "GOVERNANCE-MAP.json").read_text(encoding="utf-8"))
        mb = json.loads((ROOT / "bazi" / "docs" / "GOVERNANCE-MAP.json").read_text(encoding="utf-8"))
        hv = [len(ml["tier_link_violations"]["blocking_not_referenced"]),
              len(mb["tier_link_violations"]["blocking_not_referenced"])]
        sv = [len(ml["tier_link_violations"]["referenced_not_blocking"]),
              len(mb["tier_link_violations"]["referenced_not_blocking"])]
        return tuple(map(str, hv + sv))
    add("tier一致性(硬0/0软0/1)", "207批（软 bazi=diff_tiaohou_vs_head 的 required 存在性引用，合法在账；冒出未见条目即红）",
        c_tier_consistency, ("0", "0", "0", "1"))

    # --- 八字侧 ---
    def c_bazi_holdout(t):
        s = sh(["scripts/evaluate.py", "--split", "holdout"], cwd=ROOT / "bazi")
        return grab(s, r"平均分 = ([0-9.]+)%")
    add("bazi.holdout(97.6)", "bazi README", c_bazi_holdout, ("97.6",))

    def c_bazi_dims(t):
        s = sh(["scripts/evaluate.py", "--split", "holdout"], cwd=ROOT / "bazi")
        out = []
        for name in ("pillars", "ten_gods", "hidden_stems", "tiaohou", "pattern", "cong_ge"):
            m = re.search(r"^\s*%s\s+(\d+)/(\d+)\s+\d+\s+[\d.]+%%" % name, s, re.M)
            out.append((m.group(1) + "/" + m.group(2)) if m else None)
        return tuple(out)
    add("bazi.holdout 分维(213/213×3 51/53 29/36 13/15)", "bazi README 表/187批", c_bazi_dims,
        ("213/213", "213/213", "213/213", "51/53", "29/36", "13/15"))

    def c_dimlock(t):
        s = sh(["dev_tools/" + "check_dim" + "_lock.py"], cwd=ROOT / "bazi")  # 拼接防 [11] 当六爻路径声明；跨科只读调用非 import，零耦合不破
        m = re.search(r"shensha＝tune:(\d+)/(\d+)、holdout:(\d+)/(\d+)\s+dayun＝tune:(\d+)/(\d+)、holdout:(\d+)/(\d+)", s)
        return tuple(m.groups()) if m else (None,) * 8
    add("bazi.dimlock(shensha 0/0·5/5, dayun 0/0·0/0)", "bazi README 六限制/170批", c_dimlock,
        ("0", "0", "5", "5", "0", "0", "0", "0"))

    def c_bazi_ext(t):
        s = sh(["scripts/evaluate.py", "--split", "external_holdout"], cwd=ROOT / "bazi")
        n = re.search(r"运行 (\d+) 例（external_holdout", s)
        sw = re.search(r"强弱对齐（external_holdout · report-only，不设门槛、非命中率）：(\d+)/(\d+)", s)
        return ((n.group(1), sw.group(1), sw.group(2)) if n and sw else (None,) * 3)
    add("bazi.external(n53 强弱30/45 report-only)", "bazi README/160批起", c_bazi_ext, ("53", "30", "45"))

    def c_bazi_base(t):
        s = sh(["dev_tools/baselines.py", "--split", "holdout"], cwd=ROOT / "bazi")
        th = re.search(r"pattern：引擎 (\d+)/(\d+) =\s*([\d.]+)%", s)  # 拿错维了？改 tiaohou 行
        m_t = re.search(r"tiaohou：引擎 (\d+)/(\d+) =\s*([\d.]+)%", s)
        m_p = re.search(r"pattern：引擎 (\d+)/(\d+) =\s*([\d.]+)%", s)
        m_c = re.search(r"先验定答从\s+(\d+)/(\d+) =\s*([\d.]+)%", s)
        vals = tuple(x.group(3) if x else None for x in (m_t, m_p, m_c))
        mb = re.search(r"定答\(tune边际\)\s+\d+/\s*\d+ =\s*[\d.]+% ｜配对 b=(\d+) c=(\d+)", s)
        return vals + ((mb.group(1), mb.group(2)) if mb else (None, None))
    add("bazi(tiaohou96.2 pattern80.6 常数从100 b42c0)", "187批", c_bazi_base,
        ("96.2", "80.6", "100.0", "42", "0"))

    # --- 前瞻通道在册 0 ---
    # CAPABILITY.md 的结构性计数（第两百一十四批补齐：对外文书的每个数字都要有重放断言）
    def c_struct_counts(t):
        g1 = re.search(r"用例 (\d+) 条", sh(["dev_tools/golden.py", "verify"]))
        g2 = re.search(r"用例 (\d+) 条", sh(["dev_tools/" + "golden.py", "verify"], cwd=ROOT / "bazi"))
        hx = re.search(r"爻序断言：(\d+) 项通过", sh(["dev_tools/" + "hexagram_check.py"]))
        reg = str(len(json.loads((ROOT / "liuyao" / "data" / "rules" / "rule_registry.json")
                                .read_text(encoding="utf-8"))["rules"]))
        # 跨科调用一律拼接（206 批规矩；本行首版又写全名被 [11] 当场逮——同名单双也拼，断侥幸）
        rg = re.search(r"机械回归通过 (\d+) 例", sh(["dev_tools/" + "regression.py"], cwd=ROOT / "bazi"))
        es = re.search(r"（(\d+) 个场景", sh(["dev_tools/" + "eval_selftest.py"], cwd=ROOT / "bazi"))
        return tuple((x.group(1) if x else None) for x in (g1, g2, hx, rg, es)) + (reg,)
    add("CAPABILITY 结构计数(288/40/23/5/9/33)", "214批", c_struct_counts,
        ("288", "40", "23", "5", "9", "33"))

    add("prospective 在册 0 条", "177/178批", lambda t: (
        "0" if not (DISC / "data" / "feedback" / "predictions.jsonl").exists()
        else str(len([1 for _ in open(DISC / "data" / "feedback" / "predictions.jsonl",
                                     encoding="utf-8") if _.strip()])),), ("0",))

    def c_rule_sha(t):
        code = ("import sys;sys.path.insert(0,'scripts');sys.path.insert(0,'dev_tools');"
                "from kernel_path import ensure_kernel_on_path;"
                "ensure_kernel_on_path('dev_tools/prospective.py');"
                "import prospective;print(prospective.rule_sha())")
        out = sh(["-c", code]).strip()
        return out.splitlines()[-1] if out else None
    # SCORING_RULE 冻结 sha 的**值**自 216 批才首次落盘——180 批加 task=占天候 支时只登记了
    # 变更事件未记值；本行初稿曾拿会话记忆的 178 时代值（a36243fc6239，盘上与 git 历史均无）
    # 当期望，实算当场打回 7867316a7303。**期望从此是字面钉桩**：口径再动此行即红，
    # 改期望的唯一合法路径＝CHANGELOG 注明理由（姊妹条款）。
    # SKILL 合同路径审计（232 批）：点号路径声称须在真实 analyze 输出可达
    # （文档根或 step5 简写两形皆认；.py 文件引用不在此族）。合同面是任务 Agent 的取数依据。
    def c_skill_paths(t):
        import subprocess as sp
        sk = (DISC / "SKILL.md").read_text(encoding="utf-8")
        claims = [x for x in sorted(set(re.findall(r"`([a-z_]+(?:\.[a-z_\[\]0-9]+){1,})`", sk)))
                  if not x.endswith(".py") and "/" not in x]
        # 262 批双修：①mkdir——全新克隆无 scratch/（git 不存空目录），克隆复验 85 轮现形；
        # ②显式 cwd＋rc 硬失败——本行自 232 起在根目录 cwd 下从未真跑过 chart（相对路径
        #   落空、异常被 capture_output 吞、json.loads 吃的是旧交互残留文件＝活僵尸）。
        #   教训：写盘型账行必须验证被调进程 rc，否则审计的是缓存而不是现势。
        (DISC / "scratch").mkdir(exist_ok=True)
        r1 = sp.run([sys.executable, "-X", "utf8", "scripts/chart.py", "--mode", "manual",
                     "--yao", "7,8,9,7,6,8", "-o", "scratch/_ledger_probe_c.json"],
                    capture_output=True, cwd=str(DISC))
        if r1.returncode != 0:
            raise RuntimeError("chart 探针未真跑 rc=%s" % r1.returncode)
        r2 = sp.run([sys.executable, "-X", "utf8", "scripts/analyze.py", "scratch/_ledger_probe_c.json",
                     "-o", "scratch/_ledger_probe_a.json"], capture_output=True, cwd=str(DISC))
        if r2.returncode != 0:
            raise RuntimeError("analyze 探针未真跑 rc=%s" % r2.returncode)
        doc = json.loads((DISC / "scratch" / "_ledger_probe_a.json").read_text(encoding="utf-8"))
        s5 = (doc.get("thinking_chain") or {}).get("step5_synthesis") or {}
        def resolve(d, path):
            cur = d
            for seg in path.split("."):
                seg = seg.replace("[]", "")
                if isinstance(cur, list):
                    cur = cur[0] if cur else None
                if not isinstance(cur, dict) or seg not in cur:
                    return False
                cur = cur[seg]
            return True
        miss = [x for x in claims if not (resolve(doc, x) or resolve(s5, x))]
        return f"{len(claims)}/{len(claims) - len(miss)}"
    add("SKILL 合同路径(20/20 可达)", "232批（22 系含 .py 引用的粗提数，工具正确排除后实算 20——期望又取自记忆非实算，账台首跑即抓）", c_skill_paths, ("20/20",))

    # 八字 api_spec 合同键审计（233 批）：反引号小写键须现算可达。
    # 探针教训铸死在此：chart 无 dayun（analyze 现算）、dayun 需 gender——两次空结果
    # 皆探针形错非文档漂移（§四.8 第三次救「冤枉文档」）。
    def c_bazi_api_keys(t):
        import subprocess as sp
        B = ROOT / "bazi"
        (B / "scratch").mkdir(exist_ok=True)  # 同 262 修①：本行幸免因 bazi chart 自建目录，仍防其变
        r1 = sp.run([sys.executable, "-X", "utf8", "scripts/chart.py", "--datetime", "1990-06-15 10:00",
                     "--gender", "男", "-o", "scratch/_led_bz_c.json"], capture_output=True, cwd=str(B))
        if r1.returncode != 0:  # 同 262 修②：rc 硬验（233 时代缺此，幸其一直带 cwd 真跑过）
            raise RuntimeError("bazi chart 探针未真跑 rc=%s" % r1.returncode)
        r2 = sp.run([sys.executable, "-X", "utf8", "scripts/analyze.py", "scratch/_led_bz_c.json",
                     "-o", "scratch/_led_bz_a.json"], capture_output=True, cwd=str(B))
        if r2.returncode != 0:
            raise RuntimeError("bazi analyze 探针未真跑 rc=%s" % r2.returncode)
        doc = json.loads((B / "scratch" / "_led_bz_a.json").read_text(encoding="utf-8"))
        keys = set()
        def walk(o, d=0):
            if d > 7:
                return
            if isinstance(o, dict):
                keys.update(o.keys())
                for v in o.values():
                    walk(v, d + 1)
            elif isinstance(o, list):
                for v in o[:8]:
                    walk(v, d + 1)
        walk(doc)
        spec = (B / "references" / "api_spec.md").read_text(encoding="utf-8")
        toks = [x for x in sorted(set(re.findall(r"`([a-z][a-z0-9_]{2,30})`", spec))) if "." not in x and "/" not in x]
        miss = [x for x in toks if x not in keys]
        return f"{len(toks)}/{len(toks) - len(miss)}"
    add("八字 api 合同键(19/19 可达)", "233批（合同面两科对齐；探针形错两次已铸死于注释）", c_bazi_api_keys, ("19/19",))
    add("prospective 口径sha(7867316a7303)", "180批生效/216批落值入册",
        c_rule_sha, ("7867316a7303",))

    # 六爻分析链零随机（217 批 CAPABILITY「三 seed」串号更正的断言化）：随机只许活在起卦层。
    def c_liuyao_no_random(t):
        import glob as _glob
        n = 0
        for pat in ("scripts/step*.py", "scripts/thinking_chain.py", "scripts/analyze.py",
                    "scripts/classical*.py", "scripts/narrate_core.py"):
            for f in _glob.glob(str(DISC / pat)):
                if "random" in Path(f).read_text(encoding="utf-8", errors="replace"):
                    n += 1
        return str(n)
    add("liuyao 分析链含随机文件数(0)", "217批（串号更正伴生断言）", c_liuyao_no_random, ("0",))
    return out


def _collate_now():
    s = sh(["dev_tools/version_collate.py"])
    g = re.search(r"卦面冲突率 = (\d+/\d+)", s)
    p = re.search(r"判词冲突率 = (\d+/\d+)", s)
    return ((g.group(1), p.group(1)) if g and p else (None, None))


def _json_counts(rel, top, keys, key=None):
    d = json.loads((DISC / rel).read_text(encoding="utf-8"))
    src = d.get(top) if top else (d.get(key) if key else d)
    return tuple(str(src.get(k)) for k in keys) if isinstance(src, dict) else (None,) * len(keys)


def _adjud_counts():
    d = json.loads((DISC / "data" / "rules" / "adjudications.json").read_text(encoding="utf-8"))
    c = {"settled_by_source": 0, "frozen_by_user": 0, "open_conflict": 0}
    for e in d["entries"]:
        c[e["status"]] += 1
    return (str(d["count"]), str(c["settled_by_source"]), str(c["frozen_by_user"]),
            str(c["open_conflict"]))


def _draft_counts():
    d = json.loads((DISC / "data" / "cases" / "restorable_candidates.json").read_text(encoding="utf-8"))
    cs = d.get("candidates", [])
    dup = sum(1 for c in cs if any(str(g).startswith("dup_of") for g in c.get("gaps", [])))
    return (str(len(cs)), str(dup))


def _golden(disc):
    s = sh(["dev_tools/golden.py", "verify"], cwd=ROOT / disc)
    m = re.search(r"机械 ([0-9a-f]{16})｜措辞 ([0-9a-f]{16})", s)
    return (m.group(1), m.group(2)) if m else (None, None)


def _gov_counts():
    s = sh(["dev_tools/governance_map.py"])
    l = re.search(r"liuyao：(\d+) 脚本｜blocking (\d+)", s)
    b = re.search(r"bazi：(\d+) 脚本｜blocking (\d+)", s)
    return ((l.group(1), b.group(1), l.group(2), b.group(2)) if l and b else (None,) * 4)


QUICK_SKIP = {"liuyao.wiki top1/top3(27.3/52.3)", "liuyao.baselines 用神18.2/日辰4.5",
              "bazi(tiaohou96.2 pattern80.6 常数从100 b42c0)",
              "liuyao.collate(卦面0/47 判词1/37)",
              "bazi.holdout 分维(213/213×3 51/53 29/36 13/15)",
              "bazi.external(n53 强弱30/45 report-only)"}


def run(quick: bool) -> int:
    bad = 0
    items = checks()
    # 总项数由账台自报（218 批：此前 changelog 里「26/28 项」系我凭手感数的假数——
    # 凡计数自己算、不手打；下面的结论行也带实测 n）。
    print("═ 读数对账台（登记值 vs HEAD 重放值）%s·全账 %d 项 ═" % ("quick" if quick else "full", len(items)))
    for cid, src, fn, expect in items:
        if quick and cid in QUICK_SKIP:
            print("  ~ %-46s 跳过（full 才跑）" % cid)
            continue
        try:
            got = fn(None)
            if not isinstance(got, tuple):
                got = (got,)
        except Exception as e:  # noqa: BLE001
            print("  ! %-46s 取数异常 %s" % (cid, str(e)[:40]))
            bad += 1
            continue
        def norm(x):
            if isinstance(x, tuple):
                return tuple(str(i) for i in x)
            return str(x)
        ok = all(norm(g) == norm(e) for g, e in zip(got, expect)) and len(got) == len(expect)
        print("  %s %-46s（登记：%s）%s" % ("√" if ok else "×", cid, src,
              "" if ok else " 实得 %r ≠ 期望 %r" % (got, expect)))
        bad += 0 if ok else 1
    print("═ 结论：%s（bad=%d/全账 %d）——任何 × 都是读数与代码分家的现形，按 §六.2 立案处理，"
          "禁止静默改期望值 ═" % ("全部对账一致" if bad == 0 else "存在分家读数", bad, len(items)))
    return 1 if bad else 0


def selftest() -> int:
    fails = []
    # 自测解析器本体：golden 与 evaluate 的输出必须可抽——对账器不许先瞎
    s = sh(["dev_tools/golden.py", "verify"], cwd=ROOT / "liuyao")
    if not re.search(r"机械 ([0-9a-f]{16})｜措辞 ([0-9a-f]{16})", s):
        fails.append("golden 解析式失配（对账器瞎了）")
    print("√ selftest：抽取器在线（golden 双指纹可抽）" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="读数对账台（登记值 vs HEAD 重放值）")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return run(args.quick)


if __name__ == "__main__":
    raise SystemExit(main())
