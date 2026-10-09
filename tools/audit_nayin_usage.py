# -*- coding: utf-8 -*-
"""纳音使用审计（OPT-shenfeng_tongkao_dz-02，2026-10-07）。

审计问题：《神峰通考》对纳音持批判立场，故须证明
**引擎中 NAYIN 只作「排盘取值 / 叙述取象」层，不参与吉凶判断**。

方法（静态 + 动态双向）：
  静态：扫全仓 NAYIN/nayin 消费点，分三类——
        A 排盘取值（安星、取名、渲染字段）
        B 叙述层（拼进 description / narrate 文本）
        C 判据层（参与吉凶、格局、评分）——**出现即判红**
  动态：把 core.symbols.NAYIN 整表替换为等长伪值，重跑两科 evaluate，
        比对 tune/holdout 分数。分数不变 ⇒ 纳音对读数零影响（旁证）。

只读。不改 core 任何表值（动态替换在子进程内 monkeypatch，不落盘）。
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

# 仓库级只读审计工具（原在 `disciplines/ming/dev_tools/`，2026-10-08 移出：
# 本脚本的反事实探针同时 import 六爻与命科两科模块，属跨科审计，
# 放在学科目录内等于让 ming 反向依赖 liuyao，违反 AGENTS.md §二 依赖方向单向）。
ROOT = Path(__file__).resolve().parents[1]
# 只扫真实引擎/学科/工具/测试，不扫构建产物副本与本脚本自身
SKIP_PARTS = {".git", "__pycache__", "node_modules", "scratch", "site", "modernized", "archive"}
SELF = Path(__file__).resolve()

PAT = re.compile(r"\bnayin|NAYIN", re.I)
# 判据层信号：与「结论性字段」同现。注释/docstring 里出现「吉凶」不算。
C_SIGNAL = re.compile(
    r"\b(final_score|score|verdict|strength_score|useful|taboo|is_ji|ji_list|"
    r"cheng|ju_num|bias|weight|points?)\b"
)
B_SIGNAL = re.compile(
    r"(description|narrate|render|label|report|str\(|f\"|print\(|"
    r"append\(|markdown|\.md)"
)


def iter_py():
    for p in sorted(ROOT.rglob("*.py")):
        if any(x in p.parts for x in SKIP_PARTS):
            continue
        if p.resolve() == SELF:
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        yield p, txt


def scan() -> list[dict]:
    hits = []
    for p, txt in iter_py():
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for i, line in enumerate(txt.split("\n"), 1):
            if not PAT.search(line):
                continue
            st = line.strip()
            # 判文档字符串/注释：连续块内或以 # 开头
            hits.append({
                "file": rel, "line": i, "text": st[:120],
                "comment": st.startswith("#") or st.startswith(('"', "'", "*", "「")),
            })
    return hits


def classify(hits: list[dict]) -> tuple[dict[str, int], list[dict]]:
    cnt = {"A_排盘取值": 0, "B_叙述层": 0, "C_判据层": 0, "注释/文档": 0}
    suspects = []
    for h in hits:
        if h["comment"]:
            cnt["注释/文档"] += 1
            continue
        t = h["text"]
        if C_SIGNAL.search(t):
            cnt["C_判据层"] += 1
            suspects.append(h)
        elif B_SIGNAL.search(t):
            cnt["B_叙述层"] += 1
        else:
            cnt["A_排盘取值"] += 1
    return cnt, suspects


COUNTERFACTUAL = r'''
import sys, json, io, contextlib
from pathlib import Path
sys.path.insert(0, "core")
import yishu_core.symbols as S

vals = sorted(set(S.NAYIN.values()))
fake = {k: vals[i % len(vals)] for i, k in enumerate(S.NAYIN)}
# 伪值：把纳音名整体改掉（长度可变，不参与长度断言）
fake = {k: ("伪" + v) for k, v in fake.items()}
S.NAYIN = fake
S.NAYIN_TO_ELEMENT = {v: "木" for v in set(fake.values())}
S.nayin_of = lambda gz: fake.get(gz)
for mod in ("yishu_core.relations", "yishu_core.shensha", "yishu_core.ming_tables"):
    m = __import__(mod, fromlist=["x"])
    if hasattr(m, "nayin_of"):
        m.nayin_of = S.nayin_of

# 跑两科 evaluate（它们各自 import，取 monkeypatch 后的 S）
sys.path.insert(0, "tools")
import importlib
res = {}
try:
    ev = importlib.import_module("evaluate_helper")
except Exception:
    ev = None
for disc, mod in (("liuyao", "disciplines.liuyao.scripts.classical_analysis"),
                  ("ming", "disciplines.ming.scripts.analyze")):
    try:
        m = importlib.import_module(mod)
        res[disc] = "imported"
    except Exception as e:
        res[disc] = f"ERR {type(e).__name__}: {e}"
print(json.dumps(res, ensure_ascii=False))
'''


def dynamic() -> dict:
    r = subprocess.run([sys.executable, "-c", COUNTERFACTUAL], cwd=ROOT,
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return {"rc": r.returncode, "out": r.stdout.strip()[:600],
            "err": r.stderr.strip()[-500:]}


def score_probe() -> dict:
    """真正有意义的动态证据：伪值下跑 tools/eval.py，看两科分数是否变化。"""
    res: dict = {}
    for label, patch in (("baseline", None), ("fake_nayin", True)):
        env = None
        if patch:
            # 用 sitecustomize 注入 monkeypatch（子进程内，不落盘改 core）
            code = (
                "import sys;sys.path.insert(0,'core');"
                "import yishu_core.symbols as S;"
                "f={k:('伪'+v) for k,v in S.NAYIN.items()};"
                "S.NAYIN=f;S.NAYIN_TO_ELEMENT={v:'木' for v in set(f.values())};"
                "S.nayin_of=lambda gz:f.get(gz);"
                "import yishu_core.relations,yishu_core.shensha,yishu_core.ming_tables;"
                "[setattr(m,'nayin_of',S.nayin_of) for m in "
                "(yishu_core.relations,yishu_core.shensha,yishu_core.ming_tables)];"
                "import tools.eval as E;E.main()"
            )
            r = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            res[label] = r.stdout
        else:
            r = subprocess.run([sys.executable, "tools/eval.py"], cwd=ROOT,
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            res[label] = r.stdout
    def grab(txt):
        return re.findall(r"=== (\w+) \[(\w+)\] 平均分 = ([\d.]+)%", txt)
    b, f = grab(res["baseline"]), grab(res["fake_nayin"])
    return {"baseline": b, "fake": f, "same": b == f}


NEGATIVE_PROOF = r'''
import sys, json
sys.path.insert(0, "core")
import yishu_core.symbols as S
import disciplines.ming.scripts.chart as C

gz = "甲午"
before = S.nayin_of(gz)
chart_before = C.nayin_of(gz)
f = {k: ("伪" + v) for k, v in S.NAYIN.items()}
S.NAYIN = f
S.NAYIN_TO_ELEMENT = {v: "木" for v in set(f.values())}
S.nayin_of = lambda g: f.get(g)
for m in ("yishu_core.relations", "yishu_core.shensha", "yishu_core.ming_tables"):
    mod = __import__(m, fromlist=["x"])
    if hasattr(mod, "nayin_of"):
        mod.nayin_of = S.nayin_of
after = S.nayin_of(gz)
chart_after = C.nayin_of(gz)
# 负例：若两者未变 → 注入其实没生效，本审计的「读数不变」就是假证据
print(json.dumps({
    "gz": gz,
    "core_before": before, "core_after": after,
    "chart_before": chart_before, "chart_after": chart_after,
    "injection_effective": (before != after) and (chart_before != chart_after),
}, ensure_ascii=False))
'''


def negative_proof() -> dict:
    """铁律四.5：注入必须自证生效，否则「读数不变」不能作为证据。"""
    r = subprocess.run([sys.executable, "-c", NEGATIVE_PROOF], cwd=ROOT,
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    try:
        return json.loads(r.stdout.strip().split("\n")[-1])
    except (json.JSONDecodeError, IndexError):
        return {"error": r.stdout[-200:] + " | " + r.stderr[-300:]}


def main() -> int:
    hits = scan()
    cnt, suspects = classify(hits)

    print("=" * 74)
    print("纳音使用审计（OPT-shenfeng_tongkao_dz-02）")
    print("=" * 74)
    print(f"扫描范围：全仓 *.py（排除 {', '.join(sorted(SKIP_PARTS))} 与本脚本）")
    print(f"NAYIN/nayin 命中行：{len(hits)}")
    for k, v in cnt.items():
        print(f"  {k}: {v}")

    print("\n--- 判据层（红线）嫌疑 ---")
    if suspects:
        for h in suspects:
            print(f"  !! {h['file']}:{h['line']}  {h['text']}")
    else:
        print("  无。")

    print("\n--- 动态反事实：NAYIN 整表替换为伪值，读数是否变化 ---")
    npf = negative_proof()
    print(f"  注入自证（负例）: {npf}")
    sp = score_probe()
    print(f"  baseline: {sp['baseline']}")
    print(f"  fake    : {sp['fake']}")
    print(f"  读数是否相同: {sp['same']}")

    verdict = (not suspects) and sp["same"] and npf.get("injection_effective")
    print("\n结论：" + ("通过——纳音仅作排盘取值/叙述取象，不参与吉凶判断"
                        if verdict else
                        "不通过——存在判据层消费、读数受影响，或注入未生效（证据不成立）"))
    if not npf.get("injection_effective"):
        print("  ⚠ 注入未自证生效 ⇒「读数不变」不可作为证据（铁律四.5）")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
