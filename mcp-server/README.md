# Yi MCP Server（stdio，零第三方依赖）

让本地 AI 客户端（Claude Desktop、Cursor、Cherry Studio 等）**直接调用 Yi 引擎**
出术数报告——不需要复制提示词、不需要 GitHub 账号、不需要云端。

## 是什么

- **传输**：JSON-RPC 2.0 over stdio（每行一个请求、每行一个响应），纯标准库实现，无 `mcp` 包、无第三方依赖。
- **薄层**：只把各科已有的四段契约脚本（`chart → analyze → narrate → render`）挂到方法上，
  **不写任何新的推演/起课/断语逻辑**（`AGENTS.md` 铁律一：机械运算只归引擎）。
- **当前注册**：命科 `ming`（四柱八字：chart / analyze / narrate / render / list_methods）。
  六爻走专用 CLI/流水线；其余科按同一模式接入（见 `tools/mcp_router.py` 注册处）。

## 快速启动

```bash
# 本地测试：列出全部方法
python tools/mcp_router.py --all --list-methods

# 单科 stdio 服务（标准输入输出；AI 客户端直接连这个命令）
python tools/mcp_router.py --discipline ming

# 全科同一进程（当前只有 ming 注册）
python tools/mcp_router.py --all

# 端到端自测（一条 JSON-RPC 请求跑完 chart→analyze→narrate）
python tools/mcp_router.py --discipline ming --test-narrate
```

## 配置 Claude Desktop

`claude_desktop_config.json`（Claude Desktop 菜单 → Settings → Developer → Edit Config）：

```json
{
  "mcpServers": {
    "yi": {
      "command": "python",
      "args": ["C:/Users/<你>/Desktop/program/Yi/tools/mcp_router.py", "--all"]
    }
  }
}
```

> `command` 用你机器上 `python` 的绝对路径（`where python` 可查）；`args` 第一项用仓库内
> `tools/mcp_router.py` 的绝对路径。Cursor 等编辑器在各自的 MCP 配置里同理。

## 方法清单

| 方法 | 参数 | 返回 |
|---|---|---|
| `list_methods` | — | 全部方法帮助 |
| `ming.chart` | `datetime`(如 `1990-05-20 10:30`)、`gender`(男/女) | chart JSON（四柱/十神/空亡） |
| `ming.analyze` | 同 chart（可直接给起盘参数） | analyze JSON（强弱/格局/喜用/大运/流年/成败救应） |
| `ming.narrate` | 同上 | `{text, ...}` 因子正文 |
| `ming.render` | 同上 | `{content, format}`（md） |

请求示例（发到 stdin）：

```json
{"jsonrpc":"2.0","id":1,"method":"ming.analyze","params":{"datetime":"1990-05-20 10:30","gender":"男"}}
```

## 安全与边界

- 仅本地 stdio，不监听端口、不对外网；给 AI 客户端的命令本身即入口，无额外权限。
- 返回的分数为**古籍案例对齐分（非现实命中率）**，narrate 自带口径声明；
  AI 客户端翻译输出时不得添油加醋（铁律三）。
- 想接入新科：在 `tools/mcp_router.py` 注册处照 ming 模式加三行映射即可，
  复用该科已有四段脚本，禁止在路由器里新写判据。
