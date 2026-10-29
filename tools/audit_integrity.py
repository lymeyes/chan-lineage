#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""宗脉谱系数据完整性审计（回归守卫）。

检查项：
  1. 节点 id 唯一；root 唯一（ROOT::禅宗法脉）
  2. 每个非 root 节点的 parent 必须存在；无环（深度有限）
  3. 节点 id / name 无可疑字符：U+FFFD 替换符、代理对、私用区、控制符
  4. tree（嵌套）id 集合 == flat nodes id 集合
  5. YAML 内部 id == 文件名（去 .yaml）；文件名 ∈ 节点 id（无孤儿卡）
  6. 每个非 root 节点都有对应 YAML（无缺卡）
退出码：全部通过 0，否则 1。
"""
import json, os, re, sys, glob, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIN = os.path.join(ROOT, "data", "lineage.json")
PAT = os.path.join(ROOT, "data", "patriarchs")
ROOT_ID = "ROOT::禅宗法脉"

problems = []

def suspicious(s):
    for ch in s:
        cp = ord(ch)
        if cp == 0xFFFD or 0xD800 <= cp <= 0xDFFF or 0xE000 <= cp <= 0xF8FF or cp < 0x20:
            return "%s(%s)" % (hex(cp), unicodedata.name(ch, "?"))
    return None

def main():
    d = json.load(open(LIN, encoding="utf-8"))
    nodes = d["nodes"]
    ids = [n["id"] for n in nodes]
    idset = set(ids)

    # 1) 唯一性 + root
    if len(ids) != len(idset):
        from collections import Counter
        dup = [k for k, v in Counter(ids).items() if v > 1]
        problems.append("节点 id 重复: %s" % dup)
    # parent 为空（None/缺失）应恰好是合成根 ROOT::禅宗法脉（其余顶层分支 parent=ROOT）
    no_parent = [n["id"] for n in nodes if not n.get("parent")]
    if no_parent != [ROOT_ID]:
        problems.append("parent 为空的节点应仅为 ROOT::禅宗法脉: %s" % no_parent)
    if ROOT_ID not in idset:
        problems.append("合成根 %s 缺失" % ROOT_ID)

    # 2) parent 引用 + 环
    by_id = {n["id"]: n for n in nodes}
    for n in nodes:
        p = n.get("parent")
        if p and p != ROOT_ID and p not in idset:
            problems.append("parent 缺失: %s -> %s" % (n["id"], p))
    # 无环（沿 parent 回溯不超过节点数）
    for n in nodes:
        seen, cur = set(), n.get("parent")
        steps = 0
        while cur and cur != ROOT_ID:
            if cur in seen:
                problems.append("检测到环: %s" % n["id"]); break
            seen.add(cur); steps += 1
            if steps > len(nodes):
                problems.append("parent 链超长(疑似环): %s" % n["id"]); break
            cur = by_id.get(cur, {}).get("parent")

    # 3) 可疑字符
    for n in nodes:
        for f in ("id", "name"):
            s = n.get(f, "") or ""
            bad = suspicious(s)
            if bad:
                problems.append("可疑字符 %s.%s: %s" % (n["id"], f, bad))

    # 4) tree == flat
    tset = set()
    def collect(o):
        if isinstance(o, dict):
            if "id" in o: tset.add(o["id"])
            for v in o.values(): collect(v)
        elif isinstance(o, list):
            for x in o: collect(x)
    collect(d["tree"])
    if tset != idset:
        problems.append("tree/flat 不一致: 差集=%s" % (tset ^ idset))

    # 5)+6) YAML 一致性
    yids = set()
    for fp in glob.glob(os.path.join(PAT, "*.yaml")):
        base = os.path.basename(fp)[:-5]
        yids.add(base)
        txt = open(fp, encoding="utf-8").read()
        m = re.search(r"^id:\s*(.*)$", txt, re.M)
        inner = m.group(1).strip() if m else None
        if inner != base:
            problems.append("YAML 内部 id≠文件名: %s (内部=%s)" % (base, inner))
    orphan_yaml = sorted(yids - idset)
    if orphan_yaml:
        problems.append("孤儿卡(无对应节点): %s" % orphan_yaml)
    orphan_node = sorted(idset - yids - {ROOT_ID})
    if orphan_node:
        problems.append("缺卡节点(无 YAML): %s" % orphan_node)

    # 报告
    print("审计对象: %d 节点 / %d YAML" % (len(nodes), len(yids)))
    if problems:
        print("✗ 发现 %d 处问题:" % len(problems))
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("✓ 全部通过：id 唯一 / parent 完整无环 / 无乱码 / tree==flat / "
          "节点↔卡 100%% 对应（0 孤儿 / 0 缺卡）")
    sys.exit(0)

if __name__ == "__main__":
    main()
