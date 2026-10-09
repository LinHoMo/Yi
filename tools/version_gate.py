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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))


def _run(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def main() -> int:
    # 本文件要打印 ⚠ 与整块中文，且 §七 要求"每轮 OBSERVE 第一步跑"——在没有
    # PYTHONIOENCODING 的裸 GBK 控制台上会直接 UnicodeEncodeError 退 1（回归测试
    # tests/test_version_gate_shapes.py 实测抓到过）。与仓内其他工具同一处理。
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()
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
    local_ahead = 0
    if verified:
        # 两侧计数都要**无条件**算。旧实现只在"远端是本地祖先"这一支里数本地领先，
        # 于是历史被重写（双向分叉）时打出 `LOCAL_AHEAD: 0`——本地明明有 11 个远端没有的
        # 提交。0 是没算，不是实测为 0；本文件是 §七 指定的 HEAD 数值唯一真值源，
        # 它自己报假数会把假事实复制进每一轮的轮报。
        ca = _run("git", "rev-list", "--count", f"{remote_head}..HEAD")
        if ca.returncode == 0 and ca.stdout.strip():
            local_ahead = int(ca.stdout.strip())
        if local_ahead > 0:
            ahead_list = _run("git", "log", f"{remote_head}..HEAD",
                              "--oneline").stdout.strip().splitlines()
        cb = _run("git", "rev-list", "--count", f"HEAD..{remote_head}")
        if cb.returncode == 0 and cb.stdout.strip():
            remote_ahead = int(cb.stdout.strip())
        else:
            remote_ahead = "≥1（远端对象不在本地，需 fetch 才能列明）"

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
        print("LOCAL_AHEAD:     " + str(local_ahead))
        for ln in ahead_list[:12]:
            print("  · " + ln)
        if len(ahead_list) > 12:
            print(f"  · …（其余 {len(ahead_list) - 12} 条略）")
        print("REMOTE_AHEAD:    " + str(remote_ahead))
    print("SYNC_STATUS:     " + sync)
    if sync == "UNSYNCED":
        if isinstance(local_ahead, int) and local_ahead > 0 and \
                isinstance(remote_ahead, int) and remote_ahead > 0:
            print(f"DIVERGED:        双向分叉——本地有 {local_ahead} 个远端没有的提交，"
                  f"远端有 {remote_ahead} 个本地历史不包含的提交"
                  f"（不是「落后待推」，两侧历史互不包含；推送方式须人工决定）")
        print("⚠ 当前工作内容尚未与远端 " + args.remote + "/" + args.branch +
              " 同步：本地提交在推送前不是远端可验证事实，报告与评审须如实标注。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
