/**
 * 面向模型的工具：yi_liuyao / yi_bazi / yi_kb。
 *
 * 设计取向（与官方 adding-a-tool 指南一致）：
 *  · `output.schema` 是可编程的规范值——把排盘与结论的关键字段**结构化**交出去，
 *    模型据此解读，而不是去正则解析自然语言。
 *  · `output.render` 才是给人看的：把引擎已生成的正文（narrate 段）原样交付。
 *  · 机械运算全部在 Python 引擎里完成；这里只搬运参数、整形结果、拼装正文。
 *    （仓库铁律一：LLM 与 node 层都不许自己算卦。）
 */
import { cast, report } from './engine.mjs'
import { baziHtml, writeReportFile } from './report.mjs'

/** 把可能很长的正文做有界截断，附原文长度，避免把整篇报告塞进上下文。 */
function bounded(text, max = 6000) {
  if (typeof text !== 'string') return { text: '', truncated: false }
  if (text.length <= max) return { text, truncated: false }
  return { text: text.slice(0, max), truncated: true }
}

/** 有界纯文本（结构化字段用；区别于 bounded() 的 {text,truncated} 形态）。 */
function clip(text, max = 140) {
  if (typeof text !== 'string') return ''
  return text.length <= max ? text : text.slice(0, max)
}

/**
 * 岁运「明动」relation → 紧凑事件。丢 `basis` 长引文——那是对账层
 * （逐字书证在 analyze JSON 里全量保留，随包 SKILL 的口径也只要求结论可复核），
 * `text` 已是引擎写好的一句话结论，clip 后进结构化字段。
 */
