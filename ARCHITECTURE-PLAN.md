# 易（Yi）· 架构整改总方案

> **存在理由（2026-10-29 立）**：本仓在"零耦合、单一真源、机检治理"三条上已经做到了
> 很多仓库做不到的地步——门禁 100+ 个、负例自证成常态、文档与实跑不符即判缺陷。
> 但治理只覆盖到**学科内部**：`kernel/` 把引擎内核抽出去了，**门禁内核没有抽**；
> 两科 `check.py` 各自全绿，**根级六份治理文档不在任何门的扫描域**；六爻与八字共用
> 同一份 `CONTRACT.md`，**形态却是 1 : 6.7**。本文件想把这三处补上。
>
> **读者边界**：本文件是**派发件**。§五 的每张 TODO 卡与 §六 的提示词自含全部信息，
> 执行 Agent 拿到卡片后不需要回头读本文件其余部分。
> **效力**：与 `AGENTS.md`／`CONTRACT.md` 冲突时以那两份为准；本文件只排期，不改铁律。
> 本文件**不写分数、不写准确率**（AGENTS.md §一.3）。
>
> **本文件自身的纪律**：[36] 门会把未登记入库的 `.md` 判红，故本文件与 `DOCS.md`
> 登记行同批（A0-0 已完成，实测 `check_docs_index.py` rc=0）。

---

## 零、决策已定（2026-10-29）

三个决策点已拍板，本方案按此展开。执行时不再重新讨论。

### D1 = C（折中）· 两科 `core/yishu_core/` **维持入库**

| 做 | 不做 |
|---|---|
| CI 加 `kernel-sync` job，强制 `python kernel/sync_kernel.py --check` | 不把 `core/` 加进 `.gitignore` |
| 两科 `core/**` 进 `.gitattributes` 标 `linguist-generated` | 不改 [35] 门判据 |
| 新增 `sync_kernel.py --standalone <科>` 显式产出可独立拷贝的目录 | 不手改 `core/`（现状即禁止） |

**理由**：入库保住"单目录拷走即可运行"；而"可拷走"这件事原本是**隐性假设**
（靠 git 里恰好有副本），C 方案把它改成**显式命令**（`--standalone`），
同时用 CI job 把 [35] 从"本地有时才跑"变成"每次提交必跑"。
激进方案 A 会让全新克隆必须先 sync，把一条隐性便利换成一条显式义务，收益不抵代价。

### D2 = 复制分发 · `devkit/shared` 走 `sync_devkit.py`，不用 import

**理由**：① 与 `kernel` 同范式，直接复用 [35] 的字节比对写法，不引入第二套机制；
② 保住"两科各自单目录可独立运行"；③ 不破坏零耦合（AGENTS.md §二 1/2）。
import 方案要求 `devkit` 在 `sys.path` 上，会把"可拷走"直接打死，**不采用**。

### D3 = 中档 · 八字形状对称做到"受同等审计"

| 含 | 不含 |
|---|---|
| 补 `tests/` ＋ CHANGELOG 三件套瘦身 ＋ 契约欠账审计 ＋ 各科剖面 ＋ 共享门分发接入 | 不克隆六爻的 `step1–step5` 推演链与 9 个 `classical_enhancements_*` |

**理由**：整改目标是**形状对称**（受同等机检），不是**规模对称**（行数相等）。
六爻 22,877 行里含 5 步推演链与 9 个增强模块，八字术数结构不同，照搬只能造出空壳。
**"八字行数追平六爻"不是本方案的目标，任何执行者都不要把它当目标。**

---

## 一、现状（2026-10-29 实测读数，非印象）

### 1.1 形态地图

```
Yi/
├── 根：8 份治理 md（含本文件）                       ← 无任何门覆盖
├── kernel/          引擎内核真源（common 13 + variants 8 = 6,677 行）
├── liuyao/          scripts 49 · core 17 · dev_tools 64 · tests 5 · data 16MB
├── bazi/            scripts  8 · core 15 · dev_tools 43 · tests 0 · data 49MB
├── plugins/         分发真源（SKILL.md + mcp/8 + scripts/4）
└── 5× 宿主适配器    各自清单 + 产物（产物不入库）
```

依赖方向三条，现状成立：

```
kernel/yishu_core  ──sync_kernel.py──▶ <科>/core/yishu_core   （产物，入库；[35] 字节比对）
<科>/core          ◀────────────────  <科>/scripts            （单向）
<科>/scripts       ──build.mjs──▶     plugins/engine/ ──▶ 5 宿主 src/（产物，不入库）
```

### 1.2 规模读数

| 项 | 六爻 | 八字 | 合计 |
|---|---|---|---|
| `scripts/` 文件 / 行数 | 49 / 22,877 | 8 / 3,443 | 57 / 26,320 |
| `dev_tools/` 文件 / 行数 | 64 / 16,675 | 43 / 8,710 | 107 / 25,385 |
| `core/yishu_core/` 文件 / 行数 | 17 / 4,495 | 15 / 3,853 | — |
| `tests/` | 5 | **0** | 5 |
| `data/` 占盘 | 16 MB | 49 MB | 65 MB |
| 门禁小节编号 | `[0]–[7]`、`[11]–[20]`、`[26]–[36]`（**缺 8/9/10/21–25 共 9 个空号**） | `[0]–[28]` 连续 | — |

**读法（按 §六.4 逐条看语义，不拿计数当结论）**：

- `dev_tools` 与 `scripts` **行数 1 : 1**（25,385 vs 26,320）。门禁不是"配套"，
  它已经是与产品等体积的第二套代码。
- 两科**同名 `dev_tools` 文件 13 个**，实测构成（逐条看语义，不是一律当欠账）：

| 类别 | 文件 | 数 |
|---|---|---|
| **门**（`check_*`） | `check_case_isolation` `check_cli_encoding` `check_doc_refs` `check_house_conventions` `check_layer_contract` `check_regex_lists` `check_rule_registry` `check_source_readings` | **8** |
| **编排器** | `check.py`（六爻 954 行 / 八字 622 行） | 1 |
| **器**（非门） | `baselines` `golden` `feedback_store` | 3 |
| 包名文件 | `__init__.py`（差异仅 docstring，2 行） | 1 |

> **自更正（2026-10-29）**：本文件初稿写"13 个里有 10 个是门"，按 §六.4 逐条核后
> 实为 **8 个门 + 1 个编排器**。编排器 `check.py` 各科内容本就不同（门数与学科专属门不同），
> **不属欠账、不归并**；`__init__.py` 差异仅 docstring，**无归并价值**。
> 故 A1-1 的归并名单是 **11 个**（8 门 + 3 器），不是 13 个。

- 两科**同名 `scripts` 6 个**（`analyze`/`chart`/`evaluate`/`narrate`/`render`/`__init__`）
  ——这是 `CONTRACT.md` 四段契约**要求**的形状重复，**是刻意的，不是欠账**，整改时不碰。
  实测两科这 6 个文件全部逐字节不同（内容本就不同科）。

### 1.3 归并难度实测（`cmp -s` 逐字节 + 行数对拍）

A1-1 的 11 个归并项，按实测分三档。**这是每张子卡的起点，执行者不必重新测**：

| 档 | 文件 | 六爻 / 八字 行数 | 起点 |
|---|---|---|---|
| **L0 零风险** | `check_case_isolation.py` | 103 / 103 | 逐字节相同，直接取一份 |
| | `check_house_conventions.py` | 133 / 133 | 逐字节相同 |
| | `check_layer_contract.py` | 192 / 192 | 逐字节相同 |
| **L1 小差异** | `check_cli_encoding.py` | 262 / 261 | 逐行 diff，差异 ≤1 行级别 |
| | `check_doc_refs.py` | 267 / 268 | 同上，**且八字侧正被外部会话占用，见 §4.0** |
| | `check_regex_lists.py` | 182 / 182 | 同行数，内容不同 |
| | `golden.py` | 157 / 166 | 器 |
| | `baselines.py` | 254 / 250 | 器 |
| **L2 大差异** | `check_source_readings.py` | **692 / 443** | 差 249 行，需逐条归因 |
| | `check_rule_registry.py` | 269 / 293 | 需逐条归因 |
| | `feedback_store.py` | 178 / 237 | 器，需逐条归因 |

**关键技术验证（决定 A1-1 子卡不用动 `check.py`）**：
两科 `check.py` 对共享门的调用形态是**子进程路径串**
（例：`liuyao/dev_tools/check.py:862` → `"dev_tools/check_case_isolation.py")`）。
归并后产物仍落在 `<科>/dev_tools/<同名>.py`，**调用约定不变**——
所以 A1-1 的 11 张子卡**一律不得改两科 `check.py`**，改调用约定的活全部归 A1-2。
这条接缝保证了 11 张子卡的写域两两互斥。

