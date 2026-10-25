/**
 * 引擎调用层：把 dsh-plugin/engine/ 下的术数引擎当成「确定性计算器」来用。
 *
 * 三条硬约定（与仓库 AGENTS.md §一 一致，插件不得放宽）：
 *  1. **机械运算归代码**：起卦、排盘、装卦、旺衰、应期、格局全部由 Python 产出，
 *     node 侧只做参数搬运与结果整形，绝不重算任何象数结论。
 *  2. **子进程失败不许降级**：引擎非 0 退出或输出不是 JSON，就抛错——
 *     不返回「大概的」结果，不让模型拿半成品去断卦。
 *  3. **不写用户目录**：中间产物一律落临时目录，用完即删（仓库 §四.8 的夹具纪律）。
 */
import { spawn } from 'node:child_process'
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { resolvePython } from './python.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
/** 打包后的引擎根：<pkg>/engine/（src/ 与 lib/ 深度不同，故按目录名判定）。 */
export function engineRoot() {
  const base = dirname(HERE)
  return join(base, 'engine')
}

/** 各学科的入口脚本与约定（唯一真值源；新增学科只改这里）。 */
const DISCIPLINES = {
  liuyao: {
    label: '六爻（纳甲）',
    chartScript: ['scripts', 'chart.py'],
    analyzeScript: ['scripts', 'analyze.py'],
    narrateScript: ['scripts', 'narrate.py'],
    reportScript: ['scripts', 'render.py'],
  },
  bazi: {
    label: '八字（四柱）',
    chartScript: ['scripts', 'chart.py'],
    analyzeScript: ['scripts', 'analyze.py'],
    narrateScript: ['scripts', 'narrate.py'],
    reportScript: ['scripts', 'render.py'],
  },
}

export function disciplineNames() {
  return Object.keys(DISCIPLINES)
}

export function disciplineInfo(name) {
  const d = DISCIPLINES[name]
  if (!d) throw new Error(`未知学科：${name}（可用：${disciplineNames().join(' / ')}）`)
  return d
}

/** 跑一次 python，返回 { code, stdout, stderr }。超时与取消都走 signal。 */
function runPython(command, args, { cwd, signal, timeoutMs = 120_000 } = {}) {
  return new Promise((resolvePromise, reject) => {
    const child = spawn(command, args, {
      cwd,
      signal,
      windowsHide: true,
      env: {
        ...process.env,
        PYTHONIOENCODING: 'utf-8',
        // 禁写 .pyc：引擎目录是**只读的打包产物**，让它就地生成 __pycache__
        // 会在用户机器上悄悄长出 ≈1.2MB 派生文件；在 npm 包里/只读安装位上
        // 还可能直接写失败。启动开销的代价远小于「包里莫名多出文件」。
        PYTHONDONTWRITEBYTECODE: '1',
      },
    })
    let stdout = ''
    let stderr = ''
    let settled = false
    const timer = setTimeout(() => {
      if (settled) return
      settled = true
      child.kill()
      reject(new Error(`引擎执行超时（${timeoutMs}ms）：${args.join(' ')}`))
    }, timeoutMs)

    child.stdout.setEncoding('utf8')
    child.stderr.setEncoding('utf8')
    child.stdout.on('data', (d) => (stdout += d))
    child.stderr.on('data', (d) => (stderr += d))
    child.on('error', (err) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      reject(err)
    })
    child.on('close', (code) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      resolvePromise({ code, stdout, stderr })
    })
  })
}

/** 从可能夹带警告行的 stdout 里抠出 JSON（引擎正常时整段就是 JSON）。 */
function extractJson(text) {
  const start = text.indexOf('{')
  if (start < 0) throw new Error(`引擎输出不含 JSON：${text.slice(0, 300)}`)
  const end = text.lastIndexOf('}')
  if (end < start) throw new Error(`引擎输出的 JSON 不完整：${text.slice(start, start + 300)}`)
  return JSON.parse(text.slice(start, end + 1))
}

/**
 * 执行一个学科脚本族。
 * @param {string} discipline liuyao | bazi
 * @param {'chart'|'analyze'|'narrate'} stage
 * @param {string[]} extraArgs
 */
