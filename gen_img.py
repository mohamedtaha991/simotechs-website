import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import gaussian_filter
rng=np.random.default_rng(7)
W,H=1600,900
# ---------- landcover: desert with center-pivot farms, half classified ----------
n=gaussian_filter(rng.standard_normal((H,W)),40); n=(n-n.min())/(n.max()-n.min())
fine=gaussian_filter(rng.standard_normal((H,W)),2)
streak=gaussian_filter(rng.standard_normal((H,W)),[1,14])
base=np.stack([194+40*n+6*fine+8*streak,152+34*n+5*fine+6*streak,104+26*n+4*fine+5*streak],-1)
img=Image.fromarray(np.clip(base,0,255).astype('uint8'))
d=ImageDraw.Draw(img)
cls=Image.new('RGB',(W,H)); dc=ImageDraw.Draw(cls)
# class background from noise
c=np.zeros((H,W,3))
c[...]=[214,182,128]; c[n>0.55]=[184,129,74]; c[n<0.3]=[232,214,170]
cls=Image.fromarray(c.astype('uint8')); dc=ImageDraw.Draw(cls)
pivots=[]
for i in range(26):
    for _ in range(50):
        x,y,r=rng.integers(80,W-80),rng.integers(80,H-80),rng.integers(38,72)
        if all((x-a)**2+(y-b)**2>(r+q+10)**2 for a,b,q in pivots): pivots.append((x,y,r));break
for x,y,r in pivots:
    g=rng.integers(0,3)
    col=[(86,118,62),(110,140,70),(150,150,92)][g]
    d.ellipse([x-r,y-r,x+r,y+r],fill=col)
    if rng.random()<.6:
        a=rng.integers(0,360); d.pieslice([x-r,y-r,x+r,y+r],a,a+rng.integers(60,140),fill=(176,150,100))
    dc.ellipse([x-r,y-r,x+r,y+r],fill=[(29,107,115),(60,150,140),(120,170,150)][g])
# roads
for y0 in (300,640):
    d.line([(0,y0),(W,y0+40)],fill=(120,110,100),width=6); dc.line([(0,y0),(W,y0+40)],fill=(60,60,60),width=6)
d.line([(1150,0),(1110,H)],fill=(120,110,100),width=5); dc.line([(1150,0),(1110,H)],fill=(60,60,60),width=5)
# urban blocks near a corner
for i in range(70):
    x,y=rng.integers(1180,1560),rng.integers(380,620); w,h=rng.integers(10,26),rng.integers(10,26)
    d.rectangle([x,y,x+w,y+h],fill=tuple(int(v) for v in rng.integers(150,215,3))); dc.rectangle([x,y,x+w,y+h],fill=(110,110,120))
img=img.filter(ImageFilter.GaussianBlur(.6))
split=980
out=img.copy(); out.paste(Image.blend(img.crop((split,0,W,H)),cls.crop((split,0,W,H)),.82),(split,0))
o=ImageDraw.Draw(out)
for k,wid,al in [(18,1,40),(8,1,90),(3,1,255)]:
    lay=Image.new('RGBA',(W,H)); ImageDraw.Draw(lay).rectangle([split-k//2,0,split+k//2,H],fill=(111,224,224,al)); out=Image.alpha_composite(out.convert('RGBA'),lay)
out=out.convert('RGB')
# vignette
yy,xx=np.mgrid[0:H,0:W]; v=1-0.35*(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)
out=Image.fromarray(np.clip(np.asarray(out)*v[...,None],0,255).astype('uint8'))
out.save('src/assets/img/landcover.jpg',quality=82)

# ---------- blueprint: architecture diagram on dark slate ----------
im=Image.new('RGB',(W,H),(13,26,29)); d=ImageDraw.Draw(im)
for x in range(0,W,24): d.line([(x,0),(x,H)],fill=(19,38,42))
for y in range(0,H,24): d.line([(0,y),(W,y)],fill=(19,38,42))
for x in range(0,W,120): d.line([(x,0),(x,H)],fill=(26,52,57))
for y in range(0,H,120): d.line([(0,y),(W,y)],fill=(26,52,57))
try: f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',20)
except: f=ImageFont.load_default()
boxes={'GDB':(240,360),'ETL':(600,240),'API':(600,480),'PORTAL':(960,360),'BI':(1320,240),'FIELD':(1320,480),'QA':(240,600)}
def box(k):
    x,y=boxes[k]; return [x-90,y-46,x+90,y+46]
links=[('GDB','ETL'),('GDB','API'),('ETL','PORTAL'),('API','PORTAL'),('PORTAL','BI'),('PORTAL','FIELD'),('QA','GDB')]
glow=Image.new('RGB',(W,H)); g=ImageDraw.Draw(glow)
for a,b in links:
    (x1,y1),(x2,y2)=boxes[a],boxes[b]; mx=(x1+x2)//2
    pts=[(x1,y1),(mx,y1),(mx,y2),(x2,y2)] if y1!=y2 else [(x1,y1),(x2,y2)]
    if a=='QA': pts=[(x1,y1),(x2,y2)]
    col=(111,224,224) if a in('ETL','API') or b=='PORTAL' else (210,154,94)
    for w,c in [(10,tuple(v//3 for v in col)),(3,col)]:
        (g if w==10 else d).line(pts,fill=c,width=w,joint='curve')
im=Image.fromarray(np.clip(np.asarray(im).astype(int)+np.asarray(glow.filter(ImageFilter.GaussianBlur(8))).astype(int),0,255).astype('uint8')); d=ImageDraw.Draw(im)
for a,b in links:
    (x1,y1),(x2,y2)=boxes[a],boxes[b]; mx=(x1+x2)//2
    pts=[(x1,y1),(mx,y1),(mx,y2),(x2,y2)] if y1!=y2 and a!='QA' else [(x1,y1),(x2,y2)]
    col=(111,224,224) if a in('ETL','API') or b=='PORTAL' else (210,154,94)
    d.line(pts,fill=col,width=3,joint='curve')
for k in boxes:
    hot=k=='PORTAL'
    d.rounded_rectangle(box(k),12,fill=(18,44,48) if not hot else (24,70,76),outline=(111,224,224) if hot else (210,154,94),width=3)
    x,y=boxes[k]; tw=d.textlength(k,font=f); d.text((x-tw/2,y-12),k,fill=(232,240,238),font=f)
yy,xx=np.mgrid[0:H,0:W]; v=1-0.45*(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)
im=Image.fromarray(np.clip(np.asarray(im)*v[...,None],0,255).astype('uint8'))
im.save('src/assets/img/blueprint.jpg',quality=84)
