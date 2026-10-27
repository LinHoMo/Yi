# dsh-plugin CHANGELOG

> 本卷登记 DSH 插件（`dsh-yi-divination`）自身的批次；批次号沿用全仓流水（接两科
> CHANGELOG）。插件是两科的**打包层**：引擎与知识库都是构建产物（不入库），两科缺陷
> 修复的判据与实跑记录仍以两科 `docs/CHANGELOG.md` 为准；本卷只记插件半的事
> （架构、构建、安装、验证、发现）。
>
> **semver 映射（275 批起，规则见 AGENTS.md §二 dsh-plugin 契约）**：功能批 minor+1、
> 修复/文档批 patch+1，破坏性变更跨 1.0.0 并单独说明；**批次号是唯一真源**。
> 回溯补记：269→0.1.0（建成）、270→0.2.0（yi_kb）、271→0.2.1（清账文档）、
> 272→0.3.0（2-gram+同义词）、273→0.4.0（baziValue 结构化岁运）、274→0.5.0
> （yi_report）、275→0.5.1（构建与治理，无运行时改动）、276→0.6.0（报告美学
> 统一 + assets 打包修复）、277→**1.0.0**（API 冻结 + CI 补盲）、278→1.0.0
> （发布工件批：Release v1.0.0 + 远端恢复，无代码变更）、279→**1.0.1**（CI CRLF
> 兼容修复 + 文档收尾）、280→**1.0.2**（随包引擎同步六爻 280 批月破救法条件化，
> 无插件自身代码改动）、281→**1.0.3**（随包引擎同步六爻 281 批占差事词典+WS003
> 校勘）。

## 2026-10-27 第三百零五批（dsh-plugin）：共享打包层收敛（1.0.24，仅构建与产物面变动）

- **本批没有运行时改动**：四工具契约、技能正文、判据知识库内容全部不变，
  变的是「这些东西从哪儿来」。
- `dsh-plugin/src/{engine,python,tools,kb,report}.mjs` 与 `kb-synonyms.json`
  **不再是本包的源码**，改为由 `plugins/scripts/build.mjs` 从 `plugins/mcp/` 分发
  （真源唯一）。手工改它们会被共享自检 [1] 段（逐字节同源门）判红；
  `src/index.mjs`（DSH 宿主入口）仍是源码并显式入库。
- `SKILL.md` 真源迁到 `plugins/SKILL.md`，包根的 `SKILL.md` 改为构建产物。
- 删除 `scripts/build-engine.mjs` 与 `scripts/build-skills.mjs`；
  `package.json` 的 `build` 改为 `node ../plugins/scripts/build.mjs`。
- `python.mjs` 合成全宿主一份：`DSH_PYTHON` → `YI_PYTHON` → DSH 桌面自带运行时
  → PATH `python`/`python3` → `py`。
- `scripts/selftest.mjs` 里两条「请跑 node scripts/build-*.mjs」的提示文案改为新命令，
  **判据本身未动**。
- 实跑：`npm --prefix dsh-plugin run selftest` **13 段全绿 rc=0**（含 yi_report 与负例）；
  `node plugins/scripts/selftest.mjs` 全绿。
- 未重跑 `verify-in-dsh`（需 DSH 宿主）。

## 2026-10-26 第三百零三批（dsh-plugin）：DSH STORE 上架契约修复（1.0.23）

- 修复 DSH STORE fixed-Commit 自动检查（AI-Scarlett/DSH-Store#1581）的 **Catalog blocked** 项：
  - manifest 新增 `repository`（指向 canonical GitHub 仓库 `LinHoMo/Yi`，`directory: dsh-plugin`），
    消除「manifest repository does not match the canonical GitHub repository」。
  - 仓库根新增 `LICENSE`（MIT，与 `dsh-plugin/LICENSE`、manifest `license: "MIT"` 三处一致），
    消除 GitHub 仓库 license 元数据 `NOASSERTION` 与「固定源许可证证据需人工复核」。
  - manifest `dsh` 块新增 `compatibility`：显式声明 Node `>=22` 与 DSH `>=0.2.1-rc.2` 兼容范围及实测版本，
    消除「DSH 兼容性未显式声明」。
  - manifest `dsh` 块新增 `permissions`（files / commands / credentials 显式声明 + 范围与理由）、
    `externalServices`（零网络）、`failureBounds`（找不到 Python / 超时 / 缺失的失败边界），
    消除「runtime source contains the files/commands/credentials permission signal」与安全复核待办。
  - `dsh-plugin/README.md` 新增「权限与安全（DSH STORE 契约）」一节：依赖、权限声明、外部服务、失败边界、
    一次性 Profile 安装 / 启动 / 卸载证据。
- 声明本身不保证自动批准：本地 spawn Python + 写临时文件属 elevated 能力，DSH STORE 可能仍维持
  user-reviewed / blocked；声明与文档的目的只是把能力与边界讲清，供人工复核。
