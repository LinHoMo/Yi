# 易 · 现状交接

> 取代口头交接。分数口径的逐次变化一律查 `docs/CHANGELOG.md`；
> 本文件只写「现在是什么、怎么跑、还欠什么」。**债务速查见 `docs/TECH-DEBT.md`**。
> **一切分数是古籍案例对齐分，不是现实预测命中率**（`AGENTS.md` 铁律三）。
> 路线：`docs/YI-PLAN.md`。深度改造清单：`docs/DEEP-DIVE-PLAN.md`；
> 新门类论证：`docs/NEW-DISCIPLINES.md`；网页端 AI 取用规程：`docs/AI-SOP.md`；
> 同域项目调研（Horosa/星阙）：`docs/RESEARCH-HOROSA.md`。
> 规格归档：`docs/compose/spec/`。

**范围（2026-09-30l：八科 + 两条出报告通道）**：
- **命科**：`ming`（四柱八字，机械推演）、`ziwei`（紫微斗数，安星/四化/格局/大限）
- **卜科**：`liuyao`（六爻纳甲）、`meihua`（梅花易数）、`xiaoliuren`（小六壬）、`zeji`（择吉通书）、
  `liuren`（大六壬骨架：九宗门三传/天将乘临，机械结构标签，无吉凶断语）、
  `lingqi`（灵棋经：三部掷数查 124 课表直录书源断语）
- 六科均经各学科 `dev_tools/check.py` 全绿，仓库根 `tools/check.py --full` 全绿。
- **两条出报告通道**（同一份引擎、同一条四段契约，产出由 `tools/verify_web_parity.py` 逐字节验收）：
  **A 纯前端**（`web/` + GitHub Pages + Pyodide，**零凭证**）；
  **B 云端 Actions**（`reports` 分支固定链接 + issue 回评）。

**基线**：`main`（2026-09-30r：卦身口径修复 + 卦身/三合维度激活，权重表再分配；
30p 六爻附加三维度激活；30l 灵棋经落地为第八科；上一质量门锚 `5b0c958`）。
质量门：`tools/check.py --full` 全绿（含站点构建+自检、网页↔本机同源验收 10 例、pytest 76 项、
六爻黑箱回归 12/18 ≥ 基线 11/18）；工作区无未跟踪垃圾（生成物一律 gitignore）。

---

## 一、现在能不能信（按科）

### 六爻（disciplines/liuyao）— 可上岗助手

| 事项 | 状态 |
|---|---|
| 装卦/历法 | 可信（历法 16 项、爻序 23、金标准 288 例指纹 **`46fd569fbe945814`**；清刻本 822 纳甲/105 卦变/120 世应 0 不合） |
| 用神取法 | 四层：关系法则 → 代码消歧 → 186 键词典 → 世爻兜底 |
| 吉凶方向 | tune **95.0**、holdout **89.7**（strict 对齐分；30r 权重表再分配，与旧口径不可直接比） |
| 附加维度 | 六神临用 / 月令旺衰 / 墓库 / 卦身支 / 三合局 / 用神入三合，30p+30r 激活，strict 全对齐（对表回归） |
| 卦身 | 30r 修复口径（《卜筮正宗》安月卦身诀：世爻阴阳+世爻位→卦身支，非旧日干+代数），古籍例姤/否/坤全合 |
| **应期** | tune top-1 **58.8%**（随机~38）；holdout **50.0%**（随机~36.5）；**日/月/年分列**已输出 |
| 病药 | step5 有界加减；**星煞不进主分**（`shensha_policy`：《卜筮正宗》辟星煞） |
| 断语治理 | 标签/口吻/建议/场景/开场/动变/特殊格局句入 `verdict_texts.json` + `narrative_templates.json` + `advice_rules.json` |
| 呈现 | `render` + SVG；MCP `liuyao.*` |
| 现实命中率 | **无法评估** |

**当前读数（strict，`cd disciplines/liuyao && python tools/check.py`）**：

| 集合 | n | 对齐分 | top-1 | 备注 |
|---|---|---|---|---|
| tune | 20 | **95.0** | 58.8% | 参与过调参（30r 新权重） |
| holdout | 12 | **89.7** | 50.0% | 未参与调参（30r 新权重） |
| wikisource_holdout | 35 | **57.1** | 20.0% | 永不调参（新维度 3 例全对齐） |
| wikisource_direction | 36 | **72.2** | — | 有吉凶无验期 |
| yingqi_holdout | 2 | 87.9 | — | n 过小仅参照 |
| 黑箱回归 | 18 | 12/18 | — | 基线 ≥11 |

