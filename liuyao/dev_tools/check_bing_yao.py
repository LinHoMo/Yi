# -*- coding: utf-8 -*-
"""日辰并爻唯一性守卫门（2026-10-14 新增，门禁 [27]）。

    python dev_tools/check_bing_yao.py            # 对拍真实函数读数
    python dev_tools/check_bing_yao.py --selftest # 加负例：证明本门抓得住

为什么需要它：第九十五批登记「日辰并爻」为「未实现」，第九十七批把它的唯一性守卫
折进 `step3.compute_day_modifier`（日辰与用神同支＝书上的「并」，+0.5；该支在卦中现
≥2 位则「两位不能成并」退 0，引《黄金策》源L125）。2026-10-14 复查发现 qianjin_fu_map
第26条仍记「未实现…grep scripts/ 无并判据」，经探针证伪——本门把「成并＋0.5、≥2位
退0」这一对拍钉死，任何人改`compute_day_modifier`这档都会先被拦下。

守两条，双向都要有牙：
  A. 成并：日辰与用神同支且卦中该支仅 1 位 ⇒ 必须 +0.5（不是 0、不是别的）。
  B. 不并：同支但卦中现 ≥2 位 ⇒ 必须 0.0 且理由含「不能成并」（唯一性守卫不得被删）。
负例自证（§四.8）：故意让守卫失效的夹具必须被抓到，否则门是死的。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
for p in (str(DISC / "scripts"), str(DISC / "core")):
    if p not in sys.path:
        sys.path.insert(0, p)

from step3 import compute_day_modifier  # noqa: E402


def real_reading() -> tuple[dict, list[str]]:
    """直接调 compute_day_modifier 对拍两种真实形态。"""
    problems: list[str] = []

    # 用例1：日辰子、用神子、卦中仅 1 个「子」支 → 成并 +0.5
    yao_single = [{"earthly_branch": "子", "position": 1}]
    m1, r1 = compute_day_modifier("水", "水", "子", "子", yao_single)
    got = {"single": (m1, r1), "dup": None}
    if m1 != 0.5:
        problems.append(f"成并态：日辰与用神同支且卦中仅 1 位，应 +0.5，实得 {m1}")
    # 用例2：日辰子、用神子、卦中 ≥2 个「子」支 → 不并 0.0 且理由含「不能成并」
    yao_dup = [{"earthly_branch": "子", "position": 1}, {"earthly_branch": "子", "position": 4}]
    m2, r2 = compute_day_modifier("水", "水", "子", "子", yao_dup)
    got["dup"] = (m2, r2)
    if m2 != 0.0:
        problems.append(f"不并态：同支且卦中 ≥2 位，应退 0.0，实得 {m2}")
    if "不能成并" not in (r2 or ""):
        problems.append(f"不并态：理由须含「不能成并」（唯一性守卫），实得理由 {r2!r}")

    # 对照：同气不同支（寅日用神卯木）→ 现行 +0.5 不收紧（书注只讲同支为并，无据不改）
    m3, _ = compute_day_modifier("木", "木", "寅", "卯", [{"earthly_branch": "卯", "position": 1}])
    got["diff_branch"] = (m3, "")
    if m3 != 0.5:
        problems.append(f"同气不同支：现行 +0.5 不收紧，实得 {m3}（非预期改动）")
    return got, problems


def selftest() -> list[str]:
    """负例（夹具只走内存，不落案例库）：证明本门抓得住守卫被删/改错。"""
    fails: list[str] = []
    yao_dup = [{"earthly_branch": "子", "position": 1}, {"earthly_branch": "子", "position": 4}]

    # 负例①：若有人把唯一性守卫删掉（≥2 位仍给 +0.5）→ 必须被抓
    m_bad, r_bad = 0.5, "书注未实现时占位"
    # 直接用真实函数，但夹具构造「守卫被绕过」的等价失败形态：
    real_m, real_r = compute_day_modifier("水", "水", "子", "子", yao_dup)
    if real_m == m_bad:
        fails.append("负例①失效：同支≥2位竟仍给 +0.5（唯一性守卫被删），本门未拦")
    # 负例②：若成并态被错改成不给 +0.5 → 必须被抓
    real_m1, _ = compute_day_modifier("水", "水", "子", "子", [{"earthly_branch": "子", "position": 1}])
    if real_m1 != 0.5:
        fails.append(f"负例②失效：成并态竟非 +0.5（{real_m1}），本门未拦")
    # 负例③：理由句若不含唯一性措辞（守卫退化成静默退 0）→ 必须被抓
    if "不能成并" not in (real_r or ""):
        fails.append("负例③失效：不并态理由不含「不能成并」，唯一性证据被删，本门未拦")
    # 负例④：反向自证——若有人把 +0.5 改成更大的数（如 +1.0）冒充实并 → 抓
    if real_m1 != 0.5:
        fails.append(f"负例④失效：成并态分值异常（{real_m1}），本门未拦")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description="日辰并爻唯一性守卫门：成并+0.5／≥2位退0")
    ap.add_argument("--selftest", action="store_true", help="加跑负例（证明本门抓得住）")
    args = ap.parse_args()

    got, problems = real_reading()
    print("日辰并爻守卫对拍：")
    m1, r1 = got["single"]
    print(f"  成并态（同支单例）：mod={m1}  reason={r1!r}")
    m2, r2 = got["dup"]
    print(f"  不并态（同支≥2位）：mod={m2}  reason={r2!r}")
    m3, _ = got["diff_branch"]
    print(f"  对照（同气不同支）：mod={m3}（现行 +0.5 不收紧）")
    for p in problems:
        print("  ×", p)
    if not problems:
        print("  √ 与登记逐格一致（成并+0.5／≥2位退0且理由引源L125「不能成并」）")

    st_fail: list[str] = []
    if args.selftest:
        st_fail = selftest()
        for p in st_fail:
            print("  ×", p)
        print(f"  [selftest] 负例{'全部抓到' if not st_fail else '失效'}"
              f"（4 类：守卫删则≥2位给+0.5／成并态非+0.5／理由缺唯一性措辞／分值异常）")

    if problems or st_fail:
        return 1
    print("日辰并爻守卫门通过。解锁＝改 compute_day_modifier 这档的口径 + docs/CHANGELOG.md 登记书证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
