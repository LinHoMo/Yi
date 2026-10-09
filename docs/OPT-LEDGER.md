# 优化项裁定台账（2026-10-07 实测裁定 · 表内实数 318 条）

> **口径横幅（2026-10-09 按两科范围重算）**
>
> - **总数打架**：原标题写「全 304 条实测」、正文首行写「319 条 OPT」、§三 段标题写「276 条」，
>   三个数互不相等，也都不等于表内实数。现按**表内实数**统一为 **318 条**：
>   §一 29 ＋ §二 22 ＋ §三 267 ＝ 318。
>   数法（可复跑）：`grep -c "^| OPT-" docs/OPT-LEDGER.md` = **51**（§一 29 ＋ §二 22）；
>   §三 是 12 行「学科 · 条数 · OPT ID」分组表，把第 3 格按顿号「、」切开后展开得 **267** 个 ID
>   （逐行核过：每行「标称条数」与该行 ID 实数相等，60/56/53/25/14/14/13/10/9/8/2/3，合计 267；
>   段标题原写 276 无出处，已订正）。
> - **现行 / 历史分列**：2026-10-09 两科收缩（commit `60b2403`）删除六科及其书源、解读文档与引擎目录，
>   本台账 **167 条**的落点已不存在，逐条就地标注「（已随 2026-10-09 两科收缩删除，仅历史）」，
>   并从各节「现行」计数里剔除：现行可指认 **151 条** = §一 18 ＋ §二 11 ＋ §三 122；
>   历史 **167 条** = §一 11 ＋ §二 11 ＋ §三 145。
> - **落点判定口径**：OPT ID 的书名 key 若 ∈ `data/sources/works_registry.json` 现登记的 **27 部**
>   即「现存」，否则「落点已删」（含 `liuren_*`、`meihua_*`、`ziwei_*`、`xiaoliuren_*`、
>   `lingqijing_*`、`xieji_bianfang_dz`/`xingli_kaoyuan_dz`、`qimen_*`/`dunjia_*`/`yan-bo-diao-sou-ge`、
>   `taiyi_*`、`cezi_*`/`tuibeitu_*`/`zhuge_*`/`zhougong_*`、`jiaoshi_yilin_dz`）。
>   唯一例外：§二 的 `OPT-huangji_jingshi_dz-04` 是 `huangji_jingshi_shu_dz`（该书**现存**）的
>   笔误 key，按现存计。
> - **与 `data/sources/opt_status.json` 不同口径，不可互相换算**：状态文件只登记「已处理」ID，
>   现值 done **115**／archived **113**／rejected **21**——三数相加 **249**，但去重后**只有 245 个不同 ID**
>   （实测 4 条跨类重复登记：`ditian_sui_chanwei_dz-04`、`zhouyi_shangzhan_dz-04` 同列 done＋archived，
>   `sanming_zhimi_fu_dz-04` 同列 done＋rejected，`dunjia_yanyi_dz-05` 同列 archived＋rejected；
>   本轮只登记不改动，详见该文件 `_scope_note_2026-10-09`）。
>   与本台账的实测交集：§一 29 条中 18 条已登记、§二 22 条中 20 条已登记、
>   §三 267 条中 195 条已登记（余 72 条落点已删、从未登记）。
>   `docs/source-readings/INDEX.md` 的「待办 0 项」是按**现存 27 部解读文档**现算的
>   （文档内 155 个 OPT ID 全部已登记），与本台账这份 2026-10-07 快照口径不同，两个数各自成立。

本台账是 **318 条 OPT**（表内实数，数法见上）的**实测裁定结果**。每条均经子代理核验 + 主代理复核（行号以 cat -n 口径 Read 核准）。

## 一、已落实（表内 29 条；现行 18 条，另 11 条落点已删仅历史）

段标题原写「22 条」，与表内 29 行不符（2026-10-09 按 `grep -c "^| OPT-"` 分段计数订正）。
见下方明细；每条单独跑 `tools/eval.py` + `check_source_readings.py`，全库读数持续零回归。

