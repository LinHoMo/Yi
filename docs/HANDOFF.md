# 易 · 现状交接

> 取代口头交接。分数口径的逐次变化一律查 `docs/CHANGELOG.md`；
> 本文件只写「现在是什么、怎么跑、还欠什么」。**债务速查见 `docs/TECH-DEBT.md`**。
> 分数口径见 `AGENTS.md` 铁律三（对齐分≠命中率）。
> 路线：`docs/YI-PLAN.md`。深度改造清单：`docs/DEEP-DIVE-PLAN.md`；
> 新门类论证：`docs/NEW-DISCIPLINES.md`；网页端 AI 取用规程：`docs/AI-SOP.md`；
> 同域项目调研（Horosa/星阙）：`docs/RESEARCH-HOROSA.md`。
> 规格归档（历史过程规格，读数停在 2026-09，勿当现状引用）：`archive/compose-spec/`。

**范围（2026-10-01j：八科 + 两条出报告通道 + 代码瘦身完成；2026-10-01l 架构修正落地，见 CHANGELOG）**：
- **命科**：`ming`（四柱八字，机械推演）、`ziwei`（紫微斗数，安星/四化/格局/大限）
- **卜科**：`liuyao`（六爻纳甲）、`meihua`（梅花易数）、`xiaoliuren`（小六壬）、`zeji`（择吉通书）、
  `liuren`（大六壬骨架：九宗门三传/天将乘临，机械结构标签，无吉凶断语）、
  `lingqi`（灵棋经：三部掷数查 124 课表直录书源断语）
- **八科**各自的 `dev_tools/check.py` 全绿（2026-10-01），
  仓库根 `tools/check.py --full` 全绿（2026-10-01j 验证）。
- **两条出报告通道**（同一份引擎、同一条四段契约，产出由 `tools/verify_web_parity.py` 逐字节验收）：
  **A 纯前端**（`web/` + GitHub Pages + Pyodide，**零凭证**）；
  **B 云端 Actions**（`reports` 分支固定链接 + issue 回评）。
- **代码瘦身（Phase 7，2026-10-01j）**：六爻核心脚本 docstring 瘦身 ~1,200 行、删死代码 6 处
  （`_stem_element`/`_chinese_num`/`_moving_in_upper`/`_pillar_ten_gods`/`_next_month_with_branch`/`_add_months`）、
  删除巨型历史档 `docs/DEEP-OPTIMIZE-PLAN.md`（130 KB）；引擎行为**零漂移**。

**基线**：`main`（2026-09-30r 锚；上一质量门锚 `5b0c958`）。
质量门：`tools/check.py --full` 全绿（含站点构建+自检、网页↔本机同源验收、pytest、
六爻黑箱回归 ≥ 基线 11/18；读数 2026-10-01）。生成物一律 gitignore（工作区脏/净不入本表）。

---

## 一、现在能不能信（按科）

### 六爻（disciplines/liuyao）— 可上岗助手

| 事项 | 状态 |
|---|---|
| 装卦/历法 | 可信（历法 16 项、爻序 23、金标准 288 例指纹与基线一致——**指纹值见 `disciplines/liuyao/data/golden/digest.json`**；清刻本 822 纳甲/105 卦变/120 世应 0 不合） |
| 用神取法 | 四层：关系法则 → 代码消歧 → 210 键词典（2026-10-01：天气占 9 键 + 借贷/讨债/六畜/坟墓 15 键）→ 世爻兜底 |
| 吉凶方向 | tune **96.8**、holdout **90.2**（strict 对齐分；30r 权重表 + 10-02g 格局标签结构化，与旧口径不可直接比） |
| 附加维度 | 六神临用 / 月令旺衰 / 墓库 / 卦身支 / 三合局 / 用神入三合，30p+30r 激活，strict 全对齐（对表回归） |
| 卦身 | 30r 修复口径（《卜答正宗》安月卦身诀：世爻阴阳+世爻位→卦身支，非旧日干+代数），古籍例姤/否/坤全合 |
| **应期** | tune top-1 **58.8%**（随机~38）；holdout **50.0%**（随机~36.5）；**日/月/年分列**已输出 |
| 病药 | step5 有界加减；**星煞不进主分**（`shensha_policy`：《卜答正宗》辟星煞） |
| 断语治理 | 标签/口吻/建议/场景/开场/动变/特殊格局句入 `verdict_texts.json` + `narrative_templates.json` + `advice_rules.json` |
| 呈现 | `render` + SVG |
| 现实命中率 | **无法评估** |
| 脚本规模 | 见 §之一「当前状态」总表（唯一出处） |

**当前读数（strict，`cd disciplines/liuyao && python dev_tools/check.py`；读数 2026-10-02）**：

| 集合 | n | 对齐分 | top-1 | 备注 |
|---|---|---|---|---|
| tune | 20 | **96.8** | 58.8% | 参与过调参（30r 权重表；10-02g 格局标签结构化） |
| holdout | 12 | **90.2** | 50.0% | 未参与调参（同上） |
| wikisource_holdout | 35 | **56.9** | 20.0% | 永不调参（读数 2026-10-02；旧记 57.1/56.3 已按实测订正，见 CHANGELOG） |
| wikisource_direction | 36 | **72.2** | — | 有吉凶无验期 |
| yingqi_holdout | 2 | 87.9 | — | n 过小仅参照 |
| suigui_holdout | 2 | **94.5** | — | 《增删卜易·随鬼入墓章》真例，永不调参 |
| huozhulin_holdout | 2 | 13.1 | — | 《火珠林》原本，n 过小仅参照 |
| 黑箱回归 | 18 | 11/18 | — | 基线 ≥11 |

