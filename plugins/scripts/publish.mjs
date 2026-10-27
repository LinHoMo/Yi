#!/usr/bin/env node
/**
 * 生成**发布树** `plugins/dist/`（构建产物，不入库），供各家 git 通道消费。
 *
 * 为什么需要这一步（307 批的核心动因）：
 *   `engine/`、`skills/`、`src/` 按仓库纪律**不入库**，而 Claude Code / Codex /
 *   Gemini CLI / Yan 的远程分发走的都是 **git**（拉取已提交文件）。
 *   于是「源仓 + 产物不入库」与「远程安装」在结构上互斥——
 *   304～306 批四家全部只能本地安装，根源就在这里。
 *
 * 解法：把「源」与「发行」分离。本脚本产出一棵**只含可安装产物**的树，
 *   由它单独成为一个 git 仓库/分支被各家拉取；源仓继续维持"产物不入库"的纪律。
 *
 * 用法：
 *   node plugins/scripts/publish.mjs           # 生成 plugins/dist/
 *   node plugins/scripts/publish.mjs --check   # 只校验已生成的树（不重写）
 *
 * ⚠ 本脚本**只生成文件，不 commit、不 push、不建远程**——那是外部动作，
 *   由用户在看清楚产物后自己执行（末尾会打印确切命令）。
 */
import { cp, mkdir, readFile, rm, stat, writeFile, readdir } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { KB_DOC } from './kb-docs.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const PLUGINS_ROOT = resolve(HERE, '..')
const REPO_ROOT = resolve(PLUGINS_ROOT, '..')
const DIST = join(PLUGINS_ROOT, 'dist')

/** 与 build.mjs 的 ADAPTERS 同序；这里只声明「dist 里要不要、叫什么」。 */
const ADAPTERS = [
  { id: 'dsh', dir: 'dsh-plugin', install: 'dsh plugin --profile <profile> add "link:./dsh-plugin"' },
  { id: 'claude', dir: 'claude-plugin', install: '/plugin marketplace add <owner/yi-plugins>  →  /plugin install yi' },
  { id: 'codex', dir: 'codex-plugin', install: '在 $REPO_ROOT/.agents/plugins/marketplace.json 登记后 codex plugins install' },
  { id: 'gemini', dir: 'gemini-plugin', install: 'gemini extensions install <git url>' },
  { id: 'yan', dir: 'yan-plugin', install: 'Yan 插件市场添加来源 <git url>，稀疏路径填 yan-plugin' },
]

/** 不进发布树的东西（源仓的开发残留）。 */
const JUNK = /(__pycache__|\.pyc$|\.pyo$|\.pytest_cache|\.mypy_cache|\.tgz$|node_modules$|^\.workbuddy$)/
const SKIP_TOP = new Set(['scratch', 'node_modules', '.git', '.workbuddy'])

/** 各家需要的"入口文件"，[check] 段逐一断言其在位。 */
const ENTRY_FILES = {
  dsh: ['package.json', 'src/index.mjs'],
  claude: ['.claude-plugin/plugin.json', '.mcp.json'],
  codex: ['.codex-plugin/plugin.json', '.mcp.json'],
  gemini: ['gemini-extension.json', 'GEMINI.md'],
  yan: ['yan-plugin.json', 'INSTRUCTIONS.md'],
}

async function copyPlugin(dir) {
  const src = join(REPO_ROOT, dir)
  const dest = join(DIST, dir)
  await rm(dest, { recursive: true, force: true })
  await mkdir(dest, { recursive: true })
  const entries = await readdir(src, { withFileTypes: true })
  for (const e of entries) {
    if (SKIP_TOP.has(e.name) || JUNK.test(e.name)) continue
    await cp(join(src, e.name), join(dest, e.name), {
      recursive: e.isDirectory(),
      filter: (p) => !JUNK.test(p),
    })
  }
  console.log(`[publish] ${dir} → dist/${dir}`)
}

