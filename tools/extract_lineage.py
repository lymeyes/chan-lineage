#!/usr/bin/env python3
"""
extract_lineage.py
从「佛教-禅宗谱系-分支图.html」内嵌的 RAW 树中抽取结构化谱系数据，
输出 data/lineage.json（tree 嵌套结构 + nodes 扁平表 + meta）。
零杜撰：本脚本只搬运已有结构（id/name/house/children），并向下传播 house。
"""
import re, json, datetime, os, glob

SRC = "/Users/liuyimin/Obsidian/Noteshelf/我的笔记/我的随笔/佛教-禅宗谱系-分支图.html"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "lineage.json")

# 规范房支名（= offline_generate.HOUSE_COLORS 的键）
CANON = {
    "源头", "西天祖师", "东土祖师", "南岳系", "青原系",
    "临济宗", "杨岐派", "黄龙派", "曹洞宗", "云门宗", "法眼宗", "沩仰宗",
}

def canonical(school):
    """卡片 school 归并到规范房支名；无法归并返回 None（保留树派生 house）。"""
    if not school or school == "—":
        return None
    s = school.strip()
    if s in CANON:
        return s
    for key in CANON:
        if s.startswith(key):
            return key
    return None

def load_schools():
    schools = {}
    pat = os.path.join(os.path.dirname(__file__), "..", "data", "patriarchs", "*.yaml")
    for fp in glob.glob(pat):
        txt = open(fp, encoding="utf-8").read()
        m = re.search(r"^id:\s*(.+)$", txt, re.M)
        s = re.search(r"^school:\s*(.+)$", txt, re.M)
        if m and s:
            schools[m.group(1).strip()] = canonical(s.group(1).strip())
    return schools

def reconcile_house(tree, nodes, schools):
    """把 house 对齐到 canonical(school)，与树中父子传承边解耦。返回改动计数。"""
    n_changed = 0
    for n in nodes:
        nh = schools.get(n["id"])
        if nh is not None and n.get("house") != nh:
            n["house"] = nh
            n_changed += 1
    def rec(t):
        c = 0
        nh = schools.get(t["id"])
        if nh is not None and t.get("house") != nh:
            t["house"] = nh; c += 1
        for ch in t.get("children", []):
            c += rec(ch)
        return c
    rec(tree)
    return n_changed

def main():
    html = open(SRC, encoding="utf-8").read()
    # RAW 全部在 const RAW = ... ; 这一行内，无内嵌 ";\n"
    marker = "const RAW = "
    i = html.index(marker) + len(marker)
    j = html.index(";\n", i)
    raw_str = html[i:j]
    data = json.loads(raw_str)

    # ---- 向下传播 house（祖庭/宗派着色） ----
    def fill(n, parent_house):
        house = n.get("house") or parent_house
        return {
            "id": n["id"],
            "name": n["name"],
            "house": house,
            "children": [fill(c, house) for c in n.get("children", [])],
        }
    tree = fill(data, "源头")

    # ---- 扁平表（parent + depth） ----
    nodes = []
    seen = {}
    dup = []
    def walk(n, parent_id, depth):
        if n["id"] in seen:
            dup.append(n["id"])
        seen[n["id"]] = True
        nodes.append({
            "id": n["id"], "name": n["name"], "house": n["house"],
            "parent": parent_id, "depth": depth,
            "n_children": len(n["children"]),
        })
        for c in n["children"]:
            walk(c, n["id"], depth + 1)
    walk(tree, None, 0)

    # ---- house 对齐 school（经灯录核实的宗派），与树中父子传承边解耦 ----
    schools = load_schools()
    n_changed = reconcile_house(tree, nodes, schools)
    if n_changed:
        print("house 对齐 school：%d 个节点被覆盖" % n_changed)

    # house 分布（对齐后重算）
    from collections import Counter
    houses = Counter(n["house"] for n in nodes)
    max_depth = max(n["depth"] for n in nodes)

    out = {
        "meta": {
            "title": "禅宗法脉",
            "description": "禅宗传承谱系（七佛→西天二十八祖→东土六祖→五家七宗），从交互分支图抽取的结构化数据。",
            "source_html": "佛教-禅宗谱系-分支图.html",
            "source_texts": ["景德传灯录", "五灯会元", "祖堂集", "联灯会要", "五灯全书"],
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d"),
            "total_nodes": len(nodes),
            "max_depth": max_depth,
            "house_distribution": dict(houses),
            "house_note": ("house 自 2026-10-31 起对齐 school（经灯录核实的宗派），"
                          "与树中父子传承边解耦；无 school/祖位节点保留树派生 house。"),
            "duplicate_ids": dup,
            "note": "本文件为零杜撰的结构化底座；每位祖师的生平/引文见 data/patriarchs/<id>.yaml（待补）。",
        },
        "tree": tree,
        "nodes": nodes,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"节点总数     : {len(nodes)}")
    print(f"最大深度     : {max_depth}")
    print(f"重复 id      : {dup if dup else '无'}")
    print(f"house 分布   :")
    for k, v in houses.most_common():
        print(f"   {k:<8} {v}")
    print(f"写出         : {os.path.abspath(OUT)}")

if __name__ == "__main__":
    main()