| OPT ID | 落实内容 |
|---|---|
| OPT-huangji_jingshi_shu_dz-01 | 推翻"全文重影"+provenance双口径 |
| OPT-huangji_jingshi_shu_dz-02 | 护栏已存在且更严 |
| OPT-huangjince_dz-01 | 伏神引文两处差异三源并记 |
| OPT-huangjince_dz-02 | 游魂归魂跨书误挂3处改真实原文 |
| OPT-liuren_shending_dz-01 | 昼夜贵人壬癸昼巳夜卯（三源互证） （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-liuren_shending_dz-03 | 新增十二将家支表TWELVE_JIANG_HOME （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-liuren_shending_dz-04 | 新增日德神定经双表（不覆盖现值） （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-liuren_cuiyan_dz-03 | 天将位次补《六壬粹言》L98-108对源（复核确认零偏离） （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-xingli_kaoyuan_dz-01 | basis错指订正+天德月德书源行号补齐 （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-qimen_faqiao_dz-01 | 文档已落盘，现状过期 （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-qimen_tongzong_dz-01 | 文档已落盘，现状过期 （已随 2026-10-09 两科收缩删除，仅历史） |
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
| OPT-lingqijing_dz-02 | 阴阳㝃组附录独立key核查登记（124课+appendix分离确认） （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-liuren_duanan_dz-02 | 日为人/辰为宅/合支空亡/墓+迟滞神结构评估（纯结构，不动判据） （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-qimen_faqiao_dz-05 | 奇门法窍六十时格局格名词表抽取（63格名14类，法窍L3281-5848） （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-yiin_dz-05 | 六神旺衰（逢恩/归垣）标签试点注册到classical_enhancements |
| OPT-yuxiaji-03 | 彭祖百忌17条逐字书证补挂（天干十忌+地支十二忌+建除十二忌） （已随 2026-10-09 两科收缩删除，仅历史） |

## 二、经实测判定为不成立/已过期，予以撤销（表内 22 条 ✓；现行 11 条，另 11 条落点已删仅历史）

段标题原写「22 条」与表内行数相符（`grep -c "^| OPT-"` 分段计数复核），不订正；
但其中 11 条的落点书/科已随 2026-10-09 两科收缩删除，已逐条标注、从现行计数剔除。

下列条目经实测证据推翻或确认已过期，**不执行**并记录理由，避免把错误结论写进仓库。

