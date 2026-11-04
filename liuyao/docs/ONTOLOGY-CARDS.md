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

### 伏藏（用神不上卦）  `yi.l2.concept.fushi`
- **定义**：用神不上卦时，伏于本宫某爻之下。伏藏有气则只利暂时，出现旺相则为久为远。《火珠林》「出现伏藏」章分九宫论伏藏关系（财伏鬼、官伏财、父伏子等）。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.fushi
- **依据**：yi.l1.najia、yi.l0.wuxing
- **书证**：《火珠林》出现旺相，为久为远；伏藏有气，只利暂时。
- **代码锚点**：`data/rules/domain/caiguan_fushi.json`

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
- **代码锚点**：`data/rules/domain/question_classes.json:classes`

### 用神（占断核心）  `yi.l2.concept.yongshen`
- **定义**：所占之事对应的六亲爻：占财看妻财、占官看官鬼、占文书看父母、占解忧看子孙、占兄弟同辈看兄弟。用神为一卦之主。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen
- **派生**：yi.l2.concept.yongshen_liuqin、yi.l2.concept.yuan_shen
- **依据**：yi.l1.najia、yi.l0.wuxing
- **代码锚点**：`data/rules/domain/use_god_relations.json`

### 六亲取用规则  `yi.l2.concept.yongshen_liuqin`
- **定义**：按问类定用神：男家占女以财为用、女家占男以官为用、自占病以世爻为用、子占母孕以兄弟为用等（《增删卜易》17 条逐字规则）。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l2.concept.yongshen_liuqin
- **依据**：yi.l2.concept.yongshen、yi.l1.wuxing.ke_cycle
- **代码锚点**：`data/rules/domain/use_god_relations.json:rules`

### 原神/忌神/仇神  `yi.l2.concept.yuan_shen`
- **定义**：生用神者为原神，克用神者为忌神，克原神者为仇神。原神有力则事易成，忌神动则事受阻。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l2.concept.yuan_shen
- **派生**：yi.l3.rule.yuan_shen_wu_li
- **依据**：yi.l2.concept.yongshen、yi.l0.wuxing.sheng


## L3 · 规则层（判法）

### 暗动  `yi.l3.rule.andong`
- **定义**：静爻逢日冲：旺相=暗动、衰=日破；中间档为工程映射，source-engine 分歧已登记未裁决。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.branch.chong → yi.l3.rule.andong
- **依据**：yi.l1.branch.chong、yi.l2.concept.shi_wang
- **代码锚点**：`rule_registry.json:liuyao.andong`

### 出现无情  `yi.l3.rule.chuxian_wuqing`
- **定义**：用神出现但与日月动爻无生克关系（无情），cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l3.rule.chuxian_wuqing
- **依据**：yi.l0.wuxing.sheng、yi.l1.wuxing.ke_cycle
- **代码锚点**：`rules/registry.json:liuyao.chuxian_wuqing`

### 独发/独静  `yi.l3.rule.dufa_dujing`
- **定义**：五爻不动一爻独动为独发，反之为独静；只标象给结构提示，不改吉凶主判、不进主分。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l3.rule.dufa_dujing
- **依据**：yi.l0.bagua、yi.l2.concept.yongshen
- **代码锚点**：`rule_registry.json:liuyao.dufa_dujing`

### 方位（避乱/延医）  `yi.l3.rule.fangwei`
- **定义**：只出候选方位与书据不作吉凶判词；吉方=生世之方∪子孙之方，按月令旺衰分档并列，不代书择一。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l3.rule.fangwei
- **依据**：yi.l0.bagua、yi.l2.concept.wenlei
- **代码锚点**：`rule_registry.json:liuyao.fangwei`

### 反吟/伏吟  `yi.l3.rule.fanyin_fuyin`
- **定义**：本卦逐位比变卦地支：反吟=六冲、伏吟=不变；卦级分内外卦，深层按五行旺衰综合评分，非统一扣减。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.branch.chong → yi.l3.rule.fanyin_fuyin
- **依据**：yi.l1.branch.chong、yi.l0.wuxing
- **代码锚点**：`rule_registry.json:liuyao.fanyin_fuyin`

