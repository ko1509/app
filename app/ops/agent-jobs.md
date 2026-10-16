# ミアゲタビ AI編集部 共通の約束（全エージェントが最初に読む）

ミアゲタビ（https://miagetabi.space/ 、宇宙を見に行くガイド）の管理アプリ（アーティファクト https://claude.ai/artifact/CFkmjQnXk8beWmPEPwscjP ）で動く AI 編集部の決まり。どのエージェントも、起動したら最初にこれを読み、次に自分の手順書を読む。

## 編集部の顔ぶれ

| 役割（role） | 名前 | 起動 | 手順書 | 受け持つ依頼（job の kind） |
|---|---|---|---|---|
| `planner` | 企画 | 月・木の朝＋依頼 | `ops/planner-manual.md` | `plan` |
| `writer` | 記事作成 | 6〜23時の毎時＋依頼 | `ops/article-manual.md` | `article`（新しい稿）・`update`（公開済み記事の直し） |
| `reviewer` | 査読 | 6〜23時の毎時＋依頼 | `ops/review-manual.md` | `review`（`mode`: `draft` 稿／`update` 直し／`recheck` 公開済みの点検） |
| `designer` | 画像 | 依頼（査読 A・SNS 審査 OK のとき）＋6〜23時の毎時 | `ops/eyecatch-manual.md` | `eyecatch`（**査読で A になった稿だけ**にアイキャッチ）・`snsimage`（**SNS 審査を通った投稿**の画像） |
| `eventfetch` | イベント取得 | 月・木の朝＋依頼 | `ops/event-fetch-manual.md` | `eventfetch` |
| `watch` | 公式ウォッチ | 1日4回＋依頼 | `ops/watch-manual.md` | `watch` |
| `sns` | SNS | 依頼だけ（SNS アカウントができるまで停止） | `ops/sns-manual.md` | `sns` |
| `snsreview` | SNS 審査 | 依頼だけ（同上） | `ops/sns-review-manual.md` | `snsreview` |
| `audit` | 点検 | 毎朝＋依頼 | `ops/audit-manual.md` | `audit` |

運営者（この db の持ち主）が最終判断をする。判断が要るものは、すべて**受信箱（`inbox`）**に出す。エージェントは判断を推測で埋めない。

## 道具と資料

- **リポジトリは使わない**（clone しない）。資料はアーティファクトと一緒に公開してあるので、Artifact ツールの `read` に `url`（上のアーティファクト）と `paths` を渡して読む。
  - `ops/agent-jobs.md` … この約束
  - `ops/site-rules.md` … サイトの決まり（運営マニュアルの抜き書き。カテゴリ・タグ・表記・記事の型・更新のタイミング）
  - 各役割の手順書（上の表）
  - `ops/sky.py` … 天体の計算（方角・高さ・月の出入り・曜日・世界時の変換）。使う前に `pip install ephem==4.2`
  - `ops/md2blocks.py` … Markdown を WordPress のブロックに変換する
  - `ops/figures.py` … 記事の図（タイムライン・方角と高さ・距離）を SVG で作る
  - `ops/eyecatch.py` … アイキャッチ（写真風の CG＋記事のタイトル）を作る
  - 読んだファイルは保存先が表示される。`.py` はその保存先のまま `python3` で実行する（中身を書き写さない）。
- db（アプリの共有データ）の読み書きは **ArtifactData** ツール。
- 公開ページは GET で読んでよい（`curl -sL https://miagetabi.space/…`）。**WordPress に書き込まない**（サーバーは海外からの REST API を止めている）。

## 0. 停止の確認（最初に必ず）

`settings/agentPause` を `get` し、`roles.<自分の役割>.paused` が `true` なら、ジョブを何も変えず「停止中のため何もしません」とだけ報告して終わる。ドキュメントが無ければ停止していない。

## 1. ジョブ

1. 追加テキストに `job:<ID>` があれば、その `jobs/<ID>` だけを処理する。無ければ（定時の見回り）、`jobs` を `query`（`where: [["status","==","queued"]]`）して、自分の受け持つ `kind` のものを `createdAt` の古い順に **1 件だけ**選ぶ。
   - 1 件も無いとき：定時の仕事がある役割（企画・公式ウォッチ・SNS・点検）は手順書の「定時の仕事」をする。作成・査読・アイキャッチは、ほかは何も読まずに「仕事なし」とだけ書いて**すぐ終わる**（費用を使わない）。
2. `status` が `"queued"` でなければ何もしないで終わる（二重起動の防止）。
3. 始めたら `update` で `status: "running"`・`agent`（自分の役割）・`session`（環境変数 `CLAUDE_CODE_REMOTE_SESSION_ID`。無ければ省く）・`startedAt`・`updatedAt`・`message: "取りかかりました"`。
4. 進んだら `message`（日本語で短く。アプリにそのまま出る）・`step`・`updatedAt` を更新する。10 分に 1 回以上。
5. 終わったら `status` を次のどれかにし、`finishedAt` と結果の要約を `message` に書く。**失敗を成功と書かない。**
   - `done`：やり終えた
   - `waiting`：運営者の判断待ちで止めた（受信箱に出したとき。`inboxId` を書く）
   - `error`：失敗した（どこまで進んだか、原因を日本語で）

