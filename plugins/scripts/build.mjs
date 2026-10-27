#!/usr/bin/env node
/**
 * 一次构建，分发到所有宿主适配器。
 *
 * 305 批前的形态是「每个宿主一套 build」：`dsh-plugin/scripts/build-engine.mjs`
 * ＋ `build-skills.mjs`、`yan-plugin/scripts/build.mjs`，各自从两科收集一遍，
 * 各自产一份 `engine/` 与 `skills/`。那意味着 N 个宿主 = N 份产物 + N 条漂移面，
 * 而它们的白名单、排除表、登记表**本该是同一份**。
 *
 * 现在：
 *   1. 在 `plugins/` 下**只构建一次** `engine/` 与 `skills/`；
 *   2. 把 `plugins/mcp/*.mjs`（共享运行时，唯一真源）与产物**分发**到每个适配器目录。
 *
 * 适配器目录里剩下的都是**宿主专属文件**（`yan-plugin.json`、DSH 的 `src/index.mjs`、
 * `presets/`、各自的 README/CHANGELOG），不再是第二份引擎副本。
 *
 * 收录规则仍是白名单而非黑名单：新增目录不会因为「忘了排除」被悄悄打进包，
 * 只会因为「忘了收录」在自检里报红——后者是安全的失效方向。
 *
 * 用法：
 *   node plugins/scripts/build.mjs            # 全部分发
 *   node plugins/scripts/build.mjs --only yan # 只分发一个适配器（便于单宿主调试）
 */
