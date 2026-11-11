# 易（Yi）· 文档总索引

> **2026-10-29（第三百三十批·文档整理）新增**：本仓 Markdown 文档此前没有一张地图，
> 新人只能靠文件名猜、靠搜索碰。本表是**唯一入口**——每份文档一句话职责 ＋ 状态
> （活文档／生成物／归档留证／历史索引），并给出阅读路径。
>
> 状态口径：
> - **活文档**：会随批次持续更新，是当前口径的出处；
> - **生成物**：由 `dev_tools/` 某脚本重生成，**不要手改**（改了下批就被覆盖）；
> - **归档留证**：一次性报告／盘点，结论已入 CHANGELOG，留在仓里只为可追溯；
> - **历史索引**：只存批号与一句话，用于检索，不含明细。
>
> **份数口径**：各节标题所注份数为最近统计，随登记增减，**不单独钉死**——以
> `git ls-files '*.md'`（排除 handoff/scratch 等运行目录）实测为准。514 批起
> 不在文内依赖硬编码份数，避免减量后成假事实（见 AGENTS.md §六）。

---

## 一、阅读路径

| 你是 | 先读 | 再读 | 收尾 |
|---|---|---|---|
| **第一次接触本仓** | `README.md`（做什么、现在什么水平） | `CAPABILITY.md`（对外口径与读数） | `AGENTS.md`（改代码前必读的三条铁律） |
| **要改代码的贡献者** | `AGENTS.md` | `CONTRACT.md`（四段契约：chart→analyze→narrate→render） | 本表 → 对应学科的 `SKILL.md` |
| **要查本次架构整改结果的人** | `ARCHITECTURE-PLAN.md`（完成台账 + V1–V15 收口实测 + 偏差/欠账） | `GOVERNANCE.md`（工具台账与档位门槛） | 本表 → 对应批次 |
| **要引用对外数字的人** | `CAPABILITY.md` | `liuyao/README.md`／`bazi/README.md` | 各科 `liuyao/docs/CHANGELOG.md`／`bazi/docs/CHANGELOG.md`（最近窗口）＋ 对应 `CHANGELOG-HISTORY-INDEX.md`（逐批一句话） |
| **要按缺口继续迭代的人** | `GOVERNANCE.md`「当前真缺口」（523 批逐条核实，历史待办现状以此为准） | `CAPABILITY.md`「已知欠账」 | 对应批次的 git 提交（主 CHANGELOG 只留一行摘要） |
| **要整理仓库／清垃圾的人** | `REPO-HYGIENE.md`（六类边界、目录契约、生成物再生、清理清单） | `devkit/root/check_repo_hygiene.py` 实跑 | `AGENTS.md` §一／§二（铁律与依赖契约） |
| **联网检索的网页端 AI／只想读知识的人** | `llms.txt`（机器可读入口与 raw 直链） | `KNOWLEDGE.md`（自包含知识速读） | `examples/` 两份引擎实跑结论 |

---

## 二、根级

| 文件 | 一句话 | 状态 |
|---|---|---|
| `README.md` | 仓库总览：两科做什么、**给网页端 AI 读者的 raw 直链入口**、安装与构建、现在的真实水平（含"不是预测率"口径提醒） | 活文档 |
| `REPO-HYGIENE.md` | **仓库整理单一入口**：六类边界速查、目录真源/产物契约、生成物再生与垃圾清理、内容纪律、一次性整理流程；由 `devkit/root/check_repo_hygiene.py` 常驻复验 | 活文档 |
| `AGENTS.md` | **项目级铁律**：三条不可动摇的规则、目录与依赖契约、共享打包层契约 | 活文档 |
| `CONTRACT.md` | 四段契约的判据本体（键白名单与层间禁边；§四 键数表由契约门逐项核对） | 活文档 |
| `CAPABILITY.md` | 对外能力声明与全部读数（每行带 n 与出处，**口径不许省**） | 活文档 |
| `GOVERNANCE.md` | 治理地图：五档定义与判绿口径、待人面事项（**分布读数现取，514 批起不再在文内抄表**） | 活文档 |
| `DOCS.md` | 本表：全仓文档索引 | 活文档 |
| `ARCHITECTURE-PLAN.md` | **架构整改完成记录**（原总方案 340 批压缩）：D1–D3 决策、完成台账、V1–V15 收口实测、偏差与欠账；**文首有 514 批勘误块**（正文按登记时点保留，五处现值以勘误为准） | 归档留证 |
| `REARCHITECT-PROPOSAL.md` | **全面重估立项书**（539 批）：现状实跑证据、三种候选形态、迁移路径与判红矩阵；**D1–D6 已于 540 批 §九 逐条裁决结案**（A 继续／B 暂缓／C 不采纳、四条硬约束维持），文首「待拍板」按登记时点保留、**现行口径以 §九 为准**，不产生待办 | 归档留证 |
| `WORKTREE-AUDIT.md` | **历史 worktree 清点（552 批）**：8 个工作树逐个核对停点、脏状态、主线归宿与可回流项裁决；结论为**零补丁回流**，另给删除判据（已并入 `REPO-HYGIENE.md` §四） | 归档留证 |

