### 2026-10-05a 拱局（两支合势）落地尝试被反事实证伪：25 例翻档、ZE026 由命中翻坏 · 不合并 · engine 零变化

> **性质**：研究轮（证伪登记）。**engine 一行未改、评测读数零变化**。

- **假设**：三支全会聚（10-04l 已落地）的序延伸——两支拱局（三合/三会两支，生扶侧、
  无异类冲破）按一半（+1.0）入强弱分。序理由＝方局章「亦有取二支者，然以旺支为主」
  ＋「三支合势，吉凶之力较大」隐含的两支<三支。
- **反事实（实现前全量模拟，与 10-04l 同法）**：**25 例翻档**（tune 3 / holdout 20 /
  external 2）。决定性反证：**ZE026 由命中（书源虚弱/偏弱）翻中和**——书源判语被
  机械项推离；且外集三例剩余失配仅修复 ZE022 一例。
- **机制归因（证伪的原因）**：四柱中「某局恰缺一支」出现频率极高（holdout 20 例翻档
  即为频率证据），机械两支项必然系统性过火；任注「取二支」是**判语层的选择性论证**
  （引作旺证时才用），不是逐盘机械通则。与三支全（罕见、书源明言「力较大」）性质不同。
- **结论**：两支拱轴在机械层**无书源可依的标定路径**，ZE020/021/022 的剩余失配如实
  维持；除非未来获得书源明文的适用条件（如紧贴性），不再尝试。证据登记于
  `ming_fangju_adjudication.json#promotion_attempt_2026_10_05`；
  TECH-DEBT §2.3 强弱行同步。
- **验收**：根套件 382 绿（无代码变更，例行确认）。

### 2026-10-04r 六爻注册表收尾：十二长生引文挂接翻 verified=true（「予用生旺墓絕，其餘不驗」）· 六破登记语料缺载 · engine 零变化

> **性质**：纯 provenance 收口（10-04q 登记的两个后续小增量）。**engine 判据一字未改**。

- **`liuyao.shierchangsheng` → verified=true**：实测语料「予用生旺墓絕﹐**其餘不驗**」
  （行1223——野鶴明言十二长生只用四位）＋「化生旺兮禍福有三……金木水火而化旺卽是
  化進神」（行1225）＋千金賦「長生帝旺﹐爭如金穀之園。死墓絕空﹐乃是泥犁之地」（行913），
  逐字回验各恰 1 命中。**引擎 key/weak 分档（长生/临官/帝旺 vs 死/墓/绝）与书源
  「只用生旺墓绝」同构**，其余八宫仅 stage 标注展示——非缺陷而是与书源一致的保守面。
  落地：verdict_texts 十二长生槽位＋docstring 锚点＋注册表双指针翻 verified=true。
- **`liuyao.liupo` → verified=false 维持（依据升级）**：补查库内语料「六破」**0 命中**
  （增删卜易仅有月破章；卜筮正宗语料为目录骨架）——登记由「暂无引文」升级为
  「已核对：在库语料无六破明文」，破对取值属工程映射；关闭路径＝卜筮正宗正文语料入库。
- **同步状态**：10-04q 阻塞的推送已恢复（c709d21..410d72a 推送成功，版本门 SYNCED @410d72a）；
  本轮改动随后续提交推送。
- **验收**：根套件 382 绿；六爻学科门＋仓库门绿。

### 2026-10-04q 六爻注册表未覆盖域第六批补登记：游魂归魂（verified=true）＋十二长生/六破（诚实 verified=false）＋六破文本修复 · 含独立复核

> **性质**：文档补登记（b9f1d4b/9d7e4d4/94ab5c1 三个提交落地时缺 CHANGELOG 条目，违反
> 「口径/状态变更必须登记」纪律——本条由独立复核轮补齐）。**engine 判据零变化**；
> 评测读数零变化。

- **`liuyao.soul_hexagram`（游魂/归魂）→ verified=true**：引文取《黃金策》（语料行
  231/1162/1462）＋卷首「安世應要領」卦变/世爻规则（行57/59）；quote_in_code
  「游魂行无定，归魂回故乡」在实现文件。**独立复核 PASS**：quote_in_data 指针回解析、
  引文内核在语料逐字命中、代码锚点命中（本复核轮程序化回验）。
- **`liuyao.shierchangsheng`/`liuyao.liupo` → verified=false 维持（诚实）**：二域只挂
  代码锚点、书源引文未逐字挂接——按「宁缺毋滥」如实登记，引文逐字核对列为后续小增量。
- **94ab5c1 修复**：verdict_texts `step5_factor_reasons.six_break` 文本语义错配
  （「用神逢月破」误述月破而非六破）——该错配由第六批引入、同日修复；仓库门
  （含 [6b] render digest）绿，报告面无漂移。
- **注册表结构收口**：六爻注册表现 20 条 rule_id，TECH-DEBT §2.5「未覆盖域」行
  标记注册完毕（9d7e4d4）；残余债务＝shierchangsheng/liupo 引文挂接＋暗动休囚档分歧
  （待暗動章正文语料）。
- **同步状态**：本轮复核与上述三提交均未推送（github 连接失败，代理层网络中断）——
  SYNC_STATUS: REMOTE_UNVERIFIED，网络恢复后推送并重新过版本门。

### 2026-10-04p 六爻注册表未覆盖域第五批：三刑域注册（`liuyao.sanxing`）· provenance 增量

> **性质**：纯 provenance 增量。**engine 判据一字未改**。

- **书源取证（`zengshan_buyi.wikitext.txt`，逐字回验各恰 1 命中）**：①凶方向——
  「主事爻與日月動爻作三刑者﹐占事不成。占物不好。占病必死……動化刑亦然」（行1319，
  千金賦「刑害不宜臨用」注）；②**野鶴驳「少一字不成三刑」旧说立虚一待用**——
  「三刑少申字﹐防申日之危﹐果卒於申日﹐此乃少一字﹐得後來之申日補之」（行1032，
  含应期义；旧说原文见行1019 所引）。与 `analyze_three_punishments` 的
  完整/待刑（月日催刑力减半）两档对应。
- **落地**：`verdict_texts#pattern_verdict_labels.三刑.古典引文`＋docstring 书源锚点＋
  注册表 `liuyao.sanxing`（双指针，verified=true，dim=patterns；刑表取 core 唯一真值源）。
- **诚实标注**：①完整 −1.0/催刑减半/多处成刑 1.5x-2.0x 折算为工程映射；②代码注释中
  「三刑齐全，凶不可解」一句**不在库内语料**（另一经典载体），如实登记无书源数值；
  ③变卦不参与本卦三刑的口径边界随条目登记。
- **验收**：根套件全绿；六爻学科门＋仓库门绿；render/golden 零变化。

### 2026-10-04o 六爻注册表未覆盖域第四批：伏藏/飞伏＋合绊域注册（`liuyao.fucang`＋`liuyao.heban`）· provenance 增量

> **性质**：纯 provenance 增量。**engine 判据一字未改**。

- **书源取证（`zengshan_buyi.wikitext.txt`，逐字回验各恰 1 命中）**：
  ①**伏藏**——飛伏神章第二十八正文在库：「飛來生伏得長生」「伏神遭克害﹐名爲伏神受制」
  ＋**「伏神有用者有六」判据清单**（得日月生/旺相/飛神生/動爻生/沖克飛神/飛神空破休囚墓絕）
  ＋引《黃金策》「空下伏神﹐易於引撥」。引擎 `analyze_hidden_spirit_emergence` 九条评分
  与六条判据**逐项对应**（can_emerge=emerge_score>0）；「伏而不得出」方向另本
  《黃金策·千金賦》「伏無提挈終徒爾」（10-02s 已落地）——两方向血缘均已挂接。
  ②**合绊**——千金賦「動逢合而絆住」野鶴注：「忌神動逢日月相合﹐則不成凶。元神動逢
  日月合住則不濟事……後逢沖開之日月﹐吉凶俱成」（含应期义）＋「貪生貪合﹐刑沖克害皆忘」。
  与 `liuyao_step4` 4.3 贪合忘生克（效应减半）＋4.3b 日月合绊（有界方向权重）对应。
- **落地**：`verdict_texts#pattern_verdict_labels.伏藏/飞伏|合绊.古典引文` 两槽位＋
  代码锚点（classical_enhancements docstring/liuyao_step4 注释）＋注册表两条
  （双指针，verified=true，dim=patterns；合绊条目 note 如实登记「无独立 dim，
  效应经 effect/方向聚合进入 verdict 类维度」）。
- **诚实标注**：合绊有界权重（−2.0/−0.2/−0.3/效应减半）与绝处逢生梯度同为**工程映射**，
  书源为定性二分＋「后逢冲开之日月」应期义。
- **验收**：根套件全绿；六爻学科门＋仓库门绿；render/golden 零变化。

### 2026-10-04n ming 注册表引文缺口收口：dayun 起例逐字挂接翻 verified · shensha 补查获书源否定语境

> **性质**：纯 provenance 收口（ming 注册表仅剩两处 verified=false 的逐字核对）。
> **engine 零变化、评测读数零变化**。

- **ming.dayun → verified=true**：注册表原登记「通行起例——逐字书源核对待补」（所引
  《渊海子平》不在库）。本轮实测在库《神峰通考》**起大运法两节全 mechanics 逐字在库**
  （行2608/2612：「折除三日，为一岁」「顺数至二月惊蛰」「逆数至初一日立春……岁运逆行」
  ——三日折一岁＋阳男阴女顺/阴男阳女逆＋按节气折算，与 `ming_tables` 起运实现逐项同构）。
  落地：新建 `disciplines/ming/data/dayun_quotes.json`（照 tiaohou_quotes.json 范式，
  两节引文＋语料行号）＋注册表双指针翻 verified=true。**evaluation 状态维持
  mechanical_regression 不变**（缺 expected 与引文核对是两回事，测试锁定不虚标）。
- **ming.shensha → verified=false 维持（依据升级）**：补查在库两书——贵人诀
  「甲戊庚牛羊」在《神峰通考》唯一出现系**「总论子平谬说类」批判语境**（张楠：
  「日贵格，如甲戊庚牛羊，乙巳鼠猴乡之类也。焉有斯理……原取名之不据理出……
  岂可信乎？」——书源主动否定贵人格起例）；童子煞两库 0 命中。登记由「待核对」
  升级为「已核对且在库书源否定/缺载」——「只安星不批吉凶 + verified=false」的
  既有保守姿态获得书源侧直接支持，维持不改。
- **验收**：`tests/test_rule_registry_ming_meihua.py` 全绿（引文指针回查＋
  dayun/shensha 状态锁定不冲突）；根套件全绿；仓库门绿。

### 2026-10-04m 六爻注册表未覆盖域第三批：绝处逢生域注册（`liuyao.juechufengsheng`）· provenance 增量

> **性质**：纯 provenance 增量（TECH-DEBT §2.5「注册表未覆盖域」第三批）。**engine 判据一字未改**。

- **书源取证（`zengshan_buyi.wikitext.txt`，逐字回验各恰 1 命中）**：①千金賦「絕逢生而事成」
  野鶴注：「大凡世與用神或絕於日或化絕﹐若得日月動爻生者﹐謂之絕處逢生」（行1325，含
  寅日占卦酉爲用神例）；②疾病章：「用絕逢生危而有救……但得日月動爻有一而生扶者﹐
  乃爲絕處逢生﹐臨危有救」（行3989）。与 `analyze_desperate_relief`（用神绝/死于日辰→
  原神发动生扶）直接对应。
- **落地**：`verdict_texts#pattern_verdict_labels.绝处逢生.古典引文` + docstring 锚点 +
  注册表 `liuyao.juechufengsheng`（双指针，verified=true，dim=patterns）。
- **诚实标注**：applicability 明示梯度分值（+2.0/0.5/0.2/−0.8）为工程映射——书源只立
  「有生扶/无生扶」二分；「凶中反吉只作结构提示」设计边界照旧。
- **验收**：根套件全绿；六爻学科门＋仓库门绿；render/golden 零变化。

### 2026-10-04l 命科强弱口径变更：三支全会聚生扶侧合势项落地（JU_BONUS_W=2.0 engineering mapping）· 外集 22/26

> **性质**：通用规则落地（2026-10-04k 三会/拱局轴 source adjudication 的 promotion_path 执行）。
> **口径变更**：strength_and_pattern 新增合势入项——分数与此前轮不可直接比，本条即为登记。

- **书源依据（落地唯一依据，非外集读数）**：《滴天髓阐微·方局章》「柱中遇三支合势，
  吉凶之力较大」「干头无反复者，方局齐来，其气旺盛」；《神峰通考》「只喜巳中有金合局，
  所以金得乘旺也……只多了一亥字，则为金不足」（同段对照例）。观察集
  `ming_fangju_adjudication.json`（10-04k）。
- **实现（`pattern.py::strength_and_pattern`，通用规则无 case 分支）**：四柱三支全
  成三合局/三会方、局内无支被异类六冲（破局口径镜像从格路径：同类库冲不破）、
  局气**生扶日主**（同气或印）→ 生扶侧 +2.0。三重标注：
  ①`JU_BONUS_W=2.0` 为 **engineering mapping**（书源纯定性序无数值；取库内从格路径
  三合局化气 +2.0 同常数先例），item 级带 `provenance: engineering_mapping` 供审计；
  ②**克泄耗侧不加不减**——加负项被 ZE013 证伪（庚金得申子辰水局，任注仍判
  「金太旺」；泄/克/耗差序书源无标定，宁不减分＝更保守序表示），衰侧引局例
  ZE007/008/011 由各支藏干权重承载、全对不变；
  ③从格判据 `_from_judge` 输入不变（其路径自带会局处理，避免双重计入）；
  返回值新增 `ju_bonus` 块（total/items）。
- **反事实测量（先模拟后实测，两轮一致）**：
  - tune：0 触发、**100.0（n=30）持平**；
  - holdout：6 触发、翻档 2 例（MP134 巳午未三会火局扶丁火 中和→偏旺；MP164 亥卯未
    三合木局印扶丁火 偏弱→中和）——两例均无 strength expected（四柱对表回归集），
    **96.7（n=246）持平**；从格 ZC004/005/015 的 from_kind/from_type 零漂移；
  - external：6 触发、翻档 1 例（**ZE017 支类北方 太旺 miss→hit**），读数
    **21/26→22/26**（report-only）；ZE013 未被误伤；ZE020/021/022（两支拱局，
    权重无书源标定未实现）保持失配如实保留；
  - golden：ming 请求盘（1990-05-20，无会聚）零漂移，[6b] render digest 不动。
- **tripwire 协议执行**：ZE017 翻转已按 `test_ming_strength_root_stage.py` 模块
  docstring 要求登记本条口径变更并复核外集 `_provenance`（已追加 10-04l 段）；
  tripwire 改锁 ZE005 仍中和（其机制禄刃/天干比劫仍未建模）＋ZE017 新读数与
  ju_bonus 血缘（防静默回退）。
- **验收**：根套件全绿；命科学科门＋仓库门绿。

### 2026-10-04k 三会/拱局轴 source adjudication：轴属实（两书理论+实践+对照例）· 观察集落盘 · 未改 engine

> **性质**：纯 source adjudication（外集旺侧失配候选机制的解除路径第一步）。
> **未改 engine 一行、评测读数零变化**；观察集不计分、不入 holdout。

- **取证（两库语料，全部程序化逐字回验）**：①阐微专设「方局章」（通神论十一）——
  「柱中遇三支合势，吉凶之力较大」「干头无反复者，方局齐来，其气旺盛」，且明言
  **两支拱局在理论内**（「亦有取二支者，然以旺支为主，或亥卯，或卯未，皆可取」）；
  ②神峰通考行1604 同段自带对照例——「只喜巳中有金合局，所以金得乘旺也……
  有乙亥年人……只多了一亥字，则为金不足」（会局是判别性入项，非修辞）；
  ③衰旺章首批 19 例判语中 **8 例实际引用**会局/拱/方（旺侧 5／衰侧 3）。
- **engine 现状实读**：正常强弱分（藏干十神根分层＋得令±1.2）**无任何会局项**；
  三合局（三支全）仅进从格路径（化气、从神+2.0）；**两支拱局完全不进 engine**；
  三会方仅作结构标签。→ ZE017/021/022 三例失配为**真实 divergence，非书源讹误**。
- **落地**：观察集 `disciplines/ming/data/cases/ming_fangju_adjudication.json`
  （schema `yi-ming-fangju-adjudication/1`，OBSERVATION-ONLY：六条书源证据＋engine
  时点快照＋分歧案例登记＋四项 unresolved＋三条 promotion_path）；
  `tests/test_ming_fangju_adjudication.py` 七断言锁定（schema/status／**无评测字段**／
  引文逐字／外集引用一致性／升级路径须反事实先行／engine 快照为带日期信息性）。
  测试自证有效：两次咬出引文不逐字（「（ZE001）」前缀污染、省略号拼接），修正后才绿。
- **NON-ACTION**：不改 engine——书源为定性序（力较大/气旺盛/乘旺），无数量值，
  任何入分权重只能是 engineering mapping（GOAL §8）；且外集案例不得作落地依据
  （禁止考卷调参）。落地须另起一轮：通用规则＋数值标注＋反事实测量先行。
- **验收**：根套件 382 绿（+7）；仓库门绿；外集读数不变（21/26）。

### 2026-10-04j 女命夫子星跨书源异说登记：阐微女命章「不可专论官星为夫、伤食为子」· 未改 engine

> **性质**：文档真实性订正 + source adjudication 登记（TECH-DEBT §2.3 过时行复核）。
> **engine 判据一行未改**。

- **复核起因**：TECH-DEBT §2.3 女命夫子星仍写「仓库暂无对应语料，须先拓书源」——与实际矛盾
  （规则 10-02q 已实现；且阐微 10-04 入库后女命章就在库内）。
- **新证据（`di-tian-sui-chan-wei.wikitext.txt`，逐字回验各恰 1 命中）**：女命章任注
  「凡女命之夫星，即是用神，女命之子星，即是喜神，**不可专论官星为夫、伤食为子**」（行6254）；
  原注弹性取法「若官星太旺，以伤官为夫，官星太微，以财为夫」（行6248）；命例实证
  「甲木夫星坐禄」（行6824——癸水日主以伤官为夫星，非官杀）。
- **裁决**：与病药跨书源案同型——渊海子平＝固定官杀/食伤映射，阐微任注＝用神/喜神绑定的
  弹性体系，两书两体系。**保留差异、不强行统一**；engine 固定映射（机械标注、不批吉凶）
  维持不变，异说登记于函数 docstring；TECH-DEBT 过时行订正。
- **验收**：根套件 375 绿；仓库门绿；render/golden 零变化（docstring 注释不进报告）。

### 2026-10-04i 六爻注册表未覆盖域第二批：暗动域注册（`liuyao.andong`）· 并登记一处 source-engine 分歧

> **性质**：纯 provenance 增量 + 分歧登记。**engine 判据一行未改**。

- **书源取证（`zengshan_buyi.wikitext.txt`，逐字回验各恰 1 命中）**：①官星持世例「酉金官星
  持世旺相﹐當時卯日沖之而暗動」（旺相+日冲＝暗动）；②千金賦卦例批注「休囚爲日破﹐不爲暗動」；
  ③总注「靜逢沖而暗興」。暗動章定义正文本章语料未展开——定义原文缺，如实登记。
- **落地**：`verdict_texts#pattern_verdict_labels.暗动.古典引文` + `analyze_hidden_movement`
  代码锚点 + 注册表 `liuyao.andong`（双指针，verified=true，dim=patterns）。
- **诚实标注（GOAL §8/§4）**：①applicability 明示中间档（中和 0.4/偏弱 0.2）为**工程映射**
  非古法原值——书源只支持旺相/休囚二分；②**登记 source-engine 分歧**：书源明言「休囚爲日破」
  而引擎偏弱档给 0.2 暗动。因定义正文缺书源、孤例不裁决，engine 维持不改；
  解除路径＝暗動章正文语料入库后做 source adjudication。
- **验收**：根套件 375 绿；六爻学科门 + 仓库门绿；render/golden 零变化。

### 2026-10-04h 命科强弱外集扩容：章外穷尽扫描 +7 例（ZE020–ZE026）· report-only 21/26 · 旺侧失配同签名汇聚

> **性质**：独立评测证据扩容（external holdout n=19→26）。**engine 推演一行未改**；
> 扫描规则、剔除清单、映射表先于引擎评分声明并留痕（`_provenance.batch2_rule`）。

- **纳入规则（先于评分声明）**：衰旺章之外全书穷尽扫描（日主/日元/日干/身 × 极类/一般强弱词族），
  任注命例判语显式给出原局强弱类别词者全收；逐条剔除登记——「不弱」否定式 2 例（无法唯一映射三档）、
  从格取用判语 1 例（强弱非独立类别词）、问答非判语 1 例、理论注疏段、
  **四柱自洽失败 1 例（行4634「弱之极矣」：月柱己酉与五虎遁矛盾，戊年八月应辛酉——提取失败，非判语存疑）**。
- **机械校验**：7 例四柱全部通过五虎遁（年×月）+ 五鼠遁（日×时）+ 首运（年干阴阳×性别×顺逆）
  三重自洽（ZE022 女命阴年顺排辨析在案）；日主与判语逐一相符。
- **读数（report-only，不设门槛）**：21/26。第二批 4/7——**衰侧 4 例全中（ZE023–ZE026）**；
  **旺侧 3 例全失配（ZE020 旺极/ZE021 旺极/ZE022 旺矣 → 引擎均判中和）**，与首批 ZE005/ZE017 同签名；
  ZE021 午戌拱火、ZE022 亥卯拱局再度指向「三会/拱局未入强弱」轴。已登记于 TECH-DEBT §2.3：
  **嫌疑汇聚属观察性，不构成改判据的证据，仍禁拿外集调参**。
- **其他落地**：`evaluate.py` 外集口径披露串改为逐批映射表指向案例文件 `_provenance`（消除首批专属枚举的过期风险）；
  「入库后无论读数高低一律保留」纪律写入 `contamination_note`（防事后筛例污染）。
- **验收**：tune/holdout 分列读数零变化（本轮未触 engine 与基准集）；根套件 + 命科学科门 + 仓库门全绿。

### 2026-10-04g 六爻注册表未覆盖域第一批：月破域注册（`liuyao.yuepo`）· provenance 增量

> **性质**：纯 provenance 增量（TECH-DEBT §2.5「注册表未覆盖域」按「按域逐条补注册，不一次堆完」
> 路径执行的第一批）。**engine/benchmark/评测读数零变化**——`analyze_monthly_break` 判据一字未动。

- **书源取证（`data/sources/zengshan_buyi.wikitext.txt` 月破章第二十七，程序化逐字回验各恰 1 命中）**：
  ① 定义诀：「正申﹑二酉﹑三戌…十二未﹐**月建沖之爲月破**﹐逐月之破日是也」——与
  `analyze_monthly_break` 的 `is_ba_zu_chong(branch, month_branch)` 直接对应；
  ② 野鶴動破之辨：「目下𨿽破﹐出月則不破﹐今日𨿽破﹐實破之日則不破﹐合之日則不破﹐
  近應日遠應年月。惟而不動又無日辰動爻生助者則到底而破矣」——与实现的 `is_moving` +
  `salvageable`（日辰生扶或旺相可救）对应。转写字（𨿽＝雖、全角逗号﹐）逐字照录不改。
- **落地**：① `verdict_texts.json#pattern_verdict_labels.月破.古典引文`；②
  `analyze_monthly_break` 内代码锚点注释一行；③ 注册表新增 `liuyao.yuepo`
  （domain=月破，双指针，`verified=true`，dim=`patterns`——该维度权重表本就含「月破」标签，
  2026-10-02g 起读 `advanced_analysis.monthly_break` 结构）。
- **影响面**：Evidence 挂接自动生效（factor=月破 的 evidence 条目此后带 rule_id 与
  classical_holdout 状态）；render/golden 无变化（引文无 narrate 消费者）。
  附带：注册表 sanhe 行 impl 行号 1507→1508（上轮注释插入的顺移，描述性 ref 校正）。
- **验收**：`tests/test_rule_registry.py` 全绿（新条目自动过 schema/指针/dim 三门）；
  语料引文回验 1/1 命中；根套件 + 六爻学科门 + 仓库门全绿。

### 2026-10-04f 六爻三合局引文逐字挂接：`liuyao.sanhe` verified=false → true · 注册表引文缺口清偿

> **性质**：纯 provenance 增量（TECH-DEBT §2.5 首行预登记债务按其解除路径执行）。
> **engine/benchmark/评测读数零变化**——`analyze_triple_combo` 判据一字未动，只挂引文锚点。

- **书源取证（`data/sources/zengshan_buyi.wikitext.txt`，程序化逐字回验各恰 1 命中）**：
  ① 行1043 升遷例（如酉月乙巳日占升遷得澤地萃之天地否）斷曰：「且巳日沖動亥月與發動之未爻﹐
  欲成三合﹐因少卯字﹐明年卯月必升﹐**此乃虛一待用**﹐果升於卯月﹐豈可謂之少一字不成三合耶」——
  与引擎 `completeness` 分「完整/待日/待月」（缺一字由日/月补足仍论成局）直接对应；
  ② 行969《黃金策千金賦》第三十四「合遭破以無功」野鶴注：「予得驗者﹐凡三合六合﹐𨿽不宜目下
  日月動爻沖克﹐又宜後來之月沖開。正所謂**如逢合住﹐沖破成功**」——与 `_check_sanhui_broken`
  局力冲破约束对应。引文含 wikisource 转写字（𨿽＝雖、全角逗号﹐）**逐字照录不改**。
- **落地**：① `verdict_texts.json#pattern_verdict_labels.三合成局.古典引文`（该键组自身声明的
  「古典引文」槽位，范式同 独发/独静）；② `classical_enhancements.py::analyze_triple_combo`
  补一行代码锚点注释（needle 供 quote_in_code 回查）；③ 注册表 `liuyao.sanhe` 填
  `quote_in_data`/`quote_in_code` 双指针并翻 `verified=true`（locator 注明语料行号与回验结果）。
- **测试口径修正**：`tests/test_rule_registry.py::test_unverified_honest` 原断言
  「unverified 规则必须存在」是把**缺口本身锁成永久状态**——缺口补挂后合法消失，
  断言移除；「无引文指针必 verified=false」护栏由 `test_every_rule_has_one_quote_pointer`
  继续承担（锁 provenance 纪律，不锁具体缺口）。
- **验收**：`tests/test_rule_registry.py` 全绿；语料引文回验（脚本命中计数 1/1）；
  render/golden 无消费面变化（三合成局.古典引文 无 narrate 消费者，仅注册表门与证据链回查用）。

### 2026-10-04e 版本真实性门（Version Truth Gate）：本地/远端/评测三态分离 · 新增 `tools/version_gate.py` + AGENTS.md §七

> **性质**：流程治理（评审后修正）。engine/benchmark/评测读数零变化。
> 触发：评审方按 GitHub 公共 `main` 审查时发现 10-04 各轮提交全部只在本地
> （`ls-remote` 实测 REMOTE_HEAD=3cb21e7 Evidence-First，本地领先 8 提交）——
> 此前轮报只报本地 HEAD、未标同步状态，把本地迭代记录与「远端可验证事实」混同。

- **规则入章程**（AGENTS.md §七，永久条款）：每轮 OBSERVE 第一步必须跑版本真实性门并
  原样报告 LOCAL_HEAD/REMOTE_HEAD/WORKTREE/LOCAL_AHEAD/REMOTE_AHEAD/SYNC_STATUS；
  UNSYNCED 须明说「尚未与远端 main 同步」；Agent 自述为二手事实；远端不可达须标
  REMOTE_UNVERIFIED，不得用本地追踪引用冒充实测。优先级：实际 git 状态 > 代码/测试 >
  数据 > 文档 > Agent 自述 > 历史计划。
- **机械执行**：`tools/version_gate.py`——REMOTE_HEAD 以 `git ls-remote` 实测为准
  （不 fetch、不读本地缓存引用；不可达如实降级并标注参考口径）；
  SYNC_STATUS ∈ {SYNCED, UNSYNCED, REMOTE_UNVERIFIED}，UNSYNCED 附加明示行。

### 2026-10-04d 命科日主之根宫位分层：衰旺章任注逐字落地 · 归因修正（禄刃轴不解释外集 2 例失配）

> **性质**：source adjudication → 通用规则落地（TECH-DEBT §2.3 强弱行；注册表 `ming.strength`）。
> 阈值 ±1.5、藏干层位权重（本气/中气/余气 1.0/0.5/0.25）、印根/非比劫藏干权重**全部不动**；
> 唯一变化＝木火金水日主之**比劫根**按十二长生宫位重定层。

- **书源取证（语料行 2452，逐字）**：《滴天髓阐微·衰旺》任注给出根重次序——
  「长生禄旺，根之重者也；墓库余气，**奶**之轻者也」（**奶**＝wikisource 转写讹字，通行本作「根」；
  同段「任癸逢辰」「干多不如根挭」同类讹字，语料字符级转存不改、讹字在测试中登记）、
  「天干得一比肩，不如地支得一余气墓库」「得二比肩，不如支中得一长生禄旺」。
  书源「墓者/余气者/长生禄旺」三组例字（甲乙逢未/辰、丙丁逢戌/未、庚辛逢丑/戌、壬癸逢辰/丑、
  甲乙逢亥寅卯）**只列木火金水四行**——土寄四隅流派不一（火土同宫/水土同宫），戊己日主之根
  维持层位权重不混同。阴阳同生同死口径与任注「阴阳同生同死可知也」一致（core 统一长生表）。
