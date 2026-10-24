/* ミアゲタビ：スマホでのスクロール中の揺れ（ヘッダー・年表）対策
 * フッターコード（loos_customizer[foot_code]）の既存の <script> の「あと」に、別の <script> として足す。
 * 仕組み：スクロール中（指が動いている間＋止まって180msまで）は、requestAnimationFrame のコールバックを実行せず、次のフレームへ持ち越す。
 *   → 星の canvas・ロゴの点・data-px・ティッカーなど、毎フレームの描画がスクロール中だけ止まり、メインスレッドが空く。
 *   （iOS の Safari は、メインスレッドが忙しいと sticky／fixed の要素が追いつかず揺れるため）
 * 対象：タッチ端末（pointer:coarse）か、幅700px未満。パソコンでは何もしない。止めるのは「描画の更新」だけで、コールバックは捨てない。 */
(function () {
  var W = window, D = document;
  if (!(W.matchMedia && W.matchMedia('(pointer:coarse)').matches) && W.innerWidth >= 700) return;
  if (W.__mgCalm) return; W.__mgCalm = 1;
  var raf = W.requestAnimationFrame.bind(W), moving = false, tm = 0;
  W.addEventListener('scroll', function () {
    if (!moving) { moving = true; D.documentElement.classList.add('mg-scrolling'); }
    clearTimeout(tm);
    tm = setTimeout(function () { moving = false; D.documentElement.classList.remove('mg-scrolling'); }, 180);
  }, { passive: true });
  // 他のスクリプトの requestAnimationFrame を包む（呼び出し側は変えない）。スクロール中は、実行を次のフレームへ送るだけ
  W.requestAnimationFrame = function (cb) {
    return raf(function again(ts) {
      if (moving) { raf(again); return; }
      cb(ts);
    });
  };
})();