- 纯契约 / 文档批：**四工具 API 面与引擎零改动**；`npm run check` 全绿（selftest 77 项 + verify-in-dsh 27 项）。
- `package.json` 1.0.22→**1.0.23**（修复 / 文档批，patch+1）。

## 2026-10-26 第三百零二批（dsh-plugin）：随包引擎同步六爻 292–302 批 + 补登记欠账（1.0.19）

- **补登记（§六.2）**：第两百九十二至三百零一批随包版本号已依次升至 1.0.13–1.0.18（六爻 wikisource 用神基准 46 例、direction 基准 26 例、两现排序档 0.5、自占病层、试考/过关/贼/定罪/贸易词典三族、六冲用神旺衰门、行人化退归志层、流年双轨登记、裁决表 15 条），但本 CHANGELOG 未逐批具名——本条补索引，此后恢复逐批登记。
- 本批（六爻第三百零二批）随包：direction 三案双轨登记（裁决表 15→17 条：shijian_tiying_verdict_dual / direction_usegod_dual 新增，tiantim_heri_track 补 WSD009 party）；build-engine 白名单收 data/rules → engine/，check 全绿（selftest 77 项 + verify-in-dsh 27 项）。
- 读数口径（随包六爻 292–302 批累计）：wikisource_holdout strict 65.4→75.1、wikisource_direction 73.4→74.3（297 口径切换后 67.1→74.3）、zengshan 53.4→50.5→53.4（298 门引入 299 回补）、tune 97.9 / holdout 90.2 持平；均为古籍案例对齐分，不代表现实预测命中率。

## 2026-10-25 第两百九十一批（dsh-plugin）：六破检索记录补全随包（1.0.12）

- 六爻 `data/rules/adjudications.json` six_break_evidence 条目补检索记录：
  库内 16 源全查，唯一额外命中《焦氏易传》L43「休王相破」（概念之源，无纳甲
  计价细节）。结论不变：六破计价无逐字书证，保留与缺口登记并存（289 批）。
- check.py 过时归因块清理在 dev_tools 层（不随包），登记见六爻 CHANGELOG
  第两百九十一批。
- 零判据批：读数与金标准零变化；`npm run check` 全绿。
- `package.json` 1.0.11→**1.0.12**。

## 2026-10-25 第两百八十九批（dsh-plugin）：随包裁决表新增六破证据缺口条目（1.0.11）

- 六爻 `data/rules/adjudications.json` 9→10 条：liuyao.six_break_evidence
  （open_conflict）——六破（相破）计价在库内全部书源无逐字书证（增删零提及、
  卜筮正宗仅目录词 L120），A/B 撤除实测净退化（tune −1.9/wiki −1.5）故保留，
  证据缺口如实登记。完整叙事见 `liuyao/docs/CHANGELOG.md` 第两百八十九批。
- 纯登记批：读数与金标准零变化；`npm run check` 全绿。
- `package.json` 1.0.10→**1.0.11**（data/rules 随包内容更新，patch+1）。

## 2026-10-25 第两百八十八批（dsh-plugin）：随包裁决表新增两条分歧登记（1.0.10）

- 六爻 `data/rules/adjudications.json` 7→9 条：liuyao.xiangfa_duan_guiqi
  （WS001 占父何日归，用神旺衰论 vs 野鹤自认弃古法从象，dz L1014）、
  liuyao.bianyao_usegod（WS040 变出之财+日月冲世灵机断 vs 引擎伏藏评估，
  dz L3043）。均为书内明示双断法，引擎立场登记在案，判据零变化。
- 纯登记批：七 split 读数与金标准 digest 零变化；`npm run check` 全绿。
- `package.json` 1.0.9→**1.0.10**（data/rules 随包内容更新，patch+1；四工具
  API 面不变）。

## 2026-10-25 第两百八十七批（dsh-plugin）：随包引擎同步六爻 287 批（1.0.9）

- 六爻引擎侧六冲主散补用神旺衰门：《增删卜易》源L780「必兼用神而言，用神旺虽
  冲不破」——SCATTER 类占题六冲卦散害，用神月令旺相时不计（score 0），失陷
  维持 −2.0。书证细节与门三度拦截注释错误实况见 `liuyao/docs/CHANGELOG.md`
  第两百八十七批。
- 读数（六爻外部集，随包只报数）：七 split 全部持平——读数不动属预期（§四.7
  外部集无对应格）；金标准 digest 零漂移；`npm run check` 全绿（selftest 77+
  verify 27）。
- `package.json` 1.0.8→**1.0.9**（随包判据变更，patch+1；四工具 API 面不变）。

## 2026-10-25 第两百八十六批（dsh-plugin）：随包引擎同步六爻 286 批（1.0.8）

- 六爻引擎侧应期第3法补第四支：忌神动化回头生得源克用+用神静→冲去化出之源
  （书证源L2570「应子日者冲去午火而未土以克亥水」WS035 实案+源L1206 绝其源），
  WS035 yingqi 0→6/11 命中，wikisource_holdout 70.2→70.5，其余 split 持平。
  细节与七例目标收官状态见 `liuyao/docs/CHANGELOG.md` 第两百八十六批。
