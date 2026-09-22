# -*- coding: utf-8 -*-
"""爻序防复发断言：P0 事故的看门狗。

`python tools/hexagram_check.py`

事由：震·巽·艮·兑四个非回文经卦曾在四处各存一份"上爻在前"的镜像编码，
而所有消费代码按"自下而上"解读 —— 于是每个经卦内部三个爻的位次整体颠倒。
案例管线因为两侧同时用错而自洽，只有拿真实爻序喂它才会露馅（ZS005 恒之鼎：
古籍明载上六戌土动，旧管线算成第四爻午动）。

这里用《周易》卦象常识与古籍案例做锚，断言的是**位次**而不只是卦名。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from kernel_path import ensure_kernel_on_path   # 路径规则只在内核定位模块里一份
ensure_kernel_on_path(__file__)

from yishu_core.symbols import BAGUA_LINES, HEXAGRAM_TRIGRAMS  # noqa: E402

FAILS: list[str] = []
N = 0


def ok(cond: bool, label: str, detail: str = ""):
    global N
    if cond:
        N += 1
    else:
        FAILS.append(f"{label} — {detail}")


# ── 1. 经卦爻序（自下而上）
ok(BAGUA_LINES["乾"] == [1, 1, 1], "乾三连", BAGUA_LINES["乾"])
ok(BAGUA_LINES["坤"] == [0, 0, 0], "坤六断", BAGUA_LINES["坤"])
ok(BAGUA_LINES["震"] == [1, 0, 0], "震仰盂（初阳）", BAGUA_LINES["震"])
ok(BAGUA_LINES["艮"] == [0, 0, 1], "艮覆碗（上阳）", BAGUA_LINES["艮"])
ok(BAGUA_LINES["巽"] == [0, 1, 1], "巽下断（初阴）", BAGUA_LINES["巽"])
ok(BAGUA_LINES["兑"] == [1, 1, 0], "兑上缺（上阴）", BAGUA_LINES["兑"])
ok(BAGUA_LINES["坎"] == [0, 1, 0] and BAGUA_LINES["离"] == [1, 0, 1], "坎中满·离中虚")
ok(all(len(v) == 3 for v in BAGUA_LINES.values()), "八卦皆为三爻")
ok(len({tuple(v) for v in BAGUA_LINES.values()}) == 8, "八卦爻型互不重复")

# ── 2. 引擎按自下而上解读
import liuyao_engine as e  # noqa: E402
from datetime import datetime  # noqa: E402
DT = datetime(2024, 6, 1, 10)


def name_of(yao):
    return e.build_hexagram_result(yao, "占", "manual", DT.year, DT.month, DT.day, DT.hour)[
        "original_hexagram"]["name"]


ok(name_of([8, 7, 7, 7, 8, 8]) == "恒", "雷风恒 自下而上 喂入应判恒", name_of([8, 7, 7, 7, 8, 8]))
ok(name_of([7, 7, 8, 8, 8, 7]) == "损", "山泽损 喂入应判损", name_of([7, 7, 8, 8, 8, 7]))
ok(name_of([7, 7, 7, 8, 8, 8]) == "泰", "地天泰 干下坤上", name_of([7, 7, 7, 8, 8, 8]))
ok(name_of([8, 8, 8, 7, 7, 7]) == "否", "天地否 坤下乾上", name_of([8, 8, 8, 7, 7, 7]))
ok(name_of([7, 8, 7, 8, 7, 8]) == "既济", "水火既济 离下坎上", name_of([7, 8, 7, 8, 7, 8]))
ok(name_of([8, 7, 8, 7, 8, 7]) == "未济", "火水未济 坎下离上", name_of([8, 7, 8, 7, 8, 7]))

# ── 3. 位次与阴阳必须逐爻对上（卦名对了不代表位次对）
h = e.build_hexagram_result([8, 7, 7, 7, 8, 8], "占", "manual", DT.year, DT.month, DT.day, DT.hour)
lines = {y["position"]: y for y in h["original_hexagram"]["yao_lines"]}
ok(lines[1]["nature"] == "yin" and lines[1]["name"].startswith("初六"),
   "恒 初爻为阴（初六）", lines[1]["name"])
ok(lines[4]["nature"] == "yang" and lines[4]["name"].startswith("九四"),
   "恒 四爻为阳（九四）", lines[4]["name"])
ok(lines[6]["nature"] == "yin", "恒 上爻为阴（上六）", lines[6]["name"])
ok(lines[6]["earthly_branch"] == "戌", "恒 上六纳戌（震宫外卦午申戌）", lines[6]["earthly_branch"])

# ── 4. 动爻位次：恒之鼎应动在上六（《增删卜易》ZS005 明载戌土财爻动）
import case_runner as cr  # noqa: E402
yao = cr.hex2yao("恒", "鼎")
moving = [i + 1 for i, v in enumerate(yao) if v in (6, 9)]
ok(moving == [6], "恒之鼎 动爻应在上六", f"实得 {moving}")
h2 = e.build_hexagram_result(yao, "占", "manual", DT.year, DT.month, DT.day, DT.hour)
mv = [y for y in h2["original_hexagram"]["yao_lines"] if y.get("is_moving")]
ok(len(mv) == 1 and mv[0]["position"] == 6 and mv[0]["earthly_branch"] == "戌",
   "恒之鼎 引擎认得的动爻应为上六戌", [(y["position"], y["earthly_branch"]) for y in mv])
ok(mv and mv[0].get("changed_branch") == "巳",
   "恒之鼎 上六应化出巳（古籍：化巳火回头相生）", mv[0].get("changed_branch") if mv else None)

# ── 5. 六十四卦全覆盖自洽：由内核线序装配应能找回本名
bad = []
for nm, (up, low) in HEXAGRAM_TRIGRAMS.items():
    y = [7 if b else 8 for b in BAGUA_LINES[low] + BAGUA_LINES[up]]
    if name_of(y) != nm:
        bad.append(f"{nm}→{name_of(y)}")
ok(not bad, "64 卦自下而上装配全部自洽", f"{len(bad)} 例不符：{bad[:5]}")

print(f"爻序断言：{N} 项通过，{len(FAILS)} 项失败")
for f in FAILS:
    print("  ×", f)
if FAILS:
    print("\n结论：爻序约定又漂移了，先修内核再谈断卦。")
    raise SystemExit(1)
print("√ 爻序自下而上唯一约定成立，位次与动爻与古籍一致")
