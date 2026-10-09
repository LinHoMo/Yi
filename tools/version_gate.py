#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""版本真实性门（AGENTS.md §七）——每轮 OBSERVE 第一步运行。

报告 LOCAL_HEAD / REMOTE_HEAD / WORKTREE / LOCAL_AHEAD / REMOTE_AHEAD / SYNC_STATUS。

REMOTE_HEAD 以 `git ls-remote` 实测为准（不经 fetch、不读本地缓存引用）；
ls-remote 不可达时如实标 REMOTE_UNVERIFIED，仅附本地追踪引用口径作参考，不冒充实测。
UNSYNCED 不是失败（允许继续工作），但必须如实标注——本地提交在推送前不是
远端可验证事实（评审优先级：实际 git 状态 > 代码/测试 > 数据 > 文档 > Agent 自述）。

用法：python tools/version_gate.py [--remote origin] [--branch main]
退出码：0 = 报告完成；2 = 不在 git 仓库内（版本真实性无法确认）。
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def _run(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="版本真实性门：报告本地/远端/工作区同步状态（AGENTS.md §七）")
    ap.add_argument("--remote", default="origin", help="远端名（默认 origin）")
    ap.add_argument("--branch", default="main", help="远端分支名（默认 main）")
    args = ap.parse_args()

    head = _run("git", "rev-parse", "HEAD")
    if head.returncode != 0:
        print("NOT_A_GIT_REPO: 版本真实性无法确认", file=sys.stderr)
        return 2
    local_head = head.stdout.strip()
    local_short = _run("git", "log", "-1", "--format=%h %s").stdout.strip()

    status = _run("git", "status", "--porcelain")
    dirty = [ln.strip() for ln in status.stdout.splitlines() if ln.strip()]
    if dirty:
        shown = "; ".join(dirty[:8]) + ("…" if len(dirty) > 8 else "")
        worktree = f"dirty（{len(dirty)} 项：{shown}）"
    else:
        worktree = "clean"

    remote_head, verified, remote_note = "", False, ""
    try:
        ls = _run("git", "ls-remote", args.remote, args.branch, timeout=20)
        if ls.returncode == 0 and ls.stdout.strip():
            remote_head = ls.stdout.split()[0].strip()
            verified = True
        else:
            remote_note = (ls.stderr or "ls-remote 无输出").strip().splitlines()[-1]
    except (subprocess.TimeoutExpired, OSError) as exc:
        remote_note = f"{type(exc).__name__}: {exc}"

    ahead_list: list[str] = []
    remote_ahead = "?"
    if verified:
        ancestor = _run("git", "merge-base", "--is-ancestor", remote_head, "HEAD")
        if ancestor.returncode == 0:
            remote_ahead = 0
            cnt = _run("git", "rev-list", "--count", f"{remote_head}..HEAD")
            n = int(cnt.stdout.strip()) if cnt.returncode == 0 and cnt.stdout.strip() else -1
            if n > 0:
                ahead_list = _run("git", "log", f"{remote_head}..HEAD", "--oneline",
                                  ).stdout.strip().splitlines()
        else:
            cnt = _run("git", "rev-list", "--count", f"HEAD..{remote_head}")
            remote_ahead = (cnt.stdout.strip()
                            if cnt.returncode == 0 else "≥1（远端对象不在本地，需 fetch 才能列明）")

    if not verified:
        sync = "REMOTE_UNVERIFIED"
    elif local_head == remote_head:
        sync = "SYNCED"
    else:
        sync = "UNSYNCED"

    print("LOCAL_HEAD:      " + local_head + "  （" + local_short + "）")
    if verified:
        print("REMOTE_HEAD:     " + remote_head + "  （ls-remote 实测）")
    else:
        print("REMOTE_HEAD:     REMOTE_UNVERIFIED（无法验证远端：" + remote_note + "）")
        track = _run("git", "rev-parse", f"{args.remote}/{args.branch}")
        if track.returncode == 0:
            print("                 [参考·本地缓存引用口径，非实测] "
                  + args.remote + "/" + args.branch + " = " + track.stdout.strip())
    print("WORKTREE:        " + worktree)
    if verified:
        print("LOCAL_AHEAD:     " + (str(len(ahead_list)) if ahead_list else "0"))
        for ln in ahead_list:
            print("  · " + ln)
        print("REMOTE_AHEAD:    " + str(remote_ahead))
    print("SYNC_STATUS:     " + sync)
    if sync == "UNSYNCED":
        print("⚠ 当前工作内容尚未与远端 " + args.remote + "/" + args.branch +
              " 同步：本地提交在推送前不是远端可验证事实，报告与评审须如实标注。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
