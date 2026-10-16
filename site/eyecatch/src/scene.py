import numpy as np
from PIL import Image, ImageFilter, ImageDraw
W,H=2400,1260
rng=np.random.default_rng(11)
def blur(a,r):
    im=Image.fromarray(np.clip(a*255,0,255).astype(np.uint8));return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32)/255
def fnoise(scales=(220,90,40,16),w=(1,.6,.35,.2)):
    out=np.zeros((H,W),np.float32)
    for s,k in zip(scales,w):
        out+=k*blur(rng.random((H,W)).astype(np.float32),s/4)
    out-=out.min();out/=out.max();return out
def lerp(c1,c2,t):return c1[None,None,:]*(1-t[...,None])+c2[None,None,:]*t[...,None]
def stars(img,n,ymax,bright=1.0,seed=3):
    r=np.random.default_rng(seed);lay=np.zeros((H,W),np.float32)
    xs=r.integers(0,W,n);ys=r.integers(0,int(ymax),n);v=r.power(9,n)**2*bright
    lay[ys,xs]=np.maximum(lay[ys,xs],v)
    glow=blur(lay*1.0,1.2)*3.0+blur(lay,4)*1.2
    fade=np.clip((ymax-np.arange(H))/ (ymax*0.35),0,1)[:,None]
    return img+ (lay+glow)[...,None]*fade[...,None]*np.array([1,1,1.05])
def trail(img,pts,core=(1,.95,.85),halo=(1,.45,.12),width=5,glow=40,strength=1.0,ramp=0.0):
    lay=Image.new('L',(W,H),0);d=ImageDraw.Draw(lay);n=len(pts)
    for i in range(n-1):
        t=i/(n-1);v=int(255*((1-ramp)+ramp*min(1,t*2.2)))
        d.line([pts[i],pts[i+1]],fill=v,width=width)
    a=np.asarray(lay).astype(np.float32)/255
    g1=blur(a,glow/6);g2=blur(a,glow)
    return img+strength*(a[...,None]*np.array(core)+g1[...,None]*np.array(halo)*1.6+g2[...,None]*np.array(halo)*1.4)
def bez(p0,p1,p2,p3,n=400):
    t=np.linspace(0,1,n)[:,None];P=[np.array(p) for p in (p0,p1,p2,p3)]
    pts=(1-t)**3*P[0]+3*(1-t)**2*t*P[1]+3*(1-t)*t**2*P[2]+t**3*P[3];return [tuple(map(float,p)) for p in pts]
def finish(img,name,grain=.035,vig=.55):
    y,x=np.mgrid[0:H,0:W];d=((x-W/2)/(W/2))**2+((y-H/2)/(H/2))**2
    img=img*(1-vig*np.clip(d,0,1.4)[...,None]*0.5)
    img=img+rng.normal(0,grain,(H,W,1))
    img=np.clip(img,0,1)**(1/1.05)
    Image.fromarray((img*255).astype(np.uint8)).resize((1200,630),Image.LANCZOS).save(name,quality=94)

# ---- C 海辺の長時間露光（夜）
yy=np.linspace(0,1,H)[:,None]*np.ones((1,W));hz=int(H*0.74)
sky=lerp(np.array([.012,.018,.04]),np.array([.08,.13,.24]),np.clip(yy/0.74,0,1)**1.6)
warm=np.exp(-(((np.arange(W)[None,:]-W*0.15)/(W*0.35))**2))*np.exp(-((yy*H-hz)/(H*0.09))**2)
sky=sky+warm[...,None]*np.array([.22,.10,.04])
mw=fnoise();band=np.exp(-((np.arange(W)[None,:]*0.55-np.arange(H)[:,None]+ -380)/260.0)**2)
sky=sky+(mw**2.2*band)[...,None]*np.array([.20,.19,.26])
sky=stars(sky,3200,hz,1.1)
pts=bez((W*0.60,hz),(W*0.62,hz-380),(W*0.70,hz-760),(W*0.93,hz-930))
sky=trail(sky,pts,width=6,glow=46,ramp=0.55)
# 海
sea=np.arange(H)>=hz
ref=np.exp(-((np.arange(W)[None,:]-W*0.60)/(W*0.012))**2)*np.ones((H,1))
wav=fnoise((30,12,6),(1,.7,.5))
seac=lerp(np.array([.05,.08,.14]),np.array([.01,.015,.03]),np.clip((yy-0.74)/0.26,0,1))+ (ref*(0.25+0.6*wav))[...,None]*np.array([1,.5,.18])*np.exp(-((yy*H-hz)/(H*0.18)))[...,None]
seac=seac+((wav-0.5)*0.03)[...,None]
img=np.where(sea[:,None,None],seac,sky)
# 岬のシルエット
hill=Image.new('L',(W,H),0);d=ImageDraw.Draw(hill);xs=np.arange(0,int(W*0.42),8)
prof=hz-80-120*np.exp(-((xs-W*0.12)/(W*0.11))**2)-40*np.sin(xs/57)*np.exp(-xs/700)+ (xs/(W*0.42))**2*90
d.polygon([(0,hz+2)]+[(float(x),float(p)) for x,p in zip(xs,prof)]+[(W*0.42,hz+2)],fill=255)
hm=np.asarray(hill).astype(np.float32)[...,None]/255
img=img*(1-hm)+hm*np.array([.006,.008,.014])
finish(img,'bgC.jpg')