> 附加维度（对表回归、机械派生）适用数：tune 六神 10 / 旺衰 16 / 墓库 16 /
> 卦身支 16 / 三合 16 / 用神入三合 16，全部对齐；holdout 12/12 全部对齐。
> 权重表新旧对照见 CHANGELOG 30r。

对外引用：优先 holdout/wikisource，**必须带 n 与集合名**。

### 梅花 / 小六壬 / 择吉 — 已还原，但**分数口径已订正**（2026-09-30 审计）

- 三科均已于 2026-09-29 从 `archive/` 还原至 `disciplines/`，四段管线 + 质量门均通过
  （各科 `dev_tools/check.py` 全绿），金标准指纹未漂移。
- ⚠️ **此前写的"tune/holdout 均 100%"是误导，已订正**。2026-09-30 逐例审计
  （`disciplines/<科>/docs/EVAL-AUDIT.md`，一键复核 `python tools/eval_audit_recheck.py`）
  的结论是：那 100% 是**规则自洽回归数**，不是古籍案例对齐分，不是精度。
  三科的可评构成如下：

| 科 | 集合 | n | expected 来源 | 自洽项占权重 | 读数含义 |
|---|---|---|---|---|---|
| 梅花 | tune 10 / holdout 13 / **external_holdout 4** | 27 | 原书应验 8 + **引擎口径构造 5** + **外部独立 4（卷三·變卦式八則，永不调参）** | holdout 41.9% | 管线自洽；唯一真判据是 5 档吉凶；external 为独立对齐证据 |
| 小六壬 | tune 10 / holdout 5 | 15 | 书上原例 2（仅落宫）+ **构造 3** | **100/100** | 落宫/吉凶/事类/主数全查同一张表 |
| 择吉 | tune 10 / holdout 6 | 16 | **全部 engine_derived；古籍日例应验 0 例** | **100/100** | 等价于一次带断言的回归测试 |

- **已发现的硬泄漏**：梅花 `holdout` MH014–MH018 的 expected 出自本仓
  `data/verdicts.json#multi_move_rules`，而该表与这 5 例在**同一次提交 `010bcee`**
  一起引入。
- **正确说法**（对外引用请照此）：*规则自洽回归数：梅花 13/13、11/11、6/6、8/8；
  小六壬与择吉各维度 n/n 命中*——**带 n，不带百分比**（三科 n 全 < 20）。
- **想让三科真正可检验，唯一有效动作是建外部独立集**，范式照六爻
  （合并 `*_cases.json` + `case_splits.json` 单列"永不调参"split、
  wikisource 35 例）。**扩判据、调权重都不解决这个问题。**
- **梅花外部独立集已落地（2026-10-02r）**：`external_cases.json` 4 例取自卷三·變卦式八則
  （归妹/夬/履/革，`split="external_holdout"`，永不调参）；因该节为「物类断」且部分互变陈述非标准，
  `verdict` 与 归妹/夬/履 的 `生体/克体` 维度 `N/A`，仅 `体用关系`（4/4）与 革 的 `生体(艮)/克体(离)`（1/1）
  为可独立对齐维度。读数 `n=4`、只报命中数。小六壬/择吉 外部集仍待建。
- 三科 `evaluate.py` 现已在报分时自动打印 `[口径披露]`（集合名 / n / 是否调参 /
  自洽项占比 / 泄漏警告），n<20 时声明不发百分比、改打逐维度命中数。

### 命科 — 机械推演已立（非命运断言）

- 强弱 / 月令定格 / 扶抑喜用 / **调候用神（《穷通宝鉴》查表，2026-09-30g）** /
  大运 8 步 / 流年干支×十神 / **大运×流年机械对照**（含**岁运并临标记**
  2026-09-30u：运=年干支相同即标 `sui_yun_bing_lin`，只标记不批吉凶）
- **格局成败救应**（2026-09-30t + 30u）：成/破/救应三分类，十格规则逐条带《子平真诠》原文。
- **从格可判级（2026-09-30w）**：真/假从 / 从旺/从强/从气/从势。
- **四柱直填起盘（2026-09-30t）**：`chart_from_pillars()` 直接给定四柱干支起盘。
- **神煞（2026-09-30u 补全）**：`shensha.py` 天乙贵人/文昌/羊刃/禄神/红艳/天喜/驿马/
  桃花/华盖 + 飞刃/金舆/将星/天医/亡神/劫煞/孤辰寡宿/阴差阳错（通行起例 verified=false）。
- **女命夫子星（2026-10-02q）**：`analyze.py::female_fu_zi` 依《渊海子平·女命论》以官杀为夫星、
  食伤为子星，机械扫描四柱天干+地支藏干十神并归类（绑定 `core.relations` 单源），男命不调用；
  **只标所在，不批旺衰吉凶**（铁律三）。`narrate.py` 新增女命夫子宫专段。
- **童子煞（2026-10-02q）**：`shensha.py` 按民间通胜口诀机械安星（`verified=false`——
  不在《三命通会》《渊海子平》《滴天髓》《子平真诠》原文，经考证确认）；日时同支去重，
  **只安星不批吉凶**。
