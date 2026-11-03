#!/usr/bin/env python3
"""Step 2 of the migration. Takes the templates produced by extract.py and
pulls the shared chrome (sidebar, footer, language switcher, head meta) out of
them, so it lives in one place instead of 23 copies.

Navigation labels become stable `nav.*` keys kept in the locale files, so a new
language is still just one new JSON file. Run once, after extract.py.
"""

import json
import os
import posixpath
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES_DIR = os.path.join(ROOT, "_src", "pages")
LOCALES_DIR = os.path.join(ROOT, "_src", "locales")
SRC = os.path.join(ROOT, "_src")

SIDEBAR_RE = re.compile(r'<aside class="sidebar" id="sidebar">.*?</aside>', re.S)
FOOTER_RE = re.compile(r'<footer class="footer">.*?</footer>', re.S)
SELECT_RE = re.compile(r'<select id="lang-select".*?</select>', re.S)
LANGSCRIPT_RE = re.compile(r"<script>/\* supported languages.*?</script>\s*", re.S)
ASSET_RE = re.compile(r'(?:\.\./)*assets/')
KEY_RE = re.compile(r'data-i18n="([^"]+)"')
LINK_RE = re.compile(r'<a href="([^"]+)"([^>]*)>(.*?)</a>', re.S)


def load_locales():
    out = {}
    for lang in ("en", "zh"):
        with open(os.path.join(LOCALES_DIR, "%s.json" % lang), encoding="utf-8") as f:
            out[lang] = json.load(f)
    return out


def norm_href(page_rel, href):
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return href
    return posixpath.normpath(posixpath.join(posixpath.dirname(page_rel), href))


def slugify(text):
    s = re.sub(r"<[^>]+>", "", text)
    s = s.replace("&amp;", "and").replace("&", "and")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return (s or "item")[:40]


def parse_sidebar(html, page_rel, locales, sink):
    """Build nav.json entries; navigation copy is written into `sink` under
    stable nav.* keys."""
    used = set()

    def put(en_key):
        """en_key is the legacy per-page data-i18n key -> allocate a nav.* key."""
        en = locales["en"].get(en_key, "")
        zh = locales["zh"].get(en_key, "")
        base = "nav." + slugify(en)
        key, n = base, 2
        while key in used:
            key = "%s-%d" % (base, n)
            n += 1
        used.add(key)
        sink["en"][key] = en
        sink["zh"][key] = zh
        return key

    groups = []
    for g in re.finditer(r'<div class="nav-group">(.*?)\n    </div>', html, re.S):
        body = g.group(1)
        group = {"label": None, "items": []}
        lab = re.search(r'<div class="nav-label">.*?data-i18n="([^"]+)"', body, re.S)
        if lab:
            group["label"] = put(lab.group(1))
        sub = re.search(r'<div class="nav-sub">(.*?)</div>', body, re.S)
        for m in LINK_RE.finditer(body):
            href = norm_href(page_rel, m.group(1))
            inner = m.group(3)
            k = KEY_RE.search(inner)
            item = {"href": href}
            if k:
                item["key"] = put(k.group(1))
            else:
                item["literal"] = re.sub(r"<[^>]+>", "", inner).strip()
            if 'target="_blank"' in m.group(2):
                item["blank"] = True
            in_sub = sub and sub.start() < m.start() < sub.end()
            if in_sub:
                if not group["items"] or group["items"][-1].get("type") != "sub":
                    group["items"].append({"type": "sub", "items": []})
                group["items"][-1]["items"].append(item)
            else:
                group["items"].append(item)
        groups.append(group)
    return groups


def extract_footer(html, locales, sink):
    for m in LINK_RE.finditer(html):
        k = KEY_RE.search(m.group(3))
        if not k:
            continue
        en = locales["en"].get(k.group(1), "")
        zh = locales["zh"].get(k.group(1), "")
        slug = slugify(en)
        sink["en"]["_ui.footer." + slug] = en
        sink["zh"]["_ui.footer." + slug] = zh


