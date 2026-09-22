#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六爻 SHAP 风格因子贡献可视化
生成横向条形图 + 瀑布图，显示每项因子如何推得最终评分。
"""
import os
import sys
import json
import random

# 确保可找到 scripts 包
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

def _try_import_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        # 尝试找中文字体
        for fn in ["SimHei", "Microsoft YaHei", "Noto Sans CJK SC", "PingFang SC",
                   "Source Han Sans SC", "AR PL UMing CN", "WenQuanYi Micro Hei"]:
            if any(fn.lower() in f.name.lower() for f in fm.fontManager.ttflist):
                plt.rcParams["font.sans-serif"] = [fn]
                break
        plt.rcParams["axes.unicode_minus"] = False
        return plt
    except ImportError:
        return None


def generate_sample_hex(question: str = "婚姻感情走向", seed: int = None) -> dict:
    """调用引擎获取一个示例卦象的完整输出（含 factor_contributions）。"""
    if seed is not None:
        random.seed(seed)
    import scripts.liuyao_engine as engine
    import scripts.classical_analysis as ca
    from scripts.thinking_chain import run_thinking_chain

    yao = [random.choice([6, 7, 8, 9]) for _ in range(6)]
    months = list(range(1, 13))
    days = list(range(1, 29))
    hours = list(range(0, 23))
    d = engine.build_hexagram_result(
        yao, question, "coin",
        2024, random.choice(months), random.choice(days), random.choice(hours),
    )
    d = ca.enhance_reading(d)
    d["question"] = question
    tc = run_thinking_chain(d)
    return tc


def render_bar_chart(factor_contributions: list, verdict: str, final_score: float, out_path: str) -> bool:
    """横向条形图（SHAP 风格）：红色=拖累，绿色=助力，按绝对值排序。"""
    plt = _try_import_matplotlib()
    if plt is None:
        print("[warn] matplotlib 未安装，跳过条形图", file=sys.stderr)
        return False

    # 过滤接近 0 的
    fcs = [fc for fc in factor_contributions if abs(fc.get("score", 0)) > 0.001]
    if not fcs:
        fcs = factor_contributions[:5]
    # 按绝对值从大到小排序
    fcs_sorted = sorted(fcs, key=lambda x: abs(x.get("score", 0)), reverse=True)

    labels = [fc.get("name", "") for fc in fcs_sorted]
    values = [fc.get("score", 0) for fc in fcs_sorted]
    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in values]

    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.55)))
    y = list(range(len(labels)))
    ax.barh(y, values, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=11)
    ax.invert_yaxis()
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.set_xlabel("分数贡献", fontsize=11)
    ax.set_title(f"六爻因子贡献分解（{verdict}，最终 {final_score:+.2f}）", fontsize=13, pad=12)
    # 在条柱末端标注数值
    for i, v in enumerate(values):
        ax.text(v + (0.05 if v >= 0 else -0.05), i,
                f"{v:+.2f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=9)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close()
    return True


def render_waterfall(factor_contributions: list, verdict: str, final_score: float, out_path: str) -> bool:
    """瀑布图：base + 各因子逐步累加到最终分数。"""
    plt = _try_import_matplotlib()
    if plt is None:
        print("[warn] matplotlib 未安装，跳过瀑布图", file=sys.stderr)
        return False

    # 分离 base_score 与其余因子
    base_val = 0.0
    extra_fcs = []
    for fc in factor_contributions:
        if fc.get("factor") == "base" and fc.get("name") == "用神旺衰":
            base_val = fc.get("score", 0)
        else:
            extra_fcs.append(fc)

    # 按绝对值从大到小排序
    extra_fcs_sorted = sorted(extra_fcs, key=lambda x: abs(x.get("score", 0)), reverse=True)

    steps = [("用神旺衰(base)", base_val)]
    for fc in extra_fcs_sorted:
        steps.append((fc.get("name", ""), fc.get("score", 0)))

    # 计算累计值
    cumulative = [0.0]
    running = base_val
    for _, v in steps[1:]:
        cumulative.append(running)
        running += v
    cumulative.append(running)

    # 颜色：base 用蓝色；正因子绿；负因子红
    colors = ["#3498db"]
    for _, v in steps[1:]:
        colors.append("#2ecc71" if v >= 0 else "#e74c3c")

    fig, ax = plt.subplots(figsize=(11, max(5, len(steps) * 0.5)))
    # 瀑布柱：base 从 0 开始，其他柱从累计值开始往上/往下长
    bar_heights = [base_val] + [v for _, v in steps[1:]]
    bar_bottoms = [0.0] + cumulative[1:-1]
    x = list(range(len(steps)))
    for i in range(len(steps)):
        h = bar_heights[i]
        b = bar_bottoms[i]
        if h < 0:
            b = b + h
            h = -h
        ax.bar(x[i], h, bottom=b, color=colors[i], edgecolor="white", linewidth=0.5)

    # 累计线
    running_total = base_val
    points_x = [0]
    points_y = [base_val]
    for _, v in steps[1:]:
        running_total += v
        points_x.append(points_x[-1] + 1)
        points_y.append(running_total)
    ax.step(points_x, points_y, where="pre", color="#333", linewidth=1.2, linestyle="--", zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels([s[0] for s in steps], rotation=35, ha="right", fontsize=10)
    ax.axhline(0, color="#888", linewidth=0.8)
    ax.set_ylabel("累计分数", fontsize=11)
    ax.set_title(f"六爻分数瀑布图（{verdict}，最终 {final_score:+.2f}）", fontsize=13, pad=12)
    # 最终分数标注
    ax.annotate(f"最终 {final_score:+.2f}",
                xy=(x[-1], running_total),
                xytext=(10, 5), textcoords="offset points",
                fontsize=10, color="#333",
                arrowprops=dict(arrowstyle="->", color="#666", lw=0.8))

    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close()
    return True


def main():
    """命令行入口：python visualize_shap.py [--question X] [--outdir DIR]"""
    question = "婚姻感情走向"
    outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "viz")
    seed = None

    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--question" and i + 1 < len(argv):
            question = argv[i + 1]; i += 2
        elif argv[i] == "--outdir" and i + 1 < len(argv):
            outdir = argv[i + 1]; i += 2
        elif argv[i] == "--seed" and i + 1 < len(argv):
            seed = int(argv[i + 1]); i += 2
        else:
            i += 1

    os.makedirs(outdir, exist_ok=True)
    tc = generate_sample_hex(question, seed=seed)
    s5 = tc.get("thinking_chain", {}).get("step5_synthesis", {})
    fcs = s5.get("factor_contributions", [])
    verdict = s5.get("verdict", "平")
    final_score = s5.get("final_score", 0.0)

    bar_path = os.path.join(outdir, "shap_bar.png")
    wf_path = os.path.join(outdir, "shap_waterfall.png")

    ok1 = render_bar_chart(fcs, verdict, final_score, bar_path)
    ok2 = render_waterfall(fcs, verdict, final_score, wf_path)

    # 输出摘要 JSON 便于外部程序使用
    summary = {
        "question": question,
        "hexagram": tc.get("original_hex", {}).get("name") if isinstance(tc.get("original_hex"), dict) else "",
        "verdict": verdict,
        "final_score": final_score,
        "original_score": s5.get("factor_contribution_verification"),
        "bar_path": bar_path if ok1 else None,
        "waterfall_path": wf_path if ok2 else None,
    }
    summary_path = os.path.join(outdir, "shap_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if ok1 and ok2 else 1


if __name__ == "__main__":
    sys.exit(main())
