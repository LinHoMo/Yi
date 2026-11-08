#!/usr/bin/env node
/**
 * 共享层 + 宿主适配器包级自检。判红即 exit≠0，每条门须负例自证（AGENTS.md §四.8）。
 *
 *   [1]    src/*.mjs 与 plugins/mcp/ 真源逐字节同源
 *   [1.6]  engine/ 与 skills/ 产物在 plugins/ 与宿主侧全量同源
 *   [1.5]  产物内无 case_library.md
 *   [2]    两科入口齐备、评测 shim 未随包
 *   [3]    skills 正文同源 + 知识库篇数对账
 *   [4]    MCP 冒烟（直跑真源 server.mjs）
 *   [5]    1.0 冻结工具契约（四工具参数 schema 与 required）
 *   [6]    包体上限
 *   [7]    口径诚实：禁语 + 口径声明 + 报告模板提示语
 */
import { spawn } from 'node:child_process'
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { KB_DOC } from './kb-docs.mjs'
import { DEV_ONLY } from './dev-only.mjs'

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

function treeSnapshot(dir, exempt = new Set()) {
  const out = new Map()
  for (const f of walk(dir)) {
    if (f.symlink || exempt.has(f.rel)) continue
    out.set(f.rel, readFileSync(join(dir, ...f.rel.split('/'))))
  }
  return out
}

function treeDrift(truth, copy) {
  const problems = []
  if (!truth.size || !copy.size) problems.push(`扫到 0 个文件（真源 ${truth.size}／副本 ${copy.size}）`)
  for (const [rel, buf] of truth) {
    if (!copy.has(rel)) problems.push(`副本缺 ${rel}`)
    else if (!buf.equals(copy.get(rel))) problems.push(`字节不同源 ${rel}`)
  }
  for (const rel of copy.keys()) if (!truth.has(rel)) problems.push(`副本多出 ${rel}`)
  return problems
}

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

