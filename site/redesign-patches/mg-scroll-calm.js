/* ミアゲタビ：スマホでのスクロール中の揺れ（ヘッダー・年表）対策
 * スクロール中（止まって180msまで）は、requestAnimationFrame のコールバックの実行を次のフレームへ持ち越す（捨てない）。
 * 星・ロゴの点・data-px・ティッカーなど、毎フレームの描画がスクロール中だけ止まり、メインスレッドが空く。
 * 対象：タッチ端末（pointer:coarse）か、幅700px未満。パソコンでは何もしない。
 * 注意：WordPress は記号のアンパサンドを別の表記に書き換えるため、このファイルには使わない（論理積は入れ子の if にする）。 */
(function () {
  var W = window, D = document;
  if (W.__mgCalm) return;
  var touch = false;
  if (W.matchMedia) { touch = W.matchMedia('(pointer:coarse)').matches; }
  if (!touch) { if (W.innerWidth >= 700) return; }
  W.__mgCalm = 1;
  var raf = W.requestAnimationFrame.bind(W), moving = false, tm = 0;
  W.addEventListener('scroll', function () {
    if (!moving) { moving = true; D.documentElement.classList.add('mg-scrolling'); }
    clearTimeout(tm);
    tm = setTimeout(function () { moving = false; D.documentElement.classList.remove('mg-scrolling'); }, 180);
  }, { passive: true });
  W.requestAnimationFrame = function (cb) {
    return raf(function again(ts) {
      if (moving) { raf(again); return; }
      cb(ts);
    });
  };
})();