> 附加维度（对表回归、机械派生）适用数：tune 六神 10 / 旺衰 16 / 墓库 16 /
> 卦身支 16 / 三合 16 / 用神入三合 16，全部对齐；holdout 12/12 全部对齐。
> 权重表新旧对照见 CHANGELOG 30r。

对外引用：优先 holdout/wikisource，**必须带 n 与集合名**。

### 梅花 / 小六壬 / 择吉 — 已还原，但**分数口径已订正**（2026-09-30 审计）

- 三科均已于 2026-09-29 从 `archive/` 还原至 `disciplines/`，四段管线 + 质量门均通过
  （各科 `dev_tools/check.py` 全绿），金标准指纹未漂移。
- ⚠️ **此前写的"tune/holdout 均 100%"是误导，已订正**。2026-09-30 逐例审计
  （`disciplines/<科>/docs/EVAL-AUDIT.md`，一键复核 `python tools/eval_audit_recheck.py`）
  的结论是：那 100% 是**规则自洽回归数**，不是古籍案例对齐分，更不是精度。
  三科的可评构成如下：

| 科 | 集合 | n | expected 来源 | 自洽项占权重 | 读数含义 |
|---|---|---|---|---|---|
| 梅花 | tune 10 / holdout 13 | 23 | 原书应验 8 + **引擎口径构造 5** | holdout 41.9% | 管线自洽；唯一真判据是 5 档吉凶 |
| 小六壬 | tune 10 / holdout 5 | 15 | 书上原例 2（仅落宫）+ **构造 3** | **100/100** | 落宫/吉凶/事类/主数全查同一张表 |
| 择吉 | tune 10 / holdout 6 | 16 | **全部 engine_derived；古籍日例应验 0 例** | **100/100** | 等价于一次带断言的回归测试 |

- **已发现的硬泄漏**：梅花 `holdout` MH014–MH018 的 expected 出自本仓
  `data/verdicts.json#multi_move_rules`，而该表与这 5 例在**同一次提交 `010bcee`**
  一起引入（`aecb832` 两者皆无）。
- **正确说法**（对外引用请照此）：*规则自洽回归数：梅花 13/13、11/11、6/6、8/8；
  小六壬与择吉各维度 n/n 命中*——**带 n，不带百分比**（三科 n 全 < 20）。
- **想让三科真正可检验，唯一有效动作是建外部独立集**，范式照六爻
  （`case_runner.py` 合并 `*_cases.json` + `case_splits.json` 单列"永不调参"split，
  wikisource 35 例）。**扩判据、调权重都不解决这个问题。**
- 三科 `evaluate.py` 现已在报分时自动打印 `[口径披露]`（集合名 / n / 是否调参 /
  自洽项占比 / 泄漏警告），n<20 时声明不发百分比、改打逐维度命中数。

### 命科 — 机械推演已立（非命运断言）

- 强弱 / 月令定格 / 扶抑喜用 / **调候用神（《穷通宝鉴》查表，2026-09-30g）** /
  大运 8 步 / 流年干支×十神 / **大运×流年机械对照**（含**岁运并临标记**
  2026-09-30u：运=年干支相同即标 `sui_yun_bing_lin`，只标记不批吉凶）
- **格局成败救应（2026-09-30t 主干 + 2026-09-30u 增强）**：成格 / 破格 / 救应成格
  三分类，十格成/忌/救应规则逐条带《子平真诠》原文出处。30u 新增：
  **财格官/煞细分**（成=正官/食伤透；败=七杀透/比劫透/身弱透官；救=食伤制煞/
  合煞存财）、**印格合财存印**（财干与日主六合）、**建禄去伤存官**（伤干被合）、
  **煞刃格**（偏官+阳刃在支+印透=破）；天干五合表入 core（`STEM_WUHE`，
  内核唯一真值源）。
