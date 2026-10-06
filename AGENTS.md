# 易（Yi）· 项目级铁律

**读者边界**：本文件写给**在本仓库改代码的贡献者/编码 Agent**（Cursor、Codex 等）。
**调用 Yi 出报告的 AI（任务 Agent）不要读本文件**——你的入口是根 `llms.txt` +
`SKILL.md`（其中 §四已用"只引用不复制"的方式给你三条铁律的操作版）。
本文件与任何单个学科的 SKILL.md 冲突时，本文件优先。

本文件约束所有在本仓库工作的 agent 和 contributor。与任何单个学科的 SKILL.md 冲突时，本文件优先。

**范围**：本仓库有八科可用，均经各学科 `dev_tools/check.py` 与仓库根 `tools/check.py` 全绿。

| 学科 | 目录 | 说明 |
|---|---|---|
| **命**（四柱八字） | `disciplines/ming/` | 机械推演（强弱/格局/喜用/大运/流年），非命运断言 |
| **命**（紫微斗数） | `disciplines/ziwei/` | 安星/四化/格局/大限，四段契约 |
| **卜·六爻** | `disciplines/liuyao/` | 六爻纳甲，四段契约 chart→analyze→narrate→render |
| **卜·梅花易数** | `disciplines/meihua/` | 体用生克/互变/卦气旺衰 |
| **卜·小六壬** | `disciplines/xiaoliuren/` | 六宫掌诀断事 |
| **卜·择吉** | `disciplines/zeji/` | 建除/黄黑道/二十八宿综合裁决 |
| **卜·大六壬** | `disciplines/liuren/` | 月将加时/九宗门三传/天将乘临（骨架：机械结构标签，无吉凶断语） |
| **卜·灵棋经** | `disciplines/lingqi/` | 十二棋三部掷数，查 124 课表直录《靈棋經》原文断语（书源逐字，无书外发挥） |

**相科（面相、手相、堪舆）明确不做**——不在路线图内，不预留目录，不写占位实现。

## 一、三条不可动摇的铁律

### 1. 机械运算归代码，象数解读归 LLM

起局、排盘、装卦、定宫、纳甲、安世应、推六亲、配六神、查旬空、判旺衰、算应期、识别格局——
**必须且只能**由 Python 完成。LLM 严禁心算或"推算"任何上述结论。

LLM 的职责只有三段：收集求测信息 → 调用脚本 → 把脚本输出的结构化数据翻译成当事人看得懂的话。

脚本失败时重试一次；仍失败则告知"排盘异常"，**不得手动替代**。

### 2. 案例库与预测过程物理隔离

`**/cases/` 与 `references/case_library.md` 中的古籍案例，只允许三种访问场景：
测试运行器读取、用户明确要求事后校验、用户主动询问"有无类似案例"（须注明仅供参考）。

解读交付前禁止：打开案例库、提及案例名、以案例类比佐证、在推理链中联想案例。

### 3. 口径诚实：禁止把"对齐分"说成"预测率"

仓库内所有分数都是**古籍案例对齐分**（引擎输出与《增删卜易》等案例要点的吻合度），用于回归审计。
它衡量不了现实世界命中率。任何文档、报告、UI、对话输出中：

- ❌ 不得出现"预测准确率 99%""断事如神"一类表述
- ❌ 不得只给一个百分比而不给集合名、样本量 n、是否为未参与调参的 holdout
- ✅ 医疗、法律、投资、重大决策必须提示以专业意见为准
- ✅ 凶象用"偏向/有…信号/结构上"，不用"注定/一定/绝无可能"

## 二、目录与依赖契约

```
Yi/
├── core/                # 唯一内核 yishu_core。学科层只能 import core，禁止互相 import
├── .github/workflows/    # 云端出报告 report.yml（见 §六）
├── disciplines/
│   ├── liuyao/           # 六爻纳甲
│   ├── ming/             # 四柱八字
│   ├── ziwei/            # 紫微斗数
│   ├── meihua/           # 梅花易数
│   ├── xiaoliuren/       # 小六壬
│   ├── zeji/             # 择吉
│   ├── liuren/           # 大六壬（骨架：机械结构标签，无吉凶断语）
│   └── lingqi/           # 灵棋经（124 课表直录书源断语）
├── cli/                  # 统一命令行入口：yi <discipline> <command>
├── synthesis/            # 合参层，依赖 disciplines 的输出契约，不依赖其内部实现
├── tools/                # 仓库级命令：check / eval / demo / install / report / ci_*
└── docs/                 # 规划、规范、决策记录、审计报告、AI-SOP
```

