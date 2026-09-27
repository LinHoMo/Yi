# 命科 API

四段契约与 `docs/CONTRACT.md` 一致。输出机械因子与推演标签，**无命运断言**。

## chart

| 参数 | 类型 | 说明 |
|------|------|------|
| `--datetime` | str | 出生公历 `YYYY-MM-DD HH:MM` |
| `--gender` | str | 男/女（大运顺逆） |
| `--longitude` | float | 可选经度 |
| `-o` | path | chart JSON |

输出：`pillars`（四柱干支/纳音/天干十神）、`factors`（藏干十神）、`shensha`、`ming_shen_gong`、`xunkong`。

## analyze

输入 chart JSON → `chart_summary` + `conclusion`：

- `strength` / `strength_score` / `pattern` / `useful_gods` / `taboo_gods`
- `dayun`：8 步（干支、起止岁、**运干十神**、`approximate`）
- `liunian`：流年干支×十神对照（不批吉凶）
- `verdicts[]`：机械标签，各带 `basis`
- `方向` 恒为空；`应期` 恒为空

## narrate / render

因子正文与报告；结尾保留「非宿命论、重大决策以专业意见为准」。

## 边界

不产出命运断言；从格仅 tentative；起运岁标注 approximate。

## 六、MCP JSON-RPC 方法（`scripts/mcp_server.py`）

四段脚本经共享路由 `tools/mcp_router.py` 以 **JSON-RPC 2.0 over stdio** 暴露；
薄入口 `scripts/mcp_server.py` 锁定本学科，不另写推演。也可用
`python tools/mcp_router.py --discipline ming` 或 `--all`（四科同进程）。

**传输**：每行一个 JSON 请求，每行一个 JSON 响应；`"id"` 缺省/为 null 视为通知、无响应。

| 方法 | 参数（params） | 返回 |
|---|---|---|
| `ming.chart` | `{datetime, gender, longitude, question}`（对应 chart 段关键字参数） | chart JSON |
| `ming.analyze` | 起盘参数 dict，或 `{"chart": <chart JSON>}` | analyze JSON |
| `ming.narrate` | 同 analyze | `{text, conclusion?, chart_summary?, question?}`，`text` 为唯一交付正文 |
| `ming.render` | 同 analyze；可选 `format`: `"md"`\|`"html"`（默认 md） | `{content, format}` |
| `ming.list_methods` / `list_methods` | — | `{methods: {名: 说明}}` |

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
{"jsonrpc":"2.0","id":1,"method":"ming.narrate","params":{"datetime":"1990-05-20 10:30","gender":"男"}}
{"jsonrpc":"2.0","id":2,"method":"ming.render","params":{"datetime":"1990-05-20 10:30","gender":"男","format":"md"}}
{"jsonrpc":"2.0","id":3,"method":"list_methods","params":{}}
```
