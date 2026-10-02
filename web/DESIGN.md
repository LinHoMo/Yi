# 通道 A 纯前端站点 · 视觉选型留痕

本文件记录 `web/` 这一套手写三件套（`index.html` / `web.css` / `web.js`）美化时
**借鉴了哪些真实存在的开源项目、各自的许可证、以及为什么选它**。

原则：**借设计不借依赖**。全程没有复制任何第三方代码，也没有新增任何外部依赖
（无字体文件、无 CDN、无框架、无构建步骤）。因此站点仍是"纯静态 + 零凭证 + 零后端"。

---

## 一、候选清单（均为真实存在、可核验的开源项目）

| # | 项目 | 仓库地址 | 许可证（SPDX） | 核验方式 | 结论 |
|---|---|---|---|---|---|
| 1 | **Tufte CSS** | https://github.com/edwardtufte/tufte-css | **MIT** | 拉取仓库 `LICENSE` 逐字确认：`The MIT License (MIT) / Copyright (c) 2014 Dave Liepmann` | ✅ **选定（主）** |
| 2 | **Pico CSS** | https://github.com/picocss/pico | **MIT** | GitHub API `/repos/picocss/pico` 返回 `license.spdx_id = MIT` | ✅ **选定（次）** |
| 3 | **typo.css** | https://github.com/sofish/typo.css | ⚠️ **NOASSERTION** | 项目站自述"基于 MIT License 开源"，但 GitHub API `/repos/sofish/typo.css` 的 `license.spdx_id` 为 `NOASSERTION`（平台未识别） | ⚠️ 仅作**中文排版实践参考**，不复制其代码 |
| 4 | **shuimo-ui（水墨风 UI）** | https://github.com/shuimo-design/shuimo-ui | **MIT** | GitHub API `/repos/shuimo-design/shuimo-ui` 返回 `license.spdx_id = MIT` | ❌ 未采用（Vue 组件库，依赖与体积不符纯静态站约束），仅参考其"水墨 / 大量留白"的取向 |
| 5 | zhui（国风组件库） | https://github.com/zhui-team/zhui | 未核验成功 | GitHub API 取回失败，第三方索引站（HelloGitHub）标 MIT，**未经一手核验** | ❌ 未采用（React 组件库；且许可证未经一手核验，不作为借鉴依据） |

> 说明：候选 3、5 的许可证状态未能像 1、2、4 那样一手确认，故**不进入借鉴来源**。
> MIT 许可证要求"复制实质部分时保留版权声明"；本项目**未复制任何代码**，
> 借鉴的是不受版权保护的设计思路（版式比例、色阶、结构），即便如此仍在此逐条署名。

---

## 二、选定对象

**主：Tufte CSS — MIT — https://github.com/edwardtufte/tufte-css**
（Dave Liepmann 创建，现为 Edward Tufte 名下项目；默认分支 `gh-pages`）

**次：Pico CSS — MIT — https://github.com/picocss/pico**

**参考：typo.css — https://github.com/sofish/typo.css**（仅中文排版实践，许可证字段存疑，不取代码）

### 为什么是 Tufte CSS 作主

1. 本站内容形态是**古书式的"术数排盘 + 条件化断语"**：字号、行距、边注、引文、
   短横线这类"学术纸面"语汇，比通用后台 UI 语言更贴合。
2. Tufte CSS 的核心手法（非对称版心 + 右栏边注）**恰好服务于本仓库的铁律三**——
   "口径诚实"的说明（分数是古籍案例对齐分、非现实命中率）天然属于**边注**：
   既不打断正文阅读节奏，又始终在视野里。
3. 它与仓库既有的报告 CSS 是同一路审美：暖白纸底 + 深墨字 + 克制装饰。
   报告的色板（`core/yishu_core/report/html.py`）本身就是"纸墨"取向，
   借用 Tufte 的语言能让**外壳与内嵌报告长得像同一件东西**。
4. 项目本身零依赖、单一 CSS 文件，与"纯静态托管、禁止服务端框架"的硬约束同向。

### 为什么 Pico CSS 作次

它的"语义优先、类极少、一切可调面走 CSS 自定义属性、`[data-theme]` + `color-scheme`
管主题、`:focus-visible` 管焦点环"这套**工程纪律**，正是本站需要的：
只有一个 8 KB 级的手写 CSS，却要有可维护的令牌层与可靠的可访问性。
只取其"令牌化 + 语义化 + 焦点规范"，不引入其样式表。

---

## 三、具体借鉴了哪些设计语言

### 来自 Tufte CSS（读其 `tufte.css` 源码后逐条对应）

