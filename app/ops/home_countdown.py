#!/usr/bin/env python3
"""トップページ「NEXT LAUNCH」のカウントダウン用スクリプトを作る。

使い方:  python3 home_countdown.py launches.json > countdown-script.html
launches.json は、打ち上げの一覧（アプリの events から launch のものを書き出したもの）：
  [{"title":"H3ロケット11号機","sub":"…／種子島宇宙センター","date":"2027-02-01","time":"10:00","dateText":"","status":"確定",
    "guide":"/rockets/h3/","guideLabel":"H3ロケットを図解で見る","official":"https://…（公式ページ。無ければ空）","publicNote":"予備期間 …（読者に見せる一文。内部のメモは入れない）","rank":1}, …]
- date と time があるものはカウントダウンになる。無いもの（dateText だけ）は「日程の発表待ち」として出る。
- status が 確定・予定・延期 のものだけが入る（終了・中止・推測は入らない）。延期で日付が未定なら date を空にする。
- 日付の無いものは rank の小さい順（近そうな順）に1件だけ「日程の発表待ち」として出る。
出力を、トップページの <script> ... </script>（id="mgCount" を使っているもの）と丸ごと入れ替える。
ブラウザが開いた時刻を見て、予定時刻から6時間たったら自動で次の打ち上げに切り替わる。一覧を書き換えるのは、日程が変わったときだけ。
"""
import json, sys

END_HOURS = 6
TPL = r"""<script>
(function(){
  var L=__DATA__;
  var END=__END__*36e5,W=['SUN','MON','TUE','WED','THU','FRI','SAT'];
  var aside=document.querySelector('.mg-next'),el=document.getElementById('mgCount'); if(!aside) return; if(!el) return;
  var q=function(c){return aside.querySelector(c)};
  var nm=q('.mg-next__name'),sb=q('.mg-next__sub'),dt=q('.mg-next__date'),nt=document.getElementById('mgCountNote')||q('.mg-next__note'),lk=q('.mg-next__link'),lb=q('.mg-next__label');
  var u={d:el.querySelector('[data-u=d]'),h:el.querySelector('[data-u=h]'),m:el.querySelector('[data-u=m]'),s:el.querySelector('[data-u=s]')};
  function p(n){return (n<10?'0':'')+n}
  function official(o){return o?' 最新の日時は <a href="'+o+'" target="_blank" rel="noopener">公式</a> で確認を。':''}
  function pick(){
    var now=Date.now(),dated=L.filter(function(e){return e.t}).map(function(e){e.ms=new Date(e.t).getTime();return e}).sort(function(a,b){return a.ms-b.ms});
    for(var i=0;i<dated.length;i++) if(now<dated[i].ms+END) return dated[i];
    return L.filter(function(e){return !e.t})[0]||null;
  }
  var cur=null;
  function show(e){
    cur=e;
    if(!e){nm.textContent='次の打ち上げは未発表';sb.textContent='';dt.textContent='日程の発表待ち';nt.innerHTML='日程が出たらここに表示します。';
      u.d.textContent=u.h.textContent=u.m.textContent=u.s.textContent='—';return}
    nm.textContent=e.n;sb.textContent=e.s||'';
    if(e.t){var j=new Date(e.ms+9*36e5);dt.textContent=j.getUTCFullYear()+'.'+p(j.getUTCMonth()+1)+'.'+p(j.getUTCDate())+' '+W[j.getUTCDay()]+' — '+p(j.getUTCHours())+':'+p(j.getUTCMinutes())+' JST'}
    else dt.textContent=(e.d||'日程の発表待ち');
    nt.innerHTML=(e.note?e.note+'。':'')+(e.t?'天候などで延期されることがあります。':e.note?'':'日程が出たらここに表示します。')+official(e.o);
    if(lk)if(e.u){lk.setAttribute('href',e.u);lk.innerHTML=(e.ul||'くわしく見る')+'<span>→</span>'}
    if(!e.t) u.d.textContent=u.h.textContent=u.m.textContent=u.s.textContent='—';
  }
  function tick(){
    var now=Date.now();
    var over=cur?(cur.t?now>=cur.ms+END:false):(L.length>0);
    if(over) show(pick());
    if(cur)if(cur.t){
      var x=cur.ms-now;
      if(x<=0){u.d.textContent=u.h.textContent=u.m.textContent=u.s.textContent='00';nt.innerHTML='予定時刻を過ぎました。結果・延期は'+(cur.o?' <a href="'+cur.o+'" target="_blank" rel="noopener">公式</a> で':'公式で')+'確認を。（約'+END/36e5+'時間後に次の打ち上げへ切り替わります）'}
      else{u.d.textContent=p(Math.floor(x/864e5));u.h.textContent=p(Math.floor(x/36e5)%24);u.m.textContent=p(Math.floor(x/6e4)%60);u.s.textContent=p(Math.floor(x/1e3)%60)}
    }
    setTimeout(tick,1000-(Date.now()%1000));
  }
  show(pick());tick();
})();
</script>"""

def build(items):
    out = []
    for e in items:
        if e.get("status") not in ("確定", "予定", "延期"): continue  # 終了・中止・推測（確かでないもの）は入れない
        t = ""
        if e.get("date") and e.get("time"):
            hh, mm = e["time"].split(":"); t = f'{e["date"]}T{int(hh):02d}:{int(mm):02d}:00+09:00'
        d = {"n": e["title"], "s": e.get("sub") or e.get("place", ""), "t": t or None, "o": e.get("official") or "", "u": e.get("guide") or "", "ul": e.get("guideLabel") or "",
             "note": (e.get("publicNote") or "").rstrip("。"), "rank": e.get("rank", 99)}
        if not t: d["d"] = e.get("dateText") or "日程の発表待ち"
        out.append(d)
    out.sort(key=lambda d: (d["t"] is None, d["t"] or "", d["rank"]))
    for d in out: d.pop("rank")
    return TPL.replace("__DATA__", json.dumps(out, ensure_ascii=False, indent=1)).replace("__END__", str(END_HOURS))

if __name__ == "__main__":
    print(build(json.load(open(sys.argv[1], encoding="utf-8"))))
