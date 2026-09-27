---
name: yi
description: 易·统领 skill，中国传统术数的路由与口径统领。命（四柱八字：一生格局、趋势、宜何业、何时起伏）与卜（六爻：具体一事的趋向与应期）的意图路由、选科、脚本调用监督与合参入口。当用户提到算命、占卜、算卦、测命、批命、起卦、排盘、断卦、八字、四柱、六爻、合参，或问"某事成不成、什么时候成、我命如何"时，先用本 skill 路由，再进入对应学科的 SKILL.md。
---

# 易 · 统领 Skill

> 易 v0.0.1｜本文件是给 LLM agent 的工作指令（给人看的介绍见 `README.md`）。
> 项目铁律在 `AGENTS.md`，按 `docs/CONTRACT.md` §四.2 的要求本文件**只引用、不复制**；与任何学科 SKILL.md 冲突时以 `AGENTS.md` 为准。

## 〇、这一层管什么

易不是工具合集，是统领层：**意图路由 → 选科 → 调脚本 → 翻译输出 →（若同一人多科）合参**。
当前实现状态（2026-09 范围收缩后）：**卜科仅六爻可用**（`disciplines/liuyao/` 六爻已接四段契约薄适配层）；`meihua/`/`xiaoliuren/`/`zeji/` 已于 2026-09 经范围收缩**归档**至 `archive/`，不在当前范围；**命科（`ming`）机械推演已立**（强弱/格局/喜用/大运/流年对照，无命运断语）；合参层（`synthesis/`）已实现。

两条诚实原则：

1. 路由到建设中的科时，如实告知"该科建设中"，只能指向规划（`docs/YI-PLAN.md`、`disciplines/README.md`），不得假称能答。
2. **建设中 ≠ LLM 可以心算替代。** 铁律一对没有脚本的科同样成立：没有可跑的起局代码，就说做不了；不得手排八字、手起梅花卦、手心算应期。

## 一、意图路由

### 1.1 路由总表

| 用户问题特征 | 科 | 目录 | 状态 |
|---|---|---|---|
| 一生的格局与趋势：宜何业、何时起伏、性情禀赋、大运流年 | 命 · 四柱八字 | `disciplines/ming/` | **已实现机械推演**（四柱/强弱/格局/喜用/大运/流年对照；无命运断语）。执行规程见 `disciplines/ming/SKILL.md` |
| 具体一事的趋向与应期：成不成、吉不吉、何时应 | 卜 · 六爻纳甲 | `disciplines/liuyao/` | **已实现**（迁移前旧实现，已接四段契约薄适配层、可入合参层）。执行规程见其 `SKILL.md`，现状见其 `docs/HANDOFF.md` |
| 同上，想以数字/时间快速起卦 | 卜 · 梅花易数 | `archive/meihua/` | **已归档**（2026-09 范围收缩，不在当前范围） |
| 同上，临场速断 | 卜 · 小六壬 | `archive/xiaoliuren/` | **已归档**（2026-09 范围收缩，不在当前范围） |
| 择吉日：搬家/嫁娶/开业/动工选日子 | 卜 · 择吉 | `archive/zeji/` | **已归档**（2026-09 范围收缩，不在当前范围） |
| 面相、手相、风水堪舆 | — | — | **不做**（`AGENTS.md` 范围条款：不实现、不预留目录）。明确婉拒并说明本仓库范围 |

### 1.2 命与卜怎么判别

- **命问句**：主语是"这个人/这一生"，没有具体事件，时间尺度以年、十年计。
  典型问法："帮我看看命"、"我适合做什么行业"、"我哪几年运势好"、"我这辈子财运如何"。
- **卜问句**：具体一件事 + 期待时间点。
  典型问法："这笔投资能不能成"、"丢的东西什么时候找到"、"这个月官司吉不吉"、"他哪天回来"。
- **一句话判据**：问"一个人一生的趋势"走命；问"一件事的结果与时机"走卜。

### 1.3 歧义时反问（不要猜）