def main():
    locales = load_locales()
    sink = {"en": {}, "zh": {}}
    nav = None
    removed = {"en": set(), "zh": set()}

    pages = []
    for dirpath, dirnames, filenames in os.walk(PAGES_DIR):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.endswith(".html"):
                pages.append(os.path.relpath(os.path.join(dirpath, fn), PAGES_DIR))
    pages = sorted(p.replace(os.sep, "/") for p in pages)

    # The old pages disagree on what the sidebar contains: 12 of them expand the
    # feature sub-nav, 11 do not. Pick the richest one as the single source.
    source = None
    for rel in pages:
        text = open(os.path.join(PAGES_DIR, rel), encoding="utf-8").read()
        sb = SIDEBAR_RE.search(text)
        if sb and (source is None or sb.group(0).count("<a href=") > source[0]):
            source = (sb.group(0).count("<a href="), rel, sb.group(0))
    nav = parse_sidebar(source[2], source[1], locales, sink)
    print("nav source      : %s (%d links)" % (source[1], source[0]))

    for rel in pages:
        path = os.path.join(PAGES_DIR, rel)
        text = open(path, encoding="utf-8").read()

        sb = SIDEBAR_RE.search(text)
        if not sb:
            raise SystemExit("no sidebar in %s" % rel)
        for key in KEY_RE.findall(sb.group(0)):
            removed["en"].add(key)
            removed["zh"].add(key)
        text = text[: sb.start()] + "{{SIDEBAR}}" + text[sb.end():]

        ft = FOOTER_RE.search(text)
        if ft:
            if "_ui.footer.issues" not in sink["en"] and "Report issues" in ft.group(0):
                extract_footer(ft.group(0), locales, sink)
            for key in KEY_RE.findall(ft.group(0)):
                removed["en"].add(key)
                removed["zh"].add(key)
            text = text[: ft.start()] + "{{FOOTER}}" + text[ft.end():]

        sel = SELECT_RE.search(text)
        if sel:
            text = text[: sel.start()] + "{{LANGSWITCH}}" + text[sel.end():]

        text = LANGSCRIPT_RE.sub("{{HEAD_META}}\n", text)
        text = text.replace('<html lang="en">', '<html lang="{{LANG}}">')
        text = ASSET_RE.sub("{{ROOT}}assets/", text)

        title_key = rel[:-5].replace("/", ".")
        if title_key == "index":
            title_key = "home"
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S)
        h1key = KEY_RE.search(h1.group(1)) if h1 else None
        for lang in ("en", "zh"):
            val = locales[lang].get(h1key.group(1), "") if h1key else ""
            val = re.sub(r"<[^>]+>", "", val).replace("&amp;", "&").strip()
            sink[lang]["%s.__title" % title_key] = val or "Control Flex Wiki"
        text = re.sub(r"<title>.*?</title>", "<title>{{TITLE}}</title>", text, flags=re.S)

        open(path, "w", encoding="utf-8", newline="\n").write(text)

    for lang in ("en", "zh"):
        data = {k: v for k, v in locales[lang].items() if k not in removed[lang]}
        data.update(sink[lang])
        with open(os.path.join(LOCALES_DIR, "%s.json" % lang), "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    with open(os.path.join(SRC, "nav.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(nav, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("pages templated : %d" % len(pages))
    print("nav groups      : %d" % len(nav))
    print("nav keys        : %d" % len([k for k in sink["en"] if k.startswith("nav.")]))
    print("dropped dup keys: %d" % len(removed["en"]))
    print("keys left       : en=%d zh=%d" % (len(locales["en"]) - len(removed["en"]) + len(sink["en"]),
                                             len(locales["zh"]) - len(removed["zh"]) + len(sink["zh"])))


if __name__ == "__main__":
    main()
