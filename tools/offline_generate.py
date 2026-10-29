#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宗脉谱系 · 离线生成器
====================
读取 chan-lineage 的结构化数据（lineage.json + 祖师 YAML），
在「宗脉谱系」库内生成：

  - 祖师/<slug>.md    每人一份生平（draft 写全；named_only 诚实列名占位）
  - 站点/index.html   自包含离线谱系索引（谱系树 + 搜索 + 点人看详情）
  - 谱系总览.md / README.md

用法：
  python3 _generate.py
（只读 chan-lineage 数据，写入本目录；不改动任何源文件。）
"""
import os
import json
import datetime
import yaml

def _resolve_data_dir():
    """定位 chan-lineage/data：环境变量 > 仓库内(本文件所在仓库) > 已知默认路径。

    这样同一份脚本既能放在仓库 tools/ 下跑，也能被同步到 Obsidian 离线库里跑。
    """
    cands = []
    env = os.environ.get("CHAN_LINEAGE_DATA")
    if env:
        cands.append(env)
    here = os.path.dirname(os.path.abspath(__file__))
    cands.append(os.path.join(os.path.dirname(here), "data"))            # 仓库 tools/..
    cands.append(os.path.expanduser("~/WorkBuddy/task/Project/chan-lineage/data"))
    for c in cands:
        if os.path.exists(os.path.join(c, "lineage.json")):
            return c
    raise SystemExit(
        "找不到 chan-lineage/data（已试：%s）。\n"
        "请先跑 tools/rebuild_offline.py，或设置环境变量 CHAN_LINEAGE_DATA。" % " | ".join(cands))


SRC_DATA = _resolve_data_dir()
OUT = os.path.dirname(os.path.abspath(__file__))
PATRIARCHS = os.path.join(SRC_DATA, "patriarchs")
LINEAGE = os.path.join(SRC_DATA, "lineage.json")

HOUSE_COLORS = {
    "源头": "#a8946b", "临济宗": "#c0392b", "杨岐派": "#e07b39", "黄龙派": "#d4a017",
    "沩仰宗": "#2e8b57", "曹洞宗": "#2980b9", "云门宗": "#8e44ad", "法眼宗": "#16a085",
    "青原系": "#7f8c8d", "南岳系": "#c0588a", "牛头宗": "#6b8e23", "未知": "#999999",
}

GEN_DATE = datetime.date.today().isoformat()


def slugify(id_):
    return id_.replace("/", "_").replace(":", "_")


def load_cards():
    cards = {}
    for fn in os.listdir(PATRIARCHS):
        if not fn.endswith(".yaml"):
            continue
        try:
            with open(os.path.join(PATRIARCHS, fn), encoding="utf-8") as f:
                d = yaml.safe_load(f) or {}
            cards[d.get("id", fn[:-5])] = d
        except Exception as e:
            print("!! 读取 %s 失败: %s" % (fn, e))
    return cards


def build_payload(lineage, cards):
    """构造 HTML 嵌入用的统一数据：nodes（扁平）+ tree（嵌套）。"""
    node_by_id = {n["id"]: n for n in lineage["nodes"]}

    nodes = []
    draft = named_only = 0
    house_dist = {}
    for nid, node in node_by_id.items():
        if nid == "禅宗法脉":   # 根节点（2026-10-29 去 ROOT:: 前缀后按名字判定）
            continue
        card = cards.get(nid, {})
        status = card.get("status", "named_only")
        if status == "draft":
            draft += 1
        else:
            named_only += 1
        house = node.get("house") or card.get("school") or "未知"
        house_dist[house] = house_dist.get(house, 0) + 1
        sayings = card.get("sayings") or []
        nodes.append({
            "id": nid,
            "slug": slugify(nid),
            "name": card.get("name") or node.get("name") or nid,
            "house": house,
            "parent": node.get("parent"),
            "depth": node.get("depth", 0),
            "school": card.get("school") or "—",
            "teacher": card.get("teacher") or "—",
            "dynasty": card.get("dynasty") or "—",
            "region": card.get("region") or "—",
            "honorific": card.get("honorific") or "",
            "status": status,
            "bio": (card.get("bio") or "").strip(),
            "sayings": [{"text": s.get("text", ""), "ref": s.get("ref", "")}
                        for s in sayings if isinstance(s, dict)],
            "source_ref": card.get("source_ref") or "",
            "cbeta": card.get("cbeta") or "",
            "evidence": card.get("evidence") or ("primary" if status == "draft" else "—"),
            "verify_status": card.get("verify_status") or ("anchor_only" if status == "draft" else "stub"),
            "verify": (card.get("verify") or "").strip(),
        })

    # 由 lineage 嵌套 tree 派生（保留其层级结构），附加 slug
    def walk(t):
        return {
            "id": t["id"], "name": t["name"], "house": t.get("house", "源头"),
            "slug": slugify(t["id"]),
            "children": [walk(c) for c in t.get("children", [])],
        }
    tree_root = lineage.get("tree")
    tree = [walk(tree_root)] if isinstance(tree_root, dict) else [walk(t) for t in tree_root]

    payload = {
        "nodes": nodes,
        "tree": tree,
        "houseColors": HOUSE_COLORS,
        "stats": {
            "total": len(nodes), "draft": draft, "named_only": named_only,
            "houseDist": house_dist, "genDate": GEN_DATE,
        },
    }
    return payload


def render_md(p):
    L = []
    L.append("# %s" % p["name"])
    if p["honorific"]:
        L.append("> 禅宗法脉 · %s · %s" % (p["house"], p["honorific"]))
    else:
        L.append("> 禅宗法脉 · %s" % p["house"])
    L.append("")
    L.append("- **房支/宗派**：%s" % p["school"])
    L.append("- **朝代**：%s" % p["dynasty"])
    L.append("- **驻锡/地域**：%s" % p["region"])
    L.append("- **师承**：%s" % p["teacher"])
    if p["source_ref"] or p["cbeta"]:
        anchor = p["source_ref"] or ""
        if p["cbeta"]:
            anchor += ("；" if anchor else "") + "CBETA：" + p["cbeta"]
        L.append("- **文献锚点**：%s" % anchor)
    L.append("")
    L.append("## 生平")
    L.append("")
    bio = p["bio"] or "（暂无生平记载）"
    L.append(bio)
    L.append("")
    if p["sayings"]:
        L.append("## 语录 / 机缘")
        L.append("")
        for s in p["sayings"]:
            ref = "《%s》" % s["ref"] if s["ref"] else ""
            L.append("> %s %s" % (s["text"], ref))
        L.append("")
    L.append("## 证据与核验")
    L.append("")
    L.append("- **证据等级**：%s" % p["evidence"])
    _vsl = {"line_verified": "已逐字校核（CBETA/X）", "sourced": "已据正典核校（待 CBETA 逐字对校）"}.get(p["verify_status"], "已锚定·待逐字校核")
    L.append("- **核验状态**：%s" % _vsl)
    if p["verify"]:
        L.append("- **备注**：%s" % p["verify"])
    L.append("")
    L.append("---")
    L.append("")
    L.append("[返回宗脉谱系索引](../站点/index.html)")
    return "\n".join(L) + "\n"


HTML_TEMPLATE = r"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>宗脉谱系 · 禅宗法脉传承</title>
<style>
  :root{--bg:#fbfaf7;--panel:#ffffff;--ink:#2b2b2b;--muted:#7a756c;
        --line:#d8d2c4;--edge:#b9b2a3;--accent:#a8946b;}
  *{box-sizing:border-box;}
  html,body{margin:0;height:100%;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
        background:var(--bg);color:var(--ink);font-size:14px;}
  #app{display:flex;flex-direction:column;height:100vh;}
  header{padding:10px 16px;border-bottom:1px solid var(--line);background:var(--panel);}
  header h1{font-size:17px;margin:0 0 2px;font-weight:600;letter-spacing:.5px;}
  header .hint{font-size:12px;color:var(--muted);}
  .bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:10px 16px;
       border-bottom:1px solid var(--line);background:var(--panel);}
  .bar input[type=text]{padding:7px 11px;border:1px solid var(--line);border-radius:8px;font-size:13px;width:260px;outline:none;}
  .bar input[type=text]:focus{border-color:var(--accent);}
  .bar select{padding:6px 9px;border:1px solid var(--line);border-radius:8px;font-size:13px;background:#fff;}
  .chips{display:flex;gap:8px;flex-wrap:wrap;margin-left:auto;}
  .chip{font-size:12px;color:var(--muted);background:#f1ede3;border:1px solid var(--line);
        border-radius:20px;padding:3px 11px;}
  .chip b{color:var(--ink);}
  #main{flex:1;display:flex;min-height:0;}
  #tree{width:38%;min-width:280px;max-width:520px;overflow:auto;padding:12px 8px 40px 16px;
        border-right:1px solid var(--line);background:#fcfbf8;}
  #detail{flex:1;overflow:auto;padding:20px 26px 60px;}
  ul.t{list-style:none;margin:0;padding-left:16px;}
  ul.t ul.t{padding-left:14px;border-left:1px dashed var(--edge);margin-left:4px;}
  .n{display:flex;align-items:center;gap:6px;padding:3px 4px;border-radius:6px;cursor:pointer;line-height:1.5;}
  .n:hover{background:#f1ede3;}
  .n.sel{background:#efe7d6;font-weight:600;}
  .dot{width:9px;height:9px;border-radius:50%;flex:0 0 auto;}
  .tgl{width:14px;flex:0 0 auto;color:var(--muted);font-size:11px;user-select:none;}
  .nm{font-size:13px;}
  .nm.dim{color:var(--muted);}
  .card{border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:20px 22px;
        max-width:780px;box-shadow:0 2px 12px rgba(0,0,0,.04);}
  .card h2{margin:0 0 4px;font-size:22px;}
  .card .hon{color:var(--muted);font-size:13px;margin-bottom:14px;}
  .tags{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:14px;}
  .tag{font-size:12px;padding:3px 10px;border-radius:6px;background:#f1ede3;border:1px solid var(--line);}
  .tag.h{color:#fff;}
  .kv{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:13px;margin-bottom:14px;}
  .kv dt{color:var(--muted);}
  .bio{line-height:1.85;white-space:pre-wrap;margin:8px 0 16px;}
  .saying{border-left:3px solid var(--accent);background:#f7f3ea;padding:9px 13px;border-radius:0 8px 8px 0;
          margin:8px 0;line-height:1.8;}
  .saying .ref{display:block;font-size:12px;color:var(--muted);margin-top:3px;}
  .ev{display:inline-block;font-size:12px;padding:2px 9px;border-radius:5px;margin-right:6px;}
  .ev.p{background:#e7f4ea;color:#1d7a3a;}
  .ev.a{background:#fdeede;color:#b5701a;}
  .ev.s{background:#f0f0f0;color:#666;}
  .muted{color:var(--muted);}
  .empty{color:var(--muted);padding:40px;text-align:center;}
  .legend{font-size:12px;color:var(--muted);margin-top:18px;display:flex;gap:12px;flex-wrap:wrap;}
  .legend span{display:inline-flex;align-items:center;gap:5px;}
  footer{padding:8px 16px;border-top:1px solid var(--line);background:var(--panel);
         font-size:12px;color:var(--muted);}
  a{color:#9a6b2f;}
</style></head><body>
<div id="app">
<header><h1>宗脉谱系 · 禅宗法脉传承</h1>
<div class="hint">七佛 → 西天二十八祖 → 东土六祖 → 五家七宗；点击左侧人名查看生平与语录；支持搜索与房支筛选。</div></header>
<div class="bar">
  <input type="text" id="q" placeholder="搜索人名 / 房支 / 师承…">
  <select id="house"><option value="">全部房支</option></select>
  <div class="chips" id="chips"></div>
</div>
<div id="main">
  <div id="tree"><ul class="t" id="troot"></ul><div class="legend" id="legend"></div></div>
  <div id="detail"><div class="empty">← 从左侧谱系树点选一位祖师，或从下方结果中点选。</div></div>
</div>
<footer>宗脉谱系 · 离线静态索引 · 数据源自 chan-lineage（1977 节点）· 生成于 __GENDATE__</footer>
</div>
<script>
const PAYLOAD = __PAYLOAD__;
const HC = PAYLOAD.houseColors;
const nodes = PAYLOAD.nodes;
const byId = {}; nodes.forEach(n=>byId[n.id]=n);
const slug2node = {}; nodes.forEach(n=>slug2node[n.slug]=n);
let selected = null;

/* ---- 谱系树渲染 ---- */
function colorDot(h){const c=HC[h]||"#999";return '<span class="dot" style="background:'+c+'"></span>';}
function makeNode(t, depth){
  const li=document.createElement("li");
  const wrap=document.createElement("div"); wrap.className="n";
  const hasKids=(t.children&&t.children.length);
  const tgl=document.createElement("span"); tgl.className="tgl";
  const nm=document.createElement("span"); nm.className="nm";
  nm.innerHTML=colorDot(t.house)+" "+t.name;
  wrap.appendChild(tgl); wrap.appendChild(nm); li.appendChild(wrap);
  if(hasKids){
    const ul=document.createElement("ul"); ul.className="t";
    t.children.forEach(c=>ul.appendChild(makeNode(c,depth+1)));
    li.appendChild(ul);
    const collapsed = depth>=2;
    if(collapsed){ul.style.display="none";tgl.textContent="▸";}
    else{tgl.textContent="▾";}
    tgl.onclick=(e)=>{e.stopPropagation();const sh=ul.style.display==="none";
      ul.style.display=sh?"block":"none";tgl.textContent=sh?"▾":"▸";};
  } else { tgl.textContent="·"; tgl.style.color="transparent"; }
  wrap.onclick=(e)=>{e.stopPropagation();selectById(t.id);};
  li._t=t; li._ul=hasKids?ul:null; li._tgl=tgl;
  return li;
}
const troot=document.getElementById("troot");
PAYLOAD.tree.forEach(t=>troot.appendChild(makeNode(t,0)));

/* ---- 房支筛选下拉 ---- */
const houseSel=document.getElementById("house");
Object.keys(HC).forEach(h=>{if(PAYLOAD.nodes.some(n=>n.house===h)){
  const o=document.createElement("option");o.value=h;o.textContent=h;houseSel.appendChild(o);}});
houseSel.onchange=applyFilter;

/* ---- 统计 chips ---- */
const s=PAYLOAD.stats;
document.getElementById("chips").innerHTML=
  '<span class="chip"><b>'+s.total+'</b> 祖师</span>'+
  '<span class="chip"><b>'+s.draft+'</b> 已写生平</span>'+
  '<span class="chip"><b>'+s.named_only+'</b> 待补全</span>';

/* ---- 图例 ---- */
document.getElementById("legend").innerHTML=Object.keys(HC).filter(h=>PAYLOAD.nodes.some(n=>n.house===h))
  .map(h=>'<span>'+colorDot(h)+h+'</span>').join("");

/* ---- 详情渲染 ---- */
const detail=document.getElementById("detail");
function selectById(id){
  const n=byId[id]; if(!n)return; selected=id;
  document.querySelectorAll(".n.sel").forEach(e=>e.classList.remove("sel"));
  // 高亮树中对应项
  document.querySelectorAll("#tree .n").forEach(e=>{if(e.textContent.indexOf(n.name)>=0 && e.querySelector(".nm")){}});
  let html='<div class="card">';
  html+='<h2>'+n.name+'</h2>';
  if(n.honorific)html+='<div class="hon">'+n.honorific+'</div>';
  const hc=HC[n.house]||"#999";
  html+='<div class="tags">';
  html+='<span class="tag h" style="background:'+hc+'">'+n.house+'</span>';
  if(n.school&&n.school!=="—")html+='<span class="tag">'+n.school+'</span>';
  if(n.dynasty&&n.dynasty!=="—")html+='<span class="tag">'+n.dynasty+'</span>';
  html+='</div>';
  html+='<dl class="kv">';
  html+= (n.teacher&&n.teacher!=="—")?'<dt>师承</dt><dd>'+n.teacher+'</dd>':'';
  html+= (n.region&&n.region!=="—")?'<dt>驻锡/地域</dt><dd>'+n.region+'</dd>':'';
  html+='</dl>';
  html+='<div class="bio">'+escapeHtml(n.bio||"（暂无生平记载）")+'</div>';
  if(n.sayings&&n.sayings.length){
    html+='<h3 style="font-size:15px;margin:6px 0 8px">语录 / 机缘</h3>';
    n.sayings.forEach(s=>{html+='<div class="saying">'+escapeHtml(s.text)+
      (s.ref?'<span class="ref">《'+escapeHtml(s.ref)+'》</span>':'')+'</div>';});
  }
  if(n.source_ref||n.cbeta){
    html+='<h3 style="font-size:15px;margin:14px 0 6px">文献锚点</h3><p class="muted" style="line-height:1.8">';
    html+= escapeHtml(n.source_ref||"");
    if(n.cbeta)html+= (n.source_ref?"；":"")+'CBETA：'+escapeHtml(n.cbeta);
    html+='</p>';
  }
  const evCls=n.evidence==="primary"?"p":(n.evidence==="secondary"?"a":"s");
  const vsCls=n.verify_status==="anchor_only"?"a":(n.verify_status==="stub"?"s":"p");
  const vsLabel=n.verify_status==="line_verified"?"已逐字校核":n.verify_status==="sourced"?"已据正典核校":"已锚定待校";
  const evLabel=n.evidence==="primary"?"引自正典":(n.evidence==="secondary"?"汇编级":"—");
  html+='<div style="margin-top:14px">';
  html+='<span class="ev '+evCls+'">证据：'+evLabel+'</span>';
  html+='<span class="ev '+vsCls+'">核验：'+vsLabel+'</span>';
  html+='</div>';
  if(n.verify)html+='<p class="muted" style="margin-top:8px;font-size:12px">'+escapeHtml(n.verify)+'</p>';
  html+='<p style="margin-top:16px"><a href="../祖师/'+n.slug+'.md">在 Obsidian 中打开此祖师笔记 →</a></p>';
  html+='</div>';
  detail.innerHTML=html;
  detail.scrollTop=0;
}
function escapeHtml(t){return (t||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

/* ---- 搜索 / 筛选 ---- */
const q=document.getElementById("q");
function applyFilter(){
  const k=q.value.trim().toLowerCase();
  const h=houseSel.value;
  // 树过滤：隐藏不匹配且无匹配后代的节点
  const tlis=document.querySelectorAll("#tree li");
  // 先收集匹配 id
  const matchNodes=nodes.filter(n=>(!k||(n.name+n.house+n.teacher+n.school).toLowerCase().includes(k))&&(!h||n.house===h));
  const matchIds=new Set(matchNodes.map(n=>n.id));
  // 祖先链展开
  const needShow=new Set(matchIds);
  matchNodes.forEach(n=>{let p=n.parent;while(p){needShow.add(p);p=byId[p]?byId[p].parent:null;}});
  tlis.forEach(li=>{
    const t=li._t; if(!t)return;
    const ok=needShow.has(t.id);
    li.style.display=ok?"":"none";
    if(li._ul){ // 若有匹配后代则展开
      const hasMatchChild=matchNodes.some(n=>isDescendant(n,t));
      if(hasMatchChild){li._ul.style.display="block";if(li._tgl)li._tgl.textContent="▾";}
    }
  });
  // 结果列表（在详情区顶部简要呈现）
  if(k||h){
    let html='<div class="card"><h2 style="font-size:16px">检索结果（'+matchNodes.length+'）</h2><div class="tags">';
    matchNodes.slice(0,200).forEach(n=>{html+='<span class="tag" style="cursor:pointer" data-id="'+n.id+'">'+colorDot(n.house)+n.name+'</span>';});
    html+='</div></div>';
    detail.innerHTML=html;
    detail.querySelectorAll("[data-id]").forEach(el=>el.onclick=()=>selectById(el.getAttribute("data-id")));
  } else if(!selected){
    detail.innerHTML='<div class="empty">← 从左侧谱系树点选一位祖师，或从上方搜索。</div>';
  }
}
function isDescendant(n,anc){let p=n.parent;while(p){if(p===anc.id)return true;p=byId[p]?byId[p].parent:null;}return false;}
q.addEventListener("input",applyFilter);

// 默认展开根下两层后，选中一位重要祖师作为示例
selectById("临济玄禅师");
</script></body></html>"""