| OPT ID | 撤销/不执行理由 |
|---|---|
| OPT-taiyi_jinjing_dz-01 | 十二将「同名同序」为误判——书源L157-167与core TIAN_JIANG_ORDER 第6位起次序完全不同（天空/白虎/太常/玄武/太阴/天后 顺序相异），"0差异"验收不可达 （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-taiyi_jinjing_dz-02 | 昼夜贵人取值与书源相反——书L151「甲日朝治小吉暮治大吉」即昼小吉夜大吉，core NOBLE_DAY["甲"]=丑(大吉)/NIGHT=未(小吉) 恰反；"机制同源"结论错误 （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-huangji_jingshi_shu_dz-03 | 现状早已合规——§三 判据24条已全部为不适用(无对应学科)，第8条已入库、第9/20条部分，与建议要求一致 |
| OPT-huangji_jingshi_dz-04 | 非待办项——缺卷/题名不符是已落盘的§一/§五事实陈述，非优化项 |
| OPT-bushi_quanshu_dz-06 | 卷二无六十四卦六亲地支世应伏神全表——实测L694-3050 区间主体为《周易》卦爻辞，相关行仅23条，伏神段在L5519-5531(卷五)；落点数据不存在 |
| OPT-mingli_tanyuan_dz-04 | 前提误判——chart.py 实测零书源注释（grep 推年/命理探源 零命中），非"已补未逐行挂" |
| OPT-zengshan_buyi_dz-09 | 前提不成立——引擎无「忌神持世」否决路径（grep 零命中），且liuyao_step4.py:558 已有化出用神路径 |
| OPT-wuxing_jingji_dz-02 | 整条基于误判——shensha.py:49-50 已定义WANG_SHEN/JIE_SHA，:209-210 已_add("亡神"/"劫煞")，chart.py:28 已调用；已实现无需新增 |
| OPT-dunjia_yanyi_dz-01 | 落点字段不存在——works_registry 54条仅8字段(key/title/kind/discipline/sources/crosscheck/doc/tiny)，无notes；且§五已登记重复 （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-liuren_cuiyan_dz-10 | 映射无消费者——verdicts.json 无variants 节（现有键 _comment/verbatim_policy/preamble/men/richen/tianjiang）；书源L96/105/68为本书自有字非讹字 （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-liuren_xinjing_dz-07 | 行号张冠李戴+书证不存在——书源 grep 九宗门 零命中，「九科门」在L33/L218（非L220），L220内容为"八局之列分为九科" （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-lixuzhong_mingshu_dz-06 | 指向错误——L70=庚申/L71=辛酉(内容相同，庚申误作辛酉的复制讹条)，L72 辛酉是另一条不同命式，非同一句重出 |
| OPT-qimen_faqiao_dz-08 | 行号与计数错——列"五处"实为六处且L452重复计入；L452原文为「奇门占验类神皆本生克而定之故，不可执一而论」非加减规则 （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-sanming_zhimi_fu_dz-04 | 整条基于误读——书源 grep 阳奇/阴奇 零命中；L13「顺三竒主少年发逹，遇逆三竒主晚景享荣」之顺逆指运限年龄，非干支行进方向 |
| OPT-taiyi_mishu_dz-05 | 落点字段不存在——works_registry 无defects 字段，事实成立但须先定schema （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-taiyi_mishu_dz-06 | 越界——建议"书源吉凶断语narrative归档"违反骨架层铁律（同大六壬口径），太乙既 none-taiyi，断语归档无消费者 （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-xieji_bianfang_dz-05 | 表误认——L246「日表」/L299「二十八宿配日」经Read确认均为目录标题，无逐日二十八宿值数据，无法建抽样回归 （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-yizhangjing_dz-04 | 行号张冠李戴+书证不存在——L292/L293是命宫桃花（非core三合局TAO_HUA），L296是「论十二时夫妻犯」；书源 grep 六害 零命中 （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-liuren_xinjing_dz-06 | 现状已过期——provenance.json 已存在，字段集无variant_notes（无schema校验器，非硬缺口） （已随 2026-10-09 两科收缩删除，仅历史） |
| OPT-yuzhao_dingzhen_dz-04 | 现状已过期——yuzhao_dingzhen_dz.provenance.json 已存在（非"如尚无"） |
| OPT-bushi_zhengzong_dz-07 | 前提已过期——「暗動章定義原文缺」已被OPT-bushi_quanshu_dz-01(2026-10-07)填补；另两处行号错(L2606→L2612) |
| OPT-huangji_jingshi_shu_dz-05 | 行号张冠李戴——symbols.py:415 实为 bagua_lines 函数体内，XIAN_TIAN_TRIGRAM_NUMBERS 实际在 :428 |

## 三、待落实（表内 267 条 ID；现行 122 条，另 145 条落点已删仅历史）

段标题原写「276 条」，与表内 12 行 ID 展开实数 **267** 不符（各行标称条数相加亦为 267：
60+56+53+25+14+14+13+10+9+8+2+3），已订正。

按学科分组，逐条自核行号后执行。

> **本段是 2026-10-07 时点的待办快照，现时态已不成立**（2026-10-09 实测）：
> 表内 267 条中 **195 条**已进 `data/sources/opt_status.json`（done/archived/rejected 之一）、
> **72 条**从未登记——这 72 条的落点（书源＋解读文档＋学科目录）已全部随 `60b2403` 消失，
> 无法再执行。现存 27 部解读文档里的 155 个 OPT ID **全部已登记**，故
> `docs/source-readings/INDEX.md` 现算「待办优化清单 0 项」。**不得把本段当作现行待办读数引用。**
> 落点已删的 145 条按行标注（`liuren`/`none-qimen`/`none-zazhan`/`zeji`/`none-taiyi`/
> `xiaoliuren`/`meihua`/`lingqi`/`ziwei` 九行整行已删；`none-tonggang` 行内 8 条 `jiaoshi_yilin_dz-*`
> 已删、其余 6 条现存；`liuyao`、`ming` 两行 116 条落点均现存）。

