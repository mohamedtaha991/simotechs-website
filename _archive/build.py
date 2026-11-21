import re,json,xml.etree.ElementTree as ET
root=ET.fromstring(open('/home/claude/doc.xml').read())
def ptext(p):
    label=None;parts=[]
    for i,t in enumerate([c for c in p if c.tag=='text']):
        ch=list(t)
        if ch and ch[0].tag=='italic': continue
        s=''.join(t.itertext())
        if ch and ch[0].tag=='bold' and label is None and not parts: label=s.strip().rstrip(':').strip(); continue
        parts.append(s)
    return label,''.join(parts).strip()
blocks=[]
for el in root:
    if el.tag=='paragraph':
        l,t=ptext(el); blocks.append(dict(t='p',h=int(el.get('heading') or 0),label=l,text=t))
    elif el.tag=='list':
        items=[]
        for li in el:
            l,t=ptext(li[0]); items.append((l,t))
        blocks.append(dict(t='list',items=items))
    elif el.tag=='table':
        blocks.append(dict(t='table',rows=[[ptext(c[0])[1] or ptext(c[0])[0] for c in r] for r in el][1:]))
def sections(level):
    out=[];cur=None
    for b in blocks:
        if b['t']=='p' and b['h']:
            cur=None
            if b['h']==level: cur=dict(title=b['label'] or b['text'],f={},lists={},tables=[]);out.append(cur);last=None
            continue
        if cur is None: continue
        if b['t']=='p':
            if b['label']: cur['f'][b['label']]=b['text']; last=b['label']
        elif b['t']=='list': cur['lists'][last]=b['items']
        else: cur['tables'].append(b['rows'])
    return out