- 金标准 5 条漂移（yingqi_months 候选集扩展，无翻档），digest 带理由重落；
  `npm run check` 全绿（selftest 77+verify 27）。
- `package.json` 1.0.7→**1.0.8**（随包判据变更，patch+1；四工具 API 面不变）。

## 2026-10-25 第两百八十五批（dsh-plugin）：随包引擎同步六爻 285 批（1.0.7）

- 六爻引擎侧应期第3法补第三支：动忌化退克用+用神静→冲去忌神之支（书证
  源L1174「戌土子孙孙虽动幸化退神，不克官也，辰年冲去戌土」+源L2050/L2058），
  WS004 yingqi 0→3/11 命中，wikisource_holdout 70.1→70.2，其余 split 持平。
  细节见 `liuyao/docs/CHANGELOG.md` 第两百八十五批。
- 金标准仅 2 条漂移（yingqi 候选集扩展，无翻档），digest 带理由重落；
  `npm run check` 全绿（selftest 77+verify 27）。
- `package.json` 1.0.6→**1.0.7**（随包判据变更，patch+1；四工具 API 面不变）。

## 2026-10-25 第两百八十四批（dsh-plugin）：随包引擎同步六爻 284 批（1.0.6）

- 六爻引擎侧忌神合日月按动静分计：动忌被合=合绊不成凶 +0.3（《增删卜易》
  源L1480 逐字「旧注忌神动逢日月相合，则不成凶」+L738 动逢合谓之合绊+L3152
  求财实案），静忌被合=合起扶忌维持 −0.3/−0.25——判据方向修复，WS004 verdict
  凶→平吉，wikisource_holdout 68.6→70.1。细节与书证门负例两处踩坑见
  `liuyao/docs/CHANGELOG.md` 第两百八十四批。
- 金标准 10 条漂移全部为动忌合日月案例 score 微调（无 verdict 翻档、措辞层零
  漂移），digest 带理由重落；`npm run check` 全绿（selftest 77+verify 27）。
- `package.json` 1.0.5→**1.0.6**（随包判据变更，patch+1；四工具 API 面不变）。

## 2026-10-25 第两百八十三批（dsh-plugin）：随包引擎同步六爻 283 批（1.0.5）

- 六爻引擎侧空亡时限分层：久远类占题（功名科举/终身财福，question_class 单点
  判类）用神休囚旬空 0.3→0.55 待出空中途档；书证链 L249/L524/L823/L1415/L1358
  全录见 `liuyao/docs/CHANGELOG.md` 第两百八十三批。
- 读数（六爻外部集，随包只报数）：全部持平——读数不动属预期（§四.7：外部集
  无对应格）；金标准仅 1 条漂移（观|占升遷，功名类生效格），digest 带理由重落。
- `build-engine.mjs` 重收集 `scripts/step3.py` 入 `engine/`；`npm run check`
  全绿（selftest 77 项 + verify-in-dsh 27 项）。
- `package.json` 1.0.4→**1.0.5**（随包判据变更，patch+1；四工具 API 面不变）。

## 2026-10-25 第两百八十二批（dsh-plugin）：随包引擎同步六爻 282 批（1.0.4）

- 六爻引擎侧随官入墓计价旺衰条件化（随鬼入墓章覺子总论 L685「亦是休囚無气始見危，
  若旺而有扶亦有求解」：旺相减免 ×0.3、休囚原价）+ 功名族判类补词
  差／關差／关差／官差。判据细节与「曾试即回」的域限定版归因见
  `liuyao/docs/CHANGELOG.md` 第两百八十二批。
- 读数（六爻外部集，随包只报数）：七 split 全部持平；金标准 87 条漂移
  全部为入墓命中案例计价变化（方向与书证一致），digest 已带理由重落。
- `build-engine.mjs` 重收集 scripts（step5.py）与 data/rules（question_classes/
  verdict_texts）入 `engine/`；`npm run check` 全绿（selftest 77 项 +
  verify-in-dsh 27 项）。
- `package.json` 1.0.3→**1.0.4**（随包判据变更，patch+1；四工具 API 面不变）。

## 2026-10-25 第两百八十一批（dsh-plugin）：随包引擎同步六爻 281 批（1.0.3）

- 六爻引擎侧占差事用神词典（官差／关差／關差／差事→官鬼，书证 zengshan_buyi
  L493-510 实案「丑土官動化進神許丑日必得」）+ WS003 案卷 question 校勘
  （「占本年冬今」→「占本年冬今得關差否」，抽取截断修复）。判据与七例分歧
  归因全录见 `liuyao/docs/CHANGELOG.md` 第两百八十一批。
- 读数（六爻外部集，随包只报数）：wikisource_holdout 66.9→68.6（＋1.7），
  其余六 split 持平；金标准 digest 对拍零漂移。
