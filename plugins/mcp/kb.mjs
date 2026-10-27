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
 *  · 词频计分（全权重词）：标题命中 ×4、文件名命中 ×3、正文词频（封顶 12）、覆盖词数 ×6；
 *  · 中文 2-gram 兜底：query 里 ≥3 字的连续汉字串自动切出相邻二字窗（「世应怎么安」→
 *    世应/应怎/怎么/么安），减权重计分（标题 ×1、正文封顶 4、不计覆盖）——无空格长词
 *    整串匹配不到时仍能召回，且不会压过精确命中；
 *  · 同义词展开：src/kb-synonyms.json 组内任一词命中即整组全权重展开（用爻→用神）；
 *    只收确定同义，不收近义（忌神/仇神是不同概念，禁止入组）；
 *  · 每文件最多 2 条（防单篇刷屏），全局上限 limit（默认 5，≤10）。
 */
import { readFile, readdir } from 'node:fs/promises'
import { readFileSync } from 'node:fs'
import { basename, dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

/** 永不进入检索范围的文件（铁律二）。 */
const NEVER_SHIP = new Set(['case_library.md'])

/**
 * 知识库文件 → Yan 资源句柄（`resource:<id>`）。
 *
 * 为什么要有这一层：Yan 的插件资源装在包目录里，**不在模型的工作区内**，
 * 模型的 `read` 读不到（workspace 沙箱）。所以 `yi_kb` 不只返回 `file:line`，
 * 还要把「该去 plugins_read_resource 读哪一个 resource」一并交出去。
 * id 生成规则与 `yan-plugin.json` 的 `resources[].id` **必须同式**
 * （`scripts/build.mjs` 有双向闸门逐条对账，见 yan-plugin/CHANGELOG.md 304 批）。
 */
export function resourceIdFor(rel) {
  const slug = String(rel)
    .replace(/\.md$/u, '')
    .replace(/[^a-zA-Z0-9]+/gu, '-')
    .replace(/^-+|-+$/gu, '')
    .toLowerCase()
  return `resource:kb-${slug}`
}

/**
 * 知识库根：<root>/skills/yi-divination/references（与 bundledSkillDir 同源）。
 *
 * 305 批修真 bug：旧写法按目录名判定层级（`src` 上一级、`lib` 上两级），
 * 而共享真源现在放在 `plugins/mcp/`——命中 else 分支后多跳一级到**仓库根**，
 * 于是 `files_scanned: 0`、检索永远空手（自检 [4] 段当场抓到）。
 * 统一约定：这几个模块永远位于 `<root>/mcp/` 或 `<root>/src/`，故包根恒为 `..`。
 */
export function resolveKbRoot() {
  const moduleDir = dirname(fileURLToPath(import.meta.url))
  return join(resolve(moduleDir, '..'), 'skills', 'yi-divination', 'references')
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

/** 同义词组：<pkg>/src/kb-synonyms.json（缺文件/坏 JSON = 无同义词，不炸检索）。模块级缓存。 */
let synIndexCache = null
function synonymIndex() {
  if (synIndexCache) return synIndexCache
  synIndexCache = new Map()
  try {
    const moduleDir = dirname(fileURLToPath(import.meta.url))
    const raw = JSON.parse(readFileSync(join(moduleDir, 'kb-synonyms.json'), 'utf8'))
    for (const group of raw.groups ?? []) {
      for (const w of group) {
        const set = synIndexCache.get(w) ?? new Set()
        for (const other of group) if (other !== w) set.add(other)
        synIndexCache.set(w, set)
      }
    }
  } catch {
    /* 同义词表缺失或损坏时按「无同义词」运行——检索主体不受影响 */
  }
  return synIndexCache
}

/** query 词展开：主词 = 用户词 + 同义词（全权重）。返回 { primary, synonymsAdded }。 */
function expandWithSynonyms(terms) {
  const idx = synonymIndex()
  const primary = []
  const synonymsAdded = []
  for (const t of terms) {
    primary.push(t)
    for (const s of idx.get(t) ?? []) {
      if (!primary.includes(s)) {
        primary.push(s)
        synonymsAdded.push(s)
      }
    }
  }
  return { primary, synonymsAdded }
}

/** 连续汉字串（≥3 字）的相邻二字窗；2 字词不切（整串即词），不跨中英文边界。 */
export function cjkBigrams(term) {
  const out = new Set()
  for (const run of String(term).match(/[\u4e00-\u9fff]+/gu) ?? []) {
    if (run.length >= 3) {
      for (let i = 0; i + 2 <= run.length; i++) out.add(run.slice(i, i + 2))
    }
  }
  return [...out]
}

/**
 * 检索。query 必填（缺省/空白抛错）；discipline 限定 'liuyao'|'bazi'；
 * kbRoot 可注入（selftest 的负例自证用临时目录探针）。
 */
export async function searchKb({ query, discipline, limit = 5, maxPerFile = 2, kbRoot = resolveKbRoot() }) {
  const rawTerms = [...new Set(String(query ?? '').toLowerCase().split(/\s+/u).filter(Boolean))]
  if (!rawTerms.length) {
    throw new Error('yi_kb 需要 query（关键词，可多个，空格分隔，如 "用神 取法"）')
  }
  const { primary: terms, synonymsAdded } = expandWithSynonyms(rawTerms)
  const bigrams = [...new Set(rawTerms.flatMap((t) => cjkBigrams(t)))].filter((t) => !terms.includes(t))
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
      // 2-gram 兜底（减权重：标题 ×1、正文封顶 4、不计覆盖——兜底召回不该压过精确命中）
      let bigramHit = false
      for (const t of bigrams) {
        if (terms.includes(t)) continue
        const inTitle = titleLower.includes(t)
        const count = countOccurrences(bodyLower, t)
        if (inTitle) score += 1
        if (count) {
          score += Math.min(count, 4)
          bigramHit = true
          if (!firstHit) firstHit = sec.lines.find((l) => l.text.toLowerCase().includes(t))
        }
      }
      if (!covered && !bigramHit) continue
      score += covered * 6
      const hit = firstHit ?? sec.lines.find((l) => l.text.trim()) ?? { n: sec.startLine, text: '' }
      matches.push({
        file: rel,
        resource: resourceIdFor(rel),
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
    expanded: { synonyms: synonymsAdded, bigrams },
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
    // 两个宿主的读法不同，但共用一条提示：DSH 侧直接 read 包内路径，
    // Yan 侧包资源不在工作区，须走 plugins_read_resource 的 resource 句柄。
    hint:
      '按 file:line 只读那一节，不要整篇读；总路由表在 references/INDEX.md。' +
      'Yan 宿主的包资源不在工作区内，改用每条的 resource 句柄经 plugins_read_resource 读' +
      '（如 resource:kb-bazi-api-spec）。',
  }
}
