#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""两处 Unicode 乱码修复 + YAML 内部 id 与节点 id 一致性对账。

1) lineage.json 中字体缺字映射错误的乱码（分支图抽取残留）：
     𤦆 (U+24986) -> 瑫 (U+746B)   𥙿 (U+255FF) -> 裕 (U+88D5)
   均经《五灯会元》/CBETA 目录/佛学词典联网核验还原真实法讳。
   涉及 5 节点：国泰瑫、安国瑫、潭州龙兴裕、福州迁宗院行瑫仁慧、杭州倾心寺法瑫宗一。

2) 一致性对账（修复 clean_ids 仅改名未改内部 id 的遗漏）：
   clean_ids.py 曾按 lineage.json 的新 id 重命名了 28 个 YAML 文件名，
   但从未回写文件内部的 `id:` 字段，导致这 28 张卡的内部 id 仍带 ** 分隔符、
   与节点 id 脱节（点击节点看不到卡）。本脚本统一把每个 YAML 的内部 id 置为
   「去 **、去缺字乱码后的文件名」，确保  id == 文件名 == 节点 id  三者一致。

做法：递归替换 lineage.json 所有字符串字段；逐文件校正 YAML 内部 id 与文件名。
幂等：已正确的文件不改动。
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIN = os.path.join(ROOT, "data", "lineage.json")
PAT = os.path.join(ROOT, "data", "patriarchs")

REPL = {"𤦆": "瑫", "𥙿": "裕"}  # 缺字映射修正

def fix_str(s):
    for k, v in REPL.items():
        s = s.replace(k, v)
    return s

def walk(o):
    if isinstance(o, str):
        return fix_str(o)
    if isinstance(o, dict):
        return {fix_str(k): walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(x) for x in o]
    return o

def main():
    # ---- 1) lineage.json ----
    d = json.load(open(LIN, encoding="utf-8"))
    raw = open(LIN, encoding="utf-8").read()
    cnt = {k: raw.count(k) for k in REPL}
    d2 = walk(d)
    json.dump(d2, open(LIN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    raw2 = open(LIN, encoding="utf-8").read()
    cnt2 = {k: raw2.count(k) for k in REPL}
    print("lineage.json 乱码替换前/后:", cnt, "->", cnt2)
    node_ids = {n["id"] for n in d2["nodes"]}

    # ---- 2) YAML 内部 id 与文件名对账 ----
    renamed = 0
    id_fixed = 0
    for fn in os.listdir(PAT):
        if not fn.endswith(".yaml"):
            continue
        fp = os.path.join(PAT, fn)
        base = fn[:-5]
        # 目标文件名：修正缺字乱码
        correct_base = fix_str(base)
        # 目标内部 id：文件名再去掉 ** 分隔符
        target_id = correct_base.replace("**", "")
        # 重命名文件（仅当文件名含缺字乱码）
        if base != correct_base:
            nf = correct_base + ".yaml"
            if not os.path.exists(os.path.join(PAT, nf)):
                os.rename(fp, os.path.join(PAT, nf))
                fp = os.path.join(PAT, nf)
                renamed += 1
        # 回写内部 id 行（仅当与 target_id 不同）
        lines = open(fp, encoding="utf-8").read().split("\n")
        new_lines = []
        changed = False
        for ln in lines:
            m_id = re.match(r"^id:\s*(.*)$", ln)
            m_name = re.match(r"^name:\s*(.*)$", ln)
            if m_id and m_id.group(1).strip() != target_id:
                new_lines.append("id: " + target_id)
                changed = True
            elif m_name:
                # name 字段同样需去缺字乱码、去 ** 分隔符
                new_name = fix_str(m_name.group(1).strip()).replace("**", "")
                if new_name != m_name.group(1).strip():
                    new_lines.append("name: " + new_name)
                    changed = True
                else:
                    new_lines.append(ln)
            else:
                new_lines.append(ln)
        if changed:
            open(fp, "w", encoding="utf-8").write("\n".join(new_lines))
            id_fixed += 1

    print("YAML 文件名修正(缺字):", renamed, "| YAML 内部 id/name 修正:", id_fixed)
    # ---- 校验 ----
    yids = {os.path.basename(x)[:-5] for x in glob_yamls()}
    orphan_yaml = sorted(yids - node_ids)
    orphan_node = sorted(node_ids - yids - {"ROOT::禅宗法脉"})
    print("对账后 有 YAML 无节点:", len(orphan_yaml), orphan_yaml[:10])
    print("对账后 有节点无 YAML(去ROOT):", len(orphan_node), orphan_node[:10])

def glob_yamls():
    import glob
    return glob.glob(os.path.join(PAT, "*.yaml"))

if __name__ == "__main__":
    main()
