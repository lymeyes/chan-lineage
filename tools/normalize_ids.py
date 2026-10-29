#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""节点 id / 文件名规范化（去 L:: 前缀 + 去标题句末虚词「者」）
=================================================================
背景
----
早期从「分支图」抽取的节点带 `L::` 前缀（L = lineage 图），落到 Obsidian 后
被渲染成 `L__韶州法海禅师者.md` 这种文件名。前缀对读者毫无意义，句末「者」
更是把灯录原句的虚词带进了人名（原句作「韶州法海禪師者，曲江人也」，
「者」是句读，不是称谓一部）。

做法（关键：不重排 YAML）
------------------------
**只替换 `id:` 行 + 改文件名**，卡片其余字节原样搬运，因此正文不可能丢。
迁移前后用「抹掉 id 行后的全文指纹」做多重集比对，必须完全相等才允许删旧文件。

改名规则
--------
1. 去掉前缀 `ROOT::` / `PRE::` / `L::`。
2. 若以「者」结尾且不是真称谓（侍者 / 行者 / 尊者 / 道者），去掉该「者」。
3. 全量校验新 id 唯一、无路径分隔符、无空白首尾。

用法
----
  python3 tools/normalize_ids.py --dry-run   # 只打印将要发生什么
  python3 tools/normalize_ids.py --apply     # 真正执行（含删旧文件）
