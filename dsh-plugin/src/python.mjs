/**
 * 定位用于执行术数引擎的 Python 解释器。
 *
 * 优先级（每一档都为「已实测存在」而设计，而不是「大概在某处」）：
 *  1. `DSH_PYTHON` 显式覆盖——运维/调试用，也便于 CI 钉死版本。
 *  2. DSH 桌面自带运行时：`$DSH_HOME/dsh-runtimes/*\/dependencies/python/python.exe`。
 *     实测本机为 3.12.14（runtime.json 的 `python` 字段）。这是**首选**：
 *     用户装了 DSH 就有，不需要另装 Python，插件因此真正「装了即用」。
 *  3. 环境变量里的 `python` / `python3`（PATH 解析）。
 *  4. Windows 的 `py` 启动器。
 *
 * 找不到就抛错并**把已尝试的路径逐条列出**——静默回退到「系统随便哪个 python」
 * 会让不同机器跑出不同结果，而本仓全部口径都建立在「同一份确定性引擎」上。
 */
import { existsSync } from 'node:fs'
import { readdir } from 'node:fs/promises'
import { join } from 'node:path'

/** 说明：本模块只做定位，不缓存结果以外的副作用；缓存键含 DSH_HOME。 */
let cached = null

function isExecutable(path) {
  return existsSync(path)
}

/** 在 PATH 中查找可执行文件（不 spawn，避免为「能不能用」付出进程开销）。 */
function findOnPath(names) {
  const sep = process.platform === 'win32' ? ';' : ':'
  const exts = process.platform === 'win32' ? ['.exe', '.cmd', '.bat', ''] : ['']
  const dirs = (process.env.PATH ?? '').split(sep).filter(Boolean)
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
  const cacheKey = `${process.env.DSH_PYTHON ?? ''}\u0000${dshHome ?? ''}`
  if (cached && cached.key === cacheKey) return cached.value

  const attempted = []

  if (process.env.DSH_PYTHON) {
    const override = process.env.DSH_PYTHON
    attempted.push(override)
    if (isExecutable(override)) {
      const value = { command: override, source: 'DSH_PYTHON' }
      cached = { key: cacheKey, value }
      return value
    }
    throw new Error(
      `DSH_PYTHON 指向的路径不存在：${override}\n` + `已尝试：\n  ${attempted.join('\n  ')}`,
    )
  }

  const bundled = await findBundledPython(dshHome, attempted)
  if (bundled) {
    const value = { command: bundled, source: 'dsh-runtime' }
    cached = { key: cacheKey, value }
    return value
  }

  const onPath = findOnPath(['python', 'python3'])
  if (onPath) {
    attempted.push(onPath)
    const value = { command: onPath, source: 'PATH' }
    cached = { key: cacheKey, value }
    return value
  }

  const pyLauncher = findOnPath(['py'])
  if (pyLauncher) {
    attempted.push(pyLauncher)
    const value = { command: pyLauncher, source: 'py-launcher' }
    cached = { key: cacheKey, value }
    return value
  }

  throw new Error(
    '找不到可用的 Python 解释器，六爻/八字引擎无法运行。\n' +
      '请任选其一：\n' +
      '  · 安装 DeepSeek Harness 桌面版（自带 Python 运行时，插件会自动发现）\n' +
      '  · 安装 Python 3.10+ 并确保在 PATH 中\n' +
      '  · 设置环境变量 DSH_PYTHON 指向 python 可执行文件的绝对路径\n' +
      `已尝试的路径：\n  ${attempted.length ? attempted.join('\n  ') : '（无）'}`,
  )
}

/** 仅供测试：清掉进程内缓存。 */
export function resetPythonCache() {
  cached = null
}
