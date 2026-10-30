#!/usr/bin/env python3
"""文件名/标准名对齐：以 name（标准通行名）为准。
守卫：每张卡只允许改 id: / name: 行、新增 alias: 行，其余字节不变。"""
import io,os,re,json,sys,glob
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(ROOT,'data'); CARDS=os.path.join(DATA,'patriarchs')
HON=re.compile(r'(禪師|禅师|和尚|大師|大师|首座|菴主|庵主|居士|國師|国师|上座|法嗣|沙彌|沙弥|尼)$')
MANUAL={
 '径山杲禅师':('大慧宗杲禅师','大慧宗杲',None),
 '清凉益禅师':('法眼文益禅师','法眼文益',None),
 '黄龙心禅师':('黄龙祖心禅师','黄龙祖心','晦堂祖心'),
 '黄龙新禅师':('死心悟新禅师','死心悟新',None),
 '黄龙清禅师':('灵源惟清禅师','灵源惟清',None),
 '神鼎𬤇禅师':('神鼎洪諲禅师','神鼎洪諲',None),
 '南岳高台寺宣明佛印禅师':('佛印了元禅师','佛印了元',None),
 '天童华禅师':('应庵昙华禅师','应庵昙华','天童华'),
 '昭觉勤禅师':('圆悟克勤禅师','圆悟克勤','昭觉克勤'),
 '石霜圆禅师':('石霜楚圆禅师','石霜楚圆','慈明楚圆'),
 '纸衣和尚':('纸衣道者','纸衣道者',None),
 '云居悟禅师法嗣':('云居悟法嗣','云居悟法嗣',None),
 '五祖大满禅师旁出':('五祖大满旁出','五祖大满旁出',None),
 '六祖大鉴禅师旁出':('六祖大鉴旁出','六祖大鉴旁出',None),
 '四祖大医禅师旁出':('四祖大医旁出','四祖大医旁出',None),
 '建宁府开善木庵道琼斯首座':('建宁府开善木庵道琼首座','建宁府开善木庵道琼首座',None),
}
NAME_ONLY={'文公杨亿居士':('杨亿','杨大年'),'襄州居士庞蕴':('庞蕴','庞居士'),
           '西天二十八祖':('西天二十八祖',None)}
KEEP=set(['三祖僧璨','二祖慧可','四祖道信','五祖弘忍','六祖大鉴禅师','东土初祖菩提达摩',
          '西天初祖摩诃迦叶','西天二祖阿难'])|set(NAME_ONLY)
def clean(n): return re.sub(r'（[^）]*）|\([^)]*\)','',n).strip()
def subseq(a,b):
    it=iter(b); return all(c in it for c in a)

def edit_card(text,new_id,new_name,alias):
    lines=text.splitlines(keepends=True)
    out=[];did=dn=0
    for ln in lines:
        if re.match(r'^id:',ln): out.append('id: '+new_id+'\n'); did+=1
        elif re.match(r'^name:',ln):
            out.append('name: '+new_name+'\n')
            if alias: out.append('alias: '+alias+'\n')
            dn+=1
        else: out.append(ln)
    assert did==1 and dn==1,(new_id,did,dn)
    return ''.join(out)

ap={'--dry-run':'--dry-run' in sys.argv,'--apply':'--apply' in sys.argv}
plan=[]
for p in sorted(glob.glob(os.path.join(CARDS,'*.yaml'))):
    stem=os.path.basename(p)[:-5]
    text=io.open(p,encoding='utf-8').read()
    m=re.search(r'(?m)^name:\s*(.+)$',text); nm=m.group(1).strip() if m else ''
    core=HON.sub('',stem); nm_c=clean(HON.sub('',nm))
    if nm==core: continue
    if stem in MANUAL: plan.append((stem,)+MANUAL[stem]); continue
    if stem in NAME_ONLY:
        nn,al=NAME_ONLY[stem]; plan.append((stem,stem,nn,al)); continue
    if stem in KEEP: continue
    mo=HON.search(stem); suf=mo.group(1) if mo else ''
    if nm_c==core: continue
    if '（' in nm or '(' in nm:
        plan.append((stem,nm_c+suf,nm_c,None)); continue
    if subseq(core,nm_c) and nm_c!=core:
        plan.append((stem,nm_c+suf,nm_c,None))

stems=set(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(CARDS,'*.yaml')))
new=[t[1] for t in plan]
assert len(new)==len(set(new)),'计划内撞名'
assert not [s for s in new if s in stems and s not in [t[0] for t in plan]],'与现有文件撞名'
print('计划',len(plan),'张')
if ap['--dry-run']:
    for o,n,nn,al in plan: print(' ',o,'->',n,'|',nn,'| alias:',al)
    sys.exit(0)
mapping={};namechg={}
for old,new,nn,al in plan:
    p=os.path.join(CARDS,old+'.yaml')
    text=io.open(p,encoding='utf-8').read()
    m=re.search(r'(?m)^name:\s*(.+)$',text); oldname=m.group(1).strip()
    newtext=edit_card(text,new,nn,al)
    # 守卫：去掉 id/name/alias 行后与原文逐字节相同
    strip=lambda t:'\n'.join(l for l in t.splitlines() if not re.match(r'^(id:|name:|alias:)',l))+'\n'
    assert strip(text)==strip(newtext),'正文被改动: '+old
    if old!=new:
        os.remove(p); io.open(os.path.join(CARDS,new+'.yaml'),'w',encoding='utf-8').write(newtext)
    else:
        io.open(p,'w',encoding='utf-8').write(newtext)
    mapping[old]=new; namechg[old]=(oldname,nn)
    print('✓',old,'->',new, ('| name %s -> %s'%(oldname,nn)) if oldname!=nn else '')
# lineage.json
fp=os.path.join(DATA,'lineage.json')
d=json.load(io.open(fp,encoding='utf-8'))
cnt=0
for n in d['nodes']:
    if n['id'] in mapping:
        n['id']=mapping[n['id']]; cnt+=1
    o=namechg.get(n['id'])
    if o is None and n['id'] in namechg: o=namechg[n['id']]
    if n['id'] in namechg: n['name']=namechg[n['id']][1]
    if n.get('parent') in mapping: n['parent']=mapping[n['parent']]
def walk(node):
    if node['id'] in mapping: node['id']=mapping[node['id']]
    if node['id'] in namechg: node['name']=namechg[node['id']][1]
    for ch in node.get('children') or []: walk(ch)
walk(d['tree'])
assert cnt==len(plan),(cnt,len(plan))
io.open(fp,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2))
print('lineage.json 已同步（%d 个 id 更新）'%cnt)
