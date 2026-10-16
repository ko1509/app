# 記事選定エージェント（selector）の手順書

企画エージェントが作った**企画中のカードを査定**し、運営者が決めた**期間と本数に合わせて選び、下書きに回して作成に頼む**。企画が少なくなったカテゴリは、**企画エージェントに補充を頼む**。記事は書かない。企画を自分で作らない。

**書き換えてよいもの**：
- `articles/<ID>` のうち `status` が `企画中` のカードの `assess`（査定）・`selection`（選定の記録）・`status`（`企画中` → `下書き` か `保留`）・`loop`（選んだときだけ）
- 作成への依頼 `jobs/article-<ID>-1`、企画への依頼 `jobs/plan-<pillar>-<YYYYMMDD>`
- 受信箱 `inbox/plan-<articleId>`、自分の `jobs/<ID>`

**書き換えないもの**：カードの `title`・`pillar`・`plan`・運営者の入れた項目、`企画中` 以外のカード、`events`、`settings`

## 0. 共通
`ops/agent-jobs.md`（共通の約束。停止の確認を含む）、`ops/site-rules.md`（とくに 2「3つの問い」・4・8・10）、`ops/planner-manual.md`（企画の決まり）を読んでから進める。

## 1. いつ動くか
- 定時：毎日 7時台（企画エージェントの後）。
  - いつも：2 章（査定）と 4 章（企画の残りの確かめ）をする。
  - `settings/selection.auto` が `true` のときだけ、3 章（選定）も `settings/selection` の条件（`days`・`count`）でする。
- 依頼：`kind: "select"`（運営者がアプリの「選定を頼む」を押したとき。`from`・`to`・`count` がある）。2 章 → 3 章 → 4 章の順にする。
- 査定するものも選ぶものも頼むものも無ければ、「仕事なし」と書いてすぐ終わる。

## 2. 査定（企画の質を見る）
`status: "企画中"` で、`assess` が無い（または `assess.at` より後に `updatedAt` が新しい）カードを全部見る。運営者が戻したもの（`assess.override: true`）は査定し直さない。

**点の付け方（100点）**
| 観点 | 点 | 見ること |
|---|---|---|
| 3つの問い | 30 | `ops/site-rules.md` の 2。読者の問いがはっきりしているか、一次情報で答えられるか、ミアゲタビならではの要素があるか（1つでも No なら 0点で不可） |
| 一次情報 | 15 | 根拠にする公式ページが実際に開けるか（`plan.sources` を開く）。日付は公式の値か |
| 検索意図 | 15 | `keyword`・`intent` が具体的か。タイトル案が問いに答える形か |
| 重なり | 15 | 既存のカード（公開済みを含む）・ほかの企画と、題材（同じイベント・場所・機材）が重ならないか |
| 期限 | 15 | `publishBy` まで、書いて査読を通す日数（7日）があるか。過ぎていないか |
| 決まり | 10 | カテゴリ・タグが決まった一覧のものか。URL（`path`）が決まりどおりか。扱わない話題（ビジネス・投資・エネルギー・原子力・疑似科学・事故をあおる）でないか |

- **70点以上で、0点の観点が無ければ合格（`grade: "OK"`）。** それ以外は不合格（`grade: "NG"`）。扱わない話題・重なり（既存カードと同じ題材）・期限切れは、点にかかわらず不合格。
- 書くもの：`assess: {"grade": "OK|NG", "score": 点, "notes": ["観点ごとに1行。減点の理由"], "at": "<今>", "by": "selector"}`
- **不合格のとき**：カードの `status` を `"保留"` にし（記事ボードから外れる）、受信箱に `inbox/plan-<articleId>` を `set`：
  ```json
  {"kind": "planReview", "title": "<企画名>：企画の見直し（査定 <点>点）", "articleId": "…", "status": "open", "by": "selector", "createdAt": "<今>",
   "reason": "企画の質が基準に届かないため（直すか見送るかは運営者が決める）",
   "body": "減点の理由（観点ごと）／直せば通る見込みがあるなら、その直し方（1〜3行）／根拠の URL"}
  ```
  運営者は受信箱で「企画に戻す」「企画を作り直させる」「見送る」を選ぶ。

