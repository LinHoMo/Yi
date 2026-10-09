# -*- coding: utf-8 -*-
"""`[7d] check_eval_scores` 的牙口自证（AGENTS.md §四.8）。

背景：门批次把 `[7d]` 从"只看 eval.py 退出码"改成"每科必须真的报出 tune 与 holdout"，
但判据里 `EVAL_SCORE` 的 group(2) 是**分数**、group(1) 才是 split 名，取错格导致两科
永远被报"没出分"。本测试同时钉住两件事：
  ① 正例——两科四分齐备必须无失败（防止修反）；
  ② 负例——缺任一 split、整科消失、只有段落头没有读数，都必须判红（防止又退回"退出 0 即绿"）。
断言按"点到了哪一科"来判，不锁失败条数（一条消息可同时点名两个 split，条数不是契约）。
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))


def _load_check():
    spec = importlib.util.spec_from_file_location("ck_for_eval_scores", ROOT / "tools" / "check.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


ck = _load_check()

SCORE_L = "=== %s [strict] 平均分 = %s  (n=%s，最低 0.0，最高 100.0) ==="
FULL = "\n".join([
    "=== liuyao · tune ===", SCORE_L % ("tune", "97.2%", 20),
    "=== liuyao · holdout ===", SCORE_L % ("holdout", "90.2%", 12),
    "=== ming · tune ===", SCORE_L % ("tune", "100.0%", 30),
    "=== ming · holdout ===", SCORE_L % ("holdout", "96.2%", 246),
    "默认集合读数：liuyao/tune 97.2% (n=20)；liuyao/holdout 90.2% (n=12)；"
    "ming/tune 100.0% (n=30)；ming/holdout 96.2% (n=246)",
]) + "\n"


def _hits(fails, disc):
    return [f for f in fails if f.startswith(disc + "：")]


def test_positive_all_scores_present():
    """两科四分齐备 → 必须 0 失败（group 取错时这里会全红）。"""
    assert ck.check_eval_scores(FULL) == []


def test_missing_one_split_is_red():
    """去掉 ming 的 holdout 读数 → 必须点名 ming。"""
    out = FULL.replace("=== ming · holdout ===\n" + (SCORE_L % ("holdout", "96.2%", 246)) + "\n", "")
    fails = ck.check_eval_scores(out)
    assert _hits(fails, "ming"), fails
    assert any("holdout" in f for f in _hits(fails, "ming")), fails
    assert not _hits(fails, "liuyao"), fails


def test_missing_whole_discipline_is_red():
    """整科消失（ ming 的两段都没有）→ 必须点名 ming 且说出两个 split。"""
    out = "\n".join(l for l in FULL.splitlines()
                    if not l.startswith("=== ming") and "ming/" not in l) + "\n"
    fails = ck.check_eval_scores(out)
    assert _hits(fails, "ming"), fails
    assert all(sp in _hits(fails, "ming")[0] for sp in ("tune", "holdout")), fails


def test_headers_without_scores_are_red():
    """只有段落头、一条读数都没有 → 必须判红（这就是"扫空当通过"的老病灶）。"""
    out = "".join("=== %s · %s ===\n" % (d, s) for d in ("liuyao", "ming") for s in ("tune", "holdout"))
    fails = ck.check_eval_scores(out)
    assert fails, "扫空必须判红"
    assert _hits(fails, "liuyao") and _hits(fails, "ming"), fails


def test_empty_output_is_red():
    """eval.py 什么都没打 → 判红，不得静默放行。"""
    assert ck.check_eval_scores(""), "空输出必须判红"
