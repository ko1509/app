# スマホ（iPhone Safari）でヘッダーと年表が揺れる件の対策

2026-10-24 の引き継ぎメモ（別環境での作業）を受けて、ライブのサイト（https://miagetabi.space/history/）の実際の CSS・JS を読んで作った対策。
**この環境には WebKit（iOS）も WordPress の管理画面のログインも無いため、実機の確認と反映は行っていない。**

## 1. 対策1：スクロール中は描画を止める（`mg-scroll-calm.js`）
- 追加するもの：フッターコード（`loos_customizer[foot_code]`）の、既存の `<script>` の**あと**に、別の `<script>` として足す。既存のコードは変えない。
- 動き：タッチ端末（`pointer:coarse`）か幅700px未満のとき、スクロール中（止まって180msまで）は `requestAnimationFrame` のコールバックを次のフレームへ持ち越す。コールバックは捨てない。パソコンでは何もしない。
- ねらい：星の canvas・ロゴの点・`data-px`・ティッカーなど、毎フレームのメインスレッドの仕事をスクロール中だけ止める。iOS はメインスレッドが忙しいと sticky／fixed の要素が追いつかず揺れるため（引き継ぎメモの推定原因 1・4・5 に効く見込み）。
- 手元の確認（Chromium・スマホ相当の画面・ライブのヒストリーで1600pxをスクロール）：
  - スクロール中の canvas 描画の呼び出し：**7,735回 → 1,351回（約83%減）**。エラーなし。スクロール位置・見た目は同じ。
  - Chromium では、もともと長いタスクが出ない（性能の高い環境のため）。**iPhone で揺れが減るかは、実機でしか分からない。**
- 戻し方：足した `<script>` を消すだけ。

## 2. ライブのコードを読んで分かったこと（原因の候補の絞り込み）
- `frame()`（星・流れ星・ロゴ）は常時 rAF で動く。スマホは33msに間引き済みだが、スクロール中も動いている → 対策1で止める。
- `punch()`（`punchRects`・`blockRects`）は、本文の全テキストノードと最大500要素の `getBoundingClientRect` を測る重い処理。`scroll` のたびに `prT=0` に戻して**毎フレーム測り直す**作りだが、動くのは「打ち上げの演出（`launches.length`）」の最中だけ。演出中にスクロールすると強く揺れる可能性がある。→ 対策2の候補。
- `#mg-stars,#mg-fx{position:fixed;inset:0;width:100vw;height:100vh}`：iOS の下部バーの出入りで `100vh` と見えている高さがずれる。JS は `100vh` のプローブで canvas の大きさを固定済みなので、揺れの主因ではなさそう。
- `#body_wrap{overflow-x:clip!important}`：iOS の古い版では sticky に影響する例がある。→ 対策3の候補（横スクロールが出ないか要確認）。
- `.l-header{position:sticky;top:var(--wp-admin--admin-bar--height,0px)}`、`.mz-htl__stick{position:sticky;top:var(--hdr)}`：ヘッダーの高さは小数2桁で保持済み。

## 3. 次に試す順番（対策1で直らないとき）
1. **対策2**：`punch()` を、スクロール中は呼ばない（`W.addEventListener('scroll',function(){prT=0})` を、`prT=t` に変えて測り直しを間引く。または演出中は `moving` のとき `punch` を飛ばす）。
2. **対策3**：スマホだけ `#body_wrap{overflow-x:visible!important}` にして、`html{overflow-x:hidden}` で横のはみ出しを抑える。**ページが横に動かないか**を確かめてから。
3. **対策4**：ヘッダーをスマホだけ `position:fixed` にして、同じ高さのスペーサーを入れる。
4. **対策5**：ヒストリーのスマホ版は、固定ステージをやめて、ネイティブの横スクロール（`is-static`）にする。

## 4. 実機で切り分けてほしいこと（iPhone）
- 場所：ヒストリーか記事か ／ タイミング：指で動かしている間か、止まる直前か ／ 揺れるもの：ヘッダーだけか、年表も ／ 通常ブラウズとプライベートブラウズの違い。
- 対策1を入れたあとの変化（「少し減った」「変わらない」「年表だけ残る」など）。

## 5. 反映のしかた（引き継ぎメモの手順）
管理画面のカスタマイザーを開いたタブで、`mg-scroll-calm.js` を `<script>…</script>` で包んだものを、`wp.customize('loos_customizer[foot_code]')` の値の**最後**に足して、`wp.customize.previewer.save()`。SiteGuard Lite（WAF）はオンのまま。設定は変えない。
