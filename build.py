#!/usr/bin/env python3
"""يبني موقع الذكاء المكاني: يقرأ src/ ويكتب الصفحات الجاهزة في dist/.

التشغيل:   python build.py
المتطلبات: Python 3.9+ ومكتبة Jinja2  (pip install jinja2)
"""
import hashlib
import json
import shutil
import re
import sys
from markupsafe import Markup, escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
CONTENT = SRC / "content"
DIST = ROOT / "dist"
# اللغات: (الرمز، الاتجاه، مجلد النصوص). الأولى هي الافتراضية التي يحوّل إليها جذر الموقع.
# كل لغة تُكتب في dist/<الرمز>/ بالمسارات نفسها، فلكل صفحة نظيرتها في اللغة الأخرى.
LANGS = [("ar", "rtl", CONTENT), ("en", "ltr", CONTENT / "en")]
BASE_URL = "https://" + (ROOT / "CNAME").read_text(encoding="utf-8").strip() + "/"

# مفتاح القائمة العلوية الذي يُظلَّل في كل صفحة من src/pages
NAV_KEY = {"index": "home", "services": "services", "industries": "industries", "about": "about", "contact": "contact"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_content(content):
    """يقرأ نصوص لغة واحدة من مجلدها (src/content للعربية، src/content/en للإنجليزية)."""
    site = load(content / "site.json")
    tracks, services = [], {}
    for slug in site["tracks_order"]:
        t = load(content / "tracks" / f"{slug}.json")
        t["slug"] = slug
        # تجميع خدمات المسار حسب «group» مع الحفاظ على ترتيب الملف
        t["groups"] = []
        for s in t["services"]:
            if not t["groups"] or t["groups"][-1]["name"] != s["group"]:
                t["groups"].append({"name": s["group"], "services": []})
            t["groups"][-1]["services"].append(s)
        # مسار له «group_info»: كل مجموعة تأخذ رابطًا ووصفًا وتُعرض في صفحة مستقلة
        info = {g["name"]: g for g in t.get("group_info", [])}
        if info and set(info) != {g["name"] for g in t["groups"]}:
            sys.exit(f"خطأ في المسار {slug} ({content}): أسماء group_info لا تطابق مجموعات الخدمات.")
        for g in t["groups"]:
            g.update({k: info[g["name"]].get(k, "") for k in ("slug", "desc", "long", "img", "need", "gain", "article", "side", "side_svg", "side_caption")}) if info else g.update(slug="", desc="", long="", img="", need=[], gain=[], article="", side="", side_svg="", side_caption="")
        # صفحات الخدمات: ملف لكل خدمة داخل content/services/<المسار>/
        files = {f.stem: f for f in sorted((content / "services" / slug).glob("*.json"))}
        listed = {s["page"] for s in t["services"] if s["page"]}
        if set(files) != listed:
            sys.exit(f"خطأ في المسار {slug} ({content}): الملفات {sorted(set(files) - listed)} غير مذكورة في قائمة الخدمات، "
                     f"والصفحات {sorted(listed - set(files))} مذكورة بلا ملف.")
        for s in t["services"]:
            if s["page"]:
                page = load(files[s["page"]])
                page.update(slug=s["page"], track=slug, desc=s["desc"], group=s["group"])
                services[s["page"]] = page
        tracks.append(t)
    offers = []
    for slug in site["offers_order"]:
        o = load(content / "offers" / f"{slug}.json")
        o["slug"] = slug
        offers.append(o)
    extra = {name: load(content / f"{name}.json") for name in ("industries", "industry_groups", "values", "where", "privacy", "ui")}
    # كل قطاع يتبع مجموعة معرّفة في industry_groups.json، وكل مجموعة فيها قطاع واحد على الأقل
    gids = {g["id"] for g in extra["industry_groups"]}
    used = {r["group"] for r in extra["industries"]}
    if used != gids:
        sys.exit(f"خطأ في القطاعات ({content}): مجموعات غير معرّفة {sorted(used - gids)}، ومجموعات بلا قطاعات {sorted(gids - used)}.")
    return site, tracks, services, offers, extra


def build_lang(lang, direction, content, write):
    """يبني صفحات لغة واحدة في dist/<lang>/ ويعيد بيانات الموقع وقائمة الصفحات المكتوبة."""
    site, tracks, services, offers, extra = load_content(content)
    langs = [code for code, _, _ in LANGS]
    other, other_content = next((code, c) for code, _, c in LANGS if code != lang)
    env = Environment(loader=FileSystemLoader([SRC / "templates", SRC / "pages"]), autoescape=True,
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    env.globals.update(site=site, tracks=tracks, offers=offers, lang=lang, dir=direction, langs=langs, base_url=BASE_URL,
                       alt_lang=other, alt_name=load(other_content / "ui.json")["lang_name"], **extra)
    # رقم إصدار لكل ملف ثابت (من محتواه) يُلحق برابطه، فيجلب المتصفح النسخة الجديدة بعد كل تعديل
    env.globals["ver"] = lambda rel: hashlib.md5((SRC / "assets" / rel).read_bytes()).hexdigest()[:8]

    # [[صفحة-الخدمة|النص]] داخل نص المقال تصبح رابطًا إلى صفحة الخدمة. يتحقق البناء من وجود الصفحة.
    def linkify(text, prefix):
        def repl(mt):
            page, label = mt.group(1), mt.group(2)
            if page not in services:
                sys.exit(f"خطأ: رابط إلى خدمة غير موجودة «{page}» في نص المقال ({lang}).")
            return f'<a href="{escape(prefix)}{escape(page)}/">{escape(label)}</a>'
        parts = re.split(r"(\[\[[^\]|]+\|[^\]]+\]\])", text)
        out = []
        for part in parts:
            mt = re.fullmatch(r"\[\[([^\]|]+)\|([^\]]+)\]\]", part)
            out.append(repl(mt) if mt else str(escape(part)))
        return Markup("".join(out))
    env.filters["linkify"] = linkify
    rels = []

    def render(template, rel, nav="", **ctx):
        root = "../" * (len(Path(rel).parts) - 1)  # الطريق من الصفحة إلى جذر اللغة
        page_path = rel[: -len("index.html")]  # مثل services/geoai/ ، وفارغ للرئيسية
        html = env.get_template(template).render(root=root, home=root or "./", assets=root + "../assets/", nav=nav,
                                                 page_path=page_path, alt_href=f"{root}../{other}/{page_path}", **ctx)
        write(f"{lang}/{rel}", html)
        rels.append(rel)

    for page in sorted((SRC / "pages").glob("*.html")):
        rel = "index.html" if page.stem == "index" else f"{page.stem}/index.html"
        render(page.name, rel, nav=NAV_KEY.get(page.stem, ""))
    for t in tracks:
        render("track.html", f"services/{t['slug']}/index.html", nav="services", t=t)
        for g in t["groups"]:
            if g["slug"]:
                render("group.html", f"services/{t['slug']}/{g['slug']}/index.html", nav="services", t=t, g=g)
        for s in t["services"]:
            if not s["page"]:
                continue
            related = [x for x in t["services"] if x["page"] and x["page"] != s["page"] and x["group"] == s["group"]]
            render("service.html", f"services/{t['slug']}/{s['page']}/index.html", nav="services", t=t, s=services[s["page"]], related=related)
    for o in offers:
        render("offer.html", f"offers/{o['slug']}/index.html", nav="services", o=o)
    print(f"  dist/{lang}/: {len(rels)} صفحة  ({len(tracks)} مسارات، {len(services)} خدمة، {len(offers)} عروض)")
    return site, rels


def main():
    written = set()

    def write(rel, text):
        out = DIST / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8", newline="\n")
        written.add(out)

    built = {code: build_lang(code, direction, content, write) for code, direction, content in LANGS}
    # كل صفحة لها نظيرة في كل لغة، وإلا صار رابط مبدّل اللغة معطلًا
    LANG = LANGS[0][0]
    for code in built:
        a, b = set(built[LANG][1]), set(built[code][1])
        if a != b:
            sys.exit(f"خطأ: الصفحات تختلف بين {LANG} و{code}. ناقصة في {code}: {sorted(a - b)}، زائدة فيها: {sorted(b - a)}")
    site = built[LANG][0]

    # الجذر يحوّل إلى النسخة العربية
    write("index.html", f'<!DOCTYPE html>\n<html lang="ar" dir="rtl">\n<meta charset="utf-8">\n<title>{site["full_name"]}</title>\n'
                        f'<meta http-equiv="refresh" content="0; url={LANG}/">\n<link rel="canonical" href="{LANG}/">\n'
                        f'<a href="{LANG}/">{site["full_name"]}</a>\n</html>\n')

    # Netlify: الجذر يذهب مباشرة إلى النسخة العربية
    write("_redirects", f"/  /{LANG}/  301!\n")

    # الملفات الثابتة
    for f in (SRC / "assets").rglob("*"):
        if f.is_file():
            out = DIST / "assets" / f.relative_to(SRC / "assets")
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, out)
            written.add(out)

    # تنظيف ما بقي من بناء سابق (صفحة حُذفت أو تغيّر اسمها)
    stale = [f for f in DIST.rglob("*") if f.is_file() and f not in written]
    for f in stale:
        try:
            f.unlink()
        except OSError:
            print(f"تنبيه: ملف قديم لم يُحذف: {f.relative_to(ROOT)}")

    pages = sum(1 for f in written if f.suffix == ".html") - 1
    print(f"تم البناء: {pages} صفحة بلغتين في {', '.join(f'dist/{c}/' for c in built)}")
    print(f"للمعاينة افتح: {DIST / 'index.html'}")


if __name__ == "__main__":
    main()
