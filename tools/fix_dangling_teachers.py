#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 4 处「师承指向树中不存在的人物」的悬空引用。

措施：
  1) 补建 3 个真实历史节点（此前树中缺失）：
       - 释迦牟尼佛       挂于 过去七佛 之下（叶子）
       - 西天二十七祖般若多罗  挂于 西天二祖阿难 之下（叶子）
       - 石门慈照禅师     挂于 汾阳善昭禅师 之下（叶子）
     三张 YAML 卡由人工创建（data/patriarchs/*.yaml），本脚本负责把它们接入 lineage 树。
  2) 改 2 张卡的 teacher 字符串，使其精确命中节点 id：
       - 驸马都尉李遵勗居士  teacher: 石门慈照      -> 石门慈照禅师
       - 白云守端禅师       teacher: 杨岐方会（杨歧会禅师） -> 杨歧会禅师
     （摩诃迦叶 / 东土初祖菩提达摩 的 teacher 已是 释迦牟尼佛 / 西天二十七祖般若多罗，节点补建后即解析）

节点以「叶子」方式挂入，不重排既有祖链，避免 depth 级联改图。
用法：
  python3 tools/fix_dangling_teachers.py            # 预演（不落盘）
  python3 tools/fix_dangling_teachers.py --apply    # 执行
幂等：已存在的节点/已改的 teacher 不会重复处理。
"""
import json, os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIN = os.path.join(ROOT, "data", "lineage.json")
PAT = os.path.join(ROOT, "data", "patriarchs")

NEW_NODES = [
    dict(id="释迦牟尼佛", name="释迦牟尼佛", house="源头", parent="过去七佛", depth=2, n_children=0),
    dict(id="西天二十七祖般若多罗", name="西天二十七祖般若多罗", house="源头", parent="西天二祖阿难", depth=4, n_children=0),
    dict(id="石门慈照禅师", name="石门慈照", house="临济宗", parent="汾阳善昭禅师", depth=2, n_children=0),
]
TEACHER_FIX = {
    "驸马都尉李遵勗居士": ("石门慈照", "石门慈照禅师"),
    "白云守端禅师": ("杨岐方会（杨歧会禅师）", "杨歧会禅师"),
}


def find_node(tree, nid, parent=None):
    if tree.get("id") == nid:
        return tree, parent
    for c in tree.get("children", []):
        r = find_node(c, nid, tree.get("id"))
        if r:
            return r
    return None


def main():
    apply = "--apply" in sys.argv
    d = json.load(open(LIN, encoding="utf-8"))
    nodes = d["nodes"]
    byid = {n["id"]: n for n in nodes}
    tree = d["tree"]

    plan = []
    # 1) 补节点
    for nd in NEW_NODES:
        if nd["id"] in byid:
            print("跳过已存在节点:", nd["id"])
            continue
        # 父节点必须存在
        if nd["parent"] not in byid:
            sys.exit("父节点缺失: %s" % nd["parent"])
        parent_node, _ = find_node(tree, nd["parent"])
        if parent_node is None:
            sys.exit("树中找不到父节点: %s" % nd["parent"])
        nodes.append(nd)
        parent_node.setdefault("children", []).append(
            {"id": nd["id"], "name": nd["name"], "house": nd["house"], "children": []})
        # 父 n_children +1
        byid[nd["parent"]]["n_children"] = byid[nd["parent"]].get("n_children", 0) + 1
        plan.append("新增节点 %s（父=%s）" % (nd["id"], nd["parent"]))

    # 2) 改 teacher 串
    for cid, (old, new) in TEACHER_FIX.items():
        fp = os.path.join(PAT, cid + ".yaml")
        if not os.path.exists(fp):
            sys.exit("卡不存在: %s" % fp)
        txt = open(fp, encoding="utf-8").read()
        if ("teacher: %s" % new) in txt:
            print("跳过已改 teacher:", cid)
            continue
        if ("teacher: %s" % old) not in txt:
            sys.exit("%s 中未找到 teacher: %s" % (cid, old))
        txt = txt.replace("teacher: %s" % old, "teacher: %s" % new, 1)
        if apply:
            open(fp, "w", encoding="utf-8").write(txt)
        plan.append("改 teacher %s: %s -> %s" % (cid, old, new))

    if not plan:
        print("无需改动（已是最新状态）。")
        return
    print("计划/已执行：")
    for p in plan:
        print("  - " + p)

    if apply:
        json.dump(d, open(LIN, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("✓ lineage.json 已写回")


if __name__ == "__main__":
    main()
