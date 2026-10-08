# 本文件为聚合入口：子模块见 engine_*/chain_*/classical_*。
import os as _ks_os, sys as _ks_sys   # 内核定位规则只在 kernel_path.py 一份实现

_ks_d = _ks_os.path.dirname(_ks_os.path.abspath(__file__))

if _ks_d not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_d)

from kernel_path import ensure_kernel_on_path as _ensure_kernel

_ensure_kernel(__file__)



import argparse

import json

import logging

import os

import random

import sys

from datetime import datetime, timedelta

_log = logging.getLogger(__name__)


from yishu_core.runtime import force_utf8_stdio as _force_utf8_stdio  # noqa: E402

from engine_calendar import apply_true_solar_time, handle_zi_hour
from engine_chart import (
    coin_toss,
    time_based_hexagram,
    number_based_hexagram,
    build_hexagram_result,
)
from engine_format import (
    format_text_output,
    format_reading_output,
    apply_depth_limit,
    _apply_depth_to_result,
)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="六爻纳甲装卦引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python liuyao_engine.py --mode coin --question "我的投资运势如何？"
  python liuyao_engine.py --mode time --datetime "2026-09-18 14:30"
  python liuyao_engine.py --mode number --numbers "3,5,8"
  python liuyao_engine.py --mode manual --yao "7,8,9,7,6,8"
  python liuyao_engine.py --mode coin --output json
        """
    )

    parser.add_argument(
        "--mode",
        choices=["coin", "time", "number", "manual"],
        default="coin",
        help="起卦方式 (默认: coin)"
    )
    
    parser.add_argument(
        "--question",
        type=str,
        default="未指明的占卜问题",
        help="求测问题"
    )
    
    parser.add_argument(
        "--datetime",
        type=str,
        default=None,
        help='时间起卦的指定时间，格式: "YYYY-MM-DD HH:MM"'
    )
    
    parser.add_argument(
        "--numbers",
        type=str,
        default=None,
        help='数字起卦的三个数字，格式: "a,b,c"'
    )
    
    parser.add_argument(
        "--yao",
        type=str,
        default=None,
        help='手动指定的6个爻值，格式: "v1,v2,v3,v4,v5,v6" (6=老阴动,7=少阳静,8=少阴静,9=老阳动)'
    )
    
    parser.add_argument(
        "--output",
        choices=["json", "text", "html"],
        default="json",
        help="输出格式 (默认: json)"
    )

    parser.add_argument(
        "--format",
        choices=["json", "text", "html"],
        default=None,
        help="输出格式 (优先级高于 --output)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="随机种子，用于可复现的铜钱摇卦结果"
    )
    
    parser.add_argument(
        "--longitude",
        type=float,
        default=None,
        help="出生地经度(东经)，用于真太阳时校正。例如北京116.4，喀什75.9"
    )

    parser.add_argument(
        "--log-note",
        type=str,
        default="",
        help="占卜日志备注，记入 divination_events.jsonl 供后续验证"
    )

    # ── 报告输出专用参数 ──
    parser.add_argument(
        "--save-html",
        type=str,
        default=None,
        metavar="PATH",
        help="将HTML报告保存到指定路径（自动创建目录）"
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="生成HTML报告后自动在浏览器中打开（需配合 --format html）"
    )

    parser.add_argument(
        "--distinguish-zi-hour",
        action="store_true",
        default=False,
        help="启用早晚子时区分：早子时(23:00-00:00)日柱用当日，晚子时(00:00-01:00)日柱用翌日（出自《增删易》《卜筮正宗》）"
    )

    parser.add_argument(
        "--hour",
        type=int,
        default=None,
        help="手动指定小时(0-23)，覆盖 --datetime 或当前时间的小时值。用于精确测试子时场景。"
    )

    parser.add_argument(
        "--zi-hour-type",
        choices=["early", "late"],
        default=None,
        help="手动指定子时类型：early=早子时(当日日柱)，late=晚子时(翌日日柱)。优先级高于自动判断。"
    )

    parser.add_argument("--version", action="store_true", help="打印易·六爻版本后退出")
    parser.add_argument(
        "--depth",
        choices=["brief", "standard", "full"],
        default="standard",
        help="解读深度: brief=300字, standard=800字, full=全量(默认standard)"
    )

    return parser.parse_args()


def main():
    _force_utf8_stdio()
    args = parse_arguments()

    if getattr(args, "version", False):
        import yishu_core
        print(f"易 · 六爻 v{yishu_core.__version__}")
        return

    # 真太阳时校正 (如果提供了 --longitude)
    longitude_info = None
    if args.longitude is not None:
        if args.datetime:
            dt = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M")
            _year, _month, _day, _hour = dt.year, dt.month, dt.day, dt.hour
        else:
            now = datetime.now()
            _year, _month, _day, _hour = now.year, now.month, now.day, now.hour
        
        longitude_info = apply_true_solar_time(
            _year, _month, _day, _hour,
            longitude=args.longitude
        )
        print(f"[真太阳时校正] 经度={args.longitude}°E → "
              f"校正后 {_hour}:00 → {longitude_info['corrected_hour']}:{longitude_info['corrected_minute']:02d} "
              f"时辰={longitude_info['shichen']} "
              f"(偏移 {longitude_info['offset_minutes']} 分钟)",
              file=sys.stderr)
    
    # 确定时间
    if args.datetime:
        try:
            dt = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M")
            year, month, day, hour = dt.year, dt.month, dt.day, dt.hour
        except ValueError:
            print(f"错误：时间格式不正确，应为 YYYY-MM-DD HH:MM", file=sys.stderr)
            sys.exit(1)
    else:
        now = datetime.now()
        year, month, day, hour = now.year, now.month, now.day, now.hour
    
    # 应用真太阳时校正到 hour (用于时间起卦)
    if longitude_info is not None:
        hour = longitude_info["corrected_hour"]

    # 手动指定小时 (--hour 参数覆盖)
    if args.hour is not None:
        if not (0 <= args.hour <= 23):
            print(f"错误：--hour 参数必须在 0-23 之间，收到 {args.hour}", file=sys.stderr)
            sys.exit(1)
        hour = args.hour
        print(f"[手动指定] --hour {hour}", file=sys.stderr)

    # 设置随机种子 (可复现模式)
    rng = None
    if args.seed is not None:
        random.seed(args.seed)
        rng = random.Random(args.seed)
        print(f"[SEED {args.seed}] 可复现模式", file=sys.stderr)
    
    # 起卦
    try:
        if args.mode == "coin":
            yao_values = coin_toss(random_gen=rng)
            method = "铜钱摇卦"
            
        elif args.mode == "time":
            yao_values = time_based_hexagram(year, month, day, hour)
            method = "时间起卦"
            
        elif args.mode == "number":
            if args.numbers is None:
                print("错误：数字起卦需要 --numbers 参数，格式为 'a,b,c'", file=sys.stderr)
                sys.exit(1)
            try:
                nums = [int(x.strip()) for x in args.numbers.split(",")]
                if len(nums) != 3:
                    print("错误：数字起卦需要恰好3个数字", file=sys.stderr)
                    sys.exit(1)
                yao_values = number_based_hexagram(nums[0], nums[1], nums[2])
                method = "数字起卦"
            except ValueError:
                print("错误：数字格式不正确", file=sys.stderr)
                sys.exit(1)
                
        elif args.mode == "manual":
            if args.yao is None:
                print("错误：手动起卦需要 --yao 参数，格式为 'v1,v2,v3,v4,v5,v6'", file=sys.stderr)
                sys.exit(1)
            try:
                yao_values = [int(x.strip()) for x in args.yao.split(",")]
                if len(yao_values) != 6:
                    print("错误：手动起卦需要恰好6个爻值", file=sys.stderr)
                    sys.exit(1)
                for v in yao_values:
                    if v not in (6, 7, 8, 9):
                        print(f"错误：爻值只能是6/7/8/9，得到 {v}", file=sys.stderr)
                        sys.exit(1)
                method = "手动指定"
            except ValueError:
                print("错误：爻值格式不正确", file=sys.stderr)
                sys.exit(1)

        # 早晚子时处理 (step 0: adjust day pillar if --distinguish-zi-hour)
        zi_hour_info = None
        _pillar_year, _pillar_month, _pillar_day = year, month, day
        if args.distinguish_zi_hour and hour in (0, 23):
            _minute = longitude_info["corrected_minute"] if longitude_info else 0
            zi_hour_info = handle_zi_hour(hour, _minute, year, month, day)

            # 手动指定子时流派 override
            if args.zi_hour_type is not None:
                base_date = datetime(year, month, day)
                if args.zi_hour_type == "late":
                    # 换日派：夜子时已作次日之日辰
                    next_date = base_date + timedelta(days=1)
                    zi_hour_info = {
                        "type": "夜子时(换日派·手动)",
                        "shichen": "子",
                        "day_date": next_date,
                        "day_year": next_date.year,
                        "day_month": next_date.month,
                        "day_day": next_date.day,
                        "description": f"夜子时(手动·换日派)，日柱取{next_date.strftime('%Y-%m-%d')}日子时",
                    }
                else:  # early → 与默认口径一致
                    zi_hour_info = {
                        "type": "子时(当日派·手动)",
                        "shichen": "子",
                        "day_date": base_date,
                        "day_year": base_date.year,
                        "day_month": base_date.month,
                        "day_day": base_date.day,
                        "description": f"子时(手动·当日派)，{base_date.strftime('%Y-%m-%d')}日子时，日柱用当日",
                    }

            # 用 zi_hour_info 中的 day_date 覆盖日柱参数
            if zi_hour_info is not None:
                _pillar_year = zi_hour_info["day_year"]
                _pillar_month = zi_hour_info["day_month"]
                _pillar_day = zi_hour_info["day_day"]
                print(f"[早晚子时] {zi_hour_info['description']}", file=sys.stderr)

        # 构建完整排盘结果
        # 早晚子时模式下使用调整后的日柱日期 (_pillar_year/month/day)
        result = build_hexagram_result(
            yao_values, args.question, method,
            _pillar_year, _pillar_month, _pillar_day, hour
        )

        # 将早晚子时信息附加到结果中（将 datetime 转为字符串以兼容 JSON 序列化）
        if zi_hour_info is not None:
            if "enhancements" not in result:
                result["enhancements"] = {}
            _zi_out = dict(zi_hour_info)
            if hasattr(_zi_out.get("day_date"), "strftime"):
                _zi_out["day_date"] = _zi_out["day_date"].strftime("%Y-%m-%d")
            result["enhancements"]["zi_hour_handling"] = _zi_out
        
        # 增强分析：伏藏、暗动、月破、三合局等经典断法
        try:
            from classical_analysis import enhance_reading
            enhance_reading(result)
        except ImportError:
            _log.warning("classical_analysis 模块未安装：伏藏/暗动/月破/三合局增强跳过（ImportError）。"
                          "安装后可启用：pip install <liuyao-classical-analysis>")
        
        # 五步思维链断卦分析（基于已输出的机械排盘数据推导结论）
        chain = None
        try:
            from thinking_chain import run_thinking_chain
            chain_full = run_thinking_chain(result)
            chain = chain_full.get("thinking_chain", chain_full)
        except ImportError:
            _log.warning("thinking_chain 模块未安装：五步思维链分析跳过（ImportError）。")

        # ── 分类占法选择建议 (section_advice) ──
        verdict_text = ""
        if chain and isinstance(chain, dict):
            step5 = chain.get("step5_synthesis", {})
            if isinstance(step5, dict):
                verdict_text = step5.get("verdict", "")
        category_text = args.question or result.get("question", "")
        try:
            from advice_framework import generate_advice
            advice_items = generate_advice(verdict_text, category_text, result)
            result["section_advice"] = advice_items
        except ImportError:
            _log.warning("advice_framework 模块未安装：分类占法建议跳过（ImportError）。")

        # 确定最终输出格式 (--format 优先于 --output)
        output_format = args.format if args.format is not None else args.output

        # 应用解读深度限制
        depth = getattr(args, "depth", "standard") or "standard"

        # 输出
        if output_format == "html":
            try:
                from render import render_html
                a = dict(result)
                a["thinking_chain"] = chain
                html_out = render_html(a)
                # 保存到文件（若指定 --save-html）
                save_path = getattr(args, "save_html", None)
                if save_path:
                    save_dir = os.path.dirname(save_path)
                    if save_dir and not os.path.exists(save_dir):
                        os.makedirs(save_dir, exist_ok=True)
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(html_out)
                    print(f"[已保存] HTML 报告 → {save_path}", file=sys.stderr)
                # 自动打开浏览器
                if getattr(args, "open_browser", False):
                    import tempfile
                    import webbrowser
                    if not save_path:
                        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
                        tmp.write(html_out)
                        tmp.close()
                        save_path = tmp.name
                    webbrowser.open(f"file:///{save_path.replace(os.sep, '/')}")
                # 未保存也未打开浏览器时才输出到stdout
                if not save_path:
                    print(html_out)
            except ImportError:
                print("[WARN] render module not installed, fallback to JSON", file=sys.stderr)
                _apply_depth_to_result(result, depth)
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        elif output_format == "json":
            _apply_depth_to_result(result, depth)
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        elif output_format == "text" and chain is not None:
            full_text = format_reading_output(result, chain)
            # 将 section_advice 附加到文本报告末尾
            if result.get("section_advice"):
                full_text += "\n" + "=" * 52 + "\n"
                full_text += "【趋避建议】\n"
                for i, adv in enumerate(result["section_advice"], 1):
                    full_text += f"  {i}. {adv}\n"
            print(apply_depth_limit(full_text, depth))
        else:
            full_text = format_text_output(result)
            if result.get("section_advice"):
                full_text += "\n" + "-" * 50 + "\n"
                full_text += "趋避建议：\n"
                for i, adv in enumerate(result["section_advice"], 1):
                    full_text += f"  {i}. {adv}\n"
            print(apply_depth_limit(full_text, depth))

        # 记录占卜事件日志 (每次占卜自动记录)
        try:
            from event_logger import log_divination
            event_id = log_divination(
                result,
                notes=args.log_note or "",
                seed=args.seed,
                longitude=args.longitude,
            )
            print(f"[EVENT LOGGED] {event_id}", file=sys.stderr)
        except Exception as log_err:
            print(f"[LOG WARNING] 事件日志记录失败: {log_err}", file=sys.stderr)

    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
