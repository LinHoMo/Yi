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
    setStatus((label || '已复制') + '到剪贴板', 'ok');
  } catch (e) {
    setStatus('复制失败，请手动选中复制', 'err');
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

function renderTabs() {
  const box = $('tabs');
  box.innerHTML = '';
  for (const d of state.manifest.disciplines) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'tab';
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-selected', String(d.id === state.disc));
    b.innerHTML = `${d.name}<span class="kind">${d.kind}</span>`;
    b.onclick = () => selectDiscipline(d.id, { keepValues: true });
    box.appendChild(b);
  }
}

function renderFields(values) {
  const d = currentDiscipline();
  $('disc-summary').textContent = d ? d.summary : '';
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
      input.type = f.type === 'date' ? 'date' : (f.type === 'datetime' ? 'text' : 'text');
      if (f.type === 'datetime') input.placeholder = 'YYYY-MM-DD HH:MM（留空用当前时间）';
      if (f.placeholder) input.placeholder = f.placeholder;
    }
    input.id = id;
    input.name = f.key;
    input.dataset.key = f.key;
    if (values && values[f.key] != null) input.value = values[f.key];
    input.addEventListener('input', refreshDeepLink);
    input.addEventListener('change', refreshDeepLink);
    wrap.appendChild(input);
    box.appendChild(wrap);
  }
  refreshDeepLink();
}

function collectForm() {
  const out = {};
  for (const el of $('fields').querySelectorAll('[data-key]')) {
    const v = el.value.trim();
    if (v !== '') out[el.dataset.key] = v;
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
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('yi.theme', next); } catch (e) { /* ignore */ }
  };
}

/* ── 启动 ─────────────────────────────────────────────── */

async function main() {
  initTheme();
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
  $('deeplink-hint').textContent =
    '把这条链接给任何网页端 AI 或同事，打开就是同一个填好的表单；末尾加 &auto=1 则打开即出报告。';

  if (deep.auto && Object.keys(deep.values).length) {
    log('深链要求自动推演');
    runReport();
  } else {
    setBadge(navigator.onLine ? '待命' : '离线');
  }
}

main();