import { cp, mkdir, readFile, readdir, rm, stat, writeFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { KB_DOC } from './kb-docs.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const PLUGINS_ROOT = resolve(HERE, '..')
const REPO_ROOT = resolve(PLUGINS_ROOT, '..')
const ENGINE_DIR = join(PLUGINS_ROOT, 'engine')
const SKILL_DIR = join(PLUGINS_ROOT, 'skills', 'yi-divination')
const MCP_DIR = join(PLUGINS_ROOT, 'mcp')
const SKILL_SOURCE = join(PLUGINS_ROOT, 'SKILL.md')

/** 每科要收进 engine 的相对路径（相对该科根目录）。 */
const RUNTIME_INCLUDE = {
  liuyao: ['core', 'scripts', 'data/rules', 'references', 'assets'],
  bazi: ['core', 'scripts', 'data/rules', 'references'],
}

/** ⛔ 铁律二：案例库永不随包（按文件名排除，三层闸之一）。 */
const NEVER_SHIP = new Set(['case_library.md'])

/** 语言运行时不需要、且会让包变大的东西。 */
const JUNK = /(__pycache__|\.pyc$|\.pyo$|\.pytest_cache|\.mypy_cache)/

/**
 * 适配器登记表。**新增宿主只在这里加一条**，其余全自动：
 *  · `dir`    —— 适配器目录（相对仓库根），即宿主安装时的包根；
 *  · `skill`  —— 技能正文是否追加宿主专属附加段（null = 与真源逐字同源）；
 *  · `rootSkill` —— 是否还要在包根放一份 SKILL.md（DSH 的 npm `files` 需要）。
 */
const ADAPTERS = [
  { id: 'dsh', dir: 'dsh-plugin', skill: null, rootSkill: true },
  {
    id: 'claude',
    dir: 'claude-plugin',
    rootSkill: false,
    skill: `

## Claude Code 侧读法（构建期附加，非真源）

本插件装在 Claude Code 的插件目录里（不在你的工作区）。按下面的方式用：

1. 技能正文即本文件；判据文档在同级 \`references/\` 下，
   先用 \`yi_kb\` 定位（返回 \`文件:行\` + 节标题 + 摘录），再用 Read 读具体那一节；
2. \`yi_kb\` 给的是相对路径，完整位置是插件目录下的
   \`skills/yi-divination/references/<文件>\`，可用 Glob 定位后 Read；
3. 工具名在本宿主下保持原名 \`yi_liuyao\` / \`yi_bazi\` / \`yi_kb\` / \`yi_report\`
   （会以 \`mcp__yi__\` 前缀出现），按名调用即可；
4. 引擎是 Python：需要本机有 Python 3.10+。找不到时工具会如实报错并列出尝试过的路径，
   可在本插件的 \`.mcp.json\` 里把 \`YI_PYTHON\` 填成 python 的绝对路径。

其余一切（铁律、工作流、边界、口径）各宿主同文，以真源 \`plugins/SKILL.md\` 为准。
`,
  },
  {
    id: 'codex',
    dir: 'codex-plugin',
    rootSkill: false,
    skill: `

## Codex 侧读法（构建期附加，非真源）

1. 判据文档在同级 \`references/\` 下；先用 \`yi_kb\` 定位（返回 \`文件:行\` + 节标题 + 摘录），
   再读具体那一节，不要整篇读；\`references/INDEX.md\` 是总路由表。
2. 工具名在本宿主下带 \`mcp__yi__\` 前缀，原名仍是
   \`yi_liuyao\` / \`yi_bazi\` / \`yi_kb\` / \`yi_report\`，按名调用即可。
3. 引擎是 Python：需要本机 Python 3.10+。找不到时工具如实报错并列出尝试过的路径，
   可在 \`.mcp.json\` 的 \`env.YI_PYTHON\` 填 python 的绝对路径。

其余一切（铁律、工作流、边界、口径）各宿主同文，以真源 \`plugins/SKILL.md\` 为准。
`,
  },
  {
    id: 'gemini',
    dir: 'gemini-plugin',
    rootSkill: false,
    skill: `

## Gemini CLI 侧读法（构建期附加，非真源）

本扩展没有技能目录机制，入口说明在包根的 \`GEMINI.md\`。判据文档仍在
同级 \`references/\` 下：先用 \`yi_kb\` 定位（返回 \`文件:行\` + 节标题 + 摘录），
再读具体那一节；\`references/INDEX.md\` 是总路由表。

引擎是 Python：需要本机 Python 3.10+ 与 node。找不到时工具如实报错。

其余一切（铁律、工作流、边界、口径）各宿主同文，以真源 \`plugins/SKILL.md\` 为准。
`,
  },
  {
    id: 'yan',
    dir: 'yan-plugin',
    rootSkill: false,
    skill: `

## Yan 侧读法（构建期附加，非真源）

本技能在 Yan 里是**插件资源**，不在你的工作区里，\`read\` 读不到。按下面的句柄读：

1. \`yi_kb\` 检索后，每条结果都带 \`resource\` 句柄（如 \`resource:kb-liuyao-najia-rules\`）；
2. 用 \`plugins_read_resource\` 读该句柄，再按返回的 \`line\` 只读那一节；
3. 总路由表是 \`resource:kb-index\`（即 \`references/INDEX.md\`）。

工具名在 Yan 里会被宿主改写成 \`t_<hash>\`，但**原名不变**：描述里写着的
\`yi_liuyao\` / \`yi_bazi\` / \`yi_kb\` / \`yi_report\` 就是它们，按名调用即可。

其余一切（铁律、工作流、边界、口径）各宿主同文，以真源 \`plugins/SKILL.md\` 为准。
`,
  },
]

/** 由构建分发、因此**不属于**任何适配器源码的共享文件名（清理旧副本用）。 */
const SHARED_MCP_FILES = [
  'engine.mjs',
  'kb.mjs',
  'kb-synonyms.json',
  'python.mjs',
  'report.mjs',
  'schema.mjs',
  'server.mjs',
  'tools.mjs',
]

async function copyTree(from, to, { excludeNames = null } = {}) {
  await cp(from, to, {
    recursive: true,
    filter: (src) => {
      if (JUNK.test(src)) return false
      if (excludeNames) {
        const base = src.split(/[\\/]/u).pop() ?? ''
        if (excludeNames.has(base)) return false
      }
      return true
    },
  })
}

/** 1) engine/：从两科现场收集（只此一次）。 */
async function buildEngine() {
  await rm(ENGINE_DIR, { recursive: true, force: true })
  await mkdir(ENGINE_DIR, { recursive: true })
  const manifest = { builtAt: new Date().toISOString(), source: 'plugins/scripts/build.mjs', disciplines: {} }

  for (const [discipline, includes] of Object.entries(RUNTIME_INCLUDE)) {
    const srcRoot = join(REPO_ROOT, discipline)
    const destRoot = join(ENGINE_DIR, discipline)
    await mkdir(destRoot, { recursive: true })

    for (const rel of includes) {
      if (!existsSync(join(srcRoot, rel))) continue
      await copyTree(join(srcRoot, rel), join(destRoot, rel), {
        excludeNames: rel === 'references' ? NEVER_SHIP : null,
      })
    }

    let jsonNames = []
    try {
      jsonNames = (await readdir(join(srcRoot, 'data'), { withFileTypes: true }))
        .filter((e) => e.isFile() && e.name.endsWith('.json'))
        .map((e) => e.name)
    } catch {
      /* 该科无 data/ 不算错误 */
    }
    if (jsonNames.length) {
      await mkdir(join(destRoot, 'data'), { recursive: true })
      for (const name of jsonNames) await cp(join(srcRoot, 'data', name), join(destRoot, 'data', name))
    }
    for (const doc of ['SKILL.md', 'README.md']) {
      try {
        await cp(join(srcRoot, doc), join(destRoot, doc))
      } catch {
        /* 某科没有该文件不算错误 */
      }
    }
    manifest.disciplines[discipline] = { includes, dataJson: jsonNames }
  }

  await writeFile(join(ENGINE_DIR, 'MANIFEST.json'), JSON.stringify(manifest, null, 2) + '\n', 'utf8')
  console.log('[build] engine（一次）→', ENGINE_DIR)
  for (const [d, v] of Object.entries(manifest.disciplines)) {
    console.log(`   ${d}: ${v.includes.join(', ')} + data/*.json(${v.dataJson.length})`)
  }
}

/** 2) skills/：正文真源 + 知识库 + INDEX（只此一次）。 */
async function buildSkills() {
  await rm(SKILL_DIR, { recursive: true, force: true })
  await mkdir(SKILL_DIR, { recursive: true })

  const body = (await readFile(SKILL_SOURCE, 'utf8')).replace(/\s*$/u, '')
  await writeFile(join(SKILL_DIR, 'SKILL.md'), body + '\n', 'utf8')

  const shipped = []
  for (const discipline of ['liuyao', 'bazi']) {
    const dest = join(SKILL_DIR, 'references', discipline)
    await mkdir(dest, { recursive: true })
    let entries
    try {
      entries = await readdir(join(REPO_ROOT, discipline, 'references'), { withFileTypes: true })
    } catch {
      continue
    }
    for (const e of entries) {
      if (!e.isFile() || !e.name.endsWith('.md') || NEVER_SHIP.has(e.name)) continue
      await cp(join(REPO_ROOT, discipline, 'references', e.name), join(dest, e.name))
      shipped.push(`${discipline}/${e.name}`)
    }
  }

  // 双向闸门：漏登记 / 登记了不存在的文件 → 构建即红（负例纪律 AGENTS.md §四.8）
  const missing = shipped.filter((s) => !KB_DOC.has(s))
  const stale = [...KB_DOC.keys()].filter((s) => !shipped.includes(s))
  if (missing.length || stale.length) {
    if (missing.length) console.error('[build] 失败：以下知识库文件未登记 KB_DOC（plugins/scripts/kb-docs.mjs）：\n  ' + missing.join('\n  '))
    if (stale.length) console.error('[build] 失败：KB_DOC 登记了已不随包的文件：\n  ' + stale.join('\n  '))
    process.exitCode = 1
    return null
  }

  const sizes = new Map()
  for (const s of shipped) {
    sizes.set(s, Math.max(1, Math.round((await stat(join(SKILL_DIR, 'references', s))).size / 1024)) + 'KB')
  }
  const handle = (s) => s.replace(/\.md$/u, '').replace(/[^a-zA-Z0-9]+/gu, '-').replace(/^-+|-+$/gu, '').toLowerCase()
  const row = (s) => `| \`${s.split('/')[1]}\`（${sizes.get(s)}） | \`resource:kb-${handle(s)}\` | ${KB_DOC.get(s)} |`
  const rows = (d) => [...KB_DOC.keys()].filter((s) => s.startsWith(d + '/')).map(row)
  const index = [
    '# Yi 知识库索引',
    '',
    '按需读取：先看这一行判断该读哪篇，再按句柄读具体文件。**不要整本读**——',
    `单篇最大 ${Math.max(...shipped.map((s) => parseInt(sizes.get(s))))}KB，读错一篇就白占一大块上下文。`,
    '',
    '懒得挑篇时用 `yi_kb` 检索（返回 文件:行 + resource 句柄 + 节标题 + 摘录），先定位再读节段。',
    '',
    '## 六爻（references/liuyao/）',
    '',
    '| 文件 | resource 句柄 | 什么时候读 |',
    '|---|---|---|',
    ...rows('liuyao'),
    '',
    '## 八字（references/bazi/）',
    '',
    '| 文件 | resource 句柄 | 什么时候读 |',
    '|---|---|---|',
    ...rows('bazi'),
    '',
    '## ⛔ 不在此目录的内容',
    '',
    '古籍案例库（`case_library.md`）**刻意不随包发货**。按 AGENTS.md §一.2 铁律二，',
    '案例库与解读必须物理隔离：断卦时不得联想、引用或类比历史案例。',
    '',
  ].join('\n')
  await writeFile(join(SKILL_DIR, 'references', 'INDEX.md'), index, 'utf8')

  console.log('[build] skills（一次）→', SKILL_DIR, `｜知识库 ${shipped.length} 篇 + INDEX.md`)
  return { body, shipped }
}

/** 3) 分发：把共享运行时与产物复制到每个适配器目录。 */
async function distribute(adapter, skillBody) {
  const root = join(REPO_ROOT, adapter.dir)
  if (!existsSync(root)) {
    console.error(`[build] 适配器目录不存在：${adapter.dir}`)
    process.exitCode = 1
    return
  }

  // engine / skills（skills 的 SKILL.md 可能带宿主附加段，故逐文件复制后再覆写正文）
  await rm(join(root, 'engine'), { recursive: true, force: true })
  await cp(ENGINE_DIR, join(root, 'engine'), { recursive: true })
  await rm(join(root, 'skills'), { recursive: true, force: true })
  await cp(join(PLUGINS_ROOT, 'skills'), join(root, 'skills'), { recursive: true })
  await writeFile(
    join(root, 'skills', 'yi-divination', 'SKILL.md'),
    skillBody + (adapter.skill ?? ''),
    'utf8',
  )
  if (adapter.rootSkill) await writeFile(join(root, 'SKILL.md'), skillBody + '\n', 'utf8')

  // 共享运行时：先清掉旧副本（保留宿主专属的 index.mjs 等），再复制
  await mkdir(join(root, 'src'), { recursive: true })
  for (const name of SHARED_MCP_FILES) await rm(join(root, 'src', name), { force: true })
  for (const name of SHARED_MCP_FILES) {
    await cp(join(MCP_DIR, name), join(root, 'src', name))
  }

  console.log(`[build] → ${adapter.dir}：engine / skills / src（共享运行时 ${SHARED_MCP_FILES.length} 个文件）`)
}

async function main() {
  const only = process.argv.includes('--only') ? process.argv[process.argv.indexOf('--only') + 1] : null
  await buildEngine()
  const skills = await buildSkills()
  if (!skills) return
  for (const adapter of ADAPTERS) {
    if (only && adapter.id !== only) continue
    await distribute(adapter, skills.body)
  }
  console.log('[build] 完成。下一步：node plugins/scripts/selftest.mjs')
}

main().catch((err) => {
  console.error('[build] 失败:', err)
  process.exitCode = 1
})
