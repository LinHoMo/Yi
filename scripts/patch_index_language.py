# -*- coding: utf-8 -*-
"""index.html：主文改为完整解读，去掉「人话章节」表述。"""
from pathlib import Path
import re

P = Path(r"C:\Users\Lin\Desktop\skills\liu-yao\index.html")
html = P.read_text(encoding="utf-8")

html = html.replace("人话解读", "解读")
html = html.replace("五步思维链（可审计）", "推演过程（备查）")
html = html.replace("这意味着什么", "更直白一点")
html = html.replace("复制人话解读", "复制解读正文")
html = html.replace("五步链", "推演")
html = html.replace("人话层", "解读正文")

# 更新渲染逻辑：body 段落优先
old = '''    const h=sample.human||{};
    document.getElementById('humanHeadline').textContent=h.headline||'—';
    document.getElementById('humanPlain').textContent=h.plain_summary||'';
    document.getElementById('humanMeaning').textContent=h.what_it_means||'';
    document.getElementById('humanTiming').textContent=h.timing_plain||sample.yingqi||'';
    document.getElementById('humanAdvice').innerHTML=(h.advice||[]).map(a=>`<li>${escapeHtml(a)}</li>`).join('')||'<li>先观察关键节点</li>';
    document.getElementById('humanCaveat').textContent=h.caveat||'';

    const chain=document.getElementById('chainBox');
    chain.innerHTML='';
    chainSteps(sample).forEach((s,i)=>{
      const div=document.createElement('div');
      div.className='step '+ (s.kind||'');
      div.innerHTML=`<div class="idx">${String(i+1).padStart(2,'0')}</div>
        <div class="lab">[${escapeHtml(s.lab)}]</div>
        <p>${escapeHtml(s.body||'')}</p>`;
      chain.appendChild(div);
    });'''

new = '''    const h=sample.human||{};
    const paras=(h.body&&h.body.length)?h.body:[h.lead||h.plain_summary||''].filter(Boolean);
    document.getElementById('humanHeadline').textContent=h.headline||h.lead||'—';
    document.getElementById('humanPlain').innerHTML=paras.map(p=>`<div style="margin:0 0 12px">${escapeHtml(p)}</div>`).join('');
    document.getElementById('humanMeaning').textContent=h.what_it_means||'';
    document.getElementById('humanTiming').textContent=h.timing_plain||sample.yingqi||'';
    document.getElementById('humanAdvice').innerHTML=(h.advice||[]).map(a=>`<li>${escapeHtml(a)}</li>`).join('')||'<li>先观察关键节点</li>';
    document.getElementById('humanCaveat').textContent=h.caveat||'';

    // 推演过程：优先用 process（叙述体），没有再退回 chain 标签行
    const chain=document.getElementById('chainBox');
    chain.innerHTML='';
    const process=(h.process&&h.process.length)?h.process:null;
    if(process){
      process.forEach((s,i)=>{
        const div=document.createElement('div');
        div.className='step'+(s.label==='综合'?' synthesis':'');
        div.innerHTML=`<div class="idx">${String(i+1).padStart(2,'0')}</div>
          <div class="lab">${escapeHtml(s.label)}</div>
          <p>${escapeHtml(s.text||'')}</p>`;
        chain.appendChild(div);
      });
    } else {
      chainSteps(sample).forEach((s,i)=>{
        if(s.lab==='格局'||s.lab==='格局要点') return;
        const div=document.createElement('div');
        div.className='step '+ (s.kind||'');
        div.innerHTML=`<div class="idx">${String(i+1).padStart(2,'0')}</div>
          <div class="lab">${escapeHtml(s.lab)}</div>
          <p>${escapeHtml(s.body||'')}</p>`;
        chain.appendChild(div);
      });
    }'''

if old not in html:
    # try flexible match
    print("WARN: exact JS block not found, doing label-only update")
else:
    html = html.replace(old, new, 1)

# 副标题
html = html.replace(
    "代码排盘 · 五步思维链 · 人话解读 · HTML 导出",
    "代码排盘 · 规则推演 · 自然解读 · HTML 导出",
)
html = html.replace(
    "装卦由 <span class=\"mono\">liuyao_engine.py</span> 执行 · 断卦走五步思维链 · 人话层 <span class=\"mono\">human_narrative.py</span>",
    "装卦由 <span class=\"mono\">liuyao_engine.py</span> 执行 · 正文由 <span class=\"mono\">human_narrative.py</span> 统一撰写 · 推演过程仅作备查",
)

P.write_text(html, encoding="utf-8")
print("index.html updated", len(html))