- `build-engine.mjs` 重收集 `data/rules/question_use_gods.json` 入 `engine/`；
  `npm run check` 全绿（selftest 77 项 + verify-in-dsh 27 项）。
- `package.json` 1.0.2→**1.0.3**（随包判据变更，patch+1；四工具 API 面不变，
  §二 1.0 API 冻结遵守）。
- 排序实验「动而空升档」在六爻侧实测净负（wiki −1.3）已回退，未进本包——
  诚实记录：曾试即回（§四.1），不随包。

## 2026-10-25 第两百八十批（dsh-plugin）：随包引擎同步六爻 280 批（1.0.2）

- 六爻引擎侧月破救法集条件化 + WS035 案卷 verdict 校勘（判据与书证见
  `liuyao/docs/CHANGELOG.md` 第两百八十批）。插件无自身代码改动：`build-engine.mjs`
  重建 `engine/liuyao/`（step3.py、adjudications.json 同步），`npm run check`
  （build→selftest 77 项→verify-in-dsh）全绿。
- `package.json` 1.0.1→**1.0.2**（随包判据变更，patch+1；四工具 API 面不变，
  1.0 冻结条不触发）。
- 口径提醒不变：分数是与古籍案例要点的一致性，不代表现实预测命中率。

## 2026-10-25 第两百七十八批（dsh-plugin）：v1.0.0 发布工件 + 远端恢复（纯运维批）

发布计划 2/3（用户决策：tgz 手动分发，不上 npm 公网）：

- **远端恢复**：`origin/main` 自仓库重建（677878a）起断供，本地积压 **142+ 批未推**。
  本批以 `git tag remote-backup-20261025`（已推远端）保住旧远端历史，然后
  **force-push main**（60b2403→9c39e77），本地主干恢复真源地位。
- **GitHub Release v1.0.0**：https://github.com/LinHoMo/Yi/releases/tag/v1.0.0
  挂 `dsh-yi-divination-1.0.0.tgz`（765,888 B / 0.73MB，163 文件），说明含
  **口径诚实声明**（对齐分≠命中率、现实样本零、六爻外部集主应期 27.3%<随机期望
  31.1% 同屏、案例库不随包）与已知限制。v1.0.0 tag 随后重指到新主干 9c39e77。
- **CI 首跑结果**（push 触发，run 40189324241）：两科 gates（windows）✓ 55s；
  plugin-gates **ubuntu ✓**——`src/python.mjs` 三级解析在 PATH-only 环境下首测通过
  （138 引擎文件逐个与真源一致 + 自检 + DSH 内验证全绿），跨平台疑虑落地排除；
  plugin-gates **windows ✗**——selftest [2] 的 frontmatter 判据硬编码 `'\n'`，
  runner 按 autocrlf 检出 CRLF 后假红。修复归 279 批（判据归一化 + .gitattributes）。
- **网络记实**：git 全局代理 127.0.0.1:7890 当时未运行、直连时通时断；推送与
  tag 用命令级 `git -c http.proxy=` 绕过完成（用户配置未动）；Release 走
  `gh` 的 api/uploads.github.com 通道。此条只记录当时环境事实，不是配置建议。

## 2026-10-25 第两百七十九批（dsh-plugin）：CI CRLF 兼容修复 + 文档收尾（1.0.1）

发布计划 3/3（修复+文档批）：

- **修复**：selftest `[2]` frontmatter 判据读入后 `\r\n→\n` 归一再匹配——判据测的
  是产物，不是检出配置（CI Windows runner autocrlf 检出下假红的根因，278 批实抓）。
  同批新增根 `.gitattributes`（`* text=auto eol=lf` + 二进制白名单）：仓库索引一贯
  LF，把工作树检出行为也钉死，行级判据门从此对检出配置免疫。双保险，缺一不可。
- **文档收尾**：根 README 修 274 批漏更的陈旧（"三个工具"→四个 + 工具表行补
  `yi_report`）、安装节补 GitHub Release tgz 路径与铁律三口径提醒块；插件 README
  安装节补发布版 tgz 路径、新增「已知限制（1.0.0）」节（时区口径：引擎按本地钟表时
  直接排盘、`calendar_policy` 只管换日边界与子时归属不做时区换算——`{"boundary":
  "day","zi_hour":"same-day"}` 实测；报告文件落临时目录只增不清；平台实测边界；
  现实反馈通道 0 条）、口径边界节补六爻外部集 27.3%<31.1% 同屏。
- **禁语全仓核对**：`准确率|断事如神|命中率` 全仓 126 处命中逐一过目——全部为
  否定式声明（"不代表现实命中率"）或引擎内部指标名（自带免责），交付面零违规。
- `package.json` 1.0.0→**1.0.1**（修复批 patch+1；Release 上的 1.0.0 工件不受影响）。
- **验收补记（同日）**：本批修复推送后 CI 复跑（run 40190104854，58s）
  **三 job 全绿**——gates ✓ 56s / plugin-gates windows ✓ 24s / ubuntu ✓ 9s，
  CRLF 假红闭环；windows 侧 `[2]` 在 autocrlf 检出下过门即本批修复的直接证明。

