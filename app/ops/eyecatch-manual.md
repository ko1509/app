# 画像担当（designer）の手順書（アイキャッチ・SNS の画像）

**査読で A になった稿だけ**、記事を読んでアイキャッチ（1200×630。写真風の CG の背景に、記事の見出しを組む）を作る。作成エージェントの負担を軽くし、本文の質に集中させるために分けた役割。本文が確定してから作るので、書き直しのたびに作り直さない。

**書き換えてよいもの**：`images/<articleId>-eyecatch`、`images/sns-<投稿ID>` と、その投稿の `imageId` だけ（`posts/<ID>` を `update`。ほかの項目は変えない）、`articles/<articleId>` の `draft.eyecatch`（`draft` が無い公開済みのカードは `eyecatch`）だけ（`draft` の中のほかの項目は変えない。`draft` を丸ごと読み、`eyecatch` だけ差し替えて `draft` 全体を `update`、`if_version` を付ける）、差し替え稿の受信箱 `inbox/replace-<articleId>-<round>` の `body` の末尾への1行の追記、自分の `jobs/<ID>`
**書き換えないもの**：本文（`draft.markdown`・`blocks`）・`review`・`status`・`loop`・`events`・ほかのカード

## 0. 共通
`ops/agent-jobs.md`（共通の約束。停止の確認を含む）と `ops/site-rules.md`（とくに 6「文章と表記」・10 ロゴ）を読んでから進める。道具は `ops/eyecatch.py`（Artifact ツールの `read` で読み、保存先のまま `python3` で実行）。

## 1. いつ動くか
- 依頼：`kind: "eyecatch"`。
  - 査読が A を出したとき（`jobs/eyecatch-<articleId>-<round>`、`by: "reviewer"`）。
  - 運営者がアプリの「アイキャッチを作り直す」を押したとき（`by: "app"`。`note` に指示。例：「月の背景で」「日付を外す」）。
- 依頼：`kind: "snsimage"`（SNS 審査が投稿を OK にしたとき、運営者がアプリの「作り直す」を押したとき）。手順は 5 章。SNS の画像は SNS の自動運転が止まっていても、依頼があれば作る。
- 定時（6〜23時の毎時）は依頼の見回りだけ。依頼が無ければ「仕事なし」と書いてすぐ終わる。
- **査読で A になっていない稿には作らない**（`articles/<articleId>.review.pass` が `true` でないなら、依頼を `done` にして「査読 A 前のため作りません」と報告。ただし運営者の作り直しの依頼で、カードが `公開済み` のものは作ってよい）。

## 2. 手順
1. 共通の手順で依頼を受け取る。
2. `articles/<articleId>` を読む：`draft.seo.title`（無ければカードの `title`）・`pillar`・`draft.markdown`（本文。要点ボックスの日時・場所と、記事の情景をつかむ）。公開済みならサイトの記事の見出し（`curl -sL <url>`）。
3. 日時を入れるなら、公式ページで今の値を確かめる（本文と食い違えば入れず、報告に書く）。曜日は `sky.py weekday`。
4. **直近の記事の背景を確かめる**：`articles` の `draft.eyecatch.spec`（と `eyecatch.spec`）を新しい順に10件見て、`tone`・`ground`・主なモチーフの組み合わせが同じにならないように選ぶ。
5. 3 章の決まりで spec を作り、`python3 eyecatch.py spec.json eyecatch.jpg`。
6. **できた画像を自分で開いて確かめる**（Read で画像を見る）。次のどれかなら直して作り直す（3回まで）：
   - モチーフが見出し・英語の一文・ロゴと重なって読みにくい／画面の端で切れている／シルエットが暗くて見えない
   - 記事の中身と絵が合っていない（例：昼の施設なのに打ち上げの光跡、明け方の打ち上げなのに真夜中）
   - 3 章の「描かないもの」が入っている
