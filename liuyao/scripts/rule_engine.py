# -*- coding: utf-8 -*-
"""规则仲裁层（registry v2 执行体）。

阶段0最小闭环：把 detect_direction_caps 里的硬编码 if 判据，迁成 registry v2 JSON 条目，
由本引擎对盘面求值。目标——**纯重构、零输出漂移**：引擎产出的 cap dict 结构与原来完全一致
（rule_id/cap/src/reason_key/detail），step5 无感知。

依赖方向（无循环）：
    rule_engine ──import──> classical_enhancements_direction 的纯函数(_world_line/_month_state/_chong...)
    detect_direction_caps ──import──> rule_engine.evaluate_caps
    classical_enhancements_direction 不 import rule_engine。

v2 条目 schema（见 docs/RULE-ENGINE-REFACTOR-PLAN.md）：
    {rule_id, when{...}, gates{qcls_not/ug_cat_not/qcls_eq}, rescue_any[...],
     cap, detail_tmpl, source{...}, eval_dim}
when 只表达卦象静态事实；gates 表达适用情境域；rescue_any 表达"满足则解除"。
三者分离——这正是裸 if 里缠在一起的东西。
"""
from __future__ import annotations
import os as _ks_os, sys as _ks_os2, json as _json

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))
if _ks_d not in _ks_os2.path:
    _ks_os2.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel  # noqa: E402
_ensure_kernel(__file__)

from yishu_core.symbols import BRANCH_ELEMENTS, SHENG_CYCLE, KE_CYCLE  # noqa: E402
from classical_enhancements_direction import (  # noqa: E402  纯函数复用，无循环
    _world_line, _month_state, _chong, _broken, RANK,
)


# ── v2 规则库加载（带缓存）──────────────────────────────────────
_RULES_PATH = _ks_os.path.join(
    _ks_os.path.dirname(_ks_d), "data", "rules", "rule_engine_v2.json")
_cache = {"rules": None, "mtime": None}


def _load_rules() -> list[dict]:
    mt = _ks_os.path.getmtime(_RULES_PATH)
    if _cache["rules"] is None or _cache["mtime"] != mt:
        with open(_RULES_PATH, encoding="utf-8") as f:
            _doc = _json.load(f)
        _cache["rules"] = _doc.get("rules", []) if isinstance(_doc, dict) else _doc
        _cache["mtime"] = mt
    return _cache["rules"]