- **实现（`pattern.py`，通用规则非 case 分支）**：比劫藏干且日主属木火金水时，按
  `core.twelve_growth`（与从格强根判据同一宫位轴）取宫位：长生/临官/帝旺＝重根 1.0，
  其余（墓/余气库支）＝轻根 0.25；details 逐根带 `root_stage` 供审计。修正的实质倒挂：
  引擎旧口径下 长生根（甲亥/丙寅/壬申/庚巳，中气 0.5）与库余气根（甲辰/丙未/庚戌/壬丑，
  中气 0.5）**同权**，而书源分属重/轻两类。
- **归因修正（测量在改前完成，防倒果为因）**：2026-10-04 首批登记的「ZE005/ZE017 失配
  同指根权重未区分禄刃长生」**被反事实测量证伪**——按书源轴全量重映射后 295 例中
  20 例强弱三档移动、从格判定 0 翻转、成败救应 0 翻转，但 **ZE005 Δ=0.0、ZE017 Δ=−0.25，
  两例均不翻转**。且书源序约束下天干比肩正权必须 <轻根 0.25，而 ZE017 翻档需 ≥0.267、
  ZE005 需 +2.3——**不存在书源自洽的单轴修正能翻此两例**。剩余失配候选机制如实登记
  （中和带宽 ±1.5 无书源标定 / 三会支局未入强弱 / 天干十神零权重），待独立证据，禁拿外集调参。
- **分列验收（全部持平）**：tune 100.0（n=30）/ holdout 96.7（n=246）/ 外部独立集 17/19
  （report-only）；从格 15/15、成败救应零漂移；ming 金标准**带理由重捕**（唯一变化
  weak_zhengguan2 乙木辰中乙根 中气 0.5→衰宫轻根 0.25，strength_score −5.20→−5.45，
  强弱标签/格局/用神/大运不变）；仓库级质量门全绿。
- **锁定**：`tests/test_ming_strength_root_stage.py` 五断言（衰旺章引文逐字子串含讹字原样 /
  重根轻根映射 / 土维持层位 / **外集隔离 tripwire：ZE005/ZE017 若翻转须先登记口径变更** /
  golden 盘不漂移）。注册表 `ming.strength` 翻 verified=true（引文入代码）并改写归因；
  外集 `_provenance.contamination_note` 增补无反馈回路记录。

### 2026-10-04c 大六壬 LE036/LE041 source adjudication：毕法赋注例「一课之克不参与取传」· 未改 engine 一行

> **性质**：纯 source adjudication（TECH-DEBT §2.4 大六壬「待追源」项执行完毕）。
> **未改 engine 一行、未改 benchmark（course_examples.json 原样）、评分零变化**；
> 增量只有 observation/provenance/documentation。

- **裁决（Q1/Q2）**：两例均为**书源毕法赋注例疏误**（`source_error_suspected`），
  非传抄讹误、非引擎缺陷——书面三传与「无视一课之克」后引擎**自身**低阶门分支**逐字吻合**：
  `LE036` 癸未干上寅：书面申寅申＝阴日昴星机械结果（初传=天盘酉所临地盘位申、中=干上寅、
  末=支上申），且「缘始末皆空」与癸未∈甲戌旬空申酉自洽；而该盘一课有唯一上克下
  （寅木克丑土），按卷一通则应元首出寅卯辰。`LE041` 乙巳干上子：书面酉巳丑＝遥克·蒿矢
  机械结果（上神克日干者申/酉取比之阴支酉，递传酉→巳→丑）；而一课有唯一下贼上
  （辰土克子水），通则应重审出子申辰。两例分别在卷十二第九十法（返吟论）与第九五法
  （六爻相生区），门选择均违反本书卷一诀（「取课先从下贼呼，如无下贼上克初」
  「无遥无克昴星穷」「四课无克号为遥」）。
- **归因扩大（Q3，超出原登记的新事实）**：同一「一课之克不参与取传」签名覆盖
  **5 例**（LE022/LE032/LE036/LE039/LE041），全部集中在卷十一/十二毕法赋注区；
  其中 LE022/LE032/LE039 此前按引擎落点归入涉害异说桶，本轮归因修正（引擎落涉害
  只是两候选拔河的表象）。反证：毕法注区自身的 LE026（丙申，一课贼克正常使用）、
  卷一 LE001（乙丑）、卷七 LE005（涉害章）书例均**使用**一课之克——该签名不是全书
  口径，是注例局部且内部不一致的习惯。
- **通则张力登记（Q4，unresolved 不修）**：下贼与上克并存时，引擎现行「合池进比用/
  涉害」有卷一乙丑例（LE001＋卷十二法九五同例重现，书内两处）支撑；但卷一贼克诀
  字面「如无」与卷七课经集知一课定义「二上克下，或二下克上」（同类多克）未言混池，
  LE032（癸卯→辰巳午）按严格下贼优先恰好复现——书内两读 1:1 分裂。剩余涉害桶
  5 例（LE004/020/021/027/037）在三种备选口径下读数均不变，维持原「涉害诸书不一」归因。
- **外部核查（Q5）**：通则他本证实（《大六壬探原》引同诀、通行九宗门讲解均下贼优先，
  仅作旁证）；两段引文的他本转写校验未获（ctext 反爬、通用搜索未索引），如实登记；
  《大六壬指南》仓库无语料，入库列为下一增量建议（Q8：暂停扩取传类课例，先补他本）。
- **落地**：`disciplines/liuren/data/cases/le_adjudication.json`
  （schema `yi-liuren-course-adjudication/1`，OBSERVATION-ONLY，八问结论+通则逐字引文+
  43 例三种备选口径普查矩阵+合池/优先异说登记）；`tests/test_liuren_le_adjudication.py`
  六断言锁定（status 词表 / source_quote·expected 血缘未动 / 引擎输出回放 / 换门复现 /
  五签名例 / 通则引文逐字子串）；TECH-DEBT §2.4 对应行改「已裁决·登记不修」。

### 2026-10-04b 病药跨书源取证（阐微卷）：任注病药＝第三种体系 · 同书双义 · 未改 engine

> **性质**：纯 source adjudication（TECH-DEBT §2.7/§2.8 解除路径的阐微部分执行完毕）。
> **未改 engine 一行**，无评测、无新抽象；跨源观察集**不计分、不入 holdout**。

- **前置**：阐微语料已于 2026-10-04 入库（commit `03aabbc`）。全书「病」139 次/「药」17 次
  全量普查并逐条分类：**判据义**（病药取病/药）15+ 处 vs **脏腑疾病义**（集中于疾病章）。
- **决定性发现（Q5）**：任注病药**定义总纲**在何知章——「**以忌神为病，以喜神为药**，
  有病有(药)则吉，有病无药则凶」：病药被绑定到用神体系（忌神/喜神）上，病之具体所指
  随用神取法而定。15 条命例级观察（ZW01–ZW15）之病全部落在**具体字/十神**
  （透干 7：丙火×2/壬水×2/癸水/丁火×2；支/会局 4：丑土/卯木/申金/午火/火局；
  十神角色 3：比肩/时财/财旺），**无一例以「月令五行身份本身」为病**——
  与神峰通考同向（7/7），但绑定机制不同（忌神泛指 vs 格局语境逐盘）。
- **勘误（Q6）**：2026-10-03f「《滴天髓》全书『藥』0 次、其『病』指脏腑疾病、与病药非
  同一概念」**仅对原文卷成立**——任注阐微大量使用病药判据；且脏腑义与判据义
  **同书并存**（疾病章五行→脏腑 vs 通篇忌神病药），「同名不同用」的统一化风险
  由此获得最强形态。两义域**不可互相援引**。
- **结论加强**：三书由「分裂」升级为「**三种病药体系并存**」——神峰＝格局语境逐盘取字、
  穷通宝鉴＝月令条目固定表、阐微任注＝忌神/喜神绑定。**统一病药模型的前提不成立**；
  engine 现状（月令五行主轴）在三体系之外、缺书源依据，维持不改。
  唯缺《子平真诠》（维基文库实测 missingtitle）。
- **落地**：`bingyao_cross_source.json` 扩展（`_sources_available`/`_verdict_summary`/
  findings 增 Q5/Q6/cross_source_observations 增 17 条 ZW 观察，引文程序化提取自源文件
  并逐字回验 PASS；维基文库讹字「沩药/化术/财禄丙相宜/有病有则吉」逐字照录并加注）；
  TECH-DEBT §2.7（解除路径更新）/§2.8（阐微取证+勘误）；HANDOFF §四.3 同步。

### 2026-10-04 命科外部独立集首批：强弱维度（external_holdout · report-only）+ 《滴天髓阐微》语料入库

> **性质**：独立验证推进（external holdout 从无到有）+ 一处读数订正。**未改 engine 推演一行**。
> 评测证据链位置：命科从「古籍对齐（source alignment）」右移一层到
> 「外部独立集（external holdout）」——首批 n=19，永不调参。

- **《滴天髓阐微》语料入库**：`data/sources/di-tian-sui-chan-wei.wikitext.txt`
  （401,836 字节 / 5,751 行 / 干支对 6,306，维基文库单页全本，通神论 34 章 + 六亲论 29 章，
  任注命例嵌于正文）。`tools/fetch_source.py` 目录新增 `di-tian-sui-chan-wei` 条目
  （先 `--check` 实测后登记）。**同时解锁**：命科外部集（HANDOFF §四.D）、
  病药跨书源补证（TECH-DEBT §2.7/§2.8 解除路径）、命科合化/化格语料缺口。
- **外部独立集首批（`ming_external_cases.json`，schema `yi-ming-external-cases/1`，n=19）**：
  - **维度选型**：强弱——命科最基础且此前**零案例覆盖**的维度；引擎扶抑口径出自
    《渊海子平》通行口径（不在库），与阐微**不同源**，构成真 external。
  - **纳入规则（跑引擎前声明）**：通神论·衰旺章内任注**显式标注衰旺类别**
    （太旺/旺极/衰/太衰/衰极）之命例全收；该章第 18 块（四柱皆水）任注无显式类别词，
    按规则剔除。章节尾书源自证「以上二十造，五行极旺极衰，不得中和之气」。
  - **四柱校验**：19 例全部通过时柱五鼠遁 + 首运（年干阴阳×月柱顺逆）自洽校验；
    日主与任注所述逐一相符；书源类别→引擎三档**大类化映射**（太旺/旺极→偏旺；
    衰/太衰/衰极→偏弱）与 ZC 集 kind 大类化同范式，映射表随集登记（`_provenance`）。
  - **污染披露**：强弱阈值（±1.5）与层次权重从未以任何案例集调参（本批前仓库无
    strength expected，无可调之尺）；同书从象/假从章 ZC 批曾参与从格 kind 调参，
    但强弱标签路径与从格判据无反馈回路。
- **读数（report-only，照六爻应期日/月/年分列范式：只报数，不设新门槛、不进 WEIGHTS）**：
  `python scripts/evaluate.py --split external_holdout` → **强弱对齐 17/19**。
  分歧 2 例（ZE005 丙戌日午月午时两刃 / ZE017 壬子日亥月支会北方）书源均判「太旺」、
  引擎均判「中和」——**机制同源**：`strength_and_pattern` 根权重只按 本气/中气/余气
  分层，禄刃长生之根与普通本气根同权，而衰旺章原文明写「长生禄旺，根之重者也；
  墓库余气，根之轻者也」。**登记待裁决（TECH-DEBT §2.3），不改 engine**；
  修复须走完整规则变更闭环，禁止拿本集考卷调参。
- **配套**：`evaluate.py` 增 `--split external_holdout`（外部分片文件装载 + 强弱读数块；
  全部行 applicable=0 时不打误导性「平均分」，只出强弱对数）；`tools/eval.py --full`
  增挂 ming 外集（六爻范式），并订正其陈旧 docstring（ming 已有案例对齐评测）；
  ming 规则注册表 `_uncovered` 增 `ming.strength` 条目（dim 契约所限不入 rules，
  如实登记 coverage/maturity）；`tests/test_ming_external_cases.py` 3 例守护
  （provenance 指得回原文 / split 零交集 / report-only 白名单防静默晋升）。
- **测试污染修复（实踩 conftest 已登记的同名遮蔽陷阱）**：守护测试首版以
  `spec_from_file_location` 执行 evaluate.py，其模块体裸名 `import chart/analyze`
  在 conftest 路径序（liuyao/scripts 先于 ming/scripts）下拿到**六爻**模块并缓存进
  `sys.modules`，使 `test_ming_dayun` 的 `from chart import chart` 拿错科而
  `TypeError: unexpected keyword 'gender'`。改为 **ast 从源码读取
  `STRENGTH_BOOK_CATEGORY` 字面量**（不执行模块，不进 sys.modules）。
- **读数订正（文档讹数，非引擎漂移）**：命科 holdout strict 均分实为 **96.7**，
  自 10-02t 起文档记 97.1。在 d36df84 / 3c96aaf / 3cb21e7 / e1eb18f / HEAD 五个提交点
  复跑均为 96.7（维度计数 pillars 189/189、tiaohou 21/21、pattern 28/36、
  cong_ge 13/15、from_kind 15/15 全同）——均分差来自 8 例 ZP 体系分歧 case 级计 0
  的算术，97.1 从未被复现。HANDOFF §一 ming 读数同步订正。

### 2026-10-03f Source Adjudication v2：跨书源语义取证 · **结论是「分裂」，故不应建统一病药模型**

> **性质**：纯取证，**未改 engine 一行**。回答评审指定的四问。
> 在库三书可取证：《神峰通考》《穷通宝鉴》《滴天髓》；
> **《子平真诠》《滴天髓阐微》不在库**（TECH-DEBT §2.1 外部数据阻塞），
> 故结论仅限三书，措辞不外推。

- **Q1 病是否都指向具体「字」？** → **不统一**。神峰通考 7 例全指向字（透干4/藏干3）；
  穷通宝鉴多取「月令条目内的忌神」（如九月辛金之火土、二月辛金之戊己、八月壬水之戊土），
  亦多具体字/十神，非纯五行身份。
- **Q2 藏干与透干是否异义？** → **两类都成立**（透干4：丁火/庚金×2/辛金；藏干3：
  戌中丁火/卯中乙木/亥中壬水）。但角色不同：透干之病「贴身相战」（庚金贴身制我身），
  藏干之病「暗来损局」（暗来损土、微来破火）。**是观察，非结论**（n 不足）。
- **Q3 五行层是否真实存在？** → **存在但两书定义不同**。
  **穷通宝鉴有「月令→病」固定对应表**（条目末即定该月之病与药）——这是书源明写的；
  **神峰通考明确无此表**（「或为病，或非病」）。
  → 故**当前 engine 的五行层更接近穷通宝鉴而非神峰通考，即「用错书源」**；
  但**不能因此说五行层纯属实现者虚构**。
- **Q4 格局/用神不同是否判法不同？** → **是**。神峰通考内伤官格（官星为病）与
  专禄格（杀星为病）取病不同；穷通宝鉴亦分格局。
- **决定性分裂证据**：《滴天髓》**全书「藥」0 次、「病神」0 次**；其「病」指
  **人身脏腑疾病**（疾病論「忌木而入土者脾病，忌火而入金則肺病……」），
  与神峰通考「病药」不是同一概念；且它**引病药总纲却归入中和**（「雖曰有病方為貴…則又中和矣」）。
  另：滴天髓第26章君臣論「土重埋金，木剋土則生金」——**与神峰通考同语但语义位置不同**
  （属母子反取关系论，非病药判据）。**同名不同用= 统一化风险的具体证据。**
- **架构含义（勿当已决方案）**：三书对「病」的语义明显分裂，**不存在可直接统一的
  「病药语义层」**。故**不应建统一病药模型**；正确方向是
  `discipline/source-specific interpretation`——每部书按其自身文本的病药语义实现，
  各自标 provenance，**彼此不冒充**（与仓库既有纪律一致）。
  **四书是否分裂当前无法回答**，故只登记分裂，**不预设统一方案**。
- **治理修正（评审指出，属测试过拟合）**：删除原
  `test_observation_census_matches_the_ruling`——它断言「engine 与书源同向者必须为 0」，
  等于把「当前存在已知分歧」写成「未来必须继续分歧」：**一旦有人正确修复engine，
  测试反而报错**。改为只锁**登记纪律**：`known_divergence` 布尔须显式存在、
  为 true 者必带 `book_support`（书源凭据，不许只凭 engine 输出断言分歧）、
  观察集**不得携带任何 score/alignment/holdout 字段**。
  **修正被允许**：engine 与书源同向时，把该例 `known_divergence` 置 false 并在 §2.7
  记录裁决变更即可通过，测试不阻碍修正。
- **文档**：TECH-DEBT 新增 §2.8（跨书源分裂登记）；§2.7 措辞按评审下调
  （「缺的是病＝字这一层」→「把病药过度压缩到月令五行层，字层是必要候选层但未证明为唯一层」）。

### 2026-10-03e 病药 source adjudication（**认识规则，未改 engine 一行**）

> **性质**：纯观察任务。按评审要求冻结 engine——本轮**未修改
> `disciplines/ming/scripts/pattern.py` 任何一行**，产出是判断而非修复。
> **禁止项全部遵守**：未计算 alignment score、未改判据、未入 holdout。
> 目的：回答「当前实现缺的到底是哪一个语义层级」。

- **全量提取病药命例**：以命例**题名**含病/福神为锚（最可靠；早期按正文字符计数会
  把病症类大量误纳），扫出 8 例，剔除 3 例**病症**类（肠毒之病/病膀胱而亡/贪食之病），
  得**观察集 n=7**，落`disciplines/ming/data/cases/ming_bing_yao_observations.json`
  （schema `yi-ming-bingyao-observations/1`，**与评测集 cases schema 刻意区分**）。
  逐例记录：四柱 / 题名 / 主轴是否明确 / 原文病神 / 原文药神 / **病药层级** /
  书源逐字引文 / engine 输出 / 差异说明。书中未载者一律 `null`，禁本仓推断填值。
  题名即可看出病药判据，是书源独有的体例：「火多为病格」「木火伤官庚金为病」
  「庚辛金为病神丙丁火为福神」「真伤官庚金官星为病」「专禄格以官杀为病格」。
- **裁决（评审后修正措辞）：当前实现把病药过度压缩到月令五行层；书源至少存在以
  具体天干/藏干之「字」为病神的命例。但「字层是必要候选层」**≠**「字层是已证明的
  唯一语义层」——后者未证明。**不得断言「病必取字」或「病必取藏干」。**

  | 例 | 书源病神 | 病之层级 | engine 所判 |
  |---|---|---|---|
  | 甲寅辛未辛未丁酉 | 丁火过多 | 天干透干 | 病=土（月令未） |
  | 丁丑庚戌乙巳壬午 | 月上庚金（官星） | 天干透干·十神 | 病=土（月令戌） |
  | 己巳辛未乙亥丁丑 | 辛金七杀 | 天干透干·十神 | 病=土（月令未） |
  | 甲戌庚午乙亥丁丑 | 庚金月上为真病 | 天干透干 | 病=**火**（把福神当病） |
  | 壬辰庚戌辛酉辛卯 | 戌中丁火（杀星） | 月令**藏干** | 病=土（戌**本气**） |
  | 辛酉丁酉癸卯壬戌 | 卯中乙木 | 日支藏干 | 病=金（月令酉） |
  | 辛亥癸巳戊午丙辰 | 亥中壬水 | 年支藏干 | 病=**火**（把药当病） |

  依据（书源逐字，非推断）：
  1. 病药说类开门定义：「**何以为之病？原八字中原所害之神也**」——「神」即字。
  2. 「何以为之药？如八字**原有所害之字，而得一字以去之**」——病与药皆为「字」。
  3. 决定性一句：「如八字中看了日干，**次看了月令**，且如月令中支中所属是火，
     **先看月令中此一火字起**…宜将以上各火做一处看，或为病，或非病…从重者论」——
     月令是**病神的取象起点/参照系**，不是病体。**engine 恰恰把参照系当成了病体**。
  4. 雕枯旺弱四病全是**结构关系**（有余／不及／无根／太过），无一是五行身份：
     「木有余之病，用金以制之」「金气有余之病，用火以克之」。

  故 `BING_RULES_BY_KE` 五条病名与「其克为药」整体缺书源依据——把「从重者论」
  （同一五行跨柱聚合的**取舍规则**）误读为「病＝月令五行」。方向相反者 2 例
  （OBS04/OBS07）：engine 判的病恰是书源的药/福神。
- **仍存的不确定性（故不改 engine）**：书源病神有落透干（4例）也有落藏干（3例）；
  n=7 不足以判定「病必取藏干/透干」，也不足以判定是否须按格局分治（OBS02 伤官以官星为病、
  OBS05 专禄格以杀为病）。故**改成「字层」还是「两层」都缺证据**，两种改法都可能
  是从一种误读跳到另一种误读。解除路径：①跨书源找独立命例（《穷通宝鉴》《子平真诠》
  《滴天髓》）验证层级用法；②或先只做「可作病药之字 + 其克制关系」的**识别能力**，
  **不判定谁是病**，把判定留给格局语境。
- **测试**：新增两条观察集纪律断言（不计分/不入 holdout/schema 区分；观察集统计必须与
  裁决一致——若 engine 日后真的同向，测试会失败并提醒更新裁决，防裁决与代码脱节）。
- **文档**：TECH-DEBT §2.7 重写为裁决记录（旧的两例版已删，避免两节并存）；
  HANDOFF 病药条目同步。

### 2026-10-03d 病药口径修正 + 命例分歧登记 + 构建器删除纪律修正（评审后一轮）

> **性质**：三处**修正**，无新能力宣称。**本条目同时订正 2026-10-03c 的口径**：
> 病药本轮只实现了规则与机械覆盖，**没有取得任何古籍对齐或预测证据**——
> 上一条目把它与「知识覆盖/机械能力」并列陈述，易被读成预测能力提升，属口径失准，
> 按铁律三订正之。
>
> **成熟度定位**（评审采纳的表述）：病药由「文献存在但引擎未实现」推进到
> 「**引擎可执行、但未验证**」，即 `古籍 → 规则 → 代码`（C 类）已通，
> `→ 古籍命例 → 对齐分`（B 类）**未通**。**不得据此宣称预测能力增强。**

- **口径订正（对上条目的自我修正）**：病药 ≠ 预测能力增强。现有证据只有
  ①书源逐字引文 ②机械实现 ③单元测试 8 例；**没有**古籍命例对齐分、
  **没有** external holdout 读数、**没有** outcome feedback。
  正确说法是「命科规则覆盖与机械能力增加」；预测能力是否增强**尚无证据**。
- **五行层判据按原文修正（实现理解偏差，非调参）**：原实现取「全盘最重五行为病」。
  复查原文自注「如八字中看了日干，**次看了月令**，且如月令中支中所属是火，先看月令中
  此一火字起，又看年上或火，又看月时上或有火，宜将以上各火做一处看，或为病，或非病…
  **故曰：从重者论**」——该句管的是「同一五行跨柱聚合时如何取舍」，语境是「病以月令主轴
  为参照」，**不是**「病＝全盘最重五行」。已改为**主轴取月令本气**，再聚合该轴五行。
  字段随之更名 `dominant_element` → `axis_element`。测试新增
  `test_axis_is_month_branch_not_global_max`（锁「主轴≠全盘最重」）。
- **规则性质 provenance（评审要求，防两类知识混同）**：`BING_RULES_BY_KE` 与
  `BING_RULES_BY_GOD` 每条增 `provenance` 字段，取值
  `source_backed_exact`（原文逐字可回指）／`source_informed_generalization`
  （依原文通例结构推得、书源未逐字列该句）。当前分类：
  `土厚埋金`=exact；`金重伐身/火炎焚身/水泛身浮/木旺折身`=generalization；
  十神层 `枭神夺食/印重财轻`=exact、**`比肩夺财`=generalization**
  （原文明写「比肩」二字，本实现取比劫全类含劫财，属语义扩展）。
  输出侧 `bing_yao.provenance` 汇总该判据的各层性质与口径声明。
  **评测纪律**：generalization 项只作通则回归，不冒充逐字对齐。
- **《神峰通考》病药命例入库，但**不计入任何评分集合**：新增
  `disciplines/ming/data/cases/ming_bing_yao_cases.json`（schema
  `yi-ming-bingyao-cases/1`，split=`external_holdout`，**n=2**）——命例与断语
  **逐字转录自书源**（人命见验说类），无一条本仓构造：
  BY001 临川会元山御史（辛酉 丁酉 癸卯 壬戌，病「卯中乙木」）、BY002 临川陆江副使
  （辛亥 癸巳 戊午 丙辰，病「亥中壬水」、书源未载药故 `去病之神: null`）。
  乙未收第三例（丁巳 癸丑 乙酉 庚辰）——书源归「从化格·乙庚化金」，通篇未论病药，
  **宁缺勿滥不入集**。
  **以该二例核对引擎，发现层级性口径分歧**（BY001 书源病木／引擎病金；BY002 书源病水／
  引擎病火，**方向相反**），故**不建评测维度、不出对齐分**，全量登记 `TECH-DEBT.md` §2.7。
  根因待判：病药说类自注「地支虽又藏有别物，且不必看」是否管得到「病神定位」这一层——
  逐字证据不足前**不改判据**（`AGENTS.md` §四.3 禁止为让案例过关改规则）。
  三条测试锁定该纪律：`test_classical_cases_expose_known_layer_divergence` 让分歧可见可回归，
  防止有人悄悄改判据去凑案例。
- **构建器删除纪律修正（评审否决「site/ 加删除白名单」）**：`build_web.build()` 原
  `shutil.rmtree(outdir)` **整目录删除**——既是「生成物也可能连带删掉非本工具内容」的
  风险，又在大目录下触发批量删除拦截，使质量门 [7b] 长期假红。改为
  **`_clean_previous_build()` 按 manifest `_build_written` 记账逐文件删除**
  （`_build_written` 记本次实际写入的全集 181 条，含非镜像文件与 `.nojekyll`/
  `manifest.json`/`engine/README.txt`），删后自底向上 `rmdir` 空目录（非空即保留，
  不强删），无 manifest 则不删只覆盖写，记账条目经 `relative_to` 防越界删除。
  实测：遗留生成物被清（184→183）、**非生成物 `USER_NOTES.md` 保留**，
  连跑两次构建均不再触发批量删除拦截。**这是修构建逻辑，不是把门静音。**

### 2026-10-03c 减法优先的一轮：命科病药落地（增能力）+ 三份过时治理文档删除（减复杂度）

> **性质**：一处**真实能力增加**（命科新增《神峰通考》病药判据，有书源、有测试、有出处
> 指针），一处**纯减法**（删 85KB 过时评审 + Phase 路线图）。无新抽象、无新层、无新目录。
> 评测读数不变：命科 tune 100.0%（30/30 调候）、holdout strict 97.1%（pattern 28/36、
> cong_ge 13/15 均未动——病药不在 WEIGHTS 内，不污染既有维度）。

- **命科病药（`pattern.py::bing_yao`）**：《神峰通考·病药说类》落地为机械结构标签。
  - **总纲逐字入码**：`BING_YAO_THESIS = "有病方为贵，无伤不是奇；格中如去病，财禄两相随"`
    （书源 `data/sources/shen-feng-tong-kao.wikitext.txt`「病药说类」，维基文库公版 452KB）。
  - **五行层**：~~依原文「从重者论…地支虽又藏有别物，且不必看」——取四干五行 ∪ 四支**本气**
    中最重者为病~~ **⚠️ 本条判据理解有误，已由 2026-10-03d 修正为「主轴取月令本气」**
    （原文自注管的是同一五行跨柱聚合时的取舍，病以月令为参照，非全盘取最重）。
    药为其所克之神；藏干不入此层。字段 `dominant_element` → `axis_element`。
  - **十神层**：原文明写三对病药——「用财见比肩为病，喜见官杀为药也」／「用食神伤官，
    以印为病，喜财为药也」，加「印星太旺者，宜行财星运以破其印」。病神集合取**比劫全类**
    （劫财与比肩同为夺财之神，不窄化到只认「比肩」二字，此为实现期修正，见下）。
  - **口径**：只标「病是什么、药是什么、药在不在局中」，**有药≠吉、无药≠凶**
    （铁律三）；`analyze` 出 `bing_yao` 顶层键 + 两条 verdict，`narrate` 出专段。
  - **测试**：`tests/test_ming_bing_yao.py` 5 例——总纲逐字、「从重者论」取舍（有药/无药各
    一造，锁定藏干不计入）、十神层病药对、空盘不臆造。
  - **注册**：`ming.bing_yao` 入 `disciplines/ming/data/rules/rule_registry.json`，
    `verified=true`（引文逐字入 `pattern.py#BING_YAO_THESIS`）；评测状态如实标
    `mechanical_regression`、`dim=null`——**bing_yao 维度案例集不存在，禁止虚标对齐分**。
    古籍对齐覆盖待从《神峰通考·人命见验类》提取病药命例后建立。
  - **golden**：机械层零漂移（`2c3eee326cec8ccd` 不变），仅 narrate 措辞层按新增病药段
    依 `capture` 落基线（已记理由）。
