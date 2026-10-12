# -*- coding: utf-8 -*-
"""《易林补遗》门类定位映射查表层（**只定位、不断吉凶**）。

【OPT-yilin_buyi_dz-03 / -04 / -05，2026-10-07 新增】

本模块只提供**查表函数**，数据全在 `data/yilin_buyi_maps.json`
（SKILL.md：断语/引文进 data，代码只留算法）。四组映射：

  · 家宅三层分宫（源 L961「鬼是正厅，父为堂屋」/L964/L966）——「何人何物」；含**代占层与六爻分宫层互斥**的适用条件
  · 间爻四角色（源 L596/L1877/L2056/L1033）——媒妁/中保/中证/工匠
  · 外卦取事定方（《易林补遗》源L2234「凡占逃者在以何处，专以外卦推详」）——逃亡问**专以外卦**定八方
  · 六畜分爻分宫（《易林补遗》源L1160「初鸡二犬三猪四羊五牛六马，鸭同鸡位，猫共犬爻」）

**口径纪律（SKILL.md 铁律一/三）**：本层**只答「在何门类/何方/何物」**，
不答吉凶——原书的吉凶评断一律不入表（见 data 侧 `_meta.口径`）。
旺衰（有力/无力/空亡）属**机械层**已有的量，本层**不重复判、也不越界判**。
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = [
    "yilin_maps",
    "jiazai_yao_map",
    "jiazai_daizhan_map",
    "jianyao_role",
    "waigua_direction",
]

# 爻位数字 → 书源所用的汉字爻名（数据侧按「二爻」等汉字键存表）
_YAO_CN = {1: "初", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六"}

_MAPS: dict | None = None


def yilin_maps() -> dict:
    """懒加载 data/yilin_buyi_maps.json；缺文件返回 {}（不硬编一份）。"""
    global _MAPS
    if _MAPS is None:
        p = Path(__file__).resolve().parents[1] / "data" / "yilin_buyi_maps.json"
        try:
            _MAPS = json.loads(p.read_text(encoding="utf-8"))
        except OSError:
            _MAPS = {}
    return _MAPS


# ── 家宅三层分宫 ────────────────────────────────────────────────

def jiazai_yao_map(yao: int) -> list[str]:
    """家宅·六爻分宫（《易林补遗》源L964「初爻为基址、为井、为沟、为小口、又为鸡鹅鸭之类」）：爻位（1..6）→ 该爻所主之物/之人。

    ⚠️ 适用条件见《易林补遗》源 L966：「惟有家主来占，方取六爻分宫而察」——
    **家人代占不取此层**（用 :func:`jiazai_daizhan_map`）。本函数不自行判别
    「是否家主自占」（那是问类/身份判定，属别层），故由调用方先判身份再调。
    """
    t = (yilin_maps().get("家宅三层分宫") or {}).get("六爻分宫") or {}
    cn = _YAO_CN.get(int(yao or 0)) if yao else ""
    return list(t.get(f"{cn}爻") or []) if cn else []


def jiazai_daizhan_map(situation: str) -> dict:
    """家宅·代占层（《易林补遗》源L966「自己占，以世为主以应为妻。他人代占，以世为问卦之人，应为本主」）：{'自己占'|'他人代占'|'家人代占'} → 世应所主。

    未列情形返回 {}。注意《易林补遗》源 L966 末明言家人代占「不必取六爻分宫所断」，
    故本层与 :func:`jiazai_yao_map` **互斥**。
    """
    t = (yilin_maps().get("家宅三层分宫") or {}).get("代占") or {}
    for r in t.get("规则") or []:
        if r.get("情形") == situation:
            out = {k: v for k, v in r.items() if k != "情形"}
            out["_src"] = t.get("_src", "")
            return out
    return {}


# ── 间爻四角色 ──────────────────────────────────────────────────

_JIANYAO_QS = {"婚姻": "媒妁", "借贷": "中保", "词讼": "中证", "起造": "工匠"}


def jianyao_role(category: str) -> dict:
    """间爻在该问类下的**专职角色**（源 L596/L1877/L2056/L1033）。

    `category` 取书源问类名（婚姻/借贷/词讼/起造）；未列者返回 {}。
    本函数**只给角色名与要点**，不判「有力/无力」——那属机械层旺衰，不在本层。
    """
    role = _JIANYAO_QS.get(category or "")
    if not role:
        return {}
    e = (yilin_maps().get("间爻四角色") or {}).get(role) or {}
    if not e:
        return {}
    return {"role": role, "要点": e.get("要点") or "",
            "_src": e.get("_src", ""), "_引文": e.get("_引文", "")}


# ── 外卦取事定方（《易林补遗》源L2234「凡占逃者在以何处，专以外卦推详」）──────────────────────────────────────

def waigua_direction(palace: str) -> str:
    """逃亡问：外卦（八宫）→ 方位（《易林补遗》源 L2234「专以外卦推详」）。未列返回 ""。"""
    return (yilin_maps().get("外卦取事定方") or {}).get(palace or "") or ""
