#!/usr/bin/env python3
"""从 CBETA XML P5（.cache/xml-p5 sparse checkout）抽取纯文本，供逐字校核用。

输出 sources/<id>.txt，每行格式：
    <canonical_ref>\t<卷号>\t<正文>
canonical_ref 形如 T51n2076_p0255a11（CBETA 引用规范格式）。
正文为去除全部 XML 标记后的文字（保留原文标点）。

用法: python3 tools/extract_cbeta.py
"""
import re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, ".cache", "xml-p5")
OUT = os.path.join(ROOT, "sources")

# 已核验标题的文本清单（id -> (repo 路径, 标题)）
WORKS = {
    "T51n2076": ("T/T51/T51n2076.xml", "景德傳燈錄"),
    "T51n2077": ("T/T51/T51n2077.xml", "續傳燈錄"),
    "X80n1565": ("X/X80/X80n1565.xml", "五燈會元"),
    "X68n1315": ("X/X68/X68n1315.xml", "古尊宿語錄"),
    "X78n1556": ("X/X78/X78n1556.xml", "建中靖國續燈錄"),
    "X79n1559": ("X/X79/X79n1559.xml", "嘉泰普燈錄"),
    "T47n1985": ("T/T47/T47n1985.xml", "鎮州臨濟慧照禪師語錄"),
}

TAG = re.compile(r"<[^>]+>")
# 属性顺序无关（T 部 n 在前，X 部 ed 在前）
LB = re.compile(r'<lb\b[^>]*\bn="([0-9a-z]+)"[^>]*/?>')
JUAN = re.compile(r'<milestone\b[^>]*\bn="(\d+)"[^>]*unit="juan"[^>]*/?>|'
                  r'<milestone\b[^>]*\bunit="juan"[^>]*\bn="(\d+)"[^>]*/?>')


def extract(work_id, rel):
    fp = os.path.join(SRC, rel)
    if not os.path.exists(fp):
        print(f"[跳过] {work_id}: {rel} 不在 sparse checkout 中")
        return None
    xml = open(fp, encoding="utf-8").read()
    body = xml[xml.find("<body"):]
    # 按行锚点/卷切分，保留分隔符（属性顺序无关）
    parts = re.split(r'(<milestone\b[^>]*unit="juan"[^>]*/>|<milestone\b[^>]*\bn="\d+"[^>]*unit="juan"[^>]*/>|<milestone\b[^>]*unit="juan"[^>]*\bn="\d+"[^>]*/>|<lb\b[^>]*/?>)', body)
    cur_juan, cur_ref = 0, None
    buf = []
    out = []  # (ref, juan, text)
    for seg in parts:
        m = JUAN.match(seg)
        if m:
            cur_juan = int(m.group(1) or m.group(2))
            continue
        m = LB.match(seg)
        if m:
            if cur_ref is not None:
                txt = TAG.sub("", "".join(buf)).strip()
                if txt:
                    out.append((cur_ref, cur_juan, txt))
            cur_ref = f"{work_id}_p{m.group(1)}"
            buf = []
            continue
        buf.append(seg)
    if cur_ref is not None:
        txt = TAG.sub("", "".join(buf)).strip()
        if txt:
            out.append((cur_ref, cur_juan, txt))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for wid, (rel, title) in WORKS.items():
        lines = extract(wid, rel)
        if lines is None:
            continue
        dst = os.path.join(OUT, f"{wid}.txt")
        with open(dst, "w", encoding="utf-8") as f:
            f.write(f"# {wid} {title}\tCBETA XML P5\t{len(lines)} 行\n")
            for ref, juan, txt in lines:
                f.write(f"{ref}\t{juan}\t{txt}\n")
        total += len(lines)
        print(f"[ok] {wid} {title}: {len(lines)} 行 -> {os.path.relpath(dst, ROOT)}")
    print(f"合计 {total} 行")


if __name__ == "__main__":
    sys.exit(main())