// ── [1.6] 产物全量同源 ──────────────────────────────────────────────────────
head(1.6)
{
  const host = join(REPO_ROOT, 'dsh-plugin')
  for (const [rel, exempt] of [
    ['engine', new Set()],
    ['skills', new Set(['yi-divination/SKILL.md'])],
  ]) {
    const truth = treeSnapshot(join(PLUGINS_ROOT, rel), exempt)
    const copy = treeSnapshot(join(host, rel), exempt)
    const drift = treeDrift(truth, copy)
    if (drift.length) for (const d of drift.slice(0, 8)) bad(`${rel}/ 产物漂移：${d}`)
    else ok(`${rel}/ 全量同源（${truth.size} 文件逐字节一致）`)
  }
  const probe = mkdtempSync(join(tmpdir(), 'yi-tree-probe-'))
  try {
    mkdirSync(join(probe, 'a'))
    mkdirSync(join(probe, 'b'))
    mkdirSync(join(probe, 'empty'))
    writeFileSync(join(probe, 'a', 'x.py'), 'a')
    writeFileSync(join(probe, 'b', 'x.py'), 'b')
    const snapA = () => treeSnapshot(join(probe, 'a'))
    const snapB = () => treeSnapshot(join(probe, 'b'))
    if (!treeDrift(snapA(), snapB()).length) bad('负例自证失败：改一个字节未判红')
    writeFileSync(join(probe, 'b', 'x.py'), 'a')
    if (treeDrift(snapA(), snapB()).length) bad('负例自证失败：同源被误判')
    rmSync(join(probe, 'b', 'x.py'))
    if (!treeDrift(snapA(), snapB()).length) bad('负例自证失败：副本缺文件未判红')
    if (!treeDrift(snapA(), treeSnapshot(join(probe, 'empty'))).length) bad('负例自证失败：扫到 0 文件未判红')
    else ok('负例自证：篡改／缺文件／0 文件均判红')
  } finally {
    rmSync(probe, { recursive: true, force: true })
  }
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

  // 单一真源 `./dev-only.mjs`（539 批）：此前本段与 build.mjs 各存一份手工清单，
  // 改一边忘另一边构建与自检照样全绿（528 批 G11 同型）。521 批已删光 shim，
  // 名单转为防复活哨兵；产物若带上这些入口会 `import eval` 失败（包内无 eval/）。
  const DEV_ONLY_SHIMS = Object.fromEntries(
    Object.entries(DEV_ONLY).map(([d, names]) => [d, names.map((n) => `scripts/${n}`)]),
  )
  // 登记表自身的存在性断言：空表会让 [2] 段变成「什么都不查」的假绿
  if (!DEV_ONLY_SHIMS.liuyao?.length || !DEV_ONLY_SHIMS.bazi?.length) bad('dev-only.mjs 登记表为空或漏科')
  else ok(`排除名单与 build.mjs 同源（${Object.entries(DEV_ONLY_SHIMS).map(([d, r]) => `${d}×${r.length}`).join('／')}）`)
  const evalShimsPresent = (root) => Object.entries(DEV_ONLY_SHIMS).flatMap(
    ([d, rels]) => rels
      .filter((rel) => existsSync(join(root, 'engine', d, ...rel.split('/'))))
      .map((rel) => `${d}/${rel}`))
  const roots = [PLUGINS_ROOT, ...ADAPTERS.map((a) => join(REPO_ROOT, a.dir))]
  const leaked = roots.flatMap((root) => evalShimsPresent(root).map(
    (rel) => `${root.replace(REPO_ROOT, '')}/engine/${rel}`))
  if (leaked.length) for (const m of leaked) bad(`评测 shim 不应随包：${m}`)
  else ok('两科评测 shim 未随包（liuyao×3／bazi evaluate 只在开发树）')
  const probe = mkdtempSync(join(tmpdir(), 'yi-shim-probe-'))
  try {
    mkdirSync(join(probe, 'engine', 'bazi', 'scripts'), { recursive: true })
    writeFileSync(join(probe, 'engine', 'bazi', 'scripts', 'evaluate.py'), '')
    if (evalShimsPresent(probe).length === 1) ok('负例自证：交付包里有评测 shim 会被抓到')
    else bad('负例自证失效：探针目录里的评测 shim 未被抓到')
  } finally {
    rmSync(probe, { recursive: true, force: true })
  }
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

    const py = process.env.DSH_PYTHON || findPythonOnPath()
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
  // 冻结面 = 工具名 + 参数 schema（属性集与 required）。输出 value 结构与文本块形状
  // 由 verify-in-dsh 真跑 execute()/render() 覆盖，不在此重复。
  const FROZEN_SCHEMA = {
    yi_bazi: { props: 'datetime,gender,longitude', required: 'datetime,gender' },
    yi_kb: { props: 'discipline,limit,query', required: 'query' },
    yi_liuyao: { props: 'datetime,gender,mode,numbers,question,seed,yao', required: 'question' },
    yi_report: {
      props: 'datetime,discipline,format,gender,longitude,mode,numbers,question,seed,yao',
      required: 'discipline',
    },
  }
  const shapeOf = (t) => ({
    props: Object.keys(t?.inputSchema?.properties ?? {}).sort().join(','),
    required: [...(t?.inputSchema?.required ?? [])].sort().join(','),
  })
  const drift = (defs) => Object.entries(FROZEN_SCHEMA).flatMap(([name, want]) => {
    const got = shapeOf(defs.get(name))
    return [
      ...(got.props === want.props ? [] : [`${name} 参数集变了：${got.props} ≠ ${want.props}`]),
      ...(got.required === want.required ? [] : [`${name} required 变了：${got.required} ≠ ${want.required}`]),
    ]
  })
  const bad5 = drift(byName)
  if (bad5.length) for (const d of bad5) bad(d)
  else ok('四工具参数 schema 与 required 均与 1.0 冻结面一致')
  const probe = new Map(byName)
  const kb = byName.get('yi_kb')
  probe.set('yi_kb', { ...kb, inputSchema: { ...kb?.inputSchema, required: [] } })
  if (!drift(probe).some((d) => d.startsWith('yi_kb required'))) {
    bad('负例自证失败：required 被改仍判绿')
  } else ok('负例自证：改 required 即破坏冻结面')
}

// ── [6] 适配器包体 ──────────────────────────────────────────────────────────
head(6)
{
  const bundleOk = (files) => files.length > 0
    && files.length <= 4000
    && files.reduce((s, f) => s + f.bytes, 0) <= 64 * 1024 * 1024
    && !files.some((f) => f.symlink)
  for (const a of ADAPTERS) {
    const files = walk(join(REPO_ROOT, a.dir))
    const bytes = files.reduce((s, f) => s + f.bytes, 0)
    if (!bundleOk(files)) {
      bad(`${a.dir} 包体不合格：${files.length} 文件 / ${(bytes / 1048576).toFixed(2)}MB`
        + `${files.some((f) => f.symlink) ? '／含符号链接' : ''}`)
    } else ok(`${a.dir} 包体 ${files.length} 文件 / ${(bytes / 1048576).toFixed(2)}MB，无符号链接`)
  }
  if (bundleOk([]) || bundleOk([{ bytes: 65 * 1024 * 1024, symlink: false }])) {
    bad('负例自证失败：0 文件或超限包体仍判绿')
  } else ok('负例自证：0 文件与超限包体均判红')
}