- **从格可判级（2026-09-30w，DEEP-DIVE #3 完成）**：《滴天髓·从象/假从》任注
  驱动——真从/假从/从旺/从强/从气/从势 分级，不再是 tentative 标注。
  机械口径（v4）：生扶只认本气根；三合化气/异类冲破根破印破令（同类库冲不破）；
  从弱 = 从神权重≥4 + 失令 + 无强根（临官帝旺）+ 无本气印 + 透干比劫<3；
  从旺须得令且 sheng_fu≥5 且干不透财官杀食伤；从气=失令有根+金水/木火集中；
  从势=主导差<0.8（从神唯一本气支被异类冲 → 假从）。
  15 例 ZC 书源案例（滴天髓阐微）全入 holdout；ZC 布尔 15/15、真/假 13/15、
  种类 12/15。**已知口径分歧**：8 例 ZP（子平真诠）成败例与滴天髓从格判法冲突
  （如 ZP005 丙火寅甲印被申冲书成格 vs ZC012 同构盘书从杀），判据按滴天髓从格
  论，明细见 CHANGELOG 30w。
- **四柱直填起盘（2026-09-30t）**：`chart_from_pillars()` 直接给定四柱干支起盘
  （书源命例多无公历）；`birth.datetime_source` 标记 "datetime"/"ganzhi"；
  缺柱报错不猜。
- **神煞（2026-09-30u 补全）**：core `shensha.py` 安星含 天乙贵人/文昌/羊刃/禄神/
  红艳/天喜/驿马/桃花/华盖 + 飞刃/金舆/将星/天医/亡神/劫煞/孤辰寡宿/阴差阳错
  （通行起例 verified=false）；narrate 机械呈现、不批吉凶。
- 起运：顺行下一节、逆行上一节；运干十神；空亡；从儿/从财/从杀/专旺（tentative）
- 金标准 `3d4ff149ef6be933`；机械回归 5 例；pytest 覆盖（含 shensha/岁运并临断言）
- **案例对齐评测**：**276 例（tune 30 / holdout 246）**——
  - 调候 225 例（tune 30 / holdout 195，2026-09-30g，《穷通宝鉴》原文提取，逐格引文可回指）；
  - **格局成败 36 例（全 holdout**，《子平真诠评注》第09/13/33/41/45章
    徐注命例，**27 成格 + 5 破格 + 4 救应成格**；30u 新增 5 例：ZP031 煞刃破格
    回归、ZP033 杨杏佛、ZP034 毛状元、ZP035 张载阳、ZP036 陈陶遗；
    ZP027 expected 修正为救应成格（书源何谓救应原文）；
    expected 只记书源判词、徐注取格分歧记 note）；
  - **从格 15 例（2026-09-30w 新增，全 holdout**，《滴天髓阐微》下篇·从象/假从
    任注命例，expected 含 cong_ge/from_kind/from_type）；
  - 读数：tune 100.0%（30/30 调候）、holdout 93.8%（n=246：pillars 189/189、
    tiaohou 21/21、pattern 28/36、cong_ge 满分 11/15）——**表对表回归 + 历法链路
    验证，不是泛化证据**。
- **已知缺口**：**救应 4/5**（书源「败中有成全凭救应」命例主干可判面已用尽，
  剩余依赖地支会合/藏干/化气微观——30w 已把三合化气/六冲引入从格判据，同一套
  冲合工具可回填救应缺口，待立批次）；**从格灰区 3 例**（ZC012 寅令被申冲后印比
  俱失书仍假从、ZC014 透庚辛比无根书假从、ZC015 丁印被癸克书假从——判据按真从）
  与 **kind 缺口 2 例**（ZC011/014 财生杀书从杀、判据从势——待「财生杀」传导
  检测）；**子平/滴天口径分歧 8 例**（ZP004/005/015/020/029/032/034/036 按滴天髓
  从格论，书源为子平真诠成败例——明细 CHANGELOG 30w，属两书体系分歧非引擎缺陷）；
  调候 21/21 为 expected 与引擎同出一部原文的回归验证。
- **不做**：命运断语、流年吉凶定论

### 合参 / 工具

- `tools/check.py`（结构/内核自测/断语键一致/ming 质量门/六爻冒烟/合参/**站点构建+自检**/**网页↔本机同源**/pytest）
- `tools/eval.py`、`tools/demo.py`、`tools/mcp_router.py`、`tools/core_selftest.py`、`tools/text_keys_selftest.py`
- person + outcome-eval
- **交付通道（2026-09-30d 新增）**：`tools/build_web.py`（仓库源码镜像成静态站点 + 清单）、
  `tools/serve_web.py`（本机预览，以仓库为站点根）、`tools/check_web_site.py`（站点自检）、
  `tools/verify_web_parity.py`（两条通道产出同源逐字节验收）；站点源在 `web/`，
  发布走 `.github/workflows/pages.yml`。

