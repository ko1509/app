#!/usr/bin/env python3
"""記事の Markdown を WordPress（Gutenberg）のブロックに変換する。

出力を WordPress の編集画面の「コードエディター」に貼ると、そのまま見出し・段落・リスト・表のブロックになる
（SWELL のデザインがかかる）。

使い方:  python3 md2blocks.py article.md > article.blocks.html
         cat article.md | python3 md2blocks.py -

扱う書き方:
  ## 見出し2 / ### 見出し3 / #### 見出し4（# 見出し1 はタイトルなので本文に入れない＝無視する）
  段落（空行で区切る）、**太字**、[リンク](https://...)、`コード`
  - 箇条書き、1. 番号付き（入れ子はしない）
  | 表 | …（1 行目が見出し、2 行目が |---|）
  > 引用
  [mm_status] のようなショートコードだけの行 → ショートコードのブロック
  ---（区切り線）
先頭の --- で囲まれた frontmatter は読み飛ばす。
"""
import html
import re
import sys


def inline(text: str) -> str:
    """行内の書式を HTML にする（先にエスケープしてから戻す）。"""
    codes = []

    def keep_code(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    t = re.sub(r"`([^`]+)`", keep_code, text)
    links = []

    def keep_link(m):
        links.append((m.group(1), m.group(2)))
        return f"\x01{len(links) - 1}\x01"

    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", keep_link, t)
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    for i, (label, url) in enumerate(links):
        lab = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(label, quote=False))
        t = t.replace(f"\x01{i}\x01", f'<a href="{html.escape(url, quote=True)}">{lab}</a>')
    for i, c in enumerate(codes):
        t = t.replace(f"\x00{i}\x00", f"<code>{html.escape(c, quote=False)}</code>")
    return t


def heading(level: int, text: str) -> str:
    attrs = "" if level == 2 else f' {{"level":{level}}}'
    return f"<!-- wp:heading{attrs} -->\n<h{level} class=\"wp-block-heading\">{inline(text)}</h{level}>\n<!-- /wp:heading -->"


def paragraph(text: str) -> str:
    return f"<!-- wp:paragraph -->\n<p>{inline(text)}</p>\n<!-- /wp:paragraph -->"


def listing(items, ordered: bool) -> str:
    tag = "ol" if ordered else "ul"
    attrs = ' {"ordered":true}' if ordered else ""
    inner = "".join(f"<!-- wp:list-item -->\n<li>{inline(i)}</li>\n<!-- /wp:list-item -->" for i in items)
    return f"<!-- wp:list{attrs} -->\n<{tag} class=\"wp-block-list\">{inner}</{tag}>\n<!-- /wp:list -->"


def table(rows) -> str:
    def cells(r):
        r = r.strip().strip("|")
        return [c.strip() for c in r.split("|")]

    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    th = "".join(f"<th>{inline(c)}</th>" for c in head)
    trs = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
    return (f"<!-- wp:table -->\n<figure class=\"wp-block-table\"><table class=\"has-fixed-layout\"><thead><tr>{th}</tr></thead>"
            f"<tbody>{trs}</tbody></table></figure>\n<!-- /wp:table -->")


def quote(lines) -> str:
    inner = "\n\n".join(paragraph(l) for l in lines)
    return f"<!-- wp:quote -->\n<blockquote class=\"wp-block-quote\">{inner}</blockquote>\n<!-- /wp:quote -->"


def convert(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    if lines and lines[0].strip() == "---":  # frontmatter を飛ばす
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                lines = lines[i + 1:]
                break
    out, i = [], 0
    while i < len(lines):
        ln = lines[i].rstrip()
        s = ln.strip()
        if not s:
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            if len(m.group(1)) > 1:
                out.append(heading(len(m.group(1)), m.group(2)))
            i += 1
            continue
        if re.fullmatch(r"\[[a-z_]+[^\]]*\]", s):
            out.append(f"<!-- wp:shortcode -->\n{s}\n<!-- /wp:shortcode -->")
            i += 1
            continue
        if re.fullmatch(r"-{3,}|\*{3,}", s):
            out.append('<!-- wp:separator -->\n<hr class="wp-block-separator has-alpha-channel-opacity"/>\n<!-- /wp:separator -->')
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-{2,}", lines[i + 1].strip()):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(table(rows))
            continue
        if re.match(r"^[-*]\s+", s):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]).strip())
                i += 1
            out.append(listing(items, False))
            continue
        if re.match(r"^\d+[.)]\s+", s):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+[.)]\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+[.)]\s+", "", lines[i]).strip())
                i += 1
            out.append(listing(items, True))
            continue
        if s.startswith(">"):
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(quote([x for x in q if x]))
            continue
        para = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|[-*]\s|\d+[.)]\s|\||>|\[[a-z_]+)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(paragraph("".join(para)))  # 日本語は改行をつなげる
    return "\n\n".join(out) + "\n"


if __name__ == "__main__":
    src = sys.stdin.read() if len(sys.argv) < 2 or sys.argv[1] == "-" else open(sys.argv[1], encoding="utf-8").read()
    sys.stdout.write(convert(src))
