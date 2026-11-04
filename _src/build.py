#!/usr/bin/env python3
"""Build the wiki from _src into control-flex/.

    python _src/build.py

Source layout
    _src/pages/<path>.html     page templates, text nodes carry data-i18n
    _src/locales/<code>.json   one file per language (add a file = add a language)
    _src/nav.json              sidebar structure
    _src/site.json             base path / absolute URL for hreflang

Output
    control-flex/<code>/<path>   fully rendered pages, one tree per language
    control-flex/index.html      language picker / auto-redirect
    control-flex/<old path>      redirect stubs so existing links keep working
"""

import html as htmllib
import json
import os
import posixpath
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_src")
LOCALES_DIR = os.path.join(SRC, "locales")
PAGES_DIR = os.path.join(SRC, "pages")
OUT = os.path.join(ROOT, "control-flex")

I18N_OPEN = re.compile(r'<(\w+)([^>]*?)\sdata-i18n="([^"]+)"([^>]*?)>')
PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}")

FALLBACK = "en"


def load_site():
    with open(os.path.join(SRC, "site.json"), encoding="utf-8") as f:
        return json.load(f)


def load_locales():
    langs = []
    for fn in sorted(os.listdir(LOCALES_DIR)):
        if not fn.endswith(".json"):
            continue
        code = fn[:-5]
        with open(os.path.join(LOCALES_DIR, fn), encoding="utf-8") as f:
            data = json.load(f)
        langs.append({"code": code, "strings": data, "meta": data.get("_lang", {})})
    if not langs:
        sys.exit("no locales found")
    langs.sort(key=lambda l: (l["meta"].get("order", 99), l["code"]))
    return langs


def find_close(text, start, tag):
    pat = re.compile(r"<(/?)%s\b[^>]*>" % tag)
    depth = 1
    for m in pat.finditer(text, start):
        if m.group(1):
            depth -= 1
        else:
            depth += 1
        if depth == 0:
            return m.start(), m.end()
    raise ValueError("unbalanced <%s>" % tag)


def render_strings(template, strings, fallback, missing, page, origin):
    out = []
    cursor = 0
    pos = 0
    while True:
        m = I18N_OPEN.search(template, pos)
        if not m:
            break
        tag = m.group(1)
        key = m.group(3)
        inner_start = m.end()
        close_start, close_end = find_close(template, inner_start, tag)

        value = strings.get(key)
        if value is None:
            missing.append((page, key))
            value = fallback.get(key, "")

        attrs = (m.group(2) + m.group(4)).replace('  ', ' ').strip()
        out.append(template[cursor:m.start()])
        if attrs:
            out.append("<%s %s>%s</%s>" % (tag, attrs, value, tag))
        else:
            out.append("<%s>%s</%s>" % (tag, value, tag))
        cursor = close_end
        pos = close_end
    out.append(template[cursor:])
    return "".join(out)


def render_nav(nav, strings, fallback, base, lang, page_path):
    def text(key):
        v = strings.get(key)
        if v is None:
            v = fallback.get(key, "")
        return v

    def link(item, sub=False):
        href = item["href"]
        if not href.startswith(("http://", "https://", "mailto:", "#")):
            href = "%s/%s/%s" % (base, lang, href)
        attrs = ' target="_blank" rel="noopener"' if item.get("blank") else ""
        if "key" in item:
            label = text(item["key"])
        else:
            label = item.get("literal") or href
        return '<a href="%s"%s>%s</a>' % (href, attrs, label)

    lines = ['<aside class="sidebar" id="sidebar">', "  <nav>"]
    for group in nav:
        lines.append('    <div class="nav-group">')
        if group.get("label"):
            lines.append('      <div class="nav-label">%s</div>' % text(group["label"]))
        for item in group["items"]:
            if item.get("type") == "sub":
                lines.append('      <div class="nav-sub">')
                for s in item["items"]:
                    lines.append("        " + link(s, True))
                lines.append("      </div>")
            else:
                lines.append("      " + link(item))
        lines.append("    </div>")
    lines.append("  </nav>")
    lines.append("</aside>")
    # Restore the sidebar scroll position synchronously, before first paint, so
    # navigating between pages does not snap the menu back to the top.
    lines.append(
        "<script>\n"
        "(function () {\n"
        "  var s = document.getElementById('sidebar');\n"
        "  var KEY = 'cfxSidebarScroll';\n"
        "  var saved = null;\n"
        "  try { saved = sessionStorage.getItem(KEY); } catch (e) {}\n"
        "  if (saved !== null) {\n"
        "    s.scrollTop = +saved || 0;\n"
        "  } else {\n"
        "    var here = location.pathname.split('/').pop();\n"
        "    var links = s.querySelectorAll('a[href]');\n"
        "    for (var i = 0; i < links.length; i++) {\n"
        "      if (links[i].getAttribute('href').split('/').pop() === here) {\n"
        "        s.scrollTop = Math.max(0, links[i].offsetTop - s.clientHeight / 2);\n"
        "        break;\n"
        "      }\n"
        "    }\n"
        "  }\n"
        "  function save() {\n"
        "    try { sessionStorage.setItem(KEY, String(s.scrollTop)); } catch (e) {}\n"
        "  }\n"
        "  var t;\n"
        "  s.addEventListener('scroll', function () {\n"
        "    clearTimeout(t);\n"
        "    t = setTimeout(save, 100);\n"
        "  }, { passive: true });\n"
        "  s.addEventListener('click', function (ev) {\n"
        "    if (ev.target.closest('a')) save();\n"
        "  });\n"
        "})();\n"
        "</script>"
    )
    return "\n".join(lines)


