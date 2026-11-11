#!/usr/bin/env node
/**
 * 通用 skill 安装器（第五百四十九批）。
 *
 * 背景：497 批起本仓只保留 DSH 一个宿主适配器，技能正文真源 `plugins/SKILL.md`
 * 带标准 frontmatter，其实可被任何按 `SKILL.md` 约定发现技能的客户端读取，
 * 但**没有任何安装入口**，用户自行 clone 后不知道往哪放。本脚本补这条路径，
 * 不复活任何已删除的适配器、不改 1.0 API 冻结面、不写仓库之外的默认位置以外的东西。
 *
 *   node outreach/install-skill.mjs --target ~/.claude/skills/yi-divination
 *   node outreach/install-skill.mjs --target <dir> --dry-run
 *   node outreach/install-skill.mjs --target <dir> --force
 *
 * 铁律二：`case_library.md` 永不复制，且生成的 INDEX.md 明写禁令。
 */
import { existsSync, mkdirSync, readFileSync, readdirSync, cpSync, writeFileSync, statSync } from 'node:fs'
import { join, resolve, dirname, posix } from 'node:path'
import { fileURLToPath } from 'node:url'
import { homedir } from 'node:os'

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const NEVER_SHIP = new Set(['case_library.md'])
const RAW = 'https://raw.githubusercontent.com/LinHoMo/Yi/main'

function args() {
  const out = { target: join(homedir(), '.claude', 'skills', 'yi-divination'), dryRun: false, force: false }
  const a = process.argv.slice(2)
  for (let i = 0; i < a.length; i++) {
    if (a[i] === '--target' && a[i + 1]) out.target = resolve(a[++i])
    else if (a[i] === '--dry-run') out.dryRun = true
    else if (a[i] === '--force') out.force = true
    else if (a[i] === '--help' || a[i] === '-h') { out.help = true }
    else { console.error(`未知参数：${a[i]}`); process.exit(2) }
  }
  return out
}

function collect() {
  const items = []
  const skill = readFileSync(join(REPO, 'plugins', 'SKILL.md'), 'utf8')
  if (!/^---[\s\S]*?name:\s*yi-divination/m.test(skill)) {
    throw new Error('plugins/SKILL.md 缺 yi-divination frontmatter，拒绝安装')
  }
  items.push({ from: join(REPO, 'plugins', 'SKILL.md'), to: 'SKILL.md', content: skill })
  const rows = []
  for (const disc of ['liuyao', 'bazi']) {
    const dir = join(REPO, disc, 'references')
    for (const name of readdirSync(dir).sort()) {
      if (!name.endsWith('.md') || NEVER_SHIP.has(name)) continue
      const from = join(dir, name)
      if (!statSync(from).isFile()) continue
      items.push({ from, to: posix.join('references', disc, name) })
      rows.push({ disc, name, from })
    }
  }
  return { items, rows }
}

function indexText(rows) {
  const line = (r) => `- \`${r.disc}/${r.name}\`：${RAW}/${r.disc}/references/${r.name}`
  return [
    '# Yi 知识库索引（本地 skill 副本）',
    '',
    '按需读取：先挑篇，再按 `文件:行` 只读那一节，不要整本读。',
    '篇目登记表真源是仓库 `plugins/scripts/kb-docs.mjs`；随包构建产物另有 `INDEX.md`。',
    '',
    '## 六爻',
    ...rows.filter((r) => r.disc === 'liuyao').map(line),
    '',
    '## 八字',
    ...rows.filter((r) => r.disc === 'bazi').map(line),
    '',
    '## ⛔ 不在此目录的内容',
    '',
    '古籍案例库 `case_library.md` 刻意不复制（AGENTS.md §一.2）：断卦时不得打开、',
    '不得提及案例名、不得以案例类比佐证；它在 GitHub 上公开也**不得当作解读知识引用**。',
    '',
    '## 口径',
    '',
    '一切分数是古籍案例对齐分（回归审计用），不是现实命中率；现实侧样本为零。',
    '输出是条件化倾向陈述，不是预言；医疗、法律、投资、重大决策请以专业意见为准。',
    '',
  ].join('\n')
}

const opt = args()
if (opt.help) {
  console.log('用法：node outreach/install-skill.mjs [--target <dir>] [--force] [--dry-run]')
  process.exit(0)
}
let data
try {
  data = collect()
} catch (e) {
  console.error('[install-skill] 收集失败：' + e.message)
  process.exit(1)
}
if (existsSync(opt.target) && !opt.force) {
  console.error(`[install-skill] 目标已存在：${opt.target}\n加 --force 覆盖，或换一个 --target。`)
  process.exit(1)
}
const files = [
  ...data.items,
  { content: indexText(data.rows), to: posix.join('references', 'INDEX.md') },
]
console.log(`[install-skill] 目标 ${opt.target}`)
console.log(`[install-skill] ${files.length} 个文件（SKILL.md + ${data.rows.length} 篇判据 + INDEX.md）`)
if (opt.dryRun) {
  for (const f of files) console.log('  · ' + f.to)
  console.log('[install-skill] dry-run，未写入')
  process.exit(0)
}
for (const f of files) {
  const dest = join(opt.target, f.to)
  mkdirSync(dirname(dest), { recursive: true })
  if (f.content !== undefined) writeFileSync(dest, f.content.replace(/\s*$/u, '') + '\n', 'utf8')
  else cpSync(f.from, dest)
}
console.log('[install-skill] 完成。技能目录：' + opt.target)
console.log('[install-skill] 提示：这只是技能正文与判据，现场起卦仍需 clone 仓库或安装 DSH 插件/MCP 服务。')
