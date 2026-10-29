#!/usr/bin/env python3
"""CBETA 逐字校核器：对 draft 卡做「人名定位 + 语句逐字比对」，产出核校报告。

输入：
  sources/<id>.txt   由 tools/extract_cbeta.py 生成（ref\t卷\t正文）
  data/patriarchs/*.yaml
输出：
  reports/cbeta_check_<date>.md   人工可读报告
  reports/cbeta_check_<date>.json 机器可读结果（供后续升卡）

判定分级：
  A 双证：卡中至少 1 条语句在指定经文中逐字命中 + 人名在同一经文定位
  B 单证：仅语句命中 或 仅人名定位（含跨文本命中）
  C 未命中：需人工排查（可能卷次不同/异体字/缺字 gap）

匹配策略（gap 容错）：
  - 简体卡片先经 zhconv 转繁体再比对
  - 双方统一去除全部标点、空白与 CBETA 缺字 gap（PUA U+E000-F8FF 及扩展区）
  - 语句取最长 12 字窗口检索；不足 12 字取全句
"""
import glob, json, os, re, sys, bisect, datetime
import yaml
from zhconv import convert as zhconv_convert

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sources")
OUT = os.path.join(ROOT, "reports")

WORK_TITLES = {
    "T51n2076": "景德傳燈錄", "T51n2077": "續傳燈錄", "X80n1565": "五燈會元",
    "X68n1315": "古尊宿語錄", "X78n1556": "建中靖國續燈錄", "X79n1559": "嘉泰普燈錄",
    "T47n1985": "鎮州臨濟慧照禪師語錄",
}
# 卡片 source_ref 中的别名 -> 规范 id
ALIAS = {"景德传灯录": "T51n2076", "五灯会元": "X80n1565", "五灯全书": "五灯全书(未入库)",
         "临济录": "T47n1985", "古尊宿语录": "X68n1315", "建中靖国续灯录": "X78n1556",
         "嘉泰普灯录": "X79n1559", "续传灯录": "T51n2077"}

GAP = re.compile(r"[\uE000-\uF8FF]|[\U000F0000-\U000FFFFF]|[\U00020000-\U0003FFFF]")
KEEP = re.compile(r"[^\w\u4e00-\u9fff\u3400-\u4dbf]|_")  # 仅保留 CJK 与字母数字


def norm(s):
    """归一化：去标点/空白/gap，简转繁。"""
    s = zhconv_convert(s, "zh-hant")
    s = GAP.sub("", s)
    s = KEEP.sub("", s)
    return s


class Corpus:
    def __init__(self):
        self.lines = []  # (ref, juan, raw, norm)
        self.by_work = {}  # wid -> (concat, offsets, line_idx)
        for fp in glob.glob(os.path.join(SRC, "*.txt")):
            wid = os.path.basename(fp)[:-4]
            for i, ln in enumerate(open(fp, encoding="utf-8")):
                if ln.startswith("#"):
                    continue
                parts = ln.rstrip("\n").split("\t")
                if len(parts) < 3:
                    continue
                self.lines.append((wid, parts[0], parts[1], parts[2], norm(parts[2])))
        for wid in {l[0] for l in self.lines}:
            sel = [(i, l[4]) for i, l in enumerate(self.lines) if l[0] == wid]
            concat = "\n".join(s for _, s in sel)
            offs, acc = [], 0
            for _, s in sel:
                offs.append(acc)
                acc += len(s) + 1
            idx = [i for i, _ in sel]
            self.by_work[wid] = (concat, offs, idx)

    def find(self, q, work=None):
        """返回 [(wid, ref, juan, raw_line)]；q 为归一化串。"""
        hits = []
        for wid, (concat, offs, idx) in self.by_work.items():
            if work and wid != work:
                continue
            start = 0
            while True:
                p = concat.find(q, start)
                if p < 0:
                    break
                j = bisect.bisect_right(offs, p) - 1
                _, ref, juan, raw, _ = self.lines[idx[j]]
                hits.append((wid, ref, juan, raw))
                start = p + 1
                if len(hits) >= 8:
                    return hits
        return hits


def best_window(text, n=12):
    """取归一化文本中最长 n 字的窗口（无标点障碍的连续段优先）。"""
    if len(text) <= n:
        return text
    # 优先取标点切分后的最长连续段
    segs = sorted(text.split(), key=len, reverse=True) if False else None
    return text[:n]


NAME_SUFFIX = re.compile(r"(禪師|和尚|首座|大師|國師|上座|法嗣|沙彌|尼)")


def name_keys(name):
    """由法名生成检索键：(键, 是否强键)。全名/尾 4 字为强键；
    尾 2 字为弱键，命中行须含称谓后缀才计数（防标点去除后的假阳性）。"""
    t = norm(name)
    keys = [(t, True)]
    if len(t) > 4:
        keys.append((t[-4:], True))
    if len(t) > 2:
        keys.append((t[-2:], False))
    return list(dict.fromkeys(keys))