定時の見回りで依頼の無い仕事をしたときも、最後に `jobs/<role>-<YYYYMMDDHHMM>` を `done` で 1 件書く（アプリの履歴に出すため。`by: "schedule"`）。

## 2. 時刻と書き込み

- 時刻（`startedAt`・`finishedAt`・`updatedAt`・`createdAt`・`at`）は、**必ずその場で `date -u +%Y-%m-%dT%H:%M:%SZ` を実行して得た値**を書く（推測しない）。「今日」は日本時間で数える（`TZ=Asia/Tokyo date +%F`）。
- 既存のドキュメントを書き換えるときは、読んだ `version` を `if_version` に渡す。合わないと言われたら読み直して 1 回だけやり直す。
- 入れ子の値は、ドット区切りのパスで書かない。親のオブジェクトを丸ごと `update` する（例：`loop` を書くなら `loop` 全体）。
- **書いてよいのは、自分の手順書の「書き換えてよいもの」だけ。** ほかのエージェントの持ち物（ほかのカードの中身、査読結果、運営者の入力）を書き換えない。

## 3. 内容の約束

- 体験を作らない。運営者が書いたメモ・答えに無い体験は書かない。
- 確かめられない数字・料金・時間・固有名詞は書かない。どうしても要る見込みは「推測」と書き、理由を添える（`ops/site-rules.md` の 3）。「要確認」と書いて残すのは不可。
- 「昨日」「先週」「今週末」「来月」など相対的な日付を書かない（db にも記事にも）。
- 固有名詞（機体名・号機・施設名・地名）の表記は `ops/site-rules.md` の表記ルールとタグの表に従う。無いものは推測せず、受信箱で聞く。
- エネルギー・原子力の話題は扱わない。

## 4. 安全

- 認証情報を読み上げない・表示しない・ファイルや db に書かない。有無を確かめるなら `test -n "$X"` だけ。
- 権限の確認で拒否されたら、コマンドの形を変えて通そうとしない。失敗として報告する。
- 公開中の記事・ホーム・図鑑は、運営者が直す。エージェントは直し方の案を出すだけ。

## 5. db の形

### `jobs/<ID>`（依頼）
```json
{"kind": "article|update|eyecatch|snsimage|review|plan|watch|sns|snsreview|audit", "mode": "draft|update|recheck（review のとき）",
 "articleId": "a01", "eventId": "", "postIds": ["（snsimage のとき）"], "round": 1, "title": "対象の名前",
 "withExperience": false, "note": "運営者や前のエージェントからの指示", "rewrite": false,
 "status": "queued|running|done|waiting|error", "message": "", "step": "", "agent": "", "session": "",
 "inboxId": "", "createdAt": "", "startedAt": "", "finishedAt": "", "updatedAt": "", "kickedAt": "",
 "by": "app|loop|schedule|<役割>"}
```

### `articles/<articleId>`（記事のカード）
- 運営者が入れる項目（読むだけ）：`title`・`pillar`（`launch|sky|spot|gear|news`）・`tags`・`keyword`・`intent`・`eventDate`・`publishBy`・`monetize`・`template`・`path`・`priority`・`note`・`url`（公開URL）・`lastVerified`
- `status`：`企画中` → `下書き` → `査読中` → `公開待ち` → `公開済み` → `要更新`（`ops/site-rules.md` の 10）
- 作成が書く：`draft`（稿）・`draftPrev`（1つ前の稿）・`updateDraft`（公開済み記事の直し）
- 査読が書く：`review`・`reviewHistory`・`recheck`（公開済みの点検結果）
- 作成と査読が書く：`loop`：`{"state": "writing|reviewing|passed|failed", "round": 1, "max": 5, "updatedAt": ""}`

### `events/<ID>`（打ち上げ・天体・展示の日付）
`title`・`pillar`・`date`（YYYY-MM-DD、未定なら空）・`time`・`dateText`・`place`・`status`（`確定|予定|推測|延期|中止|終了`）・`source`・`note`・`history`（変更の記録の配列）・`by`・`addedAt`。**新しく足してよいのはイベント取得だけ**（`ops/event-fetch-manual.md`）、**既にあるものを書き換えてよいのは公式ウォッチだけ**（`ops/watch-manual.md`）。