### 1.4 现状基线（整改前的零点）

```bash
python liuyao/dev_tools/check.py   # rc=0（2026-10-29，Python 3.13.14 / Windows）
python bazi/dev_tools/check.py     # rc=0（同上）
python liuyao/dev_tools/check_docs_index.py   # rc=0
```

两科全绿。后续每一批的验收都必须以"不低于这条基线"为地板。

### 1.5 文档体量

| 文件 | 字节 |
|---|---|
| `liuyao/docs/CHANGELOG-ARCHIVE.md` | 355,751 |
| `bazi/docs/CHANGELOG.md`（**未做 330 批瘦身**） | 239,520 |
| `liuyao/docs/CHANGELOG.md` | 171,351 |
| `liuyao/docs/CHANGELOG-HISTORY-INDEX.md` | 37,011 |
| `dsh-plugin/CHANGELOG.md` | 35,688 |
| 其余 4 份宿主 + `plugins/CHANGELOG.md` | 39,609 |
| **合计** | **≈ 875 KB** |

---

## 二、诊断（七个架构级问题）

> 排序按"不处理的后果严重度"，不按工作量。每条给实测证据，不给印象。

### A1 · 门禁基建两科各造一套（P0）

- **证据**：§1.2 的 13 个同名文件，其中 8 个是门、3 个是器。
- **后果已经在发生**：六爻有 `batchnum_audit.py` / `check_docs_index.py`，八字**两个都没有**；
  六爻有 `CHANGELOG-ARCHIVE.md` + `HISTORY-INDEX.md`，八字**一个都没有**（240 KB 未瘦身）。
  同一份 `check_doc_refs.py` 在两科是两份代码（267 / 268 行），
  任何一科改了判定口径，另一科**静默分叉**——而两科 `check.py` 都报 rc=0，看不出来。
- **与铁律的关系**：AGENTS.md §二 的"内核唯一真值源"条款列了十二类数据不得存第二份，
  但**只管引擎内核，不管门禁内核**。引擎侧做到了，工具侧是同一类问题的另一半。

### A2 · 根级治理文档无任何门覆盖（P0）

- **证据一（扫描域）**：两科 `check_doc_refs.py` 均为 `for p in sorted(DISC.rglob("*"))`，
  `DISC = 学科根`。根级 8 份 md **不在扫描域内**。
- **证据二（悬空引用，实测）**：根无 `docs/` 目录，但
  `AGENTS.md:200`、`AGENTS.md:226`、`AGENTS.md:262`、`CONTRACT.md:94`
  四处以 `docs/CHANGELOG.md` 形式引用它——四份文档里三份是**判据出处**。
- **证据三（判定力被削弱）**：`_resolves()` 有 basename 兜底
  （`any(p.name == name for p in DISC.rglob(...))`），即便扫到也会靠同名文件放行，
  分不清"根级"与"学科级"。
- **后果**：最权威的四份文档，恰恰是最没人校对路径的四份。

### A3 · 两科形态不对称，却共用一份契约（P0）

- **证据**：六爻 49 脚本 / 22,877 行 vs 八字 8 脚本 / 3,443 行；
  六爻有 `tests/` 八字没有（AGENTS.md §二 与 README 已**声明并接受**）；
  `CONTRACT.md` §二 的"五步推演 step1–step5"是**六爻的实现细节**，八字无对应物；
  `CONTRACT.md` §六 欠账表 7 条中**八字侧 0 条**。
- **判定**：八字侧 0 条欠账 ≠ 八字干净。在六爻侧同一套判据能问出 7 条的地方，
  八字侧问出 0 条，读数是"**未经同等审计**"。这是最容易被误读成成果的一项。

### A4 · 契约机器判据的位置文档写错了（P1）

- **证据**：`CONTRACT.md` §四/§五 写"真值源是 `data/rules/layer_contract.json`"，
  实际是 `liuyao/data/rules/`（6,240 B）与 `bazi/data/rules/`（4,099 B）**各一份**，
  根目录无此文件。
- **性质**：AGENTS.md §六.3「文档说的和代码做的不一致，本身就是已知问题」。

### A5 · 引擎内核三份化且全部入库（P1）

- `kernel/` 6,677 行 + 两科 `core/` 4,495 + 3,853 行，同一份源码在 git 里三份。
- 与 `plugins/engine/`（产物，**不入库**）口径不一致：同样是生成物，一个入库一个不入库。
- 依赖 [35] 字节比对维持，现状成立（实测 rc=0），**按 D1=C 处置**。

### A6 · CI 覆盖面窄（P1）

现有 `.github/workflows/ci.yml` 两个 job：

| job | 内容 | 缺口 |
|---|---|---|
| `gates` | 两科 `check.py`（windows-latest，Py 3.14） | 无根级文档门、无 `kernel-sync` job |
| `plugin-gates` | `npm --prefix dsh-plugin run check`（win + ubuntu） | **其余 4 宿主无 CI** |

AGENTS.md §二 明文要求"共享层 + 宿主侧两条都要跑"，CI 只跑了 dsh 那一条。

### A7 · 门禁膨胀与空号（P2）

- 107 个 `dev_tools`、38 个 `check_*.py`；六爻门编号缺 8/9/10/21–25 共 9 个空号。
- `GOVERNANCE.md` 已建立五档与降档门槛，但**成批执行尚未排期**——
  有规矩，没人拿规矩过一遍存量。

---

## 三、理想架构（To-Be）

### 3.1 设计目标

| # | 目标 | 含义 |
|---|---|---|
| G1 | **单一真源最大化** | 凡"与学科无关"的东西——引擎内核、门禁内核、分发运行时——全仓只有一份 |
| G2 | **两科对称** | 形状一致（同样有 `tests/`、同样受契约审计、同样受文档索引门覆盖） |
| G3 | **真源 / 产物严格分层且可机判** | 入库的只能是真源；产物一律不入库，且有同步门 + 字节比对门 |
| G4 | **治理可机检** | 根级文档、批次号、文档索引、五宿主 CI 全部有门 |
| G5 | **对外契约冻结面单一** | 四工具契约只在 `plugins/mcp/` 一处，五宿主零副本（**现状已达成，只保不破**） |

### 3.2 目标目录树

```
Yi/
├── 根 8 份治理 md（含本文件）        ← 由 devkit/root/ 的三道门守
├── .github/workflows/ci.yml          ← 四 job：root / kernel-sync / 两科 / 五宿主矩阵
│
├── kernel/                           # ① 引擎内核真源
│   ├── MANIFEST.json  sync_kernel.py（+ --standalone）
│   └── yishu_core/{common,variants}/
│
├── devkit/                           # ② 门禁内核真源（★新增）
│   ├── MANIFEST.json                 # 在册共享件 + 编号登记
│   ├── sync_devkit.py                # --write 分发 / --check 比对
│   ├── shared/                       # 11 个归并项（8 门 + 3 器）的单一真源
│   ├── root/                         # 根级门
│   │   ├── check_root_docs.py        # 扫根级 md；禁用 basename 兜底
│   │   ├── check_docs_index.py       # DOCS.md ↔ 实际 .md 双向对账（从六爻 [36] 上提）
│   │   └── check_batch_num.py        # 批次号单调 + 六份 CHANGELOG 同批一致性
│   ├── pending/                      # 登记暂存区（并发写 DOCS.md 的解法，见 §4.1）
│   └── handoff/                      # 各 Agent 的交接报告（不入库）
│
├── liuyao/   bazi/                   # ③ 学科层（形状对称）
│   ├── core/yishu_core/              # 产物，按 D1=C 维持入库 + CI 强制 --check
│   ├── scripts/                      # 四段（同名是契约要求，保留）
│   ├── data/{sources,cases,rules,cache}   # cache/ 为新分层，不入库
│   ├── references/  docs/
│   ├── dev_tools/                    # 学科专属门 + devkit/shared 分发产物
│   └── tests/                        # ★八字补建
│
├── plugins/                          # ④ 分发真源（保持）
└── 5× 宿主适配器/
```

### 3.3 目标依赖图

```
devkit/shared ─sync_devkit──▶ <科>/dev_tools/<同名>.py      （产物，[37] 比对）
devkit/root   ──────────────▶ 根 CI job
kernel/       ─sync_kernel──▶ <科>/core/yishu_core/  ◀── <科>/scripts
                                                        ─build.mjs──▶ plugins/engine/ ──▶ 5 宿主

CI 四 job：
  root-gates ── kernel-sync ── 两科 gates ── plugins-matrix(5 宿主 × 2 OS)
```