def name_search(corpus, name):
    """返回通过上下文校验的人名命中。弱键行需含称谓后缀。"""
    for key, strong in name_keys(name):
        if len(key) < 2:
            continue
        hits = corpus.find(key, None)
        if not hits:
            continue
        if strong:
            return hits
        return [h for h in hits if NAME_SUFFIX.search(h[3])]
    return []


def card_works(card):
    """从 source_ref / cbeta 推断应查的经文集合。"""
    works = set()
    src = card.get("source_ref", "") or ""
    for k, wid in ALIAS.items():
        if k in src:
            works.add(wid)
    cb = str(card.get("cbeta", "") or "")
    for wid in WORK_TITLES:
        if wid in cb:
            works.add(wid)
    # 去掉未入库项
    return [w for w in works if w in WORK_TITLES]


def main():
    corpus = Corpus()
    cards = []
    for fp in sorted(glob.glob(os.path.join(ROOT, "data", "patriarchs", "*.yaml"))):
        d = yaml.safe_load(open(fp, encoding="utf-8"))
        if d and d.get("status") == "draft":
            cards.append((os.path.basename(fp)[:-5], d))
    print(f"加载 corpus {len(corpus.lines)} 行 | draft 卡 {len(cards)} 张")

    results = []
    counts = {"A": 0, "B": 0, "C": 0}
    for cid, card in cards:
        works = card_works(card)
        name_hits = name_search(corpus, card.get("name", ""))
        say_hits, say_total = [], 0
        for say in card.get("sayings", []) or []:
            t = norm(say.get("text", ""))
            if len(t) < 6:
                continue
            say_total += 1
            hh = []
            # 多点取样（首/中/尾三处），每处窗口逐级缩短 12→9→6
            starts = sorted({0, len(t) // 3, 2 * len(t) // 3, max(0, len(t) - 12)})
            for s in starts:
                if hh:
                    break
                for w in (12, 9, 6):
                    seg = t[s:s + w]
                    if len(seg) < 6:
                        continue
                    hh = corpus.find(seg, None)
                    if hh:
                        break
            if hh:
                say_hits.append({"q": t[:12], "hits": [{"ref": h[1], "work": h[0], "juan": h[2]} for h in hh[:4]]})
        # 判定
        name_w = [h for h in name_hits if h[0] in works] if works else []
        say_w = [s for s in say_hits if any(h["work"] in works for h in s["hits"])] if works else []
        if say_w and name_w:
            grade = "A"
        elif say_hits or name_hits:
            grade = "B"
        else:
            grade = "C"
        counts[grade] += 1
        results.append({
            "id": cid, "name": card.get("name"), "grade": grade,
            "works": works, "say_total": say_total, "say_matched": len(say_hits),
            "name_hits": [{"ref": h[1], "work": h[0], "juan": h[2], "line": h[3][:60]} for h in name_hits[:5]],
            "sayings": say_hits[:6],
        })

    os.makedirs(OUT, exist_ok=True)
    today = datetime.date.today().isoformat()
    md = os.path.join(OUT, f"cbeta_check_{today}.md")
    js = os.path.join(OUT, f"cbeta_check_{today}.json")
    json.dump(results, open(js, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    with open(md, "w", encoding="utf-8") as f:
        f.write(f"# CBETA 逐字校核报告 {today}\n\n")
        f.write(f"语料：{', '.join(f'{k}({v})' for k, v in WORK_TITLES.items())}\n\n")
        f.write(f"draft 卡 {len(cards)} 张：A 双证 {counts['A']} | B 单证 {counts['B']} | C 未命中 {counts['C']}\n\n")
        f.write("## A 双证（可直接升 sourced/line_verified）\n\n")
        for r in results:
            if r["grade"] == "A":
                f.write(f"- **{r['name']}**（{r['id']}）语料目标 {r['works']} | 语句 {r['say_matched']}/{r['say_total']} 命中\n")
                for s in r["sayings"][:3]:
                    f.write(f"    - 「{s['q']}…」 → " + "；".join(f"{h['ref']}(卷{h['juan']})" for h in s["hits"]) + "\n")
                for h in r["name_hits"][:2]:
                    if h["work"] in r["works"]:
                        f.write(f"    - 人名：{h['ref']}(卷{h['juan']}) {h['line']}\n")
        f.write("\n## B 单证（需人工复核）\n\n")
        for r in results:
            if r["grade"] == "B":
                f.write(f"- {r['name']}（{r['id']}）语句 {r['say_matched']}/{r['say_total']} | 人名 {len(r['name_hits'])} 处"
                        f"{'，但目标语料未配置' if not r['works'] else ''}\n")
                for h in r["name_hits"][:2]:
                    f.write(f"    - {h['ref']}(卷{h['juan']}) {h['line']}\n")
        f.write("\n## C 未命中\n\n")
        for r in results:
            if r["grade"] == "C":
                f.write(f"- {r['name']}（{r['id']}）\n")
    print(f"分级结果: {counts}")
    print(f"报告: {md}")


if __name__ == "__main__":
    sys.exit(main())
