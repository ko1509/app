#!/usr/bin/env python3
"""トップページ（ホーム）の「いま変わるところ」だけを、安全に書き換える。サイト更新エージェント用。

書き換えるのは次の3か所だけ（それ以外のHTMLには触らない）：
  1. NEXT LAUNCH のカウントダウンの <script>（id="mgCount" を使っているもの）と、表の静的な表示（名前・日付）
  2. ティッカー（class="mg-ticker__track"）
  3. UPCOMING（<ol class="mg-cal">）：過ぎた日の行を外す／新しい行を足す／既存の行の日付や文を直す

使い方（認証情報は環境変数。値は表示・保存しない）:
  python3 site_home.py plan  launches.json ops.json [--html file.html] [--out new.html]   # 差分を出すだけ（既定は公開ページから取る）
  python3 site_home.py apply launches.json ops.json                                    # 取得 → 書き換え → 検査 → 保存 → 公開ページで確認（失敗なら元に戻す）
  python3 site_home.py rollback backup.json                                            # バックアップに戻す
環境変数: MIAGETABI_WP_USER / MIAGETABI_WP_APP_PASSWORD（WordPress のアプリケーションパスワード）。MIAGETABI_WP_HOME_ID（ホームの固定ページ ID。無ければ自動で探す）

ops.json（サイト更新エージェントが、公式ページで確かめた内容から作る）:
  {"add":   [{"date":"2027-01-04","tag":"sky|launch","title":"しぶんぎ座流星群","small":"未明が見ごろ…","star":"★★★☆☆|PICK|現地 / 中継","guide":"/sky/…（無ければ空）","pick":false,"ticker":"QUADRANTIDS — 01.04"}],
   "edit":  [{"match":"H3ロケット11号機","date":"2026-11-12","small":"…","title":"…","ticker":"…"}],
   "remove":[{"match":"…"}]}
"""
import base64, datetime as dt, difflib, json, os, re, sys, urllib.request, urllib.error

BASE = "https://miagetabi.space"
JST = dt.timezone(dt.timedelta(hours=9))
WD = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from home_countdown import build as build_countdown


def today():
    return dt.datetime.now(JST).date()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------- UPCOMING ----------
LI = re.compile(r"<li\b[^>]*>.*?</li>", re.S)


def li_date(li, ref):
    m = re.search(r"<time>\s*(\d{1,2})\.(\d{1,2})", li)
    if not m:
        return None
    mo, d = int(m.group(1)), int(m.group(2))
    y = ref.year
    try:
        x = dt.date(y, mo, d)
    except ValueError:
        return None
    if x < ref - dt.timedelta(days=200): x = dt.date(y + 1, mo, d)  # 年またぎ
    return x


def li_title(li):
    m = re.search(r'<p class="mg-cal__t">(.*?)<small>', li, re.S)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""


def make_li(it):
    d = dt.date.fromisoformat(it["date"]); tag = it.get("tag", "sky")
    t = esc(it["title"])
    if it.get("guide"): t = f'<a href="{esc(it["guide"])}">{t}</a>'
    cls = ' class="-pick"' if it.get("pick") else ""
    return (f'<li{cls}><time>{d.month:02d}.{d.day:02d}<small>{WD[d.weekday()]}</small></time><span class="mg-tag -{tag}">{tag.upper()}</span>'
            f'<p class="mg-cal__t">{t}<small>{esc(it.get("small", ""))}</small></p><span class="mg-cal__star">{esc(it.get("star", ""))}</span></li>')


def edit_li(li, e):
    if e.get("date"):
        d = dt.date.fromisoformat(e["date"])
        li = re.sub(r"<time>.*?</time>", f"<time>{d.month:02d}.{d.day:02d}<small>{WD[d.weekday()]}</small></time>", li, count=1, flags=re.S)
    if e.get("small") is not None:
        li = re.sub(r"<small>(?!\w{3}</small>)(?:(?!<small>).)*?</small></p>", lambda m: f"<small>{esc(e['small'])}</small></p>", li, count=1, flags=re.S)
    if e.get("title"):
        li = re.sub(r'(<p class="mg-cal__t">)(.*?)(<small>)', lambda m: m.group(1) + (re.sub(r">[^<]+</a>", f">{esc(e['title'])}</a>", m.group(2)) if "<a " in m.group(2) else esc(e["title"])) + m.group(3), li, count=1, flags=re.S)
    return li


