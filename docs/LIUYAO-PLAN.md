# 六爻 · 专项规划

> 版本 v0.0.1（2026-09-22）｜对象：`Yi/liu-yao/`（24751 行 Python + 44k 行文档/数据/产物）
> 目标：解决你提的三个问题——**规范不够、预测水平不够、展示程度和成果不够**。

> **执行进度（2026-09-22）**：M0 全部完成；M1 完成第一批（规则表合一，288 例零漂移）；
> M2 完成 2.2 应期择优两批；M3 完成报告应期表、门户真分数、死链、命名。
> 逐条实况见 `disciplines/liuyao/docs/HANDOFF.md`；分数变化与口径见 `disciplines/liuyao/docs/CHANGELOG.md`。
> 未做：M1b 巨石拆分与断语外置、M2.1 用神决策表、M2.4 扩样、M3 呈现三合一与 SVG 卦盘、M4 迁移。

## 〇、先说一件必须接受的事

当前号称的 `tune 100% / holdout 97.7%` **今天无法复现，也无法采信**。证据：

| 问题 | 证据 |
|---|---|
| 评分器已丢失 | `data/cases/blind_eval_split.py`、`blind_eval_v8.py` 被删，仅存 git HEAD；现仓库无可用评分脚本 |
| 字段漂移送分 | `scripts/score.py` 读 `yingqi_summary/composite_score`，引擎实际输出 `yingqi/final_score` → 读不到时白送分 |
| 权重三套互斥 | 案例自带 0.4/0.3/0.2/0.1，`score.py` 里是 0.35/0.10/0.20/0.15 |
| 回归大面积失败 | `regression_test.py` 18 项只过 10 项 |
| 用例集已废 | `thinking_chain_tests.py` 12 项全 0 |
| "覆盖率 100%" 是假指标 | `coverage_test.py` 36/36 只验证段落有没有返回，不验证对错 |
| 跑评测会污染输入 | `run_blind_v5.py` 的 `date_from_str` 把月干伪造成"甲X"、默认日期 2024-06-01、hour=10 → 应期评分基于错的干支历 |
| 42 例里 5 例报错 | ZS021–025 跑不通（`_meta` 仍写 30 例，实际 30 ZS + 12 HO） |

**结论**："预测水平不够"的第一层真实含义是**你现在没有一把准的尺子**。所以本规划把"可测量"排在"提准"之前——顺序不能反，否则每轮"优化"都是在给噪声打分。

---

## 一、现状诊断（按三个问题归类）

### 1.1 规范不够