- 金标准 6 用例与基线一致（**指纹值见 `disciplines/ming/data/golden/digest.json`**）；机械回归 5 例；pytest 覆盖。
- **案例对齐评测**：**276 例（tune 30 / holdout 246）**——
  - 调候 225 例、格局成败 36 例（全 holdout）、从格 15 例（全 holdout）
  - 读数（2026-10-04 订正）：tune 100.0%（30/30 调候）、holdout **strict 96.7%**
    （n=246：pillars 189/189、tiaohou 21/21、pattern 28/36、
    cong_ge 13/15、from_kind 15/15——kind「杀势当权」通则补齐后；真/假灰区余 2 例 ZC014/015）
    ⚠️ **旧记 97.1 系文档讹数**：自 10-02t 起五个提交点（d36df84→HEAD）复跑均为 96.7，
    维度计数完全相同——均分差来自 8 例 ZP 体系分歧 case 级计 0 的算术，97.1 从未被复现。
  - **表对表回归 + 历法链路验证，不是泛化证据**
  - **外部独立集（external_holdout）已建四批（10-04 / 10-04h / 10-05h / 10-05k）**：
    《滴天髓阐微》语料入库（`data/sources/di-tian-sui-chan-wei.wikitext.txt`，401KB），
    **强弱维度** n=45（`ming_external_cases.json`；首批＝衰旺章任注显式标注例 19 例，
    第二批＝章外穷尽扫描 +7 例 ZE020–ZE026，第三批＝中和带显式判例 +11 例 ZE027–ZE037，第四批＝身弱/身旺无极类词 +8 例 ZE038–ZE045（10-05k）；
    纳入规则/剔除清单/类别映射见其 `_provenance`，永不调参）。读数为 **report-only**
    （`evaluate.py --split external_holdout`，照六爻应期分列范式，不进 WEIGHTS、不设门槛）：
    **强弱对齐 30/45**。
    天干十神维度（**2026-10-06a 登记**，复用 `score_case` 的 `ten_gods` 维度、权重 16；
    external 永不调参、只报数）：**5/5 = 100%**（ZE028/030/039/041/044 书源显式点名透干，
    经引擎对账一致——详见 CHANGELOG）。
    格局维度（**2026-10-06b 登记**，复用 `pattern` 维度、权重 12）：**2/2 = 100%**
    （ZE029 印绶格→正印格、ZE038 建禄→建禄格，书源显式点名、引擎对账一致；45 例全量扫描
    仅此 2 例达标，其余描述财/官而非点名格名）。
    藏干/神煞在《阐微》衰旺章语料中无显式点名、大运仅点名干支而非所评顺逆/起运岁数——
    此三维度外集暂不可补，须另取专论古籍源（下一轮决策）。三维度读数彼此独立、不混算准确率。

    **多书框架 + 穷通宝鉴调候批（2026-10-06c，engine 零变化）**：外部集由单书硬编码升级为多书白名单
    （`ALLOWED_BOOKS={滴天髓阐微, 穷通宝鉴}`），strength 改为按需、`test_external_expected_is_report_only`
    白名单扩至含 `tiaohou`。新增第二部古籍《穷通宝鉴》调候（tiaohou）批 **18 例（QTBJ001–018）**，
    external_holdout 现 **63 例**（45 阐微＋18 穷通）；逐例核验「日主×月令」、月令错配者剔除
    （书源「十一月丁火」小节内实为丑月例，已剔除零入库）。
    读数（report-only，永不调参，10-06c 实测）：**调候 tiaohou 6/18 满分例（33.3%）**——
    但此**非准确率**：引擎 `analyze.tiaohou` **源出** `core/yishu_core/ming_tables.TIAO_HOU`
    （《穷通宝鉴》月令×日主查表，51/120 格，与本书同源）。本批为**同源覆盖审计**而非独立验证，
    价值在①回归守护（`TIAO_HOU` 表被改时即暴露漂移）②覆盖审计（暴露缺格＝卯丙/午丙/午丁/申丁/亥丁
    引擎返回空；佐神正月/六月丙火书言「庚」而表记空）。已覆盖 4 格（寅丙/巳丙/未丙/卯丁）`main` 神
    全部命中。后续可补 `TIAO_HOU` 至更全以提覆盖；**独立验证须另取异源古籍**（子平真诠/三命通会等，
    沙箱出站网络屏蔽暂未现抓）。
    强弱仍 30/45、天干十神仍 5/5、格局仍 2/2，三维度彼此独立不混算。
    失配 15 例归因在案：旺侧 4 例（ZE017 已由三支全会聚轴修复 10-04l；ZE005 禄刃轴
    不解释（10-04d）；ZE020-022 拱局机械项证伪 10-05a——判语层选择性引用无机械标定路径）；
    中和带 6 例（ZE027/028/030/034/036/037）＝第三批直接实证：±1.5 带宽与任注中和区域
    系统性错位（引擎判偏弱×5/偏旺×1），永不调参（TECH-DEBT §2.3）；
    **身旺 5 例（ZE039/041/042/044/045）＝第四批直接实证：引擎判中和/偏弱而书源断身旺，
    任注身旺区域宽于引擎 ±1.5 带宽同构复现**，永不调参。
    评测报告分层：机械回归 / 古籍对齐（source alignment）/ 外部独立集（external holdout）/
    现实回填反馈（outcome feedback）四类口径不得互相冒充。

    **TIAO_HOU 扩面 51→90 格（2026-10-06e，engine 变更但源自书源、非外集调参）**：
    `build_tiaohou.py` 提取器重写（干大段逐句月词检索 + 精确 `'''N月X干'''` 头 + 季节兜底；
    剔除示例盘 wikitable 防误取成药例；支持「耑用」异体；引文强制原文子串，--check 可复现）。
    引擎 `TIAO_HOU` 补至 **90/120**，补齐亥/子/丑冬季与此前空白格（`子` 从 0 格起步），
    **对原 51 格零回归**，仅巳丙补出 assist 庚。外集 tiaohou 读数由 6/18 升为全命中——
    此为**引擎忠实书源**之结果（同源覆盖审计，**非独立准确率**，见上条口径）。
    措辞层漂移已 capture 归因（机械层零漂移）。**两套键务必分清**：
    `tiaohou_quotes.json`＝月序+日干（`4乙`，narrate/evidence 消费契约）；引擎 `TIAO_HOU`＝月支+日干（`巳乙`）。
    其中 16 格为季节总论兜底（via=season），可能过泛，已标注；独立验证仍待异源古籍。

