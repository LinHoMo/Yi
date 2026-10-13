# -*- coding: utf-8 -*-
"""CLI 编码红线：凡带 argparse 的中文命令行入口，在 **cp936 控制台**下必须交出可读的 UTF-8。

为什么不是静态 grep 就算：本会话两次实测证明静态判据会两头出错——
①漏报：`[2]`/`[23]` 一类按**名单**跑产器的写法，清单外新增的入口一概不查——
   本科静态数一遍才发现缺守卫者 7 个（含 `dev_tools/regression.py` 这种连守卫都没写过的）；
②假阳：`golden.py` 自己不写守卫、守卫在 `golden_kit` 里，纯按"本文件有没有 reconfigure"判会错怪它。
所以本器**跑真产物**：以 `PYTHONIOENCODING=cp936` 起子进程执行 `<入口> --help`，
把 stdout/stderr 的原始字节拿来判——能按 UTF-8 解码且出现中文＝守卫生效；
出现 GBK 字节／Traceback＝退化。

只自动跑含 `argparse` 的入口：`--help` 对 argparse 是"打印后退出"，可证明无副作用；
不带 argparse 的脚本收到 `--help` 可能**真的去跑主逻辑**（金标准 capture、构建器写盘都在此类），
故不自动执行，改为**逐条列出**要求人工确认——列出而非沉默，是这门的关键设计。

已知拦不住的一种：解释器 **import 期告警**（如模块级正则的 invalid escape sequence）
按原编码写出，早于文件内任何语句，`--help` 的 stderr 里仍可能是 GBK 字节。
本器会**点名**这种（判红并写明"import 期告警"），处置办法是消除告警源或调用方带 `PYTHONUTF8=1`，
不得靠移动守卫位置假装修好——见 docs/CHANGELOG.md 第一百五十批。

    python dev_tools/check_cli_encoding.py            # 全量
    python dev_tools/check_cli_encoding.py --selftest # 负例：GBK 产物必被抓、UTF-8 产物不误伤
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

DISC = pathlib.Path(__file__).resolve().parents[1]
ROOTS = ("scripts", "dev_tools", "tests")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

# 具名豁免（照 [20] 的纪律）：命中即 NOTE 而非判红；**若该文件不再漏，必须删除本条**（反向判红）。
# 每条都要写明确切根因与"为什么不在本批改它"。
EXEMPT: dict[str, str] = {}  # 实测无漏码入口；新增豁免须写根因与另批修法（照 [20] 纪律）

# 【静态红线·照六爻第一百六十五批】"入口必须自带守卫"从散文升级成机器断言：
# discover() 找到的每一个中文入口（argparse 与无 argparse 一视同仁）文件内必须有
# UTF-8 守卫（reconfigure 或 force_utf8_stdio），缺一即判红。
# 2026-10-13 实测本科全量入口（36 个）零缺守卫 ⇒ 按红线做而非棘轮。
# 已知判不到（如实写）：守卫在**被 import 的模块**里而非入口文件自身时会误报——
# 现库无此形态（逐文件核过）；若日后出现，走 EXEMPT 具名豁免并注明守卫所在模块。
GUARD_RE = re.compile(r"""reconfigure\(\s*encoding\s*=\s*["']utf-8|force_utf8_stdio""")


def guards_missing(disc: pathlib.Path, rels: list[str]) -> list[str]:
    out: list[str] = []
    for rel in rels:
        try:
            t = (disc / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            out.append(rel + "（读不到文件）")
            continue
        if not GUARD_RE.search(t):
            out.append(rel)
    return out


def witness(label: str, text: str) -> str | None:
    """子进程产物的编码证人：解码后含 U+FFFD 即为"原始字节不是 UTF-8"的直接痕迹。

    为什么需要它：门禁套件本身已经把各 `check_*.py` 跑过一遍并拿到 stdout，
    而那些**无 argparse 的入口**（现量由本器 discover() 现跑现数，勿在散文里写死）
    不能拿 `--help` 自动回验（可能真去跑主逻辑）。
    与其为它们另造一次执行，不如在**已经存在的那次**上取证：
    若某个子器在 cp936 下写出 GBK 字节，而本器按 UTF-8 解码（`errors="replace"`），
    替换符 U+FFFD 就会留在字符串里——它是"产物不是 UTF-8"的可判特征。

    已知判不到的一种（如实写，不假装全能）：子器自己按 cp936 正确编码中文时，
    产物是合法 GBK、解码后同样会成 U+FFFD（被抓）；但若两侧编码恰好同为本地码，
    则文本看起来正常而字节并非 UTF-8——此时靠 `probe()` 那条 `--help` 路径兜。
    """
    if "\ufffd" in (text or ""):
        i = text.index("\ufffd")
        return f"{label}：产物含替换符 U+FFFD（子器写出非 UTF-8 字节）@{i} 近旁 {text[max(0, i - 24):i + 12]!r}"
    return None


def discover(roots_dir: pathlib.Path) -> tuple[list[str], list[str]]:
    """返回 (可自动跑的 argparse 入口, 只能人工确认的非 argparse 中文入口)。"""
    auto: list[str] = []
    manual: list[str] = []
    for r in ROOTS:
        d = roots_dir / r
        if not d.exists():
            continue
        for p in sorted(d.glob("*.py")):
            t = p.read_text(encoding="utf-8", errors="replace")
            if "__main__" not in t and "argparse" not in t:
                continue
            if not CJK_RE.search(t):
                continue
            rel = str(p.relative_to(roots_dir)).replace("\\", "/")
            (auto if "argparse" in t else manual).append(rel)
    return auto, manual


def probe(disc: pathlib.Path, rel: str) -> tuple[str, str]:
    env = dict(__import__("os").environ)
    env["PYTHONIOENCODING"] = "cp936"
    try:
        r = subprocess.run([sys.executable, rel, "--help"], capture_output=True,
                           cwd=str(disc), env=env, timeout=120)
    except Exception as exc:
        return "fail", f"子进程未能跑成 {type(exc).__name__}: {str(exc)[:80]}"
    out: list[str] = []
    for name, b in (("stdout", r.stdout or b""), ("stderr", r.stderr or b"")):
        if not b:
            continue
        try:
            u = b.decode("utf-8")
        except UnicodeDecodeError as e:
            hint = "（疑 import 期解释器告警，早于文件内守卫）" if name == "stderr" else ""
            return "fail", f"{name} 出现非 UTF-8 字节 @{e.start}{hint}"
        if "Traceback" in u or "ModuleNotFoundError" in u:
            return "fail", f"{name} 有异常回显：{u.strip().splitlines()[-1][:80]}"
        out.append(u)
    if not any(CJK_RE.search(u) for u in out):
        return "note", "help 产物无可判中文（守卫在位则无妨，记为未证）"
    return "ok", ""


def negative_selftest(problems: list[str]) -> None:
    """两式：GBK 字节产物必须被抓；UTF-8 产物不得误伤。夹具只落临时目录（铁律二）。"""
    import os
    import tempfile
    with tempfile.TemporaryDirectory(prefix="clienc_") as td:
        root = pathlib.Path(td)
        (root / "scripts").mkdir()
        bad = root / "scripts" / ("bad_" + "cli.py")  # 拼串：字面量会被 [11] 当死指针
        bad.write_text("import argparse, sys\n"
                       "p = argparse.ArgumentParser(description='中文说明')\n"
                       "sys.stdout.buffer.write('乱码测试'.encode('gbk'))\n"
                       "p.parse_args()\n", encoding="utf-8")
        good = root / "scripts" / ("good_" + "cli.py")
        good.write_text("import argparse, sys\n"
                        "try:\n    sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"
                        "except Exception:\n    pass\n"
                        "argparse.ArgumentParser(description='中文说明').parse_args()\n", encoding="utf-8")
        st, msg = probe(root, "scripts/" + "bad_cli.py")
        if st != "fail":
            problems.append(f"负例自证失效：GBK 产物没被抓到 → {st}｜{msg}")
        st2, msg2 = probe(root, "scripts/" + "good_cli.py")
        if st2 == "fail":
            problems.append(f"负例自证假阳性：UTF-8 产物被判红 → {msg2}")
        # 第四式（静态红线·照六爻）：无守卫的中文入口必被抓；带守卫的不得误伤。
        noguard = root / "scripts" / ("noguard_" + "cli.py")
        noguard.write_text("# -*- coding: utf-8 -*-\n中文说明的入口，故意不写守卫\n"
                           "if __name__ == '__main__':\n    print('中文')\n", encoding="utf-8")
        withguard = root / "scripts" / ("withguard_" + "cli.py")
        withguard.write_text("# -*- coding: utf-8 -*-\nimport sys\n中文说明\n"
                             "sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n", encoding="utf-8")
        miss = guards_missing(root, ["scripts/" + "noguard_cli.py", "scripts/" + "withguard_cli.py"])
        if "scripts/" + "noguard_cli.py" not in miss:
            problems.append("负例自证失效：静态红线没抓到缺守卫入口")
        if "scripts/" + "withguard_cli.py" in miss:
            problems.append("负例自证假阳性：静态红线误伤了带守卫入口")
    # 第三式：证人须认出非 UTF-8 产物（GBK 字节按 UTF-8 解码必留 U+FFFD），且不误伤干净文本
    raw = "中文测试".encode("gbk").decode("utf-8", errors="replace")
    if witness("夹具", raw) is None:
        problems.append("负例自证失效：witness 没认出 GBK 产物")
    if witness("夹具", "正常中文输出") is not None:
        problems.append("负例自证假阳性：witness 误伤了干净 UTF-8 产物")

def main() -> int:
    import io
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="CLI 编码红线（cp936 下产物须为可读 UTF-8）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    problems: list[str] = []
    auto, manual = discover(DISC)
    if not auto and not manual:
        print(f"× 未发现任何中文 CLI 入口（{ROOTS}）——本器等于没跑，不判通过")
        return 1
    if args.selftest:
        negative_selftest(problems)
        print("  [selftest] 负例已跑（GBK 产物必被抓 / UTF-8 产物不误伤 / 缺守卫入口必被抓 / 带守卫不误伤）")

    # 静态红线：每一个中文 CLI 入口（含无 argparse 者）文件内必须自带 UTF-8 守卫。
    _miss = guards_missing(DISC, sorted(auto + manual))
    _miss = [m for m in _miss if m not in EXEMPT]
    for m in _miss:
        problems.append(f"入口缺 UTF-8 守卫（静态红线）：{m}")
    print(f"静态红线：中文 CLI 入口 {len(auto) + len(manual)} 个，缺守卫 {len(_miss)} 个")

    nok = nnote = 0
    hit_exempt: set[str] = set()
    for rel in auto:
        st, msg = probe(DISC, rel)
        if st == "fail" and rel in EXEMPT:
            hit_exempt.add(rel)
            nnote += 1
            print(f"  NOTE 具名豁免 {rel}：{msg}｜根因与另批修法见本器 EXEMPT")
        elif st == "fail":
            problems.append(f"CLI 编码退化：{rel} → {msg}")
        elif st == "note":
            nnote += 1
            if args.verbose:
                print(f"  · {rel}：{msg}")
        else:
            nok += 1
    for rel in EXEMPT:
        if rel not in hit_exempt and rel in auto:
            problems.append(f"豁免条目失效：{rel} 已不再漏码——请删除该条豁免（不许留着空壳）")
    print(f"自动回验：argparse 中文入口 {len(auto)} 个，UTF-8 产物可读 {nok} 个，"
          f"NOTE {nnote} 个，判红 {sum(1 for p in problems if 'CLI 编码退化' in p)} 个，"
          f"具名豁免命中 {len(hit_exempt)}/{len(EXEMPT)}")
    if manual:
        print(f"须人工确认（无 argparse，`--help` 可能触发主逻辑，本器不自动执行）：{len(manual)} 个")
        for rel in manual:
            print("  · " + rel)

    for x in problems:
        print("× " + x)
    if problems:
        return 1
    print("√ 全部可自动回验的中文 CLI 在 cp936 下均交出可读 UTF-8 产物")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