| 用户原话 | 反问 |
|---|---|
| "看看我的婚姻" | 是问一生的婚姻格局与节律（命），还是某一段具体婚事/某个具体人的结果（卜）？ |
| "看看我的财运" | 是问这辈子财运格局（命），还是某笔具体的钱能不能成、何时进账（卜）？ |
| "看看我的健康" | 是问长期体质趋势（命），还是某场具体的病 outcome（卜）？**两种都要提示以医疗专业意见为准** |
| 两样都想问 | 分开起盘：命一盤、卜一卦，不混在同一盘/卦里；结论的汇总交给合参层（§六） |

### 1.4 信息收集（收齐了才算路由完成）

- **卜 · 六爻**：所问何事、求测者性别与身份（影响用神选取，如女家占婚取官鬼）、起卦方式与时间（默认铜钱法、当前系统时间）。
- **卜 · 梅花易数 / 小六壬 / 择吉**（2026-09 已归档至 `archive/`，不再维护）：以下说明仅保留作历史参考——梅花所问何事、起卦方式（默认当前时刻，亦可报数/两数）、求测者性别（体用主从参考）；小六壬所问何事、起课时间（默认当前时刻，亦可报数取时）；择吉所问何事（活动类型：搬家/嫁娶/开业/动工…）、拟选日期范围。
- **命（科建成后）**：出生公历年月日时、出生地（真太阳时校正）。输入格式以 `synthesis/README.md` 人的档案 `birth` 字段（含 `calendar_policy` 历法口径）为约定。
- 缺信息影响起局时（如占婚缺性别），照六爻 `SKILL.md` 的做法：**补进 input 重跑脚本**，让引擎自己换到正确法则上，不由 LLM 另判。

## 二、LLM 的职责（正面清单）

`AGENTS.md` §一.1 划的线，正面表述只有三段，多一段都是越权：

1. **收集求测信息**（按 §1.4）；
2. **调用该科脚本**（命令见 §五）；失败重试一次，仍失败如实报"排盘异常"，**不得手动替代**；
3. **把脚本输出的结构化数据翻译成当事人看得懂的话**——是翻译不是重写：正文里每个象数结论都要能在脚本输出里找到出处。

**严禁心算或"推算"**：起局、排盘、装卦、定宫、纳甲、安世应、推六亲、配六神、查旬空、判旺衰、算应期、识别格局、定建除黄黑道二十八宿——以上全部只能由 Python 完成。

断卦的执行细节（叙事要素、主/次应期、质量自检、措辞箴言）跟随各科 SKILL.md：六爻见 `disciplines/liuyao/SKILL.md`（梅花/小六壬/择吉 已归档，见 `archive/` 对应目录）。

## 三、一卦一事（`AGENTS.md` §五）

同一问题不重复占卜（"再三则渎"）。用户在既问之后**换实质角度**提问——换用神、换层面、假设未来、比较两人、测人心——应提议另起一卦，不得在原卦里延伸硬推。超出用神覆盖域的断言（对方家庭背景、未来伴侣身份、心里想什么）属臆测，不讲。

## 四、口径诚实（`AGENTS.md` §一.3，交付前必守）

- 仓库内所有分数都是**古籍案例对齐分**（引擎输出与《增删卜易》等案例要点的吻合度），只用于回归审计，**衡量不了现实世界命中率**。禁止说成"预测率"，禁止出现"预测准确率 X%""断事如神"类表述。
- 报分必须同时给：**集合名 + 样本量 n + 是否参与过调参**；对外引用最保守的那个集合。
- 当前读数（2026-09-23 `python tools/check.py` 全门绿、退出码 0 复验）：

| 科 | 集合 | 对齐分 | n | 口径说明 |
|---|---|---|---|---|
| 六爻 | tune | 93.9% | 20 | 参与过调参 |
| 六爻 | holdout | **87.5%** | 12 | 未参与调参 |
| 六爻 | wikisource_holdout | 57.3% | 35 | 维基文库《增刪卜易》原本，从未参与任何调参 |
| 六爻 | wikisource_direction | 72.2% | 36 | 有吉凶无验期；应期 N/A |
| 梅花 / 小六壬 / 择吉 | — | 已归档（2026-09 范围收缩） | — | 历史读数见 git 历史 |

  **六爻应期**：tune top-1 58.8%、holdout top-1 50.0%（strict；随机约 36–38%）；
  wikisource_holdout top-1 20.0%（n=35，泛化未证明）。详见 `docs/HANDOFF.md`。
