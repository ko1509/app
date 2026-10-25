(function(){var o=CanvasRenderingContext2D.prototype.drawImage;CanvasRenderingContext2D.prototype.drawImage=function(){if(this.globalCompositeOperation==='destination-out')return;return o.apply(this,arguments)}})();
(function(){function fix(){var s=document.querySelector('.mz-htl.is-tl .mz-htl__foot span');if(s){if(s.style.width)s.style.width=''}}[400,900,2800].forEach(function(t){setTimeout(fix,t)});window.addEventListener('load',fix);window.addEventListener('resize',function(){setTimeout(fix,300)})})();

(function(){var cs=CSS.supports.bind(CSS);CSS.supports=function(a){if(a==='animation-timeline')return false;return cs.apply(null,arguments)}})();

(function(){var D=document,kn=null,raf=0;
function knots(){var sec=D.querySelector('.mz-htl'),tr=D.querySelector('.mz-htl__track'),vp=D.querySelector('.mz-htl__vp');if(!sec||!tr||!vp)return null;var mx=Math.max(1,tr.scrollWidth-vp.clientWidth),k=[],bad=false,ls=sec.querySelectorAll('.mz-htl__foot>div:last-child span');
Array.prototype.forEach.call(ls,function(l,i){var e=tr.querySelector('.mz-ev[data-yr="'+l.textContent.trim()+'"]');if(!e){bad=true;return}k.push(i===0?0:Math.min(1,Math.max(0,(e.offsetLeft-20)/mx)))});
if(bad||k.length<2)return null;return k}
function upd(){raf=0;var sec=D.querySelector('.mz-htl');if(!sec||sec.classList.contains('is-static'))return;var st=sec.querySelector('.mz-htl__stick'),tr=sec.querySelector('.mz-htl__track'),vp=sec.querySelector('.mz-htl__vp'),bar=sec.querySelector('.mz-htl__foot span');if(!st||!bar)return;
if(!kn)kn=knots();if(!kn)return;var top=parseFloat(getComputedStyle(st).top)||0,mx=Math.max(1,tr.scrollWidth-vp.clientWidth),p=Math.min(1,Math.max(0,(top-sec.getBoundingClientRect().top)/mx)),n=kn.length-1,q=1;
for(var i=0;i!==n;i++){if(p>kn[i+1]){if(i!==n-1)continue}var d=kn[i+1]-kn[i];q=(i+(d>0?Math.min(1,Math.max(0,(p-kn[i])/d)):1))/n;break}
bar.style.setProperty('--mzp',q.toFixed(4))}
function req(){if(!raf)raf=requestAnimationFrame(upd)}
function re(){kn=null;req()}
window.addEventListener('scroll',req,{passive:true});window.addEventListener('resize',re);window.addEventListener('load',re);[600,2800].forEach(function(t){setTimeout(re,t)});req()})();

(function(){var tr=document.querySelector('.mz-htl__track');if(!tr)return;var d=Object.getOwnPropertyDescriptor(Element.prototype,'scrollWidth');if(!d)return;
Object.defineProperty(tr,'scrollWidth',{configurable:true,get:function(){var real=d.get.call(tr),c=tr.lastElementChild;if(!c)return real;var end=c.offsetLeft+c.offsetWidth+(parseFloat(getComputedStyle(tr).paddingRight)||0);return end>0?Math.min(real,end):real}})})();
