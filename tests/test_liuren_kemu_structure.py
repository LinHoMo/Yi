# -*- coding: utf-8 -*-
"""六壬结构课目命中锁定测试（Round 3 + Round 5 新增的 6 项结构判据）。

只锁 6 项结构 hit 的加法正确性：给定特定 san_chuan，recognize() 必须包含
对应的结构课目。测试用例用精心构造的 chart_out dict（不走真实排盘），
直接验证 hit() 分支逻辑，避免波动数据干扰。

本轮新增：
  进茹/退茹/进间/退间（Round 3，步长判据：三传支序 +/-1/+2）
  关格/稼穆（Round 5，集合条件：三传 ⊆ 四仲 / 三传 ⊆ 四季土）

⚠️ 加载路径：kemu.py 模块级 import `from jiuzongmen import …` 需要本科 scripts
目录在 sys.path 里才能解析。采用 tests/pathguard.py 的 discipline_scripts()
上下文管理器，退出时自动还掉 sys.path + 清掉缓存，不影响后续测试。
（与 tests/conftest.py 的"不裸 insert 后不还"约定完全一致。）
"""
from __future__ import annotations

import importlib.util as _ilu
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIUREN = ROOT / "disciplines" / "liuren"
DATA = LIUREN / "data"

# ── 装载 pathguard，再用 discipline_scripts() 隔离地加载 kemu ──
_spec = _ilu.spec_from_file_location(
    "yi_pathguard", Path(__file__).with_name("pathguard.py"))
_pg = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_pg)

with _pg.discipline_scripts("disciplines/liuren/scripts"):
    from kemu import recognize, IMPLEMENTED

_recog = recognize
_IMPLEMENTED = IMPLEMENTED

# 顺手加载 kemu.json 验证 entry 元数据
_kemu_entries = {
    e["name"]: e
    for e in json.loads((DATA / "kemu.json").read_text(encoding="utf-8"))["entries"]
}

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES as BR


def _make_chart(san: list[str], day_gz: str = "甲寅", tianpan: dict | None = None) -> dict:
    """构造能传入 recognize() 的最小 chart_out（仅结构 hit 需要字段）。"""
    if tianpan is None:
        tianpan = {b: b for b in BR}  # 伏吟式（地盘 = 天盘）
    return {
        "moment": {"day_ganzhi": day_gz, "hour_branch": day_gz[1]},
        "san_chuan": san,
        "tianpan": tianpan,
        "men": "贼克",
        "ke_name": "元首",
        "four_courses": [],
        "chuan_tianjiang": [],
    }


def _names(result: list[dict]) -> list[str]:
    return [k["name"] for k in result]


def _has_kemu(result: list[dict], name: str) -> bool:
    return name in _names(result)


# ──────────────────────────────────────────────────── 进茹 / 退茹
def test_jin_ru_forward_step():
    """支序 +1 相连：子→丑→寅 → 命中「进茹」+「联珠」"""
    result = _recog(_make_chart(["子", "丑", "寅"]))
    assert _has_kemu(result, "进茹"), f"「进茹」未命中: {_names(result)}"
    assert _has_kemu(result, "联珠"), f"「联珠」未命中: {_names(result)}"


def test_tui_ru_backward_step():
    """支序 -1 相连：寅→丑→子 → 命中「退茹」+「联珠」"""
    result = _recog(_make_chart(["寅", "丑", "子"]))
    assert _has_kemu(result, "退茹"), f"「退茹」未命中: {_names(result)}"


# ──────────────────────────────────────────────────── 进间 / 退间
def test_jian_jian_skip_one():
    """支序 +2 隔一位：子→寅→辰 → 命中「进间」"""
    result = _recog(_make_chart(["子", "寅", "辰"]))
    assert _has_kemu(result, "进间"), f"「进间」未命中: {_names(result)}"


def test_tui_jian_skip_one_reverse():
    """支序 -2 隔一位：辰→寅→子 → 命中「退间」"""
    result = _recog(_make_chart(["辰", "寅", "子"]))
    assert _has_kemu(result, "退间"), f"「退间」未命中: {_names(result)}"


# ──────────────────────────────────────────────────── 关格 / 稼穑
def test_guan_ge_all_si_zhong():
    """三传皆四仲（子午卯酉）：命中「关格」"""
    result = _recog(_make_chart(["子", "卯", "午"]))
    assert _has_kemu(result, "关格"), f"「关格」未命中: {_names(result)}"


def test_jia_se_all_si_ji():
    """三传皆季神（辰戌丑未）：命中「稼穑」"""
    result = _recog(_make_chart(["辰", "戌", "丑"]))
    assert _has_kemu(result, "稼穑"), f"「稼穑」未命中: {_names(result)}"


# ──────────────────────────────────────────────────── 非命中负例
def test_no_false_positive_for_partial_match():
    """二仲一非仲 → 不命中「关格」（必须三传全部集合成员）"""
    result = _recog(_make_chart(["子", "卯", "寅"]))
    assert not _has_kemu(result, "关格"), f"「关格」误报: {_names(result)}"
    assert not _has_kemu(result, "稼穑"), f"「稼穑」误报: {_names(result)}"


# ──────────────────────────────────────────────────── IMPLEMENTED 旗标自证
def test_new_structural_kemu_are_implemented():
    """6 项新结构课目必须全部在 IMPLEMENTED 中（防 flag 漏翻）。"""
    for name in ["进茹", "退茹", "进间", "退间", "关格", "稼穑"]:
        assert name in _IMPLEMENTED, f"{name} 不在 IMPLEMENTED 中"
        # kemu.json 里也必须是 implemented=True
        entry = _kemu_entries.get(name)
        assert entry is not None, f"{name} 在 kemu.json 中不存在"
        assert entry.get("implemented") is True, f"{name} implemented 应为 true"