- **不做**：命运断语、流年吉凶定论

### 合参 / 工具

- `tools/check.py`（结构/内核自测/断语键一致/ming 质量门/六爻冒烟/合参/站点/同源/pytest）
- `tools/eval.py`、`tools/demo.py`、`tools/core_selftest.py`、`tools/text_keys_selftest.py`
- person + outcome-eval

### 证据链与 Agent 层（2026-10-03 新增，机器可读状态见注册表）

- **Evidence Contract**：`core/yishu_core/evidence.py`——八科 analyze 输出的结构化证据
  派生视图（id/claim/factor/rule_id/source/applicability/observation/effect/
  evaluation_status/provenance）。纯函数双宿主共用；本机 `YiRuntime.execute` 与
  浏览器 `web/engine_runtime.build_report` 的 envelope 都挂 `evidence` 信封，
  同源验收（`tools/verify_web_parity.py`）已加 **EV 列**逐例比对。
- **能力注册表（评测状态唯一真值源）**：`core/yishu_core/execution/registry.py`——
  能力性质五档（stable/experimental/mechanical_only/source_only/unavailable）+
  评测基线五档（classical_holdout/external_holdout/mechanical_regression/
  source_only/unassessed）+ `evaluation_splits`（分列名是结构事实，分数读数仍以本文件为准）。
  liuren=mechanical_only、lingqi=source_only；liuyao/ming/meihua=classical_holdout；
  ziwei/xiaoliuren/zeji/liuren=mechanical_regression。文档引用不复制。
- **六爻规则注册表**：`disciplines/liuyao/data/rules/rule_registry.json`——
  9 个优先规则域（三会局/独发独静/反吟伏吟/六合六冲/旬空真空假空/墓库/进退神/
  用神多现/应期）+ 卦身/三合，逐条带书源引文指针（quote_in_data/quote_in_code，
  测试逐条可解析）、适用条件、实现位置、评测覆盖（dim 必须是 evaluate.py WEIGHTS
  真实维度）；三合局引文未逐字挂接，`verified=false` 如实登记缺口。
- **ming / meihua 规则注册表（2026-10-03b，Phase 5）**：ming 调候/格局成败/从格/
  大运/神煞 5 域（穷通宝鉴逐字库/子平真诠/滴天髓引文锚）；meihua 体用关系/
  生克之卦/应期 3 域（外部独立集覆盖的体用域如实标 external_holdout）。
  挂接时评测状态**以注册表为准**——规则级覆盖是比学科基线更细的真值：
  ming dayun/shensha（案例集 0 applicable）如实降到 mechanical_regression。
- **canonical 反馈模型**：`core/yishu_core/feedback.py`——synthesis 档案链与六爻
  FeedbackStore 链经 adapter 折叠为同一 FeedbackRecord（两链的存储与判定口径保留，
  判定真值源仍是 `core/yishu_core/yingqi`）；`provenance.kind` 强制区分
  real_outcome / synthetic_regression，混集判败（物理/语义分离）。
- **Agent API（稳定最小五入口）**：`core/yishu_core/agent.py`——capabilities /
  validate_request / run_report / get_evidence / get_evaluation_status。
  `get_evaluation_status` 刻意不含分数（读数权威源是本文件 §一），只回答
  「哪类评测存在、该科结论可以说到什么程度」。
- **合参证据级检视**：`synthesis/evidence_cross.py` + `synthesis cli evidence-cross`——
  在旧五条裁决（`cross_rules.adjudicate`，保持不变）之下新增
  same/conflict/unassessed 清单：冲突保留双方 applicability/出处，缺失证据显式
  unassessed，跨科同向只提升一致性描述强度、不制造新事实。
  **已内嵌 `guide` 主合参文档**（同一 `cross_examine`）：`two_one`（两吉一凶）趋向
  显式标注为方向级计数倾向（裁决规则 3），不再是最终逻辑——异向结论与成立条件
  并列保留后方可采信；旧档案未携带证据时如实声明「检视不可用，描述强度不提升」。
- **断言边界与概念映射（2026-10-03b，Phase 5）**：报告 envelope 的
  `evidence.claim_policy` 按证据组合给出机器可读断言边界（方向表态强弱分层/
  应期单列/弱覆盖须声明未独立验证）；`synthesis/concept_map.json` 为跨科概念
  映射注册表（verified-only、全等匹配、当前零已验证条目——机制就位、语义债如实登记）。

---

## 二、怎么跑

### 统一 CLI

```bash
yi liuyao cast "占买房子何时有结果"
yi liuyao chart --mode coin
yi liuyao analyze chart.json
yi liuyao narrate analyze.json
yi liuyao render analyze.json
yi ming chart --datetime "1990-05-20 10:30" --gender 男
yi ming analyze chart.json
yi meihua cast "占投资"
yi meihua chart --way time
yi xiaoliuren cast "占出行"
yi zeji chart --date "2026-09-30" --activity 开市
```

安装：`pip install -e .`。

### 出报告（两条通道）

```bash
python tools/report.py --discipline liuyao --question "占求财" --datetime "2026-09-30 10:30" --mode time --outdir reports
python tools/serve_web.py                                # 本机预览
python tools/build_web.py --outdir site                  # 构建静态站点
python tools/verify_web_parity.py                        # 同源验收（逐字节）
```

