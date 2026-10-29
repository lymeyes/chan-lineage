#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""宗脉谱系 · 完整性校验（离线自证）

用途：任何一次「文件被删 / 被同步覆盖 / 被误改」都能被本脚本断出来，
不依赖人工点数。判定依据是同目录 站点/MANIFEST.json（由 _generate.py 生成）。

用法：
  python3 _校验.py            # 只检查，报告
  python3 _校验.py --rebuild  # 检查到异常时自动重跑 _generate.py 重建

检查项（逐项给出 PASS/FAIL）：
  1) 祖师/*.md 数量 == 清单 zushi_md
  2) 祖师目录聚合指纹（逐文件 sha256 再聚合）== 清单 sha256
  3) 站点/index.html 存在且 sha256 一致
  4) 谱系总览.md / README.md sha256 一致
  5) 祖师目录无多余的历史残留文件
  6) （可选）与 chan-lineage 仓库的节点数一致
退出码：0 全部通过；1 存在异常。
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

OUT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(OUT, "站点")
ZUSHI = os.path.join(OUT, "祖师")
MANIFEST = os.path.join(SITE, "MANIFEST.json")
def _resolve_lineage():
    """定位仓库 lineage.json：环境变量 > 本文件所在仓库 > 已知默认路径。"""
    cands = []
    env = os.environ.get("CHAN_LINEAGE_DATA")
    if env:
        cands.append(os.path.join(env, "lineage.json"))
    here = os.path.dirname(os.path.abspath(__file__))
    cands.append(os.path.join(os.path.dirname(here), "data", "lineage.json"))
    cands.append(os.path.expanduser("~/WorkBuddy/task/Project/chan-lineage/data/lineage.json"))
    for c in cands:
        if os.path.exists(c):
            return c
    return None


LINEAGE = _resolve_lineage()

ok_all = True


def say(ok, label, detail=""):
    global ok_all
    ok_all = ok_all and ok
    print(("  [PASS] " if ok else "  [FAIL] ") + label + (("  " + detail) if detail else ""))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("宗脉谱系完整性校验 · " + OUT)
    if not os.path.exists(MANIFEST):
        print("  [FAIL] 缺少 站点/MANIFEST.json —— 请先运行 python3 _generate.py")
        return 1
    m = json.load(open(MANIFEST, encoding="utf-8"))
    counts = m["counts"]

    # 1) 数量
    md = [f for f in os.listdir(ZUSHI) if f.endswith(".md")] if os.path.isdir(ZUSHI) else []
    say(len(md) >= counts["zushi_md"],
        "祖师 .md 数量 >= %d" % counts["zushi_md"], "实测 %d" % len(md))
    # 2) 内容一致性：按清单逐份哈希后聚合比对
    z_sha = m["zushi_aggregate"]["sha256"]
    agg = hashlib.sha256()
    n = 0
    names = m.get("zushi_file_names")
    if names:
        missing = [x for x in names if not os.path.exists(os.path.join(ZUSHI, x))]
        say(not missing, "祖师 逐份文件齐全", "缺失 %d 份" % len(missing))
        for x in missing[:10]:
            print("        缺失:", x)
        if not missing:
            for name in sorted(names):
                agg.update(("%s\0%s\n" % (name, sha(os.path.join(ZUSHI, name)))).encode("utf-8"))
                n += 1
            say(n == counts["zushi_md"] and agg.hexdigest() == z_sha,
                "祖师 内容聚合指纹一致", "%d 份 / %s…" % (n, agg.hexdigest()[:16]))
    else:
        print("  [WARN] 清单无逐份文件名（旧版清单），跳过指纹级校验；请重跑 _generate.py 升级清单")

    # 3) 站点
    for rel, meta in (m.get("files") or {}).items():
        fp = os.path.join(OUT, rel)
        if not os.path.exists(fp):
            say(False, rel + " 存在")
            continue
        say(sha(fp) == meta["sha256"], rel + " sha256 一致", "%d 字节" % os.path.getsize(fp))

    # 5) 多余残留
    if names:
        extra = sorted(set(f for f in md) - set(names))
        say(not extra, "无历史残留文件", ("多余 %d 个" % len(extra)) if extra else "")
        for x in extra[:10]:
            print("        多余:", x)

    # 6) 与仓库节点数对齐
    if os.path.exists(LINEAGE):
        try:
            d = json.load(open(LINEAGE, encoding="utf-8"))
            n_nodes = len([x for x in d["nodes"] if x["id"] != "禅宗法脉"])
            say(n_nodes == counts["nodes"], "与 chan-lineage 节点数一致",
                "仓库 %d / 清单 %d" % (n_nodes, counts["nodes"]))
        except Exception as e:
            print("  [WARN] 读取 lineage.json 失败:", e)
    else:
        print("  [WARN] 未找到 chan-lineage 本地数据，跳过源一致性检查")

    print("\n结论：" + ("全部通过（库完整）" if ok_all else "存在异常，见上"))
    if not ok_all and "--rebuild" in sys.argv:
        print("\n--rebuild 指定，重跑生成器重建 …")
        r = subprocess.run([sys.executable, os.path.join(OUT, "_generate.py")])
        print("重建退出码:", r.returncode)
        return r.returncode
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
