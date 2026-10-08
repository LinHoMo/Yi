# 优化项裁定台账（2026-10-07 全 304 条实测）

本台账是319 条 OPT 的**实测裁定结果**。每条均经子代理核验 + 主代理复核（行号以 cat -n 口径Read 核准）。

## 一、已落实（22 条）

见下方明细；每条单独跑 `tools/eval.py` + `check_source_readings.py`，全库读数持续零回归。

| OPT ID | 落实内容 |
|---|---|
| OPT-huangji_jingshi_shu_dz-01 | 推翻"全文重影"+provenance双口径 |
| OPT-huangji_jingshi_shu_dz-02 | 护栏已存在且更严 |
| OPT-huangjince_dz-01 | 伏神引文两处差异三源并记 |
| OPT-huangjince_dz-02 | 游魂归魂跨书误挂3处改真实原文 |
| OPT-liuren_shending_dz-01 | 昼夜贵人壬癸昼巳夜卯（三源互证） |
| OPT-liuren_shending_dz-03 | 新增十二将家支表TWELVE_JIANG_HOME |
| OPT-liuren_shending_dz-04 | 新增日德神定经双表（不覆盖现值） |
| OPT-liuren_cuiyan_dz-03 | 天将位次补《六壬粹言》L98-108对源（复核确认零偏离） |
| OPT-xingli_kaoyuan_dz-01 | basis错指订正+天德月德书源行号补齐 |
| OPT-qimen_faqiao_dz-01 | 文档已落盘，现状过期 |
| OPT-qimen_tongzong_dz-01 | 文档已落盘，现状过期 |
| OPT-zengshan_buyi_dz-01 | 缺陷早已登记（§四L246+§五第1/2/3/7条） |
| OPT-bushi_zhengzong_dz-01 | 六破 verified→true + 补书源L119-125（破对六对全等） |
| OPT-bushi_zhengzong_dz-02 | 伏吟locator补行号+provenance登记缺段 |
| OPT-bushi_zhengzong_dz-03 | 重复块登记（推翻"逐字全同"，定位圆神/圆通神讹字并存） |
| OPT-bushi_quanshu_dz-01 | 暗动双源并注（填补registry"暗动定义正文缺书源"缺口） |
| OPT-bushi_quanshu_dz-02 | 神煞使用审计（final_score 12项无神煞） |
| OPT-ditian_sui_chanwei_dz-01 | 新增滴天髓任注本分支7条判据+撤销"原书未入库"失效前提 |
| OPT-yilin_buyi_dz-01 | 坟墓族新增已葬/安葬/下葬/伏尸→官鬼 |
| OPT-yiin_dz-02 | 伏飞四态补《易隐》原词与出处 |
| OPT-mingli_tanyuan_dz-01 | 三合/六冲/六害/三刑补对源；六合订正不挂L184 |
| OPT-shenfeng_tongkao_dz-01 | 病药总纲挂源L40+订正位置误记 |
| OPT-ziping_zhenquan_pingzhu_dz-02 | 行运成格变格覆盖度审计+evaluate.py缺口注释（不动判据） |
| OPT-bushi_quanshu_dz-04 | 助鬼伤身评估报告（暂不新增，跨-爻链路缺失+书源注家分歧） |
| OPT-lingqijing_dz-02 | 阴阳㝃组附录独立key核查登记（124课+appendix分离确认） |
| OPT-liuren_duanan_dz-02 | 日为人/辰为宅/合支空亡/墓+迟滞神结构评估（纯结构，不动判据） |
| OPT-qimen_faqiao_dz-05 | 奇门法窍六十时格局格名词表抽取（63格名14类，法窍L3281-5848） |
| OPT-yiin_dz-05 | 六神旺衰（逢恩/归垣）标签试点注册到classical_enhancements |
| OPT-yuxiaji-03 | 彭祖百忌17条逐字书证补挂（天干十忌+地支十二忌+建除十二忌） |

## 二、经实测判定为不成立/已过期，予以撤销（22 条）