---

## 二、怎么跑

### 统一 CLI（v1.0.0 新增）

```bash
yi liuyao cast "占买房子何时有结果"       # 起卦
yi liuyao chart --mode coin                 # 排盘
yi liuyao analyze chart.json                # 推演
yi liuyao narrate analyze.json              # 叙述
yi liuyao render analyze.json               # 报告
yi ming chart --datetime "1990-05-20 10:30" --gender 男   # 命四起盘
yi ming analyze chart.json                  # 命四分析
yi meihua cast "占投资"                     # 梅花起卦
yi meihua chart --way time                  # 梅花排盘
yi xiaoliuren cast "占出行"                 # 小六壬起课
yi zeji chart --date "2026-09-30" --activity 开市       # 择吉排盘
```

> 安装：`pip install -e .`（注册 `yi` entry point）。

### 出报告（两条通道，2026-09-30d）

```bash
# 一条命令出 MD+HTML（六科任一；写进 request.json 或直接给参数）
python tools/report.py --discipline liuyao --question "占求财" \
    --datetime "2026-09-30 10:30" --mode time --outdir reports
python tools/report.py --request request.json --outdir reports --result-json out.json

# 通道 A：纯前端（浏览器内跑同一份引擎，零凭证）
python tools/serve_web.py           # 本机预览 http://127.0.0.1:8737/
#   深链： /?d=liuyao&q=占求财&dt=2026-09-30 10:30&mode=time&auto=1
python tools/build_web.py --outdir site   # 构建可发布的静态站点
python tools/check_web_site.py --site site   # 站点自检（清单↔镜像逐条 sha256）

# 两条通道同源验收（同一请求两边出报告，逐字节比对）
python tools/verify_web_parity.py

# 通道 B：云端（推上 GitHub 后）
#   AI 拼预填 issue 链接 → 用户点提交 → 报告回评 + 落到 reports 分支固定链接：
#   https://raw.githubusercontent.com/<owner>/<repo>/reports/<学科>/latest.md
#   规程见 docs/AI-SOP.md
```

### 各科直跑（[历史，仍有效]）

```bash
# 六爻
cd disciplines/liuyao
python dev_tools/check.py
python scripts/evaluate.py --split tune|holdout|wikisource_holdout|wikisource_direction|huozhulin_holdout|bushi_zhengzong_holdout
python scripts/yi_liuyao.py "所问之事" --when "..."
python scripts/mcp_server.py

# 命科
cd disciplines/ming
python scripts/chart.py --datetime "1990-05-20 10:30" --gender 男
python dev_tools/check.py                # 含机械回归

# 梅花易数
cd disciplines/meihua
python dev_tools/check.py
python scripts/chart.py --way time --question "所问之事"
python scripts/render.py -o outputs/report.md

# 小六壬
cd disciplines/xiaoliuren
python dev_tools/check.py
python scripts/chart.py --way numbers --numbers 7,7,2,3,4 --question "所问之事"
python scripts/render.py -o outputs/report.md

# 择吉
cd disciplines/zeji
python dev_tools/check.py
python scripts/chart.py --date 2026-09-30 --activity 开市 --question "开张吉否"
python scripts/render.py -o outputs/report.md

# MCP（当前仅命 ming 注册；六爻走专用 mcp_server.py）
python tools/mcp_router.py --help
python tools/mcp_router.py --discipline ming --test-narrate
```

### 仓库级 [历史，仍有效]

```bash
python tools/check.py              # 快速门
python tools/check.py --full       # + 案例评测 + 黑箱回归 + pytest tests
python -m pytest tests -q          # 76 项单测
python tools/eval.py               # 五科评测（命科无案例对齐评测，自动跳过）
```

流派开关（改了分数不可比）：`YI_GANZHI_BOUNDARY=day|instant`、`--zi-hour-type late`。

# 拆分/搬家前后的零漂移验收（报告文本 + 思维链 + 人话叙述，115 例）
# ⚠️ 下面的 tools/ 是**学科层**的 disciplines/liuyao/tools/，要先 cd 到学科根：
#    仓库根 tools/ 另有 check.py / eval.py / demo.py / mcp_router.py，两个 tools/ 别混。
cd disciplines/liuyao
python tools/refactor_guard.py --write  guard/base.json   # 改前
python tools/refactor_guard.py --compare guard/base.json  # 改后

