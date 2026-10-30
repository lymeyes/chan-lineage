#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 named_only 卡：源文本中是否其实存在该人的独立条目（缩称导致 enrich 匹配失败）。

输出 reports/abbrev_candidates.tsv，供人工核定全名。
"""
import os, re, sys, json, glob
from zhconv import convert

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sources")
PAT = os.path.join(ROOT, "data", "patriarchs")
OUT = os.path.join(ROOT, "reports", "abbrev_candidates.tsv")

def load_sources():
    """返回 [(vol, text_nospace, [(offset, vol, line, raw)])]"""
    books = []
    for f in sorted(glob.glob(os.path.join(SRC, "*.txt"))):
        vol = os.path.basename(f)[:-4]
        lines = []
        with open(f, encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.rstrip("\n")
                if raw.startswith("#"):
                    continue
                parts = raw.split("\t")
                if len(parts) < 3:
                    continue
                sid, ln, txt = parts[0], parts[1], "\t".join(parts[2:])
                lines.append((sid, txt))
        if not lines:
            continue
        buf, idx = [], []
        for sid, txt in lines:
            t = re.sub(r"\s+", "", txt)
            if not t:
                continue
            idx.append((len("".join(buf)), sid, txt))
            buf.append(t)
        books.append((vol, "".join(buf), idx))
    return books

def locate(books, needle):
    """返回 [(vol, sid, context)]"""
    hits = []
    for vol, text, idx in books:
        start = 0
        while True:
            p = text.find(needle, start)
            if p < 0:
                break
            # 二分找所在行
            lo, hi = 0, len(idx) - 1
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if idx[mid][0] <= p:
                    lo = mid
                else:
                    hi = mid - 1
            sid = idx[lo][1]
            ctx = text[max(0, p - 12): p + len(needle) + 14]
            hits.append((vol, sid, ctx))
            start = p + 1
    return hits

def read_status(path):
    st = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("status:"):
                st = line.split(":", 1)[1].strip()
                break
    return st

def main():
    books = load_sources()
    print("载入典籍：", ", ".join(f"{v}({len(t)//10000}万字)" for v, t, _ in books), file=sys.stderr)
    rows = []
    for p in sorted(glob.glob(os.path.join(PAT, "*.yaml"))):
        if read_status(p) != "named_only":
            continue
        cid = os.path.basename(p)[:-5]
        disp = cid[:-2] if cid.endswith("禅师") else cid
        if len(disp) < 2:
            continue
        trad = convert(disp, "zh-hant")
        for suffix in ("禪師", "大師", "和尚"):
            hits = locate(books, trad + suffix)
            if hits:
                rows.append((cid, disp, trad + suffix, len(hits),
                             hits[0][0], hits[0][1], hits[0][2]))
                break
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("id\tdisp\tmatched\tn_hits\tvol\tsid\tcontext\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    print(f"命中 {len(rows)} 张 → {OUT}", file=sys.stderr)

if __name__ == "__main__":
    main()
