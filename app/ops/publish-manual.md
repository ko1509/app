# 入稿エージェント（publisher）の手順書

**査読に通った稿を、アイキャッチごと WordPress に入稿する**（新しい記事の公開と、公開中の記事の差し替え）。本文・図・タイトル・説明文・カテゴリ・タグ・URL・アイキャッチを、稿のとおりに反映し、公開ページで確かめる。稿の中身は書き換えない。

**書き換えてよいもの**：WordPress の**入稿対象の記事の投稿**（`ops/publish_wp.py` が決まった項目だけ）とそのアイキャッチ画像（メディア）、`articles/<ID>` の `status`・`url`・`path`・`publishedAt`・`site`（下記）・`lastVerified`、`sitebackups/post-<ID>-<日時>`、受信箱 `inbox/…`（自分が出すもの、`replace-…` の完了）、`jobs/update-…`（鮮度の依頼）、自分の `jobs/<ID>`
**書き換えないもの**：稿（`draft`・`review`・`loop`）、ほかの投稿・固定ページ・テーマ・プラグイン・設定、`events`、`images`

## 0. 共通
`ops/agent-jobs.md`（共通の約束。停止の確認を含む）と `ops/site-rules.md`（とくに 4「URL」・8「直前の更新」・10「状態」）を読んでから進める。道具は `ops/publish_wp.py`（Artifact ツールの `read` で読み、保存先のまま `python3` で実行。中身を書き写さない）。認証情報は環境変数 `MIAGETABI_WP_USER`・`MIAGETABI_WP_APP_PASSWORD`（`test -n` で有無だけ確かめる。値は表示・記録しない）。

## 1. いつ動くか
- 依頼：`kind: "publish"`（画像担当がアイキャッチを作り終えたとき。運営者がアプリの「サイトに反映」を押したとき）。
- 定時：6〜23時の毎時（8分）。依頼が無くても、反映待ちの記事を拾う。
- 反映待ちが無ければ、ほかは何も読まずに「仕事なし」と報告して終わる。

## 2. 入稿してよい記事（上から全部そろったものだけ）
次の A（差し替え）か B（新しい記事）のどちらかで、さらに共通の条件を満たすもの。

- **A. 差し替え**：`status` が `公開済み` か `要更新`、`loop.replace` が `true`、`loop.state` が `passed`。かつ、まだ反映していない稿（`site.draftCreatedAt` が `draft.createdAt` と違う、または `site` が無い）。
- **B. 新しい記事**：`status` が `公開待ち`（査読 A で `loop.state` が `passed`）で、`site.postId` も `url` も無い。
- **共通**：`review.grade` が `A` で `review.pass` が `true`、`review.round` が `draft.round` と同じ（その稿を査読した）、`draft.blocks`・`draft.seo`・`draft.wp` がある、`images/<ID>-eyecatch` がある。
- **入稿しない**：`status` が `企画中`・`保留`・`見送り`、`loop.state` が `failed`・`reviewing`・`writing`（運営者が止めた・書き直し中のもの）、査読が A でないもの。アイキャッチがまだ無いものは**待つ**（画像担当が作る）。24時間待っても無ければ、受信箱に1件。

## 3. 手順
1. 共通の手順で依頼を受け取る（定時なら `jobs/publish-<YYYYMMDDHHMM>` を自分で作ってから進めてよい）。
2. `articles` を `query` し、2 章の条件に合うものを挙げる。依頼に `articleId` があればその記事だけ。**1回に3本まで**（古い順）。
3. 記事ごとに：
   1. `articles/<ID>` と `images/<ID>-eyecatch` を ArtifactData の `get`（`out_dir` つき）で、同じフォルダに保存する（`<ID>-article.json`・`<ID>-image.json` という名前に）。
   2. `python3 publish_wp.py plan <ID>-article.json <ID>-image.json`（何をするかを出すだけ）。新規か差し替えか、タイトル・URL（slug）・カテゴリ・タグが稿の `wp`・`seo` と合っているか確かめる。
   3. `python3 publish_wp.py apply <ID>-article.json <ID>-image.json`。ツールが、検査 → アイキャッチの画像をメディアに上げる → 記事を保存（POST）→ 保存された本文が書いたものと同じか確認 → 公開ページに題名とアイキャッチがあるか確認、までを行い、**失敗したら自分で元に戻す**。最後の行の JSON（`ok`・`postId`・`link`・`mediaId`・`mediaUrl`・`backup`）を読む。
   4. 成功したら `articles/<ID>` を `update`（`if_version` つき）：`site`: `{"postId", "mediaId", "mediaUrl", "link", "draftRound": draft.round, "draftCreatedAt": draft.createdAt, "publishedAt": "<今>", "by": "publisher"}`、`status: "公開済み"`、`url: <link>`、`path`（無ければ link のパス）、新規のときだけ `publishedAt`、`lastVerified`（稿の「最終確認：YYYY-MM-DD」の日付）。`loop` は変えない。
   5. `backup`（差し替え前の WordPress の内容）を `sitebackups/post-<ID>-<YYYYMMDDHHMM>` に `set`：`{"kind": "post", "articleId", "postId", "backup": <backup-<ID>.json の中身>, "at", "note"}`。
   6. 受信箱に `open` の `replace-<ID>-…` があれば、`answer: "入稿エージェントが反映しました"`・`status: "done"` にする。
