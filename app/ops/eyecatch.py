#!/usr/bin/env python3
"""ミアゲタビのアイキャッチ（1200×630）を作る。写真風の CG の背景に、記事のタイトルを雑誌風に組む。

使い方:  python3 eyecatch.py spec.json out.jpg
spec.json の例:
  {"title": "【10/20 4:41】H3ロケット10号機（火星探査機MMX）を見る方法｜家の近くの空・中継・種子島",
   "category": "launch", "kicker": "H3 F10 / MMX", "date": "2026.10.20 TUE", "time": "04:41 JST",
   "headline": "H3ロケット10号機を見る", "seed": 11,
   "composition": {"tone": "dawn", "ground": "sea", "horizon": 0.76, "motifs": [{"type": "trail", "x": 0.52, "height": 0.50, "plume": true}]}}
（spec の項目のくわしい説明は ops/article-manual.md の 5-5）

- title: 記事のタイトルをそのまま。先頭の【…】は小見出しに、「｜」より後ろは副題になる
- category: launch（打ち上げ）| sky（天体）| spot（宇宙スポット）| gear（機材）
- format: eyecatch（1200×630。標準）| x（X の投稿画像 1200×675）| ig（Instagram の投稿画像 1080×1350）
- label: 左上の英字ラベル（省略するとカテゴリ。SNS では EVENT・COLUMN・TONIGHT など）
- bigdate / bigdate_sub: イベントの日付を大きく（例 "10.20" / "TUE 04:41 JST"）。handle: 下に小さく入るアカウント名
- en: 英語の一文（短く。標準の型では見出しの上に斜体で小さく入る）
- layout: cinema（標準。下に大きく日本語の見出し）| panel（右に黒い帯）。transit（英語を大きく組む型）は使わない（指定しても cinema になる）
- 背景はフィルム調の色・かすみ・光漏れ（film: false で無し）。composition の項目は ops/article-manual.md の 5-5
- scene: 省略するとカテゴリで決まる。sea（海辺の長時間露光）| startrail（星の軌跡）| dawn（夜明け前の丘）
         | meteor（流星）| moon（月）| observatory（天文台のドーム）| tripod（三脚と星空）
- date / time: 入れると下に出る（延期の多い打ち上げは、日付が変わったら作り直す）
文節の切れ目で改行するため、先に pip install budoux を実行しておく（無くても動くが、改行が1文字単位になる）。
背景はすべてプログラムで描いた CG（写真ではない）なので、右下に「CG ILLUSTRATION」と入れる。
実在のロケットの形や、ロゴ・特定の人物は描かない（人は顔の無い影だけ）。ロケットの光跡は1本、流星は1〜3本まで。
"""
import json, os, re, sys, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT_W, OUT_H = 1200, 630
S = 2  # 2倍で描いて縮める（なめらかにするため）
W, H = OUT_W * S, OUT_H * S
ORANGE = (232, 72, 28)
CACHE = os.path.expanduser("~/.cache/miagetabi")
FONTS = {
    "black": "ofl/zenkakugothicnew/ZenKakuGothicNew-Black.ttf",
    "medium": "ofl/zenkakugothicnew/ZenKakuGothicNew-Medium.ttf",
    "mono": "ofl/ibmplexmono/IBMPlexMono-SemiBold.ttf",
    "mincho": "ofl/shipporimincho/ShipporiMincho-SemiBold.ttf",
    "serif_i": "ofl/cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf",
}
LOGO_URL = "https://miagetabi.space/wp-content/uploads/2026/10/miagetabi-logo-header.png"


