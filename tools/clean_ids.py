#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""剥离节点 id 中由分支图抽取残留的 '**' 分隔符（如 L::洛京黑**涧**和尚 -> L::洛京黑涧和尚）。
注意：乱码仅在 id（影响文件名），name 字段已干净，故只清理 id 并同步 tree/parent 引用与 YAML 文件名。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIN = os.path.join(ROOT, "data", "lineage.json")
PAT = os.path.join(ROOT, "data", "patriarchs")

def walk(o, m):
    if isinstance(o, dict):
        if "id" in o and o["id"] in m:
            o["id"] = m[o["id"]]
        if "parent" in o and o["parent"] in m:
            o["parent"] = m[o["parent"]]
        for v in o.values():
            walk(v, m)
    elif isinstance(o, list):
        for x in o:
            walk(x, m)

def main():
    d = json.load(open(LIN, encoding="utf-8"))
    # 建立 old_id -> new_id 映射（仅剥离 **，name 不变）
    m = {}
    for n in d["nodes"]:
        if "**" in n["id"]:
            m[n["id"]] = n["id"].replace("**", "")
    print("需改 id 数:", len(m))
    # 更新 nodes
    for n in d["nodes"]:
        if n["id"] in m:
            n["id"] = m[n["id"]]
        if "parent" in n and n["parent"] in m:
            n["parent"] = m[n["parent"]]
    # 更新 tree
    walk(d["tree"], m)
    json.dump(d, open(LIN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 重命名 YAML 文件
    for old_id, new_id in m.items():
        of = os.path.join(PAT, old_id + ".yaml")
        nf = os.path.join(PAT, new_id + ".yaml")
        if os.path.exists(of) and of != nf:
            os.rename(of, nf)
            print("rename yaml:", old_id, "->", new_id)
    print("lineage + yaml 清理完成")

if __name__ == "__main__":
    main()