下列条目经实测证据推翻或确认已过期，**不执行**并记录理由，避免把错误结论写进仓库。

| OPT ID | 撤销/不执行理由 |
|---|---|
| OPT-taiyi_jinjing_dz-01 | 十二将「同名同序」为误判——书源L157-167与core TIAN_JIANG_ORDER 第6位起次序完全不同（天空/白虎/太常/玄武/太阴/天后 顺序相异），"0差异"验收不可达 |
| OPT-taiyi_jinjing_dz-02 | 昼夜贵人取值与书源相反——书L151「甲日朝治小吉暮治大吉」即昼小吉夜大吉，core NOBLE_DAY["甲"]=丑(大吉)/NIGHT=未(小吉) 恰反；"机制同源"结论错误 |
| OPT-huangji_jingshi_shu_dz-03 | 现状早已合规——§三 判据24条已全部为不适用(无对应学科)，第8条已入库、第9/20条部分，与建议要求一致 |
| OPT-huangji_jingshi_dz-04 | 非待办项——缺卷/题名不符是已落盘的§一/§五事实陈述，非优化项 |
| OPT-bushi_quanshu_dz-06 | 卷二无六十四卦六亲地支世应伏神全表——实测L694-3050 区间主体为《周易》卦爻辞，相关行仅23条，伏神段在L5519-5531(卷五)；落点数据不存在 |
| OPT-mingli_tanyuan_dz-04 | 前提误判——chart.py 实测零书源注释（grep 推年/命理探源 零命中），非"已补未逐行挂" |
| OPT-zengshan_buyi_dz-09 | 前提不成立——引擎无「忌神持世」否决路径（grep 零命中），且liuyao_step4.py:558 已有化出用神路径 |
| OPT-wuxing_jingji_dz-02 | 整条基于误判——shensha.py:49-50 已定义WANG_SHEN/JIE_SHA，:209-210 已_add("亡神"/"劫煞")，chart.py:28 已调用；已实现无需新增 |
| OPT-dunjia_yanyi_dz-01 | 落点字段不存在——works_registry 54条仅8字段(key/title/kind/discipline/sources/crosscheck/doc/tiny)，无notes；且§五已登记重复 |
| OPT-liuren_cuiyan_dz-10 | 映射无消费者——verdicts.json 无variants 节（现有键 _comment/verbatim_policy/preamble/men/richen/tianjiang）；书源L96/105/68为本书自有字非讹字 |
| OPT-liuren_xinjing_dz-07 | 行号张冠李戴+书证不存在——书源 grep 九宗门 零命中，「九科门」在L33/L218（非L220），L220内容为"八局之列分为九科" |
| OPT-lixuzhong_mingshu_dz-06 | 指向错误——L70=庚申/L71=辛酉(内容相同，庚申误作辛酉的复制讹条)，L72 辛酉是另一条不同命式，非同一句重出 |
| OPT-qimen_faqiao_dz-08 | 行号与计数错——列"五处"实为六处且L452重复计入；L452原文为「奇门占验类神皆本生克而定之故，不可执一而论」非加减规则 |
| OPT-sanming_zhimi_fu_dz-04 | 整条基于误读——书源 grep 阳奇/阴奇 零命中；L13「顺三竒主少年发逹，遇逆三竒主晚景享荣」之顺逆指运限年龄，非干支行进方向 |
| OPT-taiyi_mishu_dz-05 | 落点字段不存在——works_registry 无defects 字段，事实成立但须先定schema |
| OPT-taiyi_mishu_dz-06 | 越界——建议"书源吉凶断语narrative归档"违反骨架层铁律（同大六壬口径），太乙既 none-taiyi，断语归档无消费者 |
| OPT-xieji_bianfang_dz-05 | 表误认——L246「日表」/L299「二十八宿配日」经Read确认均为目录标题，无逐日二十八宿值数据，无法建抽样回归 |
| OPT-yizhangjing_dz-04 | 行号张冠李戴+书证不存在——L292/L293是命宫桃花（非core三合局TAO_HUA），L296是「论十二时夫妻犯」；书源 grep 六害 零命中 |
| OPT-liuren_xinjing_dz-06 | 现状已过期——provenance.json 已存在，字段集无variant_notes（无schema校验器，非硬缺口） |
| OPT-yuzhao_dingzhen_dz-04 | 现状已过期——yuzhao_dingzhen_dz.provenance.json 已存在（非"如尚无"） |
| OPT-bushi_zhengzong_dz-07 | 前提已过期——「暗動章定義原文缺」已被OPT-bushi_quanshu_dz-01(2026-10-07)填补；另两处行号错(L2606→L2612) |
| OPT-huangji_jingshi_shu_dz-05 | 行号张冠李戴——symbols.py:415 实为 bagua_lines 函数体内，XIAN_TIAN_TRIGRAM_NUMBERS 实际在 :428 |

