/**
 * 面向模型的工具：yi_liuyao / yi_bazi。
 *
 * 设计取向（与官方 adding-a-tool 指南一致）：
 *  · `output.schema` 是可编程的规范值——把排盘与结论的关键字段**结构化**交出去，
 *    模型据此解读，而不是去正则解析自然语言。
 *  · `output.render` 才是给人看的：把引擎已生成的正文（narrate 段）原样交付。
 *  · 机械运算全部在 Python 引擎里完成；这里只搬运参数、整形结果、拼装正文。
 *    （仓库铁律一：LLM 与 node 层都不许自己算卦。）
 */
import { cast } from './engine.mjs'

/** 把可能很长的正文做有界截断，附原文长度，避免把整篇报告塞进上下文。 */
function bounded(text, max = 6000) {
  if (typeof text !== 'string') return { text: '', truncated: false }
  if (text.length <= max) return { text, truncated: false }
  return { text: text.slice(0, max), truncated: true }
}

/** 六爻：结论 + 关键结构事实。字段名与 analyze JSON 保持同名，便于复核。 */
function liuyaoValue(result) {
  const a = result.analyze
  const chart = result.chart
  const conclusion = a.conclusion ?? {}
  // 只挑「能直接对应卦象」的事实，不搬整套 thinking_chain（那是备查层）
  const lines = (chart.original_hexagram?.yao_lines ?? []).map((l) => ({
    position: l.position,
    name: l.name,
    six_relation: l.six_relation,
    six_spirit: l.six_spirit,
    branch: l.earthly_branch,
    is_moving: l.is_moving,
    is_world: l.is_world,
    is_response: l.is_response,
    is_empty: l.is_empty,
    changed_branch: l.changed_branch ?? null,
  }))
  const s5 = a.thinking_chain?.step5_synthesis ?? {}
  return {
    discipline: 'liuyao',
    question: chart.question ?? '',
    divination_time: chart.divination_time ?? {},
    empty_branches: chart.empty_branches ?? [],
    original_hexagram: {
      name: chart.original_hexagram?.name ?? '',
      palace: chart.original_hexagram?.palace ?? '',
      generation: chart.original_hexagram?.generation ?? '',
      upper_trigram: chart.original_hexagram?.upper_trigram ?? '',
      lower_trigram: chart.original_hexagram?.lower_trigram ?? '',
    },
    changed_hexagram: chart.changed_hexagram?.name ?? null,
    lines,
    use_god: {
      category: a.thinking_chain?.step2_use_god_identification?.use_god_category ?? '',
      basis: a.thinking_chain?.step2_use_god_identification?.use_god_basis ?? '',
      position: a.thinking_chain?.step2_use_god_identification?.selected_use_god?.position ?? null,
      strength: a.thinking_chain?.step3_strength_analysis?.strength_level ?? '',
    },
    conclusion: {
      direction: conclusion.方向 ?? conclusion.verdict ?? '',
      description: conclusion.说明 ?? '',
      signal_strength: conclusion.信号强度 ?? null,
      timing: conclusion.应期 ?? [],
      timing_window: conclusion.应期窗口 ?? null,
    },
    key_factors: (s5.factor_contributions ?? []).slice(0, 8).map((f) => ({
      name: f.name,
      reason: f.reason,
    })),
    narrative: bounded(result.narrative),
  }
}

/** 八字：四柱 + 结论要点。 */
function baziValue(result) {
  const a = result.analyze
  const chart = result.chart
  const c = a.conclusion ?? {}
  const pillars = chart.pillars ?? {}
  const pick = (p) =>
    p
      ? {
          ganzhi: p.ganzhi ?? '',
          stem: p.stem ?? '',
          branch: p.branch ?? '',
          nayin: p.nayin ?? '',
          ten_god: p.ten_god ?? '',
        }
      : null
  return {
    discipline: 'bazi',
    birth: chart.birth ?? {},
    pillars: {
      year: pick(pillars.year),
      month: pick(pillars.month),
      day: pick(pillars.day),
      hour: pick(pillars.hour),
    },
    conclusion: {
      direction: c.方向 ?? '',
      description: c.说明 ?? '',
      strength: c.strength ?? '',
      pattern: c.pattern ?? '',
      useful_gods: c.useful_gods ?? [],
      taboo_gods: c.taboo_gods ?? [],
    },
    narrative: bounded(result.narrative, 8000),
  }
}