| Tufte CSS 的做法（原文） | 本站如何落地 |
|---|---|
| `body { width: 87.5%; padding-left: 12.5%; max-width: 1400px }` —— 版心偏右、左留白大 | `.wrap` 采用等效的非对称思路：内容栏 + 右侧**注栏**，宽屏下正文不铺满 |
| `section > p { width: 55% }`，右 45% 留给边注 | `--measure: 32em`（中文约 32 字/行）限制正文行宽；`.card-split` 右侧留给图形/注 |
| `.sidenote, .marginnote { float: right; margin-right: -60%; width: 50%; font-size: 1.1rem }` —— 边注字号更小、行高更紧 | `.notes` / `.note`：边注区字号降至 `--fs-sm`，行高收到 1.75，左侧一道**朱砂细线**作注栏标记 |
| `hr { width: 55%; border-top: 1px solid #ccc }` —— 只用**短**横线 | `hr.rule`：前 56px 走朱砂、其余为纸色细线，替代原先"标题左侧竖条"的老写法 |
| `h1/h2/h3 { font-weight: 400 }`（标题不用粗体，靠字号与留白分层） | `.cardtitle` / `h1` 一律 `font-weight: 400`，改用**字号 + 字距 + 楷体**分层 |
| `p { font-size: 1.4rem; line-height: 2rem }`（行高约 1.43 倍，但字大） | 中文行高另按 typo.css 实践取 1.85–1.95（见下） |
| `body { background-color: #fffff8; color: #111 }` + `@media (prefers-color-scheme: dark) { #151515 / #ddd }` | 保留仓库既有的纸／墨双主题（`--paper` / `[data-theme=ink]`），并**加了首屏定主题的内联脚本**消除闪白 |
| `@media (max-width: 760px)` 下边注折叠为行内块 | `@media (max-width: 900px)` 下 `.notes` 由多列改为单列堆叠 |
| `span.newthought { font-variant: small-caps }` —— 段首"新思起" | 中文无大小写，等效改为 `.eyebrow`（字距拉开的朱砂小标）作为每节"起句" |

### 来自 Pico CSS

- **令牌化**：颜色 / 间距（4 的倍数阶梯 `--s1..--s9`）/ 圆角（`--r1..--r4`）/ 阴影（三层）
  / 字号（`--fs-hero..--fs-xs`）/ 动效（`--ease`、`--dur`）全部收敛为 CSS 自定义属性，改一处即全局生效。
- **语义优先、类尽量少**：新结构主要用 `<header>/<main>/<section>/<aside>/<hr>/<details>`，
  自造类只用于确有形态差异的部件。
- **主题契约**：`<html data-theme>` + `color-scheme: light dark`，切换时同步浏览器原生控件配色。
- **焦点规范**：统一走 `:focus-visible`（表单控件另加一层 `--accent-wash` 焦点环），
  鼠标点击不出环、键盘操作必有环。

### 来自 typo.css（仅为中文排版实践，未取代码）

- 中文正文行高取 **1.85–1.95**（西文 1.4 的比例不适用于方块字）。
- 中西文混排：`line-break: strict`（禁则）、`word-break: normal` + `overflow-wrap: break-word`、
  递进使用 `text-spacing-trim: space-first`（浏览器不支持则自动忽略）。
- 代码 / 日志字号比正文**降一档**（`--fs-xs`）并换等宽字族。

### 明确没有借的部分

- **字体文件**：Tufte CSS 自带 ET Book 网络字体，本站**不引入**（会新增外部依赖与体积）。
  改为优先使用**系统已装**的楷／宋字族栈（`--font-display` / `--font-serif`），
  Windows 自带楷体、macOS 自带 Kaiti SC，缺失时回落到通用衬线体，**零下载**。
- **任何 JS 依赖、框架、CDN**：站点仍是原生 HTML/CSS/JS。
  全文唯一的运行时外部请求，仍是既有的 Pyodide CDN（本次未改动），
  且首屏不依赖它就完整可见（表单与深链都能用）。

---

## 四、与硬约束的关系（自查）

| 硬约束 | 本次做法 |
|---|---|
| 零凭证 / 零后端 / 不上传输入 | 未新增任何请求；美化全在 CSS 与 DOM 结构层 |
| 深链协议 `?d=&q=&dt=&auto=1` | `readDeepLink` / `buildDeepLink` 与协议语义一字未改；矩阵变更时只往 `DEEPLINK_KEYS` 增了 `up`/`mid`/`down` 三个短键（灵棋经三部掷数），八科深链实测均可出报告 |
| 纯静态托管、不得引入服务端框架 | 无框架、无构建、无新文件依赖；`WEB_FILES` 集合不变 |
| CDN 可 vendor 化或优雅降级 | **未新增任何 CDN 引用** |
| 不破坏 `engine_runtime._isolate` | 美化完全没碰那段；后续矩阵变更只动 `WEB_DISCIPLINES` / `DEMO`（见 §六），并以"八科同进程连跑、逐科与本机基准比 len+校验和"复核 |
| 能力矩阵锁 | 美化层未动；后续矩阵变更按 `llms.txt` 权威表把两科挂满（见 §六），四处同步改并由门核对 |
| 口径诚实 | 报告口径说明（古籍案例对齐分 ≠ 命中率）从正文段落**提到边注区**，位置更显眼、表述一字未弱化 |