class _Ctx:
    """盘面上下文：预计算派生量，供谓词求值。"""

    def __init__(self, lines, step2, step4, month_branch, day_branch, empty_branches):
        self.lines = [y for y in (lines or []) if isinstance(y, dict)]
        self.step2 = step2 or {}
        self.month_branch = month_branch or ""
        self.day_branch = day_branch or ""
        self.empty = list(empty_branches or [])
        self.me = BRANCH_ELEMENTS.get(self.month_branch, "")
        self.de = BRANCH_ELEMENTS.get(self.day_branch, "")
        self.qcls = str(self.step2.get("question_class") or "")
        self.ug_cat = str(self.step2.get("use_god_category") or "")
        self.ug_el = str(self.step2.get("use_god_element") or "")
        self.changes = {int(d.get("position", -1)): d
                        for d in ((step4 or {}).get("details") or [])
                        if isinstance(d, dict)}
        self.world = _world_line(self.lines)
        self.wpos = int(self.world.get("position", -1)) if self.world else -1
        self.wb = (self.world or {}).get("earthly_branch", "")
        self.we = BRANCH_ELEMENTS.get(self.wb, "")
        # ── 扩展派生量（阶段1）──
        self.world_six_rel = (self.world or {}).get("six_relation") or ""
        self.world_changed_rel = (self.world or {}).get("changed_six_relation") or ""
        self.moving_rels = {str(y.get("six_relation") or "") for y in self.lines if y.get("is_moving")}
        self.changed_rels = {str(y.get("changed_six_relation") or "") for y in self.lines if y.get("is_moving")}
        self.all_rels = {str(y.get("six_relation") or "") for y in self.lines}

    # ── 派生量 ──
    @property
    def world_ct(self) -> str:
        return (self.changes.get(self.wpos, {}) or {}).get("change_type") or ""

    @property
    def world_chg_branch(self) -> str:
        return (self.changes.get(self.wpos, {}) or {}).get("changed_branch") or ""

    @property
    def world_month_state(self) -> str:
        return _month_state(self.we, self.me)

    @property
    def world_broken(self) -> bool:
        return bool(self.wb) and _broken(self.wb, self.month_branch, self.empty)

    @property
    def day_ke_world(self) -> bool:
        return bool(self.de) and bool(self.we) and KE_CYCLE.get(self.de) == self.we

    @property
    def day_sheng_world(self) -> bool:
        return bool(self.de) and bool(self.we) and SHENG_CYCLE.get(self.de) == self.we

    @property
    def world_cai_element(self) -> str:
        """本宫之财＝世爻五行所克者（我克者为财）。"""
        return KE_CYCLE.get(self.we, "") if self.we else ""

    @property
    def day_is_world_cai(self) -> bool:
        """日辰即本宫之财（《增删卜易》L2342「得日月作财而合世」例外）。"""
        return bool(self.de) and bool(self.world_cai_element) and self.de == self.world_cai_element

    @property
    def month_is_world_cai(self) -> bool:
        return bool(self.me) and bool(self.world_cai_element) and self.me == self.world_cai_element

    def yongshen_moving_lines(self) -> list[dict]:
        return [y for y in self.lines
                if y.get("six_relation") == self.ug_cat and y.get("is_moving")]

    def line_matches(self, pred: dict) -> bool:
        """某爻是否满足 {six_relation?, is_moving?, earthly_branch?} 谓词。"""
        for k, want in pred.items():
            if k == "six_relation" and self._cur.get("six_relation") != want:
                return False
            if k == "is_moving" and bool(self._cur.get("is_moving")) != bool(want):
                return False
            if k == "earthly_branch" and self._cur.get("earthly_branch") != want:
                return False
        return True


# ── when 谓词求值 ──────────────────────────────────────────────
def _eval_when(ctx: _Ctx, when: dict) -> bool:
    for key, want in (when or {}).items():
        if key == "world_moving":
            if not (ctx.world and ctx.world.get("is_moving")):
                return False
        elif key == "world_change_type":
            if ctx.world_ct != want:
                return False
        elif key == "changed_branch_chongs_month":
            cb = ctx.world_chg_branch
            if not (cb and ctx.month_branch and _chong(cb, ctx.month_branch)):
                return False
        elif key == "yongshen_moving":
            if not ctx.yongshen_moving_lines():
                return False
        elif key == "yongshen_change_type_contains":
            hit = False
            for y in ctx.yongshen_moving_lines():
                ct = (ctx.changes.get(int(y.get("position", -1)), {}) or {}).get("change_type") or ""
                if want in ct:
                    hit = True
                    break
            if not hit:
                return False
        # ── 阶段1新增谓词 ──
        elif key == "world_six_relation":
            if ctx.world_six_rel != want:
                return False
        elif key == "world_changed_relation":
            if ctx.world_changed_rel != want:
                return False
        elif key == "world_month_state_in":
            if ctx.world_month_state not in (want or []):
                return False
        elif key == "world_broken":
            if ctx.world_broken != bool(want):
                return False
        elif key == "day_ke_world":
            if ctx.day_ke_world != bool(want):
                return False
        elif key == "day_sheng_world":
            if ctx.day_sheng_world != bool(want):
                return False
        elif key == "moving_relation":
            # want 为 str（存在）或 {"not": str}（不存在）
            if isinstance(want, dict):
                if want.get("not") in ctx.moving_rels:
                    return False
            elif want not in ctx.moving_rels:
                return False
        elif key == "moving_or_changed_relation":
            # 动爻或变爻出现该六亲：want=str(存在) / {"not": str}(都不存在)
            present = want in ctx.moving_rels or want in ctx.changed_rels
            if isinstance(want, dict):
                rel = want.get("not")
                if rel in ctx.moving_rels or rel in ctx.changed_rels:
                    return False
            elif not present:
                return False
        elif key == "any_relation":
            if want not in ctx.all_rels:
                return False
        elif key == "day_element_eq":
            if ctx.de != want:
                return False
        elif key == "month_element_eq":
            if ctx.me != want:
                return False
        elif key == "day_is_world_cai":
            if ctx.day_is_world_cai != bool(want):
                return False
        elif key == "month_is_world_cai":
            if ctx.month_is_world_cai != bool(want):
                return False
        else:
            # 未知谓词＝规则写错，按"不命中"安全处理（宁可漏压不误压）
            return False
    return True


