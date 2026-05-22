"""
CLI orchestrator for the elemental-netball PDF pipeline.

Generate path  (data -> PDF):
    python src/pipeline.py generate --template matchup_report --data data/matchup.json

Ingest path  (existing PDF -> restyled PDF):
    python src/pipeline.py ingest --input path/to/draw.pdf --template fixture_draw

List templates:
    python src/pipeline.py templates
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.extract import extract, extract_fixture_draw
from src.render import render_pdf


def cmd_generate(args):
    with open(args.data) as f:
        data = json.load(f)
    out = render_pdf(args.template, data, args.output or None, keep_html=args.keep_html)
    print(f"PDF written: {out}")
    if args.keep_html:
        print(f"HTML written: {out.with_suffix('.html')}")


def cmd_ingest(args):
    pdf_path = Path(args.input)
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    # Use the specialised fixture extractor if template suggests it
    if "fixture" in args.template.lower():
        fixtures = extract_fixture_draw(pdf_path)
        data = {
            "title": f"Fixture Draw - {pdf_path.stem}",
            "fixtures": fixtures,
            "source_file": pdf_path.name,
        }
    else:
        extracted = extract(pdf_path)
        data = {
            "title": pdf_path.stem,
            "headings": extracted["structure"]["headings"],
            "body_blocks": extracted["structure"]["body_blocks"],
            "tables": extracted["structure"]["tables"],
            "source_file": pdf_path.name,
        }

    if args.dump_json:
        print(json.dumps(data, indent=2))
        return

    out = render_pdf(args.template, data, args.output or None)
    print(f"PDF written: {out}")


def cmd_templates(_args):
    templates_dir = REPO_ROOT / "templates"
    for t in sorted(templates_dir.glob("*.html")):
        if t.stem != "base":
            print(f"  {t.stem}")


def main():
    parser = argparse.ArgumentParser(
        description="elemental-netball PDF pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # generate
    gen = sub.add_parser("generate", help="Generate PDF from JSON data")
    gen.add_argument("--template", required=True, help="Template name (no .html)")
    gen.add_argument("--data", required=True, help="Path to JSON data file")
    gen.add_argument("--output", help="Output PDF path (optional)")
    gen.add_argument("--keep-html", action="store_true", help="Also save the rendered HTML alongside the PDF (editable in any browser/editor)")
    gen.set_defaults(func=cmd_generate)

    # ingest
    ing = sub.add_parser("ingest", help="Restyle an existing PDF")
    ing.add_argument("--input", required=True, help="Source PDF path")
    ing.add_argument("--template", required=True, help="Template name (no .html)")
    ing.add_argument("--output", help="Output PDF path (optional)")
    ing.add_argument("--dump-json", action="store_true", help="Print extracted JSON and exit")
    ing.set_defaults(func=cmd_ingest)

    # templates
    tpl = sub.add_parser("templates", help="List available templates")
    tpl.set_defaults(func=cmd_templates)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