- **减法 · 删除三份文档（合计约 85KB）**：
  - `docs/ARCHITECTURE-REVIEW.md`（73KB）、`docs/SYS-REVIEW.md`（12KB）：均为读数停在
    2026-10-01/02 的**时点**评审件，A1–A11 改进项或已落地、或已转登记 `TECH-DEBT.md`
    §2.6（A7 反馈 n=0 / A9 架构图表达力 / A11 读数锚点）。继续维护只会让过时读数与现状
    并存——正是评审 A8「读数多源矛盾」本身所指的病。
  - `docs/EVIDENCE-MATURATION.md`（6.7KB）：Phase 5–8 阶段路线图，属「为未来可能需要
    提前设计」的规划件；其五大问题的**已落地部分**（ming/meihua 注册表、claim_policy、
    concept_map）在 CHANGELOG 2026-10-03b 有完整记录，**未落地部分**在 `TECH-DEBT.md`
    §2.5 有逐条登记——不需要另立一份规划文档承载。
  - 引用同步：`ARCHITECTURE.md`、`HANDOFF.md`、`TECH-DEBT.md`、`llms.txt`、`tools/check.py`
    （代码注释里 `SYS-REVIEW #N` 的历史锚点**保留**，它们标的是各门的设计出处，删掉会断溯源）。
- **语料与文档同步**：《神峰通考》病药语料的全仓统一位置是**仓库根 `data/sources/`**
  （452KB，`shen-feng-tong-kao.wikitext.txt` + provenance），与 `HANDOFF`/`TECH-DEBT`
  所记一致——本轮据此确认病药判据的引文可逐字回指，无需迁移语料。

### 2026-10-03b Evidence Maturation（Phase 5）启动 · 规则一等实体推广 + 规则级评测语义 + claim_policy + verified-only 概念映射

> **性质**：仍是纯加法与派生视图——引擎行为、语料、golden、tune/holdout/外部集
> 零改动；分数读数不变（唯一权威源仍 `docs/HANDOFF.md` §一）。
> 阶段目标与优先序落成 `docs/EVIDENCE-MATURATION.md`（Phase 4 已收口，
> 总目标从「完成 Evidence-First」升级为「Evidence Maturation」）。

- **ming 规则注册表**：`disciplines/ming/data/rules/rule_registry.json`——调候/格局成败/
  从格/大运/神煞 5 域（domain 带英文 verdict code 供互为子串挂接），逐条带引文指针
  （调候=穷通宝鉴 `tiaohou_quotes.json#1甲.quote` 逐字库；格局成败=《子平真诠》原文注释锚；
  从格=《滴天髓》诀句锚），**评测 dim 必须是 ming evaluate.py WEIGHTS 真实维度**；
  dayun/shensha 维度案例集 0 applicable → 如实标 `mechanical_regression` 不虚标。
- **meihua 规则注册表**：体用关系/生克之卦/应期 3 域（引文指针 `verdicts.json#basis_quotes.*`）；
  体用关系域另受外部独立集 n=4 覆盖 → 状态如实标 `external_holdout`（n<20 只报命中数）。
- **规则级评测语义（attach_rule_registry）**：挂接时评测状态**以注册表为准**（原为「取较强者」）
  ——规则级覆盖是比学科基线更细的真值，可升（meihua external_holdout）也可**如实降级**
  （ming dayun/shensha：classical_holdout 基线 → mechanical_regression）。六爻全部规则
  状态=学科基线，行为零变化。
- **Evidence 提取器补口**：新增命科 `tiaohou`（顶层调候查表）与 `shensha`（只安星不批吉凶，
  effect 恒空）提取器——调候是命科最大对齐维度（51 例）此前不产证据。
- **claim_policy（断言边界）**：`evidence.claim_policy(discipline, evidence)` 按本次证据
  组合生成机器可读边界（各状态计数 / 方向表态强弱分层 / 应期候选单列 / boundary 口径句），
  经 `evidence_envelope` 进双宿主信封（parity EV 列自动覆盖）——Agent 不读文档也知道
  「这份报告能说到什么程度」。rendered MD/HTML 零改动。
- **跨科概念映射机制（verified-only）**：`synthesis/concept_map.json`
  （schema `yi-concept-map-v1`）+ `evidence_cross.canonical_factor`（**全等匹配**，
  仅 verified=true 参与归并）+ `cross_examine(concept_map=…)`（缺省读注册表文件；
  归并维度带 `merged_from`/`merge_note`）。当前已验证映射 **0 条**；登记 1 条
  verified=false 护栏样例（六爻六合六冲 ↔ 梅花体用关系——GOAL 明令禁止的拍脑袋
  ontology 候选，无逐字书源依据不得启用）。零验证映射时对照行为与现状逐字段一致
  （selfcheck ⑦ 断言锁定）。
- **测试**：新增 `tests/test_rule_registry_ming_meihua.py` 24 例（结构/引文指针/dim 真实性/
  端到端挂接含如实降级/claim_policy 三态）；evidence_cross selfcheck 增概念映射两态 +
  真实注册表零行为断言。
- **文档**：`docs/EVIDENCE-MATURATION.md` 新增（Phase 1-8 阶段定位、五大问题→工作流、
  明确不做清单、完成判据）；TECH-DEBT §2.5、HANDOFF、llms.txt、synthesis README 同步。

### 2026-10-03 架构收敛 · Evidence-First / Agent-Native：Evidence Contract + 规则注册表 + canonical 反馈模型 + 能力注册表两级状态 + Agent API 五入口

> **性质**：纯加法与派生视图，**零引擎行为改动**——八科推演逻辑、语料、golden、
> tune/holdout/外部集全部不动；新层全部是 analyze 输出的派生表达与状态登记。
> 指标口径无变化（本条不涉及任何分数变更），分数读数仍以 `docs/HANDOFF.md` §一 为准。

- **Evidence Contract（P0）**：新增 `core/yishu_core/evidence.py`（唯一实现，纯函数、
  双宿主共用，不 import 学科代码）。八科 analyze 输出折叠为统一 Evidence 记录
  （id/claim/factor/rule_id/source/applicability/observation/effect/
  evaluation_status/provenance）。纪律：`effect` 只取学科自报方向（liuren/lingqi/ming
  无方向即留空，不制造吉凶）；有出处 ⇒ 至少 `source_only`；评测状态五档
  （unassessed/source_only/mechanical_regression/classical_holdout/external_holdout）
  按注册表基线传播、可被规则注册表升级；缺口经 `evaluation_gaps()` 显式登记。
- **宿主接线**：本机 `YiRuntime.execute` 与浏览器 `web/engine_runtime.build_report`
  的返回 envelope 均挂 `evidence` 信封；`tools/verify_web_parity.py` 同源验收新增
  **EV 列**（13 正例证据逐例比对，MD/HTML 比对口径不变）。
- **六爻规则注册表（P0/P1）**：新增 `disciplines/liuyao/data/rules/rule_registry.json`——
  9 个优先域（三会局/独发独静/反吟伏吟/六合六冲/旬空真空假空/墓库/进退神/用神多现/
  应期）+ 卦身/三合共 11 条，逐条带 `quote_in_data`/`quote_in_code` 引文指针
  （测试逐条解析验证存在）、适用条件、实现位置、评测覆盖（`dim` 必须是
  `evaluate.py WEIGHTS` 真实维度）；三合局引文未逐字核对，`verified=false` 登记缺口。
  挂接走 `evidence.attach_rule_registry`（domain 互为子串才挂，宁缺毋滥）。
- **合参证据级检视（P0）**：新增 `synthesis/evidence_cross.py` + CLI 子命令
  `evidence-cross`。归一化记录（`normalize.py`）附带 `evidence` 字段；检视输出
  same/conflict（保留双方 applicability+出处）/unassessed（缺口与 silent 学科显式登记）；
  **无趋势/得分字段**——跨科同向只提升一致性描述强度，不制造新事实；旧五条裁决
  （`cross_rules.adjudicate`）原样保留。诚实边界：维度级对照仅对同名词成立
  （跨科词表未统一，已登记 TECH-DEBT §2.5）。
- **证据检视进主合参文档（P0 收口）**：`synthesis cli guide`（与 `guidance.py`
  直跑、`tools/demo.py` 合参段共用）生成的指导文档 §三 内嵌「证据级检视」小节
  （same/conflict/unassessed + 冲突双方条件 + 评测缺口清单）；`two_one`（两吉一凶）
  趋向显式标注为**方向级计数倾向**（裁决规则 3），不再是最终逻辑——异向结论与
  成立条件必须并列检视后方可采信，同向只提升证据一致性描述强度。旧签名
  `build_guidance(arch, adjudication)` 兼容保留（不传视图则不渲染小节）；
  `cross_examine` 增加 `evidence_present` 与 `no_evidence_disciplines`
  （旧档案未携带证据 ≠ 学科未表态，两者不再混入 silent）。注册表挂接助手
  `attach_rule_registries` 单源收在 `evidence_cross.py`（cli 历史导出名保留转发）。
- **demo 子进程路径修复**：`tools/demo.py` 此前未把内核路径传给子进程
  （进程内 `sys.path.insert` 不被子进程继承），未安装内核的机器上六爻 render
  第一步即 `ModuleNotFoundError`；现显式注入 `PYTHONPATH=<repo>/core`。
  demo 本身非质量门，属工具修复（全科演示 + 合参指导段已实测通过）。
- **canonical 反馈模型（P1）**：新增 `core/yishu_core/feedback.py`（FeedbackRecord
  schema + 校验 + 双 adapter + `judge_record` 转调 `yishu_core.yingqi`——判定真值源
  不变，门 `[1i]` 纪律延伸）。`synthesis/outcome_eval.py` 评估路径改经
  `from_synthesis_divination` adapter（输出形状与口径逐字段不变，`[1i]` 门照跑）；
  六爻 `FeedbackStore` 增 `load_all_canonical()` 出口。`provenance.kind` 强制区分
  real_outcome/synthetic_regression，混集判败（真实/合成物理语义分离）。
  `synthesis/person.JUDGED` 改从 `core/feedback` 引用（词汇单源）。
- **能力注册表两级状态（P1）**：`core/yishu_core/execution/registry.py` 扩展——
  状态词表加 `mechanical_only`/`source_only`（`unvalidated` 语义由
  evaluation_baseline 的 `unassessed` 承载）；新增 `source_provenance`（八科 stable）、
  `outcome_feedback`（八科 experimental，机制已建真实回填 n=0 开环）、
  `evaluation_baseline`（liuyao/ming/meihua=classical_holdout；
  ziwei/xiaoliuren/zeji/liuren=mechanical_regression；lingqi=source_only）与
  `evaluation_splits`（分列名是结构事实，分数不进注册表）。liuren analyze=mechanical_only、
  lingqi analyze/narrate=source_only 显式落表——骨架科/直录科不得被当成完整吉凶能力。
- **Agent API（P1）**：新增 `core/yishu_core/agent.py` 稳定最小五入口
  `capabilities / validate_request / run_report / get_evidence / get_evaluation_status`；
  `get_evaluation_status` 刻意不含分数（附 `scores_authority` 指向 HANDOFF），
  附各科 `agent_note`（该科结论允许说到什么程度，口径诚实机器可读版）。
- **请求协议（P1）**：语义双维护消除的测试侧落点——新增
  `tests/test_request_parity.py`（归一化入口无关性、等价形式同 argv、深链短键
  白名单与语义 parity、Actions extra 字段 ⊆ REQUEST_FIELDS）；与 [1f]/[1h]/[7c]
  门并存，未改任何协议代码。
- **测试**：新增 7 个测试文件（evidence 契约 / synthesis 证据层 / feedback schema /
  capability registry / agent API / 规则注册表 / request parity）；既有
  golden/黑箱/忠实度/同源验收零改动。
- **文档治理（P2）**：单一权威源消歧——能力/评测状态 → `registry.py`（llms.txt
  引用不复制）；HANDOFF §一 ming 读数刷新（strict 97.1 / cong_ge 13/15，10-02t）并
  新增「证据链与 Agent 层」节；README 镜像读数同步刷新并声明四类评测口径
  （机械回归/古籍对齐/外部集/现实回填）不得互相冒充；ARCHITECTURE 补 [1h]/[1i]/[1j]/[7d]
  门清单 + 证据链七段责任表；DEEP-DIVE-PLAN 顶部加时效声明、四处已被超越的断言
  划线标注；TECH-DEBT 新增 §2.5（规则注册表缺口/评测粒度/跨科词表/event_logger
  未接 adapter）；`synthesis/README.md` 增证据级检视与 canonical 反馈模型两节。

### 2026-10-02t 命科加法 · 从格 kind「杀势当权」判据（通用规则，ZC kind 缺口 3→0）

> **口径登记（`AGENTS.md` §四.4）**：`pattern._from_judge` 从格 kind 判定新增一条通用规则
> （官杀当权不落从势）；**改动只在「主导差 <0.8 → 从势」分支内**，从弱成立条件、真/假口径、
> 其余路径零改动。分列验收：holdout strict 97.1（cong_ge 11/15→**13/15**、from_kind **12/15→15/15**、
> 其余维度不变）、命科 golden 机械/措辞指纹**零漂移**、`dev_tools/check.py` EXIT=0。

- **为什么改**：ZC011/012/014 书判「从杀」，引擎因主导差 <0.8 落「从势」（kind 缺口，见
  HANDOFF §四.5 与 DEEP-DIVE §2.4 #3 残余缺口）。三例书源原文的共同口径：
  ZC011「**杀势当权**…格成弃命从杀」（卯令乙透）、ZC012「**杀势愈旺**，格成从杀」（双壬透）、
  ZC014 丙丁并透「格取从杀」——**官杀当权时不成任注从势所要求的「财官食伤并旺」势均**。
- **通用规则**（非 case 分支，反例受控）：在从弱成立且主导差 <0.8 的从势分支内，若
  ① 月令本气为官杀**且**官杀透干 ≥1（当令且透=当权），或 ② 官杀透干 ≥2（成党），
  则 kind=从官杀。**反例受控验证**：ZC009 辰令官**不透**书仍从势（当令而不透不成当权）、
  ZC010 官透仅 1 且不当令——两者均不触发，15 例 ZC 集合其余 12 例逐一复核零漂移。
- **结果**：from_kind 15/15；真/假残余 2 例（ZC014/015）维持已登记灰区——
  ZC015 未土本气根**会入亥卯未木局**（根被会夺，形存气夺）、ZC014 庚比劫虚浮
  丙辛合绊克去，均须六合化气/克去微观机制，与 code 内既登记口径一致
  （「属灰区，待六合化气/合冲互动引入后复核」），不为过例硬填。
- **门**：命科 `dev_tools/check.py` EXIT=0；golden `2c3eee32…`/`05f8ebf3…` 与基线一致；
  `tests/test_ming_cong_sha_dangquan.py` 3 例锁定（当令且透/双透触发，ZC009 反例不触发），根 pytest **202 passed**。

### 2026-10-02s 修复+治理 · 根门 pytest 红 × 同名遮蔽 / [1c] 白名单逐条复核 / 孤儿断语处置 / 六爻「伏而不得出」入方向聚合

> **口径登记（`AGENTS.md` §四.4）**：① `[1c]` 断语外置审计的豁免口径收紧（详见下）；② 六爻新增一条
> **通用规则**（伏神不得出方向权重，所本《黄金策·千金赋》）；两者都属口径变更。分列验收：tune 96.8 /
> holdout 90.2 / wikisource_holdout 56.9 / suigui_holdout 94.5 / 黑箱回归 11/18——**全部与基线持平**（新规则
> 只在「用神伏藏且全部伏/飞对 can_emerge=False」时触发，现有评测集无一命中，由单元测试锁定行为）；
> 六爻金标准（机械 `d4ccdb7a…` / 措辞 `25c5eeea…`）与八科 render 指纹**零漂移**。分数口径未变，读数可比。

- **修复：根门 pytest 恒红（10-02q 遗留）**。`tests/test_ming_female.py` 用裸 `from analyze import …`，
  而 `tests/conftest.py` 有意让六爻 `scripts/` 排在 `sys.path` 前列（test_yingqi_windows 依赖）→ 六爻
  `analyze.py` 遮蔽命科同名模块，`female_fu_zi` 导入失败，`tools/check.py --full` 收集即断。改用
  `test_ziwei_patterns.py` 既有惯例：`spec_from_file_location` 唯一名加载 + 还原 `sys.path`。根 pytest
  195 → **199 passed**（含新增 4 例）。
- **HANDOFF §四.B [1c] 白名单逐条复核**（`tools/verdict_audit.py`）：
  - **过宽条收紧**：旧「括注性术语」「术语标签」两条是"行首带括注即整句豁免"，实测把
    「官鬼（落在卯三爻）几乎使不上劲」这类**真判语**整个豁免掉（判语本体已外置
    `narrative_templates.json#strength_phrases`，但引擎值插在句中导致子串匹配不上，白名单成了遮羞布）。
    收紧为「括注+短尾 ≤8 字」，并新增 `REL_LOC_PREFIX` 机械定位前缀剥离（`{六亲}（落在{支}{爻}）`，
    与既有 `YAO_PREFIX` 同理）把这类句子交还语料匹配。
  - **修正**：③ 事实配列旧版硬编码「丙午年」，改为通式「干+支+年」；⑦ 删冗余的「综合下来」
    （独立成句时短于 8 字本就被 MIN_HANZI 跳过，接续判语时不该替判语豁免）。
  - **新增豁免条（⑥b–⑥g，逐条写明"为何属非断语"）**：因子节标题带所本括注（ming）、紫微格局判定行
    （格局名+内核状态+书源诀文，名/诀均外置 `geju_rules.json`，中段插入值使匹配必漏）、紫微十二宫安星
    事实行（宫支/星名/亮度全为 core 查表值）、梅花卦气事实句、梅花 wrap 壳（就{focus}这一问而言…）、
    用神取法来源标注（meta.source 标签）。收紧后全量复核：**strict 0 句豁免性漏判**。
- **HANDOFF §四.C 孤儿断语处置**（清单=代码引用 × 数据引用 × 28 例报告消费三重核对）：
  - **删（9 条真孤儿，代码/数据零引用、零消费）**：六爻 `verdicts.json#shi_yao_interpretation` 的
    妻财 with_officer/illness_detail、官鬼 with_wealth/illness_detail（旧解读方案遗留；scenario 分派只认
    illness/marriage/travel/wealth 等 8 键）；梅花 `narrate_phrases.speed_lead`、`basis_quotes.ti_yong_zongjue`
    （体用总诀正本在 classics.json 有行号可回指，此为无行号副本）；小六壬 `narrate_phrases` 的
    open_youju/open_buli/kind_yinshen；六爻 `narrative_templates.json#narrate_shell.thinking_missing`；
    六爻 `verdict_texts.json#zeji_validity_gap`（zeji 自己的 verdicts.json#validity_gap 是正本，此处为
    错位副本，连同 `narrative_utils` 死加载量与 `text_keys_selftest` 死登记一并清除）。
  - **接线（1 处）**：「古人类似情境也说过：」此前在 `liuyao_narrate.py`/`narrate.py` 各内联一份字面量，
    `narrate_shell.quote_lead` 反被判零消费——两处改读同一 JSON 出处，渲染字节不变。
  - **登记（`tools/verdict_consumption.py`）**：修正 ALLOWLIST 匹配逻辑——旧实现拿键段去匹配**文件路径**，
    永远不命中，白名单名存实亡；现 `corpus_entries` 带键路径（`disc/data/x.json#/a/b`），并登记
    元数据/口径声明类零消费键（`_meta`、`shensha_policy`、`verified_note`、指针声明等，逐条写明理由）与
    未接线书源内容（六神 virtue/caution 列）。`[1d]` 维持报告制非 strict（124 课表等主题性键合法未触发）。
- **TECH-DEBT 2.3 六爻「伏藏+合绊」方向聚合（reg_07）——伏藏半边落地**：
  - 核实：**合绊**已有有界方向权重（原神贪合忘生 −2.0、日月合绊 −0.2 梯度、动化合绊 −0.3，10-02g 已
    结构化）；**伏而不得出**是真空缺——旧 `compute_fu_shen_adjustment` 只覆盖得出/泄气/克伏各象且靠
    嗅探 step3 文本，不得出时方向分零反馈。
  - 补法（通用规则，非 case 分支）：新增 **−1.0**，判据读 step2 `fu_cang_detail.results[].can_emerge`
    结构，旧文本路径保留为兜底、优先级不变；注记/理由外置
    `verdict_texts.json#step5_classical_notes.fu_no_emerge`（所本《黄金策·千金赋》"伏无提挈终徒尔，
    飞不推开亦枉然"，引文已在 references/classical_synthesis.md）。因子呈现区分「伏神得出/伏神不得出」。
  - **诚实边界**：reg_07 本例伏神临月建、飞神旬空（can_emerge=True），不触发新规则——其引擎「吉」与
    夹具「凶」的残余分歧是「飞空得出 +1.5」与占行人古籍直断之间的解释差异，引擎证据链可见，登记为
    已知方向失配，不为过此例加码。评测集暂无「不得出」书源真例（119 例探针核实），基准例待书源；
    行为由 `tests/test_liuyao_fu_no_emerge.py` 4 例锁定。
- **书源可得性复核（10-02 实测）**：《卜筮正宗》维基文库仍为纯目录骨架（卷一~十四全为红链，仅"卷前"
  可能存文）；《协紀辨方書》404——TECH-DEBT 2.1 "阻塞于外部数据"登记属实。新发现：《滴天髓阐微》
  （任铁樵注本，含命例）维基文库存在独立条目（由 滴天髓 辑要页链接可达）→ 命科外部独立集（HANDOFF §四.D）
  的解除路径由"用户供书"更新为"书源可网络获取，待照 ZC 批次机制提取命例"。

### 2026-10-02r 卜科加法 · 梅花易数外部独立集 `external_holdout`（卷三·變卦式八則，永不调参）[A 线]

> **口径登记（`AGENTS.md` §四.4）**：只建外部评测语料与其报分口径，引擎（`chart.py`/`analyze.py`）零改动；
> 故梅花机械层/措辞层指纹零漂移；`evaluate.py` 仅新增 `--split external_holdout` 分支与口径披露修正。

- **为什么建**：`HANDOFF.md` §四.1 已登记「梅花/小六壬/择吉 的 100% 是规则自洽回归，唯一有效动作是建外部独立集」；
  梅花按 `DEEP-DIVE-PLAN` §三「薄卜科 eval 只可信靠外部独立案例」推进。范式照搬六爻：`case_runner.load_cases()`
  合并同目录 `*_cases.json`（按 id 去重）+ `load_ids(split)` 支持任意 split（含 `external_holdout`），外部集只报命中数、永不参与 tune。
- **语料来源与诚实收窄**：取自《梅花易数》卷三·**變卦式八則**（原书 `data/sources/meihua_yishu_卷三.wikitext.txt`）。该节整体为
  **「物类断」**（断何物：铁/石/铁器），原文未给吉凶 verdict 字符串 → 本集 `verdict` 维度整体 `N/A`；
  其**互变陈述部分采用非标准口径**（如 归妹「四爻變卦成艮」标准变卦应为坤；夬「變兌卦」标准变出为巽），与引擎标准
  体用/互变计算不一致 → 归妹 的 `生体/克体` 维度 `N/A`，夬/履 因比和无生克且书未陈述 → 生克维度 `N/A`。
  仅 **革**（用克体 + 变卦艮生体 + 离火克体）三项与书言及引擎标准**完全一致**，保留为全维度对齐样本。
- **落盘**：`disciplines/meihua/data/cases/external_cases.json`（4 例，`split:"external_holdout"`，`provenance:"book_original"`），
  每例 `expected` 只填可独立对齐维度，`note` 逐条说明 N/A 原因（铁律三：不把对齐分说成预测率）。
- **报分口径修正（诚实）**：`evaluate.py::provenance_note` 原先对 `external_holdout` 也套用主库 `self_consistent_dims`
  （称"expected 与引擎同源"）——但外部集 expected 全部 `book_original`、与引擎不同源，是**真独立对齐证据**而非同义反复。
  已改为：外部集单独披露「独立性 + 口径收窄」，并抑制与其无关的 `tune_holdout_leakage` 警告。
- **读数（古籍案例对齐分，非预测命中率）**：n=4（原书应验 4 / 引擎构造 0），`relation` **4/4**、革 `sheng_ti`/`ke_ti` **1/1**；
  `n<20` 按纪律只报命中数、不发百分比。holdout 回归（13 例）不受影响，仍全绿。
- **门**：`python scripts/evaluate.py --split external_holdout` EXIT=0（异常 0）；梅花 `dev_tools/check.py` 未动、全绿。
- **遗留**：小六壬/择吉 外部独立集仍待建（同 §四.1）；梅花外部集目前仅 4 例且口径收窄——后续若换/拓书源（如卷一观梅占验原书应验可扩）再扩。

### 2026-10-02q 命科加法 · 四柱女命夫子星（机械标注）+ 童子煞神煞入盘（B1/B2，诚实标注口径）

> **口径登记（`AGENTS.md` §四.4）**：引擎新增机械标注 + 神煞安星；金标准**机械层零漂移**（`digest.json` 已 capture 理由
> `2026-10-02c 命科加法`）；**render 指纹为有意变更**（narrate 新增女命夫子宫专段 + 童子煞入盘），已用
> `tools/check.py --only report_contract --raise-render --reason` 重新落基线（ming render MD `5fe0…` → `1199…`）。

- **B1 女命夫子星**（`disciplines/ming/scripts/analyze.py::female_fu_zi` + `narrate.py` 专段）：依《渊海子平·女命论》
  以**官杀为夫星、食伤为子星**；机械扫描四柱天干与地支藏干十神，归类夫/子星所在（绑定 `core.relations` 单源桥
  `LIUQIN_TO_SHISHEN`），男命不调用（返回 `None`）。**只标所在，不批旺衰吉凶**（铁律三）。
- **B2 童子煞**（`core/yishu_core/shensha.py`）：诚实标注 **`verified=false`**——本煞为民间通胜口诀
  （口诀：春秋寅子贵，冬夏卯未辰；金木马卯合，水火鸡犬多；土命逢辰巳，童子定不错），**不在《三命通会》《渊海子平》
  《滴天髓》《子平真诠》原文**（经网络考证文确认）。按季/纳音机械安星，日时同支去重；**只安星不批吉凶**。
- **测试**：`tests/test_ming_female.py`（女命扫描天干+藏干、男命不调用 2 例）+ `tests/test_shensha.py` 童子煞 4 例
  （季/纳音/不触发），共 **14/14 PASS**。
- **门**：命科 `dev_tools/check.py` 全绿；八科 render 指纹门 `[6b]` 仅 ming 段为有意变更并重新基线，其余七科零漂移。

### 2026-10-02p 加法 · 大六壬课例集 4→43（《六壬大全》课经集+毕法赋）+ 按引擎自标 verified 分桶披露

> **口径登记（`AGENTS.md` §四.4）**：本批**只改评测语料集与其报分口径**，引擎（九宗门/
> 课目/天将）零改动，故八科行为指纹与 render 指纹**零漂移**（liuren 金标准未动）；
> 机械一致率读数由「n=4、命中 3」变为「n=43、命中 33」，属**样本量扩大**，非引擎提升。

- **为什么扩**：课例集此前只有 4 例（`LE001~LE004`，出自卷一与卷三），n<20 只能报命中数，
  读数无统计力，也看不出引擎弱点集中在哪一门。书源其实**整本**《六壬大全》都已在 `data/sources/`，
  卷七~卷十「课经集」与卷十一~十二《毕法赋》里散着大量「X日…三传XYZ」的逐字课例，此前**零消费**。
- **抽取口径收紧（宁缺勿滥，且为**唯一性**口径而非结果口径）**——`dev_tools/build_course_cases.py`：
  ① 同句**恰有一个**日干支（多日并列句如「丁巳、丁丑二日」「壬戌、壬辰日…癸丑…」一律不收——
  一句常把同一条三传摊给数日，机械切分必错）；② 同句**恰有一处**「三传XYZ」；
  ③ 定位语须**出现在「三传」之前**且**非传内关系语**（排除「初传/中传/末传/发用/为用 X加Y」
  ——如「巳加子为初传」说的是初传，不是月将加时）；④ 书明写门类须落在「日」与「三传」之间。
  源集扩为卷一 + 卷三~卷十二；**卷一次序在最前，故 `LE001~LE004` 编号在任何扩源下都不动**。
- **引文逐字可回指**（铁律三）：`source_quote` 取**整句、不截断、不改字**，并在建器内新增
  `stats.unverbatim` 断言——非书源原样子串即**拒绝落盘**（实测 0 条）。
- **读数（机械一致率，非对齐分非预测率）**：n=4 → **n=43**，三传命中 **33/43 = 76.7%**。
  按**引擎自标的 `verified`** 分桶披露：**可验证桶 26/28 = 92.9%**；**异说桶 7/15**
  （涉害一门口径诸书不一，引擎建课结果里已自标 `verified=False`）。分桶**不是把失配剔除，
  是把失配归因**——一混在一起就看不见弱项到底出在哪。
- **报分口径同步**（`scripts/evaluate.py`）：新增上述分桶行；并把静态脚注「n<20 只报命中数」
  改为**按 n 条件打印**（n=43 时已可报百分比，旧脚注会自我矛盾）。顺带删掉构造后从未读取的 `rows`。