四条硬约束（目标态）：

1. `devkit/shared/*` 与 `<科>/core/yishu_core/*` 是产物，**手改即红**（字节比对）；
2. 两科之间仍**零 import、零跨科写**（AGENTS.md §二 1/2，不放松）；
3. 根级 md 与 `DOCS.md` 至少各有一道门；
4. 新增文档不登记 `DOCS.md` 即红（[36] 已达成，**上提到根 CI**）。

### 3.4 不改动的部分（明确排除，避免执行者扩大化）

- 四段契约 `chart→analyze→narrate→render` 本体、四条不许越的界、`CONTRACT.md` §七 变更规程；
- 三条铁律（AGENTS.md §一）、案例库隔离、口径诚实；
- 两科 `scripts/` 下四段同名入口（形状重复是契约要求，不是欠账）；
- 五宿主分发形态、`plugins/` 共享层唯一真源、1.0 API 冻结面；
- 批次号作为唯一真源的纪律；
- **两科 `check.py`** 除 A0-5 / A1-2 / A2-A / A5-1 四张卡明确授权外，其余卡一律不改。

---

## 四、并发协议（多 Agent 异步执行的前提）

> 本方案要派 25 个任务给多个 Agent 异步执行，**必须先解决"多人同时改一个仓库"**。
> 本节是强制协议，不是建议。

### 4.0 工作区当前已被外部会话占用（硬约束，先读）

实测 `git status --porcelain`（2026-10-29）显示**另有一个并行会话**正在做《三命通会》四库本转录，
占用以下路径。本方案的任务**一律不得触碰**，也不得在自己的分支里"顺手整理"：

```
 M bazi/dev_tools/check_doc_refs.py          ← 与 A1-1 的归并目标撞车，见下
 M bazi/dev_tools/diff_siku_sanming.py
 M bazi/dev_tools/scan_siku_gaps.py
 M bazi/docs/SANMING-SIKU-COLLATION.md
?? bazi/data/sources/sanming_tonghui_siku.dz.txt
?? bazi/data/sources/sanming_tonghui_siku.provenance.json
?? bazi/dev_tools/build_siku_dz.py
```

**冲突处置（已排定，执行者照做）**：

1. `A1-1-06`（归并 `check_doc_refs.py`）**必须在外部会话落盘并提交之后**才能动手。
   该卡标注 `blocked-by: 外部三命通会会话`。
2. 动手前必须 `git log --oneline -5` 确认该会话已提交；若未提交，
   **该卡挂起，去领别的卡，不要等待、不要自作主张改那份文件**。
3. 集成 Agent 在 merge A1-1-06 前，须确认外部会话的改动**已包含**在归并结果里
   （即：归并必须以"外部会话提交后的版本"为八字侧源，不是以 HEAD 的旧版本为源）。
4. 顺带一条不属于本方案的欠账，留给外部会话自己收口：
   `bazi/dev_tools/build_siku_dz.py` 一旦入库，`DOCS.md` 未登记会触发 [36] 判红
   （实测 `grep -c build_siku_dz DOCS.md` = 0）。

### 4.1 三条并发规则

**规则一 · 每 Agent 一棵 worktree、一条分支、一个独占写域**

```bash
git worktree add .worktrees/<TODO_ID> -b arch/<TODO_ID> main
```

- 分支命名 `arch/<TODO_ID>`（如 `arch/A1-1-04`），worktree 落在 `.worktrees/`
  （根 `.gitignore` 已有 `.worktrees/`，不脏树）。
- 每张卡写死 `owns:`（可写路径 glob）。**`owns:` 之外的路径一律只读**。
- **越域写入 = 该任务失败**，不是"顺手改一下"。发现确实需要越域 → 停下，
  在 handoff 报告里写"需要 X 路径的写权，建议由 A6-INT 协调"，**不要自己写**。

**规则二 · 共享热点文件用"登记暂存区"解并发**

`DOCS.md` 是多张卡都要追加行的热点（[36] 门要求新增 `.md` 必须登记）。解法：

- 各 Agent **不直接改 `DOCS.md`**，而是往 `devkit/pending/<TODO_ID>.mdadd` 写一行：
  ```
  | `路径/文件名.md` | 一句话职责 | 状态 |
  ```
- 由 A6-INT 集成时统一合入 `DOCS.md`。
- 这样 [36] 门**在集成完成前会判红**——这是**特性不是缺陷**：
  红色 = "有登记未合入"，集成完自然转绿，正好当作"集成未完成"的机械信号。

`CONTRACT.md` / `AGENTS.md` / `.github/workflows/ci.yml` / 两科 `check.py` 无暂存区，
靠 §4.3 的波次顺序保证串行。

**规则三 · 门禁必须在自己的 worktree 里跑通**

worktree 是干净树，`plugins/engine/`、`skills/` 不存在。跑分发面自检前先：

```bash
node plugins/scripts/build.mjs
```

其余按 AGENTS.md §二：门内自足夹具，干净树必须能跑通。

### 4.2 波次编排

| 波次 | 任务 | 并发度 | 启动条件 |
|---|---|---|---|
| **W0** | A0-1 | 1 | 无 |
| **W1** | A0-2 · A0-3 · A0-5 | 3 并行 | W0 完成 |
| **W2** | A0-4 · A1-1-01…A1-1-11 | 12 并行（域互斥） | W0 完成；A1-1-06 另需外部会话落盘 |
| **W3** | A1-2 · A1-3 | 2 并行 | W2 全部完成 |
| **W4** | A2-A · A2-B | 2 并行 | W3 完成 |
| **W5** | A3-1 · A3-2 | 2 并行 | W4 完成 |
| **W6** | A4-CI · A4-2 | 2 并行 | W1 完成（A4-2 可任意时刻） |
| **W7** | A5-1 | 1 | W3 完成 |
| 全程 | **A6-INT** | 1（持续） | 每波收口时 |

**A1-1 的 11 张子卡启动顺序建议（不是依赖，是风险序）**：
先 L2（`A1-1-09/10/11`）→ 再 L1（`A1-1-04/05/06/07/08`）→ 最后 L0（`A1-1-01/02/03`）。
理由：大差异项最能暴露"两科判据已分叉"的实情，先做能早定口径。

### 4.3 共享热点的串行保证

| 热点文件 | 独占卡（按时间序） |
|---|---|
| `devkit/MANIFEST.json` | A0-1 → A1-3 |
| `.github/workflows/ci.yml` | A0-4 → A4-CI |
| 两科 `check.py` | A0-5 → A1-2 → A2-A → A5-1 |
| `CONTRACT.md` | A0-3 → A2-B |
| `DOCS.md` | 不独占，走 §4.1 规则二的暂存区 |
| `bazi/data/sources/sanming*` 等 7 项 | **外部会话**（本方案全部卡禁入） |

---

## 五、TODO 卡片全集

> 每张卡自含：阶段 / 波次 / 批次 / 独占写域 / 依赖 / 步骤 / 验收 / 交付 / 禁止。
> 派发时把卡片原文整段粘进 §六 的提示词即可。

### 完成台账（2026-10-29 单 Agent 串行收口；批次 × 提交不变量见 `git log`）

| 卡 | 状态 | 批次 | 提交（短 hash） |
|---|---|---|---|
| A0-0 | ✅ 已完成 | 331 | `96ddd2b` |
| A0-1 | ✅ 已完成 | 331 | `209cd24` |
| A0-2 | ✅ 已完成（上线恰判红四处） | 331 | `b8bbfbb` |
| A0-3 | ✅ 已完成（四处改指 `<科>/docs/`） | 331 | `7f38f4c` |
| A0-5 | ✅ 已完成（[36] 上提，编号空出） | 331 | `fe7b5bd` |
| A0-4 | ✅ 已完成（`root-gates` job） | 331 | `623a05f` |
| A1-1-01/02/03 | ✅ 已完成（L0 三件逐字节同源） | 334 | `a1e68f2` |
| A1-1-04…11 | ✅ 已完成（L1/L2：7 单源＋4 变体） | 332–334 | `377252f` |
| A1-2 | ✅ 已完成（两科挂 [37]） | 334 | `7b5ffd7` |
| A1-3 | ✅ 已完成（11 共享件＋4 变体＋8 门编号） | 334 | `7b5ffd7` |
| A2-A | ✅ 已完成（八字 tests＋[38]） | 335 | `fe4f831` |
| A2-B | ✅ 已完成（三件套＋契约修正＋审计） | 336 | `83133a7` |
| A3-1 | ✅ 已完成（`linguist-generated`＋`--standalone`） | 337 | `07880d8` |
| A3-2 | ✅ 已完成（`data/cache/`，清空即重生） | 337 | `28fd659` |
| A4-CI | ✅ 已完成（四 job＋五宿主×2 OS） | 338 | `be60113` |
| A4-2 | ✅ 已完成（10 批/最大重叠 2，维持现状） | 338 | `226531c` |
| A5-1 | ✅ 已完成（未分类清零；不降不删；墓碑句） | 339 | 见收口提交 |
| A6-INT | ✅ 已完成（本表＋验证链＋DOCS 合入） | — | 见收口提交 |

