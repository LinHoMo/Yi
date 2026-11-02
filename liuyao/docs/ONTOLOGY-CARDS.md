# 易学图谱概念卡片（自动生成）

> 由 `dev_tools/render_ontology.py` 从 `data/ontology/` 生成。
> 每张卡片：定义 → 向上哲学推演链 → 向下派生 → 书证 → 代码锚点。
> 改 ontology 后重跑本器即可刷新。


## L0 · 元理层（哲学公理）

### 八卦  `yi.l0.bagua`
- **定义**：乾兑离震巽坎艮坤，阴阳三爻叠而成，象天地雷风水火山泽。由四象重卦而生。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua
- **派生**：yi.l1.najia
- **依据**：yi.l0.sixiang

### 两仪（阴阳）  `yi.l0.liangyi`
- **定义**：太极动而生阳、静而生阴，一分为二。阳主动、主刚、主显；阴主静、主柔、主隐。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi
- **派生**：yi.l0.sixiang、yi.l0.wuxing、yi.l0.bagua
- **依据**：yi.l0.taiji

### 四象  `yi.l0.sixiang`
- **定义**：两仪生四象：太阳、少阴、少阳、太阴。阴阳之上各分阴阳，成老少之别。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang
- **派生**：yi.l0.bagua
- **依据**：yi.l0.liangyi

### 太极  `yi.l0.taiji`
- **定义**：无极而太极，天地未分之混沌元气，万物之始。
- **派生**：yi.l0.liangyi

### 五行  `yi.l0.wuxing`
- **定义**：金木水火土五种动能。相生以互济，相克以制约——无生则无发育，无克则无节制。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing
- **派生**：yi.l0.wuxing.sheng、yi.l0.wuxing.ke
- **依据**：yi.l0.liangyi

### 五行相克  `yi.l0.wuxing.ke`
- **定义**：金克木、木克土、土克水、水克火、火克金。克者，制也、约也。过克则伤，反克则侮。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke
- **派生**：yi.l1.wuxing.ke_cycle
- **依据**：yi.l0.wuxing

### 五行相生  `yi.l0.wuxing.sheng`
- **定义**：木生火、火生土、土生金、金生水、水生木。生者，助也、育也。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng
- **派生**：yi.l1.wuxing.sheng_cycle
- **依据**：yi.l0.wuxing


## L1 · 象数层（模型）

### 六冲（地支对冲）  `yi.l1.branch.chong`
- **定义**：子午冲、丑未冲、寅申冲、卯酉冲、辰戌冲、巳亥冲。冲者，散也、动也、解也。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.branch.chong
- **派生**：yi.l2.concept.huitouke_chongjie
- **依据**：yi.l0.wuxing.ke
- **代码锚点**：`yishu_core/symbols.py:CHONG_PAIRS`

### 六合（地支相合）  `yi.l1.branch.he`
- **定义**：子丑合、寅亥合、卯戌合、辰酉合、巳申合、午未合。合者，聚也、亲也、绊也。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l1.branch.he
- **依据**：yi.l0.liangyi
- **代码锚点**：`yishu_core/symbols.py:HE_PAIRS`

### 纳甲装卦  `yi.l1.najia`
- **定义**：八卦各纳天干、地支，六亲（父母兄弟妻财官鬼子孙）由宫五行与爻五行的生克关系定出。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia
- **依据**：yi.l0.bagua、yi.l1.wuxing.ke_cycle
- **代码锚点**：`yishu_core/symbols.py:NAJIA_BRANCHES`

### 三合局  `yi.l1.sanhe`
- **定义**：三支合成一局（生旺墓）：申子辰合水、寅午戌合火、巳酉丑合金、亥卯未合木。合则气聚。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.sanhe
- **依据**：yi.l0.wuxing.sheng
- **代码锚点**：`yishu_core/symbols.py:SAN_HE_GROUPS`

### 三刑  `yi.l1.sanxing`
- **定义**：地支相刑：无恩（寅巳申）、恃势（丑戌未）、无礼（子卯）、自刑（辰午酉亥）。刑主伤、主是非。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.sanxing
- **依据**：yi.l0.wuxing.ke
- **代码锚点**：`yishu_core/symbols.py:THREE_PUNISHMENTS`