- 医疗、法律、投资、重大决策必须提示**以专业意见为准**。
- 凶象用"偏向 / 有…信号 / 结构上"，不用"注定 / 一定 / 绝无可能"。
- 无判据的安慰叙事一律不写（反例与规则见六爻 `SKILL.md` 实践箴言 3）。

## 五、各科实际可跑的命令

### 5.1 六爻（迁移前旧实现，已接四段契约薄适配层）

以下照抄 `disciplines/liuyao/docs/HANDOFF.md` §二（2026-09-23 逐条实跑核验）。
`pip install` 在**仓库根**执行；其余命令的工作目录都是 **`disciplines/liuyao/`**：

```bash
pip install -e .                          # 仓库根执行；内核包 yishu-core，无必需第三方依赖

cd disciplines/liuyao
python tools/check.py                     # 全部质量门（版本/历法/爻序/金标准指纹/冒烟/样式/用例/回归/对齐分/外部集）

python scripts/liuyao_engine.py --mode coin --question "所占之事"                 # JSON
python scripts/liuyao_engine.py --mode coin --question "所占之事" \
       --format html --save-html outputs/report.html                              # 一条命令出单文件报告
python scripts/evaluate.py --split holdout --save                                 # 古籍案例对齐评测

# 四段契约入口（与命科同构，供合参层消费；薄适配既有引擎，不引入新断法）
python scripts/chart.py --mode time --datetime "2026-09-23 10:00" \
       --question "所占之事" -o scratch/chart.json            # 起卦 → 排盘 JSON
python scripts/analyze.py scratch/chart.json -o scratch/analyze.json   # 推演 → conclusion + chart_summary
python scripts/narrate.py scratch/analyze.json                            # 正文
python scripts/render.py scratch/analyze.json -o outputs/report.md        # 报告
```

analyze 输出的 `conclusion`/`chart_summary` 可直接喂 `synthesis/cli.py add-divination`
进合参层归一化（`normalize_liuyao` 已适配）。

历法口径开关（默认值即上表分数的依据，改动会让分数不可比）：
`YI_GANZHI_BOUNDARY=day|instant`（交节"当日即换"还是"精确到时刻"）；
`--distinguish-zi-hour --zi-hour-type late`（夜子时按换日派起盘，默认不作次日）。

### 5.2 梅花 / 小六壬 / 择吉（已归档，2026-09 范围收缩）

以下三科已于 2026-09 经范围收缩**归档**至 `archive/meihua/`、`archive/xiaoliuren/`、`archive/zeji/`，命令仅作历史参考，不再维护：
`chart`（起局）→ `analyze`（推演）→ `narrate`（正文）→ `render`（报告），
各脚本均有 argparse CLI、`--help` 可看、`-o/--out` 写文件（缺省 stdout）。

```bash
cd disciplines/meihua          # 或 xiaoliuren / zeji，接口同构
python tools/check.py                       # 全部质量门（指纹/冒烟/基线；--full 加案例评测）
python tools/check.py --raise               # 确认改进后抬升基线（只准前进不准后退）

python scripts/chart.py --question "所占之事" --datetime "2026-09-23T10:00"   # 起卦 JSON
python scripts/chart.py --way numbers --year-num 5 --month 7 --day 12 --hour-num 10
python scripts/analyze.py chart.json -o analyze.json                          # 推演
python scripts/narrate.py analyze.json                                        # 正文
python scripts/render.py analyze.json -o outputs/report.md                    # 报告
python scripts/evaluate.py --split holdout                                    # 古籍案例对齐评分
```

各科差异点：
- **meihua**：`chart` 支持 `--way datetime|lunar|numbers|two_numbers`（lunar 传 `--year/--month/--day/--hour-branch`，numbers 传 `--year-num/--month/--day/--hour-num`，two_numbers 传 `--upper-num/--lower-num`），另有 `--motion 行|立|坐|卧`（数应迟速）。
- **xiaoliuren**：`chart` 支持 `--way datetime|lunar|month_day_hour|numbers`（numbers 为变通取数法，`--numbers "7,7,2,3,4"`），`--topic` 显式给事类。
- **zeji**：`chart` 输入为日期（`--date`）与活动（`--activity`，缺省从 `--question` 识别），输出建除/黄黑道/二十八宿因子。