深链：`/?d=liuyao&q=占求财&dt=2026-09-30 10:30&mode=time&auto=1`

### 各科直跑

```bash
# 六爻
cd disciplines/liuyao && python dev_tools/check.py && python scripts/yi_liuyao.py "所问之事"

# 命科
cd disciplines/ming && python dev_tools/check.py && python scripts/chart.py --datetime "1990-05-20 10:30" --gender 男

# 梅花 / 小六壬 / 择吉
cd disciplines/<科> && python dev_tools/check.py && python scripts/chart.py ...
```

### 仓库级

```bash
python tools/check.py          # 快速门
python tools/check.py --full   # + 案例评测 + 黑箱回归 + pytest
python -m pytest tests -q
python tools/eval.py
```

流派开关：`YI_GANZHI_BOUNDARY=day|instant`、`--zi-hour-type late`。

金标准验收：`cd disciplines/liuyao && python tools/golden.py verify`。

---

## 三、应期规则（核心资产）

位置：`liuyao_step5.calculate_yingqi`（主入口；拆出链见 §六）。**通用古例归纳，禁止 case-specific**。

优先级（高→低）：

1. 化出之支逢空 → 出空值日
2. 空而化回头生 → 不作空论，期于生我之日
3. 用神旬空：日辰已冲→当日；久病→冲空；近病→填实
4. 伏藏：飞克伏→先冲飞；飞空得出→伏神值日
5. 月破/入墓/合住：填实、冲墓、冲开
6. 不空：动爻先值日再逢合；静爻值日再逢冲
7. 空亡出空 / 三合 / 原神 / 化出 / 旺相
8. 静爻旺相逢冲即发（r8；《增删卜易》"静爻旺相，冲之即发"）
9. 世应位置迟速调节（r9；《增删卜易》）

**评分（strict / loose 双列）**：
- strict：单一精确支排 top-1 才命中（基线 tune 58.8%、wikisource 20.0%）
- loose：相对窗 / 绝对日期窗覆盖 expected 即命中（tune 94.1%、wikisource 60.0%）
- `--yingqi-mode strict|loose|both`（默认 both）
- `evaluate` 输出 `yingqi_day/month/year`（只报数，不设新门槛）

否证（勿重复踩坑）：

- 病药/药码进应期主排序 → holdout top-1 掉，**已回退**
- 书序整体重排 → 三集全降，**已回滚**
- 回头生全局前插 → 挤掉值日，**改仅空卦**

---

## 四、还欠什么（按优先序）

> 债务的**速查登记**见 `docs/TECH-DEBT.md`。
> **各科"老师傅程度"差距与可执行改造清单见 `docs/DEEP-DIVE-PLAN.md`**；
> 新门类论证见 `docs/NEW-DISCIPLINES.md`。
> **当前进行中的工作项与优先序见 `docs/TECH-DEBT.md` §2.5（证据链收敛）与 §2.6（评审遗留）**
> （2026-10-03b 起：规则一等实体推广 / 规则级评测覆盖 / claim_policy 断言边界 /
> verified-only 跨科概念映射）。阶段路线图件已按减法删除——工作项以 TECH-DEBT 为准，
> 不另立规划文档。

0. **wikisource 应期泛化** top-1 ~20%（**2026-10-06 扩样 n=44**、对齐分 60.8/loose 84.2：
   年级阶梯等五组通用规则 + 解析器扩样 + strict 相对窗死代码修复，见 CHANGELOG 10-06d/06f）；
   **禁止考卷调参**。
   - 《卜筮正宗》仅 912 字节目录骨架（维基文库子页 404；**2026-10-02s 复核仍属实**：卷一~十四全为红链）。parser 已搭，待正文压入。
   - 《火珠林》2 例 scorable + 5 例定性已入库（`huozhulin_holdout`）。
1. **梅花/小六壬/择吉外部独立集**：三科 100% 读数是规则自洽回归，唯一有效动作
   是建外部独立集（范式照六爻 wikisource）。此硬泄漏（梅花 MH014–MH018）与口径
   审计（`tools/eval_audit_recheck.py`）已登记。
   - ~~梅花外部集~~ ✅ 2026-10-02r 已建 `external_holdout`（卷三·變卦式八則 4 例，永不调参；
     因该节为物类断且部分互变非标准，verdict 与归妹/夬/履 生克 N/A，仅 体用关系+革 生克 可对齐）。
   - 小六壬/择吉 外部集仍待建（同 §一 梅花段说明）。**2026-10-02s 复核**：《協紀辨方書》维基文库 404、
     小六壬书源仍无数字化公版——TECH-DEBT 2.1 "阻塞于外部数据" 登记属实。
     **2026-10-06 更新**：小六壬公版书源部分解除——《玉匣記》雜占篇收《李淳風六壬時課》全节
     （在库底本内，原检索按独立书名漏检），六宫逐字对照入 `verdicts.json#cross_source`
     （五宫结构项全一致；空亡主数两源分歧如实登记，engine 不动）；占例集仍阻塞。
     择吉候选书源（選擇求真/象吉通書/鰲頭通書/造命宗鏡/選吉探原）逐题实测全 MISSING。
