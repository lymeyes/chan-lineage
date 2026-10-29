#!/usr/bin/env python3
"""
build_site.py
读 data/lineage.json + data/patriarchs/*.yaml，生成自包含、零依赖的
site/index.html（数据内嵌，可双击打开）。左侧可折叠分支树，点击节点右侧
显示生平/引文（来自 YAML；未补者显示「待补」并指向对应文件）。
"""
import json, os, glob, yaml

ROOT = os.path.dirname(__file__)
DATA = os.path.join(ROOT, "..", "data")
OUT = os.path.join(ROOT, "..", "site", "index.html")

def load():
    with open(os.path.join(DATA, "lineage.json"), encoding="utf-8") as f:
        lineage = json.load(f)
    bios = {}
    for fp in sorted(glob.glob(os.path.join(DATA, "patriarchs", "*.yaml"))):
        with open(fp, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        if d and "id" in d:
            bios[d["id"]] = d
    return lineage, bios

def main():
    lineage, bios = load()
    payload = {
        "tree": lineage["tree"],
        "nodes": lineage["nodes"],
        "meta": lineage["meta"],
        "bios": bios,
    }
    data_js = json.dumps(payload, ensure_ascii=False)
    html = TEMPLATE.replace("/*__DATA__*/", data_js)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"祖师卡已载入 : {len(bios)} 份")
    print(f"写出站点     : {os.path.abspath(OUT)}  ({len(html)//1024} KB)")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>禅宗法脉 · 交互谱系</title>
