# 择吉·接口规格（api_spec）

四段管线契约（`docs/CONTRACT.md` §一）：chart → analyze → narrate → render，段间只传结构化数据。

## 一、chart 段（`scripts/chart.py`）

**输入**（`chart(params)`，params 为 dict）：

| 键 | 类型 | 说明 |
|---|---|---|
| `date` | str/date | 公历日期 YYYY-MM-DD（或 datetime，取日期部分） |
| `datetime` | str/date | 与 `date` 同义（择吉只取日期层） |
| `hour_branch` | str | 时支（如"午"），可选；给了才出时辰值神 |
| `activity` | str | 显式事类（覆盖问句自动识别；案例库传声明事类） |
| `question` | str | 问事文本（自动识别活动 activity） |

**输出**（chart 段，关键字段）：

| 键 | 类型 | 说明 |
|---|---|---|
| `way` | str | 恒为 `date` |
| `date` | str | 公历日期 ISO |
| `weekday` | str | 星期（一二三四五六日） |
| `lunar` | dict | 农历年月日/闰月/月名 |
| `ganzhi` | dict | 年柱/月柱/日柱/月建/日支 |
| `jian_chu` | str | 建除十二神（建/除/满/平/定/执/破/危/成/收/开/闭） |
| `day_god` | str | 日值黄黑道神（青龙…勾陈） |
| `huang_dao` | bool | 日值神是否黄道 |
| `xiu` | dict | 值宿 {name, full}（宿名 + 宿名+禽名，如 牛/牛金牛） |
| `hour` | dict | 可选：{branch, god} 时支与时辰值神 |
| `activity` | str | 事类（显式或识别结果） |
| `question` | str | 问事文本 |

装配法（内核 `yishu_core.zeji_tables`）：建除 = (日支序 − 月支序) mod 12；日值神 = 青龙起支（寅月起子，每月退二支）+ 日支偏移；值宿 = 固定序循环（角…轸）以 2007-09-13=角 为锚点逐日 +1。

## 二、analyze 段（`scripts/analyze.py`）

**输入**：chart 段输出。**输出**（关键字段）：

| 键 | 类型 | 说明 |
|---|---|---|
| `schema` | str | `zeji-analyze-v2`（v1→v2 仅新增 `citations` 透出字段，判据字段未变） |
| `activity` `question` | str | 事类与问事文本 |
| `yi_hit` `ji_hit` | bool | 活动在建除/值神宜表（宜命中）、在建除忌表（忌命中） |
| `chart_summary` | dict | 日期/星期/农历/干支/建除/日值神/黄道/值宿 |
| `factors_detail` | dict | 三因子明细：jian_chu（神/宜/忌/含义）、huang_dao（神/黄道/宜/含义）、xiu（宿/全名/吉/凶） |
| `hour` | dict\|None | 时辰值神（给了时支才出） |
| `yi` `ji` | list[str] | 该活动此日有利/保留信号文本 |
| `citations` | dict | 参考书证（**只透出，不参与评分**）：`通则`（引擎两项计分判据的书证篇目）、`本例`（本例事类的书证篇目）、`缺口`（《協紀辨方書》缺书登记）、`来源`（书源文件与 provenance）。数据源 `data/citations.json` |
| `conclusion` | dict | 方向（吉/平/凶）/说明/得分/所本 |
| `factors` | list[dict] | {因子, 权重, 判据, 所本}，四因子：建除20/黄黑道20/星宿20/吉凶40 |

**两份数据的分工（不得互相替代）**：
- `data/verdicts.json` = **判据唯一真值源**（建除/黄黑道/星宿宜忌表、裁决规则、措辞模板）；`basis_*` 引据属通行口径转述（原书库内无公版，见下）。
- `data/citations.json` = **参考书证**（《玉匣記》逐字引文，带篇名与源文件行号），由 narrate 第三节照录，**不改判据、不参与评分**。
- 书证门 `dev_tools/check.py::check_citations` 断言：引文逐字可回指书源、事类全覆盖、缺口登记齐备、书证不出现判据专属键。

综合裁决（`data/verdicts.json::verdict_rule`）：黄黑道 ±1（日辰第一权）+ 建除对该活动宜 +1/忌 -1 + 星宿 ±0.5；总分 ≥1 吉、≤-1 凶、其间平。**此为学科自有规则应用，非古籍定论。**

## 三、narrate 段（`scripts/narrate.py`）

**输入**：analyze 输出。**输出**：师傅口吻 markdown 正文（一、盘面 / 二、事类宜忌 / 三、参考书证逐字引文 + 来源缺口 / 口径收尾）。只装配 analyze 判据与 `citations`，不自行推断新结论。若 `citations` 为空则不输出第三节。

## 四、render 段（`scripts/render.py`）

**输入**：analyze 输出。**输出**：单文件 Markdown 报告（正文 + 盘面数据附录 + 判读因子明细），薄层不自带 HTML 模板。

```
python scripts/render.py [analyze.json] [-o report.md]
```

## 五、案例与评分

- 案例库：`data/cases/zeji_cases.json`（tune 10 / holdout 5 / excluded 2），expected 记：建除/日值神/黄道/值宿（历法真值，通书核对）+ 宜忌命中/方向/得分（规则应用）
- 运行器：`scripts/case_runner.py`，输出 `{"cases": [...], "errors": [...]}` 契约
- 评分器：`scripts/evaluate.py`（复用 `yishu_core.eval`），维度：建除20/日值神20/黄道10/值宿20/宜忌命中15/综合方向15
- 质量门：`tools/check.py`（金标准指纹 + 冒烟 + tune/holdout 分别出分带 n）；分科门 `dev_tools/check.py`（[1c] 书证门 + [1] 金标准 + [2] 冒烟 + [3] tune/holdout）
- 书证构建器：`dev_tools/build_citations.py`（默认 dry-run，`--write` 落盘 `data/citations.json`；逐条断言引文为书源整行原文）