**执行方式偏差（如实登记）**：本方案假定 25 个 Agent 各开 worktree；本收口由
**单 Agent 串行**完成，因此没有 25 条 `arch/*` 分支，改为**主工作区逐批提交**
（每卡仍按批次号与独占写域落盘；外部三命通会会话的 7 个路径全程未改、未替它提交）。
A1-1 的 4 个逻辑不同项按 kernel 变体范式登记，而不是硬合成一份——理由见
`devkit/MANIFEST.json` 的 `variant_reasons`。A1-1 期间为让 `sync_devkit --write` 认得
新件，MANIFEST 的 `files.shared` 随归并逐步追加（本应由 A1-3 独占，串行模式下合并到同一执行者，
最终由 A1-3 复核为 11 项）。

### 通用契约：每个执行 Agent 必守（不分批、不分卡）

1. **改动范围纪律**：改引擎/推演逻辑必须两集（tune / holdout）分别出分（AGENTS.md §四.1）；
   改静态表/提取器必须 `git show HEAD:<file>` 逐格对拍，报"新增/变空/改值"三数，
   **变空与改值逐条解释**（§四.5）。
2. **负例自证**：任何新挂的门必须先塞一个明知不存在的目标，确认门判红（EXIT≠0）并报明细，
   再撤掉（§四.8）。**全绿的新门先怀疑、再证明**——"0 结果"要先确认不是路径解析错了。
3. **纪律三件套**：改层界/键面 → 同批改 `CONTRACT.md` + `<科>/data/rules/layer_contract.json`
   + `<科>/docs/CHANGELOG.md`；**三者不同步即算缺陷**（CONTRACT.md §七.1）。
4. **口径**：不得出现"预测准确率"类表述；分数一律写成"古籍案例对齐分"并带 n 与集合名（§一.3）。
5. **路径纪律**：文件名不携带版本（§三）；一次性脚本进 `scratch/`（整目录不入库）；
   CLI 用 argparse 且带 UTF-8 守卫（§四.9）。
6. **并发纪律（§四）**：worktree + 分支 + 独占写域；越域即停；`DOCS.md` 走暂存区。

---

### P0 · 立地基

#### A0-0 · 本文件与 `DOCS.md` 同批登记 —— **已完成**（批次 331，待提交）

- 状态：已完成。`DOCS.md` 根级表已加本文件行 + 阅读路径表已加"要排队/领任务的人"一行；
  `README.md` 已加本文件入口；`DOCS.md` 根级计数 6→7。
- 剩余动作：由 A6-INT 在 331 批提交。
- 验收：已实测 `python liuyao/dev_tools/check_docs_index.py` rc=0（51 份全部登记可达）。

---

#### A0-1 · 建 `devkit/` 骨架

- 阶段 P0 ｜ 波次 **W0** ｜ 批次 331 ｜ 并发度 1
- 独占写域：`devkit/MANIFEST.json`、`devkit/sync_devkit.py`、`devkit/shared/.gitkeep`、
  `devkit/root/.gitkeep`、`devkit/pending/.gitkeep`、`.gitignore`（追加 `devkit/handoff/`）
- 只读：全仓其余
- 依赖：无

**步骤**

1. 建 `devkit/MANIFEST.json`，schema `yi-devkit-manifest/1`，结构仿 `kernel/MANIFEST.json`：
   ```json
   {
     "schema": "yi-devkit-manifest/1",
     "batch": 331,
     "source": "devkit",
     "files": {
       "shared": [],
       "root": ["check_root_docs.py", "check_docs_index.py", "check_batch_num.py"]
     },
     "gate_ids": {},
     "targets": { "liuyao": "liuyao/dev_tools", "bazi": "bazi/dev_tools" }
   }
   ```
   `shared` 与 `gate_ids` **本卡留空**（由 A1-3 按实际归并结果填），不要预填猜测值。
2. 建 `devkit/sync_devkit.py`，两个模式：
   - `--write`：按 MANIFEST 把 `shared/*` 与 `root/*` 分发到 `targets` 各科路径；
   - `--check`：逐字节比对源与产物，不一致即 rc≠0 并报出文件名。
   **直接照抄 `kernel/sync_kernel.py` 的实现范式**（同机制，不另造）。
3. 三个 `.gitkeep` 占位文件。
4. `.gitignore` 追加 `devkit/handoff/`（handoff 报告不入库）。

**验收**

```bash
python devkit/sync_devkit.py --check        # rc=0
```
负例自证（两条都要做，缺一不算完成）：
- 手改 `devkit/shared/` 下任一产物 → `--check` rc≠0 且报出文件名；
- 往 `devkit/shared/` 塞一个野文件 → rc≠0 且报出文件名。
撤掉负例后 rc=0。

**交付**：分支 `arch/A0-1` + `devkit/handoff/A0-1.md`

**禁止**：预填 `shared` 清单；改 `kernel/`；改两科任何文件。

---

#### A0-2 · 建根级文档门 `devkit/root/check_root_docs.py`

- 阶段 P0 ｜ 波次 **W1** ｜ 批次 331 ｜ 与 A0-3、A0-5 并行
- 独占写域：`devkit/root/check_root_docs.py`
- 只读：全仓其余（含两科 `check_doc_refs.py` 源码，用作参照）
- 依赖：A0-1

**步骤**

1. 新门必须**扫仓库根的 `*.md`**（`ROOT.glob("*.md")`，含本文件），
   **不走 `DISC.rglob`**——这是它与现两科 `check_doc_refs.py` 的根本差异。
2. **禁用 basename 兜底**：`docs/CHANGELOG.md` 必须解析到真实路径，
   同名文件不认。这是本门的关键判据，不许为"减少误报"而加回兜底。
3. 豁免口径沿用现门（**照抄，不自创**）：
   - 负例文件名 `__` 双下划线前缀；
   - 历史散文 `HISTORY` 正则（`曾[并未已在经]|勘误|已删除|已随|不存在|负例|自测|selftest|…`）；
   - `http://` / `https://` / `<` / `…`；
   - 散文速记（含纯数字路径段）；
   - 本门自身文件。
4. 支持 `--selftest`，负例自证走临时目录（AGENTS.md §四.8）。
5. 中文入口自带 UTF-8 守卫（`sys.stdout.reconfigure(...)`，§四.9）。

**验收**

```bash
python devkit/root/check_root_docs.py --selftest   # 必须通过（负例被抓）
python devkit/root/check_root_docs.py              # 本卡完成时 rc≠0 属预期，见下
```

**本门上线时必须真的红一次**：A0-3 修四处引用之前，本门应对
`AGENTS.md:200/226/262` 与 `CONTRACT.md:94` 判红。
- 若上线即绿 → **先怀疑门没扫到根级文件**（§四.8：0 结果先确认不是路径解析错了），
  查 `ROOT.glob("*.md")` 扫到几份，再交。
- 本卡交付时把"判红输出片段"贴进 handoff，作为门真在干活的证据。

**交付**：分支 `arch/A0-2` + `devkit/handoff/A0-2.md`（含判红输出片段）

**禁止**：改 `AGENTS.md` / `CONTRACT.md`（那是 A0-3 的活）；加回 basename 兜底。

---

#### A0-3 · 修四处根级悬空引用

- 阶段 P0 ｜ 波次 **W1** ｜ 批次 331 ｜ 与 A0-2、A0-5 并行
- 独占写域：`AGENTS.md`、`CONTRACT.md`
- 只读：全仓其余
- 依赖：A0-1（可与 A0-2 并行，两卡文件不重叠）

**步骤**

实测行号，逐条核（行号可能因前序批次漂移，**以内容定位，不迷信行号**）：

| 文件 | 行 | 现引用 |
|---|---|---|
| `AGENTS.md` | 200 | `docs/CHANGELOG.md`（§三 命名表） |
| `AGENTS.md` | 226 | `docs/CHANGELOG.md`（§四.4） |
| `AGENTS.md` | 262 | `docs/CHANGELOG.md`（§六.1） |
| `CONTRACT.md` | 94 | `docs/CHANGELOG.md`（§四） |