### 十二长生  `yi.l1.shier_changsheng`
- **定义**：五行在十二地支上的生死进程：长生→沐浴→冠带→临官→帝旺→衰→病→死→墓→绝→胎→养。爻临长生帝旺为旺，临死墓绝为衰。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.shier_changsheng
- **依据**：yi.l0.wuxing.sheng
- **代码锚点**：`yishu_core/symbols.py:TWELVE_GROWTH_STAGES`

### 五行相克表  `yi.l1.wuxing.ke_cycle`
- **定义**：木→土→水→火→金→木 循环相克。过克伤身，反克为侮。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle
- **依据**：yi.l0.wuxing.ke
- **代码锚点**：`yishu_core/symbols.py:KE_CYCLE`

### 五行相生表  `yi.l1.wuxing.sheng_cycle`
- **定义**：木→火→土→金→水→木 循环相生。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.wuxing.sheng_cycle
- **依据**：yi.l0.wuxing.sheng
- **代码锚点**：`yishu_core/symbols.py:SHENG_CYCLE`


## L2 · 概念层（术语）

### 回头克  `yi.l2.concept.huitouke`
- **定义**：动爻所变出之爻，其五行反克本爻之五行（如酉金动变午火，火克金）。属《增删卜易》七化凶之一。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l2.concept.huitouke
- **派生**：yi.l3.rule.shi_hua_ke、yi.l3.rule.shi_hua_ke_wang
- **依据**：yi.l1.wuxing.ke_cycle
- **书证**：《增删卜易》凡用神原神动化回头克、化绝、化墓、化空、化鬼、化退神，皆为化凶
- **代码锚点**：`rules/predicates.py:HUA_XIONG`

### 冲解回头克  `yi.l2.concept.huitouke_chongjie`
- **定义**：回头克之凶，待冲去克神之年月日时而解（如午火克酉金，待子日冲午火）。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.branch.chong → yi.l2.concept.huitouke_chongjie
- **派生**：yi.l3.rule.shi_hua_ke_wang
- **依据**：yi.l1.branch.chong、yi.l2.concept.huitouke

### 世爻临月建/日建旺  `yi.l2.concept.shi_wang`
- **定义**：世爻五行与月建（或日辰）五行同气为旺。世旺则能胜任吉凶之任，凶来亦可待时而解。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.wuxing.sheng_cycle → yi.l2.concept.shi_wang
- **派生**：yi.l3.rule.shi_hua_ke_wang
- **依据**：yi.l1.wuxing.sheng_cycle、yi.l0.wuxing
- **代码锚点**：`rules/predicates.py:_month_state`

### 问类（分占域）  `yi.l2.concept.wenlei`
- **定义**：按问事分域：婚姻、求财、功名科举、官非词讼、疾病（久病/近病）、天气、失物、逃亡等 12 类。不同问类有不同取用与判法。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l2.concept.wenlei
- **派生**：yi.l3.rule.liuchong_bian_liuhe、yi.l3.rule.tianqi_zhan_yu、yi.l3.rule.tianqi_zhan_qing
- **依据**：yi.l0.bagua
- **代码锚点**：`data/rules/question_classes.json:classes`

### 用神（占断核心）  `yi.l2.concept.yongshen`
- **定义**：所占之事对应的六亲爻：占财看妻财、占官看官鬼、占文书看父母、占解忧看子孙、占兄弟同辈看兄弟。用神为一卦之主。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen
- **派生**：yi.l2.concept.yongshen_liuqin、yi.l2.concept.yuan_shen
- **依据**：yi.l1.najia、yi.l0.wuxing
- **代码锚点**：`data/rules/use_god_relations.json`

### 六亲取用规则  `yi.l2.concept.yongshen_liuqin`
- **定义**：按问类定用神：男家占女以财为用、女家占男以官为用、自占病以世爻为用、子占母孕以兄弟为用等（《增删卜易》17 条逐字规则）。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l2.concept.yongshen_liuqin
- **依据**：yi.l2.concept.yongshen、yi.l1.wuxing.ke_cycle
- **代码锚点**：`data/rules/use_god_relations.json:rules`

### 原神/忌神/仇神  `yi.l2.concept.yuan_shen`
- **定义**：生用神者为原神，克用神者为忌神，克原神者为仇神。原神有力则事易成，忌神动则事受阻。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l2.concept.yuan_shen
- **派生**：yi.l3.rule.yuan_shen_wu_li
- **依据**：yi.l2.concept.yongshen、yi.l0.wuxing.sheng


## L3 · 规则层（判法）

