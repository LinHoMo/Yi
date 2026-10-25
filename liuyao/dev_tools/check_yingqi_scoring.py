# -*- coding: utf-8 -*-
"""应期评分口径负例自证（第一百七十二批新增，门禁 [26]）。

     python dev_tools/check_yingqi_scoring.py            # 对拍真实读数
     python dev_tools/check_yingqi_scoring.py --selftest # 加负例：证明本门抓得住

为什么需要它：第一百七十二批改了 `score_case` 里**无语支基准**（书写「次日」这类）
的应期判分——旧口径整批判 0，而实测 wikisource E 类 6 例中 **4 例绝对日窗命中**
（判 0 是把答对的记成答错）；143 批的提案「整批 N/A 剔除」又会**抹掉那 4 个真实得分**。
新口径：**答进日窗即满分，答不进按 N/A 剔除**（applicable 不计，不记失分）。

本门守两条，双向都要有牙：
  A. **不能拿「窗口运气」冒充支级判别力**：无语支基准而答不进窗 ⇒ 必须 applicable=0
     （而不是 0 分）。旧口径在这里记 0 分，会把「引擎没给对应日期」算成应期维失分。
  B. **不能抹掉真实得分**：无语支基准而答进窗 ⇒ 必须满分且 applicable=11。
     整批 N/A 剔除（143 批提案）会静默丢掉这 4 例，均分四舍五入后几乎不动——
     与第一百六十八批「214 例回填丢失而均分纹丝不动」同族。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
for p in (str(DISC / "scripts"), str(DISC / "core")):
    if p not in sys.path:
        sys.path.insert(0, p)

import evaluate as ev  # noqa: E402

# wikisource E 类六例（书载应期写「次日」，无支级答案）。
# 真实读数（第一百七十二批实测）：WS024/WS027/WS040/WS042 绝对日窗命中（满分），
# WS028 答不进窗（N/A）。这些数是本门的对拍基准，改动须先改本文件＋CHANGELOG。
# WS005 第两百九十四批 na→hit：自占病层使 WS005 用神官鬼→世爻（裁决表
# liuyao.bing_use_god_dual 口径），yingqi 语支随之变化，实测 hit/applicable=11。
E_CLASS_EXPECTED = {
    "WS024": ("hit", 11), "WS027": ("hit", 11),
    "WS040": ("hit", 11), "WS042": ("hit", 11),
    "WS005": ("hit", 11), "WS028": ("na", 0),
}


def real_reading() -> tuple[dict, list[str]]:
    """跑真实 wikisource_holdout，返回 {id: (kind, earned, applicable)} 与问题清单。"""
    import case_runner as cr
    ids = cr.load_ids("wikisource_holdout")
    eng = cr.run_ids(ids, verbose=False)
    base = {c["id"]: c for c in cr.load_cases()}
    res = ev.evaluate(eng, "strict", "wikisource_holdout", ids, verbose=False)
    got = {}
    for row in res["rows"]:
        yq = (row.get("dims") or {}).get("yingqi")
        if row["id"] in E_CLASS_EXPECTED and yq:
            kind = "hit" if yq[1] else "na"
            got[row["id"]] = (kind, yq[0], yq[1])
    problems = []
    for cid, (want_kind, want_app) in E_CLASS_EXPECTED.items():
        if cid not in got:
            problems.append(f"{cid}: 未取到读数（该例可能已不在 wikisource_holdout 分片）")
            continue
        kind, earned, app = got[cid]
        if kind != want_kind or app != want_app:
            problems.append(
                f"{cid}: 实测 {kind}/applicable={app}，登记 {want_kind}/{want_app}"
                f"——无语支基准的判分口径变了；若确有变更，"
                f"改本文件 E_CLASS_EXPECTED + docs/CHANGELOG.md 登记后才准绿")
        if kind == "hit" and earned != 11:
            problems.append(f"{cid}: 答进日窗却不是满分（earned={earned}）——B 条失守")
    return got, problems


def selftest() -> list[str]:
    """负例（铁律二：夹具只走内存，不落案例库）：
    ①无语支基准答不进窗必须 applicable=0（不许记 0 分）；
    ②无语支基准答进窗必须满分；
    ③有支基准的例不受影响（名次口径照旧）。"""
    fails: list[str] = []
    # 锚日 2024-01-04；「次日」窗 = (1,1)。窗内日期 2024-01-05、窗外日期 2024-01-20。
    case = {"id": "T1", "input": {}, "year": 2024, "month": 1, "day": 4}
    exp = {"yingqi": "次日"}
    # ① 引擎日期在窗外 ⇒ N/A（applicable=0，不记 0 分）
    out_win = {"yingqi_dates": [{"date": "2024-01-20", "branch": "X", "rule": "r"}]}
    got = ev.score_case(dict(out_win, yingqi_branches=[]), exp, "strict", case=case)
    v = got.get("yingqi")
    if not v or v[1] != 0:
        fails.append(f"负例①失效：无语支基准且未进日窗应为 applicable=0（N/A），实得 {v}")
    # ② 引擎日期在窗内 ⇒ 满分
    in_win = {"yingqi_dates": [{"date": "2024-01-05", "branch": "X", "rule": "r"}]}
    got2 = ev.score_case(dict(in_win, yingqi_branches=[]), exp, "strict", case=case)
    v2 = got2.get("yingqi")
    if not v2 or v2[0] != 11 or v2[1] != 11:
        fails.append(f"负例②失效：无语支基准且进日窗应满分 11/11，实得 {v2}")
    # ③ 有支基准的例照旧按名次（不受本次口径变更影响）
    got3 = ev.score_case({"yingqi_branches": ["卯日", "子日"]}, {"yingqi": "卯日"}, "strict")
    v3 = got3.get("yingqi")
    if not v3 or v3[0] != 11:
        fails.append(f"负例③失效：有支基准首位命中应满分，实得 {v3}（口径被误伤）")
    # ④ 反向自证：旧口径（整批判 0／整批 N/A）必须**不再出现**——
    #    若将来有人把 `else` 分支改回 (0, w)，负例①立刻抓得到。
    if v and v[0] != 0:
        fails.append(f"负例④失效：N/A 分支的 earned 应为 0，实得 {v}")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(
        description="应期评分口径门：无语支基准「答进窗满分／答不进 N/A」，双向都要有牙")
    ap.add_argument("--selftest", action="store_true", help="加跑负例（证明本门抓得住）")
    args = ap.parse_args()

    got, problems = real_reading()
    print(f"无语支基准（E 类）{len(E_CLASS_EXPECTED)} 例对拍：")
    for cid, (kind, earned, app) in sorted(got.items()):
        print(f"  {cid}: {kind}  earned={earned}  applicable={app}")
    for p in problems:
        print("  ×", p)
    if not problems:
        print("  √ 与登记逐格一致（hit=满分且进分母／na=剔除不进分母）")

    st_fail: list[str] = []
    if args.selftest:
        st_fail = selftest()
        for p in st_fail:
            print("  ×", p)
        print(f"  [selftest] 负例{'全部抓到' if not st_fail else '失效'}"
              f"（4 类：答不进须 N/A／答进须满分／有支基准不误伤／N/A 分支 earned 须为 0）")

    if problems or st_fail:
        return 1
    print("应期评分口径门通过。解锁＝改 E_CLASS_EXPECTED + docs/CHANGELOG.md 登记书证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