7. 4 章の形で保存する。
8. 差し替え稿（カードが `公開済み`・`要更新`）で、`inbox/replace-<articleId>-<round>` が `open` なら、その `body` の末尾に「アイキャッチができました（アプリの稿の画面からダウンロード）」と1行足す。
9. 依頼を `done` にし、報告する（3行以内：どの記事に、どんな背景で作ったか）。

## 3. アイキャッチの決まり
- 先に `pip install budoux`（文節で改行するため）。書体とロゴは初回に自動で取ってくる。
- 文字とレイアウトは標準の型（`layout: "cinema"`：左上に英字のカテゴリ、下に大きな見出しと副題、右下にロゴ）。**`layout` は指定しない（`transit` などの英語を大きく組む型は使わない）。** 背景はフィルム調（自動）。
- **見出し（`headline`）と副題（`sub`）は日本語。** 英語は `en`（見出しの上の小さな一文）と `kicker`（左上の小さなラベル）だけ。見出しに日本語が無いと、ツールが記事のタイトルから日本語の見出しを作り直す。
- **背景は記事ごとに描き分ける。豊富さをいちばん大事にする。** 直近の公開記事・稿と、`tone`・`ground`・主なモチーフの組み合わせが同じにならないようにする（`articles` の `draft.eyecatch.spec` を見て確かめる）。見本は `site/eyecatch/v3/*.json`・`v4/*.json`・`launch/*.json`・`v6/*.json`・`w1/*.json`（リポジトリ。流星・施設・持ち物は v4、打ち上げは launch、月食・彗星・灯台・テントは v6、アンテナ・雨・シートは w1）と同じ形。**型は毎週増えていく**ので、作る前に手順書のこの節を読み直す。
  ```json
  {"title": "<記事のタイトル>", "category": "launch",
   "headline": "H3ロケット10号機を見る", "sub": "家の近くの空・中継・種子島", "kicker": "H3 F10 / MMX",
   "date": "2026.10.20 TUE", "time": "04:41 JST", "bignum": "10", "seed": 11,
   "composition": {"tone": "dawn", "ground": "sea", "horizon": 0.76,
                   "clouds": {"y0": 0.58, "y1": 0.72, "density": 0.5},
                   "motifs": [{"type": "trail", "x": 0.52, "height": 0.50, "curve": 0.26, "plume": true}]}}
  ```
  - `en`：**英語の一文（必ず入れる）**。見出しの上に斜体で小さく入る（雑誌 TRANSIT のような味つけ）。記事の情景や気分を短く（40字まで）。例：`Before the dawn, look south.`／`A night of falling stars.`。事実と違うこと（青空でないのに blue sky など）や、宣伝の言い方は書かない。
  - `headline`：**記事のタイトルを要約した見出し（16字まで）**。長いタイトルをそのまま入れない。`sub`：副題（30字まで）。`kicker`：英字の小見出し。
  - `composition`（背景。記事の中身に合わせて選ぶ）
    - `tone`：`night`（天の川の夜）・`moonlit`（月明かりの夜）・`bluehour`（夕方・明け方の青い時間）・`dusk`（夕焼けの残り）・`dawn`（夜明け前）・`day`（昼の青空。`sun: [x, y]` で太陽の位置）
    - `ground`：`sea`（海辺）・`island`（島と町の灯り）・`lake`（湖と山と木）・`mountains`（重なる山。`rough` で険しさ）・`forest`（山と木）・`city`（街）・`hills`（低い丘）
    - `clouds`：薄い雲（`y0`〜`y1` の高さ、`density`）。`glow`：街明かりのドームの横位置（0〜1）。`milkyway`：天の川の位置と傾き（`cx`・`cy`・`angle`・`width`）。`milky: false` で天の川を消す
    - `motifs`（複数可）：`trail`（ロケットの光跡。`x`・`height`・`side`（1 右へ／-1 左へ）・`curve`。明け方の打ち上げは `plume: true` で日が当たった噴煙。**ロケットの光跡は1本だけ**。何本も同時に上がる絵はありえないので描かない）、`pad`（照明に照らされて射点に立つロケット。打ち上げ前・予定の記事に。`x`・`scale`）、`startrail`（星の軌跡）、`meteors`（流星。`rx`・`ry` は放射点、`n` は**1〜3本**。写真のように細く、尾から頭へ明るくなって消える。たくさん降る絵にしない）、`constellation`（`name`：`orion`・`gemini`・`leo`。写真に線は写らないので星だけ。線や放射点の丸は描かない）、`moon`・`bigmoon`（`cx`・`cy`・`r`）、`planets`（接近する2つの惑星）、`iss`（光の線）、`starlink`（並んだ光点）、`dome`（天文台の影）、`tripod`・`phone`（三脚とカメラ／スマホ）
    - **打ち上げ（`category: "launch"`）は、次の型から記事に合うものを選び、直近の打ち上げ記事と同じ型を続けない**：
      | 型 | 組み合わせの例 | 合う記事 |
      |---|---|---|
      | 遠くの光跡 | `trail`（`dawn`・`night`。海・島・湖） | 家や遠くの見学場から見る |
      | 明け方の噴煙 | `trail` に `plume: true`（`dawn`。雲を足す） | 明け方・夕方の打ち上げ |
      | 街の上の光跡 | `trail`（`city`。低く短く。`height` 0.4 前後） | 家の近くの空から見る |
      | 雲の中の光 | `trail` ＋ `clouds` に `litByTrail: true` | 曇りの日・天気の記事 |
      | 分離の光 | `trail` に `separation: true` | 見どころ・光跡の見分け方 |
      | 昼の噴煙 | `tone: "day"` ＋ `smoke`（`x`・`height`・`curve`・`drift`：風で流れる量） | 昼の打ち上げ |
      | 発射の瞬間 | `liftoff`（`x`・`scale`・`rise`：地面からの高さ。昼も夜も） | 射点近くの見学場・迫力を伝える |
      | 射点に立つ機体 | `pad`（`bluehour`・`dusk`。海の向こう） | 打ち上げ前・予定・延期の記事 |
      | 見学場の人々 | `deck` ＋ 遠くの `pad` か `trail` | 見学場のガイド |
      | 月の前の光跡 | `moon`（`r` 100〜130）＋ `trail`（`moonlit`） | 月が明るい夜の打ち上げ |
      | 雨の射点 | `pad` ＋ `clouds`（厚く）＋ `rain: {"amount": 0.5〜0.8, "angle": 10〜20}`（`composition` の項目。星は `stars: 0`） | 延期・天候待ちの記事 |
    - 天体の追加：`eclipse`（皆既中の赤銅色の月を**1つだけ**、写真のように。`cx`・`cy`・`r`：120〜160。欠けていく月を並べる合成は使わない）、`comet`（彗星。`cx`・`cy` が頭、`angle` が尾の向き、`length`）
    - 施設紹介（`category: "spot"`）：`lighthouse`（岬の灯台と光の帯。`x`・`size`・`beam`：-1 左へ／1 右へ）、`antenna`（大きなパラボラアンテナと施設の明かり。JAXA の通信所・施設の一般公開に。`x`・`size`・`tilt`：皿の傾き）、`observatory`（スリットが開いて中が赤く灯る天文台。`x`・`size`）、`planetarium`（ドームのある科学館。窓と街灯の明かり）、`deck`（展望デッキの手すりと、海を見る人の影。`people`：1〜4）。見学場なら `deck` と遠くの `pad` を合わせる
    - 持ち物紹介（`category: "gear"`）：手前に物を置く。`chair`（折りたたみ椅子）・`backpack`・`thermos`（水筒）・`mug`（湯気の立つカップ）・`binoculars`（こちらを向いた双眼鏡）・`bench`（`x0` から右へのベンチ。物を上に置くときは同じ `y`）・`headlamp`（赤いライト。まわりの物の縁を赤く照らす。`color` で色）・`tent`（中の明かりで光るテント。`x`・`y`・`size`）・`sheet`（地面に敷いたレジャーシート。流星群の持ち物に。`chair`・`headlamp` と合わせる）。それぞれ `x`・`y`（置く高さ）・`size`。**物は右半分（`x` 0.55〜0.92）に置き、`y` は 0.72〜0.86**（下は見出しと重なるため）。`horizon` は 0.62〜0.66 に上げる
  - `bignum`：号機・年など大きく見せたい数字（無くてもよい）。`date`・`time` は日時が公式に確定しているイベントだけ。
  - 背景は「雰囲気の絵」で、実際の空の再現ではない。実在のロケットの形・ロゴ・人物は描かない。右下に「CG ILLUSTRATION」が入る。
