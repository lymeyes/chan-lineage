#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量补卡：把 lamp 语料里已抽出的条目，回填到 named_only 空壳卡。

背景：此前只有 110 张卡有内容，其余 1866 张（named_only）只有名字。
实测其中约七成在《五灯会元》《景德传灯录》等 7 部灯录里有完整条目
（正文中位 155 字、机缘语中位 2 条），属「未抽取」而非「无记载」。

分级诚实原则（不可混档）：
  - 本工具产出的一律标 verify_status: extracted（机器抽取，未逐字人工校订）
  - 不得冒充 sourced / line_verified（那两档须人工对校）
  - evidence: primary（文本确出自正典，只是切分未经人核）

用法：
    python3 tools/enrich_cards.py --dry-run     # 只统计，不写盘
    python3 tools/enrich_cards.py               # 写盘
    python3 tools/enrich_cards.py --limit 20    # 只做前 20 张（抽检用）
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys

import yaml
import zhconv

ENTRIES = "reports/entries_index.json"
PAT_DIR = "data/patriarchs"
LINEAGE = "data/lineage.json"

# 语料优先级：会元集大成最全，景录最早最可靠
PRI = {
    "X80n1565": 0,  # 五灯会元
    "T51n2076": 1,  # 景德传灯录
    "X78n1556": 2,  # 建中靖国续灯录
    "X79n1559": 3,  # 嘉泰普灯录
    "T51n2077": 4,  # 续传灯录
    "X68n1315": 5,  # 古尊宿语录
    "T47n1985": 6,  # 临济录
}
WORK_CN = {
    "X80n1565": "五灯会元",
    "T51n2076": "景德传灯录",
    "X78n1556": "建中靖国续灯录",
    "X79n1559": "嘉泰普灯录",
    "T51n2077": "续传灯录",
    "X68n1315": "古尊宿语录",
    "T47n1985": "镇州临济慧照禅师语录",
}
MAX_BODY = 3000   # 超过视为切分失败，不用
MIN_BODY = 30     # 太短不值得建卡
MAX_BIO = 800     # 超长生平截断并标注

# 旧卡里的模板化占位断言。实测其中约七成有完整条目，该断言为误，须清除。
PLACEHOLDER = re.compile(r"仅列其名|结构占位|未载生平|未载事迹|待据\s*CBETA|待补全|未见独立条目|仅存谱系名位")
BIO_MARK = re.compile(r"[也氏子人年寺師從參謁禮住嗣悟寂塔壽臘]")


def simp(s: str) -> str:
    return zhconv.convert(s, "zh-hans")


def bio_ok(b: str) -> bool:
    """判定抽出的 bio 是否可用（排除切分残留的碎句，如「雪峰领众到」）。"""
    if not b or len(b) < 12:
        return False
    return bool(BIO_MARK.search(b)) or len(b) >= 30


def strip_suffix(n: str) -> str:
    for suf in ("禪師", "禅师", "和尚", "大師", "大师", "首座", "菴主", "庵主", "居士"):
        if n.endswith(suf):
            return n[: -len(suf)]
    return n


def build_index(entries):
    idx = collections.defaultdict(list)
    for e in entries:
        for k in {e["name_hant"], *e.get("aliases", [])}:
            idx[k].append(e)
    return idx


def pick_entry(name: str, idx):
    """为一个节点名挑最合适的条目。返回 (entry, how) 或 (None, '')。"""
    n = strip_suffix(zhconv.convert(name, "zh-hant").strip())
    if not n:
        return None, ""
    # 1) 精确
    if n in idx:
        cands = idx[n]
        how = "exact"
    else:
        # 2) 节点名是条目名后缀（节点省略了寺名），要求 >=3 字防撞
        if len(n) < 3:
            return None, ""
        cands = [e for k, v in idx.items() if k.endswith(n) for e in v]
        how = "suffix"
    if not cands:
        # 3) 地名 + 法名：节点名末二字与条目名末二字相同，且节点的地名部分出现在条目名中
        #    例：萬年法一 → 台州萬年雪巢法一；天童正覺 → 明州天童宏智正覺
        if len(n) < 4:
            return None, ""
        tail, place = n[-2:], n[:-2]
        cands = [e for k, v in idx.items() if k.endswith(tail) and place in k for e in v]
        how = "place"
    if not cands:
        return None, ""
    cands.sort(key=lambda e: (len(e["name_hant"]) - len(n), PRI.get(e["work"], 9), -e["body_len"]))
    # 同work多条时取正文最长的（通常是本传而非旁及）
    best_work = cands[0]["work"]
    same = [c for c in cands if c["work"] == best_work]
    same.sort(key=lambda e: -e["body_len"])
    return same[0], how


