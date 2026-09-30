# -*- coding: utf-8 -*-
"""生成问题词典 `data/rules/question_use_gods.json`；带引文的族必须逐字命中原文。

    python tools/build_question_use_gods.py             # 生成 JSON
    python tools/build_question_use_gods.py --check     # 只复验已生成 JSON 的引文是否仍逐字命中

背景（对应 HANDOFF 四·2「还剩词典层」）：
  `_QUESTION_USE_GOD_MAP` 的 186 键原先以 Python 字面量埋在 scripts/chain_tables.py 里，
  没出处、没分层，`use_god_coverage.py` 也分不清"有据/词典猜"。本工具把它按**事项族**
  结构化进 data/：每族给 label + basis（citation＝原书逐字引文，locate 得到原文偏移；
  inference＝诚实标注"无逐条出处"的取舍理由），另有 references（核得中的相关原文位置）
  与 layer_citations（chain_step2 覆盖层展示用引文）。**引文逐字对不上原文就不出表**
  ——写错出处比没出处更坏（同 build_use_god_rules.py 的铁则）。

为什么 entries 顺序必须原样保留：
  打分层同分 tie-break 用 `category_first_pos`（关系首次出现位置），而关系首次出现
  位置依赖词典插入顺序——重排 entries 会静默改变取用神结果。JSON 里保序，_meta 写明。

与 build_use_god_rules.py 共用 locate/flat：口径必须一致（去 <br> 后的文本上定偏移、
忽略标点、文件侧 爲→為 归一）。**本文件所有引文一律写 為（不写 爲）**，否则 quote
侧不归一会匹配失败。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
RAW = DISC.parent.parent / "data" / "sources" / "zengshan_buyi.wikitext.txt"
OUT = DISC / "data" / "rules" / "question_use_gods.json"

sys.path.insert(0, str(HERE))
from build_use_god_rules import flat, locate  # noqa: E402  同一口径的引文定位

# 事项族：顺序＝条目顺序＝原 chain_tables 字面量的插入顺序，禁止重排/增删。
# 每族 basis 适用于全族条目；label 与 note 是给人看的取舍依据（note 不参与核验）。
# refs：相关原文位置（同样 locate 核验，但不是"该族取用"的主张，只是给读者的回查点）。
FAMILIES = [
    {"label": "自测·自身（世爻）", "god": "世爻",
     "basis": {"kind": "inference",
               "reason": "自占以世爻为己身；泛问吉凶原书无逐条取用，按世为自身引申"},
     "entries": ["自测吉凶", "自身"]},

    {"label": "尊长六亲（父母·父亲·母亲·长辈）", "god": "父母",
     "basis": {"kind": "citation", "quote": "子占父病，父爻為用神"},
     "note": "与关系法则层 p20 同引文；句中出现单字父/母/爹/娘时法则层先命中，词典多在精确类别匹配时兜底",
     "entries": ["父母", "父亲", "母亲", "长辈"]},

    {"label": "文书·考试·学业（以文书为体）", "god": "父母",
     "basis": {"kind": "citation", "quote": "以父母爻為用神，此卦六爻無父母巳火"},
     "note": "原书占文书断例；考试学业问以文书案卷为体，同族承接（非考试逐条原文）",
     "entries": ["文书", "考试", "学业"]},

    {"label": "房产·房屋", "god": "父母",
     "basis": {"kind": "citation", "quote": "父旺持世，此處淸安宜久住"},
     "note": "与关系法则层『宅/房/屋→父母』同引文（家宅住居以父母论）",
     "entries": ["房产", "房屋"]},

    {"label": "合同·证书·车辆", "god": "父母",
     "basis": {"kind": "inference",
               "reason": "父母主文书契据车船：合同证书归文书族，车辆按六亲类象——原书无现代契据逐条"},
     "entries": ["合同", "证书", "车辆"]},

    {"label": "事业·工作（现代职业）", "god": "官鬼",
     "basis": {"kind": "inference",
               "reason": "现代职业问法；按官鬼主功名职守归族，原书逐条只到占官差/功名（见后族引文）"},
     "entries": ["事业", "工作"]},

    {"label": "功名·求官·官职·升迁", "god": "官鬼",
     "basis": {"kind": "citation",
               "quote": "今以自占功名，子動而克官也，如何反為用﹖非也，仍看官爻"},
     "note": "原书驳『子动反为用』，断功名仍看官爻；覆盖层『功名→官鬼』同本条引文。文本含『功名』时覆盖层先手，本族实际承接求官/官职/升迁",
     "entries": ["功名", "求官", "官职", "升迁"]},

    {"label": "丈夫（女测）", "god": "官鬼",
     "basis": {"kind": "citation", "quote": "女家占男，皆以官為用"},
     "note": "婚姻章第八十二：女家占男以官，妻子占丈夫同理；句中含『夫/婿』时关系法则层 p20 先命中",
     "entries": ["丈夫", "丈夫运势"]},

    {"label": "男测妻子", "god": "妻财",
     "basis": {"kind": "citation", "quote": "男人自占妻者，亦以財爻為用神"},
     "entries": ["男测妻子"]},

    {"label": "感情·喜欢·女友·恋人·伴侣（现代恋爱）", "god": "妻财",
     "basis": {"kind": "inference",
               "reason": "现代恋爱问法，按男测女看妻财引申；词典不辨提问者性别——女测男会被归到妻财，已知局限，改动须重跑三集"},
     "entries": ["感情", "喜欢", "女友", "恋人", "伴侣"]},

    {"label": "疾病（泛问）", "god": "官鬼",
     "basis": {"kind": "inference",
               "reason": "官鬼为病之象，泛问疾病以官鬼承接；自占病/亲人病/医药各有带引文的法则与覆盖层，词典只兜无身份的泛问"},
     "entries": ["疾病"]},

    {"label": "官司·诉讼·法律·纠纷（现代司法）", "god": "官鬼",
     "basis": {"kind": "inference",
               "reason": "现代司法问法；原书讼事以世应论胜负、官鬼文书并看，词典把『官方之象』归官鬼——属引申，无逐条取用明文"},
     "refs": ["占訟事，世旺者得理", "官父同興公庭有理"],
     "entries": ["官司", "官司诉讼", "诉讼", "法律", "纠纷"]},

    {"label": "小偷·强盗·小人·灾难·仇人", "god": "官鬼",
     "basis": {"kind": "inference",
               "reason": "官鬼为灾殃小人之象，词典按类象归族（原书无逐条取用）"},
     "entries": ["小偷", "强盗", "小人", "灾难", "仇人"]},

    {"label": "调动·辞职·面试·招聘·编制·公务员（现代求职）", "god": "官鬼",
     "basis": {"kind": "inference",
               "reason": "现代求职/任免问法，按官鬼主功名职守引申"},
     "refs": ["占官差以官鬼為用"],
     "entries": ["调动", "辞职", "面试", "招聘", "编制", "公务员"]},

    {"label": "公司·上市（现代）", "god": "官鬼",
     "basis": {"kind": "inference",
               "reason": "现代组织/资本市场问法，原书无对应；词典按名分职权归官鬼——历史默认，取舍存疑，待三集验收后单独评估"},
     "entries": ["公司", "上市"]},

    {"label": "官（单字弱键）", "god": "官鬼",
     "basis": {"kind": "inference",
               "reason": "单字键：官为官鬼之省，子串匹配易误伤；『见贵求财』等歧义已在覆盖层先手处理，保留仅为零漂移"},
     "entries": ["官"]},

    {"label": "职位（现代）", "god": "官鬼",
     "basis": {"kind": "inference",
               "reason": "现代职位问法，按官鬼主职守引申（同求职族）"},
     "entries": ["职位"]},

    {"label": "占病·病症·近病·久病·病何·病愈", "god": "官鬼",
     "basis": {"kind": "inference",
               "reason": "泛问病字词典归官鬼（以病爻为对象）；『久病』文本被覆盖层取世爻、『自占病/自身病』先由法则层取世爻、医药先由法则层取子孙——本族只兜最泛的病问"},
     "refs": ["自占病，世為用神"],
     "entries": ["占病", "病症", "近病", "久病", "病何", "病愈"]},

    {"label": "兄弟·姐妹", "god": "兄弟",
     "basis": {"kind": "citation", "quote": "凡占兄弟，須宜問明"},
     "refs": ["兄弟爻旺相遇生扶，紫荊並茂"],
     "note": "兄弟章第四十二开篇『凡占兄弟』，全章以兄弟爻断",
     "entries": ["兄弟", "姐妹"]},

    {"label": "朋友·同事", "god": "兄弟",
     "basis": {"kind": "inference",
               "reason": "同辈朋侪按兄弟类象归族；关系法则层对『朋友/同辈』用用神章总纲引文（见 use_god_relations）"},
     "refs": ["占父母弟兄取用神者皆在用神章內詳之"],
     "entries": ["朋友", "同事"]},

    {"label": "竞争·竞争对手", "god": "兄弟",
     "basis": {"kind": "inference",
               "reason": "同行竞争按同辈类象归兄弟；原书争竞争实以世应论胜负——词典取法与原书断法不同，取舍存疑，改动须重跑三集"},
     "refs": ["彼此相爭尋世應"],
     "entries": ["竞争", "竞争对手"]},

    {"label": "求财·财运", "god": "妻财",
     "basis": {"kind": "citation", "quote": "公私占卜皆以財為用神"},
     "note": "求財章第六十八",
     "entries": ["求财", "财运"]},

    {"label": "妻子（男测）", "god": "妻财",
     "basis": {"kind": "citation", "quote": "男人自占妻者，亦以財爻為用神"},
     "entries": ["妻子"]},

    {"label": "婚姻·婚（男家视角）", "god": "妻财",
     "basis": {"kind": "citation", "quote": "男家占女，不拘父母親朋而代占者，無不以財為用"},
     "note": "婚姻章第八十二：男家占女以财、女家占男以官。词典不辨性别，女测文本无『女家/女占』等词时会落到本条——已知局限（法则层 p10 先手时不受影响）",
     "entries": ["婚姻", "婚"]},

    {"label": "妻·老婆·夫人·生病妻（男测）", "god": "妻财",
     "basis": {"kind": "citation", "quote": "男人自占妻者，亦以財爻為用神"},
     "entries": ["妻", "生病妻", "老婆", "夫人"]},

    {"label": "营谋交易（生意→银）", "god": "妻财",
     "basis": {"kind": "citation", "quote": "上至國計，下至營謀，無不以財為用"},
     "note": "求財章第六十八：营谋皆以财为用；现代经营词（项目/产品/融资…）按营谋族承接；财/钱/富/银 等单字弱键子串易误伤（矩阵标 ⚠）",
     "entries": ["生意", "投资", "货物", "钱财", "赚钱", "财", "富", "钱", "项目", "产品",
                 "融资", "创业", "合伙", "股份", "分红", "经营", "市场", "经济", "贸易",
                 "买卖", "交易", "银"]},

    {"label": "失物（失·丢·找回）", "god": "妻财",
     "basis": {"kind": "inference",
               "reason": "失物以所失财物为体归妻财（类象引申）；原书无失物逐条取用——此族曾出过『找回→父母』的错配，按无据明示，不再挂靠无关引文"},
     "entries": ["失", "丢", "失物", "找回"]},

    {"label": "僕·奴·婢·员工（雇属）", "god": "妻财",
     "basis": {"kind": "citation", "quote": "占配僕，以財爻為用"},
     "refs": ["斷卦者若執奴僕為財，則遷矣"],
     "note": "纳宠章第八十五：占配僕以财爻为用；原书另有告诫『執奴僕為財，則遷矣』——占僕人为祸/变心时另看忌神，词典只管雇属吉凶类问法",
     "entries": ["仆", "奴", "婢", "员工"]},

    {"label": "赌·赌钱·博", "god": "妻财",
     "basis": {"kind": "inference",
               "reason": "所逐者利，词典按妻财承接；原书博戏世应为先、胜以得财者兼用财——词典整归妻财是简化，取舍存疑"},
     "refs": ["有技力，首重世應，若勝以得財者，兼用財"],
     "entries": ["赌", "赌钱", "博"]},

    {"label": "健康（现代）", "god": "官鬼",
     "basis": {"kind": "inference",
               "reason": "现代健康问法，与疾病同族归官鬼（词典默认）"},
     "entries": ["健康"]},

    {"label": "出行·旅游·行人（旅途）", "god": "子孙",
     "basis": {"kind": "inference",
               "reason": "词典原值子孙（行人类象）；含『出行/行人』的文本实际被覆盖层先取世爻——本族多为被遮蔽条目，保留仅为零漂移"},
     "refs": ["世為出行人"],
     "entries": ["出行", "旅游", "旅行", "出行类", "行人", "行旅"]},

    {"label": "归·归来·何日·何时（弱时间键）", "god": "子孙",
     "basis": {"kind": "inference",
               "reason": "弱键：归期类词参与打分只微调同分 tie-break，不单独定族；词典归子孙是历史默认——取舍存疑"},
     "refs": ["用神動而克世，行人回來之速也"],
     "entries": ["归", "归来", "何日", "何时"]},

    {"label": "家·宅·搬家", "god": "父母",
     "basis": {"kind": "citation", "quote": "父旺持世，此處淸安宜久住"},
     "note": "与关系法则层『宅/房/屋→父母』同引文",
     "entries": ["家", "宅", "搬家"]},

    {"label": "父系母系尊长（父·母·爷·奶·岳父母·爸妈爹娘）", "god": "父母",
     "basis": {"kind": "citation", "quote": "子占父病，父爻為用神"},
     "note": "与关系法则层 p20 同引文：句中含单字父/母/爹/娘时法则层先命中",
     "entries": ["父", "母", "爷", "奶", "岳父", "岳母", "爸", "妈", "爹", "娘"]},

    {"label": "师长·老师·师傅·师尊", "god": "父母",
     "basis": {"kind": "citation", "quote": "父入墓中，懶於教訓"},
     "refs": ["世若休囚，必受師尊之累"],
     "note": "延師章第四十七通篇以父爻论师教：父爻入墓即『懶於教訓』，故师长归父母",
     "entries": ["师长", "老师", "师傅", "师尊"]},

    {"label": "书（单字弱键）", "god": "父母",
     "basis": {"kind": "inference",
               "reason": "单字键：书为文书之省，子串匹配易误伤，保留仅为零漂移"},
     "entries": ["书"]},

    {"label": "子女·孩子·儿子·女儿", "god": "子孙",
     "basis": {"kind": "citation", "quote": "如占子孫，取子孫為用神"},
     "note": "用神章（法则层 p20 同引文）",
     "entries": ["子女", "孩子", "儿子", "女儿"]},

    {"label": "医生·医药", "god": "子孙",
     "basis": {"kind": "citation", "quote": "占藥占醫又以子孫為用神"},
     "note": "延醫章第一百零三（法则层 p30 同引文）",
     "entries": ["医生", "医药"]},

    {"label": "宠物", "god": "子孙",
     "basis": {"kind": "citation", "quote": "不拘家禽野獸皆以子孫為用神"},
     "note": "買賣六畜章第七十九（法则层『六畜/牲口』同族）",
     "entries": ["宠物"]},

    {"label": "娱乐", "god": "子孙",
     "basis": {"kind": "inference",
               "reason": "子孙为喜悦之象，娱乐按类象归族（原书无逐条）"},
     "refs": ["子孫乃喜悅之神"],
     "entries": ["娱乐"]},

    {"label": "儿童·孙子", "god": "子孙",
     "basis": {"kind": "citation", "quote": "如占子孫，取子孫為用神"},
     "entries": ["儿童", "孙子"]},

    {"label": "怀孕", "god": "子孙",
     "basis": {"kind": "citation", "quote": "各宜分占，親占代占，皆用子孫"},
     "note": "胎孕章第八十七（法则层 p15『胎/孕』同引文）",
     "entries": ["怀孕"]},

    {"label": "功名考试（被覆盖层遮蔽的复合键）", "god": "官鬼",
     "basis": {"kind": "citation",
               "quote": "今以自占功名，子動而克官也，如何反為用﹖非也，仍看官爻"},
     "note": "键内含『功名』与『考试』，实际文本必先被覆盖层接走（功名→官鬼 / 科举考试→父母），词典值保留仅为零漂移",
     "entries": ["功名考试"]},

    {"label": "桑叶·桑·叶·蚕", "god": "妻财",
     "basis": {"kind": "inference",
               "reason": "蚕桑之利按妻财承接；原书无桑蚕专条（检索『蠶/桑葉』无命中）——类象引申，取舍存疑"},
     "entries": ["桑叶", "桑", "叶", "蚕"]},

    {"label": "价格·贵贱·价·贱·大例·大数", "god": "妻财",
     "basis": {"kind": "citation", "quote": "財化進神不可收積，化退者，其價將落"},
     "note": "囤貨賣貨章第七十三以财爻论物价；『大例/大数』原书未见，是历史遗留键，保留待单独评估",
     "entries": ["价", "价格", "贵贱", "大例", "大数", "价贵", "价贱", "贱"]},

    {"label": "见贵·贵·见官·贵客·贵用", "god": "官鬼",
     "basis": {"kind": "citation", "quote": "見貴有兩間也，為名者用官，為利者用財"},
     "note": "謁貴求財章第六十九：为名用官、为利用财；词典见贵键按求名视角归官鬼，覆盖层『见贵求财→官鬼』同族引文",
     "entries": ["见贵", "贵", "见官", "贵客", "贵用"]},

    {"label": "占师尊", "god": "父母",
     "basis": {"kind": "citation", "quote": "父入墓中，懶於教訓"},
     "note": "延師章第四十七（同师长族）",
     "entries": ["占师尊"]},

    {"label": "占父·占母", "god": "父母",
     "basis": {"kind": "citation", "quote": "子占父病，父爻為用神"},
     "entries": ["占父", "占母"]},

    {"label": "占妻·占妾", "god": "妻财",
     "basis": {"kind": "citation", "quote": "男人自占妻者，亦以財爻為用神"},
     "entries": ["占妻", "占妾"]},

    {"label": "占子·占女（指儿女）", "god": "子孙",
     "basis": {"kind": "citation", "quote": "如占子孫，取子孫為用神"},
     "note": "指占儿女；婚嫁代占另有法则层 p10（男家占女→妻财）先手",
     "entries": ["占子", "占女"]},

    {"label": "占兄弟", "god": "兄弟",
     "basis": {"kind": "citation", "quote": "凡占兄弟，須宜問明"},
     "entries": ["占兄弟"]},

    {"label": "占友", "god": "兄弟",
     "basis": {"kind": "inference",
               "reason": "同辈朋侪按兄弟类象归族（同朋友族）"},
     "entries": ["占友"]},

    {"label": "妻病", "god": "妻财",
     "basis": {"kind": "citation", "quote": "男人自占妻者，亦以財爻為用神"},
     "note": "占妻之病以妻爻为用（占其人以六亲本爻）",
     "entries": ["妻病"]},

    {"label": "子病", "god": "子孙",
     "basis": {"kind": "citation", "quote": "如占子孫，取子孫為用神"},
     "note": "覆盖层『占子病→子孙』同族",
     "entries": ["子病"]},

    {"label": "父病", "god": "父母",
     "basis": {"kind": "citation", "quote": "子占父病，父爻為用神"},
     "entries": ["父病"]},

    {"label": "兄病", "god": "兄弟",
     "basis": {"kind": "citation", "quote": "凡占兄弟，須宜問明"},
     "note": "兄弟章全章以兄弟爻断",
     "entries": ["兄病"]},

    {"label": "自占（泛）", "god": "世爻",
     "basis": {"kind": "inference",
               "reason": "自占以世爻为己身（同自测族）；句中含『自占+病/流年』等时关系法则层 p40 先手"},
     "entries": ["自占"]},

    {"label": "自占妻·自占婚", "god": "妻财",
     "basis": {"kind": "citation", "quote": "男人自占妻者，亦以財爻為用神"},
     "entries": ["自占妻", "自占婚"]},

    {"label": "自占官", "god": "官鬼",
     "basis": {"kind": "citation",
               "quote": "今以自占功名，子動而克官也，如何反為用﹖非也，仍看官爻"},
     "entries": ["自占官"]},

    {"label": "自占病", "god": "世爻",
     "basis": {"kind": "citation", "quote": "自占病，世為用神"},
     "note": "疾病章第九十九（法则层 p15/p40 同引文）",
     "entries": ["自占病"]},

    {"label": "自占学业", "god": "父母",
     "basis": {"kind": "citation", "quote": "以父母爻為用神，此卦六爻無父母巳火"},
     "note": "学业以文书为体（同文书族引文）",
     "entries": ["自占学业"]},

    {"label": "占婚·占嫁·占娶（男家视角）", "god": "妻财",
     "basis": {"kind": "citation", "quote": "男家占女，不拘父母親朋而代占者，無不以財為用"},
     "note": "婚姻章第八十二男家视角；女测文本由法则层 p10 先手（无性别词时会落到本条——已知局限）",
     "entries": ["占婚", "占嫁", "占娶"]},

    {"label": "逃仆", "god": "妻财",
     "basis": {"kind": "inference",
               "reason": "僕逃按雇属之财为用（类象引申）；原书『占配僕以財爻為用』只管配仆，逃亡无逐条"},
     "refs": ["占配僕，以財爻為用"],
     "entries": ["逃仆"]},

    {"label": "走失·逃亡", "god": "妻财",
     "basis": {"kind": "inference",
               "reason": "按所失之财物归妻财（类象引申）；原书无走失/逃亡取用明文"},
     "entries": ["走失", "逃亡"]},
]

# chain_step2 覆盖层（代码消歧层）展示用引文：同样逐字核验后入表。
LAYER_CITATIONS = {
    "出行": "世為出行人",          # 出行章第九十一：世为出行人 → 覆盖层『出行/行人→世爻』
    "功名": "今以自占功名，子動而克官也，如何反為用﹖非也，仍看官爻",
    "见贵": "見貴有兩間也，為名者用官，為利者用財",
    "占子": "如占子孫，取子孫為用神",
    "胎孕": "各宜分占，親占代占，皆用子孫",
    "自占病": "自占病，世為用神",
    "文书": "以父母爻為用神，此卦六爻無父母巳火",
}

EXPECTED_KEYS = 186   # 与原 chain_tables 字面量的有效键数一致（搬移验收基线）


def resolve(families: list[dict]) -> tuple[list[dict], list[str]]:
    """把引文换成 {citation, offset}；找不到的进 missing（缺失即不出表）。"""
    missing: list[str] = []
    out: list[dict] = []
    for fam in families:
        f = {"label": fam["label"], "basis": dict(fam["basis"]),
             "entries": [{"k": k, "v": fam["god"]} for k in fam["entries"]]}
        if fam.get("note"):
            f["note"] = fam["note"]
        b = f["basis"]
        if b.get("kind") == "citation":
            q = b.pop("quote", "")
            off, verbatim = locate(flat(), q)
            if off < 0:
                missing.append(f"[{fam['label']}] {q}")
            else:
                b["citation"] = re.sub(r"<br>|\s+", "", verbatim)
                b["offset"] = off
        if fam.get("refs"):
            resolved = []
            for q in fam["refs"]:
                off, verbatim = locate(flat(), q)
                if off < 0:
                    missing.append(f"[{fam['label']}·ref] {q}")
                else:
                    resolved.append({"citation": re.sub(r"<br>|\s+", "", verbatim),
                                     "offset": off})
            f["refs"] = resolved
        out.append(f)
    return out, missing


def main() -> int:
    from yishu_core.runtime import force_utf8_stdio  # noqa: PLC0415
    for module in (str(DISC / "scripts"), str(DISC.parents[1] / "core")):
        if module not in sys.path:
            sys.path.insert(0, module)
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="生成问题词典（事项族分组，引文须逐字命中原文）")
    ap.add_argument("--check", action="store_true", help="只复验已生成 JSON 的引文，不写文件")
    args = ap.parse_args()

    if args.check:
        if not OUT.exists():
            print(f"缺 {OUT}")
            return 1
        data = json.loads(OUT.read_text(encoding="utf-8"))
        bad: list[str] = []
        checked = 0
        for f in data.get("families", []):
            b = f.get("basis", {})
            if b.get("kind") == "citation":
                checked += 1
                off, _ = locate(flat(), b["citation"].translate(str.maketrans("爲", "為")))
                if off < 0:
                    bad.append(f"[{f['label']}] {b['citation']}")
            for r in f.get("refs", []):
                checked += 1
                off, _ = locate(flat(), r["citation"].translate(str.maketrans("爲", "為")))
                if off < 0:
                    bad.append(f"[{f['label']}·ref] {r['citation']}")
        for k, q in (data.get("layer_citations") or {}).items():
            checked += 1
            off, _ = locate(flat(), q["citation"].translate(str.maketrans("爲", "為")))
            if off < 0:
                bad.append(f"[layer:{k}] {q['citation']}")
        print(f"引文复验：{checked - len(bad)}/{checked} 条仍逐字命中原文")
        for m in bad:
            print("  × 失效：", m)
        return 1 if bad else 0

    if not RAW.exists():
        print(f"缺原文缓存 {RAW}，先跑 dev_tools/fetch_wikisource_cases.py")
        return 1

    resolved, missing = resolve(FAMILIES)
    layers: dict[str, dict] = {}
    for key, q in LAYER_CITATIONS.items():
        off, verbatim = locate(flat(), q)
        if off < 0:
            missing.append(f"[layer:{key}] {q}")
        else:
            layers[key] = {"citation": re.sub(r"<br>|\s+", "", verbatim), "offset": off}

    key_count = sum(len(f["entries"]) for f in resolved)
    print(f"引文核对：族 {len(resolved)}、键 {key_count}、引文族 "
          f"{sum(1 for f in resolved if f['basis']['kind'] == 'citation')}、"
          f"推断族 {sum(1 for f in resolved if f['basis']['kind'] == 'inference')}")
    for m in missing:
        print("  × 原文找不到，已拒收：", m)
    if missing:
        print("没有出处的引文不进表——请改引文或删除该条。")
        return 1
    if key_count != EXPECTED_KEYS:
        print(f"× 键数 {key_count} ≠ {EXPECTED_KEYS}：词典搬移必须零增删（先查快照）")
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "_meta": {
            "description": "六爻问题词典（186 条现代问法→六亲），按事项族分组；"
                           "每族给 label + 取舍依据（citation＝《增刪卜易》逐字引文与偏移，"
                           "inference＝诚实标注的无据推断）",
            "built_by": "dev_tools/build_question_use_gods.py",
            "source": str(RAW.relative_to(DISC.parent.parent)),
            "order_warning": "entries 顺序＝打分层 tie-break 依赖的插入顺序，禁止重排/增删；"
                             "改词典必须重跑 tune/holdout/wikisource 三集（AGENTS.md 四）",
            "usage": "chain_tables._QUESTION_USE_GOD_MAP 由本表加载；"
                     "取用神顺序＝关系法则(use_god_relations) → 覆盖层 → 本词典 → 世爻兜底",
            "layer_citations": "chain_step2 覆盖层（代码消歧层）的展示引文，同为逐字核验",
            "family_count": len(resolved),
            "key_count": key_count,
        },
        "families": resolved,
        "layer_citations": layers,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUT.relative_to(DISC.parent.parent)}（{len(resolved)} 族 / {key_count} 键）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
