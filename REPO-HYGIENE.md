# 易（Yi）· 仓库整理规范

> **本文件是什么**：一次性收口「边界／整治／内容／垃圾」的**单一入口**。
> 它不新增铁律、不改口径、不产生待办；与 `AGENTS.md`／`CONTRACT.md` 冲突时以那两份为准。
> 规范里每一条硬判据都由 `devkit/root/check_repo_hygiene.py` 常驻复验，不是一纸空文。
>
> **为什么不写在 `AGENTS.md`**：那份是给改代码的贡献者看的铁律与依赖契约，
> 本文件是给「整理仓库的人」看的目录/生成物/清理/登记速查，读者不同、更新节奏不同。

## 一、六类边界（一页速查）

| # | 边界 | 权威出处 | 一句话判据 | 越界后果 |
|---|---|---|---|---|
| 1 | 能力边界 | `CAPABILITY.md` | T1 排盘已验证／T2 古籍对齐分已量化含上限／**T3 现实预测不可测、不声称** | 把对齐分说成命中率即违反 §一.3 |
| 2 | 铁律边界 | `AGENTS.md` §一 | 机械运算归代码／案例库与解读物理隔离／口径诚实 | 三条皆不可动摇 |
| 3 | 层界 | `CONTRACT.md` | `chart → analyze → narrate → render` 各段职责、禁边、输出键白名单 | 改层界须同批改 CONTRACT + JSON + CHANGELOG |
| 4 | 案例库边界 | `AGENTS.md` §一.2 | `data/cases/` 与 `case_library.md` 只允许测试运行器／用户要求的事后校验／用户主动问类似案例三种访问 | 解读交付前不得打开、提及、类比；随包 `NEVER_SHIP` 三道闸 |
| 5 | 零耦合边界 | `AGENTS.md` §二 | 两科之间无 import、无跨科写；跨科只读须注明且产物落系统临时目录 | 不存在也不得复活合参层 |
| 6 | 对外／发布边界 | `README.md`「给网页端 AI 读者」、`outreach/`、`dsh-plugin/package.json` | 对外文本必须自包含静态可读、带口径脚注、给 raw 直链；1.0 API 冻结面（四工具名／schema／输出 value）不改 | 改冻结面须跨 1.0.0 并声明旧读数不可比 |

**文档状态边界**（`DOCS.md` 的四种，不许混写）：活文档＝当前口径出处；生成物＝脚本重生成、不要手改；
归档留证＝结论已入 CHANGELOG、只为可追溯；历史索引＝只有批号与一句话。

## 二、目录契约：真源 / 产物 / 不入库

| 路径 | 角色 | 真源 | 再生方式 | 入库 |
|---|---|---|---|---|
| `kernel/`、`devkit/shared/` | **内核与门禁真源** | 自身 | 改这里，再 `--write` 分发 | ✅ |
| 两科 `core/yishu_core/`、`dev_tools/` 共享件 | **生成产物** | `kernel/`、`devkit/shared/` | `python kernel/sync_kernel.py --write`／`python devkit/sync_devkit.py --write` | ✅（产物也入库，为的是单目录可拷走；手改被 [35]/[37] 判红） |
| 两科 `scripts/`、`engine/`、`rules/`、`data/`、`references/` | 学科真源 | 自身 | — | ✅ |
| `plugins/mcp/`、`plugins/scripts/`、`plugins/SKILL.md` | 共享运行时真源 | 自身 | — | ✅ |
| `plugins/engine/`、`plugins/skills/` | 构建产物 | 两科 + `plugins/mcp/` | `node plugins/scripts/build.mjs` | ❌ |
| `dsh-plugin/engine/`、`dsh-plugin/skills/`、包根技能正文（构建生成）、`dsh-plugin/src/*.mjs`（除 `dsh-plugin/src/index.mjs`） | 分发产物 | 同上 | 同上（含 `prepack` 自动跑） | ❌ |
| `llms.txt`、`KNOWLEDGE.md`、`kb/INDEX.md`、`examples/*.md` | **对外层产物（入库）** | `outreach/KNOWLEDGE-BODY.md` + 登记表 + 两科引擎 | `python outreach/build_outreach.py --write` | ✅（必须提交，否则外部读不到） |
| `site/` | Pages 产物 | 同上 | 同上 + `.github/workflows/pages.yml` 现场部署 | ❌ |
| `**/data/cache/`、`**/data/collation/`、`**/scratch/`、`**/outputs/`、`**/logs/` | 评测/比对/临时产物 | 脚本现场生成 | 清掉即由对应脚本重生 | ❌ |