def fetch(rel_or_url, name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        url = rel_or_url if rel_or_url.startswith("http") else "https://raw.githubusercontent.com/google/fonts/main/" + rel_or_url
        urllib.request.urlretrieve(url, path)
    return path


def font(kind, size, weight=None):
    f = ImageFont.truetype(fetch(FONTS[kind], os.path.basename(FONTS[kind]).replace("%5B", "[").replace("%5D", "]")), int(size * S))
    if weight:
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f


def logo_white(height):
    im = Image.open(fetch(LOGO_URL, "logo-header.png")).convert("RGBA")
    a = np.asarray(im).astype(np.int16)
    ink = (a[..., 3] > 0) & ~((a[..., 0] > 150) & (a[..., 1] < 140))  # 黒い部分だけ白に（オレンジはそのまま）
    a[ink, 0:3] = 255
    im = Image.fromarray(a.astype(np.uint8), "RGBA")
    h = int(height * S)
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


# ---------- 背景（CG） ----------
class Scene:
    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)
        self.yy = np.linspace(0, 1, H)[:, None] * np.ones((1, W), np.float32)

    def blur(self, a, r):
        im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
        return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255

    def noise(self, scales=(220, 90, 40, 16), w=(1, .6, .35, .2)):
        out = np.zeros((H, W), np.float32)
        for s, k in zip(scales, w):
            out += k * self.blur(self.rng.random((H, W)).astype(np.float32), s / 4)
        out -= out.min()
        return out / out.max()

    @staticmethod
    def lerp(c1, c2, t):
        return np.array(c1)[None, None, :] * (1 - t[..., None]) + np.array(c2)[None, None, :] * t[..., None]

    def stars(self, img, n, ymax, bright=1.0):
        lay = np.zeros((H, W), np.float32)
        xs = self.rng.integers(0, W, n); ys = self.rng.integers(0, max(1, int(ymax)), n)
        lay[ys, xs] = np.maximum(lay[ys, xs], self.rng.power(9, n) ** 2 * bright)
        glow = self.blur(lay, 1.2) * 3.0 + self.blur(lay, 4) * 1.2
        fade = np.clip((ymax - np.arange(H)) / (ymax * 0.35), 0, 1)[:, None]
        return img + ((lay + glow) * fade)[..., None] * np.array([1, 1, 1.05])

    def milkyway(self, img, offset=-380, tint=(.20, .19, .26)):
        band = np.exp(-((np.arange(W)[None, :] * 0.55 - np.arange(H)[:, None] + offset) / 260.0) ** 2)
        return img + (self.noise() ** 2.2 * band)[..., None] * np.array(tint)

    def streak(self, img, pts, core=(1, .95, .85), halo=(1, .45, .12), width=6, glow=46, strength=1.0, ramp=0.0):
        lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay); n = len(pts)
        for i in range(n - 1):
            t = i / (n - 1)
            d.line([pts[i], pts[i + 1]], fill=int(255 * ((1 - ramp) + ramp * min(1, t * 2.2))), width=width)
        a = np.asarray(lay).astype(np.float32) / 255
        g1 = self.blur(a, glow / 6); g2 = self.blur(a, glow)
        return img + strength * (a[..., None] * np.array(core) + g1[..., None] * np.array(halo) * 1.6 + g2[..., None] * np.array(halo) * 1.4)

    @staticmethod
    def bez(p0, p1, p2, p3, n=400):
        t = np.linspace(0, 1, n)[:, None]; P = [np.array(p, float) for p in (p0, p1, p2, p3)]
        pts = (1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t ** 2 * P[2] + t ** 3 * P[3]
        return [tuple(p) for p in pts]

    def silhouette(self, img, poly, color=(.006, .008, .014), soften=0):
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
        if soften: m = m.filter(ImageFilter.GaussianBlur(soften))
        a = np.asarray(m).astype(np.float32)[..., None] / 255
        return img * (1 - a) + a * np.array(color)

    def night(self, top=(.012, .018, .04), bottom=(.08, .13, .24), hz=0.74):
        return self.lerp(top, bottom, np.clip(self.yy / hz, 0, 1) ** 1.6)

    def ridge(self, base, amp=60, x0=0, x1=None, step=8):
        x1 = W if x1 is None else x1
        xs = np.arange(x0, x1 + step, step)
        prof = base + amp * np.sin(xs / 430) + amp * .5 * np.sin(xs / 190 + 1)
        return [(0, H)] + [(float(x), float(p)) for x, p in zip(xs, prof)] + [(W, H)]

    # 打ち上げ：海辺の長時間露光
    def sea(self, side=1):
        hz = int(H * 0.74)
        img = self.night()
        warm = np.exp(-(((np.arange(W)[None, :] - W * (0.15 if side > 0 else 0.85)) / (W * 0.35)) ** 2)) * np.exp(-((self.yy * H - hz) / (H * 0.09)) ** 2)
        img += warm[..., None] * np.array([.22, .10, .04])
        img = self.milkyway(img)
        img = self.stars(img, 3200, hz, 1.1)
        x0 = W * (0.60 if side > 0 else 0.40)
        pts = self.bez((x0, hz), (x0 + side * W * .02, hz - 380), (x0 + side * W * .10, hz - 760), (x0 + side * W * .33, hz - 930))
        img = self.streak(img, pts, ramp=0.55)
        ref = np.exp(-((np.arange(W)[None, :] - x0) / (W * 0.012)) ** 2) * np.ones((H, 1))
        wav = self.noise((30, 12, 6), (1, .7, .5))
        seac = self.lerp((.05, .08, .14), (.01, .015, .03), np.clip((self.yy - 0.74) / 0.26, 0, 1))
        seac = seac + (ref * (0.25 + 0.6 * wav))[..., None] * np.array([1, .5, .18]) * np.exp(-((self.yy * H - hz) / (H * 0.18)))[..., None]
        img = np.where((np.arange(H) >= hz)[:, None, None], seac, img)
        xs = np.arange(0, int(W * 0.42), 8)
        prof = hz - 80 - 120 * np.exp(-((xs - W * 0.12) / (W * 0.11)) ** 2) - 40 * np.sin(xs / 57) * np.exp(-xs / 700) + (xs / (W * 0.42)) ** 2 * 90
        poly = [(0, hz + 2)] + [(float(x), float(p)) for x, p in zip(xs, prof)] + [(W * 0.42, hz + 2)]
        if side < 0: poly = [(W - x, y) for x, y in poly]
        return self.silhouette(img, poly)

    # 打ち上げ：星の軌跡
    def startrail(self):
        img = self.lerp((.01, .012, .03), (.05, .07, .13), np.clip(self.yy, 0, 1) ** 1.4)
        lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay); cx, cy = W * 0.80, -H * 0.15
        for _ in range(620):
            rad = self.rng.uniform(80, W * 1.1); a0 = self.rng.uniform(0, 2 * np.pi)
            d.arc((cx - rad, cy - rad, cx + rad, cy + rad), np.degrees(a0), np.degrees(a0 + 0.22), fill=int(self.rng.power(5) * 255), width=2)
        a = np.asarray(lay).astype(np.float32) / 255
        img = img + (a + self.blur(a, 2) * 1.5)[..., None] * np.array([.85, .9, 1.0]) * 0.9
        img = self.streak(img, self.bez((W * .22, H * .86), (W * .25, H * .55), (W * .33, H * .28), (W * .50, H * .10)), width=7, glow=52, strength=1.1, ramp=0.4)
        return self.silhouette(img, self.ridge(H * 0.86, 14), (.004, .005, .01))

    # 夜明け前の丘
    def dawn(self, trail=True):
        t = np.clip(self.yy / 0.8, 0, 1)
        c0, c1, c2, c3 = (.01, .02, .06), (.10, .10, .30), (.55, .30, .40), (.98, .55, .28)
        img = np.where((t < .55)[..., None], self.lerp(c0, c1, t / .55),
                       np.where((t < .85)[..., None], self.lerp(c1, c2, (t - .55) / .30), self.lerp(c2, c3, np.clip((t - .85) / .15, 0, 1))))
        img = self.stars(img, 2600, int(H * 0.6), 0.8)
        if trail:
            img = self.streak(img, self.bez((W * .30, H * .80), (W * .36, H * .55), (W * .50, H * .30), (W * .78, H * .17)),
                              core=(1, .97, .9), halo=(1, .55, .25), width=4, glow=34, strength=.95, ramp=0.6)
        xs = np.arange(0, W + 8, 8)
        prof = H * 0.80 + 60 * np.sin(xs / 430) + 30 * np.sin(xs / 190 + 1) - 140 * np.exp(-((xs - W * 0.70) / (W * 0.22)) ** 2)
        return self.silhouette(img, [(0, H)] + [(float(x), float(p)) for x, p in zip(xs, prof)] + [(W, H)], (.02, .015, .03), 1)

    # 天体：流星（放射点から飛び出す）
    def meteor(self):
        img = self.night(hz=0.82)
        img = self.milkyway(img, offset=-200)
        img = self.stars(img, 3600, H * 0.82, 1.1)
        rx, ry = W * self.rng.uniform(.62, .78), H * self.rng.uniform(.12, .22)
        for _ in range(7):
            ang = self.rng.uniform(0, 2 * np.pi); r0 = self.rng.uniform(120, 420); ln = self.rng.uniform(160, 420)
            p0 = (rx + np.cos(ang) * r0, ry + np.sin(ang) * r0); p1 = (rx + np.cos(ang) * (r0 + ln), ry + np.sin(ang) * (r0 + ln))
            pts = [(p0[0] + (p1[0] - p0[0]) * k / 40, p0[1] + (p1[1] - p0[1]) * k / 40) for k in range(41)]
            img = self.streak(img, pts, core=(.95, .98, 1), halo=(.45, .6, 1), width=3, glow=14, strength=self.rng.uniform(.5, .95), ramp=0.9)
        return self.silhouette(img, self.ridge(H * 0.83, 40), (.006, .008, .014), 1)

    # 天体：月
    def moon(self):
        img = self.night(hz=0.8)
        img = self.stars(img, 1400, H * 0.8, 0.7)
        cx, cy, r = W * .70, H * .30, 120
        y, x = np.mgrid[0:H, 0:W]; d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        disk = np.clip(r - d, 0, 1)
        tex = 0.82 + 0.18 * self.noise((40, 16, 6), (1, .6, .4))
        img = img * (1 - disk[..., None]) + disk[..., None] * (tex[..., None] * np.array([1, .96, .86]))
        img += (np.exp(-np.clip(d - r, 0, None) / 90) * (d > r))[..., None] * np.array([.35, .33, .28]) * 0.6
        return self.silhouette(img, self.ridge(H * 0.82, 50), (.008, .01, .018), 1)

    # 宇宙スポット：天文台のドーム
    def observatory(self):
        img = self.dawn(trail=False)
        m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
        bx, by = W * 0.70, H * 0.80 - 140 - 10
        d.rectangle((bx - 120, by - 20, bx + 120, by + 120), fill=255)
        d.pieslice((bx - 130, by - 150, bx + 130, by + 110), 180, 360, fill=255)
        d.rectangle((bx - 14, by - 150, bx + 14, by - 40), fill=0)  # スリット
        a = np.asarray(m.filter(ImageFilter.GaussianBlur(1))).astype(np.float32)[..., None] / 255
        return img * (1 - a) + a * np.array([.02, .015, .03])

    # 機材：三脚と星空
    def tripod(self):
        img = self.night(hz=0.8)
        img = self.milkyway(img, offset=-300)
        img = self.stars(img, 3400, H * 0.8, 1.1)
        img = self.silhouette(img, self.ridge(H * 0.82, 30), (.006, .008, .014), 1)
        m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
        tx, ty = W * 0.72, H * 0.60
        for dx in (-150, 0, 150):
            d.line([(tx, ty), (tx + dx, H * 0.86)], fill=255, width=9)
        d.rectangle((tx - 70, ty - 70, tx + 80, ty), fill=255); d.polygon([(tx + 80, ty - 60), (tx + 150, ty - 95), (tx + 150, ty + 10), (tx + 80, ty - 10)], fill=255)
        a = np.asarray(m).astype(np.float32)[..., None] / 255
        return img * (1 - a) + a * np.array([.004, .005, .01])

    def film(self, img, haze_y=.74, leak=True):
        """TRANSIT のような写真の空気感：かすみ・にじみ・フィルムの色・光漏れ"""
        img = np.clip(img, 0, None)
        haze = np.exp(-((self.yy - haze_y) / .10) ** 2)[..., None] * np.array([.10, .07, .06])
        img = img + haze
        bright = np.clip(img.max(axis=2) - .55, 0, 1)
        bloom = self.blur(bright, 18)[..., None] * np.array([1, .75, .55]) * .9
        img = img + bloom
        lum = img.mean(axis=2, keepdims=True)
        shadow = np.clip(1 - lum * 2.5, 0, 1); high = np.clip((lum - .35) * 2, 0, 1)
        img = img + shadow * np.array([-.004, .018, .030]) + high * np.array([.05, .02, -.03])
        img = img * .94 + .035  # 黒を少し持ち上げる（フィルムのような浅さ）
        if leak:
            y, x = np.mgrid[0:H, 0:W]
            d = np.sqrt(((x - W * 1.02) / (W * .55)) ** 2 + ((y + H * .05) / (H * .9)) ** 2)
            img = img + (np.exp(-d * 2.2) * .28)[..., None] * np.array([1, .45, .18])
        return img

    def finish(self, img, grain=.035, vig=.55):
        y, x = np.mgrid[0:H, 0:W]; d = ((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2
        img = img * (1 - vig * np.clip(d, 0, 1.4)[..., None] * 0.5)
        img = img + self.rng.normal(0, grain, (H, W, 1))
        return Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8))

    # ---------- 組み立て式（記事ごとに空・地上・モチーフを変える） ----------
    def sky(self, tone="night", milky=True, nstars=3200, hz=0.76):
        if tone == "dawn":
            t = np.clip(self.yy / (hz + .04), 0, 1)
            c0, c1, c2, c3 = (.01, .02, .06), (.10, .10, .30), (.55, .30, .40), (.98, .55, .28)
            img = np.where((t < .55)[..., None], self.lerp(c0, c1, t / .55),
                           np.where((t < .85)[..., None], self.lerp(c1, c2, (t - .55) / .30), self.lerp(c2, c3, np.clip((t - .85) / .15, 0, 1))))
            return self.stars(img, int(nstars * .7), H * hz * .8, .8)
        if tone == "dusk":
            t = np.clip(self.yy / hz, 0, 1)
            img = np.where((t < .6)[..., None], self.lerp((.02, .03, .10), (.06, .16, .32), t / .6), self.lerp((.06, .16, .32), (.55, .42, .55), (t - .6) / .4))
            return self.stars(img, int(nstars * .5), H * hz * .7, .7)
        img = self.night(hz=hz)
        if milky: img = self.milkyway(img)
        return self.stars(img, nstars, H * hz, 1.1)

    def ground(self, img, kind, hz, trail_x=None):
        hzp = int(H * hz)
        if kind in ("sea", "island"):
            wav = self.noise((30, 12, 6), (1, .7, .5))
            seac = self.lerp((.05, .08, .14), (.01, .015, .03), np.clip((self.yy - hz) / (1 - hz), 0, 1))
            if trail_x is not None:
                ref = np.exp(-((np.arange(W)[None, :] - trail_x) / (W * 0.012)) ** 2) * np.ones((H, 1))
                seac = seac + (ref * (0.25 + 0.6 * wav))[..., None] * np.array([1, .5, .18]) * np.exp(-((self.yy * H - hzp) / (H * 0.18)))[..., None]
            img = np.where((np.arange(H) >= hzp)[:, None, None], seac + ((wav - .5) * .03)[..., None], img)
            if kind == "island":  # 平たく長い島（種子島のような）
                xs = np.arange(int(W * .05), int(W * .62), 8)
                prof = hzp - 26 - 34 * np.exp(-((xs - W * .22) / (W * .10)) ** 2) - 18 * np.sin(xs / 90) * .5 - 10 * np.exp(-((xs - W * .45) / (W * .06)) ** 2)
                img = self.silhouette(img, [(W * .05, hzp + 2)] + [(float(x), float(p)) for x, p in zip(xs, prof)] + [(W * .62, hzp + 2)])
            else:
                xs = np.arange(0, int(W * 0.42), 8)
                prof = hzp - 80 - 120 * np.exp(-((xs - W * 0.12) / (W * 0.11)) ** 2) - 40 * np.sin(xs / 57) * np.exp(-xs / 700) + (xs / (W * 0.42)) ** 2 * 90
                img = self.silhouette(img, [(0, hzp + 2)] + [(float(x), float(p)) for x, p in zip(xs, prof)] + [(W * 0.42, hzp + 2)])
            return img
        if kind == "city":  # 街並み（家の近くの空で見る）
            m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m); x = 0
            while x < W:
                bw = self.rng.integers(50, 150); bh = self.rng.integers(30, 150) * (1.8 if self.rng.random() < .08 else 1)
                d.rectangle((x, hzp - bh, x + bw, H), fill=255); x += bw + self.rng.integers(0, 10)
            a = np.asarray(m).astype(np.float32)[..., None] / 255
            img = img * (1 - a) + a * np.array([.012, .014, .022])
            win = (self.rng.random((H, W)) > .9993).astype(np.float32) * a[..., 0] * (np.arange(H)[:, None] < H * .97)
            win = self.blur(win, 1.5) * 6
            return img + win[..., None] * np.array([1, .78, .45])
        return self.silhouette(img, self.ridge(hzp, 40 if kind == "hills" else 14), (.006, .008, .014), 1)

    def m_trail(self, img, hz, x0=.60, side=1, ramp=.55, width=6, strength=1.0, height=.74):
        hzp = H * hz; x = W * x0
        pts = self.bez((x, hzp), (x + side * W * .02, hzp - H * height * .40), (x + side * W * .10, hzp - H * height * .80), (x + side * W * .33, hzp - H * height))
        return self.streak(img, pts, width=width, ramp=ramp, strength=strength)

    def m_meteors(self, img, rx=.70, ry=.18, n=2, hz=.78):
        """流れ星（写真のように）：放射点から外へ向かう細い線。尾は淡く、頭に向かって明るくなり、ふっと消える。
        1枚の写真に写るのはふつう1〜2本。いちばん明るい1本以外は暗くする"""
        rxp, ryp = W * rx, H * ry; lay = np.zeros((H, W, 3), np.float32)
        for i in range(n):
            for _ in range(80):
                ang = self.rng.uniform(0, 2 * np.pi); r0 = W * self.rng.uniform(.14, .36)
                ln = r0 * self.rng.uniform(.45, .70) * (1.5 if i == 0 else .7)
                p0 = np.array([rxp + np.cos(ang) * r0, ryp + np.sin(ang) * r0]); p1 = p0 + np.array([np.cos(ang), np.sin(ang)]) * ln
                if all(W * .04 < p[0] < W * .96 and H * .04 < p[1] < H * (hz - .08) for p in (p0, p1)): break
            amp = 1.0 if i == 0 else self.rng.uniform(.22, .45)
            m = int(ln * 3); t = np.linspace(0, 1, m)
            b = t ** 1.4 * (1 - np.clip((t - .80) / .20, 0, 1) ** 1.6)
            b = b * (1 + .35 * np.exp(-((t - self.rng.uniform(.55, .8)) / .03) ** 2))  # 途中で一瞬明るくなる
            col = np.where((t > .55)[:, None], np.array([.72, 1, .80]), np.where((t < .30)[:, None], np.array([1, .72, .78]), np.array([.95, .97, 1])))
            xs = np.clip((p0[0] + (p1[0] - p0[0]) * t).astype(int), 0, W - 1); ys = np.clip((p0[1] + (p1[1] - p0[1]) * t).astype(int), 0, H - 1)
            np.add.at(lay, (ys, xs), (b * amp)[:, None] * col / 3)
        mx = max(lay.max(), 1e-6); a = lay / mx
        g1 = np.stack([self.blur(a[..., k], .9) for k in range(3)], -1); g2 = np.stack([self.blur(a[..., k], 3.5) for k in range(3)], -1)
        g3 = np.stack([self.blur(a[..., k], 10) for k in range(3)], -1)
        return img + (g1 * 3.2 + g2 * 1.4 + g3 * .5) * min(mx, 1.0) * 1.8

    # 星座の明るい星（相対位置はおおよそ。等級と色つき）
    CONS = {"orion": [(-.95, -1.05, .5, (1, .68, .45)), (.70, -.95, 1.6, (.82, .88, 1)), (.05, -1.55, 3.4, (.85, .9, 1)),
                      (-.30, .15, 1.8, (.82, .88, 1)), (0, .03, 1.7, (.82, .88, 1)), (.28, -.08, 2.2, (.82, .88, 1)),
                      (-.70, 1.25, 2.1, (.82, .88, 1)), (.85, 1.15, .1, (.78, .86, 1))],
            "gemini": [(-.30, -1.20, 1.6, (.9, .94, 1)), (-.75, -.95, 1.1, (1, .82, .6)), (.10, -.20, 2.9, (1, .95, .85)),
                       (-.40, .10, 3.5, (1, .95, .9)), (.55, .55, 1.9, (.9, .94, 1)), (.20, .95, 3.0, (1, .9, .8))],
            "leo": [(.60, .55, 1.4, (.8, .87, 1)), (.45, -.30, 2.0, (1, .8, .55)), (.55, -.75, 3.4, (1, .95, .9)),
                    (.20, -1.00, 3.0, (1, .95, .9)), (-.15, -.95, 3.4, (1, .9, .8)), (-1.30, .20, 2.1, (.9, .94, 1)), (-.70, .00, 2.6, (.9, .94, 1))]}

    def m_constellation(self, img, name, cx=.70, cy=.30, scale=1.0, radiant=None, lines=False):
        """星座の星（写真に線は写らないので、ふつうは線を描かない）"""
        u = 150 * scale; lay = np.zeros((H, W, 3), np.float32); pts = []
        for x, y, mag, col in self.CONS.get(name, self.CONS["orion"]):
            px, py = int(W * cx + x * u), int(H * cy + y * u); pts.append((px, py))
            lay[py, px] = np.array(col) * 10 ** (-.4 * (mag - .5))
        g = [np.stack([self.blur(lay[..., k], r) for k in range(3)], -1) for r in (1.2, 3.2, 9)]
        img = img + lay * 1.5 + g[0] * 70 + g[1] * 40 + g[2] * 14
        if name == "orion":  # オリオン大星雲（ぼんやり）
            y, x = np.mgrid[0:H, 0:W].astype(np.float32)
            neb = np.exp(-(((x - W * cx - .04 * u) / (u * .07)) ** 2 + ((y - H * cy - .55 * u) / (u * .10)) ** 2))
            img = img + neb[..., None] * np.array([.25, .12, .2]) * .6
        if lines:
            m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
            for a, b in zip(pts, pts[1:]): d.line([a, b], fill=50, width=2)
            img = img + (np.asarray(m).astype(np.float32) / 255)[..., None] * np.array([.7, .8, 1.0])
        return img

    def m_moon(self, img, cx=.72, cy=.28, r=110, warm=False):
        cx, cy = W * cx, H * cy
        y, x = np.mgrid[0:H, 0:W]; dd = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        disk = np.clip(r - dd, 0, 1); tex = 0.82 + 0.18 * self.noise((40, 16, 6), (1, .6, .4))
        col = np.array([1, .78, .55]) if warm else np.array([1, .96, .86])
        img = img * (1 - disk[..., None]) + disk[..., None] * (tex[..., None] * col)
        return img + (np.exp(-np.clip(dd - r, 0, None) / (r * .8)) * (dd > r))[..., None] * col * 0.35

    def m_eclipse(self, img, cx=.70, cy=.30, r=90, sequence=False):
        """皆既月食：赤銅色の月。sequence なら、欠けていく月を弧に並べた合成（連続写真のように）"""
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        def moon(img, mx, my, rr, shadow):  # shadow：0（満月）〜1（皆既）
            dd = np.sqrt((x - mx) ** 2 + (y - my) ** 2); disk = np.clip(rr - dd, 0, 1)
            tex = .82 + .18 * self.noise((30, 12, 5), (1, .6, .4)) if not hasattr(self, "_mtex") else self._mtex
            self._mtex = tex
            sx = mx + rr * 2.2 * (1 - shadow) - rr * .2  # 地球の影（大きな円）が左から重なる
            inshadow = np.clip((rr * 1.9 - np.sqrt((x - sx) ** 2 + (y - my) ** 2)) / (rr * .25), 0, 1)
            lit = np.array([1, .96, .86]); red = np.array([.62, .22, .10]) * (.55 + .45 * shadow)
            col = lit[None, None, :] * (1 - inshadow[..., None]) + red[None, None, :] * inshadow[..., None]
            img = img * (1 - disk[..., None]) + disk[..., None] * tex[..., None] * col
            return img + (np.exp(-np.clip(dd - rr, 0, None) / (rr * .6)) * (dd > rr) * (.35 if shadow < .9 else .12))[..., None] * col.mean(axis=(0, 1))
        if not sequence: return self.blood_moon(img, W * cx, H * cy, r)
        for i, sh in enumerate((0, .25, .5, .75, 1, 1, .75)):
            t = i / 6; img = moon(img, W * (.30 + .55 * t), H * (.55 - .32 * np.sin(np.pi * (.15 + .7 * t))), r * .55, sh)
        return img

    def blood_moon(self, img, mx, my, r):
        """皆既中の月（写真のように）：赤銅色、海（暗い模様）が見え、影の中心から遠い側の縁が明るく、わずかに青白い帯"""
        y, x = np.mgrid[0:H, 0:W].astype(np.float32); dx, dy = (x - mx) / r, (y - my) / r; rr = np.sqrt(dx ** 2 + dy ** 2)
        disk = np.clip((1 - rr) * r, 0, 1)
        # 月の海：大きな低周波の暗い斑点（月面の模様のように）
        # 実際の月の表側に似た配置（左上に広い嵐の大洋・雨の海、右上に晴れの海・静かの海・危難の海、下半分は明るい高地）
        blob = np.zeros_like(rr); edge_n = self.noise((10, 5), (1, .5))
        for ox, oy, sx_, sy_ in ((-.48, -.10, .22, .38), (-.22, -.38, .20, .15), (.10, -.36, .12, .11), (.24, -.12, .13, .14), (.55, -.20, .09, .08),
                                 (.36, .18, .10, .14), (-.05, .02, .10, .08), (-.30, .30, .14, .10), (.10, .30, .07, .06)):
            blob = np.maximum(blob, np.exp(-(((dx - ox) / (sx_ * 1.35)) ** 2 + ((dy - oy) / (sy_ * 1.35)) ** 2) / 2))
        maria = self.blur(np.clip((blob + (edge_n - .5) * .4 - .35) * 2.2, 0, 1), r * .04) * .5
        tycho = np.exp(-((dx + .12) ** 2 + (dy - .62) ** 2) / (2 * .025 ** 2)) * .5
        fine = self.noise((14, 6, 3), (1, .6, .4))
        alb = np.clip(1 - maria + tycho, .3, 1.3) * (.82 + .18 * fine)
        # 影の中心は右下寄り。そこから遠い左上の縁ほど明るい
        lim = np.clip((-.55 * dx - .65 * dy + 1) / 2, 0, 1) ** 2.2
        limb = 1 - .35 * rr ** 2  # 周辺減光
        col = np.array([.50, .16, .07])[None, None, :] * (.35 + 1.7 * lim[..., None]) + np.array([.98, .60, .28])[None, None, :] * (lim[..., None] ** 3) * 1.1
        col = col * (alb * limb)[..., None]
        edge = np.exp(-((rr - .97) / .04) ** 2) * lim ** 1.5  # 縁のかすかな青白い帯（オゾン層を通った光）
        col = col + edge[..., None] * np.array([.35, .45, .55]) * .35
        img = img * (1 - disk[..., None]) + disk[..., None] * col
        glow = np.exp(-np.clip(rr - 1, 0, None) / .35) * (rr > 1) * .10
        return img + glow[..., None] * np.array([.8, .35, .2])

    def m_comet(self, img, cx=.68, cy=.30, angle=-35, length=.30):
        """彗星：明るい頭、扇形に広がる黄色いちりの尾、まっすぐで細い青いイオンの尾"""
        y, x = np.mgrid[0:H, 0:W].astype(np.float32); hx, hy = W * cx, H * cy
        th = np.radians(angle); ux, uy = np.cos(th), np.sin(th)  # 尾の向き
        u = (x - hx) * ux + (y - hy) * uy; v = -(x - hx) * uy + (y - hy) * ux; L = W * length
        dust = np.exp(-(v - u * .12) ** 2 / (2 * (12 + u * .16) ** 2)) * np.clip(u / L * 4, 0, 1) * np.exp(-np.clip(u, 0, None) / (L * .55)) * (u > 0)
        ion = np.exp(-v ** 2 / (2 * (3 + u * .02) ** 2)) * np.exp(-np.clip(u, 0, None) / (L * .9)) * (u > 0)
        head = np.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * 6 ** 2)) * 2.5 + np.exp(-np.sqrt((x - hx) ** 2 + (y - hy) ** 2) / 28) * .5
        return img + dust[..., None] * np.array([1, .9, .7]) * .55 + ion[..., None] * np.array([.55, .75, 1]) * .45 + head[..., None] * np.array([.85, 1, .9])

    def m_planets(self, img, cx=.68, cy=.42):
        for (dx, dy, col, rr) in ((0, 0, (1, .97, .9), 9), (70, 38, (1, .55, .35), 7)):
            lay = np.zeros((H, W), np.float32); lay[int(H * cy + dy), int(W * cx + dx)] = 1
            img = img + (self.blur(lay, rr * .5) * rr * 60 + self.blur(lay, rr * 3) * rr * 30)[..., None] * np.array(col)
        return img

    def m_straight(self, img, p0, p1, dots=False):
        if dots:
            lay = np.zeros((H, W), np.float32)
            for k in range(16):
                x = p0[0] + (p1[0] - p0[0]) * k / 15; y = p0[1] + (p1[1] - p0[1]) * k / 15
                lay[int(H * y), int(W * x)] = 1
            return img + (self.blur(lay, 2) * 60 + self.blur(lay, 6) * 20)[..., None] * np.array([1, 1, 1])
        pts = [(W * (p0[0] + (p1[0] - p0[0]) * k / 60), H * (p0[1] + (p1[1] - p0[1]) * k / 60)) for k in range(61)]
        return self.streak(img, pts, core=(1, 1, .96), halo=(.6, .7, 1), width=4, glow=16, strength=.9)

    def m_object(self, img, kind, hz, x=.72):
        m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m); tx = W * x; ground = H * hz + 6
        if kind == "dome":
            by = ground - 120
            d.rectangle((tx - 120, by - 20, tx + 120, ground + 40), fill=255); d.pieslice((tx - 130, by - 150, tx + 130, by + 110), 180, 360, fill=255)
            d.rectangle((tx - 14, by - 150, tx + 14, by - 40), fill=0)
        else:  # tripod + camera / phone
            ty = ground - 300
            for dx in (-150, 0, 150): d.line([(tx, ty), (tx + dx, ground + 40)], fill=255, width=9)
            if kind == "phone": d.rounded_rectangle((tx - 44, ty - 170, tx + 44, ty + 4), radius=16, fill=255)
            else:
                d.rectangle((tx - 70, ty - 70, tx + 80, ty), fill=255)
                d.polygon([(tx + 80, ty - 60), (tx + 150, ty - 95), (tx + 150, ty + 10), (tx + 80, ty - 10)], fill=255)
        a = np.asarray(m).astype(np.float32)[..., None] / 255
        return img * (1 - a) + a * np.array([.004, .005, .01])

    # ---------- 写真らしさを足す部品 ----------
    def lowres_noise(self, gw, gh, sx=1.0, sy=1.0, octaves=4):
        """横長・縦長に引き伸ばしたノイズ（雲・波）"""
        out = np.zeros((H, W), np.float32); amp = 1.0
        for o in range(octaves):
            w = max(2, int(gw * 2 ** o / sx)); h = max(2, int(gh * 2 ** o / sy))
            n = Image.fromarray((self.rng.random((h, w)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
            out += amp * np.asarray(n).astype(np.float32) / 255; amp *= .5
        out -= out.min(); return out / out.max()

    def stars_real(self, img, n, hz, bright=1.0, ext=True):
        hzp = H * hz; ys = self.rng.integers(0, int(hzp), n); xs = self.rng.integers(0, W, n)
        mag = self.rng.power(14, n) ** 3 * bright
        pal = np.array([[.70, .80, 1], [.86, .92, 1], [1, 1, 1], [1, .93, .82], [1, .80, .62]])
        cols = pal[self.rng.choice(5, n, p=[.12, .28, .30, .18, .12])]
        if ext: mag = mag * np.clip((hzp - ys) / (H * .30), .08, 1) ** .9
        lay = np.zeros((H, W, 3), np.float32); lay[ys, xs] = cols * mag[:, None]
        g = np.stack([self.blur(lay[..., k] / max(lay[..., k].max(), 1e-6), 1.1) * lay[..., k].max() for k in range(3)], -1)
        g2 = np.stack([self.blur(lay[..., k] / max(lay[..., k].max(), 1e-6), 3.5) * lay[..., k].max() for k in range(3)], -1)
        return img + lay * .9 + g * 3.2 + g2 * 1.4

    def milky_real(self, img, cx=.45, cy=.30, angle=-62, width=.17, core=(.25, .75), strength=1.0):
        y, x = np.mgrid[0:H, 0:W].astype(np.float32); th = np.radians(angle)
        u = (x - W * cx) * np.cos(th) + (y - H * cy) * np.sin(th); v = -(x - W * cx) * np.sin(th) + (y - H * cy) * np.cos(th)
        band = np.exp(-(v / (H * width)) ** 2)
        cloud = self.noise((260, 110, 46, 18, 8), (1, .7, .45, .3, .2)) ** 1.6
        dust = self.noise((90, 40, 16), (1, .6, .4))
        rift = np.exp(-((v + H * width * .12 * np.sin(u / 300)) / (H * width * .22)) ** 2) * np.clip(dust * 1.6 - .45, 0, 1)
        glow = band * cloud * (1 - .85 * rift)
        corepos = np.exp(-((u - W * (core[0] - .5) * 1.2) / (W * core[1] * .35)) ** 2)
        col = (1 - corepos)[..., None] * np.array([.55, .62, .85]) + corepos[..., None] * np.array([1, .85, .62])
        return img + glow[..., None] * col * .32 * strength

    def airglow(self, img, hz, col=(.06, .11, .06)):
        return img + np.exp(-((self.yy - (hz - .06)) / .07) ** 2)[..., None] * np.array(col)

    def lightdome(self, img, x, hz, strength=1.0):
        y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W * x) / (W * .45)) ** 2 + ((y - H * hz) / (H * .32)) ** 2)
        return img + (np.exp(-d * 2.4) * strength)[..., None] * np.array([.30, .17, .08])

    def clouds(self, img, y0, y1, lit=(.9, .6, .45), dens=.55, alpha=.85):
        n = self.lowres_noise(6, 3, sx=1.0, sy=.35)
        band = np.clip((self.yy - y0) / .04, 0, 1) * np.clip((y1 - self.yy) / .05, 0, 1)
        a = np.clip((n - (1 - dens)) * 3.2, 0, 1) * band * alpha
        under = np.clip((self.yy - y0) / max(y1 - y0, .01), 0, 1)
        col = np.array(lit)[None, None, :] * (1 - under[..., None] * .6) * (.35 + .65 * n[..., None])
        self._cloud_a = a
        return img * (1 - a[..., None]) + col * a[..., None] * .55 + img * a[..., None] * .25

    def ridge_profile(self, base, rough, seed_shift=0, step=6):
        xs = np.arange(0, W + step, step).astype(np.float32); prof = np.full_like(xs, base)
        for k, (wl, amp) in enumerate(((900, 1), (380, .5), (150, .25), (60, .12), (24, .06))):
            ph = self.rng.uniform(0, 6.28)
            prof -= rough * amp * (np.sin(xs / wl * 6.28 / 3 + ph) * .5 + .5 + .4 * np.sin(xs / (wl * .37) + ph * 1.7))
        return xs, prof

    def mountains(self, img, hz, layers=3, rough=170, trees=False, near=(.006, .008, .014)):
        hzp = H * hz; haze = img[int(hzp) - 8].mean(axis=0)
        for i in range(layers):
            t = (i + 1) / layers
            xs, prof = self.ridge_profile(hzp + 6 - rough * (1.15 - t) * .6, rough * (.55 + t * .45))
            col = haze * (1 - t) ** 1.3 * .9 + np.array(near) * t
            m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
            d.polygon([(0, H)] + [(float(x), float(p)) for x, p in zip(xs, prof)] + [(W, H)], fill=255)
            if trees and i == layers - 1:
                for x, p in zip(xs[::3], prof[::3]):
                    if self.rng.random() < .55:
                        th = self.rng.uniform(26, 70); tw = th * .32
                        d.polygon([(x - tw, p + 6), (x, p - th), (x + tw, p + 6)], fill=255)
            a = np.asarray(m.filter(ImageFilter.GaussianBlur(.8 + (1 - t) * 1.5))).astype(np.float32)[..., None] / 255
            img = img * (1 - a) + a * col
        return img

    def sea_real(self, img, hz, trail_x=None):
        hzp = int(H * hz); rows = H - hzp
        sky = img[max(0, hzp - rows):hzp][::-1]
        if sky.shape[0] < rows: sky = np.concatenate([sky, np.repeat(sky[-1:], rows - sky.shape[0], 0)], 0)
        wav = self.lowres_noise(40, 10, sx=1, sy=.12, octaves=4)[hzp:]
        refl = sky * .38 * (.7 + .5 * wav[..., None])
        depth = np.clip(np.arange(rows) / rows, 0, 1)[:, None, None]
        sea = refl * (1 - depth * .7) + np.array([.008, .014, .026]) * depth
        if trail_x is not None:
            xs = np.arange(W)[None, :]; jitter = (wav - .5) * 40
            col = np.exp(-((xs - trail_x - jitter) / (W * .010)) ** 2) * (wav > .45) * np.exp(-np.arange(rows)[:, None] / (rows * .7))
            sea = sea + col[..., None] * np.array([1, .52, .2]) * .9
        img = img.copy(); img[hzp:] = sea
        img[hzp - 2:hzp + 2] += np.array([.05, .05, .06])
        return img

    def trail_real(self, img, hz, x0=.60, side=1, height=.74, strength=1.0, curve=.33):
        hzp = H * hz; x = W * x0
        pts = self.bez((x, hzp), (x + side * W * .02, hzp - H * height * .40), (x + side * W * .10, hzp - H * height * .80), (x + side * W * curve, hzp - H * height))
        lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay); n = len(pts)
        for i in range(n - 1):
            t = i / (n - 1); v = int(255 * (1 - .55 * t)); w = int(10 - 7 * t)
            d.line([pts[i], pts[i + 1]], fill=v, width=max(2, w))
        a = np.asarray(lay).astype(np.float32) / 255
        img = img + strength * (a[..., None] * np.array([1, .93, .8]) + self.blur(a, 9)[..., None] * np.array([1, .5, .16]) * 1.8 + self.blur(a, 46)[..., None] * np.array([1, .42, .12]) * 1.5)
        y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        base = np.exp(-(((xx - x) / (W * .05)) ** 2 + ((y - hzp) / (H * .05)) ** 2))
        self._trail = pts
        return img + (base * .55 * strength)[..., None] * np.array([1, .55, .25]), pts[-1]

    def separation(self, img, pts):
        """固体ロケットブースターの分離：光跡の上のほうから、2つの小さな光が離れて落ちていく"""
        n = len(pts); x0, y0 = pts[int(n * .55)]; lay = np.zeros((H, W), np.float32)
        for dx, dy in ((-150, 230), (-70, 300)):
            for k in range(30):
                t = k / 29; xx, yy = int(x0 + dx * t), int(y0 + dy * t * t)
                if 0 <= yy < H and 0 <= xx < W: lay[yy, xx] = max(lay[yy, xx], (1 - t) * .9)
        lay = np.maximum(lay, np.roll(lay, 1, 0))
        return img + (self.blur(lay, 2) * 30 + self.blur(lay, 8) * 14)[..., None] * np.array([1, .7, .4])

    def smoke(self, img, hz, x0=.58, side=1, height=.72, curve=.22, drift=.06, width=1.0):
        """昼の打ち上げ：日に照らされた白い噴煙の柱。下ほど太く、風で流れる。先に小さく明るい炎"""
        hzp = H * hz; x = W * x0
        pts = self.bez((x, hzp), (x + side * W * .015, hzp - H * height * .45), (x + side * W * .07, hzp - H * height * .85), (x + side * W * curve, hzp - H * height), 300)
        m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m); n = len(pts)
        for i, (px, py) in enumerate(pts):
            t = i / (n - 1); r = (70 * (1 - t) ** 1.6 + 7) * width * S / 2 * (1 + .25 * self.rng.random())
            px = px - (1 - t) ** 2 * W * drift  # 下のほうの煙ほど風で流れる
            d.ellipse((px - r, py - r * .8, px + r, py + r * .8), fill=int(170 + 85 * t))
        a = np.asarray(m.filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
        tex = .72 + .28 * self.noise((40, 18, 8), (1, .6, .4))
        y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        lit = np.clip(.75 + .35 * (xx - x) / (W * .12), .55, 1.1)  # 日の当たる側が明るい
        col = (tex * lit)[..., None] * np.array([.97, .96, .93])
        img = img * (1 - a[..., None] * .92) + col * a[..., None] * .92
        tx, ty = pts[-1]; fl = np.exp(-((xx - tx) ** 2 + (y - ty) ** 2) / (2 * (5 * S) ** 2))
        return img + (fl * 2.5 + np.exp(-np.sqrt((xx - tx) ** 2 + (y - ty) ** 2) / 40) * .35)[..., None] * np.array([1, .85, .55])

    def liftoff(self, img, hz, x=.66, scale=1.0, rise=.35, tone="night"):
        """発射の瞬間を近くから：射点から上がるロケット（一般的な形）、強い炎、横に広がる地上の煙"""
        cx = W * x; gy = H * hz + 4; k = scale * S / 2
        rh, rw = 230 * k, 20 * k; by = gy - H * rise; ty = by - rh  # by：ロケットの底
        fs = 1.6 if tone == "day" else 1.0
        y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        # 空を照らす光
        img = img + (np.exp(-np.sqrt(((xx - cx) / (W * .22)) ** 2 + ((y - by) / (H * .45)) ** 2) * 2.2) * .7)[..., None] * np.array([1, .6, .28])
        # 炎（ロケットの下から地面へ）
        fm = Image.new("L", (W, H), 0); fd = ImageDraw.Draw(fm)
        fd.polygon([(cx - rw * .45, by), (cx + rw * .45, by), (cx + rw * .9, gy - 10), (cx - rw * .9, gy - 10)], fill=255)
        fa = np.asarray(fm.filter(ImageFilter.GaussianBlur(6 * k))).astype(np.float32) / 255
        core = np.asarray(fm.filter(ImageFilter.GaussianBlur(2 * k))).astype(np.float32) / 255 * np.clip(1 - (y - by) / (gy - by), 0, 1)
        img = img + fa[..., None] * np.array([1, .62, .25]) * 1.6 * fs + core[..., None] * np.array([1, .95, .8]) * 2.2 * fs + self.blur(fa, 30)[..., None] * np.array([1, .5, .2]) * 1.4
        img = np.where(core[..., None] > .5, np.maximum(img, np.array([1.0, .82, .45]) * 1.15), img)
        # 地上の煙（炎に下から照らされる）
        sm = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(sm)
        for _ in range(90):
            ox = self.rng.normal(0, W * .11); oy = -abs(self.rng.normal(0, H * .05)); r = self.rng.uniform(40, 120) * k * (1 + abs(ox) / (W * .25))
            sd.ellipse((cx + ox - r, gy + oy - r * .75, cx + ox + r, gy + oy + r * .35), fill=int(self.rng.uniform(120, 230)))
        sa = np.asarray(sm.filter(ImageFilter.GaussianBlur(14 * k))).astype(np.float32) / 255
        tex = .65 + .35 * self.noise((50, 20, 8), (1, .6, .4))
        warm = np.exp(-np.sqrt(((xx - cx) / (W * .14)) ** 2 + ((y - gy) / (H * .10)) ** 2))
        base = np.array([.30, .30, .34]) if tone != "day" else np.array([.85, .85, .86])
        scol = tex[..., None] * (base * (1 - warm[..., None]) + np.array([1, .62, .3]) * 1.3 * warm[..., None])
        img = img * (1 - sa[..., None] * .95) + scol * sa[..., None] * .95
        # 発射塔（影）とロケット
        tw = self._mask(lambda d: (d.rectangle((cx - rw * 3.6, gy - rh * 1.25, cx - rw * 2.4, gy + 10), fill=255),
                                   [d.line([(cx - rw * 2.4, gy - rh * (.2 + .25 * j)), (cx - rw * 1.2, gy - rh * (.2 + .25 * j))], fill=255, width=int(4 * k)) for j in range(4)]), .8)
        img = self.put(img, tw, (.02, .018, .02), sky=(.25, .14, .08))
        body = self._mask(lambda d: (d.rectangle((cx - rw / 2, ty + rw * .9, cx + rw / 2, by), fill=255),
                                     d.polygon([(cx - rw / 2, ty + rw * .9), (cx, ty), (cx + rw / 2, ty + rw * .9)], fill=255),
                                     [d.rectangle((cx + sx * rw * .78 - rw * .2, by - rh * .38, cx + sx * rw * .78 + rw * .2, by), fill=255) for sx in (-1, 1)]), .7)
        shade = np.clip(.45 + .55 * (cx - xx + rw * .3) / rw, .25, 1) * np.clip(.6 + .5 * (y - ty) / rh, .6, 1.1)
        return img * (1 - body[..., None]) + (body * shade)[..., None] * np.array([.98, .9, .78])

    def jellyfish(self, img, cx, cy, size=300, col=(.75, .88, 1)):
        """明け方の打ち上げで、日が当たった噴煙が広がって光る現象（模式的に）"""
        m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
        for k in range(26):
            ang = np.radians(200 + k * 5.5 + self.rng.uniform(-2, 2)); r = size * self.rng.uniform(.75, 1.05)
            d.line([(cx, cy), (cx + np.cos(ang) * r, cy + np.sin(ang) * r * .75)], fill=int(self.rng.uniform(60, 140)), width=int(self.rng.uniform(8, 22)))
        d.ellipse((cx - size * .35, cy - size * .25, cx + size * .35, cy + size * .2), fill=150)
        a = np.asarray(m.filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255
        tex = self.noise((60, 24, 10), (1, .6, .4))
        return img + (a * (.5 + .7 * tex))[..., None] * np.array(col) * .9

    # ---------- 施設・持ち物（手前の物は、空の明かりと赤いライトで縁が光る） ----------
    def _mask(self, draw_fn, soften=.8):
        m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m))
        return np.asarray(m.filter(ImageFilter.GaussianBlur(soften))).astype(np.float32) / 255

    def put(self, img, a, base=(.006, .007, .012), lamp=None, sky=(.10, .13, .20), rim=5):
        up = np.zeros_like(a); up[rim:] = a[:-rim]
        out = np.array(base) + (self.blur(np.clip(a - up, 0, 1), 1.2) * 1.4)[..., None] * np.array(sky)
        if lamp:
            lx, ly, col, st = lamp; y, x = np.mgrid[0:H, 0:W].astype(np.float32)
            fall = np.exp(-np.sqrt((x - lx) ** 2 + (y - ly) ** 2) / (W * .10)) * st
            edge = np.clip(a - self.blur(a, 4), 0, 1) * 2.5
            out = out + (fall * (.18 + edge))[..., None] * np.array(col)
        return img * (1 - a[..., None]) + a[..., None] * out

    def lamp_glow(self, img, lx, ly, col=(1, .12, .06), st=1.0, hz=.78):
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        pt = np.exp(-((x - lx) ** 2 + (y - ly) ** 2) / (2 * 6 ** 2)) * 3 + np.exp(-np.sqrt((x - lx) ** 2 + (y - ly) ** 2) / 40) * .5
        pool = np.exp(-(((x - lx) / (W * .16)) ** 2 + ((y - ly - 10) / (H * .06)) ** 2)) * (y > H * hz) * .45
        return img + ((pt + pool) * st)[..., None] * np.array(col)

    def m_pad(self, img, hz, x=.66, scale=1.0, sea=True):
        """遠くの射点：照明に照らされて立つロケット（実在の形ではない、一般的な形）"""
        cx = W * x; by = H * hz + 3; k = scale * S / 2
        rh, rw, tw = 165 * k, 13 * k, 26 * k
        y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        beams = self._mask(lambda d: [d.polygon([(cx + dx * k, by), (cx - rw * .8, by - rh * .95), (cx + rw * .8, by - rh * .95)], fill=40) for dx in (-120, 110)], 10)
        img = img + beams[..., None] * np.array([.75, .82, 1]) * 1.2
        halo = np.exp(-np.sqrt(((xx - cx) / (W * .06)) ** 2 + ((y - by + rh * .4) / (H * .10)) ** 2)) * .35
        img = img + halo[..., None] * np.array([1, .86, .66])
        def tower(d):
            d.rectangle((cx + rw * .9, by - rh * 1.08, cx + rw * .9 + tw, by), fill=255)
            d.rectangle((cx + rw * .5, by - rh * .80, cx + rw * .9, by - rh * .76), fill=255)
            for mx in (-150, 170):
                d.line([(cx + mx * k, by), (cx + mx * k, by - rh * 1.30)], fill=255, width=max(2, int(3 * k)))
            d.rectangle((cx - 260 * k, by - 6 * k, cx + 280 * k, by + 3), fill=255)
        img = self.put(img, self._mask(tower, .6), (.012, .013, .02), sky=(.05, .06, .09))
        body = self._mask(lambda d: (d.rectangle((cx - rw / 2, by - rh * .92, cx + rw / 2, by - 8 * k), fill=255),
                                     d.polygon([(cx - rw / 2, by - rh * .92), (cx, by - rh), (cx + rw / 2, by - rh * .92)], fill=255),
                                     [d.rectangle((cx + sx * (rw / 2 + 3 * k) - 3 * k, by - rh * .38, cx + sx * (rw / 2 + 3 * k) + 3 * k, by - 6 * k), fill=255) for sx in (-1, 1)]), .7)
        shade = np.clip(.65 + .35 * (cx - xx) / rw, .4, 1)
        img = img * (1 - body[..., None]) + (body * shade)[..., None] * np.array([.95, .92, .86])
        lights = np.zeros((H, W), np.float32)
        for j in range(9): lights[int(by - rh * (.1 + j * .11)), int(cx + rw * .9 + tw * (.2 if j % 2 else .8))] = 1
        img = img + self.blur(lights, 1.4)[..., None] * 30 * np.array([1, .82, .55])
        red = np.zeros((H, W), np.float32)
        for mx in (-150, 170): red[int(by - rh * 1.30), int(cx + mx * k)] = 1
        img = img + self.blur(red, 1.6)[..., None] * 40 * np.array([1, .1, .05])
        if sea:
            rows = np.arange(H)[:, None] - by; wav = self.lowres_noise(50, 12, sx=1, sy=.1, octaves=3)
            col = np.exp(-((xx - cx - (wav - .5) * 30) / (W * .012)) ** 2) * (rows > 0) * np.exp(-np.clip(rows, 0, None) / (H * .10)) * (wav > .42)
            img = img + col[..., None] * np.array([1, .9, .75]) * .5
        return img

    def m_observatory(self, img, hz, x=.72, size=1.0, lamp=None):
        """天文台：スリットが開き、中の赤い明かりと望遠鏡が見える"""
        cx = W * x; by = H * hz + 8; r = 150 * size * S / 2 * 1.4; bh = r * .9
        a = self._mask(lambda d: (d.rectangle((cx - r * 1.05, by - bh, cx + r * 1.05, H), fill=255), d.pieslice((cx - r, by - bh - r, cx + r, by - bh + r), 180, 360, fill=255)))
        y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        shade = np.clip(.5 + .5 * (xx - cx) / r, 0, 1) * (y < by - bh) * a
        img = self.put(img, a, (.02, .022, .03), sky=(.14, .16, .22))
        img = img + (shade * .05)[..., None] * np.array([.7, .8, 1])
        slit = self._mask(lambda d: d.rectangle((cx - r * .12, by - bh - r * .96, cx + r * .12, by - bh - r * .05), fill=255), .5)
        inside = np.clip(1 - (y - (by - bh - r)) / r, 0, 1) * .2 + .25
        img = img * (1 - slit[..., None]) + slit[..., None] * (inside[..., None] * np.array([.55, .05, .03]))
        tube = self._mask(lambda d: d.line([(cx - r * .05, by - bh - r * .25), (cx + r * .25, by - bh - r * 1.05)], fill=255, width=int(r * .14)), .6)
        img = img * (1 - (tube * slit)[..., None] * .9)
        door = self._mask(lambda d: d.rectangle((cx - r * .55, by - bh * .55, cx - r * .30, by), fill=255), .6)
        img = img + door[..., None] * np.array([.45, .05, .03]) + self.blur(door, 22)[..., None] * np.array([.25, .03, .02])
        return img

    def m_planetarium(self, img, hz, x=.68, size=1.0):
        """科学館・プラネタリウム：ドームのある建物、窓の明かり、街灯"""
        cx = W * x; by = H * hz + 6; bw = W * .22 * size; bh = H * .10 * size; r = bw * .38
        y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        body = self._mask(lambda d: (d.rectangle((cx - bw, by - bh, cx + bw, H), fill=255), d.pieslice((cx - r, by - bh - r * .9, cx + r, by - bh + r * .9), 180, 360, fill=255)))
        dome = self._mask(lambda d: d.pieslice((cx - r, by - bh - r * .9, cx + r, by - bh + r * .9), 180, 360, fill=255)) * (y < by - bh)
        img = self.put(img, body, (.02, .024, .036), sky=(.16, .2, .3))
        img = img + (dome * np.clip(.35 - (y - (by - bh - r * .9)) / (r * 3), 0, .35))[..., None] * np.array([.6, .7, .9])
        win = self._mask(lambda d: [d.rectangle((cx - bw + 40 + i * (2 * bw - 80) / 14, by - bh * .62, cx - bw + 40 + i * (2 * bw - 80) / 14 + (2 * bw - 80) / 22, by - bh * .30), fill=255) for i in range(15)], .7)
        img = img + win[..., None] * np.array([1, .72, .38]) * .9 + self.blur(win, 20)[..., None] * np.array([1, .6, .3]) * .5
        ent = self._mask(lambda d: d.rectangle((cx - bw * .12, by - bh * .25, cx + bw * .12, by), fill=255), .6)
        img = img + ent[..., None] * np.array([1, .8, .5]) + self.blur(ent, 40)[..., None] * np.array([1, .6, .3]) * .6
        for px in (cx - bw * 1.4, cx + bw * 1.35):
            pole = self._mask(lambda d: d.line([(px, by + 40), (px, by - bh * .9)], fill=255, width=6), .6)
            img = self.put(img, pole)
            l = np.exp(-((xx - px) ** 2 + (y - by + bh * .9) ** 2) / (2 * 7 ** 2)) * 2 + np.exp(-np.sqrt((xx - px) ** 2 + (y - by + bh * .9) ** 2) / 60) * .4
            img = img + l[..., None] * np.array([1, .75, .45])
        return img

    def m_lighthouse(self, img, hz, x=.78, size=1.0, beam=-1):
        """岬の灯台：崖の上の白い塔と、海へのびる光の帯"""
        cx = W * x; k = size * S / 2; gy = H * hz
        xs = np.arange(cx - 320 * k, W + 12, 6); top_y = gy - 70 * k
        prof = top_y + np.clip((cx - 120 * k - xs) / (200 * k), 0, 1) ** 1.5 * 110 * k + 10 * k * np.sin(xs / 23) + 7 * k * np.sin(xs / 9 + 1) + np.clip((xs - cx - 220 * k) / (W * .3), 0, 1) * 40 * k
        prof[0] = gy + 4
        cliff = self._mask(lambda d: d.polygon([(float(xs[0]), H)] + [(float(a), float(b)) for a, b in zip(xs, prof)] + [(W + 12, H)], fill=255), 1)
        img = self.put(img, cliff, (.008, .009, .014), sky=(.10, .12, .18))
        top = gy - 70 * k - 230 * k; lx, ly = cx, top + 18 * k
        y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        ang = np.arctan2(y - ly, (xx - lx) * beam); bw = np.exp(-((ang - .06) / .05) ** 2) * (xx * beam < lx * beam) ** 0 * ((xx - lx) * beam > 0)
        dist = np.sqrt((xx - lx) ** 2 + (y - ly) ** 2); img = img + (bw * np.exp(-dist / (W * .5)) * .45)[..., None] * np.array([1, .96, .85])
        tower = self._mask(lambda d: (d.polygon([(cx - 26 * k, gy - 70 * k), (cx + 26 * k, gy - 70 * k), (cx + 17 * k, top + 36 * k), (cx - 17 * k, top + 36 * k)], fill=255),
                                      d.rectangle((cx - 22 * k, top + 6 * k, cx + 22 * k, top + 36 * k), fill=255), d.pieslice((cx - 18 * k, top - 16 * k, cx + 18 * k, top + 20 * k), 180, 360, fill=255)), .7)
        shade = np.clip(.35 + .5 * (cx - xx) / (26 * k), .15, .85)
        img = img * (1 - tower[..., None]) + (tower * shade)[..., None] * np.array([.75, .78, .85])
        return img + (np.exp(-((xx - lx) ** 2 + (y - ly) ** 2) / (2 * (10 * k) ** 2)) * 2.2 + np.exp(-dist / (40 * k)) * .5)[..., None] * np.array([1, .93, .7])

    def m_antenna(self, img, hz, x=.70, size=1.0, tilt=35):
        """大きなパラボラアンテナ（JAXA の通信所のような施設。一般的な形）：空を向いた皿と台座、施設の明かり"""
        cx = W * x; gy = H * hz + 6; k = size * S / 2; R = 230 * k; th = np.radians(tilt)
        hub = (cx, gy - 330 * k)
        def dish(d):
            d.polygon([(cx - 110 * k, gy + 10), (cx - 60 * k, gy - 250 * k), (cx + 60 * k, gy - 250 * k), (cx + 110 * k, gy + 10)], fill=255)  # 台座
            d.rectangle((cx - 150 * k, gy - 60 * k, cx + 150 * k, gy + 10), fill=255)
            # 皿（傾けた楕円）を多角形で
            pts = [(hub[0] + R * np.cos(t) * np.cos(th) - R * .35 * np.sin(t) * np.sin(th), hub[1] - R * np.cos(t) * np.sin(th) * .9 - R * .35 * np.sin(t) * np.cos(th)) for t in np.linspace(0, 2 * np.pi, 120)]
            d.polygon(pts, fill=255)
            fx, fy = hub[0] - R * .55 * np.sin(th), hub[1] - R * .55 * np.cos(th) - 40 * k  # 焦点（副反射鏡）
            for t in (0, 2.1, 4.2):
                d.line([(hub[0] + R * .8 * np.cos(t) * np.cos(th), hub[1] - R * .8 * np.cos(t) * np.sin(th) * .9 - R * .28 * np.sin(t)), (fx, fy)], fill=255, width=max(2, int(5 * k)))
            d.ellipse((fx - 16 * k, fy - 12 * k, fx + 16 * k, fy + 12 * k), fill=255)
        a = self._mask(dish, .8)
        img = self.put(img, a, (.03, .033, .045), sky=(.30, .34, .45), rim=4)
        y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        lights = np.zeros((H, W), np.float32)
        for j in range(14): lights[int(gy - 20 * k - self.rng.uniform(0, 30) * k), int(cx - 140 * k + j * 21 * k)] = 1
        red = np.zeros((H, W), np.float32); red[int(hub[1] - R * .55 - 50 * k), int(hub[0] - R * .55 * np.sin(th))] = 1
        return img + self.blur(lights, 1.6)[..., None] * 22 * np.array([1, .78, .45]) + self.blur(red, 2)[..., None] * 40 * np.array([1, .1, .05])

    def rain(self, img, amount=.6, angle=12):
        """雨：細い斜めの筋、かすみ、明かりのにじみ（延期・天候待ちの記事）"""
        img = img * (1 - .25 * amount) + np.array([.10, .11, .13]) * .25 * amount
        m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m); th = np.radians(angle)
        for _ in range(int(5200 * amount)):
            x0, y0 = self.rng.uniform(0, W), self.rng.uniform(0, H); L = self.rng.uniform(30, 90)
            d.line([(x0, y0), (x0 + np.sin(th) * L, y0 + np.cos(th) * L)], fill=int(self.rng.uniform(70, 200)), width=2)
        a = np.asarray(m.filter(ImageFilter.GaussianBlur(.8))).astype(np.float32) / 255
        bright = np.clip(img.max(axis=2) - .4, 0, 1)
        return img + a[..., None] * (.30 + 1.2 * self.blur(bright, 40)[..., None]) * np.array([.85, .9, 1]) + self.blur(bright, 30)[..., None] * np.array([1, .8, .6]) * .5 * amount

    def m_tent(self, img, hz, x=.74, size=1.0, base=.90):
        """星の下のテント：中の明かりで布がやわらかく光る"""
        cx = W * x; by = H * base; w = 260 * size * S / 2; h = 190 * size * S / 2
        y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        body = self._mask(lambda d: d.polygon([(cx - w, by), (cx, by - h), (cx + w, by)], fill=255), .8)
        glow = np.clip(1 - np.sqrt(((xx - cx) / w) ** 2 + ((y - by + h * .35) / h) ** 2), 0, 1)
        fab = (.25 + .9 * glow)[..., None] * np.array([1, .66, .30])
        img = img * (1 - body[..., None]) + body[..., None] * fab
        door = self._mask(lambda d: d.polygon([(cx - w * .18, by), (cx, by - h * .62), (cx + w * .18, by)], fill=255), .6)
        img = img + door[..., None] * np.array([1, .8, .45]) * .8
        pool = np.exp(-(((xx - cx) / (w * 1.6)) ** 2 + ((y - by - 8) / (h * .25)) ** 2)) * (y > by - 4) * .35
        lines = self._mask(lambda d: [d.line([(cx + sx * w * .3, by - h * .7), (cx + sx * w * 1.6, by + 6)], fill=150, width=3) for sx in (-1, 1)], .5)
        return img + pool[..., None] * np.array([1, .6, .25]) - lines[..., None] * .05

    def m_deck(self, img, hz, people=3):
        """展望デッキ：手前に手すり、海を見る人の影（特定の人ではない）"""
        fy = H * .84
        def rail(d):
            for xx in np.arange(W * .52, W + 1, W * .095): d.rectangle((xx, H * .70, xx + 10, H), fill=255)
            d.rectangle((W * .50, H * .690, W, H * .708), fill=255); d.rectangle((W * .50, H * .80, W, H * .808), fill=255)
        def ppl(d):
            spots = [(.62, .80, 0), (.69, .58, 0), (.82, .86, 1), (.90, .80, 0)][:people]
            for px, sc, point in spots:
                X = W * px; hh = H * .36 * sc; u = hh / 8; top = fy - hh  # 8頭身くらい
                d.ellipse((X - u * .45, top, X + u * .45, top + u * 1.05), fill=255)
                d.rectangle((X - u * .18, top + u * .9, X + u * .18, top + u * 1.3), fill=255)
                d.ellipse((X - u * .92, top + u * 1.15, X + u * .92, top + u * 1.95), fill=255)
                d.polygon([(X - u * .90, top + u * 1.55), (X + u * .90, top + u * 1.55), (X + u * .62, top + u * 4.0), (X - u * .62, top + u * 4.0)], fill=255)
                d.polygon([(X - u * .66, top + u * 3.9), (X + u * .66, top + u * 3.9), (X + u * .55, fy), (X + u * .12, fy), (X, top + u * 4.9), (X - u * .12, fy), (X - u * .55, fy)], fill=255)
                for sx in (-1, 1):
                    if point and sx == 1: d.line([(X + u * .75, top + u * 1.6), (X + u * 2.4, top - u * .1)], fill=255, width=int(u * .30))
                    else: d.line([(X + sx * u * .80, top + u * 1.55), (X + sx * u * .98, top + u * 4.0)], fill=255, width=int(u * .30))
        img = self.put(img, self._mask(ppl, .8), (.008, .009, .014), sky=(.30, .22, .22), rim=4)
        return self.put(img, self._mask(rail, .6), (.006, .007, .011), sky=(.35, .26, .24), rim=3)

    def m_gear(self, img, items, hz, lamp=None):
        """持ち物を手前に置く（chair・backpack・thermos・mug・binoculars・bench・headlamp）。x は横の位置、size は大きさ"""
        fy = H * .99
        for it in items:
            k = it["type"]; X = W * it.get("x", .75); sz = it.get("size", 1.0) * H; base = H * it.get("y", .99)
            def shp(d, k=k, X=X, sz=sz, base=base):
                if k == "chair":
                    h = sz * .42; w = h * .62; seat = base - h * .45
                    d.line([(X - w * .5, base), (X + w * .5, seat)], fill=255, width=10); d.line([(X + w * .5, base), (X - w * .5, seat)], fill=255, width=10)
                    d.polygon([(X - w * .55, seat - 8), (X + w * .55, seat - 8), (X + w * .5, seat + 14), (X - w * .5, seat + 14)], fill=255)
                    d.polygon([(X + w * .30, seat), (X + w * .55, seat), (X + w * .78, base - h), (X + w * .48, base - h)], fill=255)
                    d.line([(X - w * .55, seat - h * .12), (X + w * .35, seat - h * .12)], fill=255, width=8)
                elif k == "backpack":
                    h = sz * .26; w = h * .72
                    d.rounded_rectangle((X - w / 2, base - h, X + w / 2, base), radius=int(w * .3), fill=255)
                    d.rounded_rectangle((X - w * .56, base - h * 1.04, X + w * .56, base - h * .72), radius=int(w * .3), fill=255)
                    d.arc((X - w * .2, base - h * 1.25, X + w * .2, base - h * .95), 180, 360, fill=255, width=8)
                elif k == "thermos":
                    h = sz * .24; w = h * .30
                    d.rounded_rectangle((X - w / 2, base - h, X + w / 2, base), radius=int(w * .25), fill=255)
                    d.rounded_rectangle((X - w * .42, base - h * 1.12, X + w * .42, base - h * .96), radius=6, fill=255)
                elif k == "mug":
                    h = sz * .09; w = h * 1.0
                    d.polygon([(X - w / 2, base - h), (X + w / 2, base - h), (X + w * .44, base), (X - w * .44, base)], fill=255)
                    d.arc((X + w * .28, base - h * .85, X + w * .82, base - h * .25), 270, 90, fill=255, width=9)
                elif k == "binoculars":  # こちらを向いて置いた双眼鏡（対物レンズが2つ見える）
                    r = sz * .075
                    d.rounded_rectangle((X - r * 2.25, base - r * 2.3, X + r * 2.25, base), radius=int(r * .9), fill=255)
                    d.rounded_rectangle((X - r * .5, base - r * 2.75, X + r * .5, base - r * 1.6), radius=int(r * .3), fill=255)
                elif k == "bench":
                    top = base; d.rectangle((W * it.get("x0", .40), top, W * 1.02, top + 26), fill=255)
                    d.rectangle((W * it.get("x0", .40), top + 34, W * 1.02, top + 50), fill=255)
                    for lx in (W * (it.get("x0", .40) + .05), W * .92): d.rectangle((lx, top, lx + 22, H), fill=255)
                elif k == "sheet":  # 地面に敷いたレジャーシート（遠近）と、丸めた毛布
                    w = sz * .55
                    d.polygon([(X - w * .30, base - sz * .07), (X + w * .40, base - sz * .07), (X + w * .70, base), (X - w * .65, base)], fill=255)
                    d.ellipse((X + w * .02, base - sz * .085, X + w * .30, base - sz * .045), fill=255)
                elif k == "headlamp":
                    d.rounded_rectangle((X - 34, base - 30, X + 34, base), radius=10, fill=255)
                    d.arc((X - 90, base - 60, X + 90, base + 30), 160, 20, fill=255, width=10)
            a = self._mask(shp, .8)
            img = self.put(img, a, lamp=lamp, sky=(.22, .26, .36) if k != "bench" else (.34, .38, .48))
            if k == "sheet":  # シートの格子柄（うっすら）
                w = sz * .55; y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
                stripes = (np.sin((xx - X + (y - base) * 1.4) / 14) > .55).astype(np.float32) * a * (y > base - sz * .07)
                img = img + stripes[..., None] * np.array([.035, .02, .02])
            if k == "binoculars":
                r = sz * .075; y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
                for cxl in (X - r * 1.12, X + r * 1.12):
                    dd = np.sqrt((xx - cxl) ** 2 + (y - (base - r * 1.15)) ** 2); lens = np.clip(r * .88 - dd, 0, 1)
                    glass = np.clip(.10 + .25 * (base - r * 1.15 - y) / r, 0, .4)[..., None] * np.array([.45, .55, .9])
                    ring = np.exp(-((dd - r * .9) / 3) ** 2) * .5
                    hl = np.exp(-(((xx - cxl + r * .35) / (r * .16)) ** 2 + ((y - base + r * 1.55) / (r * .10)) ** 2)) * .9
                    img = img * (1 - lens[..., None]) + lens[..., None] * glass + (ring + hl * lens)[..., None] * np.array([.9, .85, 1])
            if k == "mug" and it.get("steam", True):
                st = self.lowres_noise(18, 6, sx=.4, sy=1, octaves=4); y, xx = np.mgrid[0:H, 0:W].astype(np.float32)
                h = sz * .09; env = np.exp(-((xx - X - np.sin(y / 60) * 18) / (h * .35)) ** 2) * np.clip((base - h - y) / (h * 3.2), 0, 1) * np.clip(1 - (base - h - y) / (h * 3.2), 0, 1) * (y < base - h)
                img = img + (env * np.clip(st * 1.6 - .5, 0, 1) * .55)[..., None] * np.array([.75, .78, .85])
            if k == "headlamp":
                img = self.lamp_glow(img, X + 34, base - 15, tuple(it.get("color", (1, .12, .06))), 1.0, hz)
        return img

    def compose(self, c):
        hz = c.get("horizon", .76); tone = c.get("tone", "night"); motifs = [m if isinstance(m, dict) else {"type": m} for m in c.get("motifs", [])]
        types = [m["type"] for m in motifs]
        # 空
        if tone == "dawn":
            t = np.clip(self.yy / (hz + .02), 0, 1)
            img = np.where((t < .5)[..., None], self.lerp((.008, .014, .045), (.07, .08, .24), t / .5),
                           np.where((t < .82)[..., None], self.lerp((.07, .08, .24), (.48, .27, .38), (t - .5) / .32), self.lerp((.48, .27, .38), (1, .58, .30), np.clip((t - .82) / .18, 0, 1))))
        elif tone == "dusk":
            t = np.clip(self.yy / hz, 0, 1)
            img = np.where((t < .55)[..., None], self.lerp((.015, .03, .09), (.05, .15, .30), t / .55), self.lerp((.05, .15, .30), (.62, .46, .52), (t - .55) / .45))
        elif tone == "bluehour":
            img = self.lerp((.01, .02, .07), (.10, .22, .42), np.clip(self.yy / hz, 0, 1) ** 1.3)
        elif tone == "day":  # 昼の打ち上げ：青空と白い噴煙
            t = np.clip(self.yy / hz, 0, 1)
            img = self.lerp((.07, .22, .52), (.48, .64, .82), t ** 1.25)
            if c.get("sun"):
                sx, sy = c["sun"]; y, x = np.mgrid[0:H, 0:W].astype(np.float32); d = np.sqrt(((x - W * sx) / W) ** 2 + ((y - H * sy) / W) ** 2)
                img = img + (np.exp(-d * 12) * .30 + np.exp(-d * 70) * .8)[..., None] * np.array([1, .95, .82])
        elif tone == "moonlit":
            img = self.lerp((.02, .04, .09), (.13, .20, .32), np.clip(self.yy / hz, 0, 1) ** 1.2)
        else:
            img = self.lerp((.006, .010, .028), (.05, .085, .16), np.clip(self.yy / hz, 0, 1) ** 1.7)
        dark = tone in ("night", "moonlit")
        if "startrail" in types:
            img = img + (self.startrail_sky() - self.lerp((.01, .012, .03), (.05, .07, .13), np.clip(self.yy, 0, 1) ** 1.4))
        else:
            if dark and c.get("milky", True):
                mw = c.get("milkyway", {}); img = self.milky_real(img, mw.get("cx", .45), mw.get("cy", .30), mw.get("angle", -62), mw.get("width", .17), strength=.6 if tone == "moonlit" else 1)
            img = self.stars_real(img, c.get("stars", {"night": 5200, "moonlit": 1800, "bluehour": 900, "dusk": 700, "dawn": 1800, "day": 0}[tone]), hz, 1.0 if dark else .7)
        if dark: img = self.airglow(img, hz)
        if c.get("glow") is not None: img = self.lightdome(img, c["glow"], hz, c.get("glowStrength", 1.0))
        # 空のモチーフ
        for mo in motifs:
            k = mo["type"]
            if k == "meteors": img = self.m_meteors(img, mo.get("rx", .70), mo.get("ry", .18), min(mo.get("n", 2), 3), hz)
            elif k == "constellation": img = self.m_constellation(img, mo.get("name", "orion"), mo.get("cx", .70), mo.get("cy", .30), mo.get("scale", 1), mo.get("radiant"), mo.get("lines", False))
            elif k in ("moon", "bigmoon"): img = self.m_moon(img, mo.get("cx", .72), mo.get("cy", .28 if k == "moon" else hz - .12), mo.get("r", 110 if k == "moon" else 260), k == "bigmoon")
            elif k == "planets": img = self.m_planets(img, mo.get("cx", .68), mo.get("cy", .42))
            elif k == "eclipse": img = self.m_eclipse(img, mo.get("cx", .70), mo.get("cy", .30), mo.get("r", 90), mo.get("sequence", False))
            elif k == "comet": img = self.m_comet(img, mo.get("cx", .68), mo.get("cy", .30), mo.get("angle", -35), mo.get("length", .30))
            elif k == "iss": img = self.m_straight(img, (mo.get("x0", .30), mo.get("y0", .62)), (mo.get("x1", .95), mo.get("y1", .12)))
            elif k == "starlink": img = self.m_straight(img, (mo.get("x0", .40), mo.get("y0", .20)), (mo.get("x1", .90), mo.get("y1", .38)), dots=True)
        trail_x = None
        for mo in motifs:
            if mo["type"] == "trail":
                img, tip = self.trail_real(img, hz, mo.get("x", .60), mo.get("side", 1), mo.get("height", .74), mo.get("strength", 1.0), mo.get("curve", .33))
                trail_x = W * mo.get("x", .60)
                if mo.get("plume"): img = self.jellyfish(img, tip[0], tip[1], mo.get("plumeSize", 320))
                if mo.get("separation"): img = self.separation(img, self._trail)
            elif mo["type"] == "smoke":
                img = self.smoke(img, hz, mo.get("x", .58), mo.get("side", 1), mo.get("height", .72), mo.get("curve", .22), mo.get("drift", .06), mo.get("width", 1.0))
                trail_x = W * mo.get("x", .58)
            # 何本ものロケットが同時に上がる絵は描かない（ありえないため）。軌跡は1本だけ
        if c.get("clouds"):
            cl = c["clouds"]; img = self.clouds(img, cl.get("y0", hz - .16), cl.get("y1", hz - .02), tuple(cl.get("lit", (.9, .6, .45) if tone in ("dawn", "dusk") else (.95, .97, 1) if tone == "day" else (.35, .4, .5))), cl.get("density", .55))
            if cl.get("litByTrail") and getattr(self, "_trail", None):  # 光跡が雲の中を通り、雲が内側から照らされる
                m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).line(self._trail, fill=255, width=60)
                g = np.asarray(m.filter(ImageFilter.GaussianBlur(70))).astype(np.float32) / 255; glow = np.clip(g / max(g.max(), 1e-6) * 1.6, 0, 1.2)
                img = img + (glow * np.clip(self._cloud_a * 2.2, 0, 1) * .7)[..., None] * np.array([1, .55, .22])
        # 地上
        g = c.get("ground", "hills")
        if g in ("sea", "island", "lake"):
            img = self.sea_real(img, hz, trail_x)
            if g == "island":
                hzp = int(H * hz); xs = np.arange(int(W * .04), int(W * .64), 6)
                prof = hzp - 22 - 30 * np.exp(-((xs - W * .22) / (W * .10)) ** 2) - 6 * np.sin(xs / 37) - 12 * np.exp(-((xs - W * .46) / (W * .05)) ** 2)
                img = self.silhouette(img, [(W * .04, hzp + 1)] + [(float(x), float(p)) for x, p in zip(xs, prof)] + [(W * .64, hzp + 1)], (.012, .014, .024))
                lights = np.zeros((H, W), np.float32)
                for _ in range(26): lights[int(hzp - self.rng.uniform(3, 14)), int(self.rng.uniform(W * .08, W * .6))] = 1
                img = img + self.blur(lights, 1.6)[..., None] * 18 * np.array([1, .75, .42])
            elif g == "lake":
                img = self.mountains(img, hz, 2, 120, trees=True)
            else:
                xs = np.arange(0, int(W * .40), 6); hzp = int(H * hz)
                prof = hzp - 70 - 120 * np.exp(-((xs - W * .12) / (W * .11)) ** 2) - 30 * np.sin(xs / 57) * np.exp(-xs / 700) + (xs / (W * .40)) ** 2 * 80
                img = self.silhouette(img, [(0, hzp + 1)] + [(float(x), float(p)) for x, p in zip(xs, prof)] + [(W * .40, hzp + 1)])
        elif g == "city":
            img = self.mountains(img, hz - .03, 1, 60)
            img = self.ground(img, "city", hz, None)
        elif g in ("mountains", "forest"):
            img = self.mountains(img, hz, 3, c.get("rough", 170), trees=(g == "forest"))
        else:
            img = self.mountains(img, hz, 2, 60)
        for mo in motifs:
            if mo["type"] == "liftoff": img = self.liftoff(img, hz, mo.get("x", .66), mo.get("scale", 1.0), mo.get("rise", .35), tone)
        lamp = next(((W * m.get("x", .7) + 34, H * m.get("y", .99) - 15, tuple(m.get("color", (1, .12, .06))), m.get("strength", 1.0))
                     for m in motifs if m["type"] == "headlamp"), None)
        gear = [m for m in motifs if m["type"] in ("chair", "backpack", "thermos", "mug", "binoculars", "bench", "headlamp", "sheet")]
        for mo in motifs:
            k = mo["type"]
            if k in ("dome", "tripod", "phone"): img = self.m_object(img, k, hz, mo.get("x", .72))
            elif k == "pad": img = self.m_pad(img, hz, mo.get("x", .66), mo.get("scale", 1.0), g in ("sea", "island", "lake"))
            elif k == "observatory": img = self.m_observatory(img, hz, mo.get("x", .72), mo.get("size", 1.0))
            elif k == "planetarium": img = self.m_planetarium(img, hz, mo.get("x", .68), mo.get("size", 1.0))
            elif k == "deck": img = self.m_deck(img, hz, mo.get("people", 3))
            elif k == "lighthouse": img = self.m_lighthouse(img, hz, mo.get("x", .78), mo.get("size", 1.0), mo.get("beam", -1))
            elif k == "antenna": img = self.m_antenna(img, hz, mo.get("x", .70), mo.get("size", 1.0), mo.get("tilt", 35))
            elif k == "tent": img = self.m_tent(img, hz, mo.get("x", .74), mo.get("size", 1.0), mo.get("y", .90))
        if gear: img = self.m_gear(img, sorted(gear, key=lambda m: (m["type"] != "bench", m["type"] != "sheet")), hz, lamp)
        if c.get("rain"): img = self.rain(img, c["rain"].get("amount", .6), c["rain"].get("angle", 12))
        return img

    def startrail_sky(self):
        img = self.lerp((.01, .012, .03), (.05, .07, .13), np.clip(self.yy, 0, 1) ** 1.4)
        lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay); cx, cy = W * 0.80, -H * 0.15
        for _ in range(620):
            rad = self.rng.uniform(80, W * 1.1); a0 = self.rng.uniform(0, 2 * np.pi)
            d.arc((cx - rad, cy - rad, cx + rad, cy + rad), np.degrees(a0), np.degrees(a0 + 0.22), fill=int(self.rng.power(5) * 255), width=2)
        a = np.asarray(lay).astype(np.float32) / 255
        return img + (a + self.blur(a, 2) * 1.5)[..., None] * np.array([.85, .9, 1.0]) * 0.9