**金标准**：`python tools/golden.py verify`；改动后 `capture "理由"`（同上，在学科根执行）。

---

## 三、应期规则（核心资产）

位置：`chain_step5_yp_timing.predict_timing_core`（`_predict_timing` 经 `chain_step5_yp` 再导出，26v 拆出；签名不变）。**通用古例归纳，禁止 case-specific**。

优先级（高→低）：

1. 化出之支逢空 → 出空值日
2. 空而化回头生 → 不作空论，期于生我之日
3. 用神旬空：日辰已冲→当日；久病→冲空；近病→填实
4. 伏藏：飞克伏→先冲飞；飞空得出→伏神值日
5. 月破/入墓/合住：填实、冲墓、冲开
6. 不空：动爻先值日再逢合；静爻值日再逢冲
7. 空亡出空 / 三合 / 原神 / 化出 / 旺相
8. 静爻旺相逢冲即发（r8：用神静爻旺相 + 日辰冲之 → 应于冲日；出处《增删卜易》"静爻旺相，冲之即发；静爻休囚，冲之即破"）
9. 世应位置迟速调节（r9：世应相生速应/相克迟应，调节宽松度；出处《增删卜易》）

**评分（strict / loose 双列）**：
- strict：单一精确支排 top-1 才命中（基线：tune 58.8%，wikisource 20.0%）
- loose：相对窗 / 绝对日期窗覆盖 expected 即命中（tune 94.1%，wikisource 60.0%）
- `--yingqi-mode strict|loose|both`（默认 both）
- 关键发现：引擎在窗内命中大量 case（日级 loose=82.4%），只是未排到 top-1 — **应期区间化后读数更接近真实水平**

**分列**：`evaluate` 输出 `yingqi_day/month/year`（只报数，不设新门槛）。

否证（勿重复踩坑）：

- 病药/药码进应期主排序 → holdout top-1 掉，**已回退**
- 书序整体重排 → 三集全降，**已回滚**
- 回头生全局前插 → 挤掉值日，**改仅空卦**

---

## 四、还欠什么（按优先序）

> 债务的**速查登记 + 提交锚点 + 阻塞说明**见 `docs/TECH-DEBT.md`（单一登记入口）。
> **各科"老师傅程度"差距与可执行改造清单见 `docs/DEEP-DIVE-PLAN.md`**（含代码位置、
> 古籍依据、验收方式）；新门类论证见 `docs/NEW-DISCIPLINES.md`。
> 本节约为叙述版，用于讲清来龙去脉；几处互相指针，**不互为副本**——改一处记得同步。

0. **各科深度缺口**（2026-09-30d 审计，清单已落 `DEEP-DIVE-PLAN.md`，**尚未动引擎**）：
   - 六爻：~~缺三会局、独发独静、卦级反吟伏吟、本卦↔变卦双卦对比、三传克制；旬空只有
     权重、无"真空/假空"标签~~ **缺失环节第一批已落地（2026-09-30e）**：三会方局
     （±0.5 有界，《三命通会》）、独发/独静（只标象不进主分，《增删卜易·独发章》）、
     卦级反吟伏吟（`analyze_repetition(_deep)` 扩展）、真空/假空标签（互斥定性、宁缺勿滥）、
     双卦对比（合处逢冲事已散 −1.5 / 冲中逢合事迟成 +1.5，《黄金策》；卦体合冲判定由
     卦名白名单改内核对应位纳支判——旧白名单两表互相矛盾，属通则修复）、三传克制
     （只标记 score 恒 0）。金标准 capture 带理由；tune/holdout/应期/黑箱全部持平。
     ~~旺衰定性、六神临用、墓库零覆盖~~ **30p 已补**（六神 17 例 / 旺衰·墓库各 32 例
     基准，strict 全对齐；权重表重分配，见 CHANGELOG）。
     ~~卦身、三合零覆盖~~ **30r 已补**（卦身口径修复：原实现按日干阴阳+代数定爻位，
     与《卜筮正宗》安月卦身诀不符，已改世爻阴阳+世爻位推卦身支，古籍例姤/否/坤全合；
     卦身支/三合局/用神入三合三维激活，各 29 例基准，只填主集；权重表再分配，
     tune 95.0 / holdout 89.7，见 CHANGELOG 30r）。
     ~~报告文本无忠实度审计~~ **30s 已补**：`tools/report_faithfulness.py`（narrate 断言
     vs 引擎结构，supported/invented/contradicted 确定性分类，HorosaBench 落点），
     已挂根门；并修正 strength_reason 模板「得令/失令」措辞（与月令旺衰脱钩），
     金标准指纹 → 46fd569f（4 条 narrate 漂移，capture 带理由），见 CHANGELOG 30s。
     仍欠的**评测盲区**：墓库只验日/月墓（动墓·化墓未覆盖），
     反吟/伏吟/进退神/入墓/暗动/月破仍为格局词**子串匹配**。
   - 命科八字：~~完全没有案例评测~~ **调候批已立（2026-09-30g，51 例，《穷通宝鉴》
     原文提取，引擎 51/51）**，但**只有调候一个维度有书源案例**——四柱/十神/藏干/
     格局/神煞/大运仍无书源 expected。~~缺调候用神~~；仍缺通关、病药、格局成败救应、
     三会、四柱间独立刑冲合害、胎元、小运、流月、岁运并临、天克地冲、十神组合、
     女命夫子星。
   - 梅花/小六壬/择吉：~~tune/holdout 恒为 100%~~ **该读数已被 2026-09-30 逐例审计
     推翻并订正**——它是**规则自洽回归数**（expected 与引擎同源），不是古籍案例对齐分，
     更不是精度。结论、构成表与硬泄漏见 §一 与各科 `docs/EVAL-AUDIT.md`
     （一键复核 `python tools/eval_audit_recheck.py`）。三科剩余的**唯一有效动作是建
     外部独立集**（范式照六爻 wikisource 35 例）；扩判据、调权重都不解决。
