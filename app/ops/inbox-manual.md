# 受信箱担当（steward）の手順書

このサイトは**エージェントによる自動運転が基本**。受信箱（`inbox`）に出たものは、**まず全部、エージェントが自分で片づける**。運営者の判断に回すのは、エージェントには**できないこと**（認証情報・お金・契約・サーバーや外部サービスの設定の変更）だけ。受信箱担当は、受信箱の `open` を1件ずつ見て、下の表のとおりに**処理して閉じる**。記事は書かない・直接サイトを書き換えない（既にある役割に仕事を回す）。

**書き換えてよいもの**：`inbox/<ID>`（`status`・`answer`・`answeredAt`・`handledBy`・`ownerOnly`・`ownerReason`）、`articles/<ID>` の `loop`・`status`（下の決まりの範囲）・`autoFix`、各役割への依頼 `jobs/…`、自分の `jobs/<ID>`、`settings/plannerLog`・`settings/writerLessons`（追記のみ）
**書き換えないもの**：稿（`draft`・`updateDraft` の中身）・`review`・`events`・`posts`・`images`・`settings` のほか・WordPress

## 0. 共通
`ops/agent-jobs.md`（共通の約束。停止の確認を含む）、`ops/site-rules.md` を読んでから進める。環境変数・認証情報は見ない。

## 1. いつ動くか
- 定時：6〜23時の毎時（40分）。
- 依頼：`kind: "steward"`（アプリの「いま処理」。受信箱に新しいものが出たとき）。
- `inbox` を `query`（`status == "open"`）して、**`ownerOnly` が `true` でないもの**が無ければ「仕事なし」と書いてすぐ終わる。

## 2. 処理の表（`kind` と中身で決める）
閉じるときは `status: "done"`（対応した）か `"dismissed"`（要らなくなった）、`answer` に何をしたかを1〜2行、`answeredAt`、`handledBy: "steward"` を書く。**処理に使った依頼の ID を `answer` に書く**。

| 受信箱のもの | 処理 |
|---|---|
| `publish-…`（入稿の失敗） | 記事の `site.draftCreatedAt` が `draft.createdAt` と同じ（もう反映済み）なら `dismissed`「解消済み」。そうでなく、画像（`images/<ID>-eyecatch`）が出した日時より新しければ `dismissed`「画像が作り直された」（入稿が次の定時に拾う）。まだ同じ失敗で、本文に「403」「WAF」があれば、画像担当に `jobs/eyecatch-<ID>-<日時>`（`kind: "eyecatch"`, `note`: 「入稿が WAF の 403 で止まった。`save_jpeg` で書き出し直して作り直す（seed は同じ）」）を作って起動し、`done`。**同じ記事で3回続いたら**、`ownerOnly: true`・`ownerReason`（何が起きたか・運営者にしてほしいこと）を書いて残す（WAF の設定は運営者の操作）。 |
| `audit`（点検） | `proposal.items` を1件ずつ：`articleId` があり、その記事に進行中の直し（`loop.state` が `writing`・`reviewing`、または `jobs` の `article`・`update`・`review` が `queued`・`running`）が無ければ、3 章の「差し替えを回す」。あるなら何もしない。`articleId` が無い項目（アクセス解析など）は、`analytics/summary.status` が `error` のときだけ 5 章の `ownerOnly` に回す。すべて処理したら `done`。 |
| `change`（公式の変化・直しの案 査読A） | 記事（`articleId`）を3 章の「差し替えを回す」。`note` に、受信箱の `body`（直しの案の表と履歴の1行・`alsoFix`）をそのまま入れる。回したら `done`。イベント（`eventId`）の変化で記事が無いものは、サイト更新に `jobs/siteupdate-<日時>` を作って起動し `done`。 |
| `loopFailed`（査読で止まった） | 記事の `autoFix`（無ければ 0）を見る。**2未満**なら、受信箱の `body`（残っている指摘）を `note` にして3 章の「差し替えを回す」（`autoFix` を +1）、`done`。**2以上**なら見送る：新しい記事（`status` が `執筆中`・`査読中`）は `status: "保留"`・`loop.state: "failed"` のままにして `settings/writerLessons` に「何が通らなかったか」を足し、`dismissed`。公開済みの直しは、稿を捨てずそのまま、公開中のページは変えない（`dismissed`「公開中のページは現状のまま」）。 |
| `planReview`（企画の見直し） | 企画エージェントに `jobs/plan-<pillar>-<日付>` で作り直しを頼み、カードは `見送り`（`settings/plannerLog` に理由を足す）、`done`。 |
| `idea`（企画案） | `ops/site-rules.md` の「3つの問い」を満たし、既存のカードと題材が重ならないなら、カードを `企画中` で作る（`proposal` の項目をそのまま。ID は既存の最大＋1）、`done`。満たさなければ `dismissed` に理由。 |
| `question`（エージェントからの質問） | `ops/site-rules.md`・各手順書・公式ページで答えが出せるなら、答えを `answer` に書き、その記事の作成に書き直しを頼む（3 章）、`done`。**運営者しか知らないこと**（認証情報・お金・契約・本人の経験や写真）なら、`ownerOnly: true` で残す。 |
| `recheck`（公開済みの点検の P0） | 3 章の「差し替えを回す」（急ぎ）、`done`。 |
| ほか（`other`） | 中身を読み、上のどれかに当てはまるなら同じ処理。何かの失敗の通知なら、原因が直っているか確かめて `dismissed`。どれでもなく、運営者にしかできないなら `ownerOnly: true`。 |

