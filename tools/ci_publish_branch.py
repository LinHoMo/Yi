# -*- coding: utf-8 -*-
"""把报告 MD+HTML 提交到独立的 reports 分支并推送，回写可匿名读取的 raw URL。

reports 分支的目录约定（**稳定别名是给"只知道仓库链接"的网页 AI 用的**）：

    reports/<discipline>/latest.md           ← 该科最近一次报告（固定 URL）
    reports/<discipline>/latest.html
    reports/<discipline>/<name>-<run_id>/report.md    ← 逐次留档，不覆盖
    reports/<discipline>/<name>-<run_id>/report.html
    reports/index.json                       ← 各科最近一次的时间/run/URL 索引

为什么要有 latest：报告落到 run 专属目录时，取回 URL 里带 run_id，而网页端 AI
**拿不到** run_id（它不跑 API 也不该轮询）。有了固定别名，AI 只需
`https://raw.githubusercontent.com/{owner}/{repo}/reports/{discipline}/latest.md`
就能读到最新报告，无需任何凭证。

追加式提交，不 force push；只改 reports 分支，不碰主分支。
在 runner 上：
  python tools/ci_publish_branch.py --meta meta.json --outdir out
令牌取 GITHUB_TOKEN（或 GH_TOKEN）。可用 --origin <url> 覆盖远端（本地测试用）。
仅用标准库 + git。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

CST = timezone(timedelta(hours=8))


def git(args, cwd, check=True, env=None):
    proc = subprocess.run(["git", *args], cwd=cwd, env=env,
                          capture_output=True, text=True, encoding="utf-8")
    if check and proc.returncode != 0:
        sys.stderr.write((proc.stdout or "") + (proc.stderr or ""))
        raise RuntimeError("git " + " ".join(args) + f" 失败 ({proc.returncode})")
    return proc


def _branch_exists(origin: str, branch: str, cwd: Path) -> tuple[bool, str]:
    """判定远端分支是否存在。返回 (存在?, 诊断信息)。

    历史缺陷：旧实现把**任何** clone 失败都当成"分支不存在"，于是网络抖动或凭证
    错误会被误判，接着走 init + 非强推，必然失败且报错指向错误的方向。这里改为
    显式 `git ls-remote --exit-code --heads`：只有"远端确实没有这个分支"才算不存在。
    """
    proc = git(["ls-remote", "--exit-code", "--heads", origin, branch],
               cwd=cwd, check=False)
    if proc.returncode == 0:
        return True, ""
    if proc.returncode == 2:
        return False, ""
    return False, ((proc.stdout or "") + (proc.stderr or "")).strip()[:400] or \
        f"ls-remote 退出码 {proc.returncode}"


def main() -> int:
    ap = argparse.ArgumentParser(description="把报告提交到 reports 分支")
    ap.add_argument("--meta", default="meta.json")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--branch", default="reports")
    ap.add_argument("--origin", default="", help="覆盖远端（本地测试：某个 bare 仓库路径）")
    args = ap.parse_args()

    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    if not meta.get("should_run") or not meta.get("commit_branch"):
        print("按配置无需提交 reports 分支，跳过。")
        return 0

    repo = meta["repo"]
    name = meta.get("report_name", "report")
    discipline = meta.get("request_discipline", "misc")
    run_id = meta.get("run_id") or datetime.now(CST).strftime("%Y%m%d-%H%M%S")
    subdir = f"{discipline}/{name}-{run_id}"
    latest_dir = discipline
    generated = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S%z")

    token = "" if args.origin else (
        os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", ""))
    if args.origin:
        origin = args.origin
    else:
        if not token:
            raise RuntimeError("缺少 GITHUB_TOKEN / GH_TOKEN（或用 --origin 指定远端）")
        origin = f"https://x-access-token:{token}@github.com/{repo}.git"

    tmp = tempfile.mkdtemp(prefix="yi-reports-")
    try:
        exists, diag = _branch_exists(origin, args.branch, Path(tmp))
        if exists:
            # clone 要求目标目录不存在或为空：先清掉 mkdtemp 建的空目录
            shutil.rmtree(tmp, ignore_errors=True)
            git(["clone", "--depth", "1", "--branch", args.branch, origin, tmp],
                cwd=Path(tmp).parent)
        else:
            if diag:
                raise RuntimeError(
                    f"无法确认远端分支 {args.branch} 是否存在（不是'分支不存在'）：{diag}")
            git(["init", tmp], cwd=tmp)
            git(["checkout", "-b", args.branch], cwd=tmp)
            git(["remote", "add", "origin", origin], cwd=tmp)

        git(["config", "user.email", "yi-bot@users.noreply.github.com"], cwd=tmp)
        git(["config", "user.name", "yi-bot"], cwd=tmp)

        # 1) 逐次留档目录
        dest = Path(tmp) / subdir
        dest.mkdir(parents=True, exist_ok=True)
        copied = []
        for ext in ("md", "html"):
            src = Path(args.outdir) / f"{name}.{ext}"
            if src.is_file():
                shutil.copy2(src, dest / f"report.{ext}")
                copied.append(ext)
        if not copied:
            raise RuntimeError(f"未在 {args.outdir} 找到 {name}.md/html")

        # 2) 稳定别名（固定 URL，网页 AI 不必知道 run_id）
        latest = Path(tmp) / latest_dir
        latest.mkdir(parents=True, exist_ok=True)
        for ext in ("md", "html"):
            src = Path(args.outdir) / f"{name}.{ext}"
            if src.is_file():
                shutil.copy2(src, latest / f"latest.{ext}")

        # 3) 索引：各科最近一次的时间 / run / 相对路径
        index_p = Path(tmp) / "index.json"
        index = {"schema": "yi-reports-index/1", "updated": generated,
                 "branch": args.branch, "reports": {}}
        if index_p.is_file():
            try:
                prior = json.loads(index_p.read_text(encoding="utf-8"))
                if isinstance(prior.get("reports"), dict):
                    index["reports"] = prior["reports"]
            except json.JSONDecodeError:
                pass  # 索引坏了就重建，不让它挡住报告
        index["reports"][discipline] = {
            "updated": generated,
            "run_id": run_id,
            "name": name,
            "md": f"{latest_dir}/latest.md",
            "html": f"{latest_dir}/latest.html",
            "archive": f"{subdir}/report.md",
            "title": meta.get("request", {}).get("question", "") if isinstance(
                meta.get("request"), dict) else "",
        }
        index_p.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")

        git(["add", subdir, latest_dir, "index.json"], cwd=tmp)
        status = git(["status", "--porcelain"], cwd=tmp).stdout.strip()
        if status:
            git(["commit", "-m", f"report: {discipline}/{name} ({run_id})"], cwd=tmp)
        if exists:
            push = git(["push", "origin", f"HEAD:{args.branch}"], cwd=tmp, check=False)
        else:
            push = git(["push", "-u", "origin", args.branch], cwd=tmp, check=False)
        if push.returncode != 0:
            sys.stderr.write((push.stdout or "") + (push.stderr or ""))
            raise RuntimeError("推送 reports 分支失败（远端可能在本步骤期间有了新提交，重跑即可）")

        raw = (f"https://raw.githubusercontent.com/{repo}/{args.branch}")
        meta["md_url"] = f"{raw}/{subdir}/report.md"
        meta["html_url"] = f"{raw}/{subdir}/report.html"
        meta["latest_md_url"] = f"{raw}/{latest_dir}/latest.md"
        meta["latest_html_url"] = f"{raw}/{latest_dir}/latest.html"
        meta["index_url"] = f"{raw}/index.json"
        Path(args.meta).write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
        print("reports 分支已更新：")
        print("  固定别名 MD:   " + meta["latest_md_url"])
        print("  固定别名 HTML: " + meta["latest_html_url"])
        print("  本次留档 MD:   " + meta["md_url"])
        print("  索引:          " + meta["index_url"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