## 2026-10-25 第两百七十七批（dsh-plugin）：1.0.0——API 冻结 + CI 插件门补盲

发布计划 1/3（用户已批：tgz 手动分发，不上 npm 公网；远端恢复在 278 批）：

- **1.0 API 冻结（AGENTS §二 dsh-plugin 契约新增条）**：对外契约冻结为四工具
  `yi_liuyao` / `yi_bazi` / `yi_kb` / `yi_report` 的工具名、参数 schema、输出 value
  结构（含 `output.render` 文本块形状）与技能条目 `yi-divination`。1.0 后新增可选
  参数/字段 = minor+1；改名/删字段/改语义 = 破坏性，跨 1.0.0 单独声明。自检 [1]
  必存在清单是冻结清单的机械面——动清单先动契约条。`package.json` **0.6.0→1.0.0**。
- **CI 插件门补盲（`.github/workflows/ci.yml` 新增 `plugin-gates` job）**：此前 CI
  只跑两科 `check.py`，插件 build/selftest/verify-in-dsh 三门只活在开发者本机。
  新 job 以 matrix 跑 **windows-latest + ubuntu-latest** 双 runner——ubuntu 侧是
  `src/python.mjs` 三级解析（DSH 自带运行时 → `DSH_PYTHON` → PATH）的**首次实测**：
  runner 上前两级必然缺席，只能落 PATH。Python 定 3.12（与 DSH 自带运行时 3.12.14
  同代），Node 22（`engines` 下限）。**首跑结果以 push 后实际运行为准**；红则按
  §六.3 以实跑读数修插件，不跳过不豁免不调 CI 凑绿。
- **本批零运行时改动**：工具、引擎、排版层一字未动——1.0.0 是契约语义上的里程碑，
  不是功能批。
- **本地验证**：`npm run check` 全绿（selftest 77 项 + verify-in-dsh 27 项）。
- **semver**：0.6.0 → **1.0.0**（里程碑；配合 AGENTS 冻结条生效）。

## 2026-10-25 第两百七十六批（dsh-plugin + 六爻）：报告美学统一（宣纸卷面）+ build-engine 补收 assets（真修）

用户需求「报告可视化进行美学优化」（六爻 + 八字两个 HTML 报告统一到同一套视觉语言）：

- **真修（插件侧）**：`scripts/build-engine.mjs` 白名单没收 `assets/`——插件引擎副本
  没有 `report.css`，`render.py` 走 `css=""` 分支，**六爻 HTML 报告从 269 批起一直是
  无样式裸 HTML**（269 批真机验收时只看了「能出报告」，没看长相——漏检项）。
  修复：RUNTIME_INCLUDE 补 `assets`，并允许白名单目录缺席（bazi 无 assets/ 不炸构建）。
  自检 [8] 引擎对拍门天然覆盖新目录（真源↔副本逐文件一致）。
- **八字侧**（`src/report.mjs` 重排，纯排版层）：宣纸底 + 朱砂印「易」+ 文武线卷首；
  四柱竖排干支卡（日柱朱色顶边 + 日主徽章）；旺衰/格局/喜忌结论带（喜用玉色・忌神朱色）；
  大运卡「行运中」高亮接上（旧版 `.cur` 类写了没接线）；流年表徽章化 + 斜杠事件行；
  kv 展示层去重（引擎字段自带「空亡/得药/天克地冲」前缀时不再「空亡 空亡 午、未」）。
- **六爻侧**（两科文件，详见六爻 CHANGELOG 276 批）：`liuyao/assets/report.css` 全量重排
  （选择器一条不丢；顺手修了旧文件 335-344 行降级规则**丢失 @media 包裹**的历史 bug）；
  `render.py` 页头 emoji → 印章版式；`visualization.py` SVG 高度 500→240（去 ~320px 死白）
  + 墨/朱砂配色。
- **验证**：`python liuyao/dev_tools/check.py --fast` rc=0（零判据改动，分数未动）；
  `npm run check` 全绿（selftest 77 项 + verify-in-dsh 27 项）；前后截图
  `scratch/{bazi,liuyao}-{before,after*}.png` 人工验收。
- **体积复测**：npm pack（cd 进插件目录）= **163 文件 / 2.6 MB / tgz 0.77 MB**
  （+1 文件 = `engine/liuyao/assets/report.css`）。
- **semver**：0.5.1 → **0.6.0**（功能批）。

## 2026-10-25 第两百七十五批（dsh-plugin）：INDEX 体积自动再生 + 月巡挂钩 + semver 纪律（0.5.1）

迭代地图第 5、6、7 项（收尾批）：