function yunEvents(relations) {
  return (relations ?? []).map((r) => ({
    kind: r.kind ?? '',
    value: r.value ?? '',
    rel: r.shishen_rel ?? '',
    text: clip(r.text, 140),
  }))
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

/** 八字：四柱 + 旺衰格局 + 大运/流年/流月结构化字段（全部引擎产出，这里只整形搬运）。 */
function baziValue(result) {
  const a = result.analyze
  const chart = result.chart
  const c = a.conclusion ?? {}
  const s = a.strength ?? {}
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
  // conclusion 顶层就有 strength/pattern/useful_gods/taboo_gods 等直读键；
  // verdicts 另有 {code,label,basis} 判词表，平铺成 code→label 供速览（空亡/病药只在这里有）。
  const verdict = {}
  for (const v of c.verdicts ?? []) if (v?.code) verdict[v.code] = v.label ?? ''
  // 大运 8 步基础表；把大运「明动」按 dayun_index 并回对应步（有事件才带 events 键）。
  const yindongByIndex = new Map(
    (a.dayun_ming_yindong ?? []).map((x) => [x.dayun_index, yunEvents(x.relations)]),
  )
  const dayun = (c.dayun ?? a.dayun ?? []).map((d) => {
    const events = yindongByIndex.get(d.index)
    return {
      ganzhi: d.ganzhi ?? '',
      start_age: d.start_age ?? null,
      end_age: d.end_age ?? null,
      ten_god: d.ten_god ?? '',
      ...(events && events.length ? { events } : {}),
    }
  })
  // 流年逐年行：conclusion.liunian（干支+十神）为主干，并入两类事件——
  // 明动（流年×命局，liunian_ming_yindong）与岁运交叉（流年×所临大运，dayun_liunian）。
  const mingByYear = new Map((a.liunian_ming_yindong ?? []).map((x) => [x.year, x]))
  const crossByYear = new Map((c.dayun_liunian ?? []).map((x) => [x.year, x]))
  const liunian = (c.liunian ?? []).map((x) => {
    const cross = crossByYear.get(x.year)
    const events = [
      ...yunEvents(mingByYear.get(x.year)?.relations),
      ...(cross?.relations ?? []).map((r) => ({
        kind: r.kind ?? '',
        value: r.value ?? '',
        rel: '',
        text: clip(r.text, 80),
      })),
    ]
    return {
      year: x.year ?? null,
      liunian: x.ganzhi ?? '',
      age: x.age ?? null,
      ten_god: x.ten_god ?? '',
      ...(cross?.dayun ? { dayun: cross.dayun } : {}),
      ...(events.length ? { events } : {}),
    }
  })
  const liuyue = (a.liu_yue ?? []).map((m) => ({
    ganzhi: m.ganzhi ?? '',
    branch: m.branch ?? '',
    ten_god: m.ten_god ?? '',
  }))
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
      strength: c.strength ?? s.strength ?? '',
      strength_score: c.strength_score ?? s.strength_score ?? null,
      pattern: c.pattern ?? s.pattern ?? '',
      pattern_cheng_bai: c.pattern_cheng_bai ?? '',
      special_pattern: s.tentative_special ?? '',
      tiaohou: { main: s.tiaohou?.main ?? '', assist: s.tiaohou?.assist ?? '' },
      useful_gods: c.useful_gods ?? s.useful_gods ?? [],
      taboo_gods: c.taboo_gods ?? s.taboo_gods ?? [],
      xunkong: verdict.xunkong ?? '',
      tai_yuan: c.tai_yuan ?? verdict.tai_yuan ?? '',
      tong_guan: (c.tong_guan ?? []).map((t) => clip(t, 100)),
      tian_ke_di_chong: (c.tian_ke_di_chong ?? []).map((t) => clip(t, 100)),
      bing_yao: c.bing_yao ?? '',
      bing_yao_medicine: verdict.bing_yao_medicine ?? '',
    },
    dayun,
    liunian,
    liuyue,
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
      '调候用神全部由内置 Python 引擎计算，本工具返回结构化结论与已生成的正文：' +
      '含旺衰/格局/喜忌/空亡，以及大运 8 步（含明动事件）、流年明动逐年、流月干支结构化字段。' +
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

/**
 * 报告工具（274 批）：跑完整 cast 后渲染报告文件。
 * 六爻 html/md 与八字 md 走**引擎 render 段**（两科已验证的报告器）；
 * 八字 html 走插件排版层（src/report.mjs，文字全部来自引擎结构化字段，零新断语）。
 */
export async function runReport(args, exec) {
  const discipline = args.discipline
  if (discipline !== 'liuyao' && discipline !== 'bazi') {
    throw new Error(`discipline 必须是 liuyao 或 bazi（收到：${discipline}）`)
  }
  const fmt = args.format === 'md' ? 'md' : 'html'
  const argv = discipline === 'liuyao' ? buildLiuyaoArgs(args) : buildBaziArgs(args)
  const result = await cast(discipline, argv, { signal: exec?.signal })
  let content
  let generator
  if (discipline === 'liuyao') {
    content = await report('liuyao', result.analyze, { fmt, signal: exec?.signal })
    generator = `引擎 render 段（${fmt}）`
  } else if (fmt === 'md') {
    content = await report('bazi', result.analyze, { fmt: 'md', signal: exec?.signal })
    generator = '引擎 render 段（md）'
  } else {
    content = baziHtml(baziValue(result))
    generator = '插件排版层（数据全部来自引擎结构化字段）'
  }
  const path = await writeReportFile(discipline, fmt, content)
  const preview = clip(content.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim(), 200)
  return {
    discipline,
    format: fmt,
    path,
    bytes: Buffer.byteLength(content, 'utf8'),
    generator,
    preview,
  }
}

/**
 * yi_report：完整报告文件（274 批）。判据与正文仍是引擎产出；这里只编排
 * cast → render 段（或八字 html 排版层）→ 落临时文件，返回路径交用户打开。
 */
export function createReportTool() {
  return {
    name: 'yi_report',
    description:
      '生成完整排盘报告文件（单文件，浏览器可开）。六爻报告由引擎 render 段产出' +
      '（含装卦全表、旺衰、应期与断卦正文，html/md）；八字 html 含四柱卡、旺衰格局喜忌、' +
      '大运时间条、流年结构事件表、流月格（插件排版层，文字全部来自引擎字段）。' +
      '先完成 yi_liuyao / yi_bazi 的判读；用户要「出报告/可视化/存档」时调用，' +
      '把返回的文件路径转告用户。机械运算仍全部由 Python 引擎完成。',
    parameters: {
      discipline: { type: 'string', enum: ['liuyao', 'bazi'], required: true, description: '报告学科' },
      format: { type: 'string', enum: ['html', 'md'], description: '输出格式，默认 html' },
      question: { type: 'string', description: 'discipline=liuyao 时必填：求测问题（与 yi_liuyao 相同）' },
      mode: { type: 'string', enum: ['coin', 'time', 'number', 'manual'], description: 'liuyao 起卦方式（默认 coin）' },
      datetime: { type: 'string', description: 'liuyao=起卦时刻；bazi=出生时间 "YYYY-MM-DD HH:MM"（bazi 必填）' },
      numbers: { type: 'string', description: 'mode=number 时必填，格式 "a,b,c"' },
      yao: { type: 'string', description: 'mode=manual 时必填，6 个爻值如 "7,8,9,7,6,8"' },
      seed: { type: 'number', description: '铜钱摇卦的随机种子，用于复现同一卦' },
      gender: { type: 'string', enum: ['男', '女'], description: '性别（bazi 必填；liuyao 占婚恋时重要）' },
      longitude: { type: 'number', description: 'bazi 出生地东经，用于真太阳时校正（可选）' },
    },
    render: (_args, value) => [
      {
        type: 'text',
        text:
          `报告已生成：${value?.path ?? '（失败）'}\n` +
          `格式 ${value?.format} / ${Math.round((value?.bytes ?? 0) / 1024)} KB / ${value?.generator ?? ''}\n` +
          `预览：${value?.preview ?? ''}`,
      },
    ],
  }
}

/**
 * yi_kb：随包判据知识库检索（实现在 ./kb.mjs，纯 Node、确定性、零 LLM）。
 * 这里只放工具定义：schema、说明与 render。案例库在扫描层硬排除（铁律二）。
 */
export function createKbTool() {
  return {
    name: 'yi_kb',
    description:
      '检索随包判据知识库（纳甲规则、断卦指南、格局速查、四经典综合、书源台账、' +
      '十神/纳音术语、月支格局、接口速查）。返回 文件:行 + 节标题 + 摘录；' +
      '支持同义词自动展开（用爻↔用神、世应↔世爻/应爻、六神↔六兽）与中文 2-gram 兜底' +
      '（无空格长词如「世应怎么安」也能召回）。' +
      '先检索定位，再用 read 按 file:line 读具体节段，避免整篇读入占满上下文。' +
      '古籍案例库按铁律二不在检索范围（永不返回）。核对判据、确认术语、查格局依据时使用。',
    parameters: {
      query: { type: 'string', required: true, description: '关键词，可多个，空格分隔（如 "用神 取法"）；无空格的中文长词自动 2-gram 兜底' },
      discipline: { type: 'string', enum: ['liuyao', 'bazi'], description: '限定学科（缺省两科都搜）' },
      limit: { type: 'number', description: '最多返回几条（默认 5，上限 10）' },
    },
    render: (_args, value) => {
      const ms = value?.matches ?? []
      if (!ms.length) {
        return [
          {
            type: 'text',
            text: `知识库无匹配（query="${value?.query ?? ''}"）。可换关键词重试，或读 references/INDEX.md 按篇路由。`,
          },
        ]
      }
      const text = ms.map((m) => `${m.file}:${m.line}  §${m.title}\n  ${m.snippet}`).join('\n---\n')
      return [{ type: 'text', text }]
    },
  }
}