SCENES = {"launch": ["sea", "startrail"], "sky": ["meteor", "moon"], "spot": ["observatory", "dawn"], "gear": ["tripod"]}
LABEL = {"launch": "LAUNCH", "sky": "SKY", "spot": "SPOT", "gear": "GEAR"}


# ---------- 文字 ----------
def split_title(t):
    """先頭の【…】は小見出し、途中の【…】と「｜」より後ろは副題にする。"""
    t = t.strip(); kicker = ""
    m = re.match(r"^【([^】]+)】\s*", t)
    if m: kicker, t = m.group(1), t[m.end():]
    parts = re.split(r"[｜|]", t, maxsplit=1)
    main = parts[0].strip(); sub = parts[1].strip() if len(parts) > 1 else ""
    m = re.search(r"【([^】]+)】", main)
    if m:
        rest = main[m.end():].strip()
        sub = "・".join(x for x in [m.group(1), rest, sub] if x)
        main = main[:m.start()].strip()
    return kicker, main, sub


def summarize(main, limit=16):
    """長いタイトルを見出し用に短くする（括弧の中を外し、文節の切れ目で limit 字まで）。
    本当は作成エージェントが spec の headline に要約を書く。これは無いときの代わり。"""
    t = re.sub(r"（[^）]*）|\([^)]*\)", "", main).strip()
    if len(t) <= limit: return t
    m = re.match(r"^(.+?[？?])", t)
    if m and len(m.group(1)) <= limit + 2: return m.group(1)
    out = ""
    for c in chunks(t):
        if len(out + c) > limit: break
        out += c
    return out or t[:limit]