- **INDEX 体积自动再生**（`scripts/build-skills.mjs`）：知识库索引里的 KB 数字从手抄
  改为**构建时 `stat` 实测**——首跑即抓到手写漂移（najia_rules 手写 47KB 实测 46KB、
  classical_synthesis 手写 52KB 实测 51KB，「单篇最大」行同步自动算出）。知识库篇目
  描述集中进 `KB_DOC` 表，**双向校验**：两科新加 references 文件未登记描述 → 构建红；
  登记了已不随包的文件 → 构建红（负例 `_fake_probe.md` 实测 EXIT=1 后撤除）。
  行序改由 `KB_DOC` 键序定，不再随 `readdir` 次序漂。
- **月巡挂钩**（AGENTS.md §二 dsh-plugin 契约新增一条）：对两科 `references/`、
  `core/`、`scripts/` 的例行巡查末尾必须加跑 `npm --prefix dsh-plugin run check`——
  两科改动会静默使 `engine/`、`skills/` 构建产物过期，此门是提交前抓漂移的唯一机制；
  GOVERNANCE 月巡名册如建立须登记。本批即按该口径从仓库根用 `--prefix` 实跑验证。
- **semver 纪律**：`package.json` 0.1.0→**0.5.1**，映射表回溯补记在卷首（见上）；
  此后逐批补记。npm 包版本只是粗坐标，批次号仍是唯一真源。
- 验证：`npm --prefix dsh-plugin run check` 全绿（selftest 77 项 / verify-in-dsh 27 项）；
  纯构建与治理批，无运行时改动（src/ 零 diff，semver 故只走 patch）。

## 2026-10-25 第两百七十四批（dsh-plugin）：`yi_report` 完整排盘报告——引擎 render 段 + 八字可视化排版层

迭代地图第 4 项（缺口：报告只能靠模型手写 Markdown，排版不受控、可视化为零）：

- **引擎报告段接入**（`src/engine.mjs`）：`DISCIPLINES` 各科加 `reportScript`，新增
  `report(discipline, analyzeJson, {fmt})`——复用 cast 同一条 `runStage` 通道，六爻追加
  `-f html|md` 走 `liuyao/scripts/render.py`（单文件 HTML，引擎已验证报告器）、两科 md
  走各自 `render.py`。**不引入新断语，只呈现引擎已产出的判读**。
- **八字 HTML 排版层**（`src/report.mjs` 新建）：四柱卡（干支+纳音+十神）、旺衰/格局/
  喜忌徽章、大运时间条（含交叉事件）、流年结构化事件表、流月格——文字全部来自 273 批
  baziValue 的引擎结构化字段（`conclusion` 直取），页脚自带口径说明（古籍案例对齐分
  ≠现实命中率，§一.3）。生成文件落 `%TEMP%/yi-reports/yi-<科>-<时间戳>.<fmt>`。
- **新工具 `yi_report`**（`src/tools.mjs` `createReportTool`/`runReport`）：参数
  `discipline`（必填，非两科即抛错）/`format`/排盘同款参数；返回
  `{discipline, format, path, bytes, generator, preview}`（预览=去标签 clip 200）。
  注册顺序：yi_liuyao → yi_bazi → yi_kb → yi_report；系统提示词段「三个工具」→「四个工具」。
- **流程约束写进文档**：SKILL.md/README 均注明「先判读、后报告」——报告是判读的呈现，
  不替代判读；模型须把返回的文件路径转告用户。
- **测试**：selftest 新增 [13] 段（六爻 html 引擎渲染 ≈9KB 且含卦象、八字 html ≈10KB
  且含四柱/干支/口径页脚、八字 md、三文件 stat 落盘、负例 `discipline=tarot` 报错）；
  verify-in-dsh [1] 增 `registry.has('yi_report')`。check 全绿：selftest **77 项**、
  verify-in-dsh 26 项。
- **体积复测**：npm pack（cd 进插件目录）= **162 文件 / 2.46 MB / tgz 0.72 MB**
  （插件源码 6→7 文件、0.04→0.06 MB），README 两处体积表按实数更新。
- 踩坑两笔：①生成目录漏 `mkdir` 报 ENOENT（writeReportFile 已补 recursive mkdir）；
  ②一次 edit 误伤 createKbTool 函数头，check 前自查发现补回——「先 node --check 再
  上门」的既有纪律再次兜底。

## 2026-10-25 第两百六十九批（dsh-plugin）：**Yi 术数 DSH 插件建成入库——agent 预设 + skills 加载 + 知识库 + 内置引擎的分层架构**

**是什么**：把两科包装成 `dsh plugin --profile <p> add "link:<repo>/dsh-plugin"` 一键
安装的 DSH 插件，装了即用（引擎随包、DSH 桌面 Python 运行时自动发现），会话里直接调
工具，无需 clone 本仓库、无需手敲 `python` 命令。

