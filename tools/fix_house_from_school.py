#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_house_from_school.py
========================
将 data/lineage.json 的 `house`（房支/宗派着色）重新对齐到经灯录核实的
`school`（来自 data/patriarchs/*.yaml 的卡片字段），消除二者在「宗派归属」
层面上的不一致。

设计原则（科学严谨、零杜撰）：
- `house` 语义从「挂在哪条分支（树中位置）」改为「该人所属宗派」，与树中
  父子传承边解耦。树的 parent/children 结构原封不动，仅校正房支标签与着色。
- 借线延续等史实下，传承边（谁传谁）与宗派（属哪一宗）本就该不同，不应靠
  挪动传承边来强行让二者相等——那会杜撰历史师承。
- 仅当卡片给出「规范宗派名」时才覆盖 house；无 school（—）或非常规名
  （如「雪峰宗」，祖位）的节点保留树派生 house，避免引入灰色（无配色）节点。

规范宗派名（HouseColors 键）：
  源头 / 西天祖师 / 东土祖师 / 南岳系 / 青原系 /
  临济宗 / 杨岐派 / 黄龙派 / 曹洞宗 / 云门宗 / 法眼宗 / 沩仰宗
带括号的细化写法（如「杨岐派（虎丘派）」）归并到主宗派（杨岐派）。

幂等：重复运行结果一致。
"""
import os, re, json, datetime, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LINEAGE = os.path.join(ROOT, "data", "lineage.json")
PATRIARCHS = os.path.join(ROOT, "data", "patriarchs")

# 规范房支名（= offline_generate.HOUSE_COLORS 的键）
CANON = {
    "源头", "西天祖师", "东土祖师", "南岳系", "青原系",
    "临济宗", "杨岐派", "黄龙派", "曹洞宗", "云门宗", "法眼宗", "沩仰宗",
}

def canonical(school):
    """把卡片 school 归并到规范房支名；无法归并返回 None（保留树派生 house）。"""
    if not school or school == "—":
        return None
    s = school.strip()
    if s in CANON:
        return s
    # 带括号的细化写法：取主宗派
    for key in CANON:
        if s.startswith(key):
            return key
    # 其它（如「雪峰宗」祖位写法）不强行归并
    return None

def load_schools():
    schools = {}
    for fp in glob.glob(os.path.join(PATRIARCHS, "*.yaml")):
        txt = open(fp, encoding="utf-8").read()
        m = re.search(r"^id:\s*(.+)$", txt, re.M)
        s = re.search(r"^school:\s*(.+)$", txt, re.M)
        if m and s:
            schools[m.group(1).strip()] = canonical(s.group(1).strip())
    return schools

def apply_to_tree(tree, schools):
    """递归把 tree 节点的 house 对齐到 canonical(school)；返回是否改动。"""
    changed = False
    new_house = schools.get(tree["id"])
    if new_house is not None and tree.get("house") != new_house:
        tree["house"] = new_house
        changed = True
    for c in tree.get("children", []):
        if apply_to_tree(c, schools):
            changed = True
    return changed

def main():
    lin = json.load(open(LINEAGE, encoding="utf-8"))
    schools = load_schools()

    nodes = lin["nodes"]
    tree = lin["tree"]

    # 1) 扁平 nodes 对齐
    n_changed = 0
    for n in nodes:
        nh = schools.get(n["id"])
        if nh is not None and n.get("house") != nh:
            n["house"] = nh
            n_changed += 1

    # 2) 嵌套 tree 对齐
    t_changed = apply_to_tree(tree, schools)

    # 3) 重算 meta.house_distribution
    from collections import Counter
    houses = Counter(n["house"] for n in nodes)
    meta = lin.get("meta", {})
    meta["house_distribution"] = dict(houses)
    meta["generated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
    meta["house_note"] = ("house 自 2026-10-31 起对齐 school（经灯录核实的宗派），"
                          "与树中父子传承边解耦；无 school/祖位节点保留树派生 house。")
    lin["meta"] = meta

    json.dump(lin, open(LINEAGE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 4) 报告
    print("规范化覆盖 nodes：%d 处" % n_changed)
    print("规范化覆盖 tree ：%s" % ("是" if t_changed else "否"))
    print("house 分布（新）：")
    for k, v in houses.most_common():
        print("   %-8s %d" % (k, v))

    # 5) 复检：还剩多少「双方都有规范宗派却仍不同」的硬不一致
    hard = 0
    for n in nodes:
        sid = n["id"]; h = n["house"]
        sc_raw = schools.get(sid)
        if sc_raw is not None and h != sc_raw:
            hard += 1
    print("剩余硬不一致（节点 school 规范名 != house）：%d" % hard)

if __name__ == "__main__":
    main()