改法（**两案选一，不要各改一半**）：
- **推荐**：改指名学科 —— 三处 `AGENTS.md` 改 `<科>/docs/CHANGELOG.md`，
  `CONTRACT.md` 那处同理；
- 备选：在根建 `docs/CHANGELOG.md` 作跨科总流水索引（新增一个真源，**需 A6-INT 同意**）。

**验收**

```bash
python devkit/root/check_root_docs.py          # rc=0（需 A0-2 已就位）
python liuyao/dev_tools/check_doc_refs.py      # rc=0（不回归）
python bazi/dev_tools/check_doc_refs.py        # rc=0
```

注意：八字那份 `check_doc_refs.py` 正被外部会话修改，跑之前先 `git log --oneline -5` 确认状态；
若外部会话未落盘，本卡的"八字侧不回归"一项标注为"未验"，交 A6-INT 补验。

**交付**：分支 `arch/A0-3` + `devkit/handoff/A0-3.md`

**禁止**：顺手修别的文档路径（会与 A2-B / A4-2 撞车）；改根级以外的任何文件。

---

#### A0-5 · 文档索引门上提到根

- 阶段 P0 ｜ 波次 **W1** ｜ 批次 331 ｜ 与 A0-2、A0-3 并行
- 独占写域：`devkit/root/check_docs_index.py`、`liuyao/dev_tools/check.py`
- 只读：全仓其余
- 依赖：A0-1

**步骤**

1. 把 `liuyao/dev_tools/check_docs_index.py` **搬**到 `devkit/root/check_docs_index.py`
   （内容原样，路径常量改为仓库根）。
   **用 `git mv` 语义搬运**，并在 handoff 里写明"从 liuyao/dev_tools/ 迁出"。
2. `liuyao/dev_tools/check.py` 移除原 `[36]` 段（六爻不再挂此门）。
   **移除后该编号空出**，按 A5-1 的口径：空号不回填。
3. 在 `devkit/MANIFEST.json` 的 `files.root` 里确认已有该门登记（A0-1 已预登记，本卡只核对）。
4. 八字侧原本就没挂 [36]，无需改动。

**验收**

```bash
python devkit/root/check_docs_index.py      # rc=0
python liuyao/dev_tools/check.py            # rc=0（[36] 段已移除且不残留空壳）
```
负例自证：临时造一份未登记的 `.md`（`git add` 后）→ 门判红；撤掉后 rc=0。

**交付**：分支 `arch/A0-5` + `devkit/handoff/A0-5.md`

**禁止**：改 `bazi/dev_tools/check.py`（那是 A1-2 / A2-A 的域）；改 `DOCS.md`（走暂存区）。

---

#### A0-4 · CI 加 `root-gates` job

- 阶段 P0 ｜ 波次 **W2** ｜ 批次 331 ｜ 与 A1-1 各卡并行
- 独占写域：`.github/workflows/ci.yml`
- 只读：全仓其余
- 依赖：A0-1、A0-2、A0-5 完成

**步骤**

在 `.github/workflows/ci.yml` 的 `jobs` 里加一个 `root-gates`：

```yaml
  root-gates:
    runs-on: windows-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.14"
      - name: root gates
        run: |
          python devkit/sync_devkit.py --check
          python devkit/root/check_root_docs.py
          python devkit/root/check_docs_index.py
```

- `runs-on: windows-latest` 与现有 `gates` job 对齐（CI 文件头已写明：
  Windows 是本项目 cp936 编码红线的原始靶）。
- **不要**顺手改现有两个 job（那是 A4-CI 的活）。

**验收**

```bash
python devkit/sync_devkit.py --check && python devkit/root/check_root_docs.py && python devkit/root/check_docs_index.py
# 本地三连 rc=0
```
外加：workflow YAML 语法自检（可用 `actionlint`，无则人工核缩进与 `jobs` 层级）。

**交付**：分支 `arch/A0-4` + `devkit/handoff/A0-4.md`

**禁止**：动现有 `gates` / `plugin-gates` 两个 job；加 `continue-on-error`（等于把门关掉）。

---

### P1 · 门禁内核化

#### A1-1 · 归并 11 个共享件（8 门 + 3 器）

- 阶段 P1 ｜ 波次 **W2** ｜ 批次 332–334 ｜ **11 张子卡全部可并行**

**11 张子卡的通用步骤（每卡照做，不要跳步）**

1. **取源**：
   - L0 档（逐字节相同）→ 直接取任一科文件作为真源，**无需 diff**；
   - L1 / L2 档 → `diff -u <liuyao> <bazi>` 逐行对拍，**把每一处差异逐条归因**
     （哪边多一条判据 / 哪边豁免更宽 / 哪边是学科专属适配）。
2. **合并口径**：**以严的为准合并**。差异若属"某科有而另一科无的判据"→ 保留，
   并把该判据参数化（只对需要的科生效）；差异若属"某科豁免更宽"→ 取严的。
3. **参数化**：学科名、学科根路径**由调用方注入**，不得在 shared 里硬编码任何一科的路径或名字。
4. **落盘**：写入 `devkit/shared/<同名>.py`，然后 `python devkit/sync_devkit.py --write` 分发。
5. **逐格对拍**（AGENTS.md §四.5）：归并前后各跑一次该门，报
   "新增判定 N 条 / 移除判定 N 条"，**移除的逐条解释**并写进 handoff。
6. 若有新增 `.md`，登记行写入 `devkit/pending/A1-1-XX.mdadd`（通常无）。

**通用验收（每卡）**

```bash
python devkit/sync_devkit.py --check                  # rc=0
python liuyao/dev_tools/check.py                      # rc=0
python bazi/dev_tools/check.py                        # rc=0
python liuyao/dev_tools/<同名>.py --selftest          # 该门自带 selftest 通过（若有）
python bazi/dev_tools/<同名>.py --selftest            # 同上
```
外加：归并前后该门的**判定结果集合一致**（或差异已在 handoff 逐条解释）。

**通用禁止（每卡）**

- **不得改两科 `check.py`**（§1.3 已验证调用约定不变，改了就与 A1-2 撞车）；
- 不得改 `devkit/MANIFEST.json`（A1-3 独占）；
- 不得改 `devkit/sync_devkit.py`（A0-1 独占）；
- 不得改两科 `scripts/`（本阶段只动门禁）；
- 不得"为了让两科都绿"而删判据——删了要逐条解释并登记，否则等于偷偷降标准。

**子卡清单**（`owns:` = `devkit/shared/<f>.py` + `liuyao/dev_tools/<f>.py` + `bazi/dev_tools/<f>.py`）

| 卡 ID | 文件 | 档 | 六爻/八字 行数 | 备注 |
|---|---|---|---|---|
| **A1-1-01** | `check_case_isolation.py` | L0 | 103 / 103 | 逐字节相同，最简单，可作范式卡 |
| **A1-1-02** | `check_house_conventions.py` | L0 | 133 / 133 | 逐字节相同 |
| **A1-1-03** | `check_layer_contract.py` | L0 | 192 / 192 | 逐字节相同；**本卡只搬不改进判据内容**（改判据须同步 CONTRACT.md，属 A2-B） |
| **A1-1-04** | `check_cli_encoding.py` | L1 | 262 / 261 | 涉及 cp936 行为面，验收须在 Windows |
| **A1-1-05** | `check_regex_lists.py` | L1 | 182 / 182 | 注意 AGENTS.md §二 的 list 展平硬要求 |
| **A1-1-06** | `check_doc_refs.py` | L1 | 267 / 268 | ⚠ **blocked-by: 外部三命通会会话**，见 §4.0 |
| **A1-1-07** | `golden.py` | L1 | 157 / 166 | 器，非门 |
| **A1-1-08** | `baselines.py` | L1 | 254 / 250 | 器，非门 |
| **A1-1-09** | `check_source_readings.py` | **L2** | **692 / 443** | 差异最大，先做 |
| **A1-1-10** | `check_rule_registry.py` | **L2** | 269 / 293 | 先做 |
| **A1-1-11** | `feedback_store.py` | **L2** | 178 / 237 | 器，先做 |

**不归并（明确排除）**：`check.py`（编排器，各科本应不同）、`__init__.py`（差异仅 docstring）。
这两项**不派卡**，谁也不要去动。

---

#### A1-2 · 字节比对门 `[37]` + `check.py` 接入

