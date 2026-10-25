#!/usr/bin/env node
/**
 * 组装随包技能目录 `skills/yi-divination/`。
 *
 * 为什么需要这一步：官方 `dsh-skill-filesystem` 的技能发现规则是
 * **`<root>/<name>/SKILL.md`**，且「刻意不支持发现嵌套的 `**\/SKILL.md`」。
 * 而本仓库的知识库在 `liuyao/references/` 与 `bazi/references/` 两处，
 * 摊平到技能目录里才能被按需读取——否则模型拿不到 najia_rules 这类判据表。
 *
 * 产出结构：
 *   skills/yi-divination/
 *     SKILL.md              ← 路由与操作说明（工具怎么用、边界在哪）
 *     references/liuyao/    ← 六爻知识库（纳甲规则、断卦指南、格局参考…）
 *     references/bazi/      ← 八字知识库（十神术语、纳音释义、月支格局…）
 *
 * ⛔ case_library.md 永不收录（AGENTS.md §一.2 铁律二：案例库与解读物理隔离）。
 */
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const PLUGIN_ROOT = resolve(HERE, '..')
const REPO_ROOT = resolve(PLUGIN_ROOT, '..')
const SKILL_DIR = join(PLUGIN_ROOT, 'skills', 'yi-divination')

/** 永不随包发出的参考文档（铁律二）。 */
const NEVER_SHIP = new Set(['case_library.md'])

/** 技能正文：SKILL.md 的 routing frontmatter 由插件根 SKILL.md 提供，这里整体搬运。 */
async function main() {
  await rm(SKILL_DIR, { recursive: true, force: true })
  await mkdir(SKILL_DIR, { recursive: true })

  // 1) 技能正文：以插件根 SKILL.md 为准（单一份真源，不复制内容）
  const skillBody = await readFile(join(PLUGIN_ROOT, 'SKILL.md'), 'utf8')
  await writeFile(join(SKILL_DIR, 'SKILL.md'), skillBody, 'utf8')

  // 2) 知识库：两科 references 摊到 skills/yi-divination/references/<科>/
  const shipped = []
  for (const discipline of ['liuyao', 'bazi']) {
    const src = join(REPO_ROOT, discipline, 'references')
    const dest = join(SKILL_DIR, 'references', discipline)
    await mkdir(dest, { recursive: true })
    const { readdir } = await import('node:fs/promises')
    let entries
    try {
      entries = await readdir(src, { withFileTypes: true })
    } catch {
      continue
    }
    for (const e of entries) {
      if (!e.isFile() || !e.name.endsWith('.md')) continue
      if (NEVER_SHIP.has(e.name)) continue
      await cp(join(src, e.name), join(dest, e.name))
      shipped.push(`${discipline}/${e.name}`)
    }
  }

  // 3) 写一份索引，供模型判断「该读哪一篇」而不必盲扫。
  //    体积**构建时实测**（消灭手写 KB 漂移——275 批前这里全是手抄数字）。
  //    每篇都必须登记描述；两科新加 references 文件而忘登记 → 构建即红（负例纪律）。
  const { stat } = await import('node:fs/promises')
  const KB_DOC = new Map([
    ['liuyao/najia_rules.md', '需要核对纳甲装卦规则：八宫次序、纳支口诀、世应定位、六亲六神推演、旬空'],
    ['liuyao/interpretation_guide.md', '需要查用神取法、旺衰体系、动变规则、应期推断'],
    ['liuyao/pattern_reference.md', '判断十二大经典格局（先查这篇，短且直接可用）'],
    ['liuyao/classical_synthesis.md', '需要理论深度：四经典综合、虚空月破墓绝刑冲'],
    ['liuyao/source_ledger.md', '需要确认某条判据的书源出处'],
    ['bazi/bazi_shishen_terminology.md', '十神术语释义'],
    ['bazi/bazi_nayin_shiyi.md', '纳音释义'],
    ['bazi/bazi_yue_shi_ge.md', '月支与格局'],
    ['bazi/api_spec.md', '八字模块接口速查'],
  ])
  const missing = shipped.filter((s) => !KB_DOC.has(s))
  const stale = [...KB_DOC.keys()].filter((s) => !shipped.includes(s))
  if (missing.length > 0 || stale.length > 0) {
    if (missing.length > 0) console.error('[build-skills] 失败: 以下知识库文件未登记 KB_DOC 描述——请在 scripts/build-skills.mjs 补登记:\n  ' + missing.join('\n  '))
    if (stale.length > 0) console.error('[build-skills] 失败: KB_DOC 登记了已不随包的文件——请清理:\n  ' + stale.join('\n  '))
    process.exitCode = 1
    return
  }
  const kbSize = new Map()
  for (const s of shipped) {
    const st = await stat(join(SKILL_DIR, 'references', s))
    kbSize.set(s, Math.max(1, Math.round(st.size / 1024)) + 'KB')
  }
  const biggest = Math.max(...shipped.map((s) => parseInt(kbSize.get(s))))
  const kbRow = (s) => `| \`${s.split('/')[1]}\`（${kbSize.get(s)}） | ${KB_DOC.get(s)} |`
  const kbRows = (discipline) => [...KB_DOC.keys()].filter((s) => s.startsWith(discipline + '/')).map(kbRow)
  const index = [
    '# Yi 知识库索引',
    '',
    `按需读取：先看这一行判断该读哪篇，再读具体文件。**不要整本读**——单篇最大 ${biggest}KB，`,
    '读错一篇就白占一大块上下文。',
    '',
    '懒得挑篇时用 `yi_kb` 工具关键词检索（返回 文件:行 + 节标题 + 摘录），先定位再读节段。',
    '',
    '## 六爻（references/liuyao/）',
    '',
    '| 文件 | 什么时候读 |',
    '|---|---|',
    ...kbRows('liuyao'),
    '',
    '## 八字（references/bazi/）',
    '',
    '| 文件 | 什么时候读 |',
    '|---|---|',
    ...kbRows('bazi'),
    '',
    '## ⛔ 不在此目录的内容',
    '',
    '古籍案例库（`case_library.md`）**刻意不随包发货**。按本仓 AGENTS.md §一.2 铁律二，',
    '案例库与解读必须物理隔离：断卦时不得联想、引用或类比历史案例。若用户明确要求',
    '「事后校验」或主动问「有无类似案例」，应告知该能力需在完整仓库环境中使用。',
    '',
  ].join('\n')
  await writeFile(join(SKILL_DIR, 'references', 'INDEX.md'), index, 'utf8')

  console.log('[build-skills] 完成 →', SKILL_DIR)
  console.log('  知识库：', shipped.length, '篇')
  for (const s of shipped) console.log('   ·', s)
}

main().catch((err) => {
  console.error('[build-skills] 失败:', err)
  process.exitCode = 1
})
