#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理自相矛盾的 bio：卡已由 enrich 回填语录，但 bio 仍留着「未见独立条目」的
旧断言（enrich 的 PLACEHOLDER 正则原未覆盖此措辞）。按 template 同一口径改写。

守卫：只改 bio: 一行，其余字节不变。
"""
import io, os, re, sys, glob
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, "data", "patriarchs")
WORK_CN = {"X80n1565": "五灯会元", "T51n2076": "景德传灯录", "X78n1556": "建中靖国续灯录",
           "X79n1559": "嘉泰普灯录", "T51n2077": "续传灯录", "X68n1315": "古尊宿语录",
           "T47n1985": "镇州临济慧照禅师语录"}


def main():
    apply_ = "--apply" in sys.argv
    todo = []
    for p in sorted(glob.glob(os.path.join(CARDS, "*.yaml"))):
        d = yaml.safe_load(io.open(p, encoding="utf-8")) or {}
        bio = str(d.get("bio") or "")
        if d.get("status") != "draft" or "未见独立条目" not in bio:
            continue
        if not (d.get("sayings") or d.get("source_ref")):
            continue
        cb = str(d.get("cbeta") or "")
        pre = cb.split("_")[0] if cb else ""
        work = WORK_CN.get(pre, "所校灯录")
        newbio = "生平部分原文未载，仅存机缘语（见下）；据《%s》%s。" % (work, cb or "（锚点见 source_ref）")
        todo.append((p, d["id"], newbio))

    print("需改写 bio 的卡：%d 张" % len(todo))
    if not apply_:
        for p, cid, nb in todo[:6]:
            print("  %s → %s" % (cid, nb))
        print("  ...（dry-run，加 --apply 执行）")
        return

    for p, cid, newbio in todo:
        text = io.open(p, encoding="utf-8").read()
        lines = text.splitlines(keepends=True)
        out, n = [], 0
        for ln in lines:
            if ln.startswith("bio:"):
                out.append("bio: " + newbio + "\n"); n += 1
            else:
                out.append(ln)
        assert n == 1, cid
        io.open(p, "w", encoding="utf-8").write("".join(out))
    print("✓ 已改写 %d 张" % len(todo))


if __name__ == "__main__":
    main()