- 阶段 P1 ｜ 波次 **W3** ｜ 批次 334 ｜ 与 A1-3 并行
- 独占写域：`liuyao/dev_tools/check.py`、`bazi/dev_tools/check.py`
- 只读：全仓其余
- 依赖：**A1-1 全部 11 张完成**

**步骤**

1. 在两科 `check.py` 里挂新门 `[37]`：内核同源（devkit 唯一真源；两科 dev_tools 共享件是产物，
   手改/野文件即红）。
   **直接照抄六爻 `check.py` 的 `[35]` 段实现范式**，换成 devkit 的源/目标路径。
2. 编号 `[37]`：两科统一用同一个编号（六爻现到 `[36]`、八字现到 `[28]`，
   **`[37]` 在两科都未被占用**）。
3. 若 A1-1 的某张卡提出了调用约定变更需求，本卡统一处理（子卡不许自己改）。

**验收**

```bash
python liuyao/dev_tools/check.py    # rc=0，且输出含 [37] 段
python bazi/dev_tools/check.py      # rc=0，且输出含 [37] 段
```
负例自证（两科各试一次）：
- 手改 `liuyao/dev_tools/check_cli_encoding.py` → `[37]` 判红并报文件名；
- 往 `<科>/dev_tools/` 塞野文件 → 判红。
撤掉后 rc=0。

**交付**：分支 `arch/A1-2` + `devkit/handoff/A1-2.md`

**禁止**：改 `devkit/shared/` 内容（那是 A1-1 的成果）；改 `[35]` 段判据。

---

#### A1-3 · 门编号登记

- 阶段 P1 ｜ 波次 **W3** ｜ 批次 334 ｜ 与 A1-2 并行
- 独占写域：`devkit/MANIFEST.json`
- 只读：全仓其余
- 依赖：**A1-1 全部完成**

**步骤**

1. 按 A1-1 的实际结果填 `files.shared`（11 项，**以实为准，不预填**）。
2. 填 `gate_ids`：共享门的稳定编号清单。
   **共享门不在两科 `check.py` 里单独编号**（它们由 `[37]` 统一守），
   若某门在单科另有编号，如实登记。
3. 在 MANIFEST 的 `_comment` 里写明：
   "六爻 [8][9][10][21]–[25] 是已下线门的墓碑，**不回填**；新门从 [37] 续"。

**验收**

```bash
python devkit/sync_devkit.py --check     # rc=0
python -c "import json;d=json.load(open('devkit/MANIFEST.json',encoding='utf-8'));print(len(d['files']['shared']))"
# 输出 11
```
外加：`gate_ids` 无重复编号；两科 `check.py` 里无共享门的重复编号（**读 A1-2 的 handoff 核对**，
本卡不写 `check.py`）。

**交付**：分支 `arch/A1-3` + `devkit/handoff/A1-3.md`

**禁止**：改 `devkit/shared/`；改两科 `check.py`。

---

### P2 · 两科对称（D3 = 中档）

#### A2-A · 八字补 `tests/`

- 阶段 P2 ｜ 波次 **W4** ｜ 批次 335 ｜ 与 A2-B 并行
- 独占写域：`bazi/tests/**`、`bazi/dev_tools/check.py`
- 只读：全仓其余（含 `liuyao/tests/**` 作形状参照）
- 依赖：A1-2

**步骤**

1. 照六爻 `tests/` 的**形状**建八字对应物（smoke + regression + 专项×2 共 4 个文件形状）。
   **照形状不照内容**：八字无 `step1–step5`，专项测试要对应八字自己的受控维度
   （`bazi/dev_tools/check_dim_lock.py` 在册的维度可作选题来源）。
2. 至少落 smoke + regression 两类，**不追求填满 4 个形状**。
3. 接入 `bazi/dev_tools/check.py`（新增一个门小节，编号按八字侧当前最大号 +1）。
4. 登记进 `bazi/docs/CHANGELOG.md`（本卡独占该文件的**追加**权，A2-B 会重写它，
   详见 A2-B 卡的冲突说明）。

**验收**

```bash
python bazi/dev_tools/check.py                  # rc=0，且输出含新增的 tests 小节
python bazi/tests/smoke_test.py                 # 独立可执行、rc=0
python bazi/tests/regression_test.py            # 独立可执行、rc=0
```
外加：八字 `check.py` 报出的**测试类别数与六爻形状一致**（都有 smoke 与 regression 两类）。
负例自证：临时让一个测试失败 → `check.py` 判红；恢复后 rc=0。

**交付**：分支 `arch/A2-A` + `devkit/handoff/A2-A.md`

**禁止**：克隆六爻 `step1–step5` 相关测试（D3 中档不含）；
为凑形状写"必然通过"的空测试（会被负例自证抓到，也会造出假门）。

---

#### A2-B · 八字文档侧三件套 + `CONTRACT.md` 三项修正

- 阶段 P2 ｜ 波次 **W4** ｜ 批次 336 ｜ 与 A2-A 并行
- 独占写域：`bazi/docs/**`、`CONTRACT.md`、`liuyao/data/rules/layer_contract.json`、
  `bazi/data/rules/layer_contract.json`、`liuyao/docs/CHANGELOG.md`（追加）
- 只读：全仓其余
- 依赖：A1-2

**步骤（三件事一卡做完，因为它们都写 `CONTRACT.md`）**

1. **八字 CHANGELOG 瘦身**：按 330 批六爻的同款做法，把 `bazi/docs/CHANGELOG.md`
   拆成三件套：
   - `CHANGELOG.md`（最近窗口）
   - `CHANGELOG-ARCHIVE.md`（**全文，一字未删**——DOCS.md 归档口径的硬要求）
   - `CHANGELOG-HISTORY-INDEX.md`（一句话索引）
2. **契约欠账审计**：把 `CONTRACT.md` §六 的七条判据在八字侧逐条问一遍
   （chart 是否下判断 / analyze 是否写文章 / 禁边表 / 键白名单 / render 是否当第二个 narrate /
   模块混装）。
   **问出 0 条也要在 §六 具名写"已审计、八字侧结论 0 条"**——没登记的 0 等于没审。
3. **契约文档两处修正**：
   - §四/§五 的 `data/rules/layer_contract.json` → 改为 `<科>/data/rules/layer_contract.json`（A4）；
   - §二 改为"通用（四段职责）" + 新增"§二-bis 各科剖面"：
     六爻 = `step1–step5` 链；八字 = 按实的自身推演路径（**不虚构**，若八字无对应物就写
     "八字无此结构的对应物"）。
4. 三处同步：`CONTRACT.md` + 两科 `layer_contract.json` + 两科 `docs/CHANGELOG.md`
   （CONTRACT.md §七.1 三件套）。
5. 新增的 2 份 `.md` 登记行写入 `devkit/pending/A2-B.mdadd`（**不直接改 `DOCS.md`**）。

**验收**

```bash
python liuyao/dev_tools/check_layer_contract.py --selftest   # 通过
python bazi/dev_tools/check_layer_contract.py --selftest     # 通过
python liuyao/dev_tools/check.py                             # rc=0
python bazi/dev_tools/check.py                               # rc=0
wc -l bazi/docs/CHANGELOG.md bazi/docs/CHANGELOG-ARCHIVE.md  # 归档件行数 = 原文 2500（一字未删）
```
外加：`CONTRACT.md` §六 有八字侧结论行（哪怕是 0 条）；§二-bis 存在。

**冲突说明**：本卡重写 `bazi/docs/CHANGELOG.md`，而 A2-A 也要追加该文件。
**编排已处理**：W4 并入顺序 A2-A → A2-B，A2-B 以并入后的版本为底做拆分，
保证 A2-A 的登记行不丢。**两张卡都必须把自己的登记内容写进 handoff**，供 A6-INT 核对。

**交付**：分支 `arch/A2-B` + `devkit/handoff/A2-B.md`（含八字欠账审计结论逐条）

**禁止**：删改归档件正文（只搬不改写，唯一例外是路径修正——链接要活）；
把八字欠账结论写成"八字很干净"（未审计的 0 不是成果）。

---

### P3 · 真源 / 产物分层（D1 = C）

#### A3-1 · `core` 产物显式化

- 阶段 P3 ｜ 波次 **W5** ｜ 批次 337 ｜ 与 A3-2 并行
- 独占写域：`.gitattributes`、`kernel/sync_kernel.py`
- 只读：全仓其余
- 依赖：A2-B

**步骤**（**按 D1=C，不把 `core/` 加进 `.gitignore`**）

