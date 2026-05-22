# elemental-netball — Design System Rules for AI Agents

This file tells AI coding agents (Claude Code, etc.) how to work with this project's design system when implementing new assets, templates, or visual changes. The canonical visual spec lives in [SVG_SPEC.md](SVG_SPEC.md) — these rules are the operational shorthand.

## Project shape

- **Elemental Netball is a learning system** that teaches netball positions and matchups through a seven-colour spectrum and two mirror-image teams: **Fire Team** and **Ice Team**. Coach-facing reports (stats, heatmaps) are a secondary surface — primary outputs are educational artefacts (position guide, junior matchup card, team sheet).
- **Not a web app.** This is a Python + Jinja2 + Playwright pipeline that renders HTML/CSS into print-ready PDFs and editable HTML.
- **No React, Vue, Tailwind, or component framework.** "Components" are SVG assets + Jinja2 templates + CSS classes.
- **Design tools**: Figma (canonical), Illustrator (legacy, transitional).

## Repository layout

```
assets/svg/   SVG sources (bibs, courts, thermometers, matchup diagrams, zones)
assets/png/   PNG exports embedded in PDFs (Playwright renders these faster than SVG)
data/         Jinja2 input JSON, one per generated artefact
templates/    Jinja2 HTML templates (.html)
styles/       main.css — shared print stylesheet
src/          pipeline.py, render.py, extract.py, repair_svgs.py, recolour.py, promote.py
output/       generated PDFs + optional .html (gitignored)
repaired/     repair_svgs.py output, plus originals/ backup (gitignored)
```

- IMPORTANT: All assets live in `assets/svg/` or `assets/png/`. **Never** put assets in repo root.
- IMPORTANT: Data JSON paths are written **relative to repo root** (`"assets/png/Red_GS_Fire.png"`) — `src/render.py` resolves them to `file://` URIs before handing to Playwright.

## Design tokens (single source of truth)

The seven-position colour spectrum is the brand. **Never invent new colours.** Always use these tokens:

| Token | Hex | CSS var | Position role |
|---|---|---|---|
| Red | `#c33` | `--red` | GS Fire / GK Ice |
| Orange | `#ef6d22` | `--orange` | GA Fire / GD Ice |
| Yellow | `#fa0` | `--yellow` | WA Fire / WD Ice |
| Green | `#093` | `--green` | C (both teams) |
| Teal | `#099` | `--teal` | WD Fire / WA Ice |
| Blue | `#0052b3` | `--blue` | GD Fire / GA Ice |
| Purple | `#639` | `--purple` | GK Fire / GS Ice |
| Bib outline | `#b3b3b3` | `--bib-outline` | Neutral grey on Fire bib frames |
| Outline | `#1a1a1a` | — | Court lines, borders |

