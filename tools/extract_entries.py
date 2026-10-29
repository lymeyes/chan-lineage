#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""灯录条目提取器：把 sources/*.txt 切成「一人一条」的结构化条目。

灯录体例：条目标题以「XX禪師」重复两次标出，随后接生平与机缘语，直到下一个标题。
各藏微异：
  - 五灯会元 / 景德传灯录 / 建中靖国续灯录 / 嘉泰普灯录：`延州伏龍山奉璘禪師延州伏龍山奉璘禪師`
  - 续传灯录：`汾陽善昭禪師汾陽太子院善昭禪師`（前略后详，法名相同、寺名不全等）
故标题判定不要求两段完全相等，而要求「去『禪師』后共享 >=2 字后缀」（即法名相同）。

输出 reports/entries_index.json：
  [{title, name_hant, work, cbeta, juan, body, n_sayings, ...}]
正文保留 CBETA 行锚点（cbeta 字段即条目首个锚点，可回查原文）。

用法：
    python3 tools/extract_entries.py [--stats]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

CJK = r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0003ffff]"

# 行锚点：X80n1565_p0505a04\t13\t  或  T51n2076_p0377a20\t12\t
ANCHOR = re.compile(r"([TX]?\d*n\d+_p\d+[a-z]?\d+)\t\d+\t")
JUAN = re.compile(r"([TX]?\d*n\d+_p\d+[a-z]?\d+)\s+.*?卷|第([一二三四五六七八九十百]+)卷")

# 候选标题段：CJK 2~16 字 + 称谓
UNIT = re.compile(r"(" + CJK + r"{2,16}?(?:禪師|和尚|大師|首座|菴主|居士))")
SENT = "\x01"  # 锚点占位边界


def shared_suffix(a: str, b: str) -> int:
    """两串共享后缀长度。"""
    n = 0
    while n < min(len(a), len(b)) and a[-1 - n] == b[-1 - n]:
        n += 1
    return n


def find_titles(txt: str):
    """在无换行文本中找出所有条目标题位置（相邻两个标题段，法名共享后缀>=2）。"""
    units = [(m.start(), m.end(), m.group(1)) for m in UNIT.finditer(txt)]
    hits = []
    i = 0
    while i < len(units) - 1:
        s1, e1, t1 = units[i]
        s2, e2, t2 = units[i + 1]
        gap = s2 - e1
        # 两标题段之间只允许极短间隔（续传灯录可能带少量字）
        if 0 <= gap <= 10:
            base1, base2 = t1[:-2], t2[:-2]
            if shared_suffix(base1, base2) >= 2:
                # 取较详者作标题（通常是第二段）
                title = t2 if len(t2) >= len(t1) else t1
                hits.append((s1, e2, title, t1, t2))
                i += 2
                continue
        i += 1
    return hits


def clean_body(body: str) -> tuple[str, str, list[str]]:
    """清洗正文：抽出锚点序列，去占位符，返回 (clean_text, first_anchor, all_anchors)。"""
    anchors = re.findall(SENT + r"([^" + SENT + r"]+)" + SENT, body)
    txt = re.sub(SENT + r"[^" + SENT + r"]+" + SENT, "", body)
    txt = txt.replace(SENT, "")
    first = anchors[0] if anchors else ""
    return txt, first, anchors


# 一条「机缘语」= 一个完整问答回合。切分点只在「发问/上堂」处：
#   「僧問。…師曰。…曰。…師曰。…」属同一回合（「曰。」是回合内追问，不可切）
# 若把「師曰。」也当切点，会把一句话劈成两半（曾犯此错）。
QA_START = re.compile(r"(?:僧問|僧云|問[。：]|上堂|示眾|師乃拈|師擧|師舉)")
BIO_END = re.compile(r"(?:僧問|僧云|問[。：]|上堂|示眾)")


# 章节性标记（非人物条目）：如「四祖下七世四祖下七世旁出」「XX法嗣XX法嗣」
SECTION = re.compile(r"([\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0003ffff]{2,14})\1(?:旁出|法嗣)")
CHAPTER = re.compile(r"(?:卷第[一二三四五六七八九十百]+|旁出法嗣第[一二三四五六七八九十]+世|大鑒下第[一二三四五六七八九十]+世)")