1. **wikisource 应期泛化** top-1 ~20%（n=35）：等换书或真实反馈 n≥30；**禁止考卷调参**。
   - 《卜筮正宗》`data/sources/bushi_zhengzong.wikitext.txt` 仅 912 字节目录骨架（维基文库 14 卷子页均返回 404）；parser 空白骨架已搭（`dev_tools/fetch_wikisource_cases.py` 同模式），待正文压入即可出外部 case。
   - 《火珠林》2026-09-30 已解析：**2 例 scorable** 入 `huozhulin_holdout` + **5 例定性**（空间/人事）入 `huozhulin_qualitative.json`（因 n=2 且火珠林用纳音/飞伏体系，strict 对齐分偏低属结构性差异，不参与应期 top-1 排名）。
2. ~~择吉通书真黑箱~~ ✅ 已还原（2026-09-29），parser 全绿。
3. ~~小六壬外部书源~~ ✅ 已还原（2026-09-29），parser 全绿。
4. **巨石残余**（已全部清，见 CHANGELOG）：
   `chain_step5` 991→351、`format_reading_output` 445→~30、`step3_analyze_strength` 509→322、
   `_predict_timing` 491→四职责模块 `chain_step5_yp_timing`（26v）、
   `chain_narrate._inject_pattern_tags` 359→三职责模块 `chain_narrate_patterns`（26w）、
   `human_narrative` 979→编排/渲染/格局引文/推因 + 新模块 `human_narrative_segments`（正文段落八段素材，26x）。
   全部零指纹漂移验收通过。
5. **断语残句**：扫描后确认残留多为 argparse help 与测试夹具文本（属 CLI 文档，不是断语），
   真正面向求测者的文案已在 `data/*.json`；此项**暂不再动**，避免误伤。
6. **命科**：从格仍 tentative；运年交互只记关系不批吉凶（有意如此）。
7. 报告「格局详释」依赖案例是否触发格局词。

---

## 五、口径与纪律

1. 对齐分 ≠ 预测率；禁止「准确率 X%」
2. 报分必带：集合名 + n + 是否调参
3. 改引擎：tune/holdout 分列；tune 无故跌破基线即回归；通用规则 + 古籍出处
4. 口径变更记 `docs/CHANGELOG.md`
5. 案例库解读隔离；一卦一事
6. 金标准 `capture` 必须写理由
7. 拆分/搬家以**零指纹漂移**验收（用 `disciplines/liuyao/dev_tools/refactor_guard.py`，
   在学科根以 `dev_tools/refactor_guard.py` 调用；别自己写临时脚本——
   26u 就踩过「脚本传错参数 → 115 例全挂 → 两次指纹一致其实都是全失败」的假阳性，
   该脚本现在会强制校验有效样本数）；巨石看门狗 2200 行

