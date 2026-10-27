#!/usr/bin/env node
/**
 * 共享层 + 各宿主适配器的包级自检。
 *
 * 用法：`node plugins/scripts/build.mjs && node plugins/scripts/selftest.mjs`。
 * 判红即 exit≠0。**每条新门都必须负例自证**（AGENTS.md §四.8）。
 *
 * 段号：
 *   [1]   分发一致性：适配器 src/*.mjs 与 `plugins/mcp/` 真源**逐字节同源**（含负例自证）
 *   [1.5] 铁律二：任何产物与适配器目录里都没有 case_library.md（含负例自证）
 *   [2]   两科 engine 入口脚本与内核副本齐备（plugins/ 与各适配器）
 *   [3]   skills：正文以 `plugins/SKILL.md` 为前缀 + 篇数对账 + INDEX 在位
 *   [4]   MCP 冒烟：**直接跑真源** plugins/mcp/server.mjs（initialize/list/call）
 *   [5]   工具契约：四工具在列、inputSchema.type=object、参数集与 1.0 冻结面一致
 *   [6]   适配器清单与包体：yan-plugin.json 规范 + resources 双向对账 + 包体预算
 *   [7]   口径诚实：对外文本无「预测准确率」一类禁语（逐行 + 否定语境豁免）
 */
import { spawn } from 'node:child_process'
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { KB_DOC } from './kb-docs.mjs'
import { resourceIdFor } from '../mcp/kb.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const PLUGINS_ROOT = resolve(HERE, '..')
const REPO_ROOT = resolve(PLUGINS_ROOT, '..')
const MCP_DIR = join(PLUGINS_ROOT, 'mcp')
const SKILL_SOURCE = join(PLUGINS_ROOT, 'SKILL.md')

/** 由构建分发的共享文件（[1] 段逐字节比对的对象）。 */
const SHARED_MCP_FILES = [
  'engine.mjs', 'kb.mjs', 'kb-synonyms.json', 'python.mjs',
  'report.mjs', 'schema.mjs', 'server.mjs', 'tools.mjs',
]

/** 1.0 冻结契约的工具名（AGENTS.md §二「1.0 API 冻结」）。 */
const FROZEN_TOOLS = ['yi_bazi', 'yi_kb', 'yi_liuyao', 'yi_report']

const ADAPTERS = [
  { id: 'dsh', dir: 'dsh-plugin', manifest: null },
  { id: 'claude', dir: 'claude-plugin', manifest: '.claude-plugin/plugin.json' },
  { id: 'codex', dir: 'codex-plugin', manifest: '.codex-plugin/plugin.json' },
  { id: 'gemini', dir: 'gemini-plugin', manifest: 'gemini-extension.json', contextFile: 'GEMINI.md' },
  // resources 双向对账是 **Yan 的机制**（Yan 用 `resource:` 句柄读包内文件）；
  // Claude 没有这个声明面，所以只有 yan 开门——306 批首跑时这块没按宿主分流，
  // 把 Claude 也判成「10 条资源未登记」，是断言写宽，不是真的缺陷。
  { id: 'yan', dir: 'yan-plugin', manifest: 'yan-plugin.json', reconcileResources: true },
]

const fails = []
const notes = []
let section = ''
function head(n) {
  section = n
  console.log(`\n[${n}]`)
}
const ok = (m) => console.log('  √', m)
const bad = (m) => {
  console.log('  ×', m)
  fails.push(`[${section}] ${m}`)
}
const note = (m) => {
  console.log('  ·', m)
  notes.push(m)
}

function walk(dir, base = '', out = []) {
  let entries
  try {
    entries = readdirSync(dir, { withFileTypes: true })
  } catch {
    return out
  }
  for (const e of entries) {
    if (['.git', 'node_modules', '__pycache__'].includes(e.name)) continue
    const rel = base ? `${base}/${e.name}` : e.name
    if (e.isSymbolicLink()) {
      out.push({ rel, symlink: true, bytes: 0 })
      continue
    }
    const full = join(dir, e.name)
    if (e.isDirectory()) walk(full, rel, out)
    else if (e.isFile()) out.push({ rel, symlink: false, bytes: statSync(full).size })
  }
  return out
}
const findCaseLibrary = (files) => files.filter((f) => f.rel.split('/').pop() === 'case_library.md').map((f) => f.rel)

