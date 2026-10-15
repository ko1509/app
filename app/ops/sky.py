#!/usr/bin/env python3
"""ミアゲタビの記事用の天体計算（日本時間）。

記事の「何時に・どの方角・どのくらいの高さ」を、暗算ではなくこの道具で出す。
結果は国立天文台（ほしぞら情報・暦計算室）の記述と食い違わないか、必ず照らし合わせる。

準備:  pip install ephem==4.2   （ネットから天体暦を落とす必要はない）

使い方の例:
  python3 sky.py weekday 2026-12-14
  python3 sky.py moon 2026-12-14                 # 月の出・月の入り・月齢・明るさ（東京）
  python3 sky.py moon 2026-12-14 --city osaka
  python3 sky.py sun 2026-12-14                  # 日の出・日の入り・天文薄明
  python3 sky.py radiant geminids "2026-12-15 00:00"     # 放射点の方角と高さ（5都市）
  python3 sky.py body mars "2026-11-16 02:00"    # 惑星・月の方角と高さ（5都市）
  python3 sky.py ut2jst "2027-08-13 08:00"       # 世界時 → 日本時間
  python3 sky.py hours geminids 2026-12-14       # 夜の1時間ごとの放射点の高さと月（東京）

出力の方角は16方位（北・北北東…）と度（北=0°、東=90°）。高さは地平線からの角度（度）。
"""
import argparse
import datetime as dt
import math
import sys

try:
    import ephem
except ImportError:  # pragma: no cover
    sys.exit("ephem が入っていません: pip install ephem==4.2")

JST = dt.timezone(dt.timedelta(hours=9))
WD = "月火水木金土日"

# 都市の位置（市役所・都庁付近。緯度・経度は度、標高 m）
CITIES = {
    "sapporo": ("札幌", 43.0621, 141.3544, 20),
    "tokyo": ("東京", 35.6895, 139.6917, 40),
    "osaka": ("大阪", 34.6937, 135.5023, 10),
    "fukuoka": ("福岡", 33.5904, 130.4017, 10),
    "naha": ("那覇", 26.2124, 127.6809, 10),
    "tanegashima": ("種子島（南種子町）", 30.3778, 130.9619, 50),
}

# 主な流星群の放射点（極大のころ。赤経・赤緯は度、J2000）。
# 出典：IMO Meteor Shower Calendar（https://www.imo.net/resources/calendar/）の値の目安。
# 記事に使う前に、その年の IMO カレンダーで値を確かめ、違えば --ra --dec で上書きする。
RADIANTS = {
    "quadrantids": ("しぶんぎ座流星群", 230.0, 49.0),
    "lyrids": ("こと座流星群", 271.0, 34.0),
    "eta-aquariids": ("みずがめ座η流星群", 338.0, -1.0),
    "perseids": ("ペルセウス座流星群", 48.0, 58.0),
    "orionids": ("オリオン座流星群", 95.0, 16.0),
    "leonids": ("しし座流星群", 152.0, 22.0),
    "geminids": ("ふたご座流星群", 112.0, 33.0),
}

BODIES = {
    "moon": ("月", ephem.Moon), "mercury": ("水星", ephem.Mercury), "venus": ("金星", ephem.Venus),
    "mars": ("火星", ephem.Mars), "jupiter": ("木星", ephem.Jupiter), "saturn": ("土星", ephem.Saturn),
    "sun": ("太陽", ephem.Sun),
}

DIRS = ["北", "北北東", "北東", "東北東", "東", "東南東", "南東", "南南東",
        "南", "南南西", "南西", "西南西", "西", "西北西", "北西", "北北西"]


