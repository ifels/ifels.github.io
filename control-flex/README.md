# Control Flex Wiki

Static documentation site for the [Control Flex](https://www.curseforge.com/minecraft/mc-mods/control-flex)
Minecraft mod, served from GitHub Pages at **https://ifels.github.io/control-flex/**.

Text is written once (templates + one JSON file per language) and built into a
complete static tree for each language. There is no runtime translation and no
language swapping in the browser — every visitor gets a finished HTML page, so
first paint never flashes the wrong language and crawlers see real content.

## Naming

Display text uses **Control Flex** (with a space), matching the CurseForge listing and the
in-game key-binding category. Identifiers stay joined: the mod id `controlflex`, config paths
such as `config/controlflex/`, class names such as `ControlFlexApi` / `IControlFlexPlugin`, and
repository names (`ControlFlexMC/...`).

## Source vs output

Everything under `../_src/` is the source. Everything under `control-flex/` except
`assets/` and this README is generated — do not edit it by hand, it gets overwritten.

```
_src/
├── pages/                   # page templates
│   ├── index.html           #   Landing page
│   ├── guide/               #   getting-started, platforms, versions, features, settings
│   │   └── feature/         #   one page per feature (12 pages, breadcrumb + prev/next)
│   ├── modpack/             #   config layout, override rules, compatibility
│   │   └── compat/          #   overview, compat JSON, bridge mods, by hand
│   └── dev/                 #   redirect stubs: the old developer pages moved
├── locales/
│   ├── en.json              # one file per language; add a file = add a language
│   └── zh.json
├── nav.json                 # sidebar structure, shared by every page
├── site.json                # basePath + absolute URL (canonical / hreflang)
├── build.py                 # generator
└── one-off/                 # migration scripts, kept for reference, not needed to build
```

```
control-flex/                # generated
├── index.html               # language picker / auto redirect
├── en/**                    # complete English tree
├── zh/**                    # complete Chinese tree
├── assets/
│   ├── style.css            # all styling (light + dark via prefers-color-scheme)
│   └── app.js               # mobile sidebar, active nav, copy buttons, language memory
└── README.md
```

## Build

```bash
# from the repository root (ifels.github.io)
python _src/build.py
```

Prints the rendered page count, the number of redirect stubs, and fails loudly if
a template references an `data-i18n` key that no locale file defines. Requires
Python 3.8+ and nothing else.

Commit the generated output — GitHub Pages serves `control-flex/` directly, there
is no CI step.

## URLs

| URL | Behaviour |
|-----|-----------|
| `/control-flex/zh/guide/getting-started.html` | canonical form |
| `/control-flex/…?lang=en` | explicit language, wins over everything |
| `/control-flex/` | picks a language: `?lang` → `localStorage` → `navigator.language` → `en` |

`?lang=` is an entry shortcut, not a content switch: it redirects to the
matching static tree, so the canonical URL always carries the language segment.
Every page carries `hreflang` alternates, an `x-default`, and a self `canonical`.

Paths without a language segment (`/control-flex/guide/…`) are **not** kept
alive — they return 404, and only the entry point above survives. If old deep
links ever matter, add a `404.html` at the repository root that rewrites the
incoming path onto `/<lang>/…`.

## Editing text

1. Find the key in the page template: `<li data-i18n="guide.settings.42">…</li>`.
2. Change the same key in **both** `_src/locales/en.json` and `_src/locales/zh.json`.
3. Run `python _src/build.py`.

Keys are `<page>.<n>`, numbered in document order. When you add a paragraph, append
a **new** key at the next free number instead of renumbering — renumbering quietly
detaches existing translations.

## Adding a page

1. Create `_src/pages/<section>/<name>.html` (copy a sibling as a starting point).
2. Give every translatable text node a `data-i18n` key; leave the chrome as
   `{{SIDEBAR}}`, `{{FOOTER}}`, `{{LANGSWITCH}}`, `{{HEAD_META}}`, `{{ROOT}}`,
   `{{TITLE}}`, `{{LANG}}` placeholders.
3. Add the matching keys to every `_src/locales/*.json`.
4. Add the entry to `_src/nav.json` — the sidebar is generated, so this is the only
   place to touch (previously it was duplicated in all 23 pages).
5. `python _src/build.py`.

## Adding a language (e.g. `ja`)

```bash
cp _src/locales/en.json _src/locales/ja.json
```

Then:

1. Replace the `_lang` block with `{"name": "日本語", "htmlLang": "ja", "order": 3}`
   (only the default language keeps `"default": true`).
2. Translate every value.
3. `python _src/build.py`.

The build discovers languages from the filenames, so `control-flex/ja/**` appears,
the header switcher gains the new entry, `hreflang` alternates are added to every
page, and the redirect stubs start honouring `ja`. No template, CSS, or JS change.

## Local preview

```bash
# from the repository root (ifels.github.io)
python -m http.server 8080
# → http://127.0.0.1:8080/control-flex/   (redirects to /zh/ or /en/)
# → http://127.0.0.1:8080/control-flex/zh/guide/getting-started.html
```

## Content sources

- Player-facing features: `cfx` repo `docs/publish/mod-intro.md` (current as of 0.8.9)
- Supported platforms / launchers: `cfx-gamepad-jni` repo `docs/android/` and
  `docs/superpowers/specs/2026-09-19-android-platform-and-sdl-load-design.*.md`
- Supported MC versions / loaders / Java: per-version `cfx-<mc>` repos
  (`gradle.properties`, `versions/*/gradle.properties`, `mcmod.info` / `mods.toml` /
  `fabric.mod.json`)
- Default bindings: `cfx` repo `src/main/resources/controlflex/templates/basic.json`
- Trigger-mode / button tokens: `cfx` repo `TriggerMode.java`, `ButtonId.java`
- Bridge-mod development lives on the wiki page `/modpack/compat/bridge.html`; the source of
  truth for the API itself is the `control-flex-api` repo `docs/{en,zh}/` (getting-started,
  api-reference, plugin-guide, examples)
- Compat JSON field reference: [ControlFlexMC/cfx-compat-configs](https://github.com/ControlFlexMC/cfx-compat-configs)

When the mod's features change, keep this site in sync — the `mod-intro.md` file is the
single source of truth for player-facing behavior.
