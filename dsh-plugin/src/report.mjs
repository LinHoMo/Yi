/**
 * 插件侧报告排版层（274 批）：把**引擎已产出的结构化字段**排成单文件 HTML。
 *
 * 边界（与 AGENTS.md 对齐）：
 *  · 这里**只做呈现**：所有象数文字（干支/十神/旺衰/事件描述）一律来自工具返回的
 *    结构化字段（引擎产出）；本文件不含任何象数运算或新断语。
 *  · 六爻的 HTML 报告由引擎 render 段（render.py render_html）负责——那是两科
 *    已验证的报告器；本文件只补八字（bazi render 段目前只有 Markdown）。
 *  · 口径页脚照抄本仓铁律三：分数是古籍案例对齐分；象征推演非预言。
 */
import { tmpdir } from 'node:os'
import { mkdir, writeFile } from 'node:fs/promises'
import { join } from 'node:path'

function esc(s) {
  return String(s ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
}

const STYLE = `
:root{--ink:#1f2430;--mut:#6b7280;--line:#e5e7eb;--soft:#f7f7f5;--gold:#8a6d3b;--green:#2e7d32;--red:#b3261e}
*{box-sizing:border-box}
body{font-family:"Source Han Serif SC","Noto Serif SC",Georgia,serif;color:var(--ink);max-width:1080px;margin:24px auto;padding:0 20px;line-height:1.6;background:#fffdf9}
h1{font-size:1.5rem;border-bottom:2px solid var(--gold);padding-bottom:8px;margin-bottom:4px}
h2{font-size:1.05rem;margin:28px 0 10px;color:var(--gold)}
.meta{color:var(--mut);font-size:.85rem;margin-bottom:18px}
.pillars{display:flex;gap:12px;flex-wrap:wrap}
.pillar{flex:1;min-width:150px;background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:14px;text-align:center}
.pillar .pos{font-size:.8rem;color:var(--mut)}
.pillar .gz{font-size:1.7rem;letter-spacing:.35em;margin:6px 0 2px;padding-left:.35em}
.pillar .tg{color:var(--gold);font-size:.9rem}
.pillar .ny{color:var(--mut);font-size:.8rem}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{border:1px solid var(--line);border-radius:999px;padding:3px 12px;font-size:.85rem;background:#fff}
.chip b{font-weight:600}
.chip.good{border-color:#c8e6c9;background:#f1f8f1;color:var(--green)}
.chip.bad{border-color:#f3c1bd;background:#fdf3f2;color:var(--red)}
.dayun{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px}
.yun{min-width:118px;border:1px solid var(--line);border-radius:10px;padding:10px;background:#fff}
.yun.cur{border-color:var(--gold);background:#fbf6ec}
.yun .gz{font-size:1.15rem;letter-spacing:.2em}
.yun .age{color:var(--mut);font-size:.75rem}
.yun ul{margin:6px 0 0;padding-left:1.1em;font-size:.75rem;color:var(--mut)}
.yun li{margin-bottom:3px}
table{width:100%;border-collapse:collapse;font-size:.88rem}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{color:var(--mut);font-weight:500;background:var(--soft)}
.months{display:grid;grid-template-columns:repeat(auto-fill,minmax(84px,1fr));gap:8px}
.mo{border:1px solid var(--line);border-radius:8px;padding:8px;text-align:center;font-size:.85rem;background:#fff}
.mo .gz{letter-spacing:.15em}
.mo .tg{color:var(--gold);font-size:.75rem}
.foot{margin-top:34px;border-top:1px solid var(--line);padding-top:12px;color:var(--mut);font-size:.78rem}
`

/**
 * 八字单文件 HTML。输入是 runBazi 的 value（结构化字段全为引擎产出）。
 * @returns {string} 完整 HTML 文档
 */
export function baziHtml(v) {
  const c = v.conclusion ?? {}
  const pillars = v.pillars ?? {}
  const posName = { year: '年柱', month: '月柱', day: '日柱', hour: '时柱' }
  const b = v.birth ?? {}
  const pillarCards = ['year', 'month', 'day', 'hour']
    .map((k) => {
      const p = pillars[k]
      if (!p) return ''
      return `<div class="pillar"><div class="pos">${posName[k]}</div><div class="gz">${esc(p.ganzhi)}</div><div class="tg">${esc(p.ten_god) || '日主'}</div><div class="ny">${esc(p.nayin)}</div></div>`
    })
    .join('')
  const score = c.strength_score != null ? `（${c.strength_score > 0 ? '+' : ''}${c.strength_score}）` : ''
  const chips = [
    `<span class="chip"><b>旺衰</b> ${esc(c.strength)}${esc(score)}</span>`,
    c.pattern ? `<span class="chip"><b>格局</b> ${esc(c.pattern)}</span>` : '',
    c.pattern_cheng_bai ? `<span class="chip">成败 ${esc(c.pattern_cheng_bai)}</span>` : '',
    c.special_pattern ? `<span class="chip">特格 ${esc(c.special_pattern)}</span>` : '',
    ...(c.useful_gods ?? []).map((g) => `<span class="chip good">喜 ${esc(g)}</span>`),
    ...(c.taboo_gods ?? []).map((g) => `<span class="chip bad">忌 ${esc(g)}</span>`),
    c.tiaohou?.main ? `<span class="chip"><b>调候</b> ${esc(c.tiaohou.main)}${c.tiaohou.assist ? '・' + esc(c.tiaohou.assist) : ''}</span>` : '',
    c.xunkong ? `<span class="chip">空亡 ${esc(c.xunkong)}</span>` : '',
    c.tai_yuan ? `<span class="chip">胎元 ${esc(c.tai_yuan)}</span>` : '',
    c.bing_yao ? `<span class="chip">病 ${esc(c.bing_yao)}</span>` : '',
    c.bing_yao_medicine ? `<span class="chip good">${esc(c.bing_yao_medicine)}</span>` : '',
    ...(c.tong_guan ?? []).map((t) => `<span class="chip">通关 ${esc(t)}</span>`),
    ...(c.tian_ke_di_chong ?? []).map((t) => `<span class="chip bad">天克地冲 ${esc(t)}</span>`),
  ]
    .filter(Boolean)
    .join('')
  const now = new Date().toISOString().slice(0, 16).replace('T', ' ')
  // 大运：标出「当前年龄所在步」仅按 start_age/end_age 区间判断（纯呈现，非推演）
  const yunCards = (v.dayun ?? [])
    .map((d) => {
      const ev = (d.events ?? [])
        .map((e) => `<li title="${esc(e.kind)}${e.rel ? '・' + esc(e.rel) : ''}">${esc(e.text)}</li>`)
        .join('')
      return `<div class="yun"><div class="gz">${esc(d.ganzhi)}</div><div class="age">${d.start_age}–${d.end_age} 岁</div><div class="tg">${esc(d.ten_god)}</div>${ev ? `<ul>${ev}</ul>` : ''}</div>`
    })
    .join('')
  const lnRows = (v.liunian ?? [])
    .map((x) => {
      const ev = (x.events ?? [])
        .map((e) => `${esc(e.text)}`)
        .join('<br>')
      return `<tr><td>${x.year ?? ''}</td><td><b>${esc(x.liunian)}</b></td><td>${esc(x.ten_god)}</td><td>${esc(x.dayun ?? '')}</td><td>${ev || '—'}</td></tr>`
    })
    .join('')
  const months = (v.liuyue ?? [])
    .map((m) => `<div class="mo"><div class="gz">${esc(m.ganzhi)}</div><div class="tg">${esc(m.ten_god)}</div></div>`)
    .join('')
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>八字排盘报告 ${esc(b.datetime ?? '')}</title>
<style>${STYLE}</style>
</head>
<body>
<h1>八字排盘报告</h1>
<div class="meta">出生：${esc(b.datetime ?? '')}　性别：${esc(b.gender ?? '')}　生成：${now}　引擎：Yi 八字（子平四柱，机械排盘）</div>

<h2>四柱</h2>
<div class="pillars">${pillarCards}</div>

<h2>旺衰・格局・喜忌</h2>
<div class="chips">${chips}</div>

<h2>大运</h2>
<div class="dayun">${yunCards}</div>

<h2>流年（明动与岁运结构对照；只记结构，不批吉凶）</h2>
<table><thead><tr><th>年份</th><th>流年</th><th>十神</th><th>所临大运</th><th>结构事件</th></tr></thead><tbody>${lnRows}</tbody></table>

<h2>流月</h2>
<div class="months">${months}</div>

<div class="foot">
口径说明：本报告全部判据文字来自 Yi 引擎的结构化输出；本页面只做排版，不含任何新断语。
库内分数为「古籍案例对齐分」，用于回归审计，不是现实命中率（现实侧样本为零）。
本内容为象征推演与方向参考，不是预言；医疗、法律、投资、重大决策请以专业意见为准。
</div>
</body>
</html>
`
}

/**
 * 把报告文本写成文件。落 os.tmpdir()（引擎纪律：中间产物不进用户目录），
 * 文件名带学科与时间戳，路径随工具返回值交给用户。
 */
export async function writeReportFile(discipline, format, content) {
  const stamp = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19)
  const dir = join(tmpdir(), 'yi-reports')
  await mkdir(dir, { recursive: true })
  const path = join(dir, `yi-${discipline}-${stamp}.${format}`)
  await writeFile(path, content, 'utf8')
  return path
}
