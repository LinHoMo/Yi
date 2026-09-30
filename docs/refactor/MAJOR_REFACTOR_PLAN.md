# 易 · Major Version 重构总计划

> **审计日期**: 2026-09-29  
> **审计基础**: main@31eeb9b + 未提交更改（五科还原）  
> **目标版本**: v1.0.0（破坏性更新）  
> **审计师**: Claude Opus 5.5

---

## 〇、执行摘要

本项目由多个 AI Agent 逐步生成，虽然已建立质量门、债务登记、四段契约等规范，但仍存在**系统性结构问题**：

1. **六爻（liuyao）占据 53% 代码量**（19,437/36,678 行），内部 58 个脚本高度耦合，模块边界模糊
2. **四科重复实现**：meihua/xiaoliuren/zeji/ming 各自实现四段管线，未抽取共性
3. **测试分散**：学科内 `scripts/smoke_test.py` 与仓库根 `tests/` 并存，职责不清
4. **文档冗余**：53 个 Markdown 文件，多处重复记录（HANDOFF/CHANGELOG/TECH-DEBT/PLAN）
5. **依赖方向虽单向但隐式**：学科间无 import，但通过 synthesis 间接耦合
6. **命名不一致**：学科内 `tools/` vs 仓库根 `tools/`，已知歧义但未解决

**核心判断**：项目已进入"规范债"阶段——不缺规范文档（AGENTS.md/CONTRACT.md 写得很清楚），缺的是**结构强制执行**。

**重构策略**：

- **不是重写**：保留所有通过质量门的功能实现
- **是重组**：按第一性原理重新划分模块边界、统一接口、消除重复
- **目标**：新开发者能在 30 分钟内跑起来并理解架构；旧债不再增殖

---

## 一、当前审计发现

### 1.1 代码规模与分布

```
总计:        36,678 行 Python
├─ core:      2,793 行 (7.6%)   ✅ 结构清晰，职责单一
├─ liuyao:   19,437 行 (53.0%)  ⚠️  巨石学科，内部 58 脚本高耦合
├─ ming:        841 行 (2.3%)   ✅ 精简，符合"机械推演"定位
├─ meihua:      ~800 行          ✅ 四段管线完整
├─ xiaoliuren:  ~600 行          ✅ 四段管线完整
├─ zeji:        ~650 行          ✅ 四段管线完整
├─ synthesis: 1,201 行 (3.3%)   ✅ 职责清晰
└─ tools:     1,466 行 (4.0%)   ✅ 仓库级工具，边界明确
```

### 1.2 质量门现状

```bash
$ python tools/check.py
[0] 版本一致性 ✅
[1] 结构契约   ✅
[1b] 命名规范  ✅
[2] 内核自检   ✅
[3] ming 门    ✅
[6] 六爻冒烟   ✅
[7] 合参层     ✅
```

**基线稳固**：所有质量门绿灯，可以安全重构。

### 1.3 结构问题（按严重性排序）

#### P0 - 阻碍新学科接入

| 问题 | 影响 | 证据 |
|------|------|------|
| **四科重复实现四段管线** | 新学科需复制 8 个脚本 | meihua/xiaoliuren/zeji/ming 各有 chart/analyze/narrate/render/evaluate/case_runner/mcp_server/smoke_test |
| **无共享基类或契约强制** | 四段契约只是文档约定 | CONTRACT.md 写明接口，但无 Python Protocol/ABC 强制 |
| **评分器分散** | 每科各写一份 evaluate.py | liuyao/evaluate.py 448 行，其余科 ~150 行，核心逻辑雷同 |

#### P1 - 维护成本高

| 问题 | 影响 | 证据 |
|------|------|------|
| **六爻内部耦合** | 改一处需检查 58 个文件 | chain_step5 依赖 chain_step1-4，classical_rules 被 10+ 模块导入 |
| **测试职责不清** | 学科 smoke_test 在 scripts/ 还是 tests/？ | liuyao/tests/ 3 个 + liuyao/scripts/ 曾有 3 个（已迁移），其余科在 scripts/ |
| **文档重复记录** | 同一事实在 4 处登记 | CHANGELOG → HANDOFF → TECH-DEBT → PLAN，修改需同步 |