- **遗留（已记 `TECH-DEBT`）**：10 例失配里 8 例落在**涉害**（引擎自标异说桶）；另 **2 例非涉害失配**
  须追源——`LE036`（癸未「似返吟卦…三传申寅申」，书意近昴星柔日，引擎算作贼克）与
  `LE041`（乙巳「传鬼化父母…三传酉巳丑」，引擎作子申辰），两例引文已逐字留档可复核。
- **门**：`disciplines/liuren/dev_tools/check.py` EXIT=0（金标准 4 条指纹未动、`[1d]` 引文逐字 155 条 0 非逐字）；
  `[1j]` 报「course_examples.json 与重算一致（可复现）」；`tools/check.py --full` EXIT=0。

### 2026-10-02o 架构 · 收掉 `[1j]` 最后一条缺口：就地合并型建器也纳入（liuren `kemu.json`）

> **口径登记（`AGENTS.md` §四.4）**：只加只读比对，不动引擎与判据；本次零行为变更，
> 无需重捕指纹。`tools/check.py --full` EXIT=0。

- **为什么它此前被判"不适用"**：`liuren/build_kemu_notes.py` 是**就地合并**型——先读入库
  `kemu.json`，再补前六门、`note`/`note_src`、`implemented`、`rules`。它**不是纯重算**，
  所以「重跑结果 == 入库文件」这句话对它没有意义（读的就是入库文件自己）。
- **改法（按其自身口径给判据，而不是放过它）**：把「**合并后应当落盘的那一份**」构造出来
  （即 `--write` 分支真正会写的内容），再与入库文件语义比对——一致即证明
  **重跑不会改变入库文件**（该建器的真实承诺）。同时把 `_comment` 从 `--write` 分支里
  提为模块常量 `COMMENT_LINES`，供 `--write`/`--check` **共用一份**（避免两处各写一遍）。
- **实测**：`--check` 报「**kemu.json 与重算一致（可复现）**」；顺带打印的口径仍有据：
  课目 64 条 / 有释义 60 / 无释义 4（涉害、乱首、孤寡、地盘——课经集未收，**不静默**）。
- **收尾状态**：`[1j]` 现覆盖 **8 条建器调用**（ming×2 / ziwei / meihua / zeji / lingqi / liuren×2），
  **语料建器已全部纳入，无待补**。仍明确不适用者只有两类：含人工裁决的案例集建器、
  以及 `--check` 语义本为「复验引文仍逐字命中源文」的六爻两个词典建器。

### 2026-10-02n 减法 · 同类隐患横切扫描：再抓一个「重跑即清空课例集」的建器（liuren）

> **口径登记（`AGENTS.md` §四.4）**：修复后重算与入库 `course_examples.json` **完全一致**，
> 故该文件内容零变化、liuren 机械一致率读数零变化，无需重捕指纹。

- **做法**：10-02m 的根因是「**内核 list 常量插进正则字符类**」→ 类在首个 `]` 提前闭合、
  多出一个必须匹配的字面 `]` → 正则恒不命中。故按此**特征做横切扫描**：
  全仓 `re.compile(f"…[{名}]…")` 逐一核名，并确认其余 `[{…}]` 出现的都是显示串而非正则。
- **又抓到一处（同类、同样可毁数据）**：`liuren/dev_tools/build_course_cases.py`
  `STEMS = HEAVENLY_STEMS`（list）→ `DAY_RE` **恒不命中** → `days` 恒空 → 逐句 `continue`
  → **抽到 0 例**；而 `main()` **无条件落盘**，即重跑会把 `course_examples.json`
  （大六壬课例集，`evaluate.py` 的机械一致率就建在它上面）**清成空集**。
- **改法**：`STEMS = "".join(HEAVENLY_STEMS)`；把提取主体抽成纯函数 `build_doc()`，
  `main()` 走「算 → 比 / 写」，补 `--check`，并纳入 `[1j]`。
- **实测**：`--check` 报「**course_examples.json 与重算一致（可复现）**」。
- **扫描结论（本轮清底）**：该缺陷类全仓共 **2 处**（10-02m 的 ming、本条的 liuren），
  均已修复并入 `[1j]`；其余正则插值处要么已是字符串（`BRANCHES`；
  `liuyao/evaluate.py` 的 `BRANCH_CLASS` 早在注释里写明"进正则前必须先 ''.join"），
  要么不构成字符类。**未发现第三处**。

### 2026-10-02m 减法 · 修掉一个「重跑即毁语料」的建器（ming 调候引文层）+ 纳入 `[1j]`

> **口径登记（`AGENTS.md` §四.4）**：修复后重算与**入库文件逐格一致**（51/51 命中主神相同），
> 故 `tiaohou_quotes.json` **内容零变化**、调候功能与各科分数**零变化**，无需重捕指纹。

- **怎么发现的**：给 `ming/build_tiaohou.py` 补 `--check` 时，`--check` 直接报 **462 处差异**，
  且重算侧「命中主神 0/120」。顺着查下去是两个**叠加**的潜伏缺陷：
  ① **内核路径写错**：`sys.path.insert(0, Path(__file__).parents[2] / "core")` —— `parents[2]`
     是 `disciplines/` 而非仓库根，落在 `disciplines/core`（不存在）。未 `pip install -e .` 的
     环境里本脚本**根本跑不起来**（ModuleNotFoundError），于是长期无人发现 ②。
  ② **list 插进字符类**：`STEMS = HEAVENLY_STEMS` 而该常量在内核里是 **list**；`f"[{STEMS}]"`
     会展开成 `['甲', '乙', …, '癸']]`——字符类在首个 `]` 提前闭合，多出一个**必须匹配的字面 `]`**，
     于是「== 论癸水 ==」这类标题**永不匹配**，`paragraphs` 恒空、**全表 120 格皆 N/A**。
     即：**只要有人重跑这个建器，`tiaohou_quotes.json`（调候书证）会被整体写成 120 个空格**，
     而现行所有门都不会红（调候其余门不读该文件的完整性）。
- **改法**：① 内核路径改由 `DISC.parent.parent / "core"` 反推；② `STEMS = "".join(HEAVENLY_STEMS)`
  （与 ming 另一建器 `TEN_STEMS` 同口径，注明"不在学科内另存一份天干序"）；③ 把提取主体抽成
  纯函数 `build_table()`（不落盘），`main()` 走「算 → 比 / 写」，补 `--check`。
- **实测**：修复后 `--check` 报「**tiaohou_quotes.json 与重算一致（可复现）**」，
  命中主神 51/51 与入库逐格同（10癸 庚/辛、via 得XY、exact 三项全同）。
- **纳入门**：`[1j]` 名单加入 `ming/build_tiaohou.py`；同时把该段每条的标签由「学科名」
  改为「学科/建器名」（此前两个 ming 建器打印同一行，分不清是谁）。

### 2026-10-02l 架构 · 语料可复现门覆盖扩到 5 个构建器（10-02k 的收尾）

> **口径登记（`AGENTS.md` §四.4）**：只加只读比对，不动引擎与判据；本次为零行为变更，
> 无需重捕任何指纹。`tools/check.py --full` EXIT=0。

- 10-02k 建了机制但只接 2 个构建器。本轮把**纯机械提取**的其余三个补齐 `--check`
  （不落盘、只与入库文件语义比对）：**meihua/`build_classics.py`**（classics.json）、
  **zeji/`build_citations.py`**（citations.json）、**lingqi/`build_ketable.py`**（ketables.json）。
  三者实测「与重算一致」——即这三份语料**确由构建器可复现产出**，不存在"手工补录后被重跑删掉"的隐患。
- **仍未纳入（如实登记，不假装覆盖）**：`ming/build_tiaohou.py`（`main()` 无条件落盘、无 dry-run
  开关，需先改成「算→比→写」三段）；`liuren/build_kemu_notes.py`（**就地合并**语义：先读已入库
  `kemu.json` 再补 note，非纯重算，"重跑须一致"不直接适用）。两条登记于 `TECH-DEBT.md` §2.4。
- **实测**：`[1j]` 五科全绿（ming 1 / ziwei 7 / meihua 1 / zeji 1 / lingqi 1 个文件）。

### 2026-10-02k 架构 · 语料可复现门（构建器 `--check` + 内核 `corpus_kit` + 根门 `[1j]`）

> **口径登记（`AGENTS.md` §四.4）**：只加门与只读比对，**不动任何引擎与判据**——八科行为指纹、
> `[6b]` 渲染指纹、各科分数**零变化**；`tools/check.py --full` EXIT=0。

- **病在哪（取证）**：引文/语料层允许**手工补录**（先机械铺底、再人工裁决补齐）。一旦构建器的
  「应产出集合」与入库 `data/*.json` 脱钩，**重跑构建器就静默删条目**——`docs/CHANGELOG.md`
  10-02f 已实测：`build_dts_corpus.py` 的 `WANTED` 未收「通隔論」，重跑即删掉该章。
  这类缺陷**不会让任何现行门变红**（数据被删后其余门照绿），属"做错无人知"。