## 五之一、当前状态（2026-09-29c 重构后）

| 学科 | scripts/ 文件数 | dev_tools/ | CLI 状态 |
|---|---|---|---|
| 六爻 `liuyao` | 37（含 step1–5 + facade / narrate / timing / classical_enhancements / effects 等） | 11 | `yi liuyao cast/chart/analyze/narrate/render` |
| 命科 `ming` | 7 | 3 | `yi ming chart/analyze` |
| 梅花易数 `meihua` | 8 | 2 | `yi meihua cast/chart` |
| 小六壬 `xiaoliuren` | 8 | 2 | `yi xiaoliuren cast` |
| 择吉 `zeji` | 8 | 2 | `yi zeji chart` |
| 大六壬 `liuren` | 5 | 2 | `yi liuren chart/analyze/narrate/render` |
| 灵棋经 `lingqi` | 4 | 2 | `yi lingqi chart/analyze/narrate/render` |

- 四段契约：`docs/CONTRACT.md` 定义，根 `tools/check.py` 结构门 + 各科 `dev_tools/golden.py`
  与报告忠实度回归强制（原 `disciplines/base/` 运行时 Protocol 层因零引用已删，见 CHANGELOG）。
- 统一入口：`cli/main.py` → `yi`。
- 五分科各自 `dev_tools/check.py` 全绿，仓库根 `tools/check.py --full` 全绿。

---

## 六、架构要点

```
core/yishu_core     唯一真值源（历法/象数/旬空三刑长生/纳音/三合/星煞/十神/评分）
disciplines/<科>    四段契约 chart→analyze→narrate→render
synthesis           person + 合参 + outcome-eval
tools               check / eval / demo / mcp_router / selftests
tests/              pytest（relations/symbols/najia/yingqi/ming_dayun）
```

- **真值表**：旬空/三刑/十二长生/纳音/三合 已上收 core；看门狗盯同义表名
- **已拆**：`classical_rules_*`、`effects_harmony/structure/change`、`chain_step5` 假拆死体已删
- **已拆（26u）**：`chain_step5_adjust`（step5 八个加减项）、`engine_format_report`（报告九段）、
  `chain_step3_strength`（step3 八个修正项）。三个新模块都不反引调用方，单向依赖。
- **已拆（26v）**：`chain_step5_yp_timing`（应期四职责：收集/法则/排序/组装 + 5 个原闭包辅助提升）。
  `chain_step5_yp` 退化为再导出入口，依赖单向。
- **已拆（26w）**：`chain_narrate_patterns`（叙事格局标签三职责：收集标签 / 收集详释 / 编排注入；
  `_inject_pattern_tags` 原 359 行巨石）。`chain_narrate` 退化为再导出入口，依赖单向，规避循环依赖。
  **再拆的硬约束**：`thinking_chain.py` 从 `chain_step3` / `chain_step5` 再导出一批名字，
  搬动前先 grep `from chain_stepN import` 确认不是再导出项，否则断链。
- **已拆（26x）**：`human_narrative_segments`（正文段落素材八段：旺衰 / 结论开头 / 动变 / 特殊格局 /
  应期 / 综合定性 / 病药 / 星煞 + 私有辅助 `_pos_name`/`_question_focus`/`_clean_reason`/
  `_resolve_bing_yao_shensha`/`_line_on_pos`/`_line_plain` + 模板加载；从 `human_narrative` 按域切出）。
  `human_narrative` 保留编排（`build_human_narrative`）/ 渲染（`render_human_markdown`）/
  格局引文（`_extract_pattern_tags`/`_select_relevant_quotes`/`_pattern_advice_hint`）/ 推因
  （`_build_explain_summary`），并再导出搬移名。`human_narrative_segments` 只 import 叶子模块
  （`chain_verdicts`/`chain_tables`），单向依赖、无循环。
- **已拆（2026-09-29 B3 内核命名）**：`ming_tables.py` 曾兼存**命、卜两科共用**的纳音/三合/星煞，
  模块头却写「唯一消费方：命科，卜科不用」——**文档与事实矛盾**（B3 实锤）。按归属拆后：
  纳音 + 三合局分组 → `symbols.py`（顺带补齐该模块章程本就写着的「三合」），
  星煞 → 新 `shensha.py`（模块头按 CONTRACT §二 标注命卜两科共用），
  `ming_tables` 只剩命科专属（藏干十神 / 大运 / 命宫身宫）。消费方 6 处同步，**取值零变化**。
