#!/usr/bin/env python3
"""スマホの揺れ対策（既定：mg-progress-calm.js と .css。他にオプションの部品あり）を、WordPress のウィジェットエリア「フッター直前」（before_footer）に
カスタム HTML ウィジェットとして入れる（全ページ共通で、フッターの直前に出力される）。管理画面のカスタマイザーに入れない場合の、REST での反映方法。

  python3 deploy_widget.py plan      # 何をするかだけ出す（書かない）
  python3 deploy_widget.py apply     # 作る（同じ印のウィジェットがあれば内容を更新）
  python3 deploy_widget.py remove    # 外す（「使用停止中のウィジェット」へ移す）

環境変数 MIAGETABI_WP_USER / MIAGETABI_WP_APP_PASSWORD（値は表示しない）。印：<!-- mg-calm -->。更新は POST（PUT は止められる）。
"""
import base64, json, os, sys, urllib.error, urllib.request

BASE = "https://miagetabi.space/wp-json"
HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "<!-- mg-calm -->"
SIDEBAR = "before_footer"


def auth():
    u, p = os.environ.get("MIAGETABI_WP_USER"), os.environ.get("MIAGETABI_WP_APP_PASSWORD")
    if not (u and p): raise SystemExit("MIAGETABI_WP_USER / MIAGETABI_WP_APP_PASSWORD が環境にありません")
    return "Basic " + base64.b64encode(f"{u}:{p}".encode()).decode()


def wp(method, path, body=None):
    h = {"Authorization": auth(), "User-Agent": "miagetabi-calm", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + path, method=method, data=data, headers=h), timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"WordPress が {e.code} を返しました（{method} {path}）" + ("。WAF に止められた可能性（回避しない。止めて運営者に知らせる）" if b"<html" in e.read(300).lower() else ""))


def html():
    """ウィジェットに入れるもの。既定は「進捗バーをヘッダーの外へ」（mg-progress-calm）だけ。--progress-off：進捗バーを廃止（mg-progress-off）。
    --calm：スクロール中の描画停止（mg-scroll-calm.js）も入れる。--no-stars：スマホで星を出さない（どちらも、試したが揺れは直らなかったので、既定では入れない）"""
    rd = lambda n: open(os.path.join(HERE, n), encoding="utf-8").read()
    if "--progress-off" in sys.argv:  # 進捗バーの廃止（実験）
        css, js = rd("mg-progress-off.css"), rd("mg-progress-off.js")
    elif "--fixes" in sys.argv:  # 進捗バーは元のまま（何も足さない）
        css, js = "", ""
    else:
        css, js = rd("mg-progress-calm.css"), rd("mg-progress-calm.js")
    if "--fixes" in sys.argv: js += "\n" + rd("mg-launch-nosmoke.js"); css += rd("mg-history-bar.css")  # 打ち上げ演出の煙を描かない／年表の下の進み具合バーのズレ直し
    if "--header-fixed" in sys.argv: css += rd("mg-header-fixed.css")  # スマホのヘッダーを sticky から fixed へ
    if "--no-stars" in sys.argv: css += rd("mg-no-stars-mobile.css")
    if "--calm" in sys.argv: js += "\n" + rd("mg-scroll-calm.js")
    out = f'{MARK}<style id="mg-calm-css">{css}</style><script id="mg-calm-js">{js}</script>'
    assert "&" not in out, "「&」が含まれています（WordPress が書き換えるため入れない）"
    return out


def find():
    for w in wp("GET", "/wp/v2/widgets?per_page=100&context=edit"):
        raw = ((w.get("instance") or {}).get("raw") or {})
        if w.get("id_base") == "custom_html" and MARK in (raw.get("content") or ""): return w
    return None


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    cur = find()
    if cmd == "plan":
        print(json.dumps({"置き場所": SIDEBAR, "いまの状態": ("あり（" + cur["id"] + "）" if cur else "なし"), "文字数": len(html())}, ensure_ascii=False)); return
    if cmd == "apply":
        body = {"id_base": "custom_html", "sidebar": SIDEBAR, "instance": {"raw": {"title": "", "content": html()}}}
        w = wp("POST", f"/wp/v2/widgets/{cur['id']}", body) if cur else wp("POST", "/wp/v2/widgets", body)
        print(json.dumps({"ok": True, "id": w["id"], "sidebar": w["sidebar"]}, ensure_ascii=False)); return
    if cmd == "remove":
        if not cur: print("ありません"); return
        wp("POST", f"/wp/v2/widgets/{cur['id']}", {"sidebar": "wp_inactive_widgets"}); print("使用停止中へ移しました"); return
    raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
