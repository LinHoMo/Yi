/**
 * yi_kb：随包判据知识库的关键词检索（纯 Node、确定性、零 LLM、零 Python）。
 *
 * 动机：知识库 9 篇单篇最大 52KB，模型凭 INDEX.md 路由表盲选整篇读，
 * 读错一篇就白占一大块上下文。本模块让模型先关键词定位（返回 文件:行 +
 * 节标题 + 摘录），再按行读具体节段。
 *
 * 边界（AGENTS.md §一.2 铁律二）：
 *  · 只扫 <pkg>/skills/yi-divination/references/ 下的 .md；
 *  · `case_library.md` 在**扫描层**按文件名硬排除——即使有人把它塞进该目录
 *    也检不到（与 build-skills 的打包层排除、selftest [1.5] 的包内断言构成三道闸）。
 *
 * 算法（刻意简单、可复现）：
 *  · 按 1–3 级标题切节（代码块里的 `#` 注释可能造成多切，只影响节粒度不影响正确性）；
 *  · 词频计分：标题命中 ×4、文件名命中 ×3、正文词频（封顶 12）、覆盖词数 ×6；
 *  · 每文件最多 2 条（防单篇刷屏），全局上限 limit（默认 5，≤10）。
 */
import { readFile, readdir } from 'node:fs/promises'
import { basename, dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

/** 永不进入检索范围的文件（铁律二）。 */
const NEVER_SHIP = new Set(['case_library.md'])

/** 知识库根：<pkg>/skills/yi-divination/references（与 bundledSkillDir 同源）。 */
export function resolveKbRoot() {
  const moduleDir = dirname(fileURLToPath(import.meta.url))
  const pkgRoot = basename(moduleDir) === 'src' ? resolve(moduleDir, '..') : resolve(moduleDir, '../..')
  return join(pkgRoot, 'skills', 'yi-divination', 'references')
}

/** 列出可检索的 .md（相对 kbRoot、正斜杠）。case_library.md 永不在列。 */
export async function listKbFiles(kbRoot = resolveKbRoot()) {
  const out = []
  async function walk(dir, base = '') {
    let entries
    try {
      entries = await readdir(dir, { withFileTypes: true })
    } catch {
      return
    }
    for (const e of entries) {
      const rel = base ? `${base}/${e.name}` : e.name
      if (e.isDirectory()) await walk(join(dir, e.name), rel)
      else if (e.name.endsWith('.md') && !NEVER_SHIP.has(e.name)) out.push(rel)
    }
  }
  await walk(kbRoot)
  return out.sort()
}

/** 把一篇 md 切成节段：遇到 1–3 级标题即开新节。 */
function splitSections(text) {
  const lines = text.replace(/^\uFEFF/u, '').split(/\r?\n/u)
  const sections = []
  let cur = null
  for (let i = 0; i < lines.length; i++) {
    if (/^#{1,3}\s+\S/u.test(lines[i])) {
      if (cur) sections.push(cur)
      cur = { title: lines[i].replace(/^#{1,3}\s+/u, '').trim(), startLine: i + 1, lines: [] }
    } else {
      if (!cur) cur = { title: '(篇首)', startLine: i + 1, lines: [] }
      cur.lines.push({ n: i + 1, text: lines[i] })
    }
  }
  if (cur) sections.push(cur)
  return sections
}

function countOccurrences(haystack, needle) {
  if (!needle) return 0
  let n = 0
  let i = 0
  while ((i = haystack.indexOf(needle, i)) !== -1) {
    n += 1
    i += needle.length
  }
  return n
}

/**
 * 检索。query 必填（缺省/空白抛错）；discipline 限定 'liuyao'|'bazi'；
 * kbRoot 可注入（selftest 的负例自证用临时目录探针）。
 */
export async function searchKb({ query, discipline, limit = 5, maxPerFile = 2, kbRoot = resolveKbRoot() }) {
  const terms = [...new Set(String(query ?? '').toLowerCase().split(/\s+/u).filter(Boolean))]
  if (!terms.length) {
    throw new Error('yi_kb 需要 query（关键词，可多个，空格分隔，如 "用神 取法"）')
  }
  const cap = Math.min(Math.max(Number(limit) || 5, 1), 10)

  const files = (await listKbFiles(kbRoot)).filter((f) =>
    discipline ? f.startsWith(`${discipline}/`) : true,
  )

  const matches = []
  for (const rel of files) {
    let text
    try {
      text = await readFile(join(kbRoot, rel), 'utf8')
    } catch {
      continue
    }
    const fileLower = rel.toLowerCase()
    for (const sec of splitSections(text)) {
      const bodyLower = sec.lines.map((l) => l.text).join('\n').toLowerCase()
      const titleLower = sec.title.toLowerCase()
      let score = 0
      let covered = 0
      let firstHit = null
      for (const t of terms) {
        const inTitle = titleLower.includes(t)
        const inFile = fileLower.includes(t)
        const count = countOccurrences(bodyLower, t)
        if (inTitle) score += 4
        if (inFile) score += 3
        if (count) {
          score += Math.min(count, 12)
          if (!firstHit) firstHit = sec.lines.find((l) => l.text.toLowerCase().includes(t))
        }
        if (inTitle || inFile || count) covered += 1
      }
      if (!covered) continue
      score += covered * 6
      const hit = firstHit ?? sec.lines.find((l) => l.text.trim()) ?? { n: sec.startLine, text: '' }
      matches.push({
        file: rel,
        discipline: rel.startsWith('liuyao/') ? 'liuyao' : rel.startsWith('bazi/') ? 'bazi' : 'index',
        title: sec.title,
        line: hit.n,
        score,
        snippet: hit.text.trim().slice(0, 240),
      })
    }
  }

  matches.sort((a, b) => b.score - a.score || a.file.localeCompare(b.file) || a.line - b.line)
  const perFile = new Map()
  const picked = []
  for (const m of matches) {
    const c = perFile.get(m.file) ?? 0
    if (c >= maxPerFile) continue
    perFile.set(m.file, c + 1)
    picked.push(m)
    if (picked.length >= cap) break
  }

  return {
    kb: 'yi-divination',
    query: String(query),
    terms,
    discipline: discipline ?? 'all',
    files_scanned: files.length,
    matches: picked,
  }
}

/** 工具 execute 薄封装：补一条用法提示。缺 query 时 searchKb 抛错。 */
export async function runKb(args = {}) {
  const value = await searchKb({
    query: args.query,
    discipline: args.discipline,
    limit: args.limit,
  })
  return {
    ...value,
    hint: '按 file:line 用 read 工具读具体节段（不要整篇读）；总路由表在 references/INDEX.md。',
  }
}