2. **六爻评测盲区**：~~墓库只验日/月墓（动墓·化墓未覆盖）~~ ✅ 2026-10-02a 补齐
   （判据唯一源 `classical_enhancements.use_god_tomb_tags`；书源真例入新外部集
   `suigui_holdout`，tune/holdout 不变）；~~反吟/伏吟/进退神/暗动/月破仍为格局词子串匹配~~
   ✅ 2026-10-02g 已改**读 `advanced_analysis` 结构**（`hidden_movement`/`monthly_break`/
   `triple_combo`/`three_punishments`/`repetition`），不再扫 `step5`/`summary` 文本；
   新增 `[1.6]` 金标准已把 `patterns` 纳入机械指纹（见 CHANGELOG 10-02g）。
3. **命科缺口**：~~强弱无书源 expected~~ **外集已立四批（10-04 / 10-04h / 10-05h / 10-05k）**
   （《阐微》显式判例 n=45 report-only，30/45——失配 15 例归因在案（旺侧 4 / 中和 6 / 身旺 5），
   见 §一 命科段）；
   四柱/十神/藏干/神煞/大运仍无书源 expected；**10-01p 已补**三会局、
   胎元、流月、小运、天克地冲、十神组合（六项机械结构标签，只出结构不批吉凶）；
   **10-02b 已补**通关/关隔（《滴天髓·通隔論》逐字入库 + 日主两路判据）；
   **10-02f 已补**四柱地支**刑冲害合**（`pattern.pillar_relations` 四支两两 +
   三刑，表取内核；《滴天髓·地支論》逐字三首入库，见 CHANGELOG）；
   **10-02h 已补**四柱**天干五合**（同函数四干两两，表取 `core.relations.STEM_WUHE`）；
   ~~地支合化/争合妒合~~ **2026-10-05 取证收口**：争合识别已落地（`pillar_relations`
   「天干争合」结构标签，10-05c）；化气/羁绊＝落地前置化判定标定（月令表/根气无通则
   数值，羁绊是其补集语义——10-05e 评估在案）；~~冲开墓库~~ **书源否决不实现**
   （任注明驳「墓库逢冲必发者，谬也」，10-05d）；
   ~~病药（《神峰通考》）~~ ⚠️**2026-10-03f跨书源取证结论：语义分裂，不应建统一病药模型**。
   在库三书（《神峰通考》7例 / 《穷通宝鉴》7条 / 《滴天髓》3条）裁决：
   **《滴天髓》全书无「藥」「病神」，其「病」指人身脏腑疾病**，与病药非同一概念；
   **《穷通宝鉴》有「月令→病」固定表**（九月辛金火土为病、二月辛金戊己为病），
   而**《神峰通考》明确无此表**（「或为病，或非病」）。三书对「病」语义明显分裂，
   故正确方向是 `discipline/source-specific interpretation`（各书按自身文本实现、
   各自标 provenance、彼此不冒充），**而非统一病药规则**。
   engine 现状：五行层**更接近穷通宝鉴而非神峰通考**（用错书源），但**不得断言字层是唯一语义层**。
   仍不改engine；**2026-10-04 阐微取证已完成**（跨源表 +17 条 ZW 观察）：三书结论加强为
   **三种病药体系并存**（神峰＝格局逐盘取字 / 穷通＝月令固定表 / 阐微任注＝忌神·喜神绑定），
   任注命例级病 13/13 落具体字与神峰同向；**勘误**：「滴天髓无病药」仅对原文卷成立，
   任注脏腑义与判据义同书并存。唯缺《子平真诠》。
   全部登记见 TECH-DEBT §2.7/§2.8，观察集与跨源表**不计分、不入 holdout**。
   - ~~女命夫子星~~ ✅ 2026-10-02q 已补（`analyze.py::female_fu_zi`：官杀夫星/食伤子星，机械标注不批吉凶）。
   - ~~童子关煞~~ ✅ 2026-10-02q 已补（`shensha.py` 童子煞，民间通胜口诀、`verified=false`、只安星不批吉凶）。
   - **2026-10-02s**：《滴天髓阐微》（任铁樵注本，含命例）维基文库存在独立条目（滴天髓 辑要页链接可达）
     → 命科外部独立集（§四.D）解除路径由"用户供书"更新为"书源可网络获取，待照 ZC 批次机制提取命例"。
4. **report 段行为保护**：~~六爻 golden 只罩 chart+analyze；`render` 全文哈希未入基线，
   排版改动不会被门拦下~~ ✅ 2026-10-02c 已补（根门 `[6b]` 对八科 render MD 逐字节指纹，
   基线 `data/golden/render_digest.json`，负例自证会咬人）。六爻 `dev_tools/golden.py`
   仍只罩 chart+analyze（属各科细粒度指纹，非缺口）。
5. **从格灰区 3 例 + kind 缺口 2 例**（ZC012/014/015）——**2026-10-02t：kind 缺口已清**
   （通用规则「官杀当权不落从势」：当令且透干或双透成党 → 从官杀，from_kind 15/15，
   见 CHANGELOG 10-02t）；真/假灰区余 **2 例**（ZC0014/015：根会木局形存气夺、比劫虚浮被克去，
   须六合化气/克去微观机制，维持「待六合化气/合冲互动引入后复核」登记）。
   子平/滴天口径分歧 8 例
   （ZP004/005/015/020/029/032/034/036，属两书体系差异非引擎缺陷）。
6. ~~**`tools/eval.py` 未挂门**：在 `--full` 盒之外，回归不会被测出。~~
   ✅ 2026-10-02i 已挂：根门新增 `[7d] 各科案例对齐分一览`（跑 `tools/eval.py`），
   并统一各科 evaluate 的 `--split` 入参契约（大六壬 evaluate 此前不认 `--split`，
   使 `tools/eval.py` 恒失败 2 项）。