### `inbox/<ID>`（受信箱。運営者の判断が要るもの）
```json
{"kind": "idea|change|loopFailed|question|audit|recheck|other",
 "title": "一言で（40字まで）", "body": "Markdown。判断に要ることを全部。根拠のURLつき",
 "reason": "なぜ運営者の判断が要るか（1文）",
 "articleId": "", "eventId": "", "jobId": "",
 "proposal": {"…kind ごとの中身（各手順書）": ""},
 "status": "open", "by": "<役割>", "createdAt": "<今>"}
```
運営者がアプリで答えると `status` が `done`（対応した）か `dismissed`（見送り）になり、`answer`・`answeredAt` が入る。エージェントは `open` のものを書き換えない（自分が出したものの追記だけ、`body` の末尾に足すのは可）。同じ対象・同じ趣旨の `open` があれば新しく作らない。

### `images/<ID>`（画像。大きいので記事カードとは別に置く）
`kind`（`eyecatch`・`sns`）・`articleId`・`postId`・`format`（`eyecatch`・`x`・`ig`）・`dataUrl`（`data:image/jpeg;base64,…`）・`spec`・`createdAt`。画像担当が書き、アプリが表示・ダウンロードする。ID はアイキャッチが `<articleId>-eyecatch`、SNS が `sns-<投稿ID>`。

### `posts/<ID>`（SNS の投稿案）
`date`・`time`・`channel`（`X|Instagram`）・`status`（`下書き|差し戻し|審査済み|予約済み|投稿済み`）・`topic`（`記事|イベント|今夜の空|コラム`）・`text`・`articleId`・`eventId`・`kind`・`imageBrief`（SNS が書く画像の指示）・`imageId`（画像担当が書く）・`imageUrl`（運営者が入れる公開 URL）・`imageNote`・`sources`・`review`（`{"grade": "OK|NG", "notes": ["…"], "round", "at"}`。SNS 審査が書く）・`by`・`createdAt`

### `settings/…`
- `settings/background`：`{"server": "Claude Code Remote", "writerTriggerId", "reviewerTriggerId", "designerTriggerId", "plannerTriggerId", "eventFetchTriggerId", "watchTriggerId", "snsTriggerId", "snsReviewTriggerId", "auditTriggerId"}`
- `settings/agentPause`：`{"roles": {"<役割>": {"paused": false, "at": "", "by": "owner|auto"}}, "auto": true}`（`by: "auto"` はアプリの「自動運用」のオフで止まったもの）
- `settings/reviewLoop`：`{"enabled": true, "maxRounds": 5, "pass": "A"}`（無ければこの値。A になるまで最大5回書き直し、超えたら受信箱へ）
- `settings/writerLessons`：`{"items": [{"text", "from", "at"}]}`（査読が足す。30 件まで）
- `settings/plannerLog`：`{"items": [{"title", "decision": "採用|見送り", "reason", "at"}]}`（アプリが書く。企画が読む）

## 6. 次のエージェントへの受け渡し

- 受け渡しは `jobs/<新しいID>` を `status: "queued"` で `set` する。**同じ対象（`articleId` や `eventId`）・同じ `kind` の依頼が `queued` か `running` なら作らない。**
- ID の決まり：
  - 作成 → 査読：`review-<articleId>-<round>`（`mode: "draft"`）、直しなら `review-<articleId>-u<YYYYMMDDHHMM>`（`mode: "update"`）
  - 査読 → 作成（書き直し）：`article-<articleId>-<round+1>`
  - 査読（A のとき）→ アイキャッチ：`eyecatch-<articleId>-<round>`
  - 公式ウォッチ・点検 → 作成（直し）：`update-<articleId>-<YYYYMMDDHHMM>`
  - 点検 → 査読（公開済みの点検）：`recheck-<articleId>-<YYYYMMDD>`
  - SNS 審査（OK のとき）→ 画像：`snsimage-<YYYYMMDDHHMM>`（`postIds` に投稿の ID）
  - SNS → SNS 審査：`snsreview-<YYYYMMDDHHMM>`、SNS 審査 → SNS（書き直し）：`sns-<articleId>-r<YYYYMMDDHHMM>`
  - 企画 → 作成（運営者が「すぐ書かせる」を選んだとき、アプリが書く）：`article-<articleId>-1`
- 書いたら起動を試す：ToolSearch で `select:mcp__claude-code-remote__fire_trigger` を読み込み、`settings/background` の相手の trigger ID を `text: "job:<ID>"` で `fire_trigger` する。読み込めない・失敗したときは、依頼を `queued` のまま残してよい（相手の定時の見回りか、運営者がアプリを開いたときに起動される）。そのことを報告に 1 行書く。
- 相手の役割が停止中（`settings/agentPause`）なら、起動しない（依頼は書いてよい）。

## 7. 最後の報告（スマホに通知される）

日本語で 3 行以内。何をしたか・何を渡したか・運営者の判断が要るもの。例：
- 「a01『H3ロケット10号機を見る方法』を書きました（1回目）。査読に回しました。」
- 「H3 10号機の延期を検知（JAXA 10/19 18:00 発表）。イベントを直し、受信箱に対応の一覧を出しました。」
- 「企画：アイデアを3件、受信箱に出しました（しし座流星群・内之浦ガイド・双眼鏡）。」
