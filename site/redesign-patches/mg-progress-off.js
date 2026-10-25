/* ミアゲタビ：記事の進捗バー（.mg-prog）を廃止する実験（スマホでヘッダーが揺れる件の切り分け）
 * 本体のスクリプトがヘッダーの中に作る .mg-prog を、作られた瞬間に取り除く。フッター直前のウィジェットに入れる（本体より前に動く）。
 * 注意：WordPress が書き換える記号（アンパサンド・小なり）は、このファイルに使わない。 */
(function () {
  var W = window, D = document;
  if (W.__mgProgOff) return;
  W.__mgProgOff = 1;
  var mo = null;
  function look() {
    var n = D.querySelectorAll('.mg-prog, .mg-prog2');
    for (var i = 0; i !== n.length; i++) { if (n[i].parentNode) n[i].parentNode.removeChild(n[i]); }
  }
  look();
  if (W.MutationObserver) {
    mo = new W.MutationObserver(look);
    mo.observe(D.documentElement, { childList: true, subtree: true });
    W.addEventListener('load', function () { look(); setTimeout(function () { mo.disconnect(); }, 5000); });
  }
})();