### 伏藏/飞伏  `yi.l3.rule.fucang`
- **定义**：用神不现则本宫首卦寻伏神伏于飞神之下；得出判据六条，方向聚合对伏而不出给负向有界权重。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l3.rule.fucang
- **依据**：yi.l2.concept.yongshen、yi.l1.najia
- **代码锚点**：`rule_registry.json:liuyao.fucang`

### 卦身  `yi.l3.rule.guashen`
- **定义**：阴世从午月起、阳世从子月起，从初数至世方真；只输出供叙述层取象，不进主分，权重序无书据已登记。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l3.rule.guashen
- **依据**：yi.l1.najia、yi.l0.bagua
- **代码锚点**：`rule_registry.json:liuyao.guashen`

### 合绊/贪合忘生  `yi.l3.rule.heban`
- **定义**：动爻（含暗动）逢日/月合住=合绊：忌神合不成凶、原神合不济事，后逢冲开之日月吉凶俱成；梯度为工程映射。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l1.branch.he → yi.l3.rule.heban
- **依据**：yi.l1.branch.he、yi.l2.concept.yuan_shen
- **代码锚点**：`rule_registry.json:liuyao.heban`

### 乱动卦取用  `yi.l3.rule.huozhulin_luandong`
- **定义**：动爻数>2 出乱动卦标签及一看/二看结构象，只标象；取用口径裁定不另立，仍落 step2 优先序。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l3.rule.huozhulin_luandong
- **依据**：yi.l2.concept.yongshen、yi.l0.bagua
- **代码锚点**：`rule_registry.json:liuyao.huozhulin_luandong`

### 进退神  `yi.l3.rule.jintui_shen`
- **定义**：动爻化进（支序递进）势盛、化退势衰；回头生/克/合/泄单列，按月日旺衰量化，非统一加减。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.wuxing.sheng_cycle → yi.l3.rule.jintui_shen
- **依据**：yi.l1.wuxing.sheng_cycle、yi.l2.concept.huitouke
- **代码锚点**：`rule_registry.json:liuyao.jintui_shen`

### 绝处逢生  `yi.l3.rule.juechufengsheng`
- **定义**：用神/世爻绝死于日辰或动而化绝，得日月动爻生扶=临危有救；梯度分值为工程映射，凶中反吉只作结构提示。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.shier_changsheng → yi.l3.rule.juechufengsheng
- **依据**：yi.l1.shier_changsheng、yi.l2.concept.yuan_shen
- **代码锚点**：`rule_registry.json:liuyao.juechufengsheng`

### 六冲变合（婚姻占吉断）  `yi.l3.rule.liuchong_bian_liuhe`
- **定义**：原卦六冲主散，变卦六合主聚，婚姻占散而复聚，竟以吉断。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.branch.chong → yi.l3.rule.liuchong_bian_liuhe
- **依据**：yi.l1.branch.chong、yi.l1.branch.he
- **书证**：《增删卜易》六冲变合，散而复聚，离而必合，此婚一定还成
- **代码锚点**：`rules/registry.json:liuyao.liuchong_bian_liuhe`

### 六合/六冲  `yi.l3.rule.liuhe_liuchong`
- **定义**：卦内地支六合/六冲配对及卦级合冲、变卦合冲单列；合主聚、冲主散，断语外置。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l1.branch.he → yi.l3.rule.liuhe_liuchong
- **依据**：yi.l1.branch.he、yi.l1.branch.chong
- **代码锚点**：`rule_registry.json:liuyao.liuhe_liuchong`

### 六破  `yi.l3.rule.liupo`
- **定义**：爻支与日/月建落六破对（子酉/午卯/巳申/寅亥/辰丑/戌未）；纯破减分、合中带破减合力，世/用被破加重。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.branch.chong → yi.l3.rule.liupo
- **依据**：yi.l1.branch.chong、yi.l0.wuxing.ke
- **代码锚点**：`rule_registry.json:liuyao.liupo`