> **唯一例外**：`dsh-plugin/src/index.mjs` 是宿主专属源码，虽在 `src/` 下仍入库
> （`.gitignore` 显式 negated）。`dsh-plugin/presets/` 同理。
>
> **写文档的纪律**：凡「不入库产物」一律写成目录名或文字描述，**不要写成带扩展名的
> 文件路径**——本地 build 过文件在盘、活引用门绿，fresh checkout 上文件不存在就判死链
> （550 批首次 fresh 复验实证）。这也正是 §六 第 6 步必须做干净树复验的原因。

## 三、一条命令再生全部产物

```bash
git clone https://github.com/LinHoMo/Yi && cd Yi
node plugins/scripts/build.mjs            # engine/ + skills/ + src 8 个共享运行时
node plugins/scripts/selftest.mjs         # 共享层自检
python outreach/build_outreach.py --write # 6 份入库对外产物 + site/（含离线索引镜像）
python outreach/build_outreach.py --check # 逐字节同源复验
npm --prefix dsh-plugin run check        # 宿主侧全检
python liuyao/dev_tools/check.py && python bazi/dev_tools/check.py
```

**clone 后不 build 也能直接跑两科 Python 脚本**（无第三方运行依赖），
但**装 DSH 插件／打 tgz 必须先 build**——这是历史最大断链，README 已把 build 写成第 0 步。

## 四、垃圾清单与清理边界

### 可安全清理（本地磁盘、gitignored、可重建）

```bash
# 评测/比对/临时产物：清掉即由脚本现场重生（AGENTS.md 明文口径）
rm -rf liuyao/data/cache bazi/data/cache bazi/data/collation
rm -rf liuyao/scratch bazi/scratch liuyao/outputs liuyao/logs
find . -type d -name __pycache__ -prune -exec rm -rf {} +
# 构建产物与 Pages 产物（随后用第三节命令重建）
rm -rf plugins/engine plugins/skills dsh-plugin/engine dsh-plugin/skills site
```

其它可清：npm 锁文件、`*.log` 日志、`*.tmp` 临时文件、tgz 打包产物，
以及 540 批的基线覆盖文件（探针会自恢复）。
这些名字**故意不写成可解析的路径引用**——它们是清理目标、可能不在盘，
写成路径会被 `check_root_docs.py` 判成死链（550 批首跑实证）。

### 禁止清理 / 需人工决定（本规范不自动删）

- ⛔ `.workbuddy/`（项目数据，非缓存）、`data/cases/`、`data/sources/*.dz.txt`、
  `*.provenance.json`、`liuyao/references/case_library.md`（案例库虽不随包，但在库且受门守护）。
- ⚠️ **历史 worktree 与备份分支**：删除不可逆，**由人决定**后再执行
  `git worktree remove --force <path>` / `git branch -D <name>`。
  判定「可安全删」的三条（552 批实测 8 个历史工作树全满足，过程见 `WORKTREE-AUDIT.md`）：
  ① `git rev-list --count main..<rev>` 为 0；② `git status --porcelain` 为空；
  ③ 快照内容能在主线点名归宿（被迁移、被改写都算，不必逐字相同）。
  三条不齐即按「可能含未合并工作」保留，不猜、不批量删。