dot=lambda s:[x.strip() for x in s.split('·') if x.strip()]
tables=[b['rows'] for b in blocks if b['t']=='table']
T_OFF,T_TR,T_VAL,T_WH,T_IND,_=tables
IDS="1.1 web-gis-applications|1.4 interactive-maps-dashboards|1.8 gis-enterprise-integration|2.1.1 geospatial-data-strategy|2.1.2 data-policies-standards|2.1.3 data-governance-frameworks|2.2.1 geospatial-database-design|2.2.2 geospatial-data-warehouse|2.2.3 gis-solution-architecture|2.3.1 data-conversion-migration|2.3.2 geospatial-etl-automation|2.3.3 geospatial-apis-data-services|2.4.1 data-quality-assessment|2.4.2 automated-data-validation|2.4.3 data-update-versioning-qa|2.5.1 spatial-urban-network-analysis|2.5.2 environmental-demographic-analysis|2.5.3 suitability-multicriteria-modeling|2.5.5 geospatial-indicators-products|3.2 land-cover-land-use-classification|3.3 change-monitoring|5.1 geospatial-enterprise-gis-consulting|5.2 independent-data-architecture-advisory|5.3 digital-transformation-advisory|5.4 business-analysis-requirements|5.6 technical-feasibility-studies|5.7 technical-specifications-rfp"
ID={b:a for a,b in (x.split(' ') for x in IDS.split('|'))}
TN={'1':'gis-solutions','2':'geospatial-data','3':'remote-sensing','4':'geoai','5':'consulting'}
DOM={"2.1":"الاستراتيجية والحوكمة","2.2":"التصميم والبنية المؤسسية","2.3":"التكامل والترحيل","2.4":"ضبط الجودة والتحديث","2.5":"التحليلات الجيومكانية"}
EXTRA=[("1.2","تطبيقات GIS للأجهزة الذكية والعمل الميداني","تطبيقات ميدانية لجمع البيانات المكانية وتحديثها دون اتصال ومزامنتها مع قاعدة بيانات الجهة."),
("1.3","المنصات والبوابات الجيومكانية المؤسسية","بوابات ومنصات جيومكانية بصلاحيات وحوكمة واضحة توحّد الوصول إلى بيانات الجهة وخرائطها وخدماتها."),
("1.5","حلول إدارة الأصول والمرافق المكانية","حلول تربط موقع الأصل بحالته وصيانته وتكلفته لتخطيط أفضل وصيانة وقائية."),
("1.6","حلول التخطيط الحضري وإدارة الأراضي","حلول رقمية مكانية لدراسة الطلبات وتتبع الاستعمالات والملكيات وقراءة النمو العمراني."),
("1.7","حلول التتبع والمراقبة المكانية","تتبع لحظي للمركبات والفرق بتنبيهات جغرافية وتقارير أداء تدعم القرار التشغيلي."),
("1.9","التوأم الرقمي والنماذج ثلاثية الأبعاد","توأم رقمي ونماذج 3D تربط الواقع المكاني بالبيانات التشغيلية وتتيح اختبار السيناريوهات قبل التنفيذ."),
("2.5.4","التحليل الإحصائي الجغرافي والمكاني الزماني","تحليلات إحصائية مكانية وزمانية تكشف البؤر والاتجاهات وتقيس الأثر."),
("3.1","معالجة صور الأقمار الصناعية وتجهيز المنتجات","نحوّل الصور الخام إلى منتجات متسقة وجاهزة للتحليل والرصد بجودة موثقة."),
("3.4","المؤشرات الطيفية وتحليل المخاطر الطبيعية والبيئية","مؤشرات بيئية من الصور الفضائية وتقييم للمخاطر الطبيعية يدعم الاستدامة والاستجابة."),
("3.6","إنتاج الخرائط التحليلية ودمجها بقواعد البيانات","ننتج منتجات خرائطية من الصور الفضائية وندخلها في قواعد بياناتك لتستخدمها فرقك يوميًا."),
("4.1","تطوير نماذج GeoAI","نماذج تعلم آلي وعميق مخصصة للبيانات الجيومكانية، مختبرة وموثقة وقابلة للنشر."),
("4.2","اكتشاف وتصنيف المعالم من الصور","نستخرج المباني والطرق والمنشآت من الصور الجوية والفضائية بنماذج رؤية حاسوبية ودقة موثقة."),
("4.3","الكشف الآلي عن التغيرات المكانية","نماذج تكتشف التغيرات تلقائيًا وتوجّه الرقابة إلى المواقع الأعلى أولوية."),
("4.4","التحليلات التنبؤية المكانية","نماذج تنبؤ تقدّر الطلب والمخاطر والنمو بدقة قابلة للقياس لتخطيط استباقي للموارد."),
("4.5","المساعدات والوكلاء الذكيون الجيومكانيون","مساعدون يجيبون بالعربية عن أسئلة مكانية وينفذون التحليل على بيانات جهتك بضوابط وصول واضحة."),
("4.6","أتمتة معالجة البيانات المكانية بالذكاء الاصطناعي","نؤتمت مطابقة العناوين وتصنيف الطبقات وكشف الشذوذ ليتفرغ محللوك للعمل ذي القيمة."),
("4.8","GeoAI للتخطيط الحضري والأراضي والأصول","حلول لرصد المخالفات وتقدير الصيانة وتحليل الطلب في التخطيط الحضري والأصول."),
("4.9","حلول دعم القرار المكاني الذكي","أنظمة تقارن البدائل والمخاطر وتُظهر مبررات التوصية بشفافية لصاحب القرار."),
("5.5","إعادة هندسة الإجراءات","نعيد تصميم الإجراءات لإزالة الخطوات الزائدة ونقيس الأثر على الزمن والجهد والجودة."),
("5.8","إدارة المشاريع والإشراف الفني","ندير مشاريعك الجيومكانية ونشرف فنيًا على الموردين لتسليم بالجودة والوقت والميزانية.")]
services=[];rows=[]
for s in sections(4):
    name,slug=[x.strip() for x in s['title'].rsplit('·',1)]
    f=s['f'];seo,desc=[x.strip() for x in f['SEO'].split(' — ',1)]
    i=ID[slug]
    services.append(dict(slug=slug,name=name,seo=seo,intro=f['المقدمة'],offer=[t for _,t in s['lists']['ما نقدمه']],benefits=dot(f['ما تحصل عليه']),outputs=[x.strip().rstrip('.') for x in f['المخرجات'].split('،')],examples=dot(f['أمثلة']),cta=f['الدعوة'],track=TN[i[0]]))
    rows.append((i,name,desc,slug))