# ---- D 夜明け前の丘と人（見上げる）
sky=np.zeros((H,W,3),np.float32);t=np.clip(yy/0.8,0,1)
c0=np.array([.01,.02,.06]);c1=np.array([.10,.10,.30]);c2=np.array([.55,.30,.40]);c3=np.array([.98,.55,.28])
sky=np.where((t<.55)[...,None],lerp(c0,c1,t/.55),np.where((t<.85)[...,None],lerp(c1,c2,(t-.55)/.30),lerp(c2,c3,np.clip((t-.85)/.15,0,1))))
sky=stars(sky,2600,int(H*0.6),0.8,seed=5)
pts=bez((W*0.30,H*0.80),(W*0.36,H*0.55),(W*0.50,H*0.30),(W*0.78,H*0.17))
sky=trail(sky,pts,core=(1,.97,.9),halo=(1,.55,.25),width=4,glow=34,strength=.95,ramp=0.6)
img=sky
hill=Image.new('L',(W,H),0);d=ImageDraw.Draw(hill);xs=np.arange(0,W+8,8)
prof=H*0.80+60*np.sin(xs/430)+30*np.sin(xs/190+1)-140*np.exp(-((xs-W*0.70)/(W*0.22))**2)
d.polygon([(0,H)]+[(float(x),float(p)) for x,p in zip(xs,prof)]+[(W,H)],fill=255)
# 人（見上げる）と三脚
px,py=W*0.70,float(H*0.80-140-14)
tx=px;py=py+60;d.line([(tx,py-60),(tx-30,py+40)],fill=255,width=5);d.line([(tx,py-60),(tx+28,py+40)],fill=255,width=5);d.line([(tx,py-60),(tx,py+40)],fill=255,width=5);d.rectangle((tx-26,py-90,tx+30,py-58),fill=255);d.polygon([(tx+30,py-84),(tx+52,py-96),(tx+52,py-56),(tx+30,py-64)],fill=255)
hm=np.asarray(hill.filter(ImageFilter.GaussianBlur(1))).astype(np.float32)[...,None]/255
img=img*(1-hm)+hm*np.array([.02,.015,.03])
finish(img,'bgD.jpg',grain=.03,vig=.45)

# ---- E 星の軌跡（日周運動）＋ロケットの光跡：縦長の雑誌表紙風に使う背景
sky=lerp(np.array([.01,.012,.03]),np.array([.05,.07,.13]),np.clip(yy,0,1)**1.4)
lay=Image.new('L',(W,H),0);d=ImageDraw.Draw(lay);cx,cy=W*0.80,-H*0.15;r2=np.random.default_rng(9)
for i in range(620):
    rad=r2.uniform(80,W*1.1);a0=r2.uniform(0,2*np.pi);span=0.22;b=int(r2.power(5)*255)
    d.arc((cx-rad,cy-rad,cx+rad,cy+rad),np.degrees(a0),np.degrees(a0+span),fill=b,width=2)
a=np.asarray(lay).astype(np.float32)/255;sky=sky+(a+blur(a,2)*1.5)[...,None]*np.array([.85,.9,1.0])*0.9
pts=bez((W*0.22,H*0.86),(W*0.25,H*0.55),(W*0.33,H*0.28),(W*0.50,H*0.10))
sky=trail(sky,pts,width=7,glow=52,strength=1.1,ramp=0.4)
hill=Image.new('L',(W,H),0);d=ImageDraw.Draw(hill);xs=np.arange(0,W+8,8)
prof=H*0.86+20*np.sin(xs/300)+12*np.sin(xs/77)
d.polygon([(0,H)]+[(float(x),float(p)) for x,p in zip(xs,prof)]+[(W,H)],fill=255)
hm=np.asarray(hill).astype(np.float32)[...,None]/255
img=sky*(1-hm)+hm*np.array([.004,.005,.01])
finish(img,'bgE.jpg',grain=.04,vig=.6)
