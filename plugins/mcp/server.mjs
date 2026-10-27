/**
 * Yan 插件侧的 MCP 服务（stdio，换行分隔 JSON-RPC，协议 2025-03-26）。
 *
 * 为什么自己写而不是引 `@modelcontextprotocol/sdk`：Yan 的插件包在 `inventory()`
 * 里**跳过 `node_modules`**（`lib/plugins/manifest.js`），随包能力必须是零依赖的。
 * 本服务只用到 Node 内建模块，因此打包后可直接被 Yan 以 `$node` 拉起。
 *
 * 三条与仓库铁律对齐的硬约定（插件不得放宽）：
 *  1. **机械运算归代码**：这里没有任何象数算法，全部委托 `engine.mjs` → Python 引擎。
 *  2. **不降级**：引擎失败即如实报错（`isError` + stderr 摘要），绝不返回半成品。
 *  3. **案例库隔离**：`yi_kb` 的扫描层硬排除 `case_library.md`（铁律二），包里也没有它。
 *
 * stdout 只允许出现 JSON-RPC 报文——任何诊断信息一律走 stderr，
 * 否则会污染 Yan 的 MCP 客户端解析（它会按行 JSON.parse，脏行直接被丢弃/关闭连接）。
 */
import { selftest } from './engine.mjs'
import { runKb } from './kb.mjs'
import { toJsonSchema } from './schema.mjs'
import {
  createBaziTool,
  createKbTool,
  createLiuyaoTool,
  createReportTool,
  runBazi,
  runLiuyao,
  runReport,
} from './tools.mjs'

const PROTOCOL = '2025-03-26'
const SERVER_INFO = { name: 'yan-yi-divination', version: '1.0.0' }

/**
 * 工具表。**与 dsh-plugin 1.0 冻结契约逐字同源**：工具名、参数集、输出 value 结构
 * 都取自 `tools.mjs` 的同一份定义，本文件只做宿主适配（schema 方言 + 调用协议）。
 */
const TOOLS = [
  { spec: createLiuyaoTool(null), run: runLiuyao },
  { spec: createBaziTool(), run: runBazi },
  { spec: createKbTool(), run: runKb },
  { spec: createReportTool(), run: runReport },
]

function toolDefinitions() {
  return TOOLS.map(({ spec }) => ({
    name: spec.name,
    // Yan 会把工具名改写为 `t_<sha20>` 并在描述前加 `[插件名 / 服务 id / 原名]`，
    // 因此描述里自带真实工具名，模型仍能按名索骥。
    description: spec.description,
    inputSchema: toJsonSchema(spec.parameters),
  }))
}

/** 把 render() 产出的文本块拍平成 MCP 的 content 数组。 */
function renderContent(spec, args, value) {
  const blocks = typeof spec.render === 'function' ? spec.render(args, value) : []
  const list = Array.isArray(blocks) ? blocks : [blocks]
  const content = list
    .filter((b) => b && typeof b === 'object')
    .map((b) => ({ type: 'text', text: String(b.text ?? '') }))
  if (!content.length) content.push({ type: 'text', text: '（工具未产出文本）' })
  return content
}

async function callTool(name, args) {
  const entry = TOOLS.find((t) => t.spec.name === name)
  if (!entry) throw new Error(`未知工具：${name}`)
  const value = await entry.run(args ?? {}, { signal: undefined })
  return {
    content: renderContent(entry.spec, args ?? {}, value),
    structuredContent: value ?? null,
  }
}

function send(message) {
  process.stdout.write(JSON.stringify(message) + '\n')
}

function fail(id, code, message) {
  send({ jsonrpc: '2.0', id: id ?? null, error: { code, message: String(message).slice(0, 4000) } })
}

async function handle(message) {
  const { id, method, params } = message ?? {}
  switch (method) {
    case 'initialize':
      return send({
        jsonrpc: '2.0',
        id,
        result: { protocolVersion: params?.protocolVersion ?? PROTOCOL, capabilities: { tools: {} }, serverInfo: SERVER_INFO },
      })
    case 'tools/list':
      return send({ jsonrpc: '2.0', id, result: { tools: toolDefinitions() } })
    case 'tools/call': {
      const name = params?.name
      const args = params?.arguments ?? {}
      try {
        const result = await callTool(name, args)
        return send({ jsonrpc: '2.0', id, result: { ...result, isError: false } })
      } catch (error) {
        // 工具级失败走 `isError` 而不是 JSON-RPC error：模型能看到原因并自行决定
        // 重试一次（AGENTS.md §一.1：「重试一次；仍失败则告知排盘异常」）。
        return send({
          jsonrpc: '2.0',
          id,
          result: {
            content: [{ type: 'text', text: `工具 ${name} 执行失败：${error?.message ?? error}` }],
            isError: true,
          },
        })
      }
    }
    case 'ping':
      return send({ jsonrpc: '2.0', id, result: {} })
    default:
      return fail(id, -32601, `不支持的方法：${method}`)
  }
}

function main() {
  let buffer = ''
  process.stdin.setEncoding('utf8')
  process.stdin.on('data', (chunk) => {
    buffer += chunk
    let newline
    while ((newline = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, newline)
      buffer = buffer.slice(newline + 1)
      if (!line.trim()) continue
      let message
      try {
        message = JSON.parse(line)
      } catch {
        fail(null, -32700, 'Invalid JSON')
        continue
      }
      // 通知（无 id）不回复；客户端发起的「服务端→客户端请求」也不支持。
      if (message.id === undefined) continue
      Promise.resolve()
        .then(() => handle(message))
        .catch((error) => fail(message.id, -32603, error?.message ?? error))
    }
  })
  process.stdin.on('end', () => process.exit(0))

  // 启动自检：只往 stderr 报，不阻断加载（与 dsh-plugin/src/index.mjs 同口径）。
  selftest()
    .then((problems) => {
      if (problems.length) {
        console.error('[yi] 引擎自检发现问题：')
        for (const p of problems) console.error('  ·', p)
      }
    })
    .catch((err) => console.error('[yi] 引擎自检异常：', err?.message ?? err))
}

main()
