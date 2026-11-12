# -*- coding: utf-8 -*-
"""结论库构建器（第五百五十四批）：把"代码实跑出的结论"落成可审查、可直接消费的静态产物。

为什么要有这一层：554 批起把"演示"升级成"库"——有固定输入清单、索引与哈希；
555 批并掉原 `examples/`（同输入、同哈希），本目录成为**唯一的结论产物层**。
本器把一批**固定输入**跑成结论快照，并生成索引：

    conclusions/
    ├── INDEX.md                 # 输入 → 产物 的映射（人看 / AI 查）
    ├── liuyao/<id>.json/.md     # 六爻：引擎 JSON + 渲染报告
    └── bazi/<id>.json/.md       # 八字：同上

    python conclusions/build_conclusions.py --write     # 生成/更新全部快照
    python conclusions/build_conclusions.py --check     # 逐字节复验（CI 挂此）
    python conclusions/build_conclusions.py --selftest  # 负例自证，真盘零写入

铁律：结论只能由代码生成（§一.1）；输入全是新造中性问句，不触达 `data/cases/`（§一.2）；
每份带口径脚注（§一.3）。**不要手改产物**——改输入清单或引擎，再跑 `--write`。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "conclusions"
RAW = "https://raw.githubusercontent.com/LinHoMo/Yi/main"

CALIBER = (
    "> **口径**：本结论由 Python 引擎实跑生成，未由语言模型改写任何排盘或判定。仓库内分数是"
    "**古籍案例对齐分**（回归审计用），**不是现实命中率**；现实侧样本为 0。属条件化倾向陈述，"
    "不是预言；医疗、法律、投资、重大决策请以专业意见为准。\n"
)

# 固定输入清单：新增一条 = 加一行，再跑 --write（同批改 CHANGELOG）
CASES: list[dict] = [
    dict(
        id="ly-coin-2026-01-15", disc="liuyao", mode="coin",
        question="示例：某合作项目下月能否顺利推进",
        datetime="2026-01-15 10:30", seed=42,
    ),
    dict(
        id="ly-time-2026-03-18", disc="liuyao", mode="time",
        question="示例：某岗位竞聘在本季度是否值得投入",
        datetime="2026-03-18 14:00",
    ),
    dict(
        id="bz-1990-05-20-male", disc="bazi",
        question="示例：命局结构说明",
        datetime="1990-05-20 10:30", gender="男",
    ),
    dict(
        id="bz-1985-11-03-female", disc="bazi",
        question="示例：命局结构说明",
        datetime="1985-11-03 08:15", gender="女",
    ),
]

LY_RENDER = (
    "import sys,json;sys.path.insert(0,'scripts');"
    "from render import render;"
    "a=json.load(open(sys.argv[1],encoding='utf-8'));"
    "print(render(a,fmt='md'),end='')"
)
BZ_RENDER = (
    "import sys,json;sys.path.insert(0,'scripts');"
    "from analyze import analyze;from render import render;"
    "a=analyze(json.load(open(sys.argv[1],encoding='utf-8')));"
    "print(render(a),end='')"
)


def _run(cmd: list[str], cwd: Path) -> str:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, env=env, timeout=180)
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace")[-1000:]
        raise RuntimeError(f"引擎实跑失败（rc={proc.returncode}）：{err}")
    return proc.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def engine_json_text(case: dict) -> str:
    """跑引擎，返回规范化（LF）的 JSON 文本；解析失败即报错，不写半成品。"""
    if case["disc"] == "liuyao":
        cmd = [sys.executable, "-m", "engine", "--mode", case["mode"],
               "--question", case["question"], "--datetime", case["datetime"],
               "--output", "json"]
        if case.get("seed") is not None:
            cmd += ["--seed", str(case["seed"])]
        text = _run(cmd, ROOT / "liuyao")
    else:
        text = _run([sys.executable, "scripts/chart.py", "--datetime", case["datetime"],
                     "--gender", case["gender"], "--question", case["question"]], ROOT / "bazi")
    text = text.strip() + "\n"
    json.loads(text)  # 校验：不是合法 JSON 就不许落盘
    return text


def render_md(case: dict, json_path: Path) -> str:
    code, cwd = (LY_RENDER, ROOT / "liuyao") if case["disc"] == "liuyao" else (BZ_RENDER, ROOT / "bazi")
    body = _run([sys.executable, "-c", code, str(json_path)], cwd).strip() + "\n"
    if not body.strip():
        raise RuntimeError(f"渲染为空：{case['id']}")
    return body


def input_desc(case: dict) -> str:
    if case["disc"] == "liuyao":
        seed = f"，seed={case['seed']}" if case.get("seed") is not None else ""
        return f"mode={case['mode']}，question=「{case['question']}」，datetime={case['datetime']}{seed}"
    return f"question=「{case['question']}」，datetime={case['datetime']}，gender={case['gender']}"


def repro_cmd(case: dict) -> str:
    if case["disc"] == "liuyao":
        return (f"cd liuyao && python -m engine --mode {case['mode']} "
                f"--question \"{case['question']}\" --datetime \"{case['datetime']}\" "
                f"--output json" + (f" --seed {case['seed']}" if case.get("seed") is not None else ""))
    return (f"cd bazi && python scripts/chart.py --datetime \"{case['datetime']}\" "
            f"--gender {case['gender']}")


def _md_wrap(case: dict, json_rel: str, digest: str, size: int, body: str) -> str:
    title = "六爻纳甲占报告" if case["disc"] == "liuyao" else "八字命局因子说明"
    return (
        "<!-- 由 conclusions/build_conclusions.py --write 生成；结论由引擎实跑，请勿手改 -->\n"
        f"# {title} · {case['id']}\n\n"
        f"- 学科：{'六爻纳甲' if case['disc'] == 'liuyao' else '八字四柱'}\n"
        f"- 输入：{input_desc(case)}\n"
        f"- 复现（仓库根）：`{repro_cmd(case)}`\n"
        f"- JSON 快照：[`{json_rel}`]({json_rel})（sha256 `{digest[:16]}`，{size} 字节）\n"
        "- 同源复验：`python conclusions/build_conclusions.py --check`（逐字节比对，漂移即判红）\n\n"
        + CALIBER + "\n---\n\n" + body
    )


def build(cases: list[dict] | None = None) -> dict[str, str]:
    """返回 {相对路径: 文本}，全部为 LF。"""
    cases = CASES if cases is None else cases
    files: dict[str, str] = {}
    rows = []
    for case in cases:
        if case["disc"] not in ("liuyao", "bazi"):
            raise ValueError(f"未知学科：{case['disc']}")
        json_rel = f"conclusions/{case['disc']}/{case['id']}.json"
        md_rel = f"conclusions/{case['disc']}/{case['id']}.md"
        json_text = engine_json_text(case)
        digest = hashlib.sha256(json_text.encode("utf-8")).hexdigest()
        files[json_rel] = json_text
        # 渲染用系统临时文件（真盘零残留），避免把整份 JSON 塞进命令行
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "case.json"
            tmp.write_bytes(json_text.encode("utf-8"))
            body = render_md(case, tmp)
        files[md_rel] = _md_wrap(case, case["id"] + ".json", digest, len(json_text.encode("utf-8")), body)
        rows.append((case, json_rel, md_rel, digest, len(json_text.encode("utf-8"))))

    lines = [
        "# 结论库索引（易 / Yi）",
        "",
        "> 本库是**引擎实跑产出的结论快照**，服务两类读者：**人审查**（输入、复现命令、哈希齐全，"
        "可逐字节复算）与**语言模型取用**（按输入查表：命中即引用，未命中不得套用他条）。",
        f"> 共 {len(rows)} 条；未收录的输入请本地跑引擎（命令见各条报告抬头），或按 "
        f"[`outreach/WEB-AI-PROMPT.md`](../outreach/WEB-AI-PROMPT.md) 的三条路径处理。",
        "",
        "| ID | 学科 | 输入 | 结论报告 | JSON 快照 | sha256 |",
        "|---|---|---|---|---|---|",
    ]
    for case, json_rel, md_rel, digest, size in rows:
        lines.append(
            f"| `{case['id']}` | {'六爻' if case['disc'] == 'liuyao' else '八字'} | "
            f"{input_desc(case).replace('|', '／')} | "
            f"[`{case['id']}.md`]({case['id']}.md) | [`{case['id']}.json`]({case['id']}.json) | `{digest[:16]}` |"
        )
    lines += [
        "",
        "## 覆盖范围（重要）",
        "",
        f"- 本库只覆盖上表 {len(rows)} 条**固定输入**，不是「任意时间、任意问题都能查」。",
        "- 新增一条：在 `conclusions/build_conclusions.py` 的 `CASES` 加一行，跑 `--write`，"
        "同批登记 `CHANGELOG`。新增输入必须是新造中性问句，不得来自案例库。",
        "- 产物由 `--check` 逐字节复验：引擎或输入有任何漂移都会判红。",
        "",
        "## 口径",
        "",
        "所有结论都是引擎输出的原文快照；分数是**古籍案例对齐分**，不是现实命中率，"
        "现实侧样本为 0。属条件化倾向陈述，不是预言；医疗、法律、投资、重大决策请以专业意见为准。",
        "",
    ]
    files["conclusions/INDEX.md"] = "\n".join(lines)
    return files


def write_all(files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def compare(files: dict[str, str]) -> list[str]:
    problems = []
    for rel, text in files.items():
        p = ROOT / rel
        if not p.is_file():
            problems.append(f"缺文件：{rel}（跑 --write 生成）")
            continue
        want = text.replace("\r\n", "\n").encode("utf-8")
        got = p.read_bytes().replace(b"\r\n", b"\n")
        if want != got:
            problems.append(f"内容漂移：{rel}（在盘 {len(got)} B / 应 {len(want)} B）")
    return problems


def selftest() -> int:
    files = build()
    cases = []

    def check(name, fn):
        try:
            ok = bool(fn())
        except Exception:
            ok = False
        cases.append((name, ok))

    def rejects(fn):
        try:
            fn()
            return False
        except (ValueError, RuntimeError):
            return True

    check("正例：构建产物齐全（每条 json + md，另有 INDEX）",
          lambda: len(files) == len(CASES) * 2 + 1)
    check("每条报告都带复现命令与口径脚注",
          lambda: all("复现（仓库根）" in v and "古籍案例对齐分" in v
                      for k, v in files.items() if k.endswith(".md") and not k.endswith("INDEX.md")))
    check("每条 JSON 都可解析",
          lambda: all(json.loads(v) for k, v in files.items() if k.endswith(".json")))
    check("INDEX 覆盖全部条目", lambda: all(c["id"] in files["conclusions/INDEX.md"] for c in CASES))
    check("未知学科 → 判红", lambda: rejects(lambda: build(
        [{"id": "x", "disc": "qimen", "question": "x", "datetime": "2026-01-01 00:00"}])))
    check("缺文件 → 复验判红", lambda: any("缺文件" in p for p in compare(
        {**files, "conclusions/liuyao/nope.md": "x"})))
    check("改一个字节 → 复验判红", lambda: any("漂移" in p for p in compare(
        {**files, "conclusions/INDEX.md": files["conclusions/INDEX.md"] + "x"})))

    for name, ok in cases:
        print(f"  {'√' if ok else '×'} {name}")
    bad = [n for n, ok in cases if not ok]
    if bad:
        print(f"selftest 失败 {len(bad)} 项：{'; '.join(bad)}")
        return 1
    print(f"selftest：{len(cases)} 类正/负例全过（真盘零写入，临时 JSON 已清理）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="结论库构建器")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    try:
        files = build()
    except (ValueError, RuntimeError) as exc:
        print(f"  × {exc}")
        print("[conclusions] 构建失败：引擎或输入有问题，未写入任何文件")
        return 1
    if args.write:
        write_all(files)
        print(f"[conclusions] 已写入 {len(files)} 份产物（{len(CASES)} 条结论 + 索引）")
        return 0
    problems = compare(files)
    if problems:
        for p in problems:
            print("  × " + p)
        print("[conclusions] 复验判红：结论与引擎输出不一致，请跑 --write 后提交")
        return 1
    print(f"[conclusions] 复验全绿：{len(files)} 份产物与引擎实跑逐字节一致；共 {len(CASES)} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