7. 各科应期/数应暂无事后回填数据，效度统计依赖 `record-outcome` 积累。
8. **六爻「伏而不得出」方向权重已补（2026-10-02s）**：核实合绊已有有界权重（原神贪合忘生 −2.0 /
   日月合绊 −0.2 / 动化合绊 −0.3），真空缺是伏神不得出方向零反馈——补 −1.0（结构判据
   `fu_cang_detail.results[].can_emerge`，所本《黄金策·千金赋》"伏无提挈终徒尔"）；分列验收
   tune 96.8 / holdout 90.2 / wikisource 56.9 / 黑箱 11/18 全持平，golden 零漂移，
   `tests/test_liuyao_fu_no_emerge.py` 锁定。reg_07 残余分歧（飞空得出 +1.5 vs 占行人古籍直断）
   登记为已知方向失配，不为过例加码；「不得出」书源基准例待建（119 例探针核实评测集暂无触发例）。

---

## 五、口径与纪律

1. 对齐分 ≠ 预测率；禁止「准确率 X%」
2. 报分必带：集合名 + n + 是否调参
3. 改引擎：tune/holdout 分列；tune 无故跌破基线即回归；通用规则 + 古籍出处
4. 口径变更记 `docs/CHANGELOG.md`
5. 案例库解读隔离；一卦一事
6. 金标准 `capture` 必须写理由
7. 拆分/搬家以**零指纹漂移**验收

---

## 之一、当前状态

> **读数时点 2026-10-05 17:30**（本机 `splitlines` 口径；统计 `disciplines/<科>/scripts/*.py` 与 `dev_tools/*.py`，
> 排除 `site/`、`tools/scratch/`、`archive/`、`__pycache__/`、`*.log`）。
> 行数/文件数一律以本表为唯一出处，别处引用不复制。并行工作流仍在改语料时，读数会随之下移/上移，引用请带此时点。
>
> **与上一读数（2026-10-02 11:15：合计 81 文件 / 26,934 行）的差异**，可全部归因到已登记事项，
> 无未知项：命科 `ming` +387 行（外集两批取证登记 + 会聚/争合落地 + 合化/夫子星观察集，
> 10-04→10-05 各轮）、六爻 `liuyao` +74 行（注册表六域收口的锚点注释，10-04g→10-04r）。
> ⚠️ 旧表「dev_tools 合计 44」与其自身行合计（47）不符——系旧表合计列讹数，本次以行合计 47 为准。
> 小六壬、择吉、梅花、大六壬、灵棋经、紫微未变。

| 学科 | scripts/ 文件数 | scripts/ 总行数 | dev_tools/ .py 数（含 `__init__.py`） |
|---|---|---|---|
| 六爻 `liuyao` | 37 | 18,138 | 17 |
| 命科 `ming` | 7 | 2,802 | 9 |
| 梅花易数 `meihua` | 7 | 1,768 | 3 |
| 小六壬 `xiaoliuren` | 7 | 1,101 | 2 |
| 择吉 `zeji` | 7 | 1,086 | 3 |
| 大六壬 `liuren` | 7 | 1,286 | 5 |
| 灵棋经 `lingqi` | 4 | 271 | 3 |
| 紫微斗数 `ziwei` | 5 | 943 | 5 |
| **八科合计** | **81** | **27,395** | **47** |

- 四段契约：`docs/CONTRACT.md` 定义，结构门 + golden/忠实度回归强制。
- 统一入口：`cli/main.py` → `yi`。
- 八科 `dev_tools/check.py` 全绿，仓库根 `tools/check.py --full` 全绿。
- 代码瘦身：见 §一 顶部与 CHANGELOG 2026-10-01j。
- `docs/DEEP-OPTIMIZE-PLAN.md` 已删（历史档，130 KB）。

---

## 二、架构要点

```
core/yishu_core     唯一真值源（历法/象数/旬空三刑长生/纳音/三合/星煞/十神/评分）
disciplines/<科>    四段契约 chart→analyze→narrate→render
synthesis           person + 合参 + outcome-eval
tools               check / eval / demo / selftests
tests/              pytest
```

- **真值表**：旬空/三刑/十二长生/纳音/三合 已上收 core；看门狗盯同义表名
- **六爻脚本体系（10-01j 状态）**：`liuyao_step{1-5}.py`（主流程）+
  `classical_enhancements.py`（古典规则）+ `effects.py`（象数效应）+
  `narrative_utils.py` / `narrative_rules.py`（叙事辅助）+
  `liuyao_analyze.py`/`liuyao_narrate.py`/`liuyao_timing.py`（聚合门面）+
  `thinking_chain.py`（思维链编排）+ `evaluate.py`（评分器）+
  `event_logger.py`（日志）+ `yi_liuyao.py`（CLI 门面）
- **已删**：`chain_step5` 假拆死体、`_extra_tombs`、`_next_month_with_branch`/`_add_months`
  6 处私有函数、`__pycache__`/`guard/` 历史调优快照（~15 MB）

---

## 三、变更索引（查 CHANGELOG）

