# -*- coding: utf-8 -*-
"""合参层·指导生成（guidance/<id>.md）。

结构固定（synthesis/README.md §三）：
  1. 格局与节律（命）   —— 命科缺数据则明示「未参评」，不补位猜测（规则 5）
  2. 近期诸事（卜）     —— 逐事给方向/应期/所本法则
  3. 合参结论           —— 同向/互证/存疑分列，每条注明来自哪一科的哪个判据
  4. 可执行建议 2–4 条  —— 判据驱动 + 复验时点（到哪个窗口回看并回填 outcome）
  5. 边界声明           —— 医疗/法律/投资以专业意见为准；象征推演给方向不给定论

禁止拼贴安慰叙事：凡「未来会怎样」必须有某科显式判据支撑；本生成器只装配
档案与裁决里的既有数据，不新造结论。
"""
from __future__ import annotations

from pathlib import Path

from person import PersonArchive
from cross_rules import BU_DISCIPLINES, MING_DISCIPLINES


def _window_of(timing: list[str]) -> str:
    if not timing:
        return ""
    return "、".join(timing)


def build_guidance(archive: PersonArchive, adjudication: dict) -> str:
    d = archive.data
    pid = d["id"]
    birth = d.get("birth") or {}
    policy = birth.get("calendar_policy") or {}
    divs = d.get("divinations") or []
    lines: list[str] = []

    # ------------------------------------------------------------ 标题与档案概要
    lines += [f"# 阶段性指导 · {pid}", ""]
    lines.append(f"> 档案建立于 {d.get('created')}；出生时刻 {birth.get('solar')}"
                 + (f"（东经 {birth.get('place_longitude')}）" if birth.get("place_longitude") else "")
                 + (f"；历法口径 {policy.get('boundary')}/{policy.get('zi_hour')}"
                    if policy else "；历法口径未记录（合参前须统一）"))
    lines.append("")

    # ------------------------------------------------------------ 1. 格局与节律（命）
    lines += ["## 一、格局与节律（命）", ""]
    if "ming" in adjudication.get("missing", []):
        lines.append("命科未参评：本版本无命科档案数据，本节空缺。"
                     "**按合参规则 5，缺数据维度降级为未参评，不用其他科补位猜测**。")
    elif any(r.get("discipline") in MING_DISCIPLINES for r in divs):
        ming_recs = [r for r in divs if r.get("discipline") in MING_DISCIPLINES]
        for r in ming_recs:
            bits = [r.get("asked"), r.get("verdict")]
            extra = []
            if r.get("strength"):
                extra.append(f"强弱 {r.get('strength')}")
            if r.get("pattern"):
                extra.append(f"格局 {r.get('pattern')}")
            if r.get("based_on"):
                extra.append(str(r.get("based_on")))
            lines.append("- " + "：".join(str(b) for b in bits if b)
                         + (f"（{'；'.join(extra)}）" if extra else ""))
        lines.append("（机械因子转述，非命运断言。）")
    else:
        lines.append("无命科数据。")
    lines.append("")

    # ------------------------------------------------------------ 2. 近期诸事（卜）
    lines += ["## 二、近期诸事（卜）", ""]
    # 只列裁决后的合法记录（越位/无效输入已在第三节剔除，不在此展示）
    valid = adjudication.get("valid")
    bu = ([r for r in valid if r.get("discipline") in BU_DISCIPLINES]
          if valid is not None else
          [r for r in divs if r.get("discipline") in BU_DISCIPLINES])
    if not bu:
        lines.append("无占问记录。")
    for r in bu:
        lines.append(f"- **{r.get('asked')}**〔{r.get('discipline')}·{r.get('direction')}〕"
                     f"{r.get('verdict') or ''}")
        if r.get("timing"):
            lines.append(f"  - 应期参考：{_window_of(r.get('timing'))}")
        if r.get("based_on"):
            lines.append(f"  - 所本：{r.get('based_on')}")
        oc = (r.get("outcome") or {})
        if oc.get("recorded"):
            lines.append(f"  - 已回填结果：{oc['recorded']}")
        else:
            lines.append("  - 结果未回填：到应期窗口回看并回填 outcome，"
                         "这是唯一能积累现实效度证据的环节")
    lines.append("")

    # ------------------------------------------------------------ 3. 合参结论
    lines += ["## 三、合参结论", ""]
    for r in adjudication.get("excluded", []):
        lines.append(f"- **剔除**：{r.get('asked')} —— {r.get('reason')}")
    if adjudication.get("policy_conflict"):
        lines.append("- **时空口径存疑**：各记录日历口径不一致，合参结论先统一口径再采信。")
    lines += [f"- 裁决模式：**{adjudication.get('pattern')}**，"
              f"趋向 **{adjudication.get('trend')}**"
              f"（吉{tally(adjudication, '吉')}/平{tally(adjudication, '平')}"
              f"/凶{tally(adjudication, '凶')}）",
              ""]
    for note in adjudication.get("notes", []):
        lines.append(f"- {note}")
    if adjudication.get("missing"):
        lines.append(f"- 未参评维度：{', '.join(adjudication['missing'])}"
                     "（降级处理，不补位）")
    lines.append("")

    # ------------------------------------------------------------ 4. 可执行建议
    lines += ["## 四、可执行建议", ""]
    pattern = adjudication.get("pattern")
    trend = adjudication.get("trend")
    if pattern in ("same", "two_one"):
        tone = "按趋向安排" if trend in ("吉",) else "按趋向回避/缓办"
        lines.append(f"1. {tone}：多科同向「{trend}」，可将相关事项安排在趋向窗口内"
                     "（仍非保证，触发条件与时间窗以各科应期为准）。")
    elif pattern == "split":
        lines.append("1. 分歧事项暂缓拍板：先统一各科起局时间与历法口径复核；"
                     "仍分歧则并行观察两种趋向的触发条件，不押单边。")
    elif pattern == "single":
        lines.append("1. 单科结论仅作参考：无互证不提升强度，"
                     "以该科应期窗口回看验证。")
    else:
        lines.append("1. 各科未表态或均两可：以应期与事类细节为主，"
                     "不因求测而强行决策。")
    verify = []
    for r in bu:
        if r.get("timing"):
            verify.append(f"「{r.get('asked')}」应期参考 {_window_of(r['timing'])}")
    if verify:
        lines.append("2. 复验时点：" + "；".join(verify) + "。到点回看并回填 outcome。")
    else:
        lines.append("2. 复验时点：按各占问应期窗口回看并回填 outcome"
                     "（积累现实效度证据）。")
    pending = [r.get("asked") for r in bu
               if not ((r.get("outcome") or {}).get("recorded"))]
    if pending:
        lines.append(f"3. 未回填事项：{len(pending)} 项占问尚无结果记录，"
                     "回填后才进入效度统计。")
    lines.append("")

    # ------------------------------------------------------------ 5. 边界声明
    lines += ["## 五、边界声明", ""]
    lines.append("- 本指导为**象征推演**，给方向不给定论；凶象表述为"
                 "「偏向/有…信号/结构上」，不作「注定/一定」。")
    lines.append("- 医疗、法律、投资及重大人生决策，请以专业意见为准；"
                 "本指导不构成任何专业建议。")
    lines.append("- 合参结论只追溯各科显式判据（上表所本法则），"
                 "无判据来源的叙述不入本文。")
    lines.append("")
    return "\n".join(lines)


def tally(adjudication: dict, direction: str) -> int:
    return adjudication.get("tally", {}).get(direction, 0)


def write_guidance(archive: PersonArchive, adjudication: dict,
                   guidance_dir: str | Path) -> Path:
    text = build_guidance(archive, adjudication)
    p = Path(guidance_dir) / f"{archive.data['id']}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def main() -> int:
    import argparse
    import json
    import sys

    from cross_rules import adjudicate
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()

    ap = argparse.ArgumentParser(description="合参指导生成")
    ap.add_argument("person_json", help="person/<id>.json 路径")
    ap.add_argument("-o", "--out", help="输出目录（缺省 synthesis/guidance）")
    args = ap.parse_args()

    arch = PersonArchive(json.loads(Path(args.person_json).read_text(encoding="utf-8")))
    errs = arch.validate()
    if errs:
        print("档案校验未通过：", file=sys.stderr)
        for e in errs:
            print(f"  · {e}", file=sys.stderr)
        return 1
    recs = arch.data.get("divinations") or []
    policies = [r.get("calendar_policy") for r in recs]
    out = write_guidance(arch, adjudicate(recs, policies=policies), args.out or "guidance")
    print("指导 →", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
