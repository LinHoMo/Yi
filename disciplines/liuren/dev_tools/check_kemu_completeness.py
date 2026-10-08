# -*- coding: utf-8 -*-
"""十二盘课体完备性对拍基准（OPT-liuren_cuiyan_dz-01，只读 diff 脚本，不改判据）。

书源基准：data/sources/liuren_cuiyan_dz.dz.txt L159「十二地盘无漏遗」节。
  以地盘 X 加天盘子 为基准构型，该构型下应出现的课体名由本书卷三枚举。
  本脚本逐盘与本仓 kemu.json 的 IMPLEMENTED（scripts/kemu.py）现状对拍，
  输出「已覆盖／未覆盖」的只读报告；**不修改任何 IMPLEMENTED 条目**。

十二盘 × 对应 课体名（逐字源自 L159）：
  丑加子 → 进茹
  亥加子 → 退茹
  寅加子 → 进间
  戌加子 → 退间
  辰加子 → 顺三合
  申加子 → 逆三合
  卯加子 → 顺三交、顺关隔、顺稼穑
  酉加子 → 逆三交、逆关隔、逆稼穑
  巳加子 → 四墓
  未加子 → 四绝
  返吟（返吟节）
  伏吟（伏吟节）

对拍口径：
  - "已覆盖" = 该 课体名 在 IMPLEMENTED 中既同名课目，或在 IMPLEMENTED 某课的 verse/别名 中出现；
  - 进茹/退茹/进间/退间 归属 IMPLEMENTED「联珠」（联珠 verse 含 "连茹兼进退" "间传顺逆此中论"）；
   - 顺合/逆合/三合四局 归属 IMPLEMENTED「全局」（全局 verse 含 "水火木金土中存" 三合四局描述）或 rules.san_he_ju_extension；
  - 返吟、伏吟 直接查 IMPLEMENTED。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
ROOT = DISC.parents[1]
CORE = ROOT / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

KEMU = DISC / "data" / "kemu.json"

# 只读引用 IMPLEMENTED（不修改）。
from kemu import IMPLEMENTED as KEMU_IMPLEMENTED  # noqa: E402

# 一次性缓存：kemu.json 的 entries 与 aliases（只读，不重新加载）
_kd = json.loads(KEMU.read_text(encoding="utf-8"))
_ENTRIES_BY_NAME: dict[str, dict] = {e["name"]: e for e in _kd.get("entries", [])}
_ALIASES: dict[str, str] = _kd.get("rules", {}).get("aliases", {})

# 十二盘基准（L159）：每条目 = (盘描述, [课体名,...])。
# 「卯加子」「酉加子」各含 3 个 课体（三交/关隔/稼穑），故 12 盘合计 16 项。
TWELVE_PLATES: list[tuple[str, list[str]]] = [
    ("丑加子", ["进茹"]),
    ("亥加子", ["退茹"]),
    ("寅加子", ["进间"]),
    ("戌加子", ["退间"]),
    ("辰加子", ["顺三合"]),
    ("申加子", ["逆三合"]),
    ("卯加子", ["顺三交", "顺关隔", "顺稼穑"]),
    ("酉加子", ["逆三交", "逆关隔", "逆稼穑"]),
    ("巳加子", ["四墓"]),
    ("未加子", ["四绝"]),
    ("返吟节", ["返吟"]),
    ("伏吟节", ["伏吟"]),
]

# 已覆盖判据优先级（与 _is_covered 实现一致，作为文档参考）

def _is_covered(name: str) -> tuple[bool, str]:
    """判定 课体名 是否已落机械判据 IMPLEMENTED。

    口径（按优先级，命中即止）：
      1) 本名 = IMPLEMENTED 课目（精确）
      2) 去掉 顺/逆 前缀后的基名 = IMPLEMENTED 课目（如 逆稼穑 → 稼穑）
      3) 本名或基名 作为子串出现在某个 IMPLEMENTED 课的 verse/note 中
         （如 "稼穑" 在 IMPLEMENTED「全局」note 中出现）
      4) kemu.json rules.aliases 登记为 alias
    """
    # 基名（去 顺/逆 前缀用于回退匹配）
    base = name[1:] if name and name[0] in ("顺", "逆") else name

    # 1) 精确命中
    if name in KEMU_IMPLEMENTED:
        return True, f"IMPLEMENTED 同名课目「{name}」"

    # 2) 基名精确命中（逆稼穑 → 稼穑 不在 IMPLEMENTED，全局 IMPLEMENTED via next）
    if base != name and base in KEMU_IMPLEMENTED:
        return True, f"IMPLEMENTED 同名课目「{base}」{name}为其顺/逆变体"

    # 3) IMPLEMENTED 课的 verse/note 子串包含本名或基名
    for imp_key in KEMU_IMPLEMENTED:
        ed = _ENTRIES_BY_NAME.get(imp_key)
        if not ed:
            continue
        hay = ed.get("verse", "") + ed.get("note", "")
        if (name in hay) or (base != name and base in hay):
            return True, f"IMPLEMENTED「{imp_key}」verse/note 包含「{name}」"

    # 4) kemu.json rules.aliases 登记
    if name in _ALIASES:
        to = _ALIASES[name]
        if to in KEMU_IMPLEMENTED:
            return True, f"aliases 登记 → IMPLEMENTED「{to}」"
        return False, f"aliases 登记 → {to}（{to} 未在 IMPLEMENTED）"
    if base != name and base in _ALIASES:
        to = _ALIASES[base]
        if to in KEMU_IMPLEMENTED:
            return True, f"aliases 登记「{base}」→ IMPLEMENTED「{to}」"
        return False, f"aliases 登记 → {to}（{to} 未在 IMPLEMENTED）"
    return False, "未在 IMPLEMENTED / aliases / verse-note 子串中找到"


def run_audit() -> tuple[bool, int, int, list[str], list[str]]:
    """逐盘对拍；返回 (all_plates_ok, plates_covered, items_covered, covered_lines, missing_lines)。

    all_plates_ok = 每个 12 盘至少 1 项被覆盖（验收「12盘全部有课型归属」口径）。
    """
    covered: list[str] = []
    missing: list[str] = []
    plates_ok = 0

    print("十二盘课体完备性对拍（L159 基准 vs 本仓 IMPLEMENTED 现状）\n")
    print(f"本仓 IMPLEMENTED 课目数：{len(KEMU_IMPLEMENTED)}")
    print(f"对拍基线：12 盘（共 {sum(len(v) for _, v in TWELVE_PLATES)} 项 课体归属）\n")

    for plate, names in TWELVE_PLATES:
        plate_ok = False
        for nm in names:
            ok, how = _is_covered(nm)
            if ok:
                plate_ok = True
            line = f"  [{plate}] {nm:6s} → {'PASS' if ok else 'MISS '} — {how}"
            (covered if ok else missing).append(line)
            print(line)
        if plate_ok:
            plates_ok += 1

    print()
    return plates_ok == len(TWELVE_PLATES), plates_ok, len(covered), covered, missing


def main() -> int:
    all_ok, plates_ok, items_ok, covered, missing = run_audit()
    total_plates = len(TWELVE_PLATES)
    total_items = sum(len(v) for _, v in TWELVE_PLATES)
    print("─" * 60)
    print(f"12 盘归属覆盖：{plates_ok}/{total_plates}")
    print(f"逐项覆盖：{items_ok}/{total_items}  |  项级未覆盖：{len(missing)} 项")
    if missing:
        print("\n未覆盖项（需后续 OPT 落实 IMPLEMENTED / 登记 aliases）：")
        for m in missing:
            print(m)
    print("\nRESULT: ", end="")
    if all_ok and not missing:
        print("COMPLETE — 12 盘全部有 IMPLEMENTED 归属")
        return 0
    if all_ok:
        print(f"PARTIAL（12盘全部有归属，但 {len(missing)} 项未达 IMPLEMENTED）")
        return 0
    print(f"INCOMPLETE — {total_plates - plates_ok} 盘无归属")
    return 1


if __name__ == "__main__":
    sys.exit(main())
