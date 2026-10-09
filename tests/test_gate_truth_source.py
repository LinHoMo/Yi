# -*- coding: utf-8 -*-
"""内核唯一真值源门（tools/check.py [1]「内核规则表无学科复制」）的负例自证。

AGENTS.md §四.8：新修的门必须做负例自证——往扫描面里塞一个**明知是副本**的表，
确认门真的判红并报出 `path:line`，再撤掉；同时"全绿的新门先怀疑"，所以两侧都测：
该抓的必须抓到、正常代码不许误报。

探针全部写在**临时树**里（`check.SCAN_ROOTS_OVERRIDE` 注入），绝不往仓库
`disciplines/`、`tools/` 植文件——并行批次会共用工作区，撤不干净的负例就是事故。

2026-10-09 修掉的四种抓不到的形态（每种都有对应负例）：
  ① 表名名单手写 35 个，AGENTS.md §二 点名的 NAJIA_BRANCHES/TOMB_MAP/TIAO_HOU/JIE_SHA
     不在名单里 → 名单改为从 core 运行期反射；
  ② `=` 后必须是 `[`/`{` → `LIU_QIN = ("比肩", …)` 逃逸；注解式 `X: dict = {` 被锚绕过；
  ③ 干支串拆两段拼接绕过逐行正则 → 改为 AST 折叠后与 core 反射序列比对；
  ④ 改名副本判据是逐字节相等 → 改序/改一格/取子集必逃逸；core 指纹取空即整条静默空转。
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "core") not in sys.path:
    sys.path.insert(0, str(ROOT / "core"))

_spec = importlib.util.spec_from_file_location("yi_check_under_test", ROOT / "tools" / "check.py")
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)

from yishu_core.relations import LIUQIN_NAMES  # noqa: E402
from yishu_core.symbols import (  # noqa: E402
    EARTHLY_BRANCHES, HEAVENLY_STEMS, XUN_KONG,
)

STEM_SEQ = "".join(HEAVENLY_STEMS)
BRANCH_SEQ = "".join(EARTHLY_BRANCHES)


@pytest.fixture()
def gate(tmp_path, monkeypatch):
    """把真值源门的扫描根换到临时树（core 侧仍指真仓库：真值基线必须是真的）。"""
    disc = tmp_path / "disciplines"
    tools = tmp_path / "tools"
    disc.mkdir()
    tools.mkdir()
    monkeypatch.setattr(check, "SCAN_ROOTS_OVERRIDE", [disc, tools])
    check._NAMES_CACHE.clear()
    check._CORE_LIB_CACHE.clear()

    def plant(body: str, *, where: str = "disciplines", name: str = "probe.py") -> Path:
        p = (disc if where == "disciplines" else tools) / name
        p.write_text(body, encoding="utf-8")
        return p

    yield plant
    check._NAMES_CACHE.clear()
    check._CORE_LIB_CACHE.clear()


def _hits(fails: list[str], needle: str) -> list[str]:
    return [f for f in fails if needle in f]


# ───────────────────────── 该抓的必须抓到 ─────────────────────────

def test_reflected_name_not_in_legacy_list_is_caught(gate):
    """形态①：AGENTS.md §二 点名、旧手写名单里没有的表必须被抓，且报出 path:line。"""
    p = gate("TOMB_MAP = {'火': '戌', '水': '辰', '木': '未', '金': '丑', '土': '辰'}\n")
    fails = check.check_core_tables()
    hit = _hits(fails, "TOMB_MAP")
    assert hit, fails
    assert "probe.py:1" in hit[0], hit
    assert str(p.name) in hit[0]


def test_all_four_named_tables_in_agents_md_are_caught(gate):
    """形态①：§二 亲自点名的四张表逐个验证（JIE_SHA/TIAO_HOU/NAJIA_BRANCHES/TOMB_MAP）。"""
    for i, name in enumerate(("JIE_SHA", "TIAO_HOU", "NAJIA_BRANCHES", "TOMB_MAP")):
        gate(f"{name} = {{}}\n", name=f"probe_{i}.py")
        fails = check.check_core_tables()
        assert _hits(fails, name), (name, fails)


def test_tuple_form_is_caught(gate):
    """形态②：`LIU_QIN = ("比肩", …)`——旧判据要求 `=` 后是 `[`/`{`，tuple 逃逸。"""
    gate('LIU_QIN = ("比肩", "劫财", "食神", "伤官", "正财")\n')
    assert _hits(check.check_core_tables(), "LIU_QIN")


def test_annotated_assignment_is_caught(gate):
    """形态②：注解式 `X: dict[...] = {` 被旧锚 `^\\s*(NAME)\\s*=` 绕过。"""
    gate("TIAO_HOU: dict[str, dict[str, str]] = {'寅': {'甲': '丁'}}\n")
    assert _hits(check.check_core_tables(), "TIAO_HOU")


def test_tools_layer_is_scanned_too(gate):
    """§二 声称覆盖 tools/**（2026-10-08 之前那条覆盖面是空话）。"""
    gate("XUN_KONG = {}\n", where="tools")
    assert _hits(check.check_core_tables(), "XUN_KONG")


def test_ganzhi_concat_split_is_caught(gate):
    """形态③：`"甲乙丙丁" + "戊己庚辛壬癸"` 拆两段拼接绕过逐行正则。"""
    half = len(STEM_SEQ) // 2
    gate("S = %r + %r\n" % (STEM_SEQ[:half], STEM_SEQ[half:]))
    fails = check.check_core_string_tables()
    assert _hits(fails, "复制内核干支序列"), fails
    assert "probe.py:1" in fails[0], fails


def test_ganzhi_split_into_list_is_caught(gate):
    """形态③ 变体：十二地支拆成三段塞进 list。"""
    third = len(BRANCH_SEQ) // 3
    gate("L = [%r, %r, %r]\n"
         % (BRANCH_SEQ[:third], BRANCH_SEQ[third:2 * third], BRANCH_SEQ[2 * third:]))
    assert _hits(check.check_core_string_tables(), "复制内核干支序列")


def test_ganzhi_implicit_adjacent_concat_is_caught(gate):
    """形态③ 变体：相邻字面量隐式拼接（解析器合成一个常量）。"""
    half = len(STEM_SEQ) // 2
    gate("S = (%r\n     %r)\n" % (STEM_SEQ[:half], STEM_SEQ[half:]))
    assert _hits(check.check_core_string_tables(), "复制内核干支序列")


def test_renamed_exact_copy_is_caught(gate):
    """形态④ 档 1：换名 + 内容逐字节相同（历史事故形态 XUN_KONG → EMPTY_DEATH）。"""
    gate("EMPTY_DEATH = %s\n" % json.dumps(dict(XUN_KONG), ensure_ascii=False))
    assert _hits(check.check_core_table_renames(), "EMPTY_DEATH")


def test_renamed_reordered_list_is_caught(gate):
    """形态④ 档 2：换名 + 改序（list 用排序无关指纹）。"""
    gate("REL_REV = %r\n" % (list(reversed(LIUQIN_NAMES)),))
    fails = check.check_core_table_renames()
    assert _hits(fails, "REL_REV"), fails
    assert any("仅顺序不同" in f for f in fails), fails


def test_renamed_one_value_changed_is_caught(gate):
    """形态④ 档 3：键集与 core 全同、只改一格值。"""
    mutated = dict(XUN_KONG)
    mutated[next(iter(mutated))] = ["错", "错"]
    gate("MY_XUNKONG = %s\n" % json.dumps(mutated, ensure_ascii=False))
    fails = check.check_core_table_renames()
    assert _hits(fails, "疑似改值复制内核表 MY_XUNKONG"), fails


def test_subset_copy_is_caught(gate):
    """形态④ 档 4：键为 core 真值表的子集且交集值全同。"""
    sub = {k: XUN_KONG[k] for k in list(XUN_KONG)[:3]}
    gate("PARTIAL = %s\n" % json.dumps(sub, ensure_ascii=False))
    fails = check.check_core_table_renames()
    assert _hits(fails, "子集副本 PARTIAL"), fails


def test_function_scope_copy_is_caught(gate):
    """作用域盲区：函数内的字面量副本也得抓（模块级门看不见它）。"""
    gate("def build():\n    xun_kong_local = %s\n    return xun_kong_local\n"
         % json.dumps(dict(XUN_KONG), ensure_ascii=False))
    assert _hits(check.check_core_tables_in_scope(), "xun_kong_local")


def test_empty_core_library_is_a_failure_not_a_pass(tmp_path, monkeypatch):
    """形态④ 的静默空转：core 指纹取空时旧门 `return []`＝整条门悄悄关掉。"""
    empty_pkg = tmp_path / "empty_pkg"
    empty_pkg.mkdir()
    monkeypatch.setattr(check, "CORE_PKG", empty_pkg)
    monkeypatch.setattr(check, "_CORE_ROOT", tmp_path)
    monkeypatch.setattr(check, "SCAN_ROOTS_OVERRIDE", [tmp_path / "src"])
    (tmp_path / "src").mkdir()
    check._CORE_LIB_CACHE.clear()
    fails = check.check_core_table_renames()
    check._CORE_LIB_CACHE.clear()
    assert fails, "真值库取空必须判红，不得静默返回「无失败」"


def test_core_reflection_failure_is_reported(monkeypatch, gate):
    """core import 失败 → 名单不完整必须判红，不能拿半截名单继续打勾。"""
    class _Boom:
        @staticmethod
        def import_module(name):
            raise RuntimeError(f"simulated core import failure: {name}")

    monkeypatch.setattr(check, "importlib", _Boom)
    names, fails = check.core_table_names(refresh=True)
    assert names == set(), names
    assert fails, "反射失败必须出现在失败明细里"
    check._NAMES_CACHE.clear()


def test_scanning_nothing_is_a_failure_not_a_pass(monkeypatch, tmp_path):
    """「0 结果」不能当成「干净」（§四.8：扫了 0 份文件 ≠ 仓库没文档）。"""
    empty = tmp_path / "nowhere"
    empty.mkdir()
    monkeypatch.setattr(check, "SCAN_ROOTS_OVERRIDE", [empty])
    fails = check.check_core_tables()
    assert any("扫描 0 个文件" in f for f in fails), fails


def test_allow_entry_is_exact_and_does_not_swallow_siblings(monkeypatch, gate):
    """豁免面必须是逐条精确的：同名的别处副本照样判红。"""
    gate("XUN_KONG = {}\n", name="probe_allow.py")
    gate("XUN_KONG = {}\n", name="probe_other.py")
    monkeypatch.setitem(check.CORE_TABLE_ALLOW, "probe_allow.py::XUN_KONG", "自证用豁免")
    fails = check.check_core_tables()
    hits = _hits(fails, "XUN_KONG")
    assert any("probe_other.py" in f for f in hits), fails
    assert not any("probe_allow.py" in f for f in hits), fails


# ───────────────────────── 正常代码不许误报 ─────────────────────────

def test_core_import_and_join_is_not_flagged(gate):
    """AGENTS.md §二 钦定的正确范式（sync_tiaohou_engine.py 抄的那份）不得被判红。"""
    gate("from yishu_core.symbols import HEAVENLY_STEMS\n"
         'STEMS = "".join(HEAVENLY_STEMS)\n')
    assert check.check_core_tables() == [], check.check_core_tables()


def test_unrelated_local_tables_are_not_flagged(gate):
    """同样按五行取键、但表达另一张关系的本地表不得判成副本（旧噪声实测 108 处）。

    注意别拿 `{'木':'水',…}` 当例子——那正是 core 的 SHENG_WO（生我）本身，
    判红是对的（本测试初稿就把它当成了"无关表"，被自己的门纠了出来）。
    """
    gate("COLOR_OF_ELEMENT = {'木': '青', '火': '赤', '土': '黄', '金': '白', '水': '玄'}\n"
         "MONTH_WORD = {1: '正月', 2: '二月', 3: '三月'}\n"
         "BRANCH_OF_MONTH = {1: '寅', 2: '卯', 3: '辰', 4: '巳', 5: '午', 6: '未',\n"
         "                  7: '申', 8: '酉', 9: '戌', 10: '亥', 11: '子', 12: '丑'}\n")
    assert check.check_core_tables() == [], check.check_core_tables()


def test_regex_partial_sequence_is_not_flagged(gate):
    """正则字符类里的整串地支（`[子丑…]`）不是"整份序列字面量"——equality 语义下不误报。
    现仓这类正则有 14 处（chart/analyze 的取值字符类），改判据时先把它们测住。"""
    gate("PAT = r'[%s]'\n" % BRANCH_SEQ)
    assert check.check_core_string_tables() == []


def test_real_repository_has_no_copies():
    """真仓当前必须全绿：反射名单 + 四档内容 + 拼接归一化一起上，零新增假阳性。"""
    check._NAMES_CACHE.clear()
    check._CORE_LIB_CACHE.clear()
    assert check.SCAN_ROOTS_OVERRIDE is None
    fails = check.check_core_tables()
    assert fails == [], fails