依赖方向单向：`disciplines/<科> → core`、
`synthesis → disciplines 的 schema`、`cli/main.py → disciplines/<科>`。
学科之间禁止互相 import。违反此方向的 import 视为缺陷，评审直接驳回。
（历史备注：`disciplines/base/` 共享层（protocol/cli 基类）因全仓零引用于
2026-10-01 删除——四段契约由 `docs/CONTRACT.md` + 根 `check.py` 结构门 +
各科 golden/忠实度回归强制，不依赖运行时 Protocol；见 `docs/CHANGELOG.md`。）

### 内核唯一真值源

以下数据**在 core 中只存在一份**，学科不得复制：
天干地支、五行阴阳、六合六冲三合三刑六破、十二长生、墓库、旬空、
六十四卦卦表、八宫归属、纳甲支表、卦辞爻辞、干支历换算、调候用神表。

历史教训：同一批表曾在三个文件里各存一份且取值不一致（证据见 `docs/LIUYAO-PLAN.md` §1.1）。
新增规则表时，先确认 core 里没有；没有就加进 core，不要就地新建。

**执行方式（2026-10-06j 补充）**：这条不只是评审要求，`tools/check.py` 有机械门禁
（第 6 项「唯一真值源」），按**内容指纹**拦截两类形态——
① `disciplines/**` / `tools/**` 里出现干支序列字面量（如 `STEMS = "甲乙丙丁…"`）；
② 改名复制的内核表副本（如 `XUN_KONG → EMPTY_DEATH`）。
**新写工具先照正确范式抄**：`disciplines/ming/dev_tools/sync_tiaohou_engine.py`
——`from yishu_core.symbols import HEAVENLY_STEMS`，注意 `HEAVENLY_STEMS` 是 **list**，
插进正则字符类前须 `"".join(...)` 展平。

### 数据缺陷 vs 引擎缺陷（2026-10-06j 补充）

读数不对时，**先判责任方再动手**：是引擎错了，还是 expected/引文错了？
手段：`git show HEAD:<file>` 抽旧表，与当前逐格对拍（范式见
`disciplines/ming/dev_tools/diff_tiaohou_vs_head.py`）。

- **禁止按读数改数据**——把 expected 改成迎合引擎，等于用调参掩盖缺陷，
  且会让「分数」失去意义（同 §一 铁律三）。
- 案例库的 `source_quote` **必须是书源逐字子串**，否则违反「引文可指回原文」。
  现行情形：外集 QTBJ 批有 9 条为压缩改写（详见 `docs/TECH-DEBT.md` §2.4），
  待重建；重建须从书源重新取该格月度句，**不得改引擎凑分**。
- **月令 ≠ 月支**：正月建寅，故 6 月为**未**、午月为**五月**。改调候表前先核月支，
  勿把「午月案例」与「6月（未）那一格」混为一谈。

## 三、命名与文件规范

| 规则 | 禁止 | 要求 |
|------|------|------|
| 文件名 | `run_blind_v5.py`、`HANDOFF_V8.md` | 名字不携带版本；版本走 git 与 `docs/CHANGELOG.md` |
| 调试脚本 | `data/cases/_patch_xxx.py`、`_debug_yyy.py` | 一次性脚本放 `tools/scratch/`（已 gitignore），或写完即删 |
| 产物 | `outputs/`、`*.html`、`*.jsonl` 入库 | 全部生成物 gitignore，需要留存样例的进 `docs/samples/` 并说明 |
| 入口 | `sys.argv` 手解、无 `--help` | 每个 CLI 用 argparse，`--help` 可看，失败退出码非 0 |
| 路径 | 硬编码 `C:\Users\<name>\...` | 相对 skill 根解析，或用显式参数 |
| 断语字面量 | 在 .py 里堆砌上千条中文断语 | 断语/引文/卦辞进 `data/*.json` 或 `references/*.md`，代码只留算法 |

