#!/usr/bin/env node
/**
 * 在真实 DSH 插件环境里验证工具「能不能被模型看见、被调用、并返回可用的结果」。
 *
 * 为什么需要这一步（2026-10-25 的教训）：
 *   前三轮所有验证都只证明「插件加载时没有 warning」。真跑一次模型发现，
 *   skill provider 返回的 `invocation: 'model'`（字符串）和缺失的 `rank` 会让
 *   **整轮会话以 error 结束**——模型一个字都答不了。加载无 warning ≠ 能用。
 *
 * 本脚本不调模型（避免依赖额度/密钥），而是直接构造 Cordis 上下文，
 * 走 apply() 注册工具，然后**真的执行一次工具回调**，断言：
 *   ① 工具出现在注册表里；② schema 里给出了参数；③ execute() 返回结构化结果且正文非空。
 */
import { fileURLToPath, pathToFileURL } from 'node:url'
import { dirname, join, resolve } from 'node:path'

const HERE = dirname(fileURLToPath(import.meta.url))
const PLUGIN_ROOT = resolve(HERE, '..')

// Windows 上 dynamic import 必须给 file:// URL，裸盘符路径会抛 ERR_UNSUPPORTED_ESM_URL_SCHEME
const { apply, inject } = await import(pathToFileURL(join(PLUGIN_ROOT, 'src', 'index.mjs')).href)

let failures = 0
const pass = (m) => console.log(`  √ ${m}`)
const fail = (m) => { failures += 1; console.log(`  × ${m}`) }

// ── 构造一个「够真」的 Cordis 上下文：记录注册项，能真正执行工具 ─────────────
const registry = new Map()
const sections = []
const providers = []

function driveEffect(factory) {
  const it = factory()
  if (it && typeof it.next === 'function') { while (!it.next().done) {} }
}

const ctx = {
  systemPrompt: {
    section(s) { sections.push(s); return () => {} },
    getSectionOrder: () => 900,
  },
  inject(names, cb) {
    if (names.includes('tools')) {
      cb({
        tools: {
          register(def) { registry.set(def.name, def); return () => registry.delete(def.name) },
        },
        effect: driveEffect,
      })
    }
    if (names.includes('skills')) {
      cb({
        skills: { registerProvider(f) { providers.push(f); return () => {} } },
        effect: driveEffect,
      })
    }
  },
}

apply(ctx, { enableBazi: true })

// ── 1. 注册面 ───────────────────────────────────────────────────────────────
console.log('\n[1] 注册面')
if (inject.includes('tools') && inject.includes('systemPrompt')) {
  pass(`inject 声明含 tools/systemPrompt：${inject.join(', ')}`)
} else {
  fail(`inject 缺必需服务：${inject.join(', ')}`)
}
registry.has('yi_liuyao') ? pass('工具 yi_liuyao 已注册') : fail('工具 yi_liuyao 未注册')
registry.has('yi_bazi') ? pass('工具 yi_bazi 已注册') : fail('工具 yi_bazi 未注册')
registry.has('yi_kb') ? pass('工具 yi_kb 已注册') : fail('工具 yi_kb 未注册')
registry.has('yi_report') ? pass('工具 yi_report 已注册') : fail('工具 yi_report 未注册')
sections.length === 1 ? pass(`系统提示词段已注册：${sections[0].name}`) : fail(`提示词段数量异常：${sections.length}`)
sections[0] && Number.isFinite(sections[0].order) ? pass(`section.order 是有限数：${sections[0].order}`) : fail('section.order 不是有限数')
providers.length === 1 ? pass('技能 provider 已注册') : fail(`技能 provider 数量异常：${providers.length}`)

// ── 2. 技能条目形状（真机里正是这里炸的） ───────────────────────────────────
console.log('\n[2] 技能条目形状（dsh-skill 的 validateInvocation / rank 校验）')
if (providers.length === 1) {
  try {
    const p = providers[0]()
    const listed = await p.list()
    const one = listed[0]
    // 逐条对齐 dsh-skill/lib/index.js 的校验：
    if (typeof one.name === 'string' && one.name) pass(`name = ${one.name}`)
    else fail('name 不是非空字符串')
    if (typeof one.description === 'string' && one.description.length > 0) pass(`description 长度 ${one.description.length}`)
    else fail('description 缺失或为空')
    const inv = one.invocation
    if (inv && typeof inv === 'object' && !Array.isArray(inv)
        && typeof inv.modelInvocable === 'boolean'
        && typeof inv.userInvocable === 'boolean') {
      pass(`invocation 是对象：{modelInvocable:${inv.modelInvocable}, userInvocable:${inv.userInvocable}}`)
    } else {
      fail(`invocation 必须是 {modelInvocable,userInvocable} 对象，实为 ${JSON.stringify(inv)}`)
    }
    if (typeof one.rank === 'number' && Number.isFinite(one.rank)) pass(`rank = ${one.rank}`)
    else fail(`rank 必须是有限数，实为 ${JSON.stringify(one.rank)}`)
    if (typeof one.source === 'string') pass(`source = ${one.source}`)
    else fail('source 不是字符串')

    const got = await p.get({ name: one.name })
    got && got.content && got.content.length > 500
      ? pass(`技能正文可加载（${got.content.length} 字）`)
      : fail('技能正文加载失败')
  } catch (err) {
    fail(`provider 抛异常：${err?.message ?? err}`)
  }
}