// ── [1] 分发一致性（本批新建的核心门） ────────────────────────────────────────
head(1)
{
  const truthMissing = SHARED_MCP_FILES.filter((n) => !existsSync(join(MCP_DIR, n)))
  if (truthMissing.length) bad(`plugins/mcp/ 缺少共享真源：${truthMissing.join(', ')}`)
  else ok(`plugins/mcp/ 共享真源齐备（${SHARED_MCP_FILES.length} 个文件）`)

  for (const a of ADAPTERS) {
    const root = join(REPO_ROOT, a.dir)
    const drift = []
    const absent = []
    for (const name of SHARED_MCP_FILES) {
      const target = join(root, 'src', name)
      if (!existsSync(target)) {
        absent.push(name)
        continue
      }
      if (!readFileSync(target).equals(readFileSync(join(MCP_DIR, name)))) drift.push(name)
    }
    if (absent.length) bad(`${a.dir}/src 缺少分发文件：${absent.join(', ')}（先跑 build）`)
    else if (drift.length) bad(`${a.dir}/src 与真源不同源（手工改产物？）：${drift.join(', ')}`)
    else ok(`${a.dir}/src 与真源逐字节同源（${SHARED_MCP_FILES.length} 个文件）`)
  }

  // 负例自证：把真源副本改一个字节，门必须红
  const probe = mkdtempSync(join(tmpdir(), 'yi-drift-probe-'))
  const src = readFileSync(join(MCP_DIR, 'tools.mjs'))
  writeFileSync(join(probe, 'tools.mjs'), src)
  const tampered = readFileSync(join(probe, 'tools.mjs'))
  tampered.write('x', tampered.length - 1)
  writeFileSync(join(probe, 'tools.mjs.tampered'), tampered)
  const caught = !readFileSync(join(probe, 'tools.mjs.tampered')).equals(src)
  rmSync(probe, { recursive: true, force: true })
  if (caught) ok('负例自证：改一个字节即判定不同源（门不是瞎的）')
  else bad('负例自证失败：篡改一个字节后仍判定同源')
}

// ── [1.5] 铁律二 ────────────────────────────────────────────────────────────
head(1.5)
{
  let total = 0
  const hits = []
  for (const root of [PLUGINS_ROOT, ...ADAPTERS.map((a) => join(REPO_ROOT, a.dir))]) {
    const files = walk(root)
    total += files.length
    hits.push(...findCaseLibrary(files).map((r) => `${root.replace(REPO_ROOT, '')}/${r}`))
  }
  if (hits.length) bad(`出现 case_library.md：${hits.join(', ')}`)
  else ok(`共享层与所有适配器均无 case_library.md（扫了 ${total} 个文件）`)

  const probe = mkdtempSync(join(tmpdir(), 'yi-case-probe-'))
  writeFileSync(join(probe, 'case_library.md'), 'x')
  const seen = findCaseLibrary(walk(probe))
  rmSync(probe, { recursive: true, force: true })
  if (seen.length === 1) ok('负例自证：扫描器能抓到 case_library.md')
  else bad(`负例自证失败：扫描器在探针目录里没抓到（${seen.length}）`)
}

// ── [2] engine 入口 ─────────────────────────────────────────────────────────
head(2)
{
  const RELS = ['scripts/chart.py', 'scripts/analyze.py', 'scripts/narrate.py', 'scripts/render.py']
  const missing = []
  for (const root of [PLUGINS_ROOT, ...ADAPTERS.map((a) => join(REPO_ROOT, a.dir))]) {
    for (const d of ['liuyao', 'bazi']) {
      for (const rel of RELS) {
        if (!existsSync(join(root, 'engine', d, ...rel.split('/')))) missing.push(`${root.replace(REPO_ROOT, '')}/engine/${d}/${rel}`)
      }
      if (!existsSync(join(root, 'engine', d, 'core', 'yishu_core'))) missing.push(`${root.replace(REPO_ROOT, '')}/engine/${d}/core/yishu_core`)
    }
    if (!existsSync(join(root, 'engine', 'MANIFEST.json'))) missing.push(`${root.replace(REPO_ROOT, '')}/engine/MANIFEST.json`)
  }
  if (missing.length) for (const m of missing) bad(`缺少 ${m}`)
  else ok('共享层与各适配器的两科入口 + 内核副本 + MANIFEST 齐备')
}