def template(d: dict, e: dict) -> dict:
    """在原卡基础上填入抽取内容。"""
    work = WORK_CN.get(e["work"], e["work"])
    sayings = []
    for s in e["sayings"]:
        sayings.append({"text": simp(s), "ref": "%s（%s）" % (e["cbeta"], work)})
    out = dict(d)
    out["source_ref"] = "%s·%s" % (work, simp(e["title"]))
    out["cbeta"] = e["cbeta"]

    oldbio = str(d.get("bio") or "")
    raw_bio = simp(e.get("bio") or "")
    if bio_ok(raw_bio):
        if len(raw_bio) > MAX_BIO:
            raw_bio = raw_bio[:MAX_BIO] + "……（原文更长，见 cbeta 锚点）"
        out["bio"] = raw_bio
    elif PLACEHOLDER.search(oldbio):
        # 原卡的「未载生平与语录」断言已被本条抽取证伪，必须清除
        out["bio"] = "生平部分原文未载，仅存机缘语（见下）；据《%s》%s。" % (work, e["cbeta"])
    # 原 bio 非占位（人工写过）时保留不动

    out["sayings"] = sayings
    out["status"] = "draft"
    out["evidence"] = "primary"
    out["verify_status"] = "extracted"
    out["verify"] = (
        "机器抽取自 CBETA《%s》原文条目（起于 %s），已做简繁转换与章节标题清洗；"
        "尚未逐字人工校订（切分边界、异体字、法系归属仍待核）。"
        "原卡「未载生平事迹与语录原文」之断言，经本次语料核对为误，已订正。" % (work, e["cbeta"])
    )
    return out


def dump_yaml(path: str, obj: dict):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, allow_unicode=True, sort_keys=False, width=1000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="只处理名字含该串的节点")
    args = ap.parse_args()

    if not os.path.exists(ENTRIES):
        sys.exit("缺少 %s，先跑 tools/extract_entries.py" % ENTRIES)
    entries = [e for e in json.load(open(ENTRIES, encoding="utf-8"))
               if MIN_BODY <= e["body_len"] <= MAX_BODY]
    idx = build_index(entries)
    print("可用条目:", len(entries))

    cards = {}
    for fp in glob.glob(os.path.join(PAT_DIR, "*.yaml")):
        try:
            d = yaml.safe_load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        if d:
            cards[os.path.basename(fp)[:-5]] = (fp, d)

    targets = [(k, v) for k, v in cards.items()
               if v[1].get("status") == "named_only"
               and (not args.only or args.only in (v[1].get("name") or ""))]
    print("待补 named_only 卡:", len(targets))

    stat = collections.Counter()
    plan = []
    for cid, (fp, d) in targets:
        e, how = pick_entry(d.get("name") or "", idx)
        if not e:
            stat["miss"] += 1
            continue
        if len(e["sayings"]) == 0 and not bio_ok(simp(e.get("bio") or "")):
            stat["too_thin"] += 1
            continue
        stat[how] += 1
        plan.append((cid, fp, d, e))

    if args.limit:
        plan = plan[: args.limit]

    print("\n=== 匹配情况（全量）===")
    for k, v in stat.items():
        print(f"  {k:10s} {v}")
    print(f"\n本次将升级: {len(plan)} 张")

    if args.dry_run:
        print("\n=== 预览前 5 张 ===")
        for cid, fp, d, e in plan[:5]:
            t = template(d, e)
            print(f"\n--- {cid}  [{e['work']} {e['cbeta']}]")
            print("  bio:", (t.get("bio") or "")[:110])
            for s in t["sayings"][:2]:
                print("  语:", s["text"][:100])
        return

    for cid, fp, d, e in plan:
        dump_yaml(fp, template(d, e))
    print("已写入 %d 张卡" % len(plan))


if __name__ == "__main__":
    main()
