# Elemental Netball — SVG Specification & Cheat Sheet

> Reference for all SVG asset production. Apply to every file before committing.
> Run `python src/repair_svgs.py --dry-run` to audit compliance programmatically.

> **Status:** Existing assets in `assets/svg/` are being rebuilt in Figma against
> this spec. Until the rebuild ships, `repair_svgs.py` is the bridge that brings
> the legacy Illustrator exports into compliance. Once Figma exports replace
> them, the script becomes optional.

---

## 1. Colour Mode & Palette

### Illustrator document settings

| Setting | Value |
|---|---|
| Colour mode | **RGB** (File > Document Colour Mode > RGB Colour) |
| Colour profile | **sRGB IEC61966-2.1** (Edit > Assign Profile) |
| Units | **Pixels** (Preferences > Units > General: Pixels) |

> Never use CMYK — these assets are screen-only. CMYK hex values round differently and will produce off-brand colours.

---

### Design system palette

| Token | Hex | Shorthand | Use |
|---|---|---|---|
| Blue | `#0052b3` | `#0052b3` | GD Fire, GA Ice, court fill |
| Orange | `#ef6d22` | `#ef6d22` | GA Fire, GD Ice, hot end of spectrum |
| Purple | `#663399` | `#639` | GK Fire, GS Ice, cold end of spectrum |
| Red | `#cc3333` | `#c33` | GS Fire, GK Ice, max heat |
| Teal | `#009999` | `#099` | WD Fire, WA Ice |
| Yellow | `#ffaa00` | `#fa0` | WA Fire, WD Ice |
| Green | `#009933` | `#093` | C (Centre), mid-spectrum |
| White | `#ffffff` | `#fff` | Bib backgrounds, text on dark fill |
| Outline | `#1a1a1a` | — | Court lines, borders |
| Bib outline | `#b3b3b3` | — | Neutral grey contrast stroke on Fire bib frames (replaces the old darker-hue contrast pattern) |

Use the 3-character shorthand in SVG source — it renders identically and keeps files smaller.

---

### The spectrum is the positional identity system

The same seven-colour spectrum serves double duty: it maps performance intensity on heatmaps AND encodes court position. Warm colours = attacking end; cool colours = defensive end. The two teams are mirror images of each other on the spectrum.

```
Court position:  GS    GA    WA    C     WD    GD    GK
                 ↑ attacking end              defending end ↓

Fire Team:      #c33  #ef6d22  #fa0  #093  #099  #0052b3  #639
                 red  orange yellow green teal  blue purple

Ice Team:       #639  #0052b3  #099  #093  #fa0  #ef6d22  #c33
                purple blue  teal  green yellow orange red
```

**Key rule: every matchup pair shares a hue.** GS Fire (red filled) always plays GK Ice (red outlined). GA Fire (orange filled) always plays GD Ice (orange outlined). Colour identifies the matchup pair; Fire/Ice treatment (filled vs outlined) identifies the team within it.

This means colour blindness is not a concern for matchup reading — you never need to distinguish two different colours to identify a pair. You compare filled vs outlined of the same colour, plus positional labels and layout.

### Zone / performance gradient

The same spectrum, rendered as a continuous gradient for heatmaps and thermometers. Always runs cold (low) to hot (high):

```
#639  →  #0052b3  →  #099  →  #093  →  #fa0  →  #ef6d22  →  #c33
purple   blue    teal   green  yellow  orange   red
(cold)                                            (hot)
```

Gradient stops at offsets: 0.05 / 0.20 / 0.35 / 0.50 / 0.65 / 0.80 / 0.95

---

### Position colour map

| Position | Full name | Fire Team | Ice Team | Matchup pair colour |
|---|---|---|---|---|
| GS | Goal Shooter | Red `#c33` filled | Purple `#639` outlined | shares with GK pair |
| GA | Goal Attack | Orange `#ef6d22` filled | Blue `#0052b3` outlined | shares with GD pair |
| WA | Wing Attack | Yellow `#fa0` filled | Teal `#099` outlined | shares with WD pair |
| C | Centre | Green `#093` filled | Green `#093` outlined | — (no opposition) |
| WD | Wing Defence | Teal `#099` filled | Yellow `#fa0` outlined | shares with WA pair |
| GD | Goal Defence | Blue `#0052b3` filled | Orange `#ef6d22` outlined | shares with GA pair |
| GK | Goal Keeper | Purple `#639` filled | Red `#c33` outlined | shares with GS pair |