// ── [3] skills ──────────────────────────────────────────────────────────────
head(3)
{
  const truth = existsSync(SKILL_SOURCE) ? readFileSync(SKILL_SOURCE, 'utf8').replace(/\s*$/u, '') : ''
  if (!truth) bad('真源 plugins/SKILL.md 读不到')
  for (const a of ADAPTERS) {
    const out = join(REPO_ROOT, a.dir, 'skills', 'yi-divination', 'SKILL.md')
    if (!existsSync(out)) {
      bad(`${a.dir} 缺少 skills/yi-divination/SKILL.md`)
      continue
    }
    const body = readFileSync(out, 'utf8')
    if (!body.startsWith(truth)) bad(`${a.dir} 的 SKILL.md 不以真源正文为前缀（正文被改动）`)
    else ok(`${a.dir} 的 SKILL.md 正文与真源逐字同源${a.skill ? '（+ 宿主附加段）' : ''}`)
    const front = /^---\r?\n([\s\S]*?)\r?\n---/.exec(body)
    if (!front || !/^\s*description\s*:/mu.test(front[1])) bad(`${a.dir} 的 SKILL.md frontmatter 缺少 description`)
    else ok(`${a.dir} frontmatter 含 description`)

    let shipped = []
    try {
      for (const d of ['liuyao', 'bazi']) {
        for (const e of readdirSync(join(REPO_ROOT, a.dir, 'skills', 'yi-divination', 'references', d), { withFileTypes: true })) {
          if (e.isFile() && e.name.endsWith('.md') && e.name !== 'INDEX.md') shipped.push(`${d}/${e.name}`)
        }
      }
    } catch {
      /* 目录不存在 → 下面判红 */
    }
    shipped.sort()
    if (shipped.join('|') !== [...KB_DOC.keys()].sort().join('|')) bad(`${a.dir} 知识库篇数与登记表不符（实收 ${shipped.length}／登记 ${KB_DOC.size}）`)
    else ok(`${a.dir} 知识库 ${shipped.length} 篇与登记表一致`)
  }
  if (!existsSync(join(PLUGINS_ROOT, 'skills', 'yi-divination', 'references', 'INDEX.md'))) bad('共享层缺少 references/INDEX.md')
  else ok('共享层 references/INDEX.md 在位')
}

// ── [4] MCP 冒烟（直接跑真源） ──────────────────────────────────────────────
head(4)
let toolDefs = []
async function mcpSmoke() {
  const child = spawn(process.execPath, [join(MCP_DIR, 'server.mjs')], {
    cwd: PLUGINS_ROOT,
    windowsHide: true,
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env },
  })
  let buffer = ''
  const pending = new Map()
  let id = 0
  const request = (method, params) =>
    new Promise((res, rej) => {
      const myId = ++id
      pending.set(myId, { res, rej })
      child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: myId, method, params }) + '\n')
      setTimeout(() => {
        if (pending.has(myId)) {
          pending.delete(myId)
          rej(new Error(`${method} 超时`))
        }
      }, 30000)
    })
  child.stdout.setEncoding('utf8')
  child.stdout.on('data', (chunk) => {
    buffer += chunk
    let nl
    while ((nl = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, nl)
      buffer = buffer.slice(nl + 1)
      try {
        const msg = JSON.parse(line)
        if (pending.has(msg.id)) {
          const p = pending.get(msg.id)
          pending.delete(msg.id)
          p.res(msg)
        }
      } catch {
        /* 脏行忽略 */
      }
    }
  })
  child.stderr.on('data', () => {})
  try {
    const init = await request('initialize', { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'selftest', version: '1.0.0' } })
    child.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized', params: {} }) + '\n')
    if (init?.result?.protocolVersion === '2025-03-26') ok('initialize 返回 2025-03-26（跑的是真源 plugins/mcp/server.mjs）')
    else bad(`initialize 返回异常：${JSON.stringify(init).slice(0, 200)}`)

    const list = await request('tools/list', {})
    toolDefs = list?.result?.tools ?? []
    if (FROZEN_TOOLS.every((n) => toolDefs.some((t) => t.name === n))) ok(`tools/list 四工具在列：${toolDefs.map((t) => t.name).sort().join(', ')}`)
    else bad(`tools/list 工具集不符：${toolDefs.map((t) => t.name).join(', ')}`)

    const kb = await request('tools/call', { name: 'yi_kb', arguments: { query: '用神 取法', limit: 3 } })
    const v = kb?.result?.structuredContent
    if (kb?.result?.isError === true) bad(`yi_kb 失败：${kb?.result?.content?.[0]?.text ?? ''}`)
    else if ((v?.matches ?? []).length && String(v.matches[0].resource ?? '').startsWith('resource:kb-')) ok(`yi_kb 命中 ${v.matches.length} 条，首条 resource=${v.matches[0].resource}`)
    else bad(`yi_kb 返回异常：${JSON.stringify(v).slice(0, 200)}`)

    const py = process.env.DSH_PYTHON || process.env.YI_PYTHON || findPythonOnPath()
    if (!py) note('未找到 Python，跳过 yi_liuyao 引擎冒烟（插件在用户机器上同样会如实报错）')
    else {
      const cast = await request('tools/call', { name: 'yi_liuyao', arguments: { question: '自检冒烟：某事如何', mode: 'coin', seed: 42 } })
      if (cast?.result?.isError === true) bad(`yi_liuyao 引擎冒烟失败：${cast?.result?.content?.[0]?.text ?? ''}`)
      else if (cast?.result?.structuredContent?.original_hexagram?.name) ok(`yi_liuyao 引擎冒烟通过：${cast.result.structuredContent.original_hexagram.name}（Python ${py}）`)
      else bad(`yi_liuyao 返回缺少卦名：${JSON.stringify(cast?.result).slice(0, 200)}`)
    }
  } catch (err) {
    bad(`MCP 冒烟异常：${err?.message ?? err}`)
  } finally {
    child.stdin.end()
    child.kill()
  }
}
function findPythonOnPath() {
  const sep = process.platform === 'win32' ? ';' : ':'
  for (const name of ['python', 'python3']) {
    for (const dir of (process.env.PATH ?? '').split(sep).filter(Boolean)) {
      for (const ext of process.platform === 'win32' ? ['.exe', ''] : ['']) {
        const p = join(dir, name + ext)
        if (existsSync(p)) return p
      }
    }
  }
  return null
}
await mcpSmoke()

