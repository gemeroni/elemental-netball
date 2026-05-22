"""
repair_svgs.py — Programmatic repair of elemental-netball SVG assets.

Repairs applied per universal SVG spec:
  1. Inline CSS class properties as direct attributes (fixes blank rendering in <img src>)
  2. Add preserveAspectRatio="xMidYMid meet" to root <svg> if missing
  3. Add xmlns:xlink if missing
  4. Replace fill="transparent" with fill="none"
  5. Add vector-effect="non-scaling-stroke" to stroke-only paths (hairlines)
  6. Add stroke-linecap="round" stroke-linejoin="round" to all stroked paths
  7. Remove bare width/height from root <svg> (keep only viewBox for responsive scaling)

NOT applied (requires coordinate rescaling — designer task):
  - viewBox dimension standardisation (100×100 bibs, 200×800 thermos, 1486×2958 courts)

Usage:
    python src/repair_svgs.py                    # repair all SVGs in assets/svg/ -> repaired/
    python src/repair_svgs.py --in-place         # overwrite originals (back them up first)
    python src/repair_svgs.py --dry-run          # print report, write nothing
    python src/repair_svgs.py Blue_GA_Ice.svg    # repair specific file(s) (resolved against assets/svg/)

Status: transition tool. Once the assets are rebuilt in Figma with the design
system, exports will be spec-compliant from day one and this script can be
retired. See SVG_SPEC.md §10 for the Figma export contract.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

from lxml import etree

REPO_ROOT = Path(__file__).parent.parent
SVG_DIR = REPO_ROOT / "assets" / "svg"
REPAIRED_DIR = REPO_ROOT / "repaired"

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# CSS properties that map directly to SVG presentation attributes
PRESENTATIONAL = {
    "fill", "fill-opacity", "fill-rule",
    "stroke", "stroke-width", "stroke-opacity",
    "stroke-dasharray", "stroke-dashoffset",
    "stroke-linecap", "stroke-linejoin", "stroke-miterlimit",
    "opacity", "clip-path", "clip-rule",
    "color", "display", "visibility", "overflow",
    "font-family", "font-size", "font-style", "font-weight",
    "text-anchor", "dominant-baseline",
    "paint-order", "shape-rendering",
    "filter",
}

# CSS-only properties that cannot be inlined as XML attributes — keep in <style>
CSS_ONLY = {"isolation", "mix-blend-mode", "pointer-events"}


# ── CSS parsing ──────────────────────────────────────────────────────────────

def parse_style_block(css_text: str) -> dict[str, dict[str, str]]:
    """
    Parse CSS class rules from a <style> block.
    Returns {class_name: {property: value, ...}}.
    Handles multi-class selectors (e.g. .cls-1, .cls-2 { ... }).
    """
    rules: dict[str, dict[str, str]] = {}
    block_re = re.compile(r"([.#][\w\s,.-]+?)\s*\{([^}]*)\}", re.MULTILINE | re.DOTALL)

    for match in block_re.finditer(css_text):
        selector_str = match.group(1)
        declarations = match.group(2)

        props: dict[str, str] = {}
        for decl in declarations.split(";"):
            decl = decl.strip()
            if ":" in decl:
                prop, _, val = decl.partition(":")
                props[prop.strip()] = val.strip()

        # Handle comma-separated selectors
        for selector in selector_str.split(","):
            selector = selector.strip().lstrip(".")
            if selector:
                if selector in rules:
                    rules[selector].update(props)
                else:
                    rules[selector] = dict(props)

    return rules


def classes_of(element) -> list[str]:
    """Return list of class names on an element."""
    raw = element.get("class", "")
    return [c for c in raw.split() if c]


# ── Per-element repairs ──────────────────────────────────────────────────────

def inline_css_classes(element, css_rules: dict[str, dict[str, str]]) -> list[str]:
    """
    For each CSS class on the element, apply matching presentational properties
    as inline attributes — only if the element doesn't already have that attribute.
    Returns list of change descriptions.
    """
    changes = []
    for cls in classes_of(element):
        props = css_rules.get(cls, {})
        for prop, val in props.items():
            if prop not in PRESENTATIONAL:
                continue
            if element.get(prop) is None:
                element.set(prop, val)
                changes.append(f"  inlined .{cls} -> {prop}={val!r}")
    return changes


def fix_transparent(element) -> list[str]:
    changes = []
    if element.get("fill") == "transparent":
        element.set("fill", "none")
        changes.append("  fill='transparent' -> fill='none'")
    return changes


def add_non_scaling_stroke(element) -> list[str]:
    """
    Add vector-effect="non-scaling-stroke" to elements that have a visible stroke
    but no fill (or fill="none") — i.e. hairlines.
    Skip if already set.
    """
    changes = []
    has_stroke = element.get("stroke") not in (None, "none")
    fill = element.get("fill", "")
    is_hairline = has_stroke and fill in ("none", "")
    if is_hairline and element.get("vector-effect") is None:
        element.set("vector-effect", "non-scaling-stroke")
        changes.append("  added vector-effect='non-scaling-stroke'")
    return changes


def add_round_caps(element) -> list[str]:
    """Add stroke-linecap/join=round to any stroked path that doesn't already have them."""
    changes = []
    if element.get("stroke") not in (None, "none"):
        if element.get("stroke-linecap") is None:
            element.set("stroke-linecap", "round")
            changes.append("  added stroke-linecap='round'")
        if element.get("stroke-linejoin") is None:
            element.set("stroke-linejoin", "round")
            changes.append("  added stroke-linejoin='round'")
    return changes


