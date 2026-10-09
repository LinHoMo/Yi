# -*- coding: utf-8 -*-
"""古书源获取器：把公版古籍正文取回本地，**留下可复核的出处痕迹**。

    python tools/fetch_source.py --list                     # 看清单与本地缓存状态
    python tools/fetch_source.py --show liu-ren-da-quan     # 看某书解析出的子页
    python tools/fetch_source.py --fetch liu-ren-da-quan    # 抓取（含全部子页）
    python tools/fetch_source.py --fetch --all              # 抓清单里全部可用的书

为什么必须有这个工具（而不是各自写个小脚本）：
  1. **限流是要尊重的**。维基文库会对高频请求返回 HTTP 429。第一次探测候选门类时，
     我连打请求被限流，于是"取不到"与"没有这本书"在输出里长得一模一样——
     差点得出"《遁甲演义》不存在"的错误结论。本工具把限流**当成显式状态**重试，
     绝不把 429 静默降级成"缺失"。
  2. **出处要留痕**。每本书落盘时同时写 `*.provenance.json`：来源站点、页面标题、
     修订号、抓取时刻、sha256、字节数、子页清单。谁都可以据此复核"这段话真是书上的"。
     这与 `AGENTS.md` 铁律二（案例库隔离）配套：正文进 `data/sources/`，只做只读原料。
  3. **子页要能展开**。不少书在维基文库是"总页 + 卷次子页"（如《六壬大全》/1、/2…）。
     只抓总页会拿到空骨架——这是"书源看起来存在其实没内容"的常见坑。

设计纪律：
  * 只读公版古籍，不抓现代点校本、不抓带版权声明的站点；
  * 只做**字符级**保存，不做任何"模型转写"（转写会造出自洽性失败的假文本）；
  * 抓取与解析分离：`--fetch` 落原文，解析交给各门类自己的 parser；
  * 落盘位置默认 `data/sources/`；生成的 JSON 与 txt 是否入库由维护者按体量决定。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources"
CST = timezone(timedelta(hours=8))

API = "https://zh.wikisource.org/w/api.php"
USER_AGENT = "Yi-research/0.1 (classical text acquisition; https://github.com/)"

# 第二书源：殆知阁古代文献 v2.0（GitHub garychowcmu/daizhigev20）。
# 公版古籍的志愿转录数据集，易藏/术数/ 下 155 部术数古籍（2026-10-06 实测清点）。
# 质量口径：志愿录入/OCR 转写，**未经专业校勘**——凡维基文库有同书者必须先跑
# tools/crosscheck_source.py 对勘留痕再引用；单源书在 provenance 里如实标注"单源"。
# 抓取走 raw.githubusercontent.com 直链（git 协议被本机死代理挡，HTTP 直连正常）。
DZ_SITE = "github.com/garychowcmu/daizhigev20"
DZ_RAW = "https://raw.githubusercontent.com/garychowcmu/daizhigev20/master/"

# 请求节流：维基媒体对匿名高频请求会 429。默认每次请求之间歇 1.5 秒，
# 429 时按 5/15/30/60 秒退避重试，最多 4 次；绝不把限流当"缺失"。
SLEEP_BETWEEN = 1.5
BACKOFF = (5, 15, 30, 60)

# 候选门类 → 古书清单。`pages` 为空表示按总页自动展开子页。
# status 字段是**实测**结果，不是推测：
#   ok        = 已实测取到正文（记下字节数）
#   skeleton  = 实测只取到目录骨架（正文尚未数字化）
#   missing   = 实测 missingtitle
#   unverified= 未实测（多为触发限流后主动停手，需后续复核）
CATALOG = (
    # ── 大六壬（推荐第一科：判据树最清晰，书源已实测可用）──
    {"key": "liu-ren-da-quan", "kind": "大六壬", "title": "六壬大全",
     "pages": ["六壬大全/1", "六壬大全/2"],
     "status": "ok",
     "note": "已抓 129817 字节。卷一含《入手法》：十干寄宫诀 + 九宗门逐条判决"
             "（贼克/比用/涉害/遥克…），三传/四课/天将/月将/寄宫全部命中"},
    {"key": "liu-ren-da-quan-juan3", "kind": "大六壬", "title": "六壬大全/3",
     "pages": [], "status": "ok", "note": "已抓 72209 字节（344 行 / 干支对 62）"},
    {"key": "mei-hua-yi-shu", "kind": "梅花易数", "title": "梅花易數",
     "pages": [], "status": "ok",
     "note": "2026-09-30j 实测存在（繁体，正文 11201 字节）。三科外部独立集的书源前置："
             "抓取后从中提取卷二/卷三占验例建 external_cases（永不调参 split）"},
    {"key": "ling-qi-jing", "kind": "灵棋经", "title": "靈棋經",
     "pages": [], "status": "ok",
     "note": "2026-09-30l 实测存在（繁体，正文 36912 字节）。第二门类（备选一）书源："
             "查表即断（上中下三部掷数 → 课名/卦象/断语），core 零增补"},
    {"key": "liu-ren-zhi-nan", "kind": "大六壬", "title": "六壬指南",
     "pages": [], "status": "ok",
     "note": "2026-10-05 实测翻案：旧条目按「大六壬指南」探得 missingtitle 判不存在，"
             "系标题变体漏检——维基文库实际书名《六壬指南》（陈公献，清顺治刊，程起鸾序）。"
             "卷一（心印赋注）/卷二（指掌赋注）已数字化；卷三（占验指南）/卷四（神煞指南）"
             "实测 missingtitle（正文未数字化，占验例仍缺）。"},
    {"key": "liu-ren-bi-fa-fu", "kind": "大六壬", "title": "六壬毕法赋",
     "pages": [], "status": "missing", "note": "实测 missingtitle"},
    # ── 奇门遁甲（**降级**：主源不存在，"古书自带算例"无法兑现）──
    {"key": "dun-jia-yan-yi", "kind": "奇门遁甲", "title": "遁甲演义",
     "pages": ["遁甲演义/1"], "status": "missing",
     "note": "**实测 missingtitle**（两次复核）。此前立项文档据「检索旁证」称其"
             "「已联网核实、自带五组带日期算例」，该说法不成立——奇门的推荐理由随之降级"},
    {"key": "yan-bo-diao-sou-ge", "kind": "奇门遁甲", "title": "煙波釣叟歌",
     "pages": [], "status": "ok", "note": "已抓 5970 字节（第三轮重试成功）。实测复核：有机制纲诀"
             "（阴阳遁分界/三元五日/阳遁顺仪奇逆布/值符值使），**无 24 节气×三元定局表与算例**"},
    {"key": "yu-ding-qi-men-bao-jian", "kind": "奇门遁甲", "title": "御定奇门宝鉴",
     "pages": [], "status": "missing",
     "note": "2026-10-05 实测 missingtitle（此前 unverified 未实测）——N2 奇门定局起例"
             "书源维持未落实，骨架不启动"},
    # ── 八字（调候 / 格局；命科深度改造的判据与命例来源）──
    {"key": "qiong-tong-bao-jian", "kind": "八字·调候", "title": "穷通宝鉴",
     "pages": [], "status": "ok",
     "note": "已抓 100030 字节：56 个标题（论X木/三春甲木…=调候判据正文）"
             "+ 70 个表格（四柱命例 + 断语如「状元」「词林」）=可建案例集"},
    {"key": "lan-jiang-wang", "kind": "八字·调候", "title": "欄江網",
     "pages": [], "status": "missing",
     "note": "实测 missingtitle；《穷通宝鉴》异名在维基文库无独立页"},
    {"key": "zi-ping-zhen-quan", "kind": "八字·格局", "title": "子平真诠",
     "pages": [], "status": "missing",
     "note": "实测 missingtitle（简繁两式均无）。格局成败救应的判据来源需另找"},
    {"key": "di-tian-sui", "kind": "八字·用神", "title": "滴天髓",
     "pages": [], "status": "ok",
     "note": "2026-10-01 重抓实测 60578 字节（含任注從化論：『從得真者只論從』逐字在库），此前 skeleton 判定过期"},
    {"key": "di-tian-sui-chan-wei", "kind": "八字·用神", "title": "滴天髓闡微",
     "pages": [], "status": "ok",
     "note": "2026-10-04 实测存在：正文 401801 字节 / 干支对 6306，通神论34章+六亲论29章，"
             "任注命例嵌于各章正文。命科 external holdout（TECH-DEBT §2.3 / HANDOFF §四.D）"
             "与病药跨书源补证（TECH-DEBT §2.7/2.8 解除路径）的书源前置"},
    {"key": "yuan-hai-zi-ping", "kind": "八字·总纲", "title": "淵海子平",
     "pages": [], "status": "ok",
     "note": "2026-10-07 翻案：简体题名实测 missingtitle，繁體页《淵海子平》在库"
             "（author=楊淙/明，{{No source}} 志愿转录）；正文 178KB 已在库，"
             "本轮 --force 重抓补写 provenance。"},
    {"key": "shen-feng-tong-kao", "kind": "八字·病药", "title": "神峰通考",
     "pages": [], "status": "ok",
     "note": "2026-10-02 实测有正文：病药说类/雕枯旺弱四病说类/损益生长四药说类"
             "=病药用神判据正文章节在库（命科病药判据的语料阻塞解除）"},
    # ── 备选与旁证 ──
    # （曾有一条重复的 ling-qi-jing「四库全书本」条目：同 key 被 by_key 首匹配遮蔽、
    #   不可达，2026-10-05 删除）
    {"key": "tai-yi-jin-jing", "kind": "太乙", "title": "太乙金镜式经",
     "pages": [], "status": "missing",
     "note": "2026-10-05 实测 missingtitle（此前 unverified 未实测）"},
    {"key": "xie-ji-bian-fang", "kind": "择吉", "title": "协纪辨方书",
     "pages": [], "status": "missing",
     "note": "2026-10-05 实测 missingtitle（此前 unverified 未实测）——择吉科外部"
             "书源旁证通道关闭，维持 §2.1 阻塞登记"},
    {"key": "zi-wei-dou-shu-quan-shu", "kind": "紫微斗数", "title": "紫微斗數全書",
     "pages": [], "status": "ok",
     "note": "已抓 214512 字节（卷一/二/三，93 标题）：卷一诸星问答论十四主星性情段 + "
             "太微赋/形性赋，可校 verdicts 主星格释义"},
    {"key": "zeng-shan-bu-yi", "kind": "六爻", "title": "增刪卜易",
     "pages": [], "status": "ok",
     "note": "已有专用 parser：disciplines/liuyao/dev_tools/fetch_wikisource_cases.py"})


# ── 殆知阁异源批（2026-10-06，site=daizhige；key 一律 _dz 后缀＝殆知阁转录本）──
# 定位：① 补维基文库缺失的热门古籍；② 对在库维基文库书提供**异源对勘本**。
# 转录质量未定，引用前必跑 crosscheck（对勘）或在 provenance 登记"单源未对勘"。
DZ_CATALOG = (
    # 六爻/卜筮（补齐维基文库缺口：卜筮正宗三次复核均 missingtitle，此处全本在）
    {"key": "bushi_zhengzong_dz", "kind": "六爻", "title": "卜筮正宗",
     "dz_path": "易藏/术数/卜筮正宗.txt", "status": "ok",
     "note": "2026-10-06 实测 259KB 全本（带句读）。TECH-DEBT §2.1「维基文库仅 912B 骨架」"
             "的解除路径——liupo 等待该底本的规则可重启取证；转录质量待与黄金策/增删卜易交叉验证"},
    {"key": "bushi_quanshu_dz", "kind": "六爻", "title": "卜筮全书",
     "dz_path": "易藏/术数/卜筮全书.txt", "status": "ok"},
    {"key": "yimao_dz", "kind": "六爻", "title": "易冒",
     "dz_path": "易藏/术数/易冒.txt", "status": "ok"},
    {"key": "yiin_dz", "kind": "六爻", "title": "易隐",
     "dz_path": "易藏/术数/易隐.txt", "status": "ok"},
    {"key": "duanyi_tianji_dz", "kind": "六爻", "title": "断易天机",
     "dz_path": "易藏/术数/断易天机.txt", "status": "ok"},
    {"key": "yilin_buyi_dz", "kind": "六爻", "title": "易林补遗",
     "dz_path": "易藏/术数/易林补遗.txt", "status": "ok"},
    # 八字（子平真诠评注＝ZP 批 36 条引文的所本书源；渊海子平/三命通会=格局判据大库）
    {"key": "yuanhai_ziping_dz", "kind": "八字", "title": "渊海子平",
     "dz_path": "易藏/术数/渊海子平.txt", "status": "ok",
     "note": "维基文库实测 missingtitle 的头号命理总集，殆知阁全本在"},
    {"key": "ziping_zhenquan_pingzhu_dz", "kind": "八字", "title": "子平真诠评注",
     "dz_path": "易藏/术数/子平真诠评注.txt", "status": "ok",
     "note": "ZP 批 36 条引文的所本（徐乐吾评注，1936；作者 1948 卒，公版）；"
             "若引文逐字命中可解除 [1k] 的 36 条「书源不在库」披露"},
    {"key": "sanming_tonghui_dz", "kind": "八字", "title": "三命通会",
     "dz_path": "易藏/术数/三命通会.txt", "status": "ok"},
    {"key": "lixuzhong_mingshu_dz", "kind": "八字", "title": "李虚中命书",
     "dz_path": "易藏/术数/李虚中命书.txt", "status": "ok"},
    {"key": "wuxing_jingji_dz", "kind": "八字", "title": "五行精纪",
     "dz_path": "易藏/术数/五行精纪.txt", "status": "ok"},
    # 大六壬（六壬心镜/六壬断案=邵彦和占验案例集/壬归/御定直指/神定经/粹言；指南=对勘本）
    {"key": "liuren_xinjing_dz", "kind": "大六壬", "title": "六壬心镜",
     "dz_path": "易藏/术数/六壬心镜.txt", "status": "ok"},
    {"key": "liuren_duanan_dz", "kind": "大六壬", "title": "六壬断案",
     "dz_path": "易藏/术数/六壬断案.txt", "status": "ok",
     "note": "邵彦和断验案例集——大六壬课例评测扩样的首选书源"},
    {"key": "liuren_cuiyan_dz", "kind": "大六壬", "title": "六壬粹言",
     "dz_path": "易藏/术数/六壬粹言.txt", "status": "ok"},
    {"key": "rengui_dz", "kind": "大六壬", "title": "壬归",
     "dz_path": "易藏/术数/壬归.txt", "status": "ok"},
    {"key": "liuren_zhizhi_yuding_dz", "kind": "大六壬", "title": "六壬直指御定",
     "dz_path": "易藏/术数/六壬直指御定.txt", "status": "ok"},
    {"key": "liuren_shending_dz", "kind": "大六壬", "title": "六壬神定经",
     "dz_path": "易藏/术数/六壬神定经.txt", "status": "ok"},
    {"key": "liuren_zhinan_dz", "kind": "大六壬", "title": "六壬指南",
     "dz_path": "易藏/术数/六壬指南.txt", "status": "ok",
     "note": "在库 liu-ren-zhi-nan（维基文库卷一/二）的异源对勘本"},
    # 择吉（协纪辨方书＝择吉科最高权威 canon，维基文库实测 missingtitle）
    {"key": "xieji_bianfang_dz", "kind": "择吉", "title": "钦定协纪辨方书",
     "dz_path": "易藏/术数/钦定协纪辨方书.txt", "status": "ok",
     "note": "择吉科判据与外部集的书源前置；部头大，抓后须核完整性"},
    {"key": "xingli_kaoyuan_dz", "kind": "择吉", "title": "御定星历考原",
     "dz_path": "易藏/术数/御定星历考原.txt", "status": "ok"},
    # 奇门（TECH-DEBT §2.3「定局起例表书源未落实」的解除候选）
    {"key": "dunjia_yanyi_dz", "kind": "奇门遁甲", "title": "遁甲演义",
     "dz_path": "易藏/术数/遁甲演义.txt", "status": "ok",
     "note": "维基文库两次复核 missingtitle；N2 奇门定局表的书源解除候选"},
    {"key": "qimen_baojian_dz", "kind": "奇门遁甲", "title": "御定奇门宝鉴",
     "dz_path": "易藏/术数/奇门宝鉴御定.txt", "status": "ok"},
    {"key": "qimen_tongzong_dz", "kind": "奇门遁甲", "title": "奇门遁甲统宗",
     "dz_path": "易藏/术数/奇门遁甲统宗.txt", "status": "ok"},
    # 太乙
    {"key": "taiyi_jinjing_dz", "kind": "太乙", "title": "太乙金镜式经",
     "dz_path": "易藏/术数/太乙金镜式经.txt", "status": "ok"},
    # 术数通纲 / 易占
    {"key": "wuxing_dayi_dz", "kind": "术数通纲", "title": "五行大义",
     "dz_path": "易藏/术数/五行大义.txt", "status": "ok"},
    {"key": "jiaoshi_yilin_dz", "kind": "易占", "title": "焦氏易林",
     "dz_path": "易藏/术数/焦氏易林.txt", "status": "ok"},
    # 2026-10-07 第二批补漏（对照易藏/术数 155 部线上实测清单逐名核对）：
    # 八字：民国三大热门入门/歌诀；六爻：纳甲祖源与金钱课；其余见 kind。
    # 相书（人伦大统赋/太清神鉴/柳庄相法/冰鉴等）与堪舆书（葬书/撼龙经/青囊等）
    # 一律不收——AGENTS.md「相科（面相、手相、堪舆）明确不做」。
    {"key": "qianli_minggao_dz", "kind": "八字", "title": "千里命稿",
     "dz_path": "易藏/术数/千里命稿.txt", "status": "ok",
     "note": "韦千里（1934），民国命理入门第一热门；作者 1988 卒，公版"},
    {"key": "mingli_tanyuan_dz", "kind": "八字", "title": "命理探源",
     "dz_path": "易藏/术数/命理探源.txt", "status": "ok",
     "note": "袁树珊（1916），民国命理汇纂热门"},
    {"key": "lantai_miaoxuan_dz", "kind": "八字", "title": "兰台妙选",
     "dz_path": "易藏/术数/兰台妙选.txt", "status": "ok",
     "note": "万民英辑，纳音取象格局派代表"},
    {"key": "yuzhao_dingzhen_dz", "kind": "八字", "title": "玉照定真经",
     "dz_path": "易藏/术数/玉照定真经.txt", "status": "ok",
     "note": "题郭璞，命理歌诀派早期经典"},
    {"key": "sanming_zhimi_fu_dz", "kind": "八字", "title": "三命指迷赋",
     "dz_path": "易藏/术数/三命指迷赋.txt", "status": "ok"},
    {"key": "jingshi_yizhuan_dz", "kind": "六爻·祖源", "title": "京氏易传",
     "dz_path": "易藏/术数/京氏易传.txt", "status": "ok",
     "note": "京房纳甲筮法祖源，六爻装卦规则的源头文献"},
    {"key": "zhouyi_shangzhan_dz", "kind": "六爻", "title": "周易尚占",
     "dz_path": "易藏/术数/周易尚占.txt", "status": "ok"},
    {"key": "wenwang_jinqianke_dz", "kind": "六爻", "title": "文王金钱课",
     "dz_path": "易藏/术数/文王金钱课.txt", "status": "ok",
     "note": "民间金钱卜卦热门文本"},
    {"key": "taiyi_mishu_dz", "kind": "太乙", "title": "太乙秘书",
     "dz_path": "易藏/术数/太乙秘书.txt", "status": "ok"},
    {"key": "huangji_jingshi_shu_dz", "kind": "术数通纲", "title": "皇极经世书",
     "dz_path": "易藏/术数/皇极经世书.txt", "status": "ok",
     "note": "邵雍元会运世体系，术数宇宙论通纲"},
    {"key": "qimen_faqiao_dz", "kind": "奇门遁甲", "title": "奇门法窍",
     "dz_path": "易藏/术数/奇门法窍.txt", "status": "ok"},
    {"key": "tuibeitu_dz", "kind": "预言", "title": "推背图",
     "dz_path": "易藏/术数/推背图.txt", "status": "ok"},
    {"key": "zhougong_jiemeng_dz", "kind": "民俗占", "title": "周公解梦",
     "dz_path": "易藏/术数/周公解梦.txt", "status": "ok"},
    {"key": "cezi_midie_dz", "kind": "测字", "title": "测字秘牒",
     "dz_path": "易藏/术数/测字秘牒.txt", "status": "ok",
     "note": "程省（清），测字术代表典籍"},
    {"key": "zhuge_shenshu_dz", "kind": "签占", "title": "秘本诸葛神数",
     "dz_path": "易藏/术数/秘本诸葛神数.txt", "status": "ok"},
    {"key": "yizhangjing_dz", "kind": "掌诀", "title": "神机妙算一掌经",
     "dz_path": "易藏/术数/神机妙算一掌经.txt", "status": "ok",
     "note": "佛门一掌经，掌诀推命；与小六壬同属掌诀推演谱系"},
    # 在库维基文库书的异源对勘本（crosscheck 用，不单独建案例）
    {"key": "zengshan_buyi_dz", "kind": "六爻·对勘", "title": "增刪卜易",
     "dz_path": "易藏/术数/增删卜易.txt", "status": "ok"},
    {"key": "huangjince_dz", "kind": "六爻·对勘", "title": "黃金策",
     "dz_path": "易藏/术数/黄金策.txt", "status": "ok"},
    {"key": "qiong_tong_bao_jian_dz", "kind": "八字·对勘", "title": "穷通宝鉴",
     "dz_path": "易藏/术数/穷通宝鉴.txt", "status": "ok"},
    {"key": "shenfeng_tongkao_dz", "kind": "八字·对勘", "title": "神峰通考",
     "dz_path": "易藏/术数/神峰通考.txt", "status": "ok"},
    {"key": "ditian_sui_chanwei_dz", "kind": "八字·对勘", "title": "滴天髓闡微",
     "dz_path": "易藏/术数/滴天髓阐微.txt", "status": "ok"},
    {"key": "meihua_yishu_dz", "kind": "梅花·对勘", "title": "梅花易數",
     "dz_path": "易藏/术数/梅花易数.txt", "status": "ok"},
    {"key": "huozhulin_dz", "kind": "六爻·对勘", "title": "火珠林",
     "dz_path": "易藏/术数/火珠林.txt", "status": "ok"},
    {"key": "lingqijing_dz", "kind": "灵棋·对勘", "title": "靈棋經",
     "dz_path": "易藏/术数/灵棋经.txt", "status": "ok"},
)


# ── HTTP ────────────────────────────────────────────────────────────────────

class RateLimited(RuntimeError):
    """明确的限流状态。绝不与「页面不存在」混为一谈。"""


def _get(params: dict, *, retries: int = 4) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            time.sleep(SLEEP_BETWEEN)
            return data
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code == 429:
                wait = BACKOFF[min(attempt, len(BACKOFF) - 1)]
                print(f"    · 限流 429，等待 {wait}s 后重试（第 {attempt + 1} 次）")
                time.sleep(wait)
                continue
            if exc.code == 404:
                return {"error": {"code": "missingtitle"}}
            raise
        except Exception as exc:  # 网络抖动
            last = exc
            time.sleep(BACKOFF[min(attempt, len(BACKOFF) - 1)])
    raise RateLimited(f"重试 {retries} 次仍失败：{last!r}")


def page_wikitext(title: str) -> tuple[str, dict]:
    """取单页 wikitext。返回 (正文, 元信息)；页面不存在返回 ("", {...})。"""
    data = _get({"action": "parse", "format": "json", "formatversion": "2",
                 "prop": "wikitext|revid", "page": title, "redirects": "1"})
    if "error" in data:
        return "", {"title": title, "error": data["error"].get("code", "error")}
    parse = data.get("parse") or {}
    text = ((parse.get("wikitext")) or "")
    if isinstance(text, dict):  # 老式 formatversion=1 结构
        text = text.get("*", "")
    return text, {"title": parse.get("title") or title,
                  "revid": parse.get("revid"),
                  "pageid": parse.get("pageid")}


def subpages(title: str) -> list[str]:
    """列出某页的全部子页（如《六壬大全》的卷次页）。"""
    data = _get({"action": "query", "format": "json", "formatversion": "2",
                 "list": "allpages", "apprefix": title + "/", "aplimit": "200"})
    if "error" in data:
        return []
    pages = ((data.get("query") or {}).get("allpages")) or []
    return [p.get("title", "") for p in pages if p.get("title")]


def page_exists(title: str) -> bool:
    data = _get({"action": "query", "format": "json", "formatversion": "2",
                 "titles": title, "redirects": "1"})
    if "error" in data:
        return False
    pages = ((data.get("query") or {}).get("pages")) or []
    return bool(pages) and not pages[0].get("missing")


# ── 落盘与留痕 ──────────────────────────────────────────────────────────────

def _slug(entry: dict) -> str:
    return entry["key"]


def _is_dz(entry: dict) -> bool:
    return bool(entry.get("dz_path"))


def raw_path(entry: dict) -> Path:
    suffix = "dz.txt" if _is_dz(entry) else "wikitext.txt"
    return SOURCES / f"{_slug(entry)}.{suffix}"


def prov_path(entry: dict) -> Path:
    return SOURCES / f"{_slug(entry)}.provenance.json"


def load_prov(entry: dict) -> dict | None:
    p = prov_path(entry)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def stat_text(text: str) -> dict:
    """正文字面统计：给"这本书里到底有没有可编程结构"一个客观读数。"""
    ganzhi = re.findall(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]", text)
    tables = len(re.findall(r"\{\|", text))
    headings = len(re.findall(r"^=+[^=\n]+=+", text, re.M))
    lines = [l for l in text.splitlines() if l.strip()]
    return {"bytes": len(text.encode("utf-8")), "chars": len(text),
            "lines": len(lines), "ganzhi_pairs": len(ganzhi),
            "tables": tables, "headings": headings}


def fetch(entry: dict, *, force: bool = False) -> dict:
    """抓取一本书（含子页），落原文 + 出处。返回出处 dict。"""
    key = entry["key"]
    if raw_path(entry).is_file() and not force:
        prov = load_prov(entry) or {}
        print(f"  = {key}：已有缓存（{prov.get('stats', {}).get('bytes', '?')} 字节），"
              f"加 --force 可重抓")
        return prov

    print(f"  → {key}（{entry['title']}）")
    titles = list(entry.get("pages") or [])
    if not titles:
        # 总页 + 自动展开的子页
        main_text, meta = page_wikitext(entry["title"])
        if meta.get("error"):
            print(f"    × 总页不可用：{meta['error']}")
            return {"key": key, "status": meta["error"], "pages": []}
        print(f"    · 总页 {meta['title']} 取到 {len(main_text)} 字符，展开子页…")
        subs = subpages(meta.get("title") or entry["title"])
        titles = [meta.get("title") or entry["title"]] + subs
        print(f"    · 子页 {len(subs)} 个")
        texts = {meta.get("title") or entry["title"]: main_text}
    else:
        texts = {}

    order: list[str] = []
    for t in titles:
        if t in texts:
            order.append(t)
            continue
        text, meta = page_wikitext(t)
        if meta.get("error"):
            print(f"    · 跳过 {t}（{meta['error']}）")
            continue
        texts[t] = text
        order.append(t)

    if not order:
        return {"key": key, "status": "empty", "pages": []}

    body = "\n\n".join(
        f"<!-- ==== {t} ==== -->\n{texts[t]}" for t in order if texts.get(t))
    st = stat_text(body)
    SOURCES.mkdir(parents=True, exist_ok=True)
    raw_path(entry).write_text(body, encoding="utf-8")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    prov = {
        "key": key, "kind": entry["kind"], "title": entry["title"],
        "site": "zh.wikisource.org", "api": API,
        "pages": order, "page_count": len(order),
        "fetched": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S%z"),
        "sha256": digest, "stats": st,
        "source_file": raw_path(entry).relative_to(ROOT).as_posix(),
        "note": ("公版古籍原文的字符级转存，未做任何改写或模型转写；"
                 "子页以 <!-- ==== 标题 ==== --> 分隔。"),
    }
    prov_path(entry).write_text(json.dumps(prov, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    print(f"    √ 落盘 {st['bytes']} 字节 / {st['lines']} 行 / "
          f"干支对 {st['ganzhi_pairs']} / 表格 {st['tables']} / 标题 {st['headings']}")
    print(f"      出处 → {prov_path(entry).relative_to(ROOT).as_posix()}")
    return prov


def fetch_dz(entry: dict, *, force: bool = False) -> dict:
    """抓取殆知阁转录本（raw.githubusercontent.com 直链），落原文 + 出处。

    与 fetch() 同一套留痕纪律：sha256、字节数、抓取时刻、来源路径全部落
    provenance；HTTP 404 如实记 missing，绝不与限流混淆。
    """
    key = entry["key"]
    if raw_path(entry).is_file() and not force:
        prov = load_prov(entry) or {}
        print(f"  = {key}：已有缓存（{prov.get('stats', {}).get('bytes', '?')} 字节），"
              f"加 --force 可重抓")
        return prov

    url = DZ_RAW + urllib.parse.quote(entry["dz_path"])
    print(f"  → {key}（{entry['title']}）← 殆知阁 {entry['dz_path']}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = resp.read().decode("utf-8", errors="strict")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print("    × 404：该路径在 daizhigev20 实测不存在")
            return {"key": key, "status": "notfound", "pages": []}
        raise
    except Exception as exc:
        raise RateLimited(f"网络失败（不是『书不存在』）：{exc!r}")

    st = stat_text(body)
    if st["bytes"] < 500:
        print(f"    ! 仅 {st['bytes']} 字节，疑似骨架/空文件，仍照实落盘")
    SOURCES.mkdir(parents=True, exist_ok=True)
    raw_path(entry).write_text(body, encoding="utf-8")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    prov = {
        "key": key, "kind": entry["kind"], "title": entry["title"],
        "site": DZ_SITE, "path": entry["dz_path"], "url": url,
        "pages": [entry["dz_path"]], "page_count": 1,
        "fetched": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S%z"),
        "sha256": digest, "stats": st,
        "source_file": raw_path(entry).relative_to(ROOT).as_posix(),
        "note": ("殆知阁古代文献 v2.0 志愿转录本（简体、带句读），未经专业校勘；"
                 "与维基文库同书者引用前须跑 tools/crosscheck_source.py 对勘留痕。"),
    }
    prov_path(entry).write_text(json.dumps(prov, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    print(f"    √ 落盘 {st['bytes']} 字节 / {st['lines']} 行 / "
          f"干支对 {st['ganzhi_pairs']} / 标题 {st['headings']}")
    print(f"      出处 → {prov_path(entry).relative_to(ROOT).as_posix()}")
    return prov


def by_key(key: str) -> dict | None:
    for e in CATALOG + DZ_CATALOG:
        if e["key"] == key:
            return e
    return None


def cmd_list() -> int:
    print("%-24s %-10s %-22s %-10s %s" % ("key", "门类", "书名", "状态", "本地缓存"))
    print("-" * 92)
    for e in CATALOG:
        prov = load_prov(e)
        cached = (f"{prov['stats']['bytes']}B/{prov['page_count']}页"
                  if prov else "—")
        print("%-24s %-10s %-22s %-10s %s" % (
            e["key"], e["kind"], e["title"], e["status"], cached))
        if e.get("note"):
            print("%-24s %s" % ("", "└ " + e["note"]))
    print("\n── 殆知阁异源批（site=github.com/garychowcmu/daizhigev20，简体转录）──")
    for e in DZ_CATALOG:
        prov = load_prov(e)
        cached = (f"{prov['stats']['bytes']}B" if prov else "—")
        print("%-24s %-10s %-22s %-10s %s" % (
            e["key"], e["kind"], e["title"], e["status"], cached))
    print("\n状态口径：ok=实测取到正文；skeleton=只有目录骨架；missing/notfound=实测不存在；"
          "unverified=未实测（多为限流后主动停手，需复核）。"
          "殆知阁批 status 以 provenance 实测为准，未经实测一律 unverified。")
    return 0


def cmd_show(key: str) -> int:
    e = by_key(key)
    if not e:
        print(f"× 清单里没有 {key}（用 --list 查看）")
        return 2
    print(f"《{e['title']}》（{e['kind']}）status={e['status']}")
    if e.get("note"):
        print("  实测备注：" + e["note"])
    if e.get("pages"):
        print("  清单内写定的子页：")
        for p in e["pages"]:
            print("    · " + p)
    print("  探测子页（可能触发限流，会明确重试）…")
    subs = subpages(e["title"])
    if not subs:
        print("    （无子页，或该总页不存在）")
    for p in subs:
        print("    · " + p)
    prov = load_prov(e)
    if prov:
        print("  本地缓存：" + json.dumps(prov.get("stats"), ensure_ascii=False))
    return 0


def cmd_check(titles: list[str]) -> int:
    """逐标题实测存在性并报正文字节数。

    用途：**解决"这本书到底有没有"的争执**。同一个书名，有人凭检索结果说"有"，
    有人抓取失败说"无"——两种说法都不算数，只有 `action=query` 的 missing 字段算数。
    本命令对每个标题分别报：存在 / 不存在 / 被限流（**不等于不存在**）。
    """
    rc = 0
    for title in titles:
        try:
            data = _get({"action": "query", "format": "json", "formatversion": "2",
                         "titles": title, "redirects": "1",
                         "prop": "info"})
        except RateLimited as exc:
            print("  ? %-30s 被限流，无法判定（**不是**不存在）：%s" % (title, exc))
            rc = 1
            continue
        if "error" in data:
            print("  ? %-30s 查询出错：%s" % (title, data["error"].get("code")))
            rc = 1
            continue
        pages = ((data.get("query") or {}).get("pages")) or []
        if not pages:
            print("  ? %-30s 无返回" % title)
            rc = 1
            continue
        page = pages[0]
        if page.get("missing"):
            print("  × %-30s 不存在（missingtitle）" % title)
            rc = 1
            continue
        real = page.get("title") or title
        text, meta = page_wikitext(real)
        st = stat_text(text)
        if st["bytes"] < 500:
            verdict = "存在但正文过短（可能是总页/骨架）"
        else:
            verdict = f"存在，正文 {st['bytes']} 字节 / 干支对 {st['ganzhi_pairs']}"
        print("  √ %-30s %s%s" % (title, verdict,
                                  f"（重定向→{real}）" if real != title else ""))
    return rc


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(
        description="古书源获取器（维基文库；限流显式重试、出处留痕、子页展开）")
    ap.add_argument("--list", action="store_true", help="列出清单与缓存状态")
    ap.add_argument("--show", metavar="KEY", help="看某书的子页与缓存")
    ap.add_argument("--check", nargs="*", metavar="TITLE",
                    help="直接核查书名/页面标题是否存在（判定『有没有这本书』的唯一依据）")
    ap.add_argument("--fetch", nargs="*", metavar="KEY", help="抓取指定书（可多个）")
    ap.add_argument("--all", action="store_true", help="配合 --fetch：抓清单里 status=ok 的全部")
    ap.add_argument("--force", action="store_true", help="已有缓存也重抓")
    args = ap.parse_args()

    if args.check:
        print("逐标题实测（结论只认 API 的 missing 字段；限流≠不存在）：")
        return cmd_check(args.check)
    if args.list or not (args.fetch or args.show):
        return cmd_list()
    if args.show:
        return cmd_show(args.show)
    keys = list(args.fetch or [])
    if args.all:
        keys += [e["key"] for e in CATALOG if e["status"] == "ok"]
    if not keys:
        print("× 没给要抓的书（--fetch KEY...，或 --all 抓 status=ok 的全部）")
        return 2

    ok = 0
    for key in dict.fromkeys(keys):
        e = by_key(key)
        if not e:
            print(f"  × 清单里没有 {key}")
            continue
        try:
            prov = fetch_dz(e, force=args.force) if _is_dz(e) else fetch(e, force=args.force)
        except RateLimited as exc:
            print(f"  × {key}：被限流且重试未过 —— {exc}")
            print("     这是「取不到」，**不是**「这本书不存在」；稍后重试。")
            continue
        if prov.get("sha256"):
            ok += 1
        elif prov.get("status"):
            # 如实区分三类结果，绝不把"取不到"说成"不存在"
            kind = {"missingtitle": "维基文库上没有这个页面",
                    "empty": "页面存在但没有正文",
                    "skeleton": "只有目录骨架"}.get(prov["status"], prov["status"])
            print(f"  ! {key}：{kind}")
    print(f"\n完成 {ok}/{len(set(keys))} 本。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