1. `.gitattributes` 追加两行，把两科 core 标为生成物：
   ```
   liuyao/core/yishu_core/** linguist-generated
   bazi/core/yishu_core/** linguist-generated
   ```
   注意：仓库现有 `.gitattributes` 第一项是 `* text=auto eol=lf`，
   **追加项不要动它**（CRLF 归一化是 278 批的行级判据基础）。
2. `kernel/sync_kernel.py` 新增 `--standalone <科>` 模式：
   产出一份**独立可拷贝目录**（含 `core/yishu_core/` + `scripts/` + 运行必需 `data/`），
   使"单目录拷走即可运行"从隐性假设变成显式命令。
3. **不新增 CI job** —— `kernel-sync` job 归 A4-CI（独占 `ci.yml`）。

**验收**

```bash
python kernel/sync_kernel.py --check                    # rc=0
python kernel/sync_kernel.py --standalone liuyao --out "$TEMP/yi_ly_standalone"
python "$TEMP/yi_ly_standalone/scripts/chart.py" --help  # rc=0，且 UTF-8 可读
python liuyao/dev_tools/check.py                        # rc=0（[35] 仍绿）
python bazi/dev_tools/check.py                          # rc=0
```
`--standalone` 的落点必须是系统临时目录（AGENTS.md §四.8 夹具口径）。
负例自证：手改 `liuyao/core/yishu_core/` 任一文件 → `sync_kernel.py --check` 判红。

**交付**：分支 `arch/A3-1` + `devkit/handoff/A3-1.md`

**禁止**：把 `core/` 加进 `.gitignore`（D1 已定为 C）；改 `.gitattributes` 现有的 `eol=lf` 行。

---

#### A3-2 · `data/cache/` 层

- 阶段 P3 ｜ 波次 **W5** ｜ 批次 337 ｜ 与 A3-1 并行
- 独占写域：`.gitignore`、两科 `data/**`、引用了被迁路径的两科 `scripts/**` 与 `dev_tools/**`
- 只读：全仓其余
- 依赖：A2-B

**步骤**

1. `.gitignore` 追加 `**/data/cache/`。
2. 把现有落进 `data/` 的产物（含 `**/data/cases/eval_*.json` 一类）统一改落 `data/cache/`，
   逐条更新引用路径。
3. **逐格对拍**（§四.5）：迁移前后报"迁移 N 个 / 落空 N 个"，落空逐条解释。

**验收**

```bash
git ls-files '*/data/cache/*' | wc -l            # 输出 0
python liuyao/dev_tools/check.py                 # rc=0
python bazi/dev_tools/check.py                   # rc=0
```
外加（关键）：**清掉盘上 cache 后两科 `check.py` 仍 rc=0**——证明没有门依赖缓存存在
（184 批的自愈要求：全新克隆能现场重生成）。

**交付**：分支 `arch/A3-2` + `devkit/handoff/A3-2.md`

**禁止**：把案例源 `data/cases/` 的**本体**迁走（只有 `eval_*` 一类产物进 cache）；
迁 `data/sources/`（古籍底本是不可变源，且部分被外部会话占用）。

---

### P4 · 分发面与 CI

#### A4-CI · CI 四 job 齐备

- 阶段 P4 ｜ 波次 **W6** ｜ 批次 338 ｜ 与 A4-2 并行
- 独占写域：`.github/workflows/ci.yml`
- 只读：全仓其余
- 依赖：A0-4、A3-1

**步骤**

1. 加 `kernel-sync` job（D1=C 的 CI 面）：
   ```yaml
   kernel-sync:
     runs-on: windows-latest
     steps:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: "3.14"
       - name: kernel single source
         run: |
           python kernel/sync_kernel.py --check
           python devkit/sync_devkit.py --check
   ```
2. 把 `plugin-gates` 的 matrix 从 `dsh × 2 OS` 扩成
   `{dsh, claude, codex, gemini, yan} × 2 OS`；
   无 npm script 的宿主直接调
   `node plugins/scripts/build.mjs` + `node plugins/scripts/selftest.mjs`
   + 该宿主的清单断言。
3. 现有 `gates` job **保持不动**（两科 `check.py` 已覆盖）。
4. 四 job 目标态：`root-gates` / `kernel-sync` / `gates` / `plugin-gates`（五宿主矩阵）。

**验收**

```bash
# 本地逐宿主实跑
node plugins/scripts/build.mjs
node plugins/scripts/selftest.mjs
npm --prefix dsh-plugin run check
```
外加：workflow 里五个宿主 id 齐全；无 `continue-on-error`。

**注意**：五宿主 × 2 OS = 10 个 runner，第一次跑必然有任何一条颜色。
按 CI 文件头既有口径处理——**以实跑读数更正文件与 CHANGELOG，不反向"调 CI 凑绿"**。

**交付**：分支 `arch/A4-CI` + `devkit/handoff/A4-CI.md`

**禁止**：为凑绿加 `continue-on-error` 或删 matrix 项。

---

#### A4-2 · 六份 CHANGELOG 合并评估（先评估，不先改结构）

- 阶段 P4 ｜ 波次 **任意** ｜ 批次 338 ｜ 与 A4-CI 并行
- 独占写域：`plugins/CHANGELOG.md`（结论登记）
- 只读：全仓其余（六份 CHANGELOG 全部只读）
- 依赖：无（可最早做）

**步骤**

1. 统计六份 CHANGELOG（5 宿主 + 1 共享层）的批次号区间与重叠度，出一份对拍结论。
2. **结论若为"重叠度低、各自记录宿主专属事实"→ 维持现状并写明理由，结案。**
   AGENTS.md §六.5 诚实结案：实证证明不可改进的不强改。
3. 结论登记进 `plugins/CHANGELOG.md`。

**验收**

```bash
# 结论行可读且含依据（批次区间 + 重叠度读数）
grep -n "CHANGELOG 合并评估" plugins/CHANGELOG.md
```
外加：结论必须有**读数支撑**（各份批次区间、重叠批数），不许只写"维持现状"四个字。

**交付**：分支 `arch/A4-2` + `devkit/handoff/A4-2.md`

**禁止**：为了整洁直接合并六份（先评估）；改各宿主 CHANGELOG 正文。

---

### P5 · 门禁瘦身

#### A5-1 · 按 GOVERNANCE 五档过一遍存量（含门编号墓碑说明）

- 阶段 P5 ｜ 波次 **W7** ｜ 批次 339 ｜ 并发度 1
- 独占写域：两科 `dev_tools/**`（含删除）、`GOVERNANCE.md`、两科 `docs/CHANGELOG.md`（追加）、
  `liuyao/docs/CHANGELOG.md`（含墓碑说明）
- 只读：全仓其余
- 依赖：A1-2

**步骤**

1. 用 `liuyao/dev_tools/governance_map.py` 出当前档位表（**先实跑，不抄 `GOVERNANCE.md` 里的旧快照**）。
2. 逐条按 `GOVERNANCE.md` §一 的门槛判：
   - blocking → 连续一季 0 判红 **且** 负例自证仍可跑 **且** CHANGELOG 具名，才可降 nightly；
   - ondemand → 两季 0 使用记录，才可删（删前查文档活引用，[11] 会拦）；
   - build / tool → 不设降档。
3. **降档 ≠ 删除**：降档只改调用频率、不改判据；删才动文件。
4. 更新 `GOVERNANCE.md` 的档位分布表（`GOVERNANCE-MAP.json` 由生成器重生成，
   本卡只更新 `.md` 的快照并注明取自哪次实跑）。
5. **门编号墓碑说明**（并入本卡）：在 `liuyao/docs/CHANGELOG.md` 写一句
   "六爻 [8][9][10][21]–[25] 是已下线门的墓碑，不回填；新门从 [37] 续"。

**验收**

```bash
python liuyao/dev_tools/governance_map.py       # 出表 rc=0
python liuyao/dev_tools/check.py                # rc=0
python bazi/dev_tools/check.py                  # rc=0
python liuyao/dev_tools/readout_ledger.py --quick   # 项数与实一致
```
外加：每个降档/删除项在 CHANGELOG **具名**（含理由 + 依据的季度）；
`GOVERNANCE.md` 分布表与本次实跑一致；墓碑句存在。

**交付**：分支 `arch/A5-1` + `devkit/handoff/A5-1.md`（含降档/删除逐项清单）

**禁止**：以"减少门数量"为目标（判据是"门还在守什么"，不是数量）；
删掉还有活引用的脚本（[11] 会拦，别硬来）。

---

### 集成

#### A6-INT · 集成 Agent（全程持续）

见 §六 的提示词 B。

---

## 六、派发提示词

