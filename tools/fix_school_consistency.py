#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 school 与师承宗派不符。

判定规则（用户拍板，2026-10-30）：
  school 应当以「直传师（immediate teacher）的宗派」为准，沿师承链向下传播；
  但存在历史特例需强制覆盖（OVERRIDE），且创始人自立更深家系时保留自身 school。

  - OVERRIDE：曹洞宗借法眼宗线延续的历史特例——大阳警玄将法脉托付投子义青，
    故 大阳玄 及其下游（投子青→芙蓉道楷→丹霞淳→法嗣…）皆应归 曹洞宗，
    即便其直传师被错标为法眼宗。至少 大阳玄 强制 曹洞宗，下游靠传播自动归位。
  - 创始人保护：若节点自身 school 是直传师 school 的「后裔」（更深家系，如 杨岐派
    之于 临济宗），保留自身 school，不被下拉到师之宗派。
  - 未赋值（—）不动；非法宗派名（如 雪峰宗）重分类到直传师合法宗派。

✅ 与旧 reports/school_mismatch.md 结论一致：芙蓉 cluster 归 曹洞宗、洞山聪 cluster 归 云门宗。

用法：
  python3 tools/fix_school_consistency.py            # 预演
  python3 tools/fix_school_consistency.py --apply    # 落盘（仅改 school 行）
"""
import os, sys, glob, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = os.path.join(ROOT, "data", "patriarchs")

DEPTH = {'源头':0,'西天祖师':0,'东土祖师':1,'南岳系':2,'青原系':2,
         '临济宗':3,'曹洞宗':3,'云门宗':3,'法眼宗':3,'沩仰宗':3,'杨岐派':4,'黄龙派':4}
SCHOOL_PARENT = {
    '西天祖师':'源头','东土祖师':'源头',
    '南岳系':'东土祖师','青原系':'东土祖师',
    '临济宗':'南岳系','沩仰宗':'南岳系','杨岐派':'临济宗','黄龙派':'临济宗',
    '曹洞宗':'青原系','云门宗':'青原系','法眼宗':'青原系',
}
# 历史特例覆盖表：id -> 强制宗派（曹洞宗借法眼宗线延续等）
OVERRIDE = {'大阳玄禅师': '曹洞宗'}

def ancestors(x):
    s={x}; cur=x
    while cur in SCHOOL_PARENT:
        cur=SCHOOL_PARENT[cur]; s.add(cur)
    return s

def main():
    apply = "--apply" in sys.argv
    cards={}
    for fp in glob.glob(os.path.join(PAT,"*.yaml")):
        cid=os.path.basename(fp)[:-5]
        d=yaml.safe_load(open(fp,encoding="utf-8")) or {}
        cards[cid]={'school':d.get('school'),'teacher':d.get('teacher'),'fp':fp}
    school={c:cards[c]['school'] for c in cards}
    teacher={c:cards[c]['teacher'] for c in cards}

    def base_of(s):
        if not isinstance(s,str): return s
        return s.split("（")[0].split("(")[0].strip()

    def teacher_ancestors(cid):
        s=set(); cur=teacher.get(cid); seen=set()
        while cur and cur not in seen:
            seen.add(cur); s.add(cur); cur=teacher.get(cur)
        return s
    # 仅在校正范围内改动：大阳玄（曹洞宗）子树 + 洞山聪（云门宗）子树
    caodong_scope=set(); yunmen_scope=set()
    for cid in cards:
        anc=teacher_ancestors(cid)
        if "大阳玄禅师" in anc: caodong_scope.add(cid)
        if "洞山聪禅师" in anc: yunmen_scope.add(cid)
    caodong_scope.add("大阳玄禅师"); yunmen_scope.add("洞山聪禅师")
    SCOPE = caodong_scope | yunmen_scope

    def decide(cid):
        """返回该校正后的 school（与原始不同则非 None）。"""
        if cid not in SCOPE:               # 限定范围，避免沿错标师承全局误传
            return None
        sc=school[cid]
        if sc is None or sc=="—":
            return None
        b=base_of(sc)
        if cid in OVERRIDE:
            return OVERRIDE[cid]
        t=teacher.get(cid)
        cand=school.get(t) if (t and t in school) else None
        if cand is None or cand not in DEPTH:
            return None
        if b not in DEPTH:                 # 自身 school 为非法名：归到直传师合法宗派
            return cand
        if cand==sc or cand in ancestors(b):
            return None                     # 相等 / 师为自身祖先（创始人保护）：保留
        return cand

    for _ in range(500):
        new_changes={}
        for cid in cards:
            ns=decide(cid)
            if ns is not None and ns!=school[cid]:
                new_changes[cid]=ns
        if not new_changes:
            break
        for cid,ns in new_changes.items():
            school[cid]=ns
    # 收敛后：以最终 school 值对账（避免迭代顺序依赖导致按错误目标落盘）
    final={cid: school[cid] for cid in cards
           if cards[cid]['school'] is not None and cards[cid]['school'] != "—"
           and school.get(cid) is not None and school[cid] != cards[cid]['school']}

    print("拟变更 %d 张卡的 school：" % len(final))
    from collections import Counter
    grp=Counter((cards[c]['school'],final[c]) for c in final)
    for (o,n),k in sorted(grp.items(),key=lambda x:-x[1]):
        print("  %s -> %s : %d 张" % (o,n,k))
    print("\n明细：")
    for cid in sorted(final):
        print("  %s : %s -> %s" % (cid, cards[cid]['school'], final[cid]))

    if apply and final:
        for cid,ns in final.items():
            fp=cards[cid]['fp']; txt=open(fp,encoding="utf-8").read()
            old=cards[cid]['school']
            txt=txt.replace("school: %s"%(old if old is not None else ""), "school: %s"%ns, 1)
            open(fp,"w",encoding="utf-8").write(txt)
        print("\n✓ 已落盘 %d 张" % len(final))
    elif apply:
        print("无需改动。")

if __name__=="__main__":
    main()
