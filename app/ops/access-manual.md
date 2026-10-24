# 計測エージェント（access）の手順書

サイトのアクセス記録（GA4）を取り出して、アプリの「アクセス」タブ用に `analytics/summary` に書く。**読むだけ**。サイトも記事も触らない。

**書き換えてよいもの**：`analytics/summary`、`analytics/day-<YYYYMMDD>`（その日の控え）、自分の `jobs/<ID>`
**書き換えないもの**：それ以外すべて

## 0. 共通
`ops/agent-jobs.md`（共通の約束。停止の確認を含む）を読んでから進める。

## 1. いつ動くか
毎朝（6時台）と、依頼 `kind: "access"`（アプリの「いま更新」）。

## 2. 手順
1. 環境変数 `GA4_PROPERTY_ID`・`GA4_SERVICE_ACCOUNT_JSON` があるか**有無だけ**確かめる（値は表示しない）。無ければ受信箱に `kind: "question"` で「計測の設定が未完です（アプリの「アクセス」タブの手順）」と出して終わる。
2. `python3 ops/ga4_report.py 28 > /tmp/access.json`（`ops/` のスクリプト。失敗したら終わりの 4 章へ）。
3. `analytics/summary` に `set`（`geo`＝国別（ISO コード）・`jpRegions`＝日本の都道府県別・`pageTitles` も含む。アプリが世界地図・日本地図・人気ページのカードにする）（ファイルの中身そのまま。`status: "ok"`、`updatedAt`）。あわせて `analytics/day-<今日>` に `totals` を書く（推移の控え）。
4. 失敗したとき：`analytics/summary` は消さず `update` で `status: "error"`・`error`（1行。鍵やIDを含めない）・`updatedAt` だけ書く。
5. 依頼を `done` にし、1行で報告する（利用者数・閲覧数）。

## 3. 見方の決まり
- 「0」と「まだ計測前」を区別する。サイトにタグを入れた日より前の数字は無い。
- 個人を特定できる情報（IPアドレス等）は扱わない。GA4 の集計値だけ。

## 4. してはいけないこと
- 鍵・プロパティIDを表示・保存・コミットすること。GA4 の設定を変えること。
