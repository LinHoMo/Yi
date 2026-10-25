# -*- coding: utf-8 -*-
"""流派裁决表 v0（第一百八十八批·B2）——四书互驳处，引擎采谁、凭什么、状态如何，一次说清。

背景：全仓所有「与古书吻合」的声称此前都含混指四本书的合成体；但库里明文存在互驳
（觉子曰辟诸书之谬在《增删》是逐章体例，被《黄金策》旧注与《易冒》夹击）。本表把
**每一个已知分歧点**登记为：各方立场（逐字书证＋行号）→ 引擎立场 → 锚点 → 状态。
状态只有三种，不许含糊：
  settled_by_source  引擎照所据书文执行（书内自记例外也逐字在册）
  frozen_by_user     用户裁定冻结（引批次号）
  open_conflict      未决——引擎与语料自证相左，不得称已裁（#33 系此类的正式户口）

本表不改引擎、不进评分面、不挂门（第一百七十六批冻结守台账类新增）；它是「与古书吻合」
这句话的**展开定义**——今后任何报告引用吻合率，须能指回本表的哪几行。

    python dev_tools/build_adjudications.py            # 构建＋落盘（先逐字回验）
    python dev_tools/build_adjudications.py --verify   # 复核在册文件每条书证
    python dev_tools/build_adjudications.py --selftest # 负例：篡改书证必须拒写
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
sys.path.insert(0, str(HERE))
from stable_write import write_stable  # noqa: E402  203 批：幂等写，时间戳=内容最后变化

SRC = DISC / "data" / "sources" / "zengshan_buyi_dz.dz.txt"
OUT = DISC / "data" / "rules" / "adjudications.json"

Z = "《增刪卜易》（zengshan_buyi_dz.dz.txt）"

ENTRIES = [
    {
        "id": "liuyao.xunkong_variants",
        "dispute": "旬空判法：诸书列十一类空（真空/假空/动空/冲空…）vs 野鹤一句「旺不为空」的从简",
        "parties": [
            {"who": "诸书（转述）", "quote": "旬空之法，诸书论太烦，有真空、假空、动空、冲空、填空、无故自空、有散而空、墓空、绝空、害空、安空、破空", "source": Z, "line": 893},
            {"who": "野鹤/觉子", "quote": "非比休囚之真空到底而为空也", "source": Z, "line": 643},
        ],
        "engine_position": "采《增删》简化：真空/假空互斥判定（宁缺勿滥），不采十一类名目",
        "engine_anchor": "rule_registry: liuyao.xunkong_zhenjia → scripts/step3.py:583",
        "status": "settled_by_source",
    },
    {
        "id": "liuyao.clash_scatter_weight",
        "dispute": "冲散权重：《黄金策》空亡重而冲散轻 vs 《易冒》最重冲散 vs 野鹤「旺相冲之愈强，散百中一二」",
        "parties": [
            {"who": "黄金策（转述）", "quote": "黄金策以空亡为重，冲散为轻", "source": Z, "line": 852},
            {"who": "易冒（转述）", "quote": "易冒最重冲散", "source": Z, "line": 852},
            {"who": "野鹤/觉子", "quote": "旺相者冲之愈强", "source": Z, "line": 692},
        ],
        "engine_position": "从《增删》：用神旺相冲不破、休囚始论散；六合/六冲只出结构标签不覆写旺衰",
        "engine_anchor": "rule_registry: liuyao.liuhe_liuchong → scripts/effects.py:analyze_clash_harmony",
        "status": "settled_by_source",
    },
    {
        "id": "liuyao.sanhe_empty_break",
        "dispute": "三合局内一空一破是否破局：「破则不成局」派 vs 《增删》「待填满之日月成之」派",
        "parties": [
            {"who": "《增删》", "quote": "三合局中若有一空破者，待填满之日月成之", "source": Z, "line": 767},
        ],
        "engine_position": "三合/三会成立不以空破即废（待填/待冲结构标签在册；三会成立不再按三合破局论——第一百六十九批 registry 注）",
        "engine_anchor": "rule_registry: liuyao.sanhe → scripts/classical_enhancements.py:analyze_triple_combo；liuyao.sanhui impl 注",
        "status": "settled_by_source",
    },
    {
        "id": "liuyao.month_break_day_stem",
        "dispute": "月破是否永破：「破而不破（临日建/有生扶）」vs 一律论破；例外＝忌神发动伤用（寡不敌众，破亦为破）",
        "parties": [
            {"who": "《增删》例文", "quote": "亥为月破，临日建而不破", "source": Z, "line": 708},
            {"who": "《增删》总论", "quote": "逢月破而不破", "source": Z, "line": 692},
            {"who": "野鹤总论", "quote": "惟而不动又无日辰动爻生助者则到底而破矣", "source": Z, "line": 991},
            {"who": "《增删》实案例外", "quote": "卯木子孙，临月破，又动出申金伤克，虽值日辰，难过酉月卯日", "source": Z, "line": 1911},
        ],
        "engine_position": "月破层存在且救法集条件化（第两百八十批）：临日建1.0/日合0.5/日辰生扶0.5，例外＝卦中忌神类动爻克伤用神时救法不给（L692 寡不敌众；L1911 临日辰仍凶）；第一百五十九批唤醒 is_month_break 死键后外部 top-1 22.7→27.3 为该立场的读数侧写",
        "engine_anchor": "rule_registry: liuyao.yuepo → scripts/classical_enhancements.py:analyze_monthly_break；step3.compute_month_break_modifier（280 批条件化）",
        "status": "settled_by_source",
    },
    {
        "id": "liuyao.tianshi_frost_claims",
        "dispute": "占天时：旧注「冬天以子孙为霜雪」vs 野鹤「占天时不论旺衰，亦未有以子孙为霜雪」",
        "parties": [
            {"who": "旧注（转述）", "quote": "旧注有云，冬天以子孙为霜雪", "source": Z, "line": 1963},
            {"who": "野鹤/觉子", "quote": "所以占天时，不论旺衰，亦未有以子孙为霜雪也", "source": Z, "line": 1971},
        ],
        "engine_position": "占天候台架从《增删》：只看发动六亲（子孙/财=晴、父母=雨），不论旺衰、不设季节变体",
        "engine_anchor": "dev_tools/tianhou.py 裁决表（第一百八十批）；未入引擎用神层（入层须另批带书证两集出分）",
        "status": "settled_by_source",
    },
    {
        "id": "liuyao.moving_line_yingqi_priority",
        "dispute": "应期取支主位：「神兆机于动，先重动爻」总注法 vs 现行应期以用神取支为纲",
        "parties": [
            {"who": "《增删》断例", "quote": "神兆机于动，余从来不言散", "source": Z, "line": 550},
        ],
        "engine_position": "应期阶梯以用神为主（七条规则），克神/变爻/元神取支仅部分入池——与本书自证存在已登记分歧",
        "engine_anchor": "step5.calculate_yingqi 七条阶梯；#33 档案（失败形态 B 类 30%＝对支在池不在首）",
        "status": "open_conflict",
        "note": "本项是引擎与所据书的已知偏差，不是裁决完成；#33 结案判据（是否改双主位）留用户裁，不许由实现侧代劳（§四.3）。",
    },
    {
        "id": "liuyao.usegod_two_present",
        "dispute": "用神两现取舍：古法序（旺/动/不破/不空）vs 书内自记例外（应验偏在空破之爻）vs《易冒》有伤无伤键",
        "parties": [
            {"who": "古法（《增删》述）", "quote": "舍其休囚，用其旺相，舍其静爻，而用动爻，舍其月破，而用不破，舍其旬空，用其不空，舍其被伤，用其不伤。此古法也", "source": Z, "line": 1396},
            {"who": "《增删》例外自记", "quote": "得其验者，应乎旬空月破，舍其不空，而用旬空，舍其不破，而用月破", "source": Z, "line": 1396},
        ],
        "engine_position": "A 古法序为第一键并冻结（第一百七十二批：B 易冒键书注样本 4/7 反书注、C 与 A 同分无增益）；例外条款在册不实现——n=6 不足以普适（该批自注），强判反违书",
        "engine_anchor": "step2._use_god_rules；门 [26]/取舍序冻结登记见 CHANGELOG 第一百七十二批",
        "status": "frozen_by_user",
    },
    {
        "id": "liuyao.xiangfa_duan_guiqi",
        "dispute": "占父何日归：用神旺衰论断凶（古法：父母持世破而化空无生助→不能归）vs 象法断应期（野鹤自认「余不以此论之」，改断朱雀临父动持世→卯日有信、未日出空归）。书内两断法并存，野鹤明言弃古法从象",
        "parties": [
            {"who": "野鹤自认（古法结论）", "quote": "以古法断者，作用神而无气，其父不能归也", "source": Z, "line": 1014},
            {"who": "野鹤弃古法从象", "quote": "余不以此论之，竟断朱雀临父动而持世，卯日有信，午未日必归", "source": Z, "line": 1014},
            {"who": "象法应期逻辑", "quote": "应未日归者，父化未土旬空出空之日到也", "source": Z, "line": 1014},
        ],
        "engine_position": "引擎忠于用神旺衰框架（判凶与古法结论一致，wikisource WS001 verdict 维度按古法立场计分）；象法断（六神临身象＋出空应期归）属灵机应变，未机械化为通用判据（单一实案＋六神象不可量化），登记不修（第两百八十八批）",
        "engine_anchor": "scripts/step3.py（用神旺衰框架）；案例 liuyao/data/cases/wikisource_cases.json WS001",
        "status": "open_conflict",
    },
    {
        "id": "liuyao.bianyao_usegod",
        "dispute": "求财用神候选：古法变爻不作用神（伏藏妻财午飞克伏判凶）vs 野鹤灵机（兄临世爻日破月破不克变出之财＋日月俱作财来冲世→明日冲实必得）。且书内同案自认久远/目下双断（久远无财、目下必得）",
        "parties": [
            {"who": "野鹤灵机断", "quote": "兄临世爻日破月破，不克变出之财，日月俱作财来冲世，只因应爻而逢空，明日冲实，定送财来，果于次日送来", "source": Z, "line": 3043},
            {"who": "书内双断自认", "quote": "若逢久远之财有否，则无财。若问目下之财，明日戊午必得", "source": Z, "line": 3043},
        ],
        "engine_position": "引擎取用神伏藏评估（妻财午伏于亥水下飞克伏，WS040 判凶）；「变出之爻作用神」「日月冲世作财来」属灵机应变，未入用神候选规则（变爻不作用神是引擎既有通则，翻转须多实案＋总论书证，现仅单例），登记不修（第两百八十八批）",
        "engine_anchor": "scripts/step3.py resolve_fu_cang_result（伏藏评估）；案例 liuyao/data/cases/wikisource_cases.json WS040",
        "status": "open_conflict",
    },
    {
        "id": "liuyao.six_break_evidence",
        "dispute": "六破（相破对：子酉/午卯/巳申/寅亥/辰丑/戌未）计价的书证缺口：《增删卜易》三底本全文零提及「六破/相破」，《卜筮正宗》dz 整理本仅目录行出现词名（L120）、正文无论——现计价（世/用被破−0.3、他爻−0.15）无逐字书证支撑",
        "parties": [
            {"who": "库内 16 源全查唯一概念源", "quote": "休王相破资益可定吉凶也", "source": "《焦氏易传》（jingshi_yizhuan_dz.dz.txt）——汉代京房体系「休王相破」与旺衰并提，系相破概念之源，但无六爻纳甲六破计价细节", "line": 43},
            {"who": "卜筮正宗", "quote": "合局\t六冲\t六破\t六穿\t六刑", "source": "《卜筮正宗》（bushi_zhengzong_dz.dz.txt）绪论名词目录行（原文制表符分隔）", "line": 120},
        ],
        "engine_position": "保留六破计价（effects.analyze_six_breaks，step5 5.5e 消费）：外部读数实证其方向正确（第两百八十九批 A/B：撤除计价 tune strict 97.9→96.0、wikisource_holdout 70.5→69.0、holdout/direction/zengshan 持平——净退化）；书证缺口如实登记——若后批找到《卜筮正宗》正文或他源六破逐字书证，按书证重估幅度与条件（如旺衰门/久远占适用性）；在此之前不作书证洁癖式撤除，也不虚构出处",
        "engine_anchor": "scripts/effects.py:analyze_six_breaks；scripts/step5.py:615-619（5.5e 六破损伤消费）",
        "status": "open_conflict",
        "note": "《增删卜易》三底本全文检索记录与 A/B 实验数据原文见两科 CHANGELOG 第两百八十九批（检索类记录无逐字行号，不入 parties 回验面）。",
    },
    {
        "id": "liuyao.bing_use_god_dual",
        "dispute": "自占病取用双轨：问吉凶生死以世爻为用（通则句＋实案世爻亥水）vs 问愈期用药以子孙为用（用针而愈实案围绕子孙展开）——《增删》总纲两句并提，实占两例取向相反",
        "parties": [
            {"who": "总纲（自占病通例）", "quote": "占病者如自占病，若得世爻旺相或日月动爻生合世爻", "source": Z, "line": 17},
            {"who": "通则句", "quote": "自占吉凶者以世爻为用神", "source": Z, "line": 436},
            {"who": "实案（生死取向）", "quote": "自占病世爻亥水为用神", "source": Z, "line": 561},
            {"who": "实案（愈期取向）", "quote": "果于次日用针而愈。或曰：子孙化退神，何其用药亦效", "source": Z, "line": 1182},
        ],
        "engine_position": "引擎按通则句默认世爻为用（第两百九十四批自占病层：无六亲主体的纯占病→世爻，置于疾病→官鬼词典之前）；问愈期重子孙医药的变体未机械化（单一实案不可作通用判据）；E 类应期基准 WS005 na→hit 随本口径更新（check_yingqi_scoring.E_CLASS_EXPECTED，本批登记）",
        "engine_anchor": "scripts/step2.py 自占病覆盖层；dev_tools/check_yingqi_scoring.py E_CLASS_EXPECTED；案例 wikisource WS005/WS008/WS020",
        "status": "open_conflict",
        "note": "wikitext 底本对应句（行号见两科 CHANGELOG 第两百九十四批）：「自占者，宜世爻旺相……占他人以應爻爲用」「自占看世爻，旺相者非眞，代占看用神」「自占病亥水克世」（繁体原文，出处背景）。dz 底本行号：宜世爻旺相句=L1468、入墓自占看世爻句=L1330、自占病亥水克世句=L1100。",
    },
    {
        "id": "liuyao.tiantim_heri_track",
        "dispute": "占天时问「何日雨/晴」的取用轨分歧：通用六亲轨（占雨用父爻、占晴用子孙财爻）vs 何日反断轨（旺极晴神入墓之日应雨——用神收藏日为变天应期）。通用轨可机械化且引擎已实现；反断轨仅单一实案，不可作通用判据",
        "parties": [
            {"who": "通用六亲轨（总纲）", "quote": "觉子曰：占雨用父爻，占晴用子孙爻、财爻，世应何干", "source": Z, "line": 1953},
            {"who": "实案（通用轨：暗动父爻应雨日）", "quote": "卦中申金父爻暗動﹐動而逢令之日﹐果於辰日天變﹐巳日大雨", "source": "zengshan_buyi.wikitext.txt", "line": 1744},
            {"who": "实案（反断轨：旺极子孙入墓应雨）", "quote": "午火子孫臨日月旺之極矣﹐乃爲用爻重疊﹐逢墓庫以收藏﹐故知戌必雨。果於戌日申時雨", "source": "zengshan_buyi.wikitext.txt", "line": 1281},
            {"who": "实案（本日阴晴两断轨：兄爻为云先阴后晴，WSD009 占本日陰晴）", "quote": "申金兄爻爲云﹐化卯木財爻﹐是由雲霧中變出日色之象﹐果一日陰雲申時而見日色﹐次日卯時大晴", "source": "zengshan_buyi.wikitext.txt", "line": 1699},
        ],
        "engine_position": "引擎实现通用轨（第两百八十七批占雨用父母/占晴用子孙财，verdict_texts 收总纲句）；反断轨未实现（单一实案不可机械化，登记不修）。wikisource 评测 WS019/WS025/WS027/WS028 四例 category 失分系书内两轨显形的诚实代价：基准按断辞落（WS019 子孙=反断轨、其余通用轨），引擎恒走通用轨",
        "engine_anchor": "scripts/step2.py 占天时通用轨（第八十七批背景天气剥离）；verdict_texts.json 占雨占晴总纲句；案例 wikisource WS019/WS025/WS027/WS028",
        "status": "open_conflict",
        "note": "wikitext 对应行：总纲句=L1686、WS025 实案=L1744、WS019 实案=L1281（繁体原文，出处背景）。另 WS028 占何日晴书取妻财（占晴通用轨内「子孙、财爻」两用并许，L1750），引擎取子孙——同轨内两用，亦不判引擎错。",
    },
    {
        "id": "liuyao.shikao_usegod_dual",
        "dispute": "试考类取用双轨：总纲以官鬼为用（求名章），实占亦有以父母（文书/榜）为主应者。两轨各有逐字书证与实案，单案不足以改词典通用轨",
        "parties": [
            {"who": "总纲（官鬼轨）", "quote": "占功名者以官鬼爻为用神，此卦午火官星即为用神", "source": Z, "line": 456},
            {"who": "实案（官星持世轨：WSD001 占鄕試）", "quote": "斷曰﹕酉金官星持世旺相﹐當時卯日沖之而暗動", "source": "zengshan_buyi.wikitext.txt", "line": 454},
            {"who": "实案（父母文书轨：WS012 占試中否）", "quote": "未父化進神﹐巳火官動而生世﹐吉兆顯然﹐坐以待報﹐果於寅日揭榜", "source": "zengshan_buyi.wikitext.txt", "line": 645},
            {"who": "实案（官空破舍官论世轨：WS014 占升遷，官星两现一空一破）", "quote": "世爻極旺﹐旣臨日建又得月令作官星而合世﹐但卦中官星兩現﹐一空一破", "source": "zengshan_buyi.wikitext.txt", "line": 852},
        ],
        "engine_position": "引擎词典试考族→父母（第两百九十五批 WS012 书证落库）；WSD001/018 两例书取官星持世，基准按断辞落、引擎按词典走父母轨——category 失分为书内两轨显形的诚实代价（第两百九十九批归因登记）。不机械改词典：改之则伤 WS012 同族书证",
        "engine_anchor": "data/rules/question_use_gods.json 试考族；案例 wikisource WS012/WSD001/WSD018",
        "status": "open_conflict",
        "note": "wikitext 对应行：WSD001 断辞=L454、WS012 断辞=L645。dz L456 总纲同时覆盖「占鬼崇、妖蘖、乱臣、贼盗都以官鬼爻为用神」。",
    },
    {
        "id": "liuyao.huaxtui_xingren_gui",
        "dispute": "化退在行人归占的反用：通用轨以化退为衰象计凶侧，行人归占实案明言化退主归志（动破而变日月，岂可谓之退不及）——verdict 侧反用轨单实案未机械化，应期侧同书证家族的冲去忌神支已实装（第二八五批）",
        "parties": [
            {"who": "通用轨（化退=元神无力六之一）", "quote": "元神休囚动化退神三也", "source": Z, "line": 551},
            {"who": "通用轨（近占/久远分层）", "quote": "占近事岂可曰退？若占久远之事，待休囚之时而退者得也", "source": Z, "line": 1182},
            {"who": "实案反用轨（ZD050 兄何日归来）", "quote": "断曰：兄动化退，已有归志，但因戌逢月破", "source": Z, "line": 1246},
        ],
        "engine_position": "双轨均已实装：应期侧=第二八五批应期第3法③支（动忌化退克用+用神静→冲去忌神本支，书证即 parties 反用轨同源）；verdict 侧=第三百批行人归占化退归志层（+1.0 抵回用神化退衰价，检测 step4 details[].change_type，书证即 parties 归期歌诀）。zengshan 50.5→53.4 全额回补（ZD050 凶→吉复位）",
        "engine_anchor": "liuyao/scripts/step5.py 行人区 1a 支（travel_huatui_guizhi）；timing.py 应期第3法③支；案例 zengshan ZD050",
        "status": "settled",
        "note": "dz L1246 全句：「断曰：兄动化退，已有归志，但因戌逢月破，在外诸事未遂，六月可望，后至戌月方回，乃应实破之月也，此乃动破而变日月，岂可谓之退不及也？」wikitext 对应=L612。",
    },
    {
        "id": "liuyao.liunian_shiguan_dual",
        "dispute": "流年取用双轨：总纲以世爻为的（官鬼持世=灾非凶象），题面与实占意图分离时（因功名故占流年）书取官星持世轨并明确否决流年作鬼断——占遠應近框架的流年支",
        "parties": [
            {"who": "总纲（流年世爻轨）", "quote": "若遇官鬼持世，得日月动爻作财星生合世爻者，必见灾非", "source": Z, "line": 12},
            {"who": "占遠應近总纲（题面分离）", "quote": "有为婚姻故，占月令者。因功名，故占流年", "source": Z, "line": 1855},
            {"who": "实案反用轨（WS021 占流年·援例功名）", "quote": "占功名，以官为官，最喜官星持世。占流年以官为鬼，不宜官鬼持世", "source": Z, "line": 1862},
        ],
        "engine_position": "引擎判类「流年」→世爻轨（通用轨正确）；WS021 expected 按断辞落官鬼@寅（书以官星持世断援例成败），category 失分为书内双轨显形的诚实代价。dz L1855 占遠應近章是题面分离的总纲（婚姻故占月令/功名故占流年/现任官府故占在任），与第二八一批 WS022 登记同框架——题面意图分离的组合条件待框架批，不为本案开私有分支",
        "engine_anchor": "data/rules/question_classes.json 流年类；step2 用神选取世爻轨；案例 wikisource WS021",
        "status": "open_conflict",
        "note": "dz L1862 全句尾：「若以流年作鬼断者，如天远矣。」wikitext 对应=L1554、L1545。",
    },
    {
        "id": "liuyao.shijian_tiying_verdict_dual",
        "dispute": "时间题（何时来/何日到）的 verdict 口径双轨：书以应验为吉（果至/果到即记吉），且问「来否」时书明言不按平安断；引擎 verdict 走用神旺衰吉凶轨（用神受制记凶）——两轨对同一卦给反向结论",
        "parties": [
            {"who": "实案（应验吉轨：WSD003 占母路隔千里何时来，父母不来而妹至）", "quote": "父母必不來﹐兄弟必來。彼曰﹕有妹無弟。果於次年三月妹至﹐此乃兄弟化空﹐爻空亦能退也", "source": "zengshan_buyi.wikitext.txt", "line": 656},
            {"who": "实案（问题转换轨：WSD024 占母在外何时来，野鹤明言不按平安断）", "quote": "此卦若问父母平安否，父母卯木日月动爻冲克，必不安矣。今问其来否，不以此断，只可断用神伏藏也，克而不来，六合冲亦不来，后果在外平安", "source": Z, "line": 3306},
            {"who": "实案（归期克世反吉轨：WSD025 占父远去何日回）", "quote": "断曰：今日乃是午日，午火父爻克世爻，今日必到。果于申时到", "source": Z, "line": 3330},
            {"who": "反例轨（书自认凶：WS001 占父何日归）", "quote": "竟断朱雀临父动而持世，卯日有信，午未日必归", "source": Z, "line": 1014},
            {"who": "一卦两事轨（WSD008 占母病：题面母病六冲即愈记吉，现卦子孫變鬼另报子灾）", "quote": "此卦不現母病﹐而現子女有災", "source": "zengshan_buyi.wikitext.txt", "line": 1611},
        ],
        "engine_position": "引擎 verdict 按用神旺衰+吉凶化轨（第两百六十四批体系）；「应验即吉」「问来否不按平安断」「归期用神克世反吉」三支时间题口径未机械化（条件组合属框架批：须先识别时间题类+书内应验句式，单一实案族不足以定通用判据）。wikisource WSD003 verdict 失分=口径双轨显形的诚实代价；WSD024/025 引擎读数与书答同向（基准吉、引擎吉侧）不受影响；WSD008 题面母病轨吉（六冲即愈）与现卦子灾轨凶并现，verdict 反向为一卦两事双轨显形",
        "engine_anchor": "scripts/step5.py verdict 化轨；案例 wikisource WSD003/WSD024/WSD025",
        "status": "open_conflict",
        "note": "WS001 案（dz L1014）已有专条 xiangfa_duan_guiqi 登记，本条引其反例面：并非所有归期题都记应验吉，书自认不能归者仍以凶断——双轨边界在书内自述。",
    },
    {
        "id": "liuyao.direction_usegod_dual",
        "dispute": "出行/方向题取用双轨：总纲自占吉凶以世爻为用；南行实案以应爻官星动而生世为断主体（官贵相生论吉凶）——方向题的断对象是「行程吉凶」还是「生我之源」",
        "parties": [
            {"who": "总纲（自占吉凶世爻轨）", "quote": "自占吉凶者以世爻为用神", "source": Z, "line": 436},
            {"who": "实案（应爻官星生世轨：WSD006 予占南行）", "quote": "予以應爻爲官星動而生世﹐官貴相生者﹐𨿽則可喜", "source": "zengshan_buyi.wikitext.txt", "line": 1393},
        ],
        "engine_position": "引擎判类「出行/南行」→世爻轨（总纲正确）；WSD006 expected 按断辞落官鬼@巳（书以应爻官星为断主体），category/branch 失分为书内双轨显形的诚实代价。不机械化：改词典则伤 WSD019（住京都占地方）等世爻轨同 split 书证",
        "engine_anchor": "data/rules/question_use_gods.json 出行族；step2 用神选取世爻轨；案例 wikisource WSD006/WSD019",
        "status": "open_conflict",
        "note": "wikitext L1393 全句续：「但嫌巳火墓於戌月而又化墓﹐生我之官爻卽又入墓耶﹐兼且又是六沖﹐疑爲不吉。」——官星入墓+六冲论行程疑虑，断对象全程是官星非世爻。",
    },
    {
        "id": "liuyao.douqin_zisun_track",
        "dispute": "斗类娱乐题取用双轨：斗殴打架以兄弟（对手）为用，斗禽斗蟋蟀书以子孙持世为我方禽畜、父爻动为敌禽（父母克子孙=彼伤我）——同「斗」字两轨",
        "parties": [
            {"who": "实案（斗禽轨：WSD023 占鵪鶉）", "quote": "子孫持世以臨日辰﹐父爻𨿽動﹐亥水制之﹐獨不宜亥爲月破﹐𨿽可制火﹐今日巳午時切不可斗", "source": "zengshan_buyi.wikitext.txt", "line": 3616},
        ],
        "engine_position": "引擎判类无斗禽轨（「斗」未入用神词典），占鵪鶉落泛问轨→category 失分；不机械化：斗禽娱乐题库内仅此一实案，且斗殴族书证（兄弟为对手）与斗禽轨（子孙为我方）语义相反，误并则两伤",
        "engine_anchor": "data/rules/question_use_gods.json；案例 wikisource WSD023",
        "status": "open_conflict",
        "note": "书内应期轨亦特殊：父爻得令之时（巳午时）不可斗——应期取忌神当令时段，非寻常用神受制应凶轨。",
    },
    {
        "id": "liuyao.youshen_guan_track",
        "dispute": "忧神轨：占六亲病书以官鬼持世为「忧」（忧去即愈，官鬼非病之用神而是心忧之象）——与常轨「官鬼为疾病类用神/忌神」语义相反，且觉子自划边界（占自身兄弟妻儿此法是也，父母妻夫不宜）",
        "parties": [
            {"who": "实案（忧神轨：WSD027 占子病）", "quote": "官鬼持世﹐憂也﹐今日子日沖去憂心﹐管許立愈﹐果於本日愈", "source": "zengshan_buyi.wikitext.txt", "line": 3981},
            {"who": "轨边界（觉子曰自注）", "quote": "如占自身及兄弟妻兒者﹐此法是也﹐若占父母之災﹐官鬼爲父母之元神﹐豈宜子動而傷耶", "source": "zengshan_buyi.wikitext.txt", "line": 3981},
        ],
        "engine_position": "引擎占病走用神旺衰轨（占子孙病取子孙），官鬼持世记忌神持世凶侧→WSD027 verdict 反向；不机械化：忧神轨须先识别「忧象断」与「病象断」的题面分歧，库内单实案不足定通用判据；觉子边界注（占父母/妻夫不宜）本身即书内自认的适用域限制",
    {
        "id": "liuyao.liuchong_bianhe_track",
        "dispute": "六冲变合轨：六冲主散（常轨），但六冲卦变六合书内明示通则级例外——不看用神竟以吉断（散而复聚）",
        "parties": [
            {"who": "例外轨（书内通则自注）", "quote": "诸合皆以用神旺者为吉，独此六冲卦变六合得不看用神，竟以吉断。", "source": "zengshan_buyi_dz.dz.txt", "line": 756},
            {"who": "常轨（六冲主散）", "quote": "予屡试之，旺相者冲之不散", "source": "zengshan_buyi_dz.dz.txt", "line": 844},
        ],
        "engine_position": "引擎六冲主散按用神旺衰门计价（第二八七/二九八批），变六合化散为聚的例外轨未入判据（卦变六合形态识别缺载）——ZD023 verdict 引擎侧无从命中；不机械化：例外轨书证为通则自注+单实案，须先补「六冲变合」卦形识别与散聚语义层框架批",
        "engine_anchor": "scripts/step4.py _detect_hexagram_harmony_clash_pattern（六冲主散）；scripts/step5.py hex_adjustment（六冲卦性门）",
        "status": "open_conflict",
        "note": "ZD023（占婚悔而复成）use_god 基准因此留空——书断不取用神（dz L756），引擎 use_god 维度对该例不评属预期。",
    },
    {
        "id": "liuyao.xiaofu_track_liunian",
        "dispute": "流年孝服轨：占在任/流年问自身，书以世爻财断自身平安之外，另以父母受克断孝服（丁艰）——流年吉凶定性取诸亲受克叠加，非单看世爻",
        "parties": [
            {"who": "实案（ZD151 占在任平安）", "quote": "财休囚得午火生之，自身不妨，须防孝服", "source": "zengshan_buyi_dz.dz.txt", "line": 2900},
            {"who": "孝服机理（同案）", "quote": "午日冲动子水，父母被戌土财爻克，世化官空，八九月必见，果于八月丁艰。", "source": "zengshan_buyi_dz.dz.txt", "line": 2900},
        ],
        "engine_position": "引擎流年轨按世爻旺衰断自身（平吉），父母受克辅断孝服并升格整体凶定性未入判据——ZD151 verdict 平吉/书凶方向相反；不机械化：孝服轨需「流年定性=世爻自身+诸亲受克事件加权」的框架批，库内单实案",
        "engine_anchor": "scripts/step5.py verdict 化轨（流年世体）；案例 zengshan ZD151",
        "status": "open_conflict",
        "note": "与 youshen_guan_track 同族：流年/忧问的凶定性常不在世爻自身而在六亲事件（孝服/忧去），verdict 维度对这类案例的 miss 属框架显形。",
    },
]


def verify_entries(entries) -> list[str]:
    src_lines = SRC.read_text(encoding="utf-8").splitlines()
    # 跨书书证按 parties[].source 括号内文件名路由到对应底本回验（第二九四批）：
    # 裁决表允许多方书证来自库内不同底本（焦氏易传/卜筮正宗等），单一 SRC 机制
    # 会把别书逐字引文误判为不命中。source 缺文件名时默认 SRC（增删 dz）。
    lines_cache = {SRC.name: src_lines}
    bad = []
    for e in entries:
        for q in e["parties"]:
            src_name = SRC.name
            m = re.search(r"([A-Za-z_]+\.[a-z]+\.txt)", str(q.get("source", "")))
            if m:
                cand = DISC / "data" / "sources" / m.group(1)
                if cand.exists():
                    src_name = m.group(1)
                    if src_name not in lines_cache:
                        lines_cache[src_name] = cand.read_text(encoding="utf-8").splitlines()
            lines = lines_cache[src_name]
            ln = lines[q["line"] - 1] if 0 < q["line"] <= len(lines) else ""
            if q["quote"] not in ln:
                bad.append("%s: 书证非该 L%d 行逐字子串（%s…）" % (e["id"], q["line"], q["quote"][:24]))
    return bad


def cmd_build() -> int:
    bad = verify_entries(ENTRIES)
    if bad:
        print("× 书证逐字回验未过，拒绝落盘：")
        for b in bad:
            print("  · " + b)
        return 1
    doc = {"schema": "yi-liuyao-adjudications/1", "discipline": "liuyao",
           "built_at": datetime.now().isoformat(timespec="seconds"),
           "_comment": "流派裁决表：「与古书吻合」的展开定义。引用任何吻合率须能指回本表行。"
                       "不改引擎不进评分面不挂门（§176 冻结声明）。状态三值见 builder docstring。",
           "count": len(ENTRIES),
           "entries": ENTRIES}
    write_stable(OUT, doc)
    print("√ 裁决表落成 %s｜%d 项分歧点（settled %d／frozen %d／open %d），书证 %d 条全部逐字回验过"
          % (OUT.name, len(ENTRIES),
             sum(1 for e in ENTRIES if e["status"] == "settled_by_source"),
             sum(1 for e in ENTRIES if e["status"] == "frozen_by_user"),
             sum(1 for e in ENTRIES if e["status"] == "open_conflict"),
             sum(len(e["parties"]) for e in ENTRIES)))
    return 0


def cmd_verify() -> int:
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    bad = verify_entries(doc["entries"])
    for b in bad:
        print("  · " + b)
    print("√ 在册裁决表 %d 项书证全部可回指原书行" % len(doc["entries"]) if not bad
          else "× 回验未过 %d 条" % len(bad))
    return 0 if not bad else 1


def cmd_selftest() -> int:
    fails = []
    n = len(verify_entries(ENTRIES))
    if n:
        fails.append("正书证回验本应全过，实报 %d 条问题" % n)
    tampered = [dict(ENTRIES[0], parties=[dict(ENTRIES[0]["parties"][0], quote="旬空之法诸书不论")] )]
    if not verify_entries(tampered):
        fails.append("篡改书证未被识破（回验是摆设）")
    shift = [dict(ENTRIES[1], parties=[dict(ENTRIES[1]["parties"][0], line=1)])]
    if not verify_entries(shift):
        fails.append("行号挪移未被识破")
    ids = [e["id"] for e in ENTRIES]
    if len(ids) != len(set(ids)):
        fails.append("裁决项 id 重复")
    if not any(e["status"] == "open_conflict" for e in ENTRIES):
        fails.append("open_conflict 被清零——不许把未决粉饰为已裁")
    print("√ selftest：正验全过/篡改拒/行号挪移拒/id 唯一/未决项保留 全过" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="流派裁决表构建器（B2，逐字书证回验后落盘）")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    if args.verify:
        return cmd_verify()
    return cmd_build()


if __name__ == "__main__":
    raise SystemExit(main())
