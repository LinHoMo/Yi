/* 易 · Yi 纯前端推演台
 *
 * 设计要点
 *   1. 页面与仓库源码是**同源**的：站点把仓库镜像到 ./engine/...，Pyodide 里按
 *      仓库原有相对布局落盘，于是学科脚本里的 Path(__file__).parents[3] / "core"
 *      一类路径原样成立。
 *   2. 请求 → 命令行参数的映射不在 JS 里，在内核 yishu_core.report；
 *      JS 只负责"取文件、落盘、调用、呈现"。
 *   3. 首次推演才下载 Python 运行时（约 10 MB），之后同一浏览器走缓存。
 *      页面本身不依赖运行时即可显示（表单、深链都能用）。
 *
 * 本轮只做"看得见的部分"：入场动效、页签键盘可达性、科目元信息、轻提示、
 * 时间快捷填入、主题切换过渡。**协议与引擎调用未改**——深链键、manifest 取用、
 * engine_runtime 调用、_isolate 隔离全在各自原位。
 */
'use strict';

const CDN = {
  // 可换镜像：只需提供 pyodide.mjs 与 pyodide-lock.json 的同一版本目录
  base: 'https://cdn.jsdelivr.net/pyodide/v0.28.3/full/',
};

const $ = (id) => document.getElementById(id);
const state = {
  manifest: null,
  pyodide: null,
  booting: null,
  disc: null,
  result: null,
  written: new Set(),
  ready: false,
};

const REDUCED = !!(window.matchMedia
  && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

/* ── 小工具 ───────────────────────────────────────────── */

function log(msg) {
  const el = $('log');
  const t = new Date().toLocaleTimeString('zh-CN', { hour12: false });
  el.textContent += `[${t}] ${msg}\n`;
  el.scrollTop = el.scrollHeight;
}

function setStatus(text, kind) {
  $('status-text').textContent = text;
  const box = $('status');
  box.className = 'status' + (kind ? ' ' + kind : '');
}

function setBadge(text, kind) {
  const b = $('engine-badge');
  b.textContent = '引擎 ' + text;
  b.className = 'badge' + (kind ? ' ' + kind : '');
}

function setProgress(ratio) {
  $('progress-wrap').hidden = ratio == null;
  if (ratio != null) $('progress').style.width = Math.round(ratio * 100) + '%';
}

function showError(msg) {
  const el = $('form-error');
  el.hidden = false;
  el.textContent = msg;
}

function clearError() {
  $('form-error').hidden = true;
}

/* 轻提示：替代原先"借用报告状态行"的复制反馈 */
let toastTimer = null;
function toast(msg, kind) {
  const el = $('toast');
  if (!el) return;
  el.textContent = msg;
  el.className = 'toast' + (kind ? ' ' + kind : '');
  el.hidden = false;
  requestAnimationFrame(() => el.classList.add('in'));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.classList.remove('in');
    setTimeout(() => { el.hidden = true; }, REDUCED ? 0 : 320);
  }, 2200);
}

