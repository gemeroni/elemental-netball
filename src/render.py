"""
Render a Jinja2 HTML template to PDF using Playwright.

Usage:
    from src.render import render_pdf
    render_pdf("matchup_report", data, "output/matchup.pdf")
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
STYLES_DIR = REPO_ROOT / "styles"
ASSETS_DIR = REPO_ROOT
OUTPUT_DIR = REPO_ROOT / "output"


def render_pdf(
    template_name: str,
    data: dict,
    output_path: str | Path | None = None,
    page_format: str = "A4",
    keep_html: bool = False,
) -> Path:
    """
    Render `template_name` (without .html extension) with `data` and write a PDF.
    Returns the path to the generated PDF.

    When ``keep_html=True``, also writes the rendered HTML next to the PDF using
    the same stem (e.g. ``foo.pdf`` + ``foo.html``). The saved HTML is fully
    editable in any browser/editor; sub-resources (CSS, bibs) are referenced
    by ``file://`` URI so the document is portable as long as those files
    remain at their absolute paths.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    if output_path is None:
        stem = template_name.replace("/", "_")
        output_path = OUTPUT_DIR / f"{stem}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    output_path = Path(output_path)

    # Inject runtime helpers into every template
    data.setdefault("generated_at", datetime.now().strftime("%d %b %Y %H:%M"))
    data["css_path"] = (STYLES_DIR / "main.css").as_uri()
    data["assets_dir"] = ASSETS_DIR.as_uri()

    # Resolve asset paths to file:// URIs so Playwright can load them
    _resolve_asset_paths(data)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    template = env.get_template(f"{template_name}.html")
    html = template.render(**data)

    if keep_html:
        html_path = output_path.with_suffix(".html")
        html_path.write_text(html, encoding="utf-8")

    # Write HTML to a temp file so Chromium loads it with a file:// origin,
    # which allows it to load external file:// CSS and image resources.
    # page.set_content() uses a null origin that blocks file:// sub-resources.
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".html")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(html)
        tmp_uri = Path(tmp_path).as_uri()

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(tmp_uri, wait_until="networkidle")
            page.pdf(
                path=str(output_path),
                format=page_format,
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
    finally:
        os.unlink(tmp_path)

    return output_path


def render_html(template_name: str, data: dict) -> str:
    """Return rendered HTML string (useful for debugging without launching Chromium)."""
    data.setdefault("generated_at", datetime.now().strftime("%d %b %Y %H:%M"))
    data["css_path"] = (STYLES_DIR / "main.css").as_uri()
    data["assets_dir"] = ASSETS_DIR.as_uri()
    _resolve_asset_paths(data)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    return env.get_template(f"{template_name}.html").render(**data)


# ── Asset path resolution ────────────────────────────────────────────────────

_PATH_KEYS = {
    "home_badge_path", "away_badge_path", "court_path",
    "court_heatmap_path", "thermometer_path", "logo_path",
    "fire_badge_path", "ice_badge_path",
    "our_badge_path", "opp_badge_path",
    "badge_path",
}


def _resolve_asset_paths(data: dict) -> None:
    """Walk the data dict and convert any *_path values to file:// URIs."""
    for key, value in data.items():
        if isinstance(value, str) and key in _PATH_KEYS:
            p = Path(value)
            if not p.is_absolute():
                p = ASSETS_DIR / p
            if p.exists():
                data[key] = p.as_uri()
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _resolve_asset_paths(item)
        elif isinstance(value, dict):
            _resolve_asset_paths(value)


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 3:
        print("Usage: python render.py <template_name> <data.json> [output.pdf]")
        sys.exit(1)
    with open(sys.argv[2]) as f:
        payload = json.load(f)
    out = render_pdf(sys.argv[1], payload, sys.argv[3] if len(sys.argv) > 3 else None)
    print(f"Written: {out}")
