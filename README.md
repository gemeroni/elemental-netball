# Elemental Netball

A learning system for netball. Built around a seven-colour position spectrum that maps each court position to a hue, with two mirror-image teams (**Fire Team** and **Ice Team**) sharing the matchups. Designed so a 7-year-old playing their first season, a parent helping them learn, and a coach running training all see the same visual language.

The pipeline generates print-ready PDFs (and editable HTML) from JSON data via Jinja2 + Playwright.

## What it teaches

- **Which position plays whom** — every matchup pair shares a hue. GS Fire (red) always plays GK Ice (red). Find the colour, find the pair.
- **The seven positions and their roles** — the position guide explains each role in full sentences a child can read with a parent.
- **Which end of the court is which** — the colour spectrum runs warm (attacking) to cool (defensive) for Fire Team, and the reverse for Ice Team.

## Outputs

- `position_guide` — standalone explainer of the system. Two variants:
  - `position_guide_home.json` — HOME GAMES, we play as the **Fire Team** (red → purple)
  - `position_guide_away.json` — AWAY GAMES, we play as the **Ice Team** (purple → red)
- `junior_matchup` — kid-friendly matchup card: bibs + names only, no stats. 1 page, 7 pairs
- `team_sheet` — single-team lineup card for handing to umpires/scorers. 7 positions + reserves + signature blocks
- `matchup_report` — full coach matchup card with stats per pair
- `zone_report` — single-player heatmap + zone breakdown
- `base` — shared shell (header / footer)

## Layout

```
assets/svg/   SVG sources (bibs, courts, thermometers, matchup diagrams, zone overlays)
assets/png/   PNG exports for embedding in PDFs
data/         JSON input for each template
templates/    Jinja2 HTML templates
styles/       main.css — shared print styles
src/          pipeline + render + extract + repair_svgs + recolour + promote
```

## Generate a PDF

```bash
python src/pipeline.py generate --template position_guide --data data/position_guide_home.json
python src/pipeline.py generate --template junior_matchup --data data/junior_matchup_sample.json
python src/pipeline.py generate --template team_sheet     --data data/team_sheet_sample.json
python src/pipeline.py generate --template matchup_report --data data/matchup_sample.json
python src/pipeline.py generate --template zone_report    --data data/zone_sample.json
python src/pipeline.py templates   # list available templates
```

Pass `--keep-html` to also save the rendered HTML alongside the PDF for editing:

```bash
python src/pipeline.py generate --template position_guide --data data/position_guide_home.json --keep-html
# writes output/position_guide_<timestamp>.pdf  AND  output/position_guide_<timestamp>.html
```

## Editing the output

- **PDF in Illustrator** — vector PDF with editable text and shapes. Install Inter (or convert text to outlines first) so type doesn't substitute.
- **HTML in a browser/editor** — pass `--keep-html` and edit text, colours, layout directly. Re-saving doesn't require regenerating; the HTML is the document.
- **Source-side** — change content in `data/*.json`, layout in `templates/*.html`, styles in `styles/main.css`, then regenerate.

## Design system

See [SVG_SPEC.md](SVG_SPEC.md) for the palette, viewBox conventions, bib variant rules and the Figma export contract. See [CLAUDE.md](CLAUDE.md) for the agent-facing rules that codify those conventions.

Run `python src/repair_svgs.py --dry-run` to audit SVGs against the spec.

## Canonical naming

- **Fire Team** and **Ice Team** are the two team identities in this system. Use the full proper-noun form in any user-facing copy. Bare "Fire" / "Ice" is only acceptable as a variant adjective ("Fire bib", "Ice spectrum").
- **Position codes**: GS, GA, WA, C, WD, GD, GK.
- **Position colours**: red, orange, yellow, green, teal, blue, purple — in that spectrum order.

## Decisions locked

- Existing SVGs will be **rebuilt in Figma** against SVG_SPEC.md; `repair_svgs.py` is a transition tool.
- Thermometer aspect ratio is **200×800 (1:4)** — bodies redesigned in the Figma rebuild.
- Asset directory is **`assets/svg/` + `assets/png/`**, no longer flat in repo root.
- C (Centre) keeps both Fire Team / Ice Team variants — same hue, different treatment (filled vs outlined).
- Junior matchup is **1 page, 7 pairs** (one per home-team position).
- Project framing: **learning system first**, coach reports second.
