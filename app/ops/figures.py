#!/usr/bin/env python3
"""ミアゲタビの記事に入れる図（SVG）を作る。運営マニュアル「イラストと図の入れ方」に合わせる：
線画、黒 #111・線 1.5〜2px、塗りは白と灰色、いちばん伝えたい1か所だけオレンジ #E8481C、
夜空の図は #0B0B10 の地に白。文字は少なく大きく。英字ラベルは IBM Plex Mono。
コメントや <script> は入れない（サーバーの WAF で保存が止まるため）。数字は sky.py で出した値だけを使う。

使い方:  python3 figures.py spec.json out.svg
spec の type:
  timeline … 当日の動き   {"type":"timeline","title":"TIMELINE","items":[{"time":"3:46","label":"中継が始まる"},
                              {"time":"4:41","label":"打ち上げ","accent":true}, ...]}
  skydir   … 方角と高さ   {"type":"skydir","title":"東京から見た空（4:47ごろ）","points":[{"az":200,"alt":15,"label":"ロケット","accent":true}],
                              "path":[[190,10],[200,15],[215,19]], "center":180}
             az は方位角（北0°・東90°・南180°・西270°）、alt は地平線からの高さ（度）。center は図の真ん中の方角
  distance … 発射台からの距離 {"type":"distance","title":"射点からの距離","origin":"発射台","items":[{"name":"恵美之江展望公園","km":3.5}, ...]}
"""
import html, json, math, sys

INK, ORANGE, GRAY, NIGHT = "#111", "#E8481C", "#6b6b6b", "#0B0B10"
JP = "Zen Kaku Gothic New, Noto Sans JP, sans-serif"
EN = "IBM Plex Mono, ui-monospace, monospace"
e = lambda s: html.escape(str(s), quote=True)


def svg(w, h, body, bg=None, label=""):
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{e(label)}" '
            f'style="max-width:{w}px;height:auto;display:block;margin:0 auto">{rect}{body}</svg>')


def t(x, y, s, size=16, fill=INK, anchor="start", font=JP, weight=500, ls=0):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}">{e(s)}</text>')


def timeline(spec):
    items = spec["items"]; w = 720; top = 64; step = 58; h = top + step * (len(items) - 1) + 36
    b = [t(24, 34, spec.get("title", "TIMELINE"), 13, GRAY, font=EN, weight=600, ls=3)]
    x = 150
    b.append(f'<line x1="{x}" y1="{top - 8}" x2="{x}" y2="{top + step * (len(items) - 1) + 8}" stroke="{INK}" stroke-width="2"/>')
    for i, it in enumerate(items):
        y = top + step * i; acc = it.get("accent")
        b.append(t(x - 22, y + 7, it["time"], 22, ORANGE if acc else INK, "end", EN, 600))
        b.append(f'<circle cx="{x}" cy="{y}" r="{9 if acc else 6}" fill="{ORANGE if acc else "#fff"}" stroke="{ORANGE if acc else INK}" stroke-width="2"/>')
        b.append(t(x + 24, y + 7, it["label"], 19, INK, weight=900 if acc else 500))
    return svg(w, h, "".join(b), "#fff", spec.get("title", "タイムライン"))


DIRS = ["北", "北北東", "北東", "東北東", "東", "東南東", "南東", "南南東", "南", "南南西", "南西", "西南西", "西", "西北西", "北西", "北北西"]


