/**
 * Yi 插件（六爻 + 八字）宿主端入口。
 *
 * 三件事，都走官方扩展点（docs/cookbook/extension-cookbook.zh.md 的「功能→机制映射」）：
 *  1. `ctx.tools.register(...)` —— 让模型能**直接调用**起卦/排盘，不必自己敲 python。
 *  2. `ctx.skills.registerProvider(...)` —— 把 SKILL.md 作为技能交给模型按需加载
 *     （官方把 skill 归为「section + 工具注册」；这里注册 provider，宿主负责注入）。
 *  3. `ctx.systemPrompt.section(...)` —— 告诉模型「这套工具何时用、边界在哪」。
 *
 * 设计约束（来自本仓 AGENTS.md，插件不得放宽）：
 *  · 机械运算归代码：node 半不含任何象数算法，全部委托给打包的 Python 引擎。
 *  · 口径诚实：工具描述与技能正文不得出现「预测准确率」一类表述。
 *  · 找不到 Python 时**不装作能用**：插件照常加载，但工具如实报错并给出补救路径。
 */
import { existsSync, readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { basename, dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { selftest } from './engine.mjs'
import { runKb } from './kb.mjs'
import {
  createBaziTool,
  createKbTool,
  createLiuyaoTool,
  createReportTool,
  runBazi,
  runLiuyao,
  runReport,
} from './tools.mjs'

/**
 * 取 `defineTool`：它是 dsh-tools 的具名导出，由宿主提供（插件不打包它）。
 *
 * 用**同步** createRequire 而不是 await import：本函数在 Cordis 的
 * `effect(function*(){...})` 生成器里调用，生成器体内的 await 有语法限制
 * （实测 `Unexpected reserved word`）。取不到就返回 null，退回原始
 * JSON Schema 注册——不会静默变成「没注册」。
 * @returns {Function|null}
 */
function loadDefineTool() {
  try {
    const require = createRequire(import.meta.url)
    const mod = require('@deepseek-ai/dsh-tools')
    return typeof mod?.defineTool === 'function' ? mod.defineTool : null
  } catch {
    return null
  }
}

export const name = 'yi'

/**
 * 依赖注入。
 *
 * ⚠ `systemPrompt` / `skills` 必须写在 `inject` 里：Cordis 的服务属性只有在声明后
 * 才可读，未声明就访问会抛 `cannot get property "X" without inject`——整条插件
 * 会变成「did not activate」，而宿主**只打印一行 warning 就继续启动**。
 * 这是 2026-10-25 装进真实 profile 时才暴露的：本地假 ctx 测试完全看不见它。
 */
export const inject = ['tools', 'systemPrompt']

const SKILL_NAME = 'yi-divination'
const PROVIDER_NAME = 'yi-bundled'

/**
 * 宿主把插件装载后，模型看到的一段说明。
 * 措辞刻意保守：本仓铁律三禁止把对齐分说成预测率，这里连「准」字都不用。
 */
const SECTION_TEXT = `## Yi（六爻 / 八字）

本机装有一套确定性术数引擎与随包判据知识库，通过四个工具调用。**排盘与推演全部由内置
Python 代码完成，你不得自己心算或推算任何卦象、干支、纳甲、旺衰、应期。**

- \`yi_liuyao\`：六爻纳甲。起卦（铜钱/时间/数字/手动）→ 装卦 → 断卦 → 出正文。
- \`yi_bazi\`：八字四柱。排盘 → 十神/藏干/旺衰/格局/喜用/大运流年 → 出正文。
- \`yi_kb\`：判据知识库关键词检索（纳甲/用神/格局/应期等判据表）。返回 文件:行 + 节标题
  + 摘录，先检索定位再按行读具体节段，不要整篇读入。
- \`yi_report\`：完整排盘报告文件（单文件 HTML）。先判读后出报告；把返回的文件路径转告用户。

使用要点：

1. **先把人话变成可算输入**：问的是什么事、求测者性别与身份、起卦时刻。
   占感情时性别会改变用神（男占婚取妻财、女占婚取官鬼），务必问清再起。
2. **一卦一事**：同一问题不重复占卜（再三则渎）。用户换了实质角度（换用神、换层面、
   假设未来、比较两人、测人心）时，提议**另起一卦**，不要在原卦里硬推。
3. **照工具输出讲**：工具返回的 \`narrative\` 是引擎生成的正文，已按本仓规范写好措辞。
   你的价值是把 \`narrative\` 与结构化字段翻译成当事人听得懂的话，而不是重写判据。
4. **边界**：这是象征推演与方向参考，不是预言。凶象用「偏向／有…信号／结构上」，
   不用「注定／一定／绝无可能」。医疗、法律、投资、重大决策一律提示以专业意见为准。
5. **口径**：库内一切分数是「古籍案例对齐分」，不是现实命中率。现实侧样本为零，
   不得声称预测能力。
`

/**
 * 从 <pkg>/skills/yi-divination/SKILL.md 读技能正文；读不到就退回 <pkg>/SKILL.md。
 *
 * 两个位置的关系（刻意如此）：`skills/` 是**官方 skill-filesystem 的发现格式**，
 * 供 `bundledSkillDir` 扫描；插件根的 `SKILL.md` 是打包前的唯一真源，
 * `build-skills.mjs` 从它生成 `skills/`。providers 优先读前者，保证随包技能
 * 与文件系统发现看到的是**同一份内容**。
 */
function resolveSkillPath() {
  const moduleDir = dirname(fileURLToPath(import.meta.url))
  const pkgRoot = basename(moduleDir) === 'src' ? resolve(moduleDir, '..') : resolve(moduleDir, '../..')
  const candidates = [
    join(pkgRoot, 'skills', 'yi-divination', 'SKILL.md'),
    join(pkgRoot, 'SKILL.md'),
  ]
  for (const p of candidates) {
    if (existsSync(p)) return { path: p, pkgRoot }
  }
  throw new Error(`[yi] 找不到 SKILL.md（已找：${candidates.join(' / ')}）`)
}

function bundledSkillProvider() {
  const { path: skillPath, pkgRoot } = resolveSkillPath()
  const raw = readFileSync(skillPath, 'utf8')
  const end = raw.indexOf('\n---\n', 4)
  if (!raw.startsWith('---\n') || end < 0) {
    throw new Error(`[yi] SKILL.md frontmatter 不合法：${skillPath}`)
  }
  const front = raw.slice(4, end)
  const m = /^\s*description\s*:\s*(.+?)\s*$/mu.exec(front)
  if (!m) throw new Error(`[yi] SKILL.md frontmatter 缺少 description：${skillPath}`)
  const rawDesc = m[1]
  // YAML 行内字符串的引号与 >- 折行都天然归一：这里只取「引号内或整行」的最小可信值
  const description = rawDesc.replace(/^['"]|['"]$/gu, '').replace(/^>-?\s*/u, '').trim()
  const body = raw.slice(end + 5)
  // ⚠ `invocation` 必须是**对象**（{modelInvocable, userInvocable}），不是字符串。
  // 2026-10-25 真机实测：写成 `invocation: 'model'` 时，`dsh --profile headless` 直接抛
  //   skill provider "yi-bundled" returned skill "yi-divination" with a non-object invocation policy
  // 且**整轮会话以 error 结束**——不是警告、不是跳过，是模型一个字都答不了。
  // 前三轮"插件能激活"的验证全绿，因为该异常只在**真正组装技能目录**（即跑模型）时才触发。
  // 校验源码见 dsh-skill/lib/index.js 的 validateInvocation。
  const entry = {
    name: SKILL_NAME,
    description,
    invocation: { modelInvocable: true, userInvocable: true },
    source: 'bundled',
    provider: PROVIDER_NAME,
    // `rank` 亦为必填且必须是有穷数字（校验源码同 validateInvocation 附近）：
    // 漏了会抛 `invalid rank`，同样让整轮会话以 error 结束。
    // 取官方的 bundled 档位（skill-filesystem 文档：bundledSkillDir 按 rank 600 扫描），
    // 保持与官方随包技能同档，不抢用户/项目技能的优先级。
    rank: 600,
    path: skillPath,
    resourceBase: { kind: 'directory', path: pkgRoot },
    locator: skillPath,
  }
  return {
    name: PROVIDER_NAME,
    list: () => Promise.resolve([entry]),
    get: () => Promise.resolve({ ...entry, content: body }),
  }
}

/**
 * @param {import('@deepseek-ai/cordis').Context} ctx
 * @param {{ enableBazi?: boolean }} [config]
 */
export function apply(ctx, config) {
  const enableBazi = config?.enableBazi !== false

  // ── 系统提示词 ───────────────────────────────────────────────────────────
  // `order` 必须显式给有限数值：仓库内贡献者走 getSectionOrder() 取官方分配，
  // 而官方文档明载「外部贡献可用任何有限 order」。初版漏了 order，宿主报
  // `order must be a finite number` 并令整条插件不激活（装真机时才暴露）。
  // 取一个靠后的值：让 Yi 的说明排在核心规范之后，不抢占架构性段落。
  ctx.systemPrompt.section({
    name: 'yi:divination',
    order: 900,
    text: SECTION_TEXT,
  })

  // ── 工具 ─────────────────────────────────────────────────────────────────
  ctx.inject(['tools'], (toolsCtx) => {
    toolsCtx.effect(function* () {
      // `defineTool` 是 @deepseek-ai/dsh-tools 的**具名导出**，不是 ctx.tools 的方法
      // （2026-10-25 读 asar 里 dsh-tools/lib/index.js 的 export 列表确认）。
      //
      // ⚠ 实测：插件目录通常**解析不到** `@deepseek-ai/dsh-tools`（它是宿主提供的
      // peer，不在本包的 node_modules 里），所以线上几乎总是走 fallback 分支。
      // 初版 fallback 只交了 {name, description, parameters, execute}——**没有
      // output.render**，于是模型拿不到正文（`verify-in-dsh.mjs` 第 [3] 段抓到的
      // `output.render 未产出文本块`）。fallback 必须与主路径**同等地**带 render。
      const defineTool = loadDefineTool()

      /** 两条注册路径共用的定义构造，保证 render 不会只在其中一条上存在。 */
      const build = (spec, run) => {
        const base = {
          name: spec.name,
          description: spec.description,
          parameters: spec.parameters,
          output: { schema: { type: 'object' }, render: spec.render },
        }
        const impl = { async execute(args, exec) { return run(args, exec) } }
        return defineTool ? defineTool({ ...base, ...impl }) : { ...base, ...impl }
      }

      yield toolsCtx.tools.register(build(createLiuyaoTool(defineTool), runLiuyao))

      if (enableBazi) {
        yield toolsCtx.tools.register(build(createBaziTool(), runBazi))
      }

      // 判据知识库检索：纯 Node、不依赖 Python，与 enableBazi 无关，恒注册。
      yield toolsCtx.tools.register(build(createKbTool(), runKb))

      // 完整报告文件（274 批）：cast → render 段（或八字 html 排版层）→ 临时文件。
      yield toolsCtx.tools.register(build(createReportTool(), runReport))
    }, 'yi: divination tools')
  })

  // ── 技能 ─────────────────────────────────────────────────────────────────
  ctx.inject(['skills'], (skillCtx) => {
    skillCtx.effect(() => skillCtx.skills.registerProvider(() => bundledSkillProvider()), 'yi: bundled skill')
  })

  // ── 启动自检：只打印，不阻断加载 ─────────────────────────────────────────
  // 引擎缺文件时工具会在调用时报错；这里提前把话说清楚，免得用户以为是模型的锅。
  selftest()
    .then((problems) => {
      if (problems.length) {
        console.warn('[yi] 引擎自检发现问题：')
        for (const p of problems) console.warn('  ·', p)
      }
    })
    .catch((err) => console.warn('[yi] 引擎自检异常：', err?.message ?? err))
}
