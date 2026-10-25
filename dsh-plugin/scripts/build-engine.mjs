#!/usr/bin/env node
/**
 * 把两个学科科目录里「运行时真正需要」的部分收进 dsh-plugin/engine/。
 *
 * 为什么要这一步（而不是直接把仓库塞进 npm 包）：
 *   仓库 134MB，其中 34MB 是 bazi/data/cases、4.8MB 是 liuyao/data/cases，
 *   还有 9.5MB 的评测量词库 sources/。这些只服务「古籍对齐分」与回归门，
 *   起卦/排盘/断语一个字都用不到。
 *
 * 实测最小集（2026-10-25，本机实测起卦与排盘均成功）：
 *   liuyao/core + liuyao/scripts + liuyao/data/rules + liuyao/data/*.json  ≈ 4.5MB
 *   bazi/core   + bazi/scripts   + bazi/data/rules   + bazi/data/*.json    ≈ 1.6MB
 *
 * 收录规则是白名单而非黑名单：新增目录不会因为「忘了排除」而被悄悄打进包，
 * 只会因为「忘了收录」而在自检里报红——后者是安全的失效方向。
 */
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const PLUGIN_ROOT = resolve(HERE, '..')
const REPO_ROOT = resolve(PLUGIN_ROOT, '..')
const ENGINE_DIR = join(PLUGIN_ROOT, 'engine')

/** 每科要收进去的相对路径（相对该科根目录）。 */
const RUNTIME_INCLUDE = {
  liuyao: ['core', 'scripts', 'data/rules', 'references'],
  bazi: ['core', 'scripts', 'data/rules', 'references'],
}

/**
 * ⛔ 案例库与解读必须物理隔离（仓库 AGENTS.md §一.2 铁律二）。
 *
 * `references/case_library.md`（165KB）是黑箱测试用案例库：只允许测试脚本、
 * 用户明确要求校验、用户主动问「有无类似案例」三种场景访问。把它打进发布包，
 * 等于给模型开了一条「断卦时联想历史案例」的暗道——那正是铁律二禁止的行为。
 * 这里按**文件名**排除，且自检里有一条专门断言它没被打进来。
 */
const REFERENCE_EXCLUDE = new Set(['case_library.md'])


/** 每科 data/ 下直读的 *.json（rules 之外的单文件数据）。 */
const DATA_JSON_EXCLUDE = new Set([])

/** 语言运行时不需要、且会让包变大的东西。 */
const JUNK = /(__pycache__|\.pyc$|\.pyo$|\.pytest_cache|\.mypy_cache)/

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

async function listJson(dir) {
  const { readdir } = await import('node:fs/promises')
  const out = []
  let entries
  try {
    entries = await readdir(dir, { withFileTypes: true })
  } catch {
    return out
  }
  for (const e of entries) {
    if (e.isFile() && e.name.endsWith('.json') && !DATA_JSON_EXCLUDE.has(e.name)) out.push(e.name)
  }
  return out
}

async function main() {
  await rm(ENGINE_DIR, { recursive: true, force: true })
  await mkdir(ENGINE_DIR, { recursive: true })

  const manifest = { builtAt: new Date().toISOString(), disciplines: {} }

  for (const [discipline, includes] of Object.entries(RUNTIME_INCLUDE)) {
    const srcRoot = join(REPO_ROOT, discipline)
    const destRoot = join(ENGINE_DIR, discipline)
    await mkdir(destRoot, { recursive: true })

    for (const rel of includes) {
      await copyTree(join(srcRoot, rel), join(destRoot, rel), {
        excludeNames: rel === 'references' ? REFERENCE_EXCLUDE : null,
      })
    }

    // data/*.json（单文件数据）
    const dataDir = join(srcRoot, 'data')
    const jsonNames = await listJson(dataDir)
    if (jsonNames.length) {
      await mkdir(join(destRoot, 'data'), { recursive: true })
      for (const name of jsonNames) {
        await cp(join(dataDir, name), join(destRoot, 'data', name))
      }
    }

    // 学科的 SKILL.md 与 README 是给人/模型看的，随引擎一起走
    for (const doc of ['SKILL.md', 'README.md']) {
      try {
        await cp(join(srcRoot, doc), join(destRoot, doc))
      } catch {
        /* 某科没有该文件不算错误 */
      }
    }

    manifest.disciplines[discipline] = {
      includes,
      dataJson: jsonNames,
    }
  }

  await writeFile(join(ENGINE_DIR, 'MANIFEST.json'), JSON.stringify(manifest, null, 2) + '\n', 'utf8')
  console.log('[build-engine] 完成 →', ENGINE_DIR)
  for (const [d, v] of Object.entries(manifest.disciplines)) {
    console.log(`  ${d}: ${v.includes.join(', ')} + data/*.json(${v.dataJson.length})`)
  }
}

main().catch((err) => {
  console.error('[build-engine] 失败:', err)
  process.exitCode = 1
})