def _eval_gates(ctx: _Ctx, gates: dict) -> bool:
    g = gates or {}
    if "qcls_not" in g and ctx.qcls in g["qcls_not"]:
        return False
    if "qcls_eq" in g and ctx.qcls != g["qcls_eq"]:
        return False
    if "ug_cat_not" in g and ctx.ug_cat in g["ug_cat_not"]:
        return False
    if "ug_cat_eq" in g and ctx.ug_cat != g["ug_cat_eq"]:
        return False
    return True


def _eval_rescue(ctx: _Ctx, rescue_any: list) -> bool:
    """任一救应条件满足＝规则被解除（不压）。"""
    for pred in (rescue_any or []):
        # 形式A：{"line_exists": {six_relation, is_moving}} —— 某爻存在
        if "line_exists" in pred:
            need = pred["line_exists"]
            for y in ctx.lines:
                ok = True
                for k, want in need.items():
                    if k == "six_relation" and y.get("six_relation") != want:
                        ok = False; break
                    if k == "is_moving" and bool(y.get("is_moving")) != bool(want):
                        ok = False; break
                if ok:
                    return True
        else:
            # 形式B：直接复用 when 谓词（如 day_is_world_cai）——满足则解救
            if _eval_when(ctx, pred):
                return True
    return False


def _detail(rule: dict, ctx: _Ctx) -> str:
    """detail_tmpl 里的 {占位} 用派生量替换。"""
    tmpl = rule.get("detail_tmpl", "")
    mstate = _month_state(ctx.we, ctx.me)
    ctx_vars = {
        "world_branch": ctx.wb,
        "world_month_state": mstate,
        "world_change_type": ctx.world_ct,
        "world_chg_branch": ctx.world_chg_branch,
        "ug_cat": ctx.ug_cat,
        "world_moving_phrase": "且发动" if (ctx.world and ctx.world.get("is_moving")) else "安静",
    }
    try:
        return tmpl.format(**ctx_vars)
    except Exception:
        return tmpl


def evaluate_caps(lines, step2, step4, month_branch, day_branch, empty_branches) -> list[dict]:
    """对盘面求值所有 v2 规则，返回命中的 cap dict 列表（结构与旧 detect 一致）。"""
    ctx = _Ctx(lines, step2, step4, month_branch, day_branch, empty_branches)
    caps = []
    for rule in _load_rules():
        if not _eval_gates(ctx, rule.get("gates")):
            continue
        if not _eval_when(ctx, rule.get("when")):
            continue
        if _eval_rescue(ctx, rule.get("rescue_any")):
            continue
        # cap 可为字符串（固定档）或 {"moving":..,"still":..}（按世爻动静分档）
        cap_field = rule["cap"]
        if isinstance(cap_field, dict):
            cap_val = cap_field.get("moving") if (ctx.world and ctx.world.get("is_moving")) else cap_field.get("still")
        else:
            cap_val = cap_field
        caps.append({
            "rule_id": rule["rule_id"],
            "cap": cap_val,
            "src": (rule.get("source") or {}).get("locator", ""),
            "reason_key": rule.get("reason_key", "shi_hua_gui"),
            "detail": _detail(rule, ctx),
        })
    return caps