- `python3 eyecatch.py spec.json eyecatch.jpg` で作り、4 章の形で db に保存する。作ったら画像を開いて確かめる：モチーフが見出しと重なって読みにくい・画面の端で切れている・シルエットが暗くて見えない、のどれかなら `x`・`height`・`horizon` を変えて作り直す。

- 描かないもの：何本も同時に上がるロケット、たくさん降る流星、星座の線、実在のロケットの形・ロゴ・特定の人物、写真や他サイトの画像（JAXA などの画像は許可なく使えない）。
- 運営者の `note` の指示があれば、それを優先する（決まりに反するときは、反しない形で近づけ、報告に書く）。

## 4. 保存する形
- 画像：`images/<articleId>-eyecatch` に `set`：
  `{"kind": "eyecatch", "articleId": "a01", "dataUrl": "data:image/jpeg;base64,<eyecatch.jpg を base64 にしたもの>", "spec": {…}, "createdAt": "<今>"}`
  （`python3 -c "import base64;print(base64.b64encode(open('eyecatch.jpg','rb').read()).decode())"` で作る。ArtifactData の `file_path` に JSON ファイルを渡すと楽）
- カード：`draft.eyecatch`（`draft` が無ければ `eyecatch`）に `{"spec": {…}, "imageId": "<articleId>-eyecatch", "round": <稿の round>, "createdAt": "<今>"}`。

