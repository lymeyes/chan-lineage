#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正 lineage.json 中两处 Unicode 乱码（分支图抽取残留 / 字体缺字映射错误）。

经 WebSearch 核对《五灯会元》/CBETA/佛学词典权威来源：
  - 𤦆 (U+24986) 应为 瑫 (U+746B)：如「杭州倾心寺法瑫宗一禅师」「婺州国泰院瑫禅师」「安国瑫禅师」
  - 𥙿 (U+255FF) 应为 裕 (U+88D5)：如「潭州龙兴裕禅师」（区别于「潭州龙兴禅师」）

涉及 5 个节点（均为 named_only 占位，尚无 draft YAML 卡）：
  国泰𤦆禅师 / 安国𤦆禅师 / 潭州龙兴𥙿禅师 /
  福州迁宗院行𤦆仁慧禅师 / 杭州倾心寺法𤦆宗一禅师

做法：对所有字符串字段（name/id/parent/tree 递归/其他）做字符替换，
保持 JSON 结构不变（indent=1，与 clean_ids.py 一致）。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIN = os.path.join(ROOT, "data", "lineage.json")

REPL = {"𤦆": "瑫", "𥙿": "裕"}

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
    d = json.load(open(LIN, encoding="utf-8"))
    before = sum(len(v) for v in REPL.values())  # placeholder
    # count occurrences in raw text
    raw = open(LIN, encoding="utf-8").read()
    cnt = {k: raw.count(k) for k in REPL}
    print("替换前字符计数:", cnt)
    d2 = walk(d)
    json.dump(d2, open(LIN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    raw2 = open(LIN, encoding="utf-8").read()
    cnt2 = {k: raw2.count(k) for k in REPL}
    print("替换后字符计数:", cnt2)
    print("lineage.json 乱码修正完成")

if __name__ == "__main__":
    main()