// ── [5] 工具契约 ────────────────────────────────────────────────────────────
head(5)
{
  const byName = new Map(toolDefs.map((t) => [t.name, t]))
  for (const n of FROZEN_TOOLS) {
    const t = byName.get(n)
    if (!t) {
      bad(`冻结工具缺失：${n}`)
      continue
    }
    if (t?.inputSchema?.type !== 'object') bad(`${n} 的 inputSchema.type 不是 object（MCP 宿主会拒收）`)
  }
  if (toolDefs.length === FROZEN_TOOLS.length && toolDefs.every((t) => t?.inputSchema?.type === 'object')) {
    ok(`四工具 inputSchema 均为 object，且数量恰为冻结面 ${FROZEN_TOOLS.length}`)
  }
  const liuyao = byName.get('yi_liuyao')
  const keys = Object.keys(liuyao?.inputSchema?.properties ?? {}).sort().join(',')
  if (keys === 'datetime,gender,mode,numbers,question,seed,yao') ok('yi_liuyao 参数集与 1.0 冻结面一致')
  else bad(`yi_liuyao 参数集变了：${keys}（改冻结面必须同时改 AGENTS.md §二）`)
}

// ── [6] 适配器清单与包体 ────────────────────────────────────────────────────
head(6)
{
  const ID_RE = /^[a-z][a-z0-9-]{0,47}$/
  const SEMVER_RE = /^\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?$/
  for (const a of ADAPTERS) {
    const root = join(REPO_ROOT, a.dir)
    const files = walk(root)
    const bytes = files.reduce((s, f) => s + f.bytes, 0)
    if (files.length > 4000) bad(`${a.dir} 文件数 ${files.length} 超上限 4000`)
    if (bytes > 64 * 1024 * 1024) bad(`${a.dir} 包体 ${(bytes / 1048576).toFixed(2)}MB 超上限 64MB`)
    if (files.some((f) => f.symlink)) bad(`${a.dir} 含符号链接（宿主拒收）`)
    if (files.length && files.length <= 4000 && bytes <= 64 * 1024 * 1024 && !files.some((f) => f.symlink)) {
      ok(`${a.dir} 包体 ${files.length} 文件 / ${(bytes / 1048576).toFixed(2)}MB，无符号链接`)
    }

    if (!a.manifest) continue
    let m = null
    try {
      m = JSON.parse(readFileSync(join(root, a.manifest), 'utf8'))
    } catch (err) {
      bad(`${a.dir}/${a.manifest} 读不出来：${err?.message ?? err}`)
      continue
    }
    /** 每家的清单规则与 MCP 声明面都不同，按宿主分流（不要写成一个 if-else 链）。 */
    const MANIFEST_RULES = {
      claude: [
        ['name 为稳定 kebab-case 标识', /^[a-z][a-z0-9-]*$/.test(m.name ?? '')],
        ['version 符合 semver', SEMVER_RE.test(m.version ?? '')],
        ['description 非空', !!m.description],
        ['清单里不放组件（组件必须在插件根）', Object.keys(m).every((k) => !['skills', 'commands', 'agents', 'hooks', 'mcpServers'].includes(k))],
        ['skills/yi-divination/SKILL.md 在位', existsSync(join(root, 'skills', 'yi-divination', 'SKILL.md'))],
      ],
      codex: [
        ['name 为 kebab-case（同时是命名空间与缓存键）', /^[a-z][a-z0-9-]*$/.test(m.name ?? '')],
        ['version 符合 semver', SEMVER_RE.test(m.version ?? '')],
        ['skills 指针为 ./skills/', m.skills === './skills/'],
        ['mcpServers 指针为 ./.mcp.json', m.mcpServers === './.mcp.json'],
        ['skills/yi-divination/SKILL.md 在位', existsSync(join(root, 'skills', 'yi-divination', 'SKILL.md'))],
      ],
      gemini: [
        ['name 小写短横线（并应与扩展目录同名）', /^[a-z0-9-]+$/.test(m.name ?? '')],
        ['version 符合 semver', SEMVER_RE.test(m.version ?? '')],
        ['contextFileName 指向包内 GEMINI.md', m.contextFileName === 'GEMINI.md' && existsSync(join(root, 'GEMINI.md'))],
      ],
      yan: [
        ['schemaVersion === 1', m.schemaVersion === 1],
        ['id 合法', ID_RE.test(m.id ?? '')],
        ['version 符合 semver', SEMVER_RE.test(m.version ?? '')],
        ['instructions 指向包内文件', typeof m.instructions === 'string' && existsSync(join(root, m.instructions))],
        ['mcpServers 恰 1 条 local + $node', m.mcpServers?.length === 1 && m.mcpServers[0].type === 'local' && m.mcpServers[0].command === '$node'],
      ],
    }
    for (const [label, pass] of MANIFEST_RULES[a.id] ?? []) (pass ? ok : bad)(`${a.dir}: ${label}`)

    /**
     * MCP 声明面：各家变量不同（${CLAUDE_PLUGIN_ROOT} / ${CODEX_PLUGIN_ROOT} /
     * ${extensionPath} / 清单内联）。**写死绝对路径换台机器就指不到包内入口**，
     * 故各自断言自己的变量在位，并做一次替换负例自证。
     */
    const MCP_SPEC = {
      claude: { file: '.mcp.json', varName: '${CLAUDE_PLUGIN_ROOT}' },
      codex: { file: '.mcp.json', varName: '${CODEX_PLUGIN_ROOT}' },
      gemini: { file: 'gemini-extension.json', varName: '${extensionPath}', inline: true },
    }
    const spec = MCP_SPEC[a.id]
    if (spec) {
      let mcp = null
      try {
        mcp = JSON.parse(readFileSync(join(root, spec.file), 'utf8'))
      } catch (err) {
        bad(`${a.dir}/${spec.file} 读不出来：${err?.message ?? err}`)
      }
      const server = mcp?.mcpServers?.yi
      const args = (server?.args ?? []).join(' ')
      const checks2 = [
        ['存在 yi 服务', !!server],
        ['command 为 node', server?.command === 'node'],
        [`args 用 ${spec.varName} 定位入口`, args.includes(spec.varName)],
        ['入口指向包内 src/server.mjs', args.includes('src/server.mjs')],
      ]
      for (const [label, pass] of checks2) (pass ? ok : bad)(`${a.dir}: ${label}`)
      const badArgs = args.replace(spec.varName, 'C:/Users/someone/yi')
      if (badArgs !== args && !badArgs.includes(spec.varName)) ok(`${a.dir}: 负例自证（路径写死即被判红）成立`)
      else bad(`${a.dir}: 负例自证失败（换掉 ${spec.varName} 后仍未判红）`)
    }

    if (!a.reconcileResources) continue

    // resources 双向对账（resource:kb-* 句柄必须与实收文件同式）
    const declared = new Map((m.resources ?? []).map((r) => [r.path, r.id]))
    const reconcile = (rels) => {
      const problems = []
      for (const rel of rels) {
        const path = `skills/yi-divination/references/${rel}`
        const want = resourceIdFor(rel).replace(/^resource:/u, '')
        if (!declared.has(path)) problems.push(`未登记资源：${path}`)
        else if (declared.get(path) !== want) problems.push(`资源 id 不符：${path} 记为 ${declared.get(path)}，应为 ${want}`)
      }
      for (const path of declared.keys()) {
        if (!rels.some((rel) => `skills/yi-divination/references/${rel}` === path)) problems.push(`登记了不存在的资源：${path}`)
      }
      return problems
    }
    const kbFiles = ['INDEX.md', ...KB_DOC.keys()]
    const problems = reconcile(kbFiles)
    if (problems.length) for (const p of problems) bad(`${a.dir}: ${p}`)
    else ok(`${a.dir}: resources 与实收知识库双向一致（${kbFiles.length} 条）`)

    // 负例自证：a) 抽掉一篇 → 多出「登记了不存在的资源」；b) 多塞一篇 → 「未登记资源」
    const probeA = reconcile(['INDEX.md', ...[...KB_DOC.keys()].slice(1)])
    const probeB = reconcile(['INDEX.md', ...KB_DOC.keys(), 'liuyao/__no_such_probe.md'])
    if (probeA.length === 1 && /登记了不存在的资源/u.test(probeA[0])) ok(`${a.dir}: 负例自证 a（抽掉一篇即报红）成立`)
    else bad(`${a.dir}: 负例自证 a 失败（报红 ${probeA.length} 条，应为 1 条「登记了不存在的资源」）`)
    if (probeB.length === 1 && /未登记资源/u.test(probeB[0])) ok(`${a.dir}: 负例自证 b（多塞一篇即报红）成立`)
    else bad(`${a.dir}: 负例自证 b 失败（报红 ${probeB.length} 条，应为 1 条「未登记资源」）`)
  }
}

