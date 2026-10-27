#!/usr/bin/env node
/**
 * 插件自检：验证「装进 DSH 之后真的能用」，而不是「文件都在」。
 *
 * 每项都有负例自证（仓库 §四.8 的规矩）：一项检查如果永远只会变绿，
 * 它和「什么都没查」在输出上完全同形。
 */
import { existsSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { engineRoot, selftest as engineSelftest, cast } from '../src/engine.mjs'
import { resolvePython, resetPythonCache } from '../src/python.mjs'
import { buildLiuyaoArgs, buildBaziArgs } from '../src/tools.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const PLUGIN_ROOT = resolve(HERE, '..')

let failures = 0
const pass = (msg) => console.log(`  √ ${msg}`)
const fail = (msg) => {
  failures += 1
  console.log(`  × ${msg}`)
}

async function section(title, fn) {
  console.log(`\n${title}`)
  try {
    await fn()
  } catch (err) {
    fail(`本段抛异常：${err?.message ?? err}`)
  }
}

// ── 1. 包结构 ────────────────────────────────────────────────────────────────
await section('[1] 包结构完整性', async () => {
  for (const rel of [
    'src/index.mjs',
    'src/engine.mjs',
    'src/python.mjs',
    'src/tools.mjs',
    'src/kb.mjs',
    'src/kb-synonyms.json',
    'src/report.mjs',
    'SKILL.md',
    'cordis.patch.yml',
    'engine/MANIFEST.json',
    'skills/yi-divination/SKILL.md',
    'skills/yi-divination/references/INDEX.md',
    'presets/yi-divination.yml',
  ]) {
    const p = join(PLUGIN_ROOT, rel)
    if (existsSync(p)) pass(`存在 ${rel}`)
    else fail(`缺失 ${rel}`)
  }
})

// ── 1.5 知识库与案例库隔离 ──────────────────────────────────────────────────
await section('[1.5] 知识库随包 + 案例库被隔离（铁律二）', async () => {
  const { readdir } = await import('node:fs/promises')

  let kb = 0
  for (const discipline of ['liuyao', 'bazi']) {
    const dir = join(PLUGIN_ROOT, 'skills', 'yi-divination', 'references', discipline)
    let entries = []
    try {
      entries = await readdir(dir, { withFileTypes: true })
    } catch {
      fail(`知识库目录缺失：${discipline}`)
      continue
    }
    const md = entries.filter((e) => e.isFile() && e.name.endsWith('.md'))
    kb += md.length
    if (md.length) pass(`${discipline} 知识库 ${md.length} 篇`)
    else fail(`${discipline} 知识库为空`)
  }
  if (kb < 6) fail(`知识库总篇数 ${kb} 偏少，疑似打包流程漏收`)

  // 铁律二：案例库绝不能出现在任何随包目录
  async function findCaseLib(dir, hits = []) {
    let entries = []
    try {
      entries = await readdir(dir, { withFileTypes: true })
    } catch {
      return hits
    }
    for (const e of entries) {
      const p = join(dir, e.name)
      if (e.isDirectory()) await findCaseLib(p, hits)
      else if (e.name === 'case_library.md') hits.push(p)
    }
    return hits
  }
  const leaks = await findCaseLib(PLUGIN_ROOT)
  if (leaks.length === 0) pass('案例库未被随包发出（AGENTS.md §一.2 铁律二）')
  else for (const l of leaks) fail(`案例库被随包发出：${l}`)

  // 负例自证：扫一个真放了 case_library.md 的临时目录，必须报出来
  const probeDir = join(PLUGIN_ROOT, '_probe_caselib_', 'x')
  const fsp = await import('node:fs/promises')
  await fsp.mkdir(probeDir, { recursive: true })
  await fsp.writeFile(join(probeDir, 'case_library.md'), 'probe', 'utf8')
  const probeHits = await findCaseLib(join(PLUGIN_ROOT, '_probe_caselib_'))
  await fsp.rm(join(PLUGIN_ROOT, '_probe_caselib_'), { recursive: true, force: true })
  if (probeHits.length === 0) fail('负例失效：造一个 case_library.md 竟扫不到，本段判据是死的')
  else pass('负例自证：造一个 case_library.md 能被扫到（已清理）')
})

// ── 2. SKILL.md frontmatter（负例：坏 frontmatter 必须被识破）────────────────
// CRLF 兼容（278 批 CI 实测）：Windows runner 按 autocrlf=true 检出时 SKILL.md
// 是 \r\n，硬编码 '\n' 的判据会假红——归一后再判，判据测的是产物不是检出配置。
await section('[2] SKILL.md frontmatter', async () => {
  const { readFileSync } = await import('node:fs')
  const raw = readFileSync(join(PLUGIN_ROOT, 'SKILL.md'), 'utf8').replace(/\r\n/g, '\n')
  const end = raw.indexOf('\n---\n', 4)
  if (!raw.startsWith('---\n') || end < 0) {
    fail('SKILL.md 没有合法 frontmatter')
  } else {
    const front = raw.slice(4, end)
    const hasName = /^name:\s*\S+/mu.test(front)
    const hasDesc = /^description:\s*\S+/mu.test(front)
    if (hasName && hasDesc) pass('frontmatter 含 name 与 description')
    else fail(`frontmatter 缺字段（name=${hasName}, description=${hasDesc}）`)
  }
  // 负例自证：构造一个**确定不合规**的 frontmatter，判据必须识破。
  // （初版探针取 SKILL.md 前几行正文，那里恰好也有 `name:`，属探针自身写错——
  //  已改为显式构造坏样本：没有 `---` 包夹、且缺 description。）
  const probeBroken = '# 标题\n\nname: foo\n随便写点正文。\n'
  const pEnd = probeBroken.indexOf('\n---\n', 4)
  const validShape = probeBroken.startsWith('---\n') && pEnd >= 0
  if (validShape) {
    fail('负例失效：构造的坏样本竟被判为合法 frontmatter，本段判据不可信')
  } else {
    pass('负例自证：缺 --- 包夹的非法 frontmatter 能被判出不合规')
  }
})

// ── 3. Python 定位 ──────────────────────────────────────────────────────────
await section('[3] Python 解释器定位', async () => {
  resetPythonCache()
  const { command, source } = await resolvePython()
  if (existsSync(command)) pass(`已定位（来源 ${source}）：${command}`)
  else fail(`定位到的解释器不存在：${command}`)

  // 负例自证：指向一个不存在的路径必须抛错，而不是悄悄回退
  const saved = process.env.DSH_PYTHON
  process.env.DSH_PYTHON = join(PLUGIN_ROOT, '_no_such_python_.exe')
  resetPythonCache()
  try {
    await resolvePython()
    fail('负例失效：DSH_PYTHON 指向不存在的文件竟未报错（静默回退）')
  } catch {
    pass('负例自证：DSH_PYTHON 指向不存在的文件会报错，不静默回退')
  } finally {
    if (saved === undefined) delete process.env.DSH_PYTHON
    else process.env.DSH_PYTHON = saved
    resetPythonCache()
  }
})

// ── 4. 引擎文件 ─────────────────────────────────────────────────────────────
await section('[4] 打包引擎完整性', async () => {
  const problems = await engineSelftest()
  if (problems.length === 0) pass(`引擎根 ${engineRoot()} 的入口脚本与内核副本齐全`)
  else for (const p of problems) fail(p)

  // 确认没有把案例库打进来（34MB，只服务评测，运行时用不到）
  const heavy = ['liuyao/data/cases', 'bazi/data/cases', 'liuyao/data/sources', 'bazi/data/sources']
  let shipped = 0
  for (const rel of heavy) {
    if (existsSync(join(engineRoot(), rel))) {
      shipped += 1
      fail(`评测用数据被打进了包：${rel}（会白占体积）`)
    }
  }
  if (shipped === 0) pass('未打包 cases/ 与 sources/（评测专用数据不进发布包）')
})

// ── 5. 六爻端到端 ───────────────────────────────────────────────────────────
await section('[5] 六爻端到端（起卦 → 装卦 → 断卦 → 正文）', async () => {
  const argv = buildLiuyaoArgs({ question: '自检占学业', mode: 'manual', yao: '7,8,9,7,6,8' })
  const { chart, analyze, narrative } = await cast('liuyao', argv)

  chart.original_hexagram?.name
    ? pass(`起卦成功：${chart.original_hexagram.name}（${chart.original_hexagram.palace}宫）`)
    : fail('chart 缺 original_hexagram')

  chart.original_hexagram?.yao_lines?.length === 6
    ? pass('六爻齐全（6 条爻线）')
    : fail(`爻线数量异常：${chart.original_hexagram?.yao_lines?.length}`)

  analyze.conclusion?.方向
    ? pass(`断卦结论：${analyze.conclusion.方向}`)
    : fail('analyze 缺 conclusion.方向')

  const useGod = analyze.thinking_chain?.step2_use_god_identification?.use_god_category
  useGod ? pass(`用神识别：${useGod}`) : fail('step2 缺用神')

  narrative && narrative.length > 100
    ? pass(`正文已生成（${narrative.length} 字）`)
    : fail(`正文异常（长度 ${narrative?.length}）`)

  // 铁律三自检：正文不得出现把对齐分说成预测率的表述
  const banned = /预测准确率|预测率\s*[0-9]|断事如神|命中率\s*[0-9]/u
  if (banned.test(narrative)) {
    fail('正文出现「预测准确率/命中率」一类越界表述（违反口径诚实）')
  } else {
    pass('正文无「预测准确率/命中率」类越界表述')
  }
})

// ── 5.5 判据回归：随官入墓不得对同一支位重复计价 ─────────────────────────────
await section('[5.5] 随官入墓去重（用神取世爻时世随/用随是同一件事）', async () => {
  // 乾·全静：世爻上爻戌，官鬼午火墓于戌 → 世随、用随同时命中同一支。
  // 旧实现在这里扣 −1.0 与 −1.5 两遍，把「用神中和」的盘压到大凶。
  const { analyze } = await cast('liuyao', ['--mode', 'manual', '--yao', '7,7,7,7,7,7', '--question', '占问'])
  const s5 = analyze.thinking_chain?.step5_synthesis ?? {}
  const tombAdj = s5.officer_tomb_adjustment
  const strength = analyze.thinking_chain?.step3_strength_analysis?.strength_level

  if (typeof tombAdj !== 'number') {
    fail('取不到 officer_tomb_adjustment')
    return
  }
  // 该盘三场景合计：官鬼入墓 −0.3 + 用随 −1.5 = −1.8；旧实现会到 −2.8
  if (tombAdj >= -1.81) pass(`随官入墓修正为 ${tombAdj}（已去重；旧实现为 −2.8）`)
  else fail(`随官入墓仍是 ${tombAdj} —— 同一支位被重复计价（应为 −1.8）`)

  // 负例自证：判据要能真的分辨「−1.8 与 −2.8」，不能宽到两者都算通过
  const probeOld = -2.8
  if (probeOld >= -1.81) fail('负例失效：旧值 −2.8 竟被判为通过，阈值写错了')
  else pass('负例自证：旧值 −2.8 会被判为失败（阈值可用）')

  strength ? pass(`同盘用神旺衰：${strength}（说明分差来自入墓项而非旺衰）`) : null
})

// ── 6. 八字端到端 ───────────────────────────────────────────────────────────
await section('[6] 八字端到端（排盘 → 格局 → 正文）', async () => {
  const argv = buildBaziArgs({ datetime: '1990-05-20 12:00', gender: '男' })
  const { chart, analyze, narrative } = await cast('bazi', argv)

  const p = chart.pillars ?? {}
  p.year?.ganzhi && p.day?.ganzhi
    ? pass(`排盘成功：${p.year.ganzhi} ${p.month?.ganzhi} ${p.day.ganzhi} ${p.hour?.ganzhi}`)
    : fail('chart 缺四柱')

  analyze.conclusion?.strength
    ? pass(`旺衰：${analyze.conclusion.strength}`)
    : fail('analyze 缺 conclusion.strength')

  analyze.conclusion?.pattern
    ? pass(`格局：${analyze.conclusion.pattern}`)
    : fail('analyze 缺 conclusion.pattern')

  narrative && narrative.length > 50
    ? pass(`正文已生成（${narrative.length} 字）`)
    : fail(`正文异常（长度 ${narrative?.length}）`)

  // ── 273 批：baziValue 结构化岁运字段（大运/流年/流月）────────────────────
  const { runBazi } = await import('../src/tools.mjs')
  const value = await runBazi({ datetime: '1990-05-20 12:00', gender: '男' })
  Array.isArray(value.dayun) && value.dayun.length === 8
    ? pass(`dayun 结构化：8 步（${value.dayun[0].ganzhi}→${value.dayun[7].ganzhi}）`)
    : fail(`dayun 结构化异常（${value.dayun?.length ?? typeof value.dayun}）`)
  Array.isArray(value.liunian) && value.liunian.length === 12 && value.liunian[0].liunian === '庚午'
    ? pass(`liunian 结构化：12 年（${value.liunian[0].year} ${value.liunian[0].liunian} 起），含事件 ${value.liunian.filter((x) => x.events?.length).length} 条`)
    : fail('liunian 结构化异常（应为 12 年且首年 1990 庚午）')
  Array.isArray(value.liuyue) && value.liuyue.length === 12
    ? pass(`liuyue 结构化：12 月（首月 ${value.liuyue[0].ganzhi}）`)
    : fail(`liuyue 结构化异常（${value.liuyue?.length ?? typeof value.liuyue}）`)
  value.conclusion?.strength === '偏弱' && value.conclusion?.pattern === '伤官格'
    ? pass('conclusion 结构化取到旺衰/格局真值')
    : fail(`conclusion 结构化异常（${value.conclusion?.strength}/${value.conclusion?.pattern}）`)
  value.conclusion?.xunkong
    ? pass(`verdict 平铺：空亡=${value.conclusion.xunkong}`)
    : fail('conclusion.xunkong 为空（verdicts 平铺失效）')
})

// ── 7. 参数校验 ─────────────────────────────────────────────────────────────
await section('[7] 参数语义校验（缺必填要报错，不能蒙混）', async () => {
  try {
    buildLiuyaoArgs({ question: 'x', mode: 'manual' })
    fail('负例失效：mode=manual 缺 yao 竟未报错')
  } catch {
    pass('mode=manual 缺 yao 会报错')
  }
  try {
    buildLiuyaoArgs({ question: 'x', mode: 'number' })
    fail('负例失效：mode=number 缺 numbers 竟未报错')
  } catch {
    pass('mode=number 缺 numbers 会报错')
  }
})

// ── 8. 打包引擎与两科真源的一致性 ───────────────────────────────────────────────
await section('[8] 打包产物与两科真源一致（防「悄悄过期」：引擎 + 知识库全覆盖）', async () => {
  const { readFileSync: rf } = await import('node:fs')
  const { readdir } = await import('node:fs/promises')
  const { createHash } = await import('node:crypto')
  const repoRoot = resolve(PLUGIN_ROOT, '..')
  const digest = (p) => createHash('sha256').update(rf(p)).digest('hex').slice(0, 16)

  /** 递归列出相对路径（跳过 __pycache__/*.pyc）。 */
  async function walk(dir, base = '') {
    const out = []
    let entries
    try {
      entries = await readdir(dir, { withFileTypes: true })
    } catch {
      return out
    }
    for (const e of entries) {
      const rel = base ? `${base}/${e.name}` : e.name
      if (e.isDirectory()) {
        if (e.name === '__pycache__') continue
        out.push(...(await walk(join(dir, e.name), rel)))
      } else if (!/\.(pyc|pyo)$/u.test(e.name)) {
        out.push(rel)
      }
    }
    return out
  }

  // ── 8a 引擎：逐文件全量对拍（不是抽一个） ──────────────────────────────────
  // 包内副本一旦落后于真源，插件跑的就是旧口径；只抽查一个文件等于给「其余 137 个
  // 悄悄过期」留后门。本仓历史事故正是「同一批表多存一份且取值不一致」。
  let engineChecked = 0
  let engineStale = 0
  for (const discipline of ['liuyao', 'bazi']) {
    const packagedRoot = join(engineRoot(), discipline)
    const files = await walk(packagedRoot)
    for (const rel of files) {
      // 打包时额外放进去的随包文档（README/SKILL）不在真源同级，跳过比对但计数
      const srcPath = join(repoRoot, discipline, rel)
      if (!existsSync(srcPath)) continue
      engineChecked += 1
      if (digest(srcPath) !== digest(join(packagedRoot, rel))) {
        engineStale += 1
        if (engineStale <= 3) fail(`已过期：${discipline}/${rel}`)
      }
    }
  }
  if (engineStale === 0) {
    pass(`引擎 ${engineChecked} 个文件逐个与真源一致（无过期副本）`)
  } else {
    fail(`引擎共 ${engineStale}/${engineChecked} 个文件过期 → 请跑 node ../plugins/scripts/build.mjs`)
  }

  // ── 8b 知识库：随包 skills/references 与两科 references 逐篇对拍 ────────────
  let kbChecked = 0
  let kbStale = 0
  for (const discipline of ['liuyao', 'bazi']) {
    const srcDir = join(repoRoot, discipline, 'references')
    const pkgDir = join(PLUGIN_ROOT, 'skills', 'yi-divination', 'references', discipline)
    const files = await walk(pkgDir)
    for (const rel of files) {
      if (rel === 'INDEX.md') continue // 生成的索引，无真源
      const srcPath = join(srcDir, rel)
      if (!existsSync(srcPath)) {
        fail(`知识库文件无真源：${discipline}/${rel}`)
        continue
      }
      kbChecked += 1
      if (digest(srcPath) !== digest(join(pkgDir, rel))) {
        kbStale += 1
        fail(`知识库过期：${discipline}/${rel} → 请跑 node ../plugins/scripts/build.mjs`)
      }
    }
  }
  if (kbStale === 0 && kbChecked > 0) {
    pass(`知识库 ${kbChecked} 篇逐篇与两科 references 一致`)
  } else if (kbChecked === 0) {
    fail('知识库一篇都没比对上——疑似 build-skills 没跑或目录结构变了')
  }

  // ── 8c 反向覆盖：真源有的判据表，包里不能漏 ────────────────────────────────
  // 上面 8a 只证明「包里有的都对」，不证明「该有的都在」。漏收比过期更隐蔽：
  // 模型调用某个分支时才炸。这里对 references 做反向核对（案例库按铁律二豁免）。
  let missing = 0
  for (const discipline of ['liuyao', 'bazi']) {
    const srcDir = join(repoRoot, discipline, 'references')
    const pkgDir = join(PLUGIN_ROOT, 'skills', 'yi-divination', 'references', discipline)
    for (const rel of await walk(srcDir)) {
      if (rel === 'case_library.md') continue // 铁律二：刻意不随包
      if (!existsSync(join(pkgDir, rel))) {
        missing += 1
        fail(`真源有、包里缺：${discipline}/references/${rel}`)
      }
    }
  }
  if (missing === 0) pass('反向覆盖：两科 references 已全部收录（案例库按铁律二豁免）')

  // ── 负例自证 ───────────────────────────────────────────────────────────────
  const a = digest(join(repoRoot, 'liuyao', 'SKILL.md'))
  const b = digest(join(repoRoot, 'bazi', 'SKILL.md'))
  if (a === b) fail('负例失效：两个不同文件算出了相同指纹，判据不可信')
  else pass('负例自证：不同内容的文件指纹不同，本段判据可用')
})

// ── 10. Agent preset 声明合法性（真机踩过的两个方言坑）──────────────────────
await section('[10] Agent preset 声明（补丁方言 / 子插件 / 技能根）', async () => {
  const { readFileSync: rf } = await import('node:fs')
  const presetPath = join(PLUGIN_ROOT, 'presets', 'yi-divination.yml')
  const text = rf(presetPath, 'utf8')

  // 坑①：补丁层里新增插件必须写成 `- insert:`；裸 `- id:` 会被当成「改已有行」
  const hasInsert = /^-\s*insert:/mu.test(text)
  if (hasInsert) pass('顶层条目使用 `- insert:`（否则宿主报 entry not found 并跳过）')
  else fail('顶层条目缺 `- insert:` —— 裸 `- id:` 不会新增插件，等于没装')

  // 坑②：preset 的 config.id 与行 id 是两回事，两者都要有
  const hasPresetId = /^\s+-\s*id:\s*preset-yi-divination/mu.test(text)
  const hasConfigId = /^\s+id:\s*yi-divination$/mu.test(text)
  if (hasPresetId && hasConfigId) pass('行 id 与 config.id 都在（前者是编辑地址，后者是会话标识）')
  else fail(`行 id=${hasPresetId} / config.id=${hasConfigId}，缺一不可`)

  // 子插件列表必须含本插件，且技能根指向包内 skills/
  if (/^\s+-\s*name:\s*dsh-yi-divination$/mu.test(text)) pass('子插件列表含 dsh-yi-divination')
  else fail('子插件列表缺少 dsh-yi-divination')

  const hasBundledDir = /bundledSkillDir:/u.test(text)
  if (hasBundledDir) pass('技能根用官方 bundledSkillDir 挂载')
  else fail('缺 bundledSkillDir：随包知识库将无法被发现')

  // 负例自证：把 insert 行抹掉后，判据必须报红
  const broken = text.replace(/^-\s*insert:/mu, '- id:')
  const brokenHasInsert = /^-\s*insert:/mu.test(broken)
  if (brokenHasInsert) fail('负例失效：抹掉 insert 后判据仍认为合法，判据不可信')
  else pass('负例自证：抹掉 insert 关键字能被判出不合规')
})

// ── 11. 安装脚本的 YAML 合并安全性 ──────────────────────────────────────────
await section('[11] 安装脚本不会破坏 profile 补丁（空列表 / 幂等）', async () => {
  const { execFileSync } = await import('node:child_process')
  const fsp = await import('node:fs/promises')
  const os = await import('node:os')

  const tmp = await fsp.mkdtemp(join(os.tmpdir(), 'yiprobe-'))
  const patchPath = join(tmp, 'cordis.patch.yml')
  try {
    // 场景 A：默认模板是空 flow sequence `[]` —— 追加会产出非法 YAML，必须被替换
    await fsp.writeFile(patchPath, '# comment\n[]\n', 'utf8')
    execFileSync(process.execPath, [join(PLUGIN_ROOT, 'scripts', 'install-preset.mjs'), '_x', '--profile-root', tmp], {
      stdio: 'pipe',
    })
    const merged = await fsp.readFile(patchPath, 'utf8')
    const stillEmptyFlow = /^\[\]$/mu.test(merged) && /- insert:/u.test(merged)
    if (stillEmptyFlow) fail('空 `[]` 与列表条目共存 —— YAML 会解析失败（真机实测过）')
    else if (/- insert:/u.test(merged)) pass('空列表被正确替换为 `- insert:` 序列')

    // 场景 B：幂等 —— 再跑一次不应新增第二份
    const before = await fsp.readFile(patchPath, 'utf8')
    execFileSync(process.execPath, [join(PLUGIN_ROOT, 'scripts', 'install-preset.mjs'), '_x', '--profile-root', tmp], {
      stdio: 'pipe',
    })
    const after = await fsp.readFile(patchPath, 'utf8')
    if (before === after) pass('重复运行不改动文件（幂等）')
    else fail('重复运行改变了补丁层内容 —— 会重复插入')
  } finally {
    await fsp.rm(tmp, { recursive: true, force: true })
  }
})

// ── 9. 引擎目录保持干净（不被运行期派生文件污染）────────────────────────────
await section('[9] 引擎目录未被派生文件污染', async () => {
  const { readdir } = await import('node:fs/promises')

  async function scan(dir, hits = []) {
    let entries
    try {
      entries = await readdir(dir, { withFileTypes: true })
    } catch {
      return hits
    }
    for (const e of entries) {
      const p = join(dir, e.name)
      if (e.isDirectory()) {
        if (e.name === '__pycache__') hits.push(p)
        else await scan(p, hits)
      } else if (/\.(pyc|pyo)$/u.test(e.name)) {
        hits.push(p)
      }
    }
    return hits
  }

  const dirty = await scan(engineRoot())
  if (dirty.length === 0) {
    pass('无 __pycache__/*.pyc（已设 PYTHONDONTWRITEBYTECODE）')
  } else {
    fail(
      `引擎目录出现 ${dirty.length} 个派生文件，首例：${dirty[0]}\n` +
        '    这会让发布包虚胖约 1.2MB，且在只读安装位上可能写入失败。' +
        '请确认子进程 env 带 PYTHONDONTWRITEBYTECODE=1，并跑 build-engine 重建。',
    )
  }

  // 负例自证：判据必须能认出真的 __pycache__ 目录名，否则它是瞎的。
  const probe = join(engineRoot(), '_probe_', '__pycache__')
  await (await import('node:fs/promises')).mkdir(probe, { recursive: true })
  const probeHits = await scan(join(engineRoot(), '_probe_'))
  await (await import('node:fs/promises')).rm(join(engineRoot(), '_probe_'), { recursive: true, force: true })
  if (probeHits.length === 0) fail('负例失效：造出来的 __pycache__ 没被扫到，本段判据是死的')
  else pass('负例自证：造一个 __pycache__ 能被扫到（已清理）')
})

// ── 12. yi_kb 判据知识库检索 ────────────────────────────────────────────────
await section('[12] yi_kb 判据知识库检索（含铁律二扫描层排除）', async () => {
  const fsp = await import('node:fs/promises')
  const os = await import('node:os')
  const { runKb, searchKb, listKbFiles } = await import('../src/kb.mjs')

  // 真库端到端：纳甲相关 query 应召回 najia_rules.md（考召回不考排名）
  const r1 = await runKb({ query: '纳甲 装卦 世应' })
  r1.files_scanned >= 9
    ? pass(`扫描 ${r1.files_scanned} 篇`)
    : fail(`扫描篇数异常：${r1.files_scanned}（应 ≥9）`)
  r1.matches.length >= 1
    ? pass(`命中 ${r1.matches.length} 条，首条 ${r1.matches[0].file}:${r1.matches[0].line} §${r1.matches[0].title}`)
    : fail('真库检索零命中')
  r1.matches.some((m) => m.file.includes('najia_rules'))
    ? pass('召回包含 najia_rules.md')
    : fail(`未召回 najia_rules.md：${r1.matches.map((m) => m.file).join(', ')}`)
  r1.matches[0]?.snippet
    ? pass(`摘录非空（${r1.matches[0].snippet.length} 字）`)
    : fail('首条摘录为空')

  // 2-gram 兜底：无空格长 query 整串不在库中，靠二字窗仍应召回（考召回不考排名）
  const rb = await runKb({ query: '世应怎么安' })
  rb.matches.length >= 1
    ? pass(`2-gram 兜底召回 ${rb.matches.length} 条`)
    : fail('2-gram 兜底失效：「世应怎么安」零命中')
  rb.matches.some((m) => m.file.includes('najia_rules'))
    ? pass('2-gram 兜底召回包含 najia_rules.md')
    : fail(`2-gram 兜底未召回 najia_rules.md：${rb.matches.map((m) => m.file).join(', ')}`)
  rb.expanded?.bigrams?.includes('世应')
    ? pass('2-gram 展开清单可复核（expanded.bigrams）')
    : fail(`expanded.bigrams 异常：${JSON.stringify(rb.expanded?.bigrams)}`)

  // 同义词展开：库里没有「用爻」，展开成「用神」后应召回（考展开不考排名）
  const rs = await runKb({ query: '用爻' })
  rs.matches.length >= 1
    ? pass(`同义词展开召回 ${rs.matches.length} 条`)
    : fail('同义词展开失效：「用爻」零命中')
  rs.expanded?.synonyms?.includes('用神') && rs.matches[0]?.snippet?.includes('用神')
    ? pass('同义词展开：用爻→用神（摘录含「用神」可复核）')
    : fail(`同义词展开异常：${JSON.stringify(rs.expanded?.synonyms)} / ${(rs.matches[0]?.snippet ?? '').slice(0, 40)}`)

  // 学科过滤：discipline=bazi 时命中必须全在 bazi/ 下
  const r2 = await runKb({ query: '十神', discipline: 'bazi' })
  const wrong = r2.matches.filter((m) => !m.file.startsWith('bazi/'))
  wrong.length === 0
    ? pass(`discipline=bazi 过滤生效（${r2.matches.length} 条全在 bazi/）`)
    : fail(`过滤失效：${wrong.map((w) => w.file).join(', ')}`)

  // 无关词：不报错、不编造，返回空匹配。
  // （2-gram 兜底上线后，探针词的每个 ≥3 字汉字串的二字窗也必须不在库中——
  //   旧探针「不存在的词」的二字窗「存在」在库中大量出现，已换。）
  const r3 = await runKb({ query: '汽车维修zzz量子塌缩' })
  r3.matches.length === 0
    ? pass('无关词返回空匹配（不编造结果）')
    : fail(`无关词竟有匹配：${r3.matches.map((m) => m.file).join(', ')}`)

  // 缺 query 必须报错（对齐 [7] 参数语义校验口径）
  try {
    await runKb({})
    fail('负例失效：缺 query 竟未报错')
  } catch {
    pass('缺 query 会报错')
  }

  // 铁律二（扫描层）：case_library.md 即使被放进知识库目录也检不到
  const tmp = await fsp.mkdtemp(join(os.tmpdir(), 'yikb-'))
  try {
    const dir = join(tmp, 'liuyao')
    await fsp.mkdir(dir, { recursive: true })
    await fsp.writeFile(join(dir, 'case_library.md'), '# 案例库\n\n探针词青龙伏吟不存在的案例库内容zzz\n', 'utf8')
    const listed = await listKbFiles(tmp)
    listed.length === 0
      ? pass('扫描层排除：case_library.md 不在可检索清单')
      : fail(`扫描层漏排：${listed.join(', ')}`)
    const r4 = await searchKb({ query: '探针词青龙伏吟', kbRoot: tmp })
    r4.matches.length === 0
      ? pass('检索层排除：对 case_library.md 内容的检索零命中')
      : fail(`检索漏排：${JSON.stringify(r4.matches[0])}`)
    // 负例自证：文件确实在那里——排除来自判据，不是目录为空
    const exists = await fsp
      .stat(join(dir, 'case_library.md'))
      .then(() => true, () => false)
    exists
      ? pass('负例自证：探针文件确实存在（排除来自判据而非目录为空）')
      : fail('负例失效：探针文件没写成功，本段排除判据未被真正考验')
  } finally {
    await fsp.rm(tmp, { recursive: true, force: true })
  }
})

// ── 13. 报告工具（274 批）：引擎 render 段 + 插件排版层 + 落文件 ─────────────
await section('[13] yi_report 报告（六爻引擎 HTML / 八字排版层 HTML / 落文件 / 负例）', async () => {
  const { runReport } = await import('../src/tools.mjs')
  const { stat } = await import('node:fs/promises')

  const bl = await runReport({ discipline: 'liuyao', question: '占今日工作进展', mode: 'time' })
  bl.format === 'html' && bl.path.endsWith('.html')
    ? pass(`六爻报告（引擎 render 段）：${Math.round(bl.bytes / 1024)} KB`)
    : fail(`六爻报告异常：${bl.format} ${bl.path}`)
  const lTxt = await import('node:fs/promises').then((m) => m.readFile(bl.path, 'utf8'))
  lTxt.includes('<html') && lTxt.includes('爻')
    ? pass('六爻报告含完整 HTML 与卦象内容')
    : fail('六爻报告内容异常（缺 <html> 或爻）')

  const bb = await runReport({ discipline: 'bazi', datetime: '1990-05-20 12:00', gender: '男' })
  bb.format === 'html' && bb.bytes > 2000
    ? pass(`八字报告（插件排版层）：${Math.round(bb.bytes / 1024)} KB`)
    : fail(`八字报告异常：${bb.format} ${bb.bytes}B`)
  const bTxt = await import('node:fs/promises').then((m) => m.readFile(bb.path, 'utf8'))
  bTxt.includes('四柱') && bTxt.includes('壬午') && bTxt.includes('古籍案例对齐分')
    ? pass('八字报告含四柱卡/大运/口径页脚（文字全部来自引擎字段）')
    : fail('八字报告内容异常（缺四柱/干支/口径页脚）')

  const bm = await runReport({ discipline: 'bazi', datetime: '1990-05-20 12:00', gender: '男', format: 'md' })
  bm.format === 'md'
    ? pass('八字 md 报告（引擎 render 段）可出')
    : fail('八字 md 报告异常')
  for (const p of [bl.path, bb.path, bm.path]) {
    const ok = await stat(p).then(() => true, () => false)
    if (!ok) fail(`报告文件未落盘：${p}`)
  }

  try {
    await runReport({ discipline: 'tarot', datetime: '1990-05-20 12:00', gender: '男' })
    fail('负例失效：discipline=tarot 竟未报错')
  } catch {
    pass('负例自证：discipline 非法时明确报错')
  }
})

console.log('\n' + '='.repeat(52))
if (failures === 0) {
  console.log('自检全部通过。')
  process.exitCode = 0
} else {
  console.log(`自检未通过：${failures} 处失败。`)
  process.exitCode = 1
}