| 记号 | 内容 |
|---|---|
| 10-04 | 命科外部独立集首批（《阐微》衰旺章强弱 19 例，report-only 17/19，禄刃根分歧 2 例登记）+ 阐微语料入库 + holdout 读数订正 97.1→96.7（本棒） |
| 10-02s | 根门 pytest 遮蔽修复 + [1c] 白名单复核收紧 + 孤儿断语处置 + 六爻伏而不得出 −1.0 |
| 10-01j | 六爻 docstring 瘦身 + 死代码清除 + DEEP-OPTIMIZE-PLAN 删除 |
| 10-01i | 修"门在干净克隆上必红"两处 + 八科分科门挂进 CI |
| 10-01h | 修"核心常量进正则"回归（六爻 19/20 报错） |
| 10-01g | MCP 全量移除 + 活跃面引用清零 |
| 10-01f | 取证门语料池瘦身 97% + focus 主语剥离 |
| 10-01e | 断语外置改为黑箱取证 + 七科 golden 补 narrate |
| 10-01c | 真值源门升级 + 清 25 处运行时副本 |
| 30x–30r | 卦身/三合维度激活 + 权重表再分配 |
| 30l | 灵棋经落地（第八科） |
| 30g | 命科调候落地：《穷通宝鉴》表入内核 + 51 例 |
| 30e | 三科评测口径审计："100%"订正 + 报分口径披露 |
| 30d | 两条出报告通道：纯前端 + 云端固定链接 |
| 29c | v1.0.0 结构重构（统一 CLI + disciplines/base 共享层） |
| 29a | 质量门编码修复（子进程 UTF-8）+ 内核命名拆分 |

---

## 四、可执行清单（按优先序）

> 每项都写清完成标准与验收命令，做完不通过验收即视为未完成。
> 叙述版债务见上文 §四，机械登记见 `docs/TECH-DEBT.md`。

### 0. 交接状态

- **代码状态**：工作区干净，HEAD 至 2026-10-05i+j（`59a57bf` 命科外集第三批
  中和带 ZE027–037 / `b45ce1b` 大六壬合池→下贼优先口径变更 / `dcbdf63` 该轮出处
  错标订正——《六壬指南》语料入库与目录翻案见 CHANGELOG 10-05h/i）。
- **门状态**：`tools/check.py` **EXIT=0**（10-05 复验）；根 pytest **387 passed**；
  八科行为指纹、六爻/大六壬金标准全绿零漂移。
- **最近交付**：10-05i 大六壬口径变更（《六壬指南》心印赋注显式文本，反事实 43 例
  净值 33/43 不变，LE001 转入古籍异说桶）；10-05h 命科外集第三批（中和带 +11 例，
  report-only 30/45）；10-05a–f 合化/拱局/冲开墓库/羁绊 source adjudication 系列
  （engine 零变化为主，见 CHANGELOG）。
- 跑门环境：Python 3.12+（3.10 见 §五之一 兼容修复）

### 1. 可执行清单（按优先序）

| # | 任务 | 完成标准 | 验收 |
|---|---|---|---|
| **A** | ~~render 段加 golden 基线~~ ✅ 2026-10-02c：根门 `[6b]` 八科 render MD 逐字节指纹入 `data/golden/render_digest.json` | 改一字即被测出 | `check.py --full` EXIT=0 |
| **B** | ~~`NON_VERDICT` 白名单逐条复核~~ ✅ 2026-10-02s：过宽的括注两条收紧为「括注+短尾」，新增机械定位前缀剥离（官鬼（落在卯三爻）类真判语交还语料匹配），③修正硬编码、⑦删冗余、⑥b–g 逐条补"为何属非断语" | 复核后 strict 0 句豁免性漏判 | `verdict_audit --strict` EXIT=0 |
| **C** | ~~孤儿断语清理~~ ✅ 2026-10-02s：删 9 条真孤儿（六爻 4+2、梅花 2、小六壬 3、verdict_texts 错位副本 1 + 死加载量）+ quote_lead 接线（两处内联合一）+ verdict_consumption ALLOWLIST 键级匹配修正与登记 | 清单与处置见 CHANGELOG 10-02s；八科 golden 零漂移（全量门 EXIT=0） | `check.py --full` EXIT=0 |
| **D** | 命科外部独立集：~~字面标准（≥20 例书源 holdout 不参与调参）~~ 已由 子平真诠 36 例 + 滴天髓阐微 ZC 15 例 满足；**跨书源集已立四批（10-04/10-04h/10-05h/10-05k）**：《滴天髓阐微》语料入库 + 强弱维度 n=45（`ming_external_cases.json`，external_holdout 永不调参，report-only 读数 **30/45**，失配 4 例归因在案见 §一 命科段）——扩集方向：阐微其余章节显式可判例（中和/身强弱语，10-05a 拱局证伪后弱侧优先）、病药跨书源补证（§2.7/2.8 解除路径已开） | 新 holdout split 读数（永不调参） | ✅ `evaluate.py --split external_holdout`（30/45）+ golden 不漂移 + `check.py --full` 全绿 |
| **E** | ~~六爻动墓·化墓用例~~ ✅ 2026-10-02a：判据 `use_god_tomb_tags`（日/月/动/化四类）+ 书源真例 `suigui_holdout` | 墓库维度覆盖动/化墓 | tune/holdout strict 不变（96.8/89.7）+ `dev_tools/check.py` EXIT=0 |
| **F** | `tools/eval.py` 挂 `--full` 档 | 当前 EXIT=0 再挂，否则挂上去就是常红 | `--full` EXIT=0 + eval 分数有输出 |

### 2. 取证口径的坑（实踩记录）

1. 待检句与语料池必须走同一个 `_hanzi` 归一函数
2. 绝不能在抽汉字前剥 `{...}`——会跨行吞 JSON 区间
3. `cases/`、`guard/`、`scratch/` 不能当措辞真值源
4. 模板前缀跟着模板走；`{focus}` 自举剥离
5. `--verbose` 语料汉字数是关键信号；暴涨 = 语料池被污染

### 3. 需要拍板的

- 语料池边界：是否还有其他"产物性目录"也须剔？判据 = "这条目录里存的是不是引擎输出"
- `{focus}` 剥离是否算放宽判据：新增剥离规则须在 CHANGELOG 写明理由