assert len(services)==27,len(services)
rows+= [(a,b,c,None) for a,b,c in EXTRA]
rows.sort(key=lambda r:[int(x) for x in r[0].split('.')])
tracks=[];offers=[]
for s in sections(3):
    m=re.match(r'المسار: (.+) \(/ar/services/([\w-]+)\)',s['title'])
    f=s['f']
    if m:
        slug=m.group(2);n=[k for k,v in TN.items() if v==slug][0]
        sv=[dict(name=b,desc=c,slug=d,group=DOM.get(a[:3]) if n=='2' else None) for a,b,c,d in rows if a[0]==n]
        tracks.append(dict(slug=slug,name=m.group(1),seo=f['عنوان SEO'],title=f['العنوان'],intro=f['المقدمة'],benefits=dot(f['ما تحصل عليه']),outputs=[x.strip().rstrip('.') for x in f['المخرجات'].split('،')],examples=dot(f['أمثلة على ما نعمله']),cta=f['الدعوة'],gate='شرط النشر' in f,services=sv))
    m=re.match(r'العرض \d: (.+) \(/ar/offers/([\w-]+)\)',s['title'])
    if m:
        k='مناسب لك إذا' if 'مناسب لك إذا' in s['lists'] else 'أمثلة على النماذج الأولية'
        offers.append(dict(slug=m.group(2),name=m.group(1),seo=f['عنوان SEO'],title=f['العنوان'],intro=f['المقدمة'],fitTitle='مناسب لك إذا' if k.startswith('مناسب') else k,fit=[t for _,t in s['lists'][k]],steps=[t for _,t in s['lists']['كيف يسير']],receive=dot(f['ما تستلمه']),cta=f['الدعوة']))
assert len(tracks)==5 and len(offers)==3
for t,r in zip(tracks,T_TR): t['card']=r[1]
for o,r in zip(offers,T_OFF): o['short']=r[0];o['card']=r[1]
where=[dict(q=r[0],a=r[1],slug=t['slug']) for r,t in zip(T_WH,tracks)]
priv=[]
for i,b in enumerate(blocks):
    if b['t']=='p' and b['h']==2 and (b['text'] or '').startswith('سياسة الخصوصية'):
        priv=[list(x) for x in [bb for bb in blocks[i:] if bb['t']=='list'][0]['items']]
titles=dict(home="الذكاء المكاني للحلول الرقمية | بيانات جيومكانية وتحليلات وGIS في السعودية",about="من نحن | الذكاء المكاني للحلول الرقمية",services="خدماتنا | بيانات جيومكانية وGIS واستشعار عن بعد وGeoAI واستشارات",industries="القطاعات التي نخدمها | الذكاء المكاني",contact="تواصل معنا | الذكاء المكاني",privacy="سياسة الخصوصية | الذكاء المكاني")
D=dict(tracks=tracks,offers=offers,services=services,industries=T_IND,values=T_VAL,where=where,privacy=priv,titles=titles)
html=open('template.html').read().replace('/*DATA*/',json.dumps(D,ensure_ascii=False).replace('</','<\\/'))
open('index.html','w').write(html)
print(len(html),[ (t['slug'],len(t['services'])) for t in tracks],[o['slug'] for o in offers],len(priv),where[0],services[0]['benefits'],tracks[1]['benefits'])