**Fire** = filled badge, position colour background, white text.
**Ice** = white background, position colour stroke, position colour text.

---

## 2. Document Setup

### XML declaration
```xml
<?xml version="1.0" encoding="UTF-8"?>
```
Always first line. No BOM.

### Root element
```xml
<svg
  xmlns="http://www.w3.org/2000/svg"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  viewBox="0 0 W H"
  preserveAspectRatio="xMidYMid meet">
```

- Always include `viewBox`. Never use fixed `width`/`height` alone — that breaks responsive scaling.
- `preserveAspectRatio="xMidYMid meet"` for all diagrams that must fit a container without distortion.
- Use `xMidYMid slice` only for full-bleed backgrounds.
- Include `xmlns:xlink` even if no `xlink:href` is currently present — future-proofs for `<use>` patterns.

### Standard viewBox dimensions per asset type

| Asset type | viewBox | Aspect ratio |
|---|---|---|
| Bibs (position icons) | `0 0 100 100` | 1:1 square |
| Thermometers | `0 0 200 800` | 1:4 portrait |
| Courts / Zone diagrams | `0 0 1486 2958` | 1:1.99 portrait |
| Matchup diagrams | `0 0 930 226` | ~4:1 landscape |

> **Thermometer ratio (locked):** The current 1:3.12 export is being retired.
> The Figma rebuild redesigns the body to fit the 1:4 spec (200×800). The
> bulb stays proportional to the new body — do not uniform-scale the legacy
> file to reach 1:4.

> **Current state:** As of May 2026, the exported assets use non-standard dimensions. Run the Illustrator rescale workflow in Section 7 to normalise them, OR wait for the Figma rebuild which targets these dimensions natively.

---

## 3. Styling Rules

### Inline attributes — not `<style>` blocks

Write fill and stroke properties **directly on each element**:

```xml
<!-- CORRECT -->
<rect fill="#0052b3" stroke="#1a1a1a" stroke-width="4"/>

<!-- WRONG — breaks in <img src> if <style> is stripped on export -->
<rect class="cls-2"/>
```

If a `<style>` block must exist (e.g. for `mix-blend-mode` which has no attribute equivalent), **also add inline fallback attributes on every shape it targets**. The repair script enforces this automatically.

### Colour values

