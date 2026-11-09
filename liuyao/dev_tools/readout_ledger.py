# -*- coding: utf-8 -*-
"""读数对账台（第两百批·防御性维护）——登记值 vs 当前 HEAD 重放值，逐位核对。

176→199 批把二十余个关键读数写散在 CHANGELOG/README/CAPABILITY 里。凡散落的数字，
终有一天和产生它的代码分家（§六.3 的时延版）。本器把**每个对外声称的读数**做成可重放
断言：expected 逐字来自登记文本（注明批次），actual 由当前 HEAD 现场重跑取回。

    python dev_tools/readout_ledger.py --quick   # 快组（纯文本/装配/小扫描，秒级~2min）
    python dev_tools/readout_ledger.py           # 全量（含两科评测与外部集，十分钟级）
    python dev_tools/readout_ledger.py --selftest

对账失败＝读数已与代码分家：要么改代码前偷动了读数（缺陷），要么登记文本过期（§六.2）——
两种都必须立案，不许静默刷新基线。
"""
from __future__ import annotations
# 批量注入：eval/ 上 path（替换 scripts/ 兼容 shim）
import sys as _sys
from pathlib import Path as _P
_ed = 'C:\\Users\\31103\\Desktop\\Yi\\liuyao\\eval'
if _ed not in _sys.path:
    _sys.path.insert(0, _ed)

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
ROOT = DISC.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402


def sh(args, cwd=None):
    r = subprocess.run([sys.executable, "-X", "utf8"] + args,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(cwd or DISC))
    return (r.stdout or "") + (r.stderr or "")


def grab(text, pat, group=1):
    m = re.search(pat, text)
    return m.group(group) if m else None


