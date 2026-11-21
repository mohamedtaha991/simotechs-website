# تحليل إمكانية الوصول إلى المستشفيات في الرياض من بيانات OpenStreetMap:
# المسافة المباشرة إلى أقرب مستشفى + مناطق خدمة كل مستشفى (أقرب مستشفى) + الطرق الرئيسية.
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = sys.argv[1]; OUT = sys.argv[2]
LAT0, LAT1 = 24.53, 24.94          # جنوب، شمال
LON0, LON1 = 46.53, 46.89          # غرب، شرق
W, H = 1200, 1500
KX = 111.32 * math.cos(math.radians((LAT0 + LAT1) / 2))   # كم لكل درجة طول
KY = 110.57                                               # كم لكل درجة عرض

def px(lon, lat):
    return ((lon - LON0) / (LON1 - LON0) * W, (LAT1 - lat) / (LAT1 - LAT0) * H)

hosp = []
for e in json.load(open(f'{D}/hosp.json', encoding='utf-8'))['elements']:
    lat = e.get('lat') or e.get('center', {}).get('lat'); lon = e.get('lon') or e.get('center', {}).get('lon')
    if lat and LAT0 <= lat <= LAT1 and LON0 <= lon <= LON1:
        hosp.append((lon, lat))
hosp = np.array(hosp); print('hospitals in frame', len(hosp))

# شبكة الحساب بنصف الدقة
S = 2; gw, gh = W // S, H // S
gx = LON0 + (np.arange(gw) + .5) / gw * (LON1 - LON0)
gy = LAT1 - (np.arange(gh) + .5) / gh * (LAT1 - LAT0)
X, Y = np.meshgrid(gx * KX, gy * KY)
hx, hy = hosp[:, 0] * KX, hosp[:, 1] * KY
best = np.full(X.shape, np.inf); lab = np.zeros(X.shape, int)
for i in range(len(hosp)):
    d = np.hypot(X - hx[i], Y - hy[i]); m = d < best
    best[m] = d[m]; lab[m] = i
dist = best  # كم

# قناع العمران: المناطق القريبة من الطرق فقط
roads = json.load(open(f'{D}/roads.json', encoding='utf-8'))['elements']
rm = Image.new('L', (gw, gh), 0); rd = ImageDraw.Draw(rm)
for e in roads:
    pts = [((p['lon'] - LON0) / (LON1 - LON0) * gw, (LAT1 - p['lat']) / (LAT1 - LAT0) * gh) for p in e['geometry']]
    if len(pts) > 1: rd.line(pts, fill=255, width=2)
urban = np.asarray(rm.filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.GaussianBlur(14)), float) / 255
urban = np.clip(urban * 1.6, 0, 1)

# لون المسافة
stops = [(0, (0, 94, 149)), (1.5, (0, 121, 193)), (3, (86, 197, 255)), (4.5, (234, 244, 251)), (6, (245, 176, 65)), (9, (211, 84, 0))]
def ramp(v):
    out = np.zeros(v.shape + (3,))
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        t = np.clip((v - a) / (b - a), 0, 1)[..., None]
        m = ((v >= a) & (v < b))[..., None] if b != stops[-1][0] else (v >= a)[..., None]
        out = np.where(m, np.array(ca) * (1 - t) + np.array(cb) * t, out)
    return out
col = ramp(dist)
bg = np.array([243, 246, 249], float)
a = (urban * .92)[..., None]
img = (col * a + bg * (1 - a)).astype(np.uint8)

# حدود مناطق الخدمة
edge = np.zeros(lab.shape, bool)
edge[:, 1:] |= lab[:, 1:] != lab[:, :-1]; edge[1:, :] |= lab[1:, :] != lab[:-1, :]
edge &= urban > .35
img[edge] = (img[edge] * .45 + np.array([11, 37, 69]) * .55).astype(np.uint8)

base = Image.fromarray(img).resize((W, H), Image.BICUBIC).convert('RGBA')

# الطرق
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
style = {'secondary': (1, 110), 'primary': (2, 170), 'trunk': (3, 220), 'motorway': (4, 240)}
for cls in ['secondary', 'primary', 'trunk', 'motorway']:
    w, al = style[cls]
    for e in roads:
        if e['tags'].get('highway') != cls: continue
        pts = [px(p['lon'], p['lat']) for p in e['geometry']]
        if len(pts) > 1: od.line(pts, fill=(255, 255, 255, al), width=w, joint='curve')
base = Image.alpha_composite(base, ov)

# المستشفيات
od = ImageDraw.Draw(base)
for lon, lat in hosp:
    x, y = px(lon, lat)
    od.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(255, 255, 255, 255))
    od.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(11, 37, 69, 255))

# بلا مفتاح ألوان؛ الشرح في تعليق الصورة على الموقع. نُبقي نسبة البيانات لأنها شرط رخصة OpenStreetMap
od = ImageDraw.Draw(base)
od.text((W - 360, H - 46), '© OpenStreetMap contributors', font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 20), fill=(90, 100, 110))

base.convert('RGB').save(OUT, quality=88, optimize=True, progressive=True)
print('saved', OUT, 'max dist km', round(float(dist[urban > .5].max()), 1))
