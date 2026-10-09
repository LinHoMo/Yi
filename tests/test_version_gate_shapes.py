# -*- coding: utf-8 -*-
"""`tools/version_gate.py` 的四种同步形态都必须报出**实测计数**。

回归的缺陷（2026-10-09 实测）：旧实现只在"远端是本地祖先"这一支里数 LOCAL_AHEAD，
历史被重写（双向分叉）时打出 `LOCAL_AHEAD: 0`——本地当时实有 11 个远端不包含的提交。
§七 把本工具定为 HEAD 数值的唯一真值源，它自己报 0 就是把假事实复制进每一轮轮报，
而且 0 看起来比"没算"更像结论。

用**本地文件远端**跑，全程不联网：网络与代理是否可达属于环境，形态判定不该依赖它。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "tools" / "version_gate.py"


def _git(cwd: Path, *args: str) -> str:
    p = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@e", *args],
        cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=60)
    assert p.returncode == 0, f"git {' '.join(args)} 失败：{p.stdout}{p.stderr}"
    return p.stdout.strip()


def _mk(tmp_path: Path):
    bare = tmp_path / "up.git"
    bare.mkdir()
    _git(bare, "init", "--bare", "-b", "main")
    work = tmp_path / "work"
    work.mkdir()
    _git(work, "init", "-b", "main")
    _git(work, "remote", "add", "origin", str(bare))
    return work


def _commit(work: Path, name: str) -> str:
    (work / f"{name}.txt").write_text(name, encoding="utf-8")
    _git(work, "add", "-A")
    _git(work, "commit", "-m", name)
    return _git(work, "rev-parse", "HEAD")


def _gate(work: Path) -> str:
    p = subprocess.run([sys.executable, str(GATE)], cwd=str(work),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    assert p.returncode == 0, p.stdout + p.stderr
    return p.stdout


def _val(out: str, key: str) -> str:
    for ln in out.splitlines():
        if ln.startswith(key):
            return ln.split(":", 1)[1].strip()
    raise AssertionError(f"输出里没有 {key}：\n{out}")


def test_synced_reports_zero_both_sides(tmp_path):
    work = _mk(tmp_path)
    _commit(work, "A")
    _git(work, "push", "-u", "origin", "main")
    out = _gate(work)
    assert _val(out, "SYNC_STATUS") == "SYNCED"
    assert _val(out, "LOCAL_AHEAD") == "0"
    assert _val(out, "REMOTE_AHEAD") == "0"


def test_local_ahead_only(tmp_path):
    work = _mk(tmp_path)
    _commit(work, "A")
    _git(work, "push", "-u", "origin", "main")
    _commit(work, "B")
    _commit(work, "C")
    out = _gate(work)
    assert _val(out, "SYNC_STATUS") == "UNSYNCED"
    assert _val(out, "LOCAL_AHEAD") == "2"
    assert _val(out, "REMOTE_AHEAD") == "0"


def test_diverged_history_is_not_reported_as_zero_ahead(tmp_path):
    """双向分叉：本地把历史重写后，两侧都有对方没有的提交。

    旧实现在这里打 `LOCAL_AHEAD: 0`（因为"远端是本地祖先"不成立，那一支根本没跑）。
    """
    work = _mk(tmp_path)
    _commit(work, "A")
    _commit(work, "B")          # 远端将有 A、B
    _git(work, "push", "-u", "origin", "main")
    root = _git(work, "rev-list", "--max-parents=0", "main")
    _git(work, "reset", "--hard", root)      # 回到 A
    _commit(work, "C")                       # 本地改成 A、C、D
    _commit(work, "D")
    out = _gate(work)
    assert _val(out, "LOCAL_AHEAD") == "2", "重写后的本地提交必须被数出来，不得报 0"
    assert _val(out, "REMOTE_AHEAD") == "1"
    assert _val(out, "SYNC_STATUS") == "UNSYNCED"
    assert "DIVERGED" in out and "两侧历史互不包含" in out, \
        "分叉必须显式标注，不能只说「尚未同步」让人以为推一下就完"


def test_unreachable_remote_is_unverified_not_synced(tmp_path):
    work = _mk(tmp_path)
    _commit(work, "A")
    _git(work, "push", "-u", "origin", "main")
    _git(work, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    out = _gate(work)
    assert _val(out, "SYNC_STATUS") == "REMOTE_UNVERIFIED"
    assert "SYNCED" not in _val(out, "SYNC_STATUS")