- ⚠️ **CHANGELOG 里的登记时点事实**：历史条目按登记时点保留、不改写；
  发现过期用「文首勘误块 / 现状表」更正，禁止静默改旧读数（§六.2）。

## 五、内容纪律（禁止清单）

1. **不钉会变的数**：篇目数、包体文件数/体积、版本号、对齐分读数，一律回指真源或标「以实跑为准」。
   517 批清过 DOCS.md 的四节硬编码份数，539 批清过技能正文手钉的 KB 数，549 批清过 README 的包体快照。
2. **不硬编码本机绝对路径**：549 批实证 33 个 `.py` 被批量注入本机路径，导致 fresh checkout 全红；
   一律按 `__file__` 相对定位或走 `kernel_path`／`engine/_bootstrap`。
3. **不手写代码产出的结论**：`examples/` 两份报告由四段流水线实跑生成；
   `KNOWLEDGE.md`、`kb/INDEX.md`、`llms.txt` 由构建器拼装。改内容改真源，再 `--write`。
4. **不手改生成物**：两科 `core/`、`dev_tools/` 共享件、随包 `INDEX.md`、对外产物、Pages 产物。
5. **口径脚注不可省**：一切对外文本带「古籍案例对齐分 ≠ 现实命中率／非预言／重大决策以专业意见为准」；
   禁句扫描保留**否定语境豁免**（「不是预测准确率」是合规声明，不是违规）。
6. **新增文档同批登记 `DOCS.md`**：索引门按 `git ls-files '*.md'` 逐份查；
   两科主 CHANGELOG 维持最近 15 批窗口，退出窗口的批号＋日期只准搬进历史索引、不准删。
7. **批次号是版本真源**，semver 只是粗粒度坐标；功能批 minor+1、修复/文档批 patch+1。
   Release 的 tag 与 `dsh-plugin/package.json` 版本由 `release.yml` 对账，不一致即判红。

## 六、一次性整理流程（照做即可）

1. 先跑 `python devkit/root/check_repo_hygiene.py` 看当前四类问题清单。
2. 修活文档假事实（状态、版本、篇目数、死链）——只改活文档，历史条目加勘误不改正文。
3. 按第四节清可重建垃圾，再按第三节一条命令重建，避免「清完不可用」。
4. 跑 `python outreach/build_outreach.py --check` 确认对外产物同源。
5. 跑两科 `check.py`、根级 5 门、`kernel`／`devkit` sync、账台、pytest、build+selftest、dsh check。
6. 用 `git worktree add --detach <临时目录> HEAD` 做一次 **fresh checkout 复验**——
   本地因 gitignored 文件在盘而全绿、CI 全红，本仓已踩过三次，这一步不能省。
7. 同批登记 `DOCS.md`、写 CHANGELOG（含批号与日期）、提交信息带「第N批」。
8. 推送后确认 `quality-gates` / `deploy-knowledge-pages` / `release-plugin` 三个 workflow 全绿。

## 七、门在哪

| 门 | 守什么 | 入口 |
|---|---|---|
| `check_repo_hygiene.py` | 生成物零入库／零硬编码绝对路径／活文档不钉过期数 | `python devkit/root/check_repo_hygiene.py [--selftest]` |
| `check_docs_index.py` | 每份 md 登记可达 + CHANGELOG 15 批窗口 | 同上（root-gates 挂线） |
| `check_root_docs.py` | 根级文档活引用零死链 | 同上 |
| `check_batch_num.py` | CHANGELOG 批号必须在提交信息里 | 同上 |
| `sync_devkit.py --check` / `sync_kernel.py --check` | 真源↔产物逐字节同源 | 仓库根 |
| `build_outreach.py --check` / `--registry` / `--selftest` | 对外产物同源 + 双登记表四向对账 + 三条铁律 | `outreach/` |
| `plugins/scripts/selftest.mjs` [1]/[1.5]/[7] | 共享运行时同源、案例库不随包、禁语与口径 | `plugins/` |