async function runStage(discipline, stage, extraArgs, { signal } = {}) {
  const info = disciplineInfo(discipline)
  const root = join(engineRoot(), discipline)
  const script = join(root, ...info[`${stage}Script`])
  const { command } = await resolvePython()

  const { code, stdout, stderr } = await runPython(command, [script, ...extraArgs], {
    cwd: root,
    signal,
  })

  if (code !== 0) {
    throw new Error(
      `${info.label} ${stage} 阶段失败（退出码 ${code}）\n` +
        `stderr: ${stderr.trim().slice(0, 1200) || '（空）'}`,
    )
  }
  return { stdout, stderr }
}

/**
 * 一起卦/排盘：chart 阶段产出排盘 JSON。
 * @param {string} discipline
 * @param {string[]} args 直接透传给 chart.py 的参数
 */
export async function chart(discipline, args, options = {}) {
  const { stdout } = await runStage(discipline, 'chart', args, options)
  return extractJson(stdout)
}

/**
 * 推演：analyze 阶段读 chart JSON，产出含 conclusion 与 thinking_chain 的结果。
 * @param {string} discipline
 * @param {object} chartJson
 */
export async function analyze(discipline, chartJson, options = {}) {
  const dir = await mkdtemp(join(tmpdir(), 'yi-dsh-'))
  try {
    const chartPath = join(dir, 'chart.json')
    const analyzePath = join(dir, 'analyze.json')
    await writeFile(chartPath, JSON.stringify(chartJson), 'utf8')
    await runStage(discipline, 'analyze', [chartPath, '-o', analyzePath], options)
    const raw = await readFile(analyzePath, 'utf8')
    return extractJson(raw)
  } finally {
    await rm(dir, { recursive: true, force: true })
  }
}

/** 正文：narrate 阶段把 analyze JSON 翻成人话。 */
export async function narrate(discipline, analyzeJson, options = {}) {
  const dir = await mkdtemp(join(tmpdir(), 'yi-dsh-'))
  try {
    const analyzePath = join(dir, 'analyze.json')
    await writeFile(analyzePath, JSON.stringify(analyzeJson), 'utf8')
    const { stdout } = await runStage(discipline, 'narrate', [analyzePath], options)
    return stdout.trim()
  } finally {
    await rm(dir, { recursive: true, force: true })
  }
}

/** 一步到位：chart → analyze → narrate。失败任一步即抛错，不返回半成品。 */
export async function cast(discipline, chartArgs, options = {}) {
  const chartJson = await chart(discipline, chartArgs, options)
  const analyzeJson = await analyze(discipline, chartJson, options)
  const narrative = await narrate(discipline, analyzeJson, options)
  return { chart: chartJson, analyze: analyzeJson, narrative }
}

/**
 * 报告：render 阶段把 analyze JSON 渲染成报告全文（引擎自己的报告器，插件不重写判据）。
 * liuyao 支持 fmt='html'（render.py 单文件 HTML）与 'md'；bazi 只有 md。
 * @returns {string} 报告全文（stdout）
 */
export async function report(discipline, analyzeJson, { fmt = 'md', signal } = {}) {
  const dir = await mkdtemp(join(tmpdir(), 'yi-dsh-'))
  try {
    const analyzePath = join(dir, 'analyze.json')
    await writeFile(analyzePath, JSON.stringify(analyzeJson), 'utf8')
    const extra = discipline === 'liuyao' ? ['-f', fmt === 'html' ? 'html' : 'md'] : []
    const { stdout } = await runStage(discipline, 'report', [analyzePath, ...extra], { signal })
    return stdout
  } finally {
    await rm(dir, { recursive: true, force: true })
  }
}

/** 引擎自检：确认打包的引擎目录与入口脚本都在。 */
export async function selftest() {
  const problems = []
  const root = engineRoot()
  const { existsSync } = await import('node:fs')
  for (const name of disciplineNames()) {
    const info = disciplineInfo(name)
    for (const stage of ['chart', 'analyze', 'narrate']) {
      const p = join(root, name, ...info[`${stage}Script`])
      if (!existsSync(p)) problems.push(`缺少入口脚本：${name}/${stage} → ${p}`)
    }
    const core = join(root, name, 'core', 'yishu_core')
    if (!existsSync(core)) problems.push(`缺少内核副本：${core}`)
  }
  if (!existsSync(root)) problems.push(`引擎根目录不存在：${root}`)
  return problems
}

export { resolve, engineRoot as packageRoot }
