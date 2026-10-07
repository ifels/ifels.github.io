# ControlFlex Wiki

Static documentation site for the [ControlFlex](https://www.curseforge.com/minecraft/mc-mods/control-flex)
Minecraft mod. Served from GitHub Pages at:

**https://ifels.github.io/control-flex/**

No build step: plain HTML + CSS + a small JS file. Push to `main` and GitHub Pages serves it.

## Structure

```
control-flex/
├── index.html               # Landing page (hero, three audiences, versions, quick start)
├── guide/                   # Player Guide
│   ├── getting-started.html #   Install, first launch, templates, default bindings
│   ├── features.html        #   Layers, trigger modes, combos, radial menus, analog, rumble…
│   └── settings.html        #   Settings UI, rebinding, calibration, config paths, FAQ
├── modpack/                 # Modpacks & Compatibility
│   ├── index.html           #   Config layout, override rules, template JSON format
│   └── compat.html          #   Auto-discovery, Mod Adaptation, community configs, compat JSON
├── dev/                     # Developers
│   ├── index.html           #   API quick start (JitPack, availability check, first bridge mod)
│   ├── api-reference.html   #   Full interface reference + threading model
│   └── examples.html        #   Plugin lifecycle + end-to-end examples
└── assets/
    ├── style.css            # All styling (light + dark via prefers-color-scheme)
    └── app.js               # Language switching, mobile sidebar, active nav, copy buttons
```

## Adding a page

1. Copy an existing page in the same section as a starting point.
2. Update `<title>`, the `<h1>`, and the content. Keep the header and sidebar block as-is
   (adjust `../` prefixes if the new page sits at a different depth).
3. Add a link to the sidebar of **every** page (the sidebar is duplicated per page).
4. Write content in both languages — see below.

## Languages

The site currently ships **English (`en`)** and **Chinese (`zh`)**, switchable from the
header dropdown. The preference is stored in `localStorage.preferredLang`, the same key
the root `ifels.github.io` page uses.

Content blocks are marked with `data-lang`:

```html
<div data-lang="zh">…Chinese…</div>
<div data-lang="en">…English…</div>

<p><span data-lang="zh">中文文字</span><span data-lang="en">English text</span></p>
```

Visibility rules hide every `[data-lang]` block whose language is not the active
`<html lang>`.

### Adding a language (e.g. `ja`)

1. `assets/app.js` — add `'ja'` to the `LANGS` array (this injects the visibility rules).
2. Every page header — add `<option value="ja">日本語</option>` to the language `<select>`,
   and add `'ja'` to the inline `S` array in the `<head>` script.
3. Add `<... data-lang="ja">` blocks with the translations next to the existing ones.
4. `assets/style.css` — optionally add a static fallback rule for no-JS visitors:
   `html[lang="ja"] [data-lang]:not([data-lang="ja"]) { display: none !important; }`

## Local preview

```bash
# from the repository root (ifels.github.io)
python -m http.server 8080
# → http://127.0.0.1:8080/control-flex/
```

## Content sources

- Player-facing features: `cfx` repo `docs/publish/mod-intro.md` (current as of 0.8.9)
- Default bindings: `cfx` repo `src/main/resources/controlflex/templates/basic.json`
- Trigger-mode / button tokens: `cfx` repo `TriggerMode.java`, `ButtonId.java`
- Developer docs: `control-flex-api` repo `docs/{en,zh}/` (getting-started, api-reference,
  plugin-guide, examples)
- Compat JSON field reference: [ControlFlexMC/cfx-compat-configs](https://github.com/ControlFlexMC/cfx-compat-configs)

When the mod's features change, keep this site in sync — the `mod-intro.md` file is the
single source of truth for player-facing behavior.
