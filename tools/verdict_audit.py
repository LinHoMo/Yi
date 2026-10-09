# -*- coding: utf-8 -*-
"""断语外置**取证**门：跑真实报告，反查哪些中文句子没进 `data/*.json`。

  python tools/verdict_audit.py                 # 只报告（始终退出 0，人审用）
  python tools/verdict_audit.py --strict        # 白名单外的未外置句一律判失败
  python tools/verdict_audit.py --verbose       # 逐句列全部中文结论句
  python tools/verdict_audit.py --selftest      # 检出集负例自证（表格断语、四字短句断语）

为什么是"取证"而不是静态正则（AGENTS.md §三 的落地方式）：
  旧的 `check_verdict_literals` 是**文本启发式**——数 .py 里的中文字面量条数。
  两个方向都不可靠：① 假阴性：硬编码在 .py 里的断语只要不是"≥3 条连续字典值"
  就抓不到（本次审计就逮到小六壬 `事势偏顺，宫义为吉` 一整句漏外置）；
  ② 假阳性：把 docstring / 模块说明 / argparse help 当成断语批量外置，
  只会让代码读不懂。本脚本不猜代码长什么样，而是**看终端用户到底读到了什么**。

判据：报告正文里每句 ≥`MIN_HANZI` 个汉字的中文结论句，若不在本科 `data/**` 与
`references/**` 语料池里，即为"疑似未外置断语"。**表格单元格同样在审计范围内**
（旧实现按 `line.startswith("|")` 整行豁免，报告里写进表格的断语从未被审）。

用例集见本模块 `CASES`（条数**不写死在任何说明文字里**——两科收缩后手写的"10 条"
已是假事实；运行输出与 `tools/check.py` 的 [1c] 标签都从 `len(CASES)` 现算）。
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

MIN_HANZI = 4
# 判定阈值：4 个汉字（2026-10-09 由 8 降下）。理由（负例见 --selftest）：
# 报告里的断语常以**四字短句串**出现——「官鬼持世，事恐反复，财星入墓，求之不得」
# 被标点切成 4 个 4 字小句，旧阈值 8 让整串**一句都不进检出集**（实测每例 157 句里
# 123 句以"短于 8 字"被跳过）。降阈值后真误报由 NON_VERDICT/ALLOW_PAT 白名单按
# 逐条理由挡，而不是靠把阈值抬回去掩盲区。
# 整行累计闸门：小句 ≥MIN_HANZI **且**所在行累计 ≥MIN_HANZI_LINE。这样四字短句串
# 必被检出（行累计 16 字），而单独一行只有 4 个字的孤立标签仍按结构行放过——
# 否则把"盲区"换成"噪声"，审计一样失去分辨力。
MIN_HANZI_LINE = 8
# 中文结论句的**字面定义**：这一句主要得是中文。表格单元格里混排的机械片段
# （`2026-10-02(用神卯冲空(酉))`、`1990庚午(正官)`，以及把 Python dict repr
# 直接印进报告的 `{'branch': '子', …}`——后者本身是该修的缺陷，但它不是"断语"）
# 汉字占比都在 1/2 以下。旧阈值 8 顺手把它们挡在门外，降阈值后必须显式判比例。
MIN_HANZI_RATIO = 0.5
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
    r"|查表直录|机械标签|无吉凶断语|不写命运断语|非吉凶断语"
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


# ── 机械事实/模板壳的**形状**豁免（2026-10-09 随 MIN_HANZI 降到 4 一并补）──────
#
# 阈值 8 时这些片段压根不进检出集；降到 4 之后它们成批出现，且**都不是措辞**——
# 是"内核/数据里的一个值被拼进模板"后剩下的短串。与 NON_VERDICT 的区别：
# NON_VERDICT 认的是"这句话属口径/出处标注"，这里认的是"这一小串是个机械值槽位"。
# 一律 **锚定整句**（^…$）且不允许携带吉凶词，避免顺手豁免真判语（如 `青龙临用`
# 不在其中——它以「爻」结尾的形态是「六神临位」事实，而 `青龙临用，事恐反复`
# 的后半句照样进检出集）。干支/十神一律由内核派生（AGENTS.md §二 唯一真值源）。
from yishu_core.symbols import EARTHLY_BRANCHES as _EB  # noqa: E402
from yishu_core.symbols import HEAVENLY_STEMS as _HS  # noqa: E402
from yishu_core.relations import SHISHEN_TO_LIUQIN as _SHISHEN  # noqa: E402

_STEMS = "".join(_HS)
_BRANCHES = "".join(_EB)
_STEM_CLS = f"[{_STEMS}]"                  # 单个天干
_BRANCH_CLS = f"[{_BRANCHES}]"             # 单个地支
_GANZHI_CLS = f"[{_STEMS}{_BRANCHES}]"     # 单个干支字
_SHISHEN_CLS = "(?:" + "|".join(_SHISHEN) + ")"
_MECH_LOC = f"(?:初|[一二三四五六上])?爻"

MECHANICAL_FACT = re.compile(
    r"^就[一-龥]{2,8}来说$"                                   # ① wrap 模板壳：就{focus}来说
    rf"|^落在{_GANZHI_CLS}?[一二三四五六上]?爻$"              # ② chart 层定位槽 (落在{支}{爻})
    rf"|^[一-龥]{{2,5}}临[用]?{_MECH_LOC}$"                   # ③ 星煞/六神临位事实（无吉凶词）
    rf"|^[一-龥]{{2,4}}@{_GANZHI_CLS}$"                       # ④ 神煞落支标记 {name}@{支}
    rf"|^{_GANZHI_CLS}{{2}}\({_SHISHEN_CLS}\)$"               # ⑤ 流年表单元格 干支(十神)
    rf"|^{_GANZHI_CLS}{{2}}({_SHISHEN_CLS})$"                 # ⑥ 同上（无括注形态）
    rf"|^{_BRANCH_CLS}日(?:应事|当值)$"                        # ⑦ 应期槽 {支}日应事/当值
    rf"|^逢{_BRANCH_CLS}(?:冲|合){_BRANCH_CLS}?皆动$"          # ⑧ 应期槽 逢{支}冲/合皆动
    rf"|^{_BRANCH_CLS}日\s*这几日$"                            # ⑨ 应期提示尾槽
    rf"|^[年月日时]{{1,2}}干{_GANZHI_CLS}{{2}}[合冲刑害破]$"    # ⑩ 干支关系事实（core 算出）
    r"|^\*{0,2}(?:机械对照|机械关系|通行起法|从重者论)\*{0,2}$"
    # ⑪ 方法/边界标签（render 层的口径小票，内容由 core 的判据决定，不是叙述措辞）
    r"|^不是命运断言$"
    # ⑫ 铁律三口径句被 `，` 切出来的尾段（整行已在 NON_VERDICT ④，这里补切片形态）
)


def is_mechanical(clause: str) -> bool:
    return bool(MECHANICAL_FACT.match(re.sub(r"^\**|\**$", "", clause.strip())))


# 结构行与免责声明：不是断语，不该进 data（前者是排版，后者跨科统一由 report/py 层给）
ALLOW_PAT = re.compile(
    r"^#{1,6}\s"                                   # Markdown 标题
    r"|（(?:出厂|口径|免责|框架|非|只|不)[^）]*）"   # 括注性说明
    r"|(?:口径|免责)?提示[：:]?(?:此占|本|报告)?(?:为)?象数参考|不作现实承诺|以专业意见为准"
    r"|^[一-龥]{1,6}[、:：]?$"                      # 纯结构短标签
    # wrap 模板壳（`就{focus}来说，{text}`）的引导段本身：语料池抽汉字后只剩
    # 「就来说」，渲染值插在中间，子串必不比中——它是排版壳不是措辞。
    # （旧阈值 8 时它天然不出现在检出集；降到 4 后必须显式认下这层壳）
    r"|^就[一-龥]{2,8}来说$"
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


def _clauses_of_line(line: str) -> list[str]:
    """一行（含 Markdown 表格行）→ 待审小句。

    2026-10-09 修复的盲区：旧实现 `if not line or line.startswith("|"): continue`
    让**整行表格不审计**——报告里 `| 宜 | 青龙临用，兄弟持世，事恐反复 |` 这类
    措辞写进表格就永久逃逸（断语进表格是 render 层的常见形态）。现按 `|` 拆格，
    逐格走与正文完全相同的剥离/切句口径，不给表格任何特殊待遇。
    """
    cells = line.split("|") if line.lstrip().startswith("|") else [line]
    out: list[str] = []
    for cell in cells:
        s = cell.strip()
        if not s:
            continue
        s = re.sub(r"^\s*(?:[-*]\s*|\d+\.\s*)?", "", s)
        if ALLOW_PAT.search(s):
            continue
        # 按标点切成最小可外置单元：整句常带前缀（「就开市择日而言：…」），
        # 整句比对会让"其实已外置"的断语被误报成漏外置。
        # 切分符现含 ASCII/弯引号：语料池抽汉字后本就不带引号，留着它只会让
        # `'绝处逢生'之险` 这类"引用词+尾巴"既不比中、又被当成新断语。
        # **不含括号**——NON_VERDICT ① 靠"行首是 （《"认书源标注行，把括号也当
        # 切分符会让 `（《滴天髓》…）` 的行首消失、整批出处标注被误报
        # （实测：加括号切分后三例合计从 13 句涨到 80 句，涨的都是假阳）。
        out.extend(re.split(r"[，。；：、！？「」——…\"'“”‘’]", s))
    return out


#: 单字系词/结构词白名单——**不是数据值的副本**（那是 §二 禁区），只放行汉语里
#: 承担句法而非内容的字。用于 `_corpus_covered()` 的"逐段覆盖"判定。
GLUE = set("属为是的在与及则即乃于有主见无又而之其此该")


def _corpus_covered(h: str, blob: str, min_seg: int = 2) -> bool:
    """整句是否可被「语料片段 + 单字系词」逐段覆盖（模板拼槽位的情形）。

    为什么需要它：narrate 用 f-string 把数据槽位拼成句子，如
    `f"{pattern}属{side}"` → 「伤官格属逆用」。三段里 `伤官格`、`逆用` 各自都在语料池，
    `属` 是系词，但整串 6 字不是 blob 的连续子串——按整句比对就是假阳性。
    这里做通用判定，不再手贴 `^…格属(顺用|逆用)$` 这类把数据取值抄进门里的正则。

    有牙齿的边界：段长 ≥2 必须逐字来自语料，单字只允许 GLUE 里的虚词；
    任何一处内容字无法覆盖即判 False（所以编造的断语照样漏不过去——见 --selftest 负例）。
    """
    if not h:
        return False
    i = 0
    n = len(h)
    while i < n:
        best = 0
        for ln in range(min(n - i, 24), min_seg - 1, -1):
            if h[i:i + ln] in blob:
                best = ln
                break
        if best:
            i += best
            continue
        if h[i] in GLUE:
            i += 1
            continue
        return False
    return True


def find_unexternalized(md_text: str, blob: str, focuses: set[str], *,
                        min_hanzi: int = MIN_HANZI,
                        min_hanzi_line: int = MIN_HANZI_LINE,
                        min_hanzi_ratio: float = MIN_HANZI_RATIO) -> tuple[list[str], dict]:
    """报告正文 →（疑似未外置句, 检出统计）。纯函数，`--selftest` 与真实报告共用。"""
    stats = {"sent": 0, "skip": 0, "covered": 0}
    found: list[str] = []
    for line in md_text.splitlines():
        line = line.strip()
        if not line:
            continue
        clauses = _clauses_of_line(line)
        if not clauses:
            continue
        line_hanzi = len(_hanzi("".join(clauses)))
        for clause in clauses:
            h = _hanzi(_strip_yao_prefix(_strip_locator_prefix(clause)))
            stats["sent"] += 1
            body = re.sub(r"\s", "", clause)
            if (len(h) < min_hanzi or line_hanzi < min_hanzi_line
                    or (body and len(h) / len(body) < min_hanzi_ratio)):
                stats["skip"] += 1
                continue
            if h in blob or _strip_focus(h, focuses) in blob:
                continue
            if _corpus_covered(h, blob):
                stats["covered"] += 1        # 槽位拼句：各段都在语料，不算未外置
                continue
            c = clause.strip()
            if is_mechanical(c) or not is_verdict(c):
                continue
            found.append(c)
    return found, stats


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
    md_text = mds[-1].read_text(encoding="utf-8")
    stats = {"sent": 0, "skip": 0, "corpus": len(_hanzi(_corpus(disc)))}
    # 语料池同样抽成纯汉字串：data/*.json 里的断语常带引号/全角标点
    # （如 narrative_templates.json 的 须防'仇神动则助纣为虐'），
    # 若拿原始文本做包含判断，引号会把连续汉字切断 → 已外置的断语被误报。
    blob = _hanzi(_corpus(disc))
    found, sub = find_unexternalized(md_text, blob, _focuses(md_text))
    stats.update(sub)
    return found, stats


# ── 检出集负例自证（AGENTS.md §四.8）───────────────────────────────────────
#
# 跑真实报告要起 3 个子进程（分钟级），[2b] 每次跑全部门不可能等它；本自证只测
# **检出集本身有没有牙**：把两条已实测的逃逸形态写进合成正文，语料池留空，
# 必须被抓。正例侧同时证明"关掉盲区没有把白名单一起拆掉"。
SELFTEST_NEG: tuple[tuple[str, str, int, str], ...] = (
    ("表格单元格里的断语必须被抓",
     "| 宜 | 青龙临用，兄弟持世，事恐反复 |\n", 3,
     '旧实现 `line.startswith("|")` 整行豁免：写进表格的断语从未被审'),
    ("四字短句串断语必须被抓",
     "官鬼持世，事恐反复，财星入墓，求之不得\n", 4,
     "旧实现 MIN_HANZI=8 + 按标点切碎：整串一句都不进检出集"),
    ("表格里的短句串（行累计够、单格短）必须被抓",
     "| 判断 | 事恐反复，财星入墓 |\n", 2,
     "单元格切分后每格仅 4 字，行累计 8 字——两个盲区叠加的形态"),
)

SELFTEST_POS: tuple[tuple[str, str, int, str], ...] = (
    ("已进语料池的句子不得误报",
     "官鬼持世，事恐反复\n", 0, "blob 里已有该串（真外置），检出必须为空"),
    ("口径/免责行不得进检出集",
     "本报告不作现实承诺，医疗、法律、投资请以专业意见为准。\n", 0,
     "铁律三要求写在输出里，进 data 反而是倒退"),
    ("机械值槽位不得进检出集",
     "| 流年 | 戊寅(正财) | 己卯(偏财) |\n", 0,
     "干支(十神)是 core 派生事实；MECHANICAL_FACT ⑤ 按形状豁免"),
    ("孤立短标签（行累计不足）维持旧口径",
     "财星入墓\n", 0,
     "单行 4 字：靠行累计闸门放过——明写在此，免得日后把它当成「已覆盖」"),
)


def _selftest_blob() -> str:
    """正例用的假语料池：含着「官鬼持世/事恐反复」整串，以及槽位片段与「青龙临用」。"""
    return _hanzi("断语库：官鬼持世；事恐反复。格局名：伤官格；用法分类：逆用。"
                  "象曰：青龙临用。")


# 逐段覆盖（_corpus_covered）专用：blob 里**有**这一段、但整句里夹着没出处的造词。
# 用空语料池测不出来（那时无段可覆盖），必须给一个部分命中的 blob 才验得出"放宽没放宽过头"。
SELFTEST_PARTIAL: tuple[tuple[str, str, int, str], ...] = (
    ("槽位拼句不得误报（伤官格+属+逆用）",
     "伤官格属逆用\n", 0,
     "narrate 的 f-string 形态：各段都在语料，整串 6 字不是连续子串——旧判据在此假阳性"),
    ("部分覆盖不得豁免夹带的新断语",
     "青龙临用，主必大贵\n", 1,
     "blob 有「青龙临用」而无「主必大贵」：有据段放过、造词句必须被抓"),
)


def run_selftest() -> int:
    bad: list[str] = []
    # 负例用**空语料池**（"这条措辞压根没外置"是唯一前提，抓到才算有牙）；
    # 正例用含该串的假语料池（证明"已外置"仍不比中＝误报，白名单也没被拆掉）。
    empty_blob = ""
    pos_blob = _selftest_blob()
    focuses: set[str] = set()
    for name, md, min_hit, why in SELFTEST_NEG:
        found, stats = find_unexternalized(md, empty_blob, focuses)
        if len(found) < min_hit:
            bad.append(f"负例「{name}」只抓到 {len(found)} 句（应 ≥{min_hit}）"
                       f"→ {found}｜检出 {stats['sent']} 句｜{why}")
    for name, md, expect, why in SELFTEST_POS:
        found, _ = find_unexternalized(md, pos_blob, focuses)
        if len(found) != expect:
            bad.append(f"正例「{name}」检出 {len(found)} 句（应 {expect}）→ {found}｜{why}")
    for name, md, expect, why in SELFTEST_PARTIAL:
        found, _ = find_unexternalized(md, pos_blob, focuses)
        if len(found) != expect:
            bad.append(f"覆盖判例「{name}」检出 {len(found)} 句（应 {expect}）→ {found}｜{why}")
    print(f"断语外置取证门自证：负例 {len(SELFTEST_NEG)} 条、正例 {len(SELFTEST_POS)} 条、"
          f"逐段覆盖判例 {len(SELFTEST_PARTIAL)} 条")
    for name, *_ in SELFTEST_NEG:
        print(f"  · 负例 {name}")
    if bad:
        print("× 自证失败：")
        for b in bad:
            print("  -", b)
        return 1
    print(f"逐段覆盖判例 {len(SELFTEST_PARTIAL)} 条（槽位拼句不误报、夹带造词仍须被抓）")
    print(f"SELFTEST PASS（正例 {len(SELFTEST_POS)} 例 + 负例 {len(SELFTEST_NEG)} 例）")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="断语外置取证（跑真实报告反查）")
    ap.add_argument("--strict", action="store_true", help="白名单外未外置句即失败")
    ap.add_argument("--verbose", action="store_true",
                    help="列每科检出句数与语料命中数（证明 0 失败是真的干净）")
    ap.add_argument("--save", action="store_true",
                    help="把跑出的报告留在 tools/scratch/verdict_audit/ 供人工复核；"
                         "默认落临时目录，跑完即删，不留垃圾")
    ap.add_argument("--selftest", action="store_true",
                    help="检出集负例自证（表格断语、四字短句串都必须被抓；不跑引擎）")
    args = ap.parse_args()

    if args.selftest:
        return run_selftest()

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
    print(f"断语外置取证：跑 {len(CASES)} 份真实报告"
          f"（小句阈值 ≥{MIN_HANZI} 字、行累计 ≥{MIN_HANZI_LINE} 字、汉字占比 ≥{MIN_HANZI_RATIO}）")
    for case in CASES:
        miss, stats = audit_case(case, outdir)
        total_miss += len(miss)
        print(f"\n### {case['discipline']}｜{case.get('question') or case.get('activity') or ''}"
              f"｜未外置 {len(miss)} 句")
        if args.verbose:
            print(f"  [明细] 检出 {stats['sent']} 句，未达阈值/白名单未计 "
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
