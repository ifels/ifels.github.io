#!/usr/bin/env python3
"""One-shot migration: pull the paired [data-lang] nodes out of the legacy
single-file-bilingual HTML in ../../control-flex and split them into

    _src/pages/<path>.html   template with <X data-i18n="key">default</X>
    _src/locales/en.json     source strings
    _src/locales/zh.json     translations

Run once. Afterwards _src/pages is the source of truth and build.py takes over.
"""

import json
import os
import re
import sys
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "control-flex")
PAGES_DIR = os.path.join(ROOT, "_src", "pages")
LOCALES_DIR = os.path.join(ROOT, "_src", "locales")

# files that are not content pages
SKIP = {"404.html"}

TAG_OPEN = re.compile(r"<(span|div)\b([^>]*?)data-lang=\"(en|zh)\"([^>]*)>")
ANY_SPAN = re.compile(r"<span\b[^>]*>|</span>")
ANY_DIV = re.compile(r"<div\b[^>]*>|</div>")


def node_end(text, open_tag_match):
    """Return end offset (`<` of the matching close tag) for the element whose
    opening tag ends at open_tag_match.end()."""
    tag = open_tag_match.group(1)
    pattern = ANY_SPAN if tag == "span" else ANY_DIV
    close = "</%s>" % tag
    depth = 1
    for tok in pattern.finditer(text, open_tag_match.end()):
        if tok.group(0) == close:
            depth -= 1
        elif tok.group(0).startswith("<%s" % tag):
            depth += 1
        if depth == 0:
            return tok.start(), tok.end()
    raise ValueError("unbalanced <%s> at %d" % (tag, open_tag_match.start()))


def collect_nodes(text):
    nodes = []
    pos = 0
    while True:
        m = TAG_OPEN.search(text, pos)
        if not m:
            break
        start, end = node_end(text, m)
        nodes.append(
            {
                "tag": m.group(1),
                "lang": m.group(3),
                "outer_start": m.start(),
                "inner_start": m.end(),
                "inner_end": start,
                "outer_end": end,
                "inner": text[m.end():start],
            }
        )
        pos = end
    return nodes


def page_key(path):
    p = path.replace(os.sep, "/")
    if p.endswith(".html"):
        p = p[:-5]
    if p == "index":
        return "home"
    return p.replace("/", ".")


def migrate(rel_path, report):
    path = os.path.join(SRC_DIR, rel_path)
    text = open(path, encoding="utf-8").read()
    nodes = collect_nodes(text)

    strings = {"en": OrderedDict(), "zh": OrderedDict()}
    key_base = page_key(rel_path)
    out = []
    cursor = 0
    i = 0
    counter = 0
    while i < len(nodes):
        n = nodes[i]
        if i + 1 < len(nodes):
            m = nodes[i + 1]
            if (
                m["lang"] != n["lang"]
                and text[n["outer_end"]:m["outer_start"]].strip() == ""
                and m["tag"] == n["tag"]
            ):
                pair = {n["lang"]: n, m["lang"]: m}
                if set(pair) == {"en", "zh"}:
                    counter += 1
                    key = "%s.%d" % (key_base, counter)
                    strings["en"][key] = pair["en"]["inner"].strip()
                    strings["zh"][key] = pair["zh"]["inner"].strip()
                    out.append(text[cursor:n["outer_start"]])
                    out.append(
                        '<%s data-i18n="%s">%s</%s>'
                        % (n["tag"], key, pair["en"]["inner"].strip(), n["tag"])
                    )
                    cursor = m["outer_end"]
                    i += 2
                    continue
        report["unpaired"].append((rel_path, n["lang"], n["inner"][:60]))
        i += 1
    out.append(text[cursor:])
    result = "".join(out)

    # sanity: no data-lang left
    left = result.count('data-lang=')
    if left:
        report["leftover"].append((rel_path, left))

    return result, strings


def main():
    if not os.path.isdir(SRC_DIR):
        sys.exit("control-flex/ not found")

    pages = []
    for dirpath, dirnames, filenames in os.walk(SRC_DIR):
        dirnames[:] = [d for d in dirnames if d not in {".git"}]
        for fn in filenames:
            if not fn.endswith(".html") or fn in SKIP:
                continue
            abs_p = os.path.join(dirpath, fn)
            pages.append(os.path.relpath(abs_p, SRC_DIR))
    pages.sort()

    report = {"unpaired": [], "leftover": [], "pages": []}
    all_strings = {"en": OrderedDict(), "zh": OrderedDict()}

    for rel in pages:
        template, strings = migrate(rel, report)
        dst = os.path.join(PAGES_DIR, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "w", encoding="utf-8", newline="\n").write(template)
        all_strings["en"].update(strings["en"])
        all_strings["zh"].update(strings["zh"])
        report["pages"].append((rel, len(strings["en"])))

    for lang in ("en", "zh"):
        dst = os.path.join(LOCALES_DIR, "%s.json" % lang)
        with open(dst, "w", encoding="utf-8", newline="\n") as f:
            json.dump(all_strings[lang], f, ensure_ascii=False, indent=2)
            f.write("\n")

    print("pages migrated : %d" % len(pages))
    print("strings        : en=%d zh=%d" % (len(all_strings["en"]), len(all_strings["zh"])))
    print("unpaired nodes : %d" % len(report["unpaired"]))
    for item in report["unpaired"][:20]:
        print("   ! %s [%s] %r" % item)
    print("leftover       : %d" % len(report["leftover"]))
    for item in report["leftover"][:20]:
        print("   ! %s still has %d data-lang" % item)

    missing = set(all_strings["en"]) - set(all_strings["zh"])
    extra = set(all_strings["zh"]) - set(all_strings["en"])
    print("zh missing     : %d %s" % (len(missing), sorted(missing)[:5]))
    print("zh extra       : %d %s" % (len(extra), sorted(extra)[:5]))
    empty = [k for k, v in all_strings["zh"].items() if not v.strip()]
    print("empty zh       : %d %s" % (len(empty), empty[:5]))


if __name__ == "__main__":
    main()
