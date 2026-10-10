# -*- coding: utf-8 -*-
"""《京氏易传》八宫速览表 → core.EIGHT_PALACES 逐宫对拍（**外部真值源**）。

【OPT-jingshi_yizhuan_dz-02，2026-10-07 新增】

为什么需要这个门：core 的 `EIGHT_PALACES`（八宫六十四卦归属）若被误改，
现有读数未必暴露（案例集未必覆盖全 64 卦的宫属）。本书卷下 **L99-L106**
是一张**独立的八宫速览表**（每宫列八卦，按世次一至六世、游魂、归魂排列），
与 core 同为「乾姤遁否观剥晋大有」一系，是**外部书源证据**。

本脚本**只读、只报差异**（范式同 `disciplines/ming/dev_tools/diff_tiaohou_vs_head.py`）：
  · 书源侧：解析 L99-L106 八个宫块的卦名序列（并登记源行号）；
  · 引擎侧：取 `core.yishu_core.symbols.EIGHT_PALACES[p]["order"]` 的卦名序；
  · 逐宫逐位比对，报「一致 N 格 / 改值 N 格 / 变空 N 格」，**逐条列出**。

用法：
    python dev_tools/diff_jingshi_vs_core.py            # 人读报告，EXIT=0/1
    python dev_tools/diff_jingshi_vs_core.py --json     # 机器读

退出码：0 全同；1 有差异；2 书源缺失/解析不出宫块（门输入坏了，须报而非静默放过）。

**书源用字异体（照录不改、不静默归一）**：本书作「干」（乾）、「兊」（兑）、
「筮嗑」（噬嗑）、「頥」（颐）、「涣」等，且宫块以**全名**书写。
本脚本在解析时把**异体字映射表**（下表）显式列出，映射表本身是**书源字形**，
不是 core 的第二份卦名真值源；映射不命中者判失败（宁缺勿滥），不猜。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.symbols import EIGHT_PALACES  # noqa: E402

SRC = ROOT / "data" / "sources" / "jingshi_yizhuan_dz.dz.txt"
SCAN_FROM, SCAN_TO = 99, 106          # 书源 L99-L106 八宫速览表

# 宫名：书源写法 → core 写法（异体仅此数个，皆书源字形）
PALACE_VARIANTS = {"干": "乾", "坎": "坎", "艮": "艮", "震": "震",
                   "坤": "坤", "巽": "巽", "兊": "兑", "兑": "兑"}
# 卦名异体：书源写法 → core 写法（据 core.EIGHT_PALACES 反查可用性）
GUA_VARIANTS = {"筮嗑": "噬嗑", "頥": "颐", "兑": "兑", "兊": "兑"}

# 世次序（core 与书源同）：一至六世、游魂、归魂
STAGES = ["一世", "二世", "三世", "四世", "五世", "六世", "游魂", "归魂"]

# ── 底本缺字/讹字处理（**core 一律不动**，只在本门登记并显式打印）──
# 底本 L105 左栏作「旅鼎未济<U+E860>」：U+E860 是**私用区码位**（ Unicode
# Private Use Area），即 wikisource 转录时「蒙」字未能正确转码所留的残码。
# 判据：core.EIGHT_PALACES 离宫为「离 旅 鼎 未济 蒙 涣 讼 同人」，第四位即「蒙」；
# 且同栏其余七卦（旅鼎未济／涣讼同人）逐字合乎 core 唯此处残缺。
# 故判为**书源转录残缺**，本门从 core 取该位并在报告里单列（AGENTS.md §四.8：
# 豁免必须可见，不得静默吞掉）。
PUA_FILL = ""        # 底本残码字符
PUA_EXPECTED = {"离": {"蒙"}}   # 宫 → {残码位应为何卦}


def parse_source() -> dict:
    """书源 → {宫: {卦名: 源行号}}；同时记每宫的卦序列（按书源出现次序）。"""
    if not SRC.exists():
        return {}
    lines = SRC.read_text(encoding="utf-8").split("\n")
    # 书源 L99-L106 是**两栏八行**的固定版式，逐行实测（token 以全角空格切分）：
    #   L99: [干, 姤遁否观,  震, 豫解恒升]      L100: [剥晋大有,   井大过随]
    #   L101:[坎, 节屯既济革, 艮, 贲大畜损]      L102: [丰明夷师,   睽履中孚渐]
    #   L103:[坤, 复临泰大壮, 巽, 小畜家人益无妄] L104: [夬需比, 筮嗑頥蛊]
    #   L105:[旅鼎未济蒙, 兊, 困萃咸蹇]        L106: [涣讼同人,   谦小过归妹]
    # 即：**每两行一组，一组＝两宫**；组内首行 token0=左宫名、token1=左宫前四卦、
    # token2=右宫名、token3=右宫前四卦；次行 token0/1 分别是两宫的后四卦。
    # 故按「行对」解析：第 2k、2k+1 行处理第 k 组。
    # 另注：**底本 L105 左宫名缺字**（该行左 token 直接是卦名「旅鼎未济蒙」，
    # 无「离」字）——按版式左列宫序（乾坎坤离）推定为离宫，并在报告中显式标注，
    # 不静默补（AGENTS.md §四.8：推定必须可见）。
    out: dict[str, dict] = {}
    for pair in range(4):
        r1, r2 = SCAN_FROM + pair * 2, SCAN_FROM + pair * 2 + 1
        if r1 > len(lines) or r2 > len(lines):
            break
        t1 = [t for t in re.split(r"[　\s]+", lines[r1 - 1]) if t]
        t2 = [t for t in re.split(r"[　\s]+", lines[r2 - 1]) if t]
        if len(t2) < 2:
            continue
        # 组内首行：**正常四 token** [左宫名, 左前四卦, 右宫名, 右前四卦]；
        # **末组因底本缺「离」宫名只有三 token** [左前四卦, 右宫名, 右前四卦]。
        if len(t1) >= 4:
            left_gua, right = t1[1], PALACE_VARIANTS.get(t1[2], "")
            right_gua = t1[3]
        elif len(t1) == 3:
            # 缺字：左宫名无 → 按 _LEFT_ORDER 推定；token0=左前四卦、1=右宫名、2=右前四卦
            left_gua, right, right_gua = t1[0], PALACE_VARIANTS.get(t1[1], ""), t1[2]
        else:
            continue
        left = PALACE_VARIANTS.get(t1[0], "") or _left_by_order(pair)
        if left and left not in out:
            out[left] = {}
            for g in _split_gua(left_gua):
                out[left].setdefault(g, f"L{r1}")
            for g in _split_gua(t2[0]):
                out[left].setdefault(g, f"L{r2}")
        if right and right not in out:
            out[right] = {}
            for g in _split_gua(right_gua):
                out[right].setdefault(g, f"L{r1}")
            for g in _split_gua(t2[1]):
                out[right].setdefault(g, f"L{r2}")
    return out


# 左列自上而下的宫序（乾坎坤离）——底本 L105 左宫名缺字，据此推定
_LEFT_ORDER = ("乾", "坎", "坤", "离")


def _left_by_order(pair: int) -> str:
    return _LEFT_ORDER[pair] if pair < len(_LEFT_ORDER) else ""


# 左栏自上而下的宫序（干坎艮震巽…）；底本缺「离」宫名，据此定位缺字宫
_COL_ORDER = ("乾", "坎", "艮", "震", "巽", "离", "兑")
def _split_gua(blob: str) -> list[str]:
    """把「姤遁否观剥晋大有」这类连写切成卦名列表。

    切分依据是**书源字形**：先把底本异体字（干/兊/筮嗑/頥…）归一到 core 用字，
    再按 core 八宫表里的**已知卦名集合**做最长优先切。不建第二份卦名表——
    异体映射是**书源字形**归一（GUA_VARIANTS），不是另立真值源。
    """
    known = {h for v in EIGHT_PALACES.values() for h, _ in v["order"]}
    s = blob
    for src, dst in GUA_VARIANTS.items():      # 异体归一（筮嗑→噬嗑、頥→颐 等）
        if src in s and src != dst:
            s = s.replace(src, dst)
    # 私用区残码：本门不比该位（由调用方按 PUA_EXPECTED 登记豁免），先剔除避免错切
    s = s.replace(PUA_FILL, "")
    out, i = [], 0
    while i < len(s):
        for size in (2, 1):
            cand = s[i:i + size]
            if cand and cand in known:
                out.append(cand)
                i += size
                break
        else:
            # 未识别字（含底本私用区字符）：跳过一个字，不猜
            i += 1
    return out


def core_seq() -> dict:
    """core → {宫: [卦名×8]}（按 order 的书写次序）。"""
    return {p: [h for h, _ in v["order"]] for p, v in EIGHT_PALACES.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description="《京氏易传》八宫表 vs core 对拍")
    ap.add_argument("--json", action="store_true", help="机器读输出")
    args = ap.parse_args()

    src = parse_source()
    if not src or len(src) < 8:
        got = sorted(src)
        print(f"书源解析只出 {len(got)} 宫（{got}），不足八宫——"
              f"门输入坏了（源缺失或格式变化），须修脚本而非静默放过", file=sys.stderr)
        return 2

    eng = core_seq()
    _src_text = SRC.read_text(encoding="utf-8")
    same, changed, emptied, waived = 0, [], [], []
    palaces = sorted(set(src) | set(eng), key=lambda p: (p not in src, p))
    for p in palaces:
        s_seq = list(src.get(p, {}).keys())
        # core 的 order **含本宫首卦**（标「六世」），而书源速览表**不列本宫首卦**
        # （乾宫只从「姤」起）——两者差一位，属版式差异不是数据差异。
        # 故对拍时把 core 去掉首卦，与书源同长后再逐位比。
        e_all = eng.get(p, [])
        e_seq = e_all[1:] if e_all else []
        if not s_seq:
            emptied.append({"宫": p, "书源": "（书源无此宫块）", "引擎": "、".join(e_all)})
            continue
        if not e_seq:
            emptied.append({"宫": p, "书源": "、".join(s_seq), "引擎": "（core 无此宫）"})
            continue
        # 底本私用区残码：该宫少一位 → 书源序列右侧整体左移一位，属**书源残缺**，
        # 不是 core 改值。检出残码即整宫按「书源残缺」登记并豁免（core 不动）。
        if p in PUA_EXPECTED and PUA_FILL in _src_text:
            waived.append({"宫": p, "残缺位": sorted(PUA_EXPECTED[p]),
                           "src": f"L{SCAN_FROM + 6}",
                           "理由": "底本该位为 Unicode 私用区残码（转录残缺），"
                                   "非卦名；core 取值不动，本门豁免该宫该位"})
            # 残缺宫的比法：core 侧**去掉**残缺位的那一卦 → 与书源同长同位，
            # 于是比的就是「除该残缺位外，其余各位是否逐位全同」。
            e_cmp = [g for g in e_seq
                     if g not in PUA_EXPECTED[p]]
            for i in range(max(len(s_seq), len(e_cmp))):
                s = s_seq[i] if i < len(s_seq) else ""
                e = e_cmp[i] if i < len(e_cmp) else ""
                if s and e and s == e:
                    same += 1
                else:
                    changed.append({"宫": p,
                                    "世次": STAGES[i] if i < len(STAGES) else f"第{i + 1}位",
                                    "位": i + 1, "书源": s or "（无）", "引擎": e or "（无）",
                                    "src": src.get(p, {}).get(s, "")})
            continue
        for i in range(max(len(s_seq), len(e_seq))):
            s = s_seq[i] if i < len(s_seq) else ""
            e = e_seq[i] if i < len(e_seq) else ""
            stage = STAGES[i] if i < len(STAGES) else f"第{i + 1}位"
            if s and e and s == e:
                same += 1
            else:
                changed.append({"宫": p, "世次": stage, "位": i + 1,
                                "书源": s or "（无）", "引擎": e or "（无）",
                                "src": src.get(p, {}).get(s, "")})

    report = {
        "书源": SRC.name,
        "书源宫数": len(src),
        "一致格数": same,
        "改值格数": len(changed),
        "书源残缺豁免宫数": len(waived),
        "变空宫数": len(emptied),
        "对拍总格数": same + len(changed),
        "改值明细": changed,
        "残缺豁免明细": waived,
        "变空明细": emptied,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if (changed or emptied) else 0

    print(f"《京氏易传》八宫速览表（{SRC.name} L{SCAN_FROM}-L{SCAN_TO}） vs core.EIGHT_PALACES")
    print(f"书源宫数 {len(src)}｜一致 {same} 格｜改值 {len(changed)} 格"
          f"｜书源残缺豁免 {len(waived)} 宫｜变空 {len(emptied)} 宫"
          f"｜对拍总格 {same + len(changed)}")
    if changed:
        print("\n改值明细（逐条）：")
        for c in changed:
            print(f"  {c['宫']}宫 {c['世次']}：书源 {c['书源']} vs 引擎 {c['引擎']}"
                  f"  [{c['src'] or '—'}]")
    if waived:
        print("\n书源残缺豁免（**core 未动**，逐条列出以免静默吞掉）：")
        for w in waived:
            print(f"  {w['宫']}宫 缺 {'、'.join(w['残缺位'])}  [{w['src']}] —— {w['理由']}")
    if emptied:
        print("\n变空明细（逐条）：")
        for e in emptied:
            print(f"  {e['宫']}宫：书源 {e['书源']}｜引擎 {e['引擎']}")
    if not changed and not emptied:
        print(f"\n√ 八宫六十四卦归属与 core 逐位全同"
              f"（无改值、无变空；书源残缺 {len(waived)} 宫已单列）")
    return 1 if (changed or emptied) else 0


if __name__ == "__main__":
    sys.exit(main())