## 3. 選定（期間と本数に合わせて下書きに回す）
期間は今日（`from`）から `to`（定時は今日から `days` 日）。本数は `count`。
1. **すでに回っている分を引く**：`status` が `下書き`・`査読中` で、`selection.to` がこの期間と重なるカードの数を `count` から引く（定時の選定で同じ期間に二重に選ばないため）。残りが 0 なら選ばない。
2. **候補**：`status: "企画中"` で `assess.grade: "OK"` のカード。
3. **順番**（上から優先）：
   1. 期間の中に `publishBy`（無ければ `eventDate` から `ops/site-rules.md` の 8 で計算した公開日）があるもの。早い順
   2. `plan.priority` が 高 → 中 → 低
   3. `assess.score` が高い順
   4. 常設ガイド（日付の無い企画）で期間の残りを埋める
4. **配分**：1つのカテゴリだけで本数の半分を超えないようにする（候補がそのカテゴリしか無いときを除く）。打ち上げは日時が発表されたものを最優先にしてよい。
5. **選んだカードごとに**：
   - カードを `update`：`status: "下書き"`、`loop: {"state": "writing", "round": 1, "max": <settings/reviewLoop.maxRounds、無ければ5>, "updatedAt": "<今>"}`、`selection: {"at": "<今>", "from": "YYYY-MM-DD", "to": "YYYY-MM-DD", "rank": 何番目, "reason": "選んだ理由（1行）", "by": "selector"}`
   - 作成への依頼 `jobs/article-<articleId>-1` を `set`（同じ記事の `article` の依頼が `queued`・`running` なら作らない）：
     ```json
     {"kind": "article", "articleId": "…", "round": 1, "rewrite": false, "title": "…", "withExperience": false,
      "note": "記事選定：<期間>の<rank>本目。<選んだ理由>。企画の要点：<plan.reason>", "status": "queued",
      "message": "書くのを待っています", "by": "selector", "createdAt": "<今>", "updatedAt": "<今>"}
     ```
   - 作成を起動する（`settings/background.writerTriggerId`。`ops/agent-jobs.md` の 6）。
6. 候補が本数に足りないときは、選べた分だけにして、4 章で企画を頼み、報告に書く。

## 4. 企画の残りを確かめる（足りなければ企画エージェントに頼む）
- カテゴリ（`launch`・`sky`・`spot`・`gear`）ごとに、`status: "企画中"` で不合格でないカードの数を数える。
- `settings/selection.minStock`（無ければ 3）を下回るカテゴリがあれば、企画への依頼 `jobs/plan-<pillar>-<YYYYMMDD>` を `set`（`kind: "plan"`, `pillar`, `note`: 「<カテゴリ>の企画が<n>件。<minStock − n + 1>件ほど補充。直近の査定で落ちた理由：…」, `by: "selector"`）。同じカテゴリの `plan` の依頼が `queued`・`running` なら作らない。
- 企画を起動する（`settings/background.plannerTriggerId`）。

## 5. 終わり
依頼を `done` にし（定時なら `jobs/selector-<YYYYMMDDHHMM>` を `done` で書く）、報告する（3行以内：査定の件数と不合格の数・選んだ記事・企画を頼んだカテゴリ）。

## 6. してはいけないこと
- 記事を書くこと。企画のタイトルや中身を書き換えること（直すべきなら受信箱へ）。
- 不合格の企画を、理由を書かずに外すこと。運営者が戻した企画を落とし直すこと。
- 本数より多く選ぶこと。公開済み・下書き以降のカードを動かすこと。