### 出现无情  `yi.l3.rule.chuxian_wuqing`
- **定义**：用神出现但与日月动爻无生克关系（无情），cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l3.rule.chuxian_wuqing
- **依据**：yi.l0.wuxing.sheng、yi.l1.wuxing.ke_cycle
- **代码锚点**：`rules/registry_v2.json:liuyao.chuxian_wuqing`

### 六冲变合（婚姻占吉断）  `yi.l3.rule.liuchong_bian_liuhe`
- **定义**：原卦六冲主散，变卦六合主聚，婚姻占散而复聚，竟以吉断。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.branch.chong → yi.l3.rule.liuchong_bian_liuhe
- **依据**：yi.l1.branch.chong、yi.l1.branch.he
- **书证**：《增删卜易》六冲变合，散而复聚，离而必合，此婚一定还成
- **代码锚点**：`rules/registry_v2.json:liuyao.liuchong_bian_liuhe`

### 求财凶爻持世  `yi.l3.rule.qiu_cai_xiong_chi_shi`
- **定义**：求财占凶爻持世，动则凶、静则平凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l3.rule.qiu_cai_xiong_chi_shi
- **依据**：yi.l1.wuxing.ke_cycle
- **代码锚点**：`rules/registry_v2.json:liuyao.qiu_cai_xiong_chi_shi`

### 世动化鬼（回头克格）  `yi.l3.rule.shi_hua_gui_huitouke`
- **定义**：世动化官鬼回头克世，cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l2.concept.huitouke → yi.l3.rule.shi_hua_gui_huitouke
- **依据**：yi.l2.concept.huitouke
- **代码锚点**：`rules/registry_v2.json:liuyao.shi_hua_gui.huitouke`

### 世动化鬼（提火格）  `yi.l3.rule.shi_hua_gui_tihuo`
- **定义**：世动化出官鬼（提火之局），cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l2.concept.huitouke → yi.l3.rule.shi_hua_gui_tihuo
- **依据**：yi.l2.concept.huitouke
- **代码锚点**：`rules/registry_v2.json:liuyao.shi_hua_gui.tihuo`

### 世动回头克（即时压凶）  `yi.l3.rule.shi_hua_ke`
- **定义**：世爻动而变回头克，即时 cap=凶，压 verdict 档。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l2.concept.huitouke → yi.l3.rule.shi_hua_ke
- **依据**：yi.l2.concept.huitouke
- **代码锚点**：`rules/registry_v2.json:liuyao.shi_hua_ke`

### 世临月建旺回头克（待时救应）  `yi.l3.rule.shi_hua_ke_wang`
- **定义**：世动回头克，但世临月建旺，cap=吉——回头克只延迟应期，不害其吉。由 apply_caps 第二遍救应抬吉。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.wuxing.sheng_cycle → yi.l2.concept.shi_wang → yi.l3.rule.shi_hua_ke_wang
- **依据**：yi.l2.concept.shi_wang、yi.l2.concept.huitouke_chongjie
- **书证**：《增删卜易》世临月建之官定得面见，被午火回头之克，须待子日冲去午火方得拜谒
- **代码锚点**：`rules/registry_v2.json:liuyao.shi_hua_ke_wang`

### 世动回头生逢月破  `yi.l3.rule.shi_huitou_sheng_yuepo`
- **定义**：世动本化回头生（吉），但所变之爻逢月破，生而无力，cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.branch.chong → yi.l3.rule.shi_huitou_sheng_yuepo
- **依据**：yi.l1.branch.chong、yi.l0.wuxing.sheng
- **代码锚点**：`rules/registry_v2.json:liuyao.shi_huitou_sheng_yuepo`

### 天气占晴（结构判）  `yi.l3.rule.tianqi_zhan_qing`
- **定义**：天气占晴之结构判，cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l3.rule.tianqi_zhan_qing
- **依据**：yi.l0.bagua
- **代码锚点**：`rules/registry_v2.json:liuyao.tianqi_zhan_qing`

### 天气占雨（结构判）  `yi.l3.rule.tianqi_zhan_yu`
- **定义**：天气占以父母/财爻动静定雨晴，cap=凶（主雨不成晴）。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l3.rule.tianqi_zhan_yu
- **依据**：yi.l0.bagua
- **代码锚点**：`rules/registry_v2.json:liuyao.tianqi_zhan_yu`

