#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 teacher 悬空引用：teacher 字段大量沿用灯录缩称（云门偃/马祖一/雪峰存…），
而卡 id 已规范化为通行全名（云门文偃/马祖道一/雪峰义存），二者对不上，
导致 1869 张卡的师承指向不存在的节点。

做法：
  1. 精确命中
  2. 剥掉括号注释（「石头希迁（亦参马祖）」这类人工备注）后重试
  3. 「地名 + 单字法名」→ 唯一「同地名 + 同末字」的更全名
  4. MANUAL 表兜底（异体字、上轮改名、单字名等）
无法解析的保留原值，由审计报告列出，不臆造。

守卫：每张卡只改 teacher: 一行，其余字节不变。
"""
import io, os, re, sys, glob, json, collections
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, "data", "patriarchs")

MANUAL = {
    "清凉益": "法眼文益禅师", "径山杲": "大慧宗杲禅师", "昭觉勤": "圆悟克勤禅师",
    "黄龙清": "灵源惟清禅师", "黄龙新": "死心悟新禅师", "黄龙心": "黄龙祖心禅师",
    "晦堂祖心（黄龙心禅师）": "黄龙祖心禅师",
    "天童华": "应庵昙华禅师", "天童华禅师（应庵昙华）": "应庵昙华禅师",
    "神鼎𬤇": "神鼎洪諲禅师", "金山颕": "金山昙颖禅师",
    "长庆棱": "长庆慧稜禅师", "长庆慧棱": "长庆慧稜禅师",
    "天台韶": "天台德韶国师", "天台德韶": "天台德韶国师",
    "鼓山晏": "鼓山晏国师",
    "安国𤦆": "安国瑫禅师", "国泰𤦆": "国泰瑫禅师",
    "魏府大觉": "魏府大觉和尚",
    "盐官安": "盐官齐安国师", "嵩岳安": "嵩岳安国师",
    "六祖慧能": "六祖大鉴禅师",
    "纸衣": "纸衣道者",
    "慧可": "二祖慧可", "僧璨": "三祖僧璨", "道信": "四祖道信", "弘忍": "五祖弘忍",
    "摩诃迦叶": "西天初祖摩诃迦叶", "菩提达摩": "东土初祖菩提达摩",
    "茱萸": "茱萸和尚", "破灶堕": "破灶堕和尚",
    "罗汉桂琛（玄沙师备下，雪峰义存再传）": "罗汉琛禅师",
    "宝峰克文（云庵真净）": "宝峰文禅师",
    "双峰": "双峰和尚", "岳山祖": "岳山祖庵主",
    "翠微无学（石头希迁再传）": "翠微学禅师",
    "南阳忠": "南阳忠国师", "杭州天龙": "杭州天龙和尚",
}
# 卡里确实不存在对应节点，保留原值，审计报告单列
KNOWN_UNRESOLVED = {"西天二十七祖般若多罗", "释迦牟尼佛", "石门慈照",
                    "杨岐方会（杨歧会禅师）"}

PLACEHOLDER = {"—", "-", "", "禅宗法脉"}


def clean(t):
    return re.sub(r"[（(][^）)]*[）)]", "", t).strip()


def build(ids):
    core = {}
    for i in ids:
        if i.endswith("禅师"):
            core.setdefault(i[:-2], []).append(i)
        elif i.endswith("国师"):
            core.setdefault(i[:-2], []).append(i)
    return core


def resolve(t, ids, core):
    if t in ids or t in PLACEHOLDER:
        return t
    if t in MANUAL:
        return MANUAL[t] if MANUAL[t] in ids else None
    for c0 in (t, clean(t)):
        c2 = c0
        for suf in ("禅师", "国师", "和尚"):
            if c2.endswith(suf):
                c2 = c2[: -len(suf)]
                break
        if not c2:
            continue
        if c2 in core and len(core[c2]) == 1:
            return core[c2][0]
        ks = [k for k in core if k.startswith(c2[:-1]) and k.endswith(c2[-1]) and k != c2]
        if len(ks) == 1:
            return core[ks[0]][0]
    return None


def set_teacher(text, new):
    lines = text.splitlines(keepends=True)
    out, n = [], 0
    for ln in lines:
        if re.match(r"^teacher:", ln):
            out.append("teacher: " + new + "\n"); n += 1
        else:
            out.append(ln)
    assert n == 1, n
    return "".join(out)


def main():
    apply_ = "--apply" in sys.argv
    cards = {}
    for p in glob.glob(os.path.join(CARDS, "*.yaml")):
        d = yaml.safe_load(io.open(p, encoding="utf-8")) or {}
        cards[d.get("id") or os.path.basename(p)[:-5]] = (p, d)
    ids = set(cards)
    core = build(ids)

    plan, unresolved = [], collections.Counter()
    for cid, (p, d) in sorted(cards.items()):
        t = d.get("teacher")
        if not isinstance(t, str) or not t.strip():
            continue
        t = t.strip()
        r = resolve(t, ids, core)
        if r is None:
            unresolved[t] += 1
            continue
        if r != t:
            plan.append((cid, p, t, r))

    print("需修 teacher: %d 张；无法解析保留原值: %d 名 / %d 张" %
          (len(plan), len(unresolved), sum(unresolved.values())))
    for t, c in unresolved.most_common():
        flag = "  (已知：卡中确无此节点)" if t in KNOWN_UNRESOLVED else "  ⚠ 待考"
        print("   %s\t%d%s" % (t, c, flag))
    if not apply_:
        for cid, _p, t, r in plan[:12]:
            print("  %-22s %s -> %s" % (cid, t, r))
        print("  ... 共 %d 张（dry-run，加 --apply 执行）" % len(plan))
        return

    for cid, p, t, r in plan:
        text = io.open(p, encoding="utf-8").read()
        new = set_teacher(text, r)
        a = "\n".join(l for l in text.splitlines() if not l.startswith("teacher:"))
        b = "\n".join(l for l in new.splitlines() if not l.startswith("teacher:"))
        assert a == b, "正文被改动: " + cid
        io.open(p, "w", encoding="utf-8").write(new)
    print("✓ 已修 %d 张卡的 teacher" % len(plan))
    io.open(os.path.join(ROOT, "reports", "teacher_unresolved.txt"), "w", encoding="utf-8").write(
        "\n".join("%s\t%d" % (t, c) for t, c in unresolved.most_common()) + "\n")


if __name__ == "__main__":
    main()