def render_footer(strings, fallback, base):
    def text(key):
        v = strings.get(key)
        return v if v is not None else fallback.get(key, "")

    issues = text("_ui.footer.report-issues")
    configs = text("_ui.footer.community-configs")
    return """<footer class="footer">
  <div class="footer-inner">
    <span>Control Flex — LGPL-3.0 · SDL3 (zlib)</span>
    <a href="https://github.com/ControlFlexMC/control-flex/issues" target="_blank" rel="noopener">%s ↗</a>
    <a href="https://github.com/ControlFlexMC/control-flex-api" target="_blank" rel="noopener">control-flex-api ↗</a>
    <a href="https://github.com/ControlFlexMC/cfx-compat-configs" target="_blank" rel="noopener">%s ↗</a>
  </div>
</footer>""" % (issues, configs)


def render_langswitch(langs, current, base, page_path, strings):
    def name(l):
        return l["meta"].get("name") or l["code"]

    parts = ['<div class="lang-switch" role="group" aria-label="Language">']
    for l in langs:
        if l["code"] == current["code"]:
            parts.append(
                '<span class="lang-current" aria-current="true">%s</span>' % name(l)
            )
        else:
            parts.append(
                '<a href="%s/%s/%s" hreflang="%s" lang="%s" data-set-lang="%s">%s</a>'
                % (base, l["code"], page_path, l["code"], l["code"], l["code"], name(l))
            )
    parts.append("</div>")
    return "".join(parts)


def head_meta(site, langs, current, page_path, title):
    base = site["basePath"]
    url = site["siteUrl"]
    targets = {l["code"]: "%s/%s/%s" % (base, l["code"], page_path) for l in langs}
    out = [
        "<script>"
        "(function(){var q=new URLSearchParams(location.search).get('lang');if(!q)return;"
        "var m=%s;if(!m[q])return;try{localStorage.setItem('preferredLang',q);}catch(e){}"
        "if(q!==%s)location.replace(m[q]+location.hash);})();"
        "</script>" % (json.dumps(targets), json.dumps(current["code"]))
    ]
    out.append('<link rel="canonical" href="%s%s/%s/%s">' % (url, base, current["code"], page_path))
    for l in langs:
        out.append(
            '<link rel="alternate" hreflang="%s" href="%s%s/%s/%s">'
            % (l["code"], url, base, l["code"], page_path)
        )
    default = next((l for l in langs if l["meta"].get("default")), langs[0])
    out.append(
        '<link rel="alternate" hreflang="x-default" href="%s%s/%s/%s">'
        % (url, base, default["code"], page_path)
    )
    out.append('<meta property="og:title" content="%s">' % htmllib.escape(title, quote=True))
    out.append('<meta property="og:locale" content="%s">' % current["code"].replace("-", "_"))
    return "\n".join(out)


def depth_of(page_path):
    return page_path.count("/")


def collect_pages():
    pages = []
    for dirpath, dirnames, filenames in os.walk(PAGES_DIR):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.endswith(".html"):
                rel = os.path.relpath(os.path.join(dirpath, fn), PAGES_DIR)
                pages.append(rel.replace(os.sep, "/"))
    return sorted(pages)


