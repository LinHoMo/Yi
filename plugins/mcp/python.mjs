/**
 * 定位用于执行术数引擎的 Python 解释器（**全宿主唯一一份**）。
 *
 * 305 批前，`dsh-plugin/src/python.mjs` 与 `yan-plugin/src/python.mjs` 是两份只差
 * 第一档的副本——正是 AGENTS.md §二 警告过的「同表多存」形态。现在合成一份，
 * 每个宿主只走自己那一档，其余同序。
 *
 * 优先级（每一档都为「已实测存在」而设计，而不是「大概在某处」）：
 *  1. `DSH_PYTHON` 显式覆盖（DSH 宿主；运维/调试用，也便于 CI 钉死版本）。
 *  2. `YI_PYTHON` 显式覆盖（Yan 宿主：由插件配置项 pythonPath 注入）。
 *  3. DSH 桌面自带运行时：`$DSH_HOME/dsh-runtimes/*\/dependencies/python/python.exe`。
 *     实测本机为 3.12.14。这是**DSH 侧的首选**：用户装了 DSH 就有，不需另装 Python。
 *  4. 环境变量里的 `python` / `python3`（PATH 解析）。
 *  5. Windows 的 `py` 启动器。
 *
 * 找不到就抛错并**把已尝试的路径逐条列出**——静默回退到「系统随便哪个 python」
 * 会让不同机器跑出不同结果，而本仓全部口径都建立在「同一份确定性引擎」上。
 */
import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { readdir } from 'node:fs/promises'
import { join } from 'node:path'

let cached = null

function isExecutable(path) {
  return existsSync(path)
}

/**
 * 探活：存在一个可执行文件 ≠ 它是能用的 Python。
 *
 * Windows 上最典型的坑：微软商店的 **应用执行别名** `python.exe`（0 字节占位），
 * `existsSync` 为真、spawn 后只会弹商店、退出码非 0。306 批前只判存在，
 * 于是"装了 Python"的机器上第一次起卦就崩在一个打不开的解释器上。
 * 这里用一次 `-c` 探针（8s 超时）确认它真能跑，结果随 resolvePython 一起缓存。
 */
function usable(command) {
  return new Promise((resolvePromise) => {
    let child
    try {
      child = spawn(command, ['-c', 'import sys;sys.stdout.write("ok")'], {
        windowsHide: true,
        stdio: ['ignore', 'pipe', 'pipe'],
      })
    } catch {
      resolvePromise(false)
      return
    }
    let out = ''
    let settled = false
    const finish = (value) => {
      if (settled) return
      settled = true
      try {
        child.kill()
      } catch {
        /* 已退出 */
      }
      resolvePromise(value)
    }
    child.stdout?.on('data', (d) => (out += d))
    child.on('error', () => finish(false))
    child.on('close', (code) => finish(code === 0 && out.includes('ok')))
    setTimeout(() => finish(false), 8000)
  })
}

/** 在 PATH 中查找可执行文件（不 spawn，避免为「能不能用」付出进程开销）。 */
function findOnPath(names) {
  const sep = process.platform === 'win32' ? ';' : ':'
  const exts = process.platform === 'win32' ? ['.exe', '.cmd', '.bat', ''] : ['']
  const dirs = (process.env.PATH ?? process.env.Path ?? '').split(sep).filter(Boolean)
  for (const name of names) {
    for (const dir of dirs) {
      for (const ext of exts) {
        const candidate = join(dir, name + ext)
        if (isExecutable(candidate)) return candidate
      }
    }
  }
  return null
}