- **过程式巨石，零抽象**：`thinking_chain.py` 6396 行、`classical_analysis.py` 4318 行、`liuyao_engine.py` 4042 行，**0 个 class**。thinking_chain 单文件 38 张常量表（584 行）、861 个 `if`、1522 处中文字面量；`step5_synthesize` 一个函数 940 行。
- **同一规则三处双写且取值不一致**：`NAJIA_BRANCHES`/`HEXAGRAM_TRIGRAMS`/`EIGHT_PALACES`/`HE_PAIRS`/`BREAK_PAIRS`/`TOMB_MAP` 各存三份。判定冲突实例：日破（`classical_analysis.py:1080-1124` vs `thinking_chain.py:1653/1971/2158`）、绝处逢生（`:1892` vs `:1996-2030/2657`）、回头克（`:1679-1709` vs `:3307`）。
- **`precision_gaps.md` 的 10 个缺口已全部实现，但以"三处各写一遍"的方式实现**——所以文档看着像已修，实际是三份可能互相矛盾的判据。这不是缺功能，是缺架构。
- **数据双份**：`data/hexagrams.json` 与代码内嵌卦表各一套（宫/纳甲/上下卦 0 差异，但 34/64 卦辞被截断、json 缺"遁"用"遯"、py 里革卦"巳日"应作"己日"），且 json 只被 visualization 读，还带 `../../skills/liu-yao` 硬编码回退路径。
- **断链**：`king_wen_sequence` 已删除，`liuyao_engine.py:1880/2118` 仍 import，被 `except ImportError` 静默吞掉。
- **调用路径缺字段**：`build_hexagram_result()` 不产 `advanced_analysis`，只有 CLI 才走 `enhance_reading()` → 同一引擎两种输出形状。
- **仓库卫生**：112 个 `_debug_*/_patch_*` 脚本曾被提交进 `data/cases/`；`outputs/`、`references/pattern_reference.md`、`scripts/build_html_report.py`、`scripts/visualize_shap.py` **未纳入 git**；303KB `logs/divination_events.jsonl` 与 `index.html`、`assets/portal_data.json` 反而全量入库；4 个 0 commits ahead 的分支（`holdout/benchmark`、`optimize/holdout-v2/v3`、`external/classical-holdout`）；**无 README、无 requirements、无 AGENTS.md**；文件名带版本号（`run_blind_v5.py`）、文档指向他人机器的绝对路径（`C:\Users\Lin\Desktop\skills\liu-yao`）。
- **历法精度是真实 bug，不是玄学**：注释称 sxtwl 优先、实际 lunar_python 优先（且 `sxtwl.Lunar()` 是旧 API，装了也大概率崩）；本机两库皆无时走近似表 → `get_year_stem_branch` **完全不判立春**（2024-02-03 返回甲辰，应癸卯），月支用固定节气日，边界 ±1–2 天错，粗估约 7% 日期受影响；无任何日历自检。

### 1.2 预测水平不够

- **用神取法靠 207 项问题词典硬编码**（`_QUESTION_USE_GOD_MAP`）。旁证：SKILL.md 专门写了一段"交叉校验（禁止省略）——思维链选的用神若与指南冲突以指南为准"，等于承认代码选不准，用提示词兜底。
- **应期不可验证**：应期输出是密度化的支/日罗列（"重点应期：X日、Y日…"），缺少"哪个法则推出哪个日、事后对错如何回收"的闭环，因此无法评分，也无法改进。用户真正在意的恰恰是这一个字段。
- **断语库无出处治理**：`QUOTE_DATABASE` 与散落的 1500 条字面量混在代码里，无"出处/可核对/已勘误"标记。
- **反馈信号被丢弃**：`logs/divination_events.jsonl` 已积累 303KB 真实求测记录，但没有任何结果回收（对/错）与再评估管线。

### 1.3 展示与成果不够

- **三套呈现互不相通、风格不一致**：门户 `index.html`（1999 行，自包含可 `file://` 直开，但卦盘只是 CSS `<i>` 色块条，不是 SVG；"打开完整样例报告"按钮 `window.open('sample_report_ZS001.html')` **指向不存在的文件**；盲评看板一排硬编码 100 分）／`build_html_report.py`（1120 行，未入库，与 `visualization.build_html_report` **命名撞车的第二套生成器**，表格为主）／人话 `.md`。
- **`visualization.py`(1501 行，富 SVG) 与 `build_html_report.py`(1120 行) 是两套并行的报告引擎**，`outputs/reports/` 里 `sample.html` 与 `sample_report.html` 内容重复。
- **"SHAP" 名不副实**：`visualize_shap.py` 是 matplotlib 手画因子贡献条形图，与机器学习归因无关，靠命名显得专业——这类东西一旦被内行看到会反噬可信度，改名 `factor_waterfall.py`。
- **样例质量不一致**：`outputs/感情卦_巽之涣_20260922.md` 是合格的黄金样例（排盘表＋六神临用＋兄弟持世引《火珠林》＋卦身临财＋格局详释＋公历应期 2026-10-08/11-07＋象判边界）；`正缘卦_雷风益之晋_20260922.md` 是残缺薄版（只有应期与推演，缺排盘表/六神/持世/格局）。两份都没入库。
- **MCP 只到排盘**：`mcp_server.py` 提供 `divinate/quick_reading/validate_hexagram/get_classical_quotes/list_methods`，与 `api_spec.md` 一致，但**未暴露人话解读、报告导出、盲评**；反过来 SKILL.md 强调的五步链与强制叙事要素在 API 层无对应导出。
- 根目录 `reports/` 是空目录；没有一键"问题 → 成品报告"的闭环。

