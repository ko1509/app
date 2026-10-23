#!/usr/bin/env python3
"""査読に通った記事の稿を、アイキャッチごと WordPress に入稿する。入稿エージェント用。

使い方（認証情報は環境変数。値は表示・保存しない）:
  python3 publish_wp.py plan  article.json image.json            # 何をするか（新規／差し替え、カテゴリ、タグ、画像）を出すだけ。書かない
  python3 publish_wp.py apply article.json image.json            # 取得 → 検査 → 画像を上げる → 記事を保存（POST）→ 公開ページで確認（失敗なら元に戻す）
  python3 publish_wp.py rollback backup.json                     # 差し替え前に戻す
  python3 publish_wp.py snsmedia image.json post-ID alt文           # SNS 用の図解画像（images/sns-…）をメディアに上げ、公開 URL を出す（画像担当が使う。記事は書かない）
article.json … アプリの db の articles/<ID>（draft・review・wp・seo・status を持つもの）。image.json … images/<ID>-eyecatch（dataUrl を持つもの）。
環境変数: MIAGETABI_WP_USER / MIAGETABI_WP_APP_PASSWORD
結果は最後の行に JSON（ok・postId・link・mediaId・mode・backup のファイル名）。バックアップは backup-<記事ID>.json に書く。
"""
import base64, json, os, re, sys, time, urllib.error, urllib.request

BASE = "https://miagetabi.space"


def _auth():
    u, p = os.environ.get("MIAGETABI_WP_USER"), os.environ.get("MIAGETABI_WP_APP_PASSWORD")
    if not (u and p): raise PermissionError("MIAGETABI_WP_USER / MIAGETABI_WP_APP_PASSWORD が環境にありません")
    return "Basic " + base64.b64encode(f"{u}:{p}".encode()).decode()


def wp(method, path, body=None, raw=None, headers=None):
    h = {"Authorization": _auth(), "User-Agent": "miagetabi-publisher"}
    data = None
    if raw is not None: data = raw
    elif body is not None: data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    h.update(headers or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + "/wp-json" + path, method=method, data=data, headers=h), timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"WordPress が {e.code} を返しました（{method} {path}）" + ("。サーバーの WAF に止められた可能性" if b"<html" in e.read(200).lower() else ""))


def load(path):
    d = json.load(open(path, encoding="utf-8"))
    return d.get("data", d)


def check(card, img):
    """入稿してよいかの検査。1つでも外れたら書かない"""
    dr = card.get("draft") or {}; rv = card.get("review") or {}
    if not rv.get("pass") or rv.get("grade") != "A": raise ValueError("査読が A ではありません")
    if rv.get("round") != dr.get("round"): raise ValueError(f"査読（{rv.get('round')}回目）が稿（{dr.get('round')}回目）のものではありません")
    for k in ("blocks", "seo", "wp"):
        if not dr.get(k): raise ValueError(f"稿に {k} がありません")
    seo, w, blocks = dr["seo"], dr["wp"], dr["blocks"]
    if not (seo.get("title") and seo.get("description")): raise ValueError("seo の title / description がありません")
    if not (w.get("slug") and w.get("category")): raise ValueError("wp の slug / category がありません")
    if len(blocks) < 3000: raise ValueError("本文（blocks）が短すぎます")
    if re.search(r"<script|javascript:|onerror\s*=", blocks, re.I): raise ValueError("本文に <script> などがあります")
    if "mg-info" not in blocks: raise ValueError("要点ボックス（mg-info）がありません")
    if not img or not img.get("dataUrl", "").startswith("data:image/jpeg;base64,"): raise ValueError("アイキャッチ画像がありません")
    if card.get("status") in ("企画中", "保留", "見送り"): raise ValueError(f"状態が「{card.get('status')}」です")


def ids(kind, slugs):
    items = wp("GET", f"/wp/v2/{kind}?per_page=100&_fields=id,slug")
    m = {x["slug"]: x["id"] for x in items}
    miss = [s for s in slugs if s not in m]
    if miss: raise ValueError(f"WordPress に {kind} がありません: {miss}")
    return [m[s] for s in slugs]


def find_post(card):
    w = (card.get("draft") or {}).get("wp") or {}
    pid = card.get("wpPostId")
    if pid:
        return wp("GET", f"/wp/v2/posts/{pid}?context=edit&_fields=id,slug,status,link,title,content,excerpt,featured_media,categories,tags,date")
    r = wp("GET", f"/wp/v2/posts?slug={w['slug']}&status=any&context=edit&_fields=id,slug,status,link,title,content,excerpt,featured_media,categories,tags,date")
    return r[0] if r else None


def plan(card, img):
    check(card, img)
    dr = card["draft"]; w = dr["wp"]; post = find_post(card)
    return {"mode": "差し替え" if post else "新規", "postId": post["id"] if post else None, "title": dr["seo"]["title"], "slug": w["slug"], "category": w["category"], "tags": w.get("tags", []),
            "本文の文字数": len(dr["blocks"]), "WP の今の本文": len(post["content"]["raw"]) if post else 0, "画像": f'{len(img["dataUrl"]) * 3 // 4 // 1024} KB'}


