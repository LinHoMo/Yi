# 易（Yi）· 文档总索引

> **2026-10-29（第三百三十批·文档整理）新增**：本仓 Markdown 文档此前没有一张地图，
> 新人只能靠文件名猜、靠搜索碰。本表是**唯一入口**——每份文档一句话职责 ＋ 状态
> （活文档／生成物／归档留证／历史索引），并给出三条阅读路径。
>
> 状态口径：
> - **活文档**：会随批次持续更新，是当前口径的出处；
> - **生成物**：由 `dev_tools/` 某脚本重生成，**不要手改**（改了下批就被覆盖）；
> - **归档留证**：一次性报告／盘点，结论已入 CHANGELOG，留在仓里只为可追溯；
> - **历史索引**：只存批号与一句话，用于检索，不含明细。

---

## 一、三条阅读路径

| 你是 | 先读 | 再读 | 收尾 |
|---|---|---|---|
| **第一次接触本仓** | `README.md`（做什么、现在什么水平） | `CAPABILITY.md`（对外口径与读数） | `AGENTS.md`（改代码前必读的三条铁律） |
| **要改代码的贡献者** | `AGENTS.md` | `CONTRACT.md`（四段契约：chart→analyze→narrate→render） | 本表 → 对应学科的 `SKILL.md` |
| **要查本次架构整改结果的人** | `ARCHITECTURE-PLAN.md`（完成台账 + V1–V15 收口实测 + 偏差/欠账） | `GOVERNANCE.md`（工具台账与档位门槛） | 本表 → 对应批次 |
| **要引用对外数字的人** | `CAPABILITY.md` | `liuyao/README.md`／`bazi/README.md` | `docs/CHANGELOG.md`（最近窗口）＋ `docs/CHANGELOG-HISTORY-INDEX.md`（逐批一句话） |

---

## 二、根级（7 份）

| 文件 | 一句话 | 状态 |
|---|---|---|
| `README.md` | 仓库总览：两科做什么、现在的真实水平（含"不是预测率"的口径提醒） | 活文档 |
| `AGENTS.md` | **项目级铁律**：三条不可动摇的规则、目录与依赖契约、共享打包层契约 | 活文档 |
| `CONTRACT.md` | 四段契约的判据本体（chart→analyze→narrate→render 的键白名单与禁边） | 活文档 |
| `CAPABILITY.md` | 对外能力声明与全部读数（每行带 n 与出处，**口径不许省**） | 活文档 |
| `GOVERNANCE.md` | 治理地图：工具台账、批次在册、待人面事项 | 活文档 |
| `DOCS.md` | 本表：全仓文档索引 | 活文档 |
| `ARCHITECTURE-PLAN.md` | **架构整改完成记录**（原总方案 340 批压缩）：D1–D3 决策、完成台账、V1–V15 收口实测、偏差与欠账 | 归档留证 |

## 三、六爻（`liuyao/`，19 份）

### 主入口

| 文件 | 一句话 | 状态 |
|---|---|---|
| `liuyao/SKILL.md` | 宿主模型读的操作合同（意图路由、能力边界、禁句表） | 活文档 |
| `liuyao/README.md` | 六爻科说明与读数表（"现在的真实水平"整片） | 活文档 |

### 文档（`liuyao/docs/`）

| 文件 | 一句话 | 状态 |
|---|---|---|
| `liuyao/docs/CHANGELOG.md` | 批次流水，**只保留最近窗口**（2026-10-29 起；更早见索引） | 活文档 |
| `liuyao/docs/CHANGELOG-HISTORY-INDEX.md` | **逐批一句话索引**（342 批精简：原 154 批事实标题＋更早 49–156 批一句话；全文归档已删） | 历史索引 |
| `liuyao/docs/JUDGMENT-TABLE.md` | 判定表：书证底稿、9 格、13 条题类覆盖、20 处代码覆写清单（另 7 条已迁规则数据层 verdict_overrides），含"不换判词"的结论 | 活文档 |
| `liuyao/docs/CASE-LIBRARY-AUDIT.md` | 案例库应期抽取审计（dz 底本通道） | 活文档 |
| `liuyao/docs/YIIN-CASE-AUDIT.md` | 《易隐》案例集审计（`yiin_holdout`） | 活文档 |
| `liuyao/docs/ADJUDICATION-BRIEF.md` | 待裁简报（**生成物**：`dev_tools/adjudication_brief.py` 重生成） | 生成物 |
| `liuyao/docs/TIANHOU.md` | 占天候试验台协议（读数规则、换源即改口径） | 活文档 |
| `liuyao/docs/ONTOLOGY-CARDS.md` | 易学知识图谱本体卡片（L0–L4 概念人读版） | 活文档 |
| `liuyao/docs/YI-KNOWLEDGE-GRAPH.md` | 易学知识图谱手册（演化树、象数层、书证层、AI 检索视图） | 活文档 |
| `liuyao/docs/RULE-ENGINE-REFACTOR-PLAN.md` | 规则仲裁层改造：当前架构（rules/ 独立树、21 cap+7 verdict_overrides）与剩余待办（T28/T29/T30/T31） | 活文档 |

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

## 四、八字（`bazi/`，14 份）

| 文件 | 一句话 | 状态 |
|---|---|---|
| `bazi/SKILL.md` | 八字科宿主模型操作合同 | 活文档 |
| `bazi/README.md` | 八字科说明与读数表 | 活文档 |
| `bazi/docs/CHANGELOG.md` | 八字批次流水，**只保留最近窗口**（2026-10-29 起；更早见索引） | 活文档 |
| `bazi/docs/CHANGELOG-HISTORY-INDEX.md` | **逐批一句话索引**（342 批精简：原 81 节标题保留；全文归档已删） | 历史索引 |
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

## 五、共享层与 DSH 适配器（`plugins/` 与 `dsh-plugin/`，5 份）

| 文件 | 一句话 | 状态 |
|---|---|---|
| `plugins/SKILL.md` | 共享技能正文唯一真源 | 活文档 |
| `plugins/README.md` | 共享打包层说明（一次构建、分发到 DSH） | 活文档 |
| `plugins/CHANGELOG.md` | 共享层批次流水 | 活文档 |
| `dsh-plugin/README.md` | DSH 宿主说明 | 活文档 |
| `dsh-plugin/CHANGELOG.md` | DSH 宿主批次流水 | 活文档 |

> 497 批起只保留 DSH 一个宿主（claude/codex/gemini/yan 已删除）。
> 宿主侧的 `engine/`、`skills/`、`src/` 是**构建产物**（不入库），由
> `node plugins/scripts/build.mjs` 生成、`node plugins/scripts/selftest.mjs` 自检——**不在本表内**。

---

## 六、维护口径

- 新增文档时，**同批在本表登记一行**（不登记就等于没有）。
- 文档转归档时，把状态改成"归档留证"并在 `docs/CHANGELOG.md` 写一句为什么；
  归档只搬不改写正文（唯一例外是**路径修正**——链接要活）。
- 文档成为生成物时，在表里写明"由哪个脚本重生成"，并把该脚本登记进
  `liuyao/dev_tools/governance_map.py` 的台账。
- 本表与实际文件不一致时，以**实际文件**为准并同批修正本表——本表是索引，不是真值源。