Use **literal hex values** — never CSS variables (`var(--pos-gs)` doesn't resolve inside `<img src>`-loaded SVGs):

```xml
fill="#c33"     <!-- correct -->
fill="var(--pos-gs)"  <!-- wrong outside inline-embedded SVG -->
```

Use `fill="currentColor"` only when the SVG is inline-embedded in HTML and you want CSS theming via `color:` on the parent.

### CSS-only properties (keep in `<style>`, no attribute equivalent)

- `isolation: isolate`
- `mix-blend-mode: multiply`

These cannot be written as XML attributes. They must stay in a `<style>` block. Add inline `fill`/`stroke` fallbacks on the same elements so the shape renders even if the CSS is stripped.

---

## 4. IDs and Classes

- **Namespace IDs** to avoid collisions when two SVGs share a page:
  `id="zone-fill-top-third"` not `id="top"`
- **Stable class names** for script-targeted nodes: `.zone-fill`, `.bib-token`
- Remove Illustrator-generated `id="Layer_2"` / `id="Layer_1-2"` from exported files — they are noise and create collisions.

---

## 5. Text

- Font: `font-family="Gamay, 'Work Sans', sans-serif"` with `font-weight` and `font-size` as attributes
- Centre alignment: `text-anchor="middle"` and `dominant-baseline="central"` (not `alignment-baseline`)
- **Convert text to paths** for any asset that ships as a static file outside a webfont-loading context — this applies to all bib files and exported zone diagrams

---

## 6. Strokes

- Add `vector-effect="non-scaling-stroke"` to hairlines (court lines, 1px borders) — prevents stroke fattening at scale
- Default: `stroke-linecap="round"` and `stroke-linejoin="round"` on all stroked paths (brand's soft feel)
- Bib Ice variant stroke: `stroke-width="6"` on the badge border, in the position colour
- Bib Fire variant outer frame: thin neutral grey stroke (`#b3b3b3`) — provides contrast against light backgrounds without competing with the position hue. Replaces the older darker-hue contrast pattern, which produced muddy results on yellow and other warm hues

---

## 7. Filters & Shadows

- Drop shadows: CSS `filter: drop-shadow(0 3px 4px rgba(0,0,0,.22)) drop-shadow(0 1px 1px rgba(0,0,0,.18))` on the container — not inside the SVG
- If using `<filter>` inside SVG, set `filterUnits="userSpaceOnUse"` with explicit `x`, `y`, `width`, `height` to prevent shadow clipping
- No gradients in body content (zone diagrams, thermometer bars) — flat fills only. Gradients are allowed only in the heatmap overlay layer

---

## 8. Transparency

```xml
fill="none"          <!-- correct for empty regions -->
fill="transparent"   <!-- wrong — some renderers stroke the background -->
```

- `pointer-events="none"` on decorative layers; only interactive zones should receive events

---

## 9. Asset-specific Specs

### Bibs (position icons)

```xml
<svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
```
- Square, bib oval centred
- Ship as PNG for product UI; SVG for inline glyph use only
- **Fire**: `fill="<position-hex>"` on badge background, `fill="#fff"` on text
- **Ice**: `fill="#ffffff"` on badge background, `stroke="<position-hex>"` `stroke-width="6"` on border, position colour text

### Court overlays

```xml
<svg viewBox="0 0 1486 2958" preserveAspectRatio="xMidYMid meet">
```
- Position absolutely over the court PNG using the same `preserveAspectRatio`
- Zone fills: named `<rect>` or `<path>` with `class="zone-fill"`, `fill="rgba(0,0,0,0)"` by default
- Toggle with `.allowed` / `.forbidden` CSS classes that override `fill`
- Court lines and circle outlines: `stroke="#1a1a1a"` `stroke-width="4"` `fill="none"`
- Wrap allowed-zone shapes in: `<g id="allowed-zones" fill="<position-hex>" fill-opacity="0.18">`

### Thermometers

```xml
<svg viewBox="0 0 200 800" preserveAspectRatio="xMidYMid meet">
```
- Capsule body: `<rect x="60" y="20" width="80" height="700" rx="40" ry="40">`
- Bulb: `<circle cx="100" cy="740" r="50">`
- Each temperature band = a separate `<rect>` with explicit `y` and `height`, flat fills only — no gradients in the thermometer body

### Zone diagrams (per-colour)

- Reuse court viewBox `0 0 1486 2958`
- Allowed zone highlight: `<g id="allowed-zones" fill="<position-hex>" fill-opacity="0.18">`
- Third lines and circle outlines: `stroke="#1a1a1a"` `stroke-width="4"` `fill="none"`

---

## 10. Illustrator Export Workflow

### Colour setup (once per document)

1. **File > Document Colour Mode > RGB Colour**
2. **Edit > Assign Profile > sRGB IEC61966-2.1**
3. **Preferences > Units > General: Pixels**

### Resizing to standard viewBox (per asset)

Scale factors from current dimensions:

| Asset | Current | Target | Scale |
|---|---|---|---|
| Bibs | ~113 × 113 | 100 × 100 | **88.19%** |
| Courts / Zones | ~356 × 709 | 1486 × 2958 | **417.4%** |
| Thermometers | 86.9 × 271.5 | 200 × 800 | non-uniform — see note |

> **Thermometer note:** Current ratio is 1:3.12; spec is 1:4. Requires a design decision — either redesign the thermometer body to be taller, or update the spec to 200:625 (matching current proportions). Do not uniform-scale — it will distort the bulb.

**Steps:**

1. Press **Shift+O** (Artboard tool) — set W and H in control bar to target values
2. Press **Esc**, then **Ctrl+A** to select all artwork
3. **Object > Transform > Scale** — Uniform, enter scale %, tick **Scale Strokes & Effects**
4. Open **Align** panel (Shift+F7), align to Artboard: centre horizontally + vertically
5. **File > Export As > SVG**

### SVG export settings (critical)

| Setting | Value | Why |
|---|---|---|
| Styling | **Presentation Attributes** | Writes `fill="#0052b3"` directly on elements — prevents blank-on-export bug |
| Font | Convert to Outlines | Removes webfont dependency |
| Images | Embed | Self-contained file |
| Responsive | **ON** | Omits fixed `width`/`height` from root `<svg>` — keeps viewBox-only |
| Preserve Illustrator Editing Capabilities | **OFF** | Removes bloated Illustrator XML namespace |
| Minify | OFF | Keep readable |

> **Presentation Attributes is the single most important setting.** Selecting it means the repair script never needs to be run on your exports — fills and strokes come out as inline attributes from day one.

### Batch export (multiple artboards)

**File > Export As > Export for Screens** — exports all artboards to individual SVGs in one pass with the same settings.

---

## 11. Sanity Checklist

Before committing any SVG:

- [ ] Open as standalone file in browser — renders correctly, no console errors
- [ ] Drop into `<img src="...">` tag — still renders (proves no external CSS dependency)
- [ ] Inline-embed it and apply `color:` change to parent — text/strokes that should re-tint do
- [ ] Scale container to 50% and 200% — strokes don't pixelate, shadows don't clip
- [ ] Search file for `<style>` — if present, every shape it targets also has inline fallback attributes

---

## 12. Programmatic Repair

The repair script handles items 1-7 above automatically for existing assets in `assets/svg/`:

```bash
# Audit all SVGs (no writes)
python src/repair_svgs.py --dry-run

# Write repaired copies to repaired/ directory
python src/repair_svgs.py

# Overwrite originals (backs up to repaired/originals/)
python src/repair_svgs.py --in-place

# Repair specific files only (resolved against assets/svg/)
python src/repair_svgs.py Blue_GA_Ice.svg Orange_GA_Fire.svg
```

The script does **not** handle viewBox dimension normalisation (Section 10) — that requires the Illustrator rescale workflow above, or the Figma rebuild.

**Lifecycle:** This script is a transition tool. Once the Figma design system
ships and assets are re-exported with Presentation Attributes ON (Section 10),
new SVGs will be spec-compliant from day one and repair becomes unnecessary.

---

## 13. Repository layout

```
assets/
  svg/        all SVG sources (bibs, courts, thermometers, matchups, zone diagrams)
  png/        PNG exports for embedding in PDFs (Playwright renders these faster than SVG)
data/         Jinja2 input JSON for each template
templates/    Jinja2 HTML templates (one per PDF type)
styles/       main.css — shared print styles
src/          pipeline + render + extract + repair_svgs
output/       generated PDFs (gitignored)
repaired/     output of repair_svgs.py (gitignored)
```

In data JSON, asset paths are written **relative to the repo root**:

```json
"home_badge_path": "assets/png/Red_GS_Fire.png"
```

`src/render.py` resolves these to `file://` URIs before handing the HTML to Playwright.

---

## 14. Figma export contract

When the design system ships, every Figma component must export under these settings to land spec-compliant in `assets/svg/`:

| Setting | Value | Why |
|---|---|---|
| Format | SVG | — |
| Outline text | **ON** | Removes webfont dependency (Section 5) |
| Include "id" attribute | **OFF** | Strips Figma layer noise from output |
| Include bounding box | OFF | We rely on `viewBox` only (Section 2) |
| Use simplified stroke | OFF | Preserves stroke widths exactly |
| Sizing | 1× | viewBox at design size |

**Frame & layer naming convention:**

- Top-level frame name → file stem on export
  - `bib/gs/fire` → `Bib_GS_Fire.svg`
  - `court/zone/orange` → `Orange_Zone.svg`
  - `thermometer/blue` → `Blue_Thermometer.svg`
- Filenames in `assets/svg/` use **PascalCase with underscores**, no spaces. Configure Figma export with this pattern.
- Layers inside template frames (page-layout designs) name themselves as their Jinja variable:
  - `text/{{ home_player }}` for bound text
  - `slot/{{ matchup.home_badge_path }}` for image placeholders
  - `static/...` for elements the pipeline never replaces

**Tokens (Figma variables → SVG hex):** the seven primitives in Section 1 are the source of truth. Figma variables resolve to literal hex on export so the SVG never references CSS custom properties (Section 3).
