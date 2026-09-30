# -*- coding: utf-8 -*-
"""择吉·解读（narrate 段）—— 把 analyze 的判据翻译成人话。

只装配 analyze 输出的因子宜忌与综合裁决，不自行推断新结论（CONTRACT §一）。
"""
from __future__ import annotations
import json
from pathlib import Path as _P


_NP = json.loads((_P(__file__).resolve().parents[1] / 'data' / 'verdicts.json').read_text(encoding='utf-8')).get('narrate_phrases', {})


def _direction_label(direction: str) -> str:
    return {"吉": "吉（可用）", "平": _NP["label_ping"], "凶": _NP["label_xiong"]}.get(direction, direction)


def narrate(a: dict) -> str:
    """analyze 输出 → 完整正文（markdown）。"""
    q = (a.get("question") or "").strip()
    activity = a.get("activity") or "通用"
    s = a.get("chart_summary") or {}
    f = a.get("factors_detail") or {}
    v = a.get("conclusion") or {}
    hour = a.get("hour")

    lines = [f"# 择吉·{activity}择日（{s.get('日期')}）", ""]

    if q:
        lines.append(f"你问「{q}」。先说结论：**{v.get('说明')}**，"
                     f"整体是「{_direction_label(v.get('方向'))}」。")
    else:
        lines.append(f"就{activity}择日而言：**{v.get('说明')}**，"
                     f"整体是「{_direction_label(v.get('方向'))}」。")
    lines.append("")

    # 日盘要素
    lines += ["## 一、此日盘面", ""]
    gz = s.get("干支") or {}
    lines.append(f"{s.get('日期')}（星期{s.get('星期')}），农历{s.get('农历')}。")
    lines.append(f"干支：{gz.get('年柱')}年 {gz.get('月柱')}月 {gz.get('日柱')}日。")
    jc = f.get("jian_chu") or {}
    hd = f.get("huang_dao") or {}
    xr = f.get("xiu") or {}
    lines.append(f"建除十二神：**{jc.get('神')}**日——{jc.get('含义')}。")
    lines.append(f"日值神：**{hd.get('神')}**（{'黄道吉神' if hd.get('黄道') else '黑道凶神'}）——{hd.get('含义')}。")
    lines.append(f"值宿：**{xr.get('全名')}**（{'吉宿' if xr.get('吉') else '凶宿' if xr.get('凶') else '—'}）。")
    if hour:
        lines.append(f"若择{hour.get('时支')}时：值神{hour.get('值神')}"
                     f"（{'黄道' if hour.get('黄道') else '黑道'}）。")
    lines.append("")

    # 事类宜忌
    lines += ["## 二、就你问的{activity}".format(activity=activity), ""]
    yi = a.get("yi") or []
    ji = a.get("ji") or []
    if yi:
        lines.append(_NP["yi_lead"] + "；".join("· " + y for y in yi) + "。")
    if ji:
        lines.append(_NP["ji_lead"] + "；".join("· " + j for j in ji) + "。")
    if not yi and not ji:
        lines.append(_NP["neutral_lead"])
    lines.append("")

    # 口径收尾
    lines += ["---", ""]
    direction = v.get("方向")
    if direction == "凶":
        lines.append("口径提示：凶系为结构信号，措辞用「偏向/有…信号」，不作「注定」；"
                     "择日为象数参考，重大事项请结合专业意见（如安葬涉法规、医疗涉医嘱）。")
    else:
        lines.append("口径提示：择日为象数参考，不作现实承诺；"
                 "如涉医疗、法律、投资，请以专业意见为准。")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import json as _json
    import sys as _sys
    from datetime import date as _date
    from pathlib import Path as _Path

    CORE = _Path(__file__).resolve().parents[3] / "core"
    for _p in (str(_Path(__file__).resolve().parent), str(CORE)):
        if _p not in _sys.path:
            _sys.path.insert(0, _p)
    from yishu_core.runtime import force_utf8_stdio  # noqa: E402
    force_utf8_stdio()

    ap = argparse.ArgumentParser(description="择吉解读（narrate 段）")
    ap.add_argument("analyze_json", nargs="?",
                    help="analyze 输出 JSON 文件（缺省跑嫁娶演示）")
    ap.add_argument("-o", "--out", type=_Path, help="写出解读文本")
    args = ap.parse_args()

    if args.analyze_json:
        a = _json.loads(_Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from chart import chart_from_date
        from analyze import analyze
        a = analyze(chart_from_date(_date(2026, 9, 25)))
        a["question"] = "结婚嫁娶吉否"
        a["activity"] = "嫁娶"
    text = narrate(a)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print("解读 →", args.out)
    else:
        print(text)
