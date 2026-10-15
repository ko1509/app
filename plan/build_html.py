"""plan/ の Markdown を 1 枚の HTML（アーティファクト用）にまとめる。

使い方: PYTHONPATH=<markdown を入れた場所> python3 plan/build_html.py
出力: plan/index.html
"""
import html
import pathlib
import re

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLAN = ROOT / "plan"

SECTIONS = [
    ("s1a", "1-A", "市場調査：今後12か月のイベント", PLAN / "01a-market-events.md"),
    ("s1b", "1-B", "競合と手薄な部分", PLAN / "01b-competitors.md"),
    ("s2", "2", "サイト設計", PLAN / "02-site-design.md"),
    ("s3", "3", "最初に書く記事20本", PLAN / "03-first-20-articles.md"),
    ("s4a", "4-A", "テンプレート：打ち上げ観覧", PLAN / "templates/01-launch-viewing.md"),
    ("s4b", "4-B", "テンプレート：天体イベント", PLAN / "templates/02-sky-event.md"),
    ("s4c", "4-C", "テンプレート：宇宙スポット見学", PLAN / "templates/03-space-spot.md"),
    ("s5", "5", "90日間の行動計画", PLAN / "04-90day-plan.md"),
    ("s6", "付録A", "AIで定型化するプロンプト", PLAN / "05-ai-workflow.md"),
    ("s7", "付録B", "サイト構築の手順（WordPress＋SWELL）", ROOT / "site/README.md"),
]


def convert(md_text: str) -> str:
    # リポジトリ内のファイルへのリンクはページ上では開けないので、文字だけ残す
    md_text = re.sub(r"\[([^\]]+)\]\((?!https?://)[^)]+\)", r"\1", md_text)
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])
    # 各ファイルの # をこのページでは h2 にする（h1 はページの題名だけ）
    for n in (4, 3, 2, 1):
        body = re.sub(rf"<(/?)h{n}>", rf"<\1h{n + 1}>", body)
    body = re.sub(r"<h2>.*?</h2>\s*", "", body, count=1)  # 章の題名は自前で出す
    body = body.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    # 本文中の生の URL もリンクにする（コードの中は除く）
    parts = re.split(r"(<pre>.*?</pre>|<code>.*?</code>|<a [^>]*>.*?</a>)", body, flags=re.S)
    for i, p in enumerate(parts):
        if i % 2 == 0:
            parts[i] = re.sub(
                r"(https?://[^\s<>）」、。]+)",
                lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(1)}</a>',
                p,
            )
    return "".join(parts)


def main() -> None:
    toc = []
    secs = []
    for sid, num, title, path in SECTIONS:
        toc.append(f'<li><a href="#{sid}"><span class="n">{html.escape(num)}</span>{html.escape(title)}</a></li>')
        body = convert(path.read_text(encoding="utf-8"))
        secs.append(
            f'<section class="sec" id="{sid}"><p class="eyebrow">{html.escape(num)}</p>'
            f"<h2>{html.escape(title)}</h2>{body}</section>"
        )
    tpl = (PLAN / "page_template.html").read_text(encoding="utf-8")
    out = tpl.replace("{{TOC}}", "\n".join(toc)).replace("{{SECTIONS}}", "\n".join(secs))
    (PLAN / "index.html").write_text(out, encoding="utf-8")
    print("wrote", PLAN / "index.html", len(out), "bytes")


if __name__ == "__main__":
    main()
