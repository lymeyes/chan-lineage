#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""缩称卡改名：把「地名+单字法名」的缩称卡改为「地名+通行全名」。

背景：灯录条目标题多作「地名＋庵号＋法名」，谱系树生成时截成了单字，
如「百丈海」实为百丈怀海、「天童觉」实为天童正觉（宏智正觉）。
缩称导致 enrich 的 exact/suffix 匹配全部落空，这 117 张被误标「未见独立条目」。

守卫：
  1. 每张卡只允许改 id: / name: 行与新增 alias: 行，其余字节逐个不变
  2. 新 id 不得与现有卡撞名
  3. 计划内新 id 互相不撞
  4. lineage.json 的 nodes / parent / tree 同步，且节点数不变
"""
import io, os, re, sys, json, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CARDS = os.path.join(DATA, "patriarchs")
LINEAGE = os.path.join(DATA, "lineage.json")

# 旧 id -> (新 id, alias)   alias = 原缩称（保留可检索）
RENAME = {
    "万年一禅师": ("万年法一禅师", "万年一"),
    "万年贲禅师": ("万年昙贲禅师", "万年贲"),
    "三祖宗禅师": ("三祖法宗禅师", "三祖宗"),
    "上封才禅师": ("上封本才禅师", "上封才"),
    "上封秀禅师": ("上封祖秀禅师", "上封秀"),
    "东林总禅师": ("东林常总禅师", "东林总"),
    "东林颜禅师": ("东林道颜禅师", "东林颜"),
    "东禅岳禅师": ("东禅思岳禅师", "东禅岳"),
    "中竺妙禅师": ("中竺元妙禅师", "中竺妙"),
    "乌巨行禅师": ("乌巨道行禅师", "乌巨行"),
    "九峰韶禅师": ("九峰鉴韶禅师", "九峰韶"),
    "云居如禅师": ("云居法如禅师", "云居如"),
    "云居祐禅师": ("云居元祐禅师", "云居祐"),
    "云居舜禅师": ("云居晓舜禅师", "云居舜"),
    "云峰悦禅师": ("云峰文悦禅师", "云峰悦"),
    "云盖智禅师": ("云盖守智禅师", "云盖智"),
    "云盖本禅师": ("云盖智本禅师", "云盖本"),
    "五祖常禅师": ("五祖晓常禅师", "五祖常"),
    "五祖自禅师": ("五祖表自禅师", "五祖自"),
    "仰山伟禅师": ("仰山行伟禅师", "仰山伟"),
    "何山珣禅师": ("何山守珣禅师", "何山珣"),
    "佛日才禅师": ("佛日智才禅师", "佛日才"),
    "保宁玑禅师": ("保宁圆玑禅师", "保宁玑"),
    "保宁英禅师": ("保宁子英禅师", "保宁英"),
    "元丰满禅师": ("元丰清满禅师", "元丰满"),
    "光孝兰禅师": ("光孝慧兰禅师", "光孝兰"),
    "光孝慜禅师": ("光孝果慜禅师", "光孝慜"),
    "兜率悦禅师": ("兜率从悦禅师", "兜率悦"),
    "净因成禅师": ("净因法成禅师", "净因成"),
    "净因臻禅师": ("净因道臻禅师", "净因臻"),
    "净土思禅师": ("净土善思禅师", "净土思"),
    "净慈昌禅师": ("净慈道昌禅师", "净慈昌"),
    "净慈明禅师": ("净慈悟明禅师", "净慈明"),
    "北塔广禅师": ("北塔思广禅师", "北塔广"),
    "北宗秀禅师": ("北宗神秀禅师", "北宗秀"),
    "北禅贤禅师": ("北禅智贤禅师", "北禅贤"),
    "华藏民禅师": ("华藏安民禅师", "华藏民"),
    "大愚芝禅师": ("大愚守芝禅师", "大愚芝"),
    "大洪恩禅师": ("大洪报恩禅师", "大洪恩"),
    "大洪遂禅师": ("大洪守遂禅师", "大洪遂"),
    "大洪预禅师": ("大洪庆预禅师", "大洪预"),
    "大随静禅师": ("大随元静禅师", "大随静"),
    "天封归禅师": ("天封子归禅师", "天封归"),
    "天童交禅师": ("天童澹交禅师", "天童交"),
    "天童觉禅师": ("天童正觉禅师", "天童觉"),
    "天衣怀禅师": ("天衣义怀禅师", "天衣怀"),
    "太平懃禅师": ("太平慧懃禅师", "太平懃"),
    "夹山纯禅师": ("夹山晓纯禅师", "夹山纯"),
    "宝峰照禅师": ("宝峰惟照禅师", "宝峰照"),
    "广因要禅师": ("广因择要禅师", "广因要"),
    "广灵祖禅师": ("广灵希祖禅师", "广灵祖"),
    "建隆庆禅师": ("建隆昭庆禅师", "建隆庆"),
    "开先珣禅师": ("开先智珣禅师", "开先珣"),
    "开先瑛禅师": ("开先行瑛禅师", "开先瑛"),
    "开善谦禅师": ("开善道谦禅师", "开善谦"),
    "归宗章禅师": ("归宗弘章禅师", "归宗章"),
    "慧日雅禅师": ("慧日文雅禅师", "慧日雅"),
    "慧林深禅师": ("慧林怀深禅师", "慧林深"),
    "护国元禅师": ("护国景元禅师", "护国元"),
    "护国月禅师": ("护国齐月禅师", "护国月"),
    "报本元禅师": ("报本慧元禅师", "报本元"),
    "报本兰禅师": ("报本有兰禅师", "报本兰"),
    "教忠光禅师": ("教忠弥光禅师", "教忠光"),
    "明招慧禅师": ("明招文慧禅师", "明招慧"),
    "昭觉元禅师": ("昭觉道元禅师", "昭觉元"),
    "昭觉白禅师": ("昭觉纯白禅师", "昭觉白"),
    "智海平禅师": ("智海道平禅师", "智海平"),
    "本觉一禅师": ("本觉守一禅师", "本觉一"),
    "栖贤迁禅师": ("栖贤智迁禅师", "栖贤迁"),
    "泐潭准禅师": ("泐潭文准禅师", "泐潭准"),
    "泐潭清禅师": ("泐潭善清禅师", "泐潭清"),
    "泐潭澄禅师": ("泐潭怀澄禅师", "泐潭澄"),
    "泐潭英禅师": ("泐潭洪英禅师", "泐潭英"),
    "法云本禅师": ("法云善本禅师", "法云本"),
    "法云秀禅师": ("法云法秀禅师", "法云秀"),
    "洞庭月禅师": ("洞庭慧月禅师", "洞庭月"),
    "灵隐光禅师": ("灵隐慧光禅师", "灵隐光"),
    "灵隐远禅师": ("灵隐慧远禅师", "灵隐远"),
    "玉泉皓禅师": ("玉泉承皓禅师", "玉泉皓"),
    "玉泉芳禅师": ("玉泉谓芳禅师", "玉泉芳"),
    "琅邪起禅师": ("琅邪永起禅师", "琅邪起"),
    "瑞岩海禅师": ("瑞岩义海禅师", "瑞岩海"),
    "甘露宣禅师": ("甘露仲宣禅师", "甘露宣"),
    "甘露颙禅师": ("甘露德颙禅师", "甘露颙"),
    "白杨顺禅师": ("白杨法顺禅师", "白杨顺"),
    "石头回禅师": ("石头自回禅师", "石头回"),
    "石门易禅师": ("石门元易禅师", "石门易"),
    "石门远禅师": ("石门绍远禅师", "石门远"),
    "石霜永禅师": ("石霜法永禅师", "石霜永"),
    "福严感禅师": ("福严慈感禅师", "福严感"),
    "称心倧禅师": ("称心省倧禅师", "称心倧"),
    "称心明禅师": ("称心守明禅师", "称心明"),
    "育王裕禅师": ("育王端裕禅师", "育王裕"),
    "育王谌禅师": ("育王介谌禅师", "育王谌"),
    "胜因静禅师": ("胜因咸静禅师", "胜因静"),
    "褒亲瑞禅师": ("褒亲有瑞禅师", "褒亲瑞"),
    "西禅净禅师": ("西禅守净禅师", "西禅净"),
    "西禅琏禅师": ("西禅文琏禅师", "西禅琏"),
    "西禅需禅师": ("西禅鼎需禅师", "西禅需"),
    "谷隐俨禅师": ("谷隐知俨禅师", "谷隐俨"),
    "象田卿禅师": ("象田梵卿禅师", "象田卿"),
    "道场全禅师": ("道场法全禅师", "道场全"),
    "道场慧禅师": ("道场居慧禅师", "道场慧"),
    "道场琳禅师": ("道场慧琳禅师", "道场琳"),
    "道场辩禅师": ("道场明辩禅师", "道场辩"),
    "金山宁禅师": ("金山善宁禅师", "金山宁"),
    "金山新禅师": ("金山瑞新禅师", "金山新"),
    "金山颕禅师": ("金山昙颖禅师", "金山颕"),
    "长芦了禅师": ("长芦清了禅师", "长芦了"),
    "长芦信禅师": ("长芦崇信禅师", "长芦信"),
    "雪窦宗禅师": ("雪窦嗣宗禅师", "雪窦宗"),
    "雪窦雅禅师": ("雪窦法雅禅师", "雪窦雅"),
    "青原信禅师": ("青原惟信禅师", "青原信"),
    "黄龙忠禅师": ("黄龙法忠禅师", "黄龙忠"),
    "黄龙震禅师": ("黄龙道震禅师", "黄龙震"),
    "龙翔珪禅师": ("龙翔士珪禅师", "龙翔珪"),
    "龙门远禅师": ("龙门清远禅师", "龙门远"),
}


def edit_card(text, new_id, new_name, alias):
    lines = text.splitlines(keepends=True)
    out, did, dn = [], 0, 0
    for ln in lines:
        if re.match(r"^id:", ln):
            out.append("id: " + new_id + "\n"); did += 1
        elif re.match(r"^name:", ln):
            out.append("name: " + new_name + "\n")
            if alias:
                out.append("alias: " + alias + "\n")
            dn += 1
        else:
            out.append(ln)
    assert did == 1 and dn == 1, (new_id, did, dn)
    return "".join(out)


def main():
    apply_ = "--apply" in sys.argv
    stems = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(CARDS, "*.yaml"))}

    # 幂等 / 断点续跑：旧卡不存在但新卡已在 = 上次已改完，跳过
    missing, already = [], []
    for k, (new, _a) in RENAME.items():
        if k in stems:
            continue
        (already if new in stems else missing).append(k)
    if missing:
        sys.exit("待改卡既无旧名也无新名：%s" % missing[:5])
    if already:
        print("跳过已完成 %d 张" % len(already))
    done_new = {RENAME[k][0] for k in already}
    mapping, plan = {}, []
    new_ids = [v[0] for v in RENAME.values()]
    assert len(new_ids) == len(set(new_ids)), "计划内撞名"
    clash = [n for n in new_ids if n in stems and n not in done_new]
    if clash:
        # 上次中断残留：新卡已建、旧卡未删。正文（去 id/name/alias）相同则视为同一卡的中间态，清掉旧卡
        strip2 = lambda t: "\n".join(
            l for l in t.splitlines() if not re.match(r"^(id:|name:|alias:)", l)) + "\n"
        inv = {v[0]: k for k, v in RENAME.items()}
        for n in list(clash):
            old = inv[n]
            a = io.open(os.path.join(CARDS, old + ".yaml"), encoding="utf-8").read()
            b = io.open(os.path.join(CARDS, n + ".yaml"), encoding="utf-8").read()
            if strip2(a) != strip2(b):
                sys.exit("真撞名（正文不同）：%s vs %s" % (old, n))
            print("清理上次中断残留：%s（新卡 %s 已在）" % (old, n))
            if apply_:
                os.remove(os.path.join(CARDS, old + ".yaml"))
            stems.discard(old)
            mapping.setdefault(old, n)
            already.append(old)
            clash.remove(n)
        done_new |= {RENAME[k][0] for k in already}
    if clash:
        sys.exit("与现有卡撞名：%s" % clash)

    mapping_need_reset = 0
    for old, (new, alias) in RENAME.items():
        if old in already:
            mapping[old] = new      # lineage 仍需同步
            continue
        p = os.path.join(CARDS, old + ".yaml")
        text = io.open(p, encoding="utf-8").read()
        new_name = new[:-2] if new.endswith("禅师") else new
        newtext = edit_card(text, new, new_name, alias)
        strip = lambda t: "\n".join(
            l for l in t.splitlines() if not re.match(r"^(id:|name:|alias:)", l)) + "\n"
        assert strip(text) == strip(newtext), "正文被改动: " + old
        plan.append((old, new, new_name, alias, text, newtext))
        mapping[old] = new

    print("将改名 %d 张（跳过 %d 张法名待考）" % (len(plan), 2))
    if not apply_:
        for o, n, nn, al, _, _ in plan:
            print("  %-14s -> %-16s name=%s alias=%s" % (o, n, nn, al))
        print("\n[dry-run] 加 --apply 执行")
        return

    for old, new, nn, al, text, newtext in plan:
        p = os.path.join(CARDS, old + ".yaml")
        io.open(os.path.join(CARDS, new + ".yaml"), "w", encoding="utf-8").write(newtext)
        os.remove(p)
    print("✓ 卡片已改名 %d 张" % len(plan))

    d = json.load(io.open(LINEAGE, encoding="utf-8"))
    n0 = len(d["nodes"])
    newset = set(mapping.values())
    cnt = skip = 0
    for n in d["nodes"]:
        if n["id"] in mapping:
            n["id"] = mapping[n["id"]]
            n["name"] = n["id"][:-2] if n["id"].endswith("禅师") else n["id"]
            cnt += 1
        elif n["id"] in newset:
            skip += 1
        if n.get("parent") in mapping:
            n["parent"] = mapping[n["parent"]]

    def walk(node):
        if node.get("id") in mapping:
            node["id"] = mapping[node["id"]]
            node["name"] = node["id"][:-2] if node["id"].endswith("禅师") else node["id"]
        for ch in node.get("children") or []:
            walk(ch)

    for root in d["tree"] if isinstance(d["tree"], list) else [d["tree"]]:
        walk(root)
    if cnt + skip != len(mapping):
        sys.exit("lineage 节点数不符：改 %d + 已改 %d ≠ 计划 %d" % (cnt, skip, len(mapping)))
    assert len(d["nodes"]) == n0
    io.open(LINEAGE, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2))
    print("✓ lineage.json 同步 %d 个节点（另 %d 个此前已同步）" % (cnt, skip))
    io.open(os.path.join(ROOT, "reports", "rename_abbrev.json"), "w", encoding="utf-8").write(
        json.dumps(mapping, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