| 学科 | 条数 | OPT ID |
|---|---|---|
| liuyao | 60 | duanyi_tianji_dz-01、duanyi_tianji_dz-02、huangjince_dz-03、huangjince_dz-04、huozhulin_dz-01、huozhulin_dz-02、jingshi_yizhuan_dz-02、yiin_dz-01、yiin_dz-03、yilin_buyi_dz-02、yilin_buyi_dz-03、yimao_dz-01、yimao_dz-02、zengshan_buyi_dz-02、zengshan_buyi_dz-03、zengshan_buyi_dz-04、zengshan_buyi_dz-05、zhouyi_shangzhan_dz-01、bushi_quanshu_dz-03、bushi_zhengzong_dz-04、bushi_zhengzong_dz-05、duanyi_tianji_dz-03、duanyi_tianji_dz-04、huangjince_dz-05、huangjince_dz-06、huozhulin_dz-03、jingshi_yizhuan_dz-01、jingshi_yizhuan_dz-03、wenwang_jinqianke_dz-01、yiin_dz-04、yiin_dz-06、yilin_buyi_dz-04、yilin_buyi_dz-05、yilin_buyi_dz-06、yilin_buyi_dz-07、yimao_dz-03、yimao_dz-04、yimao_dz-05、yimao_dz-06、yimao_dz-07、zengshan_buyi_dz-06、zengshan_buyi_dz-07、zhouyi_shangzhan_dz-02、bushi_quanshu_dz-05、bushi_zhengzong_dz-06、duanyi_tianji_dz-05、duanyi_tianji_dz-06、huangjince_dz-07、huozhulin_dz-04、jingshi_yizhuan_dz-04、wenwang_jinqianke_dz-02、wenwang_jinqianke_dz-03、yiin_dz-07、yilin_buyi_dz-08、yimao_dz-08、yimao_dz-09、yimao_dz-10、zengshan_buyi_dz-08、zhouyi_shangzhan_dz-03、zhouyi_shangzhan_dz-04 |
| ming | 56 | lantai_miaoxuan_dz-01、lantai_miaoxuan_dz-02、lixuzhong_mingshu_dz-02、mingli_tanyuan_dz-02、mingli_tanyuan_dz-06、qiong_tong_bao_jian_dz-01、qiong_tong_bao_jian_dz-02、sanming_tonghui_dz-01、sanming_tonghui_dz-02、sanming_tonghui_dz-03、shenfeng_tongkao_dz-02、yuanhai_ziping_dz-01、yuanhai_ziping_dz-02、yuanhai_ziping_dz-03、ziping_zhenquan_pingzhu_dz-01、ditian_sui_chanwei_dz-02、ditian_sui_chanwei_dz-04、lantai_miaoxuan_dz-03、lantai_miaoxuan_dz-04、lixuzhong_mingshu_dz-01、lixuzhong_mingshu_dz-03、mingli_tanyuan_dz-03、qianli_minggao_dz-01、qiong_tong_bao_jian_dz-03、sanming_tonghui_dz-04、sanming_tonghui_dz-05、sanming_zhimi_fu_dz-01、shenfeng_tongkao_dz-03、shenfeng_tongkao_dz-04、wuxing_jingji_dz-01、wuxing_jingji_dz-03、yuanhai_ziping_dz-04、yuzhao_dingzhen_dz-01、yuzhao_dingzhen_dz-02、ziping_zhenquan_pingzhu_dz-03、ziping_zhenquan_pingzhu_dz-04、ditian_sui_chanwei_dz-03、lantai_miaoxuan_dz-05、lixuzhong_mingshu_dz-04、lixuzhong_mingshu_dz-05、lixuzhong_mingshu_dz-07、mingli_tanyuan_dz-05、qianli_minggao_dz-02、qianli_minggao_dz-03、qianli_minggao_dz-04、qiong_tong_bao_jian_dz-04、sanming_tonghui_dz-06、sanming_tonghui_dz-07、sanming_zhimi_fu_dz-02、sanming_zhimi_fu_dz-03、sanming_zhimi_fu_dz-05、shenfeng_tongkao_dz-05、wuxing_jingji_dz-04、yuanhai_ziping_dz-05、yuzhao_dingzhen_dz-03、ziping_zhenquan_pingzhu_dz-05 |
| liuren （已随 2026-10-09 两科收缩删除，仅历史） | 53 | liu-ren-da-quan-01、liu-ren-da-quan-02、liuren_cuiyan_dz-01、liuren_cuiyan_dz-02、liuren_cuiyan_dz-04、liuren_cuiyan_dz-09、liuren_duanan_dz-01、liuren_shending_dz-02、liuren_shending_dz-07、liuren_xinjing_dz-01、liuren_xinjing_dz-02、liuren_xinjing_dz-03、liuren_zhinan_dz-01、liuren_zhinan_dz-02、liuren_zhinan_dz-04、liuren_zhinan_dz-07、liuren_zhizhi_yuding_dz-01、liuren_zhizhi_yuding_dz-02、liuren_zhizhi_yuding_dz-03、rengui_dz-01、rengui_dz-02、rengui_dz-03、liu-ren-da-quan-03、liuren_cuiyan_dz-05、liuren_cuiyan_dz-06、liuren_cuiyan_dz-07、liuren_cuiyan_dz-08、liuren_shending_dz-05、liuren_shending_dz-06、liuren_xinjing_dz-04、liuren_xinjing_dz-05、liuren_zhinan_dz-03、liuren_zhinan_dz-05、liuren_zhinan_dz-06、liuren_zhinan_dz-08、liuren_zhizhi_yuding_dz-04、liuren_zhizhi_yuding_dz-05、liuren_zhizhi_yuding_dz-06、rengui_dz-04、rengui_dz-05、rengui_dz-06、liuren_cuiyan_dz-11、liuren_cuiyan_dz-12、liuren_duanan_dz-03、liuren_duanan_dz-04、liuren_shending_dz-08、liuren_shending_dz-09、liuren_zhinan_dz-09、liuren_zhinan_dz-10、liuren_zhinan_dz-11、liuren_zhizhi_yuding_dz-07、rengui_dz-07、rengui_dz-08 |
| none-qimen （已随 2026-10-09 两科收缩删除，仅历史） | 25 | dunjia_yanyi_dz-04、qimen_baojian_dz-01、qimen_baojian_dz-02、qimen_faqiao_dz-02、qimen_faqiao_dz-03、qimen_tongzong_dz-02、qimen_tongzong_dz-03、qimen_tongzong_dz-04、qimen_baojian_dz-03、qimen_baojian_dz-04、qimen_faqiao_dz-04、qimen_faqiao_dz-06、qimen_faqiao_dz-07、qimen_tongzong_dz-05、qimen_tongzong_dz-06、yan-bo-diao-sou-ge-01、dunjia_yanyi_dz-05、qimen_baojian_dz-05、qimen_baojian_dz-06、qimen_faqiao_dz-09、qimen_faqiao_dz-10、qimen_tongzong_dz-07、qimen_tongzong_dz-08、yan-bo-diao-sou-ge-02、yan-bo-diao-sou-ge-03 |
| none-tonggang | 14 | jiaoshi_yilin_dz-01、jiaoshi_yilin_dz-02、jiaoshi_yilin_dz-03、huangji_jingshi_shu_dz-04、jiaoshi_yilin_dz-04、jiaoshi_yilin_dz-05、jiaoshi_yilin_dz-06、wuxing_dayi_dz-01、wuxing_dayi_dz-02、huangji_jingshi_shu_dz-06、jiaoshi_yilin_dz-07、jiaoshi_yilin_dz-08、wuxing_dayi_dz-03、wuxing_dayi_dz-04 （本行 14 条中 8 条 `jiaoshi_yilin_dz-01…08` 落点《焦氏易林》——书源与解读文档已随 2026-10-09 两科收缩删除，仅历史；其余 6 条（《皇极经世书》2 + 《五行大义》4）落点现存） |
| none-zazhan （已随 2026-10-09 两科收缩删除，仅历史） | 14 | cezi_midie_dz-01、cezi_midie_dz-02、cezi_midie_dz-03、cezi_midie_dz-04、tuibeitu_dz-01、tuibeitu_dz-02、tuibeitu_dz-03、tuibeitu_dz-04、zhougong_jiemeng_dz-01、zhougong_jiemeng_dz-02、zhougong_jiemeng_dz-03、zhuge_shenshu_dz-01、zhuge_shenshu_dz-02、zhuge_shenshu_dz-03 |
| zeji （已随 2026-10-09 两科收缩删除，仅历史） | 13 | xieji_bianfang_dz-01、xingli_kaoyuan_dz-02、xingli_kaoyuan_dz-03、xingli_kaoyuan_dz-04、xieji_bianfang_dz-02、xieji_bianfang_dz-03、xingli_kaoyuan_dz-05、xingli_kaoyuan_dz-06、xingli_kaoyuan_dz-07、xieji_bianfang_dz-04、xingli_kaoyuan_dz-08、xingli_kaoyuan_dz-09、xingli_kaoyuan_dz-10 |
| none-taiyi （已随 2026-10-09 两科收缩删除，仅历史） | 10 | taiyi_jinjing_dz-03、taiyi_jinjing_dz-04、taiyi_jinjing_dz-05、taiyi_jinjing_dz-06、taiyi_mishu_dz-02、taiyi_mishu_dz-04、taiyi_jinjing_dz-07、taiyi_jinjing_dz-08、taiyi_mishu_dz-01、taiyi_mishu_dz-03 |
| xiaoliuren （已随 2026-10-09 两科收缩删除，仅历史） | 9 | yizhangjing_dz-01、yuxiaji-01、yizhangjing_dz-02、yizhangjing_dz-03、yuxiaji-02、yuxiaji-04、yizhangjing_dz-05、yuxiaji-05、yuxiaji-06 |
| meihua （已随 2026-10-09 两科收缩删除，仅历史） | 8 | meihua_yishu_dz-02、meihua_yishu_dz-01、meihua_yishu_dz-04、meihua_yishu_dz-05、meihua_yishu_dz-03、meihua_yishu_dz-06、meihua_yishu_dz-07、meihua_yishu_dz-08 |
| lingqi （已随 2026-10-09 两科收缩删除，仅历史） | 2 | lingqijing_dz-01、lingqijing_dz-03 |
| ziwei （已随 2026-10-09 两科收缩删除，仅历史） | 3 | zi-wei-dou-shu-quan-shu-01、zi-wei-dou-shu-quan-shu-02、zi-wei-dou-shu-quan-shu-03 |