| 层 | 机制 | 落点 |
|---|---|---|
| 工具 | `ctx.tools.register()` | `yi_liuyao`（coin/time/number/manual 四种起卦）／`yi_bazi`（datetime+gender） |
| 技能+知识库 | `ctx.skills.registerProvider()` + 预设侧 `bundledSkillDir` | `skills/yi-divination/SKILL.md` + `references/{liuyao,bazi}/` 9 篇判据 + INDEX.md 路由表 |
| Agent 预设 | `@deepseek-ai/dsh-agent-preset` | `presets/yi-divination.yml`（工具+技能+系统提示词段一体，`- insert:` 方言） |
| 系统提示词段 | `ctx.systemPrompt.section()`（order 900） | 铁律一（机械运算归代码）／一卦一事／口径诚实的会话内重申 |

**构建与产物纪律**：`engine/`（137 文件白名单打包）、`skills/`（9 篇组装 + INDEX.md
再生）均为构建产物，**不入库**（根 `.gitignore` 本批起排除 `dsh-plugin/engine/`、
`dsh-plugin/skills/`、`node_modules/` 与锁文件）——避免 AGENTS.md §二 警告过的
「同表多存、取值不一致」事故土壤。改两科后必须 `npm --prefix dsh-plugin run check`
（build → selftest → verify-in-dsh）再提交，过期副本由逐文件一致性门判红。

**验证（全绿）**：`selftest` 12 段 48 项，含 8 处负例自证（patch 方言缺 `insert` 判红、
引擎指纹不一致判红、案例库混入知识库判红、`__pycache__` 污染判红等）；`verify-in-dsh`
在 DSH 0.2.1-rc.2 真机验证工具注册／技能字段／执行渲染链路。`npm pack` 实测解包
2.43 MB、tgz 0.71 MB；`data/cases/`（38 MB）、`data/sources/`（9.5 MB）、
`references/case_library.md`（165 KB，铁律二）不在包内。

**真机踩坑 9 条**（invocation 必须是 OBJECT、rank 必须有限、systemPrompt 段必须带
order、fallback 必须给 `output.render`、`PYTHONDONTWRITEBYTECODE` 等）逐条记在
`dsh-plugin/README.md`，不在此重复。

**同批对齐**：根 `README.md` 增加「作为 DSH 插件安装」一节；`AGENTS.md` §二目录树
收录 `dsh-plugin/` 并新增「dsh-plugin 契约」小节（同步口径：改两科 → npm run check →
提交）；插件批次自此登记本卷。

**安装态**：desktop profile 已装（link:）且预设已追加（`scripts/install-preset.mjs`
幂等）；预设注册表 `default: standard` 未动，是否把 `yi-divination` 设为默认预设待
用户决定（改一行即可）。

## 2026-10-25 第两百七十批（dsh-plugin）：**新增 `yi_kb` 判据知识库检索工具——先定位再读节段，省上下文**

**动机**：知识库 9 篇单篇最大 52KB，模型凭 INDEX.md 路由表整篇盲读，读错一篇就白占
一大块上下文。`yi_kb` 让模型先关键词定位（返回 文件:行 + 节标题 + 摘录），再按行读
具体节段。

**实现**（`src/kb.mjs`，纯 Node、确定性、零 LLM 零 Python）：
- 只扫 `skills/yi-divination/references/` 下 `.md`；`case_library.md` 在**扫描层**按
  文件名硬排除——与打包层（`build-skills.mjs` NEVER_SHIP）、自检 [1.5] 包内断言构成
  铁律二的三道闸。
- 检索：按 1–3 级标题切节；词频计分（标题命中 ×4、文件名命中 ×3、正文词频封顶 12、
  覆盖词数 ×6）；每文件最多 2 条防单篇刷屏；`limit` 夹在 1..10（默认 5）。
- 无关词返回空清单不编造；缺 `query` 抛错（对齐 [7] 参数语义校验口径）。

**注册与文档**：`src/index.mjs` 恒注册（纯 Node，与 `enableBazi` 无关）；系统提示词段
（「两个工具」→「三个工具」）、SKILL.md（单一真源）、INDEX.md 模板、README、预设注释
同步提法。

**验证（全绿）**：`selftest` 新增 [12] 十断言（含 4 项负例性质）——扫描层排除用「探针文件
确实存在但不在可检索清单」证明判据在起作用（不是目录为空）；`verify-in-dsh` 新增
yi_kb 注册／执行／render 三查。

## 2026-10-25 第两百七十一批（dsh-plugin）：遗留项清账 + 文档实测对齐

纯文档/配置批：未动引擎、检索逻辑与构建脚本；`engine/`、`skills/` 产物与 270 批一致。

- **default 预设维持 `standard`（落纸决策，非改数）**：Yi 预设刻意最小化子插件列表
  （术数本体 + 技能通道，不塞 bash/web/search），设为默认会改变**所有新会话**的可用
  工具面；术数会话按需在新建时选择。仓内 preset 注释保留一行指引，要翻默认改一行即可。
- **desktop profile 补丁注释同步**：工具清单补 `yi_kb`（与仓内 `presets/yi-divination.yml`
  对齐）。该文件在仓库外（用户自有 profile），不入库；`install-preset.mjs` 不含该注释
  文本，无第二修复点。
