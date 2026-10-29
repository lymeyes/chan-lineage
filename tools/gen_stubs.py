#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 lineage.json 中尚未有祖师卡的节点生成 structural stub 卡（status: named_only）。

原则（学术诚信底线）：
- 只写入「可从谱系树直接推导」的结构化事实：姓名、宗派(house)、师承(parent)。
- 绝不杜撰生平事迹、世寿、住持地或语录公案。
- bio 字段明确说明「灯录仅列名，待据 CBETA 补全」，属占位说明而非虚构内容。
- 已存在（59 份 draft）的卡片不会被覆盖。

用法：python3 tools/gen_stubs.py
"""
import json, os, glob, yaml

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATRIARCHS = os.path.join(BASE, "data", "patriarchs")
LINEAGE = os.path.join(BASE, "data", "lineage.json")
ROOT = "禅宗法脉"

d = json.load(open(LINEAGE, encoding="utf-8"))
nodes = d["nodes"]
byid = {n["id"]: n for n in nodes}

# 已存在的卡片（按 id）
existing = set()
for c in glob.glob(os.path.join(PATRIARCHS, "*.yaml")):
    try:
        y = yaml.safe_load(open(c, encoding="utf-8"))
        if y and y.get("id"):
            existing.add(y["id"])
    except Exception:
        pass

count = 0
skipped = 0
for n in nodes:
    nid = n["id"]
    if nid == ROOT:
        skipped += 1
        continue
    if nid in existing:
        skipped += 1
        continue
    name = n.get("name") or nid
    house = n.get("house") or "源头"
    school = "—" if house == "源头" else house
    p = n.get("parent")
    if p is None or p == ROOT:
        teacher = "—"
    else:
        teacher = byid.get(p, {}).get("name") or "—"
    # 师承若为脊柱汇总节点，保持原名（如「……西天二十八祖……」）
    card = {
        "id": nid,
        "name": name,
        "school": school,
        "teacher": teacher,
        "status": "named_only",
        "bio": (
            f"《灯录》仅列其名，列为「{teacher}」之法嗣，未载生平事迹与语录原文。"
            "此卡为结构占位，待据 CBETA 数字化藏经"
            "（《五灯会元》《景德传灯录》《祖堂集》《联灯会要》《五灯全书》）逐条补全。"
        ),
        "sayings": [],
        "verify": "structural stub derived from lineage tree; no lamp-record content yet.",
    }
    out = os.path.join(PATRIARCHS, f"{nid}.yaml")
    with open(out, "w", encoding="utf-8") as f:
        yaml.safe_dump(card, f, allow_unicode=True, sort_keys=False)
    count += 1

print(f"generated named_only stubs = {count}")
print(f"skipped (root or already has card) = {skipped}")
print(f"total cards now = {count + len(existing)}")
