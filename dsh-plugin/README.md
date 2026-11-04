# dsh-yi-divination

> DeepSeek Harness（DSH）插件：**六爻纳甲** 与 **八字四柱** 的确定性排盘与解读。
> 装了即用：自带 Python 引擎与运行数据，不需 clone 仓库、不需手配路径。

## 安装

发布版：从 GitHub Release 下载 tgz 后安装——<https://github.com/LinHoMo/Yi/releases/tag/v1.0.0>

```sh
dsh plugin --profile <profile> install ./dsh-yi-divination-1.0.0.tgz   # 发布版
dsh plugin --profile <profile> add "link:<本目录绝对路径>"                # 开发版
node scripts/install-preset.mjs <profile>                                # 可选，幂等
```

`<profile>` 是 `$DSH_HOME/profiles/` 下的目录名（桌面版 `desktop`）。卸载：
`dsh plugin --profile <profile> remove dsh-yi-divination`。

## 四个工具

| 工具 | 作用 |
|---|---|
| `yi_liuyao` | 六爻纳甲排盘（`question` 必填；`mode`／`datetime`／`numbers`／`yao`／`seed`／`gender`） |
| `yi_bazi` | 八字四柱（`datetime`／`gender` 必填；`longitude` 可选） |
| `yi_kb` | 判据知识库检索（`query` 必填；`discipline`／`limit` 可选） |
| `yi_report` | 单文件报告（`discipline` 必填；`format` = html／md，其余参数同对应排盘工具） |

参数与返回结构以 `src/tools.mjs` 的 inputSchema 为准（1.0 冻结面，AGENTS.md §二）。
六爻 html 与两科 md 走引擎 render 段；八字 html 由 `src/report.mjs` 排版，文字全部来自引擎字段。

### 知识库

`skills/yi-divination/references/` 下的判据文档篇数以 `INDEX.md` 与
`plugins/scripts/kb-docs.mjs` 登记表为准；先用 `yi_kb` 按关键词定位，再按 `文件:行` 读节段。

> ⛔ 古籍案例库 `case_library.md` 刻意不随包（AGENTS.md §一.2）：打包层排除、
> 自检 [1.5] 断言、`yi_kb` 扫描层排除，三道闸。

## Python 解释器

优先级：`DSH_PYTHON` → DSH 桌面自带运行时 → PATH 的 `python`／`python3` → Windows `py`。
全找不到时逐条列出已尝试路径并报错，不静默回退——确定性口径不允许换解释器。

## 构建与自检

```sh
node ../plugins/scripts/build.mjs     # 一次构建，分发到本宿主
node ../plugins/scripts/selftest.mjs  # 共享层包级自检（含负例自证）
npm run check                         # build + selftest + verify-in-dsh
```

`engine/`、`skills/`、`src/*.mjs` 是构建产物，不入库、不要手改（selftest [1]／[1.6]
逐字节同源门会判红）。`verify-in-dsh` 构造 Cordis 上下文、真跑 `execute()` 并断言
技能条目形状（invocation 为对象、rank 为有穷数）与 render 文本块。
包体实测值以 `npm pack --dry-run --json` 与自检实跑输出为准，不在本文抄快照。

## 口径边界（重要）

- 引擎内一切分数是**古籍案例对齐分**（与古籍要点的吻合度），**不是现实命中率**；现实侧样本为零。
- 输出是象征推演与方向参考，不是预言；凶象用「偏向／有…信号／结构上」表述。
- 医疗、法律、投资、重大决策请以专业意见为准。
- 八字结论是机械推演，不含命运吉凶断言；方向字段为空属正常。
- 外部集已参与调参，读数见 `CAPABILITY.md`（带集合名、n 与出处）。

## 已知限制

- 时区：按输入的本地钟表时直接排盘，不做时区换算；`longitude` 只做真太阳时经度校正。
- 报告写入系统临时目录（`%TEMP%/yi-reports/` 或 `os.tmpdir()/yi-*`），目录只增不清。
- 现实占断反馈在册 0 条；本插件没有任何现实命中率数据。

## 权限与安全

manifest 的 `dsh.permissions` / `externalServices` / `failureBounds` 是唯一真源：
运行期零 npm 依赖、零出站网络；只 spawn 随包只读的 Python 引擎，报告只写临时目录；
读白名单环境变量（`DSH_HOME`／`DSH_PYTHON`／`PATH` 等），不读密钥与凭证。
兼容范围见 `package.json`（Node >=22，DSH >=0.2.1-rc.2）。

## 许可

MIT（根 `LICENSE`／`dsh-plugin/LICENSE`／manifest 三处一致）。
