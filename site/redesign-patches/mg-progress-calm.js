/* ミアゲタビ：記事の進捗バーを、ヘッダーの外の固定要素にする（スマホでヘッダーが揺れる件の対策）
 * 元の進捗バー（.mg-prog）は、固定のヘッダーの「中」にあって、スクロールのたびに、記事と全見出しの位置を測ってから、バーの幅を書き換えていた。
 * → ヘッダーから外して捨て、body 直下の固定要素（.mg-prog2）に置き換える。幅の更新は、1フレームに1回までにして、位置の値は最初に測って持っておく。
 *   スクロール中に、ヘッダーの中身は書き換えない。
 * フッター直前のウィジェットに入れる（本体のスクリプトより前に動くので、.mg-prog が作られるのを待って差し替える）。
 * 注意：WordPress は記号のアンパサンドと「小なり」を書き換える恐れがあるので、このファイルには使わない（論理積は入れ子の if、比較は「>」だけ）。 */
(function () {
  var W = window, D = document;
  if (W.__mgProg2) return;
  W.__mgProg2 = 1;
  var done = false, mo = null;
  function start(old) {
    if (done) return;
    var pc = D.querySelector('.post_content');
    if (!pc) return;
    done = true;
    if (mo) mo.disconnect();
    var bar = D.createElement('div');
    bar.className = 'mg-prog2';
    bar.setAttribute('aria-hidden', 'true');
    D.body.appendChild(bar);
    if (old.parentNode) old.parentNode.removeChild(old);
    var top = 0, h = 1, vh = W.innerHeight, last = -1, pend = 0;
    function measure() {
      var r = pc.getBoundingClientRect();
      top = r.top + W.scrollY; h = r.height; vh = W.innerHeight;
    }
    function paint() {
      pend = 0;
      var p = (W.scrollY - top + vh * 0.3) / Math.max(1, h - vh * 0.4);
      if (p > 1) p = 1;
      if (p > 0) { } else { p = 0; }
      if (Math.abs(p - last) > 0.0005) { last = p; bar.style.transform = 'scaleX(' + p.toFixed(4) + ')'; }
    }
    function req() { if (!pend) { pend = 1; W.requestAnimationFrame(paint); } }
    measure(); paint();
    W.addEventListener('scroll', req, { passive: true });
    W.addEventListener('resize', function () { measure(); req(); });
    W.addEventListener('load', function () { measure(); req(); });
    if (W.ResizeObserver) { new W.ResizeObserver(function () { measure(); req(); }).observe(pc); }
  }
  function look() {
    var old = D.querySelector('.mg-prog');
    if (old) start(old);
  }
  look();
  if (done) return;
  if (W.MutationObserver) {
    mo = new W.MutationObserver(look);
    mo.observe(D.documentElement, { childList: true, subtree: true });
  }
  W.addEventListener('load', function () { look(); setTimeout(function () { if (mo) mo.disconnect(); }, 5000); });
})();