- **已拆（2026-09-29 B2 首批）**：`classical_rules_patterns` 909 → 369 行（原 `scripts/` 最大），
  切出 `classical_rules_combo`（`_check_broken_combo` + `analyze_triple_combo`）与
  `classical_rules_growth`（`analyze_twelve_growth` + `analyze_desperate_relief`）；
  门面 `classical_rules` 改从新模块取数，`__all__` 24 项不变、消费方零改动。
  **裁剪 import 要按别名判 `X as Y`**——首版按原名判，删掉了 `CINTERP`，
  冒烟当场 36/36 归零（记 AUDIT §四之四）。
- **质量门编码（2026-09-29）**：`yishu_core.runtime.utf8_subprocess_env()` 让所有 gate 子进程
  `PYTHONUTF8=1`，与父进程解码对齐——仓库级 `tools/check.py` 在中文 Windows 上由恒红转全绿。
  **新写子进程调用必须走它**，别手拼 `env`；CLI 还要 `force_utf8_stdio()`。
- **MCP**：六爻 7 方法（专用 `mcp_server.py`）；命 ming 经 `tools/mcp_router.py` 注册 chart/analyze/narrate/render/list_methods（meihua/xiaoliuren/zeji 已归档）

---

## 七、变更索引（查 CHANGELOG）

| 记号 | 内容 |
|---|---|
| 26e–m | 整洁/断语第一批/命骨架/大运/巨石拆分 |
| 26n | 真值表上收 + step5 假拆清理 + 命科机械扩充 |
| 26o–s | 星煞口径/建议库/场景提示/键自测 |
| 26t | internal-depth-pack：断语收尾 + effects 拆分 + pytest + MCP 四科 + 应期分列 + 运年交互 |
| 26u | 巨石收尾：step5 / 报告排版 / step3 三拆（零指纹漂移）+ 死导入清理 |
| 26v | 巨石收尾续：_predict_timing 491 行应期巨石按职责切出（零指纹漂移）+ 死代码清理 |
| 26w | 巨石收尾续：chain_narrate._inject_pattern_tags 359 行格局标签巨石按职责切出（零指纹漂移）+ 死导入清理 |
| 26x | 巨石收尾续：human_narrative 979 行按域拆——正文段落八段素材切到 human_narrative_segments，编排/渲染/格局引文/推因留 human_narrative（零指纹漂移）+ 死导入清理 |
| 26y | CI 硬化：修复 pytest 从根目录收集失败（importlib 模式 + testpaths，零逻辑改动）——`pytest -q` 从根干净 76 passed |
| 26z | 范围收缩：仅保留 `ming`+`liuyao`，`meihua`/`xiaoliuren`/`zeji` 归档 `archive/`；清理 `tools/`+`synthesis/` 引用与死代码；绑定文档同步 |
| 26aa | 历史债务文档化：新增 `docs/TECH-DEBT.md` 统一登记（已清偿/待清偿 + 提交锚点 + 防新债纪律）+ 治理扫描（死脚本、冗余 skills 判定**无需动作**） |
| 27-tidy | 仓库清理（清 gitignore 生成物与遗留 `.worktrees/`）+ 修 `tools/eval.py`（ming 无评测器不再误报失败、默认改回 `tune+holdout`、对齐 docstring）+ 本 handoff 重写 |
| 29a | **B1 测试迁出生产 `scripts/`**（→ 科内 `tests/`）；**质量门编码修复**（子进程 UTF-8，仓库级门由恒红转全绿）；`ctext`/`ctpl` 五副本收敛 `chain_verdicts`；**B3 内核命名拆分**（纳音/三合→`symbols`、星煞→新 `shensha`）；**B2 首批**（`classical_rules_patterns` 909→369 行）——逐项零指纹漂移验收 |
| 29c | **v1.0.0 结构重构（五科底座归一）**：新增 `disciplines/base/` 共享层（protocol + cli 基类）；六爻 scripts/ 58→28→37 文件；统一 CLI `yi <discipline> <command>`（`cli/main.py` + pyproject entry point）；5 科 `tools/` → `dev_tools/`；`synthesis/normalize.py` + `tools/eval.py` 支持五科；新增 `docs/ARCHITECTURE.md` + `docs/MIGRATION.md` —— 功能 zero-drift 验收 |