# ── 读数账目：id -> (登记出处, 取数函数, 比对) ──────────────────────────────
def checks():
    out = []

    def add(cid, src, fn, expect):
        out.append((cid, src, fn, expect))

    # --- 六爻内部集 ---
    def c_tune(t):
        s = sh(["eval/evaluate.py", "--split", "tune"])
        return (grab(s, r"平均分 = ([0-9.]+)%.*n=20"),
                grab(s, r"strict top-1 命中 ([0-9.]+)%"),
                grab(s, r"平均排在第 ([0-9.]+) 位"))
    add("liuyao.tune(97.9/64.7/1.53)", "README 表/172批", c_tune,
        ("97.9", "64.7", "1.53"))

    def c_holdout(t):
        s = sh(["eval/evaluate.py", "--split", "holdout"])
        return (grab(s, r"平均分 = ([0-9.]+)%"),
                grab(s, r"strict top-1 命中 ([0-9.]+)%"),
                grab(s, r"平均排在第 ([0-9.]+) 位"))
    add("liuyao.holdout(90.2/50.0/1.6)", "README 表", c_holdout,
        ("90.2", "50.0", "1.6"))

    # --- 外部集 ---
    def c_wiki(t):
        s = sh(["eval/evaluate.py", "--split", "wikisource_holdout"])
        return (grab(s, r"平均分 = ([0-9.]+)%"), grab(s, r"strict top-1 命中 ([0-9.]+)%"),
                grab(s, r"平均排在第 ([0-9.]+) 位"))
    # 339 批曾按 69.8/29.5/2.16 登记，理由是「315 封存后口径变了」——344 批查实该归因错误：
    # 315 只把 50 例切 dev/test，n 与标签都没变；真正原因是 1592923（易隐批）重生成
    # wikisource_cases.json 时清空了 292/297/298 批的 74 use_god／52 branch／32 note。
    # 344 批按 1592923^ 恢复字段后，同 HEAD 引擎逐位回到 308 读数（75.8/31.8/2.03）。
    add("liuyao.wikisource(75.8/31.8/2.03)", "181批→308批；344批恢复被 1592923 清空的标签后实跑改回", c_wiki,
        ("75.8", "31.8", "2.03"))

    def c_dz(t):
        s = sh(["eval/evaluate.py", "--split", "zengshan_dz_holdout"])
        return (grab(s, r"平均分 = ([0-9.]+)%"), grab(s, r"strict top-1 命中 ([0-9.]+)%"))
    add("liuyao.zengshan_dz(86.5/48.3)",
        "README 表→308批→402批改期望（dz 扩样 21→29；priority-anchor＋CASE_RE 之/单字题）；"
        "415 批多支基准口径修正（yingqi_branches 全纳入，原 60.3/37.9；新旧不可比）；"
        "419 批恢复 403 批清空的 18 例用神书证（use_god/branch/note）并补支式抽取，61.5→61.8（新旧不可比）；"
        "498 批修 ZD214 expected 错配（建器把相邻坎之井验语酉戌安到离之旅头上，实应卯辰），61.8→64.3/41.4→44.8（新旧不可比）；"
        "501 批回原文补全 8 例空用神(类别+支)与 8 例空 verdict，N/A 清零（category 15/21→22/29、branch 16/21→24/29；verdict 11/18→14/26 因暴露 5 例引擎判反暂降），64.3→64.5（新旧不可比）；"
        "502 批逐例建卦理判别（非拧权重）：①六亲持世原恒 0 分只展示，按世爻六亲×情境计分（官鬼持世占功名+1.0/父母占考+1.0/子孙占官-0.8/兄弟占财-0.8）；②原神同类成局触发「贪合忘生-2.0」，新增判别——用神临月令旺（god_month_score>=4，如ZD196官鬼木在寅月=5）则改判「原神得局生用+1.5」，用神月处死地（如reg_19妻财午火在亥月=1）保持-2.0。ZD196大凶→平吉命中。verdict strict 14/26→15/26(53.8→57.7)，strict avg 64.5→66.0（新旧不可比），regression 19/19+思维链12/12全绿；"
        "503 批：verdict cap 系统原把「世爻动化官鬼（变鬼）」与「世爻动化回头克」混为一谈——只认变爻六亲==官鬼，而回头克是「变爻五行克世爻五行」，变爻六亲按卦宫定（如ZD197世爻官鬼午火独发、变亥水在乾宫为子孙而非官鬼），于是源L3625「化回头克皆非吉地（旺世也压）」这一型整体漏压。新增独立分支：世爻独发动化回头克（ct==回头克，不论变爻六亲）即压凶cap，解救只认子孙动（日辰扶世不救回头克——ZD197原文「临日本旺仍不宜回头克，卒于亥月」）。ZD197吉→凶命中。verdict strict 15/26→16/26(57.7→61.5)、legacy 18/29→19/29，strict avg 66.0→67.6（新旧不可比），regression 19/19+思维链12/12全绿；"
        "504 批：对偶型漏压——世爻独发动化回头生本吉，但若变爻(原神)被月建冲破(月破)则生世无源。ZD222占寿：世爻子孙子水动化申金回头生，然申金在寅月被寅冲破(月破)，原文「世化申金回头生，不宜寅月冲破，卒卯年」。新增分支：世爻动化回头生且变爻与月建相冲即压凶cap；门控实测排除『行人』(wikisource占行人世爻未土化巳火回头生、巳火亥月破被误压→占行人看归期不看生死)与『功名科举』(占功名回头生本吉)，只压疾病·寿类死兆(qcls=其他/疾病)。ZD222平吉→凶命中。verdict strict 16/26→17/26(61.5→65.4)、legacy 19/29→20/29，strict avg 67.6→69.4（新旧不可比），regression 19/19+思维链12/12全绿，wikisource 75.8无漂移、golden无漂移；"
        "505 批：修ZD029占子痘用神取错——question='子痘症'不含『病』字(漏触发自占病轨)、不含『子病』、『痘』不在任何用神关键词，最终兜底取世爻丑土；实应取五爻子孙巳火(书证dz L831「巳火子孙既当春令」)。在step2 _decide_use_god的『占子病→子孙』层纳入『痘』(痘疹=儿科传染病，占痘即占孩子病；全库仅此一例含痘，无地支/卦名歧义)。ZD029用神世爻→子孙巳火、verdict平吉→凶双中，应期定位同步转对。verdict strict 17/26→18/26(65.4→69.2)、top-1 44.8→48.3、strict avg 69.4→72.8（新旧不可比），regression 19/19+思维链12/12全绿，wikisource 75.8/bushi 68.1/golden 8f60·8168全无漂移；"
        "506 批：修ZD016占弟被讼判反——用神兄弟酉金五爻独动化申金(退神)，引擎旧只把『化退神』当格局结构、未转verdict凶，又因忌神午火被未土合绊(午未合)判吉2.42；书判「酉金兄爻化退神…退至申年而无路」大凶(L948用神动化退神皆为化凶)。新增3c分支：用神动化退神即压凶cap。门控实测排除『行人』(ZD050占行人兄动化退=已有归志=吉，同象异断)与『子孙』(golden占妻胎安否用神子孙化退被误压)。ZD016吉→凶命中。verdict strict 18/26→19/26(69.2→73.1)、strict avg 72.8→74.4（新旧不可比），regression 19/19+思维链12/12全绿，wikisource 75.8/bushi 68.1/golden 8f60·8168全无漂移；"
        "**511 批复查：上述 61.8→64.5→66.0→67.6→69.4→72.8→74.4 的整条阶梯无法在对应提交上复现**。"
        "在 308f009^（501 批父）实跑 64.3%（use_god N/A=8、verdict 11/18），在 308f009（501）及其后"
        " 961528c／8b37efb／41986c7／43dfde6／356115f／9f497de 各点实跑恒为 87.4%（use_god N/A=0、verdict 26/26）——"
        "**501 批把 8 例 expected 按原文补全后 N/A 清零，strict 从 64.3 直跳 87.4（+23.1），登记只记 64.3→64.5**。"
        "故旧登记值不是「跑出来的」，是未重跑的估计；本项按可复现实值 87.4 重挂，并声明旧序列不可比。"
        "**512 批**：verdict 26/26 已逐例回底本取证（26 条非空 verdict 均有书载结果句，对照全表在 CHANGELOG 512 §一），"
        "并查明 26/26 的成因是**开发集被逐例修到全对**（10 例按书断调优），只能按「外部·开发集」讲；"
        "**513 批**：建器分块越界抓到 ZD102 的 expected 取自下一案（小过之丰「应在初九辰日即雨」），"
        "按本卦临之蒙实文改回亥日——该案原是对着污染值「白给」的一分，去掉后 strict 87.4→86.5、legacy 96.3→96.2"
        "（top-1 48.3 不变；**新旧不可比**，且此降为去污染所致，不是回归）",
        c_dz, ("86.5", "48.3"))

    def c_bushi(t):
        s = sh(["eval/evaluate.py", "--split", "bushi_zhengzong_holdout"])
        return (grab(s, r"平均分 = ([0-9.]+)%"), grab(s, r"strict top-1 命中 ([0-9.]+)%"))
    # 413 批：吉凶只取结果句强结果词（22/36 与引擎一致），strict 68.3→64.7（分母新增 verdict 维）。
    add("liuyao.bushi_zhengzong(65.3/23.7)",
        "408批首建→409通用确认句→410相对期→412用神→413吉凶结果句"
        "→414多单位自答（BZ0462 卯年→卯日；读数不动属预期）"
        "→417用神「为用」简写（6 例 N/A→明示；64.7→65.3，新旧不可比）"
        "→**511 批复查：417 之后 502/503 登记的 66.5／68.1 在任何提交上均不可复现**——"
        "308f009^（501 父）、961528c、8b37efb、41986c7、43dfde6、356115f、9f497de 与 HEAD 八点实跑恒为 65.3%／23.7%（n=38）。"
        "502/503 的版子改的是 verdict cap（对 zengshan 生效），对 bushi 无连带；旧 +1.2／+1.6 两跳系未重跑的估计。"
        "本项按实值 65.3 回归登记，声明 66.5／68.1 不可复核",
        c_bushi, ("65.3", "23.7"))

    def c_yiin(t):
        s = sh(["eval/evaluate.py", "--split", "yiin_holdout"])
        return (grab(s, r"平均分 = ([0-9.]+)%"),
                grab(s, r"strict top-1 命中 ([0-9.]+)%"),
                grab(s, r"平均排在第 ([0-9.]+) 位"),
                grab(s, r"应期信息量体检（n=([0-9]+)"))
    add("liuyao.yiin(44.6/18.2/2.43, n=11)",
        "326批首建→423批补「果在日期后」式：YI029/031/034/044 由 claim 改实录，"
        "应期分母 7→11；43.9/28.6/2.25→44.6/18.2/2.43（新旧不可比）",
        c_yiin, ("44.6", "18.2", "2.43", "11"))

    def c_window2(t):
        s = sh(["dev_tools/window_report.py"])
        blk = s.split("═ zengshan_dz_holdout")[0]
        # 实际格式是编号行「  1   12/44 =  27.3%」（200 批立案教训：模式抄实样非凭印象）
        t1 = re.search(r"^\s+1\s+(\d+)/(\d+) =\s*([\d.]+)%", blk, re.M)
        t3 = re.search(r"^\s+3\s+(\d+)/(\d+) =\s*([\d.]+)%", blk, re.M)
        return ((t1.group(3), t3.group(3)) if t1 and t3 else (None, None))
    add("liuyao.wiki top1/top3(31.8/61.4)", "181/199批→308批；344批恢复标签后实跑改回",
        c_window2, ("31.8", "61.4"))

    def c_baselines(t):
        s = sh(["dev_tools/baselines.py"])
        yong = re.search(r"用神值支\s+(\d+)/\s*\d+ =\s*([\d.]+)%", s)
        day = re.search(r"日辰即答\s+(\d+)/\s*\d+ =\s*([\d.]+)%", s)
        return ((yong.group(2), day.group(2)) if yong and day else (None, None))
    # 344 批：18.2 是 183 批旧值；引擎「用神值支」基线随用神取支改进升到 25.0
    #（1592923 的 WS003 题面截短会把它打到 22.7，恢复题面后回到 25.0）。
    # 这是未登记的**基线变强**，不是引擎回归；README 的「31.8 > 18.2」须同批改为 25.0。
    add("liuyao.baselines 用神25.0/日辰4.5", "183批→344批改期望（用神取支改进，非评分口径变化）",
        c_baselines, ("25.0", "4.5"))

    # --- 版本对拍/毕业/分诊（JSON 直读 + 现场重生成核对） ---
    add("liuyao.collate(卦面0/47 判词1/37)", "185批", lambda t: _collate_now(), ("0/47", "1/37"))
    # 401 批改期望 18/63/161 → 43/39/160：400 批 parser 修正后重建毕业册（口径变更，
    # 新旧不可比：新增 restorable 含已在册/重复/非单点，不是 43 个新案）。
    add("liuyao.graduation(43/39/160)", "189批→401批改期望（400 parser 重建）", lambda t: _json_counts(
        "data/cases/verifications_graduation.json", "summary",
        ("restorable", "partial_needs_human", "unrestorable")), ("43", "39", "160"))
    # 401 批改期望 15/35/5/8 → 8/18/3/10：随毕业册重建，多数 partial 转 restorable；
    # B 路 3/10 是 371 批 parse_b 修好后首次重建（旧册 5/8 已登记为过期）。
    add("liuyao.triage(8/18/3/10)", "199批→401批改期望（随毕业册重建）", lambda t: _json_counts(
        "data/cases/verifications_triage.json", None,
        ("A_有验支候选", "A_无验支结案候选", "B_异写候选", "B_真分歧需人"), key="buckets"),
        ("8", "18", "3", "10"))
    # 401 批改期望 13/0 → 32/0：43 条 restorable 双器复核；11 条 needs_human 已逐条裁决
    # （decision 在册，按本册口径不计 needs_human）。
    add("liuyao.restorable_recheck(共识32/分歧0)", "201批→377批→401批改期望", lambda t: _json_counts(
        "data/cases/restorable_recheck.json", None, ("consensus", "needs_human")), ("32", "0"))
    # 411 批改期望：6 条「日期阻塞」逐条核原文后结案——4 条日期不可重建
    # （L1032/L1515/L3338 缺日干、L1741 缺月建）、2 条非单点（L2324/L3559）。
    # 498 批改期望：3 条「待回原文」回原文核毕归位——L1279 观之益串味确证但《易林補遺》
    # 无建器覆盖面（→新候选·建器阻塞 0→1）、L1006 兑之讼改判为命再占连占卦（→不升）、
    # L2093 坎之井验出 ZD214 建器串味（→不升，修 ZD214 系改外部集机读值另批）；
    # 同时清 6 行 next_batch=411 残留字段。reread 3→0、not_enrolled 3→5。
    add("liuyao.restorable_adjudication(43=30+3+5+0+1+0+4)", "401批→405批→411批→498批核毕待回原文3条",
        lambda t: _json_counts(
            "data/cases/restorable_adjudication.json", "summary",
            ("total", "already", "non_single", "not_enrolled", "reread",
             "new_builder_blocked", "new_date_blocked", "new_date_unrecoverable")),
        ("43", "30", "3", "5", "0", "1", "0", "4"))
    add("liuyao.draft_candidates(10含dup4)", "204批", lambda t: _draft_counts(), ("10", "4"))

    # --- 裁决表/治理图/指纹 ---
    # 304 批改期望 7=5+1+1 → 27=5+1+20：分歧表自 248 批起扩容（新增流派分歧点逐条入册），
    # 旧值属于「登记文本过期」而非读数回归；改值理由登记在 liuyao/docs/CHANGELOG.md 304 批。
    # 309 批改期望 5→6：原第四态 `settled` 已按三值词汇归位为 settled_by_source
    # （builder 文件头明文「状态只有三种，不许含糊」，原值属词汇漂移）。
    add("liuyao.adjudications(27=6+1+20)", "188批→304/309批改期望", lambda t: _adjud_counts(),
        ("27", "6", "1", "20"))
    # 309 批：漂移已裁定归零（settled → settled_by_source），期望值转为空串；
    # 本项继续当哨兵——再冒出词汇表外的状态名仍会判红。
    add("liuyao.adjud 状态词汇漂移(空)", "304批→309批改期望", lambda t: _adjud_unknown(), ("",))
    # 金标准基线已随结构演进前移（193 批应期窗口键、276 批报告措辞等）；
    # `golden.py verify` 当前输出「与基线指纹一致（机械+措辞均未漂移）」，
    # 说明**盘与金标准一致**，是账台登记值过期，不是回归（308 批定性）。
    add("liuyao.golden(96c7/8168)", "193批→308批改期望；320 批纳入 judgment 判定块；321–324 批判定器 v3–v6 内容变化再重基线（机械指纹变、措辞始终未变）；362 批象层上线：正文增【象上看】段与用神口径提示 → 措辞指纹 405b→7960（机械层未动，评分未改）；364 批用神合日月按动静分计（源L738）：机械指纹 6f70→3a19（288 例中 4 条读数变化、1 例 verdict 翻档），措辞指纹仍未动；468 批经典引文按 quote_kind 分标 → 措辞 7960→53e1f9ee326d43d0；469 批六亲持世括注改「（据《…》今译）」→ conclusion 断语文本变化，机械 3a19→e761fe9dcda5d108、措辞 53e1→7014d01b3a1fc1c7（tune 97.9／holdout 90.2 分数逐位未动，属口径措辞修正非行为漂移）；502 批六亲持世计分(原恒0)+原神得局生用判别(god_month_score>=4改+1.5)→ reason 与 narrate 断语文本漂移，机械 e761→cccd9920647a1138、措辞 7014→8168eff9e560d6c2（tune/holdout 分数未动，属有意评分精修后 capture）；503 批世爻独发动化回头克独立压凶cap（源L3625，解救只认子孙动）→ 3 例 verdict/concl_sha 翻档（同人占妻胎×2、复占行人×1），机械 cccd→8f60e077f66827a7、措辞 8168 未变（属有意 cap 精修后 capture）；**511 批按 digest#drift_log 回补 8f60→7f05→96c7**：504–506 区间 T29 救应规则（六冲变合婚姻占吉断）与 D 系列 direction caps 已 capture 并写入 drift_log，账台期望停在 503（属登记过期，非回归；`golden.py verify` 与盘逐位一致）", lambda t: _golden("liuyao"),
        ("96c7f5d168ca6140", "8168eff9e560d6c2"))
    add("bazi.golden(b7674/fd1a)", "176批前→308批改期望；362 批象层上线：正文增【象上看】段（宫位/六亲/脏腑）→ 措辞指纹 3512→baa1（机械层未动，评分未改）；"
        "363 批行运成格变格分列读数：narrate 增【行运成格变格】段（只命名结构引动，不覆写本命格局成败、不进评分）→ 措辞指纹 baa1→168c→72b4（末次为裁决行去重），机械层始终未动；"
        "374 批岁运五式（合先于克）与 383／385 批化格字段 → 机械 21a4ff76a5e75662、措辞 872bde611188a5e9；"
        "394 批化格补三条（妒合两两相配／禄旺＋化神不通不化／定义例改日主无根）→ 措辞 872b→085b1b5be0178428（仅 mid_jianlu 一例 假化→不化，机械层零漂移）；"
        "396 批五行专旺门 → MP066 无→炎上·真从（special_pattern 入 conclusion），机械 21a4→b7674a8f6d8d1162、措辞 085b→081d93e081f54b2b（另 3 例不在 golden 40）；"
        "411 批（原 401，批号归位）报告层补十神作用篇提纲 → 措辞 081d→e158d5cb8a92e005（机械层零漂移；capture 见 digest#narrate_drift_log）；"
        "466 批 narrate 十神作用提示行改用正则提取行号（兼容 source 两种写法，修复空格格式渲染整串路径）→ 措辞 e158→fd1a1b0b60e06104（机械层零漂移，capture 同样入 drift_log）。"
        "（364 批六爻欠账清理时账台报分家：bazi/dev_tools/golden.py 已 capture 而本账期望值仍停在 baa1，属登记过期不是回归，按 drift_log 归因回补。"
        "注意：本值随 capture 同步；若再分家，先读 drift_log 再改，勿凭记忆填。）",
        lambda t: _golden("bazi"),
        ("b7674a8f6d8d1162", "fd1a1b0b60e06104"))

    def _cap_expect():
        """期望值直接取两科 digest.json 实值，不在账台再抄一份指纹清单。"""
        out = []
        for d in ("liuyao", "bazi"):
            j = json.loads((ROOT / d / "data" / "golden" / "digest.json").read_text(encoding="utf-8"))
            out += [j["digest"], j["narrate_digest"]]
        return tuple(out)

    add("capability.golden 文本↔digest(4)",
        "539 批新增：CAPABILITY T1 双科双指纹声明 ↔ golden/digest.json 实值（466 批正文未回流）；"
        "期望值现场取 digest 真源，不新增 check.py 门号、不新增门文件（守 528 约定）",
        lambda t: _capability_golden(), _cap_expect())
    add("governance(78/49, blk 34/30)",
        "194批（312 补 310；315 补 314/315 两门；317 补 judge_shadow；329 补 fetch_zengshan_dz_cases；"
        "331 批 check_docs_index 上提到 devkit/root → 六爻 blk 28→27、脚本仍 63；"
        "339 批 A5-1 按实登记 7 个存量未分类脚本 → 八字 37→43；"
        "344 批新增 check_expected_coverage → 六爻 63→64、blk 27→28；"
        "362 批两科各新增 check_xiang（blocking）＋xiang_coverage（nightly）→ 六爻 64→66、blk 28→29，八字 43→45、blk 26→27；"
        "364 批六爻新增 check_bond_polarity（门 [40]，blocking）→ 六爻 66→67、blk 29→30，八字不变；"
        "408 批六爻新增 build_bushi_zhengzong_cases → 六爻 67→68；"
        "420 批八字新增 check_expected_coverage（门 [40]，blocking）→ 八字 45→46、blk 27→28；"
        "422 批六爻新增 check_prose_readings（门 [41]，blocking）→ 六爻 68→69、blk 30→31，八字不变；"
        "430 批八字恢复 check_case_quotes（门 [41]，blocking）→ 八字 46→47、blk 28→29，六爻不变；"
        "433 批两科各新增 check_source_provenance（门 [42]，blocking）→ 六爻 69→70、blk 31→32，"
        "八字 47→48、blk 29→30；438 批六爻新增 check_case_source_hashes（门 [43]，blocking）"
        "→ 六爻 70→71、blk 32→33，八字不变；499 批八字新增 cross_version_collate.py"
        "（跨版本窗口对拍，观测非 blocking 门）→ 八字 48→49，blk 不变）"
        "；**511 批：六爻 71→74 是 ontology 三件（check_ontology／ontology_subgraph／render_ontology）"
        "自建图起就未入治理表、也未挂 check.py，地图一直报「未分类」而无人回改**——同批已补登记（tier 见 governance_map.py），"
        "并记下缺口：check_ontology 仍只是手工门，未接线"
        "；**512 批已接线**：`check_ontology` 升 blocking 并进 `check.py` [44]（孤儿/父链/幽灵引用/impl 锚定四条），"
        "六爻 blocking 33→34，脚本总数 74 不变"
        "；**535 批：六爻 74→75** 是新增 `readme_reconcile.py`（README 关键数字↔readout_ledger 真值对账的 B 轻门 reconcile 器，"
        "挂 CI root-gates，tier=ondemand 非 blocking）——本器自落库即入治理表（CURATED 已挂、地图不再报「未分类」），属正当 +1，"
        "期望由 74 回挂 75（blk 不变）"
        "；**537 批：六爻 75→76** 是新增 `static_enhancement_guard.py`（536 静卦静默降级缺陷的常驻回归守卫："
        "逐静卦断言 advanced_analysis 含 enhance_reading 经典增强签名键，--selftest 注入空增强判红有齿；"
        "挂 CI root-gates，tier=ondemand 非 blocking）——本器自落库即入治理表（CURATED 已挂），属正当 +1，"
        "期望由 75 回挂 76（blk 不变）"
        "；**542 批：六爻 76→77** 是新增 `verify_yilin_candidates.py`（《易林補遺》L1279 七案候选池的"
        "只读同源复验器：引文逐字／ID 零泄漏／无反推／预注册未开卷，8 类内存负例；挂 CI root-gates，"
        "tier=ondemand 非 blocking）——同批入治理表 CURATED，属正当 +1，期望由 76 回挂 77（blk 不变）"
        "；**543 批：六爻 77→78** 是新增 `open_yilin_candidates.py`（用户授权后的一次性开卷器："
        "机读重建七案盘面、按 542 批冻结的 top-1 指标逐例判卷、只此一次开封、n<30 只报红绿；"
        "`--verify` 只读挂 CI root-gates，tier=ondemand 非 blocking）——同批入治理表 CURATED，"
        "属正当 +1，期望由 77 回挂 78（blk 不变）",
        lambda t: _gov_counts(), ("78", "49", "34", "30"))

    # 344 批：expected 书证/机械派生字段的覆盖生存线（门 [38]）。
    # 1592923 的事故证明「聚合分掉 6 分、所有门全绿」可以并存；本项把非空计数
    # 直接入账，任何整批清空都会在同一条账上显形。
    def c_expected_coverage(t):
        s = sh(["dev_tools/check_expected_coverage.py"])
        fields = ("use_god", "use_god_branch", "use_god_position", "use_god_note",
                  "use_god_wangshuai", "use_god_muku", "use_god_six_spirit", "verdict")
        found = dict(re.findall(r"·\s+([A-Za-z_]+)\s+(\d+)/", s))
        return tuple(found.get(f, "") for f in fields)
    add("liuyao.expected_coverage(78/55/3/32/3/3/3/58)",
        "344批（恢复 1592923 清空的 292/297/298 批书证标签；门 [38]）",
        c_expected_coverage, ("78", "55", "3", "32", "3", "3", "3", "58"))

    # 422 批：prose 通道吉凶书证（门 [41]）。421 批只校验「引文在全库任意处」，
    # L2334 把 L2911（ZDP024）的句子记到 ZDP012 名下仍全绿；本项把册/案例/分片
    # 三组计数与两个分片读数一起钉住，任何清空、错指或分片漂移都在同一行显形。
    def c_prose(t):
        cs = json.loads((DISC / "data" / "cases" / "zengshan_dz_prose_cases.json")
                        .read_text(encoding="utf-8"))["cases"]
        rd = json.loads((DISC / "data" / "cases" / "zengshan_dz_prose_readings.json")
                        .read_text(encoding="utf-8"))["readings"]
        sp = json.loads((DISC / "data" / "cases" / "case_splits.json")
                        .read_text(encoding="utf-8"))
        nv = sum(1 for c in cs if (c.get("expected") or {}).get("verdict"))
        s1 = sh(["eval/evaluate.py", "--split", "zengshan_dz_prose_holdout"])
        s2 = sh(["eval/evaluate.py", "--split", "zengshan_dz_prose_direction"])
        return (str(len(cs)), str(len(rd)), str(nv),
                str(len(sp["zengshan_dz_prose_direction"])),
                grab(s1, r"平均分 = ([0-9.]+)%"), grab(s2, r"平均分 = ([0-9.]+)%"))
    add("liuyao.prose(38/28/23/19, 89.2/60.6)",
        "422 批（421 批 L2334 跨案引文修正＋11 例旧册非空吉凶补书证＋7 例书载明确结果入册；"
        "direction n 12→19，新旧不可比；门 [41]）",
        c_prose, ("38", "28", "23", "19", "89.2", "60.6"))

    # 案例分母（234 批）：账台钉率也钉分母——删/添一例而率恰不动时，分母行会红。
    def c_case_denoms(t):
        sp = json.loads((DISC / "data" / "cases" / "case_splits.json").read_text(encoding="utf-8"))
        cl = json.loads((DISC / "data" / "cases" / "classical_cases.json").read_text(encoding="utf-8"))
        n_cl = cl.get("cases") if isinstance(cl, dict) else cl
        return tuple(map(str, (len(n_cl if n_cl else cl),
                                len(sp["tune"]), len(sp["holdout"]),
                                len(sp["wikisource_holdout"]), len(sp["wikisource_direction"]),
                                len(sp["zengshan_dz_holdout"]),
                                len(sp["bushi_zhengzong_holdout"]))))
    add("六爻案例分母(44/20/12/50/31/29/38)", "234批（率与分母并钉）；402 批 zengshan_dz 21→29；"
        "408 批 bushi_zhengzong 0→26；409 批通用确认句回溯 26→36；410 批相对期 36→38；"
        "414 批 BZ0462 期望单位修正（n 不变，不增删案例）",
        c_case_denoms, ("44", "20", "12", "50", "31", "29", "38"))

    def c_bazi_denoms(t):
        cc = json.loads((ROOT / "bazi" / "data" / "cases" / "bazi_classical_cases.json")
                        .read_text(encoding="utf-8"))["cases"]
        ex = json.loads((ROOT / "bazi" / "data" / "cases" / "bazi_external_cases.json")
                        .read_text(encoding="utf-8"))
        from collections import Counter
        c = Counter(x.get("split") for x in cc)
        return (str(c["tune"]), str(c["holdout"]), str(len(ex.get("cases") or ex)))
    add("八字案例分母(61/279/69)", "234批；339 批实跑 53→62（326/329 批语料扩样后外部集 +9 例）；"
        "368 批清例后 holdout 278→276（两例同考点双建被清，非引擎回归）；"
        "395 批《千里命稿》从格 4 例入册（QL001 进 tune、QL002-004 进 holdout）→ 60/276→61/279；"
        "411 批（原 401）外部集《消息赋》3 例入册 → 62→65；"
        "412 批《命理约言》MY001 入册 → 65→66（该批只改语料未回改本账，408 批补登）；"
        "414 批 MY002 入册 → 66→67（同批未回改本账，414 六爻批补登）；"
        "415 批 YP001/YP002 入册 → 67→69（同批未回改本账，416 批补登）",
        c_bazi_denoms, ("61", "279", "69"))

    # 头牌值在位性（235 批）：现状文档（README×2/CAPABILITY/GOVERNANCE）必须各含每个
    # 主读数**至少一处**——文档被改回旧值（176 批 97.3 事故族）时现值消失即红。
    # 不查"旧值不得出现"：更正记录合法引用旧值，absence 判据在该域机械不可分（235 探针实证）。
    def c_headline_present(t):
        docs = [(ROOT / x).read_text(encoding="utf-8") for x in
                ("liuyao/README.md", "bazi/README.md", "CAPABILITY.md", "GOVERNANCE.md")]
        # 235 批清单按当时现值；308 批 bazi holdout 97.6→99.5、368 批再→100.0，
        # 97.6 只作历史注记（163 批），不再入「现值在位」清单；387 批换成 93.3；
        # 395 批千里 3 造入 holdout 后 cong 14/15→17/18，按现状改为 94.4。
        heads = ("97.9", "90.2", "62.4", "27.3", "33.3", "52.3", "94.4", "96.2", "80.6")
        gone = [h for h in heads if not any(h in d for d in docs)]
        return f"{len(heads) - len(gone)}/{len(heads)}" + ("" if not gone else " 缺:" + ",".join(gone))
    add("头牌值在位(9/9)", "235批（176 事故族的正向断言）；387 批 97.6→93.3（97.6 是 308 前旧值）；"
        "395 批 93.3→94.4（cong 14/15→17/18）",
        c_headline_present, ("9/9",))

    # tracked×ignore 漂移（237 批）：任何已跟踪文件不得再命中 ignore 规则（产物规矩的存量面）。
    def c_ignore_drift(t):
        import subprocess as sp
        r = sp.run(["git", "-C", str(ROOT), "ls-files", "-i", "-c", "--exclude-standard"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
        rows = [x for x in (r.stdout or "").splitlines() if x.strip()]
        return str(len(rows))
    add("tracked×ignore 漂移(0)", "237批（236 一次性杂检的常设化）", c_ignore_drift, ("0",))

    # tracked 完整性（238 批）：全库可 UTF-8 解码＋全 tracked JSON 可解析——
    # 各门只读自己那几个文件，从未有全量口径；破损会在最意外的运行时现形。
    def c_tracked_integrity(t):
        import subprocess as sp
        # 312 批修：本项原判据"全库可 UTF-8 解码"把二进制资产当破损件
        # （实抓旧 claude-plugin/assets/icon.png 恒计 1，导致该项长期 × 而被当噪声；
        #  该目录已于 497 批删除）——
        # 二进制按扩展名豁免；文本仍全量解码，JSON 仍全量解析。
        BINARY_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".bmp",
                         ".woff", ".woff2", ".ttf", ".otf", ".tgz", ".zip", ".gz", ".pdf"}
        files = sp.run(["git", "-C", str(ROOT), "ls-files", "-z"],
                       capture_output=True).stdout.split(b"\0")
        bd = bj = 0
        for f in filter(None, files):
            p = ROOT / f.decode("utf-8", errors="replace")
            if not p.exists():
                continue
            if p.suffix.lower() in BINARY_SUFFIX:
                continue
            b = p.read_bytes()
            try:
                b.decode("utf-8")
            except UnicodeDecodeError:
                bd += 1
            if p.suffix == ".json":
                try:
                    json.loads(b.decode("utf-8", errors="replace"))
                except Exception:
                    bj += 1
        return (str(bd), str(bj))
    add("tracked 完整性(解码0/JSON0)", "238批（353 文件 89 JSON 全量口径首立）", c_tracked_integrity, ("0", "0"))

    # 零耦合铁律（§二）的机器化（243 批）——AGENTS「两科禁止任何相互 import」五十批无门。
    # 判据只收 import 图（机械可分）；路径字符串启发式已废——实测唯一命中是 docstring
    # 说明文里的科名（243 探针记录，字符串级误报形态留此供后人不再重蹈）。
    def c_no_cross_import(t):
        import ast as _ast
        n = 0
        for d, other in (("bazi", "liuyao"), ("liuyao", "bazi")):
            for p in (ROOT / d).rglob("*.py"):
                if "__pycache__" in str(p):
                    continue
                try:
                    tree = _ast.parse(p.read_text(encoding="utf-8", errors="replace"))
                except SyntaxError:
                    continue
                for nd in _ast.walk(tree):
                    mods = ([a.name for a in nd.names] if isinstance(nd, _ast.Import)
                            else [nd.module] if isinstance(nd, _ast.ImportFrom) and nd.module else [])
                    n += sum(1 for m in mods if m == other or m.startswith(other + "."))
        return str(n)
    add("两科零耦合 import(0)", "243批（§二铁律五十三批后获断言版）", c_no_cross_import, ("0",))

    # --raise 合并基回归（244 批）：241 病的常设齿（静态双钉＋六爻功能探针，bytes 级自恢复）。
    def c_raise_guard(t):
        r = sh(["dev_tools/check_raise_regression.py"])
        return "PASS" if "全净" in r else (r.strip().splitlines() or ["?"])[-1][:40]
    add("raise 回归守卫(PASS)", "244批（修过的病必须带齿常驻）", c_raise_guard, ("PASS",))

    # 嵌入式 --only 声称的键真实性（249 批）：报错文案/注释里让用户去跑
    # `check.py --only X` 的每一处 X 必须是该科 want 真值源里的真键——
    # 249 全库首扫抓 1 处坏键（fetch_huozhulin 的 selfconsistency，已修 case_selfconsistency）。
    def c_embedded_only_keys(t):
        import re as _re

        def keys_of(dname: str) -> set:
            ck = (ROOT / dname / "dev_tools" / "check.py").read_text(encoding="utf-8")
            return (set(_re.findall(r'want\("([a-z_0-9]+)"\)', ck))
                    | set(_re.findall(r'\("([a-z_0-9]+)",\s*"\[', ck)))
        K = {d: keys_of(d) for d in ("liuyao", "bazi")}
        bad = 0
        for d in ("liuyao", "bazi"):
            for p in (ROOT / d).rglob("*.py"):
                if "__pycache__" in str(p) or p.name == "check.py":
                    continue
                s = p.read_text(encoding="utf-8", errors="replace")
                for m in _re.finditer(r"check\.py[^\n\"']*--only\s+([a-z_0-9,\s]+)", s):
                    for tok in _re.split(r"[,\s]+", m.group(1).strip()):
                        if tok and tok not in K[d]:
                            bad += 1
        return str(bad)
    add("嵌入式 --only 坏键(0)", "249批（报错文案是 Agent 的行动指令，它自己先得可执行）", c_embedded_only_keys, ("0",))

    # 登记×提交在册（254 批·253 事故的结构性反应）：现代史（≥176）每个 changelog
    # 标题批号必须被至少一条提交信息（全信息体、中文或阿拉伯数字形）提及——
    # 防"写了条目没提交"的半个虚构面（72 型虚构若落在 changelog 上，下轮 quick 即红）。
    # 已知具名历史孤儿：221（误编号案：实体在 8275cef 而信息写 212，勘误文本未入任何信息体）。
    # 孤儿批次**结案表**（309 批）：batch → 结案依据（真实提交 hash + 为什么机械匹配不到）。
    # 有提交不等于匹配得上——本表的意义是把「匹配失败的原因」逐条钉死，
    # 而不是把 11 条当成「没提交」一笔带过（那正是 253 批那类"叙事代替核查"的复辟）。
    SETTLED_ORPHANS = {
        221: "提交 8275cef：标题写作『第两百一十二…不，第两百二十一』，**编号后没跟『批』字**，正则匹配不到；实际即 221 的 [24] 活性判据",
        264: "提交 21990da『第两百六十四～两百六十八批合并入库』：范围简写只匹配到首号",
        265: "同 21990da（合并入库，范围简写未逐条展开）",
        266: "同 21990da",
        267: "同 21990da",
        268: "同 21990da",
        297: "提交 e8c12a0『第两百九十七、两百九十八批』：顿号并列只匹配到首号",
        298: "同 e8c12a0（顿号并列未逐条展开）",
        317: "【已登记】317 批提交信息显式写了第三百一十七批，本条不再计入孤儿（保留原文备查）",
        324: "提交 fbd9e22：提交标 234、changelog 记 324，编号不一致，待统一",
        325: "提交 b9f49ff：提交标 235、changelog 记 325，编号不一致，待统一",
    }
    _ORPHAN_CACHE = {}

    def c_registration_orphans(t):
        import re as _re
        import subprocess as _sp
        cn = {"〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9}

        def parse(s):
            tot = num = 0
            for ch in s:
                if ch in cn:
                    num = num * 10 + cn[ch]
                elif ch == "十":
                    tot += (num or 1) * 10; num = 0
                elif ch == "百":
                    tot += (num or 1) * 100; num = 0
                elif ch == "千":
                    tot += (num or 1) * 1000; num = 0
            return tot + num
        heads = set()
        for d in ("liuyao", "bazi"):
            # 读 HEAD 版本而非工作树：巡逻语义＝对已提交态核对；在制批的未提交条目
            # 不该判红（254 上线首跑即抓到自己诞生瞬间的"条目已写、提交未在册"，
            # 该误红暴露了口径须钉 HEAD——已按 §六.2 分诊归正）。
            # 批号在册口径（342 批精简后）：主 CHANGELOG **与历史索引**都算数——
            # 342 批删除了 CHANGELOG-ARCHIVE 全文，把 154 批（六爻）／81 节（八字）
            # 的 `## 日期 第N批` 标题保留进 `CHANGELOG-HISTORY-INDEX.md`；批号一个没少，
            # 只是换了文件。只读主文件会把它们全判成孤儿。
            for fn in ("docs/CHANGELOG.md", "docs/CHANGELOG-HISTORY-INDEX.md"):
                txt = _sp.run(["git", "-C", str(ROOT), "show", f"HEAD:{d}/{fn}"],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace").stdout
                heads |= {parse(x) for x in _re.findall(
                    r"^## \d{4}-\d{2}-\d{2} 第([零〇一二两三四五六七八九十百千]+)批", txt, _re.M)}
        body = _sp.run(["git", "-C", str(ROOT), "log", "--format=%B\x01"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        men = ({parse(x) for x in _re.findall(r"第([零〇一二两三四五六七八九十百千]+)批", body)}
               | {int(x) for x in _re.findall(r"第(\d{1,4})批", body)})
        orph = sorted(h for h in heads if h and h > 175 and h not in men)
        _ORPHAN_CACHE['orph'] = orph
        return str(len(orph))

    def c_registration_unsettled(t):
        orph = _ORPHAN_CACHE.get('orph') or c_registration_orphans(t) and _ORPHAN_CACHE['orph']
        return str(len([h for h in orph if h not in SETTLED_ORPHANS]))
    # 308 批改期望 1 → 11：历史遗留的 10 条孤儿批次（264-268、297、298、317、324、325 等）
    # 属「写了 changelog、提交信息没带批次号」，逐条结案另批；本项的意义是**不得再新增**，
    # 故把期望值抬到当前盘值并立案，新的孤儿仍会判红（理由见 liuyao/docs/CHANGELOG.md 308 批）。
    add("登记×提交在册(2=221+264)", "254批→308批改期望；317 批补记（317 号已登记，11→10）；330 批文档整理后并行会话的提交补登了 319/326/327/328 批，孤儿 10→8（342 批起批号在册口径扫 CHANGELOG-HISTORY-INDEX.md，归档全文已删）；**511 批：孤儿降至 2**（221／264，二者均在 SETTLED_ORPHANS 有结案依据：221 提交信息编号后没跟「批」字、264 是 264–268 合并入库的范围简写），故按实值 2 重挂；新增孤儿仍判红", c_registration_orphans, ("2",))
    # 309 批：孤儿**逐条结案**。查清根因不是"没提交"，而是三种机械匹配失败：
    #   ① 合并入库用了范围简写「第A～B批」→ 只匹配到首号（264-268 全部落进 21990da）；
    #   ② 顿号并列「第A、B批」→ 只匹配到首号（297/298 落进 e8c12a0）；
    #   ③ 提交标题里的编号**没带『批』字**（221 落进 8275cef，写作「第两百一十二…不，第两百二十一」）。
    # 另有 317/324/325 属**提交编号与 changelog 编号不一致**（提交标 237/234/235），
    # 已具名登记、待编号勘误批统一。本项断言「**表外不得新增**」，新的未结案孤儿即判红。
    add("登记×提交 未结案孤儿(0)", "309批（逐条结案表见 SETTLED_ORPHANS）", c_registration_unsettled, ("0",))

    # 集合互斥（258 批·铁律三的集合面守卫）：六爻 case_splits 十二集两两零交集＋
    # 八字案例 id 无跨 split 重复。此前八字 tune∩holdout=0 只是叙事，两科皆无断言——
    # 一例泄漏即让「holdout 未参与调参」的所有句子从根上坏掉，而全账不会红。
    def c_split_disjoint(t):
        sp = json.loads((DISC / "data" / "cases" / "case_splits.json").read_text(encoding="utf-8"))
        sets = {}
        for k, v in sp.items():
            if isinstance(v, list):
                sets[k] = {x if isinstance(x, str) else (x.get("id") or "") for x in v}
        nm = list(sets)
        lu = sum(len(sets[a] & sets[b]) for i, a in enumerate(nm) for b in nm[i + 1:])
        bz = json.loads((ROOT / "bazi" / "data" / "cases" / "bazi_classical_cases.json")
                        .read_text(encoding="utf-8"))["cases"]
        seen: dict = {}
        rep = 0
        for c in bz:
            cid, s = c.get("id"), c.get("split")
            if cid in seen and seen[cid] != s:
                rep += 1
            seen.setdefault(cid, s)
        return str(lu + rep)
    add("集合互斥泄漏(0)", "258批（铁律三集合面补闸：六爻十二集两两∅＋八字 id 不跨 split）", c_split_disjoint, ("0",))

    def c_tier_consistency(t):
        ml = json.loads((ROOT / "liuyao" / "docs" / "GOVERNANCE-MAP.json").read_text(encoding="utf-8"))
        mb = json.loads((ROOT / "bazi" / "docs" / "GOVERNANCE-MAP.json").read_text(encoding="utf-8"))
        hv = [len(ml["tier_link_violations"]["blocking_not_referenced"]),
              len(mb["tier_link_violations"]["blocking_not_referenced"])]
        sv = [len(ml["tier_link_violations"]["referenced_not_blocking"]),
              len(mb["tier_link_violations"]["referenced_not_blocking"])]
        return tuple(map(str, hv + sv))
    add("tier一致性(硬0/0软9/4)", "207批（软 bazi=diff_tiaohou_vs_head 的 required 存在性引用，合法在账；冒出未见条目即红）；439 批 build_siku_dz 由 [43] 以 --check 消费，软引用 1→2；463 批 build_tiaohou 由 [9] 以 --check 消费，软引用 2→3；464 批 build_dts_corpus 由八字 [9]、build_question_use_gods／build_use_god_rules 由六爻 [12] 消费（bazi 3→4、liuyao 0→2，同属合法存在性引用）；472 批 build_adjudications 由六爻 [12] 以 --verify 消费（liuyao 2→3）；**519 批 [46] 构建器同步门接入，六爻新增 6 条 --check 存在性引用**：build_zengshan_dz_cases／build_bushi_zhengzong_cases／build_yiin_cases／build_yingqi_set／build_usegod_position／build_extra_dimensions（liuyao 3→9，逐条见 519 批 check.py 的 build_sync 表；**519 批接线后 `GOVERNANCE-MAP.json` 产物未同步，6 个脚本的 run_by_check_py 仍为 false，522 批重生成产物使图与代码一致**，并同步回改本账期望、逐条归因）。硬引用两科仍 0／0、八字软引用仍 4，计数口径未变，纯属合法条目增加，非引擎回归",
        c_tier_consistency, ("0", "0", "9", "4"))

    # --- 八字侧 ---
    def c_bazi_holdout(t):
        s = sh(["eval/evaluate.py", "--split", "holdout"], cwd=ROOT / "bazi")
        return grab(s, r"平均分 = ([0-9.]+)%")
    # 308 批改期望：holdout 均分 97.6 → 99.5（pattern 由 29/36 抬到 36/36 为主因）；
    # 368 批清例后再 → 100.0（n=276，满分 275/276、仍有 1 例不满分；打印值 99.99x 四舍五入）。
    add("bazi.holdout(100.0)", "bazi README→308批→368批改期望", c_bazi_holdout, ("100.0",))

    def c_bazi_dims(t):
        s = sh(["eval/evaluate.py", "--split", "holdout"], cwd=ROOT / "bazi")
        out = []
        for name in ("pillars", "ten_gods", "hidden_stems", "tiaohou", "pattern", "cong_ge"):
            m = re.search(r"^\s*%s\s+(\d+)/(\d+)\s+\d+\s+[\d.]+%%" % name, s, re.M)
            out.append((m.group(1) + "/" + m.group(2)) if m else None)
        return tuple(out)
    add("bazi.holdout 分维(213/213×3 51/51 36/36 17/18)", "bazi README 表/187批→308批→368批→395批改期望"
        "（368 批 ZC015 收掉：cong 13/15→14/15；395 批千里 3 造入 holdout：cong 14/15→17/18）", c_bazi_dims,
        ("213/213", "213/213", "213/213", "51/51", "36/36", "17/18"))

    def c_dimlock(t):
        s = sh(["dev_tools/" + "check_dim" + "_lock.py"], cwd=ROOT / "bazi")  # 拼接防 [11] 当六爻路径声明；跨科只读调用非 import，零耦合不破
        m = re.search(r"shensha＝tune:(\d+)/(\d+)、holdout:(\d+)/(\d+)\s+dayun＝tune:(\d+)/(\d+)、holdout:(\d+)/(\d+)", s)
        return tuple(m.groups()) if m else (None,) * 8
    add("bazi.dimlock(shensha 0/0·5/5, dayun 0/0·0/0)", "bazi README 六限制/170批", c_dimlock,
        ("0", "0", "5", "5", "0", "0", "0", "0"))

    def c_bazi_ext(t):
        s = sh(["eval/evaluate.py", "--split", "external_holdout"], cwd=ROOT / "bazi")
        n = re.search(r"运行 (\d+) 例（external_holdout", s)
        sw = re.search(r"强弱对齐（external_holdout · report-only，不设门槛、非命中率）：(\d+)/(\d+)", s)
        return ((n.group(1), sw.group(1), sw.group(2)) if n and sw else (None,) * 3)
    add("bazi.external(n69 强弱34/57 report-only)",
        "bazi README/160批起；339 批实跑 53→62；411 批（原 401）消息赋 3 例 → 65（外集扩样后同步）；"
        "412 批命理约言 MY001 → 66（强弱读数同批改 33/55；该批未回改本账，408 批补登）；"
        "414 批 MY002 → 67（强弱 34/56；同批未回改本账，414 六爻批补登）；"
        "415 批 YP001/YP002 → 69（强弱 34/57：YP001 分歧进分母不进分子；同批未回改本账，416 批补登）",
        c_bazi_ext, ("69", "34", "57"))

    def c_bazi_base(t):
        s = sh(["dev_tools/baselines.py", "--split", "holdout"], cwd=ROOT / "bazi")
        m_t = re.search(r"tiaohou：引擎 (\d+)/(\d+) =\s*([\d.]+)%", s)
        m_p = re.search(r"pattern：引擎 (\d+)/(\d+) =\s*([\d.]+)%", s)
        m_c = re.search(r"先验定答从\s+(\d+)/(\d+) =\s*([\d.]+)%", s)
        vals = tuple(x.group(3) if x else None for x in (m_t, m_p, m_c))
        mb = re.search(r"定答\(tune边际\)\s+\d+/\s*\d+ =\s*[\d.]+% ｜配对 b=(\d+) c=(\d+)", s)
        return vals + ((mb.group(1), mb.group(2)) if mb else (None, None))
    # 344 批：pattern 80.6 是 187 批旧值；308 批已实测 100.0（36/36，McNemar p=0.004），
    # 但账台行漏改。此处按 308 实测回填，不是新提升。
    add("bazi(tiaohou100.0 pattern100.0 常数从100 b42c0)",
        "187批→308批实测（344 批回填漏登）；368 批清例后 tiaohou 96.2→100.0（51/51）", c_bazi_base,
        ("100.0", "100.0", "100.0", "42", "0"))

    # --- 前瞻通道在册 0 ---
    # CAPABILITY.md 的结构性计数（第两百一十四批补齐：对外文书的每个数字都要有重放断言）
    def c_struct_counts(t):
        g1 = re.search(r"用例 (\d+) 条", sh(["dev_tools/golden.py", "verify"]))
        g2 = re.search(r"用例 (\d+) 条", sh(["dev_tools/" + "golden.py", "verify"], cwd=ROOT / "bazi"))
        hx = re.search(r"爻序断言：(\d+) 项通过", sh(["dev_tools/" + "hexagram_check.py"]))
        reg = str(len(json.loads((ROOT / "liuyao" / "data" / "rules" / "legacy" / "rule_registry.json")
                                .read_text(encoding="utf-8"))["rules"]))
        # 跨科调用一律拼接（206 批规矩；本行首版又写全名被 [11] 当场逮——同名单双也拼，断侥幸）
        rg = re.search(r"机械回归通过 (\d+) 例", sh(["dev_tools/" + "regression.py"], cwd=ROOT / "bazi"))
        es = re.search(r"（(\d+) 个场景", sh(["dev_tools/" + "eval_selftest.py"], cwd=ROOT / "bazi"))
        return tuple((x.group(1) if x else None) for x in (g1, g2, hx, rg, es)) + (reg,)
    add("CAPABILITY 结构计数(288/40/23/5/9/33)", "214批", c_struct_counts,
        ("288", "40", "23", "5", "9", "33"))

    add("prospective 在册 0 条", "177/178批", lambda t: (
        "0" if not (DISC / "data" / "feedback" / "predictions.jsonl").exists()
        else str(len([1 for _ in open(DISC / "data" / "feedback" / "predictions.jsonl",
                                     encoding="utf-8") if _.strip()])),), ("0",))

    def c_rule_sha(t):
        code = ("import sys;sys.path.insert(0,'scripts');sys.path.insert(0,'dev_tools');"
                "from kernel_path import ensure_kernel_on_path;"
                "ensure_kernel_on_path('dev_tools/prospective.py');"
                "import prospective;print(prospective.rule_sha())")
        out = sh(["-c", code]).strip()
        return out.splitlines()[-1] if out else None
    # SCORING_RULE 冻结 sha 的**值**自 216 批才首次落盘——180 批加 task=占天候 支时只登记了
    # 变更事件未记值；本行初稿曾拿会话记忆的 178 时代值（a36243fc6239，盘上与 git 历史均无）
    # 当期望，实算当场打回 7867316a7303。**期望从此是字面钉桩**：口径再动此行即红，
    # 改期望的唯一合法路径＝CHANGELOG 注明理由（姊妹条款）。
    # SKILL 合同路径审计（232 批）：点号路径声称须在真实 analyze 输出可达
    # （文档根或 step5 简写两形皆认；.py 文件引用不在此族）。合同面是任务 Agent 的取数依据。
    def c_skill_paths(t):
        import subprocess as sp
        sk = (DISC / "SKILL.md").read_text(encoding="utf-8")
        claims = [x for x in sorted(set(re.findall(r"`([a-z_]+(?:\.[a-z_\[\]0-9]+){1,})`", sk)))
                  if not x.endswith(".py") and "/" not in x]
        # 262 批双修：①mkdir——全新克隆无 scratch/（git 不存空目录），克隆复验 85 轮现形；
        # ②显式 cwd＋rc 硬失败——本行自 232 起在根目录 cwd 下从未真跑过 chart（相对路径
        #   落空、异常被 capture_output 吞、json.loads 吃的是旧交互残留文件＝活僵尸）。
        #   教训：写盘型账行必须验证被调进程 rc，否则审计的是缓存而不是现势。
        (DISC / "scratch").mkdir(exist_ok=True)
        r1 = sp.run([sys.executable, "-X", "utf8", "scripts/chart.py", "--mode", "manual",
                     "--yao", "7,8,9,7,6,8", "-o", "scratch/_ledger_probe_c.json"],
                    capture_output=True, cwd=str(DISC))
        if r1.returncode != 0:
            raise RuntimeError("chart 探针未真跑 rc=%s" % r1.returncode)
        r2 = sp.run([sys.executable, "-X", "utf8", "scripts/analyze.py", "scratch/_ledger_probe_c.json",
                     "-o", "scratch/_ledger_probe_a.json"], capture_output=True, cwd=str(DISC))
        if r2.returncode != 0:
            raise RuntimeError("analyze 探针未真跑 rc=%s" % r2.returncode)
        doc = json.loads((DISC / "scratch" / "_ledger_probe_a.json").read_text(encoding="utf-8"))
        s5 = (doc.get("thinking_chain") or {}).get("step5_synthesis") or {}
        def resolve(d, path):
            cur = d
            for seg in path.split("."):
                seg = seg.replace("[]", "")
                if isinstance(cur, list):
                    cur = cur[0] if cur else None
                if not isinstance(cur, dict) or seg not in cur:
                    return False
                cur = cur[seg]
            return True
        miss = [x for x in claims if not (resolve(doc, x) or resolve(s5, x))]
        return f"{len(claims)}/{len(claims) - len(miss)}"
    add("SKILL 合同路径(20/20 可达)", "232批（22 系含 .py 引用的粗提数，工具正确排除后实算 20——期望又取自记忆非实算，账台首跑即抓）", c_skill_paths, ("20/20",))

    # 八字 api_spec 合同键审计（233 批）：反引号小写键须现算可达。
    # 探针教训铸死在此：chart 无 dayun（analyze 现算）、dayun 需 gender——两次空结果
    # 皆探针形错非文档漂移（§四.8 第三次救「冤枉文档」）。
    def c_bazi_api_keys(t):
        import subprocess as sp
        # 308 批：探针产物改为**系统临时目录**。
        # 原实现把中间 JSON 写进 `bazi/scratch/`——那是**跨科写**（六爻侧的脚本往
        # 八字科目录里落文件）。`scratch/` 被 gitignore 所以不脏树，但它使
        # 「零耦合」只能按「不做 import」来读。按 AGENTS.md §二 308 批新定的口径
        # （无 import **且无跨科写**），这里改为临时目录，用完即删。
        import os as _os
        import tempfile as _tf
        B = ROOT / "bazi"
        with _tf.TemporaryDirectory(prefix="yi-ledger-bz-") as tmp:
            cp = _os.path.join(tmp, "chart.json")
            ap = _os.path.join(tmp, "analyze.json")
            r1 = sp.run([sys.executable, "-X", "utf8", "scripts/chart.py", "--datetime", "1990-06-15 10:00",
                         "--gender", "男", "-o", cp], capture_output=True, cwd=str(B))
            if r1.returncode != 0:  # 同 262 修②：rc 硬验（233 时代缺此，幸其一直带 cwd 真跑过）
                raise RuntimeError("bazi chart 探针未真跑 rc=%s" % r1.returncode)
            r2 = sp.run([sys.executable, "-X", "utf8", "scripts/analyze.py", cp,
                         "-o", ap], capture_output=True, cwd=str(B))
            if r2.returncode != 0:
                raise RuntimeError("bazi analyze 探针未真跑 rc=%s" % r2.returncode)
            doc = json.loads(open(ap, encoding="utf-8").read())
            keys = set()

            def walk(o, d=0):
                if d > 7:
                    return
                if isinstance(o, dict):
                    keys.update(o.keys())
                    for v in o.values():
                        walk(v, d + 1)
                elif isinstance(o, list):
                    for v in o[:8]:
                        walk(v, d + 1)

            walk(doc)
            spec = (B / "references" / "api_spec.md").read_text(encoding="utf-8")
            toks = [x for x in sorted(set(re.findall(r"`([a-z][a-z0-9_]{2,30})`", spec))) if "." not in x and "/" not in x]
            miss = [x for x in toks if x not in keys]
            return f"{len(toks)}/{len(toks) - len(miss)}"
    add("八字 api 合同键(19/19 可达)", "233批（合同面两科对齐；探针形错两次已铸死于注释）", c_bazi_api_keys, ("19/19",))
    add("prospective 口径sha(7867316a7303)", "180批生效/216批落值入册",
        c_rule_sha, ("7867316a7303",))

    # 六爻分析链零随机（217 批 CAPABILITY「三 seed」串号更正的断言化）：随机只许活在起卦层。
    # 第五百零八批升格：step 链与 classical 族已移到 <学科根>/engine/ 下，glob 同步换基准，
    # 否则这两族悄悄退出「零随机」扫描面（覆盖面缩水、读数照旧 0）。
    def c_liuyao_no_random(t):
        import glob as _glob
        n = 0
        for pat in ("engine/pipeline/*.py", "scripts/thinking_chain.py", "scripts/analyze.py",
                    "engine/classical/*.py", "scripts/classical_analysis.py",
                    "scripts/narrate_core.py"):
            for f in _glob.glob(str(DISC / pat)):
                if "random" in Path(f).read_text(encoding="utf-8", errors="replace"):
                    n += 1
        return str(n)
    add("liuyao 分析链含随机文件数(0)", "217批（串号更正伴生断言）", c_liuyao_no_random, ("0",))
    return out


def _collate_now():
    s = sh(["dev_tools/version_collate.py"])
    g = re.search(r"卦面冲突率 = (\d+/\d+)", s)
    p = re.search(r"判词冲突率 = (\d+/\d+)", s)
    return ((g.group(1), p.group(1)) if g and p else (None, None))


def _json_counts(rel, top, keys, key=None):
    d = json.loads((DISC / rel).read_text(encoding="utf-8"))
    src = d.get(top) if top else (d.get(key) if key else d)
    return tuple(str(src.get(k)) for k in keys) if isinstance(src, dict) else (None,) * len(keys)


def _adjud_counts():
    """
    裁决表分布。**不再用 `c[e["status"]] += 1`**——248 批起盘上出现了词汇表外的
    `settled`，那行写法直接 `KeyError: 'settled'`，门从「报数」退化成「抛异常」
    （304 批实测：账台只打印「取数异常 'settled'」，既不判红也不推动任何人）。
    改成 `dict.get` 计数，未知状态另由一个独立账台项盯（见下 `_adjud_unknown`）。
    """
    d = json.loads((DISC / "data" / "rules" / "domain" / "adjudications.json").read_text(encoding="utf-8"))
    c = {"settled_by_source": 0, "frozen_by_user": 0, "open_conflict": 0}
    for e in d["entries"]:
        c[e["status"]] = c.get(e["status"], 0) + 1
    return (str(d["count"]), str(c["settled_by_source"]), str(c["frozen_by_user"]),
            str(c["open_conflict"]))


def _adjud_unknown():
    """
    裁决表状态词汇漂移哨兵：返回**不在三值词汇表内**的状态名（逗号分隔，无则空串）。

    存在理由：`build_adjudications.py` 的 docstring 声明状态为三值
    （settled_by_source / frozen_by_user / open_conflict），而盘上有 1 条
    `settled`——是补进词汇表还是改回 `settled_by_source` 属**判据语义裁定**，
    AGENTS.md §二 禁止按读数改数据，故这里不代为裁定，只把它显形为一行账。
    再冒出新状态名时本项立即判红。
    """
    VOCAB = {"settled_by_source", "frozen_by_user", "open_conflict"}
    d = json.loads((DISC / "data" / "rules" / "domain" / "adjudications.json").read_text(encoding="utf-8"))
    unknown = sorted({str(e.get("status")) for e in d["entries"]} - VOCAB)
    return (",".join(unknown),)


def _draft_counts():
    d = json.loads((DISC / "data" / "cases" / "restorable_candidates.json").read_text(encoding="utf-8"))
    cs = d.get("candidates", [])
    dup = sum(1 for c in cs if any(str(g).startswith("dup_of") for g in c.get("gaps", [])))
    return (str(len(cs)), str(dup))


def _golden(disc):
    s = sh(["dev_tools/golden.py", "verify"], cwd=ROOT / disc)
    m = re.search(r"机械 ([0-9a-f]{16})｜措辞 ([0-9a-f]{16})", s)
    return (m.group(1), m.group(2)) if m else (None, None)


def _capability_golden():
    """539 批：CAPABILITY.md 主文的双科双指纹，与 digest.json 实值对账。

    466 批八字措辞指纹已 capture 为 fd1a…，账台 bazi.golden 项同步钉死，但 CAPABILITY
    正文仍停在 411 批的 e158…——门守住了盘、文本没回流，是 G12–G16 同族第 5 处漂移。
    期望值由 checks() 现场读 digest.json 取回（不抄第三份清单），于是闭环为：
    ① `*.golden` 两项守「盘 ↔ 账台期望」；② 本项守「对外文本 ↔ 同一份盘」。
    """
    text = (ROOT / "CAPABILITY.md").read_text(encoding="utf-8")
    out = []
    # 注：六爻行写「机械层／措辞层」、八字行写「机械／措辞」，两科措辞不统一——
    # 539 批首跑即因这个「层」字失配判红，故用 `层?` 兼容两种形状（不回改历史文案）。
    for anchor in ("六爻：", "八字："):
        m = re.search(r"- " + anchor + r".*?机械层? `([0-9a-f]{16})`／措辞层? `([0-9a-f]{16})`", text)
        out += list(m.groups()) if m else ["<缺指纹>", "<缺指纹>"]
    return tuple(out)


def _gov_counts():
    s = sh(["dev_tools/governance_map.py"])
    l = re.search(r"liuyao：(\d+) 脚本｜blocking (\d+)", s)
    b = re.search(r"bazi：(\d+) 脚本｜blocking (\d+)", s)
    return ((l.group(1), b.group(1), l.group(2), b.group(2)) if l and b else (None,) * 4)


QUICK_SKIP = {"liuyao.wiki top1/top3(31.8/61.4)", "liuyao.baselines 用神25.0/日辰4.5",
              "bazi(tiaohou100.0 pattern100.0 常数从100 b42c0)",
              "liuyao.collate(卦面0/47 判词1/37)",
              "bazi.holdout 分维(213/213×3 51/51 36/36 17/18)",
              "bazi.external(n69 强弱34/57 report-only)"}


def _verdict(bad: int, skipped: int) -> str:
    """结论行口径（344 批）：有跳过项时不得说「全部对账一致」。"""
    if bad:
        return "存在分家读数"
    if skipped:
        return "已跑项全部一致（未跑项不计入结论）"
    return "全部对账一致"


def run(quick: bool) -> int:
    bad = 0
    skipped = 0
    items = checks()
    planned_skip = sum(1 for cid, _, _, _ in items if quick and cid in QUICK_SKIP)
    # 总项数由账台自报（218 批：此前 changelog 里「26/28 项」系我凭手感数的假数——
    # 凡计数自己算、不手打；下面的结论行也带实测 n）。
    # 344 批：quick 跳过的项**不再冒充「全账」**——旧文案在跳过 5 项时仍打印
    # 「全部对账一致（bad=0/全账 39）」，正是本仓反复清掉的假绿形态。
    print("═ 读数对账台（登记值 vs HEAD 重放值）%s·登记 %d 项（本轮跑 %d，跳 %d）═"
          % ("quick" if quick else "full", len(items), len(items) - planned_skip, planned_skip))
    for cid, src, fn, expect in items:
        if quick and cid in QUICK_SKIP:
            print("  ~ %-46s 跳过（full 才跑）" % cid)
            skipped += 1
            continue
        try:
            got = fn(None)
            if not isinstance(got, tuple):
                got = (got,)
        except Exception as e:  # noqa: BLE001
            print("  ! %-46s 取数异常 %s" % (cid, str(e)[:40]))
            bad += 1
            continue
        def norm(x):
            if isinstance(x, tuple):
                return tuple(str(i) for i in x)
            return str(x)
        ok = all(norm(g) == norm(e) for g, e in zip(got, expect)) and len(got) == len(expect)
        print("  %s %-46s（登记：%s）%s" % ("√" if ok else "×", cid, src,
              "" if ok else " 实得 %r ≠ 期望 %r" % (got, expect)))
        bad += 0 if ok else 1
    verdict = _verdict(bad, skipped)
    print("═ 结论：%s（bad=%d，已跑 %d/%d，跳过 %d）——任何 × 都是读数与代码分家的现形，"
          "按 §六.2 立案处理，禁止静默改期望值 ═"
          % (verdict, bad, len(items) - skipped, len(items), skipped))
    return 1 if bad else 0


def selftest() -> int:
    fails = []
    # 自测解析器本体：golden 与 evaluate 的输出必须可抽——对账器不许先瞎
    s = sh(["dev_tools/golden.py", "verify"], cwd=ROOT / "liuyao")
    if not re.search(r"机械 ([0-9a-f]{16})｜措辞 ([0-9a-f]{16})", s):
        fails.append("golden 解析式失配（对账器瞎了）")
    # 344 批：证明 quick 跳过项时不再自称「全部对账一致」，且 QUICK_SKIP 没有死 id
    if _verdict(0, 0) != "全部对账一致":
        fails.append("结论口径：无跳过时应为「全部对账一致」")
    if _verdict(0, 2) != "已跑项全部一致（未跑项不计入结论）":
        fails.append("结论口径：有跳过时仍自称全部一致（假绿）")
    ids = {cid for cid, _, _, _ in checks()}
    missing = sorted(QUICK_SKIP - ids)
    if missing:
        fails.append(f"QUICK_SKIP 指向不存在的项：{missing}")
    print("√ selftest：抽取器在线（golden 双指纹可抽）；结论口径与 QUICK_SKIP 在册"
          if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="读数对账台（登记值 vs HEAD 重放值）")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return run(args.quick)


if __name__ == "__main__":
    raise SystemExit(main())