---

## 五、已知取舍

1. **墨色主题下内嵌报告仍是浅色纸面**。报告 HTML 由 `core/yishu_core/report/html.py`
   生成，带自己的浅色 CSS，且 `core/` 不在本次改动范围内。深色主题下它表现为
   "暗桌上的一张纸"，视觉上是自洽的，如需统一需改 `core`（本轮不做）。
2. **`--font-display` 的楷体依赖系统字体**。这是"零下载"的代价；缺失时回落到衬线体，
   不会出现豆腐块或布局塌陷。
3. **`background-attachment: fixed` 的纸纹**在 iOS Safari 上会退化为随内容滚动，
   属可接受的优雅降级。

---

## 六、本轮追加（2026-10-01：矩阵变更 + 门加固）

美化落地之后，同一批又做了两件与视觉无关、但与"这个站点到底能跑什么"直接相关的事。
两件都不引入新依赖，也不改任何推演逻辑。

### 6.1 通道 A 由六科挂满八科

`liuren`（大六壬骨架）、`lingqi`（灵棋经）此前只在本机 CLI 与通道 B 可跑。现按
`llms.txt` 权威表把二者挂上网页通道，四处同步（缺一处即被门锁打死）：

| # | 文件 | 改动 |
|---|---|---|
| ① | `tools/build_web.py` | `DISCIPLINE_META` 增 `liuren`/`lingqi` 两条（含 `fields` 与 `caveat` 口径行，`caveat` 是前端唯一口径来源） |
| ② | `web/engine_runtime.py` | `WEB_DISCIPLINES` 增两科；`DEMO` 增两科（`smoke()` 自检与页面"自检"按钮按 id 取用，缺键即 KeyError） |
| ③ | `llms.txt` | 能力矩阵两行 → 三通道全 ✓；说明句重写 |
| ④ | `web/index.html` / `web/web.js` / `web/web.css` | 文案"六科"→"八科"；新增 `.caveat`；`renderFields` 支持 `type:"number"`；`collectForm()` 把数字框转 `Number`（内核要 0..4 整数，字符串会被拒） |
| ⑤ | `tools/verify_web_parity.py` | 覆盖不变式（见 6.3）；补 liuren / lingqi / "跑过两科后回到第一科"三例正例 |

`core/yishu_core/report/request.py` **未改**——`DISCIPLINES` 本就是八科，`REQUIRED` 也已含
这两科（liuren 要 `datetime`，lingqi 要三个 0..4 整数）；请求→CLI 参数的映射仍只有一份。

口径红线照旧：liuren 的页面与报告均标明**骨架科 · 无吉凶断语**，lingqi 标明
**《靈棋經》原文逐字直录**。前端不另写口径文案，只从站点清单的 `caveat` 字段渲染，
避免两处漂移。

### 6.2 窄屏页签：从"隐藏滚动条横滑"改为换行

八科之后，单行横滑会把后几科藏到屏幕外、且滚动条被隐藏——**挂上了却找不到**。
窄屏（≤620px）下改为换行铺满，八科一屏可见（390px 宽实测 3 行）。

### 6.3 把"门说的一致"变成"门断言的一致"

原先 `tools/verify_web_parity.py` 里另存着一份写死的"web 通道不挂载"名单，于是
「站点已挂载的集合」与「门验过的集合」是两个东西：站点说八科，门只验六科。现改为：

- `WEB_CHANNEL_UNAVAILABLE` **从 `DISCIPLINE_META` 派生**（引擎学科集合 − 站点挂载集合），
  不再写死任何名单；
- 新增**覆盖不变式**：同源验收正例覆盖的学科集合必须**恒等**于站点挂载集合，
  不等即红并逐项点名差集；
- `tools/check_web_site.py` 新增清单口径检查：`manifest.disciplines` ≡
  `engine_runtime.WEB_DISCIPLINES`（llms.txt 那句"同口径"过去只是注释，现在有门看着）。

两条新门都做过**证伪**——不会红的检查等于没有检查：把站点副本里的 `WEB_DISCIPLINES`
少写一科，站点自检即红并打印两个集合；把正例少一科，同源验收在跑任何用例之前就红，
点名"站点已挂载、同源验收却无正例：lingqi"。

---

## 七、验收留痕（2026-10-01）

### 7.1 三道门