### 墓库（随官入墓）  `yi.l3.rule.muku`
- **定义**：官鬼入墓于世/用/同墓分场景，动而化墓加剧；伏神、合局入墓单列；吉凶综合判断，不单凭入墓定凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.shier_changsheng → yi.l3.rule.muku
- **依据**：yi.l1.shier_changsheng、yi.l2.concept.yongshen
- **代码锚点**：`rule_registry.json:liuyao.muku`

### 求财凶爻持世  `yi.l3.rule.qiu_cai_xiong_chi_shi`
- **定义**：求财占凶爻持世，动则凶、静则平凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l3.rule.qiu_cai_xiong_chi_shi
- **依据**：yi.l1.wuxing.ke_cycle
- **代码锚点**：`rules/registry.json:liuyao.qiu_cai_xiong_chi_shi`

### 三合局  `yi.l3.rule.sanhe`
- **定义**：申子辰/寅午戌/巳酉丑/亥卯未三支成局，completeness 分待用/成局；静爻可参与，局力受冲破条件约束。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.sanhe → yi.l3.rule.sanhe
- **依据**：yi.l1.sanhe、yi.l0.wuxing.sheng
- **代码锚点**：`rule_registry.json:liuyao.sanhe`

### 三会局  `yi.l3.rule.sanhui`
- **定义**：三支会一方局（寅卯辰会木等），或月日补一字；用神旺衰定加减，寒暖燥湿只取象不加减。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.sanhe → yi.l3.rule.sanhui
- **依据**：yi.l1.sanhe、yi.l0.wuxing
- **代码锚点**：`rule_registry.json:liuyao.sanhui`

### 三刑  `yi.l3.rule.sanxing`
- **定义**：无恩/恃势/无礼/自刑四类；卦内三字齐备为完整、月日补一字为催刑（力减半），变卦不参与本卦三刑。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.sanxing → yi.l3.rule.sanxing
- **依据**：yi.l1.sanxing、yi.l0.wuxing.ke
- **代码锚点**：`rule_registry.json:liuyao.sanxing`

### 身爻启用  `yi.l3.rule.shen_yao_activation`
- **定义**：世爻旬空或月破时身爻（据安卦身诀定宫位）参与用神取法；世不空不破则不启用，只标象不打分。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l3.rule.shen_yao_activation
- **依据**：yi.l2.concept.yongshen、yi.l1.najia
- **代码锚点**：`rule_registry.json:liuyao.shen_yao_activation`

### 世动化鬼（回头克格）  `yi.l3.rule.shi_hua_gui_huitouke`
- **定义**：世动化官鬼回头克世，cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l2.concept.huitouke → yi.l3.rule.shi_hua_gui_huitouke
- **依据**：yi.l2.concept.huitouke
- **代码锚点**：`rules/registry.json:liuyao.shi_hua_gui.huitouke`

### 世动化鬼（提火格）  `yi.l3.rule.shi_hua_gui_tihuo`
- **定义**：世动化出官鬼（提火之局），cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l2.concept.huitouke → yi.l3.rule.shi_hua_gui_tihuo
- **依据**：yi.l2.concept.huitouke
- **代码锚点**：`rules/registry.json:liuyao.shi_hua_gui.tihuo`

### 世动回头克（即时压凶）  `yi.l3.rule.shi_hua_ke`
- **定义**：世爻动而变回头克，即时 cap=凶，压 verdict 档。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l2.concept.huitouke → yi.l3.rule.shi_hua_ke
- **依据**：yi.l2.concept.huitouke
- **代码锚点**：`rules/registry.json:liuyao.shi_hua_ke`