## 四、第三批落实（2026-10-07 收口）

| 批次 | 条数 | 内容 |
|---|---|---|
| A 类批量归档 | 113 | 经实测确认为「登记不动/留底/不适用/超范围」，一次性归档至 `docs/OPT-ARCHIVED.md`，无需代码改动（2026-10-09 核：该文件表内确为 **113 行** ✓；其中 **73 行**落点已随两科收缩删除，见该文件的同口径标注） |
| B 类补对源 | 35 | 全部补注记/对源/外置语料（零判定变更）：六爻 19、命科 10、无学科 16 ⚠️ **本行自身打架**：19＋10＋16 ＝ **45**，与标称 35 不符；本段未列 ID，无法从表内重算，故不擅自改数，仅登记为**不可核验**（2026-10-09） |
| D/C 类新增 | 28+ | （已随 2026-10-09 两科收缩删除，仅历史）大六壬结构表 20、择吉 5、梅花 3；新增 `structure_tags.py`、`zeji_tables.py` 四门/干鬼/三杀/人神表等 |
| 回退项 | 1 | 三项结构标签（助鬼伤身/门类动静/财官伏五乡）接入 `advanced_analysis` 后致 liuyao tune strict 96.8%→93.1%（应期 20/20→12/20），违反铁律四，已回退接入（实现与引文保留），待有 holdout 用例后重新接入 |

