# トップページのカウントダウン（自動切り替え）

`NEXT LAUNCH` のカウントダウンを、**打ち上げが終わったら自動で次へ**切り替える。

## 入れ替え（運営者が1回）
1. WordPress のトップページの編集画面で、いまのカウントダウンの `<script> … </script>`（`id="mgCount"` を使っているもの）を、`countdown-script.html` の中身に丸ごと入れ替える。表の `<aside class="mg-next">` の HTML はそのまま使える（クラス名で書き換える）。
2. 以後は、見た人の時計で自動で切り替わる。

## 動き
- 日付の決まった打ち上げのうち、予定時刻から**6時間たっていない**いちばん早いものを出す。時刻を過ぎたら 00:00 のまま「結果・延期は公式で確認を」と出し、6時間後に次へ。
- 日付の決まったものが無ければ、「日程の発表待ち」と近そうな打ち上げの名前・時期を出す。
- 延期・日付の確定があったら、一覧を作り直して入れ替える（`ops/site-rules.md` の 12）。

## 作り直し
`python3 home_countdown.py launches.json > countdown-script.html`（`launches.json` の形は `home_countdown.py` の先頭）。いまの一覧は `launches.json`。
