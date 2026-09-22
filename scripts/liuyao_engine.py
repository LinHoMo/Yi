#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六爻纳甲装卦引擎 (Liu Yao NaJia Hexagram Engine)
================================================
完整的六爻占卜系统实现：
- 四种起卦方式：铜钱摇卦、时间起卦、数字起卦、手动指定
- 完整装卦流程：定卦宫 → 纳甲装干支 → 安世应 → 定六亲 → 配六神 → 查空亡
- 输出标准 JSON 结构供上层解读使用

仅使用 Python 标准库，无外部依赖。
"""
import os as _ks_os, sys as _ks_sys   # 内核路径引导，不依赖导入顺序
_CORE_DIR = _ks_os.path.join(_ks_os.path.dirname(_ks_os.path.abspath(__file__)),
                              _ks_os.pardir, "core")
if _ks_os.path.isdir(_CORE_DIR) and _ks_os.path.abspath(_CORE_DIR) not in _ks_sys.path:
    _ks_sys.path.insert(0, _ks_os.path.abspath(_CORE_DIR))
from yishu_core.symbols import (  # noqa: E402  象数基元唯一真值源
    ADVANCE_PAIRS,
    BRANCH_ELEMENTS,
    BREAK_PAIRS,
    CHONG_PAIRS,
    EARTHLY_BRANCHES,
    EIGHT_PALACES,
    HEAVENLY_STEMS,
    HEXAGRAM_TRIGRAMS,
    HE_PAIRS,
    KE_CYCLE,
    NAJIA_BRANCHES,
    RETREAT_PAIRS,
    SHENG_CYCLE,
    STEM_ELEMENTS,
    TOMB_MAP,
)

import argparse
import json
import math
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# =============================================================================
# 高精度农历库（可选，仅作交叉校验）
# =============================================================================
# 主计算走 core/yishu_core/ganzhi_calendar（太阳黄经求节气，纯标准库、可自检）。
# lunar-python / sxtwl 装了就拿来旁证，没装也绝不降级为近似算法。
# 校验入口：crosscheck_optional_libraries()

# =============================================================================
# 第一部分：基础数据定义
# =============================================================================

# 八卦 (Bagua) - 从下往上读（下爻到上爻）
# 1 = 阳爻(solid/broken)，0 = 阴爻
BAGUA = {
    "乾": {"lines": [1, 1, 1], "nature": "yang", "element": "金", "symbol": "☰"},
    "坤": {"lines": [0, 0, 0], "nature": "yin",  "element": "土", "symbol": "☷"},
    "震": {"lines": [0, 0, 1], "nature": "yang", "element": "木", "symbol": "☳"},
    "巽": {"lines": [1, 1, 0], "nature": "yin",  "element": "木", "symbol": "☴"},
    "坎": {"lines": [0, 1, 0], "nature": "yang", "element": "水", "symbol": "☵"},
    "离": {"lines": [1, 0, 1], "nature": "yin",  "element": "火", "symbol": "☲"},
    "艮": {"lines": [1, 0, 0], "nature": "yang", "element": "土", "symbol": "☶"},
    "兑": {"lines": [0, 1, 1], "nature": "yin",  "element": "金", "symbol": "☱"},
}

# 反向查找：由三爻编码到卦名
def _build_trigram_lookup():
    lookup = {}
    for name, info in BAGUA.items():
        key = tuple(info["lines"])
        lookup[key] = name
    return lookup

TRIGRAM_LOOKUP = _build_trigram_lookup()

# 天干 (10 Heavenly Stems)

# 地支 (12 Earthly Branches)

# 天干五行

# 地支五行

# 地支数字对应(用于时间起卦)
BRANCH_NUMBERS = {
    "子": 1, "丑": 2, "寅": 3, "卯": 4, "辰": 5, "巳": 6,
    "午": 7, "未": 8, "申": 9, "酉": 10, "戌": 11, "亥": 12
}

# 纳甲 - 天干
# 乾纳甲壬(内甲外壬), 坤纳乙癸(内乙外癸), 震纳庚, 坎纳戊, 艮纳丙, 巽纳辛, 离纳己, 兑纳丁
NAJIA_STEMS = {
    "乾": {"inner": "甲", "outer": "壬", "nature": "yang"},
    "坤": {"inner": "乙", "outer": "癸", "nature": "yin"},
    "震": {"inner": "庚", "outer": "庚", "nature": "yang"},
    "坎": {"inner": "戊", "outer": "戊", "nature": "yang"},
    "艮": {"inner": "丙", "outer": "丙", "nature": "yang"},
    "巽": {"inner": "辛", "outer": "辛", "nature": "yin"},
    "离": {"inner": "己", "outer": "己", "nature": "yin"},
    "兑": {"inner": "丁", "outer": "丁", "nature": "yin"},
}

# 纳甲 - 地支 (内卦与外卦)
# 阳卦(乾震坎艮)从下往上顺排，阴卦(坤巽离兑)从下往上逆排

# =============================================================================
# 地支关系对（六合、六冲、六破）
# =============================================================================

# 地支六合（子丑合、寅亥合、卯戌合、辰酉合、巳申合、午未合）

# 地支六冲（子午冲、丑未冲、寅申冲、卯酉冲、辰戌冲、巳亥冲）

# 地支六破（次于六冲的克害关系）
# 子酉破、午卯破、巳申破、寅亥破、辰丑破、戌未破
# 注意：巳申、寅亥既是六合又是六破 → "合中带破"

# =============================================================================
# 第二部分：六十四卦数据
# =============================================================================

# 六十四卦完整数据
# 下卦(inner/lower)和上卦(outer/upper)组成六爻
HEXAGRAMS = [
    # (序号, 卦名, 上卦, 下卦, 卦辞)
    (1,  "乾",   "乾", "乾", "元亨利贞"),
    (2,  "坤",   "坤", "坤", "元亨，利牝马之贞"),
    (3,  "屯",   "坎", "震", "元亨利贞，勿用有攸往，利建侯"),
    (4,  "蒙",   "艮", "坎", "亨，匪我求童蒙，童蒙求我"),
    (5,  "需",   "坎", "乾", "有孚，光亨，贞吉，利涉大川"),
    (6,  "讼",   "乾", "坎", "有孚，窒惕，中吉，终凶"),
    (7,  "师",   "坤", "坎", "贞，丈人吉，无咎"),
    (8,  "比",   "坎", "坤", "吉，原筮，元永贞，无咎"),
    (9,  "小畜", "巽", "乾", "亨，密云不降雨，自我西郊"),
    (10, "履",   "乾", "兑", "履虎尾，不咥人，亨"),
    (11, "泰",   "坤", "乾", "小往大来，吉亨"),
    (12, "否",   "乾", "坤", "否之匪人，不利君子贞，大往小来"),
    (13, "同人", "乾", "离", "同人于野，亨，利涉大川，利君子贞"),
    (14, "大有", "离", "乾", "元亨"),
    (15, "谦",   "坤", "艮", "亨，君子有终"),
    (16, "豫",   "震", "坤", "利建侯行师"),
    (17, "随",   "兑", "震", "元亨利贞，无咎"),
    (18, "蛊",   "艮", "巽", "元亨，利涉大川，先甲三日，后甲三日"),
    (19, "临",   "坤", "兑", "元亨利贞，至于八月有凶"),
    (20, "观",   "巽", "坤", "盥而不荐，有孚颙若"),
    (21, "噬嗑", "离", "震", "亨，利用狱"),
    (22, "贲",   "艮", "离", "亨，小利有攸往"),
    (23, "剥",   "艮", "坤", "不利有攸往"),
    (24, "复",   "坤", "震", "亨，出入无疾，朋来无咎"),
    (25, "无妄", "乾", "震", "元亨利贞，其匪正有眚，不利有攸往"),
    (26, "大畜", "艮", "乾", "利贞，不家食吉，利涉大川"),
    (27, "颐",   "艮", "震", "贞吉，观颐，自求口实"),
    (28, "大过", "兑", "巽", "栋桡，利有攸往，亨"),
    (29, "坎",   "坎", "坎", "习坎，有孚，维心亨，行有尚"),
    (30, "离",   "离", "离", "利贞，亨，畜牝牛吉"),
    (31, "咸",   "兑", "艮", "亨，利贞，取女吉"),
    (32, "恒",   "震", "巽", "亨，无咎，利贞，利有攸往"),
    (33, "遁",   "乾", "艮", "亨，小利贞"),
    (34, "大壮", "震", "乾", "利贞"),
    (35, "晋",   "离", "坤", "康侯用锡马蕃庶，昼日三接"),
    (36, "明夷", "坤", "离", "利艰贞"),
    (37, "家人", "巽", "离", "利女贞"),
    (38, "睽",   "离", "兑", "小事吉"),
    (39, "蹇",   "坎", "艮", "利西南，不利东北，利见大人，贞吉"),
    (40, "解",   "震", "坎", "利西南，无所往，其来复吉"),
    (41, "损",   "艮", "兑", "有孚，元吉，无咎，可贞，利有攸往"),
    (42, "益",   "巽", "震", "利有攸往，利涉大川"),
    (43, "夬",   "兑", "乾", "扬于王庭，孚号，有厉告自邑"),
    (44, "姤",   "乾", "巽", "女壮，勿用取女"),
    (45, "萃",   "兑", "坤", "亨，王假有庙，利见大人，亨，利贞"),
    (46, "升",   "坤", "巽", "元亨，用见大人，勿恤，南征吉"),
    (47, "困",   "兑", "坎", "亨，贞，大人吉，无咎，有言不信"),
    (48, "井",   "坎", "巽", "改邑不改井，无丧无得，往来井井"),
    (49, "革",   "兑", "离", "巳日乃孚，元亨利贞，悔亡"),
    (50, "鼎",   "离", "巽", "元吉，亨"),
    (51, "震",   "震", "震", "亨，震来虩虩，笑言哑哑"),
    (52, "艮",   "艮", "艮", "艮其背，不获其身，行其庭，不见其人，无咎"),
    (53, "渐",   "巽", "艮", "女归吉，利贞"),
    (54, "归妹", "震", "兑", "征凶，无攸利"),
    (55, "丰",   "震", "离", "亨，王假之，勿忧，宜日中"),
    (56, "旅",   "离", "艮", "小亨，旅贞吉"),
    (57, "巽",   "巽", "巽", "小亨，利有攸往，利见大人"),
    (58, "兑",   "兑", "兑", "亨，利贞"),
    (59, "涣",   "巽", "坎", "亨，王假有庙，利涉大川，利贞"),
    (60, "节",   "坎", "兑", "亨，苦节不可贞"),
    (61, "中孚", "巽", "兑", "豚鱼吉，利涉大川，利贞"),
    (62, "小过", "震", "艮", "亨，利贞，可小事，不可大事"),
    (63, "既济", "坎", "离", "亨小，利贞，初吉终乱"),
    (64, "未济", "离", "坎", "亨，小狐汔济，濡其尾，无攸利"),
]

# 由上下卦名对查找卦
def _build_hexagram_lookup():
    lookup = {}
    for seq, name, upper, lower, judgment in HEXAGRAMS:
        key = (upper, lower)
        lookup[key] = (seq, name, judgment)
    return lookup

HEXAGRAM_LOOKUP = _build_hexagram_lookup()

# 爻辞数据 (六十四卦各爻爻辞, 从初爻到上爻)
HEXAGRAM_LINE_TEXTS = {
    "乾": [
        "潜龙勿用",
        "见龙在田，利见大人",
        "君子终日乾乾，夕惕若厉，无咎",
        "或跃在渊，无咎",
        "飞龙在天，利见大人",
        "亢龙有悔",
    ],
    "坤": [
        "履霜，坚冰至",
        "直方大，不习无不利",
        "含章可贞，或从王事，无成有终",
        "括囊，无咎无誉",
        "黄裳，元吉",
        "龙战于野，其血玄黄",
    ],
    "屯": [
        "磐桓，利居贞，利建侯",
        "屯如邅如，乘马班如，匪寇婚媾，女子贞不字，十年乃字",
        "即鹿无虞，惟入于林中，君子几不如舍，往吝",
        "乘马班如，求婚媾，往吉，无不利",
        "屯其膏，小贞吉，大贞凶",
        "乘马班如，泣血涟如",
    ],
    "蒙": [
        "发蒙，利用刑人，用说桎梏，以往吝",
        "包蒙吉，纳妇吉，子克家",
        "勿用取女，见金夫，不有躬，无攸利",
        "困蒙，吝",
        "童蒙，吉",
        "击蒙，不利为寇，利御寇",
    ],
    "需": [
        "需于郊，利用恒，无咎",
        "需于沙，小有言，终吉",
        "需于泥，致寇至",
        "需于血，出自穴",
        "需于酒食，贞吉",
        "入于穴，有不速之客三人来，敬之终吉",
    ],
    "讼": [
        "不永所事，小有言，终吉",
        "不克讼，归而逋，其邑人三百户，无眚",
        "食旧德，贞厉，终吉，或从王事，无成",
        "不克讼，复即命渝，安贞吉",
        "讼，元吉",
        "或锡之鞶带，终朝三褫之",
    ],
    "师": [
        "师出以律，否臧凶",
        "在师中，吉无咎，王三锡命",
        "师或舆尸，凶",
        "师左次，无咎",
        "田有禽，利执言，无咎，长子帅师，弟子舆尸，贞凶",
        "大君有命，开国承家，小人勿用",
    ],
    "比": [
        "有孚比之，无咎，有孚盈缶，终来有它，吉",
        "比之自内，贞吉",
        "比之匪人",
        "外比之，贞吉",
        "显比，王用三驱，失前禽，邑人不诫，吉",
        "比之无首，凶",
    ],
    "小畜": [
        "复自道，何其咎，吉",
        "牵复，吉",
        "舆说辐，夫妻反目",
        "有孚，血去惕出，无咎",
        "有孚挛如，富以其邻",
        "既雨既处，尚德载，妇贞厉，月几望，君子征凶",
    ],
    "履": [
        "素履，往无咎",
        "履道坦坦，幽人贞吉",
        "眇能视，跛能履，履虎尾，咥人，凶，武人为于大君",
        "履虎尾，愬愬，终吉",
        "夬履，贞厉",
        "视履考祥，其旋元吉",
    ],
    "泰": [
        "拔茅茹，以其汇，征吉",
        "包荒，用冯河，不遐遗，朋亡，得尚于中行",
        "无平不陂，无往不复，艰贞无咎，勿恤其孚，于食有福",
        "翩翩，不富以其邻，不戒以孚",
        "帝乙归妹，以祉元吉",
        "城复于隍，勿用师，自邑告命，贞吝",
    ],
    "否": [
        "拔茅茹，以其汇，贞吉，亨",
        "包承，小人吉，大人否，亨",
        "包羞",
        "有命无咎，畴离祉",
        "休否，大人吉，其亡其亡，系于苞桑",
        "倾否，先否后喜",
    ],
    "同人": [
        "同人于门，无咎",
        "同人于宗，吝",
        "伏戎于莽，升其高陵，三岁不兴",
        "乘其墉，弗克攻，吉",
        "同人，先号咷而后笑，大师克相遇",
        "同人于郊，无悔",
    ],
    "大有": [
        "无交害，匪咎，艰则无咎",
        "大车以载，有攸往，无咎",
        "公用亨于天子，小人弗克",
        "匪其彭，无咎",
        "厥孚交如，威如，吉",
        "自天佑之，吉无不利",
    ],
    "谦": [
        "谦谦君子，用涉大川，吉",
        "鸣谦，贞吉",
        "劳谦，君子有终，吉",
        "无不利，撝谦",
        "不富以其邻，利用侵伐，无不利",
        "鸣谦，利用行师，征邑国",
    ],
    "豫": [
        "鸣豫，凶",
        "介于石，不终日，贞吉",
        "盱豫，悔，迟有悔",
        "由豫，大有得，勿疑，朋盍簪",
        "贞疾，恒不死",
        "冥豫，成有渝，无咎",
    ],
    "随": [
        "官有渝，贞吉，出门交有功",
        "系小子，失丈夫",
        "系丈夫，失小子，随有求得，利居贞",
        "随有获，贞凶，有孚在道，以明，何咎",
        "孚于嘉，吉",
        "拘系之，乃从维之，王用亨于西山",
    ],
    "蛊": [
        "干父之蛊，有子，考无咎，厉终吉",
        "干母之蛊，不可贞",
        "干父之蛊，小有晦，无大咎",
        "裕父之蛊，往见吝",
        "干父之蛊，用誉",
        "不事王侯，高尚其事",
    ],
    "临": [
        "咸临，贞吉",
        "咸临，吉无不利",
        "甘临，无攸利，既忧之，无咎",
        "至临，无咎",
        "知临，大君之宜，吉",
        "敦临，吉无咎",
    ],
    "观": [
        "童观，小人无咎，君子吝",
        "窥观，利女贞",
        "观我生，进退",
        "观国之光，利用宾于王",
        "观我生，君子无咎",
        "观其生，君子无咎",
    ],
    "噬嗑": [
        "屦校灭趾，无咎",
        "噬肤灭鼻，无咎",
        "噬腊肉，遇毒，小吝，无咎",
        "噬干胏，得金矢，利艰贞，吉",
        "噬干肉，得黄金，贞厉，无咎",
        "何校灭耳，凶",
    ],
    "贲": [
        "贲其趾，舍车而徒",
        "贲其须",
        "贲如濡如，永贞吉",
        "贲如皤如，白马翰如，匪寇婚媾",
        "贲于丘园，束帛戋戋，吝，终吉",
        "白贲，无咎",
    ],
    "剥": [
        "剥床以足，蔑贞凶",
        "剥床以辨，蔑贞凶",
        "剥之，无咎",
        "剥床以肤，凶",
        "贯鱼，以宫人宠，无不利",
        "硕果不食，君子得舆，小人剥庐",
    ],
    "复": [
        "不远复，无祗悔，元吉",
        "休复，吉",
        "频复，厉无咎",
        "中行独复",
        "敦复，无悔",
        "迷复，凶，有灾眚",
    ],
    "无妄": [
        "无妄，往吉",
        "不耕获，不菑畲，则利有攸往",
        "无妄之灾，或系之牛，行人之得，邑人之灾",
        "可贞，无咎",
        "无妄之药，勿有喜",
        "无妄，行有眚，无攸利",
    ],
    "大畜": [
        "有厉，利已",
        "舆说輹",
        "良马逐，利艰贞，曰闲舆卫，利有攸往",
        "童牛之牿，元吉",
        "豶豕之牙，吉",
        "何天之衢，亨",
    ],
    "颐": [
        "舍尔灵龟，观我朵颐，凶",
        "颠颐，拂经，于丘颐，征凶",
        "拂颐，贞凶，十年勿用，无攸利",
        "颠颐，吉，虎视眈眈，其欲逐逐，无咎",
        "拂经，居贞吉，不可涉大川",
        "由颐，厉吉，利涉大川",
    ],
    "大过": [
        "藉用白茅，无咎",
        "枯杨生稊，老夫得其女妻，无不利",
        "栋桡，凶",
        "栋隆，吉，有它吝",
        "枯杨生华，老妇得其士夫，无咎无誉",
        "过涉灭顶，凶，无咎",
    ],
    "坎": [
        "习坎，入于坎窞，凶",
        "坎有险，求小得",
        "来之坎坎，险且枕，入于坎窞，勿用",
        "樽酒簋贰，用缶，纳约自牖，终无咎",
        "坎不盈，祗既平，无咎",
        "系用徽纆，置于丛棘，三岁不得，凶",
    ],
    "离": [
        "履错然，敬之无咎",
        "黄离，元吉",
        "日昃之离，不鼓缶而歌，则大耋之嗟，凶",
        "突如其来如，焚如，死如，弃如",
        "出涕沱若，戚嗟若，吉",
        "王用出征，有嘉折首，获匪其丑，无咎",
    ],
    "咸": [
        "咸其拇",
        "咸其腓，凶，居吉",
        "咸其股，执其随，往吝",
        "贞吉，悔亡，憧憧往来，朋从尔思",
        "咸其脢，无悔",
        "咸其辅颊舌",
    ],
    "恒": [
        "浚恒，贞凶，无攸利",
        "悔亡",
        "不恒其德，或承之羞，贞吝",
        "田无禽",
        "恒其德，贞，妇人吉，夫子凶",
        "振恒，凶",
    ],
    "遁": [
        "遁尾，厉，勿用有攸往",
        "执之用黄牛之革，莫之胜说",
        "系遁，有疾厉，畜臣妾吉",
        "好遁，君子吉，小人否",
        "嘉遁，贞吉",
        "肥遁，无不利",
    ],
    "大壮": [
        "壮于趾，征凶，有孚",
        "贞吉",
        "小人用壮，君子用罔，贞厉，羝羊触藩，羸其角",
        "贞吉，悔亡，藩决不羸，壮于大舆之輹",
        "丧羊于易，无悔",
        "羝羊触藩，不能退，不能遂，无攸利，艰则吉",
    ],
    "晋": [
        "晋如摧如，贞吉，罔孚，裕无咎",
        "晋如愁如，贞吉，受兹介福，于其王母",
        "众允，悔亡",
        "晋如鼫鼠，贞厉",
        "悔亡，失得勿恤，往吉，无不利",
        "晋其角，维用伐邑，厉吉，无咎，贞吝",
    ],
    "明夷": [
        "明夷于飞，垂其翼，君子于行，三日不食，有攸往，主人有言",
        "明夷，夷于左股，用拯马壮，吉",
        "明夷于南狩，得其大首，不可疾贞",
        "入于左腹，获明夷之心，于出门庭",
        "箕子之明夷，利贞",
        "不明晦，初登于天，后入于地",
    ],
    "家人": [
        "闲有家，悔亡",
        "无攸遂，在中馈，贞吉",
        "家人嗃嗃，悔厉吉，妇子嘻嘻，终吝",
        "富家，大吉",
        "王假有家，勿恤，吉",
        "有孚，威如，终吉",
    ],
    "睽": [
        "悔亡，丧马勿逐，自复，见恶人，无咎",
        "遇主于巷，无咎",
        "见舆曳，其牛掣，其人天且劓，无初有终",
        "睽孤，遇元夫，交孚，厉无咎",
        "悔亡，厥宗噬肤，往何咎",
        "睽孤，见豕负涂，载鬼一车，先张之弧，后说之弧，匪寇婚媾，往遇雨则吉",
    ],
    "蹇": [
        "往蹇，来誉",
        "王臣蹇蹇，匪躬之故",
        "往蹇，来反",
        "往蹇，来连",
        "大蹇，朋来",
        "往蹇，来硕，吉，利见大人",
    ],
    "解": [
        "无咎",
        "田获三狐，得黄矢，贞吉",
        "负且乘，致寇至，贞吝",
        "解而拇，朋至斯孚",
        "君子维有解，吉，有孚于小人",
        "公用射隼于高墉之上，获之，无不利",
    ],
    "损": [
        "已事遄往，无咎，酌损之",
        "利贞，征凶，弗损益之",
        "三人行，则损一人，一人行，则得其友",
        "损其疾，使遄有喜，无咎",
        "或益之十朋之龟，弗克违，元吉",
        "弗损益之，无咎，贞吉，利有攸往，得臣无家",
    ],
    "益": [
        "利用为大作，元吉，无咎",
        "或益之十朋之龟，弗克违，永贞吉，王用享于帝，吉",
        "益之用凶事，无咎，有孚中行，告公用圭",
        "中行，告公从，利用为依迁国",
        "有孚惠心，勿问元吉，有孚惠我德",
        "莫益之，或击之，立心勿恒，凶",
    ],
    "夬": [
        "壮于前趾，往不胜为咎",
        "惕号，莫夜有戎，勿恤",
        "壮于頄，有凶，君子夬夬，独行遇雨，若濡有愠，无咎",
        "臀无肤，其行次且，牵羊悔亡，闻言不信",
        "苋陆夬夬，中行无咎",
        "无号，终有凶",
    ],
    "姤": [
        "系于金柅，贞吉，有攸往，见凶，羸豕孚蹢躅",
        "包有鱼，无咎，不利宾",
        "臀无肤，其行次且，厉，无大咎",
        "包无鱼，起凶",
        "以杞包瓜，含章，有陨自天",
        "姤其角，吝，无咎",
    ],
    "萃": [
        "有孚不终，乃乱乃萃，若号，一握为笑，勿恤，往无咎",
        "引吉，无咎，孚乃利用禴",
        "萃如嗟如，无攸利，往无咎，小吝",
        "大吉，无咎",
        "萃有位，无咎，匪孚，元永贞，悔亡",
        "赍咨涕洟，无咎",
    ],
    "升": [
        "允升，大吉",
        "孚乃利用禴，无咎",
        "升虚邑",
        "王用亨于岐山，吉，无咎",
        "贞吉，升阶",
        "冥升，利于不息之贞",
    ],
    "困": [
        "臀困于株木，入于幽谷，三岁不觌",
        "困于酒食，朱绂方来，利用亨祀，征凶，无咎",
        "困于石，据于蒺藜，入于其宫，不见其妻，凶",
        "来徐徐，困于金车，吝，有终",
        "臲卼，困于赤绂，乃徐有说，利用祭祀",
        "困于葛藟，于臲卼，曰动悔，有悔，征吉",
    ],
    "井": [
        "井泥不食，旧井无禽",
        "井谷射鲋，瓮敝漏",
        "井渫不食，为我心恻，可用汲，王明，并受其福",
        "井甃，无咎",
        "井冽，寒泉食",
        "井收，勿幕，有孚，元吉",
    ],
    "革": [
        "巩用黄牛之革",
        "巳日乃革之，征吉，无咎",
        "征凶，贞厉，革言三就，有孚",
        "悔亡，有孚改命，吉",
        "大人虎变，未占有孚",
        "君子豹变，小人革面，征凶，居贞吉",
    ],
    "鼎": [
        "鼎颠趾，利出否，得妾以其子，无咎",
        "鼎有实，我仇有疾，不我能即，吉",
        "鼎耳革，其行塞，雉膏不食，方雨亏悔，终吉",
        "鼎折足，覆公餗，其形渥，凶",
        "鼎黄耳金铉，利贞",
        "鼎玉铉，大吉，无不利",
    ],
    "震": [
        "震来虩虩，后笑言哑哑，吉",
        "震来厉，亿丧贝，跻于九陵，勿逐，七日得",
        "震苏苏，震行无眚",
        "震遂泥",
        "震往来厉，亿无丧，有事",
        "震索索，视矍矍，征凶，震不于其躬，于其邻，无咎，婚媾有言",
    ],
    "艮": [
        "艮其趾，无咎，利永贞",
        "艮其腓，不拯其随，其心不快",
        "艮其限，列其夤，厉薰心",
        "艮其身，无咎",
        "艮其辅，言有序，悔亡",
        "敦艮，吉",
    ],
    "渐": [
        "鸿渐于干，小子厉，有言，无咎",
        "鸿渐于磐，饮食衎衎，吉",
        "鸿渐于陆，夫征不复，妇孕不育，凶，利御寇",
        "鸿渐于木，或得其桷，无咎",
        "鸿渐于陵，妇三岁不孕，终莫之胜，吉",
        "鸿渐于陆，其羽可用为仪，吉",
    ],
    "归妹": [
        "归妹以娣，跛能履，征吉",
        "眇能视，利幽人之贞",
        "归妹以须，反归以娣",
        "归妹愆期，迟归有时",
        "帝乙归妹，其君之袂，不如其娣之袂良，月几望，吉",
        "女承筐无实，士刲羊无血，无攸利",
    ],
    "丰": [
        "遇其配主，虽旬无咎，往有尚",
        "丰其蔀，日中见斗，往得疑疾，有孚发若，吉",
        "丰其沛，日中见沫，折其右肱，无咎",
        "丰其蔀，日中见斗，遇其夷主，吉",
        "来章，有庆誉，吉",
        "丰其屋，蔀其家，窥其户，阒其无人，三岁不觌，凶",
    ],
    "旅": [
        "旅琐琐，斯其所取灾",
        "旅即次，怀其资，得童仆贞",
        "旅焚其次，丧其童仆，贞厉",
        "旅于处，得其资斧，我心不快",
        "射雉，一矢亡，终以誉命",
        "鸟焚其巢，旅人先笑后号咷，丧牛于易，凶",
    ],
    "巽": [
        "进退，利武人之贞",
        "巽在床下，用史巫纷若，吉，无咎",
        "频巽，吝",
        "悔亡，田获三品",
        "贞吉，悔亡，无不利，无初有终，先庚三日，后庚三日，吉",
        "巽在床下，丧其资斧，贞凶",
    ],
    "兑": [
        "和兑，吉",
        "孚兑，吉，悔亡",
        "来兑，凶",
        "商兑未宁，介疾有喜",
        "孚于剥，有厉",
        "引兑",
    ],
    "涣": [
        "用拯马壮，吉",
        "涣奔其机，悔亡",
        "涣其躬，无悔",
        "涣其群，元吉，涣有丘，匪夷所思",
        "涣汗其大号，涣王居，无咎",
        "涣其血，去逖出，无咎",
    ],
    "节": [
        "不出户庭，无咎",
        "不出门庭，凶",
        "不节若，则嗟若，无咎",
        "安节，亨",
        "甘节，吉，往有尚",
        "苦节，贞凶，悔亡",
    ],
    "中孚": [
        "虞吉，有它不燕",
        "鸣鹤在阴，其子和之，我有好爵，吾与尔靡之",
        "得敌，或鼓或罢，或泣或歌",
        "月几望，马匹亡，无咎",
        "有孚挛如，无咎",
        "翰音登于天，贞凶",
    ],
    "小过": [
        "飞鸟以凶",
        "过其祖，遇其妣，不及其君，遇其臣，无咎",
        "弗过防之，从或戕之，凶",
        "无咎，弗过遇之，往厉必戒，勿用永贞",
        "密云不雨，自我西郊，公弋取彼在穴",
        "弗遇过之，飞鸟离之，凶，是谓灾眚",
    ],
    "既济": [
        "曳其轮，濡其尾，无咎",
        "妇丧其茀，勿逐，七日得",
        "高宗伐鬼方，三年克之，小人勿用",
        "繻有衣袽，终日戒",
        "东邻杀牛，不如西邻之禴祭，实受其福",
        "濡其首，厉",
    ],
    "未济": [
        "濡其尾，吝",
        "曳其轮，贞吉",
        "未济，征凶，利涉大川",
        "贞吉，悔亡，震用伐鬼方，三年有赏于大国",
        "贞吉，无悔，君子之光，有孚，吉",
        "有孚于饮酒，无咎，濡其首，有孚失是",
    ],
}

# =============================================================================
# 第三部分：八宫系统 (决定世应位置)
# =============================================================================

# 八宫卦序 (分宫卦象次序歌)
# 每个宫：本宫卦(六世) → 一世 → 二世 → 三世 → 四世 → 五世 → 游魂 → 归魂

# 构建反向查找：卦名 → (宫名, 世代)
def _build_palace_lookup():
    lookup = {}
    for palace_name, palace_data in EIGHT_PALACES.items():
        for hex_name, generation in palace_data["order"]:
            lookup[hex_name] = (palace_name, generation)
    return lookup

PALACE_LOOKUP = _build_palace_lookup()

# 世爻位置 (generation → 世爻位置, 1-based, 1=初爻, 6=上爻)
WORLD_POSITION = {
    "六世": 6,
    "五世": 5,
    "四世": 4,
    "三世": 3,
    "二世": 2,
    "一世": 1,
    "游魂": 4,
    "归魂": 3,
}

# 应爻位置 (世爻位置 → 应爻位置)
# 世在初→应在四, 世在二→应在五, 世在三→应在上,
# 世在四→应在初, 世在五→应在二, 世在上→应在三
RESPONSE_POSITION = {
    1: 4,
    2: 5,
    3: 6,
    4: 1,
    5: 2,
    6: 3,
}

# =============================================================================
# 第四部分：六神系统
# =============================================================================

# 六神序列: 青龙、朱雀、勾陈、螣蛇、白虎、玄武
SIX_SPIRITS = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]

# 日干起六神 (从初爻开始配)
DAY_STEM_SPIRIT_START = {
    "甲": 0,  # 青龙起初爻
    "乙": 0,  # 青龙起初爻
    "丙": 1,  # 朱雀起初爻
    "丁": 1,  # 朱雀起初爻
    "戊": 2,  # 勾陈起初爻
    "己": 3,  # 螣蛇起初爻
    "庚": 4,  # 白虎起初爻
    "辛": 4,  # 白虎起初爻
    "壬": 5,  # 玄武起初爻
    "癸": 5,  # 玄武起初爻
}

# =============================================================================
# 第五部分：旬空系统
# =============================================================================

# 旬空 (空亡) 由日柱甲子决定
# 甲子旬: 戌亥空, 甲戌旬: 申酉空, 甲申旬: 午未空
# 甲午旬: 辰巳空, 甲辰旬: 寅卯空, 甲寅旬: 子丑空
EMPTY_DEATH = {
    "甲子": ["戌", "亥"],
    "甲戌": ["申", "酉"],
    "甲申": ["午", "未"],
    "甲午": ["辰", "巳"],
    "甲辰": ["寅", "卯"],
    "甲寅": ["子", "丑"],
}

# 第六部分：四柱干支计算 —— 委托历法内核 (core/yishu_core)
# =============================================================================
# 本部分不再自带历法近似。年界在立春、月界在十二节、日界以夜子时为界，
# 全部由 yishu_core.ganzhi_calendar 按太阳黄经求交节时刻后给出。
# 历法正确性由 `python core/yishu_core/calendar_check.py` 自检。
#
# 历史缺陷（2026-09-22 修，详见 docs/CHANGELOG.md）：
#   1. 旧实现在未装 lunar-python/sxtwl 时完全不判立春 → 每年 1 月至立春前年柱错一位
#   2. 月支用固定近似日（Feb 4 交立春等）→ 交节边界 ±1~2 天内月建错
#   3. 五鼠遁写作 (stem_start + branch_idx) % 12 再减 10 → 戊/癸日辰时之后时柱错

def _load_ganzhi_kernel():
    """定位并导入历法内核。找不到时明确报错，绝不退回近似算法。"""
    try:
        from yishu_core import ganzhi_calendar as _gc  # 已安装为包
        return _gc
    except ImportError:
        pass
    core_dir = Path(__file__).resolve().parents[1] / "core"
    if not (core_dir / "yishu_core").is_dir():
        raise RuntimeError(f"缺少历法内核目录：{core_dir / 'yishu_core'}")
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    from yishu_core import ganzhi_calendar as _gc
    return _gc


_GANZHI = _load_ganzhi_kernel()
from yishu_core.runtime import force_utf8_stdio as _force_utf8_stdio  # noqa: E402

# 交节流派："day" = 交节当日即换月/换年（默认，保持既有断卦行为）；"instant" = 精确到时刻
GANZHI_BOUNDARY = os.environ.get("YI_GANZHI_BOUNDARY", "day")


def _noon(year, month, day):
    return datetime(year, month, day, 12, 0)


def get_year_stem_branch(year, month=0, day=0):
    """年干支。以立春为年界：未过立春仍作前一年。"""
    if month > 0 and day > 0:
        dt = _noon(year, month, day)
    else:
        dt = _noon(year, 6, 15)  # 未给月日 → 取年中，必在立春之后
    return _GANZHI.ganzhi_of(dt, boundary=GANZHI_BOUNDARY).year_ganzhi


def get_month_stem_branch(year, month, day):
    """月干支。以十二节定月支，五虎遁定月干。"""
    return _GANZHI.ganzhi_of(_noon(year, month, day), boundary=GANZHI_BOUNDARY).month_ganzhi


def get_day_stem_branch(year, month, day):
    """日干支。由儒略日数直接取模，不查表、无累积误差。"""
    return _GANZHI.day_ganzhi_of(year, month, day)


def get_hour_stem_branch(day_stem, hour):
    """时干支。五鼠遁，日干 + 时辰地支。"""
    return _GANZHI.hour_ganzhi_of(day_stem, hour)


def ganzhi_moment(dt):
    """完整四柱 + 节气上下文，供需要交节信息的上层调用。"""
    return _GANZHI.ganzhi_of(dt if isinstance(dt, datetime) else _noon(*dt[:3]),
                             boundary=GANZHI_BOUNDARY)


def crosscheck_optional_libraries(years=range(2000, 2031)):
    """若装了 lunar-python / sxtwl，抽样交叉核对内核结果；不一致则返回差异清单。

    这两个库只是旁证，不参与主计算（主计算需自检、可移植、无编译依赖）。
    """
    diffs = []
    try:
        from lunar_python import Solar
    except ImportError:
        Solar = None
    if Solar is None:
        return diffs
    for y in years:
        for m, d in ((1, 5), (2, 2), (2, 6), (3, 15), (5, 6), (6, 21), (8, 8),
                     (10, 9), (11, 8), (12, 22)):
            try:
                lunar = Solar.fromYmd(y, m, d).getLunar()
            except Exception:
                continue
            mine = _GANZHI.ganzhi_of(_noon(y, m, d), boundary=GANZHI_BOUNDARY)
            theirs = (lunar.getYearInGanZhiByLiChun() if GANZHI_BOUNDARY == "day"
                      else lunar.getYearInGanZhi())
            if mine.year_ganzhi != theirs or mine.month_ganzhi != lunar.getMonthInGanZhi() \
                    or mine.day_ganzhi != lunar.getDayInGanZhi():
                diffs.append({
                    "date": f"{y}-{m:02d}-{d:02d}",
                    "kernel": f"{mine.year_ganzhi} {mine.month_ganzhi} {mine.day_ganzhi}",
                    "library": f"{theirs} {lunar.getMonthInGanZhi()} {lunar.getDayInGanZhi()}",
                })
    return diffs


# =============================================================================
# =============================================================================
# 第七部分：起卦方法
# =============================================================================

def coin_toss(random_gen=None):
    """
    铜钱摇卦法
    三枚铜钱投掷，每枚正面=3，反面=2
    三枚之和：6(老阴/动爻/阴), 7(少阳/静爻/阳), 8(少阴/静爻/阴), 9(老阳/动爻/阳)
    摇6次，从初爻到上爻
    
    Args:
        random_gen: 可选的 random.Random 实例，用于可复现结果。
                   为 None 时使用全局 random 模块。
    """
    rng = random_gen or random
    yao_values = []
    for _ in range(6):
        # 模拟三枚铜钱
        coins = [rng.choice([2, 3]) for _ in range(3)]
        total = sum(coins)
        yao_values.append(total)
    return yao_values

def time_based_hexagram(year, month, day, hour):
    """
    梅花易数时间起卦法
    年数 + 月数 + 日数 → ÷8 余数 = 上卦
    年数 + 月数 + 日数 + 时数 → ÷8 余数 = 下卦
    年数 + 月数 + 日数 + 时数 → ÷6 余数 = 动爻
    """
    # 年数用地支数
    year_branch = get_year_stem_branch(year, month, day)[1]
    year_num = BRANCH_NUMBERS[year_branch]
    
    # 月数用月份
    month_num = month
    
    # 日数用日期
    day_num = day
    
    # 时数用地支数
    if hour == 23 or hour == 0:
        hour_num = 1  # 子时
    elif 1 <= hour < 3:
        hour_num = 2
    elif 3 <= hour < 5:
        hour_num = 3
    elif 5 <= hour < 7:
        hour_num = 4
    elif 7 <= hour < 9:
        hour_num = 5
    elif 9 <= hour < 11:
        hour_num = 6
    elif 11 <= hour < 13:
        hour_num = 7
    elif 13 <= hour < 15:
        hour_num = 8
    elif 15 <= hour < 17:
        hour_num = 9
    elif 17 <= hour < 19:
        hour_num = 10
    elif 19 <= hour < 21:
        hour_num = 11
    else:
        hour_num = 12
    
    # 余数对应八卦: 1乾 2兑 3离 4震 5巽 6坎 7艮 8坤
    trigram_by_remainder = {
        1: "乾", 2: "兑", 3: "离", 4: "震",
        5: "巽", 6: "坎", 7: "艮", 0: "坤"
    }
    
    upper_rem = (year_num + month_num + day_num) % 8
    lower_rem = (year_num + month_num + day_num + hour_num) % 8
    
    upper_trigram = trigram_by_remainder[upper_rem]
    lower_trigram = trigram_by_remainder[lower_rem]
    
    # 动爻
    moving_rem = (year_num + month_num + day_num + hour_num) % 6
    moving_yao = moving_rem if moving_rem != 0 else 6  # 1-6, 0 means 6th
    
    # 构造六爻
    upper_lines = BAGUA[upper_trigram]["lines"]  # bottom to top: [下,中,上]
    lower_lines = BAGUA[lower_trigram]["lines"]
    
    # 合卦: yao从下到上 = lower[0],lower[1],lower[2],upper[0],upper[1],upper[2]
    yao_lines = lower_lines + upper_lines  # [y0,y1,y2,y3,y4,y5]
    
    # 转换为6/7/8/9 值
    yao_values = []
    for i, line in enumerate(yao_lines):
        if line == 1:  # yang line
            if (i + 1) == moving_yao:
                yao_values.append(9)  # old yang (moving)
            else:
                yao_values.append(7)  # young yang
        else:  # yin line
            if (i + 1) == moving_yao:
                yao_values.append(6)  # old yin (moving)
            else:
                yao_values.append(8)  # young yin
    
    return yao_values

def number_based_hexagram(a, b, c):
    """
    数字起卦法
    三个数a,b,c
    a % 8 → 上卦
    b % 8 → 下卦
    c % 6 → 动爻
    
    余数对应: 1乾 2兑 3离 4震 5巽 6坎 7艮 0坤
    """
    trigram_by_remainder = {
        1: "乾", 2: "兑", 3: "离", 4: "震",
        5: "巽", 6: "坎", 7: "艮", 0: "坤"
    }
    
    upper_rem = a % 8
    lower_rem = b % 8
    moving_rem = c % 6
    
    upper_trigram = trigram_by_remainder[upper_rem]
    lower_trigram = trigram_by_remainder[lower_rem]
    moving_yao = moving_rem if moving_rem != 0 else 6
    
    upper_lines = BAGUA[upper_trigram]["lines"]
    lower_lines = BAGUA[lower_trigram]["lines"]
    yao_lines = lower_lines + upper_lines
    
    yao_values = []
    for i, line in enumerate(yao_lines):
        if line == 1:
            if (i + 1) == moving_yao:
                yao_values.append(9)
            else:
                yao_values.append(7)
        else:
            if (i + 1) == moving_yao:
                yao_values.append(6)
            else:
                yao_values.append(8)
    
    return yao_values

# =============================================================================
# 第八部分：装卦核心逻辑
# =============================================================================

def yao_value_to_lines(yao_values):
    """
    将6个数值(6/7/8/9)转为卦象信息
    返回 (下卦三爻, 上卦三爻) 的二进制列表, bottom to top
    """
    # yao_values[0]=初爻(bottom), yao_values[5]=上爻(top)
    # 下卦(内卦) = yao_values[0:3]
    # 上卦(外卦) = yao_values[3:6]
    
    lower_trigram_lines = []
    upper_trigram_lines = []
    
    for i in range(3):
        val = yao_values[i]
        # 6(old yin)=阴, 7(young yang)=阳, 8(young yin)=阴, 9(old yang)=阳
        if val in (7, 9):
            lower_trigram_lines.append(1)
        else:
            lower_trigram_lines.append(0)
    
    for i in range(3, 6):
        val = yao_values[i]
        if val in (7, 9):
            upper_trigram_lines.append(1)
        else:
            upper_trigram_lines.append(0)
    
    return lower_trigram_lines, upper_trigram_lines

def find_trigram_name(trigram_lines):
    """由三爻查找卦名"""
    key = tuple(trigram_lines)
    return TRIGRAM_LOOKUP.get(key, "未知")

def find_hexagram(upper_trigram_name, lower_trigram_name):
    """
    由上下卦查找六十四卦信息
    HEXAGRAM_LOOKUP 的 key 是 (upper, lower)
    """
    key = (upper_trigram_name, lower_trigram_name)
    result = HEXAGRAM_LOOKUP.get(key)
    if result:
        return result  # (seq, name, judgment)
    return None

def find_changed_hexagram(yao_values):
    """
    找到变卦信息（动爻变后的卦）
    返回变卦名和变了哪些爻
    """
    changed_indices = []
    new_values = list(yao_values)
    
    for i, val in enumerate(yao_values):
        if val == 9:  # 老阳变阴
            new_values[i] = 8
            changed_indices.append(i + 1)  # 1-based
        elif val == 6:  # 老阴变阳
            new_values[i] = 7
            changed_indices.append(i + 1)
    
    if not changed_indices:
        return None, []
    
    lower_lines, upper_lines = yao_value_to_lines(new_values)
    upper_name = find_trigram_name(upper_lines)
    lower_name = find_trigram_name(lower_lines)
    
    hex_info = find_hexagram(upper_name, lower_name)
    if hex_info:
        return hex_info, changed_indices
    return None, changed_indices

def get_palace_info(hex_name):
    """
    获取卦所属的宫和世代
    """
    result = PALACE_LOOKUP.get(hex_name)
    if result:
        return result  # (palace_name, generation)
    
    # 如果查不到，尝试从HEXAGRAMS中找
    for seq, name, upper, lower, judgment in HEXAGRAMS:
        if name == hex_name:
            # 尝试推断宫
            # 这里应该不会走到，因为PALACE_LOOKUP包含所有64卦
            return (upper, "未知")
    
    return ("未知", "未知")

def get_palace_element(palace_name):
    """获取宫五行"""
    if palace_name in EIGHT_PALACES:
        return EIGHT_PALACES[palace_name]["element"]
    # 如果不是宫名，可能是直接传入八卦名
    if palace_name in BAGUA:
        return BAGUA[palace_name]["element"]
    return "未知"

def determine_six_relations(branch, palace_element):
    """
    根据爻的地支五行和宫五行，确定六亲
    我(governor) = 宫五行
    生我者 = 父母
    我生者 = 子孙
    克我者 = 官鬼
    我克者 = 妻财
    同我者 = 兄弟
    """
    branch_element = BRANCH_ELEMENTS.get(branch, "未知")
    
    if branch_element == "未知" or palace_element == "未知":
        return "未知"
    
    # 五行相生: 木→火→土→金→水→木
    sheng_wo = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}  # 生我者的五行
    wo_sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 我生者的五行
    ke_wo = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}     # 克我者的五行
    wo_ke = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}     # 我克者的五行
    
    if branch_element == palace_element:
        return "兄弟"
    elif sheng_wo.get(palace_element) == branch_element:
        return "父母"
    elif wo_sheng.get(palace_element) == branch_element:
        return "子孙"
    elif ke_wo.get(palace_element) == branch_element:
        return "官鬼"
    elif wo_ke.get(palace_element) == branch_element:
        return "妻财"
    else:
        return "未知"

def get_empty_death(day_stem_branch):
    """
    根据日柱旬空查空亡
    由日干支的前两个字符判断旬
    """
    # 提取日柱的天干地支对
    stem = day_stem_branch[0]
    branch = day_stem_branch[1]
    day_pair = stem + branch
    
    # 查表
    if day_pair in EMPTY_DEATH:
        return EMPTY_DEATH[day_pair]
    
    # 如果不在预计算表中，根据天干推算
    # 甲子旬:0-9, 甲戌旬:10-19, 甲申旬:20-29, 甲午旬:30-39, 甲辰旬:40-49, 甲寅旬:50-59
    # day_pair在60甲子中的序号
    stem_idx = HEAVENLY_STEMS.index(stem)
    branch_idx = EARTHLY_BRANCHES.index(branch)
    
    # 计算60甲子序号
    for i in range(60):
        if i % 10 == stem_idx and i % 12 == branch_idx:
            xun_index = i // 10
            break
    else:
        return []
    
    xun_keys = ["甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅"]
    return EMPTY_DEATH.get(xun_keys[xun_index], [])

def get_six_spirit(day_stem, line_position):
    """
    获取某爻的六神
    day_stem: 日天干
    line_position: 1(初爻) 到 6(上爻)
    """
    start_idx = DAY_STEM_SPIRIT_START.get(day_stem, 0)
    # line_position 1(初)对应start, 则index = start_idx + (line_position - 1)
    spirit_idx = (start_idx + line_position - 1) % 6
    return SIX_SPIRITS[spirit_idx]

def get_yao_name(position, nature):
    """
    获取爻名
    position: 1-6 (初到上)
    nature: "yang" or "yin"
    初九, 九二, 九三, 九四, 九五, 上九
    初六, 六二, 六三, 六四, 六五, 上六
    """
    yang_names = ["初九", "九二", "九三", "九四", "九五", "上九"]
    yin_names = ["初六", "六二", "六三", "六四", "六五", "上六"]
    
    if nature == "yang":
        return yang_names[position - 1]
    else:
        return yin_names[position - 1]

def get_yao_symbol(yao_value):
    """获取爻符号"""
    if yao_value in (7, 9):
        return "━━━"  # yang
    else:
        return "━ ━"  # yin

# =============================================================================
# 第九部分：编排输出
# =============================================================================

def build_hexagram_result(yao_values, question, method, year, month, day, hour, explicit_time=None):
    """
    基于6个爻值，构建完整的排盘结果

    explicit_time : dict, optional
        显式指定四柱（用于古典案例盲评——公历重算会丢失原始干支）。
        可含键：year_sb / month_sb / day_sb（完整干支，如"戊戌"），
        或 month_branch / day_branch（仅地支；天干缺失时月干用"甲"占位，
        日干缺失时按甲日计，仅影响六神与旬空精度，不影响旺衰主路径）。
        提供时跳过公历推算；未提供时行为与原来完全一致。
    """
    # 1. 找出上下卦
    lower_lines, upper_lines = yao_value_to_lines(yao_values)
    lower_trigram_name = find_trigram_name(lower_lines)
    upper_trigram_name = find_trigram_name(upper_lines)
    
    # 2. 查找本卦信息
    hex_info = find_hexagram(upper_trigram_name, lower_trigram_name)
    if not hex_info:
        raise ValueError(f"无法识别的卦: 上{upper_trigram_name}下{lower_trigram_name}")
    
    seq, hex_name, judgment = hex_info
    
    # 3. 确定宫和世代
    palace_name, generation = get_palace_info(hex_name)
    palace_element = get_palace_element(palace_name)
    
    # 4. 世应位置
    world_pos = WORLD_POSITION.get(generation, 1)
    response_pos = RESPONSE_POSITION.get(world_pos, 4)
    
    # 5. 计算四柱
    if explicit_time and isinstance(explicit_time, dict):
        if explicit_time.get("day_sb"):
            day_sb = explicit_time["day_sb"]
            year_sb = explicit_time.get("year_sb") or get_year_stem_branch(year, month, day)
            month_sb = explicit_time.get("month_sb") or get_month_stem_branch(year, month, day)
        else:
            mb = explicit_time.get("month_branch")
            db = explicit_time.get("day_branch")
            if db:
                day_sb = "甲" + db
                month_sb = ("甲" + mb) if mb else get_month_stem_branch(year, month, day)
                year_sb = get_year_stem_branch(year, month, day)
            else:
                year_sb = get_year_stem_branch(year, month, day)
                month_sb = get_month_stem_branch(year, month, day)
                day_sb = get_day_stem_branch(year, month, day)
    else:
        year_sb = get_year_stem_branch(year, month, day)
        month_sb = get_month_stem_branch(year, month, day)
        day_sb = get_day_stem_branch(year, month, day)
    hour_sb = get_hour_stem_branch(day_sb[0], hour)
    
    # 6. 旬空
    empty_branches = get_empty_death(day_sb)
    
    # 7. 日干 (用于六神)
    day_stem = day_sb[0]
    
    # 8. 构建爻信息
    yao_lines_output = []
    moving_yaos = []
    
    for i in range(6):
        position = i + 1  # 1-based, 1=初爻(bottom), 6=上爻(top)
        val = yao_values[i]
        is_moving = val in (6, 9)
        
        # 阴阳属性
        if val in (7, 9):
            nature = "yang"
        else:
            nature = "yin"
        
        # 纳甲天干 (根据上下卦)
        if i < 3:
            # 内卦(下卦)
            stem = NAJIA_STEMS[lower_trigram_name]["inner"]
        else:
            # 外卦(上卦)
            stem = NAJIA_STEMS[upper_trigram_name]["outer"]
        
        # 纳甲地支
        if i < 3:
            branch = NAJIA_BRANCHES[lower_trigram_name]["inner"][i]
        else:
            branch = NAJIA_BRANCHES[upper_trigram_name]["outer"][i - 3]
        
        # 六亲
        six_relation = determine_six_relations(branch, palace_element)
        
        # 六神
        six_spirit = get_six_spirit(day_stem, position)
        
        # 旬空
        is_empty = branch in empty_branches
        
        # 爻名
        yao_name = get_yao_name(position, nature)
        
        # 爻符号
        symbol = get_yao_symbol(val)
        
        # 世应
        is_world = (position == world_pos)
        is_response = (position == response_pos)
        
        # 爻辞
        line_text = ""
        if hex_name in HEXAGRAM_LINE_TEXTS:
            line_text = HEXAGRAM_LINE_TEXTS[hex_name][i]
        
        yao_info = {
            "position": position,
            "name": yao_name,
            "nature": nature,
            "symbol": symbol,
            "heavenly_stem": stem,
            "earthly_branch": branch,
            "six_relation": six_relation,
            "six_spirit": six_spirit,
            "is_moving": is_moving,
            "is_world": is_world,
            "is_response": is_response,
            "is_empty": is_empty,
            "line_text": line_text,
        }
        
        yao_lines_output.append(yao_info)
        
        if is_moving:
            moving_yaos.append(position)
    
    # 9. 变卦信息
    changed_hex_name = None
    changed_judgment = None
    changed_changed_lines = []
    
    if moving_yaos:
        new_hex_info, changed_changed_lines = find_changed_hexagram(yao_values)
        if new_hex_info:
            changed_seq, changed_hex_name, changed_judgment = new_hex_info
    
    # 八卦卜象解读（trigram symbolism interpretation）
    try:
        import os as _os
        _scripts_dir = _os.path.dirname(_os.path.abspath(__file__))
        if _scripts_dir not in sys.path:
            sys.path.insert(0, _scripts_dir)
        from trigram_symbolism import build_trigram_interpretation as _build_trigram_interp
        trigram_interp = _build_trigram_interp(
            {"original_hexagram": {"upper_trigram": upper_trigram_name, "lower_trigram": lower_trigram_name}},
            category="general"
        )
    except Exception as _e:
        # pragma: no cover - graceful degradation
        trigram_interp = None

    # 构建输出
    result = {
        "question": question,
        "divination_time": {
            "datetime": f"{year}-{month:02d}-{day:02d} {hour:02d}:00",
            "year_stem_branch": year_sb,
            "month_stem_branch": month_sb,
            "day_stem_branch": day_sb,
            "hour_stem_branch": hour_sb,
        },
        "method": method,
        "empty_branches": empty_branches,
        "trigram_interpretation": trigram_interp,
        "original_hexagram": {
            "name": hex_name,
            "sequence": seq,
            "upper_trigram": upper_trigram_name,
            "lower_trigram": lower_trigram_name,
            "palace": palace_name,
            "palace_element": palace_element,
            "generation": generation,
            "judgment": judgment,
            "yao_lines": yao_lines_output,
        },
        "changed_hexagram": {
            "name": changed_hex_name,
            "judgment": changed_judgment,
            "changed_lines": moving_yaos if changed_hex_name else [],
        } if changed_hex_name else None,
        "analysis_hints": {
            "possible_use_gods": generate_analysis_hints(question),
        },
    }
    
    return result

def generate_analysis_hints(question):
    """
    根据问题关键词生成用神建议
    """
    hints = []
    
    # 定义关键词映射
    finance_keywords = ["财", "钱", "投资", "生意", "收入", "利", "赚", "经济", "金", "上市", "公司", "项目", "产品", "融资", "创业", "合伙", "股份", "分红", "上市", "经营", "市场"]
    career_keywords = ["事业", "工作", "升职", "官", "职", "考", "升", "提拔", "调动", "辞职", "面试", "招聘", "编制", "公务员"]
    love_keywords = ["感情", "婚", "恋", "爱", "桃花", "对象", "另一半", "伴侣"]
    health_keywords = ["健康", "病", "疾", "身", "医", "药"]
    study_keywords = ["学", "考试", "文", "书", "成绩", "毕业", "学位"]
    travel_keywords = ["出行", "旅游", "旅行", "出远门"]
    lawsuit_keywords = ["官", "诉讼", "官司", "纠纷", "法律"]
    family_keywords = ["家", "宅", "房", "居", "搬家"]
    
    for kw in finance_keywords:
        if kw in question:
            hints.append("财运类：取妻财爻为用神")
            break
    
    for kw in career_keywords:
        if kw in question:
            hints.append("事业类：取官鬼爻为用神")
            break
    
    for kw in love_keywords:
        if kw in question:
            hints.append("感情类：男测取妻财爻，女测取官鬼爻为用神")
            break
    
    for kw in health_keywords:
        if kw in question:
            hints.append("健康类：取官鬼爻（病症）+ 世爻（自身）为用神")
            break
    
    for kw in study_keywords:
        if kw in question:
            hints.append("学业类：取父母爻为用神")
            break
    
    for kw in travel_keywords:
        if kw in question:
            hints.append("出行类：以世爻为主，兼看子孙爻")
            break
    
    for kw in lawsuit_keywords:
        if kw in question:
            hints.append("诉讼类：取官鬼爻为用神")
            break
    
    for kw in family_keywords:
        if kw in question:
            hints.append("家宅类：取父母爻（建筑）+ 相应爻位看风水")
            break
    
    if not hints:
        hints.append("通用：以世爻为主，兼看卦象整体生克")
    
    return hints

# =============================================================================
# 第十部分：文本输出格式
# =============================================================================

def format_text_output(result):
    """将JSON结果格式化为可读的文本输出"""
    lines = []
    lines.append("=" * 50)
    lines.append("六爻纳甲排盘结果")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"求测问题：{result['question']}")
    lines.append(f"起卦方式：{result['method']}")
    
    dt = result['divination_time']
    lines.append(f"起卦时间：{dt['datetime']}")
    lines.append(f"年柱：{dt['year_stem_branch']}  月柱：{dt['month_stem_branch']}")
    lines.append(f"日柱：{dt['day_stem_branch']}  时柱：{dt['hour_stem_branch']}")
    lines.append(f"旬空：{', '.join(result['empty_branches'])}")
    lines.append("")
    
    oh = result['original_hexagram']
    lines.append("-" * 50)
    lines.append(f"本卦：{oh['name']}  (第{oh['sequence']}卦)")
    lines.append(f"卦象：{oh['upper_trigram']}上{oh['lower_trigram']}下")
    lines.append(f"归属：{oh['palace']}宫 ({oh['palace_element']}行)")
    lines.append(f"世代：{oh['generation']}卦")
    lines.append(f"卦辞：{oh['judgment']}")
    lines.append("")

    # 排盘表
    lines.append("排盘详表（从上爻到下爻）：")
    lines.append(f"{'爻位':<6}{'六神':<6}{'六亲':<6}{'地支':<6}{'干支':<8}{'动静':<8}{'标记':<8}")
    lines.append("-" * 50)
    
    for yao in reversed(oh['yao_lines']):  # 从上爻开始显示
        pos_str = yao['name']
        moving_str = "动" if yao['is_moving'] else "静"
        stem_branch = f"{yao['heavenly_stem']}{yao['earthly_branch']}"
        
        markers = []
        if yao['is_world']:
            markers.append("世")
        if yao['is_response']:
            markers.append("应")
        if yao['is_empty']:
            markers.append("空")
        marker_str = "/".join(markers)
        
        lines.append(f"{pos_str:<6}{yao['six_spirit']:<6}{yao['six_relation']:<6}{yao['earthly_branch']:<6}{stem_branch:<8}{moving_str:<8}{marker_str:<8}")
    
    lines.append("")
    
    # 变卦
    if result['changed_hexagram']:
        ch = result['changed_hexagram']
        lines.append("-" * 50)
        lines.append(f"变卦：{ch['name']}")
        lines.append(f"变卦卦辞：{ch['judgment']}")
        lines.append(f"动爻位置：{', '.join(f'第{n}爻' for n in ch['changed_lines'])}")
        lines.append("")
    
    # 用神建议
    lines.append("-" * 50)
    lines.append("用神建议：")
    for hint in result['analysis_hints']['possible_use_gods']:
        lines.append(f"  - {hint}")

    # 卜象解析（八卦类象）
    ti = result.get("trigram_interpretation") if isinstance(result, dict) else None
    if ti and isinstance(ti, dict) and not ti.get("error"):
        try:
            from trigram_symbolism import format_trigram_interpretation_text as _fmt_trigram
            formatted_trigram = _fmt_trigram(ti)
        except Exception:
            formatted_trigram = None
        if formatted_trigram:
            lines.append("")
            lines.append("-" * 50)
            lines.append("【卜象解析】")
            for tline in formatted_trigram.split("\n"):
                lines.append(f"  {tline}")

    # 经典分析摘要
    if 'advanced_analysis' in result:
        aa = result['advanced_analysis']
        lines.append("")
        lines.append("-" * 50)
        lines.append("经典断法分析：")
        
        # 伏藏
        if aa.get('hidden_spirit_analysis'):
            hs = aa['hidden_spirit_analysis']
            if isinstance(hs, dict) and hs.get('has_hidden_spirit'):
                lines.append(f"  [伏藏] {hs.get('summary', '')}")
                for detail in hs.get('details', []):
                    if isinstance(detail, dict):
                        status = "得出" if detail.get('can_emerge') else "不得出"
                        hr = detail.get('reason', '')
                        lines.append(
                            f"    - {detail.get('missing_relation', '?')}伏("
                            f"{detail.get('hidden_spirit', {}).get('branch', '?')})"
                            f"飞{detail.get('covering_spirit', {}).get('six_relation', '?')}"
                            f"({detail.get('covering_spirit', {}).get('branch', '?')})"
                            f" → {status}（{hr}）"
                        )
                    else:
                        lines.append(f"    - {detail}")
        
        # 暗动
        if aa.get('hidden_movement'):
            hm = aa['hidden_movement']
            if isinstance(hm, dict) and hm.get('has_hidden_movement'):
                lines.append(f"  [暗动] {hm.get('summary', '')}")
        
        # 月破
        if aa.get('monthly_break'):
            mb = aa['monthly_break']
            if isinstance(mb, dict) and mb.get('has_monthly_break'):
                lines.append(f"  [月破] {mb.get('summary', '')}")
        
        # 三合局
        if aa.get('triple_combo'):
            tc = aa['triple_combo']
            if isinstance(tc, dict) and tc.get('has_triple_combo'):
                lines.append(f"  [三合] {tc.get('summary', '')}")
                for cd in tc.get('details', []):
                    if isinstance(cd, dict) and cd.get('description'):
                        lines.append(f"    - {cd['description']}")
        
        # 进退神
        if aa.get('advance_retreat'):
            ar = aa['advance_retreat']
            if isinstance(ar, dict) and ar.get('has_advance_retreat'):
                lines.append(f"  [进退] {ar.get('summary', '')}")
        
        # 六合六冲
        if aa.get('clash_harmony'):
            ch = aa['clash_harmony']
            if isinstance(ch, dict) and ch.get('summary'):
                lines.append(f"  [卦格] {ch['summary']}")
        
        # 反吟伏吟
        if aa.get('repetition'):
            rp = aa['repetition']
            if isinstance(rp, dict) and rp.get('summary'):
                lines.append(f"  [吟反] {rp['summary']}")
        
        # 旺衰总结
        if aa.get('element_strength'):
            es = aa['element_strength']
            if es.get('summary'):
                lines.append(f"  [旺衰] {es['summary']}")
    
    # 应期精确日期（来自思维链 step5.9b）
    tc = result.get("thinking_chain", {})
    step5 = tc.get("step5_synthesis", {}) or result.get("step5_synthesis", {})
    yq = step5.get("yingqi_dates") if step5 else None

    if yq and yq.get("dates"):
        lines.append("")
        lines.append("-" * 50)
        lines.append(f"应期（{yq.get('speed', '待定')}）：")
        if yq.get("use_god_branch"):
            lines.append(f"  用神：{yq['use_god_branch']}（{yq.get('use_god_element', '?')}）"
                         f"  旺衰：{yq.get('strength_level', '?')}")
        for d in yq.get("dates", []):
            dt_str = d.get("date", "?")
            rule = d.get("rule", "")
            branch = d.get("branch", "")
            desc = d.get("description", "")
            branch_info = f" [{branch}]" if branch else ""
            lines.append(f"  {dt_str}{branch_info} — {rule}（{desc}）")
        if yq.get("summary_text"):
            lines.append(f"  → {yq['summary_text']}")

    lines.append("")
    lines.append("=" * 50)

    return "\n".join(lines)


# =============================================================================
# 第十部分(B)：思维链文本报告格式
# =============================================================================

def format_reading_output(result, chain=None):
    """将思维链结果格式化为清晰的中文占卜报告。

    参数
    ----
    result : dict
        build_hexagram_result() 返回的完整排盘结果。
    chain : dict, optional
        run_thinking_chain() 返回的五步思维链字典。
        若为 None，则尝试从 result["thinking_chain"] 读取。

    返回
    ----
    str
        格式化的中文报告文本。
    """
    if chain is None:
        chain = result.get("thinking_chain", {})

    step1 = chain.get("step1_situational_reading", {})
    step2 = chain.get("step2_use_god_identification", {})
    step3 = chain.get("step3_strength_analysis", {})
    step4 = chain.get("step4_change_analysis", {})
    step5 = chain.get("step5_synthesis", {})

    dt = result.get("divination_time", {})
    oh = result.get("original_hexagram", {})
    ch = result.get("changed_hexagram", {})
    aa = result.get("advanced_analysis", {})
    empty = result.get("empty_branches", [])
    hints = result.get("analysis_hints", {}).get("possible_use_gods", [])

    lines = []
    W = 52  # 报告宽度

    # ── 标题头 ──
    lines.append("=" * W)
    lines.append("六 爻 纳 甲 占 卜 报 告".center(W))
    lines.append("=" * W)
    lines.append("")

    # ── 求测信息 ──
    lines.append("【求测信息】")
    lines.append(f"  问  题：{result.get('question', '未指明')}")
    lines.append(f"  方  式：{result.get('method', '铜钱摇卦')}")
    lines.append(f"  时  间：{dt.get('datetime', '未知')}")
    lines.append("")

    # ── 干支历法 ──
    lines.append("【干支历法】")
    lines.append(f"  年柱：{dt.get('year_stem_branch', '?')}　"
                 f"月柱：{dt.get('month_stem_branch', '?')}")
    lines.append(f"  日柱：{dt.get('day_stem_branch', '?')}　"
                 f"时柱：{dt.get('hour_stem_branch', '?')}")
    if empty:
        lines.append(f"  旬  空：{', '.join(empty)}")
    lines.append("")

    # ── 卦象 ──
    lines.append("─" * W)
    lines.append("【卦象一览】")
    lines.append(f"  本 卦：{oh.get('name', '?')}　"
                 f"{oh.get('upper_trigram', '?')}上{oh.get('lower_trigram', '?')}下　"
                 f"第{oh.get('sequence', '?')}卦")
    lines.append(f"  归 属：{oh.get('palace', '?')}宫（{oh.get('palace_element', '?')}行）"
                 f"　{oh.get('generation', '?')}卦")
    if oh.get('judgment'):
        lines.append(f"卦　辞：{oh['judgment']}")
    lines.append("")

    # 排盘表（上爻→下爻）
    yao_lines = oh.get("yao_lines", [])
    if yao_lines:
        lines.append("  排盘详表：")
        lines.append(f"  {'爻位':<4}{'六神':<5}{'六亲':<5}{'地支':<5}{'干支':<7}{'动静':<5}{'标记':<6}")
        lines.append("  " + "-" * (W - 4))
        for yao in reversed(yao_lines):
            pos_s = yao.get("name", "?")
            spirit_s = yao.get("six_spirit", "?")
            rel_s = yao.get("six_relation", "?")
            branch_s = yao.get("earthly_branch", "?")
            stem_s = f"{yao.get('heavenly_stem', '')}{branch_s}"
            moving_s = "动" if yao.get("is_moving") else "静"
            markers = []
            if yao.get("is_world"):
                markers.append("世")
            if yao.get("is_response"):
                markers.append("应")
            if yao.get("is_empty"):
                markers.append("空")
            mark_s = "/".join(markers) if markers else "－"
            lines.append(
                f"  {pos_s:<4}{spirit_s:<5}{rel_s:<5}{branch_s:<5}{stem_s:<7}{moving_s:<5}{mark_s:<6}"
            )
        lines.append("")

    # 变卦
    if ch:
        lines.append(f"  变 卦：{ch.get('name', '?')}")
        if ch.get('judgment'):
            lines.append(f"  变卦辞：{ch['judgment']}")
        changed_pos = ch.get("changed_lines", [])
        if changed_pos:
            pos_txt = "、".join(f"第{n}爻" for n in changed_pos)
            lines.append(f"  动 爻：{pos_txt}")
        lines.append("")

    # ── 用神建议 ──
    if hints:
        lines.append("─" * W)
        lines.append("【用神建议】")
        for h in hints[:5]:
            lines.append(f"  · {h}")
        lines.append("")

    # ── 五步思维链分析 ──
    lines.append("=" * W)
    lines.append("【五步思维链分析】")
    lines.append("=" * W)

    # ── Step 1: 观局 ──
    lines.append("")
    lines.append("  ┌── Step 1 ─ 观局 ──────────────────────────┐")
    if step1:
        lines.append(f"  │ 本卦：{step1.get('hexagram_name', '?')}　"
                     f"{step1.get('palace', '?')}宫　{step1.get('palace_element', '?')}行")
        desc1 = step1.get("description", "")
        if desc1:
            # 分行显示长描述
            for para in desc1.split("。"):
                para = para.strip()
                if para:
                    lines.append(f"  │ {para}")
    lines.append("  └──────────────────────────────────────────┘")

    # ── Step 2: 定用 ──
    lines.append("")
    lines.append("  ┌── Step 2 ─ 定用神 ────────────────────────┐")
    if step2:
        lines.append(f"  │ 用神：{step2.get('use_god_category', '?')}　"
                     f"五行：{step2.get('use_god_element', '?')}")
        pos2 = step2.get("selected_position")
        if pos2:
            lines.append(f"  │ 位置：第{pos2}爻　"
                     f"六亲：{step2.get('selected_relation', '?')}")
        desc2 = step2.get("description", "")
        if desc2:
            for para in desc2.split("。"):
                para = para.strip()
                if para:
                    lines.append(f"  │ {para}")
        # 原神/忌神
        ys_text = step2.get("yuan_shen_text", "")
        js_text = step2.get("ji_shen_text", "")
        if ys_text:
            lines.append(f"  │ 原神：{ys_text}")
        if js_text:
            lines.append(f"  │ 忌神：{js_text}")
    lines.append("  └──────────────────────────────────────────┘")

    # ── Step 3: 断旺 ──
    lines.append("")
    lines.append("  ┌── Step 3 ─ 断旺衰 ────────────────────────┐")
    if step3:
        strength = step3.get("strength_level", "?")
        eff_score = step3.get("effective_score", 0)
        lines.append(f"  │ 旺衰等级：{strength}（评分 {eff_score:.2f}）")
        desc3 = step3.get("description", "")
        if desc3:
            for para in desc3.split("。"):
                para = para.strip()
                if para:
                    lines.append(f"  │ {para}")
        # 关键因素
        factors = step3.get("key_factors", step3.get("factors", []))
        if isinstance(factors, list) and factors:
            lines.append(f"  │ 关键因素：")
            for f in factors[:6]:
                lines.append(f"  │   · {f}")
    lines.append("  └──────────────────────────────────────────┘")

    # ── Step 4: 察变 ──
    lines.append("")
    lines.append("  ┌── Step 4 ─ 察动变 ────────────────────────┐")
    if step4:
        net_eff = step4.get("net_effect", 0)
        net_desc = step4.get("net_effect_description", "无动爻")
        lines.append(f"  │ 动变净效应：{net_eff:+.2f}（{net_desc}）")
        desc4 = step4.get("description", "")
        if desc4:
            for para in desc4.split("。"):
                para = para.strip()
                if para:
                    lines.append(f"  │ {para}")
        # 逐爻分析
        yaos_detail = step4.get("yao_analysis", step4.get("moving_details", []))
        if isinstance(yaos_detail, list) and yaos_detail:
            lines.append(f"  │ 逐爻分析：")
            for yd in yaos_detail[:6]:
                if isinstance(yd, dict):
                    yd_pos = yd.get("position", "?")
                    yd_desc = yd.get("description", yd.get("analysis", ""))
                    if not yd_desc and yd.get("change_type"):
                        yd_desc = yd["change_type"]
                    if yd_desc:
                        lines.append(f"  │   第{yd_pos}爻：{yd_desc}")
                elif isinstance(yd, str) and yd:
                    lines.append(f"  │   {yd}")
    lines.append("  └──────────────────────────────────────────┘")

    # ── Step 5: 综合 ──
    lines.append("")
    lines.append("  ┌── Step 5 ─ 综合判断 ──────────────────────┐")
    if step5:
        verdict = step5.get("verdict", "?")
        final_score = step5.get("final_score", 0)
        verdict_desc = step5.get("verdict_description", "")
        confidence = step5.get("confidence", "?")
        conf_desc = step5.get("confidence_description", "")

        lines.append(f"  │ 判　语：{verdict}（{final_score:.2f}分）")
        if verdict_desc:
            lines.append(f"  │ 说　明：{verdict_desc}")
        lines.append(f"  │ 置信度：{confidence}%（{conf_desc}）")

        # 格局识别
        sp = step5.get("special_pattern", {})
        if isinstance(sp, dict) and sp.get("pattern"):
            lines.append(f"  │ 格　局：{sp['pattern']} — {sp.get('description', '')}")

        # 各项调整明细
        adj_items = []
        bc = step5.get("base_score", 0)
        adj_items.append(f"基础旺衰 {bc:.2f}")
        ce = step5.get("change_net_effect", 0)
        if ce != 0:
            adj_items.append(f"动变 {ce:+.2f}")
        ha = step5.get("hex_adjustment", 0)
        if ha != 0:
            hr = step5.get("hex_adjustment_reason", "")
            adj_items.append(f"卦体 {ha:+.1f}（{hr}）")
        sa = step5.get("spirit_adjustment", 0)
        if sa != 0:
            sr = step5.get("spirit_adjustment_reasons", "")
            if isinstance(sr, list) and sr:
                sr = "、".join(sr)
            adj_items.append(f"六神 {sa:+.1f}（{sr}）")
        tp_s = step5.get("tp_score", 0)
        if tp_s != 0:
            tp_r = step5.get("tp_reason", "")
            adj_items.append(f"三刑 {tp_s:+.1f}（{tp_r}）")
        dmb = step5.get("dmb_adjustment", 0)
        if dmb != 0:
            adj_items.append(f"日月合 {dmb:+.2f}")
        sb_a = step5.get("sb_adjustment", 0)
        if sb_a != 0:
            adj_items.append(f"六破 {sb_a:+.2f}")
        hm_c = step5.get("hidden_movement_count", 0)
        if hm_c and hm_c > 0:
            hm_r = step5.get("hidden_movement_reason", "")
            hm_m = step5.get("hidden_movement_modifier", 0)
            adj_items.append(f"暗动 {hm_m:+.1f}（{hm_r}）")
        ghr = step5.get("greedy_harmony_reason", "")
        if ghr:
            ghs = step5.get("greedy_harmony_score", 0)
            adj_items.append(f"贪合 {ghs:+.2f}（{ghr}）")
        pa = step5.get("pattern_adjustment", 0)
        if pa != 0:
            adj_items.append(f"格局 {pa:+.1f}")

        if adj_items:
            lines.append(f"  │ 评分明细：{' + '.join(adj_items)} = {final_score:.2f}")
    lines.append("  └──────────────────────────────────────────┘")

    # ── 格局识别摘要 ──
    lines.append("")
    lines.append("─" * W)
    lines.append("【格局识别】")
    patterns_found = []
    if isinstance(aa, dict):
        # 伏藏
        hs = aa.get("hidden_spirit_analysis", {})
        if isinstance(hs, dict) and hs.get("has_hidden_spirit"):
            patterns_found.append(f"伏藏：{hs.get('summary', '')}")
        # 暗动
        hm = aa.get("hidden_movement", {})
        if isinstance(hm, dict) and hm.get("has_hidden_movement"):
            patterns_found.append(f"暗动：{hm.get('summary', '')}")
        # 月破
        mb = aa.get("monthly_break", {})
        if isinstance(mb, dict) and mb.get("has_monthly_break"):
            patterns_found.append(f"月破：{mb.get('summary', '')}")
        # 三合局
        tc = aa.get("triple_combo", {})
        if isinstance(tc, dict) and tc.get("has_triple_combo"):
            patterns_found.append(f"三合局：{tc.get('summary', '')}")
        # 进退神
        ar = aa.get("advance_retreat", {})
        if isinstance(ar, dict) and ar.get("has_advance_retreat"):
            patterns_found.append(f"进退神：{ar.get('summary', '')}")
        # 六合六冲
        ch_aa = aa.get("clash_harmony", {})
        if isinstance(ch_aa, dict) and ch_aa.get("summary"):
            patterns_found.append(f"卦格：{ch_aa['summary']}")
        # 反吟伏吟
        rp = aa.get("repetition", {})
        if isinstance(rp, dict) and rp.get("summary"):
            patterns_found.append(f"吟反：{rp['summary']}")
        # 三刑
        tp = aa.get("three_punishments", {})
        if isinstance(tp, dict) and tp.get("has_punishment"):
            patterns_found.append(f"三刑：{tp.get('summary', '')}")
        # 六亲持世
        sy = aa.get("shi_yao_relation", {})
        if isinstance(sy, dict) and sy.get("description"):
            patterns_found.append(f"六亲持世：{sy['description']}")
        # 纳音
        ny = aa.get("nayin", {})
        if isinstance(ny, dict) and ny.get("description"):
            patterns_found.append(f"纳音：{ny['description']}")

    if step5 and isinstance(sp, dict) and sp.get("pattern"):
        patterns_found.append(f"特殊格局：{sp['pattern']}（{sp.get('description', '')}）")

    if patterns_found:
        for p in patterns_found:
            lines.append(f"  · {p}")
    else:
        lines.append("  （无特殊格局）")
    lines.append("")

    # ── 卜象解析 ──
    ti_r = result.get("trigram_interpretation") if isinstance(result, dict) else None
    if ti_r and isinstance(ti_r, dict) and not ti_r.get("error"):
        try:
            from trigram_symbolism import format_trigram_interpretation_text as _fmt_trigram_r
            tri_lines = _fmt_trigram_r(ti_r).split("\n")
        except Exception:
            tri_lines = []
        if tri_lines:
            lines.append("─" * W)
            lines.append("【卜象解析】")
            for tl in tri_lines:
                lines.append(tl)
            lines.append("")

    # ── 应期推断 ──
    lines.append("─" * W)
    lines.append("【应期推断】")
    timing = step5.get("timing", {}) if step5 else {}
    ying_dates = step5.get("yingqi_dates", {}) if step5 else {}

    if timing:
        speed = timing.get("speed", "待断")
        summary_t = timing.get("summary_text", "")
        lines.append(f"  整体节奏：{speed}")
        if summary_t:
            lines.append(f"  方法综述：{summary_t}")

    if ying_dates and ying_dates.get("dates"):
        use_branch = ying_dates.get("use_god_branch", "")
        use_elem = ying_dates.get("use_god_element", "")
        if use_branch:
            lines.append(f"  用　　神：{use_branch}（{use_elem}）")
        strength_l = ying_dates.get("strength_level", "")
        if strength_l:
            lines.append(f"  旺　　衰：{strength_l}")
        lines.append(f"  应期日期：")
        for d in ying_dates.get("dates", []):
            dt_s = d.get("date", "?")
            rule = d.get("rule", "")
            branch = d.get("branch", "")
            desc = d.get("description", "")
            br_info = f" [{branch}]" if branch else ""
            lines.append(f"    {dt_s}{br_info} — {rule}（{desc}）")
        yq_summary = ying_dates.get("summary_text", "")
        if yq_summary:
            lines.append(f"  小　　结：{yq_summary}")
    elif step5 and step5.get("verdict"):
        # fallback: use step5 verdict to estimate timing
        verdict_now = step5.get("verdict", "")
        if verdict_now in ("大吉", "吉"):
            lines.append("  应期推断：事顺势而为，逢值逢合应速。")
        elif verdict_now in ("凶", "平凶"):
            lines.append("  应期推断：守静安时，待用神旺相之月可转。")
        else:
            lines.append("  应期推断：吉凶参半，逢值逢冲应之。")
    else:
        lines.append("  应期推断：待定")
    lines.append("")

    # ── 最终判语 ──
    lines.append("=" * W)
    lines.append("【最 终 判 语】".center(W))
    lines.append("=" * W)
    lines.append("")

    if step5:
        verdict = step5.get("verdict", "待定")
        final_score = step5.get("final_score", 0)
        verdict_desc = step5.get("verdict_description", "")
        confidence = step5.get("confidence", "?")

        # 判语大字
        lines.append(f"　　　　　　◖ {verdict} ◗")
        lines.append("")
        if verdict_desc:
            lines.append(f"　　{verdict_desc}")
        lines.append("")
        lines.append(f"　　综合评分：{final_score:.2f} / 5.00")
        lines.append(f"　　置信　度：{confidence}%（{step5.get('confidence_description', '')}）")

        # pattern override notes
        pvn = step5.get("pattern_verdict_note", "")
        if pvn:
            lines.append("")
            lines.append(f"　　※ {pvn}")
        otn = step5.get("officer_tomb_verdict_note", "")
        if otn:
            lines.append("")
            lines.append(f"　　※ {otn}")

        # 经典引文
        cqs = step5.get("classical_quotes", [])
        if isinstance(cqs, list) and cqs:
            lines.append("")
            lines.append("　　【经典引文】")
            for cq in cqs:
                if isinstance(cq, dict):
                    src = cq.get("source", "")
                    quote = cq.get("quote", "")
                    lines.append(f"　　· {src}：「{quote}」")

        # 卦身摘要
        body_note = step5.get("hexagram_body_note", "")
        if body_note:
            lines.append("")
            lines.append(f"　　【卦身】{body_note}")

    lines.append("")
    lines.append("=" * W)
    lines.append("报告中　·　仅供参考".center(W))
    lines.append("=" * W)

    return "\n".join(lines)


# =============================================================================
# 第十一部分：真太阳时校正
# =============================================================================

def apply_true_solar_time(year, month, day, hour, longitude, standard_longitude=120.0):
    """
    真太阳时校正
    返回校正后的 hour 和 minute。
    - longitude: 经度, 东经为正
    - standard_longitude: 标准子午线经度 (中国CST = 120)

    时差 = (经度 - 标准子午线) * 4 分钟
    均时差(Equation of Time) 采用简化公式: ~±16分钟
    """
    # 经度差修正 (每度4分钟)
    longitude_offset_minutes = (longitude - standard_longitude) * 4.0

    # 均时差简化公式 (单位: 分钟)
    # 基于日数n (1-365), B = (n-81)*360/365
    day_of_year = (datetime(year, month, day) - datetime(year, 1, 1)).days + 1
    B = math.radians((day_of_year - 81) * 360 / 365.0)
    eot_minutes = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)

    total_offset = longitude_offset_minutes + eot_minutes

    # 应用到输入时间
    total_minutes = hour * 60 + int(total_offset)

    # Handle rollover
    while total_minutes < 0:
        total_minutes += 1440
    while total_minutes >= 1440:
        total_minutes -= 1440

    corrected_hour = total_minutes // 60
    corrected_minute = total_minutes % 60

    # 转为时辰 (23-1点子时, 1-3点丑时, etc.)
    shichen = _hour_to_shichen(corrected_hour, corrected_minute)

    return {
        "corrected_hour": corrected_hour,
        "corrected_minute": corrected_minute,
        "shichen": shichen,
        "offset_minutes": int(total_offset),
    }


def _hour_to_shichen(hour, minute=0):
    """将小时和分钟转换为十二时辰名称"""
    total = hour * 60 + minute
    if total >= 23 * 60 or total < 1 * 60:
        return "子"
    if total < 3 * 60:
        return "丑"
    if total < 5 * 60:
        return "寅"
    if total < 7 * 60:
        return "卯"
    if total < 9 * 60:
        return "辰"
    if total < 11 * 60:
        return "巳"
    if total < 13 * 60:
        return "午"
    if total < 15 * 60:
        return "未"
    if total < 17 * 60:
        return "申"
    if total < 19 * 60:
        return "酉"
    if total < 21 * 60:
        return "戌"
    return "亥"


def handle_zi_hour(hour, minute, year, month, day):
    """子时（夜子／晨子）判定。

    默认口径：日辰以当日历日为准，夜子时不作次日。
      - 夜子时（旧码误标"早子时"）23:00–23:59 → 日柱用当日
      - 晨子时（旧码误标"晚子时"）00:00–00:59 → 日柱用当日

    历史缺陷（2026-09-22 修）：旧实现在 hour == 0 时返回**翌日**日柱，
    等于把 00:00–01:00 起的所有卦的日辰推后一天——任何流派都不持此说。
    欲采"23 点换日"一派，用 `--zi-hour-type late` 显式指定，不默认生效。

    Returns:
        dict（含 type/shichen/day_* 与说明），非子时返回 None
    """
    base_date = datetime(year, month, day)

    if hour == 23:
        zi_type, label = "night_zi", "夜子时(23:00-00:00)"
    elif hour == 0:
        zi_type, label = "morning_zi", "晨子时(00:00-01:00)"
    else:
        return None

    return {
        "type": zi_type,
        "shichen": "子",
        "day_date": base_date,
        "day_year": base_date.year,
        "day_month": base_date.month,
        "day_day": base_date.day,
        "description": f"{label}，{base_date.strftime('%Y-%m-%d')}日子时，日柱用当日",
    }


# =============================================================================
# 第十二部分(A)：梅花易数互参
# =============================================================================

def mei_hua_divination(question: str, year: int, month: int, day: int,
                        hour: int, number: int = None) -> dict:
    """
    梅花易数起卦互参。

    先天八卦数（先天八卦，伏羲八卦序）：
    1=乾  2=兑  3=离  4=震  5=巽  6=坎  7=艮  8=坤

    规则：
    - 上卦 = (年 + 月 + 日) mod 8
    - 下卦 = (年 + 月 + 日 + 时) mod 8
    - 动爻 = (年 + 月 + 日 + 时) mod 6 + 1

    Body/Use 体用：
    - 动爻在下卦(1-3爻) → 上卦为体 下卦为用
    - 动爻在上卦(4-6爻) → 下卦为体 上卦为用
    - 体用五行生克定吉凶
    """
    trigram_map = {
        1: ("乾", "天", "金"), 2: ("兑", "泽", "金"),
        3: ("离", "火", "火"), 4: ("震", "雷", "木"),
        5: ("巽", "风", "木"), 6: ("坎", "水", "水"),
        7: ("艮", "山", "土"), 8: ("坤", "地", "土"),
    }

    # 也可选数字起卦
    if number is not None:
        upper_idx = number % 8
        lower_idx = (number + hour) % 8
        moving_yao = (number + hour) % 6 + 1
    else:
        upper_idx = (year + month + day) % 8
        lower_idx = (year + month + day + hour) % 8
        moving_yao = (year + month + day + hour) % 6 + 1

    # 将 0 映射到 8（坤）
    upper_idx = upper_idx if upper_idx > 0 else 8
    lower_idx = lower_idx if lower_idx > 0 else 8

    upper = trigram_map[upper_idx]
    lower = trigram_map[lower_idx]

    # 体用判断：有动爻的一方为用，无动的一方为体
    # 动爻 1-3 → 动在下卦 → 上卦为体，下卦为用
    # 动爻 4-6 → 动在上卦 → 下卦为体，上卦为用
    if moving_yao <= 3:
        body, use = upper, lower
    else:
        body, use = lower, upper

    body_elem = body[2]
    use_elem = use[2]

    # 五行相生（Sheng）：木→火→土→金→水→木
    SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    # 五行相克（Ke）：木→土→水→火→金→木
    KE = {"木": "土", "火": "金", "土": "水", "水": "火", "金": "木"}

    if body_elem == use_elem:
        interaction = "比和"      # 大吉
        score = 3.5
    elif SHENG.get(body_elem) == use_elem:
        interaction = "体生用"    # 泄气
        score = 2.0
    elif SHENG.get(use_elem) == body_elem:
        interaction = "用生体"    # 进气大吉
        score = 4.0
    elif KE.get(body_elem) == use_elem:
        interaction = "体克用"    # 可控
        score = 2.5
    else:
        interaction = "用克体"    # 大凶
        score = 0.5

    # 动爻所在卦
    moving_in_lower = (moving_yao <= 3)

    return {
        "method": "梅花易数",
        "upper_hexagram": upper[0],
        "lower_hexagram": lower[0],
        "upper_nature": upper[1],
        "lower_nature": lower[1],
        "full_hexagram": f"{upper[0]}上{lower[0]}下",
        "moving_yao": moving_yao,
        "moving_in_lower": moving_in_lower,
        "body": body[0],
        "use": use[0],
        "body_element": body_elem,
        "use_element": use_elem,
        "interaction": interaction,
        "score": score,
        "interpretation": (
            f"{body[0]}({body_elem})为体，{use[0]}({use_elem})为用，"
            f"体用{interaction}"
        ),
        "auspicious": score >= 3.0,
        "details": {
            "upper_trigram": {"name": upper[0], "element": upper[2]},
            "lower_trigram": {"name": lower[0], "element": lower[2]},
            "moving_yao_position": moving_yao,
            "moving_in_lower_trigram": moving_in_lower,
        },
    }


def mei_hua_cross_reference(question: str, year: int, month: int, day: int,
                             hour: int) -> dict:
    """
    梅花易数 + 六爻互参。

    同时起：
    1. 六爻卦（铜钱摇卦/时间起卦）
    2. 梅花易数卦（时间/数字起卦）

    然后交叉验证两个体系的一致性。
    """
    # 六爻起卦 — 用时间起卦
    liuyao_yao_values = time_based_hexagram(year, month, day, hour)
    liuyao_result = build_hexagram_result(
        liuyao_yao_values, question, "时间起卦(六爻)",
        year, month, day, hour
    )

    # 运行思维链
    liuyao_chain = None
    try:
        from thinking_chain import run_thinking_chain
        chain_result = run_thinking_chain(liuyao_result)
        liuyao_chain = chain_result.get("thinking_chain", chain_result)
    except ImportError:
        pass

    # 梅花起卦
    mei_hua_result = mei_hua_divination(question, year, month, day, hour)

    # 交叉验证
    cross_checks = []

    # 比较两卦的 吉凶方向
    liuyao_score = None
    liuyao_verdict = ""
    if liuyao_chain:
        s5 = liuyao_chain.get("step5_synthesis", {})
        liuyao_score = s5.get("final_score", 2.5)
        liuyao_verdict = s5.get("verdict", "")

    mei_hua_score = mei_hua_result.get("score", 2.5)

    # 判定方向是否一致
    liuyao_favorable = liuyao_score >= 2.5 if liuyao_score is not None else True
    mei_hua_favorable = mei_hua_score >= 3.0

    if liuyao_favorable == mei_hua_favorable:
        cross_checks.append({
            "check": "吉凶方向一致性",
            "result": "一致",
            "detail": f"六爻{'吉' if liuyao_favorable else '凶'}向，梅花{'吉' if mei_hua_favorable else '凶'}向",
        })
    else:
        cross_checks.append({
            "check": "吉凶方向一致性",
            "result": "矛盾",
            "detail": f"六爻{'吉' if liuyao_favorable else '凶'}向，梅花{'吉' if mei_hua_favorable else '凶'}向 — 需审慎解读",
        })

    # 五行元素共振
    liuyao_element = liuyao_result.get("original_hexagram", {}).get("palace_element", "")
    mei_hua_body_elem = mei_hua_result.get("body_element", "")
    mei_hua_use_elem = mei_hua_result.get("use_element", "")

    if liuyao_element and liuyao_element in (mei_hua_body_elem, mei_hua_use_elem):
        cross_checks.append({
            "check": "五行元素共振",
            "result": "共振",
            "detail": f"六爻宫五行({liuyao_element})与梅花体/用五行({mei_hua_body_elem}/{mei_hua_use_elem})共振",
        })
    else:
        cross_checks.append({
            "check": "五行元素共振",
            "result": "无显著共振",
            "detail": f"六爻宫五行({liuyao_element})，梅花体用五行({mei_hua_body_elem}/{mei_hua_use_elem})",
        })

    # 综合判断
    agree_count = sum(1 for c in cross_checks if c["result"] in ("一致", "共振"))
    total_checks = len(cross_checks)
    confidence = agree_count / total_checks if total_checks > 0 else 0.5

    return {
        "mode": "梅花易数互参",
        "liuyao_result": liuyao_result,
        "mei_hua_result": mei_hua_result,
        "thinking_chain": liuyao_chain,
        "cross_checks": cross_checks,
        "cross_confidence": confidence,
        "summary": (
            f"六爻卦：{liuyao_result['original_hexagram']['name']}"
            f"（{liuyao_verdict}，评分{liuyao_score:.2f}）；"
            f"梅花卦：{mei_hua_result['full_hexagram']}"
            f"（{mei_hua_result['interaction']}，评分{mei_hua_score:.2f}）；"
            f"交叉验证置信度{confidence:.0%}"
        ),
    }


# =============================================================================
# 第十二部分(B)：批量演卦对比
# =============================================================================

def batch_divination(question: str, n: int = 10, method: str = "time",
                     year: int = None, month: int = None, day: int = None,
                     hour: int = None, seed: int = None) -> dict:
    """
    批量演卦对比。

    生成 N 个卦（使用不同种子或时间扰动），积累统计信息：
    - 吉凶分布
    - 平均评分
    - 最常见卦
    - 卦体多样性
    """
    from collections import Counter
    from datetime import datetime

    if year is None:
        now = datetime.now()
        year, month, day, hour = now.year, now.month, now.day, now.hour

    results = []
    rng = random.Random(seed) if seed is not None else random.Random()

    for i in range(n):
        # 对铜钱模式用不同种子；对时间模式加了分钟/秒扰动
        if method == "coin":
            sub_rng = random.Random(seed + i if seed is not None else rng.randint(0, 999999))
            yao_values = coin_toss(random_gen=sub_rng)
            m = "铜钱摇卦"
        elif method == "number":
            a = rng.randint(1, 1000)
            b = rng.randint(1, 1000)
            c = rng.randint(1, 6)
            yao_values = number_based_hexagram(a, b, c)
            m = f"数字起卦({a},{b},{c})"
        else:
            # 时间起卦 + i 秒扰动（模拟不同时刻起卦）
            yao_values = time_based_hexagram(year, month, day, hour)
            m = "时间起卦"

        result = build_hexagram_result(
            yao_values, question, m, year, month, day, hour
        )

        # 运行思维链
        try:
            from thinking_chain import run_thinking_chain
            chain_full = run_thinking_chain(result)
            chain = chain_full.get("thinking_chain", chain_full)
        except ImportError:
            chain = None

        s5 = chain.get("step5_synthesis", {}) if chain else {}
        verdict = s5.get("verdict", "待定")
        fscore = s5.get("final_score", 2.5)
        hex_name = result["original_hexagram"]["name"]

        results.append({
            "index": i + 1,
            "hexagram": hex_name,
            "verdict": verdict,
            "score": fscore,
            "method": m,
            "result": result,
            "thinking_chain": chain,
        })

    # 统计
    verdicts = [r["verdict"] for r in results]
    scores = [r["score"] for r in results]
    hexagrams = [r["hexagram"] for r in results]
    hex_counts = Counter(hexagrams)

    # 吉凶分布（基于 verdict 字段）
    dist_auspicious = sum(1 for v in verdicts if "吉" in v and "凶" not in v)
    dist_inauspicious = sum(1 for v in verdicts if "凶" in v and "吉" not in v)
    dist_mixed = sum(1 for v in verdicts if "平" in v or ("吉" in v and "凶" in v))

    # 平均评分
    avg_score = sum(scores) / len(scores) if scores else 0.0
    min_score = min(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0

    # 最常见卦
    most_common = hex_counts.most_common(1)[0] if hex_counts else None

    # 卦体多样性
    diversity = len(hex_counts)

    # 稳定性：同一卦出现 N 次以上为稳定
    stability_threshold = max(2, n // 3)  # 至少出现 n/3 次视为稳定
    stable_hex = [(h, c) for h, c in hex_counts.items() if c >= stability_threshold]
    is_stable = len(stable_hex) > 0 and stable_hex[0][1] >= stability_threshold

    return {
        "mode": "批量演卦对比",
        "n": n,
        "question": question,
        "verdict_distribution": {
            "吉": dist_auspicious,
            "凶": dist_inauspicious,
            "平/混合": dist_mixed,
        },
        "score_statistics": {
            "mean": round(avg_score, 3),
            "min": round(min_score, 3),
            "max": round(max_score, 3),
            "range": round(max_score - min_score, 3),
        },
        "most_common_hexagram": {
            "name": most_common[0],
            "count": most_common[1],
            "percentage": round(most_common[1] / n * 100, 1),
        } if most_common else None,
        "hexagram_diversity": diversity,
        "total_hexagrams": len(HEXAGRAMS),
        "diversity_ratio": round(diversity / n, 3),
        "is_stable": is_stable,
        "stable_hexagrams": [
            {"name": h, "count": c} for h, c in sorted(stable_hex, key=lambda x: -x[1])
        ],
        "hexagram_frequency": hex_counts.most_common(),
        "individual_results": results,
        "summary": (
            f"共演{n}卦：吉{dist_auspicious}、凶{dist_inauspicious}、平{dist_mixed}；"
            f"均分{avg_score:.2f}（{min_score:.2f}~{max_score:.2f}）；"
            f"出现{diversity}种不同卦；"
            + (f"最频为{most_common[0]}（{most_common[1]}次）" if most_common else "")
            + (f"，卦象{'稳定' if is_stable else '不稳定'}"
              if is_stable else "")
        ),
    }


# =============================================================================
# 第十二部分(C)：命令行接口
# =============================================================================

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="六爻纳甲装卦引擎 - 完整的六爻占卜系统（含梅花易数互参、批量演卦、反幻觉校验）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python liuyao_engine.py --mode coin --question "我的投资运势如何？"
  python liuyao_engine.py --mode time --datetime "2026-09-18 14:30"
  python liuyao_engine.py --mode number --numbers "3,5,8"
  python liuyao_engine.py --mode manual --yao "7,8,9,7,6,8"
  python liuyao_engine.py --mode mei_hua --question "测试" --year 2024 --month 6 --day 15 --hour 10
  python liuyao_engine.py --batch 5 --question "测投资"
  python liuyao_engine.py --verify interp.txt --mode coin --question "测投资"
  python liuyao_engine.py --mode coin --output json
  python liuyao_engine.py --mode quick --question "今日运程"
        """
    )

    parser.add_argument(
        "--mode",
        choices=["coin", "time", "number", "manual", "mei_hua", "quick"],
        default="coin",
        help="起卦方式 (默认: coin)。mei_hua 模式下同时起六爻与梅花两卦并交叉验证；quick 为直觉速读模式"
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

    # ── 梅花易数互参专用参数 ──
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="起卦年份（梅花易数互参模式必填）"
    )
    parser.add_argument(
        "--month",
        type=int,
        default=None,
        help="起卦月份（梅花易数互参模式必填）"
    )
    parser.add_argument(
        "--day",
        type=int,
        default=None,
        help="起卦日期（梅花易数互参模式必填）"
    )

    # ── 批量演卦专用参数 ──
    parser.add_argument(
        "--batch",
        type=int,
        default=None,
        help="批量起卦次数（生成 N 个卦并统计对比）。同时使用 coin 模式时以不同种子起卦"
    )

    # ── 反幻觉校验专用参数 ──
    parser.add_argument(
        "--verify",
        type=str,
        default=None,
        help="对指定的 LLM 解读文件执行反幻觉校验（需配合其他起卦参数或传入 --engine-result JSON）"
    )
    parser.add_argument(
        "--engine-result",
        type=str,
        default=None,
        help="引擎输出 JSON 文件路径（--verify 模式下可选，默认使用本次起卦的引擎结果）"
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


def apply_depth_limit(text: str, depth: str) -> str:
    """解读深度限制器

    参数
    ----
    text : str
        原始文本输出。
    depth : str
        brief / standard / full

    返回
    ----
    str
        按深度截断后的文本。
    """
    limits = {
        "brief": 300,     # ~150汉字
        "standard": 800,  # ~400汉字
        "full": 99999,    # 无限制
    }
    limit = limits.get(depth, 99999)
    if len(text) <= limit:
        return text

    # Smart truncation at sentence boundary
    truncated = text[:limit]
    last_period = truncated.rfind("。")
    last_newline = truncated.rfind("\n")
    cut_at = max(last_period, last_newline)
    if cut_at > limit * 0.5:
        return truncated[:cut_at + 1] + "\n...(输出已达深度上限，使用 --depth full 获取全文)"
    return truncated + "...[截断]"


def _apply_depth_to_result(result: dict, depth: str) -> dict:
    """对 JSON 结果中的描述字段按深度截断。

    brief 模式下保留关键判语和标准字段，截断长描述。
    """
    if depth == "full":
        return result

    # Fields in result that contain long descriptive text
    long_fields_top = ["summary_text"]
    thinking_keys = ["thinking_chain", "step5_synthesis"]

    # Truncate top-level long fields
    for field in long_fields_top:
        val = result.get(field, "")
        if isinstance(val, str) and len(val) > 200:
            result[field] = apply_depth_limit(val, "brief")

    # Walk into thinking_chain → step5_synthesis
    tc = result.get("thinking_chain", {})
    if isinstance(tc, dict):
        for key in tc:
            step = tc[key]
            if isinstance(step, dict):
                for desc_key in ("description", "verdict_description",
                                 "reasoning_chain"):
                    val = step.get(desc_key, "")
                    if isinstance(val, str) and len(val) > 150:
                        step[desc_key] = apply_depth_limit(
                            val, "brief" if depth == "brief" else "standard"
                        )
                # step5 summary_text
                if key == "step5_synthesis":
                    summary = step.get("summary_text", "")
                    if isinstance(summary, str) and len(summary) > 200:
                        step["summary_text"] = apply_depth_limit(summary, depth)

    return result


# ---------------------------------------------------------------------------
# 辅助函数：批量演卦 / 反幻觉校验 / 梅花文本格式化
# ---------------------------------------------------------------------------

def _format_mei_hua_text(cross_result: dict) -> str:
    """将梅花易数互参结果格式化为可读文本。"""
    lines = []
    W = 52
    lines.append("=" * W)
    lines.append("梅花易数 · 六爻互参报告".center(W))
    lines.append("=" * W)
    lines.append("")

    # 梅花结果
    mh = cross_result.get("mei_hua_result", {})
    if mh:
        lines.append("【梅花易数卦】")
        lines.append(f"  卦　象：{mh.get('full_hexagram', '?')}")
        lines.append(f"　上卦：{mh.get('upper_hexagram', '?')}"
                     f"({mh.get('details', {}).get('upper_trigram', {}).get('element', '?')})")
        lines.append(f"　下卦：{mh.get('lower_hexagram', '?')}"
                     f"（{mh.get('details', {}).get('lower_trigram', {}).get('element', '?')}）")
        lines.append(f"　动爻：第{mh.get('moving_yao', '?')}爻"
                     f"（{'下卦' if mh.get('moving_in_lower') else '上卦'}）")
        lines.append(f"　体　用：{mh.get('body', '?')}({mh.get('body_element', '?')})"
                     f"为体，{mh.get('use', '?')}({mh.get('use_element', '?')})为用")
        lines.append(f"　关　系：{mh.get('interaction', '?')}（评分 {mh.get('score', 0):.2f}）")
        lines.append("")

    # 六爻结果
    lr = cross_result.get("liuyao_result", {})
    if lr:
        oh = lr.get("original_hexagram", {})
        ch = lr.get("changed_hexagram")
        lines.append("【六爻卦】")
        lines.append(f"　本卦：{oh.get('name', '?')}　"
                     f"{oh.get('upper_trigram', '?')}上{oh.get('lower_trigram', '?')}下")
        lines.append(f"　宫　位：{oh.get('palace', '?')}宫（{oh.get('palace_element', '?')}行）")
        if ch:
            lines.append(f"　变卦：{ch.get('name', '?')}　"
                         f"动爻 第{', '.join(str(n) for n in ch.get('changed_lines', []))}爻")
        lines.append("")

    # 交叉验证
    cross_checks = cross_result.get("cross_checks", [])
    confidence = cross_result.get("cross_confidence", 0)
    if cross_checks:
        lines.append("─" * W)
        lines.append("【交叉验证】")
        for cc in cross_checks:
            mark = "OK" if cc.get("result") in ("一致", "共振") else "!!"
            lines.append(f"  [{mark}] {cc.get('check', '?')}：{cc.get('detail', '')}")
        lines.append(f"　置信度：{confidence:.0%}")
        lines.append("")

    summary = cross_result.get("summary", "")
    if summary:
        lines.append("─" * W)
        lines.append(f"　{summary}")
        lines.append("")
    lines.append("=" * W)
    return "\n".join(lines)


def _check_batch_mode(args):
    """执行批量演卦模式。"""
    from datetime import datetime

    # 确定时间
    if args.datetime:
        dt = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M")
        year, month, day, hour = dt.year, dt.month, dt.day, dt.hour
    else:
        now = datetime.now()
        year, month, day, hour = now.year, now.month, now.day, now.hour

    if args.hour is not None:
        hour = args.hour

    # 决定批量起卦方法
    method = args.mode if args.mode in ("coin", "number") else "coin"

    batch_result = batch_divination(
        question=args.question,
        n=args.batch,
        method=method,
        year=year, month=month, day=day, hour=hour,
        seed=args.seed,
    )

    output_format = args.format if args.format is not None else args.output
    if output_format == "json":
        print(json.dumps(batch_result, ensure_ascii=False, indent=2, default=str))
    else:
        print(_format_batch_text(batch_result))


# ---------------------------------------------------------------------------
# 直觉速读模式 (Quick Reading) & 单爻断法 (Single-Yao Judgment)
# ---------------------------------------------------------------------------

def _identify_use_god(yao_lines: list, hints: list) -> tuple:
    """从建卦结果中识别用神六亲及对应爻位置。

    返回 ``(relation, position, branch)``，找不到则返回 ``(None, 0, "")``。
    """
    # 先从 hints 中提取六亲名
    target_relation = None
    for hint in hints:
        for rel in ["妻财", "官鬼", "父母", "子孙", "兄弟"]:
            if f"取{rel}" in hint:
                target_relation = rel
                break
        if target_relation:
            break
    if not target_relation:
        # 默认取妻财（通用问财运/结果）
        target_relation = "子孙"

    for y in yao_lines:
        if y["six_relation"] == target_relation:
            return target_relation, y["position"], y["earthly_branch"]
    # fallback: return first line info
    if yao_lines:
        y = yao_lines[0]
        return y["six_relation"], y["position"], y["earthly_branch"]
    return None, 0, ""


def _find_decisive_yao(yao_lines: list) -> dict:
    """找出最具影响力的单爻：优先取动爻，若无动爻则取世爻。"""
    moving = [y for y in yao_lines if y["is_moving"]]
    if moving:
        return moving[0]
    world = [y for y in yao_lines if y["is_world"]]
    if world:
        return world[0]
    return yao_lines[0] if yao_lines else {}


def _compute_quick_score(yao_lines: list, hints: list, day_branch: str) -> int:
    """简化的评分逻辑（0–100）。

    规则：
    - 基础分 65
    - 用神不空 +8
    - 用神非月破 +5
    - 有动爻且原神明动 +10
    - 忌神明动克用神 -12
    - 用神临日支 +7
    """
    score = 65

    relation, pos, branch = _identify_use_god(yao_lines, hints)
    if not relation:
        return score

    target = None
    for y in yao_lines:
        if y["six_relation"] == relation:
            target = y
            break
    if not target:
        return score

    # 旬空检查
    if not target.get("is_empty", False):
        score += 8

    # 原神（生用神之六亲 = 父母）暗中生
    # 忌神（克用神之六亲 = 官鬼/子孙等）明动克
    sheng_relation = None
    for r in ["父母", "兄弟", "子孙", "妻财", "官鬼"]:
        pass
    # 简化的生克：用神的五行 → 生我者（父母）为原神
    # 根据六亲反推：用神为妻财→原神为子孙；用神为官鬼→原神为妻财...
    yuan_map = {
        "妻财": "子孙",
        "官鬼": "妻财",
        "父母": "官鬼",
        "子孙": "兄弟",
        "兄弟": "父母",
    }
    ji_map = {
        "妻财": "兄弟",
        "官鬼": "子孙",
        "父母": "妻财",
        "子孙": "官鬼",
        "兄弟": "父母",
    }
    yuan_rel = yuan_map.get(relation, "")
    ji_rel = ji_map.get(relation, "")

    for y in yao_lines:
        if y["is_moving"]:
            if y["six_relation"] == yuan_rel:
                score += 10
            elif y["six_relation"] == ji_rel:
                score -= 12
            elif y["six_relation"] == relation:
                # 用神自身动：阴阳转变，力量增强
                score += 5

    # 日支临值
    if branch == day_branch:
        score += 7

    return max(30, min(95, score))


def _score_to_verdict(score: int) -> str:
    """分数转断语简词。"""
    if score >= 85:
        return "大吉"
    elif score >= 75:
        return "吉"
    elif score >= 65:
        return "中平"
    elif score >= 55:
        return "需审慎"
    elif score >= 45:
        return "艰难"
    else:
        return "不利"


def _verdict_to_action(verdict: str) -> str:
    """断语转建议行动项。"""
    actions = {
        "大吉": "顺势而为，果断行动，勿失良机",
        "吉": "稳步推进，保持当前方向",
        "中平": "量力而行，静观其变",
        "需审慎": "三思后行，避免冲动决策",
        "艰难": "守静为上，退一步海阔天空",
        "不利": "停止当前计划，重新审视局势",
    }
    return actions.get(verdict, "细察形势，因时而动")


def quick_reading(question: str, year: int, month: int, day: int, hour: int,
                  method: str = "coin") -> str:
    """直觉速读 — 200字以内的即时解读。

    流程：起卦 → 定用神 → 找关键动爻 → 单句断语。
    """
    # 1. 起卦
    if method == "time":
        yao_values = time_based_hexagram(year, month, day, hour)
        method_str = "时间起卦"
    elif method == "number":
        # 默认随机数字起卦
        import random
        random.seed()
        a, b, c = random.randint(1, 100), random.randint(1, 100), random.randint(1, 100)
        yao_values = number_based_hexagram(a, b, c)
        method_str = "数字起卦"
    else:
        yao_values = coin_toss()
        method_str = "铜钱摇卦"

    # 2. 建卦
    result = build_hexagram_result(
        yao_values, question, method_str, year, month, day, hour
    )
    oh = result["original_hexagram"]
    yao_lines = oh["yao_lines"]
    hints = result["analysis_hints"]["possible_use_gods"]
    day_branch = result["divination_time"]["day_stem_branch"]

    # 3. 用神 + 关键爻
    relation, pos, branch = _identify_use_god(yao_lines, hints)
    decisive = _find_decisive_yao(yao_lines)
    decisive_text = decisive.get("line_text", "")
    moving_count = sum(1 for y in yao_lines if y["is_moving"])

    # 4. 评分
    score = _compute_quick_score(yao_lines, hints, day_branch[1] if len(day_branch) > 1 else "")
    verdict = _score_to_verdict(score)
    action = _verdict_to_action(verdict)

    # 5. 单句原因
    hex_name = oh["name"]
    if decisive_text and decisive.get("is_moving"):
        one_line = f"第{decisive['position']}爻动「{decisive_text}」"
    elif moving_count == 0:
        one_line = f"{hex_name}静卦，以世爻断之"
    else:
        one_line = f"{hex_name}卦动爻 {moving_count} 个，{verdict}之象"

    return (
        f"【{question}】\n"
        f"{verdict}（{score}分）\n"
        f"{one_line}\n"
        f"建议：{action}"
    )


def single_yao_judgment(question: str, year: int, month: int, day: int, hour: int,
                        yao_values: list = None) -> str:
    """单爻断法 — 仅当只有一个动爻时生效。

    若无动爻或多动爻，回退到 :func:`quick_reading`。
    """
    # 起卦（若未提供爻值）
    if yao_values is None:
        yao_values = coin_toss()

    result = build_hexagram_result(
        yao_values, question, "单爻断法", year, month, day, hour
    )
    oh = result["original_hexagram"]
    hex_name = oh["name"]
    yao_lines = oh["yao_lines"]
    moving = [y for y in yao_lines if y["is_moving"]]

    if len(moving) != 1:
        # 回退到速读
        return quick_reading(question, year, month, day, hour)

    line = moving[0]
    line_text = line.get("line_text", "（爻辞缺失）")
    line_pos = line["position"]
    line_name = line.get("name", f"第{line_pos}爻")
    line_relation = line["six_relation"]
    line_branch = line["earthly_branch"]
    line_spirit = line["six_spirit"]

    # 位置解读
    pos_meanings = {
        1: "初爻动，事在萌发，吉凶初现端倪",
        2: "二爻动，得中道，多主和合顺利",
        3: "三爻动，事多凶悔，进退两难之际",
        4: "四爻动，近君位惧，宜慎言慎行",
        5: "五爻动，居尊决断，大事将定",
        6: "上爻动，事物至极，盛极则衰",
    }
    pos_meaning = pos_meanings.get(line_pos, "动爻所示，细察爻辞")

    # 现代白话
    modern_interp = (
        f"此第{line_pos}爻动，时当{'初起' if line_pos <= 2 else '转折' if line_pos <= 4 else '极变'}之时。"
        f"爻辞所言{line_text}，{pos_meaning}。"
    )

    return (
        f"【单爻断法 · {question}】\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"本卦：{hex_name}（{oh.get('judgment', '')}）\n"
        f"动爻：第{line_pos}爻（{line_name}）{line_relation}·{line_branch}\n"
        f"六神：{line_spirit}\n"
        f"\n"
        f"爻辞：「{line_text}」\n"
        f"\n"
        f"断曰：{pos_meaning}\n"
        f"\n"
        f"今译：{modern_interp}\n"
        f"\n"
        f"决：细玩爻辞之义，循之以行，得失自明。\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def _format_batch_text(batch_result: dict) -> str:
    """将批量演卦结果格式化为可读文本。"""
    lines = []
    W = 60
    lines.append("=" * W)
    lines.append("批量演卦对比报告".center(W))
    lines.append("=" * W)
    lines.append(f"　问　题：{batch_result.get('question', '?')}")
    lines.append(f"　总　数：{batch_result.get('n', 0)} 卦")
    lines.append("")

    dist = batch_result.get("verdict_distribution", {})
    lines.append("─" * W)
    lines.append("【吉凶分布】")
    lines.append(f"　吉：{dist.get('吉', 0)}　　"
                 f"凶：{dist.get('凶', 0)}　　"
                 f"平/混合：{dist.get('平/混合', 0)}")
    lines.append("")

    score = batch_result.get("score_statistics", {})
    lines.append("【评分统计】")
    lines.append(f"　均值：{score.get('mean', 0):.3f}　"
                 f"最低：{score.get('min', 0):.3f}　"
                 f"最高：{score.get('max', 0):.3f}　"
                 f"极差：{score.get('range', 0):.3f}")
    lines.append("")

    mch = batch_result.get("most_common_hexagram")
    lines.append("【卦体统计】")
    if mch:
        lines.append(f"　最常见卦：{mch.get('name', '?')}（{mch.get('count', 0)}次，"
                     f"{mch.get('percentage', 0):.1f}%）")
    lines.append(f"　卦体多样性：{batch_result.get('hexagram_diversity', 0)} 种不同卦"
                 f"（共 {batch_result.get('total_hexagrams', 64)} 卦）")
    lines.append(f"　多样性比：{batch_result.get('diversity_ratio', 0):.3f}")
    lines.append(f"　稳　定　性：{'稳定' if batch_result.get('is_stable') else '不稳定'}")

    stable = batch_result.get("stable_hexagrams", [])
    if stable:
        lines.append("　稳定卦象：")
        for sh in stable:
            lines.append(f"　　· {sh.get('name', '?')}（{sh.get('count', 0)}次）")

    # 频率表
    hf = batch_result.get("hexagram_frequency", [])
    if hf:
        lines.append("　频率表（前10）：")
        for h_name, h_count in hf[:10]:
            pct = h_count / batch_result.get("n", 1) * 100
            lines.append(f"　　· {h_name}：{h_count}次 ({pct:.1f}%)")
    lines.append("")

    summary = batch_result.get("summary", "")
    if summary:
        lines.append("─" * W)
        lines.append(f"　{summary}")
    lines.append("")
    lines.append("=" * W)
    return "\n".join(lines)


def _check_verify_mode(args):
    """执行反幻觉校验模式。"""
    # 读取引擎结果
    engine_result = None
    if args.engine_result:
        with open(args.engine_result, "r", encoding="utf-8") as f:
            engine_result = json.load(f)
    else:
        # 先用指定 mode 起一卦
        from datetime import datetime
        if args.datetime:
            dt = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M")
            year, month, day, hour = dt.year, dt.month, dt.day, dt.hour
        else:
            now = datetime.now()
            year, month, day, hour = now.year, now.month, now.day, now.hour

        if args.mode == "coin":
            yao_values = coin_toss()
            method = "铜钱摇卦"
        elif args.mode == "time":
            yao_values = time_based_hexagram(year, month, day, hour)
            method = "时间起卦"
        elif args.mode == "number" and args.numbers:
            nums = [int(x.strip()) for x in args.numbers.split(",")]
            yao_values = number_based_hexagram(nums[0], nums[1], nums[2])
            method = "数字起卦"
        elif args.mode == "manual" and args.yao:
            yao_values = [int(x.strip()) for x in args.yao.split(",")]
            method = "手动指定"
        else:
            yao_values = coin_toss()
            method = "铜钱摇卦(默认)"

        engine_result = build_hexagram_result(
            yao_values, args.question, method,
            year, month, day, hour
        )
        # 运行思维链
        try:
            from thinking_chain import run_thinking_chain
            chain_full = run_thinking_chain(engine_result)
            chain = chain_full.get("thinking_chain", chain_full)
            engine_result["thinking_chain"] = chain
        except ImportError:
            chain = None
            pass

    # 读取解读文本
    with open(args.verify, "r", encoding="utf-8") as f:
        interp_text = f.read()

    # 运行校验
    try:
        from hallucination_guard import verify_interpretation, generate_report
        checks = verify_interpretation(engine_result, interp_text)
        report = generate_report(checks)
    except ImportError:
        print("错误：hallucination_guard 模块未找到", file=sys.stderr)
        sys.exit(1)

    # 输出
    output_format = args.format if args.format is not None else args.output
    if output_format == "json":
        output = {
            "score": report.score,
            "risk_level": report.risk_level,
            "summary": report.summary,
            "checks": [
                {
                    "check_name": c.check_name,
                    "passed": c.passed,
                    "detail": c.detail,
                    "severity": c.severity,
                }
                for c in checks
            ],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("六爻反幻觉校验报告".center(60))
        print("=" * 60)
        print(f"通过率：{report.score * 100:.0f}% "
              f"({sum(1 for c in checks if c.passed)}/{len(checks)})")
        print(f"风险等级：{report.risk_level}")
        print(f"总结：{report.summary}")
        print("-" * 60)
        for c in checks:
            mark = "PASS" if c.passed else "FAIL"
            print(f"  [{mark}/{c.severity}] {c.check_name}: {c.detail}")
        print("=" * 60)


def main():
    _force_utf8_stdio()
    args = parse_arguments()

    if getattr(args, "version", False):
        import yishu_core
        print(f"易 · 六爻 v{yishu_core.__version__}")
        return

    # ── 模式1：批量演卦 (优先级最高，覆盖 --mode) ──
    if args.batch is not None and args.batch > 0:
        _check_batch_mode(args)
        return

    # ── 模式2：反幻觉校验 (独立模式) ──
    if args.verify is not None:
        _check_verify_mode(args)
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

        elif args.mode == "quick":
            # 直觉速读模式：极简输出，200字以内
            now = datetime.now()
            year = args.year if args.year is not None else now.year
            month = args.month if args.month is not None else now.month
            day = args.day if args.day is not None else now.day
            hour = args.hour if args.hour is not None else now.hour
            output = quick_reading(args.question, year, month, day, hour)
            print(output)
            return

        elif args.mode == "mei_hua":
            # 梅花易数互参模式：同时起六爻 + 梅花，交叉验证
            if not all([args.year, args.month, args.day, args.hour is not None]):
                print("错误：梅花易数互参模式需要 --year、--month、--day、--hour 参数",
                      file=sys.stderr)
                print("示例：--mode mei_hua --question \"测试\" --year 2024 --month 6 --day 15 --hour 10",
                      file=sys.stderr)
                sys.exit(1)
            cross_result = mei_hua_cross_reference(
                args.question, args.year, args.month, args.day, args.hour
            )
            # 输出结果
            output_format = args.format if args.format is not None else args.output
            if output_format == "json":
                print(json.dumps(cross_result, ensure_ascii=False, indent=2, default=str))
            else:
                print(_format_mei_hua_text(cross_result))
            return

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
            pass  # 若无 classical_analysis 模块，仅跳过增强
        
        # 五步思维链断卦分析（基于已输出的机械排盘数据推导结论）
        chain = None
        try:
            from thinking_chain import run_thinking_chain
            chain_full = run_thinking_chain(result)
            chain = chain_full.get("thinking_chain", chain_full)
        except ImportError:
            pass  # 若无 thinking_chain 模块，仅跳过思维链

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
            pass  # 若无 advice_framework 模块，不附加建议

        # 确定最终输出格式 (--format 优先于 --output)
        output_format = args.format if args.format is not None else args.output

        # 应用解读深度限制
        depth = getattr(args, "depth", "standard") or "standard"

        # 输出
        if output_format == "html":
            try:
                from visualization import build_html_report
                html_out = build_html_report(result)
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
                print("[WARN] visualization module not installed, fallback to JSON", file=sys.stderr)
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