**新增机械门**：大六壬 `check.py` 增 [1e] 结构标签全覆盖、[1f] 课体别名、[1g] 月支判囚死、[1h] 三方条数对账；`check_source_readings.py` README 增「跨行表格行」引用安全子条；择吉一致性回归脚本含负例自证。

> **2026-10-09 订正（本句两处会被读成「现存」**）：
> ① 这里的 `[1e]–[1h]` 是**已删学科自己的** `disciplines/liuren/dev_tools/check.py` 里的门
> （该文件已删；取历史版本核对：`git show HEAD~1` 加同名路径，L464/522/564/574 即这四条标签），
> 该文件与 `disciplines/liuren/` 整目录已随 `60b2403` 删除，**今不存在**。
> 根 `tools/check.py` 今天也有 `[1e]–[1h]` 四个标签，但**是另外的门**
> （[1e] 能力矩阵锁、[1f] 输入协议指纹、[1g] 案例库隔离、[1h] 深链短键锁），与本题无关，
> 不得据此认为这四条已删门仍在位。
> ② 「择吉一致性回归脚本」与其书源、解读文档一并随择吉科删除，不可复跑。
> ③ `check_source_readings.py` README 的「跨行表格行」引用安全子条**规则文本仍在**
> （实测 `docs/source-readings/README.md:56`），但它标注的出处 `OPT-qimen_tongzong_dz-08`
> 所指《奇门遁甲统宗》书源与解读文档已随收缩删除——该子条本身不依赖已删科，仍对现存 27 部生效，
> 只是举例出处已成历史（该 README 不在本轮改范围内，已作为转交项登记）。
