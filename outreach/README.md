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
| 构建器 | `outreach/build_outreach.py` | `--write` / `--check` / `--selftest` |
| 工具 | `outreach/install-skill.mjs` | 把技能装进通用 `skills/` 目录 |
| 入库产物 | `llms.txt`、`KNOWLEDGE.md`、`kb/INDEX.md`、`examples/*.md` | **由构建器生成、入库**，供 GitHub / raw / 联网检索直接读 |
| 不入库产物 | `site/`（gitignore） | GitHub Pages Actions 现场生成后部署，见 `.github/workflows/pages.yml` |

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
python outreach/build_outreach.py --write      # 重生成 5 份入库产物 + site/
python outreach/build_outreach.py --check      # CI 常驻同源复验（默认动作）

node outreach/install-skill.mjs --target ~/.claude/skills/yi-divination
```

`--check` 挂在 `.github/workflows/ci.yml` 的 `root-gates`；`pages.yml` 每次 push 到 main
先跑 `--check` 再 `--write` 并部署 `site/`。新增/改动判据篇目须同步 `plugins/scripts/kb-docs.mjs`
与 `KNOWLEDGE-BODY.md`，随后重跑 `--write` 并把产物一起提交。

## 与既有 `plugins/skills/` 的关系

`plugins/scripts/build.mjs` 生成的 `skills/yi-divination/references/INDEX.md` 是**随包产物**（不入库），
服务 `yi_kb` 检索；`kb/INDEX.md` 是**对外导览**（入库），服务 GitHub 读者与联网 AI。
两者篇目同源于 `kb-docs.mjs`，但用途不同、不互为真源——不要合并，也不要手改任一份。