def update_upcoming(html, ops, ref):
    m = re.search(r'(<ol class="mg-cal">)(.*?)(</ol>)', html, re.S)
    if not m: raise ValueError("UPCOMING（ol.mg-cal）が見つかりません")
    items = [(li_date(x, ref), x) for x in LI.findall(m.group(2))]
    removed, added, edited = [], [], []
    keep = []
    for d, x in items:
        t = li_title(x)
        if d and d < ref: removed.append(t); continue                       # 過ぎた日
        if any(r["match"] in t for r in ops.get("remove", [])): removed.append(t); continue
        for e in ops.get("edit", []):
            if e["match"] in t: x = edit_li(x, e); edited.append(t)
        keep.append((li_date(x, ref), x))
    for it in ops.get("add", []):
        d = dt.date.fromisoformat(it["date"])
        if d < ref: continue
        if any(li_date(x, ref) == d and (it["title"] in li_title(x) or li_title(x) in it["title"]) for _, x in keep): continue  # 同じ行がある
        keep.append((d, make_li(it))); added.append(it["title"])
    keep.sort(key=lambda p: p[0] or dt.date.max)
    body = "\n    " + "\n    ".join(x for _, x in keep) + "\n  "
    return html[:m.start(2)] + body + html[m.end(2):], {"removed": removed, "added": added, "edited": edited}, keep