## 三、六爻（`liuyao/`）

### 主入口

| 文件 | 一句话 | 状态 |
|---|---|---|
| `liuyao/SKILL.md` | 宿主模型读的操作合同（意图路由、能力边界、禁句表） | 活文档 |
| `liuyao/README.md` | 六爻科说明与读数表（"现在的真实水平"整片） | 活文档 |

### 文档（`liuyao/docs/`）

| 文件 | 一句话 | 状态 |
|---|---|---|
| `liuyao/docs/CHANGELOG.md` | 批次流水（523 批压缩）：**最近 15 批、每批一行结论摘要**；窗口／单批长度由 `devkit/root/check_docs_index.py` 现场判，更早见索引 | 活文档 |
| `liuyao/docs/CHANGELOG-HISTORY-INDEX.md` | **逐批一句话索引**（342 批精简：原 154 批事实标题＋更早 49–156 批一句话；全文归档已删） | 历史索引 |
| `liuyao/docs/JUDGMENT-TABLE.md` | 判定表：书证底稿、9 格、题类覆盖与代码覆写清单，含"不换判词"结论；未签条目只作设计输入、不得进代码 | 活文档 |
| `liuyao/docs/CASE-LIBRARY-AUDIT.md` | 案例库应期抽取审计（dz 底本通道） | 活文档 |
| `liuyao/docs/CASE-LIBRARY-AUDIT-YINGQI.md` | 案例库**应期**抽取审计（519 批由 `dev_tools/build_yingqi_set.py` 生成；525 批起报告头改数据源 sha256 指纹＝幂等，与落盘集同由 [46] `--check` 逐字复验） | 生成物 |
| `liuyao/docs/YIIN-CASE-AUDIT.md` | 《易隐》案例集审计（`yiin_holdout`） | 活文档 |
| `liuyao/docs/ADJUDICATION-BRIEF.md` | 待裁简报（**生成物**：`dev_tools/adjudication_brief.py` 重生成；525 批起只读 `--check` 同源复验挂 CI，探针走临时目录） | 生成物 |
| `liuyao/docs/TIANHOU.md` | 占天候试验台协议（读数规则、换源即改口径） | 活文档 |
| `liuyao/docs/ONTOLOGY-CARDS.md` | 易学知识图谱本体卡片（L0–L4 概念人读版；`dev_tools/render_ontology.py` 重生成，与图谱逐字同源由 [44] 门守，524 批起） | 生成物 |
| `liuyao/docs/YI-KNOWLEDGE-GRAPH.md` | 易学知识图谱手册（演化树、象数层、书证层、AI 检索视图） | 活文档 |
| `liuyao/docs/RULE-ENGINE-REFACTOR-PLAN.md` | 规则仲裁层**结案记录**（510 批压成结案态：现行 `rules/`＋`engine/` 结构、D1–D5/T28–T31 完成台账、维持边界；方案正文已删） | 归档留证 |

### 参考（`liuyao/references/`）

| 文件 | 一句话 | 状态 |
|---|---|---|
| `liuyao/references/case_library.md` | 六爻古籍案例库（**解读路径禁止读取**，见 AGENTS 铁律二） | 活文档 |
| `liuyao/references/classical_synthesis.md` | 四大经典文献综合参考 | 活文档 |
| `liuyao/references/najia_rules.md` | 纳甲装卦规则参考 | 活文档 |
| `liuyao/references/interpretation_guide.md` | 断卦方法论详解 | 活文档 |
| `liuyao/references/pattern_reference.md` | 十五大经典格局参考 | 活文档 |
| `liuyao/references/source_ledger.md` | 六爻书源台账（可得性与出处状态） | 活文档 |
| `liuyao/references/odd_questions.md` | 奇问杂占读法（问得怪、问得虚） | 活文档 |

## 四、八字（`bazi/`）