4. **鮮度の確認（入稿のあと、記事ごとに）**：稿の「最終確認」が7日より前、または `eventDate` が今日より前なら、**事実が古い可能性がある**。`jobs/update-<ID>-<YYYYMMDDHHMM>`（`kind: "update"`, `note`: 「入稿した稿の最終確認が<日付>で、<理由>。今の公式で確かめ直して直しの案を」, `by: "publisher"`）を `queued` で書き、作成を起動する（`settings/background.writerTriggerId`。`ops/agent-jobs.md` の 6）。
5. **失敗したとき**（`NG:` が出た）：ツールが元に戻している。**同じ失敗を繰り返さない**（1回だけやり直してよい）。受信箱 `inbox/publish-<ID>`（**記事ごとに1件。同じ ID に `set` して上書き**。時刻を ID に付けない）を `set`：`{"kind": "other", "title": "<記事名>：サイトに反映できませんでした", "body": "どの段階で・何が起きたか（NG の文言。認証情報の値は書かない）／WordPress の状態（元に戻した）／運営者にしてほしいこと", "reason": "自動で反映できなかったため", "articleId", "status": "open", "by": "publisher", "createdAt"}`。
6. 依頼を `done`（反映した・待つだけだった）か `waiting`（受信箱に出した。`inboxId`）にし、報告する（3行以内：反映した記事と新規／差し替え、待っている記事、受信箱に出したもの）。

**同じ失敗を毎時くり返さない**：`articles/<ID>` に対応する `jobs/publish-…` の直近が `error` で、画像（`images/<ID>-eyecatch`）の `createdAt` も稿（`draft.createdAt`）もそのときから変わっていなければ、その記事は今回は入稿しない（受信箱担当が画像の作り直しなどを回す）。

## 3-2. アイキャッチのアップロードが 403 で止まるとき（実際に起きたこと）
- 原因の1つは、**画像の中身がサーバーの WAF の規則に引っかかる誤検知**。JPEG は中身がランダムなバイト列で、`/*` から約1.3KB 以内に `*/`（SQL のコメントの形）が偶然並ぶと、WAF が止める（2026-10-21 のふたご座流星群の画像で確認。成功した画像は、その間隔が 2.7KB 以上だった）。ファイル名や認証は関係ない。
- 見分け方：**認証なしで、同じ画像を `POST /wp-json/wp/v2/media` に送る**（何も作られない）。403 の素の HTML なら WAF、401 の JSON なら通っている。
- **対処（運営者の決定 10/22）**：`ops/eyecatch.py` の `save_jpeg` が、書き出した JPEG に「'#」（引用符＋#）や「/*…*/」の並びが出たら品質を1ずつずらして書き出し直す。入稿エージェントは画像に触らない。403 が出たら、画像担当に `eyecatch` の作り直しを頼む（受信箱に書く）。同じ失敗を毎時くり返さない（画像が変わるまで同じ記事の入稿を再試行しない）。
- 実際の原因（a04）：「'#」の2バイトが画像に3か所あり、WAF が SQL のコメントと誤検知した。
- やってはいけない：運営者の決定なしに画像のバイトを変えて WAF を通すこと（再エンコード・画質を変えて再送など）は、運営者が決めるまでしない。失敗として報告し、受信箱に、この診断（どの画像が・認証なしで 403 になるか）を書く。運営者の選択肢は、①WAF で `/wp-json/wp/v2/media` への書き込みを除外する（おすすめ）、②アイキャッチを作り直して中身を変える。

## 4. してはいけないこと
- 査読が A でない稿・運営者が止めた稿（`見送り`・`保留`・`loop.state` が `failed`）を入稿すること。アイキャッチ無しで入稿すること。
- 稿の中身（文・数字・日時）を直すこと。直したいことは、受信箱か `update` の依頼にする。
- 入稿対象以外の投稿・固定ページ・設定を書き換えること。`publish_wp.py` の検査を迂回すること（検査に落ちたら書かない）。
- 認証情報を表示・記録すること。WAF や権限の拒否を、コマンドの形を変えて通そうとすること。
- 反映に失敗したのに「反映した」と報告すること。