---

## 二、施工阶段

### M0 止血与立规（1 轮，不碰推演逻辑）

| # | 任务 | 验收 |
|---|---|---|
| 0.1 | 仓库卫生：提交删除 112 个 `_debug/_patch`；`outputs/`、`logs/`、`__pycache__`、`scratch/` 进 `.gitignore`；未入库的 4 个文件逐个定去留；4 个空分支删（先 `git log` 确认无独有提交） | `git status` 干净；`git ls-files` 无生成物 |
| 0.2 | **恢复唯一评分器**：从 HEAD 取回评分逻辑 → `core/eval/`，删 `score.py` 的重复实现与漂移字段；统一权重为单一来源（案例文件不携带权重） | `python tools/eval.py --split tune --split holdout` 打印两集合各自均分与 n；同输入两次运行分毫不差 |
| 0.3 | 修评测输入失真：`run_blind` 系列改为显式传完整干支时间，禁止伪造月干与默认 2024-06-01 | 重跑后基线分数变化被记录并解释（这是**真基线**，此前 100% 不可信） |
| 0.4 | **历法内核 + 自检**：`core/calendar` 独立成模块；内嵌 1900–2100 精确节气表（数据文件，可逐条核对）；修立春年界与节气月界；sxtwl/lunar-python 降为显式可选加速并修 API 误用；补 30+ 边界日断言 | `python -m yishu_core.calendar --self-check` 全绿；含 2024-02-03→癸卯 等边界用例 |
| 0.5 | 补 `requirements.txt`/`pyproject.toml`、README、AGENTS.md（已建）；修死引用 `king_wen_sequence` | 干净环境 `pip install -e . && python tools/check.py` 通过 |
| 0.6 | 归并三套测试口径为一套（`regression/coverage/thinking_chain_tests` 三合一），废掉 0/12 的旧用例集 | 一个入口、退出码可信、失败项可定位 |

**M0 交付判据：能一句话回答"这套引擎现在到底几分"。**

### M1 内核合一与拆分（2–3 轮，破坏性重构）

| # | 任务 | 验收 |
|---|---|---|
| 1.1 | 规则表单点化：六张双写表 + 内外两份卦表合一，`data/hexagrams.json` 与代码取一为真值源，另一份删除；顺带修卦辞截断/遯遁/己巳之误（逐条记 `docs/TEXTUAL-CORRECTIONS.md`） | `grep` 全仓每表仅一处定义 |
| 1.2 | 按四段契约拆巨石：`chart`（装配）/`analyze/*`（22 个关系检测器一文件一族）/`narrate`/`render`；`liuyao_engine` 退化为 CLI 薄壳 | 无单文件 >1200 行；`build_hexagram_result` 与 CLI 输出**同一 schema** |
| 1.3 | 断语/引文外置：1500+ 中文字面量 → `data/verdicts.json`（每条带 `source`、`school`、`verified`）；861 个 `if` 改数据驱动查表 | 代码里不再出现成段断语；`step5_synthesize` < 200 行 |
| 1.4 | 消除双写冲突：日破/绝处逢生/回头克等由单点判定，其余环节只消费结论 | 同卦两次路径产出的判据完全一致（新增一致性测试） |
| 1.5 | 每步跑 tune+holdout | tune 均分不低于 M0 真基线 −2，否则当轮停止 |

### M2 断卦能力提升（3–4 轮，按可测维度逐项推进）

