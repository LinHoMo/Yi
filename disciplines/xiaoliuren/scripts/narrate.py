# -*- coding: utf-8 -*-
"""小六壬·解读（narrate 段）—— 把 analyze 的判据翻译成人话。

只装配 analyze 输出的宫义/诀辞/主数，不自行推断新结论（CONTRACT §一）。
综合判断纪律（《贺氏》难点释疑3）：出行/求财等事类提示不可死板套宫义，
由当事人结合具体事物权衡——engine 不越权改判。
"""
from __future__ import annotations
import json
from pathlib import Path as _P

from chart import CN_NUM as _CN        # 汉字数目只有一份（chart.py），不在此另抄


_NP = json.loads((_P(__file__).resolve().parents[1] / 'data' / 'verdicts.json').read_text(encoding='utf-8')).get('narrate_phrases', {})


def _direction_label(direction: str) -> str:
    return {"吉": "吉", "平": "平（两可，宜缓）", "凶": "凶（偏不利）"}.get(direction, direction)


def _num_list(nums: list[int]) -> str:
    return "、".join(_CN[n] if n <= 10 else str(n) for n in nums)

def _topic_cn(topic: str) -> str:
    return {"失物": "失物", "行人": "行人归期", "求财": "求财",
            "官讼": "官讼", "疾病": "疾病", "婚姻": "婚姻",
            "出行": "出行", "家宅": "家宅", "工作": "谋事", "天气": "天气"}.get(topic, "人事")


def narrate(a: dict) -> str:
    """analyze 输出 → 完整正文（markdown）。"""
    q = (a.get("question") or "").strip()
    topic = a.get("topic") or "人事"
    p = a.get("palace") or {}
    name = p.get("宫名", "")
    con = a.get("conclusion") or {}
    tv = a.get("topic_verdict") or {}
    t = a.get("timing") or {}

    lines = [f"# 小六壬·{_topic_cn(topic)}占（{name}）", ""]

    opening = con.get("说明") or _NP["open_ping"]
    if q:
        lines.append(f"你问「{q}」。先说结论：**{opening}**，"
                     f"整体是「{_direction_label(con.get('方向'))}」。")
    else:
        lines.append(f"就此事来说：**{opening}**，"
                     f"整体是「{_direction_label(con.get('方向'))}」。")
    lines.append("")

    # 落宫解读
    lines += ["## 一、落宫：{name}".format(name=name), ""]
    meta = [
        ("五行", p.get("五行")), ("颜色", p.get("颜色")), ("方位", p.get("方位")),
        ("属神", p.get("属神")), ("掌诀位置", p.get("位置")),
    ]
    lines.append("，".join(f"{k}「{v}」" for k, v in meta if v and v != "—") + "。")
    lines.append("")
    lines.append(f"此宫含义：**{p.get('含义')}**。{p.get('总诀')}。")
    lines.append("")

    # 事类断语
    lines += [_NP["section_title"], ""]
    line = tv.get("诀句") or ""
    if line:
        lines.append(f"落在{name}，{_NP['jiaju_lead']}**「{line}」**。")
    else:
        lines.append(_NP["kind_que"])
    cov = tv.get("覆盖") or {}
    if cov:
        lines.append("")
        lines.append(_NP["coverage_lead"].replace(
            "{jue}", str(cov.get("诀辞", 0))).replace(
            "{yin}", str(cov.get("引申", 0))).replace("{que}", str(cov.get("阙", 0))))
    lines.append("")

    # 应期主数
    lines += ["## 三、应期与数目", ""]
    nums = t.get("主数") or []
    if nums:
        lines.append(_NP["number_lead"].replace("{nums}", _num_list(nums)))
    lines.append("")

    # 综合判断提示 + 口径收尾
    if a.get("comprehensive"):
        lines += ["## 四、综合权衡", ""]
        lines.append(_NP["palace_caveat"])
        lines.append("")

    # 断语来源与覆盖（缺口如实登记，不冒充古籍原文）
    lines += [_NP["coverage_title"], ""]
    lines.append(_NP["source_gap_lead"])
    lines.append("")
    lines += ["---", ""]
    direction = con.get("方向")
    if direction == "凶":
        lines.append(_NP["disclaimer_xiong"])
    else:
        lines.append(_NP["disclaimer"])
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import json as _json
    import sys as _sys
    from pathlib import Path as _Path

    CORE = _Path(__file__).resolve().parents[3] / "core"
    for _p in (str(_Path(__file__).resolve().parent), str(CORE)):
        if _p not in _sys.path:
            _sys.path.insert(0, _p)
    from yishu_core.runtime import force_utf8_stdio  # noqa: E402
    force_utf8_stdio()

    ap = argparse.ArgumentParser(description="小六壬解读（narrate 段）")
    ap.add_argument("analyze_json", nargs="?",
                    help="analyze 输出 JSON 文件（缺省跑空亡演示）")
    ap.add_argument("-o", "--out", type=_Path, help="写出解读文本")
    args = ap.parse_args()

    if args.analyze_json:
        a = _json.loads(_Path(args.analyze_json).read_text(encoding="utf-8"))
    else:
        from chart import chart_from_month_day_hour
        from analyze import analyze
        a = analyze(chart_from_month_day_hour(8, 15, 9))
        a["question"] = "去朋友家，测有人否"
        a["topic"] = "行人"
    text = narrate(a)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print("解读 →", args.out)
    else:
        print(text)