async function writeRootFiles() {
  await writeFile(join(DIST, 'LICENSE'), await readFile(join(REPO_ROOT, 'LICENSE'), 'utf8'), 'utf8')

  // Claude 市场目录（仓库根）——插件指向同仓子目录。
  // ⚠ 未真机验证：Claude 的 marketplace.json 能否把 source 指到同仓子目录，
  //    官方文档示例是「市场仓 → 独立插件仓」。真机跑通前请以 --plugin-dir 为准。
  await mkdir(join(DIST, '.claude-plugin'), { recursive: true })
  await writeFile(
    join(DIST, '.claude-plugin', 'marketplace.json'),
    JSON.stringify(
      {
        _note: '本目录**未真机验证**：Claude Code 的市场条目通常指向独立插件仓库，此处改为指向同仓子目录，需实测确认。未跑通前请用 claude --plugin-dir ./claude-plugin 本地试装。',
        name: 'yi-plugins',
        owner: { name: 'Yi contributors' },
        plugins: [
          {
            name: 'yi',
            source: { source: 'url', url: 'https://github.com/LinHoMo/yi-plugins.git' },
            path: './claude-plugin',
            description: '六爻纳甲与八字四柱的确定性排盘与解读（随包 Python 引擎）',
            version: '1.0.0',
          },
        ],
      },
      null,
      2,
    ) + '\n',
    'utf8',
  )

  // Codex 仓库级市场（$REPO_ROOT/.agents/plugins/marketplace.json）
  await mkdir(join(DIST, '.agents', 'plugins'), { recursive: true })
  await writeFile(
    join(DIST, '.agents', 'plugins', 'marketplace.json'),
    JSON.stringify(
      {
        name: 'yi-plugins',
        'interface.displayName': 'Yi 术数',
        plugins: [
          {
            name: 'yi',
            source: { source: 'local', path: './codex-plugin' },
            policy: { installation: 'AVAILABLE', authentication: 'ON_FIRST_USE' },
            category: 'Utilities',
          },
        ],
      },
      null,
      2,
    ) + '\n',
    'utf8',
  )

  // Gemini：把仓库根本身做成一个扩展，MCP 入口指进子目录
  // （Gemini CLI 一个仓库 = 一个扩展，故不能像 Claude/Codex 那样用市场目录）
  await writeFile(
    join(DIST, 'gemini-extension.json'),
    JSON.stringify(
      {
        name: 'yi-plugins',
        version: '1.0.0',
        description: '六爻纳甲与八字四柱的确定性排盘与解读（随包 Python 引擎）。',
        mcpServers: {
          yi: {
            command: 'node',
            args: ['${extensionPath}/gemini-plugin/src/server.mjs'],
            cwd: '${extensionPath}/gemini-plugin',
          },
        },
        contextFileName: 'GEMINI.md',
      },
      null,
      2,
    ) + '\n',
    'utf8',
  )
  await writeFile(join(DIST, 'GEMINI.md'), await readFile(join(REPO_ROOT, 'gemini-plugin', 'GEMINI.md'), 'utf8'), 'utf8')

  // Yan：无需目录文件，它会遍历树找 yan-plugin.json；只需别把别的清单挡住。
  const readme = [
    '# Yi 术数插件发行树',
    '',
    '本仓库只放**可安装的产物**（含随包 Python 引擎与判据知识库）。它是自动生成物，',
    '**不要手工编辑**——源在 [LinHoMo/Yi](https://github.com/LinHoMo/Yi) 的 `plugins/`，',
    '由 `plugins/scripts/publish.mjs` 生成。',
    '',
    '古籍案例库按隔离纪律**永不随包**；库内一切分数是古籍案例对齐分，不是现实命中率。',
    '',
    '## 各宿主怎么装',
    '',
    '| 宿主 | 目录 | 安装 |',
    '|---|---|---|',
    ...ADAPTERS.map((a) => `| ${a.id} | \`${a.dir}/\` | ${a.install} |`),
    '',
    '需要本机 **Python 3.10+**（引擎是 Python）与 **node**（MCP 入口）。',
    '',
    '> ⚠ Claude 的市场条目（`.claude-plugin/marketplace.json`）**未真机验证**：',
    '> 官方示例是「市场仓 → 独立插件仓」，这里改指同仓子目录。',
    '> 未跑通前请用 `claude --plugin-dir ./claude-plugin` 本地试装。',
    '',
  ].join('\n')
  await writeFile(join(DIST, 'README.md'), readme, 'utf8')
  console.log('[publish] 根文件：README.md / LICENSE / marketplace 目录 / gemini-extension.json')
}

