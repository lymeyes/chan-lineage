#!/usr/bin/env python3
"""
extract_lineage.py
从「佛教-禅宗谱系-分支图.html」内嵌的 RAW 树中抽取结构化谱系数据，
输出 data/lineage.json（tree 嵌套结构 + nodes 扁平表 + meta）。
零杜撰：本脚本只搬运已有结构（id/name/house/children），并向下传播 house。
"""
import re, json, datetime, os

SRC = "/Users/liuyimin/Obsidian/Noteshelf/我的笔记/我的随笔/佛教-禅宗谱系-分支图.html"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "lineage.json")

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

    # house 分布
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