"""
import argparse
import io
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data")
CARDS = os.path.join(DATA, "patriarchs")

PREFIX = re.compile(r"^(ROOT|PRE|L)::")
KEEP_ZHE = ("侍者", "行者", "尊者", "道者")   # 「者」属称谓本体，不可去

# 个别 id 的手工定向（规则外特例，理由见注释）
EXTRA_ID = {
    # 分支图省略三祖~二十七祖造成的占位符「……」不属于人名
    "……西天二十八祖……": "西天二十八祖",
}


def new_id_of(old):
    s = PREFIX.sub("", old)
    s = EXTRA_ID.get(s, s)
    if s.endswith("者") and not s.endswith(KEEP_ZHE):
        s = s[:-1]
    return s


def card_text_without_id(text):
    """抹掉 id: 行，用于内容指纹比对。"""
    return re.sub(r"(?m)^id:.*$", "", text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json-only", action="store_true",
                    help="只重写 lineage.json（用于卡片已换名而 json 中断的续跑）")
    a = ap.parse_args()
    if not (a.dry_run or a.apply or a.json_only):
        ap.error("必须指定 --dry-run / --apply / --json-only")

    d = json.load(io.open(os.path.join(DATA, "lineage.json"), encoding="utf-8"))
    nodes = d["nodes"]

    if a.json_only:
        _rewrite_json(d, nodes)
        return

    # ---------- 1. 建映射并校验 ----------
    mapping = {}
    for n in nodes:
        old, new = n["id"], new_id_of(n["id"])
        if old in mapping:
            sys.exit("重复旧 id: " + old)
        mapping[old] = new

    news = list(mapping.values())
    dup = {x for x in news if news.count(x) > 1} if len(news) < 200 else set()
    if len(news) < 200:
        if dup:
            sys.exit("新 id 冲突: %s" % dup)
    else:
        from collections import Counter
        c = Counter(news)
        bad = [k for k, v in c.items() if v > 1]
        if bad:
            sys.exit("新 id 冲突 %d 个: %s" % (len(bad), bad[:10]))

    for new in news:
        if not new or new != new.strip() or any(ch in new for ch in "/\\\0:"):
            sys.exit("新 id 不合法: %r" % new)

    changed = [(o, n) for o, n in mapping.items() if o != n]
    print("节点 %d 个，其中 %d 个需要改名" % (len(nodes), len(changed)))
    zhe = [n for o, n in changed if o.endswith("者") and not n.endswith("者")]
    print("  去「者」的：%d 个" % len(zhe))
    print("  仅去前缀的：%d 个" % (len(changed) - len(zhe)))
    print("\n抽 12 例：")
    for o, n in changed[:12]:
        print("  %-34s → %s" % (o, n))

    # ---------- 2. 卡片内容指纹（迁移前）----------
    files = [f for f in os.listdir(CARDS) if f.endswith(".yaml")]
    print("\n卡片文件: %d" % len(files))
    texts = {}
    for f in files:
        t = io.open(os.path.join(CARDS, f), encoding="utf-8").read()
        m = re.search(r"(?m)^id:\s*(\S*)\s*$", t)
        if not m:
            sys.exit("卡片缺 id 行: " + f)
        cid = m.group(1)
        if cid + ".yaml" != f:
            # 已知历史：fix_mojibake 之后应已对齐；若出现即中止，别在脏数据上迁移
            sys.exit("文件名与 id 不一致，先修再迁: %s (id=%s)" % (f, cid))
        texts[cid] = t

    missing = [o for o in mapping if o not in texts and o != "ROOT::禅宗法脉"]
    if missing:
        sys.exit("❌ 有 %d 个非根节点无卡片，状态可疑，先修数据再迁移: %s"
                 % (len(missing), missing[:5]))

    # 内容指纹多重集：抹掉 id 行后的全文
    def fingerprint(items):
        from collections import Counter
        return Counter(card_text_without_id(t) for t in items)

    before = fingerprint(texts.values())

    if a.dry_run:
        print("\n[dry-run] 未写入任何文件。确认无误后加 --apply 执行。")
        return

    # ---------- 3. 写新卡（暂存目录先清空，防上次运行残留混入指纹）----------
    staged = {}
    for cid, t in texts.items():
        nid = mapping.get(cid, cid)
        newtext = re.sub(r"(?m)^id:.*$", "id: " + nid, t, count=1)
        staged[nid] = newtext

    tmpdir = os.path.join(DATA, ".cards_new")
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir)
    for nid, t in staged.items():
        io.open(os.path.join(tmpdir, nid + ".yaml"), "w", encoding="utf-8").write(t)
    n_staged = len(os.listdir(tmpdir))
    print("\n新卡已写入暂存目录: %d 份" % n_staged)
    if n_staged != len(staged):
        sys.exit("暂存写入不完整，中止")

    # ---------- 4. 内容指纹校验（写后，删前）----------
    after_items = []
    for f in os.listdir(tmpdir):
        after_items.append(io.open(os.path.join(tmpdir, f), encoding="utf-8").read())
    after = fingerprint(after_items)
    if before != after:
        only_b = before - after
        only_a = after - before
        sys.exit("❌ 内容指纹不一致，已中止（旧文件未删）。多出旧=%d 多出新=%d"
                 % (len(only_b), len(only_a)))
    print("✅ 内容指纹一致：%d 份卡正文逐字节相同（仅 id 行不同）" % sum(after.values()))

    # ---------- 5. 原子式换血：旧文件先整体挪进 trash（同卷 rename，可回滚）----------
    trash = os.path.join(DATA, ".cards_trash")
    if os.path.exists(trash):
        shutil.rmtree(trash)
    os.makedirs(trash)
    for f in files:
        os.replace(os.path.join(CARDS, f), os.path.join(trash, f))
    for f in os.listdir(tmpdir):
        os.replace(os.path.join(tmpdir, f), os.path.join(CARDS, f))
    now = len(os.listdir(CARDS))
    if now != len(staged):
        # 换血不完整：整体回滚后再报错
        for f in os.listdir(CARDS):
            os.remove(os.path.join(CARDS, f))
        for f in os.listdir(trash):
            os.replace(os.path.join(trash, f), os.path.join(CARDS, f))
        sys.exit("❌ 换血不完整（%d/%d），已回滚旧卡" % (now, len(staged)))
    print("新卡已就位: %d 份" % now)
    shutil.rmtree(trash)
    shutil.rmtree(tmpdir)

    # ---------- 6. 重写 lineage.json ----------
    _rewrite_json(d, nodes)


def _rewrite_json(d, nodes):
    mapping = {n["id"]: new_id_of(n["id"]) for n in nodes}
    for n in nodes:
        n["id"] = mapping[n["id"]]
        if n.get("parent") is not None:
            n["parent"] = mapping[n["parent"]]
        if n["name"] == "……西天二十八祖……":
            n["name"] = "西天二十八祖（综述）"

    def walk(node):
        node["id"] = mapping[node["id"]]
        for ch in node.get("children") or []:
            walk(ch)

    walk(d["tree"])
    d["meta"]["id_scheme"] = "clean-name（2026-10-29 去 L::/PRE::/ROOT:: 前缀与标题句末「者」）"
    io.open(os.path.join(DATA, "lineage.json"), "w", encoding="utf-8").write(
        json.dumps(d, ensure_ascii=False, indent=2))
    print("lineage.json 已重写（nodes + tree + parent 同步）")


if __name__ == "__main__":
    main()