#### P2 - 用户体验差

| 问题 | 影响 | 证据 |
|------|------|------|
| **入口分散** | 每科不同命令 | liuyao 用 `yi_liuyao.py`，ming 用 `chart.py` + `analyze.py`，无统一 CLI |
| **报告格式不一** | HTML/MD/JSON 混杂 | liuyao 输出 HTML，ming 输出结构化 JSON，合参层不知道怎么拼 |
| **MCP 服务器各自实现** | 6 个独立 mcp_server.py | 每科 200-700 行，工具注册逻辑重复 |

### 1.4 技术债务（已登记）

见 `docs/TECH-DEBT.md`。关键项：

- ✅ 已清偿：B1/B2/B3 巨石拆分、质量门编码、断语外置大部分
- ⌛ 待清偿但非阻塞：wikisource 应期泛化（需外部数据）、classical_rules 残余断语
- ✅ 有意保持：命科不批吉凶、星煞不进主分

**判断**：技术债已受控，不阻碍重构。

### 1.5 测试覆盖

- **pytest**: 76 passed (tests/ 目录，覆盖 core 与 liuyao 核心链路)
- **学科 smoke_test**: 各科自测，覆盖四段管线端到端
- **黑箱回归**: liuyao 18 例金标准指纹
- **案例评测**: liuyao tune/holdout，其余科 100% 对齐分

**判断**：测试充分，可作为重构安全网。

---

## 二、第一性原理推导

### 2.1 系统存在理由

**核心用户**：个人求测者（命运趋势 + 具体决策）

**最小闭环**：
1. 输入：出生时空（命）/ 问题+起卦参数（卜）
2. 处理：机械排盘 → 规则推演 → 人话解读
3. 输出：单份报告（盘面 + 正文 + 判据）

**不可变约束**：
- **铁律一**：排盘必须由代码完成（LLM 不心算）
- **铁律二**：案例库与预测过程物理隔离
- **铁律三**：不宣称现实预测命中率
- **四段契约**：chart → analyze → narrate → render（硬边界）
- **内核唯一真值源**：干支历、象数表、卦辞只在 core 存一份

### 2.2 必要模块

按依赖方向（只能单向）：

```
core/           # 时空计算 + 象数表（零依赖，可独立发包）
  ├─ calendar   # 干支历、节气、农历
  ├─ symbols    # 五行生克、纳甲、八宫
  └─ eval       # 评分器

disciplines/    # 各学科（只依赖 core，学科间零依赖）
  ├─ liuyao/
  ├─ ming/
  ├─ meihua/
  ├─ xiaoliuren/
  └─ zeji/

synthesis/      # 合参层（依赖各科的 schema，不依赖实现）

cli/            # 统一入口（依赖 disciplines + synthesis）
```

**删除判断**：
- ❌ 不删 archive/（git 历史已记录，删了反而查不到）
- ❌ 不删 docs/compose/spec/（规格归档，虽然不再更新）
- ✅ 可删 `.workbuddy/memory/2026-09-27.md`（已在 git diff 里标记删除）
- ✅ 可删学科内重复的 `__init__.py`（空文件，非包）

### 2.3 失败模式

1. **质量门红灯**：阻止合入
2. **案例对齐分下跌**：回滚重构
3. **学科间循环依赖**：违反架构，直接驳回
4. **LLM 心算排盘**：SKILL.md 明确禁止，但无代码强制

---

## 三、目标架构

### 3.1 目录结构（目标态）