function download(name, text, mime) {
  const blob = new Blob([text], { type: (mime || 'text/plain') + ';charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

async function copyText(text, label) {
  try {
    await navigator.clipboard.writeText(text);
    toast((label || '已复制') + '到剪贴板');
  } catch (e) {
    toast('复制失败，请手动选中复制', 'err');
  }
}

/* ── 深链：给网页端 AI 用的协议 ─────────────────────────
 *   ?d=<学科>&q=<所问>&dt=<时间>&g=<性别>&mode=<六爻方式>&way=<梅花/小六壬方式>
 *   &num=<数字>&date=<择吉日期>&activity=<事类>&yb=<时支>&auto=1
 * auto=1 表示"打开即推演"，网页端 AI 可以让用户点一条链接直接拿报告。
 */
const DEEPLINK_KEYS = {
  q: 'question', dt: 'datetime', g: 'gender', mode: 'mode', way: 'way',
  num: 'numbers', yao: 'yao', date: 'date', activity: 'activity',
  yb: 'hour_branch', dir: 'direction', seed: 'seed',
  // 灵棋经三部掷面数：短名与请求字段同名，省一层心智映射（0–4 整数）
  up: 'up', mid: 'mid', down: 'down',
};

function readDeepLink() {
  const p = new URLSearchParams(location.search);
  const disc = p.get('d') || p.get('discipline') || '';
  const values = {};
  for (const [short, key] of Object.entries(DEEPLINK_KEYS)) {
    const v = p.get(short);
    if (v) values[key] = v;
  }
  return { disc, values, auto: p.get('auto') === '1' };
}

function buildDeepLink() {
  const p = new URLSearchParams();
  if (state.disc) p.set('d', state.disc);
  const inv = {};
  for (const [short, key] of Object.entries(DEEPLINK_KEYS)) inv[key] = short;
  for (const [k, v] of Object.entries(collectForm())) {
    if (v === '' || v == null) continue;
    p.set(inv[k] || k, v);
  }
  const base = location.origin + location.pathname;
  return base + '?' + p.toString();
}

function refreshDeepLink() {
  $('deeplink').value = buildDeepLink();
}

/* ── 表单 ─────────────────────────────────────────────── */

function currentDiscipline() {
  return (state.manifest.disciplines || []).find((d) => d.id === state.disc);
}

function pad2(n) { return String(n).padStart(2, '0'); }

function nowValue(withTime) {
  const d = new Date();
  const day = `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
  return withTime ? `${day} ${pad2(d.getHours())}:${pad2(d.getMinutes())}` : day;
}

function renderTabs() {
  const box = $('tabs');
  box.innerHTML = '';
  const list = state.manifest.disciplines;
  list.forEach((d, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'tab';
    b.id = 'tab-' + d.id;
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-selected', String(d.id === state.disc));
    b.setAttribute('aria-controls', 'fields');
    b.tabIndex = d.id === state.disc ? 0 : -1;
    b.innerHTML = `${d.name}<span class="kind">${d.kind}</span>`;
    b.onclick = () => selectDiscipline(d.id, { keepValues: true });
    b.addEventListener('keydown', (ev) => onTabKey(ev, i));
    box.appendChild(b);
  });
}

/* 页签键盘可达：左右/上下切换，Home/End 到首尾 */
function onTabKey(ev, i) {
  const list = state.manifest.disciplines;
  let j = null;
  if (ev.key === 'ArrowRight' || ev.key === 'ArrowDown') j = (i + 1) % list.length;
  else if (ev.key === 'ArrowLeft' || ev.key === 'ArrowUp') j = (i - 1 + list.length) % list.length;
  else if (ev.key === 'Home') j = 0;
  else if (ev.key === 'End') j = list.length - 1;
  if (j == null) return;
  ev.preventDefault();
  const target = list[j].id;
  selectDiscipline(target, { keepValues: true });
  const el = $('tab-' + target);
  if (el) el.focus();
}

function renderFields(values) {
  const d = currentDiscipline();
  $('disc-summary').textContent = d ? d.summary : '';
  renderCaveat(d);
  $('disc-meta').textContent = d ? disciplineMeta(d) : '';
  const box = $('fields');
  box.innerHTML = '';
  for (const f of d.fields) {
    const wrap = document.createElement('div');
    wrap.className = 'field';
    const id = 'f-' + f.key;
    const label = document.createElement('label');
    label.htmlFor = id;
    label.innerHTML = f.label + (f.required ? '<span class="req">*</span>' : '');
    wrap.appendChild(label);

    let input;
    if (f.type === 'select') {
      input = document.createElement('select');
      for (const [val, text] of f.options) {
        const o = document.createElement('option');
        o.value = val;
        o.textContent = text;
        input.appendChild(o);
      }
    } else {
      input = document.createElement('input');
      if (f.type === 'date') {
        input.type = 'date';
      } else if (f.type === 'number') {
        // 灵棋经三部掷面数一类的整数字段：范围交给浏览器先拦一道，
        // 真正把关的仍是内核（越界/缺数由 request.chart_argv 明确拒绝）。
        input.type = 'number';
        input.step = f.step != null ? f.step : 1;
        input.inputMode = 'numeric';
        if (f.min != null) input.min = f.min;
        if (f.max != null) input.max = f.max;
      } else {
        input.type = 'text';
      }
      if (f.type === 'datetime') input.placeholder = 'YYYY-MM-DD HH:MM（留空用当前时间）';
      if (f.placeholder) input.placeholder = f.placeholder;
    }
    input.id = id;
    input.name = f.key;
    input.dataset.key = f.key;
    if (values && values[f.key] != null) input.value = values[f.key];
    input.addEventListener('input', refreshDeepLink);
    input.addEventListener('change', refreshDeepLink);

    // 时间类字段给一个"当前"快捷键：既省事，也把期望的格式演示出来
    if (f.type === 'datetime' || f.type === 'date') {
      const withTime = f.type === 'datetime';
      const row = document.createElement('div');
      row.className = 'field-row';
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'nowbtn';
      btn.textContent = withTime ? '现在' : '今天';
      btn.title = withTime ? '填入当前时间（YYYY-MM-DD HH:MM）' : '填入今天（YYYY-MM-DD）';
      btn.onclick = () => {
        input.value = nowValue(withTime);
        refreshDeepLink();
        saveDraft();
      };
      row.appendChild(input);
      row.appendChild(btn);
      wrap.appendChild(row);
    } else {
      wrap.appendChild(input);
    }
    box.appendChild(wrap);
  }
  refreshDeepLink();
}

/* 口径标注（铁律三的执行）：骨架科"无吉凶断语"、书源直录类"原文逐字"这类
   限定必须出现在页面上，不让用户误以为能断事。文案来自清单（DISCIPLINE_META），
   前端不另写一份，避免两处口径漂移。 */
function renderCaveat(d) {
  const el = $('disc-caveat');
  if (!el) return;
  const note = (d && d.caveat) ? d.caveat : '';
  el.textContent = note;
  el.hidden = !note;
}

/* 科目元信息：用清单里已有的 per_discipline，不新增任何请求 */
function disciplineMeta(d) {
  const pd = (state.manifest.per_discipline || {})[d.id];
  if (!pd) return '';
  const kb = (pd.bytes / 1024).toFixed(1);
  const rt = pd.runtime_files ? `，运行期脚本 ${pd.runtime_files} 个` : '';
  return `站点镜像：本学科 ${pd.files} 个文件 / ${kb} KB${rt}（含内核，全部在浏览器内取用）`;
}

function collectForm() {
  const out = {};
  for (const el of $('fields').querySelectorAll('[data-key]')) {
    const v = el.value.trim();
    if (v === '') continue;
    // 数字输入框转 Number：内核 chart_argv 要求 0..4 的整数，字符串会被拒
    out[el.dataset.key] = el.type === 'number' ? Number(v) : v;
  }
  return out;
}

function selectDiscipline(id, opts) {
  const keep = (opts && opts.keepValues) ? collectForm() : {};
  state.disc = id;
  renderTabs();
  renderFields(keep);
  saveDraft();
}

/* 记住上一次选择（本机，不外传） */
function saveDraft() {
  try {
    localStorage.setItem('yi.draft', JSON.stringify({
      disc: state.disc, values: collectForm(),
    }));
  } catch (e) { /* 隐私模式忽略 */ }
}

function loadDraft() {
  try {
    const raw = localStorage.getItem('yi.draft');
    return raw ? JSON.parse(raw) : null;
  } catch (e) { return null; }
}

/* ── Pyodide 启动与引擎取回 ───────────────────────────── */

async function loadPyodideOnce(onProgress) {
  if (state.pyodide) return state.pyodide;
  if (state.booting) return state.booting;
  state.booting = (async () => {
    setBadge('下载运行时…', 'busy');
    log('加载 Pyodide 运行时：' + CDN.base);
    const mod = await import(CDN.base + 'pyodide.mjs');
    const py = await mod.loadPyodide({
      indexURL: CDN.base,
      stdout: (s) => log('py: ' + s),
      stderr: (s) => log('py! ' + s),
    });
    state.pyodide = py;
    log('运行时就绪：Python ' + py.version);
    if (onProgress) onProgress();
    return py;
  })();
  return state.booting;
}

function neededFiles(disc, profile) {
  // 跑一科只需要：内核全部 + 本科全部（清单里已标注 discipline / profile）。
  const out = [];
  for (const f of state.manifest.files) {
    if (f.profile !== profile) continue;
    if (f.discipline === '*' || f.discipline === disc) out.push(f);
  }
  return out;
}

async function fetchIntoVFS(py, files, label) {
  let done = 0;
  const pending = files.filter((f) => !state.written.has(f.path));
  if (!pending.length) return 0;
  const concurrency = 8;
  let cursor = 0;
  async function worker() {
    while (cursor < pending.length) {
      const f = pending[cursor++];
      const res = await fetch(f.path, { cache: 'force-cache' });
      if (!res.ok) throw new Error(`取文件失败 ${res.status}：${f.path}`);
      const text = await res.text();
      py.FS.mkdirTree(f.path.split('/').slice(0, -1).join('/'));
      py.FS.writeFile(f.path, text);
      state.written.add(f.path);
      done++;
      if (done % 12 === 0) log(`${label} ${done}/${pending.length}`);
    }
  }
  await Promise.all(Array.from({ length: concurrency }, worker));
  log(`${label} 完成：${pending.length} 个文件`);
  return pending.length;
}

async function ensureEngineRuntime() {
  const py = await loadPyodideOnce();
  if (!state.ready) {
    // 运行时侧的适配层只需装一次；学科代码随每次推演按需补取（见 runReport）
    await fetchIntoVFS(py, neededFiles(state.disc, 'code'), '取引擎代码');
    const src = await (await fetch('engine_runtime.py')).text();
    py.FS.writeFile('/engine_runtime.py', src);
    py.runPython('import sys; sys.path.insert(0, "/")');
    state.ready = true;
    setBadge('已就绪', 'ok');
  }
}

/* ── 推演 ─────────────────────────────────────────────── */

async function runReport() {
  clearError();
  const d = currentDiscipline();
  if (!d) return;
  const values = collectForm();
  for (const f of d.fields) {
    if (f.required && !values[f.key]) {
      showError(`请填写：${f.label.replace(/（.*?）/g, '')}`);
      return;
    }
  }
  const req = Object.assign({ discipline: state.disc }, values);
  if (req.seed) req.seed = Number(req.seed);

  const outCard = $('out-card');
  outCard.setAttribute('aria-busy', 'true');
  $('run').disabled = true;
  $('result-actions').hidden = true;
  $('fallback-md').hidden = true;
  setProgress(0.05);
  setStatus('准备运行时…', 'busy');
  $('result').innerHTML = '<p class="placeholder">正在准备运行时与引擎…</p>';

  try {
    await ensureEngineRuntime();
    const py = state.pyodide;
    setProgress(0.35);
    // 学科代码与数据表都按当前学科补取：第一次装运行时，之后切科只补新科
    // （state.written 去重，已落盘的文件不会重复下载）
    await fetchIntoVFS(py, neededFiles(state.disc, 'code'), '取引擎代码');
    setProgress(0.45);
    setStatus('取回本学科数据表…', 'busy');
    await fetchIntoVFS(py, neededFiles(state.disc, 'doc'), '取数据表');

    setProgress(0.7);
    setStatus('推演中（chart → analyze → render）…', 'busy');
    log('请求：' + JSON.stringify(req));
    const api = py.pyimport('engine_runtime');
    const json = api.run(JSON.stringify(req), state.manifest.engine_root, '/out');
    const res = JSON.parse(json);
    state.result = res;

    setProgress(1);
    setStatus(`完成：${res.title}`, 'ok');
    renderReport(res);
  } catch (err) {
    console.error(err);
    const msg = (err && err.message) ? err.message : String(err);
    setStatus('推演失败', 'err');
    $('result').innerHTML = '<p class="placeholder">推演失败，详见下方日志。</p>';
    log('ERROR ' + msg);
    showError(msg.length > 400 ? msg.slice(0, 400) + '…' : msg);
  } finally {
    outCard.removeAttribute('aria-busy');
    $('run').disabled = false;
    setProgress(null);
  }
}

function renderReport(res) {
  const box = $('result');
  box.innerHTML = '';
  const frame = document.createElement('iframe');
  frame.setAttribute('title', 'Yi 报告');
  frame.srcdoc = res.html;
  box.appendChild(frame);
  setTimeout(() => {
    try { frame.style.height = Math.max(560, frame.contentDocument.body.scrollHeight + 40) + 'px'; }
    catch (e) { /* 跨域保护下忽略 */ }
  }, 400);

  $('result-actions').hidden = false;
  $('fallback-md').hidden = false;
  $('fallback-md').textContent = res.md;
  const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '');
  const stem = `${res.discipline}-${stamp}`;
  $('dl-md').onclick = () => download(stem + '.md', res.md, 'text/markdown');
  $('dl-html').onclick = () => download(stem + '.html', res.html, 'text/html');
  $('copy-md').onclick = () => copyText(res.md, 'MD 正文已复制');
  $('open-html').onclick = (ev) => {
    ev.preventDefault();
    const blob = new Blob([res.html], { type: 'text/html;charset=utf-8' });
    window.open(URL.createObjectURL(blob), '_blank');
  };
}

/* ── 主题 ─────────────────────────────────────────────── */

function initTheme() {
  let saved = null;
  try { saved = localStorage.getItem('yi.theme'); } catch (e) { /* ignore */ }
  if (!saved) {
    saved = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'ink' : 'paper';
  }
  document.documentElement.dataset.theme = saved;
  $('theme').onclick = () => {
    const next = document.documentElement.dataset.theme === 'ink' ? 'paper' : 'ink';
    const apply = () => {
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem('yi.theme', next); } catch (e) { /* ignore */ }
    };
    // 支持 View Transitions 的浏览器走一次纸墨过渡，其余直接换
    if (document.startViewTransition && !REDUCED) document.startViewTransition(apply);
    else apply();
  };
}

/* ── 入场动效 ─────────────────────────────────────────── */

function initReveal() {
  const items = document.querySelectorAll('.reveal');
  window.__yiRevealReady = true;   // 关掉首屏脚本里的三秒兜底
  if (!items.length || !('IntersectionObserver' in window)) {
    items.forEach((el) => el.classList.add('in'));
    return;
  }
  const io = new IntersectionObserver((entries) => {
    for (const en of entries) {
      if (en.isIntersecting) {
        en.target.classList.add('in');
        io.unobserve(en.target);
      }
    }
  }, { rootMargin: '0px 0px -6% 0px', threshold: 0.04 });
  items.forEach((el) => io.observe(el));
}

/* ── 启动 ─────────────────────────────────────────────── */

async function main() {
  initTheme();
  initReveal();

  try {
    const res = await fetch('manifest.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error(res.status + ' ' + res.statusText);
    state.manifest = await res.json();
  } catch (e) {
    setBadge('清单缺失', 'err');
    $('result').innerHTML =
      '<p class="placeholder">读不到 manifest.json —— 本页需要通过站点访问' +
      '（GitHub Pages 或 <code>python tools/serve_web.py</code>），不能直接双击本地文件打开。</p>';
    return;
  }

  const m = state.manifest;
  $('build-info').textContent =
    `引擎内核 v${m.yishu_core_version}　｜　镜像 ${m.totals.files} 个文件 / ` +
    `${(m.totals.bytes / 1024).toFixed(0)} KB　｜　构建于 ${m.generated}　｜　${m.notice || ''}`;

  const deep = readDeepLink();
  const draft = loadDraft();
  const known = new Set(m.disciplines.map((d) => d.id));
  let disc = null;
  if (deep.disc && known.has(deep.disc)) disc = deep.disc;
  else if (draft && draft.disc && known.has(draft.disc)) disc = draft.disc;
  else disc = m.disciplines[0].id;

  state.disc = disc;
  renderTabs();
  const preset = Object.keys(deep.values).length ? deep.values
    : ((draft && draft.disc === disc) ? draft.values : {});
  renderFields(preset);

  $('form').addEventListener('submit', (ev) => { ev.preventDefault(); runReport(); });
  $('reset').onclick = () => {
    renderFields({});
    saveDraft();
    clearError();
    setStatus('等待推演');
    $('result-actions').hidden = true;
    $('fallback-md').hidden = true;
    $('result').innerHTML = '<p class="placeholder">报告将显示在这里。</p>';
  };
  $('fields').addEventListener('change', saveDraft);
  $('fields').addEventListener('input', saveDraft);
  $('copylink').onclick = () => copyText($('deeplink').value, '深链已复制');
  // 深链框整条选中，方便直接复制
  $('deeplink').addEventListener('focus', (ev) => ev.target.select());
  $('deeplink-hint').textContent =
    '把这条链接给任何网页端 AI 或同事，打开就是同一个填好的表单；末尾加 &auto=1 则打开即出报告。';

  if (deep.auto && Object.keys(deep.values).length) {
    log('深链要求自动推演');
    // 窄屏下表单与报告串成单列：自动把报告滚进视野，省掉一次手动下滑
    if (!REDUCED && window.matchMedia
        && window.matchMedia('(max-width: 980px)').matches) {
      setTimeout(() => {
        const box = $('out-card');
        if (box) box.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 240);
    }
    runReport();
  } else {
    setBadge(navigator.onLine ? '待命' : '离线');
  }
}

main();