def upload(img, slug, alt):
    b = base64.b64decode(img["dataUrl"].split(",", 1)[1])
    stamp = time.strftime("%Y%m%d%H%M")
    m = wp("POST", "/wp/v2/media", raw=b, headers={"Content-Type": "image/jpeg", "Content-Disposition": f'attachment; filename="{slug}-eyecatch-{stamp}.jpg"'})
    wp("POST", f"/wp/v2/media/{m['id']}", body={"alt_text": alt, "title": alt})
    return m["id"], m["source_url"]


def apply(card, img, aid):
    check(card, img)
    dr = card["draft"]; w = dr["wp"]; seo = dr["seo"]; blocks = dr["blocks"].replace("\r\n", "\n")
    cat = ids("categories", [w["category"]]); tags = ids("tags", w.get("tags", [])) if w.get("tags") else []
    post = find_post(card); backup = None
    if post:
        backup = {"id": post["id"], "title": post["title"]["raw"], "content": post["content"]["raw"], "excerpt": post["excerpt"]["raw"], "featured_media": post["featured_media"],
                  "categories": post["categories"], "tags": post["tags"], "status": post["status"], "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        json.dump(backup, open(f"backup-{aid}.json", "w", encoding="utf-8"), ensure_ascii=False)
    mid, murl = upload(img, w["slug"], seo["title"][:60])
    body = {"title": seo["title"], "content": blocks, "excerpt": seo["description"], "slug": w["slug"], "status": "publish", "categories": cat, "tags": tags, "featured_media": mid}
    try:
        saved = wp("POST", f"/wp/v2/posts/{post['id']}", body=body) if post else wp("POST", "/wp/v2/posts", body=body)
        got = wp("GET", f"/wp/v2/posts/{saved['id']}?context=edit&_fields=id,content,featured_media,link,status,title,excerpt")
        if got["content"]["raw"].replace("\r\n", "\n").strip() != blocks.strip(): raise RuntimeError("保存した本文が、書いたものと違います（WordPress が書き換えた可能性）")
        if got["featured_media"] != mid: raise RuntimeError("アイキャッチが設定されていません")
        req = urllib.request.Request(got["link"] + ("&" if "?" in got["link"] else "?") + "_=" + str(int(time.time())), headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        if seo["title"].split("｜")[0][:12] not in html.replace("&#8211;", "–"): raise RuntimeError("公開ページに題名が見つかりません")
        if str(mid) not in html and murl.split("/uploads/")[1].split(".")[0][:30] not in html: raise RuntimeError("公開ページにアイキャッチが見つかりません")
    except Exception:
        if post and backup:
            wp("POST", f"/wp/v2/posts/{post['id']}", body={k: backup[k] for k in ("title", "content", "excerpt", "featured_media", "categories", "tags", "status")})
        elif not post and "saved" in dir():
            wp("POST", f"/wp/v2/posts/{saved['id']}", body={"status": "draft"})
        raise
    return {"ok": True, "mode": "差し替え" if post else "新規", "postId": saved["id"], "link": got["link"], "mediaId": mid, "mediaUrl": murl, "backup": f"backup-{aid}.json" if backup else None}


def main():
    cmd = sys.argv[1]
    if cmd == "rollback":
        b = json.load(open(sys.argv[2], encoding="utf-8")); wp("POST", f"/wp/v2/posts/{b['id']}", body={k: b[k] for k in ("title", "content", "excerpt", "featured_media", "categories", "tags", "status")}); print("戻しました"); return
    if cmd == "snsmedia":  # SNS 用の画像を公開 URL にする（Metricool は公開 URL しか受け取れない）
        img = load(sys.argv[2]); pid = re.sub(r"[^A-Za-z0-9-]", "", sys.argv[3]); alt = sys.argv[4] if len(sys.argv) > 4 else "ミアゲタビの図"
        if not img.get("dataUrl", "").startswith("data:image/jpeg;base64,"): raise ValueError("画像がありません")
        b = base64.b64decode(img["dataUrl"].split(",", 1)[1])
        m = wp("POST", "/wp/v2/media", raw=b, headers={"Content-Type": "image/jpeg", "Content-Disposition": f'attachment; filename="sns-{pid}-{time.strftime("%Y%m%d%H%M")}.jpg"'})
        wp("POST", f"/wp/v2/media/{m['id']}", body={"alt_text": alt, "title": alt})
        print(json.dumps({"ok": True, "mediaId": m["id"], "url": m["source_url"]}, ensure_ascii=False)); return
    card = load(sys.argv[2]); img = load(sys.argv[3]); aid = os.path.basename(sys.argv[2]).split(".")[0].split("-")[0]
    if cmd == "plan": print(json.dumps(plan(card, img), ensure_ascii=False, indent=1))
    elif cmd == "apply": print(json.dumps(apply(card, img, aid), ensure_ascii=False))
    else: raise SystemExit(__doc__)


if __name__ == "__main__":
    try: main()
    except (PermissionError, RuntimeError, ValueError) as e: print("NG:", e); sys.exit(2)