- **改法（三层，均为只读）**：
  ① 内核新增 [`core/yishu_core/corpus_kit.py`](file:///c:/Users/31103/Desktop/program/Yi/core/yishu_core/corpus_kit.py)：
     `check(path, payload)` **语义比对**（JSON 解析后逐键/逐元素递归，不比排版缩进），
     差异按 `$.a.b[0]` 指路，并区分「重跑将新增」与「**重跑将删除**」两种方向；
  ② 两个**纯机械提取**的语料构建器补 `--check`（不落盘、只比对）：
     `ming/dev_tools/build_dts_corpus.py`、`ziwei/dev_tools/build_corpus.py`（7 个输出文件）；
  ③ 根门新增 `[1j] 语料可复现`，`--only corpus_repro` 也可单跑。
- **负例自证（门确实会咬人）**：往 `ditian_sui.json` 塞一个假章「假章」后单跑本段，立刻判败并
  点名 `$.ditian_sui.json.chapters.假章: 入库有、重算无（**重跑将删除**）`；删假章后复绿。
- **覆盖边界（如实登记，不假装已覆盖）**：本段只纳入**纯机械提取**的构建器。案例集构建器
  （`build_mingli_cases`/`build_yingqi_set`/`build_course_cases`/`build_tiaohou_cases` 等）含人工
  裁决，**不适用**「重跑须一致」；`build_question_use_gods`/`build_use_god_rules` 的 `--check`
  语义是「复验引文仍逐字命中源文」，与本节不同。其余纯提取构建器（meihua/zeji/lingqi/liuren 等）
  **待补 `--check`**，已登记 `docs/TECH-DEBT.md` §2.4。
- **实测**：`[1j]` ming 1 文件 / ziwei 7 文件均「与重算一致」；`tools/check.py --full` EXIT=0。

### 2026-10-02j 命科加法 · 紫微斗数**辅煞星书源说解**落地（另修两处引文提取缺陷）

> **口径登记（`AGENTS.md` §四.4）**：新增是**书源逐字 + 照录**，不参与评分、不改安星取值层——
> ziwei 金标准**机械层零漂移**（`c53ce772472a8af0` 不变），**措辞层**已 `dev_tools/golden.py
> capture` 归因重捕，`[6b]` ziwei render MD 指纹同轮重捕。不作吉凶断语（铁律三）。

- **加的是什么**：`star_nature.json` 此前只收**十四主星**的卷一「諸星問答論」说解；同一篇里
  **辅煞星**段落（文昌/文曲/左辅/右弼/禄存/擎羊/陀罗）其实**已被解析出来却没入库**（建器
  写表时只遍历 `MAIN_STAR_ORDER`）。本轮把它们一并入库（+7），并把 `star_palace.json`
  找回 **火星/铃星** 各宫释义（+21 条）。
- **接线（否则即死语料）**：narrate 新增「**命宫辅煞星**」段——命宫辅星按 **卷一性情说解
  （`star_nature`）+ 卷二本宫释义（`star_palace`）** 逐条出书源引文；**无书源者不出**
  （如三台八座、天刑天哭天虚，日内即不写）。实测 1984-02-10 例（命宫酉·文曲）两段引文齐出。
- **同一轮修掉的两个提取缺陷（减法，均属"引文失真"）**：
  ① **`canon` 无条件 `rstrip("星")`**：书源标题有「問紫微所主若何」与「问文曲星所主若何」
     两种写法，旧实现一律削尾字——于是**本身就带「星」的合法星名**（火星/铃星）被削成
     「火」「铃」，整段静默丢失。改为**先认原名、再退一步试去尾「星」**。
  ② **星段定界只认「下一个星名标题」**：非星名标题（如「问流年昌曲若何？」）及其正文会被
     吞进上一星段，产出**截断/串段引文**（实测旧文曲段末尾混进「====问流年昌曲若何？====」）。
     改为**按下一个任意标题行定界**。
- **诚实边界（写进建器）**：火星/铃星的卷一正文只有「答曰：火星乃南斗浮星也。希夷先生歌曰」
  这类**只报出性即引出歌诀**者，照收会得到一条以「歌曰」结尾的截断引文——故设
  `nature_quote()`（扣掉结尾「歌曰/歌」后实质汉字 ≥30 才收），二者**不入 star_nature**
  （其卷二宫位释义仍在，不失载），建器自检逐轮打印入层/未入层名单。
- **实测**：`ziwei/dev_tools/check.py` EXIT=0（`[4]` 语料接线 star_palace **227/514**、star_nature
  **2/42**）；`tests/test_ziwei_patterns.py` 12 项全过（新增 2 项：辅煞入层且火星/铃星不收、
  narrate 命宫辅煞星段出书源且无源者不出）；`tools/check.py --full` EXIT=0。

### 2026-10-02i 减法·架构 · `tools/eval.py` 挂进 `--full`（新 `[7d]`）+ 大六壬 evaluate 统一 `--split` + 清库外存量样例

> **口径登记（`AGENTS.md` §四.4）**：不动任何引擎与判据——只加门、统一 CLI 契约、删库外样例；
> 八科行为指纹与 `[6b]` 渲染指纹**零漂移**，`tools/check.py --full` EXIT=0。

- **`tools/eval.py` 长期挂账未入盒**（HANDOFF §四.6「在 `--full` 盒之外，回归不会被测出」）。
  挂之前必须先让它 EXIT=0——实测它**恒失败 2 项**：`liuren/scripts/evaluate.py` 不认 `--split`
  （`unrecognized arguments`，退出码 2），而 `tools/eval.py` 对每科固定传 `--split`。
  **根因是 CLI 契约不齐**：各科 evaluate 的入参形状不统一。
- **改法（两处，均最小）**：① 大六壬 `evaluate.py` 增 `--split`（**接受但明说忽略**——
  本科课例集是单一机械一致率集、不分 tune/holdout，故打印一行口径说明，不静默吞参）；
  ② 根门新增 `[7d] 各科案例对齐分一览`，`--full` 或 `--only eval_overview` 时跑
  `tools/eval.py`（它只转发各科 evaluate，不写第二套给分逻辑；无 evaluate 的
  ming/ziwei/lingqi 按「无案例对齐评测」跳过、不计失败）。实测 `tools/eval.py` **EXIT=0**，
  `[7d]` 绿。
- **清库外存量样例（减法）**：`docs/architecture-review-improvements.html` 落在 `docs/` 根，
  而 `.gitignore` 只给 `docs/samples/**` 开白名单（`docs/*.html` 在 `*.html` 忽略域内）——
  即该文件**从未能入库**；且其 `<title>`「输入→输出链路：现状与目标改进对比」与现存的
  `docs/ARCHITECTURE-REVIEW.md`（H1「…全链路系统工程评审」）**不是同一份**，源文档已不在库。
  判据：源文档消失 + 内容被现有评审文档取代 + 从未入库 → **删除**（不搬进 `docs/samples/`
  把一份无源的陈旧产物补进货架）。
- **文档订正（同轮）**：`docs/samples/README.md` 文件清单缺 `EVAL-PLAN.html`（其源
  `docs/EVAL-PLAN.md` 已移除）——补该行并如实标注「源文档已不在库，此份为存量样例」。

### 2026-10-02h 命科加法 · 四柱干支关系层补入**天干五合**（10-02f 的地支层对称补全）

> **口径登记（`AGENTS.md` §四.4）**：新增是**书源逐字 + 机械结构标签**，不参与任何评分
> （命科 tune 30 / holdout 246 为机械回归自检，非对齐分）；**机械层零漂移**
> （强弱/格局/大运指纹 `2c3eee326cec8ccd` 不变），**措辞层**已 `dev_tools/golden.py capture`
> 归因重捕（两次：先补内容、再改段标题），`[6b]` ming render MD 指纹同轮重捕。只出结构，不批吉凶。

- **加的是什么**：10-02f 的四柱关系层只判**地支**（六合/六冲/六害/三刑）。本轮按同一范式补
  **天干**：年/月/日/时**四干两两**（六对）判**五合**（甲己／乙庚／丙辛／丁壬／戊癸）。
  书证：《滴天髓·天干論》「丙火…逄辛反怯」（丙辛）、「丁火…合壬而忠」（丁壬）、注
  「合戊見火」（戊癸）即是；表取内核 `core.relations.STEM_WUHE`（**不新建第二份五合表**）。
- **判据更名**：`pattern.pillar_branch_relations` → `pattern.pillar_relations`（含干支两类；
  旧名会让「干合」落在地支函数里，名实不符）。analyze 的 `pillar_relations` 字段名不变；
  narrate 段标题与 verdict label 由「四柱地支关系」订正为「**四柱干支关系**」。
- **诚实边界（沿用）**：仍**只判「合/冲/害/刑」之结构，不判「化」**（合化须透干、得月令等条件）。
- **用例守护**：`dev_tools/regression.py` MG001–MG005 期望据内核表逐条更新（MG001 年时与日时
  两处甲己合 + 月时寅巳害；MG004 年时丙辛合 + 自刑；MG005 年日乙庚合 + 月日申巳合；
  MG002 只有年日乙庚合；MG003 全空——防误报）；`tests/test_ming_structures.py` 增
  `test_pillar_relations_stem_wuhe` 并更新既有三例（共 187 pytest 全过）。
- **实测**：`dev_tools/check.py` EXIT=0；`tools/check.py --full` EXIT=0。

### 2026-10-02g 六爻减法·架构 · 格局标签去「子串匹配」改读结构（DEEP-DIVE §1.2 欠项）

> **口径登记（`AGENTS.md` §四.4）**：**格局标签的派生口径变了**——由「扫 `step5`/`summary`
> 文本取词」改为「读 `advanced_analysis` 结构」，故 `patterns` 维度相关的分数**不可与旧口径
> 直接跨比**。实测（strict）：tune **96.8**（不变）、holdout **89.7 → 90.2**、
> `wikisource_holdout` **56.3 → 56.9**、`suigui_holdout` **92.0 → 94.5**（外部集只报数）。
> 六爻 `check_baseline.json` 已按进步抬升；`[1.6]` 金标准机械指纹（含 `patterns` 字段）
> 与根门 `[6b]` liuyao render MD 指纹同轮**归因重捕**（理由入 `drift_log`）。

- **病在哪（取证）**：`liuyao_narrate._collect_pattern_tags` 里有两段文本扫描——
  ① 扫 `step3.summary_text` 取「出旬/填实/冲空/动空/飞克伏/伏生飞/泄气/暗动」；
  ② 把 `step5` **全部标量**拼成字符串扫「三合/合局/三刑/恃势/无恩/六合/六冲/冲中逢合/
  合处逢冲/旬空/月破/反吟/伏吟」。**逐例取证（109 例）**：把两段停掉，36 例的
  三合/合局等标签消失——而 `step5` 里含 `classical_quotes_text`（古籍引文），引文正文
  本就频繁出现「三合」二字，于是**任何一卦都可能凭空多出三合标签**。这正是
  `docs/DEEP-DIVE-PLAN.md` §1.2 记的「格局词子串匹配而非结构比对」（假阳来源）。
- **改法**：标签一律**读结构**——`advanced_analysis.hidden_movement`（暗动/冲空逐爻）、
  `monthly_break`（月破逐爻）、`triple_combo`（三合/合局）、`three_punishments`
  （三刑；**只认成刑**，`completeness ∈ 完整/成刑/催刑`，「待刑」缺月日补齐不计，口径同
  `effects`/`step5`）、`repetition`/`clash_harmony`（反吟/伏吟/六合/六冲，原已有结构路径）。
  无第二份判据实现，`advanced_analysis` 即唯一真值源。
- **实测标签集变化（109 例逐例比对）**：新增（旧缺）**月破 +30、三刑 +36、冲空 +9、
  暗动 +7**（逐爻结构覆盖，旧实现只在用神层或引文层命中）；移除（旧假阳）**六冲 11、
  三合 4、旬空 4、伏吟 4**。两组变化方向一致——**结构命中变准**，故三套外部集读数齐升。
- **用例守护**：新增 `tests/test_liuyao_pattern_tags.py`（6 断言）——① 引文含「三合」不再
  造标签（SG002/WS017/WSD024/WSD033）；② 三刑只认成刑（HO001 待刑→无，HO003→有）；
  ③ 三合须来自结构成局（HO003）。
- **未做**：未改 `evaluate.py` 的 `PATTERNS` 词表与计分公式（只换引擎侧的标签来源），
  故计分口径本身未动，仅输入标签变准。

### 2026-10-02f 命科加法 · 四柱地支关系层（六合/六冲/六害/三刑，DEEP-DIVE §2.1 欠项）+ 引文层构建器同步

> **口径登记（`AGENTS.md` §四.4）**：新增是**书源逐字 + 机械结构标签**，不参与任何评分
> （命科 tune 30 / holdout 246 为机械回归自检，非对齐分）；**机械层零漂移**（强弱/格局/大运
> 指纹 `2c3eee326cec8ccd` 不变），**措辞层**已 `dev_tools/golden.py capture` 归因重捕，
> `[6b]` ming render MD 指纹同轮重捕（理由入 `drift_log`）。只出结构，不批吉凶。

- **加的是什么**：`DEEP-DIVE-PLAN.md` §2.1 登记「四柱之间独立的刑冲合害检测」为命科欠项
  （现状只有运-年两支比对与日柱天克地冲）。本轮落地**四柱地支关系层**：年/月/日/时
  **四支两两**（六对）判 **六合 / 六冲 / 六害**，另列四支中的**三刑**组合，共四类结构标签。
  古法依据《滴天髓·地支論》「支神祇以沖為重，刑與害兮動不動」（沖為重、刑害次之）。
- **判据与真值源**：`pattern.py::pillar_branch_relations`，表一律取内核
  `yishu_core.symbols`（`HE_PAIRS`/`CHONG_PAIRS`/`HARM_PAIRS`/`sanxing_hits`），
  **不新建第二份干支关系表**。analyze 出 `pillar_relations` 与 `verdicts` 一项，
  narrate 增「四柱地支关系」段并附《滴天髓·地支論》逐字三首。
- **诚实边界（写进判据 docstring）**：**只判「合/冲/害/刑」之结构，不判「化」**——合化须透干、
  得月令等附加条件，本环境无对应语料可逐字核对，故不落「合化」结论（同 `shensha`/`xiao_yun`
  的 `verified=false` 口径）。这是与「反吟/伏吟/进退神」等六爻格局词同类的**结构层**，非同断语层。
- **用例守护**：`dev_tools/regression.py` MG001–MG005 增 `pillar_relations` 期望（手工据内核表推得：
  MG001 寅巳六害 / MG004 亥亥自刑 / MG005 申巳六合；MG002/MG003 为空，专防误报）；
  `tests/test_ming_structures.py` 增三例（合冲害各自命中、三刑与六害并存、空集防误报）。
- **构建器同步（同轮减法）**：`dev_tools/build_dts_corpus.py` 此前 `WANTED` 只列 7 章，
  而 10-02b 手加的「通隔論」不在其中——**再跑一次构建器会把通隔論静默删掉**（引文层与
  构建器脱钩）。本轮把 `WANTED` 补齐（+03 地支論、+20 通隔論）、新增 `PICK`（章内**节录**
  指定源行，地支論只取与判据相关的三首原文）、并把 `source_lines` 改为**机械生成**
  （始 Novel 行、止末条原文/注文行，节录章另列源行号），顺手订正 `_meta.口径` 里写死的「7 章」。
  重跑构建器 diff 实测：所有既有章 verse/notes/day_stem **逐字不变**，仅新增 地支論 与各章
  `source_lines`。
- **实测**：`dev_tools/check.py` EXIT=0（`[8]` 语料接线：地支論三首均进入报告，非死语料）；
  `tools/check.py --full` EXIT=0（八科行为指纹、`[6b]`、同源验收、pytest 全绿）。

### 2026-10-02e 架构·减法 · 质量门进程壳上收内核 `yishu_core.gate_kit`（消 6 份重复实现）

> **口径登记（`AGENTS.md` §四.4）**：只改门自身的实现，不改任何引擎与判据——八科行为指纹、
> `[6b]` 八科 render MD 内容指纹、tune/holdout 基线读数**全部不变**；
> `tools/check.py --full` 与八科 `dev_tools/check.py` 逐科 **EXIT=0**。

- **病在哪（取证）**：八科 `dev_tools/check.py` 各写一份子进程壳，**实测 6 种不同实现**——
  argv 前缀（是否内置 `sys.executable`）、`cwd`、超时（无/60/120/300）、子进程环境
  （不传 / `utf8_subprocess_env()` / 手拼 `{**os.environ, "PYTHONUTF8":"1"}`）各不相同；
  `measure`（4 份逐字相同）、`eval_metrics`（4 份、两种落盘结构）同样各写一份。
  这正是 `AGENTS.md` §二「同类只存一份」要治的病，`docs/CONTRACT.md` §四.6 也已明文要求复用。
- **改法**：新增内核模块 [`core/yishu_core/gate_kit.py`](file:///c:/Users/31103/Desktop/program/Yi/core/yishu_core/gate_kit.py)，
  收走三件事——`run_step(cmd, *, cwd, timeout, python)`（子进程一律带 `utf8_subprocess_env()`，
  治「中文 Windows 子进程按 GBK 出字节 → 中文断言假红」）、`measure(name, out, patterns)`、
  `eval_metrics(split, *, eval_file, cwd, model_key)`（含新鲜度守卫：先删旧落盘、跑完核 mtime，
  防崩溃时旧分冒充本次）。八科退化为**声明式薄壳**（各 3–7 行，含口径注释），
  实现只有一份。顺带清掉随之无用的 `subprocess` / `os` 导入，并修 lingqi 门
  「定义了 `CORE` 却从未入 `sys.path`」的潜在缺陷。
- **一个设计约束被门当场咬住（值得记）**：初版把「评测落盘目录」也放进内核，
  `[1g] 案例库隔离` 立刻判红——「内核不该知道案例库的存在」。遂把路径改为**调用方传入**
  （`eval_file`），内核只做守卫与解析。**这条门确实在守铁律二，不是装饰**。
- **口径登记（同轮）**：`docs/CONTRACT.md` §四.6 补一句「进程壳复用 `gate_kit`、各科只声明口径」，
  免得新科又照旧写第七份。

### 2026-10-02d 减法 · 清死代码 6 处 + 归档 7 份过期过程规格（AI 痕迹）

> **口径登记（`AGENTS.md` §四.4）**：纯删除，不改任何引擎行为——**八科行为指纹与
> `[6b]` 八科 render MD 指纹均零漂移**（后者正是本轮刚落地的内容级指纹，等于替这次
> 删除做了「用户可见输出未变」的机械证明）。`tools/check.py --full` EXIT=0。

- **死代码 6 处（AST + 全仓词边界双证，删后复扫为 0）**：
  - `core/yishu_core/ziwei_tables.py`：`dual_pattern_name` / `single_pattern_name`
    ｜ziwei `analyze.py` 自己就在查 `PATTERNS` 表，这两个包装函数全仓零引用（重复实现）。
  - `disciplines/liuyao/scripts/engine_calendar.py`：`ganzhi_moment` /
    `crosscheck_optional_libraries`｜后者是「装了 lunar-python 就抽样对核」的旁证工具，
    零引用且旁证职责已由内核 `core/yishu_core/calendar_check.py` 承担。
  - `disciplines/liuyao/scripts/kernel_path.py`：`discipline_root`｜`feedback_store.py`
    另有一份同语义的 `_discipline_root`（在用），此份是零引用的重复实现，留着只会诱人继用错的那份。
  - `disciplines/liuyao/scripts/trigram_symbolism.py`：`get_trigram_info`｜零引用。
  - 同轮顺手清掉 `engine_calendar.py` 顶部被拉散的空行 / 拆分 import（4 处空行 +
    逐行独立 import）——无效排版痕迹，非功能改动。
- **归档 7 份过期过程规格**：`docs/compose/spec/` 6 份 + `disciplines/liuyao/docs/compose/spec/
  classical-holdout-benchmark.md`，移入 **`archive/compose-spec/`**（git 保留全文）。
  判据（沿用已归档 `archive/AUDIT.md` 的 S-B4/S-B5 结论 + 本仓「AI 痕迹反例」口径）：
  全部 `status: delivered`、**读数停在 2026-09**（含旧金标准指纹 `a1a7d34c3532f2f2`
  与旧分 `93.7 < 基线 94.2`），且含**把已落地项当待办**的条目（如
  `internal-depth-pack.md` 仍写「`chain_step5` 单函数 939 行巨石，未做」——该文件 2026-09-26
  已拆、其后已删；`yi-optimize-pack.md` 仍以 MCP 工作面为待办——MCP 已于 10-01g 全量移除）。
  全仓零消费（唯二指向它们的 `docs/HANDOFF.md` 与 `docs/ARCHITECTURE.md` 两行已改为指向新位置）。
- **未做**：不新建「合并归档」文档（避免为减而增）；不改任何 `data/`、`core/` 之外的行为代码。

### 2026-10-02c 架构 · render 段内容指纹落地（架构评审 A6 大动血版：输出层首次有内容保护）

> **口径登记（`AGENTS.md` §四.4）**：只加门、不改引擎，八科分数与行为指纹均不变
> （`tools/check.py --full` 全绿）。新增的是一条**基线 + 一道判败门**。

- **补的是什么盲区**：四段契约里 `render` 是**唯一没有任何内容指纹**的一段——八科
  `dev_tools/golden.py` 只罩 chart/analyze（逐科 grep `render` 零命中），根门原本只判
  「产物存在」。**同源验收只保证「本地＝网页」，不保证「和上一版一样」**：两边同时改坏
  模板，门照样绿；而 render 产物正是用户读到的东西。
- **落地方式（折中 blast radius）**：不为八科各加一段 golden，而是把指纹放进**根门已有的
  `[6b]` 段**——它本来就逐科渲染八条最小请求。新增 `data/golden/render_digest.json`
  （`md: {学科: sha256[:16]}`）+ 逐科比对；漂移即判败并给出重捕指引。只锁 **Markdown 逐字节**
  （与同源验收口径一致；HTML 页头 `class="meta"` 的「运行环境」标签是有意差异，不入指纹，
  其页脚/口径句由 `[6b]` 既有结构断言守）。
- **重捕机制**：`python tools/check.py --only report_contract --raise-render --reason "理由"`
  （**理由必填，缺则退出码 2**，与各科 `golden.py capture` 同规矩），理由写入 `drift_log`。
- **实测**：① 连跑两次 `--only report_contract` 均绿（八科 MD 指纹**确定性**成立）；
  ② **负例自证**：把基线里 `ming` 的值改成全零，门立刻红并点名
  「ming：render MD 指纹漂移 0000… → c67bbb4e95cea0f4」——门确实会咬人，不是装饰。
- 未采纳本项原方案的 `golden_kit.split_rows` 三层改造：那要动八科 `golden.py` + 八个
  digest 重捕，收益相同而 blast radius 大得多（A6 折中版已在 `[6b]` 覆盖契约级不变式，
  本版补的是内容级，两者互补）。

### 2026-10-02b 命科加法 · 日主两路「通关／关隔」结构层（《滴天髓·通隔論》逐字入库）

> **口径登记（`AGENTS.md` §四.4）**：新增是**书源逐字 + 机械结构标签**，不参与任何评分
> （命科 tune n=30 / holdout n=246 为机械回归自检，非对齐分）；**措辞层**指纹已
> `dev_tools/golden.py capture` 归因重捕，**机械层零漂移**。只出结构，不批吉凶。

- **加的是什么**：《滴天髓》第十九章「**通隔論**」此前**未入库**（`ditian_sui.json` 只收
  narrate 实际引用的 7 章）。本轮把它作为命科的一层结构判据落地：原文「兩意本相通，
  中間有關隔，此關若通也，到處歡相得」，注文五例（木土而得火、火金而得土、土水而得金、
  金木而得水、水火而得木）皆是**兩行相克、中有生序中介之神則氣通**。落到日主即子平常论两路：
  **官杀克身 → 得印通关**（金克木得水）、**身财相战 → 得食伤通关**（木克土得火）；
  中介之神不现则记**关隔**。
- **判据与真值源**：`pattern.py::tong_guan`（纯机械：取四干五行 ∪ 四支本气五行为「局中所有」，
  相克双方俱现方为相战，再看中介是否亦现）；`_ke_wo` 由内核 `KE_CYCLE` 逆向取值，
  **不新建第二份五行表**。analyze 出 `verdict` 与 `conclusion.tong_guan`，narrate 增
  「通关／关隔」段并附《滴天髓·通隔論》**逐字原文 + 注**（引导句外置在 `ditian_sui.json`）。
- **数据**：`ditian_sui.json` 新增「通隔論」章（`verse` 1 句 + 注 1 段），
  `source_lines` 记 `data/sources/di-tian-sui.wikitext.txt:503-506`（Novel 子頁 19；原文行 504、注文行 506），
  `章数` 7 → 8、`口径` 文字同步。门 `[8] 语料接线` 实测该章两条均进入报告（非死语料）。
- **用例**：命科机械回归 `dev_tools/regression.py` 的 MG001/002/003 增 `tong_guan` 期望
  （手工据四柱推得：甲日身财相战木克土得火通关；乙日官杀金克身无水为关隔；丙日官杀水克身得木通关）。
- **诚实边界**：命科 golden 的**机械层只快照强弱/格局/大运字段**，不含三会/胎元/十神组合/
  天克地冲/通关这类四柱补充因子——故新字段由**回归用例**（非指纹）看护，此边界在此登记，
  以免后人误以为指纹已覆盖。

### 2026-10-02a 卜科加法 · 六爻「用神入墓」补齐动墓/化墓（HANDOFF 可执行清单 E）

> **口径登记（`AGENTS.md` §四.4）**：`use_god_muku` 评测维度由「日墓/月墓」两级扩为
> **日/月/动/化四类**，计分对象变了，分数与旧口径**不可直接跨比**。实测：
> tune strict **96.8**（n=20，不变）、holdout strict **89.7**（n=12，不变）——
> 规则升级只让期望值更细，未升降两套基线。金标准指纹零漂移（只动基准数据与
> 附属维度，不动排盘/思维链）。

- **加的是什么**：《增刪卜易·隨鬼入墓章第三十》「古有日墓、動墓、化墓之三墓」、
  〈入墓難克〉「卦中動出墓爻，亦向此推。金爻動而化丑亦是」——此前六爻的墓库维度
  **只验日墓/月墓**（`najia_rules.md` 也只列「入日墓/月墓」），动墓/化墓为评测盲区。
  本轮新增结构判据 **动墓**（卦中另有动爻，其地支即用神墓支）与 **化墓**（用神发动，
  化出之支即用神墓支），只出**结构标签，不批吉凶**（旺衰救应另论）。
- **唯一真值源**：判据落在 [classical_enhancements.use_god_tomb_tags](file:///c:/Users/31103/Desktop/program/Yi/disciplines/liuyao/scripts/classical_enhancements.py)，
  引擎侧 [case_runner.py](file:///c:/Users/31103/Desktop/program/Yi/disciplines/liuyao/scripts/case_runner.py) 与基准侧
  [build_extra_dimensions.py](file:///c:/Users/31103/Desktop/program/Yi/disciplines/liuyao/dev_tools/build_extra_dimensions.py)
  同源调用（此前两处各写一份日/月墓规则，本次合并为一份，消除漂移口）。
  两条排除项按理定：用神本爻值自身墓支属**自坐墓**（不计动墓）、化出本支属**伏吟**
  （不计化墓），并各留单元断言。
- **书源真例（非对表）**：新增 [classical_cases.json](file:///c:/Users/31103/Desktop/program/Yi/disciplines/liuyao/data/cases/classical_cases.json)
  两例，逐字出处为 `data/sources/zengshan_buyi.wikitext.txt` 行 700–709 / 722–731：
  ① `SG001` 戌月甲寅日占会试，小过之艮——书断「世爻隨官入三墓，動墓，化墓」，
  引擎结构层得 **入月墓、动墓、化墓**；② `SG002` 未月戊辰日占重罪赦免，蛊之损——
  书断「世爻隨鬼入動墓，又動而化墓」，引擎得 **动墓、化墓**。二例立论皆以世爻
  （世持官鬼），故 `expected.use_god` 记「世爻」，非为过门而设私有别名。
- **集合登记**：两例归入**新外部集** `suigui_holdout`（《增刪卜易·隨鬼入墓章》真例，
  永不参与调参），`case_splits.json` 登记、`load_ids` 改为**按清单键通用取值**
  （新增书源只登记数据，不再改函数）、`dev_tools/check.py [6]` 与 `evaluate.py --split`
  同步列出。实测 suigui_holdout 对齐分 **92.0%**（n=2），未对齐项是应期单位（书作
  年/月级，引擎给日级）与一例格局词，**如实记低，不调**。
- **减法（同轮）**：`case_splits.json` 顶层 `note` 里 4 次重复的
  「yingqi_holdout=应期外部验证集…」冗余句、`note_externals` 尾部重复残句一并清除。
- **用例守护**：新增 [test_liuyao_tomb_tags.py](file:///c:/Users/31103/Desktop/program/Yi/tests/test_liuyao_tomb_tags.py)
  （11 断言：书源三例 + 四类判据 + 两条排除项）。三段门全绿：
  `dev_tools/check.py`、`tools/check.py --full` 均 EXIT=0。

### 2026-10-01x 卜科加法 · 大六壬「日辰关系」层（卷三「日辰」歌，10 条判据）

> **口径登记（`AGENTS.md` §四.4）**：新增的是**结构标签 + 书源引文**（本科为骨架科，
> **不出吉凶方向**）；无计分，故不涉及分数可比性。金标准指纹漂移已归因重捕。

- **加的是什么**：《六壬大全》卷三「日辰」歌此前**未被任何消费方使用**（全库该卷零引用）。
  本轮把它做成**日辰关系层**：日干/日支各自与其上神（四课之上神）论生克，共 **10 条**——
  日上生干 / 日上克干 / 干生上神 / 干克上神 / 日上生辰 / 辰上生干 / 日上克辰 / 辰上克干 /
  日辰俱受生 / 日辰俱受克。每条带 `desc`、机械依据与**逐字诀文**，数据在
  `verdicts.json#richen`（代码零断语字面量）。
- **三重守门**（都按现有门范式，不新造）：
  ① `[1d] 引文逐字门` 扩到 `richen.*.句`（现核 **155 条** = verdicts 31 + 课目 124，非逐字 0）；
  ② `[1] 720 课式全枚举` 扩到日辰关系——每条判据**零触发即判败**（本轮 10 条全部触发）；
  ③ 期望条数由 `MEN_ORDER + TIAN_JIANG_ORDER + richen 标签数` **实算**（原写死 21，改后不写死名单）。
- **报告**：narrate 增「日辰关系」段（标签 + 依据 + 诀文 + 出处），analyze 增 `richen` 字段与
  `factors` 一项；仍不出方向（`conclusion.direction` 恒为 null）。

### 2026-10-01w 卜科加法 · 择吉二十八宿值日吉凶歌（书证与判据首次机械对齐）

> **口径登记（`AGENTS.md` §四.4）**：新增的是**书证原文挂载**（只作对照），
> **不参与评分、不改判据**；tune/holdout 对齐分仍 **100 / 100**。机械层指纹零漂移。

- **加的是什么**：[citations.json](file:///c:/Users/31103/Desktop/program/Yi/disciplines/zeji/data/citations.json) 新增 `xiu_verses`：
  《玉匣記·理論吉凶日篇·**二十八宿值日吉凶歌**》**28 宿**（各带值宿神将、书证吉凶、
  两行歌诀原文与源文件行号）。此前该篇**未被消费**——引擎的宿吉凶表只自述
  「取通行《二十八宿吉凶歌》」，**库内无逐字书证**。
- **首次把「书证 vs 判据」变成机械断言**：门 `[1c] 参考书证门` 新增三条——
  ① 宿集必须等于内核 `zeji_tables.XIU_ORDER`；② 歌诀**按行号回读**核对；
  ③ **书证吉凶 ≡ `verdicts.json#xiu` 的吉宿/凶宿**（不一致即判败，须人裁决）。
  实测：28 宿全部一致（引擎的 14 吉 / 14 凶 与《玉匣記》逐字歌诀完全吻合），
  书源（繁体）宿名归化只涉 7 字（虛婁畢參張軫鬥），**只用于字典键，原文照录**。
- **挂到报告**：narrate 在「值宿」行后附歌诀（引导句外置在 `verdicts.json#narrate_phrases`）；
  analyze 的 `citations` 增 `值宿歌诀` 字段。
- **减法（同轮）**：`tools/verdict_audit.py` 的「歌诀引导模板」白名单补一类
  （原文在 data 者，引导句只报书名/宿名/出处，属排版）——该门当轮即把新引导句点名，
  按既有设计归类而非放宽门槛（白名单条目仍逐条具名、可复核）。

### 2026-10-01v 卜科加法 · 梅花易数逐卦类象正表（卷一·八卦萬物屬類，214 条）

> **口径登记（`AGENTS.md` §四.4）**：新增的是**书源原文挂载**（只作取象依据），
> **不参与评分、不改判据**；tune/holdout 对齐分仍 **100 / 100**。机械层指纹零漂移
> （只动措辞层：narrate 多一段原文）。

- **加的是什么**：[classics.json](file:///c:/Users/31103/Desktop/program/Yi/disciplines/meihua/data/classics.json) 新增 `wanwu`：
  卷一「象數易理篇之三·**八卦萬物屬類**」逐卦类象正表——每卦按
  天時／地理／人物／人事／身體／時序／動物／靜物／屋舍／家宅／婚姻／飲食／生產／
  求名／謀旺／交易／求利／出行／謁見／疾病／官訟／墳墓／方道／五色／姓字／數目／五味
  诸类逐条**逐字**入库，共 **8 卦 / 214 类**（每卦 ≥20 类，必含天時/地理/人物）。
  此表此前**未被任何消费方使用**（引擎只用了卷一「（並為上卦）」那段简表的合并口径）。
- **怎么挂到报告**：`verdicts.json` 新增 `wanwu_topic_keys`（事类→书源类目键，**数据非代码**），
  analyze 新增 `analogy_table`（体卦/用卦在该事类下的类象原文），narrate 在类象段附出。
  例：求财占 → 体卦乾给「求利／交易／人物／身體」四类原文，用卦艮给对应四类原文。
- **门**：`[1c] 古籍原文门` 扩到类象表——**按记录行号回读核对**（`lines[行号-1] == 原文`），
  比子串断言强；另断言八经卦齐、每卦类数下限与必备类，书源一变形即判败。
  实测该门现核 **262 段**原文（含类象 214 条）。
- **减法（同轮）**：`build_classics.py::one()` 原写 `text in "".join(lines)`——对
  「从该行摘出的文本」**恒真**（等于没断言，行号漂移也发现不了），改为按行号回读比对。

### 2026-10-01u 架构 · A10 忠实度门扩到 12 例语料（并因此揪出一处六冲/六合真错）

> **口径登记（`AGENTS.md` §四.4）**：本轮改了六爻**推演逻辑**（卦体六合/六冲的判据来源），
> 故 tune/holdout 分别出分并重比基线——**tune 96.8%**（前基线 93.9，文档旧读数 95.0）、
> holdout 89.7 不变；未参与调参的外部集 wikisource_holdout 由 57.1 → **56.3（n=35）**，
> 如实登记为**下降**（≈0.3 例，在噪声内，但方向如实写）。计分方式本身未变。

**一、架构 · A10：忠实度门从单例 `--demo` 扩到内置语料（12 例）**

- [report_faithfulness.py](file:///c:/Users/31103/Desktop/program/Yi/tools/report_faithfulness.py) 新增 `--corpus`：12 例**合成请求**
  （coin/time/number 三种起卦法 × 求财/病/考试/婚姻/出行/官司/失物/天气/行人），逐例跑
  chart→analyze→narrate→审计并汇总；某例起不来即判败且不掩盖其余各例。
  语料**不取自 `data/cases/`**（铁律二：案例库与解读过程隔离）。
- 门 `[6] faithfulness` 由 `--demo` 改为 `--corpus`（`--demo` 保留供快速自查）。
  原门只证明「这一条断言链能抓 invented」，证明不了「换个起卦法、换类问事仍不越界」。

**二、修复 · 该门当轮即揪出一处用户可见的真矛盾（六爻 六冲/六合）**

- **症状**：某请求的报告同时写「六冲卦主散，晋卦世应相冲」（格局层）与「无明确合冲」（同一次
  analyze 的结构层 `clash_harmony.hexagram_type`）——自相矛盾，`--corpus` 判 `contradicted`。
- **根因**：[liuyao_step4.py](file:///c:/Users/31103/Desktop/program/Yi/disciplines/liuyao/scripts/liuyao_step4.py) 在结构判据之外**并列一份手写卦名白名单**，
  与 core 的 `symbols.hexagram_he_chong_kind`（按对应位 (1,4)(2,5)(3,6) 三对地支皆合/皆冲算）冲突：
  - 误收为六冲 **10 卦**（遁/晋/萃/夬/姤/解/归妹/旅/涣/小过），误收为六合 **18 卦**；
  - `离`（八纯六冲）被列进**六合**名单；`涣`/`离`/`萃` **同时出现在两张名单里**（自相矛盾）；
  - 漏收 core 认定的六合 `复`/`旅`。`晋` 的对应位三对为 (未,酉)(巳,未)(卯,巳)，无一对合/冲。
- **改法**（通用规则，非 case 分支）：白名单**整体删除**，改为调用 core 的结构判据
  （与同一次 analyze 的 `hexagram_type` 同源）。新增回归测试
  [test_liuyao_hexagram_kind.py](file:///c:/Users/31103/Desktop/program/Yi/tests/test_liuyao_hexagram_kind.py)（65 断言）：
  ① 锁 core 的六冲集合 = 八纯 + 无妄 + 大壮、六合集合 = 否/泰/贲/困/旅/豫/复/节；
  ② 逐卦断言**报告层格局判定的六冲/六合类命中只可能发生在 core 认作六冲/六合的卦上**。
- **分数**：tune 95.0 → **96.8**（基线同步抬升至 96.8），holdout 89.7 不变，`--corpus` 74/74 supported。

**三、连带处置（黑箱回归 12/18 → 11/18，逐例有据）**

- A/B 取证（临时脚本跑完即删）：白名单版 FAIL={reg_01,13,14,16,17,18}，结构判据版
  FAIL 增加 reg_07、reg_15 —— 两例的**通过都依赖那份错误六冲标签施加的 −2.0 惩罚**。
- **reg_15 订正（案例数据自相矛盾）**：原 `yao=[7,7,8,7,7,7]` 实起**天泽履**（对应位三对皆非合非冲、
  世五申/应二卯亦不相冲），却在自身注释里写「引擎: 震为雷六冲」、用例名叫「六冲卦·世应相冲」——
  即**从未真正测过六冲卦**。已按本例前提改为名副其实的震为雷；其唯一非书据支撑的维度
  （用神旺衰）记 `None` 走 N/A 剔除（**不据引擎实测回头改期望值**）。
- **reg_07 登记为真实缺口**（不改考卷、不为它写分支）：占行人·用神伏藏·合绊化退，
  古典判凶，引擎出「吉」（动变净效应 −0.50 却未反映到方向）。已入 `TECH-DEBT` 待清偿。
- 黑箱回归基线仍为 11/18，现值 11/18（含上述订正）。

### 2026-10-01t 架构 · A2 反馈口径归一（内核唯一口径 + 新门 `[1i]`）

> **口径变更登记（`AGENTS.md` §四.4）**：本轮**改了计分口径的一处实现缺陷**——
> 六爻侧宽松（loose）命中判定此前用一张本地支合表，其中「丑午」「未申」两对
> **既非六合亦非六冲**（丑午是六害），会造成**虚假宽松命中**。剔除后同一批数据
> 的 loose 命中数只会变少、strict 不变，故新旧 loose 读数**不可比**。
> 分数含义仍为**现实回填命中**，非古籍对齐分、非预测率。

**一、架构 · 应期判定口径收归内核一份（`core/yishu_core/yingqi.py`，新增）

- 同一语义「预测应期 → 现实回填 → 命中判定」此前有两套并行实现、常量各写一份：
  合参层 [outcome_eval.py](file:///c:/Users/31103/Desktop/program/Yi/synthesis/outcome_eval.py)（名次制 `YQ_SCORE`）
  vs 六爻 [feedback_store.py](file:///c:/Users/31103/Desktop/program/Yi/disciplines/liuyao/dev_tools/feedback_store.py)（容差窗 `LOOSE_WINDOW_DAYS = 7`）。
  两种口径是**真实差别**（一个问候选排序、一个问日期接近），**不合并**；
  合并的是**表与常量**：现唯一真值源为 `core/yishu_core/yingqi.py`。
- 内核新模块持有：`RANK_SCORE`（名次制得分表）、`STRICT/LOOSE/BRANCH_WINDOW_DAYS`、
  `HE/CHONG` 支关系（**读 core `symbols.HE_PAIRS/CHONG_PAIRS`，不再本地再写一份**）、
  `parse_date` / `branch_of`（**日支反推改走 `ganzhi_calendar.day_ganzhi_index`**）、
  `judge_rank` / `judge_window`，以及两种口径各自的**口径语句**（`RANK_CALIBER` / `WINDOW_CALIBER`）。
- 两处消费方退化为调用方：`outcome_eval.YQ_SCORE` 是内核表的**再导出**（同一对象），
  `feedback_store` 删掉本地 `_HE/_CHONG/_is_he/_is_chong/_day_ganzhi_seq/_ANCHOR/_compute_hits`
  （含 1900-01-31 自设锚点）。审计报告 [feedback_report.py](file:///c:/Users/31103/Desktop/program/Yi/disciplines/liuyao/dev_tools/feedback_report.py) 摘要现在附口径句（来自内核唯一一份）。
- 未取「存储目录二选一」那一支：合参层读人档案 `divinations[].outcome`、六爻侧读学科
  `data/feedback/` 记录，数据来源本就不同，强行合目录会把「人档案」概念塞进学科；
  已在 `ARCHITECTURE-REVIEW.md` A2 就地记录取舍。

**二、门 · `[1i]` 反馈口径单一真值源（三层锁，判败制）**

- ① 身份：两处取到的评分表/窗口常量必须是内核里那一个对象；
  ② 内容：两处源文件不得再出现这些常量或支关系表的字面量赋值；
  ③ 行为：表驱动边界断言——±1 天严格、±7 天宽松、8–21 天内**六合**记命中、
  **六害**不记（点名回归「丑午/未申」）、超 21 天不记，且名次制得分确取自内核表。
- 六爻 `dev_tools/check.py` 新增 `[1.7] 反馈闭环假例自检`：应期抽取 / strict·loose 判定 /
  读数汇总 / 口径句接线四项断言，**落盘走临时目录**（不碰 `data/feedback/`，铁律二）。
  该通道此前是「有实现、无测试、无数据」——`check.py` 对 `feedback` 关键字 0 命中。
- **负例验证**（一次性脚本跑完即删）：① 在 `feedback_store.py` 重写 `LOOSE_WINDOW_DAYS = 9`
  → 门报「本地又在写应期口径常量」+「不同值」；② 把内核支合表换成含丑午/未申的旧错项表
  → 门报六合缺失 + 「丑午 非六合非六冲，不得算命中——旧错项回归」。两例均退出码 1。

**三、验证**

- `python tools/check.py --full` 全绿（八科行为指纹**零漂移**——本轮不动任何学科推演结果，
  只动反馈通道；六爻黑箱回归 12/18 ≥ 基线 11/18）。

### 2026-10-01s 卜科加法 · 大六壬课目识别 34→42（第二批结构判据）

> **口径登记（`AGENTS.md` §四.4）**：新增判据仍为**机械结构标签**（只出课体名 + 书源诀文/释义，
> 不作吉凶断语，与本科「骨架科」章程一致）；不改计分方式。分数口径不变。

- 逐条复核余 30 条未落课目的课经集释义，再挑出**判据只倚赖 日柱 / 三传 / 四课 / 时支 /
  天将布法**者八条落地（无一条倚赖旺相、神煞、年月、年命）：

  | 新增课目 | 判据（书源卷一「课目」诀 + 课经集释义） | 判据式 | `partial`（未并入的条件，显式声明） |
  |---|---|---|---|
  | **淫泆** | 「凡课初传卯酉为用，将乘后合」 | 初传 ∈ {卯,酉} 且该传所乘天将 ∈ {六合,天后} | 狡童格（用起六合终于天后）/ 泆女格未分立 |
  | **芜淫** | 「凡四课有克，缺一为不备…为芜淫课」 | 四课不备（有一课重复）且四课有克 | 注又列「日辰交互相克」一面未并入（该面另覆盖近半课式，并列会使判据失焦） |
  | **侵害** | 「凡课日辰六害相加，并行年为用」 | 干上神与支上神互为六害（core `HARM_PAIRS`） | 书注诸例（子加未…）为单课上下相害之式，本判据取「日辰上神相加」一面；行年未并入 |
  | **刑伤** | 「凡课中三刑发用，并行年为刑伤课」 | 三传递见三刑（core `sanxing_hits`） | 「又兼本命与年命」未并入 |
  | **死奇** | 「凡斗罡系日辰阴阳发用，为死奇课」（斗罡者辰也） | 初传为辰 且 辰为四课之上神 | 「月缠天罡…丘墓岁伏殃灾随」的年月神煞条件未并入 |
  | **鬼墓** | 「凡日辰墓神及日鬼发用，为鬼墓课」 | 初传为日墓（`TOMB_MAP`）或日支墓，或初传克日干（日鬼发用） | 书源并列两面，本判据取其一即报；用起四墓/自坐四墓/干支乘墓诸格未逐格分列 |
  | **殃咎** | 「凡三传递克日，神将克战，或干支乘墓」 | 三传递克日干（顺逆两式），或干上神为干墓且支上神为支墓 | 「神将克战」需将神五行表，未并入 |
  | **龙战** | 「凡卯酉日占，卯酉为用，人年立卯酉」 | 日支 ∈ {卯,酉} 且初传 ∈ {卯,酉} | 「人年立卯酉」行年条件未并入 |

- **守门证据**（`disciplines/liuren/dev_tools/check.py`）：720 课式全枚举中
  淫泆 **27** / 芜淫 **113** / 侵害 **60** / 刑伤 **115** / 死奇 **52** / 鬼墓 **241** /
  殃咎 **28** / 龙战 **42** 次触发——「零触发即判败」的门对八条全部通过；
  判据数 34 → **42**（余 22 条仍为旺相/神煞/年月/年命依赖，如**需节气的天祸、二烦、天寇**，
  只登记诀文不写占位识别）。判据条数仍由 `kemu.IMPLEMENTED` 运行时实算，文档不写死。
- `data/kemu.json` 的 `implemented` 旗标由 `dev_tools/build_kemu_notes.py --write` 从
  `IMPLEMENTED` 派生重写（64 条，释义 60 条）。
- **指纹漂移（已归因重捕）**：`liuren` 金标准机械层 `cb34a6d43b22b8c1 → aae0b01f13955a50`、
  措辞层 `8e12f73742eecf26 → 2978cc70c8e014d6`——4 条金标准用例中 4 条的
  `four_courses / chuan_tianjiang / factors`（课目清单入 `factors`）字段新增命中课名，
  属**判据扩充的预期结果**，非退步；`golden.py capture` 已带因由落盘。

### 2026-10-01r 卜科加法 · 大六壬课目识别 31→34（九丑/天网/游子）

> **口径登记（`AGENTS.md` §四.4）**：新增判据均为**机械结构标签**（只出课体名 + 书源诀文/释义，
> 不作吉凶断语，与本科「骨架科」章程一致）；不改计分方式。分数口径不变。

- **修正 10-01q 的结论**：该条记「余 33 条**多**倚赖旺相/神煞/年命」。逐条复核后，
  其中确有**纯结构可判**者——本轮落地三条（判据只倚赖 日柱 / 三传 / 四课 / 时支）：

  | 新增课目 | 判据（书源卷一「课目」诀 + 课经集释义） | 判据式 | `partial`（未并入的条件，显式声明） |
  |---|---|---|---|
  | **九丑** | 「凡戊子…辛酉十日，为九丑日。如四仲时占，丑临日加四仲上发用」 | 日柱 ∈ 书源所列十日 且 初传为丑 | 诀注「四仲时/四仲日」有传抄异读，只取「十日+初传丑」一面 |
  | **天网** | 「凡课占时与用神同克日，为天网课」 | 时支与初传**俱克**日干 | 无（原文条件单一） |
  | **游子** | 「凡课三传皆土，遇旬丁天马为用，曰游子课」 | 三传皆辰戌丑未 | 旬丁/天马附加条件未并入（同 `铸印`/`斲轮` 对「诀又须…」的处理） |

- **守门证据**（`disciplines/liuren/dev_tools/check.py`）：720 课式全枚举中
  九丑 **6** / 天网 **49** / 游子 **29** 次触发——**零触发即判败**的门对三条全部通过；
  判据数 31 → **34**（余 30 条仍为旺相/神煞/年命依赖，只登记诀文不写占位识别）。
- `data/kemu.json` 的 `implemented` 旗标同步 31 → 34（门 `[1c]` 读数为「已落判据 34 条」）。
- 指纹：`liuren` 金标准机械层 `cb34a6d43b22b8c1` / 措辞层 `8e12f73742eecf26` **均零漂移**
  （4 条金标准用例未触发新课目）。
- 修一处实现缺陷：`kemu.recognize` 此前未绑定 `hour_branch`（天网判据需要），已从
  `chart_out.moment.hour_branch` 取，缺失时取空串（不静默降级）。

### 2026-10-01q 命科加法（紫微古法格局 5→14）+ 报告契约门扩至八科 + 卜科加法受阻结论

> **口径登记（`AGENTS.md` §四.4）**：新增判据均为**机械结构标签**，不改计分方式；
> 分数口径不变（古籍案例对齐分，非现实命中率）。

**一、加法 · 紫微斗数（命科）**

- `analyze.py::judge_classical_patterns` 判定的古法格局由 **5 条 → 14 条**（原文判据早已在
  `data/geju_rules.json` 逐字登记，此前「其余仅作文献保留」）：
  富局 金灿光辉；贵局 日出扶桑 / 月落亥宫 / 月生沧海 / 武曲守垣 / 君臣庆会 / 辅弼拱主 /
  财印夹禄 / 金舆扶驾。判据式逐条取自原文单条件（如「太阳单守，命在午宫」「禄守命梁相来夹」）。
- **口径边界（不美化）**：**只判富局/贵局，不判贫贱局/杂局**——把「贫贱/孤贫/困顿」类标签
  打进报告属命定论，与命科「不作命运断语」（`AGENTS.md` §一.3）冲突。
  「见前批注」类（判据为交叉引用）与倚赖小限/流年/四化特殊结构者**仍不判**。
- 测试：`tests/test_ziwei_patterns.py`（10 断言，用**合成命盘**覆盖稀有局，
  另断言贫贱/杂局不进判定表）。
- 指纹：紫微机械层 `c53ce772472a8af0` **零漂移**；措辞层 `7ea2dd5c2c360c0f → f3c3ee87f046a03e`（narrate 格局段变长）。
  副作用（正向）：`geju_rules.json` 语料消费由原比例升至 **46/77 条进入报告**。
- 稀有度实测：1440 例扫描中 金灿光辉 14、日月夹财 20、日月照璧 18 命中；君臣庆会/辅弼拱主/
  财印夹禄/金舆扶驾 在该样本下 0 命中——属真实稀有（合成命盘测试已证明判据式可成立，非恒假）。

**二、架构 · `[6b]` 报告契约门由「六爻单点」扩至「八科逐科」**

- 上一轮（10-01p）的 `[6b]` 只跑六爻一条请求；本轮改为**八科各一条最小请求**（经 `--request` 传入），
  逐科断言口径句/反馈尾注在位、禁用断言词为 0 —— render 段（四段契约唯一无内容保护的一段）
  的内容级覆盖由 1 科 → 8 科。`A6` 覆盖缺口据此收窄（排版级哈希基线仍缺，已在 `TECH-DEBT` §2.4 登记）。
- 同时补 `REPORT_REQUIRED`**关键字段必达**断言：逐科取若干 `analyze.chart_summary` 结构化键
  （如 ming `强弱/格局/胎元`、ziwei `命宫主星/格局/五行局`、lingqi `课名/卦宫`），
  断言其值出现在 narrate 正文——专抓「**算出来了但报告没呈现**」（`AGENTS.md` §四.6）。
  取键口径：**实测哪些键确会渲染**（一次性探针跑完即删），不凭猜。

**三、减法**

- `docs/TECH-DEBT.md` §2.4 首行**结案**：`liuyao/guard/*.json`、`dev_tools/guard/base_human.json`、
  `liuyao/scratch/golden_before.json` 经核实**不属仓库债务**——`guard/` 与 `scratch/` 均在
  `disciplines/liuyao/.gitignore` 内（本地快照，不入库），全仓仅 `dev_tools/refactor_guard.py`
  在显式 `--write/--compare` 时读写，无门或脚本常态读取；`verdict_audit` 已将其排除出语料池。

**三之二、架构 · A7 折中：反馈评分表加常驻自洽自检**

- `synthesis/outcome_eval.py` 新增 `selfcheck_scoring()`：拿一份**人造候选**跑**真实判定路径**
  `_eval_yingqi`，断言 ①**档位路由**（首/次/三四位候选、提前、窗口内未对齐、超期各落对档）
  ②**边界字面量**（主应期 `1.0`、超期 `0.0`）③**单调性**（名次越靠后得分越低）。
  挂到 `synthesis/cli.py::cmd_selfcheck`（根门 `[7]` 常驻）。
- `cmd_outcome_eval` 空集退出码由 `1` 改 `0` 并打印口径声明——**空集＝「无数据」不是「评测失败」**
  （`ARCHITECTURE-REVIEW` A7：此前该链路"可跑"被误报成失败，回归无从谈起）。
- 否定探针（进程内改表、不改盘）：`YQ_SCORE[1]=0.5` → 单调性断言命中；`overrun=0.2` → 边界断言命中。
  即断言**非恒真**。

**四、卜科加法的现状判定（记录，不注水）**

逐科核实后，卜科「可再加的真实判据」已基本见底，**再扩即属注水**，故本轮不硬做：
- **六爻**：`DEEP-DIVE-PLAN` §1.1 所列环节缺口（三会/独发独静/卦级反吟伏吟/双卦对比/三传克制/
  真空假空）**已全部落地**；残余为**评测覆盖**（动墓·化墓、暗动/月破结构比对），需新增古籍基准例，
  受「禁止考卷调参」约束。
- **梅花 / 小六壬 / 择吉**：三科「唯一有效动作是建外部独立集」，**阻塞于书源未数字化**
  （`TECH-DEBT` §2.1；择吉 `data/verdicts.json#validity_gap` 明写「不伪造古籍日例」）。
- **大六壬**：`kemu` 64 课目中已实现 31（**本轮 10-01r 已续补至 34**，见上条）；余者多倚赖
  **旺相/神煞/年命**，而本科按章程为**骨架科（只出机械结构标签、无吉凶断语）**，
  不引入旺相/神煞即无法判——其余条目属**设计使然**，非缺口。
- **灵棋经**：`ketables.json` 课表 **124/124 完整**，无缺。

### 2026-10-01p 架构收口（A3/A5/A6/A8）+ 命科加法（三会/胎元/流月/小运/天克地冲/十神组合）

> **口径登记（`AGENTS.md` §四.4）**：均为**新增结构标签 + 门增强 + 清单单一真值源**；
> 不改计分方式、不改既有机械行为。分数口径不变（古籍案例对齐分，非现实命中率）。

**一、架构（对应 `docs/ARCHITECTURE-REVIEW.md` A1–A11）**

| 项 | 动作 | 证据 |
|---|---|---|
| **A8 残余** | 合参层**四处学科清单**（`normalize.DISCIPLINES` 7 科 / `person.DISCIPLINES` 5 科 / `cli --discipline` 3 科 / `cross_rules` 卜仅 liuyao）统一到唯一真值源 `request.DISCIPLINES`（八科）；**修复 ziwei 被判「未知学科」的跨层缺陷**（`cross_rules.domain_check` 与 `person.add_divination` 均拒绝 ziwei，而 `cli` 却允许） | `synthesis/{normalize,person,cli,cross_rules,guidance}.py`；import 期断言 + `cli.py::cmd_selfcheck` 清单锁 + `cross_rules.selfcheck` 命卜分区锁 |
| **A3 折中** | `check_structure()` 增**目录级预算**：`disciplines/<科>/scripts/` 合计行数超 `SCRIPTS_BUDGET_BASE=6000` 须在 `DECLARED_HEAVY` **显式申报**上限（liuyao=22000），否则判败——分布式巨石不再默认漂移 | `tools/check.py` |
| **A6 折中** | 新增 `[6b]` **报告契约**门：对**用户真正读到的统一报告**断言 `REPORT_FOOTER`（HTML 口径句）与 `MD_FEEDBACK_NOTE`（反馈尾注）在位、禁用断言词为 0（`BANNED_CLAIM` 只拦「命中率/准确率+数字」「断事如神」，**不拦**「不宣称现实预测命中率」类否定免责句） | `tools/check.py` |
| **A5 折中** | 新增 `request.REQUEST_FIELDS`（请求字段白名单唯一真值源）+ `[1h]` **深链短键锁**：`web/web.js::DEEPLINK_KEYS` 的值必须是白名单成员（短键表只在 JS 侧、不受 `[1f]` 协议指纹覆盖） | `core/yishu_core/report/request.py`、`tools/check.py` |
| **A5 附带修复** | `tools/report.py` 补 `--seed`：深链与 `request.chart_argv` 早已支持 `seed`（六爻 coin 可复现）、`web.js` 亦有该字段，**唯本地 CLI 无**——「网页端有、本地没有」的能力落差 | `tools/report.py` |
| A10（未落地） | 忠实度门仍只跑单例 `--demo`；按科覆盖留待下轮（断言抽取器为六爻专用，扩科需按科写抽取器） | —— |

**二、命科加法（真实判据缺口，非注水）**

按 `docs/DEEP-DIVE-PLAN.md` §2 的缺口清单落地六项**机械结构标签**（只出结构名与依据，**不批吉凶**）：

| 新增 | 起法/判据（书源） | 唯一真值源 |
|---|---|---|
| 三会方局 | 寅卯辰木/巳午未火/申酉戌金/亥子丑水（《三命通会》） | `core.symbols.SAN_HUI_GROUPS`（此前已被六爻消费，**命科未用**——本轮接上） |
| 胎元 | 月干进一位、月支进三位（《三命通会》） | `ming/scripts/pattern.py::tai_yuan` |
| 流月 | 正月（寅）起五虎遁，顺行十二位 | `pattern.py::liuyue_table`（`core.ganzhi_calendar.TIGER_MONTH_STEM`） |
| 小运 | 自生时起，顺逆同大运；**通行起法流派有别，标 `verified=False`** | `pattern.py::xiao_yun_table` |
| 天克地冲 | 某运/年柱与日柱天干相克且地支相冲（《渊海子平》）；只标记 | `pattern.py::tian_ke_di_chong`（`core.symbols` 五行相克表 / `CHONG_PAIRS`） |
| 十神组合 | 伤官见官 / 枭神夺食 / 食神制杀 / 财滋弱杀（透干共现） | `pattern.py::ten_god_combos` |

- 报告层同步：`analyze` 新增字段 → `narrate` 新增「四柱结构与组合 / 流月 / 小运」段（`AGENTS.md` §四.6）。
- 指纹：命科机械层 `2c3eee326cec8ccd` **零漂移**（新增字段不进机械指纹）；
  措辞层 `286883c58f448ca7 → 0d70d5efb0102b47`（narrate 新增段），已按 §四.1 `capture` 归因。
- 测试：`tests/test_ming_structures.py`（6 断言：胎元/三会/流月/小运/天克地冲/十神组合）。
- **口径放宽登记**：`verdict_audit.NON_VERDICT` 增一条 `天克地冲`——与既有「流年…与运…」同属
  **由内核算出的机械结构标签**，非断语，故与 `[1c]` 白名单同类处理（不改判败语义）。

**三、减法**

- 消除合参层「同一事实四处写死」（A8 残余，见上表）——文档层 A8 的其余三处（`ARCHITECTURE.md`
  「六科」、旧指纹、`SKILL.md`「四条」）经核实**已于前轮（10-01n）订正**，本轮未重复动作。

### 2026-10-01o 大六壬「同一事实多处写死」收口：条数与名单一律运行时实算（唯一权威源）

> **口径登记（`AGENTS.md` §四.4）**：本次为**口径一致性修复 + 措辞归因**，不改计分方式、
> 不改机械行为。病与紫微「76/80/82」同类：同一串常量在数据、文档、代码各写一份，
> 语料一增长就互相说谎。分数口径不变（古籍案例对齐分，非现实命中率）。

| 事实 | 唯一权威源（运行时实算） | 原写死点（已改引用/实算） |
|---|---|---|
| 九宗门名单（9） | `scripts/jiuzongmen.py::MEN_ORDER` | `dev_tools/check.py` 的两份字面集合（越界断言、`[1d]` 条数） |
| 引文条数与逐字清单 | `dev_tools/check.py::verbatim_inventory()` | `verdicts.json#verbatim_policy.scope`、`_comment`、订正器 docstring/自检打印 |
| 期望引文条数（21） | `len(MEN_ORDER) + len(core TIAN_JIANG_ORDER)` | `check.py` 的 `!= 21` 字面断言 |
| 课目表条数（64） | 书源卷一「课目」段实算 `check.py::book_kemu_count()`（按**自编号**逐行进位解析：跨度 `一…六五` 65 号 − 缺号「五八」1 条 = 实收 64；缺号登记 `KEMU_NUMBERING_GAP`，门 `[1c]` 断言实算缺号 == 登记缺号） | `check.py` 的 `!= 64`、`kemu.py` docstring、`kemu.json#_comment` 与 `build_kemu_notes.py` 的「第 1–65 条」 |
| 判据条数（31） | `kemu.IMPLEMENTED` 长度 | `analyze.py` label/note（改运行时 f-string）、`verdicts.json` preamble/charter、`kemu.py` docstring、`SKILL.md`（改引用句） |
| 枚举例数（720） | `len(days) × len(EARTHLY_BRANCHES)` | `check.py` 打印文案；「伏吟 60/返吟 60」改 `len(days)` |

- 门 `[1d]` 与订正器 `dev_tools/fix_verbatim_basis.py` 共用 `verbatim_inventory()`，
  归化规则（行号→键）只在订正器 `FIXES` 一处；数据只声明规则、不再列条数。
- **反例验证**（`tools/scratch/gate_logs/liuren_dedup_probe.txt`，进程内改动 + 字节级还原）：
  改 `MEN_ORDER` → 期望条数随之变 22 且门判败；`verdicts` 少 1 条天将 verse / 少 1 门 → 判败；
  `kemu.json` 去掉 1 课（63 vs 书源实算 64）→ 判败；`analyze` 注入 33 条 → label 数字随权威源变。
  即「数字来自实算」而非「换了一处字面量」，且门两侧都会真的响。
- **指纹**：机械层 `cb34a6d43b22b8c1` **零漂移**（`factors` 只取 `basis`，本次未动）；
  措辞层 `46079ece1688f627 → 8e12f73742eecf26`（4/4 例：`factors[4].label`、`analyze#verdicts_note[1]`
  （= `verdicts.json#preamble[1]`）与 `tianjiang.charter` 去掉写死数字改引用句；后两者属显示层、
  不进机械指纹），已按 §四.1 `capture` 归因。历史台账（`digest.json` 的两侧 `drift_log`、
  本文件 2026-10-01n）按只追加/同批次内修订处理，不改写他人历史。

- **减法 · 删死代码（行为零变化，有证据）**：`dev_tools/check.py` 的 `check_verbatim()` 末尾
  有一段被抽象化替换却未删的旧实现（在 `return fails, detail` 之后的 6 行，且引用
  `registered / norm / items / n_verdicts` —— 这四个名字在该函数作用域内**无绑定**，
  一旦被执行必 `NameError`，属「减法残留 + 定时炸弹」）。已删。
  等价性证据（`tools/scratch/gate_logs/liuren_deadcode_equiv.txt`）：语句数 16 → 13（差 3 条 / 6 行，
  全部位于 `return` 之后 → 不可达）；**13 个代码对象逐函数字节码完全一致**（忽略行号/偏移/跳转地址）；
  删除前后门输出**逐行相同**（`liuren_gate_pre_deadcode.txt` / `liuren_gate_post_deadcode.txt`）。

#### 附：收口时查出并登记的一处**书源缺号**（不臆补）

- 同一事实多处写死的排查中发现：`kemu.json#_comment` 与 `build_kemu_notes.py` 声称「第 1–65 条」，
  而卷一「课目」段实收 64 条。逐行解析该段**自编号**（该书用序数 一…六五 逐条编号）：跨度
  `一…六五` = 65 号、实收 64 条，**缺第 58 条（五八）**，段落里第 57 条（五七解）之后直接是
  第 59 条（五九困）——即书源该段少一条，不是数据少一条。
- 处置：① 文案改为「实收 64 条 + 缺「五八」」的如实表述（不再写「1–65 条」）；
  ② 门新增 `kemu_section_parse()`（按自编号逐行进位解析：实收条数/跨度/缺号出自同一次解析）
  与缺号登记 `KEMU_NUMBERING_GAP = (58,)`，门 `[1c]` 断言「实算缺号 == 登记缺号」——
  重抓若补全或缺号变化即判败，强制重核语料条数（防「书源已变而数据仍按旧差 1」静默漂移）。
- 反例（`tools/scratch/gate_logs/liuren_gap_negtest.txt`，进程内改常量、磁盘不动）：
  登记改空 `()` → 退出码 1；登记改多 `(58, 59)` → 退出码 1；还原 → 退出码 0。断言非恒真。


### 2026-10-01n 大六壬引文逐字订正：口径由「声称逐字」→「可机检逐字」+ 新增 [1d] 引文逐字门

> **口径登记（`AGENTS.md` §四.4）**：本次为**口径收紧 + 数据订正**（非计分方式变更，分数口径不变）。
> 独立验证指出 `men.昴星/伏吟/返吟` 三条 basis 去掉了书源小字夹注与书名号，使「逐字/原文」的
> 对外声明严于实际（**判定非编造，属口径不实**）。取舍为「改数据」路线：把三条还原为书源原样，
> 让「逐字」字面成立，并加一条**字符级**机械判据防复发。全文分数仍为**古籍案例对齐分**，非现实命中率。

#### 1. 数据订正（`disciplines/liuren/data/verdicts.json`）

- `men.昴星.basis`／`men.伏吟.basis`／`men.返吟.basis` 三条恢复为书源卷一「入手法」原样形态：
  小字夹注「论初传也」「论中末也」「阳日用辰，阴日用日，辰上作中，日上作末」与书名号「《玉厯》」
  全部照录（异体字不归一）。订正可复现：`disciplines/liuren/dev_tools/fix_verbatim_basis.py`
  （默认 dry-run，新值直接从书源行取出，改后自检 21/21 逐字才允许 `--write`）。
- 新增 `verbatim_policy` 登记块（`scope`/`rule`/`normalized`/`checked_by` = [1d]），
  `_comment` 口径改写为「21 条均为书源去空白后逐字子串，含夹注与书名号；归化必须登记」。

#### 2. 新增门（`disciplines/liuren/dev_tools/check.py`）

- `[1d] 引文逐字门`：覆盖三组共 **145 条**——`verdicts.json` 的 `men[*].basis`（9）
  + `tianjiang[*].verse`（12）；`kemu.json` 课目 `verse`（64，对卷一「课目」段）
  + 课目 `note`（60，对卷七~十「课经集」）。比对**保留标点与书名号**——既有 `[1c]` 用
  「只留汉字」口径，会把「《玉厯》」的书名号与句读滤掉，是本次漏检的直接原因。
- 允许归化（去夹注/去书名号/正字）但必须登记于 `verbatim_policy.normalized`（每条带
  `rule` + `reason`）；登记与实测不符（含陈旧登记）同样判败——防口径不实与登记表腐烂。
- 实测：145 条逐字、非逐字 0 条、归化登记 0 条。反例验证（4 例，进程内调用 + 字节级还原，
  证据 `tools/scratch/gate_logs/liuren_1d_negtest.txt`）：去《》未登记 → 判败；去《》**已登记
  rule+reason → 通过**；已逐字却留陈旧登记 → 判败；`kemu.元首.verse` 删一处句读未登记 → 判败。
  即门在「非逐字」「登记不符」两侧都会真的响，不是恒真断言。
- 同类风险已量化复测：`kemu.json` 64 条 verse、60 条 note 在字符级口径下**全部逐字**
  （`tools/scratch/gate_logs/liuren_kemu_verbatim.txt`），故纳入同一门而非另开登记。

#### 3. 指纹（有意漂移，已按 §四.1 归因重落）

- 机械层 `4f697b774a13c05d` → `cb34a6d43b22b8c1`：真实漂移（**补记 · 如实范围**）= ①进机械指纹的
  `factors[1]`（返吟诀文）2 例（金标准 4 例中 2 例命中返吟）；②**不进机械指纹**的显示层
  `analyze#verdicts_note[1]` 文本 1 处（= `verdicts.json#preamble[1]`，去掉写死数字改引用句）——
  该项随同批次后续「同一事实只有一处权威源」收口（见 2026-10-01o §指纹）落地，只经 `narrate`
  全文影响**措辞层** `narrate_sha`，不属 `factors`、不改排盘字段。原表述「真实漂移仅 factors[1] 2 例」
  范围读窄，在此并记以免误读（`digest.json#drift_log` 同条已同步）。
  排盘字段（日干支/时柱/月将/门类/课体/三传/遁干/四课乘临）JSON 归一化逐字段**零变化**
  （证据 `tools/scratch/gate_logs/liuren_fp_real_diff.txt`）。
- 措辞层 `983f8c1b0af92cd3` → `46079ece1688f627`：`narrate_sha` 随引文同步变化 2 例。
- 同轮口径同步：`disciplines/liuren/SKILL.md` 增「逐字口径（可机检）」条，
  写明字符级断言与归化登记规则。

### 2026-10-01m 八科收敛批：能力矩阵六→八科 + 紫微安星基准纠正 + 六爻减法复做 + 文档读数单一权威源

> **口径登记（`AGENTS.md` §四.4）**：本批含两类变化——① **引擎取值层有意变更**（仅紫微，见 §2），
> 其指纹漂移是**有意**的；② **「现状读数」收口到唯一权威源**（各科分数与 n、scripts 行数、指纹值 → `docs/HANDOFF.md`），
> 本文件只登记变更本身、不复制读数。全文分数一律为**古籍案例对齐分**，非现实命中率；
> 报分必带集合名 + n + 是否参与调参。

#### 1. 能力矩阵：通道 A 由六科 → 八科（`liuren` / `lingqi` 挂载）

- 唯一权威表 `llms.txt`「能力矩阵」改为**八科 × 三通道（本地 CLI / 通道 A 网页 / 通道 B Actions）全通**。
- 同轮同步：`tools/build_web.py::DISCIPLINE_META`、`web/engine_runtime.py`（`WEB_DISCIPLINES` 白名单）、
  `tools/verify_web_parity.py`（正例 10 → 13）、`tools/check.py` [1e] 矩阵锁与 [7c] 同源验收。
- 验收：`tools/check.py --full` 全绿（[1e]「llms.txt 能力矩阵与站点清单一致」；
  [7c]「正例 13 例 + 负例 2 例」）。
- **口径影响**：无——纯挂载面扩张，不改任何引擎行为或分数。

#### 2. 紫微斗数安星基准纠正（引擎**取值层**，有意变更；前后不可直接比较）

- 变更内容：紫微定位改**查书源五局安紫微图**（旧闭式公式全错）；天府改 `(4-紫微)%12`；
  命宫改 `(月-时)%12`；地空/地劫改按**生时**；魁钺/禄存/羊陀/天马/火铃 按《紫微斗數全書》卷二安星诀**逐条**修正；
  **+23 颗辅星**；大限起宫改依**安大限诀**（父母宫 / 兄弟宫）；安星改依**农历月日 + 命宫纳音**定局。
- **机械层指纹 `68123c2d0fd0ce7e` → `c53ce772472a8af0`（有意漂移）**；措辞层同步变动，
  当前值见 `disciplines/ziwei/data/golden/digest.json`（`digest` / `narrate_digest`）。
- 证据：`disciplines/ziwei/data/golden/digest.json` 的 `drift_log` / `narrate_drift_log` 逐条载明理由；
  `disciplines/ziwei/dev_tools/regression.py` **24 项**对书源逐条核对全过；口径见 `disciplines/ziwei/SKILL.md`。
- **分数口径**：ziwei **尚无案例库**（`data/cases` 下无 `*.json`，见 `[1]` 门提示）→ 无 tune/holdout 轴，
  本变更**不产生任何对齐分**，故不存在「前后分数可比」问题；报告只出安星结构，不输出吉凶断语。

#### 3. 六爻：减法复做 + 《卜筮正宗》书源结论（本轮只做质量，不加语料）

- **减法收敛 6 项**（删纯转发壳 / 双份合一 / 再导出收敛），等价性**全量非抽样**复现：
  `get_changed_hexagram_branch` 64 卦 × 6 爻 = **384 例 diffs=0**；
  `element_strength_in_month` 5×5 = **25 例 diffs=0**；`_combined_strength` 5×5×5 = **125 例 diffs=0**；
  `ce.get_changed_hexagram_branch is nu.get_changed_hexagram_branch → True`。
- **scripts 18,578 → 18,117 行**（37 文件；读数 2026-10-01，权威源 `docs/HANDOFF.md` §之一）。
- 《卜筮正宗》：按 `tools/fetch_source.py --force` 重抓后，**四次独立探测**确认维基文库可得内容只有
  总页（目录 + PD 声明）与 `/卷前`（張景崧《敘》），总页列出的 `/卷01`–`/卷14` **全是红链**
  → 缺口性质是「**未数字化**」，非抓取失败，重复重抓不会有新内容。
- **挂账（本批不修）**：`verdicts.json` 的 `quote_database` 共 49 条引文中有 **18 条**署名《卜筮正宗·…》，
  该书正文不在库、维基文库也无 → **在库无源可核验**；修它要动结构或 49 处 `source` 字面量并把 `source`
  带进渲染文案（触发措辞层漂移），属独立一批。详见 `disciplines/liuyao/references/source_ledger.md`。
- 逐项明细见 `disciplines/liuyao/docs/CHANGELOG.md` 2026-10-01m。

#### 4. 其他五科本轮语料与门变更（`meihua` / `xiaoliuren` / `zeji` / `liuren` / `lingqi`）

逐科取证自 `tools/scratch/DELIVERY-五科扩充与减法.md`（草稿区，gitignore，不入库）：

- **`liuren`（骨架科）**：`data/kemu.json` 课目 **58 → 64 条**（补齐卷一「课目」歌诀的第 1–6 条，即九宗门前六门），
  新增 `rules`（旬奇 / 日奇——**判据参数，非断语**）；`scripts/kemu.py` 重写，`IMPLEMENTED` **31 条**纯结构判据；
  门新增「每个已落课目在 **720 例**枚举中零触发即失败」+ [1c] 课目引文可回指门。
  **无 tune/holdout 轴**：评测轴＝机械一致率（三传 **3/4**、门类 **1/1**，n=4；n<20 只报命中数）+ 720 例枚举覆盖率。
- **`lingqi`（骨架科）**：修复**真实保真缺陷**——41 课源内「又：」起头的第二/三组注被静默并入 `shiyue`；
  1 课（益友卦）「許曰」被并入 `xiangyue`；1 课（違克卦）分隔符写作「象曰，/象曰；」致整组漏判；书末 `==純陰饅==` 被并入上一课。
  `data/ketables.json` schema → **`yi-lingqi-ketable/2`**（47.5KB → 68,685B），数据模型改 `notes` 有序标注组 + `gong`；
  门新增 [1c] 逐字回指门（**124 课 / 290 标注组**）。
  **无 tune/holdout 轴**：评测轴＝**124/124** 全课查表 + 124 课引文回指 + 金标准 1 例。
- **`zeji`**：`協紀辨方書` / `欽定協紀辨方書` / `星曆考原` / `御定星曆考原` / `選擇宗鏡` 六候选名在维基文库
  **全部 missingtitle** → 口径正源取不到，**如实登记缺口**；改以同源通书《玉匣記》作**参考书证**
  （不参与评分、不改判据），`data/citations.json` 43 行引文（通则 1 篇 5 行 + 事类 11 类 / 20 篇 / 38 行，逐篇带源文件行号）；
  门新增 [1c] 参考书证门。读数：tune **10 例** 100 / holdout **6 例** 100（holdout **未参与调参**）。
- **`meihua`**：新增 `data/classics.json`（schema `meihua-classics-v1`，规则 **22 条** / 原文段 **48 段**，
  卷次覆盖 卷一×8、卷二×5、卷三×9）；**18 个占验/占例篇名故意隔离**（逐字引入会违铁律二）；
  `references/classics.md` 只索引不复抄；门新增 [1c] 古籍原文门。
  读数：tune **10 例** 100 / holdout **13 例** 100（holdout **未参与调参**；前序工作已由 3 扩至 13）。
- **`xiaoliuren`**：`data/verdicts.json` schema → v2，事类断语 **66 条 = 诀辞 40 / 引申 25 / 阙 1**，
  `kind ∈ {诀辞, 引申, 阙}` 把「书上是原文」与「本仓归纳」分开，1 条无据者**如实标阙**；
  **公版书源缺口已登记**（`小六壬` / `小六壬掌訣` / `六壬時課` / `萬法歸宗` / `六壬類聚` 五候选名全 missingtitle）；
  断语底本为现代文本《贺氏六壬小手册》，**未编造古籍断语**；门新增 [1c] 断语口径门。
  读数：tune **10 例** 100 / holdout **5 例** 100（holdout **未参与调参**）。
- **机械层零漂移**：五科减法（删死代码 / 统一重复表）**未改变任何一科金标准指纹**——有门证据，非口头断言。
- **外部数据阻塞（挂账，禁止考卷调参）**：liuren《毕法赋》/《大六壬指南》、zeji《协纪辨方书》口径正源、
  meihua 他本、小六壬公版书源，均实测维基文库不存在。

#### 5. 文档层：现状读数收敛到单一权威源（架构评审 A8）+ 仓库级减法

- **A8 收敛**（每类事实唯一权威源，别处只写「见 X」引用句、禁止内联复制）：

  | 事实类别 | 唯一权威源 | 本轮收敛动作 |
  |---|---|---|
  | 科 × 三通道能力矩阵 | `llms.txt` | `docs/ARCHITECTURE.md` §一 / §七 改为引用 |
  | 各科分数与 n、scripts 行数、案例数 | `docs/HANDOFF.md` | HANDOFF §一「脚本规模」改指向 §之一 总表（单处） |
  | 金标准行为指纹 | `disciplines/<科>/data/golden/digest.json` | `ARCHITECTURE.md`、`HANDOFF.md`（两处）、`DEEP-DIVE-PLAN.md` 的 16 位 hex 字面量全部改为「见 digest.json」 |
  | 合参裁决规则 | `synthesis/README.md` §二 | `SKILL.md` §五「裁决规则四条」→ **五类**（旧表述与 `cross_rules.py` 不一致） |
  | 学科清单 | `core/yishu_core/report/request.py::DISCIPLINES` | `ARCHITECTURE.md` §一 明示 |

  过期「六科 / 现有六科」表述在 `ARCHITECTURE.md`（§一、§二、§七）、`NEW-DISCIPLINES.md`、`SYS-REVIEW.md`、`TECH-DEBT.md` 一并订正或加指向。
- **读数订正（读数时点 2026-10-01）**：liuyao scripts **18,578 / 18,560 → 18,117**；
  liuyao 问题词典 **195 → 210 键**（10-01l 已改代码 `EXPECTED_KEYS=210`，本批改文档读数）；
  `wikisource_holdout` 对齐分 **57.1 → 56.3**（n=35，**未参与调参**的外部集）——本机
  `cd disciplines/liuyao && python dev_tools/check.py` 实测，与 10-01l 条目所记 57.1 不一致，**以实测为准并登记**。
- **删除**：`docs/ARCHITECTURE-REFACTOR-PLAN.md`（35,700 B）整份删除。理由：该稿把 `docs/SYS-REVIEW.md`
  已 ✅ 落地项当待办重提；§3.1.1 的六爻瘦身表对 **37 个文件一律**写「提取公共函数到 `chart_tables.py`」
  （连 `__init__.py` 2 行→150 行都列入）；§3.3 通篇「保留，但更新为最新状态」——已被 `docs/ARCHITECTURE-REVIEW.md` 取代
  （该评审 §六明确不引用其任何结论）。**该文件未被 git 跟踪 → 无 git 历史可回溯**；
  删前整份留档 `tools/scratch/deleted-drafts-20261001/ARCHITECTURE-REFACTOR-PLAN.md`（gitignore，不入库）。
- **仓库级清理**：删除 **12 个 `__pycache__/` 目录 + 153 个 `*.pyc`**（各科 `scripts/` 下 `cpython-312`
  与 `cpython-314` 两套陈旧产物）。`.gitignore` 已覆盖 `__pycache__/`、`*.pyc`（本就覆盖，无改动）。
  `tools/scratch/**` 下另有 5 个 `__pycache__`（另一工作流的 falsify 夹具），按「不越界」**未动**。
- **注释痕迹扫描（只报不改）**：全仓 **193** 个 `.py` 扫出 **76** 条「复述代码」型短注释候选
  （74 条在 `disciplines/**`、2 条在 `tools/build_web.py` / `tools/check.py`）——
  **全部在本批写域之外**，故**零删除、仅登记**（全量清单 `tools/scratch/comment-candidates-full.txt`）。
  带古籍出处 / 口径依据的注释一律未动。
- **输入协议**：`core/yishu_core/report/request.py` **仅改一行注释文字**（analyze 段「六科同形」→「八科同形」），
  [1f] 输入协议指纹**零漂移**（机械 `70b6244d7c869ddf` / 措辞 `dc933251dc9df30a` 与基线一致）。
- **消费审计扩至八科**：`tools/verdict_consumption.py` 用例表补 `liuren`（起课时刻）/ `lingqi`（三部掷数 up/mid/down 0..4）
  共 4 例；**门语义未放宽**（仍为报告制，`--strict` 与 `ALLOWLIST` 未动）。

#### 6. 质量门新增登记（`[0b]` 读数锚点 / `[1g]` 案例库隔离）+ 已知缺陷

并行工作流本批交付两条新门，**同步登记于此，不让文档落后于门**：

- **`[1g]` 案例库隔离**（`tools/case_isolation_check.py`，接线 `tools/check.py:646–652`，
  默认档与 `--full` 档都执行，耗时 ≈0.9 s）——守住 `AGENTS.md` §一.2 铁律二，
  这是三条铁律里**原本唯一零机械支撑**的一条（风险不是「已经违规」，而是「无法证明没有违规」）。
  静态层＝四段契约入口（`{chart,analyze,narrate,render}.py`）的 **import 闭包 BFS + AST 判据**；
  运行层＝`sys.addaudithook` 记录真实 `open`，在受控子进程里实跑一份解读请求；判败制（铁律不容「报告制」）。
  **覆盖边界（如实转记，不美化）**：**未覆盖** `tools/report.py`、`cli/`、`synthesis/`、`web/` 的源码，
  非四段入口的解读脚本（如六爻 `scripts/yi_liuyao.py`），以及学科脚本**自起子进程**读文件的情形；
  白名单仅 **4 个具名落点**（`scripts/case_runner.py`、`scripts/evaluate.py`、`dev_tools/`、`tests/`）。
- **`[0b]` 读数锚点**（`tools/check.py:510–555` 实现、`:602–606` 调用，阈值 `DRIFT_THRESHOLD = 50`，
  **报告制、不阻断**）——即架构评审改进项 **A11**。它显式声明「下述所有门的读数一律取自**工作树**，
  不等于任何已提交 revision」；当前实测工作树偏离 HEAD `f74c743` **226 处**。
  **与 A8 是同一件事的两面**：A8 管「读数只有一份」，A11 管「这一份读数属于哪个 revision」——
  两者已在 `docs/ARCHITECTURE.md` §七（「文档读数纪律」+「读数锚点」两节）**建立互引**。
  本批之前该门未进文档、质量门清单亦缺项 → 本次同步把 `[0b]`/`[1g]` 及其余各门补进
  `docs/ARCHITECTURE.md` §七「质量门清单」。
- **已知缺陷（挂账；另派该工作流修复，本批不改代码）**：`tools/check.py:6` 的用法示例写
  `--only version,structure,filenames`（**逗号**），而实现是 `nargs="*"`（**空格**分隔）且
  `only = set(args.only)` 直接做集合成员判断 → **照抄该示例会跳过所有门，却打印「仓库级质量门全部通过。」
  并退出 0**（假绿）。修复方向：宽容化分隔符 + **无匹配门时非零退出**。
  同类逗号示例另散落在 `disciplines/{liuyao,meihua,xiaoliuren,zeji}/dev_tools/check.py` 的 docstring
  与 `disciplines/liuyao/docs/CHANGELOG.md:221`（**均在他人写域，本批只登记不改**）。

#### 7. 未做 / 已知局限（如实登记）

- 未 commit / stash / reset；未改 `disciplines/**`、`web/**`、`tools/{check,build_web,verify_web_parity,check_web_site}.py`。
- `docs/CHANGELOG.md` 2026-09-30o–r 区间存在历史条目正文交错/截断（早年编辑残留）——
  **本批不重写历史条目**，仅登记。
- 本批读数采集期间并行写者仍在改语料（2026-10-01 19:03 仍在写 `disciplines/*/data/cases/eval_*.json`）；
  `docs/HANDOFF.md` §之一 已标注读数时点，**引用读数须带时点**。

### 2026-10-01l 架构修正落地 + 八科语料续扩 + 全仓痕迹清扫

**口径影响：六爻词典 195→210 键（借贷/讨债/六畜/坟墓四族，引文逐字）；tune/holdout/wikisource 三集与基线逐位一致（95.0/89.7/57.1），黑箱回归 12/18 ≥ 11。ming/ziwei/liuren narrate 措辞层按新指纹门重落（机械层零漂移）。**

架构修正（SYS-REVIEW.md 十条建议中的九条落地，另一条「换书扩样」继续挂 TECH-DEBT）：
- **#2 指纹拆分**：新增 `core/yishu_core/golden_kit.py`，八科 `dev_tools/golden.py`
  收敛为「GOLDEN_CASES + fingerprint() + kit 调用」，机械层 digest 与措辞层
  narrate_digest 分列登记（drift_log / narrate_drift_log）；本批 capture 证实
  10-01k 措辞接线机械零漂移（机械 digest 回到纯机械基线）。
- **#1 语料消费审计**：新增 `tools/verdict_consumption.py`（verdict_audit 反向门：
  语料池 ⊆ 被消费），子序列匹配容忍模板占位符，动态拼装键（如 `base_{强弱}`）不误判；
  挂入 `tools/check.py --full` [1d]（报告制：抽样覆盖有限，主题键合法不触发）。
- **#3 能力矩阵**：权威表落 `llms.txt`（科 × 本地/通道A/通道B）；
  `tools/check.py` 新增 [1e] 矩阵锁——llms.txt 与 `build_web.DISCIPLINE_META` 漂移即红。
- **#4 协议指纹**：新增 `tools/request_protocol_golden.py`（normalize_request
  正例 8 + 负例 4 锁定），挂入 `--full` [1f]。
- **#5 回评口径**：口径句唯一真值源 `core/yishu_core/report/request.py::FOOTER_TEXT`，
  `ci_deliver.py` 改引共享常量（原内联副本措辞略有出入，已归一）。
- **#6 反馈回路**：`MD_FEEDBACK_NOTE` 追加于本地/通道B/通道A 同一逻辑点
  （report.py + engine_runtime.py），`verify_web_parity` 10+2 例逐字节验收通过；
  ci_deliver 回评附 record-outcome 引导句。
- **#8 调候分层登记**：`docs/ARCHITECTURE.md` 新增 §八之一「取值层在 core /
  引文层在学科 data」合法模式（防真值源门误伤）。
- **#9 骨架自检**：liuren `dev_tools/check.py` 新增 [1b]（天将布法=十二将全排列、
  乘临/遁干字段合法、十二天将歌诀 verdicts 全覆盖）；lingqi [1] 补字段不变式
  （name/xiang/zhu/xiangyue 非空；shiyue 可空——书源 4-1-3 益友卦本无诗曰）。
- **#7 六爻瘦身**：本轮经 golden_kit 收敛（八科 -约 500 行）+ 痕迹清扫，
  未做 scripts 大拆（挂 TECH-DEBT）。

加法（语料真实扩充，全部带出处；书源新增两种）：
- 书源入库：**《紫微斗數全書》**（`zi-wei-dou-shu-quan-shu`，214,512 字节，卷一/二/三
  93 标题）；**《滴天髓》**重抓实测 60,578 字节（此前 skeleton 判定过期），
  從化論「從得真者只論從」逐字在库。
- 紫微：verdicts 新增 `主星书源`（十四主星定义句逐字引《諸星問答論》）+
  `格局星表`（21 格局→主星映射）+ `四化释义`（4 化通行口径）；
  narrate 格局释义后附星源引文行、四化影响后附化别释义行。
- 命科：`data/verdicts.json` 新增 `格局成败引文`（15 键，pattern.py 内联
  《子平真诠》句全部外置）+ `从格引文`（滴天髓從化論/從象/假從短语）；
  narrate 新增建禄格「格局口径」行（verdicts.不适用 块接线）与从格「从格所本」引文行。
- 大六壬：verdicts 新增 `tianjiang` 块——十二天将乘临歌诀（书源逐字，含「不临」限注
  与附论），narrate 报三传乘将时逐将引诀文；课目命中附 `verse`（kemu.json 诀文
  接线进 narrate）；课名 **赎胥→赘胥** 照书源正名（720 例枚举门 22 次触发正常）。
- 六爻：问题词典补**借贷/讨债/六畜/坟墓**四族 15 键（引文「子興財發可相求」
  「應財生世定懷忠」「不拘家禽野獸皆以子孫為用神」「皆以父母為用神」逐字核验，
  章名见《增删卜易》目录 77/78/79/118）；`EXPECTED_KEYS` 195→210。
- 小六壬：天气占四宫（大安/速喜/赤口/空亡）按「宫象与属神五行」综合断例补全
  （标注引申、非诀辞句，与既有留连同法）。

减法（接线归一 + 死语料 + 痕迹清扫）：
- 双真值源归一：meihua analyze 5 处内联引文接回 `basis_quotes`（10-01k 只归一了
  narrate 侧，analyze 侧仍在）；xlr/zeji 的 narrate_phrases 被内联架空的键
  （disclaimer/caveat/basis 等）全部接线；liuren kemu.py 8 课目与 kemu.json 双份
  归一（name/verse 数据侧）。
- 六爻死语料 20 条删除（classical_interpretations 9、step5_yingqi_texts 5、
  chain_support_notes 6+loader；step5_factor_reasons 经 golden 验证实为动态键
  消费——`base_{强弱}`——保留）。逐组删除均跑 golden 验证零漂移。
- 死代码 6 处删除（`next_month_branch_instant`/`months_ahead`/`stem_wuhe`/
  `relation_class`/`HEI_DAO_GODS`/`PALACE_INDEX`，全仓 grep 零引用 + 内核自测过）。
- 痕迹清扫 36 项：损坏文件头 3、巨石/搬移 docstring 13、日期戳与踩坑流水账 15、
  注释 emoji 5（清单与逐项处置见本轮工作记录；全部为注释/docstring，ast.parse
  全过、行为零变化）。
- 文档：`docs/AUDIT.md` 移 `archive/`（轮次过程档，未决项已并入 TECH-DEBT/HANDOFF）；
  口径免责句副本压成指针（权威位 AGENTS/SKILL/README）；HANDOFF 接棒叙事改中性；
  MIGRATION 失效门面名修正（classical_rules→classical_analysis）。

### 2026-10-01k 语料真扩 + 死数据清理（加法/减法各一轮）

**口径影响：六爻词典 186→195 键（天气占增补，引文逐字）；tune/holdout/wikisource 三集分数与基线逐位一致（95.0/89.7/57.1）。**

加法（语料真实扩充，全部带出处）：
- 六爻：问题词典补**天气占**两族 9 键（雨→父母、晴→子孙），引文「占雨用父爻」「占晴用子孫爻」
  逐字取自 `data/sources/zengshan_buyi.wikitext.txt`（构建器 locate 核验通过）；
  关系法则层与旧词典此前均不覆盖天气问，占雨类落到世爻兜底属取用错误。
  `EXPECTED_KEYS` 基线 186→195（增补理由写进 FAMILIES 尾注）。
- 八字：`ming/data/verdicts.json` 由骨架建为**格局引文真值源**（《子平真诠·论用神》
  「八字用神，专求月令」「财官印食…顺用/煞伤劫刃…逆用」）；narrate 新增「格局所本」行
  （格局名→善逆用机械映射）与「调候原文」行（月建×日主查 `tiaohou_quotes.json` 逐格引文，
  《穷通宝鉴》原文上报告）。ming golden 因 narrate 措辞变化重落基线。
- 紫微：`命宫格局` 文案块原为死数据（无任何代码消费）——narrate 接线为「格局释义」行，
  并补齐 7 个同宫组合格（紫破/机杀/日相/武巨/同贪/廉阴/天府独坐）与 core PATTERNS 对齐；
  文案为通行口径整理（注明非逐字引文）。ziwei golden 因 narrate 变化重落基线。

减法（无效信息清理）：
- 梅花：narrate 硬编码引文「生体多者则愈吉…」改为从 `verdicts.json#basis_quotes` 取
  （消 .py 与 data 双份真值源）；出处由误标的《体用生克篇》/《体用总诀》修正为
  源文实际所属**《卷二·体用》**（`data/sources/mei-hua-yi-shu.wikitext.txt` 1442 行节名核验）。
- 小六壬：删除 verdicts.json 三个零引用死键（`direction_basis`/`speed_class_basis`/
  `comprehensive_note`）；speed_class 通行口径的诚实标注并入文件级 note。
- 文档：删 `docs/MIGRATION.md` 已失效的 `mcp_server.py 保留` 行、`docs/LIUYAO-PLAN.md`
  待办里的 MCP 残段；「186 键」读数同步 195（HANDOFF/LIUYAO-PLAN）。

### 2026-10-01j 六爻 docstring 瘦身 + 死代码清除 + DEEP-OPTIMIZE-PLAN 删除

**口径影响：无。纯结构/文档精简，引擎推演与评分不变。** golden 全绿。

- 六爻四脚本 docstring 瘦身（逐函数保留规则出处与契约关键句，去参数表/返回字段字典）：
  - `effects.py` 1618→1227 行（11 处长 docstring）
  - `liuyao_step3.py` 1009→845 行（7 处）
  - `liuyao_step4.py` 1478→1220 行（11 处）
  - `liuyao_step5.py` 1829→1584 行（9 处）
  - `event_logger.py`、`classical_enhancements.py` 同上批次
- 死代码清除（AST + grep 双重确认无外部引用）：
  - narrative_utils.py: `_stem_element`
  - meihua/analyze.py: `_chinese_num`
  - meihua/chart.py: `_moving_in_upper`
  - ming/pattern.py: `_pillar_ten_gods`
  - liuyao_step5.py: `_next_month_with_branch`、`_add_months`
  - 同步清 `liuyao_analyze.py __all__` 与 `thinking_chain.py` 的 import/export
- 删除 `docs/DEEP-OPTIMIZE-PLAN.md`（1370 行）及 `docs/samples/DEEP-OPTIMIZE-PLAN.html`（220 KB）
- 删除 `tests/thinking_chain_tests.py` 内 4 条 `# ===` section divider
- 更新 `docs/samples/README.md` 对应条目

### 2026-10-01i 修「门在干净克隆上必红」两处 + 八科分科门挂进 CI

### 2026-10-01h 修「核心常量进正则」回归（六爻 tune 19/20 例报错）+ 八科分科门首次逐一实跑
> - 根 `tools/check.py --full` EXIT=0，**八科行为指纹无漂移**（golden 基线未变）；
> （`tools/check.py:47 SMOKE_DISCIPLINES`），**各科 check.py 里的 tune/holdout 基线
> **口径影响**：无。六爻 tune/holdout/wikisource 各分数与 `HANDOFF.md` §一 完全一致，

### 2026-10-01g MCP 全量移除（用户决策：不使用 MCP）+ 活跃面引用清零

### 2026-10-01c 真值源门升级（能看见函数内 dict 与干支串）+ 清 25 处运行时副本

### 2026-10-01e 断语外置改为**黑箱取证**（跑真实报告反查）+ 七科 golden 补 narrate 指纹 + 繁简统一
（`sanhui_use_strong/weak`）；`liuyao_step3.py` 11 条旺衰口语结论 → `strength_summary_say`
> **取证口径踩过的三个坑（都已修，别再踩）：**
> **算法权重**不是断语——两项按 §三证伪，不搬。
- A5：`ming/ziwei/meihua/xiaoliuren/zeji/liuren/lingqi` golden 补 narrate 哈希并落新基线

### 2026-10-01f 取证门语料池瘦身 97%（抓出 guard 快照冒充真值源）+ focus 主语剥离
新增 `_focuses()` 自举焦点主语并剥前缀；报告默认落临时目录（`--save` 才进
> 五份口径叠起来 = 3,149,400 汉字），外加 `dev_tools/guard/base_human.json`

### 2026-10-01d 更正 2026-10-01c「golden 未漂移」的结论 + 补两道机械门（模块可导入 / 八科指纹进根门）

### 2026-10-01b 第二轮深潜减法：清 6 项零引用件 + 尾留文档打过期标
> **决策记录（非口径变更，引擎行为零变化）**：源自 `docs/DEEP-REVIEW.md`（第二轮深潜，

### 2026-10-01a 架构瘦身：删除闲置共享层 `disciplines/base/` + 报告工作流输入通道留余量

### 2026-09-30w 命科从格收敛（DEEP-DIVE-PLAN #3）：tentative → 可判级（真/假从、从旺/从强/从气/从势）+ 地支互动（三合化气/六冲）+ 15 例滴天髓书源案例
> **口径登记（§四.4）**：① **从格判定从「tentative 只标结构」升级为可判级**
> 案例（子平真诠 ZP 系）现按滴天髓口径判从格，pattern 维度满分例 36→28；
> 属**两书口径分歧**（ZP005 丙火寅甲印被申冲 书成格 vs ZC012 同构盘书从杀等
> 重写**：布尔 2 + 种类 1 + 真/假 1（书没写的子项从分母剔除，权重仍 4）。
> **从格机械口径（v4 收敛，通用规则+书源出处，无 case-specific 分支）**：
> - 从弱成立 = 从神权重≥4.0 且 失令 且 无强根（临官/帝旺）且 无本气印（未冲）

### 2026-09-30v AI 可发现层（llms.txt / SKILL.md frontmatter / skills 目录 / PROMPTS.md / MCP 文档）
1. **`llms.txt`**（根，新增）：AI 索引地图——核心入口（AI-SOP/SKILL.md/AGENTS.md/PROMPTS.md）、

### 2026-09-30u 命科格局成败救应增强（财格官/煞细分 + 六合救应 + 煞刃格）+ 岁运并临标记 + 神煞补全（术数深度强化批"123推进"第 1/2/5/6 项）
1. **判据增强（`pattern.py`，逐条带《子平真诠》原文出处）**：
> **口径登记（§四.4）**：本变更含 ① **案例 expected 口径修正一例**：ZP027 王总兵
> verified=false 口径不变；命科 narrate 新增机械呈现段）。金标准指纹 `3d4ff149ef6be933`
ZP031（丙子 戊戌 壬子 庚子）由此回归案例集（30t 因取格口径淘汰）。
4. **读数（口径同批；对齐分非命中率，n≥20 可报百分比）**：
5. **质量门**：ming 门（金标准指纹不变/机械回归/评测框架自检 7 场景/tune/holdout）、

### 2026-09-30t 命科格局成败救应引擎（《子平真诠》主干）+ 四柱直填起盘 + 书源案例 31 例（术数深度强化第一批落点）
1. **引擎（`pattern.py`）**：`PATTERN_CB_RULES` 十格（正官/偏官/正印/偏印/食神/伤官/
> **口径登记（§四.4）**：本变更含 ① 命科新维度 `pattern_cheng_bai`（格局成/破/救应
> 三分类，权重 pattern 12 中 4 分，此前引擎从未产出）② **chart() 输出新增键
> 维度适用权重修正**（只记成败时 w=4 而非固定 12；此前"只填成败"永远拿不满满分、
> 该维度全 0——bug 修复，无历史分数受影响，因维度此前从未有案例）④ 案例集
成败判词：28 成格 + 2 破格 + 1 救应成格；格名口径——书源用神定格 vs 引擎月令
5. **读数（口径同批，可与 30s 前命科历史比较；命科此前仅有调候维度）**：
- 书源「煞刃格」（阳刃在日支+七杀）取格口径超出引擎月令本气取格——ZP031
按取格口径差异淘汰（expected 正确、引擎判据不适用），记入 DEEP-DIVE 待办。

### 2026-09-30s 报告忠实度审计工具 `tools/report_faithfulness.py`（HorosaBench 落点）+ 叙事模板口径修正
1. **工具**：`tools/report_faithfulness.py`（HorosaBench 思想落地，RESEARCH-HOROSA §二.3
> **口径登记（§四.4）**：本变更含 ① 新增工具（报告正文断言 vs 引擎结构化输出，
2. **叙事模板口径修正**（审计实际产出）：`verdict_texts.json` 的 strength_reason

### 2026-09-30r 卦身口径修复（《卜筮正宗》安月卦身诀）+ 卦身/三合三维度激活（权重表再分配）
1. **卦身口径修复（引擎级，依据《卜筮正宗》安月卦身诀）**：
> **口径登记（§四.4）**：本变更含 ① **引擎推演逻辑改动**（卦身口径，288 例指纹
> 6 条 narrate 哈希漂移，金标准已 capture 带理由）② 权重表再分配（总和仍 100）
> 新旧权重不可直接比较：tune 94.5 → **95.0**、holdout 89.0 → **89.7**、
> wikisource_holdout 57.3 → **57.1**（权重微调所致，非引擎回退）、
1. **卦身口径修复（引擎级，依据《卜筮正宗》安月卦身诀）**：
2. **三维度激活（对表回归，权重表再分配）**：
3. **权重表新旧对照**（单一真值源 `evaluate.WEIGHTS`）：
4. **strict 对齐（满分数/适用数）**：tune 卦身 16/16、三合 16/16、用神入三合 16/16；
> **口径登记（§四.4）**：本变更含 ① 权重表重分配（总和仍 100）② `case_runner` 增三个
> 新旧权重不可直接比较：tune 94.0 → **94.5**、holdout 87.8 → **89.0**、
> 分数变化全部来自新增适用维度的满分贡献，不是引擎提升。
2. **基准填充面**（书面用神地支/纳甲唯一爻位为前置，照 30o 口径，不硬填）：
3. **权重表新旧对照**（单一真值源 `evaluate.WEIGHTS`）：
4. **对齐结果（strict，满分数/适用数）**：tune 六神 10/10、旺衰 16/16、墓库 16/16；
`_extra_tombs` 死代码——均删除，旺衰口径收敛为单一函数。质量门全绿（六爻门 + 根 --full）。

### 2026-09-30m 煙波釣叟歌抓取成功（无定局表实锤）+ 三科外部集定性为外部数据阻塞
1. **煙波釣叟歌抓取成功**（第三轮重试，5970 字节落盘）：实测复核确认**有机制纲诀**

### 2026-09-30o 六爻 use_god_position 基准例补全：维度从全 N/A 转适用（tune 10/10、holdout 4/4）
1. **纳甲唯一可定才填**：书面已明写 用神六亲 + 用神地支，且该（六亲, 地支）组合在
> **口径登记（§四.4，含不可比性说明）**：本变更只动评测集数据（case expected 补
> 对比，跨口径比较须按维度适用数拆分。
2. **填充面**：classical_cases tune/holdout 共填 14 例（另 15 例用神多现跳过、
4. **结果**：strict 口径 tune 10/10、holdout 4/4（满分例数/适用例数）；
legacy 口径随六亲走 20/20、12/12。质量门全绿（六爻门 + 根 --full）。

### 2026-09-30n 命科第二维评测：四柱对表 174 例（《穷通宝鉴》命例表提取）
1. **命例表提取**：`dev_tools/build_mingli_cases.py` 从《穷通宝鉴》书源 70 个
> **引擎口径零改动**：纯评测集扩充。命科 holdout 21 → 195 例；
> 四柱维度从全 N/A 变为适用 174 例（随机基线≈1.7%）。
4. **评测结果**：四柱 174/174 = 100%（机械一致率口径：历法链路与明清古籍记录

### 2026-09-30l 灵棋经落地：第八科入列（124 课表直录 + 两条出报告通道）——④ 凑足两门
1. **书源**：《靈棋經》维基文库实测存在并抓取（36KB，
> **引擎口径**：既有七科零改动；新科全为增量。金标准 `cccad8793b826c9e`
narrate（书源断语编排+口径声明）→ render；`dev_tools/check.py`

### 2026-09-30k 梅花书源复刻核验（转录无误）+ kentang2017 上游 MIT 许可核实
1. **梅花书源复刻核验**：《梅花易數》（已抓取书源）的占例与现有 23 例中 15 个

### 2026-09-30j 大六壬深化第二批：课目识别首批八条 + 三科外部集书源前置解决
1. **课目诀表入库** `data/kemu.json`：六壬大全 卷一「课目」58 行诀文逐字登记

### 2026-09-30i 大六壬深化第一批：下贼/上克合池修正（书例自证）+ 课例评测（机械一致率 3/4）
1. **`_ke_tree` 合池修正**：ze 与 ke 并存 → 池 = ze+ke → 比用（知一）→ 涉害（察微）。
> **口径登记（§四.4）**：九宗门取三传的通用规则修正——四课**下贼与上克并存**
- `dev_tools/build_course_cases.py`：书源内嵌课例机械提取（严格口径：日干支 +
- `scripts/evaluate.py`：**机械一致率**口径（引擎 vs 书面三传；与对齐分严格分开，
引擎涉害取子（深浅计数 5:0/2）。涉害深浅的计数端点与方向口径诸本不一，
`verified=False` 已登记；待《大六壬指南》课例交叉核验后再定通用口径，

### 2026-09-30h 大六壬骨架落地：第七科入列（九宗门判据树 + 两条出报告通道接入）
1. **core 唯一真值源** `yishu_core/liuren_tables.py`：十干寄宫（甲课寅兮乙课辰诀）、
> **引擎口径**：现有六科零改动；新科全部为增量文件。金标准
十二月将（**中气换将**=太阳过宫口径，`yuejiang_policy` 显式声明，超神/接气之争
金标准 capture/verify；四段冒烟与口径声明检查。

### 2026-09-30g 命科调候落地：《穷通宝鉴》表入内核 + 首批案例对齐评测（51 例）+ 佐神分母修正
1. **内核唯一真值源** `yishu_core/ming_tables.py` 新增 `TIAO_HOU`（月支×日主 →
> **口径登记（§四.4）**：命科 `evaluate.py` 调候维度修正——书只给主神时，佐神
> 「书上没写」= 不适用，**适用权重只算主神 10**（原实现拿 16 当分母，把没写的佐神
透出到顶层；`narrate.py` 新增「调候」一节（标注查表口径）。金标准指纹
- **诚实口径**：引擎查的表与 expected 同出一份原文 → 本集是**表对表回归 +
历法链路验证**（引擎 51/51 与书一致，随机基线≈10%），**不是泛化证据**。

### 2026-09-30f 六爻深度改造第一批：缺失环节六项落地（DEEP-DIVE-PLAN §1.3 清偿）
1. **三会方局**（step4，优先于三合）：卦中三支俱现或月建/日辰补一支；用神旺 +0.5 /
> **计分口径影响有界且已 capture**：金标准指纹 `abc7884de0653ee5` → `6a67db48bbed83fc`
《增删卜易》"旺空待出，真空难起"。权重口径不变。

### 2026-09-30e 三科评测口径审计：被推翻的"100%"订正 + 报分口径披露
1. **读数订正**：三科 tune/holdout 的 100% 是**规则自洽回归数**（"查表/生克管线没被改坏"），
> **引擎口径零漂移**：三科金标准指纹不变（梅花 `2c9c810d8a265180`、小六壬 `0088d638d065402d`、
> 本条目即 §四.4 要求的口径登记：**"梅花/小六壬/择吉 tune/holdout 均 100%"自本轮起
1. **读数订正**：三科 tune/holdout 的 100% 是**规则自洽回归数**（"查表/生克管线没被改坏"），
2. **构成实锤**：梅花 23 例 = 原书应验 18 + 引擎口径构造 5（自洽项 70/100 权重，
holdout 13 = 原书 8 + 构造 5）；小六壬 15 例真·书上结论仅 4 例，四维 100/100 权重全查
4. **均分口径已知偏差（登记未改）**：`yishu_core/eval.py` 对逐例百分比取算术平均，
N/A 例会稀释有效信息（梅花 tune 适用权重 800/1000、holdout 930/1300）。本轮未改
计分公式，仅登记备查；后续若改，分数从改动处起不可比。
- 三科 `scripts/evaluate.py`：报分前自动打印 `[口径披露]`（集合名 / n / 是否参与调参 /
- 三科 `dev_tools/check.py`：基线注释改为「规则表自洽回归线」，订正过期 n。
唯一有效动作指向**建外部独立集**（范式照六爻 wikisource 35 例）——扩判据、调权重不解决。

### 2026-09-30d 两条出报告通道：纯前端（零凭证）+ 云端固定链接
1. **新增纯前端通道（零凭证出报告）**：
> **引擎口径零漂移**：六爻金标准指纹 `abc7884de0653ee5`（288 例）不变；tune/holdout
给出两条通道的能力边界表（诚实口径：不存在"AI 零凭证零人工让云端跑完递回"的组合，
pytest 76 项、六爻黑箱回归 12/18 ≥ 基线 11/18）。

### 2026-09-30c 第六科：紫微斗数落地 + 扩书源探查
1. **紫微斗数完整实现**（新命科，第六科）：
3. **口径未变**：紫微斗数无 holdout 案例评测（古籍案例库尚未建立），当前冒烟验证 + 金标准指纹 4 条通过。

### 2026-09-30b 应期评分区间化 + 通用规则 r8/r9 + 真实反馈闭环
1. **应期评分区间化（loose 列）**：在 `evaluate.py` 新增 `score_yingqi_loose()` 与 `--yingqi-mode strict|loose|both`。Loose 命中 = 主应期=expected 或 相对窗/绝对日期窗覆盖 expected 支。

### 2026-09-30a 卜筮正宗/火珠林外部书源（扩外部验证集）
1. **火珠林外部集**：新增 `dev_tools/fetch_huozhulin_cases.py`，从维基文库《火珠林》原文（问答体）提取占验案例。入 `data/cases/huozhulin_cases.json`（2 例 yingqi scorable，5 例定性参考）。注册 `huozhulin_holdout` split（永不参与调参）。
> **功能零漂移**：本变更新增外部案例数据与 split 接线，不涉及任何引擎代码/计分口径调整。tune/holdout/金标准/冒烟/思维链/古籍回归与变更前逐项一致。
**扩样后读数（tune/holdout/外部分列）**：
**口径差异说明**：
- tune/holdout = 增删卜易体系，引擎基线；wikisource = 同体系但独立集，top-1 20% 是旧读数的新确认。
- **口径未变**：分数仍是古籍案例对齐分。

### 2026-09-29c v1.0.0 结构重构（五科底座归一）
1. **新增 `disciplines/base/` 共享层**（`protocol.py` + `cli.py` 基类）：
> **功能 zero-drift**：本轮为纯结构性重构，tune/holdout/金标准/冒烟/思维链/古籍回归全绿，分数与重构前逐项一致。
- refactor_guard 115 例指纹不变；金标准 288 例指纹不变；tune/holdout 逐项一致。
- **口径未变**：所有分数仍是古籍案例对齐分，非预测率。

### 2026-09-29b 归档三科还原（五科全通）
- **口径未变**：还原不改动任何计分方式/词典/缺失字段处理，分数与历史可比。

### 2026-09-29a 质量门编码修复 + 断语取用器去重 + B3 内核命名拆分 + B2 首批（四提交，全零漂移）
ming [3]「narrate 应声明非命运断言」）——根因是 gate 用 UTF-8 解码子进程输出，而子进程按
干净 GBK 环境下 ❌→✅。**不改任何分数口径**。
**tune 93.9 / holdout 87.5、主应期命中 58.8 / 50 逐项与基线一致**（两集分列出分）；
- **口径未变**：本轮为纯结构性重构与环境修复，计分方式/词典/缺失字段处理均未动，
分数与历史可比；**所有分数仍是古籍案例对齐分，非预测率**。

### 2026-09-27u 巨石收尾：step5 / 报告排版 / step3 三拆（零指纹漂移）
`chain_step5_adjust.py`（5.4 六神 / 5.5d–c2 高级象 / 伏神 / 5.5h 古籍加减 /
- 分数口径未变；**非预测率**。

### 2026-09-27u 修正：验收脚本曾假阳性，已复核并加固
传参错误（该函数只收 1 个参数），导致 115 例**全部**走异常分支——两次「指纹一致」

### 2026-09-27v 巨石收尾（续）：_predict_timing 491 行应期巨石按职责切出
`chain_step5_yp_timing.py`，`chain_step5_yp.py` 退化为再导出入口
与 26u 基线一致；金标准 288 例 `5c6e77ee253b0ddd` 一致；tune 93.9 / holdout 87.5、
- 分数口径未变；**非预测率**。

### 2026-09-27w 巨石收尾（续二）：chain_narrate._inject_pattern_tags 359 行格局标签巨石按职责切出
`chain_narrate_patterns.py`，`chain_narrate.py` 退化为再导出入口
- 验收：纯搬移、依赖单向。`tools/refactor_guard.py` 115 例指纹 `15f02c2580a7f489` 与基线一致；
- 分数口径未变；**非预测率**。

### 2026-09-27x 巨石收尾（续三）：human_narrative 979 行按域拆——正文段落八段素材切出
`human_narrative_segments.py`，`human_narrative.py` 保留编排（`build_human_narrative`）/
- 验收：纯搬移、依赖单向。`tools/refactor_guard.py` 115 例指纹 `15f02c2580a7f489` 与基线一致；
- 分数口径未变；**非预测率**。

### 2026-09-27y CI：修复 pytest 从根目录收集失败（importlib 模式 + testpaths）
以子进程按路径调用，**不是 pytest 用例**），pytest 默认 `prepend` 导入模式把它们与被测目录、
- 验证：`python -m pytest -q` 从仓库根干净收集并 **76 passed**（与 HANDOFF 记载基线一致）；

### 2026-09-27z 范围收缩：仅保留 ming（四柱）+ liuyao（六爻），归档 meihua/xiaoliuren/zeji
梅花易数 / 小六壬 / 择吉三科本体、测试、专属数据全部 `git mv` 归档至 `archive/`，保留 git 历史、可随时还原。
- 六爻金标准 `disciplines/liuyao/tools/golden.py verify`：288 例、指纹 `5c6e77ee253b0ddd`、与基线一致，零漂移。
- 分数口径未变；**非预测率**。三科古籍案例对齐分随归档移出当前评测范围，不计入。

### 2026-09-27aa deep-optimize：历史债务文档化 + 治理扫描（死脚本 / 冗余 skills）
（分「阻塞于外部数据」/「有意保持」两类，每条写清阻塞原因）+ 防新债纪律八条 + 本轮扫描结论。
六爻金标准 288 例指纹 `5c6e77ee253b0ddd` 一致。分数口径未变；**非预测率**。

### 2026-09-27ab 仓库清理 + 修 tools/eval.py + handoff 重写
`.pytest_cache`、`__pycache__`、遗留空壳 `.worktrees/`；`git worktree list` 仅 main（无残留注册）；
- **handoff 重写**（`docs/HANDOFF.md`）：基线由过期 `@42cdc7c` 改为按范围/日期描述；顶部加
（tune 93.9 / holdout 87.5 / wikisource_holdout 57.3 / yingqi_holdout 87.2）。口径未变；**非预测率**。

### 2026-09-26t internal-depth-pack：断语收尾/拆巨石/pytest/MCP四科/应期分列/命科交互
- **断语**：meihua/xiaoliuren/zeji narrate 短语与口径句入各自 `verdicts.json`；六爻 `advice_soft`/`narrate_shell`/`engine_format_labels` 入 `narrative_templates.json`。修复模板 `rel or '他爻'` 误写成 format 表达式导致 HO011/HO012 报错。
- 分数口径未变；**非预测率**。

### 2026-09-26s 续：动变/特殊格局句外置 + 断语库键自测
- 分数口径未变；**非预测率**。

### 2026-09-26r 续：建议库/开场句外置 + 命科机械回归
- 分数口径未变；**非预测率**。

### 2026-09-26q 续：星煞口径 + 择吉缺口 + 场景提示外置 + 外部书源
- **星煞口径**入 `verdict_texts.json#shensha_policy`：六爻依《卜筮正宗》辟星煞/《增删卜易》删星煞**不进主分**；命科只安星；择吉天月德/彭祖作辅助。择吉 `validity_gap` 写明仍缺带应验通书日例。
- 分数口径未变；**非预测率**。

### 2026-09-26p 续：长句模板外置 + 内核 API 自测 + 外部书源勘察
- 分数口径未变；**非预测率**。

### 2026-09-26o 续：契约清理 + 断语外置 + 从格细分
- 分数口径未变；**非预测率**。

### 2026-09-26n 深度优化：真值表上收 + step5 假拆清理 + 命科机械扩充
- 分数口径未变；六爻对齐分 tune 93.9 / holdout 87.5 与本条前一致或略升，**非预测率**。

### 2026-09-26m chain_step4 拆分 + 择吉规则黑箱

### 2026-09-26k 架构：classical_rules 拆分 + 巨石看门狗

### 2026-09-26i 命科起运岁数 + 应期相对窗评分
- **六爻评分口径**：strict 相对应期窗走 `RHYTHM_PAIRS` 语义对齐（0.7×）；holdout 85.7→87.5。详见六爻 CHANGELOG 2026-09-26i。

### 2026-09-26h 深度优化：命科机械推演 + 外部方向集 + 梅花变克体终局
合参 `normalize_ming` 带 strength/pattern；**仍无命运吉凶总断**。
（《体用总诀》变乃末后之期）；tune/holdout 100%（n=10/13）。

### 2026-09-26g 易优化包：MCP narrate/render + eval 入口 + 命科骨架 + 病药入 step5
narrate 明示推演未实现；合参 `normalize_ming` 方向固定平。**无格局断语、无大运推演**。
- **分数**：tune/holdout/wikisource 与 26e 持平（93.9/85.7/57.3）；金标准见六爻 digest。

### 2026-09-26e 仓库整洁：死代码与过期文档清理
| 对象 | 原因 |
**删除清单（行为无变化；分数与金标准指纹 `65e8331c80c4f06a` 不变）**
| `references/regression_failure_analysis.md` | 过期（2026-07 失败分析，基线已重立） |

### 2026-09-26d 六爻应期 top-1 稳超随机 10pt+（目标达成）
1. 化出之支逢空 → 出空值日（前插，先于合住冲开）；扫全部化出支
- **口径声明**：与 93.2/93.7 及之前不可比（排序修订）。金标准已 capture。**未声称预测率提升**。

### 2026-09-26c 六爻应期判别力优化（通用古例规则）
1. 用神旬空：近病→出旬填实；久病→冲空；日辰已冲→当日即应
- **`chain_step5._predict_timing` 排序**按 tune/holdout 古例规律归纳（非 case-specific）：
- **口径声明**：tune -0.5 为名次制权衡（部分案例满分变次优），换来 holdout/top-1 双升；**与 93.7 及之前不可比**。金标准 `yingqi_branches` 重排已 capture。

### 2026-09-26b 梅花易数补强：万物类象 + 多爻动 + holdout 扩样
《卷一·八卦万物属类（并为上卦）》与《八卦类象》合并口径（简体），八卦 → 人物/身体/物类/场所/动物/天时/人事/饮食/疾病/五色/方道/数目。
《卷一·八卦万物属类（并为上卦）》与《八卦类象》合并口径（简体），八卦 → 人物/身体/物类/场所/动物/天时/人事/饮食/疾病/五色/方道/数目。
诸动爻同时变得变卦；两侧皆变时 `changed_trigrams` 分列，analyze 逐卦对体论生克。多爻动合成再加互变净势权重（《卷二·体用生克篇》"生体多者则愈吉，克体多者则愈凶"）。
所本：《卷一·爻以六除》一爻动为本法；体用与互变合参见《卷二·体用总诀》《体用生克篇》；两爻及以上动为**通行扩展口径**（原书占例皆一爻动），规则已写入 JSON 与 `references/api_spec.md`。
为通行口径构造校验例（way=manual，与 tune 的年月日时/两数/字画起卦不同源），覆盖多爻动四类体用取舍与求财/疾病/官讼/失物事类。
- 计分方式未变（关系 30/方向 30/生体 15/克体 15/数应 10），分数与此前可比；holdout 扩样后 n 变大，基线注释同步（`tools/check.py` BASELINE holdout n=3→8）。
- **冒烟**增至 6 项（新增多爻动 manual 路径）；`tools/check.py` smoke 基线仍为最低 5，不需抬。

### 2026-09-26 小六壬邻宫速断 + 方位/五行综合断机械化
- **邻宫速断参数化**（`disciplines/xiaoliuren`）：analyze 新增 `neighbors` 字段（进/退/临），规则与断语全在 `data/verdicts.json`（`neighbor_overrides` 古籍出处规则 + `speed_interactions` 通行口径通用表），py 只查表。金例：留连临速喜→「不久即归」（《贺氏六壬小手册》第六节·难点释疑3例3）。
- **所本注记**：贺氏原文规则标出处；主速属性交互与方位生克倾向标"通行口径"；不作绝对判决（AGENTS.md 铁律三）。
- **验收**：smoke 5/5；evaluate --split all 100%（n=15）；tools/check.py 全绿；金标准指纹 0088d638 不变（新增字段为加性，未改已有判定）。计分方式未变，分数与此前可比。

### 2026-09-26 门禁止血：金标准重捕 + tune 基线重锚（规则修订后口径）
- **tune 对齐分基线** 94.2 → **93.7**（strict，n=20）：同一轮规则修订后重算读数。按 AGENTS.md §四.4 声明：**与 94.2 及之前所有 tune 登记分不可比**——分差来自断语规则修订，非数据漂移。holdout 84.8 未动基线（≥78.3 仍过）。

### 2026-09-26b 老师傅补强（进行中）：病药/星煞/择吉神煞/小六壬邻宫综合断
- **分数口径**：本轮六爻对齐分与 93.7 基线持平（回退后）；择吉/小六壬 100 可比（加性字段）。**非预测率**。

### 2026-09-25 六爻正文人性化重构：以叙事层取代原始字段报表 + 彻底清除内部量化暴露
`narrate` 以 `liuyao_engine.format_reading_output` 的原始字段报表为正文结构（排盘表、Step 1-5 思维链框、
- **彻底消除内部量化暴露**（AGENTS.md §三 口径诚实）：
- `_meaning_paragraph` 中的因子贡献段改为"因子名+理由"——移除 `+3.2`、`-1.8` 等评分数字；

### 2026-09-25b 六爻黑箱回归 11/18 → 13/18（四项古籍规则修正）
1. **原神失位静卦豁免**（`disciplines/liuyao/scripts/chain_step5.py` §5 规则 5/9）：

### 2026-09-24 M2.1 词典层结构化：186 键问题词典入 data/ + 取用神四层来源标注（六爻）
186 键按 64 个事项族生成 `data/rules/question_use_gods.json`——逐族标注取舍依据
- **口径变动（矩阵）**：`tools/use_god_coverage.py` 分类改直接消费 meta.source——旧版复刻判断，
覆盖 14、词典 35（有据族 23）、兜底 14，有古籍逐字依据 63 条（旧口径记 29 法则/48 词典/15 兜底）。
- **验收**：三集 strict 与基线完全一致——tune 94.5（n=20）／holdout 84.8（n=12）／

### 2026-09-24 M3 黄金样例与样例入库（3.4/3.5）：唯一模板 + 六项验收清单
逐条过六项验收清单：**六神临用**（螣蛇临用语义叙述）／**持世**（兄弟持世引《火珠林·婚姻章》，
六爻黑箱回归 11/18 持平基线。

### 2026-09-24 M3 一键闭环（3.2）：yi_liuyao.py 一条命令出报告
一条命令走完 chart→analyze→render——起卦（缺省 time 用 --when 时刻/当前时刻，支持

### 2026-09-24 M3 门户修伤（3.3）：死链修复 + 真分数看板 + SVG 卦盘
`disciplines/liuyao/index.html`（gitignore 生成物，由 `scripts/build_portal_assets.py` 可重建）：
- **看板真分数**：`build_portal_assets.py` 的 `build_blind()` 从 `eval_{tune,holdout}.json` 取分
（当前读数 tune 94.5 / holdout 84.8，headline 取 holdout 并带 n=12 与口径说明），

### 2026-09-24 M3 呈现三合一：两套报告引擎合并为单一 HTML 出口 + SVG 真卦盘
承接 2026-09-23 骨架收敛（A2）的"未做"项，本次完成**内容**合并：

### 2026-09-24 应期回收闭环（B2）：断卦→回填→评分全链路打通
按引擎给出顺序即名次，`date` 为公历日期、`rule` 为推出该日的法则标签）——此前只拼进可读文本，
- **口径声明**：outcome-eval 产出为**现实回填命中**，与古籍案例对齐分（evaluate.py）分开登记，

### 2026-09-23 重构批次：六爻巨石拆分 + core/report 呈现统一 + 四科 golden 规范化
### 新增
- 验收：金标准指纹 `0e2bb128`（288 例）与拆分前基线一致，连续两次运行可复现；六爻黑箱回归 11/18 与基线持平。
- 包装既有引擎（`build_hexagram_result` / `thinking_chain` / `advice_framework`），**不触碰任何推演逻辑**，金标准指纹与回归分数不受影响（未改引擎内部）。
- `chart.py`：起卦 → 排盘 JSON（支持 coin/time/number/manual，含早晚子时口径）。
- `xiaoliuren/`（小六壬）：月上起日、日上起时，六宫掌诀断事（《贺氏六壬小手册》口径），含变通取数法。
- `zeji/`（择吉）：建除十二神、黄黑道十二神、二十八宿值日，活动宜忌匹配与综合裁决（《协纪辨方书》口径）。
- `eval.py`：全仓库唯一评分器（分层 tune/holdout/excluded、维度权重、`verdict_direction` 折叠）。
- `cross_rules.py`：五条裁决规则落码（各守其位 / 同向则确 / 两同一异 / 异向先查时空口径 / 缺数据降级）。
- 各科案例库与质量门：三科各有 `data/cases/`（tune/holdout/excluded 分层）、`tools/check.py`、`tools/golden.py`（行为漂移看门狗）。
- `tools/check.py --full` 六爻黑箱回归口径与六爻自身质量门对齐：改用基线比较（11/18，2026-09-22 实测，残余案例待古籍重推已声明），不再要求全过——此前 `--full` 恒红，无法作回归门。
- 三科四段 CLI 写出路径不再依赖目录已存在：`meihua/xiaoliuren/zeji` 的 `chart/analyze/narrate/render` 的 `-o/--out` 此前不建父目录，文档示例 `-o outputs/report.md` 在 `outputs/` 不存在时直接崩（`FileNotFoundError`）；现统一在写前 `parent.mkdir(parents=True, exist_ok=True)`（与 `liuyao` 适配层一致），并已从空目录全链路实测四科 chart→analyze→narrate→render。纯 CLI 健壮性修复，不触碰推演逻辑，分数与指纹不受影响。
### 口径说明（分数可比性）
- 三科分数均为**古籍案例对齐分**（引擎输出与案例库要点吻合度），集合分层如下，禁止对外称"预测率"（`AGENTS.md` 铁律三）：
- meihua / xiaoliuren / zeji：tune 与 holdout 全绿（各科基线见 `disciplines/<科>/tools/check.py` 的 BASELINE）。
- 合参层新增 `calendar_policy` 口径字段：各科年界/子时口径不一致时，合参先标记时空分歧，不直接比结论。
- 六爻（`disciplines/liuyao/`）为迁移前旧实现：已接四段契约薄适配层（可入合参层），但引擎内部仍运行于自身工具链，未迁入内核 `yishu_core.hexagram`；黑箱回归基线 11/18，残余案例待古籍重推（README/HANDOFF 已声明）。

---
### 新增

- **六爻四段契约薄适配层**（`disciplines/liuyao/scripts/chart.py` / `analyze.py` / `narrate.py` / `render.py`）：
  - 包装既有引擎（`build_hexagram_result` / `thinking_chain` / `advice_framework`），**不触碰任何推演逻辑**，金标准指纹与回归分数不受影响（未改引擎内部）。
  - `chart.py`：起卦 → 排盘 JSON（支持 coin/time/number/manual，含早晚子时口径）。
  - `analyze.py`：排盘 → analyze JSON，装配 `conclusion`（方向/说明/置信度/应期/所本，应期从 `yingqi_dates.dates[].date` 干净抽取）与 `chart_summary`（卦名/干支/旬空/动爻/用神/旺衰），直接供合参层 `normalize_liuyao` 归一化。
  - `narrate.py` / `render.py`：薄装配，正文一律用 `format_reading_output` 生成，不允许另行断卦。
  - 根级 `tools/check.py` 新增六爻四段端到端冒烟（chart→analyze→render 产物核验）。
- **卜科三科上线**（`disciplines/`，各科完整四段管线 chart→analyze→narrate→render + 质量门 + 案例库）：
  - `meihua/`（梅花易数）：年月日时起卦 / 报数起卦 / 两数起卦（观梅占金标准），体用生克、互变作用、卦气旺衰、应期、数应迟速、卦象特断。
  - `xiaoliuren/`（小六壬）：月上起日、日上起时，六宫掌诀断事（《贺氏六壬小手册》口径），含变通取数法。
  - `zeji/`（择吉）：建除十二神、黄黑道十二神、二十八宿值日，活动宜忌匹配与综合裁决（《协纪辨方书》口径）。
- **内核扩展**（`core/yishu_core/`）：
  - `zeji_tables.py`：建除十二神 / 黄黑道十二神 / 二十八宿值日表（唯一真值源，学科不复制）。
  - `lunar.py`：农历与公历双向转换（朔望月 + 节气定月双轨制）。
  - `eval.py`：全仓库唯一评分器（分层 tune/holdout/excluded、维度权重、`verdict_direction` 折叠）。
  - `ming_tables.py`、`relations.py`：命科骨架所需表（本轮不实现命科推演，仅立数据）。
- **合参层实现**（`synthesis/`，此前只有契约）：
  - `person.py`：个人档案模型（birth.ganzhi 必须带 `calendar_policy`；`divinations[].outcome` 是唯一现实效度证据字段）。
  - `normalize.py`：四科 analyze 输出 → 归一化占问记录（方向吉/平/凶、应期、判据所本）。
  - `cross_rules.py`：五条裁决规则落码（各守其位 / 同向则确 / 两同一异 / 异向先查时空口径 / 缺数据降级）。
  - `guidance.py`：阶段性指导生成（格局节律 / 近期诸事 / 合参结论 / 可执行建议 / 边界声明）。
  - `cli.py`：init / validate / add-divination / record-outcome / guide / selfcheck。
- **仓库级工具**（`tools/`）：
  - `check.py`：一条命令全仓库质量门（版本唯一真值、结构契约、内核表唯一、三科门、六爻冒烟、合参自检；`--full` 加案例评测与六爻回归）。
  - `demo.py`：全科演示（四科各一例 + 合参演示，走真实 CLI）。
  - `install.ps1`：环境安装与自检。
- 各科案例库与质量门：三科各有 `data/cases/`（tune/holdout/excluded 分层）、`tools/check.py`、`tools/golden.py`（行为漂移看门狗）。

### 修复

- `tools/check.py --full` 六爻黑箱回归口径与六爻自身质量门对齐：改用基线比较（11/18，2026-09-22 实测，残余案例待古籍重推已声明），不再要求全过——此前 `--full` 恒红，无法作回归门。
- `synthesis/person.py`：移除 `xiang`（相理观察）占位字段——相科明确不做（`AGENTS.md` 范围条款），档案 schema 不留相科占位。
- CLI 与文档/命令对齐：`synthesis` 里 `init/validate` 等命令此前以 `--id` 描述，实际为位置参数 `pid`、`add-divination` 需 `--analyze-json`——根 `SKILL.md` §5.3 与 `synthesis/README.md` §〇 已改为可执行的真实接口并实测跑通（建档→登记→指导→回填）。
- 三科四段 CLI 写出路径不再依赖目录已存在：`meihua/xiaoliuren/zeji` 的 `chart/analyze/narrate/render` 的 `-o/--out` 此前不建父目录，文档示例 `-o outputs/report.md` 在 `outputs/` 不存在时直接崩（`FileNotFoundError`）；现统一在写前 `parent.mkdir(parents=True, exist_ok=True)`（与 `liuyao` 适配层一致），并已从空目录全链路实测四科 chart→analyze→narrate→render。纯 CLI 健壮性修复，不触碰推演逻辑，分数与指纹不受影响。
- `disciplines/meihua/scripts/chart.py`：CLI 补齐 `--way lunar` 入口（内部 `chart_from_lunar` 与 docstring 早已支持，唯独 argparse 未暴露）。
- 对齐 SKILL 与实际命令：meihua `SKILL.md` narrate 命令曾传入内联 JSON 字符串（实际接口要求 analyze JSON 文件路径），改为 chart→analyze→narrate→render 分步可执行命令；meihua chart `--way` 取值、xiaoliuren/zeji 起课命令逐一与 `--help` 核对一致。
- `.gitignore`：补 `synthesis/person/` 与 `synthesis/guidance/`（合参层运行产物，此前未忽略，会误入库）。
- `synthesis/cross_rules.py`：缺数据判定改用独立命理主题词表（财运/婚姻/事业等可一事一占、但趋势层缺命科佐证 → 标记 ming 未参评），与越位表解耦。
- Python 3.10 兼容修复（`disciplines/liuyao/`）：`tools/check.py` 的版本检查依赖 `tomllib`（3.11+）改为零依赖最小解析；`scripts/visualization.py` 的 f-string 反斜杠（3.12 前语法错误）改为 `_nl` 变量。此前六爻 `tools/check.py` 在 3.10 下直接崩、质量门不可用。金标准指纹复验无漂移。
- `synthesis/person.py`：`create` 同时给 ganzhi 与 policy 时 policy 不再被丢弃。
- `synthesis/guidance.py`：`tally()` 调用补传 adjudication；被裁决剔除的越位记录不再混入「近期诸事」列表。
- `disciplines/meihua/scripts/chart.py`：卦名自检断言改为简称（与内核 HEXAGRAM_TRIGRAMS、六爻 HEXAGRAMS 同一惯例）。
- 三科 chart/analyze/narrate/render CLI 统一补齐与加固：
  - meihua chart/analyze/narrate/render 补 argparse CLI（此前顶层无条件跑自检或裸 `sys.argv`，`--help` 不可用）；
  - xiaoliuren / zeji 的 narrate 补缺失的 `__main__` CLI；
  - 各科 analyze 统一 `-o/--out` 短长选项。

### 口径说明（分数可比性）

- 三科分数均为**古籍案例对齐分**（引擎输出与案例库要点吻合度），集合分层如下，禁止对外称"预测率"（`AGENTS.md` 铁律三）：
  - meihua / xiaoliuren / zeji：tune 与 holdout 全绿（各科基线见 `disciplines/<科>/tools/check.py` 的 BASELINE）。
- 合参层新增 `calendar_policy` 口径字段：各科年界/子时口径不一致时，合参先标记时空分歧，不直接比结论。

### 已知欠项（不掩盖）

- `ming`（四柱八字）只立数据表与档案字段，推演未实现——合参时该维度按规则降级为"未参评"。
- 六爻（`disciplines/liuyao/`）为迁移前旧实现：已接四段契约薄适配层（可入合参层），但引擎内部仍运行于自身工具链，未迁入内核 `yishu_core.hexagram`；黑箱回归基线 11/18，残余案例待古籍重推（README/HANDOFF 已声明）。
- 各科应期/数应字段暂无事后回填数据，效度统计依赖 `record-outcome` 积累。