```
Yi/
├── pyproject.toml              # 内核包 yishu-core
├── README.md                   # 快速开始 + 一条命令演示
├── AGENTS.md                   # 项目铁律（不变）
│
├── core/yishu_core/            # 内核（可独立发包）
│   ├── calendar.py             # 合并 ganzhi_calendar + lunar
│   ├── symbols.py              # 象数表（含纳音、三合、星煞）
│   ├── eval.py                 # 评分器（唯一）
│   ├── runtime.py              # 跨平台适配
│   └── __init__.py
│
├── disciplines/                # 学科层（各科自包含）
│   ├── base/                   # 🆕 共享基类与工具
│   │   ├── protocol.py         # 四段契约 Protocol 定义
│   │   ├── runner.py           # 通用 case_runner / evaluate
│   │   ├── mcp.py              # MCP 服务器基类
│   │   └── cli.py              # 学科级 CLI 基类
│   │
│   ├── liuyao/                 # 六爻（最复杂学科）
│   │   ├── SKILL.md            # 学科文档
│   │   ├── core/               # 🆕 核心推演（纯函数）
│   │   │   ├── chart.py
│   │   │   ├── analyze.py      # 合并 chain_step1-5
│   │   │   └── narrate.py
│   │   ├── rules/              # 🆕 规则引擎（数据驱动）
│   │   │   ├── classical.py    # 合并 classical_rules_*
│   │   │   └── timing.py       # 应期核心逻辑
│   │   ├── data/               # 数据（不变）
│   │   ├── tests/              # 单元测试（pytest 收集）
│   │   └── cli.py              # 学科入口
│   │
│   ├── ming/                   # 四柱（结构已优）
│   ├── meihua/                 # 梅花（结构已优）
│   ├── xiaoliuren/             # 小六壬（结构已优）
│   └── zeji/                   # 择吉（结构已优）
│
├── synthesis/                  # 合参层（不变）
│   ├── person.py
│   ├── cross_rules.py
│   └── guidance.py
│
├── cli/                        # 🆕 统一命令行入口
│   ├── main.py                 # yi <discipline> <command>
│   └── mcp_server.py           # 统一 MCP 路由
│
├── tools/                      # 仓库级工具（不变）
│   ├── check.py
│   ├── eval.py
│   └── demo.py
│
├── tests/                      # 仓库级测试（不变）
│   └── test_*.py
│
└── docs/                       # 文档（精简后）
    ├── ARCHITECTURE.md         # 🆕 架构决策记录
    ├── MIGRATION.md            # 🆕 v0→v1 迁移指南
    ├── CHANGELOG.md            # 保留（合并 TECH-DEBT 已清偿项）
    ├── HANDOFF.md              # 保留（合并 YI-PLAN）
    └── refactor/               # 本次重构文档
```

### 3.2 核心变更

#### 变更 1：新增 `disciplines/base/` 共享层

**目标**：消除四科重复实现。

**内容**：
- `protocol.py`: 定义 `ChartProtocol`, `AnalyzeProtocol`, `NarrateProtocol`, `RenderProtocol`
- `runner.py`: 通用 `run_cases()` + `evaluate_discipline()`
- `mcp.py`: MCP 服务器基类，子类只需注册工具
- `cli.py`: 学科 CLI 基类，提供 `chart/analyze/narrate/render` 子命令

**不做**：不抽象学科推演逻辑（六爻的应期规则与命科的大运推演完全不同，强行抽象会产生空接口）。

#### 变更 2：liuyao 内部重组

**现状**：58 个脚本，职责交叉。

**目标态**：
```
liuyao/
├── core/          # 纯函数推演（无 I/O）
│   ├── chart.py
│   ├── analyze.py    # 合并 chain_step1-5，保留分步函数但统一入口
│   └── narrate.py    # 合并 chain_narrate + human_narrative
│
├── rules/         # 规则引擎（数据驱动）
│   ├── classical.py  # 合并 classical_rules_* 7 个文件
│   ├── timing.py     # 应期核心（合并 chain_step5_yp_timing + yingqi_windows）
│   └── effects.py    # 合并 effects_* 3 个文件
│
├── support/       # 工具函数（保留，已清晰）
│   ├── tables.py     # classical_tables + engine_tables
│   └── utils.py      # chain_support
│
├── data/          # 不变
├── tests/         # 不变
└── cli.py         # 新统一入口
```

**合并原则**：
- 按**职责域**合并，不按文件大小
- 合并后单文件不超过 800 行（可放宽至 1200 行如有充分理由）
- 保留所有公共函数签名（向后兼容）

#### 变更 3：统一 CLI

**现状**：
```bash
cd disciplines/liuyao && python scripts/yi_liuyao.py "问题"
cd disciplines/ming && python scripts/chart.py --datetime "..." --gender 男
```