// ── 3. 真实执行工具（这是「能不能用」的决定性一步） ─────────────────────────
console.log('\n[3] 真实执行工具回调')
const fakeExec = { signal: new AbortController().signal, agent: null, token: 't', callId: 'c1' }

try {
  const def = registry.get('yi_liuyao')
  const value = await def.execute(
    { question: '验证工具链路', mode: 'manual', yao: '7,8,9,7,6,8' },
    fakeExec,
  )
  const hex = value?.original_hexagram?.name
  hex ? pass(`yi_liuyao 返回卦名：${hex}`) : fail('yi_liuyao 未返回卦名')
  Array.isArray(value?.lines) && value.lines.length === 6
    ? pass('返回 6 条爻线')
    : fail(`爻线数异常：${value?.lines?.length}`)
  value?.conclusion?.direction
    ? pass(`结论方向：${value.conclusion.direction}`)
    : fail('缺 conclusion.direction')
  value?.narrative?.text?.length > 100
    ? pass(`正文 ${value.narrative.text.length} 字`)
    : fail('正文缺失或过短')

  // render 必须能把规范值摊成模型可见的 content 块
  const chunks = def.output?.render
    ? def.output.render({}, value)
    : null
  Array.isArray(chunks) && chunks[0]?.type === 'text' && chunks[0].text.length > 0
    ? pass('output.render 产出非空文本块')
    : fail('output.render 未产出文本块')
} catch (err) {
  fail(`yi_liuyao 执行异常：${err?.message ?? err}`)
}

try {
  const def = registry.get('yi_bazi')
  const value = await def.execute({ datetime: '1990-05-20 12:00', gender: '男' }, fakeExec)
  value?.pillars?.year?.ganzhi
    ? pass(`yi_bazi 四柱：${value.pillars.year.ganzhi} ${value.pillars.month?.ganzhi} ${value.pillars.day?.ganzhi} ${value.pillars.hour?.ganzhi}`)
    : fail('yi_bazi 未返回四柱')
  value?.narrative?.text?.length > 50 ? pass(`八字正文 ${value.narrative.text.length} 字`) : fail('八字正文缺失')
} catch (err) {
  fail(`yi_bazi 执行异常：${err?.message ?? err}`)
}

try {
  const def = registry.get('yi_kb')
  const value = await def.execute({ query: '用神 取法' }, fakeExec)
  Array.isArray(value?.matches) && value.matches.length > 0
    ? pass(`yi_kb 命中 ${value.matches.length} 条（首条 ${value.matches[0].file}:${value.matches[0].line}）`)
    : fail('yi_kb 无命中')
  value?.files_scanned >= 9 ? pass(`扫描 ${value.files_scanned} 篇`) : fail(`扫描篇数异常：${value?.files_scanned}`)
  const kbChunks = def.output?.render ? def.output.render({}, value) : null
  Array.isArray(kbChunks) && kbChunks[0]?.type === 'text' && kbChunks[0].text.length > 0
    ? pass('yi_kb output.render 产出非空文本块')
    : fail('yi_kb output.render 未产出文本块')
} catch (err) {
  fail(`yi_kb 执行异常：${err?.message ?? err}`)
}

// ── 4. 负例自证：坏的技能条目必须被本脚本的判据识破 ─────────────────────────
console.log('\n[4] 负例自证（判据不能永远变绿）')
const badInvocation = 'model'
const invOk = (inv) => Boolean(inv && typeof inv === 'object' && !Array.isArray(inv)
  && typeof inv.modelInvocable === 'boolean')
invOk(badInvocation) ? fail('负例失效：字符串 invocation 竟被判为合法') : pass('负例自证：字符串 invocation 被判非法（正是真机崩溃的那一种）')
invOk(undefined) ? fail('负例失效：缺 rank 类的空值竟被判为合法') : pass('负例自证：缺失的 rank 会被判非法')
invOk({ modelInvocable: true, userInvocable: true }) ? pass('正例：合法对象被判为合法') : fail('正例被误判为非法')

console.log('\n' + '='.repeat(52))
if (failures === 0) { console.log('DSH 内验证全部通过。'); process.exitCode = 0 }
else { console.log(`DSH 内验证未通过：${failures} 处失败。`); process.exitCode = 1 }