def direction(az_deg: float) -> str:
    return DIRS[int((az_deg + 11.25) // 22.5) % 16]


def parse_jst(s: str) -> dt.datetime:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, fmt).replace(tzinfo=JST)
        except ValueError:
            pass
    sys.exit(f"日時の形が読めません: {s}（例 2026-12-15 00:00）")


def fmt_jst(d: dt.datetime) -> str:
    d = d.astimezone(JST)
    return f"{d.year}年{d.month}月{d.day}日（{WD[d.weekday()]}）{d.hour}:{d.minute:02d}"


def observer(city: str, when: dt.datetime) -> ephem.Observer:
    _, lat, lon, elev = CITIES[city]
    o = ephem.Observer()
    o.lat, o.lon, o.elevation = str(lat), str(lon), elev
    o.date = ephem.Date(when.astimezone(dt.timezone.utc).replace(tzinfo=None))
    o.pressure = 0  # 大気差を入れない（出入りは下で地平線の補正を入れる）
    return o


def hm(d) -> str:
    """時:分 だけ（無ければ「なし」）。"""
    if not d:
        return "なし"
    d = d.astimezone(JST)
    return f"{d.hour}:{d.minute:02d}"


def to_jst(d: ephem.Date) -> dt.datetime:
    return d.datetime().replace(tzinfo=dt.timezone.utc).astimezone(JST)


def altaz_fixed(city, when, ra_deg, dec_deg):
    o = observer(city, when)
    star = ephem.FixedBody()
    star._ra, star._dec, star._epoch = math.radians(ra_deg), math.radians(dec_deg), ephem.J2000
    star.compute(o)
    return math.degrees(star.az), math.degrees(star.alt)


def altaz_body(city, when, key):
    o = observer(city, when)
    b = BODIES[key][1]()
    b.compute(o)
    return math.degrees(b.az), math.degrees(b.alt)


def rise_set(city, day: dt.date, key, horizon="-0:34"):
    """その日（日本時間 0:00〜24:00）の出・南中・入り。"""
    start = dt.datetime(day.year, day.month, day.day, tzinfo=JST)
    o = observer(city, start)
    o.horizon = horizon
    o.pressure = 1010
    b = BODIES[key][1]()
    out = {}
    for name, fn in (("出", o.next_rising), ("南中", o.next_transit), ("入り", o.next_setting)):
        try:
            t = to_jst(fn(b, start=o.date))
            out[name] = t if t.date() == day else None
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            out[name] = None
    return out


def cmd_weekday(a):
    d = parse_jst(a.date)
    print(f"{d.year}年{d.month}月{d.day}日は{WD[d.weekday()]}曜日")


def cmd_ut2jst(a):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            u = dt.datetime.strptime(a.ut, fmt).replace(tzinfo=dt.timezone.utc)
            break
        except ValueError:
            u = None
    if not u:
        sys.exit("例: 2027-08-13 08:00")
    print(f"世界時 {a.ut} = 日本時間 {fmt_jst(u)}")


def cmd_moon(a):
    day = parse_jst(a.date).date()
    city = a.city
    rs = rise_set(city, day, "moon", horizon="0")
    noon = dt.datetime(day.year, day.month, day.day, 21, 0, tzinfo=JST)
    m = ephem.Moon(observer(city, noon))
    prev_new = ephem.previous_new_moon(observer(city, noon).date)
    age = observer(city, noon).date - prev_new
    print(f"{CITIES[city][0]}・{day.year}年{day.month}月{day.day}日（{WD[day.weekday()]}）の月")
    for k in ("出", "南中", "入り"):
        print(f"  月の{k}: {hm(rs[k]) if rs[k] else 'この日はなし'}")
    print(f"  21時の月齢: {age:.1f}　輝面比（明るく見える割合）: {m.phase:.0f}%")


def cmd_sun(a):
    day = parse_jst(a.date).date()
    rs = rise_set(a.city, day, "sun")
    tw = rise_set(a.city, day, "sun", horizon="-18")
    print(f"{CITIES[a.city][0]}・{day}")
    print(f"  日の出 {hm(rs['出'])}　日の入り {hm(rs['入り'])}")
    print(f"  天文薄明の終わり（夜が暗くなる）{hm(tw['入り'])}　始まり（明るくなり始める）{hm(tw['出'])}")


def cmd_radiant(a):
    when = parse_jst(a.when)
    name, ra, dec = RADIANTS[a.shower]
    ra = a.ra if a.ra is not None else ra
    dec = a.dec if a.dec is not None else dec
    print(f"{name}の放射点（赤経{ra}° 赤緯{dec}°）　{fmt_jst(when)}")
    for c in ("sapporo", "tokyo", "osaka", "fukuoka", "naha"):
        az, alt = altaz_fixed(c, when, ra, dec)
        print(f"  {CITIES[c][0]}: {direction(az)}（{az:.0f}°）の空、高さ {alt:.0f}°" + ("（地平線の下）" if alt < 0 else ""))


def cmd_body(a):
    when = parse_jst(a.when)
    print(f"{BODIES[a.body][0]}　{fmt_jst(when)}")
    for c in ("sapporo", "tokyo", "osaka", "fukuoka", "naha"):
        az, alt = altaz_body(c, when, a.body)
        print(f"  {CITIES[c][0]}: {direction(az)}（{az:.0f}°）の空、高さ {alt:.0f}°" + ("（地平線の下）" if alt < 0 else ""))


def cmd_hours(a):
    day = parse_jst(a.date).date()
    name, ra, dec = RADIANTS[a.shower]
    print(f"{name}・{CITIES[a.city][0]}・{day} の夜（放射点の高さ／月の高さ）")
    for h in range(18, 31):
        t = dt.datetime(day.year, day.month, day.day, tzinfo=JST) + dt.timedelta(hours=h)
        _, ralt = altaz_fixed(a.city, t, ra, dec)
        _, malt = altaz_body(a.city, t, "moon")
        _, salt = altaz_body(a.city, t, "sun")
        sky = "暗い" if salt < -18 else ("薄明" if salt < -6 else "明るい")
        print(f"  {t.month}/{t.day}({WD[t.weekday()]}) {t.hour:2d}時  放射点 {ralt:5.0f}°  月 {malt:5.0f}°{'（沈んでいる）' if malt < 0 else ''}  空:{sky}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("weekday"); s.add_argument("date"); s.set_defaults(f=cmd_weekday)
    s = sp.add_parser("ut2jst"); s.add_argument("ut"); s.set_defaults(f=cmd_ut2jst)
    for name, fn in (("moon", cmd_moon), ("sun", cmd_sun)):
        s = sp.add_parser(name); s.add_argument("date"); s.add_argument("--city", default="tokyo", choices=CITIES); s.set_defaults(f=fn)
    s = sp.add_parser("radiant"); s.add_argument("shower", choices=RADIANTS); s.add_argument("when")
    s.add_argument("--ra", type=float); s.add_argument("--dec", type=float); s.set_defaults(f=cmd_radiant)
    s = sp.add_parser("body"); s.add_argument("body", choices=BODIES); s.add_argument("when"); s.set_defaults(f=cmd_body)
    s = sp.add_parser("hours"); s.add_argument("shower", choices=RADIANTS); s.add_argument("date")
    s.add_argument("--city", default="tokyo", choices=CITIES); s.set_defaults(f=cmd_hours)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