<style>
  :root{
    --bg:#ffffff; --panel:#f8fafc; --line:#e2e8f0; --ink:#1e293b; --muted:#64748b;
    --accent:#0f172a;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--ink);background:var(--bg)}
  #app{display:flex;height:100vh}
  #left{width:360px;min-width:300px;border-right:1px solid var(--line);display:flex;flex-direction:column;background:var(--panel)}
  #head{padding:12px 14px;border-bottom:1px solid var(--line)}
  #head h1{font-size:15px;margin:0 0 8px}
  #head .sub{font-size:11px;color:var(--muted);margin-bottom:8px}
  #tools{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
  #tools input{flex:1;min-width:120px;padding:5px 8px;border:1px solid var(--line);border-radius:6px;font-size:12px}
  #tools button{padding:5px 9px;border:1px solid var(--line);background:#fff;border-radius:6px;font-size:12px;cursor:pointer}
  #tools button:hover{background:#eef2f7}
  #tree{flex:1;overflow:auto;padding:8px 6px;font-size:13px;line-height:1.5}
  ul.t{list-style:none;margin:0;padding-left:14px}
  ul.t.root{padding-left:0}
  li.t{margin:1px 0}
  .row{display:flex;align-items:center;gap:5px;padding:2px 4px;border-radius:5px;cursor:pointer;white-space:nowrap}
  .row:hover{background:#eef2f7}
  .row.sel{background:#dbeafe}
  .tg{width:14px;text-align:center;color:var(--muted);font-size:10px;user-select:none}
  .dot{width:9px;height:9px;border-radius:50%;flex:none}
  .nm{overflow:hidden;text-overflow:ellipsis}
  .nm.hit{background:#fde68a}
  #right{flex:1;overflow:auto;padding:26px 34px}
  .empty{color:var(--muted);margin-top:40px;text-align:center}
  .badge{display:inline-block;padding:2px 9px;border-radius:999px;color:#fff;font-size:12px;margin-left:8px;vertical-align:middle}
  h2{font-size:22px;margin:0 0 4px}
  .hon{color:var(--muted);font-size:14px;margin-bottom:14px}
  .crumbs{font-size:12px;color:var(--muted);margin-bottom:18px;line-height:1.8}
  .crumbs b{color:var(--ink)}
  .meta-grid{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;font-size:13px;margin-bottom:18px}
  .meta-grid .k{color:var(--muted)}
  .sec{margin-top:22px}
  .sec h3{font-size:14px;border-left:3px solid var(--accent);padding-left:8px;margin:0 0 8px}
  .bio{white-space:pre-wrap;font-size:14px;line-height:1.9;background:var(--panel);padding:12px 14px;border-radius:8px}
  .say{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-bottom:10px;background:#fff}
  .say .t{white-space:pre-wrap;font-size:14px;line-height:1.8}
  .say .r{font-size:12px;color:var(--muted);margin-top:6px}
  .todo{border:1px dashed #cbd5e1;color:var(--muted);border-radius:8px;padding:12px 14px;font-size:13px}
  code{background:#f1f5f9;padding:1px 5px;border-radius:4px;font-size:12px}
</style>
</head>
<body>
<div id="app">
  <div id="left">
    <div id="head">
      <h1>禅宗法脉 · 交互谱系</h1>
      <div class="sub" id="subline"></div>
      <div id="tools">
        <input id="q" placeholder="搜索人名…" />
        <button id="expand">展开全部</button>
        <button id="reset">重置</button>
      </div>
    </div>
    <div id="tree"></div>
  </div>
  <div id="right"><div class="empty">← 点击左侧任一节点，查看其生平与引文</div></div>
</div>
<script>
const PAYLOAD = /*__DATA__*/;
const {tree:RAW, nodes:NODES, meta:META, bios:BIOS} = PAYLOAD;
const HOUSES = {"源头":"#6b7280","南岳系":"#2563eb","临济宗":"#dc2626","沩仰宗":"#ea580c",
  "黄龙派":"#d97706","杨岐派":"#ca8a04","青原系":"#059669","曹洞宗":"#0891b2",
  "云门宗":"#7c3aed","法眼宗":"#db2777"};
const ID2NAME = {}; const ID2HOUSE = {}; const ID2PARENT = {}; const ROWBYID = {};
NODES.forEach(n=>{ID2NAME[n.id]=n.name;ID2HOUSE[n.id]=n.house;ID2PARENT[n.id]=n.parent;});
document.getElementById('subline').textContent =
  `${META.total_nodes} 节点 · 最大 ${META.max_depth} 世 · 数据源：${META.source_texts.join('/')}`;

const treeEl = document.getElementById('tree');
const rightEl = document.getElementById('right');
let selId = null;

function makeNode(n, depth){
  const li = document.createElement('li'); li.className='t';
  const row = document.createElement('div'); row.className='t row';
  const hasKids = n.children && n.children.length;
  const tg = document.createElement('span'); tg.className='tg';
  tg.textContent = hasKids ? '▾' : '';
  const dot = document.createElement('span'); dot.className='dot';
  dot.style.background = HOUSES[n.house]||'#9ca3af';
  const nm = document.createElement('span'); nm.className='nm'; nm.textContent=n.name;
  nm.dataset.id = n.id;
  row.appendChild(tg); row.appendChild(dot); row.appendChild(nm);
  li.appendChild(row);
  let ul=null;
  if(hasKids){
    ul=document.createElement('ul'); ul.className='t';
    n.children.forEach(c=>ul.appendChild(makeNode(c, depth+1)));
    li.appendChild(ul);
  }
  // 默认折叠深层
  if(depth>=4 && hasKids){ ul.style.display='none'; tg.textContent='▸'; }
  tg.onclick = (e)=>{ e.stopPropagation();
    if(!hasKids) return;
    const open = ul.style.display!=='none';
    ul.style.display = open?'none':'block';
    tg.textContent = open?'▸':'▾';
  };
  row.onclick = ()=>select(n.id);
  row._tg = tg; row._ul = ul; row._hasKids = hasKids;
  nm._row = row; ROWBYID[n.id] = row;
  return li;
}
treeEl.appendChild(makeNode(RAW,0));

function select(id){
  selId=id;
  document.querySelectorAll('.row.sel').forEach(r=>r.classList.remove('sel'));
  const r = ROWBYID[id];
  if(r) r.classList.add('sel');
  renderDetail(id);
}

function renderDetail(id){
  const b = BIOS[id];
  const name = ID2NAME[id]||id;
  const house = ID2HOUSE[id]||'';
  const color = HOUSES[house]||'#9ca3af';
  // 谱系路径
  const path=[]; let p=id;
  while(p){ path.unshift(ID2NAME[p]||p); p=ID2PARENT[p]; }
  const teacher = ID2PARENT[id]? (ID2NAME[ID2PARENT[id]]||ID2PARENT[id]) : '—';
  let h = `<h2>${name}${b&&b.honorific?` <span class="hon">（${b.honorific}）</span>`:''}`+
          (house?`<span class="badge" style="background:${color}">${house}</span>`:'')+`</h2>`;
  h += `<div class="crumbs">谱系：${path.map(x=>`<b>${x}</b>`).join(' → ')}</div>`;
  h += `<div class="meta-grid">`;
  if(b){
    if(b.dynasty) h+=`<div class="k">朝代</div><div>${b.dynasty}</div>`;
    if(b.birth_death) h+=`<div class="k">生卒</div><div>${b.birth_death}</div>`;
    if(b.region) h+=`<div class="k">驻锡</div><div>${b.region}</div>`;
    if(b.teacher) h+=`<div class="k">师承</div><div>${b.teacher}</div>`;
    else h+=`<div class="k">师承</div><div>${teacher}</div>`;
    if(b.source_ref) h+=`<div class="k">首要出处</div><div>${b.source_ref}</div>`;
    if(b.cbeta) h+=`<div class="k">CBETA</div><div>${b.cbeta}</div>`;
    if(b.status) h+=`<div class="k">状态</div><div>${b.status}</div>`;
    if(b.evidence) h+=`<div class="k">证据等级</div><div>${b.evidence==='primary'?'引自正典（一手灯录）':'汇编级（二手综述）'}</div>`;
    if(b.verify_status){const vsl=b.verify_status==='line_verified'?'已逐字校核（CBETA/X）':b.verify_status==='sourced'?'已据正典核校（待 CBETA 逐字对校）':'已锚定·待逐字校核';h+=`<div class="k">核验状态</div><div>${vsl}</div>`;}
  } else {
    h+=`<div class="k">师承</div><div>${teacher}</div>`;
  }
  h += `</div>`;
  if(b && b.bio){
    h += `<div class="sec"><h3>生平</h3><div class="bio">${escapeHtml(b.bio)}</div></div>`;
  }
  if(b && b.sayings && b.sayings.length){
    h += `<div class="sec"><h3>代表公案 / 语录</h3>`;
    b.sayings.forEach(s=>{
      h += `<div class="say"><div class="t">${escapeHtml(s.text)}</div>`+
           (s.ref?`<div class="r">出处：${escapeHtml(s.ref)}</div>`:'')+`</div>`;
    });
    h += `</div>`;
  }
  if(!b){
    h += `<div class="todo">生平 / 引文：<b>待补</b>。请编辑 <code>data/patriarchs/${id}.yaml</code>，`+
         `按 <code>data/schema.md</code> 填写（须标注精确出处，不得杜撰）。</div>`;
  } else if(b.status==='sample'){
    h += `<div class="todo">此卡为 <b>样例种子</b>（status: sample），内容取自灯录并标注出处，`+
         `待 CBETA 电子佛典逐字校核后改为 core。</div>`;
  }
  rightEl.innerHTML = h;
}
function escapeHtml(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

// 搜索
document.getElementById('q').addEventListener('input', e=>{
  const v=e.target.value.trim();
  if(!v){ document.querySelectorAll('.nm.hit').forEach(x=>x.classList.remove('hit')); return; }
  let first=null;
  document.querySelectorAll('.nm').forEach(nm=>{
    const hit = nm.textContent.indexOf(v)>=0;
    nm.classList.toggle('hit', hit);
    if(hit){
      // 展开所有祖先（按 id 回溯父链）
      let pid = ID2PARENT[nm.dataset.id];
      while(pid){ const r=ROWBYID[pid]; if(r && r._hasKids && r._ul){ r._ul.style.display='block'; r._tg.textContent='▾'; } pid=ID2PARENT[pid]; }
      if(!first) first=nm.dataset.id;
    }
  });
  if(first) select(first);
});
document.getElementById('expand').onclick=()=>{
  document.querySelectorAll('#tree .tg').forEach(tg=>{ if(tg.textContent==='▸'){tg.click();} });
};
document.getElementById('reset').onclick=()=>{ location.reload(); };
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