### 凶爻持世克财  `yi.l3.rule.xiong_chi_shi_ke_cai`
- **定义**：忌神/凶爻持世而克妻财，求财占 cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l3.rule.xiong_chi_shi_ke_cai
- **依据**：yi.l1.wuxing.ke_cycle
- **代码锚点**：`rules/registry_v2.json:liuyao.xiong_chi_shi_ke_cai`

### 用神化退神  `yi.l3.rule.yongshen_hua_tui`
- **定义**：用神动而化退神（气退减），cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l3.rule.yongshen_hua_tui
- **依据**：yi.l0.wuxing、yi.l2.concept.huitouke
- **代码锚点**：`rules/registry_v2.json:liuyao.yongshen_hua_tui`

### 元神无力  `yi.l3.rule.yuan_shen_wu_li`
- **定义**：原神（生用神者）休囚空破不动，无力生用，cap=平凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l3.rule.yuan_shen_wu_li
- **依据**：yi.l0.wuxing.sheng
- **代码锚点**：`rules/registry_v2.json:liuyao.yuan_shen_wu_li`


## L4 · 书证层（古籍断语）

### 六冲变合（书证）  `yi.l4.evidence.chong_bian_he`
- **定义**：卦逢六冲本主散，变卦六合则散而复聚。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.branch.chong → yi.l3.rule.liuchong_bian_liuhe → yi.l4.evidence.chong_bian_he
- **依据**：yi.l3.rule.liuchong_bian_liuhe
- **书证**：《增删卜易》L25835「六冲变合，散而复聚，离而必合，此婚一定还成」

### 出现无情（书证）  `yi.l4.evidence.chuxian_wuqing`
- **定义**：官鬼父母虽则出现，既不持世、又不生合世爻，与我无益。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l3.rule.chuxian_wuqing → yi.l4.evidence.chuxian_wuqing
- **依据**：yi.l3.rule.chuxian_wuqing
- **书证**：《增删卜易·仕宦》L2786「出现无情，难遂青云之志」

### 求财兄弟持世（书证）  `yi.l4.evidence.qiu_cai_xiong_shi`
- **定义**：兄弟是劫财之神，持世则财难入手。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l3.rule.qiu_cai_xiong_chi_shi → yi.l4.evidence.qiu_cai_xiong_shi
- **依据**：yi.l3.rule.qiu_cai_xiong_chi_shi
- **书证**：《增删卜易》L419「占求财妻财持世者必得，兄弟持世者难求」

### 变鬼（书证）  `yi.l4.evidence.shi_hua_gui`
- **定义**：世爻休囚受克而动变出官星，是名变鬼。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l2.concept.huitouke → yi.l3.rule.shi_hua_gui_huitouke → yi.l4.evidence.shi_hua_gui
- **依据**：yi.l3.rule.shi_hua_gui_huitouke
- **书证**：《增删卜易》L1643「化克化鬼，弟兄妻子休逢」

### 世旺回头克待时（书证）  `yi.l4.evidence.shi_hua_ke_wang`
- **定义**：世临月建之官，被回头克，待冲去克神之日方得见。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.wuxing.sheng_cycle → yi.l2.concept.shi_wang → yi.l3.rule.shi_hua_ke_wang → yi.l4.evidence.shi_hua_ke_wang
- **依据**：yi.l3.rule.shi_hua_ke_wang
- **书证**：《增删卜易·谒贵章》酉月丙寅日「世临月建之官定得面见，被午火回头之克，须待子日冲去午火方得拜谒」

### 兄弟持世克财（书证）  `yi.l4.evidence.xiong_chi_shi_ke_cai`
- **定义**：兄弟持世为耗财克妻之神。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l3.rule.xiong_chi_shi_ke_cai → yi.l4.evidence.xiong_chi_shi_ke_cai
- **依据**：yi.l3.rule.xiong_chi_shi_ke_cai
- **书证**：《增删卜易》L2613「兄爻持世财化退神者，亦同此意，非反目即生离」

### 元神无力（书证）  `yi.l4.evidence.yuan_shen_wu_li`
- **定义**：元神休囚静而不动，或空破、或动而化凶，不能生用神，虽有如无。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l3.rule.yuan_shen_wu_li → yi.l4.evidence.yuan_shen_wu_li
- **依据**：yi.l3.rule.yuan_shen_wu_li
- **书证**：《增删卜易》L551「元神虽现又有不能生用神者有六」