**目标**：
```bash
yi liuyao cast "问题"                    # 一键出报告
yi liuyao chart --mode coin              # 单步：起卦
yi liuyao analyze <chart.json>           # 单步：推演
yi ming chart --datetime "..." --gender 男
yi meihua cast "问题"
```

**实现**：
- 新增 `cli/main.py`，使用 `click` 或 `typer` 构建子命令树
- 各学科 `cli.py` 继承 `disciplines/base/cli.py`
- 安装后 `yi` 命令全局可用（pyproject.toml `[project.scripts]`）

#### 变更 4：文档精简

**现状**：53 个 MD 文件，多处重复。

**目标**：核心 7 份文档

| 文件 | 职责 | 来源 |
|------|------|------|
| `README.md` | 快速开始 | 保留 |
| `AGENTS.md` | 项目铁律 | 保留 |
| `docs/ARCHITECTURE.md` | 架构决策 | 🆕 合并 CONTRACT + YI-PLAN |
| `docs/CHANGELOG.md` | 口径与变更 | 保留，合并 TECH-DEBT 已清偿项 |
| `docs/HANDOFF.md` | 现状交接 | 保留 |
| `docs/MIGRATION.md` | v0→v1 迁移 | 🆕 |
| `disciplines/<科>/SKILL.md` | 学科文档 | 保留（5 份） |

**删除/归档**：
- `docs/YI-PLAN.md` → 合并进 ARCHITECTURE.md
- `docs/LIUYAO-PLAN.md` → 内容已在 liuyao/docs/CHANGELOG.md
- `docs/TECH-DEBT.md` → 已清偿项写进 CHANGELOG，待清偿项写进 HANDOFF
- `docs/CONTRACT.md` → 合并进 ARCHITECTURE.md
- `docs/compose/spec/*.md` → 归档（历史规格，不删但标记 deprecated）

---

## 四、模块边界与依赖规则

### 4.1 依赖方向（强制单向）

```
cli → synthesis → disciplines/base → disciplines/<科> → core
                                   ↘ disciplines/<科> →↗
```

**规则**：
1. `core` 零外部依赖（只用 Python 标准库）
2. 学科只能 `import yishu_core`，禁止 `import disciplines.<其他科>`
3. `disciplines/base` 只能依赖 `core`，不依赖具体学科
4. `synthesis` 通过 Protocol 依赖学科接口，不依赖实现
5. `cli` 可以依赖所有层

**检查**：质量门新增依赖方向检查（解析 AST import 语句）。

### 4.2 公共接口（Protocol）

```python
# disciplines/base/protocol.py
from typing import Protocol, Dict, Any

class ChartProtocol(Protocol):
    """起卦/排盘接口"""
    def chart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """纯确定性，无解读"""
        ...

class AnalyzeProtocol(Protocol):
    """规则推演接口"""
    def analyze(self, chart: Dict[str, Any]) -> Dict[str, Any]:
        """输出因子、权重、判据、所本法则"""
        ...

class NarrateProtocol(Protocol):
    """人话叙述接口"""
    def narrate(self, analysis: Dict[str, Any]) -> str:
        """唯一交付正文"""
        ...

class RenderProtocol(Protocol):
    """报告渲染接口"""
    def render(self, analysis: Dict[str, Any], format: str = "html") -> str:
        """调用 yishu_core.report"""
        ...
```

**强制**：各学科 `cli.py` 必须声明实现这些 Protocol（mypy 检查）。

### 4.3 数据模型（JSON Schema）

**现状**：各科输出结构不一致。

**目标**：定义 `disciplines/base/schema.json`

```json
{
  "chart": {
    "discipline": "liuyao | ming | ...",
    "timestamp": "ISO8601",
    "input_params": {},
    "chart_data": {}
  },
  "analysis": {
    "chart": {},
    "factors": [],
    "verdict": {"direction": "吉|凶|平", "confidence": 0.0-1.0},
    "basis": []
  },
  "narrative": {
    "summary": "...",
    "reasoning": "...",
    "advice": "..."
  }
}
```

**验证**：新增 `tools/schema_check.py`，质量门调用。

---

## 五、删除/合并/重命名清单

