# ミアゲタビ 編集エージェントの共通手順（依頼の受け方・データの置き場所）

ミアゲタビ（https://miagetabi.space/ 、宇宙を見に行くガイド）の管理アプリ（アーティファクト https://claude.ai/artifact/CFkmjQnXk8beWmPEPwscjP ）から、記事の作成と査読を依頼されたときの共通の決まり。作成エージェントも査読エージェントも、最初にこれを読む。

- **リポジトリは使わない**（clone しない）。資料はアーティファクトと一緒に公開してあるので、Artifact ツールの `read` に `url`（上のアーティファクト）と `paths` を渡して読む。
  - `ops/agent-jobs.md` … この手順書
  - `ops/article-manual.md` … 記事作成エージェントの手順書
  - `ops/review-manual.md` … 査読エージェントの手順書（査読の基準）
  - `ops/sky.py` … 天体の計算（方角・高さ・月の出入り・曜日・世界時の変換）
  - `ops/md2blocks.py` … Markdown を WordPress のブロックに変換する
  - 読んだファイルは保存先が表示される。`.py` はその保存先のまま `python3` で実行する（中身を書き写さない）。`sky.py` を使う前に `pip install ephem==4.2` を実行する。
- db（アプリの共有データ）の読み書きは **ArtifactData** ツール。既存のドキュメントを書き換えるときは、読んだ `version` を `if_version` に渡す。合わないと言われたら読み直して 1 回だけやり直す。
- 時刻（`startedAt`・`finishedAt`・`updatedAt`・`createdAt`・`at`）は、**必ずその場で `date -u +%Y-%m-%dT%H:%M:%SZ` を実行して得た値**を書く（推測しない）。日本時間が要るときは `TZ=Asia/Tokyo date`。
- **WordPress に書き込まない。** サーバーは海外からの REST API を止めている。公開ページを GET で読むのはよい。
- 認証情報をどこにも書かない・表示しない。
- 運営者（この db の持ち主）への報告・質問は、すべて日本語。

## 0. 停止の確認（最初に必ず）
ジョブに触る前に `settings/agentPause` を `get` し、`roles.<自分の役割>.paused` が `true` なら、ジョブを `queued` のまま何も変えず、「停止中のため何もしません」とだけ報告して終わる。役割は作成が `writer`、査読が `reviewer`。ドキュメントが無ければ停止していない。

## 1. 依頼を受け取る
1. 追加テキストに `job:<ID>` があれば、その `jobs/<ID>` を `get` する。無ければ（定期の見回り）、`jobs` を `list` して、自分の `kind`（作成は `"article"`、査読は `"review"`）で `status` が `"queued"` のものを、`createdAt` の古い順に 1 件選ぶ。1 件も無ければ、ほかは何も読まずに「仕事なし」とだけ書いて終わる。
2. `status` が `"queued"` でなければ何もしないで終わる（二重起動の防止）。
3. `update` で `status: "running"`・`startedAt`・`updatedAt`・`message: "取りかかりました"`・`agent`（`"writer"` か `"reviewer"`）・`session`（環境変数 `CLAUDE_CODE_REMOTE_SESSION_ID` の値。無ければ省く）にする。
4. 作業の節目ごとに `message`（日本語で短く）・`step`（`"research"`・`"write"`・`"check"`・`"save"` など）・`updatedAt` を更新する。10 分に 1 回以上。アプリはこれを「いま動いているエージェント」として表示する。
5. 終わったら `status: "done"`・`finishedAt`・`message`（結果を 1 行）。失敗したら `status: "error"`・`message` に原因を日本語で書いて終わる（どこまで進んだかがわかるように）。

## 2. db の形

### `jobs/<ID>`（依頼）
```json
{"kind": "article" | "review", "articleId": "a01", "round": 1, "title": "記事のタイトル案",
 "withExperience": false, "note": "運営者からの指示（無いこともある）", "rewrite": false,
 "status": "queued" | "running" | "done" | "error", "message": "", "step": "", "agent": "", "session": "",
 "createdAt": "", "startedAt": "", "finishedAt": "", "updatedAt": "", "by": "app" | "loop"}
```

### `articles/<articleId>`（記事のカード。アプリの記事ボード）
運営者が入れた項目（読むだけ。書き換えない）:
`title`（タイトル案）・`pillar`（`launch` 打ち上げ／`sky` 天体／`spot` 宇宙スポット／`gear` 機材）・`keyword`（検索キーワード）・`intent`（検索意図）・`eventDate`・`publishBy`・`monetize`（収益化の導線）・`template`・`path`（URL）・`priority`・`note`・`url`（公開URL）

エージェントが書く項目:
- `status`: 作成エージェントが最初の稿を書いたら `"下書き"`（`"公開済み"` のカードは変えない）。査読で合格したら査読エージェントが `"確認待ち"`。
- `draft`: 作成エージェントの稿（形は `ops/article-manual.md` の 6 章）
- `draftPrev`: 書き直す前の稿（作成エージェントが書き直しの前に移す。1 つ前だけ残す）
- `review`: 最新の査読（形は `ops/review-manual.md` の 6 章）
- `reviewHistory`: これまでの査読の要約の配列 `[{"round", "grade", "p0", "p1", "p2", "at"}]`
- `loop`: `{"state": "writing" | "reviewing" | "passed" | "failed", "round": 1, "max": 3, "updatedAt": ""}`

### `events/<ID>`（イベント。打ち上げ・天体・展示の日付）
`title`・`pillar`・`date`（YYYY-MM-DD、未定なら空）・`time`・`dateText`・`place`・`status`（確定／予定／推測／延期／終了）・`source`・`note`。記事の題材のイベントを探すのに読む。**書き換えない**（延期などに気づいたら `report` に書く）。

### `settings/…`
- `settings/background`: `{"writerTriggerId", "reviewerTriggerId", "server": "Claude Code Remote"}`（Routine の ID）
- `settings/agentPause`: `{"roles": {"writer": {"paused": false}, "reviewer": {"paused": false}}}`
- `settings/writerLessons`: `{"items": [{"text": "教訓（1 文）", "from": "a01 の 1 回目の査読", "at": ""}]}`（査読エージェントが足す。最大 30 件）
- `settings/reviewLoop`: `{"enabled": true, "maxRounds": 3, "pass": "A"}`（無ければこの値とみなす）

## 3. 次のエージェントへの受け渡し
- 受け渡しは `jobs` に `status: "queued"` の依頼を `set` で書く（doc_id は下の決まり）。
  - 作成 → 査読: `review-<articleId>-<round>`
  - 査読 → 作成（書き直し）: `article-<articleId>-<round+1>`
- 書いたら起動する: ToolSearch で `select:mcp__claude-code-remote__fire_trigger` を読み込み、`settings/background` の該当する ID（査読なら `reviewerTriggerId`、作成なら `writerTriggerId`）を `text: "job:<doc_id>"` で `fire_trigger` する。読み込めない・失敗したときは、依頼を `queued` のまま残してよい（定期の見回りか、アプリを開いたときに起動される）。そのことを報告に 1 行書く。

## 4. 最後の報告（スマホに通知される）
日本語で 3 行以内。例:
- 「a01『H3ロケット10号機を見る方法』を書きました（1回目）。査読に回しました。」
- 「a01 の査読：B（P1 が 3 件）。書き直しを依頼しました（2回目）。」
- 「a01 の査読：A。記事ボードで『確認待ち』になりました。」