### 5.3 合参层（`synthesis/`，已实现）

工作目录是 **`synthesis/`**：

```bash
cd synthesis
python cli.py init P001 --solar "1990-05-20 07:15"                      # 新建档案 → person/P001.json
python cli.py validate P001                                             # 校验档案
python cli.py add-divination P001 --discipline ming \
       --analyze-json <ming/analyze.json> --at "1990-05-20 07:15"      # 登记占问（归一化，需该科 analyze 输出）
python cli.py record-outcome P001 --event-id EVT001 --result 应验         # 回填现实结果
python cli.py guide P001                                                 # 生成阶段性指导 → guidance/P001.md
python cli.py selfcheck                                                  # 合参层自检
```

提示：`add-divination` 的良输入是**各科 `analyze` 段输出的 JSON**（先用 §5.2 的
chart→analyze 拿到），系统自动归一化为统一占问记录；不传 `--asked` 则取 analyze 的问句。

### 5.4 仓库级命令（工作目录是仓库根）

```bash
python tools/check.py            # 全仓库质量门（版本/结构/内核/三科/六爻冒烟/合参自检；--full 加案例评测与六爻回归）
python tools/demo.py             # 全科演示（六爻 + 命 两科各一例 + 合参演示，走真实 CLI）→ tools/scratch/demo.md
powershell -File tools/install.ps1 -Check -Demo   # 环境安装 + 质量门 + 演示
```

## 六、合参入口（`synthesis/`）

合参层**已实现**（`synthesis/`：person / normalize / cross_rules / guidance / cli）。两科（六爻/命）输出可归一化为统一占问记录（方向吉/平/凶、应期、判据所本），再按 `docs/YI-PLAN.md` §二与 `synthesis/README.md` §二的四条裁决规则合参：

1. **各守其位**：命定趋势与节律，卜决具体一事之趋向与应期。任何一科越位（用六爻断人一生格局、用八字断某笔钱能否当日到账）→ 判为无效输入。
2. **同向则确**：各科指向一致时可提升陈述强度（仍不用"注定"）。
3. **异向则卜**：冲突时不平均、不取巧，先回溯起局时间/干支边界/用神选取（经验上分歧九成来自时空口径与取用错误）；核对后仍分歧，则如实并列两种趋向及其触发条件，交当事人。
4. **禁止拼贴安慰叙事**：没有经文依据或卦象理据的"未来会更好"一律不写。

口径纪律：各科年界/子时口径不一致时（`calendar_policy`），合参先标记时空分歧、不直接比结论；命科未实现时按规则降级为"该维度未参评"。

当用户已有档案、要求"综合看看"时：先 `cli.py validate` 校验档案完整性（birth.ganzhi 必须带 `calendar_policy`），再按 §5.3 流程登记/合参；未建档则 `cli.py init`。

## 七、文档地图（2026-09-23 逐一核实存在）

| 文件 | 写什么 |
|---|---|
| `AGENTS.md` | 三条铁律、目录依赖契约、命名规范、引擎改动验收门槛、一卦一事 |
| `README.md` | 给人看：这是什么、怎么跑、现在的真实水平 |
| `docs/YI-PLAN.md` | 总规划：定位、架构、里程碑 M0–M5、验收标准 |
| `docs/CONTRACT.md` | 新学科接入契约：四段管线、内核提供什么、口径与流派显式化 |
| `docs/CHANGELOG.md` | 仓库级变更日志（跨科/内核/口径）；学科内细节见各科 CHANGELOG |
| `disciplines/README.md` | 学科状态表：谁已实现、谁建设中、谁不做 |
| `disciplines/liuyao/SKILL.md` | 六爻执行规程（收集信息/起卦/解读/自检/箴言） |
| `archive/meihua/SKILL.md` | 梅花执行规程（已归档，2026-09 范围收缩） |
| `archive/xiaoliuren/SKILL.md` | 小六壬执行规程（已归档） |
| `archive/zeji/SKILL.md` | 择吉执行规程（已归档） |
| `disciplines/liuyao/docs/HANDOFF.md` | 六爻交接：哪些可信、怎么跑、还欠什么 |
| `synthesis/README.md` | 合参层契约与实现：人的档案 schema、裁决规则、指导输出格式 |