### 5.1 删除（7 项）

| 路径 | 理由 | 风险 |
|------|------|------|
| `.workbuddy/memory/2026-09-27.md` | 已在 git diff 标记删除 | 无 |
| `disciplines/*/scripts/__init__.py`（空文件） | 学科非 Python 包 | 无 |
| `disciplines/*/tools/__init__.py`（空文件） | 同上 | 无 |
| `docs/YI-PLAN.md` | 合并进 ARCHITECTURE.md | 无（内容已迁移） |
| `docs/LIUYAO-PLAN.md` | 内容已在 liuyao/CHANGELOG | 无 |
| `docs/CONTRACT.md` | 合并进 ARCHITECTURE.md | 无 |
| `docs/TECH-DEBT.md` | 拆分到 CHANGELOG + HANDOFF | 无 |

### 5.2 合并（liuyao 重点，14 组）

| 目标 | 合并来源 | 预估行数 |
|------|----------|----------|
| `liuyao/core/analyze.py` | chain_step1-5（5 个文件） | ~2,500 → 800 |
| `liuyao/core/narrate.py` | chain_narrate + chain_narrate_patterns + human_narrative + human_narrative_segments（4 个） | ~1,800 → 600 |
| `liuyao/rules/classical.py` | classical_rules + classical_rules_combo + classical_rules_effects + classical_rules_growth + classical_rules_hidden + classical_rules_patterns + classical_support（7 个） | ~3,500 → 1,000 |
| `liuyao/rules/timing.py` | chain_step5_yp + chain_step5_yp_timing + yingqi_windows（3 个） | ~1,200 → 600 |
| `liuyao/rules/effects.py` | effects_change + effects_harmony + effects_structure（3 个） | ~1,500 → 500 |
| `liuyao/support/tables.py` | classical_tables + engine_tables（2 个） | ~600 → 400 |
| `liuyao/support/utils.py` | chain_support + chain_verdicts（2 个） | ~800 → 500 |

**合并策略**：
- 保留所有公共函数（向后兼容）
- 私有函数 `_xxx` 可以内联或重命名避免冲突
- 增加模块级注释说明各函数域

### 5.3 重命名（2 项）

| 旧 | 新 | 理由 |
|---|---|---|
| `disciplines/liuyao/tools/` | `disciplines/liuyao/dev_tools/` | ✅ 已完成 |
| `disciplines/ming/tools/` | `disciplines/ming/dev_tools/` | ✅ 已完成 |

**其余学科（meihua/xiaoliuren/zeji）的 `tools/` 也改为 `dev_tools/` —— 均已完成。**

---

## 六、测试策略

### 6.1 保留（回归安全网）

- ✅ `tests/` 下所有 pytest（76 passed）
- ✅ 各学科金标准指纹（liuyao 18 例黑箱回归）
- ✅ 各学科案例评测（tune/holdout 分列）

### 6.2 调整

**问题**：学科 `smoke_test.py` 位置不一致
- liuyao: `tests/smoke_test.py` ✅
- meihua/xiaoliuren/zeji: `scripts/smoke_test.py` ⚠️

**目标**：统一迁移到各科 `tests/smoke_test.py`（pytest 可收集）。

### 6.3 新增

1. **依赖方向检查**（`tools/check.py` 扩展）
   - 解析所有 `.py` 的 import 语句
   - 检查是否有学科间互相 import
   - 检查是否有 `from disciplines.<科>` 出现在 core/base

2. **Schema 验证**（`tools/schema_check.py`）
   - 各科 `chart/analyze/narrate` 输出符合 JSON Schema
   - 合参层输入验证

3. **Protocol 合规**（mypy）
   - 各学科 `cli.py` 必须声明实现 Protocol
   - CI 加入 `mypy --strict disciplines/`

---

## 七、迁移策略

### 7.1 迁移原则

1. **向后兼容**：v0.0.1 的所有公共 API 在 v1.0.0 仍可用（标记 deprecated）
2. **渐进迁移**：新旧入口并存一个版本
3. **文档先行**：先写 MIGRATION.md，再动代码

### 7.2 破坏性变更