NO_START = set("、。，．・：；？！ー）」』】〕ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ々")
NO_END = set("（「『【〔")


def chunks(text):
    """文節に分ける（BudouX。無ければ1文字ずつ）。"""
    try:
        import budoux
        return budoux.load_default_japanese_parser().parse(text)
    except Exception:
        return list(text)


def wrap_chars(text, fnt, maxw, d):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=fnt) <= maxw or not cur or ch in NO_START:
            cur += ch; continue
        if cur[-1] in NO_END:
            lines.append(cur[:-1]); cur = cur[-1] + ch; continue
        lines.append(cur); cur = ch
    if cur: lines.append(cur)
    return lines


def wrap(text, fnt, maxw, d):
    """文節の切れ目で折り返す。1つの文節が長すぎるときだけ文字で折る。2行になるときは長さを釣り合わせる。"""
    cs = chunks(text); lines, cur = [], ""; wrap.broke = False
    for c in cs:
        if d.textlength(cur + c, font=fnt) <= maxw:
            cur += c; continue
        if cur: lines.append(cur); cur = ""
        if d.textlength(c, font=fnt) <= maxw: cur = c
        else:
            parts = wrap_chars(c, fnt, maxw, d); lines += parts[:-1]; cur = parts[-1]; wrap.broke = True
    if cur: lines.append(cur)
    if len(lines) == 2 and len(cs) > 1:  # 2行なら、両方が収まる中でいちばん釣り合う切れ目を選ぶ
        best = None
        for i in range(1, len(cs)):
            l1, l2 = "".join(cs[:i]), "".join(cs[i:])
            w1, w2 = d.textlength(l1, font=fnt), d.textlength(l2, font=fnt)
            if w1 <= maxw and w2 <= maxw:
                score = max(w1, w2) + (0 if w1 >= w2 * 0.8 else (w2 - w1) * 0.3)
                if best is None or score < best[0]: best = (score, [l1, l2])
        if best: lines = best[1]
    return lines