## 三、待落实（276 条）

按学科分组，逐条自核行号后执行。

| 学科 | 条数 | OPT ID |
|---|---|---|
| liuyao | 60 | duanyi_tianji_dz-01、duanyi_tianji_dz-02、huangjince_dz-03、huangjince_dz-04、huozhulin_dz-01、huozhulin_dz-02、jingshi_yizhuan_dz-02、yiin_dz-01、yiin_dz-03、yilin_buyi_dz-02、yilin_buyi_dz-03、yimao_dz-01、yimao_dz-02、zengshan_buyi_dz-02、zengshan_buyi_dz-03、zengshan_buyi_dz-04、zengshan_buyi_dz-05、zhouyi_shangzhan_dz-01、bushi_quanshu_dz-03、bushi_zhengzong_dz-04、bushi_zhengzong_dz-05、duanyi_tianji_dz-03、duanyi_tianji_dz-04、huangjince_dz-05、huangjince_dz-06、huozhulin_dz-03、jingshi_yizhuan_dz-01、jingshi_yizhuan_dz-03、wenwang_jinqianke_dz-01、yiin_dz-04、yiin_dz-06、yilin_buyi_dz-04、yilin_buyi_dz-05、yilin_buyi_dz-06、yilin_buyi_dz-07、yimao_dz-03、yimao_dz-04、yimao_dz-05、yimao_dz-06、yimao_dz-07、zengshan_buyi_dz-06、zengshan_buyi_dz-07、zhouyi_shangzhan_dz-02、bushi_quanshu_dz-05、bushi_zhengzong_dz-06、duanyi_tianji_dz-05、duanyi_tianji_dz-06、huangjince_dz-07、huozhulin_dz-04、jingshi_yizhuan_dz-04、wenwang_jinqianke_dz-02、wenwang_jinqianke_dz-03、yiin_dz-07、yilin_buyi_dz-08、yimao_dz-08、yimao_dz-09、yimao_dz-10、zengshan_buyi_dz-08、zhouyi_shangzhan_dz-03、zhouyi_shangzhan_dz-04 |
| ming | 56 | lantai_miaoxuan_dz-01、lantai_miaoxuan_dz-02、lixuzhong_mingshu_dz-02、mingli_tanyuan_dz-02、mingli_tanyuan_dz-06、qiong_tong_bao_jian_dz-01、qiong_tong_bao_jian_dz-02、sanming_tonghui_dz-01、sanming_tonghui_dz-02、sanming_tonghui_dz-03、shenfeng_tongkao_dz-02、yuanhai_ziping_dz-01、yuanhai_ziping_dz-02、yuanhai_ziping_dz-03、ziping_zhenquan_pingzhu_dz-01、ditian_sui_chanwei_dz-02、ditian_sui_chanwei_dz-04、lantai_miaoxuan_dz-03、lantai_miaoxuan_dz-04、lixuzhong_mingshu_dz-01、lixuzhong_mingshu_dz-03、mingli_tanyuan_dz-03、qianli_minggao_dz-01、qiong_tong_bao_jian_dz-03、sanming_tonghui_dz-04、sanming_tonghui_dz-05、sanming_zhimi_fu_dz-01、shenfeng_tongkao_dz-03、shenfeng_tongkao_dz-04、wuxing_jingji_dz-01、wuxing_jingji_dz-03、yuanhai_ziping_dz-04、yuzhao_dingzhen_dz-01、yuzhao_dingzhen_dz-02、ziping_zhenquan_pingzhu_dz-03、ziping_zhenquan_pingzhu_dz-04、ditian_sui_chanwei_dz-03、lantai_miaoxuan_dz-05、lixuzhong_mingshu_dz-04、lixuzhong_mingshu_dz-05、lixuzhong_mingshu_dz-07、mingli_tanyuan_dz-05、qianli_minggao_dz-02、qianli_minggao_dz-03、qianli_minggao_dz-04、qiong_tong_bao_jian_dz-04、sanming_tonghui_dz-06、sanming_tonghui_dz-07、sanming_zhimi_fu_dz-02、sanming_zhimi_fu_dz-03、sanming_zhimi_fu_dz-05、shenfeng_tongkao_dz-05、wuxing_jingji_dz-04、yuanhai_ziping_dz-05、yuzhao_dingzhen_dz-03、ziping_zhenquan_pingzhu_dz-05 |
| liuren | 53 | liu-ren-da-quan-01、liu-ren-da-quan-02、liuren_cuiyan_dz-01、liuren_cuiyan_dz-02、liuren_cuiyan_dz-04、liuren_cuiyan_dz-09、liuren_duanan_dz-01、liuren_shending_dz-02、liuren_shending_dz-07、liuren_xinjing_dz-01、liuren_xinjing_dz-02、liuren_xinjing_dz-03、liuren_zhinan_dz-01、liuren_zhinan_dz-02、liuren_zhinan_dz-04、liuren_zhinan_dz-07、liuren_zhizhi_yuding_dz-01、liuren_zhizhi_yuding_dz-02、liuren_zhizhi_yuding_dz-03、rengui_dz-01、rengui_dz-02、rengui_dz-03、liu-ren-da-quan-03、liuren_cuiyan_dz-05、liuren_cuiyan_dz-06、liuren_cuiyan_dz-07、liuren_cuiyan_dz-08、liuren_shending_dz-05、liuren_shending_dz-06、liuren_xinjing_dz-04、liuren_xinjing_dz-05、liuren_zhinan_dz-03、liuren_zhinan_dz-05、liuren_zhinan_dz-06、liuren_zhinan_dz-08、liuren_zhizhi_yuding_dz-04、liuren_zhizhi_yuding_dz-05、liuren_zhizhi_yuding_dz-06、rengui_dz-04、rengui_dz-05、rengui_dz-06、liuren_cuiyan_dz-11、liuren_cuiyan_dz-12、liuren_duanan_dz-03、liuren_duanan_dz-04、liuren_shending_dz-08、liuren_shending_dz-09、liuren_zhinan_dz-09、liuren_zhinan_dz-10、liuren_zhinan_dz-11、liuren_zhizhi_yuding_dz-07、rengui_dz-07、rengui_dz-08 |
| none-qimen | 25 | dunjia_yanyi_dz-04、qimen_baojian_dz-01、qimen_baojian_dz-02、qimen_faqiao_dz-02、qimen_faqiao_dz-03、qimen_tongzong_dz-02、qimen_tongzong_dz-03、qimen_tongzong_dz-04、qimen_baojian_dz-03、qimen_baojian_dz-04、qimen_faqiao_dz-04、qimen_faqiao_dz-06、qimen_faqiao_dz-07、qimen_tongzong_dz-05、qimen_tongzong_dz-06、yan-bo-diao-sou-ge-01、dunjia_yanyi_dz-05、qimen_baojian_dz-05、qimen_baojian_dz-06、qimen_faqiao_dz-09、qimen_faqiao_dz-10、qimen_tongzong_dz-07、qimen_tongzong_dz-08、yan-bo-diao-sou-ge-02、yan-bo-diao-sou-ge-03 |
| none-tonggang | 14 | jiaoshi_yilin_dz-01、jiaoshi_yilin_dz-02、jiaoshi_yilin_dz-03、huangji_jingshi_shu_dz-04、jiaoshi_yilin_dz-04、jiaoshi_yilin_dz-05、jiaoshi_yilin_dz-06、wuxing_dayi_dz-01、wuxing_dayi_dz-02、huangji_jingshi_shu_dz-06、jiaoshi_yilin_dz-07、jiaoshi_yilin_dz-08、wuxing_dayi_dz-03、wuxing_dayi_dz-04 |
| none-zazhan | 14 | cezi_midie_dz-01、cezi_midie_dz-02、cezi_midie_dz-03、cezi_midie_dz-04、tuibeitu_dz-01、tuibeitu_dz-02、tuibeitu_dz-03、tuibeitu_dz-04、zhougong_jiemeng_dz-01、zhougong_jiemeng_dz-02、zhougong_jiemeng_dz-03、zhuge_shenshu_dz-01、zhuge_shenshu_dz-02、zhuge_shenshu_dz-03 |
| zeji | 13 | xieji_bianfang_dz-01、xingli_kaoyuan_dz-02、xingli_kaoyuan_dz-03、xingli_kaoyuan_dz-04、xieji_bianfang_dz-02、xieji_bianfang_dz-03、xingli_kaoyuan_dz-05、xingli_kaoyuan_dz-06、xingli_kaoyuan_dz-07、xieji_bianfang_dz-04、xingli_kaoyuan_dz-08、xingli_kaoyuan_dz-09、xingli_kaoyuan_dz-10 |
| none-taiyi | 10 | taiyi_jinjing_dz-03、taiyi_jinjing_dz-04、taiyi_jinjing_dz-05、taiyi_jinjing_dz-06、taiyi_mishu_dz-02、taiyi_mishu_dz-04、taiyi_jinjing_dz-07、taiyi_jinjing_dz-08、taiyi_mishu_dz-01、taiyi_mishu_dz-03 |
| xiaoliuren | 9 | yizhangjing_dz-01、yuxiaji-01、yizhangjing_dz-02、yizhangjing_dz-03、yuxiaji-02、yuxiaji-04、yizhangjing_dz-05、yuxiaji-05、yuxiaji-06 |
| meihua | 8 | meihua_yishu_dz-02、meihua_yishu_dz-01、meihua_yishu_dz-04、meihua_yishu_dz-05、meihua_yishu_dz-03、meihua_yishu_dz-06、meihua_yishu_dz-07、meihua_yishu_dz-08 |
| lingqi | 2 | lingqijing_dz-01、lingqijing_dz-03 |
| ziwei | 3 | zi-wei-dou-shu-quan-shu-01、zi-wei-dou-shu-quan-shu-02、zi-wei-dou-shu-quan-shu-03 |

## 四、第三批落实（2026-10-07 收口）

| 批次 | 条数 | 内容 |
|---|---|---|
| A 类批量归档 | 113 | 经实测确认为「登记不动/留底/不适用/超范围」，一次性归档至 `docs/OPT-ARCHIVED.md`，无需代码改动 |
| B 类补对源 | 35 | 全部补注记/对源/外置语料（零判定变更）：六爻 19、命科 10、无学科 16 |
| D/C 类新增 | 28+ | 大六壬结构表 20、择吉 5、梅花 3；新增 `structure_tags.py`、`zeji_tables.py` 四门/干鬼/三杀/人神表等 |
| 回退项 | 1 | 三项结构标签（助鬼伤身/门类动静/财官伏五乡）接入 `advanced_analysis` 后致 liuyao tune strict 96.8%→93.1%（应期 20/20→12/20），违反铁律四，已回退接入（实现与引文保留），待有 holdout 用例后重新接入 |

**新增机械门**：大六壬 `check.py` 增 [1e] 结构标签全覆盖、[1f] 课体别名、[1g] 月支判囚死、[1h] 三方条数对账；`check_source_readings.py` README 增「跨行表格行」引用安全子条；择吉一致性回归脚本含负例自证。
