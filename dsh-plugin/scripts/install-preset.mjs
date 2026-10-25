#!/usr/bin/env node
/**
 * 把 presets/yi-divination.yml 合并进某个 DSH profile 的用户补丁层。
 *
 * 为什么要合并而不是覆盖：`cordis.patch.yml` 是**用户自己的**补丁层，里面通常已有
 * 别的配置（模型、权限、搜索…）。直接整文件覆盖等于把用户既有配置删光——这是
 * 装插件最容易造成破坏的一步。本脚本只做「追加尚未存在的行 id」，其余原样保留。
 *
 * 幂等：重复运行不会重复插入；已存在同名 id 的行会被跳过并说明。
 *
 * 用法：
 *   node scripts/install-preset.mjs <profile> [--profile-root <dir>]
 * 默认 profile 根：$DSH_HOME/profiles/<profile>
 */
import { existsSync, readFileSync, writeFileSync, copyFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const PLUGIN_ROOT = resolve(HERE, '..')
const PRESET_FILE = join(PLUGIN_ROOT, 'presets', 'yi-divination.yml')

/** 本 preset 会插入的行 id —— 幂等判定与冲突提示都以它为准。 */
const PRESET_ROW_IDS = ['agent-preset-registry', 'preset-yi-divination']

function usage() {
  console.error('用法: node scripts/install-preset.mjs <profile> [--profile-root <dir>]')
  console.error('例:   node scripts/install-preset.mjs desktop')
}

function parseArgs(argv) {
  const args = argv.slice(2)
  if (args.length === 0 || args.includes('-h') || args.includes('--help')) {
    usage()
    process.exit(args.length === 0 ? 2 : 0)
  }
  const profile = args.find((a) => !a.startsWith('--'))
  const rootIdx = args.indexOf('--profile-root')
  const profileRoot = rootIdx >= 0 ? args[rootIdx + 1] : null
  if (!profile) {
    usage()
    process.exit(2)
  }
  return { profile, profileRoot }
}

/**
 * 从补丁文本里收集**任意缩进层级**的 `- id:` 行（幂等判定用）。
 *
 * 真机坑：初版只匹配行首 `- id:`，而补丁方言把新增行缩进在 `- insert:` 之下
 * （`    - id: agent-preset-registry`）。于是第二次运行认不出「已经装过」，
 * 会重复插入一份。自检 [11] 的幂等负例正是抓这个的。
 */
function existingRowIds(text) {
  const ids = new Set()
  for (const line of text.split('\n')) {
    const m = /^\s*-\s*id:\s*(\S+)\s*$/u.exec(line)
    if (m) ids.add(m[1].replace(/^['"]|['"]$/gu, ''))
  }
  return ids
}

/**
 * 从预设文件里取出「可以作为补丁追加的完整顶层条目」。
 *
 * 补丁层方言（真机实测）：新增插件必须写成 `- insert: [...]`；一个裸 `- id: xxx`
 * 会被解释成「修改已存在的行」，目标不存在时宿主只报一行 warning 并跳过。
 * 因此本函数按**顶层 `- ` 开头**切块，整块搬运，不去拆里面的 id。
 */
function topLevelBlocks(text) {
  const lines = text.split('\n')
  const blocks = []
  let current = null
  for (const line of lines) {
    if (/^-\s/u.test(line)) {
      if (current) blocks.push(current)
      current = [line]
    } else if (current) {
      current.push(line)
    }
    // current 为 null 时的行是文件头注释，丢弃（补丁层不保留注释无妨）
  }
  if (current) blocks.push(current)
  return blocks.map((ls) => ls.join('\n').replace(/\s+$/u, '')).filter((b) => b.length > 0)
}

/** 取插入块里声明的行 id（用于幂等判定）。 */
function declaredRowIds(blockText) {
  const ids = []
  for (const line of blockText.split('\n')) {
    const m = /^\s+-\s*id:\s*(\S+)/u.exec(line)
    if (m) ids.push(m[1].replace(/^['"]|['"]$/gu, ''))
  }
  return ids
}

/**
 * 判断补丁正文是否为「空列表」文档。
 *
 * 踩过的坑（2026-10-25 真机实测）：DSH 生成的默认 `cordis.patch.yml` 正文是
 * 一个 flow sequence `[]`。若直接在它后面追加 `- id: ...`，YAML 会变成
 * 「空 flow sequence 后面又跟了 block sequence」——解析器直接报
 * `end of the stream or a document separator is expected`，**整个 profile 起不来**。
 * 空列表必须整段替换，而不是追加。
 */
function isEffectivelyEmptyList(text) {
  const stripped = text
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.length > 0 && !l.startsWith('#'))
    .join('')
  return stripped === '' || stripped === '[]'
}

function main() {
  const { profile, profileRoot } = parseArgs(process.argv)
  const dshHome = process.env.DSH_HOME ?? join(process.env.USERPROFILE ?? process.env.HOME ?? '.', '.dsh')
  const root = profileRoot ? resolve(profileRoot) : join(dshHome, 'profiles', profile)

  if (!existsSync(root)) {
    console.error(`× profile 目录不存在：${root}`)
    console.error('  （先用 DSH 创建该 profile，或检查 --profile-root / DSH_HOME）')
    process.exit(1)
  }

  const patchPath = join(root, 'cordis.patch.yml')
  const presetText = readFileSync(PRESET_FILE, 'utf8')
  const blocks = topLevelBlocks(presetText)

  if (blocks.length === 0) {
    console.error(`× ${PRESET_FILE} 里没有解析出任何顶层条目`)
    process.exit(1)
  }

  const original = existsSync(patchPath) ? readFileSync(patchPath, 'utf8') : ''
  const existing = existingRowIds(original)
  const originalEmpty = isEffectivelyEmptyList(original)

  // 幂等判定：按「预设声明的行 id 是否都已在补丁层里出现」而非按插入块文本比对
  const presetIds = blocks.flatMap(declaredRowIds)
  const missing = presetIds.filter((id) => !existing.has(id))
  const hasRegistry = existing.has('agent-preset-registry')

  if (missing.length === 0) {
    console.log(`· 补丁层已含全部 preset 行（${presetIds.join(', ')}），无需改动。`)
    if (hasRegistry) {
      console.log('  注意：已存在的 agent-preset-registry 行**保持原样**，未改它的 default 值。')
      console.log('  想让它默认选中 Yi，请自行把该行 config.default 改成 yi-divination。')
    }
    return
  }

  // 备份后再写：补丁层是用户资产，改坏了要能退回
  if (existsSync(patchPath) && !originalEmpty) {
    const backup = `${patchPath}.bak-${new Date().toISOString().replace(/[:.]/gu, '-')}`
    copyFileSync(patchPath, backup)
    console.log(`· 已备份原补丁：${backup}`)
  }

  const blockText = blocks.join('\n\n')

  // 空列表（或不存在）→ **替换**为纯序列；非空 → 追加
  let merged
  if (originalEmpty) {
    merged = `${blockText}\n`
    if (existsSync(patchPath)) {
      const backup = `${patchPath}.bak-${new Date().toISOString().replace(/[:.]/gu, '-')}`
      copyFileSync(patchPath, backup)
      console.log(`· 已备份原补丁（空列表，将被替换）：${backup}`)
    }
  } else {
    merged = `${original.replace(/\s+$/u, '')}\n\n# ── Yi 术数插件：agent preset（由 dsh-yi-divination 安装脚本追加）──\n${blockText}\n`
  }

  writeFileSync(patchPath, merged, 'utf8')

  console.log(`√ 已${originalEmpty ? '写入（原为空列表）' : '合并进'} ${patchPath}`)
  for (const id of presetIds) console.log(`   ${existing.has(id) ? '=' : '+'} ${id}`)

  if (hasRegistry && missing.length > 0) {
    console.log('\n注意：agent-preset-registry 行已存在，**未新增第二份**。')
    console.log('若要让「新建会话」默认选中 Yi，请手动把该行 config.default 改为 yi-divination。')
  }

  console.log('\n下一步：重启 DSH（或刷新 Web 页面），在新建会话时选择「Yi 术数」。')
}

main()