## 四、修改引擎的验收门槛

任何改动 `core/` 或学科层推演逻辑的提交，必须：

1. 跑 tune 与 holdout 两个集合并**分别出分**，禁止把 holdout 混进 tune 均分冒充提升。
2. tune 均分无故跌破 95 即视为回归，停止合入。
3. 修复某类错误时，改**通用规则**并说明其古籍出处；禁止为让某个案例过关而写私有别名或 case-specific 分支。
4. 指标口径变了（计分方式、词典、缺失字段处理）必须在 `docs/CHANGELOG.md` 写明，否则分数不可比。
5. **逐格对拍证明「真改进」**：改静态表/提取器前后，用
   `git show HEAD:<file>` 抽旧表与新表逐格比对，报「新增 N 格 / 变空 N 格 / 改值 N 格」——
   **「变空」与「改值」必须逐条解释**（范式 `disciplines/ming/dev_tools/diff_tiaohou_vs_head.py`）。
   只报「新覆盖了几格」会掩盖悄悄回归。
6. **静态表与 data 层不同源时用同步脚本，不手改**：引擎表是字面量、data 是产物，
   手改必漂移。改完跑该学科的同步脚本 `--check`（如
   `disciplines/ming/dev_tools/sync_tiaohou_engine.py --check`），并把它挂进可跑的门。
7. **外部集读数持平不构成「修对了」的证据**：若本轮修的格在外集里没有对应案例，
   读数本就不该动。须明确写出「读数不动属预期」，不得拿持平当成果。
   反之读数变好时，须先排除「改数据/改 expected 凑分」（见上「数据缺陷 vs 引擎缺陷」）。
8. **新挂的门必须做负例自证**：往文档/数据里塞一个**明知不存在**的目标
   （文件名用单下划线，如 `docs/` + `_no_such_probe` + `.md` 拼出的那一个），
   确认门真的判红（EXIT≠0）并报出明细，再撤掉。
   **全绿的新门先怀疑、再证明**——2026-10-06 实踩：死链门挂完是「全绿」的，
   实为豁免逻辑把负例一起吞了（`Path.glob()` 返回 generator、真值恒 `True`）。
   同理，任何「0 结果」都要先确认不是路径解析错了（扫了 0 份文件 ≠ 仓库没文档）。
   文档里**举例用的假路径一律用 `__` 双下划线前缀**（约定见
   `tools/check_doc_deadlinks.py` 的 `FAKE_PATH`），死链门只豁免这类——
   单下划线仍是真死链，照样判红。

## 五、一卦一事

同一问题不重复占卜（"再三则渎"）。用户在既问之后换实质角度提问（换用神、换层面、假设未来、比较两人、测人心）——
应提议另起一卦，不得在原卦里延伸硬推。超出用神覆盖域的断言（对方家庭背景、未来伴侣身份、心里想什么）属臆测，不讲。

## 六、出报告的两条通道（"给链接即出报告"）

仓库上传 GitHub 后，网页端 AI（只能读公开文本、发 HTTP，不能在本地 clone 跑 Python）
按 `docs/AI-SOP.md` 操作即可拿到 MD+HTML 报告。**两条通道跑同一份引擎、同一条四段契约**，
产出同源；`tools/verify_web_parity.py` 是这条同源性的自动验收。

### 通道 A · 纯前端（零凭证，网页 AI 首选）

- 站点源在 `web/`，由 `tools/build_web.py` 把仓库镜像成静态站点
  （`engine/<仓库相对路径>`），`.github/workflows/pages.yml` 发布到 GitHub Pages。
- 页面在浏览器内用 **Pyodide** 跑 `chart→analyze→render`：**零凭证、零后端、
  不上传任何输入**。深链协议 `?d=<学科>&q=…&dt=…&auto=1` 让 AI 只需拼一条 URL。
- Pyodide 没有 `subprocess`，故浏览器侧执行器是 `web/engine_runtime.py`（同进程
  `runpy`）；**请求→命令行参数的映射只有一份**，在内核 `yishu_core.report.request`，
  三个执行器（本机/CI 子进程、浏览器同进程、将来任何宿主）共用，禁止各写一份。
