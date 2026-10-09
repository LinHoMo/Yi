# -*- coding: utf-8 -*-
"""文档死链门（tools/check_doc_deadlinks.py，根门 `[1b-2]`）的负例自证。

AGENTS.md §四.8：新挂/新修的门必须做负例自证，并且**撤掉负例后复绿**。
本文件把 2026-10-09 补的两类能力钉住：

  ① 扫描面：`llms.txt`（原被 `.txt` 后缀一刀切排除，**永不入扫**）、
     `disciplines/*/SKILL.md`、`skills/*/SKILL.md`（原不在 glob 清单里）
     ——这三类正是任务 AI 的入口、路径引用最密处；
  ② 新判据：被活跃文档点名的仓库内路径若**未被 git 追踪**即判红
     （实测：未入库的 `docs/audits/*.md` 让门本地绿、干净 clone 红，
      而 `ci.yml` 正是在干净 checkout 上跑 `--full`）。

既有语义一并测住（防止扩面时把豁免语义改坏）：文档里举例用的假路径以 `__`
双下划线前缀豁免，**单下划线仍是真死链**——`FAKE_PATH` 只认双下划线。

探针一律写在临时树里（必要时临时 `git init` 一座小仓库），不碰工作区。
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "yi_deadlinks_under_test", ROOT / "tools" / "check_doc_deadlinks.py")
dl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dl)

GIT_OK = shutil.which("git") is not None


@pytest.fixture()
def tree(tmp_path):
    """返回一个 builder：写若干文件，可选 git init + add，然后跑扫描。"""
    real_root = dl.ROOT

    def build(files: dict[str, str], *, git_add: list[str] | None = None):
        for rel, body in files.items():
            p = tmp_path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        if git_add is not None:
            assert GIT_OK, "git 不可用（本用例需要它）"
            subprocess.run(["git", "-C", str(tmp_path), "init", "--quiet"],
                           capture_output=True, timeout=60)
            if git_add:
                subprocess.run(["git", "-C", str(tmp_path), "add", *git_add],
                               capture_output=True, timeout=60)
        return tmp_path

    yield build
    dl.ROOT = real_root
    dl._TRACKED_SET = None
    dl.GIT_STATE = "unknown"


def _scan(root: Path):
    return dl.run_scan(root)


def test_active_globs_cover_entry_documents():
    """判据 0：三类入口文档必须**在清单里**（不在清单里则写多少死链都不报警）。"""
    assert "llms.txt" in dl.ACTIVE_GLOBS
    assert "disciplines/*/SKILL.md" in dl.ACTIVE_GLOBS
    assert "skills/*/SKILL.md" in dl.ACTIVE_GLOBS
    # `.txt` 的泛排除不许被取消（书源 *.txt 一旦入扫会刷出成千上万条假引用），
    # 扩面走"逐个点名的例外"。
    assert ".txt" in dl.EXCLUDE_SUFFIX
    assert dl.ALWAYS_SCAN_NAMES == {"llms.txt"}


def test_llms_txt_is_scanned_and_bites(tree):
    """该抓的必须抓到：`llms.txt` 里的死链必须判红（旧版因 `.txt` 排除永不入扫）。"""
    root = tree({
        "llms.txt": "先读 `docs/_no_such_from_llms.md`，再读 `AGENTS.md`\n",
        "AGENTS.md": "# 真文件\n",
    })
    rc, dead, n_files, _untracked = _scan(root)
    assert rc == 1, dead
    assert any("_no_such_from_llms" in d[2] for d in dead), dead
    assert n_files >= 2


def test_discipline_and_skill_shell_md_are_scanned(tree):
    """该抓的必须抓到：`disciplines/*/SKILL.md` 与 `skills/*/SKILL.md` 里的死链判红。"""
    root = tree({
        "disciplines/ming/SKILL.md": "口径见 `docs/_no_such_in_disc_skill.md`\n",
        "skills/ming/SKILL.md": "口径见 `docs/_no_such_in_skill_shell.md`\n",
    })
    _rc, dead, _n, _u = _scan(root)
    refs = [d[2] for d in dead]
    assert any("_no_such_in_disc_skill" in r for r in refs), refs
    assert any("_no_such_in_skill_shell" in r for r in refs), refs


@pytest.mark.skipif(not GIT_OK, reason="需要 git")
def test_untracked_reference_is_red_and_tracked_one_is_not(tree):
    """新判据两侧：未入库目标判红并报出引用处；已入库目标不误报。"""
    root = tree({
        "docs/audits/_present_but_untracked.md": "# 本机有、库里没有\n",
        "docs/committed_target.md": "# 已入库\n",
        "docs/cite_both.md":
            "引用一：`docs/audits/_present_but_untracked.md`\n"
            "引用二：`docs/committed_target.md`\n",
    }, git_add=["docs/committed_target.md", "docs/cite_both.md"])
    rc, dead, _n, untracked = _scan(root)
    assert rc == 1, (dead, untracked)
    assert any("_present_but_untracked" in u[2] for u in untracked), untracked
    assert not any("committed_target" in u[2] for u in untracked), untracked
    # 引用处必须报出「谁在哪一行点了这个名」
    hit = [u for u in untracked if "_present_but_untracked" in u[2]][0]
    assert hit[0].endswith("cite_both.md") and hit[1] == 1, hit
    # 真死链桶不许被污染（目标存在，只是没入库）
    assert not any("_present_but_untracked" in d[2] for d in dead), dead


@pytest.mark.skipif(not GIT_OK, reason="需要 git")
def test_tracked_reference_passes_clean(tree):
    """撤掉负例后复绿：全部引用目标都已入库 ⇒ 退出码 0。"""
    root = tree({
        "docs/target.md": "# 在库\n",
        "docs/cite.md": "见 `docs/target.md`\n",
    }, git_add=["docs/target.md", "docs/cite.md"])
    rc, dead, _n, untracked = _scan(root)
    assert rc == 0, (dead, untracked)


def test_git_unavailable_is_disclosed_not_silently_passing(tree, monkeypatch, tmp_path):
    """不是 git 仓库时：不许把"没法判"说成"判过了"——必须有 GIT_STATE 披露行。"""
    root = tree({
        "docs/target.md": "# 存在但无 git\n",
        "docs/cite.md": "见 `docs/target.md`\n",
    })  # 不 git init
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc, _dead, _n, untracked = _scan(root)
    out = buf.getvalue()
    assert rc == 0 and not untracked        # 未知状态不判败（不冤枉非 git 环境）
    assert "git 不可用" in out, out          # 但必须显式说明这条判据没执行
    assert dl.GIT_STATE == "unavailable"


def test_fake_path_exemption_still_single_underscore_bites(tree):
    """既有豁免语义不许被扩面改动破坏：`__` 假路径豁免、单下划线仍是真死链。"""
    root = tree({
        "docs/a.md": "举例写法：`docs/__fake_example.md`\n",
        "docs/b.md": "真死链：`docs/_no_such_single.md`\n",
    })
    _rc, dead, _n, _u = _scan(root)
    refs = [d[2] for d in dead]
    assert not any("__fake_example" in r for r in refs), refs
    assert any("_no_such_single" in r for r in refs), refs


def test_zero_files_scanned_is_not_green(tree):
    """扫到 0 份文档＝路径解析错了，必须退出码 2 而不是"全部通过"。"""
    root = tree({"notes/target.md": "# 在\n"})
    rc, _dead, n_files, _u = _scan(root / "no_such_dir")
    assert rc == 2 and n_files == 0


def test_built_in_selftest_still_passes():
    """工具自带的 --selftest（负例必须全被抓）在改完后仍须为 0。"""
    assert dl.selftest() == 0
