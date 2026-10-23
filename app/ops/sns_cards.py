#!/usr/bin/env python3
"""SNS 用の図解カードを作る（写真風の画像は使わない）。夜空の黒 #0B0B10 の地に白い線と文字、
強調（accent）はオレンジ #E8481C を1か所だけ。右下に「模式図」と MIAGETABI。値は sky.py などで確かめたものだけを入れる。

使い方:  python3 sns_cards.py spec.json out.jpg
  spec の format: "x"（1200×675）| "ig"（1080×1350）。カルーセルは "slides": [spec, …] を書くと out-1.jpg, out-2.jpg … に書く。
  spec の type:
    week      … 見上げ予報   {"title":"今週の見上げ予報","range":"10/26〜11/1","rows":[{"day":"26（月）","when":"夜","text":"ISSが南西の空に4分","accent":true}]}
    direction … 方角と高さ   {"title":"明日の夜の空","sub":"東京 19:32ごろ","center":180,"points":[{"az":225,"alt":30,"label":"ISS","accent":true}],"path":[[225,10],[200,60]]}
    slide     … 1枚の説明    {"kicker":"1/5","title":"12月14日の夜、流星を見る方法","lines":["時刻：…","方角：…"],"cover":true}
    poll      … 投票の図     {"title":"打ち上げを一度見るなら？","options":["種子島で現地観覧","自宅で中継"]}
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eyecatch as ec

NIGHT, INK, ORANGE, WHITE, DIM = (11, 11, 16), (11, 11, 16), (232, 72, 28), (255, 255, 255), (150, 150, 160)
SIZE = {"x": (1200, 675), "ig": (1080, 1350)}


def fnt(kind, px):
    return ImageFont.truetype(ec.fetch(ec.FONTS[kind], os.path.basename(ec.FONTS[kind]).replace("%5B", "[").replace("%5D", "]")), int(px))


def wrap(d, text, f, maxw):
    out, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=f) > maxw and cur:
            out.append(cur); cur = ch
        else:
            cur += ch
    return out + ([cur] if cur else [])


def frame(spec):
    W, H = SIZE[spec.get("format", "x")]
    im = Image.new("RGB", (W, H), NIGHT)
    d = ImageDraw.Draw(im)
    m = round(W * .06)
    d.text((m, H - m - 18), "MIAGETABI", font=fnt("mono", 18), fill=DIM)
    lab = "模式図"
    d.text((W - m - d.textlength(lab, font=fnt("medium", 18)), H - m - 20), lab, font=fnt("medium", 18), fill=DIM)
    return im, d, W, H, m


def heading(d, spec, W, m, y, size):
    f = fnt("black", size)
    for ln in wrap(d, spec["title"], f, W - 2 * m):
        d.text((m, y), ln, font=f, fill=WHITE); y += int(size * 1.25)
    if spec.get("sub") or spec.get("range"):
        f2 = fnt("medium", int(size * .5)); d.text((m, y + 6), spec.get("sub") or spec["range"], font=f2, fill=DIM); y += int(size * .5 * 1.6)
    return y + int(size * .5)


def week(spec):
    im, d, W, H, m = frame(spec); y = heading(d, spec, W, m, m, 54 if W > 1100 else 62)
    rows = spec["rows"]; fd, ft = fnt("black", 34), fnt("medium", 34)
    avail = H - m * 2 - 40 - y; step = min(110, avail // max(1, len(rows)))
    for r in rows:
        col = ORANGE if r.get("accent") else WHITE
        d.line([(m, y), (W - m, y)], fill=(70, 70, 80), width=2)
        d.text((m, y + step * .5 - 22), r["day"] + (" " + r["when"] if r.get("when") else ""), font=fd, fill=col)
        tx = m + (330 if W > 1100 else 300)
        for i, ln in enumerate(wrap(d, r["text"], ft, W - m - tx)[:2]):
            d.text((tx, y + 10 + i * 40 if len(wrap(d, r["text"], ft, W - m - tx)) > 1 else y + step * .5 - 22), ln, font=ft, fill=col)
        y += step
    d.line([(m, y), (W - m, y)], fill=(70, 70, 80), width=2)
    return im


def direction(spec):
    im, d, W, H, m = frame(spec); y = heading(d, spec, W, m, m, 54 if W > 1100 else 62)
    c = spec.get("center", 180); x0, x1 = m, W - m; y1 = H - m - 110; y0 = max(y + 10, m + 200)
    span = 180.0; px = lambda az: x0 + ((((az - c + 180) % 360) - 180) / span + .5) * (x1 - x0)
    py = lambda alt: y1 - alt / 90 * (y1 - y0)
    for alt in (30, 60, 90):
        d.line([(x0, py(alt)), (x1, py(alt))], fill=(50, 50, 60), width=1); d.text((x0 + 4, py(alt) - 22), f"{alt}°", font=fnt("mono", 18), fill=DIM)
    d.line([(x0, y1), (x1, y1)], fill=WHITE, width=3)
    names = {0: "北", 45: "北東", 90: "東", 135: "南東", 180: "南", 225: "南西", 270: "西", 315: "北西"}
    for az, nm in names.items():
        x = px(az)
        if x0 <= x <= x1:
            d.line([(x, y1), (x, y1 + 12)], fill=WHITE, width=3); d.text((x - 16, y1 + 18), nm, font=fnt("medium", 28), fill=WHITE)
    pts = [(px(a), py(h)) for a, h in spec.get("path", [])]
    if len(pts) > 1: d.line(pts, fill=WHITE, width=4)
    for p in spec["points"]:
        x, yy = px(p["az"]), py(p["alt"]); col = ORANGE if p.get("accent") else WHITE
        d.ellipse([x - 12, yy - 12, x + 12, yy + 12], fill=col)
        lf = fnt("medium", 32); tw = d.textlength(p["label"], font=lf)
        d.text((min(x + 20, x1 - tw), yy - 44), p["label"], font=lf, fill=col)
    return im


def slide(spec):
    im, d, W, H, m = frame(spec)
    if spec.get("kicker"): d.text((m, m), spec["kicker"], font=fnt("mono", 26), fill=ORANGE if spec.get("cover") else DIM)
    cover = spec.get("cover"); size = (96 if W < 1100 else 80) if cover else (64 if W < 1100 else 52)
    y = int(H * (.3 if cover else .2))
    f = fnt("black", size)
    for ln in wrap(d, spec["title"], f, W - 2 * m):
        d.text((m, y), ln, font=f, fill=WHITE); y += int(size * 1.3)
    y += 30; fl = fnt("medium", 52 if W < 1100 else 40)
    for i, line in enumerate(spec.get("lines", [])):
        col = ORANGE if (spec.get("accentLine") == i) else WHITE
        for ln in wrap(d, line, fl, W - 2 * m):
            d.text((m, y), ln, font=fl, fill=col); y += int(fl.size * 1.5)
        y += 14
    return im


def poll(spec):
    im, d, W, H, m = frame(spec); y = heading(d, spec, W, m, m, 58 if W > 1100 else 66)
    f = fnt("medium", 40); n = len(spec["options"]); step = min(120, (H - m * 2 - 60 - y) // max(1, n))
    for o in spec["options"]:
        d.rounded_rectangle([m, y, W - m, y + step - 18], radius=12, outline=WHITE, width=3)
        d.text((m + 28, y + (step - 18) / 2 - 24), o, font=f, fill=WHITE); y += step
    return im


MAKE = {"week": week, "direction": direction, "slide": slide, "poll": poll}


def render(spec, out):
    fmt = spec.get("format", "x")
    items = spec.get("slides")
    if items:
        base, ext = os.path.splitext(out); outs = []
        for i, s in enumerate(items, 1):
            s = {"format": fmt, **s, "kicker": s.get("kicker") or f"{i}/{len(items)}"}
            p = f"{base}-{i}{ext}"; ec.save_jpeg(MAKE[s.get("type", "slide")](s), p); outs.append(p)
        return outs
    ec.save_jpeg(MAKE[spec["type"]](spec), out); return [out]


if __name__ == "__main__":
    print("ok", *render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2] if len(sys.argv) > 2 else "card.jpg"))