- **计数对齐**（消灭「文档说的和做的不一致」）：`npm pack --dry-run --json` 复测 =
  **160 文件 / 2.44 MB / tgz 0.72 MB**（270 加 `kb.mjs`：插件源码 4→5 文件、0.03→0.04 MB；
  引擎 2.21 / 知识库 0.17 不变），两处 README 体积表按实数更新；selftest 复跑全绿
  **58 项 / 0 失败**（269 记 48 项 + [12] 段十项），README「12 段」→「13 段」、
  「48 项」→「58 项」，负例数改定性表述；270 条目「六断言 + 2 负例」系实现中途口径，
  已就地更正为终态十断言；根 README 工具清单两处补 `yi_kb`。
- 复现注记：`npm pack` 对 `--prefix` 不生效（按 CWD 找 package.json），须
  `cd dsh-plugin && npm pack --dry-run --json`（README 复现命令本就如此写）。

## 2026-10-25 第两百七十二批（dsh-plugin）：yi_kb 召回质量——中文 2-gram 兜底 + 同义词展开

迭代地图第 1、2 项（缺口：无空格长 query 整串匹配漏召；术语别称检索不到）：

- **中文 2-gram 兜底分词**（`src/kb.mjs` 新增 `cjkBigrams`）：query 里 ≥3 字的连续汉字串
  自动切出相邻二字窗（「世应怎么安」→ 世应/应怎/怎么/么安），减权重计分（标题 ×1、
  正文封顶 4、不计覆盖）——整串匹配不到时仍能召回，且不压过精确命中；2 字词不切
  （整串即词），不跨中英文边界。返回值新增 `expanded.bigrams` 供复核。
- **同义词展开**（新增 `src/kb-synonyms.json` + `expandWithSynonyms`）：组内任一词命中
  即整组全权重展开；返回值新增 `expanded.synonyms`。只收「确定同义」，不收近义
  （忌神/仇神、旺相/休囚是不同概念，禁止入组）；当前 KB 无「喜用神/调候」覆盖，
  相关组暂不收录（防假扩充）。词表放 `src/` 随 files 白名单进包，不改打包配置。
- **真 Bug 修于自检**：首版把 `if (!covered) continue` 留在 bigram 计分之后——只有二字窗
  命中的节被整节丢弃（「世应怎么安」零命中）；修正为 `if (!covered && !bigramHit) continue`。
- **测试**：selftest [12] 10→15 断言（2-gram 召回／含 najia_rules／expanded.bigrams 可复核；
  同义词 用爻→用神 召回／摘录含「用神」可复核）；无关词探针换「汽车维修zzz量子塌缩」——
  其每个 ≥3 字汉字串的二字窗已验证零库内命中（旧探针「不存在的词」二字窗「存在」在库中
  大量出现，会被兜底误召回）。selftest 全绿 **63 项 / 0 失败**；verify-in-dsh 全绿。
- **文档**：SKILL.md（单一真源）、README、工具 description／参数说明同步
  「2-gram 兜底 + 同义词展开」。
- pack 复测：**161 文件**（+kb-synonyms.json）/ 2.44 MB / tgz 0.72 MB（体积表按实数更新）。

## 2026-10-25 第两百七十三批（dsh-plugin）：yi_bazi 结构化岁运字段

迭代地图第 3 项（缺口：`baziValue` 只给四柱+结论梗概，模型讲大运流年只能复述 narrative）：

- **`baziValue` 重构**（`src/tools.mjs`）：新增三块结构化字段，全部引擎产出、node 只整形——
  - `conclusion` 补全：旺衰/分数/格局/成败/特格外加 调候、空亡与病药（从 verdicts 平铺）、
    胎元、通关、天克地冲、喜忌（`useful_gods`/`taboo_gods` 此前取自 `c.useful_gods` 本就有值，
    本批补 `strength_score`/`pattern_cheng_bai`/`special_pattern` 等）；
  - `dayun`：8 步基础表（干支/起讫岁/十神），并把大运明动按 `dayun_index` 并回对应步；
  - `liunian`：12 年逐年行（干支/十神），并入两类事件——明动（流年×命局）与
    岁运交叉（流年×所临大运，含 `dayun` 字段标明所临何运）；
  - `liuyue`：12 月干支十神。
- **事件 text 一律 clip（140/80 字）**：`basis` 逐字书证是对账层，不进结构化字段
  （analyze JSON 全量保留，铁律二的「引文可指回」不受影响）。
- **自检**：[6] 增 5 断言（dayun 8 步／liunian 12 年且首年 1990 庚午／liuyue 12 月／
  conclusion 旺衰格局真值／verdicts 平铺空亡）。实测发现 `conclusion.liunian` 是
  **12 年**（1990–2001）而非 8 年——首版断言按 8 年写，实跑抓出后改正。
  selftest 全绿 **68 项 / 0 失败**；verify-in-dsh 全绿。
- **文档**：SKILL.md（yi_bazi 节加「结构化岁运字段」说明：讲大运流年直接引字段，
  不要凭 narrative 复述）、README 同步。