### 世临月建旺回头克（待时救应）  `yi.l3.rule.shi_hua_ke_wang`
- **定义**：世动回头克，但世临月建旺，cap=吉——回头克只延迟应期，不害其吉。由 apply_caps 第二遍救应抬吉。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.wuxing.sheng_cycle → yi.l2.concept.shi_wang → yi.l3.rule.shi_hua_ke_wang
- **依据**：yi.l2.concept.shi_wang、yi.l2.concept.huitouke_chongjie
- **书证**：《增删卜易》世临月建之官定得面见，被午火回头之克，须待子日冲去午火方得拜谒
- **代码锚点**：`rules/registry.json:liuyao.shi_hua_ke_wang`

### 世动回头生逢月破  `yi.l3.rule.shi_huitou_sheng_yuepo`
- **定义**：世动本化回头生（吉），但所变之爻逢月破，生而无力，cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.branch.chong → yi.l3.rule.shi_huitou_sheng_yuepo
- **依据**：yi.l1.branch.chong、yi.l0.wuxing.sheng
- **代码锚点**：`rules/registry.json:liuyao.shi_huitou_sheng_yuepo`

### 十二长生  `yi.l3.rule.shierchangsheng`
- **定义**：各爻五行在日支十二长生表查位；只取生旺（长生/临官/帝旺）与死/墓/绝分档，余宫仅标注不进分。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l1.shier_changsheng → yi.l3.rule.shierchangsheng
- **依据**：yi.l1.shier_changsheng、yi.l0.wuxing.sheng
- **代码锚点**：`rule_registry.json:liuyao.shierchangsheng`

### 游魂/归魂  `yi.l3.rule.soul_hexagram`
- **定义**：游魂卦（各宫第七卦）主行无定、归魂卦（各宫第八卦）主有归；由卦之 generation（七/八世）自动判定。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l3.rule.soul_hexagram
- **依据**：yi.l0.bagua、yi.l1.najia
- **代码锚点**：`rule_registry.json:liuyao.soul_hexagram`

### 天气占晴（结构判）  `yi.l3.rule.tianqi_zhan_qing`
- **定义**：天气占晴之结构判，cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l3.rule.tianqi_zhan_qing
- **依据**：yi.l0.bagua
- **代码锚点**：`rules/registry.json:liuyao.tianqi_zhan_qing`

### 天气占雨（结构判）  `yi.l3.rule.tianqi_zhan_yu`
- **定义**：天气占以父母/财爻动静定雨晴，cap=凶（主雨不成晴）。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l3.rule.tianqi_zhan_yu
- **依据**：yi.l0.bagua
- **代码锚点**：`rules/registry.json:liuyao.tianqi_zhan_yu`

### 用神多现取舍  `yi.l3.rule.use_god_multi`
- **定义**：用神两现/多现时按取舍优先级选（舍闲爻取持世/临月日等书源序），无命中回落通用序并明示；三方取舍序分歧已登记不改实现。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l3.rule.use_god_multi
- **依据**：yi.l2.concept.yongshen、yi.l2.concept.yongshen_liuqin
- **代码锚点**：`rule_registry.json:liuyao.use_god_multi`

### 用神两现野鹤反法  `yi.l3.rule.wild_crane_reverse`
- **定义**：用神两现且一空/破对一不空/不破时标反法结构；只检测触发条件，不改主判选择、不进主分。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l3.rule.wild_crane_reverse
- **依据**：yi.l2.concept.yongshen、yi.l2.concept.yongshen_liuqin
- **代码锚点**：`rule_registry.json:liuyao.wild_crane_reverse`

### 泄用之神  `yi.l3.rule.xie_yong_zhi_shen`
- **定义**：动爻五行为用神所生（我生），原落闲神致净效应恒 0，补定价 -0.3 与既有泄气口径同量级。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l2.concept.yuan_shen → yi.l3.rule.xie_yong_zhi_shen
- **依据**：yi.l2.concept.yuan_shen、yi.l1.wuxing.sheng_cycle
- **代码锚点**：`rule_registry.json:liuyao.xie_yong_zhi_shen`

