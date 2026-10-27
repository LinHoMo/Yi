/**
 * 插件侧报告排版层（274 批建成，276 批美学重排）：把**引擎已产出的结构化字段**
 * 排成单文件 HTML。
 *
 * 边界（与 AGENTS.md 对齐）：
 *  · 这里**只做呈现**：所有象数文字（干支/十神/旺衰/事件描述）一律来自工具返回的
 *    结构化字段（引擎产出）；本文件不含任何象数运算或新断语。装饰性版式元素
 *    （印章字「易」、段落标题、性别→乾造/坤造的称谓映射）不是断语。
 *  · 「行运中」高亮只按 start_age/end_age 区间与出生年份粗算年龄（纯呈现，
 *    与引擎 approximate 口径一致，不参与判读）。
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
:root{
  --paper:#efe7d5;--sheet:#faf6ec;--card:#fdfaf2;
  --ink:#332e26;--mut:#8c8271;--line:#d9cfb8;--hair:#e6ddc8;
  --cinnabar:#a8402f;--indigo:#41586a;--gold:#96783a;
  --jade:#3f7252;--jade-bg:#eef3ea;--jade-line:#c9d8c5;
  --red:#a8402f;--red-bg:#f7ebe6;--red-line:#e0c4b8;
}
*{box-sizing:border-box}
html{background:var(--paper)}
body{
  font-family:"Noto Serif SC","Source Han Serif SC","Songti SC","SimSun",Georgia,serif;
  color:var(--ink);max-width:980px;margin:0 auto;padding:28px 20px 40px;line-height:1.7;
}
.sheet{
  background:
    linear-gradient(180deg,rgba(255,255,255,.55),rgba(255,255,255,0) 120px),
    var(--sheet);
  border:1px solid var(--line);border-radius:4px;
  box-shadow:0 1px 2px rgba(80,64,40,.12),0 12px 32px rgba(80,64,40,.10);
  padding:44px 52px 40px;
}
/* ── 卷首 ─────────────────────────────────────────────── */
.head{text-align:center;margin-bottom:10px}
.seal{
  width:44px;height:44px;margin:0 auto 14px;display:flex;align-items:center;justify-content:center;
  background:var(--cinnabar);color:#f9f2e4;font-size:1.5rem;font-weight:700;border-radius:7px;
  box-shadow:inset 0 0 0 2px rgba(249,242,228,.35),0 2px 6px rgba(120,40,25,.28);
  letter-spacing:0;
}
h1{font-size:1.9rem;font-weight:700;letter-spacing:.42em;margin:0 0 10px;padding-left:.42em}
.sub{color:var(--mut);font-size:.85rem;letter-spacing:.06em}
.sub b{color:var(--ink);font-weight:600}
.rule{margin:22px auto 0;width:100%;border-top:3px solid var(--ink);position:relative}
.rule::after{content:'';position:absolute;left:0;right:0;top:6px;border-top:1px solid var(--ink)}
/* ── 段题 ─────────────────────────────────────────────── */
h2{
  display:flex;align-items:center;gap:10px;
  font-size:1.02rem;font-weight:700;letter-spacing:.3em;margin:34px 0 14px;color:var(--ink);
}
h2::before{content:'';width:8px;height:8px;background:var(--cinnabar);transform:rotate(45deg);flex:none}
h2::after{content:'';flex:1;border-top:1px solid var(--hair)}
h2 .hint{font-size:.72rem;color:var(--mut);letter-spacing:.05em;font-weight:400}
/* ── 四柱 ─────────────────────────────────────────────── */
.pillars{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.pillar{
  background:var(--card);border:1px solid var(--line);border-top:3px solid var(--indigo);
  border-radius:4px;padding:16px 12px 14px;text-align:center;position:relative;
  box-shadow:0 1px 3px rgba(80,64,40,.08);
}
.pillar.day{border-top-color:var(--cinnabar)}
.pillar .pos{font-size:.78rem;color:var(--mut);letter-spacing:.5em;padding-left:.5em}
.pillar .gz{
  writing-mode:vertical-rl;margin:10px auto 8px;height:5.4rem;
  font-size:2.05rem;font-weight:700;letter-spacing:.28em;line-height:1;
  display:flex;align-items:center;
}
.pillar.day .gz{color:var(--cinnabar)}
.pillar .badge{
  position:absolute;top:8px;right:8px;font-size:.62rem;color:#f9f2e4;background:var(--cinnabar);
  padding:1px 6px;border-radius:3px;letter-spacing:.2em;padding-left:calc(6px + .2em);
}
.pillar .tg{color:var(--gold);font-size:.9rem;letter-spacing:.2em;padding-left:.2em}
.pillar .ny{color:var(--mut);font-size:.76rem;margin-top:2px;letter-spacing:.1em}
/* ── 结论带 ───────────────────────────────────────────── */
.verdict{
  display:grid;grid-template-columns:auto auto 1fr;gap:0 36px;align-items:stretch;
  background:var(--card);border:1px solid var(--line);border-radius:4px;padding:18px 24px;
  box-shadow:0 1px 3px rgba(80,64,40,.08);
}
.v-item{padding-right:36px;border-right:1px solid var(--hair)}
.v-k{font-size:.72rem;color:var(--mut);letter-spacing:.4em;margin-bottom:4px}
.v-v{font-size:1.35rem;font-weight:700;letter-spacing:.1em}
.v-v .score{font-size:.85rem;color:var(--mut);font-weight:400;font-variant-numeric:tabular-nums}
.v-item .gods{font-size:1.15rem;font-weight:700;letter-spacing:.3em;margin-top:6px}
.v-item .gods.good{color:var(--jade)}
.v-item .gods.bad{color:var(--red)}
.v-cols{display:flex;gap:28px;align-items:flex-start;flex-wrap:wrap}
.v-cols .v-item{border-right:1px solid var(--hair);padding-right:28px;margin-right:0}
.v-cols .v-item:last-child{border-right:none;padding-right:0}
.v-more{grid-column:1/-1;border-top:1px dashed var(--hair);margin-top:16px;padding-top:12px;
  display:flex;flex-wrap:wrap;gap:6px 0;font-size:.82rem;color:var(--ink)}
.v-more .kv{margin-right:22px}
.v-more .kv i{font-style:normal;color:var(--mut);margin-right:6px}
/* ── 徽章（冗余小项） ─────────────────────────────────── */
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{
  border:1px solid var(--line);border-radius:3px;padding:2px 10px;font-size:.8rem;background:var(--card);
  color:var(--ink);letter-spacing:.05em;
}
.chip b{font-weight:600;color:var(--mut);margin-right:4px}
.chip.good{border-color:var(--jade-line);background:var(--jade-bg);color:var(--jade)}
.chip.bad{border-color:var(--red-line);background:var(--red-bg);color:var(--red)}
/* ── 大运 ─────────────────────────────────────────────── */
.dayun{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(104px,1fr);gap:10px;position:relative;padding-top:6px}
.yun{
  background:var(--card);border:1px solid var(--line);border-top:3px solid var(--indigo);
  border-radius:4px;padding:10px 9px 12px;text-align:center;position:relative;
  box-shadow:0 1px 3px rgba(80,64,40,.08);
}
.yun.cur{border-top-color:var(--cinnabar);background:#fbf3e9}
.yun .gz{font-size:1.2rem;font-weight:700;letter-spacing:.22em;padding-left:.22em}
.yun.cur .gz{color:var(--cinnabar)}
.yun .age{color:var(--mut);font-size:.72rem;font-variant-numeric:tabular-nums;margin-top:2px}
.yun .tg{color:var(--gold);font-size:.78rem;letter-spacing:.15em;margin-top:1px}
.yun .live{
  position:absolute;top:-14px;left:50%;transform:translateX(-50%);
  font-size:.62rem;color:#f9f2e4;background:var(--cinnabar);padding:0 6px;border-radius:3px;
  letter-spacing:.2em;white-space:nowrap;
}
.yun ul{margin:8px 0 0;padding:0;list-style:none;font-size:.72rem;color:var(--mut);text-align:left;line-height:1.55}
.yun li{margin-top:4px;padding-left:9px;position:relative}
.yun li::before{content:'';position:absolute;left:0;top:.55em;width:3px;height:3px;background:var(--gold);border-radius:50%}
/* ── 流年 ─────────────────────────────────────────────── */
table{width:100%;border-collapse:collapse;font-size:.86rem}
th,td{border-bottom:1px solid var(--hair);padding:8px 10px;text-align:left;vertical-align:top}
thead th{
  color:var(--mut);font-weight:600;font-size:.78rem;letter-spacing:.2em;
  background:var(--card);border-bottom:2px solid var(--line);white-space:nowrap;
}
tbody tr:nth-child(even){background:rgba(217,207,184,.14)}
td.yr{color:var(--mut);font-variant-numeric:tabular-nums;white-space:nowrap}
td.gz{font-weight:700;letter-spacing:.15em;white-space:nowrap}
.tag{
  display:inline-block;border:1px solid var(--line);border-radius:3px;background:var(--card);
  padding:0 7px;font-size:.76rem;color:var(--ink);white-space:nowrap;
}
.tag.gold{color:var(--gold);border-color:#e2d3ac}
.ev{position:relative;padding-left:12px;margin-top:1px}
.ev::before{content:'';position:absolute;left:1px;top:.72em;width:4px;height:1px;background:var(--gold)}
/* ── 流月 ─────────────────────────────────────────────── */
.months{display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:10px}
.mo{
  background:var(--card);border:1px solid var(--line);border-radius:4px;padding:10px 6px 9px;
  text-align:center;box-shadow:0 1px 2px rgba(80,64,40,.06);
}
.mo .gz{font-size:1.05rem;font-weight:700;letter-spacing:.18em;padding-left:.18em}
.mo .tg{color:var(--gold);font-size:.72rem;margin-top:2px;letter-spacing:.1em}
/* ── 卷尾 ─────────────────────────────────────────────── */
.foot{margin-top:40px;text-align:center;color:var(--mut);font-size:.76rem;line-height:1.9}
.foot .frule{width:180px;margin:0 auto 12px;border-top:3px solid var(--ink);position:relative}
.foot .frule::after{content:'';position:absolute;left:0;right:0;top:2px;border-top:1px solid var(--ink)}
/* ── 打印 ─────────────────────────────────────────────── */
@media print{
  html,body{background:#fff}
  .sheet{box-shadow:none;border:none;padding:10mm 6mm}
  .pillar,.yun,.verdict,.mo,.chip{box-shadow:none}
  h2{break-after:avoid}
  tr{break-inside:avoid}
}
@media (max-width:760px){
  .sheet{padding:26px 18px 30px}
  .pillars{grid-template-columns:repeat(2,1fr)}
  .verdict{grid-template-columns:1fr}
  .v-item{border-right:none;border-bottom:1px solid var(--hair);padding:0 0 12px;margin-bottom:12px}
  .dayun{grid-auto-flow:row;grid-template-columns:repeat(2,1fr)}
  .yun .live{top:8px;left:auto;right:8px;transform:none}
}
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
      const badge = k === 'day' ? '<div class="badge">日主</div>' : ''
      return `<div class="pillar${k === 'day' ? ' day' : ''}">${badge}<div class="pos">${posName[k]}</div><div class="gz">${esc(p.ganzhi)}</div><div class="tg">${esc(p.ten_god) || '日主'}</div><div class="ny">${esc(p.nayin)}</div></div>`
    })
    .join('')

  const score = c.strength_score != null ? ` <span class="score">${c.strength_score > 0 ? '+' : ''}${c.strength_score}</span>` : ''
  const pattern = c.pattern ? esc(c.pattern) + (c.pattern_cheng_bai ? '・' + esc(c.pattern_cheng_bai) : '') : '—'
  // 呈现层称谓映射：性别字段 → 乾造/坤造（非断语）
  const genderName = b.gender === '男' ? '乾造' : b.gender === '女' ? '坤造' : esc(b.gender ?? '')
  const kv = (k, val) => {
    if (!val) return ''
    // 展示层去重：引擎字段常自带与标签同文的前缀（空亡/得药/天克地冲…），避免「空亡 空亡 …」
    const text = String(val).startsWith(k) ? String(val).slice(k.length).replace(/^[：:\s]+/, '') : val
    return `<span class="kv"><i>${k}</i>${esc(text)}</span>`
  }
  const more = [
    kv('特格', c.special_pattern),
    kv('调候', c.tiaohou?.main ? c.tiaohou.main + (c.tiaohou.assist ? '・' + c.tiaohou.assist : '') : ''),
    kv('空亡', c.xunkong),
    kv('胎元', c.tai_yuan),
    kv('病', c.bing_yao),
    kv('得药', c.bing_yao_medicine),
    ...(c.tong_guan ?? []).map((t) => kv('通关', t)),
    ...(c.tian_ke_di_chong ?? []).map((t) => kv('天克地冲', t)),
  ]
    .filter(Boolean)
    .join('')

  // 「行运中」高亮：按出生年份粗算年龄落在哪步大运区间（纯呈现，与引擎 approximate 同口径）
  const birthYear = parseInt(String(b.datetime ?? ''), 10)
  const nowYear = new Date().getFullYear()
  const age = Number.isFinite(birthYear) ? nowYear - birthYear : NaN
  const yunCards = (v.dayun ?? [])
    .map((d) => {
      const ev = (d.events ?? [])
        .map((e) => `<li title="${esc(e.kind)}${e.rel ? '・' + esc(e.rel) : ''}">${esc(e.text)}</li>`)
        .join('')
      const isCur = Number.isFinite(age) && age >= d.start_age && age <= d.end_age
      const live = isCur ? '<div class="live">行运中</div>' : ''
      return `<div class="yun${isCur ? ' cur' : ''}">${live}<div class="gz">${esc(d.ganzhi)}</div><div class="age">${d.start_age}–${d.end_age} 岁</div><div class="tg">${esc(d.ten_god)}</div>${ev ? `<ul>${ev}</ul>` : ''}</div>`
    })
    .join('')
  const lnRows = (v.liunian ?? [])
    .map((x) => {
      const ev = (x.events ?? []).map((e) => `<div class="ev">${esc(e.text)}</div>`).join('')
      return `<tr><td class="yr">${x.year ?? ''}</td><td class="gz">${esc(x.liunian)}</td><td><span class="tag gold">${esc(x.ten_god)}</span></td><td><span class="tag">${esc(x.dayun ?? '')}</span></td><td>${ev || '—'}</td></tr>`
    })
    .join('')
  const months = (v.liuyue ?? [])
    .map((m) => `<div class="mo"><div class="gz">${esc(m.ganzhi)}</div><div class="tg">${esc(m.ten_god)}</div></div>`)
    .join('')
  const now = new Date().toISOString().slice(0, 16).replace('T', ' ')
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>八字排盘报告 ${esc(b.datetime ?? '')}</title>
<style>${STYLE}</style>
</head>
<body>
<div class="sheet">
<header class="head">
  <div class="seal">易</div>
  <h1>八字排盘</h1>
  <div class="sub">出生 <b>${esc(b.datetime ?? '')}</b>　・　${genderName}　・　生成 ${now}　・　Yi 引擎（子平四柱，机械排盘）</div>
  <div class="rule"></div>
</header>

<h2>四柱</h2>
<div class="pillars">${pillarCards}</div>

<h2>旺衰・格局・喜忌</h2>
<div class="verdict">
  <div class="v-item"><div class="v-k">旺衰</div><div class="v-v">${esc(c.strength ?? '—')}${score}</div></div>
  <div class="v-item"><div class="v-k">格局</div><div class="v-v">${pattern}</div></div>
  <div class="v-cols">
    <div class="v-item"><div class="v-k">喜用</div><div class="gods good">${esc((c.useful_gods ?? []).join('　')) || '—'}</div></div>
    <div class="v-item"><div class="v-k">忌神</div><div class="gods bad">${esc((c.taboo_gods ?? []).join('　')) || '—'}</div></div>
  </div>
  <div class="v-more">${more}</div>
</div>

<h2>大运</h2>
<div class="dayun">${yunCards}</div>

<h2>流年<span class="hint">明动与岁运结构对照；只记结构，不批吉凶</span></h2>
<table><thead><tr><th>年份</th><th>流年</th><th>十神</th><th>所临大运</th><th>结构事件</th></tr></thead><tbody>${lnRows}</tbody></table>

<h2>流月</h2>
<div class="months">${months}</div>

<div class="foot">
  <div class="frule"></div>
  口径说明：本报告全部判据文字来自 Yi 引擎的结构化输出；本页面只做排版，不含任何新断语。<br>
  库内分数为「古籍案例对齐分」，用于回归审计，不是现实命中率（现实侧样本为零）。<br>
  本内容为象征推演与方向参考，不是预言；医疗、法律、投资、重大决策请以专业意见为准。
</div>
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