- 浏览器是单一解释器，而八科的 `scripts/` **目录同名**（每科都有 `chart.py`）。
  跑某科前必须把别科模块清出 `sys.modules` 并把本科 `scripts/` 提到 `sys.path` 最前
  （`engine_runtime._isolate`）——否则同名遮蔽会让某一科拿到别科的盘面。
- 本地预览：`python tools/serve_web.py`（以仓库为站点根，改完刷新即生效）。

### 通道 B · 云端 Actions（要留档、要回评时用）

- 工作流 `.github/workflows/report.yml`：触发 = `workflow_dispatch` / `issues` /
  `issue_comment`（`/yi` 命令）/ `repository_dispatch`（type `yi-report`）。
  ⚠️ `workflow_dispatch.inputs` **最多 10 个**，超了工作流直接不注册。表单只暴露
  6 个字段（discipline/question/datetime/gender/extra/commit_branch，留 4 个余量）；
  mode/numbers/way/date/activity 等高级字段进 `extra`（JSON 对象字符串，
  `tools/ci_request.py` 解析合并），或走 issue 正文 / `repository_dispatch`。
- runner 上**零第三方依赖**直接跑 `python tools/report.py`（chart→analyze→render→统一 HTML）；
  不得在工作流里引入未声明的依赖或私有服务。
- 回传三通道：① **固定链接** `reports/<学科>/latest.{md,html}` +
  `reports/index.json`（URL 里不含 run id，AI 无需轮询 API）；② 逐次留档
  `reports/<学科>/<name>-<run_id>/`；③ issue/评论触发时回写评论。
  Artifact（**下载需登录**）只作人工补充。
- 触发半场的写操作必须有凭证（Token）或由人点预填 issue 链接。`/yi` 评论只对
  OWNER/MEMBER/COLLABORATOR 生效（`YI_ALLOW_ASSOCIATIONS` 可放开）。
- 报告与回评内容同样受铁律三约束：分数为古籍案例对齐分、非命中率，重大事项提示专业意见。
- `reports` 分支、`site/` 与生成的报告文件都是产物，遵循 gitignore/分支隔离，
  不混入主分支历史。

### 修订 §六 的门槛

改 `web/`、`tools/build_web.py`、`web/engine_runtime.py`、`core/yishu_core/report/request.py`
或任一学科 `scripts/` 的 CLI 契约时，必须跑：
`python tools/check.py --full`（含站点构建+自检、网页/本地同源验收）。

## 七、版本真实性门（Version Truth Gate，2026-10-04e 增）

任何一轮迭代的 OBSERVE 第一步、任何代码/架构/能力评审之前，必须先确认并报告仓库版本状态。
三个状态不得混同：**Remote Truth**（`origin/main`，网上可验证的版本）、
**Local Working Truth**（本地 `HEAD` + 工作区）、**Evaluation Truth**（tests/golden/holdout/external 读数）。

机械执行：`python tools/version_gate.py`（OBSERVE 第一步跑，输出块原样进轮报）。

```
LOCAL_HEAD:
REMOTE_HEAD:
WORKTREE:
LOCAL_AHEAD:
REMOTE_AHEAD:
SYNC_STATUS:
```

1. 未确认 HEAD 前，不得声称「当前仓库最新状态」。
2. `SYNC_STATUS: UNSYNCED` 时可以继续工作，但必须明说「当前工作尚未与远端 main 同步」；
   本地提交在推送前不是远端可验证事实，不得描述成远端最新状态。
3. 有未提交修改（WORKTREE dirty）时，工作区行为不得描述成已提交事实。
4. 若本轮任务依赖上一轮 commit，必须确认该 commit 真实存在于当前 HEAD 历史中。
5. 远端不可访问时必须明确写出「无法验证远端」（`REMOTE_UNVERIFIED`），不得用本地
   追踪引用冒充实测、不得自行推断。
6. 任何评审必须注明依据：remote main / local HEAD / working tree / 用户提供的 Agent 报告。
   **Agent 自述是二手事实**；除非代码/commit 已实际验证，报告中结论不得当作仓库事实。

版本真实性优先级：实际 git 状态 > 实际代码/测试 > 当前数据 > 当前文档 > Agent 自述 > 历史计划。