| 变更 | 影响 | 迁移路径 |
|------|------|----------|
| **CLI 统一为 `yi <科> <命令>`** | 旧命令 `python scripts/yi_liuyao.py` 废弃 | 保留旧脚本但打印 deprecation warning："Use `yi liuyao cast` instead" |
| **学科 `tools/` → `dev_tools/`** | 学科内开发工具路径变化 | 影响学科开发者，不影响用户；HANDOFF 更新 |
| **liuyao 内部模块合并** | 学科内 import 路径变化 | 只影响扩展 liuyao 的开发者；保留旧导入别名一个版本 |
| **文档精简（7 份核心）** | 历史文档查找 | 归档文件夹加 README 索引："已合并进 ARCHITECTURE.md" |

### 7.3 迁移检查清单

- [ ] 所有旧 CLI 命令加 deprecation warning
- [ ] 旧 import 路径保留别名（`from .core.analyze import step1_read_situation as _step1`）
- [ ] MIGRATION.md 列出所有破坏性变更 + 替代方案
- [ ] README.md 更新为新命令
- [ ] 各学科 SKILL.md 更新为新命令

---

## 八、破坏性变更列表

### 8.1 用户可见变更

1. **CLI 入口统一**
   - 旧：`python disciplines/liuyao/scripts/yi_liuyao.py "问题"`
   - 新：`yi liuyao cast "问题"`
   - 迁移：旧脚本保留但 deprecated

2. **报告格式标准化**
   - 旧：各科输出 HTML/JSON/MD 混杂
   - 新：统一 JSON 结构（可选 HTML/MD 渲染）
   - 迁移：`--format` 参数兼容旧行为

3. **MCP 服务器统一**
   - 旧：每科独立 `python scripts/mcp_server.py`
   - 新：`yi mcp`（自动注册所有学科）
   - 迁移：旧服务器标记 deprecated

### 8.2 开发者可见变更