### 凶爻持世克财  `yi.l3.rule.xiong_chi_shi_ke_cai`
- **定义**：忌神/凶爻持世而克妻财，求财占 cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.wuxing.ke_cycle → yi.l3.rule.xiong_chi_shi_ke_cai
- **依据**：yi.l1.wuxing.ke_cycle
- **代码锚点**：`rules/registry.json:liuyao.xiong_chi_shi_ke_cai`

### 旬空（真空/假空）  `yi.l3.rule.xunkong_zhenjia`
- **定义**：真空=休囚无气+日克+无生扶；假空=旺相有扶，出空（值日/冲日）即应；两档之外不硬贴标签。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l3.rule.xunkong_zhenjia
- **依据**：yi.l1.najia、yi.l0.wuxing.sheng
- **代码锚点**：`rule_registry.json:liuyao.xunkong_zhenjia`

### 用神十八法（易冒）  `yi.l3.rule.yimao_shibafafa`
- **定义**：《易冒》类总章用神旺衰十八法结构分类标签候选源，目前只作登记，不参与主分、不作吉凶断语来源。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l3.rule.yimao_shibafafa
- **依据**：yi.l2.concept.yongshen、yi.l2.concept.wenlei
- **代码锚点**：`rule_registry.json:liuyao.yimao_shibafafa`

### 应期  `yi.l3.rule.yingqi_rules`
- **定义**：结构化候选应期有序给出（date+rule，顺序即名次）；年/月/日单位须对上才命中，回填判定口径唯一。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l3.rule.yingqi_rules
- **依据**：yi.l2.concept.yongshen、yi.l0.wuxing
- **代码锚点**：`rule_registry.json:liuyao.yingqi_rules`

### 用神化退神  `yi.l3.rule.yongshen_hua_tui`
- **定义**：用神动而化退神（气退减），cap=凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l3.rule.yongshen_hua_tui
- **依据**：yi.l0.wuxing、yi.l2.concept.huitouke
- **代码锚点**：`rules/registry.json:liuyao.yongshen_hua_tui`

### 忧解/忧疑  `yi.l3.rule.you_jie`
- **定义**：子孙持世/动=忧解，官鬼持世/动=忧疑；域限定（防患/功名武擢），只标象不改吉凶主判。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l3.rule.you_jie
- **依据**：yi.l2.concept.yongshen、yi.l0.bagua
- **代码锚点**：`rule_registry.json:liuyao.you_jie`

### 元神无力  `yi.l3.rule.yuan_shen_wu_li`
- **定义**：原神（生用神者）休囚空破不动，无力生用，cap=平凶。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.sheng → yi.l3.rule.yuan_shen_wu_li
- **依据**：yi.l0.wuxing.sheng
- **代码锚点**：`rules/registry.json:liuyao.yuan_shen_wu_li`

### 月破  `yi.l3.rule.yuepo`
- **定义**：爻支被月建冲为月破；动则能伤，出月/实破日/合日不破，不动又无日辰动爻生助者到底破。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.wuxing → yi.l0.wuxing.ke → yi.l1.branch.chong → yi.l3.rule.yuepo
- **依据**：yi.l1.branch.chong、yi.l2.concept.shi_wang
- **代码锚点**：`rule_registry.json:liuyao.yuepo`

### 助鬼伤身（易冒版）  `yi.l3.rule.zhu_gui_shang_shen_yimao`
- **定义**：成立三要件：世受官鬼克+官鬼长生于日+双修正不命中；用官占豁免，只标结构不改吉凶主判、不进主分。
- **向上推演**：yi.l0.taiji → yi.l0.liangyi → yi.l0.sixiang → yi.l0.bagua → yi.l1.najia → yi.l2.concept.yongshen → yi.l3.rule.zhu_gui_shang_shen_yimao
- **依据**：yi.l2.concept.yongshen、yi.l1.wuxing.ke_cycle
- **代码锚点**：`rule_registry.json:liuyao.zhu_gui_shang_shen_yimao`


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
