(function(){var o=CanvasRenderingContext2D.prototype.drawImage;CanvasRenderingContext2D.prototype.drawImage=function(){if(this.globalCompositeOperation==='destination-out')return;return o.apply(this,arguments)}})();
(function(){function fix(){var s=document.querySelector('.mz-htl.is-tl .mz-htl__foot span');if(s){if(s.style.width)s.style.width=''}}[400,900,2800].forEach(function(t){setTimeout(fix,t)});window.addEventListener('load',fix);window.addEventListener('resize',function(){setTimeout(fix,300)})})();

(function(){var cs=CSS.supports.bind(CSS);CSS.supports=function(a){if(a==='animation-timeline')return false;return cs.apply(null,arguments)}})();
