# 公式ウォッチエージェント（watch）の手順書

打ち上げの延期・日程変更・中止と、天体イベント・施設の変更を、公式の発表からいち早く見つける。見つけたらアプリのイベントを直し、運営者に「何を直すか」の一覧を受信箱で知らせ、作成エージェントに記事の直しの案を頼む。毎朝の見回りでは、直前更新（T−7・T−3・T−1・当日・翌日）の依頼も積む。

**書き換えてよいもの**：`events/<ID>` の `date`・`time`・`dateText`・`status`・`note`・`source`・`history`・`checkedAt`、受信箱 `inbox/change-…`、作成への依頼 `jobs/update-…`、自分の `jobs/<ID>`
**書き換えないもの**：`events` の `title`・`pillar`・`place`、`articles`（カード）、公開中のサイト

## 0. 共通
`ops/agent-jobs.md`（共通の約束。停止の確認を含む）と `ops/site-rules.md`（とくに 8「直前の更新」「延期が発表されたら」）を読んでから進める。

## 1. いつ動くか
- 定時：1日4回（6時台・12時台・18時台・22時台）。6時台の回だけ、3 章の「直前更新の依頼」もする。
- 依頼：`kind: "watch"`（運営者がアプリの「公式を確認」を押したとき。`eventId` があればそのイベントだけ）。
- 新しいイベントを足すのはイベント取得エージェント。公式ウォッチは既にあるイベントの変化だけを見る（新しい打ち上げの発表に気づいたら、報告に1行書く）。
- 見る対象が無いとき（日付が今日から30日以内で、`status` が `確定`・`予定`・`延期` のイベントが1つも無い）は、「見る対象なし」と報告してすぐ終わる。

## 2. 見る対象と見る場所
対象：`events` のうち、`date` が今日の前日〜30日後（未定なら `status` が `予定`・`延期`）のもの。打ち上げ（`pillar: "launch"`）を先に見る。

| 題材 | 見る場所（実際に開く） |
|---|---|
| JAXA の打ち上げ | 特設ページ（`events.source`）、プレスリリース https://www.jaxa.jp/press/ 、打ち上げ情報 https://fanfun.jaxa.jp/countdown/ |
| カイロス（スペースワン） | https://www.space-one.co.jp/ のお知らせ、和歌山県の見学の案内 https://www.wakayama-rocket.com/ |
| ZERO（インターステラ） | https://www.istellartech.com/ のお知らせ |
| 見学場・交通規制 | 南種子町・肝付町・串本町のお知らせ（`events.source` か記事の出典） |
| 天体イベント | 国立天文台 ほしぞら情報（日時の変更は通常ないが、見え方の条件の訂正を見る） |
| 施設 | 施設の公式サイトの休館・臨時開館のお知らせ |

SNS（JAXA の公式 X など）は手がかりにだけ使う。**公式サイトの発表で確かめられたものだけ**を変化として扱う。

## 3. 手順
1. 共通の手順で依頼を受け取る（定時なら `jobs/watch-<YYYYMMDDHHMM>` を自分で作ってから進めてよい）。
2. 対象のイベントごとに公式ページを開き、日付・時刻・状況を `events` の値と比べる。曜日は `sky.py weekday` で確かめる。
3. **変化があったら**（日時の変更・延期・中止・再開・見学の中止など）：
   1. `events/<ID>` を `update`（`if_version` つき）：新しい `date`・`time`・`status`（`延期`・`中止`・`確定` など）・`note`（発表の要点1行）・`source`（発表のURL）・`checkedAt`、`history` に `{"at": "<今>", "from": {"date", "time", "status"}, "to": {"date", "time", "status"}, "source": "URL", "summary": "1行"}` を足す（配列全体を書く）。
   2. 受信箱に `inbox/change-<eventId>-<YYYYMMDDHHMM>` を `set`：
      ```json
      {"kind": "change", "title": "<イベント名>：延期（新しい日は未定）", "status": "open", "by": "watch", "createdAt": "<今>",
       "eventId": "…", "articleId": "（関係する公開済みカードがあれば最初の1つ）",
       "reason": "公開中の記事・ホームは運営者が直すため（目標：発表から30分以内）",
       "body": "発表の要点（いつ・誰が・何を）と URL。\n\n直すところ：\n- [ ] 記事 …（URL）の要点ボックス「今の状況」→ 延期 [delay]、新しい日時\n- [ ] 最終確認の日時・更新履歴を1行\n- [ ] ホームのカウントダウン data-target と表紙カード・ティッカー・UPCOMING（2回ずつ）\n- [ ] 図鑑 /rockets/… の NEXT と /launch/schedule/ の表\n- [ ] X で告知",
       "proposal": {"from": {"date": "", "time": "", "status": ""}, "to": {"date": "", "time": "", "status": ""}, "source": "URL", "articles": ["a01"]}}
      ```
      同じイベントの同じ変化の `open` があれば作らない。
   3. **サイト更新に渡す**：`jobs/siteupdate-<YYYYMMDDHHMM>`（`kind: "siteupdate"`, `note`: 「<イベント名>の日付・状況が変わった」, `by: "watch"`）を `queued` で書き、サイト更新を起動する（`settings/background.siteUpdateTriggerId`。`ops/agent-jobs.md` の 6）。同じ依頼が `queued`・`running` なら作らない。ホームのカウントダウン・ティッカー・UPCOMING は、サイト更新が直す（運営者が貼り替えるのは、サイト更新が WordPress に書けなかったときだけ）。
   4. そのイベントを題材にした記事（`articles` で `eventDate` か `title` が一致し、`status` が `公開済み`・`要更新`・`公開待ち`）ごとに、作成へ `jobs/update-<articleId>-<YYYYMMDDHHMM>` を依頼（`kind: "update"`、`note` に「急ぎ：<発表の要点>（URL）。inboxId: <上のID>」）。`公開待ち` の記事は `kind: "article"` の書き直し（`round` は `loop.round + 1`）にする。
4. **変化がなければ**：`events/<ID>` の `checkedAt` だけ更新する。
5. **直前更新の依頼（6時台の回だけ）**：公開済みの記事で、題材のイベントが今日から見て T−7・T−3・T−1・当日（T−0）・翌日（T+1）にあたるものに、作成へ `jobs/update-<articleId>-<YYYYMMDD>` を依頼（`note` に「直前更新 T−3：<ops/site-rules.md の 8 のその日の作業>。draft.updateChecklist の T−3 の項目」）。同じ記事の `update` が `queued`・`running` なら作らない。
6. 依頼を `done` にし、報告する（3行以内：変化があったもの、受信箱に出したもの、積んだ直し）。変化が無ければ「変化なし（○件確認）」の1行。

## 4. 判断の決まり（上から順に効く）
1. 公式サイトに日時・状況の発表がある → 変化として扱う。
2. 報道・SNS だけで、公式に発表が無い → 変化として扱わない。受信箱に `kind: "other"` で「公式未発表だが報道あり」と URL を出す（同じものが `open` なら出さない）。
3. 公式のページが開けない → 変えない。報告に書く。2回続けて開けなければ受信箱に出す。
4. 打ち上げの「予備期間」の中で日がずれただけでも、変化として扱う（読者の予定が変わるため）。

## 5. してはいけないこと
- 報道や SNS のうわさで、イベントの日時・状況を書き換えること。
- 記事・図鑑・ホームを自分で直すこと（記事の案は作成エージェント、直すのは運営者。ホームの3か所だけはサイト更新が直す）。
- 1つの変化で、受信箱に何件も出すこと（1つのイベントの1つの変化に1件）。