> **提示词本体在 [`DISPATCH.md`](DISPATCH.md)**（本仓唯一的派发件真源，含提示词 A／B 与派发清单）。
> 本文件不复制一份——复制就是第二份真源，正是本方案要治的病。
> 派发流程：开 `DISPATCH.md` → 复制提示词 A 整段 → 把 `{{TODO_ID}}` 换成卡 ID、
> 把 `{{TODO_CARD}}` 换成 §五 里那张卡的**原文整段** → 发出。

### 提示词 B · 集成 Agent（A6-INT）

见 [`DISPATCH.md`](DISPATCH.md) 的「提示词 B」。

---

## 七、验收标准总账

每个阶段收口时逐条打勾，**缺一项该阶段不算完成**。

| # | 验收项 | 命令 / 判据 | 起于 |
|---|---|---|---|
| V1 | 两科门禁不低于基线 | `python liuyao/dev_tools/check.py` 与 `python bazi/dev_tools/check.py` 均 rc=0 | 每批 |
| V2 | 分发面不漂移 | `node plugins/scripts/build.mjs && node plugins/scripts/selftest.mjs` rc=0 | 改动 core/scripts/references 时 |
| V3 | 根级文档无悬空引用 | `python devkit/root/check_root_docs.py` rc=0（**且负例自证已做**） | P0 起 |
| V4 | 文档索引对账 | `python devkit/root/check_docs_index.py` rc=0 | P0 起 |
| V5 | 门禁单一真源 | `python devkit/sync_devkit.py --check` rc=0（**且负例自证已做**） | P1 起 |
| V6 | 内核单一真源 | `python kernel/sync_kernel.py --check` rc=0（+ CI `kernel-sync` job） | P3 起 |
| V7 | 契约三件套同步 | `CONTRACT.md` + 两科 `layer_contract.json` + 两科 `CHANGELOG.md` 三处一致 | 改层界/键面时 |
| V8 | 两科形状对称 | 八字有 `tests/`（smoke+regression 两类）、三件套 CHANGELOG、契约欠账结论行 | P2 末 |
| V9 | CI 四 job | `root-gates` / `kernel-sync` / `gates` / `plugin-gates`（五宿主 × 2 OS） | P4 末 |
| V10 | 门禁档位在册 | `governance_map.py` 实跑档位表与 `GOVERNANCE.md` 一致，降档/删除均已具名 | P5 末 |
| V11 | 口径 | 全仓无"预测准确率"类表述（自检 [7] 段逐行扫） | 每批 |
| V12 | 登记 × 提交 | 写进 CHANGELOG 的批次**必须能在 git log 里指到提交** | 每批 |
| V13 | 并发合规 | 25 条分支全部来自 `arch/<ID>`，越域写入 0 次，`devkit/handoff/` 未入库 | 全程 |
| V14 | handoff 齐备 | 25 份报告齐备，每份含实测输出片段（不是只写"通过"） | 全程 |
| V15 | 集成后全链 | 每 merge 一条必跑验证链，rc 全 0 | 全程 |

**负例自证清单（新挂的门必做，三条齐全才算过）**：

```
1. 造明知不存在的目标 → 门必须 EXIT≠0 且报出明细（文件名 + 行号）
2. 撤掉负例 → 门回到 rc=0
3. 命令 + 输出片段写进该批 CHANGELOG
```

### 收口实测（2026-10-29，单 Agent 串行收口；逐条对应 V1–V15）

| # | 实测 | 读数 |
|---|---|---|
| V1 | 两科 `check.py` | `rc=0` / `rc=0`（liuyao 含 [37]，bazi 含 [37]/[38]） |
| V2 | `node plugins/scripts/build.mjs` + `selftest.mjs` | `rc=0`；自检 7 段全绿（含负例自证） |
| V3 | `python devkit/root/check_root_docs.py` | `rc=0`（8 份根级 md，129 条引用，0 死链）；`--selftest` rc=0（4 类负例） |
| V4 | `python devkit/root/check_docs_index.py` | `rc=0`（55 份文档全部登记可达）；负例（`__probe.md` git add）判红后撤掉回绿 |
| V5 | `python devkit/sync_devkit.py --check` | `rc=0`（11 共享件 × 2 科）；`--selftest` 6 类负例全抓 |
| V6 | `python kernel/sync_kernel.py --check` | `rc=0`（17/15 文件＋4 变体）；CI `kernel-sync` job 已挂 |
| V7 | 契约三件套 | 本轮未改键面/禁边，两科 `check_layer_contract.py --selftest` 均 rc=0；结论行已写进 CONTRACT §六 |
| V8 | 八字形状 | `tests/smoke+regression` 在册、CHANGELOG 三件套（2500/460/76 行）、§六 八字审计表在册 |
| V9 | CI 四 job | `root-gates`/`kernel-sync`/`gates`/`plugin-gates`（五宿主 × 2 OS），无 `continue-on-error` |
| V10 | 治理地图 | `governance_map.py --strict` rc=0（两科未分类 0）；本批不降不删，结论与墓碑句在册 |
| V11 | 口径 | `selftest.mjs` [7] 段禁语扫描全绿；本轮全部文字用"古籍案例对齐分/非预测命中率" |
| V12 | 登记 × 提交 | `readout_ledger.py --quick` rc=0（bad=0/全账 39，含"登记×提交在册"一项） |
| V13 | 并发合规 | 单 Agent 串行（见 §五 完成台账下的偏差登记）；外部三命通会 7 路径未改未提交；`devkit/handoff/` 不入库 |
| V14 | handoff | 25 张卡＋A6-INT 报告齐备，均在 `devkit/handoff/`（gitignore） |
| V15 | 集成后全链 | 每 merge 等价动作后均跑两科 `check.py`＋`sync_devkit --check`＋`kernel --check`，最终 rc 全 0 |

**已知欠账（诚实登记）**：`devkit/root/check_batch_num.py` 尚未实现（A6-INT 步骤 4
的"门尚未就位时先记欠账"）；批次×提交不变量暂由 `readout_ledger` 的
"登记×提交在册"项守。本项不影响 V12 的现有读数，但若要把它升级成独立门，需另批实现
（扫描七份 CHANGELOG 的批次号并对 `git log` 逐批回指）。

---

## 八、显式不做的事

> 这些是本方案**主动排除**的方向。执行者若发现 TODO 里没有但看起来该做的事，
> 先对照本节——不在本节也不在 TODO 里的，交 handoff 报告，不要自己加。

1. **不合并两科**——零耦合是设计目标，不是待修的重复（AGENTS.md §二）。
2. **不复活 `synthesis` 合参层**——已移除且不得复活。
3. **不克隆六爻的推演链到八字**——形状对称 ≠ 规模对称（D3 中档）。
4. **不回填六爻门编号的 9 个空号**——墓碑不复用，新门从 [37] 续。
5. **不归并 `check.py` 与 `__init__.py`**——前者是各科编排器（本应不同），后者差异仅 docstring。
6. **不删两科 `scripts/` 下的四段同名入口**——那是契约要求的形状重复。
7. **不把两科 `core/` 加进 `.gitignore`**——D1 已定为 C。
8. **不把 `devkit/shared` 改成 import 共享**——会破坏单目录独立性（D2）。
9. **不为整洁而合并六份 CHANGELOG**——先评估，结论若为维持则结案。
10. **不改四段契约本体与三条铁律**——本方案只动治理覆盖面，不动被治理的对象。
11. **不追求"门禁行数下降"这个数字本身**——瘦身的判据是"门还在守什么"（GOVERNANCE 五档）。
12. **不触碰外部三命通会会话占用的 7 个路径**（§4.0）。

---

## 九、与既有文档的关系

| 文件 | 本方案动它吗 | 谁动 / 怎么动 |
|---|---|---|
| `AGENTS.md` | 是 | A0-3 修 3 处悬空引用；A1-1 后 A6-INT 补"门禁内核真源"条；A3-2 后补 `data/cache/` 层 |
| `CONTRACT.md` | 是 | A0-3 修 1 处悬空引用；A2-B 改路径 + 加 §二-bis 剖面 + 八字欠账结论 |
| `DOCS.md` | 是 | A0-0 已完成；后续由 A6-INT 从 `devkit/pending/` 合入 |
| `GOVERNANCE.md` | 是 | A5-1 更新档位分布表 |
| `README.md` | 是 | A0-0 已完成入口；A1-1 后 A6-INT 补 `devkit/` 目录树；A2-A 后补八字 `tests/` 一行 |
| `CAPABILITY.md` | **否** | 本方案不改任何对外读数 |

> 立本文件时 A0-0 已完成（含 `README.md` 入口）；其余由对应卡的批次负责。