def skydir(spec):
    w, h = 760, 420; left, right, base, top = 50, 710, 340, 50
    c = spec.get("center", 180); span = spec.get("span", 180)
    amax = spec.get("altMax", max([p["alt"] for p in spec.get("points", [])] + [a for _, a in spec.get("path", [])] + [30]) + 10)
    amax = int(math.ceil(amax / 10) * 10)
    X = lambda az: left + ((((az - c + 540) % 360) - 180) / span + 0.5) * (right - left)
    Y = lambda alt: base - alt / amax * (base - top)
    b = [t(24, 32, spec.get("title", "SKY"), 15, "#fff", weight=900)]
    for a in range(10, amax + 1, 10):  # 高さの目盛り
        b.append(f'<line x1="{left}" y1="{Y(a):.1f}" x2="{right}" y2="{Y(a):.1f}" stroke="#fff" stroke-opacity=".18" stroke-dasharray="2 6"/>')
        b.append(t(right + 6, Y(a) + 4, f"{a}°", 12, "#fff", font=EN, weight=500))
    b.append(f'<line x1="{left}" y1="{base}" x2="{right}" y2="{base}" stroke="#fff" stroke-width="2"/>')
    for i, name in enumerate(DIRS):  # 16方位のうち、図に入るものに目盛り
        az = i * 22.5; x = X(az)
        if left - 1 <= x <= right + 1 and abs(((az - c + 540) % 360) - 180) <= span / 2:
            big = i % 2 == 0
            b.append(f'<line x1="{x:.1f}" y1="{base}" x2="{x:.1f}" y2="{base + (10 if big else 5)}" stroke="#fff"/>')
            if big: b.append(t(x, base + 30, name, 16, "#fff", "middle", weight=900 if i % 4 == 0 else 500))
    if spec.get("path"):
        pts = " ".join(f"{X(a):.1f},{Y(al):.1f}" for a, al in spec["path"])
        b.append(f'<polyline points="{pts}" fill="none" stroke="#fff" stroke-width="2" stroke-dasharray="3 5"/>')
    for p in spec.get("points", []):
        x, y = X(p["az"]), Y(p["alt"]); acc = p.get("accent")
        b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{9 if acc else 5}" fill="{ORANGE if acc else "#fff"}"/>')
        if p.get("label"): b.append(t(x + 14, y - 10, p["label"], 15, "#fff", weight=900 if acc else 500))
    b.append(t(24, h - 18, spec.get("note", "高さ10°＝腕を伸ばしたこぶし1個分（模式図）"), 12, "#fff", font=JP))
    return svg(w, h, "".join(b), NIGHT, spec.get("title", "方角と高さ"))


def distance(spec):
    items = sorted(spec["items"], key=lambda x: x["km"]); w = 720; top = 70; step = 46; h = top + step * len(items) + 40
    kmax = max(i["km"] for i in items); kmax = math.ceil(kmax / 5) * 5 or 5
    x0, x1 = 40, 600; X = lambda km: x0 + km / kmax * (x1 - x0)
    b = [t(24, 32, spec.get("title", "DISTANCE"), 15, INK, weight=900)]
    b.append(f'<rect x="{x0 - 7}" y="{top - 30}" width="14" height="14" fill="{ORANGE}"/>')
    b.append(t(x0 + 14, top - 18, spec.get("origin", "発射台"), 13, INK, weight=900))
    for i, it in enumerate(items):
        y = top + step * i
        b.append(f'<line x1="{x0}" y1="{y}" x2="{X(it["km"]):.1f}" y2="{y}" stroke="{INK}" stroke-width="2"/>')
        b.append(f'<circle cx="{X(it["km"]):.1f}" cy="{y}" r="5" fill="{INK}"/>')
        b.append(t(X(it["km"]) + 12, y + 5, f'{it["name"]}  {it["km"]:g}km', 15, INK))
    yb = top + step * len(items)
    b.append(f'<line x1="{x0}" y1="{yb}" x2="{x1}" y2="{yb}" stroke="{GRAY}"/>')
    for k in range(0, kmax + 1, 5 if kmax > 10 else 1):
        b.append(f'<line x1="{X(k):.1f}" y1="{yb}" x2="{X(k):.1f}" y2="{yb + 6}" stroke="{GRAY}"/>')
        b.append(t(X(k), yb + 22, f"{k}km", 11, GRAY, "middle", EN))
    return svg(w, h, "".join(b), "#fff", spec.get("title", "距離"))


KINDS = {"timeline": timeline, "skydir": skydir, "distance": distance}

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = KINDS[spec["type"]](spec)
    assert "<script" not in out and "/*" not in out and "<!--" not in out
    open(sys.argv[2] if len(sys.argv) > 2 else "figure.svg", "w", encoding="utf-8").write(out)
    print("ok")
