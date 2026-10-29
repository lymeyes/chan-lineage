#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 5 个因分支图 IDS 拆解得来的乱码节点名，并升级为据《五灯会元》核校的真实 draft 卡。

依据（均已联网核验）：
  1. 杭州报慈院从[王)]  -> 杭州报慈院从瑰禅师（五灯会元卷八；房支应属法眼宗，parent=长庆棱）
  2. 临安府中天竺[仁-二+幻]堂中仁 -> 临安府中天竺幻堂中仁禅师（五灯会元卷十九，杨岐派）
  3. [婺-女+]州双溪印首座 -> 婺州双溪印首座（五灯会元卷十七，黄龙派，CBETA A026828）
  4. 隆兴府祐圣法[宋-木+居] -> 隆兴府祐圣法居禅师（五灯会元卷十七，黄龙派）
  5. 密州[山耆]山宁 -> 密州煮山宁禅师（五灯会元卷十六，云门宗，parent=雪窦明）
"""
import json, os, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIN = os.path.join(ROOT, "data", "lineage.json")
PAT = os.path.join(ROOT, "data", "patriarchs")

# old_id -> (new_id, new_name, new_house|None)
RENAME = {
    "L::杭州报慈院从**[王*)]**禅师": ("L::杭州报慈院从瑰禅师", "杭州报慈院从瑰", "法眼宗"),
    "L::临安府中天竺**[仁-二+幻]**堂中仁禅师": ("L::临安府中天竺幻堂中仁禅师", "临安府中天竺幻堂中仁", None),
    "L::[婺-女+]**州双溪印首座": ("L::婺州双溪印首座", "婺州双溪印首座", None),
    "L::隆兴府祐圣法**[宋-木+居]**禅师": ("L::隆兴府祐圣法居禅师", "隆兴府祐圣法居", None),
    "L::密州**[山*耆]**山宁禅师": ("L::密州煮山宁禅师", "密州煮山宁", "云门宗"),
}

# 真实卡片内容（据《五灯会元》通行本，verify_status=sourced）
CARDS = {
    "L::杭州报慈院从瑰禅师": {
        "id": "L::杭州报慈院从瑰禅师", "name": "杭州报慈院从瑰",
        "honorific": "杭州报慈院从瑰禅师", "school": "法眼宗", "dynasty": "五代",
        "region": "杭州报慈院", "teacher": "长庆慧棱",
        "source_ref": "五灯会元·卷八·报慈从瑰禅师 / 五灯全书·卷八",
        "cbeta": "《五灯会元》未入大正藏，属卍续藏 X 部；本卡据通行本核校。",
        "bio": "杭州报慈院从瑰禅师，福州陈氏子。师承法眼宗长庆慧棱，为法眼一脉在杭州的重要传人。",
        "sayings": [
            {"text": "僧问：「承古有言，今人看古教，未免心中闹。欲免心中闹，应须看古教。如何是古教？」师曰：「如是我闻。」曰：「如何是心中闹？」师曰：「那畔雀儿声。」",
             "ref": "五灯会元·卷八·报慈从瑰禅师"},
        ],
        "status": "draft", "verify": "内容据《五灯会元》卷八（通行本）核校，待对校卍续藏 X 部五灯会元。",
        "evidence": "primary", "verify_status": "sourced",
    },
    "L::临安府中天竺幻堂中仁禅师": {
        "id": "L::临安府中天竺幻堂中仁禅师", "name": "临安府中天竺幻堂中仁",
        "honorific": "中天竺幻堂中仁禅师（赐号幻堂）", "school": "杨岐派", "dynasty": "宋",
        "region": "临安府中天竺", "teacher": "圆悟克勤",
        "source_ref": "五灯会元·卷十九·中竺中仁 / 五灯全书·卷四十三 / 嘉泰普灯录·卷十五",
        "cbeta": "《五灯会元》属卍续藏 X 部；嘉泰普灯录见 CBETA X79n1558。",
        "bio": "临安府中天竺幻堂中仁禅师，洛阳人。少依东京奉先院出家，宋宣和初（1119）赐牒于庆基殿落发进具，后往来三藏译经所谛穷经论。时圆悟克勤居天宁，凌晨谒之，悟劈口击之，因坠一齿，即大悟，留天宁。后开法大觉，迁中天竺，次徙灵峰。孝宗淳熙甲午（1174）四月八日诏入赐座说法，举「不与万法为侣」因缘令拈提。",
        "sayings": [
            {"text": "上堂：「九十春光已过半，养花天气正融和。海棠枝上莺声好，道与时流见得么？虽然如是，且透声透色一句作么生道？金勒马嘶芳草地，玉楼人醉杏花天。」",
             "ref": "五灯会元·卷十九·中竺中仁"},
            {"text": "举狗子无佛性话，乃曰：「二八佳人刺绣迟，紫荆花下啭黄鹂。可怜无限伤春意，尽在停针不语时。」",
             "ref": "五灯会元·卷十九·中竺中仁"},
            {"text": "帝举「不与万法为侣」因缘，师拈罢，颂曰：「秤锤搦出油，闲言长语休。腰缠十万贯，骑鹤上扬州。」",
             "ref": "五灯会元·卷十九·中竺中仁 / 五灯全书·卷四十三"},
        ],
        "status": "draft", "verify": "内容据《五灯会元》卷十九、《五灯全书》卷四十三（通行本）核校，待对校卍续藏 X 部。",
        "evidence": "primary", "verify_status": "sourced",
    },
    "L::婺州双溪印首座": {
        "id": "L::婺州双溪印首座", "name": "婺州双溪印首座",
        "honorific": "婺州双溪印首座", "school": "黄龙派", "dynasty": "北宋",
        "region": "婺州双溪", "teacher": "宝峰克文（云庵真净）",
        "source_ref": "五灯会元·卷十七·宝峰文禅师法嗣 / 五灯全书·卷三十八 / 嘉泰普灯录（CBETA A026828）",
        "cbeta": "CBETA 人名规范资料库 A026828；嘉泰普灯录见 X79n1558。",
        "bio": "婺州双溪印首座，北宋临济宗黄龙派，宝峰克文（云庵真净）弟子。自见真净，彻证宗猷，归遁双溪，隐而不出。",
        "sayings": [
            {"text": "偶书曰：「折脚铛儿谩自煨，饭余长是坐堆堆。一从近日生涯拙，百鸟衔华去不来。」",
             "ref": "五灯会元·卷十七·宝峰文禅师法嗣"},
            {"text": "以触衣碎甚，作偈曰：「不挂寸丝方免寒，何须特地袅长竿。而今落落零零也，七佛之名甚处安？」",
             "ref": "五灯会元·卷十七·宝峰文禅师法嗣"},
        ],
        "status": "draft", "verify": "内容据《五灯会元》卷十七、《五灯全书》卷三十八（通行本）核校，CBETA 人名库 A026828 已对应。",
        "evidence": "primary", "verify_status": "sourced",
    },
    "L::隆兴府祐圣法居禅师": {
        "id": "L::隆兴府祐圣法居禅师", "name": "隆兴府祐圣法居",
        "honorific": "隆兴府祐圣法居禅师", "school": "黄龙派", "dynasty": "宋",
        "region": "隆兴府祐圣院", "teacher": "黄龙慧南",
        "source_ref": "五灯会元·卷十七·黄龙慧南法嗣 / 五灯全书·卷三十八",
        "cbeta": "《五灯会元》属卍续藏 X 部。",
        "bio": "隆兴府祐圣法居禅师，潮阳郑氏子。晚见黄龙慧南，深蒙印可，为黄龙派二代传人。",
        "sayings": [
            {"text": "上堂：「此事如医家验病方，且杂毒满腹，未易攻治，必瞑眩之药，而后可瘳。就令徇意投之，适足狂惑，增其沉痼。求其已病，不亦左乎？法堂前草深，于心无愧。」",
             "ref": "五灯会元·卷十七·黄龙慧南法嗣"},
        ],
        "status": "draft", "verify": "内容据《五灯会元》卷十七（通行本）核校，待对校卍续藏 X 部。",
        "evidence": "primary", "verify_status": "sourced",
    },
    "L::密州煮山宁禅师": {
        "id": "L::密州煮山宁禅师", "name": "密州煮山宁",
        "honorific": "密州煮山宁禅师", "school": "云门宗", "dynasty": "宋",
        "region": "密州煮山", "teacher": "雪窦重显（雪窦明禅师）",
        "source_ref": "五灯会元·卷十六·雪窦明禅师法嗣 / 五灯全书·卷三十四",
        "cbeta": "《五灯会元》属卍续藏 X 部。",
        "bio": "密州煮山宁禅师，雪窦重显（明禅师）法嗣，云门宗传人。",
        "sayings": [
            {"text": "上堂：「有时孤峰顶上啸月眠云，有时大洋海中翻波走浪，有时十字街头七穿八穴。诸人还相委悉么？樟树花开盛，芭蕉叶最多。」",
             "ref": "五灯会元·卷十六·雪窦明禅师法嗣"},
        ],
        "status": "draft", "verify": "内容据《五灯会元》卷十六（通行本）核校，待对校卍续藏 X 部。",
        "evidence": "primary", "verify_status": "sourced",
    },
}

def walk(o, renames):
    if isinstance(o, dict):
        if "id" in o and o["id"] in renames:
            new_id, new_name, new_house = renames[o["id"]]
            o["id"] = new_id
            o["name"] = new_name
            if new_house:
                o["house"] = new_house
        if "parent" in o and o["parent"] in {k: v[0] for k, v in renames.items()}:
            o["parent"] = {k: v[0] for k, v in renames.items()}[o["parent"]]
        for k, v in list(o.items()):
            walk(v, renames)
    elif isinstance(o, list):
        for x in o:
            walk(x, renames)

def main():
    d = json.load(open(LIN, encoding="utf-8"))
    # 1) 修正 nodes 列表
    for n in d["nodes"]:
        if n["id"] in RENAME:
            new_id, new_name, new_house = RENAME[n["id"]]
            n["id"] = new_id
            n["name"] = new_name
            if new_house:
                n["house"] = new_house
            if "parent" in n and n["parent"] in {k: v[0] for k, v in RENAME.items()}:
                n["parent"] = {k: v[0] for k, v in RENAME.items()}[n["parent"]]
    # 2) 修正 tree
    walk(d["tree"], RENAME)
    json.dump(d, open(LIN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("lineage.json 已更新 5 个节点 + 2 处房支")

    # 3) 重命名并写入真实卡片
    for old_id, (new_id, _, _) in RENAME.items():
        old_f = os.path.join(PAT, old_id + ".yaml")
        new_f = os.path.join(PAT, new_id + ".yaml")
        if os.path.exists(old_f):
            if old_f != new_f:
                os.rename(old_f, new_f)
            print("rename:", old_id, "->", new_id)
        card = CARDS[new_id]
        with open(new_f, "w", encoding="utf-8") as f:
            yaml.safe_dump(card, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print("write :", new_f)

if __name__ == "__main__":
    main()
