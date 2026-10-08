# -*- coding: utf-8 -*-
"""断语外置**取证**门：跑真实报告，反查哪些中文句子没进 `data/*.json`。

  python tools/verdict_audit.py                 # 只报告（始终退出 0，人审用）
  python tools/verdict_audit.py --strict        # 白名单外的未外置句一律判失败
  python tools/verdict_audit.py --verbose       # 逐句列全部中文结论句

为什么是"取证"而不是静态正则（AGENTS.md §三 的落地方式）：
  旧的 `check_verdict_literals` 是**文本启发式**——数 .py 里的中文字面量条数。
  两个方向都不可靠：① 假阴性：硬编码在 .py 里的断语只要不是"≥3 条连续字典值"
  就抓不到（本次审计就逮到小六壬 `事势偏顺，宫义为吉` 一整句漏外置）；
  ② 假阳性：把 docstring / 模块说明 / argparse help 当成断语批量外置，
  只会让代码读不懂。本脚本不猜代码长什么样，而是**看终端用户到底读到了什么**。

判据：报告正文里每句 ≥8 个汉字的中文结论句，若不在本科 `data/**` 与
`references/**` 语料池里，即为"疑似未外置断语"。

复用 `verify_web_parity.py` 的 10 条正例——同一个请求集，一份维护两处受益。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT / "tools"))

from yishu_core.runtime import force_utf8_stdio, utf8_subprocess_env  # noqa: E402

# 与 verify_web_parity.py 同源：同一批正例，断语外置审计与同源验收共用
CASES = (
    {"discipline": "liuyao", "question": "占本周面试能否通过", "mode": "time",
     "datetime": "2026-09-30 10:30"},
    {"discipline": "liuyao", "question": "占求财", "mode": "manual",
     "datetime": "2026-09-22 23:40", "yao": "7,8,9,7,6,8"},
    {"discipline": "ming", "datetime": "1990-05-20 10:30", "gender": "男"},
)

MIN_HANZI = 8
CN = re.compile(r"[\u4e00-\u9fff]")

# 「非断语」豁免：这些中文句在报告里出现属正常，搬进 data/*.json 反而是倒退
#   — 书源标注（（《某书·篇》）+ 结论标签）
#   — 事实陈述（干支配列：丙午年 丁酉月 丁未日）
#   — 模块/口径说明与免责（铁律三要求必须写在输出里，不能进 data）
#   — 结构化术语标签（**用克体**、六神辅助（青龙临用））
# 2026-10-02 逐条复核（HANDOFF §四.B）：每条都补了「为何属非断语」；两条过宽的
# 括注分支（旧 02/06：行首带括注即整句豁免）已收紧为「括注后短尾」，此前它们把
# 「官鬼（落在卯三爻）几乎使不上劲」这类真判语整个豁免掉——那类句子由下方
# REL_LOC_PREFIX 机械定位前缀剥离（与 YAO_PREFIX 同理）交还语料匹配，不再靠白名单。
NON_VERDICT = re.compile(
    r"（\s*[《＜]"                       # ① 书源括注：出处标注（（《增删卜易》））不是断语
    r"|^\s*[（(]?[^，。；：！（）]{0,10}（[^）]{1,14}）[^）]{0,8}$"
    # ② 括注性术语标签：整句 = 「术语（机械值）」且括注后短尾（如「用神旺衰（用神极弱）」
    #    「这副卦是丰（坎宫·五世）」）；旧版无短尾约束，任何行首带括注的判语都被整句豁免
    r"|^\s*(?:干支|年月日时|[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]年)"
    # ③ 事实配列：干支历行列（「丙午年 丁酉月 丁未日」）是机械事实；旧版硬编码「丙午年」
    r"|本模块不宣称|不作现实承诺|以专业意见为准"
    # ④ 免责声明（铁律三要求必须写在输出里，跨科统一由代码给）
    r"|查表直录|机械标签|无吉凶断语|不写命运断语"
    # ⑤ 口径声明：查表/机械边界声明
    r"|^\s*\*{0,2}[^，。；：！（）]{0,12}\*{0,2}（[^）]{1,14}）[^）]{0,8}$"
    # ⑥ 表格/标题式术语标签：加粗短标签+括注（同 ② 短尾约束）
    r"|^\s*\*{0,2}[\u4e00-\u9fff×]{1,12}\*{0,2}（[^）]{0,16}$"
    # ⑥b 因子节标题带所本括注（「**流月**（正月起五虎遁：…」等，× 属标题用字）
    r"|^\*{0,2}[\u4e00-\u9fff]{2,10}\*{0,2}（(?:富局|贵局|杂局)·(?:未)?成立）"
    # ⑥c 紫微格局判定行 = 格局名 + 内核判定状态（富局/贵局·未成立）+ 书源诀文；
    #    名与诀文均外置 geju_rules.json，中间插入的状态值使子串匹配必漏
    r"|^\*{0,2}[\u4e00-\u9fff]{2,4}\*{0,2}（[子丑寅卯辰巳午未申酉戌亥]宫）"
    r"[\u4e00-\u9fff]{1,6}（[子丑寅卯辰巳午未申酉戌亥]宫(?:入庙|庙|旺|得地|得|利|平|不得地|落陷)）$"
    # ⑥d 紫微十二宫安星事实行：「**迁移**（午宫）武曲（午宫旺）」——宫名/宫支/星名/亮度
    #    全是 core 安星表的机械查表值，无断语
    r"|在当下月令是\*{0,2}[旺相休囚死]"
    # ⑥e 梅花卦气事实句：「体卦乾（金）在当下月令是**旺**」——卦气旺衰查表值
    r"|^就[^，。]{2,8}这一问而言（用卦为"
    # ⑥f 梅花报告包裹壳（「就{focus}这一问而言（用卦为X）」）：wrap 模板+机械取象括注
    r"|问题词典推断|有古籍逐条出处|无古籍逐条出处"
    # ⑥g 用神取法来源标注（question_use_gods 的 meta.source 标签），非断语
    r"|六爻纳甲·|命·因子推演|大六壬·|灵棋经·|小六壬分析|择吉分析|紫微斗数因子推演"
    r"|六爻纳甲推演|以上为机械"
    # ⑦ 科目章节标题（「综合下来」已删：独立成句时短于 8 字被 MIN_HANZI 跳过，
    #    接续真判语时它不该替判语豁免）
    r"|^占[^，。]{2,12}$"
    # ⑧ 用户问句回显（报告开头"你问「X」"里的 X 本就是输入，不是断语）
    r"|起卦于|时机上可多留意|星煞只记"
    # ⑨ 事实/结构行：起卦时刻、应期提示、星煞口径说明
    r"|古歌诀有云|古人类似情境"
    # ⑩ 歌诀引导模板（后接的歌诀原文来自 data，模板本身不算断语）
    r"|二十八宿值日吉凶歌"
    # ⑪ 择吉「值宿歌诀」引导句（原文在 data/citations.json#xiu_verses，引导句只报
    #    书名/宿名/神将/出处，属排版）
    r"|流年[干支].{1,2}[与对]运[干支].{1,2}"  # ⑫ 内核术语派生的事实句（十神/刑合由 core 算出）
    r"|天克地冲"                              # ⑬ 命科结构标签（干支相克相冲，core 算出）
    r"|无法逐字核对|通行起例|机械安星，不批吉凶|只记是否临爻"
    # ⑭ 出处/口径诚实声明（铁律三要求写进输出，跨科统一由代码/核心给）
    r"|^《[^》]+》\s*\+"
    # ⑮ 书源并列注（语料里以「《卷二·体用总诀》」形式存在，此处为渲染后的拼接）
    r"|^两下里是.*的关系$|^留意克体之卦|^但有小阻"
    # ⑯ 已有 rel_* 模板覆盖、被标点切碎的片段
)


def is_verdict(clause: str) -> bool:
    """该句是否属「应外置到 data/*.json 的断语」。"""
    return not NON_VERDICT.search(clause)
# 结构行与免责声明：不是断语，不该进 data（前者是排版，后者跨科统一由 report/py 层给）
ALLOW_PAT = re.compile(
    r"^#{1,6}\s"                                   # Markdown 标题
    r"|（(?:出厂|口径|免责|框架|非|只|不)[^）]*）"   # 括注性说明
    r"|(?:口径|免责)?提示[：:]?(?:此占|本|报告)?(?:为)?象数参考|不作现实承诺|以专业意见为准"
    r"|^[一-龥]{1,6}[、:：]?$"                      # 纯结构短标签
)


def _argv(case: dict, outdir: Path) -> list[str]:
    """请求 dict → report.py 命令行（键名与 report.py 参数同名）。"""
    cmd = [sys.executable, str(ROOT / "tools" / "report.py"),
           "--outdir", str(outdir)]
    for k, v in case.items():
        if k == "discipline":
            cmd += ["--discipline", v]
        else:
            cmd += [f"--{k.replace('_', '-')}", str(v)]
    return cmd


# 爻位＋六亲是 chart 层的机械定位信息（「三爻兄弟」≠ 措辞），模板里只存成
# `{pos}{rel}`。渲染后它们会顶在断语前面，若不剥掉，已外置的模板会被判成漏外置。
YAO_PREFIX = re.compile(r"^[一二三四五六七八九十初上去末]{1,2}爻[\u4e00-\u9fff]{0,4}")


def _strip_yao_prefix(clause: str) -> str:
    return YAO_PREFIX.sub("", clause)


# 六亲＋「（落在支爻）」同属 chart 层机械定位：旺衰模板存成 `{use_cat}{loc}正文`
# （liuyao_narrate._strength_sentence 的 loc = （落在{支}{爻}）），渲染成
# 「官鬼（落在卯三爻）几乎使不上劲」。插入值夹在句中，纯子串匹配必漏——
# 与 YAO_PREFIX 同理剥掉这个定位括注，让正文部分回到语料匹配。
# 2026-10-02（HANDOFF §四.B）：此前这类句子被过宽的括注白名单整句豁免，判语
# 「几乎使不上劲」既不在语料也无人看见；白名单收紧后由本剥离接管。
REL_LOC_PREFIX = re.compile(
    r"^[子孙妻财父母兄弟官鬼]{2}（落在[子丑寅卯辰巳午未申酉戌亥]"
    r"(?:初|[一二三四五六七八九十])爻?）"
)


def _strip_locator_prefix(clause: str) -> str:
    return REL_LOC_PREFIX.sub("", clause)


# `{focus}` 是**输入侧的焦点主语**（由问题抽出，如「所问之事」），不是引擎措辞：
# wrap_pos = "就{focus}来说，{text}。" 保证每份报告都套这层壳，于是渲染后
# 「所问之事」会顶在断语前面（「所问之事阻力不光是面上的…」），
# 而语料池存的是模板串 `{focus}阻力不光是面上的…`，抽汉字后焦点已被吃掉
# → 一边有主语一边没有，直接比对必然漏判。
# 焦点词不硬编码（取值随问题变），从本报告自举：wrap 模板出现就一定会捕获到。
FOCUS_WRAP = re.compile(r"就([\u4e00-\u9fff]{2,8})来说")


def _focuses(md_text: str) -> set[str]:
    return {m.group(1) for m in FOCUS_WRAP.finditer(md_text)}


def _strip_focus(h: str, focuses: set[str]) -> str:
    for f in sorted(focuses, key=len, reverse=True):
        if h.startswith(f):
            return h[len(f):]
    return h


def _hanzi(s: str) -> str:
    """抽汉字：**待检句与语料池走同一函数**，这是判定的唯一归一口径。

    两边都抽成纯汉字串后，两类噪声自动消失，不需要任何额外剥离：
      · 标点（语料里 须防'仇神动则助纣为虐' 的引号 → 连续汉字不断）
      · 占位符（模板存 `{pos}{rel}虽是阻力…`，渲染成「三爻兄弟虽是阻力…」，
        语料侧的 "虽是阻力…" 是渲染串的真子串，直接命中）

    注意别在抽汉字前先剥离 `{...}`：正则 `[^{}]*` 会跨行吞掉区间内容，
    把 JSON 语料整段吃掉（实踩：择吉 verdicts.json 被吞到只剩 527 汉字）。
    """
    return "".join(CN.findall(s))


def _corpus(disc: str) -> str:
    """本科 data/** + references/** + 内核术语池。

    内核必须算进语料池：十神名（偏印/正官…）等术语的真值源在
    `core/yishu_core/relations.py`，本就该由内核产出，不算"本科漏外置"。
    """
    parts = []
    for p in (ROOT / "core").rglob("*.py"):
        try:
            parts.append(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            pass
    base = ROOT / "disciplines" / disc
    for p in base.rglob("*"):
        if p.suffix not in (".json", ".md", ".txt") or not p.is_file():
            continue
        # 案例库不算措辞真值源：按铁律二它只服务测试与事后校验，里面的
        # 文本是**旧版引擎 / 古籍书录**的产出，拿它充语料会让审计失真
        # （本仓就出现过"报告句只在 cases 里出现过"而被判成已外置）。
        #
        # guard/ 与 scratch/ 同理，且更危险：它们是**报告产物的快照**
        # （guard/base.json 里存的是人工确认过的 human_markdown 全文）。
        # 把它们当语料 = "报告里写出过的句子就算外置"，审计直接变成橡皮图章。
        # 六爻一份 guard 就有 63 万汉字，五份口径叠起来吃掉语料池 67%，
        # 分辨力被稀释到近乎为零（实测剔除后才会暴露真漏外置）。
        if p.name == "case_library.md" or {"cases", "guard", "scratch"} & set(p.parts):
            continue
        try:
            parts.append(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            pass
    return "\n".join(parts)


def audit_case(case: dict, outdir: Path) -> tuple[list[str], dict]:
    """跑一条真实报告，返回（疑似未外置句, 明细统计）。

    统计供 --verbose 打印：读了多少句、多少被白名单/长度过滤掉、语料有多少汉字。
    没有它会看不出"0 句失败"是因为真干净还是因为压根没检出。
    """
    disc = case["discipline"]
    out = subprocess.run(_argv(case, outdir), capture_output=True, text=True,
                         encoding="utf-8", errors="replace",
                         env=utf8_subprocess_env(), cwd=ROOT)
    mds = sorted(outdir.glob(f"{disc}-*.md"))
    if not mds:
        return ([f"{disc}: 报告未生成（report.py 退出码 {out.returncode}）"],
                {"sent": 0, "skip": 0, "corpus": 0})
    stats = {"sent": 0, "skip": 0, "corpus": len(_hanzi(_corpus(disc)))}
    # 语料池同样抽成纯汉字串：data/*.json 里的断语常带引号/全角标点
    # （如 narrative_templates.json 的 须防'仇神动则助纣为虐'），
    # 若拿原始文本做包含判断，引号会把连续汉字切断 → 已外置的断语被误报。
    blob = _hanzi(_corpus(disc))
    focuses = _focuses(mds[-1].read_text(encoding="utf-8"))
    found: list[str] = []
    for line in mds[-1].read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("|"):
            continue
        line = re.sub(r"^\s*(?:[-*]\s*|\d+\.\s*)?", "", line)
        if ALLOW_PAT.search(line):
            continue
        # 按标点切成最小可外置单元：整句常带前缀（「就开市择日而言：…」），
        # 整句比对会让"其实已外置"的断语被误报成漏外置。
        for clause in re.split(r"[，。；：、！？「」——…]", line):
            h = _hanzi(_strip_yao_prefix(_strip_locator_prefix(clause)))
            stats["sent"] += 1
            if len(h) < MIN_HANZI:
                stats["skip"] += 1
                continue
            if h in blob or _strip_focus(h, focuses) in blob:
                continue
            c = clause.strip()
            if is_verdict(c):
                found.append(c)
    return found, stats


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="断语外置取证（跑真实报告反查）")
    ap.add_argument("--strict", action="store_true", help="白名单外未外置句即失败")
    ap.add_argument("--verbose", action="store_true",
                    help="列每科检出句数与语料命中数（证明 0 失败是真的干净）")
    ap.add_argument("--save", action="store_true",
                    help="把跑出的报告留在 tools/scratch/verdict_audit/ 供人工复核；"
                         "默认落临时目录，跑完即删，不留垃圾")
    args = ap.parse_args()

    # 默认临时目录：这道题要的是"读到的措辞"，报告本身是中间产物。
    # 早先在 scratch 里落盘，等于每跑一次门就攒 80 个钩子文件，与"清掉 scratch"冲突。
    if args.save:
        outdir = ROOT / "tools" / "scratch" / "verdict_audit"
        outdir.mkdir(parents=True, exist_ok=True)
    else:
        import tempfile
        outdir = Path(tempfile.mkdtemp(prefix="yi-verdict-"))
    hard = []
    total_miss = 0
    for case in CASES:
        miss, stats = audit_case(case, outdir)
        total_miss += len(miss)
        print(f"\n### {case['discipline']}｜{case.get('question') or case.get('activity') or ''}"
              f"｜未外置 {len(miss)} 句")
        if args.verbose:
            print(f"  [明细] 检出 {stats['sent']} 句，短于{MIN_HANZI}字未计 "
                  f"{stats['skip']} 句，本科语料 {stats['corpus']} 汉字")
        for s in miss:
            print("  ·", s[:90])
            hard.append(f"{case['discipline']}: {s[:60]}")
    print(f"\n合计疑似未外置断语 {total_miss} 句（口径提示/标题/结构标签已按白名单排除）")
    if args.save:
        print(f"报告留档于 {outdir}")
    elif args.verbose:
        print("（报告已落临时目录并清理；要留档加 --save）")
    return 1 if (args.strict and hard) else 0


if __name__ == "__main__":
    raise SystemExit(main())