- IMPORTANT: In HTML/CSS, reference colours via the CSS custom properties in `styles/main.css` (`:root` block) — never hardcode hex.
- IMPORTANT: In SVG files, colours **must** be literal hex (CSS vars don't resolve inside `<img src>`-loaded SVGs). See SVG_SPEC.md §3.
- If the palette changes, run `python src/recolour.py --pair "#oldhex=#newhex" --apply` — it swaps across CSS, JSON, MD, and SVG in one pass.

## The Fire Team / Ice Team variant logic

This is non-obvious and easy to get wrong. **Fire Team** and **Ice Team** are canonical proper-noun names — always use them in full when referring to the teams (not bare "Fire" or "Ice"). Bare "Fire" / "Ice" is only OK as a variant adjective ("Fire bib", "Ice variant", "Fire spectrum").

- **Fire Team bib** = filled bib (solid colour rounded rect + thin `#b3b3b3` grey outer frame + white text).
- **Ice Team bib** = white interior + thick (6pt) coloured stroke + coloured text. No grey frame.
- **C (Centre)** is green for both teams. Treatment (filled vs outlined) differs, hue does not.
- **Matchup pair rule**: opposing positions share a hue. GS Fire (red) plays GK Ice (red). GA Fire (orange) plays GD Ice (orange). Etc. See SVG_SPEC.md §1 for the full map.
- **Spectrum direction**:
  - Fire spectrum (attacking → defensive): red → orange → yellow → green → teal → blue → purple
  - Ice spectrum is the reverse: purple → blue → teal → green → yellow → orange → red

## SVG asset conventions

Per SVG_SPEC.md (read it for the long version):

- **viewBox dimensions** (locked):
  - Bibs: `0 0 100 100`
  - Thermometers: `0 0 200 800`
  - Courts / zone diagrams: `0 0 1486 2958`
  - Matchup diagrams: `0 0 930 226`
- IMPORTANT: Always include `xmlns:xlink` and `preserveAspectRatio="xMidYMid meet"` on root `<svg>`.
- IMPORTANT: Use **inline presentation attributes** (`fill="#c33"`), not `<style>` blocks with classes. The repair script enforces this; design tools should be configured to emit it directly.
- IMPORTANT: Remove Illustrator/Figma id noise (`id="Layer_2"`, etc.) before commit.
- Convert all text to outlines on export — bibs ship without webfont dependencies.

## Figma export contract

When exporting any asset from Figma into this repo (see SVG_SPEC.md §14):

| Setting | Value |
|---|---|
| Format | SVG |
| Outline text | ON |
| Include "id" attribute | OFF |
| Include bounding box | OFF |
| Use simplified stroke | OFF |
| Sizing | 1× (viewBox at design size) |

**Frame naming convention** (drives file names on export):
- `bib/<position>/<treatment>` → e.g. `bib/gs/fire` → `Bib_GS_Fire.svg`
- `court/zone/<colour>` → `Orange_Zone.svg`
- `thermometer/<colour>` → `Blue_Thermometer.svg`

**File names**: PascalCase with underscores, no spaces. Example: `Red_GS_Fire.svg`, `Yellow_Thermometer.svg`.

## Figma MCP integration flow

When asked to implement a Figma design in this repo:

1. Run `get_design_context` for the node — get structured representation and any tokens/components mapped.
2. Run `get_screenshot` for visual reference.
3. **Do not import the React+Tailwind output literally.** This project is Python+Jinja2+CSS. Translate manually:
   - Layout primitives → use existing `.junior-grid`, `.junior-row`, `.matchup-card`, `.stats-grid`, `.zone-section` classes in `styles/main.css` first.
   - Tokens → map Figma colour variables to the CSS custom properties in `:root`.
   - Spacing → use `mm` units (this is print, not web). Match existing rhythm (gap `6mm` page-level, `2.5mm` within `.junior-grid`).
4. If the asset is an SVG (bib, diagram, zone overlay), export per the contract above and drop into `assets/svg/`. Then re-export the PNG variant to `assets/png/` for embedding.
5. Run `python src/repair_svgs.py --dry-run` to audit; run without `--dry-run` if changes are listed.
6. Validate against the Figma screenshot for visual parity. Generate a PDF preview:
   ```
   python src/pipeline.py generate --template <name> --data data/<name>.json --keep-html
   ```

## Template conventions

- All page templates extend `base.html`.
- `base.html` provides the page shell (header brand + meta, footer) and a `{% block content %}` slot, plus a `{% block header_meta %}` slot for templates that need a custom header right-side (used by `position_guide`).
- Templates reference assets via path fields in data JSON. The supported keys are listed in `_PATH_KEYS` in `src/render.py` (`home_badge_path`, `away_badge_path`, `our_badge_path`, `opp_badge_path`, `badge_path`, `court_path`, `court_heatmap_path`, `thermometer_path`, `logo_path`). Add new keys to that set if a new template needs them.
- Page sizing is A4 (210×297mm) with 18mm margins, enforced by `@page` and `.page` in `main.css`.

## Matchup pair tint (`--mc`)

When rendering a row that shows a position pair, set `--mc` (matchup colour) on the row element to the shared hue. CSS uses it via `color-mix(in srgb, var(--mc) 6%, transparent)` for backgrounds and `var(--mc) 70%, var(--grey-dark)` for emphasis text.

Example:
```html
<div class="junior-row" style="--mc: {{ matchup.matchup_hex }};">
```

The hex in `matchup_hex` **must** match the shared hue of the bibs in that row. The most common bug in this codebase is mismatched `matchup_hex` (e.g. orange row using yellow tint). See SVG_SPEC.md §1 for the pair map.

## Generating output

```bash
python src/pipeline.py generate --template <name> --data <data.json>             # PDF only
python src/pipeline.py generate --template <name> --data <data.json> --keep-html # PDF + editable HTML alongside
python src/pipeline.py templates                                                  # list templates
```

- PDFs from Playwright are **vector** — editable in Illustrator with layers preserved.
- The `--keep-html` flag saves the rendered HTML for direct editing in a browser or text editor.

## Style rules

- IMPORTANT: **No em-dashes** in any file content (per global user rule). Use a hyphen (`-`) or rephrase with a full stop.
- Inter is the brand font, loaded from Google Fonts in `main.css`. Bibs convert text to outlines so they don't need the font installed.
- Comments in Python and CSS should explain *why* a rule exists when it's non-obvious (e.g. why repair_svgs.py exists, why `set_content()` won't work in Playwright).

## Things that look reasonable but are wrong

- Putting SVGs or PNGs in repo root → no, always under `assets/`.
- Using `<style>` blocks in SVGs → no, inline attributes only (SVG_SPEC.md §3).
- Hardcoding hex in CSS → no, use `var(--colourname)`.
- Using `var(--colourname)` in SVGs → no, literal hex (SVG_SPEC.md §3).
- Adding a new colour to the palette → no, the 7-position spectrum is the brand. If a real need arises, update SVG_SPEC.md §1 first and run `recolour.py` to propagate.
- Renaming the existing 14 bib filenames → no, they're referenced by data JSON and downstream tools (`promote.py` has a hardcoded `TARGET_BIBS` set).