/** --check：发布树是否真的「装了即用」。 */
async function check() {
  const fails = []
  const okList = []
  const missingOf = (root, rels) => rels.filter((rel) => !existsSync(join(root, ...rel.split('/'))))
  for (const a of ADAPTERS) {
    const root = join(DIST, a.dir)
    const rels = [...ENTRY_FILES[a.id], 'src/server.mjs', 'engine/MANIFEST.json', 'skills/yi-divination/SKILL.md', 'engine/liuyao/scripts/chart.py']
    const missing = missingOf(root, rels)
    if (missing.length) for (const m of missing) fails.push(`${a.dir} 缺少 ${m}`)
    else okList.push(`${a.dir} 自包含（清单 + MCP 入口 + engine + skills 齐备）`)
  }
  // 负例自证：塞一个明知不存在的入口，检查器必须抓到
  {
    const probe = missingOf(join(DIST, 'claude-plugin'), ['.mcp.json', 'src/__no_such_probe.mjs'])
    if (probe.length === 1 && probe[0] === 'src/__no_such_probe.mjs') okList.push('负例自证：多塞一个缺失入口即被抓到（门不是瞎的）')
    else fails.push(`负例自证失败：应抓到 1 条，实得 ${probe.length}`)
  }
  // 案例库零随包（发布树同样受铁律二约束）
  let hits = []
  async function walk(dir, base = '') {
    for (const e of await readdir(dir, { withFileTypes: true })) {
      const rel = base ? `${base}/${e.name}` : e.name
      if (e.name === 'case_library.md') hits.push(rel)
      else if (e.isDirectory()) await walk(join(dir, e.name), rel)
    }
  }
  if (existsSync(DIST)) await walk(DIST)
  if (hits.length) fails.push(`发布树含 case_library.md：${hits.join(', ')}`)
  else okList.push('发布树无 case_library.md')

  // 知识库篇数
  const kbDir = join(DIST, 'yan-plugin', 'skills', 'yi-divination', 'references')
  let n = 0
  if (existsSync(kbDir)) {
    for (const d of ['liuyao', 'bazi']) {
      try {
        n += (await readdir(join(kbDir, d))).filter((f) => f.endsWith('.md')).length
      } catch {
        /* 缺目录即判红 */
      }
    }
  }
  if (n !== KB_DOC.size) fails.push(`发布树知识库 ${n} 篇 ≠ 登记表 ${KB_DOC.size} 篇`)
  else okList.push(`发布树知识库 ${n} 篇与登记表一致`)

  console.log('\n[publish --check]')
  for (const l of okList) console.log('  √', l)
  if (fails.length) {
    for (const f of fails) console.log('  ×', f)
    process.exitCode = 1
  } else {
    console.log('  发布树可安装性检查全绿')
  }
}

async function main() {
  if (process.argv.includes('--check')) {
    await check()
    return
  }
  if (!existsSync(join(REPO_ROOT, 'yan-plugin', 'engine'))) {
    console.error('[publish] 产物缺失：先跑 node plugins/scripts/build.mjs')
    process.exitCode = 1
    return
  }
  await rm(DIST, { recursive: true, force: true })
  await mkdir(DIST, { recursive: true })
  for (const a of ADAPTERS) await copyPlugin(a.dir)
  await writeRootFiles()
  await check()

  console.log('\n生成完毕：' + DIST)
  console.log('发布（外部动作，需你自己执行，看清产物再跑）：')
  console.log('  # 方案 A：独立发行仓（推荐，各家默认分支即可消费）')
  console.log('  cp -r plugins/dist/. ../yi-plugins/ && cd ../yi-plugins && git init && git add -A && git commit -m "Yi plugins dist" && git remote add origin <你的发行仓> && git push -u origin main')
  console.log('  # 方案 B：同仓发行分支')
  console.log('  git worktree add -B plugins-dist .worktrees/dist && cp -r plugins/dist/. .worktrees/dist/ && cd .worktrees/dist && git add -A && git commit -m "Yi plugins dist" && git push origin plugins-dist')
}

main().catch((err) => {
  console.error('[publish] 失败:', err)
  process.exitCode = 1
})