# ── Root <svg> repairs ───────────────────────────────────────────────────────

def fix_root(root, filename: str) -> list[str]:
    changes = []

    # Track whether xlink needs adding (handled in write_repaired via string post-processing)
    if "xlink" not in root.nsmap:
        root.set("_needs_xlink", "1")  # sentinel; stripped before writing
        changes.append("  added xmlns:xlink")

    # Add preserveAspectRatio if missing
    if root.get("preserveAspectRatio") is None:
        root.set("preserveAspectRatio", "xMidYMid meet")
        changes.append("  added preserveAspectRatio='xMidYMid meet'")

    # Remove fixed width/height if viewBox is present (keep responsive)
    if root.get("viewBox") is not None:
        for attr in ("width", "height"):
            val = root.get(attr, "")
            # Only remove bare pixel/unit dimensions — keep % values
            if val and not val.endswith("%"):
                del root.attrib[attr]
                changes.append(f"  removed fixed {attr}='{val}' (viewBox present)")

    # Remove Illustrator/Inkscape id noise on root
    if root.get("id", "").startswith("Layer_"):
        del root.attrib["id"]
        changes.append("  removed Illustrator Layer_ id from root <svg>")

    return changes


# ── Main repair routine ──────────────────────────────────────────────────────

SHAPED_TAGS = {
    f"{{{SVG_NS}}}{tag}"
    for tag in ("path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "g")
}


def repair_svg(svg_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """
    Repair a single SVG file.
    Returns (changed: bool, report_lines: list[str]).
    """
    report = [f"\n{svg_path.name}"]

    # Preserve original XML declaration
    raw = svg_path.read_bytes()
    has_xml_decl = raw.lstrip().startswith(b"<?xml")

    parser = etree.XMLParser(remove_blank_text=False, recover=True)
    try:
        tree = etree.parse(str(svg_path), parser)
    except etree.XMLSyntaxError as exc:
        report.append(f"  ERROR: could not parse — {exc}")
        return False, report

    root = tree.getroot()

    # Collect all <style> blocks
    css_rules: dict[str, dict[str, str]] = {}
    for style_el in root.iter(f"{{{SVG_NS}}}style"):
        if style_el.text:
            css_rules.update(parse_style_block(style_el.text))

    any_changes = False

    # Root-level fixes
    root_changes = fix_root(root, svg_path.name)
    if root_changes:
        report.extend(root_changes)
        any_changes = True

    # Walk all elements
    for el in root.iter():
        tag = el.tag
        if not isinstance(tag, str):
            continue  # skip comments / PI nodes

        el_changes: list[str] = []

        if tag in SHAPED_TAGS:
            if css_rules:
                el_changes += inline_css_classes(el, css_rules)
            el_changes += fix_transparent(el)
            el_changes += add_non_scaling_stroke(el)
            el_changes += add_round_caps(el)

        if el_changes:
            any_changes = True
            # Use a short label for the element in the report
            el_id = el.get("id") or el.get("class") or ""
            label = f"<{tag.split('}')[-1]}>{f' [{el_id}]' if el_id else ''}"
            report.append(f"  {label}")
            report.extend(el_changes)

    if not any_changes:
        report.append("  (no changes needed)")

    return any_changes, report


# ── Output helpers ───────────────────────────────────────────────────────────

def write_repaired(svg_path: Path, output_path: Path):
    """Parse, repair, and serialise the SVG to output_path."""
    raw = svg_path.read_bytes()
    has_xml_decl = raw.lstrip().startswith(b"<?xml")

    parser = etree.XMLParser(remove_blank_text=False, recover=True)
    tree = etree.parse(str(svg_path), parser)
    root = tree.getroot()

    css_rules: dict[str, dict[str, str]] = {}
    for style_el in root.iter(f"{{{SVG_NS}}}style"):
        if style_el.text:
            css_rules.update(parse_style_block(style_el.text))

    fix_root(root, svg_path.name)

    for el in root.iter():
        tag = el.tag
        if not isinstance(tag, str) or tag not in SHAPED_TAGS:
            continue
        if css_rules:
            inline_css_classes(el, css_rules)
        fix_transparent(el)
        add_non_scaling_stroke(el)
        add_round_caps(el)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove sentinel attribute before serialising
    needs_xlink = root.get("_needs_xlink") == "1"
    if needs_xlink:
        del root.attrib["_needs_xlink"]

    xml_bytes = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=has_xml_decl,
        encoding="UTF-8",
    )

    # Inject xmlns:xlink with correct prefix (lxml would use ns0)
    if needs_xlink:
        xml_str = xml_bytes.decode("utf-8")
        xlink_decl = 'xmlns:xlink="http://www.w3.org/1999/xlink"'
        # Insert after the SVG namespace declaration
        xml_str = xml_str.replace(
            'xmlns="http://www.w3.org/2000/svg"',
            f'xmlns="http://www.w3.org/2000/svg" {xlink_decl}',
            1,
        )
        xml_bytes = xml_str.encode("utf-8")

    output_path.write_bytes(xml_bytes)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help="SVG files to repair (default: all in assets/svg/)")
    parser.add_argument("--in-place", action="store_true", help="Overwrite originals (backs up to repaired/originals/)")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing anything")
    args = parser.parse_args()

    if args.files:
        svg_files = []
        for f in args.files:
            p = Path(f)
            if not p.is_absolute() and not p.exists():
                p = SVG_DIR / p.name
            svg_files.append(p)
    else:
        svg_files = sorted(SVG_DIR.glob("*.svg"))

    if not svg_files:
        print("No SVG files found.")
        sys.exit(0)

    total = len(svg_files)
    changed = 0
    errors = 0

    print(f"Scanning {total} SVG file(s)…")
    if args.dry_run:
        print("(dry run — no files will be written)\n")

    for svg_path in svg_files:
        if not svg_path.exists():
            print(f"  SKIP (not found): {svg_path}")
            errors += 1
            continue

        has_changes, report = repair_svg(svg_path, dry_run=True)
        print("\n".join(report))

        if has_changes:
            changed += 1
        if has_changes and not args.dry_run:
            if args.in_place:
                backup_dir = REPO_ROOT / "repaired" / "originals"
                backup_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(svg_path, backup_dir / svg_path.name)
                write_repaired(svg_path, svg_path)
                print(f"  -> written in-place (backup: repaired/originals/{svg_path.name})")
            else:
                out_path = REPAIRED_DIR / svg_path.name
                write_repaired(svg_path, out_path)
                print(f"  -> written: repaired/{svg_path.name}")

    print(f"\nDone. {changed}/{total} file(s) {'would be ' if args.dry_run else ''}repaired.")
    if errors:
        print(f"  {errors} error(s) — see above.")


if __name__ == "__main__":
    main()