# ---------- ティッカー ----------
def update_ticker(html, ops, keep, ref):
    m = re.search(r'(<div class="mg-ticker__track">)(.*?)(</div>)', html, re.S)
    if not m: return html, False
    tick = {}
    for it in ops.get("add", []) + ops.get("edit", []):
        if it.get("ticker"): tick[it.get("title") or it.get("match")] = it["ticker"]
    old = re.findall(r"<span>(.*?)</span>", m.group(2), re.S)
    old = old[: len(old) // 2] if len(old) % 2 == 0 and old[: len(old) // 2] == old[len(old) // 2:] else old
    # 過ぎた日の項目（先頭が MM.DD 形式で終わるもの）を外し、足す
    live = []
    for s in old:
        mm = re.search(r"(\d{2})\.(\d{2})", s)
        d = None
        if mm:
            try: d = dt.date(ref.year, int(mm.group(1)), int(mm.group(2)))
            except ValueError: pass
            if d and d < ref - dt.timedelta(days=200): d = dt.date(ref.year + 1, d.month, d.day)
        if d and d < ref: continue
        live.append(s)
    for k, v in tick.items():
        if v not in live: live.append(v)
    def key(s):
        mm = re.search(r"(\d{2})\.(\d{2})", s)
        return (int(mm.group(1)), int(mm.group(2))) if mm else (99, 99)
    live.sort(key=lambda s: ((key(s)[0] < ref.month - 6) * 12 + key(s)[0], key(s)[1]))
    live = live[:6]
    if not live: return html, False
    spans = "".join(f"<span>{s}</span>" for s in live)
    return html[:m.start(2)] + "\n  " + spans + "\n  " + spans + "\n" + html[m.end(2):], True


# ---------- NEXT LAUNCH ----------
def update_next(html, launches, ref):
    ev = [e for e in launches if e.get("status") in ("確定", "予定", "延期") and e.get("date") and e.get("time")]
    ev.sort(key=lambda e: (e["date"], e["time"]))
    now = dt.datetime.now(JST)
    nxt = None
    for e in ev:
        hh, mm = e["time"].split(":"); t = dt.datetime.fromisoformat(f'{e["date"]}T{int(hh):02d}:{int(mm):02d}:00+09:00')
        if now < t + dt.timedelta(hours=6): nxt = (e, t); break
    def sub(cls, text, h):
        return re.sub(rf'(<p class="{cls}">).*?(</p>)', lambda m: m.group(1) + text + m.group(2), h, count=1, flags=re.S)
    if nxt:
        e, t = nxt
        html = sub("mg-next__name", esc(e["title"]), html); html = sub("mg-next__sub", esc(e.get("sub") or e.get("place", "")), html)
        html = sub("mg-next__date", f'{t.year}.{t.month:02d}.{t.day:02d} {WD[t.weekday()]} — {t.hour:02d}:{t.minute:02d} JST', html)
        html = re.sub(r'(id="mgCount" data-target=")[^"]*(")', lambda m: m.group(1) + t.isoformat() + m.group(2), html, count=1)
    return html


def update(html, launches, ops, ref=None):
    ref = ref or today()
    out = html
    scripts = [m for m in re.finditer(r"<script>.*?</script>", out, re.S) if "getElementById('mgCount')" in m.group(0)]
    if len(scripts) != 1: raise ValueError(f"カウントダウンの script が {len(scripts)} 個あります（1個のはず）")
    out = out[:scripts[0].start()] + build_countdown(launches) + out[scripts[0].end():]
    out, info, keep = update_upcoming(out, ops, ref)
    out, tk = update_ticker(out, ops, keep, ref); info["ticker"] = tk
    out = update_next(out, launches, ref)
    check(html, out)
    return out, info


def check(a, b):
    """壊していないかの検査。1つでも外れたら書かない"""
    for pat in (r'<div class="mg-home">', r'<ol class="mg-cal">', r'id="mgCount"', r'<aside class="mg-next"', r'<div class="mg-ticker__track">'):
        na, nb = len(re.findall(pat, a)), len(re.findall(pat, b))
        if nb < 1 or na != nb: raise ValueError(f"検査に失敗：{pat} の数が {na} → {nb} に変わりました")
    for tag in ("section", "div", "ol", "li", "aside", "script", "style"):
        da = len(re.findall(rf"<{tag}\b", a)) - len(re.findall(rf"</{tag}>", a)); db = len(re.findall(rf"<{tag}\b", b)) - len(re.findall(rf"</{tag}>", b))
        if da != db: raise ValueError(f"検査に失敗：<{tag}> の開きと閉じのずれが {da} → {db} に変わりました")
    if len(re.findall(r"<style", a)) != len(re.findall(r"<style", b)): raise ValueError("検査に失敗：style の数が変わりました")
    if abs(len(b) - len(a)) > 0.3 * len(a): raise ValueError("検査に失敗：変更が大きすぎます（30%超）")
    sc = [m.group(0) for m in re.finditer(r"<script>.*?</script>", b, re.S) if "getElementById('mgCount')" in m.group(0)][0]
    if "&" in sc.replace("</script>", ""): raise ValueError("検査に失敗：script に & があります（WordPress が &#038; に書き換えて壊れるため使えません）")
    if re.search(r"/\*.*?\*/|<!--", re.search(r"<script>.*?</script>", b, re.S).group(0), re.S) and False: pass


# ---------- WordPress ----------
def _auth():
    u, p = os.environ.get("MIAGETABI_WP_USER"), os.environ.get("MIAGETABI_WP_APP_PASSWORD")
    if not (u and p): raise PermissionError("MIAGETABI_WP_USER / MIAGETABI_WP_APP_PASSWORD が環境にありません")
    return "Basic " + base64.b64encode(f"{u}:{p}".encode()).decode()


def wp(method, path, body=None):
    req = urllib.request.Request(BASE + "/wp-json" + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": _auth(), "Content-Type": "application/json", "User-Agent": "miagetabi-site-update"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"WordPress が {e.code} を返しました（{path}）。WAF に止められた・権限が足りない・認証が違う、のどれかです")


def home_id():
    if os.environ.get("MIAGETABI_WP_HOME_ID"): return int(os.environ["MIAGETABI_WP_HOME_ID"])
    for pg in wp("GET", "/wp/v2/pages?per_page=100&context=edit&_fields=id,link"):
        if pg["link"].rstrip("/") == BASE: return pg["id"]
    raise RuntimeError("ホームの固定ページが見つかりません（MIAGETABI_WP_HOME_ID を設定してください）")


def _script(html):
    m = [x.group(0) for x in re.finditer(r"<script>.*?</script>", html, re.S) if "getElementById('mgCount')" in x.group(0)]
    return m[0] if len(m) == 1 else None


def public_ok(expected_html):
    """公開ページの script が、書いたものと一字一句同じか（WordPress が書き換えていないか）を確かめる"""
    req = urllib.request.Request(BASE + "/?_=" + str(int(dt.datetime.now().timestamp())), headers={"User-Agent": "Mozilla/5.0"})
    s = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    want = _script(expected_html)
    return want is not None and want in s and 'id="mgCount"' in s


def main():
    cmd = sys.argv[1]
    if cmd == "rollback":
        b = json.load(open(sys.argv[2], encoding="utf-8")); wp("POST", f"/wp/v2/pages/{b['id']}", {"content": b["raw"]}); print("戻しました"); return
    launches = json.load(open(sys.argv[2], encoding="utf-8")); ops = json.load(open(sys.argv[3], encoding="utf-8")) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else {}
    args = sys.argv[3:]
    if cmd == "plan":
        src = open(args[args.index("--html") + 1], encoding="utf-8").read() if "--html" in args else urllib.request.urlopen(urllib.request.Request(BASE + "/", headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode()
        new, info = update(src, launches, ops)
        if "--out" in args: open(args[args.index("--out") + 1], "w", encoding="utf-8").write(new)
        print(json.dumps(info, ensure_ascii=False, indent=1))
        print("".join(list(difflib.unified_diff(src.splitlines(True), new.splitlines(True), "いま", "新しい", n=0))[:120]))
        return
    if cmd == "apply":
        pid = home_id(); page = wp("GET", f"/wp/v2/pages/{pid}?context=edit&_fields=id,content")
        raw = page["content"]["raw"]; new, info = update(raw, launches, ops)
        if new == raw: print("変更なし"); return
        json.dump({"id": pid, "raw": raw, "at": dt.datetime.now(JST).isoformat()}, open("home-backup.json", "w", encoding="utf-8"), ensure_ascii=False)
        wp("POST", f"/wp/v2/pages/{pid}", {"content": new})
        if not public_ok(new):  # 公開ページで、script が残っているか確かめる（権限で <script> が削られる場合がある）
            wp("POST", f"/wp/v2/pages/{pid}", {"content": raw}); raise RuntimeError("保存後の確認に失敗したので、元に戻しました（公開ページの <script> が、書いたものと違います。削られた・書き換えられた可能性）")
        print(json.dumps({"ok": True, "pageId": pid, **info}, ensure_ascii=False))
        return
    raise SystemExit(__doc__)


if __name__ == "__main__":
    try: main()
    except (PermissionError, RuntimeError, ValueError) as e: print("NG:", e); sys.exit(2)