/** 枚举 DSH 自带运行时里的 python.exe（按目录名排序，取第一个可用的）。 */
async function findBundledPython(dshHome, attempted) {
  if (!dshHome) return null
  const runtimesDir = join(dshHome, 'dsh-runtimes')
  if (!isExecutable(runtimesDir)) return null
  let runtimes
  try {
    runtimes = (await readdir(runtimesDir, { withFileTypes: true }))
      .filter((e) => e.isDirectory())
      .map((e) => e.name)
      .sort()
  } catch {
    return null
  }
  for (const runtime of runtimes) {
    for (const rel of [
      ['dependencies', 'python', 'python.exe'],
      ['dependencies', 'python', 'bin', 'python3'],
    ]) {
      const candidate = join(runtimesDir, runtime, ...rel)
      attempted.push(candidate)
      if (isExecutable(candidate)) return candidate
    }
  }
  return null
}

/**
 * @param {{ dshHome?: string }} [options]
 * @returns {Promise<{ command: string, source: string }>}
 */
export async function resolvePython(options = {}) {
  const dshHome = options.dshHome ?? process.env.DSH_HOME ?? null
  const cacheKey = `${process.env.DSH_PYTHON ?? ''}\u0000${process.env.YI_PYTHON ?? ''}\u0000${dshHome ?? ''}`
  if (cached && cached.key === cacheKey) return cached.value

  const attempted = []
  const rejected = []

  // 1) + 2) 宿主各自的显式覆盖变量：指了就必须能用，否则直接报错（不悄悄回退）
  for (const [name, source] of [
    ['DSH_PYTHON', 'DSH_PYTHON'],
    ['YI_PYTHON', 'YI_PYTHON'],
  ]) {
    const override = process.env[name]
    if (!override) continue
    attempted.push(override)
    if (!isExecutable(override)) {
      throw new Error(
        `${name} 指向的路径不存在：${override}\n已尝试：\n  ${attempted.join('\n  ')}`,
      )
    }
    if (!(await usable(override))) {
      throw new Error(
        `${name} 指向的文件不能作为 Python 运行：${override}\n` +
          '（Windows 上常见的是微软商店的「应用执行别名」占位文件——' +
          '请在插件配置里填真正的 python.exe 绝对路径，或关掉该别名）',
      )
    }
    const value = { command: override, source }
    cached = { key: cacheKey, value }
    return value
  }

  // 3) DSH 桌面自带运行时（Yan 宿主下 DSH_HOME 一般不存在，自然跳过）
  const bundled = await findBundledPython(dshHome, attempted)
  if (bundled && (await usable(bundled))) {
    const value = { command: bundled, source: 'dsh-runtime' }
    cached = { key: cacheKey, value }
    return value
  }

  // 4) + 5) PATH 与 Windows py 启动器（逐个探活，跳过空壳别名）
  for (const [name, source] of [
    ['python', 'PATH'],
    ['python3', 'PATH'],
    ['py', 'py-launcher'],
  ]) {
    const found = findOnPath([name])
    if (!found) continue
    attempted.push(found)
    if (!(await usable(found))) {
      rejected.push(`${found}（存在但不可执行，疑似应用执行别名）`)
      continue
    }
    const value = { command: found, source }
    cached = { key: cacheKey, value }
    return value
  }

  throw new Error(
    '找不到可用的 Python 解释器，六爻/八字引擎无法运行。\n' +
      '请任选其一：\n' +
      '  · 安装 DeepSeek Harness 桌面版（自带 Python 运行时，插件会自动发现）\n' +
      '  · 安装 Python 3.10+ 并确保在 PATH 中（Windows 官方安装器勾选 Add python.exe to PATH）\n' +
      '  · 设置 DSH_PYTHON（DSH）或 YI_PYTHON（Yan，插件配置「Python 解释器路径」）指向 python 可执行文件\n' +
      `已尝试的路径：\n  ${attempted.length ? attempted.join('\n  ') : '（无）'}` +
      (rejected.length ? `\n已跳过（存在但跑不起来）：\n  ${rejected.join('\n  ')}` : ''),
  )
}

/** 仅供测试：清掉进程内缓存。 */
export function resetPythonCache() {
  cached = null
}