| # | 维度 | 做法 | 可测验收 |
|---|---|---|---|
| 2.1 | **用神取法正确率** | 207 项问题词典 → 取法决策表（问类 × 求测者性别/身份 × 六亲），每类 ≥5 例；把 SKILL.md 的"LLM 交叉校验"降级为兜底而非主判 | 新增"用神取法"独立子指标，目标 ≥95%，删掉提示词里的祈祷段 |
| 2.2 | **应期精度**（用户最在意、也最可验证） | 统一应期法则链（旺衰/动静/空破墓绝/合冲刑害 → 应支 → 公历日期），每步可回溯；从案例中抽出**带明确应期的子集**单独打分 | 应期命中率作为对外主指标；报告里应期能显示"由何法则推出" |
| 2.3 | 格局判定一致性 | 10 项古籍缺口在单点内核上重测，逐格局配正反例（成立/不成立/待补） | 每格局有正负例，无"只报成立不报破局" |
| 2.4 | 外部效度 | 新增 20–30 例**未参与任何调参**的古籍案例进永久 holdout；从 `logs/divination_events.jsonl` 建结果回收模板（事后对错登记），有反馈的实占逐步进评测 | holdout 与 tune 分数并列展示，标注 n |
| 2.5 | 场景覆盖 | 按求测类（财/病/婚/行/失/讼/文/孕）建断语覆盖矩阵，找空档补规则 | 每类有 ≥3 例通过，无默认落到"事业"这种错分 |

### M3 展示与成果（1–2 轮）

| # | 任务 | 验收 |
|---|---|---|
| 3.1 | **三套呈现合一**：`render` 单一入口进 `core/report`，删掉并行生成器；卦盘改真 SVG（爻线/六亲/六神/世应/空破标记/动变箭头）；`visualize_shap.py` → `factor_waterfall.py` | 一条命令一种产物；`grep` 无第二套 HTML 模板 |
| 3.2 | **一键闭环**：`python -m yi_liuyao "所问之事" --when ...` → 排盘＋思维链＋正文＋单文件 `report.html` | 从零到可分享报告一条命令，无人工拼裝 |
| 3.3 | 门户修伤：死链、硬编码 100 分看板换成真可复现分数（tune/holdout 分列＋n＋口径说明）、案例可切换、样式与报告统一 | `file://` 直开可用；看板数字与 `eval.py` 一致 |
| 3.4 | **定黄金样例为唯一模板**：以 `感情卦_巽之涣` 那份的要素完整度为最低标准，写进 SKILL.md 验收；残缺薄版不得交付 | 新样例逐条过"六神临用/持世/卦身/格局详释/公历应期/边界克制"清单 |
| 3.5 | README + 截图 + 3 个样例进 `docs/samples/`；MCP 扩到完整解读与报告导出，与 SKILL.md 工作面对齐 | `tools/demo.py` 产出可分享的三件套 |

### M4 并入易的体系

- 目录迁至 `Yi/disciplines/liuyao/`，`SKILL.md` 只留学科内容，通用铁律上收 `Yi/AGENTS.md`
- 接入 `synthesis/person` 档案：一卦一事 → 同一人的多次卜问可累积、可回看、可反馈
- 与梅花易数同题互验（不同起局法对同一事的判据差异，是检验内核抽象是否正确的最便宜手段）

---

## 三、明确不做

- ❌ 宣称现实世界预测命中率（六爻属象征推演与方向参考）
- ❌ 为让某案例过关而加私有别名/case-specific 断语
- ❌ 医疗、法律、投资的自动决策口吻
- ❌ 无基线驱动的 UI 大重构（M3 之前不动门户）
- ❌ 在未审计的数据上把 ZS021–030 计入 holdout（其中多例与 tune 同源或卦名残缺，已列 excluded）

## 四、里程碑顺序不可调换的理由

`规范/可测量(M0)` → `内核合一(M1)` → `准确度(M2)` → `展示(M3)`。

先做 M3 会得到漂亮的门户和一个仍不可信的分数；先做 M2 会在三处双写的判据上继续分叉，且没有尺子判断改好了还是改坏了。**唯一例外**：若你需要对外有一个能看的东西，可把 3.4（黄金样例模板）+ 3.2（一键出报告）提到 M0 后，其余展示层留在 M3。