// ── [7] 口径诚实 ────────────────────────────────────────────────────────────
head(7)
{
  const FORBIDDEN = [/预测准确率/u, /预测率/u, /断事如神/u, /命中率\s*\d/u]
  const NEGATION = /(不得|禁止|不许|不可|切勿|❌|不是|并非|而非|杜绝|避免)/u
  const scan = (text) => {
    const hits = []
    text.split(/\r?\n/u).forEach((line, i) => {
      for (const re of FORBIDDEN) if (re.test(line) && !NEGATION.test(line)) hits.push(`第 ${i + 1} 行：${line.trim().slice(0, 80)}`)
    })
    return hits
  }
  const declared = [
    join(PLUGINS_ROOT, 'SKILL.md'),
    ...ADAPTERS.flatMap((a) => [join(REPO_ROOT, a.dir, 'README.md')]),
    join(REPO_ROOT, 'README.md'),
    join(REPO_ROOT, 'CAPABILITY.md'),
    join(MCP_DIR, 'tools.mjs'),
  ]
  for (const p of declared.filter((f) => !existsSync(f))) {
    bad(`对外文书缺失：${p.replace(REPO_ROOT, '')}`)
  }
  const targets = declared.filter((f) => existsSync(f))
  if (!targets.length) bad('对外文本扫描目标为 0 份——不能当通过')
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

  // [7b] 口径声明覆盖门（308 批新增）：**每一份对外文书都必须自带口径声明**
  // （「古籍案例对齐分，不是现实命中率」）。立这条门的直接原因是 304 批抓到的
  // 「诚实徽章反向失真」——一句本该示弱的话因数字过期变成了失真，而它所在的那份
  // 文档当时根本没写口径。声明到人、到文档，比只写在仓库铁律里更不容易漏。
  const CALIBER = /(古籍案例对齐分|不是现实命中率|不代表现实预测命中率|不是现实预测命中率)/u
  const docTargets = targets.filter((f) => !f.endsWith('.mjs'))
  const caliberOk = (files) => files.length > 0
    && files.every((f) => CALIBER.test(readFileSync(f, 'utf8')))
  const bare = docTargets.filter((f) => !CALIBER.test(readFileSync(f, 'utf8')))
  if (bare.length) for (const f of bare) bad(`缺口径声明：${f.replace(REPO_ROOT, '')}`)
  else if (caliberOk(docTargets)) ok(`对外文书口径声明全覆盖（${docTargets.length} 份文档）`)
  else bad('口径声明门扫了 0 份文档——不能当通过')
  if (caliberOk([])) bad('负例自证失败：0 份文档仍判绿')
  else ok('负例自证：0 份文档不会判绿')
  const probeDir2 = mkdtempSync(join(tmpdir(), 'yi-caliber-probe-'))
  const probeFile2 = join(probeDir2, '_probe.md')
  writeFileSync(probeFile2, '# 某插件\n\n装了即用。')
  const missed = !CALIBER.test(readFileSync(probeFile2, 'utf8'))
  rmSync(probeDir2, { recursive: true, force: true })
  if (missed) ok('负例自证：缺口径声明的文档会被抓到')
  else bad('负例自证失败：口径声明扫描器抓不到明知缺失的文档')

  // 报告模板是源码，不要求口径声明；但禁语与免责提示语必须逐份在位。
  const REPORT_SOURCES = [
    join(MCP_DIR, 'report.mjs'),
    join(REPO_ROOT, 'liuyao', 'scripts', 'render.py'),
    join(REPO_ROOT, 'bazi', 'scripts', 'render.py'),
  ]
  const DISCLAIMER = /专业意见为准/u
  for (const f of REPORT_SOURCES.filter((p) => !existsSync(p))) {
    bad(`报告模板缺失：${f.replace(REPO_ROOT, '')}`)
  }
  const reportFiles = REPORT_SOURCES.filter((p) => existsSync(p))
  if (!reportFiles.length) bad('报告模板扫描目标为 0 份——不能当通过')
  for (const f of reportFiles) {
    const text = readFileSync(f, 'utf8')
    for (const hit of scan(text)) bad(`${f.replace(REPO_ROOT, '')} ${hit}`)
    if (!DISCLAIMER.test(text)) bad(`报告模板缺免责提示语：${f.replace(REPO_ROOT, '')}`)
  }
  if (reportFiles.length === REPORT_SOURCES.length) {
    ok(`报告模板禁语与免责提示语全覆盖（${reportFiles.length} 份）`)
  }
  const probe3 = mkdtempSync(join(tmpdir(), 'yi-report-probe-'))
  try {
    const bare = join(probe3, '_probe.mjs')
    writeFileSync(bare, 'const x = 1\n')
    if (DISCLAIMER.test(readFileSync(bare, 'utf8'))) bad('负例自证失败：提示语扫描器恒真')
    else ok('负例自证：缺免责提示语的模板会被抓到')
  } finally {
    rmSync(probe3, { recursive: true, force: true })
  }
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