| 文件 | 一句话 | 状态 |
|---|---|---|
| `bazi/SKILL.md` | 八字科宿主模型操作合同 | 活文档 |
| `bazi/README.md` | 八字科说明与读数表 | 活文档 |
| `bazi/docs/CHANGELOG.md` | 八字批次流水（523 批压缩）：**最近 15 批、每批一行结论摘要**；更早见索引 | 活文档 |
| `bazi/docs/CHANGELOG-HISTORY-INDEX.md` | **逐批一句话索引**（342 批删全文；510 批去重并补录 10-29～11-02 的 110 节标题） | 历史索引 |
| `bazi/docs/EVAL-PLAN.md` | 八字案例评测方案（分维与门槛的出处） | 活文档 |
| `bazi/docs/SANMING-SIKU-COLLATION.md` | 《三命通会》两转录渠道对拍报告 | 归档留证 |
| `bazi/references/bazi_liuqin_gongwei.md` | 六亲·家宅·家人读法 | 活文档 |
| `bazi/references/bazi_jibing_tizhi.md` | 疾病·体质读法（不诊断、不预测生死） | 活文档 |
| `bazi/references/bazi_qianshi_yanpan.md` | 前事·验盘（用已发生的事校准） | 活文档 |
| `bazi/references/bazi_tiaohou.md` | 调候（《穷通宝鉴》月令取用） | 活文档 |
| `bazi/references/bazi_yue_shi_ge.md` | 五虎遁／五鼠遁歌诀 | 活文档 |
| `bazi/references/bazi_shishen_terminology.md` | 十神术语古今映射 | 活文档 |
| `bazi/references/bazi_nayin_shiyi.md` | 纳音释义 | 活文档 |
| `bazi/references/api_spec.md` | 八字科 API 说明 | 活文档 |

## 五、共享层与 DSH 适配器（`plugins/` 与 `dsh-plugin/`）

| 文件 | 一句话 | 状态 |
|---|---|---|
| `plugins/SKILL.md` | 共享技能正文唯一真源 | 活文档 |
| `plugins/README.md` | 共享打包层说明（一次构建、分发到 DSH） | 活文档 |
| `plugins/CHANGELOG.md` | 共享层批次流水 | 活文档 |
| `dsh-plugin/README.md` | DSH 宿主说明 | 活文档 |
| `dsh-plugin/CHANGELOG.md` | DSH 宿主批次流水 | 活文档 |

> 497 批起只保留 DSH 一个宿主（claude/codex/gemini/yan 已删除）。
> 宿主侧的 `engine/`、`skills/`、`src/`、`SKILL.md` 是**构建产物**（不入库），由
> `node plugins/scripts/build.mjs` 生成、`node plugins/scripts/selftest.mjs` 自检——**不在本表内**。

---

## 六、维护口径

- 新增文档时，**同批在本表登记一行**（不登记就等于没有）。
- 文档转归档时，把状态改成"归档留证"并在 `docs/CHANGELOG.md` 写一句为什么；
  归档只搬不改写正文（唯一例外是**路径修正**——链接要活）。
- 文档成为生成物时，在表里写明"由哪个脚本重生成"，并把该脚本登记进
  `liuyao/dev_tools/governance_map.py` 的台账。
- 本表与实际文件不一致时，以**实际文件**为准并同批修正本表——本表是索引，不是真值源。
- 两科主 CHANGELOG 的**窗口与单批长度**由 `devkit/root/check_docs_index.py` 现场判（523 批扩面）：
  退出窗口的批号＋日期只准搬进历史索引，不准删；每批只留一行自足的结论摘要，
  过程叙述与收口明细交 git 历史。历史待办现状以 `GOVERNANCE.md`「当前真缺口」为准。

---

## 七、对外可发现层（第五百四十九批新建）

> 这一层解决「网页端大模型只能读静态文本、不会执行 Python」的缺口：
> 把代码产出的结论与判据知识变成 GitHub / raw / Pages 上可直接抓取的入库产物。
> 构建器与铁律说明见 `outreach/README.md`。

| 文件 | 一句话 | 状态 |
|---|---|---|
| `KNOWLEDGE.md` | 面向 AI 的自包含术数知识速读（术语表、四段契约、三条铁律、FAQ）；由构建器拼装 | 生成物 |
| `kb/INDEX.md` | 面向 GitHub 读者与联网 AI 的判据篇目导览＋raw 直链（与随包 INDEX 用途不同） | 生成物 |
| `examples/liuyao-example.md` | 固定输入下由四段流水线实跑生成的六爻完整结论报告 | 生成物 |
| `examples/liuyao-time-example.md` | 固定输入下由四段流水线实跑生成的六爻「时间起卦」结论报告（确定性起卦，演示 time 模式） | 生成物 |
| `examples/bazi-example.md` | 固定输入下由四段流水线实跑生成的八字完整结论报告 | 生成物 |
| `outreach/README.md` | 对外层的真源／产物／铁律／命令说明 | 活文档 |
| `outreach/KNOWLEDGE-BODY.md` | 知识正文的人写真源（构建器把它拼进 `KNOWLEDGE.md`） | 活文档 |
| `outreach/RELEASE-NOTES.md` | 自动发布 Release 的正文真源（口径声明随包，不用 `--generate-notes`） | 活文档 |

> 非 Markdown 的入口 `llms.txt`、`site/`（gitignore，Pages Actions 生成）、
> `.github/workflows/pages.yml` 与 `release.yml` 不在本表统计范围内。
> 入库产物一律由 `python outreach/build_outreach.py --write` 生成、`--check` 逐字节复验，
> **不要手改**；改动真源后须同批重跑 `--write` 并一起提交。