def main():
    import argparse
    import hashlib
    ap = argparse.ArgumentParser(description="宗脉谱系离线库生成器")
    ap.add_argument("--prune", action="store_true",
                    help="删除 祖师/ 下不属于当前节点集合的历史 .md 残留（默认不删，仅报告）")
    args = ap.parse_args()

    with open(LINEAGE, encoding="utf-8") as f:
        lineage = json.load(f)
    cards = load_cards()
    payload = build_payload(lineage, cards)

    # 1) 祖师/<slug>.md
    zushif_dir = os.path.join(OUT, "祖师")
    os.makedirs(zushif_dir, exist_ok=True)
    written = 0
    for p in payload["nodes"]:
        path = os.path.join(zushif_dir, p["slug"] + ".md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(render_md(p))
        written += 1
    print("祖师 .md 写入：%d 份" % written)

    # 1b) 历史残留体检（只报告；--prune 才删）
    expect = {p["slug"] + ".md" for p in payload["nodes"]}
    ondisk = {n for n in os.listdir(zushif_dir) if n.endswith(".md")}
    stale = sorted(ondisk - expect)
    if stale:
        print("祖师 目录多余 %d 个历史残留文件：" % len(stale))
        for s in stale[:20]:
            print("   -", s)
        if len(stale) > 20:
            print("   ... 另 %d 个" % (len(stale) - 20))
        if args.prune:
            for s in stale:
                os.remove(os.path.join(zushif_dir, s))
            print("已按 --prune 删除上述 %d 个残留文件" % len(stale))
        else:
            print("（未删除；如需清理请执行 python3 _generate.py --prune）")

    # 2) 站点/index.html
    site_dir = os.path.join(OUT, "站点")
    os.makedirs(site_dir, exist_ok=True)
    json_str = json.dumps(payload, ensure_ascii=False)
    json_str = json_str.replace("</", "<\\/")  # 防止 </script> 截断
    html = (HTML_TEMPLATE
            .replace("__PAYLOAD__", json_str)
            .replace("__GENDATE__", GEN_DATE))
    with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("站点/index.html 写入：%d 字符 / %d 字节" % (len(html), len(html.encode("utf-8"))))

    # 3) 谱系总览.md
    write_overview(payload)

    # 4) README.md
    write_readme()

    # 5) 完整性清单（供 _校验.py 自证）
    write_manifest(payload, expect, zushif_dir, site_dir)

    print("完成。draft=%d named_only=%d total=%d" %
          (payload["stats"]["draft"], payload["stats"]["named_only"], payload["stats"]["total"]))


def write_manifest(payload, expect, zushif_dir, site_dir):
    """写出 站点/MANIFEST.json：文件哈希 + 数量 + 祖师目录聚合指纹。

    校验逻辑见同目录 _校验.py：任何缺失/篡改/多余都能被断言出来。
    """
    import hashlib
    import glob

    def sha(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    files = {}
    for name in ("index.html",):
        fp = os.path.join(site_dir, name)
        if os.path.exists(fp):
            files["站点/" + name] = {"sha256": sha(fp), "bytes": os.path.getsize(fp)}
    for name in ("谱系总览.md", "README.md", "_generate.py"):
        fp = os.path.join(OUT, name)
        if os.path.exists(fp):
            files[name] = {"sha256": sha(fp), "bytes": os.path.getsize(fp)}

    # 祖师目录：逐文件哈希后聚合成单一指纹（避免清单过大）
    agg = hashlib.sha256()
    total_bytes = 0
    n = 0
    for name in sorted(expect):
        fp = os.path.join(zushif_dir, name)
        if not os.path.exists(fp):
            continue
        h = sha(fp)
        agg.update(("%s\0%s\n" % (name, h)).encode("utf-8"))
        total_bytes += os.path.getsize(fp)
        n += 1

    manifest = {
        "schema": "chan-lineage-offline-library/1",
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "gen_date": GEN_DATE,
        "source": {
            "lineage_json": LINEAGE,
            "patriarchs": PATRIARCHS,
            "repo": "https://github.com/lymeyes/chan-lineage",
        },
        "counts": {
            "nodes": payload["stats"]["total"],
            "draft": payload["stats"]["draft"],
            "named_only": payload["stats"]["named_only"],
            "zushi_md": n,
        },
        "zushi_aggregate": {"files": n, "bytes": total_bytes, "sha256": agg.hexdigest()},
        "zushi_file_names": sorted(expect),
        "files": files,
    }
    with open(os.path.join(site_dir, "MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print("完整性清单写入：站点/MANIFEST.json（祖师 %d 份，聚合指纹 %s…）" % (n, agg.hexdigest()[:16]))


def write_overview(payload):
    s = payload["stats"]
    L = []
    L.append("# 宗脉谱系 · 总览")
    L.append("")
    L.append("> 禅宗法脉传承的离线知识库：七佛 → 西天二十八祖 → 东土六祖 → 五家七宗。")
    L.append("")
    L.append("## 这是什么")
    L.append("")
    L.append("本库以「驾鹤集」同样的方式组织——**每人一份生平笔记 + 一个自包含 HTML 索引**——")
    L.append("把禅宗法脉从七佛到五家七宗的传承做成可在 Obsidian 中浏览、也可离线双击打开的静态谱系。")
    L.append("")
    L.append("## 目录结构")
    L.append("")
    L.append("```")
    L.append("宗脉谱系/")
    L.append("├── 源文档/         随笔里的原始手辑（禅宗谱系、分支图、脑图）")
    L.append("├── 祖师/           <slug>.md  —— 每人一份生平（%d 份）" % s["total"])
    L.append("├── 站点/           index.html —— 自包含离线谱系索引（树+搜索+详情）")
    L.append("├── _generate.py    生成器（读 chan-lineage 数据，重建上述全部）")
    L.append("├── 谱系总览.md     本文件")
    L.append("└── README.md       使用与再生成说明")
    L.append("```")
    L.append("")
    L.append("## 数据规模（生成于 %s）" % s["genDate"])
    L.append("")
    L.append("| 指标 | 数值 |")
    L.append("| --- | --- |")
    L.append("| 祖师总数 | %d |" % s["total"])
    L.append("| 已写生平（draft） | %d |" % s["draft"])
    L.append("| 诚实列名占位（named_only） | %d |" % s["named_only"])
    L.append("")
    L.append("### 房支分布")
    L.append("")
    for h, c in sorted(s["houseDist"].items(), key=lambda x: -x[1]):
        L.append("- **%s**：%d 人" % (h, c))
    L.append("")
    L.append("## 严谨性与证据等级")
    L.append("")
    L.append("- **draft（已写生平）**：内容源自一手灯录（《景德传灯录》《五灯会元》《祖堂集》《联灯会要》《五灯全书》），")
    L.append("  并锚定到可独立核验的 CBETA 大正藏典籍编号（如临济录 `T47n1985`、景德传灯录 `T51n2076`）。")
    L.append("  统一标注 `evidence: primary` / `verify_status: anchor_only`（已锚定到典籍 work 级，逐字校核待补）。")
    L.append("- **named_only（诚实占位）**：仅列其名、房支、师承，不杜撰生平或语录，待据 CBETA 逐条补全。")
    L.append("- **诚实边界**：本环境无法抓 CBETA 全文逐字核对，故不夸大引文精确度；凡卷次除高度确信者外一律标「待核」。")
    L.append("")
    L.append("## 怎么看")
    L.append("")
    L.append("1. **Obsidian 内浏览**：直接打开 `祖师/` 下任意 `.md`，或在关系图中纵览传承。")
    L.append("2. **离线网页**：双击 `站点/index.html`（无需联网/服务器），左侧谱系树点选、搜索、按房支筛选。")
    L.append("3. **原始手辑**：`源文档/` 保留你随笔里的手辑原稿与分支图，作溯源对照。")
    L.append("")
    L.append("## 再生成")
    L.append("")
    L.append("```bash")
    L.append("python3 _generate.py")
    L.append("```")
    L.append("")
    L.append("> 数据源为 `chan-lineage`（GitHub: lymeyes/chan-lineage）。祖师生平的逐步补全、CBETA 逐字校核")
    L.append("> 在该仓库推进后，重跑本脚本即可同步到本库。")
    with open(os.path.join(OUT, "谱系总览.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def write_readme():
    L = []
    L.append("# 宗脉谱系 · 使用说明")
    L.append("")
    L.append("离线静态谱系库，结构仿「驾鹤集」：`祖师/` 每人一份 `.md` 生平 + `站点/index.html` 自包含索引。")
    L.append("")
    L.append("## 再生成")
    L.append("```bash")
    L.append("python3 _generate.py")
    L.append("```")
    L.append("脚本只读 `chan-lineage` 的项目数据（")
    L.append("`/Users/liuyimin/WorkBuddy/task/Project/chan-lineage/data`），")
    L.append("在本目录重建 `祖师/*.md` 与 `站点/index.html`，不改动任何源文件。")
    L.append("")
    L.append("## 字段说明（祖师/<slug>.md）")
    L.append("- `school` 房支/宗派 · `teacher` 师承 · `dynasty` 朝代 · `region` 驻锡地")
    L.append("- `source_ref` / `cbeta` 文献锚点（CBETA 大正藏编号）")
    L.append("- `evidence` 证据等级（primary=一手灯录）· `verify_status` 核验状态（anchor_only=已锚定待逐字校核）")
    L.append("")
    L.append("## 注意事项")
    L.append("- `祖师/` 下近 2000 份 `.md` 由脚本生成，请勿手工逐一编辑；如需修订生平，应在 `chan-lineage` 仓库的")
    L.append("  `data/patriarchs/*.yaml` 中修改后重跑本脚本。")
    L.append("- `源文档/` 为随笔原稿复制件，保留不作改动。")
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