| 命令 | 结果 |
|---|---|
| `python tools/build_web.py --outdir site` | 站点已生成：镜像 **158 个文件 / 1976.8 KB** |
| `python tools/check_web_site.py --site site` | **全 √**：清单与镜像逐条对齐（158）；各科运行期文件齐全（内核 24 个，共 8 科）；学科集合同口径（清单与 `engine_runtime` 均 8 科） |
| `python tools/verify_web_parity.py` | **全 √**：覆盖检查 站点挂载 8 科 ≡ 正例覆盖 8 科；正例 **13 例** MD/HTML 逐字节同源（含 liuren、lingqi、以及"跑过两科后回到 liuyao"）；负例 **2 例**两侧一致拒绝 |
| `python tools/check.py --full` | exit 1，**6 项失败全部落在 `disciplines/**` 非 web 作用域**，逐项为：① `[1]` `disciplines/ziwei/dev_tools/build_corpus.py` 改名复制内核表 `MAIN_STARS`（未跟踪新文件）② `[1]` 同文件复制干支序列 ③ `[1]` `disciplines/ming/dev_tools/build_dts_corpus.py:33` 复制天干序列 ④ `[1c]` 断语外置取证 ⑤ `[4]` ziwei 质量门 ⑥ `[5]` ziwei 行为指纹（`narrate_sha` 漂移）。web 相关各段全绿：[1e] 能力矩阵锁 √、[1f] 输入协议指纹 √、[7b] 站点构建+自检 √、[7c] 同源验收 √、[8] pytest √、[2] 内核自检 √、[3] ming √、[6] 六爻 √、[7] 合参 √。`git status` 显示 `disciplines/**`+`core/**` 有 133 处并发改动，均非本次写入 |

### 7.2 浏览器实证（不是静态检查通过就算数）

八科在**同一页面会话内先后连跑**，逐科与"本机子进程链路"的基准比长度与码点级 FNV-1a
校验和（校验和由浏览器内同构 JS 对报告正文复算）：

| 科 | 报告长度（浏览器/本机） | FNV-1a（浏览器/本机） | 同源 | 标题 |
|---|---|---|---|---|
| liuyao | 1357 / 1357 | 1377402780 / 1377402780 | √ | 六爻纳甲 · 占本周面试能否通过 |
| ming | 1597 / 1597 | 2461900493 / 2461900493 | √ | 四柱八字 · 命盘分析 |
| ziwei | 1413 / 1413 | 2644489975 / 2644489975 | √ | 紫微斗数 · 命盘分析 |
| meihua | 1300 / 1300 | 1070291651 / 1070291651 | √ | 梅花易数 · 占投资 |
| xiaoliuren | 1711 / 1711 | 2797492980 / 2797492980 | √ | 小六壬 · 占出行 |
| zeji | 1729 / 1729 | 3721005276 / 3721005276 | √ | 择吉 |
| liuren | 1517 / 1517 | 3730085112 / 3730085112 | √ | 大六壬 · 占本周面试能否通过 |
| lingqi | 514 / 514 | 1220387280 / 1220387280 | √ | 灵棋经 · 占求财 |

**结论**：八科同进程轮跑无"某科拿到别科盘面"——`engine_runtime._isolate` 未被前端改动破坏。
另实测三条深链（`?d=liuyao&…&auto=1`、`?d=lingqi&q=…&up=2&mid=1&down=3&auto=1`、
`?d=liuren&…&auto=1`）均自动推演出报告，`up`/`mid`/`down` 短键生效。

### 7.3 截图（绝对路径，均在 `tools/scratch/web-review/`）

- 改版后桌面：`A01-desktop-home.png`、`A03-desktop-liuren-form.png`、
  `A04-desktop-lingqi-form.png`、`A05-desktop-full.png`、`A06-desktop-workbench-clean.png`、
  `A07-ink-home.png`
- 改版后窄屏：`A08-mobile-home.png`、`A09-mobile-workbench.png`、
  `A16-mobile-lingqi-form.png`、`A14-mobile-report.png`、`A15-mobile-report-full.png`
- 深链过程/结果：`A10-deeplink-running.png`、`A11-deeplink-liuyao-report.png`、
  `A12-deeplink-lingqi-report.png`、`A13-deeplink-liuren-report.png`
- 改版前对照（**同主题强制浅色**，否则深色/浅色差异会混进"前后对比"）：
  `B1-before-desktop-home.png`、`B2-before-desktop-full.png`、`B3-before-mobile-home.png`
- 更早期（六科时代、同一套美化）另存 `01-*` … `13-*`，非本轮验收依据。

出图口径：`bu.cdp("Page.captureScreenshot", clip=…, captureBeyondViewport=True)`，
裁剪坐标按设备像素比换算（本机 K≈1.5007，`scale=1/K` 输出 1:1 CSS 像素图）；
`.reveal` 入场动效依赖 IntersectionObserver，**取帧前先把整页滚一遍**，
否则视口外的区块在整页截图里是空白（这一步是踩过才写下的）。