def scrub(text: str) -> str:
    """去掉正文中混入的章节标题、重复标题残片。"""
    text = SECTION.sub("", text)
    text = CHAPTER.sub("", text)
    # 重复标题残片（同名两段相邻）
    text = re.sub(r"(.{2,18}?)(?:禪師|和尚|大師)\1", r"\1", text)
    return text


def split_content(text: str):
    """把条目正文拆成 (bio, [saying...])。

    - bio：正文开头到第一个问答标志之前（多为籍贯/姓氏/出家/得法经过）
    - 若全文无问答标志，则整段视为 bio（纯叙述型条目），不产出 saying
    """
    text = scrub(text)
    m = BIO_END.search(text)
    if m is None:
        return text.strip("　 。，"), []
    bio = text[: m.start()] if m.start() > 0 else ""
    rest = text[m.start() :]
    parts, last = [], 0
    for mm in QA_START.finditer(rest):
        cut = mm.start()
        # 「師」+「問」被切开时，把「師」留给下一回合（否则前句尾多一个孤字）
        if cut - last > 0 and rest[cut - 1] == "師":
            cut -= 1
        if cut - last >= 6:
            parts.append(rest[last:cut])
            last = cut
    parts.append(rest[last:])
    says = [p.strip("　 。") for p in parts if len(p.strip()) >= 8]
    bio = bio.lstrip("者")  # 「XX禪師者，延陵人也」→ 剥掉前导「者」
    bio = bio.strip("　 。，")
    return bio, says


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true", help="只打印统计")
    ap.add_argument("--out", default="reports/entries_index.json")
    args = ap.parse_args()

    src = "sources"
    if not os.path.isdir(src):
        sys.exit("缺少 sources/，先跑 tools/extract_cbeta.py")

    all_entries = []
    per_work = {}
    for fp in sorted(glob.glob(os.path.join(src, "*.txt"))):
        work = os.path.basename(fp)[:-4]
        raw = open(fp, encoding="utf-8").read()
        txt = ANCHOR.sub(lambda m: SENT + m.group(1) + SENT, raw)
        txt = txt.replace("\n", "").replace("\t", "")
        titles = find_titles(txt)
        if not titles:
            per_work[work] = 0
            continue
        for k, (s, e, title, t1, t2) in enumerate(titles):
            nxt = titles[k + 1][0] if k + 1 < len(titles) else len(txt)
            body, first, anchors = clean_body(txt[e:nxt])
            if len(body) < 10:
                continue
            # 标题本身是章节名（含「法嗣/旁出/卷第/第N世」）则不是人物条目
            if re.search(r"(?:旁出|法嗣|卷第|第[一二三四五六七八九十]+世)", title):
                continue
            bio, says = split_content(body)
            all_entries.append(
                {
                    "title": title,
                    "name_hant": title[:-2],
                    "aliases": sorted({t1[:-2], t2[:-2]}),
                    "work": work,
                    "cbeta": first,
                    "n_anchors": len(anchors),
                    "body": body,
                    "body_len": len(body),
                    "bio": bio,
                    "sayings": says,
                }
            )
        per_work[work] = len(titles)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=1)

    print("=== 各藏条目数 ===")
    for k, v in per_work.items():
        print(f"  {k:12s} {v:5d}")
    print(f"\n合计条目: {len(all_entries)}  ->  {args.out}")
    if all_entries:
        lens = sorted(e["body_len"] for e in all_entries)
        say = sorted(len(e["sayings"]) for e in all_entries)
        print(
            "正文长度 中位 %d / 均值 %d / 最大 %d"
            % (lens[len(lens) // 2], sum(lens) // len(lens), lens[-1])
        )
        print(
            "语句条数 中位 %d / 均值 %.1f / 最大 %d"
            % (say[len(say) // 2], sum(say) / len(say), say[-1])
        )
        withbio = sum(1 for e in all_entries if len(e["bio"]) >= 6)
        print(f"含生平(bio>=6字)的条目: {withbio}")


if __name__ == "__main__":
    main()