def fit(text, kind, sizes, maxw, maxlines, d):
    """文節を割らずに maxlines 行に収まる、いちばん大きい文字の大きさを選ぶ。無ければ割ってでも収まるもの。"""
    first = None
    for sz in sizes:
        f = font(kind, sz); ls = wrap(text, f, maxw * S, d)
        if len(ls) <= maxlines:
            if not wrap.broke: return f, ls, sz
            first = first or (f, ls, sz)
    return first or (f, ls[:maxlines], sz)


def spaced(d, xy, text, fnt, fill, track=0.18):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill); x += d.textlength(ch, font=fnt) + fnt.size * track
    return x


def textlen_spaced(d, text, fnt, track=0.18):
    return sum(d.textlength(ch, font=fnt) + fnt.size * track for ch in text)


def shadowed(base, draw_fn, radius=18, alpha=150):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(sh), (0, 0, 0, alpha))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius)))
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(lay), None); base.alpha_composite(lay)


VROT = set("ー－―〜～…‥()（）「」『』【】〔〕[]｛｝<>＜＞=＝-")


def vtokens(text):
    """縦書きの単位に分ける（半角の英数字は2〜3字なら縦中横、長ければ横倒し）"""
    toks = []
    for m in re.finditer(r"[A-Za-z0-9./:]+|.", text):
        toks.append(m.group(0))
    return toks


