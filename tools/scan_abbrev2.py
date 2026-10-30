#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精确扫描：named_only 卡中，节点名是「地名+单字法名」縮稱，
而条目索引里存在同地名、同末字、法名更完整的独立条目。

输出 reports/abbrev_candidates2.tsv，供人工逐人核定。
"""
import os, re, sys, json, glob, collections
import yaml, zhconv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = os.path.join(ROOT, "data", "patriarchs")
ENTRIES = os.path.join(ROOT, "reports", "entries_index.json")
OUT = os.path.join(ROOT, "reports", "abbrev_candidates2.tsv")

PRI = {"X80n1565": 0, "T51n2076": 1, "X78n1556": 2, "X79n1559": 3,
       "T51n2077": 4, "X68n1315": 5, "T47n1985": 6}
SUF = ("禪師", "禅师", "和尚", "大師", "大师", "首座", "菴主", "庵主", "居士")

def strip_suffix(n):
    for s in SUF:
        if n.endswith(s):
            return n[: -len(s)]
    return n

def main():
    entries = [e for e in json.load(open(ENTRIES, encoding="utf-8"))
               if 30 <= e["body_len"] <= 3000]
    keys = collections.defaultdict(list)
    for e in entries:
        for k in {e["name_hant"], *e.get("aliases", [])}:
            keys[k].append(e)
    print("条目 %d / 键 %d" % (len(entries), len(keys)), file=sys.stderr)

    rows = []
    for p in sorted(glob.glob(os.path.join(PAT, "*.yaml"))):
        d = yaml.safe_load(open(p, encoding="utf-8"))
        if not d or d.get("status") != "named_only":
            continue
        cid = os.path.basename(p)[:-5]
        n = strip_suffix(zhconv.convert(str(d.get("name") or cid), "zh-hant").strip())
        if len(n) < 3:
            continue            # 太短，suffix 规则本就拒配
        if n in keys:
            continue            # exact 会命中，不属缩称问题
        head, last = n[:-1], n[-1]
        cands = collections.OrderedDict()
        for k, v in keys.items():
            if k == n or len(k) <= len(n):
                continue
            if k.startswith(head) and k.endswith(last):
                for e in v:
                    cands.setdefault((k, e["work"]), e)
        if not cands:
            continue
        best = sorted(cands.values(),
                      key=lambda e: (PRI.get(e["work"], 9), -e["body_len"]))[:2]
        rows.append((cid, n, len(cands),
                     " | ".join("%s(%s,%d)" % (e["name_hant"], e["work"], e["body_len"])
                                for e in best)))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("id\tname_hant\tn_cand\tcandidates(name,work,bodylen)\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    print("候选 %d 张 → %s" % (len(rows), OUT), file=sys.stderr)

if __name__ == "__main__":
    main()
