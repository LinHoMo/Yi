# 小六壬·接口规格（api_spec）

四段管线契约（`docs/CONTRACT.md` §一）：chart → analyze → narrate → render，段间只传结构化数据。

## 一、chart 段（`scripts/chart.py`）

**输入**（`chart(params)`，params 为 dict）：

| 键 | 类型 | 说明 |
|---|---|---|
| `way` | str | `datetime` / `lunar` / `month_day_hour` / `numbers`，默认 `datetime` |
| `datetime` | str/datetime | `way=datetime`：公历时刻 ISO 字符串，自动转农历月日+时辰 |
| `year` `month` `day` `hour_branch` | int×3 + str | `way=lunar`：农历年月日 + 时支（如"申"） |
| `month` `day` `hour_ordinal` | int×3 | `way=month_day_hour`：农历月日 + 时辰序数（子=1…亥=12） |
| `numbers` | list[int] | `way=numbers`：报数（任意个数，正整数） |
| `topic` | str | 显式事类（覆盖问句自动识别；案例库传声明事类） |
| `direction` | str | 目标方位（东/南/中/西/北等），供 analyze 方位/五行综合断；可缺省 |
| `question` | str | 问事文本（自动识别事类 topic） |

**输出**（chart 段，关键字段）：

| 键 | 类型 | 说明 |
|---|---|---|
| `way` | str | 起课方式 |
| `steps` | list[int] | 各步落宫序（月宫/日宫/时宫，或逐数） |
| `step_names` | list[str] | 各步名称 |
| `palace` | int | **课体**：时宫落宫序（0=大安…5=空亡） |
| `month` `day` `hour_ordinal` | int | month_day_hour 起课的原始参数 |
| `numbers` | list[int] | numbers 起课的原始报数 |
| `topic` | str | 事类 |
| `direction` | str | 目标方位（可缺省） |
| `question` | str | 问事文本 |

起课法（《贺氏六壬小手册》第二节）：以"大安"起正月顺数至所求月；以月宫起初一顺数至所求日；以日宫起子时顺数至所求时辰。变通/随机取数（第三、四节）：第一数自大安起数，其后自上数落宫起数。

## 二、analyze 段（`scripts/analyze.py`）

**输入**：chart 段输出。**输出**（关键字段）：

| 键 | 类型 | 说明 |
|---|---|---|
| `schema` | str | `xiaoliuren-analyze-v1` |
| `topic` `question` | str | 事类与问事文本 |
| `chart_summary` | dict | 落宫/起课方式/报数/月日时/时辰序 |
| `steps` | list[dict] | 步序与各步落宫名 |
| `palace` | dict | 六要素：宫名/五行/颜色/方位/属神/位置/主数/含义/总诀/方向 |
| `neighbors` | dict | **邻宫速断**：进宫/退宫/临宫[]，各含 宫名/关系/主速/速断/说明/所本 |
| `direction_element` | dict | **方位/五行综合断**：输入方位/方位五行/落宫五行/关系/倾向/说明/所本 |
| `topic_verdict` | dict | topic/诀句/宫义/所本 |
| `timing` | dict | 主数/解读/所本 |
| `comprehensive` | bool | 是否综合判断事类（出行/求财） |
| `conclusion` | dict | 方向/说明/宫义/所本 |
| `factors` | list[dict] | {因子, 权重, 判据, 所本}，六因子：落宫30/吉凶方向30/事类断语20/应期主数20/邻宫速断0/方位五行0 |

方向取法（`data/verdicts.json`）：大安/速喜/小吉→吉，赤口/空亡→凶，留连→平（两可宜缓）。

邻宫速断（`data/verdicts.json`）：进=顺数下一位、退=逆数上一位、临=掌诀相邻。规则先查 `neighbor_overrides`（有古籍出处，如『留连临速喜→不久即归』），未命中按主速属性查 `speed_interactions`（通行口径）。py 只查表。

方位/五行综合断（`data/verdicts.json`）：输入方位→查 `direction_element_map` 得方位五行→`core.wuxing_relation` 与落宫五行生克→查 `direction_relation` 得倾向（助/泄/阻/制/和）。例：西方金生留连水=生我→助。

## 三、narrate 段（`scripts/narrate.py`）

**输入**：analyze 输出。**输出**：师傅口吻 markdown 正文（标题/结论/落宫解读/事类断语/应期主数/综合权衡提示/口径收尾）。只装配 analyze 判据，不自行推断新结论。

## 四、render 段（`scripts/render.py`）

**输入**：analyze 输出。**输出**：单文件 Markdown 报告（正文 + 盘面数据附录 + 判读因子明细），薄层不自带 HTML 模板。

```
python scripts/render.py [analyze.json] [-o report.md]
```

## 五、案例与评分

- 案例库：`data/cases/xiaoliuren_cases.json`（tune 10 / holdout 5 / excluded 2）
- 运行器：`scripts/case_runner.py`，输出 `{"cases": [...], "errors": [...]}` 契约
- 评分器：`scripts/evaluate.py`（复用 `yishu_core.eval`），维度：落宫30/吉凶方向30/事类诀句20/应期主数20
- 质量门：`tools/check.py`（金标准指纹 + 冒烟 + tune/holdout 分别出分带 n）

## 六、MCP JSON-RPC 方法（`scripts/mcp_server.py`）

四段脚本经共享路由 `tools/mcp_router.py` 以 **JSON-RPC 2.0 over stdio** 暴露；
薄入口 `scripts/mcp_server.py` 锁定本学科，不另写推演。也可用
`python tools/mcp_router.py --discipline xiaoliuren` 或 `--all`（四科同进程）。

**传输**：每行一个 JSON 请求，每行一个 JSON 响应；`"id"` 缺省/为 null 视为通知、无响应。

| 方法 | 参数（params） | 返回 |
|---|---|---|
| `xiaoliuren.chart` | 与 chart 段 `chart(params)` 同构的 dict | chart JSON |
| `xiaoliuren.analyze` | 起盘参数 dict，或 `{"chart": <chart JSON>}` | analyze JSON |
| `xiaoliuren.narrate` | 同 analyze | `{text, conclusion?, chart_summary?, question?}`，`text` 为唯一交付正文 |
| `xiaoliuren.render` | 同 analyze；可选 `format`: `"md"`\|`"html"`（默认 md） | `{content, format}` |
| `xiaoliuren.list_methods` / `list_methods` | — | `{methods: {名: 说明}}` |

**format**：本 render 段仅出 Markdown；`format=html` 返回 JSON-RPC error `-32602`。

**错误码**：`-32700` 解析 / `-32600` 非法请求 / `-32601` 方法不存在 / `-32602` 参数错误 / `-32603` 内部错误。

```bash
python scripts/mcp_server.py --help
python scripts/mcp_server.py --list-methods
python scripts/mcp_server.py --test-narrate          # 冒烟：演示盘 narrate
python scripts/mcp_server.py                        # stdio 服务
```

JSON-RPC 示例：

```json
{"jsonrpc":"2.0","id":1,"method":"xiaoliuren.narrate","params":{"way":"month_day_hour","month":8,"day":15,"hour_ordinal":9,"question":"测有人否"}}
{"jsonrpc":"2.0","id":2,"method":"xiaoliuren.render","params":{"way":"month_day_hour","month":8,"day":15,"hour_ordinal":9,"question":"测有人否","format":"md"}}
{"jsonrpc":"2.0","id":3,"method":"list_methods","params":{}}
```