1. **学科内 tools/ → dev_tools/**
   - 影响：学科开发者 import 路径
   - 迁移：搜索替换 + HANDOFF 更新

2. **liuyao 内部模块重组**
   - 影响：扩展 liuyao 的第三方
   - 迁移：保留旧导入别名一个版本

3. **四段契约从文档变为 Protocol**
   - 影响：新学科接入必须实现 Protocol
   - 迁移：`disciplines/base/protocol.py` 提供示例

---

## 九、风险与回滚

### 9.1 风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 合并后质量门红灯 | 中 | 高 | 每个合并后立即跑 `tools/check.py` |
| 案例对齐分下跌 | 低 | 高 | 合并前后跑 `refactor_guard.py`（零漂移） |
| 用户旧脚本失效 | 高 | 中 | 保留旧脚本一个版本 + deprecation warning |
| 文档迁移遗漏 | 中 | 低 | MIGRATION.md 列出所有变更 + 示例 |

### 9.2 回滚方案

每个任务阶段独立 git commit，标签格式 `refactor/<阶段>-<任务ID>`。

**回滚点**：
- 阶段 0 完成：`git tag refactor/stage0-done`
- 阶段 1 完成：`git tag refactor/stage1-done`
- ...

**回滚命令**：
```bash
git reset --hard refactor/stage<N>-done
git clean -fd
python tools/check.py --full  # 验证回滚后绿灯
```

---

## 十、验收标准

### 10.1 功能验收

- [ ] `python tools/check.py --full` 全绿
- [ ] 所有学科 tune/holdout 分数不低于基线（liuyao tune≥93.9, holdout≥87.5）
- [ ] pytest 76+ passed（新增测试可能增加数量）
- [ ] 各学科端到端：`yi <科> cast` 出单份报告

### 10.2 结构验收

- [ ] 依赖方向检查通过（无学科间循环依赖）
- [ ] 学科数量 ≤ 6（liuyao/ming/meihua/xiaoliuren/zeji + base）
- [ ] liuyao 脚本数量 ≤ 20（从 58 → ~15-20）
- [ ] 文档数量 ≤ 20（从 53 → ~15，核心 7 份）

### 10.3 体验验收

- [ ] 新开发者跑通 README 示例 ≤ 30 分钟
- [ ] `yi --help` 列出所有学科和命令
- [ ] 旧用户按 MIGRATION.md 迁移 ≤ 1 小时

### 10.4 债务验收

- [ ] 无新增"已知问题"（TECH-DEBT 不增长）
- [ ] 巨石看门狗通过（单文件 ≤ 800 行，放宽至 1200 行需注释说明）
- [ ] 断语字面量检查通过（代码无成段中文）

---

## 十一、给弱执行模型的总规则

执行 `EXECUTION_TASKS.md` 中的任务时，必须遵守：

### 11.1 任务执行纪律

1. **一次只做一个任务**，按 `EXECUTION_TASKS.md` 顺序执行
2. **开始前读取任务全文** + 涉及的所有文件
3. **不自行扩大范围**：任务说改 A 就只改 A，不顺手改 B
4. **不自行新增**：不新增依赖、抽象、文档、测试，除非任务明确要求
5. **遇歧义立即停止**：报告 "任务 T-XXX 歧义：<具体问题>"，不要猜

### 11.2 验证要求

每个任务完成后必须：

1. 运行任务指定的验证命令（如 `python tools/check.py`）
2. 报告验证结果（通过/失败 + 输出摘要）
3. 如果失败，**回滚本次修改**，报告失败原因
4. **不允许"先提交，测试失败再修"**

### 11.3 重构三不原则

1. **不保留双份实现**：合并后删除源文件，不留"备份"
2. **不保留兼容层**：除非 MIGRATION.md 明确要求
3. **不保留死代码**：`# TODO` / `# FIXME` / 注释掉的代码一律删除

### 11.4 报告格式

任务完成报告格式：

```
## 任务 T-XXX 完成报告

**任务**: <标题>
**涉及文件**: <列表>
**验证命令**: <命令>
**验证结果**: ✅ 通过 / ❌ 失败

### 修改摘要
- <修改 1>
- <修改 2>

### 验证输出（摘要）
<输出前 20 行>

### 遗留问题（如有）
<问题描述>
```

### 11.5 禁止事项

- ❌ 不允许自行宣布"整体重构完成"（必须由用户或强模型审查）
- ❌ 不允许跳过验证命令
- ❌ 不允许"验证失败但我觉得没问题"
- ❌ 不允许修改 `EXECUTION_TASKS.md`（任务单是不可变的）

---

## 十二、后续规划（v1.0.0 之后）

本次重构聚焦**结构清理**，以下特性延后：

1. **性能优化**：liuyao 推演耗时（目前 ~2s 可接受）
2. **Web UI**：当前 HTML 报告已够用
3. **并发评测**：案例评测串行（重构后考虑并行）
4. **CI/CD**：当前本地质量门够用，推送前手动跑

**判断依据**：这些不阻碍新学科接入，也不影响当前用户。

---

## 附录 A：术语表

| 术语 | 含义 |
|------|------|
| **四段契约** | chart → analyze → narrate → render，学科接入标准 |
| **铁律** | AGENTS.md 三条不可动摇原则（运算归代码/案例隔离/口径诚实） |
| **对齐分** | 古籍案例对齐分，非现实预测命中率 |
| **tune/holdout** | 参与调参/未参与调参的案例集合 |
| **零漂移** | 重构前后指纹一致（用 `refactor_guard.py` 验证） |
| **巨石** | 单文件超过 800 行（放宽至 1200 行需注释说明） |

---

## 附录 B：关键决策记录

| 决策 | 理由 | 日期 |
|------|------|------|
| **不重写，只重组** | 质量门全绿，功能稳定，无需重写 | 2026-09-29 |
| **不删 archive/** | git 历史已记录，删了反而查不到 | 2026-09-29 |
| **不强行抽象推演逻辑** | 六爻应期与命科大运完全不同，抽象无意义 | 2026-09-29 |
| **liuyao 合并到 ~15 文件** | 保留职责分离，但减少耦合 | 2026-09-29 |
| **保留旧 CLI 一个版本** | 平滑迁移，不破坏用户脚本 | 2026-09-29 |

---

**审计完成时间**: 2026-09-29 19:30  
**下一步**: 执行 `EXECUTION_TASKS.md` 任务单
