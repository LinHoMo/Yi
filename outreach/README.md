# 对外可发现层（outreach/）

> 第五百四十九批新建。本目录解决一个具体问题：**网页端大模型联网检索只能读静态文本，
> 不会执行 Python**，而本仓此前「结论只在运行时产生、当场交付、从不落盘」。
> 结果就是：仓库公开、代码齐全、判据知识齐备，外部 AI 却既搜不到、也读不到任何成品结论。

## 真源与产物

| 角色 | 路径 | 说明 |
|---|---|---|
| 真源（人写） | `outreach/KNOWLEDGE-BODY.md` | 面向 AI 的自包含术数知识正文、术语表、铁律、FAQ |
| 真源（登记） | `plugins/scripts/kb-docs.mjs` | 判据篇目登记表，与随包知识库构建器共用**同一份**，不新增第二登记表 |
| 真源（判据） | `liuyao/references/`、`bazi/references/` | 判据全文（案例库 `case_library.md` 永不进对外层） |
| 真源（引擎） | 两科 `scripts/`、`engine/`、`core/` | 示例结论由四段流水线现场实跑 |
| 构建器 | `outreach/build_outreach.py` | `--write` / `--check` / `--registry` / `--selftest` |
| 工具 | `outreach/install-skill.mjs` | 把技能装进通用 `skills/` 目录 |
| 入库产物 | `llms.txt`、`KNOWLEDGE.md`、`kb/INDEX.md`、`examples/*.md` | **由构建器生成、入库**，供 GitHub / raw / 联网检索直接读 |
| 不入库产物 | `site/`（gitignore） | GitHub Pages Actions 现场生成后部署；含判据索引离线镜像与逐篇全文副本 |

## 三条铁律怎么守

- **§一.1 机械运算归代码**：`examples/` 两份报告逐字来自 `chart → analyze → narrate → render` 实跑，
  固定输入（`datetime` + `seed`），两次运行逐字节一致；`--check` 把产物与现场重跑结果逐字节比对，
  手改即判红。人只写「知识说明」，不写任何占断结论。
- **§一.2 案例库隔离**：示例输入是**新造中性问句**，不触达 `data/cases/`；
  `validate_rows` 拒绝登记表出现 `case_library`，`validate` 拒绝示例出现该字样；
  `llms.txt`／`KNOWLEDGE.md`／`kb/INDEX.md` 三处均明示「虽在仓库公开，禁止用于解读」。
- **§一.3 口径诚实**：所有对外文本带脚注（对齐分 ≠ 现实命中率、非预言、专业意见优先）；
  `validate` 逐行扫禁句并保留否定语境豁免（与 plugins 自检 [7] 同口径），11 类正负例自证。

## 命令

```bash
python outreach/build_outreach.py --selftest   # 内存负例，真盘零写入
python outreach/build_outreach.py --write      # 重生成 6 份入库产物 + site/
python outreach/build_outreach.py --check      # CI 常驻同源复验（默认动作，含双登记表对账）
python outreach/build_outreach.py --registry   # 只跑双登记表对账（不跑引擎，秒级）

node outreach/install-skill.mjs --target ~/.claude/skills/yi-divination
```

`--check` 挂在 `.github/workflows/ci.yml` 的 `root-gates`；`pages.yml` 每次 push 到 main
先跑 `--check` 再 `--write` 并部署 `site/`。新增/改动判据篇目须同步 `plugins/scripts/kb-docs.mjs`
与 `KNOWLEDGE-BODY.md`，随后重跑 `--write` 并把产物一起提交。

## 双登记表怎么对账（552 批加固）

`kb/INDEX.md`（对外导览，入库）与随包 `skills/yi-divination/references/INDEX.md`
（构建产物）是同一份登记表的两个渲染结果。此前只有「登记了就得在盘」的单向检查，
解析用宽松正则——认不出的行会被**静默跳过**，磁盘新增篇目没登记也不会红。现在四向对账：

| 方向 | 判据 | 失守后果 |
|---|---|---|
| ① 解析 ↔ JS | `--check` 直接 `import` `kb-docs.mjs` 的 `KB_DOC`，与 Python 解析逐条比 keys／描述／顺序（node 不在 PATH 时跳过并打印原因） | 两侧读到不同份数，读者看到残表 |
| ② 登记 ↔ 磁盘 | 两科 `references/*.md`（排除 `case_library.md` 与 `INDEX.md`）必须全部在登记表内 | 新增判据对外层静默缺席 |
| ③ 登记 ↔ 随包索引 | 已构建时比篇目集合与描述原文 | 插件内检索缺篇／描述分家 |
| ④ 每篇 ↔ 产物 | `llms.txt`／`KNOWLEDGE.md`／`kb/INDEX.md`／`site` 索引逐篇恰好可见，站内相对链接全部可解析 | 分节渲染漏一篇仍全绿（新增第三个科时最易踩） |

解析侧另改为 fail-closed：块内每一非空非注释行必须是单行 `['<科>/<篇>.md', '<描述>']`
字面量，否则带行号判红；描述含 `|` 或换行也判红（会撑坏 Markdown 表格）。
`--selftest` 为上述每条规则各留一条负例（29 类全过才绿，含首页与全部可读版的站内链接门、文内与页内锚点门）。


## 与既有 `plugins/skills/` 的关系

`plugins/scripts/build.mjs` 生成的 `skills/yi-divination/references/INDEX.md` 是**随包产物**（不入库），
服务 `yi_kb` 检索；`kb/INDEX.md` 是**对外导览**（入库），服务 GitHub 读者与联网 AI。
两者篇目同源于 `kb-docs.mjs`，但用途不同、不互为真源——不要合并，也不要手改任一份。
552 批起两个构建器互为对账：`--check` 会把随包索引与登记表逐篇比，任一侧改漏即红。

## Pages 镜像（site/）

`site/` 不入库，由 `--write` 现场生成、`pages.yml` 部署。552 批把离线阅读做成两层：

- **判据索引镜像**：`kb/INDEX.md` 与可点的 `kb/INDEX.html`，链接全为站内相对路径，
  断网/离线下载后也能一页点进每一篇。落在 `kb/` 子目录而非根——Windows 大小写不敏感，
  `site/INDEX.md` 与 `site/index.md` 实测是同一个文件（`.resolve()` 指回 `index.md`），
  写根会互相覆盖并顶掉 Pages 首页。
- **每篇 HTML 可读版**：Pages 对 `.md` 返回 `text/markdown`，浏览器不保证内联，标题/表格
  都是原始标记；故每篇判据、三份示例与 `KNOWLEDGE.md` 另外生成 HTML（内置转换器、零依赖），
  同时保留同名 `.md` 原文供抓取与 diff。转换器只覆盖仓内实际用到的语法，认不出的行按段落
  兜底、**绝不丢内容**；代码块未闭合直接判红。页内链接在构建期解析成站内 `.html`，
  未镜像的仓内文件指回 GitHub，案例库按 §一.2 **只留文字、不生成链接**。

构建期还守两条：每篇必须有 `.md`＋`.html` 两份产物（少一份判红），以及全站相对链接必须可解析
（首页、两份索引、14 篇判据与 3 份示例共 20 个 HTML 页逐页扫，死链 0）。
