# -*- coding: utf-8 -*-
"""大六壬·质量门：契约文件 + 四段冒烟 + 九宗门全枚举守门 + 金标准。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = DISC.parents[1] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES  # noqa: E402

from jiuzongmen import (  # noqa: E402
    CHONG_OF,
    classify_tianpan,
    four_courses,
    san_chuan_full,
)


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run([sys.executable, *cmd], cwd=DISC, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=300,
                       env={**__import__("os").environ, "PYTHONUTF8": "1"})
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def build_tianpan(jiang: str, hour: str) -> dict[str, str]:
    ji = EARTHLY_BRANCHES.index(jiang)
    hi = EARTHLY_BRANCHES.index(hour)
    return {g: EARTHLY_BRANCHES[(ji - hi + i) % 12] for i, g in enumerate(EARTHLY_BRANCHES)}


def enumerate_gate() -> tuple[list[str], dict]:
    """60 日 × 12 月将 × 12 时 = 8640 例全枚举；门类守门断言。"""
    fails: list[str] = []
    from yishu_core.ganzhi_calendar import ganzhi_pair

    days = [ganzhi_pair(i) for i in range(60)]
    stats: dict[str, int] = {}
    bieze_days: dict[str, int] = {}
    bazhuan_days: dict[str, int] = {}
    fuyin = fanyin = jinglanshe = 0
    chain_mens = {"贼克", "比用", "涉害", "遥克"}
    for day in days:
        # 月将固定取「子」作代表：delta = 月将-时辰 随 12 时辰取遍 0..11，
        # 门类结构只依赖 (日, delta)，与月将取哪个支无关
        for hour in EARTHLY_BRANCHES:
            tianpan = build_tianpan("子", hour)
            res = san_chuan_full(day[0], day[1], tianpan)
            men = res["men"]
            if men not in {"贼克", "比用", "涉害", "遥克", "昴星",
                           "别责", "八专", "伏吟", "返吟"}:
                fails.append(f"{day}{hour}：门类 {men} 越界")
            stats[men] = stats.get(men, 0) + 1
            chuan = res["san_chuan"]
            if len(chuan) != 3 or any(b not in EARTHLY_BRANCHES for b in chuan):
                fails.append(f"{day}{hour}：三传非法 {chuan}")
            if men in chain_mens:
                if chuan[1] != tianpan[chuan[0]] or chuan[2] != tianpan[chuan[1]]:
                    fails.append(f"{day}{hour}：中末链断裂 {chuan}")
            kind = classify_tianpan(day[0], day[1], tianpan)
            if kind == "伏吟":
                fuyin += 1
            elif kind == "返吟":
                fanyin += 1
                if res["ke_name"] == "井栏射":
                    jinglanshe += 1
            if men == "别责":
                bieze_days[day] = bieze_days.get(day, 0) + 1
            if men == "八专":
                bazhuan_days[day] = bazhuan_days.get(day, 0) + 1
    # 诀文锚定断言（《六壬大全·入手法》逐字，每日 12 课口径）
    if fuyin != 60:
        fails.append(f"伏吟数 {fuyin} ≠ 60（60 日各 1 课）")
    if fanyin != 60:
        fails.append(f"返吟数 {fanyin} ≠ 60")
    if jinglanshe != 6:
        fails.append(f"井栏射 {jinglanshe} ≠ 6（诀：六日该无克，丑未同干丁己辛）")
    expect_bieze = {"戊辰": 1, "戊午": 1, "丙辰": 1, "辛未": 2, "辛丑": 2, "丁酉": 1, "辛酉": 1}
    if bieze_days != expect_bieze:
        fails.append(f"别责课分布 {bieze_days} ≠ 诀注（刚三柔六共九课：{expect_bieze}）")
    expect_bazhuan_days = {"甲寅", "庚申", "丁未", "己未", "癸丑"}
    if set(bazhuan_days) != expect_bazhuan_days:
        fails.append(f"八专日 {sorted(bazhuan_days)} ≠ 五日（两课无克号八专）")
    if stats.get("昴星", 0) <= 0 or stats.get("遥克", 0) <= 0 or stats.get("涉害", 0) <= 0:
        fails.append(f"九宗门覆盖不全：{stats}")
    return fails, stats


def main() -> int:
    fails: list[str] = []

    required = ["SKILL.md", "scripts/chart.py", "scripts/analyze.py",
                "scripts/narrate.py", "scripts/render.py",
                "scripts/jiuzongmen.py", "data/verdicts.json",
                "dev_tools/check.py", "dev_tools/golden.py"]
    missing = [r for r in required if not (DISC / r).exists()]
    if missing:
        fails.append(f"缺 {missing}")
    print("[0] 契约文件", "√" if not missing else "×")

    fails2, stats = enumerate_gate()
    if fails2:
        fails.extend(fails2)
        print("[1] 九宗门全枚举守门 ×", *fails2[:6], sep="\n    ")
    else:
        print(f"[1] 九宗门全枚举守门 √ 720 例（60 日×12 时辰）门类分布 {stats}")

    code, out = run(["scripts/chart.py", "--datetime", "2024-02-20 10:30",
                     "--question", "占求财", "-o", "scratch/chart.json"])
    if code != 0:
        fails.append("chart 冒烟失败")
        print(out[-800:])
    else:
        print("[2] chart 冒烟 √")

    code, out = run(["scripts/analyze.py", "scratch/chart.json", "-o", "scratch/analyze.json"])
    if code != 0:
        fails.append("analyze 冒烟失败")
        print(out[-800:])
    else:
        print("[3] analyze 冒烟 √")

    code, out = run(["scripts/narrate.py", "scratch/analyze.json"])
    if code != 0 or "不是吉凶断语" not in out:
        fails.append("narrate 应声明非吉凶断语")
        print(out[-800:])
    else:
        print("[4] narrate 口径声明 √")

    code, out = run(["scripts/render.py", "scratch/analyze.json", "-o", "scratch/report.md"])
    if code != 0 or not (DISC / "scratch" / "report.md").exists():
        fails.append("render 冒烟失败")
        print(out[-800:])
    else:
        print("[5] render 冒烟 √")

    code, out = run(["dev_tools/golden.py", "verify"])
    if code != 0:
        fails.append("金标准指纹漂移")
        print(out[-800:])
    else:
        print("[6] 金标准 √", out.strip())

    if fails:
        print("\n质量门未通过：", *fails, sep="\n  · ")
        return 1
    print("\n大六壬质量门全部通过。")
    print("口径：本课输出为机械结构标签，非吉凶断语；一切分数是古籍案例对齐分，"
          "不是现实预测命中率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