## 5. SNS の画像（`kind: "snsimage"`）
SNS 審査が OK にした投稿（`postIds`）に画像を作る。運営者の「作り直す」の依頼も同じ（`note` に指示）。
1. 投稿ごとに `posts/<ID>` を読む。`status` が `審査済み` でないもの（作り直しの依頼を除く）、`予約済み`・`投稿済み` のものは作らない。
2. 形：`channel` が `X` なら `"format": "x"`（1200×675）、`Instagram` なら `"format": "ig"`（1080×1350）。`imageBrief` の `label`・`headline`・`sub`・`bigdate`・`bigdate_sub`・`en` をそのまま spec に入れ、`scene` から 3 章の `composition` を選ぶ。`handle` に `settings/sns` の Instagram のユーザー名（`@` つき。未設定なら入れない）。
   - 縦長（ig）は下 40% に文字が入る。`horizon` は 0.50〜0.62 にして、主役（光跡・月・物）を上半分に置く。
   - 同じ題材の X と Instagram は、同じ情景で形だけ変える（`seed` も同じ）。
   - 直近の SNS 画像（`images` の `kind: "sns"` の `spec`、新しい順に10件）と背景がかぶらないようにする。
3. 作った画像を開いて確かめる（2 章の 6 と同じ基準。日時が本文と同じかも）。
4. `images/sns-<投稿ID>` を `set`：`{"kind": "sns", "postId", "format", "dataUrl", "spec", "createdAt"}`。`posts/<ID>` に `imageId: "sns-<投稿ID>"` を `update`（`if_version` つき）。
5. 依頼を `done` にし、報告する（3行以内：何件作ったか）。
見本は `site/sns/samples/*.json`（リポジトリ）。

## 6. してはいけないこと
- 本文・査読結果・状態・投稿の文を書き換えること。査読 A 前の稿に作ること（運営者の依頼で公開済みのものは除く）。
- 写真・他サイトの画像を使うこと。AI の画像を写真として扱うこと（右下の「CG ILLUSTRATION」を消さない）。
- 確かめていない日時を入れること。
