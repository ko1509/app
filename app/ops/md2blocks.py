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
  [shortcode] のようなショートコードだけの行 → ショートコードのブロック
  ---（区切り線）
  「最終確認：…」で始まる段落 → <p class="mg-verified">（サイトの最終確認の一行）
サイトの部品（運営マニュアル「デザインのルール」。::: で囲む）:
  :::info H3 F10 / MMX          → 要点ボックス mg-info（見出しの右に QUICK FACTS）
  今の状況: [go] 予定どおり（…）  ← 「項目: 値」を1行ずつ。値の頭の [go] [delay] [sky] [stop] は状況の札
  打ち上げ: 2026年10月20日（火）4時41分
  :::
  :::point いちばんのおすすめ   → 強調 mg-point（1記事に2つまで）
  本文
  :::
  :::src                        → 出典 mg-src（「- 名前：URL」を1行ずつ）
  :::history                    → 更新履歴 mg-history（「- 2026-10-16　公開用に作成」）
  :::fig FIG.01 キャプション     → 図 mg-fig。中に「@figures/timeline.svg」のように SVG のファイルを1行（Markdown のファイルからの相対パス）
  （figures.py で作る。キャプションには「模式図」などの注記を入れる）
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


STATUS_TAG = {"go": ("-go", "GO"), "delay": ("-delay", "DELAY"), "sky": ("", "SKY"), "stop": ("-stop", "STOP"), "done": ("-done", "DONE"), "open": ("-go", "OPEN")}


def html_block(markup: str) -> str:
    return f"<!-- wp:html -->\n{markup}\n<!-- /wp:html -->"


def info_box(head: str, lines) -> str:
    rows = []
    for ln in lines:
        if ":" not in ln and "：" not in ln:
            continue
        k, v = re.split(r"[:：]", ln, maxsplit=1)
        v = v.strip()
        tag = ""
        m = re.match(r"^\[(go|delay|sky|stop|done|open)\]\s*", v)
        if m:
            cls, label = STATUS_TAG[m.group(1)]
            tag = f'<span class="mg-status {cls}">{label}</span>'
            v = v[m.end():]
        rows.append(f"<dt>{html.escape(k.strip(), quote=False)}</dt><dd>{tag}{inline(v)}</dd>")
    head_html = html.escape(head.strip() or "INFO", quote=False)
    return html_block(f'<div class="mg-info"><div class="mg-info__head">{head_html}<span>QUICK FACTS</span></div><dl>{"".join(rows)}</dl></div>')


def point_box(title: str, lines) -> str:
    body = "".join(inline(x) for x in lines)
    return html_block(f'<div class="mg-point"><b>{html.escape(title.strip(), quote=False)}</b>{body}</div>')


def list_box(cls: str, title: str, lines) -> str:
    items = []
    for ln in lines:
        t = re.sub(r"^[-*]\s+", "", ln.strip())
        if not t:
            continue
        # 「名前：URL」の URL はリンクにする
        t = inline(t)
        t = re.sub(r'(?<!href=")(https?://[^\s<]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', t)
        items.append(f"<li>{t}</li>")
    return html_block(f'<div class="{cls}"><b>{html.escape(title, quote=False)}</b><ul>{"".join(items)}</ul></div>')


BASE_DIR = "."


def figure(arg: str, body) -> str:
    m = re.match(r"^(FIG\.?\s*\d+)\s*(.*)$", arg.strip())
    num, cap = (m.group(1), m.group(2)) if m else ("", arg.strip())
    svgs = []
    for ln in body:
        if ln.startswith("@"):
            import os
            svg = open(os.path.join(BASE_DIR, ln[1:].strip()), encoding="utf-8").read()
            svg = re.sub(r"<\?xml[^>]*>", "", svg)
            svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
            if "<script" in svg or "/*" in svg:
                raise SystemExit("図に <script> や /* */ が入っています（WAF で保存できません）")
            svgs.append(svg.strip())
    capt = (f"<b>{html.escape(num)}</b>" if num else "") + inline(cap)
    return html_block(f'<figure class="mg-fig">{"".join(svgs)}<figcaption>{capt}</figcaption></figure>')


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
        m = re.match(r"^:::(info|point|src|history|fig)\s*(.*)$", s)
        if m:
            kind, arg = m.group(1), m.group(2)
            body = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                if lines[i].strip():
                    body.append(lines[i].strip())
                i += 1
            i += 1
            if kind == "info":
                out.append(info_box(arg, body))
            elif kind == "point":
                out.append(point_box(arg, body))
            elif kind == "fig":
                out.append(figure(arg, body))
            elif kind == "src":
                out.append(list_box("mg-src", arg or "出典（すべて最終確認日に閲覧）", body))
            else:
                out.append(list_box("mg-history", arg or "更新履歴", body))
            continue
        if s.startswith("最終確認："):
            out.append(f'<!-- wp:paragraph {{"className":"mg-verified"}} -->\n<p class="mg-verified">{inline(s)}</p>\n<!-- /wp:paragraph -->')
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
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|[-*]\s|\d+[.)]\s|\||>|\[[a-z_]+|:::|最終確認：)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(paragraph("".join(para)))  # 日本語は改行をつなげる
    return "\n\n".join(out) + "\n"


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] != "-":
        import os
        BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[1]))
        src = open(sys.argv[1], encoding="utf-8").read()
    else:
        src = sys.stdin.read()
    sys.stdout.write(convert(src))