def draw_vertical(img, x, y, text, fnt, fill, lead=1.12):
    """右上の (x, y) を始点に、上から下へ縦に書く。x は列の中心。"""
    d = ImageDraw.Draw(img); sz = fnt.size
    for tk in vtokens(text):
        if len(tk) == 1 and not tk.isascii():
            if tk in VROT:
                g = Image.new("RGBA", (sz * 2, sz * 2), (0, 0, 0, 0)); ImageDraw.Draw(g).text((sz // 2, sz // 2), tk, font=fnt, fill=fill)
                g = g.rotate(-90, resample=Image.BICUBIC); img.alpha_composite(g, (int(x - sz), int(y - sz * .55)))
            elif tk in "、。，．":
                d.text((x - sz * .5 + sz * .55, y - sz * .55), tk, font=fnt, fill=fill)
            else:
                d.text((x - d.textlength(tk, font=fnt) / 2, y), tk, font=fnt, fill=fill)
            y += sz * lead
        elif len(tk) <= 3:
            f2 = fnt if len(tk) == 1 else fnt.font_variant(size=int(sz * (0.82 if len(tk) == 2 else 0.62)))
            d.text((x - d.textlength(tk, font=f2) / 2, y + (sz - f2.size) * .4), tk, font=f2, fill=fill)
            y += sz * lead
        else:
            w = int(d.textlength(tk, font=fnt)) + 4
            g = Image.new("RGBA", (w, sz * 2), (0, 0, 0, 0)); ImageDraw.Draw(g).text((0, sz // 3), tk, font=fnt, fill=fill)
            g = g.rotate(-90, expand=True, resample=Image.BICUBIC); img.alpha_composite(g, (int(x - g.width / 2), int(y)))
            y += w + sz * .15
    return y


def render_transit(spec, bg, cat, main, sub, kicker):
    d = ImageDraw.Draw(bg); M = 64 * S
    # 下を少し暗くして文字を読みやすく
    grad = np.zeros((H, W, 4), np.uint8); a = np.clip((np.arange(H) / H - 0.5) / 0.5, 0, 1) ** 1.6 * 120
    grad[..., 3] = a[:, None].astype(np.uint8); bg.alpha_composite(Image.fromarray(grad, "RGBA"))
    # 上：誌名とカテゴリ（小さく）
    mono = font("mono", 12)
    x = spaced(d, (M, 50 * S), "MIAGETABI", mono, (255, 255, 255, 230), .32)
    d.ellipse((x + 10 * S, 54 * S, x + 17 * S, 61 * S), fill=ORANGE)
    spaced(d, (x + 28 * S, 50 * S), (LABEL[cat] + ("  /  " + kicker if kicker else "")), mono, (255, 255, 255, 170), .24)
    # 英語の一文（大きな斜体のセリフ）
    en = spec.get("en") or ""
    if en:
        fe = font("serif_i", 92, 400)
        lines = en.split("\n") if "\n" in en else [en]
        while max(d.textlength(l, font=fe) for l in lines) > 760 * S and fe.size > 50 * S: fe = fe.font_variant(size=int(fe.size * .92))
        y = H - 150 * S - int(fe.size * 1.0) * len(lines)
        def eng(dd, col):
            yy = y
            for l in lines:
                dd.text((M - 4 * S, yy), l, font=fe, fill=col or (255, 252, 245)); yy += int(fe.size * 1.0)
        shadowed(bg, eng, 22, 120); d = ImageDraw.Draw(bg)
    # 下：日時・場所（細いモノスペース）と線
    meta = "  ·  ".join(x for x in [spec.get("date"), spec.get("time"), spec.get("place")] if x)
    d.line((M, H - 104 * S, M + 48 * S, H - 104 * S), fill=(255, 255, 255, 200), width=2 * S)
    if meta: spaced(d, (M, H - 88 * S), meta, font("mono", 14), (255, 255, 255, 230), .16)
    if sub: d.text((M, H - 62 * S), sub, font=font("mincho", 17), fill=(255, 255, 255, 215))
    # 右：日本語の見出しを縦書き（明朝）
    fj = font("mincho", 40)
    vt = len("".join(vtokens(main)))
    while (len(vtokens(main)) * fj.size * 1.12 > H - 150 * S) and fj.size > 26 * S: fj = fj.font_variant(size=int(fj.size * .92))
    cols = [main]
    if len(vtokens(main)) * fj.size * 1.12 > H - 150 * S:  # 長ければ文節で2列に
        cs = chunks(main); half = len(main) / 2; acc = ""; i = 0
        while i < len(cs) and len(acc + cs[i]) <= half + 2: acc += cs[i]; i += 1
        cols = [acc, "".join(cs[i:])]
    xr = W - 84 * S
    def vert(img_, col):
        for k, ctext in enumerate(cols):
            draw_vertical(img_, xr - k * fj.size * 1.6, 92 * S, ctext, fj, col or (255, 255, 255))
    sh = Image.new("RGBA", bg.size, (0, 0, 0, 0)); vert(sh, (0, 0, 0, 150)); bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    vert(bg, None)
    d = ImageDraw.Draw(bg)
    cg = font("mono", 9); spaced(d, (W - M - int(textlen_spaced(d, "CG ILLUSTRATION", cg, .14)), H - 34 * S), "CG ILLUSTRATION", cg, (255, 255, 255, 120), .14)


FORMATS = {"eyecatch": (1200, 630), "x": (1200, 675), "ig": (1080, 1350)}  # アイキャッチ／X（16:9）／Instagram（4:5）


def set_size(fmt):
    global OUT_W, OUT_H, W, H
    OUT_W, OUT_H = FORMATS.get(fmt, FORMATS["eyecatch"]); W, H = OUT_W * S, OUT_H * S


def render(spec, out):
    fmt = spec.get("format", "eyecatch"); set_size(fmt); tall = fmt == "ig"
    cat = spec.get("category", "launch") if spec.get("category") in SCENES else "launch"
    seed = int(spec.get("seed", 1)); layout = spec.get("layout", "cinema")
    scene = spec.get("scene") or SCENES[cat][seed % len(SCENES[cat])]
    sc = Scene(seed)
    if spec.get("composition"):
        img = sc.compose(spec["composition"])
    else:
        img = {"sea": lambda: sc.sea(1 if seed % 2 else -1) if layout == "cinema" else sc.sea(1)}.get(scene, getattr(sc, scene))()
    if spec.get("film", True):  # フィルムのような色・かすみ・光漏れ（エモい写真の空気感）
        img = sc.film(img, (spec.get("composition") or {}).get("horizon", .76) - .02, leak=spec.get("leak", True))
        bg = sc.finish(img, grain=.05, vig=.68).convert("RGBA")
    else:
        bg = sc.finish(img).convert("RGBA")
    kicker0, main, sub = split_title(spec["title"])
    main = spec.get("headline") or summarize(main)
    if not re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", main): main = summarize(split_title(spec["title"])[1])  # 見出しは日本語に統一
    if "sub" in spec: sub = spec["sub"]
    elif len(sub) > 30: sub = summarize(sub, 30)
    kicker = spec.get("kicker") or kicker0
    if spec.get("bignum"):  # 号機・年などの大きな数字（白抜き）
        bn = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bn); bf = font("mono", 460)
        tw = bd.textlength(str(spec["bignum"]), font=bf)
        bd.text((W - tw - 30 * S, H * .02), str(spec["bignum"]), font=bf, fill=(0, 0, 0, 0), stroke_width=2 * S, stroke_fill=(255, 255, 255, 46))
        bg.alpha_composite(bn)
    if layout == "transit" and spec.get("allowTransit"):  # 英語を大きく組む型は使わない（見出しは日本語に統一）
        render_transit(spec, bg, cat, main, sub, kicker)
        bg.convert("RGB").resize((OUT_W, OUT_H), Image.LANCZOS).save(out, quality=88, optimize=True, progressive=True)
        return
    d0 = ImageDraw.Draw(bg); M = 60 * S
    mono_s = font("mono", 13); mono_l = font("mono", 16)
    if layout == "panel":
        pw = 430 * S
        panel = Image.new("RGBA", (pw, H), (11, 11, 16, 255)); bg.alpha_composite(panel, (W - pw, 0))
        d = ImageDraw.Draw(bg); x0 = W - pw + 48 * S
        d.rectangle((x0, 58 * S, x0 + 9 * S, 67 * S), fill=ORANGE)
        spaced(d, (x0 + 20 * S, 54 * S), LABEL[cat], mono_s, (255, 255, 255))
        if kicker: spaced(d, (x0, 150 * S), kicker, font("mono", 12), (255, 255, 255, 150))
        f, ls, sz = fit(main, "black", (50, 46, 42, 38, 34, 32, 30), 334, 4, d)
        y = 180 * S
        for ln in ls:
            d.text((x0, y), ln, font=f, fill=(255, 255, 255)); y += int(f.size * 1.22)
        y += 18 * S; d.rectangle((x0, y, x0 + 56 * S, y + 4 * S), fill=ORANGE); y += 26 * S
        if sub:
            fs, ls2, _ = fit(sub, "medium", (18, 16, 15), 330, 3, d)
            for ln in ls2:
                d.text((x0, y), ln, font=fs, fill=(255, 255, 255, 215)); y += int(fs.size * 1.6)
        if spec.get("date"):
            spaced(d, (x0, H - 92 * S), spec["date"], font("mono", 15), (255, 255, 255), .12)
        if spec.get("time"):
            spaced(d, (x0, H - 66 * S), spec["time"], font("mono", 15), ORANGE, .12)
        spaced(d, (24 * S, H - 30 * S), "CG ILLUSTRATION", font("mono", 10), (255, 255, 255, 140), .14)
    else:
        grad = np.zeros((H, W, 4), np.uint8); a = np.clip((np.arange(H) / H - 0.45) / 0.55, 0, 1) ** 1.3 * 150
        grad[..., 3] = a[:, None].astype(np.uint8); bg.alpha_composite(Image.fromarray(grad, "RGBA"))
        d = ImageDraw.Draw(bg)
        d.rectangle((M, 56 * S, M + 9 * S, 65 * S), fill=ORANGE)
        x = spaced(d, (M + 20 * S, 52 * S), spec.get("label") or LABEL[cat], mono_s, (255, 255, 255))
        if kicker: spaced(d, (x + 14 * S, 52 * S), kicker, mono_s, (255, 255, 255, 160))
        f, ls, sz = fit(main, "black", (84, 76, 68, 60, 54, 48) if tall else (66, 60, 56, 52, 48, 44), 840 if tall else 800, 3 if tall else 2, d)
        foot = 64 * S + (40 * S if spec.get("date") or spec.get("time") else 0) + (30 * S if spec.get("handle") else 0)
        fs = font("medium", 26 if tall else 22)
        subl = []
        if sub:
            fs, subl, _ = fit(sub, "medium", (26, 24, 22) if tall else (22, 20, 19), 900 if tall else 1000, 2, d)
        subh = int(fs.size * 1.5) * len(subl)
        lh = int(f.size * 1.18); y = H - foot - subh - lh * len(ls) - (14 * S if sub else 0)
        en = (spec.get("en") or "").replace("\n", " ").strip()
        if en:  # 英語の一文（TRANSIT のような斜体のセリフ）を見出しの上に小さく
            fe = font("serif_i", 34, 400)
            while d.textlength(en, font=fe) > 760 * S and fe.size > 24 * S: fe = fe.font_variant(size=int(fe.size * .94))
            ye = y - int(fe.size * 1.30)
        bd = spec.get("bigdate")
        if bd:  # イベントの日付を大きく（SNS 画像）
            fb = font("mono", 120 if tall else 70); yb = (ye if en else y) - int(fb.size * 1.25)
        def title(dd, col):
            if bd:
                x2 = dd.textlength(bd, font=fb) + M + 18 * S
                dd.text((M - 4 * S, yb), bd, font=fb, fill=col or (255, 255, 255))
                if spec.get("bigdate_sub"):
                    dd.text((x2, yb + int(fb.size * .58)), spec["bigdate_sub"], font=font("mono", 26 if tall else 18), fill=col or ORANGE)
            if en: dd.text((M + 2 * S, ye), en, font=fe, fill=col or (255, 244, 228, 235))
            yy = y
            for ln in ls:
                dd.text((M, yy), ln, font=f, fill=col or (255, 255, 255)); yy += lh
            yy += 14 * S
            for sl in subl:
                dd.text((M, yy), sl, font=fs, fill=col or (255, 255, 255, 220)); yy += int(fs.size * 1.5)
        shadowed(bg, title)
        d = ImageDraw.Draw(bg)
        if spec.get("date") or spec.get("time"):
            x = M
            if spec.get("date"): x = spaced(d, (M, H - 92 * S), spec["date"], mono_l, (255, 255, 255), .12) + 14 * S
            if spec.get("time"): spaced(d, (x, H - 92 * S), spec["time"], mono_l, ORANGE, .12)
        if spec.get("handle"): spaced(d, (M, H - 58 * S), spec["handle"], font("mono", 13), (255, 255, 255, 190), .10)
        lg = logo_white(22); bg.alpha_composite(lg, (W - M - lg.width, H - 84 * S))
        cg = font("mono", 10); spaced(d, (W - M - int(textlen_spaced(d, "CG ILLUSTRATION", cg, .14)), H - 40 * S), "CG ILLUSTRATION", cg, (255, 255, 255, 140), .14)
    bg.convert("RGB").resize((OUT_W, OUT_H), Image.LANCZOS).save(out, quality=88, optimize=True, progressive=True)


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    render(spec, sys.argv[2] if len(sys.argv) > 2 else "eyecatch.jpg")
    print("ok", sys.argv[2] if len(sys.argv) > 2 else "eyecatch.jpg")