## 3. 差し替えを回す（公開中の記事を、全文の差し替え稿に書き直して自動で反映する）
公開中の記事の直しは、**全文の差し替え稿**（`ops/article-manual.md` の 10 章）にして、査読 A → アイキャッチ → 入稿の自動の流れに乗せる。
1. 記事の `status` が `公開済み`・`要更新` で、`loop.state` が `writing`・`reviewing` でないことを確かめる（進行中ならそれに任せる）。
2. `round` = （`loop.round` + 1）。`jobs/article-<ID>-<round>` を `queued` で `set`：`{"kind": "article", "articleId", "round", "title", "replace": true, "rewrite": true, "withExperience": false, "note": "<直す理由と、直す箇所の表・指摘。根拠の URL>", "by": "steward", "message": "書くのを待っています", "createdAt", "updatedAt"}`。
3. `articles/<ID>` を `update`（`if_version`）：`loop: {"state": "writing", "round": <round>, "max": <settings/reviewLoop.maxRounds、無ければ5>, "base": <loop.round、無ければ0>, "replace": true, "updatedAt": "<今>"}`。`status` は変えない。`updateDraft` は捨てずに残す。
4. 作成を起動する（`settings/background.writerTriggerId`。`ops/agent-jobs.md` の 6）。

## 4. 起動のしかた
他の役割の起動は `ops/agent-jobs.md` の 6 のとおり（`settings/background` の `…TriggerId` を `fire_trigger` に渡す。追加テキストに `job:<ID>`）。起動できなくても依頼は残るので、定時で拾われる。

## 5. 運営者の判断に残すもの（`ownerOnly: true`）
次のときだけ：認証情報・パスワード・鍵の入れ直し／お金・契約・規約／WAF・サーバー・外部サービスの設定の変更／運営者本人の経験・写真・好み。`ownerReason` に**何が起きたか・運営者が何をすればよいか（具体的な手順）**を書く。それ以外を残さない。`ownerOnly` にしたものは、自分では閉じず、運営者が閉じる。

## 6. 終わり
自分の `jobs/steward-<YYYYMMDDHHMM>`（定時）か依頼を `done` にし、報告する（2行以内：片づけた件数と内訳、運営者に残した件数）。

## 7. してはいけないこと
- 稿・査読・WordPress を直接書き換えること。記事を書くこと。
- 運営者にしかできないことを、推測で埋めて閉じること。
- 理由を書かずに閉じること。同じ記事に、進行中の直しがあるのに、重ねて差し替えを回すこと。
- 認証情報を表示・記録すること。