// ── [7] 口径诚实 ────────────────────────────────────────────────────────────
head(7)
{
  const FORBIDDEN = [/预测准确率/u, /预测率/u, /断事如神/u, /命中率\s*\d/u]
  /**
   * 逐行扫描 + **否定语境豁免**。本仓对外文书里「预测准确率」几乎只出现在自己禁令
   * 的那句话里（「不得说预测准确率 X%」），整文件匹配会把立规矩的那只手判成违规
   * （304 批首跑即误伤）。豁免面刻意做窄：同一行有明确否定标记才算禁止语境。
   */
  const NEGATION = /(不得|禁止|不许|不可|切勿|❌|不是|并非|而非|杜绝|避免)/u
  const scan = (text) => {
    const hits = []
    text.split(/\r?\n/u).forEach((line, i) => {
      for (const re of FORBIDDEN) if (re.test(line) && !NEGATION.test(line)) hits.push(`第 ${i + 1} 行：${line.trim().slice(0, 80)}`)
    })
    return hits
  }
  const targets = [
    join(PLUGINS_ROOT, 'SKILL.md'),
    ...ADAPTERS.flatMap((a) => [join(REPO_ROOT, a.dir, 'README.md'), join(REPO_ROOT, a.dir, 'INSTRUCTIONS.md')]),
    join(REPO_ROOT, 'README.md'),
    join(REPO_ROOT, 'CAPABILITY.md'),
    join(MCP_DIR, 'tools.mjs'),
  ].filter((p) => existsSync(p))
  let clean = true
  for (const p of targets) {
    for (const hit of scan(readFileSync(p, 'utf8'))) {
      bad(`${p.replace(REPO_ROOT + '\\', '')} ${hit}`)
      clean = false
    }
  }
  const probeDir = mkdtempSync(join(tmpdir(), 'yi-forbid-probe-'))
  const probeFile = join(probeDir, '_probe.md')
  writeFileSync(probeFile, '本工具预测准确率 99%')
  const caught = FORBIDDEN.some((re) => re.test(readFileSync(probeFile, 'utf8')))
  rmSync(probeDir, { recursive: true, force: true })
  if (!caught) bad('负例自证失败：禁语扫描器抓不到明知存在的禁语')
  else if (clean) ok(`对外文本与工具描述无禁语（扫了 ${targets.length} 处）＋负例自证通过`)
}

console.log('\n' + '─'.repeat(60))
if (fails.length) {
  console.log(`自检判红：${fails.length} 项`)
  for (const f of fails) console.log('  ×', f)
  process.exitCode = 1
} else {
  console.log('自检全绿')
}
for (const n of notes) console.log('  ·（提示）', n)