REDIRECT_TMPL = """<!DOCTYPE html>
<html lang="%(lang)s">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Control Flex Wiki</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="%(absolute)s">
<script>
(function () {
  var path = %(path)s;
  var supported = %(codes)s;
  var lang = null;
  var q = new URLSearchParams(location.search).get('lang');
  if (q && supported.indexOf(q) >= 0) {
    lang = q;
    try { localStorage.setItem('preferredLang', q); } catch (e) {}
  } else {
    try { lang = localStorage.getItem('preferredLang'); } catch (e) {}
    if (!lang) {
      var nav = (navigator.languages && navigator.languages[0]) || navigator.language || 'en';
      lang = String(nav).toLowerCase().split('-')[0];
    }
  }
  if (supported.indexOf(lang) < 0) lang = %(default)s;
  location.replace(%(prefix)s + lang + '/' + path);
})();
</script>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
max-width:36rem;margin:18vh auto;padding:0 1.5rem;color:#333;line-height:1.6}
a{color:#1f9d55}
</style>
</head>
<body>
<p>%(message)s</p>
<p><a href="%(default)s/%(path_attr)s">%(manual)s</a></p>
</body>
</html>
"""


def main():
    site = load_site()
    langs = load_locales()
    base = site["basePath"]
    with open(os.path.join(SRC, "nav.json"), encoding="utf-8") as f:
        nav = json.load(f)

    codes = [l["code"] for l in langs]
    default = next((l for l in langs if l["meta"].get("default")), langs[0])
    fallback = next(l for l in langs if l["code"] == FALLBACK)["strings"]

    # wipe previously generated output, but keep assets/ and hand-written files
    # such as README.md. Directories left empty (e.g. an old guide/ tree) go too.
    for entry in os.listdir(OUT):
        p = os.path.join(OUT, entry)
        if entry == "assets":
            continue
        if os.path.isdir(p):
            if entry in codes:
                shutil.rmtree(p)
                continue
            keep = []
            for dirpath, _, filenames in os.walk(p):
                for fn in filenames:
                    full = os.path.join(dirpath, fn)
                    if fn.endswith(".html"):
                        os.remove(full)
                    else:
                        keep.append(full)
            if not keep:
                shutil.rmtree(p)
        elif entry.endswith(".html"):
            os.remove(p)

    pages = collect_pages()
    missing = []
    written = 0

    for page_path in pages:
        template = open(os.path.join(PAGES_DIR, page_path), encoding="utf-8").read()
        page_key = page_path[:-5].replace("/", ".")
        if page_key == "index":
            page_key = "home"

        for lang in langs:
            strings = lang["strings"]
            depth = depth_of(page_path) + 1
            root = "../" * depth

            title = strings.get(page_key + ".__title") or fallback.get(page_key + ".__title") or "Control Flex Wiki"
            if page_path != "index.html":
                title = "%s · Control Flex Wiki" % title

            body = render_strings(template, strings, fallback, missing, page_path, lang["code"])
            body = body.replace("{{LANG}}", lang["meta"].get("htmlLang") or lang["code"])
            body = body.replace("{{TITLE}}", htmllib.escape(title, quote=False))
            body = body.replace("{{ROOT}}", root)
            body = body.replace("{{SIDEBAR}}", render_nav(nav, strings, fallback, base, lang["code"], page_path))
            body = body.replace("{{FOOTER}}", render_footer(strings, fallback, base))
            body = body.replace("{{LANGSWITCH}}", render_langswitch(langs, lang, base, page_path, strings))
            body = body.replace("{{HEAD_META}}", head_meta(site, langs, lang, page_path, title))

            leftover = PLACEHOLDER.search(body)
            if leftover:
                sys.exit("unreplaced placeholder %s in %s (%s)" % (leftover.group(0), page_path, lang["code"]))

            dst = os.path.join(OUT, lang["code"], page_path.replace("/", os.sep))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8", newline="\n") as f:
                f.write(body)
            written += 1

    # language picker at the project root
    picker = REDIRECT_TMPL % {
        "lang": default["code"],
        "absolute": "%s%s/%s/" % (site["siteUrl"], base, default["code"]),
        "path": json.dumps("index.html"),
        "path_attr": "index.html",
        "codes": json.dumps(codes),
        "default": json.dumps(default["code"]),
        "prefix": json.dumps(""),
        "message": "正在载入 Control Flex Wiki · Loading Control Flex Wiki",
        "manual": "English / 中文",
    }
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(picker)

    print("languages : %s" % ", ".join("%s(%s)" % (l["code"], l["meta"].get("name", "")) for l in langs))
    print("pages     : %d x %d = %d rendered" % (len(pages), len(langs), written))
    print("entry     : control-flex/index.html (language picker)")
    if missing:
        print("MISSING   : %d keys" % len(missing))
        for page, key in missing[:15]:
            print("   ! %s -> %s" % (page, key))
        sys.exit(1)
    print("strings   : all keys resolved")


if __name__ == "__main__":
    main()