/**
 * 构造工具定义。`defineTool` 由宿主注入（插件按 dsh-tools 的导出约定取用），
 * 拿不到就退回「原始 JSON Schema ToolDefinition」——两条路都是官方支持的注册形态。
 */
export function createLiuyaoTool(_defineTool) {
  return {
    name: 'yi_liuyao',
    description:
      '六爻纳甲起卦与断卦。机械排盘（定宫、纳甲、世应、六亲、六神、旬空、旺衰、应期）' +
      '全部由内置 Python 引擎完成，本工具返回结构化结论与已生成的正文。' +
      '用户问起卦、摇卦、占卜、测吉凶、问某事如何时使用。' +
      '同一问题不重复占卜（再三则渎）；换实质角度请问用户是否另起一卦。',
    parameters: {
      question: { type: 'string', required: true, description: '求测问题（原话即可，越具体越好）' },
      mode: {
        type: 'string',
        enum: ['coin', 'time', 'number', 'manual'],
        description: '起卦方式：coin=铜钱摇卦（默认）、time=时间起卦、number=三数起卦、manual=手动爻值',
      },
      datetime: { type: 'string', description: '起卦时刻 "YYYY-MM-DD HH:MM"，缺省用当前时间' },
      numbers: { type: 'string', description: 'mode=number 时必填，格式 "a,b,c"' },
      yao: { type: 'string', description: 'mode=manual 时必填，6 个爻值如 "7,8,9,7,6,8"（6/7/8/9）' },
      seed: { type: 'number', description: '铜钱摇卦的随机种子，用于复现同一卦' },
      gender: { type: 'string', enum: ['男', '女'], description: '求测者性别（占婚恋等用神取法不同时重要）' },
    },
    render: (args, value) => [
      { type: 'text', text: value.narrative.text || '（引擎未产出正文）' },
    ],
  }
}

export function createBaziTool() {
  return {
    name: 'yi_bazi',
    description:
      '八字（四柱）排盘与格局分析。子平四柱、十神、藏干、旺衰、格局、喜用、大运流年、' +
      '调候用神全部由内置 Python 引擎计算，本工具返回结构化结论与已生成的正文。' +
      '用户问八字、排盘、命理、四柱、大运、流年、喜用神时使用。' +
      '需要出生时间；时辰不确定时须先问清，不可臆测。',
    parameters: {
      datetime: {
        type: 'string',
        required: true,
        description: '出生时间 "YYYY-MM-DD HH:MM"（公历；时辰不明请先向用户确认）',
      },
      gender: { type: 'string', required: true, enum: ['男', '女'], description: '性别（大运顺逆依赖于此）' },
      longitude: { type: 'number', description: '出生地东经，用于真太阳时校正（可选）' },
    },
    render: (args, value) => [
      { type: 'text', text: value.narrative.text || '（引擎未产出正文）' },
    ],
  }
}

/** 把模型给的参数翻译成引擎命令行参数。参数校验由宿主先做，这里只做语义组装。 */
export function buildLiuyaoArgs(args) {
  const mode = args.mode ?? 'coin'
  const argv = ['--question', args.question ?? '']
  argv.push('--mode', mode)

  if (args.datetime) argv.push('--datetime', String(args.datetime))
  if (mode === 'number') {
    if (!args.numbers) throw new Error('mode=number 需要提供 numbers（如 "3,5,7"）')
    argv.push('--numbers', String(args.numbers))
  }
  if (mode === 'manual') {
    if (!args.yao) throw new Error('mode=manual 需要提供 yao（6 个爻值，如 "7,8,9,7,6,8"）')
    argv.push('--yao', String(args.yao))
  }
  if (args.seed !== undefined && args.seed !== null) argv.push('--seed', String(args.seed))
  return argv
}

export function buildBaziArgs(args) {
  const argv = ['--datetime', String(args.datetime), '--gender', String(args.gender)]
  if (args.longitude !== undefined && args.longitude !== null) {
    argv.push('--longitude', String(args.longitude))
  }
  return argv
}

/** 供工具 execute 复用的两个薄封装。 */
export async function runLiuyao(args, exec) {
  const argv = buildLiuyaoArgs(args)
  const result = await cast('liuyao', argv, { signal: exec?.signal })
  return liuyaoValue(result)
}

export async function runBazi(args, exec) {
  const argv = buildBaziArgs(args)
  const result = await cast('bazi', argv, { signal: exec?.signal })
  return baziValue(result)
}
