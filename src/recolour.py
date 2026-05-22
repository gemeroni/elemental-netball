"""
recolour.py — Apply hex colour swaps across the whole repo.

Use when the palette is adjusted (e.g. yellow darkened for contrast) and you
need every place that references the old hex updated in one pass.

Targets:
  - styles/*.css        (CSS custom properties)
  - SVG_SPEC.md         (palette tables, gradient stops)
  - data/*.json         (matchup_hex fields, etc.)
  - assets/svg/*.svg    (fill / stroke attributes)

Each swap matches both the 3-char and 6-char form of a hex (e.g. #06c and
#0066cc), case-insensitive.

Mapping format — newline-separated `old=new` lines. Example mapping.txt:

    #f93=#e8920a      # yellow darkened for white-text contrast
    #099=#00807a      # teal nudge

Usage:
    python src/recolour.py mapping.txt              # dry-run, prints diff
    python src/recolour.py mapping.txt --apply      # write changes
    python src/recolour.py --pair "#f93=#e8920a"    # one-off, dry-run
    python src/recolour.py --pair "#f93=#e8920a" --apply
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

TARGET_GLOBS = [
    "styles/*.css",
    "SVG_SPEC.md",
    "README.md",
    "data/*.json",
    "assets/svg/*.svg",
    "templates/*.html",
]


def expand_hex(h: str) -> str:
    """Normalise to 6-char lowercase form. #06C -> #0066cc."""
    h = h.strip().lower()
    if not h.startswith("#"):
        h = "#" + h
    body = h[1:]
    if len(body) == 3:
        body = "".join(c * 2 for c in body)
    if len(body) != 6 or not re.fullmatch(r"[0-9a-f]{6}", body):
        raise ValueError(f"Bad hex: {h}")
    return "#" + body


def shorten_hex(six: str) -> str | None:
    """Return 3-char form if possible, else None. #0066cc -> #06c. #ff5533 -> #f53."""
    body = six[1:]
    if len(body) == 6 and all(body[i] == body[i + 1] for i in (0, 2, 4)):
        return "#" + body[0] + body[2] + body[4]
    return None


def parse_mapping_text(text: str) -> list[tuple[str, str]]:
    """Parse `old=new` per line. Use `//` for comments since `#` starts hex values."""
    pairs: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or "=" not in line:
            continue
        old, new = line.split("=", 1)
        old = old.strip().split()[0]
        new = new.strip().split()[0]
        pairs.append((expand_hex(old), expand_hex(new)))
    return pairs


def patterns_for(old_six: str) -> list[re.Pattern]:
    """Build regex patterns matching every spelling of the old hex."""
    forms = {old_six}
    short = shorten_hex(old_six)
    if short:
        forms.add(short)
    # Match each form case-insensitively, with a non-hex boundary on the right
    # so that "#06c" doesn't accidentally match inside "#06cabc".
    return [
        re.compile(re.escape(form) + r"(?![0-9a-fA-F])", re.IGNORECASE)
        for form in forms
    ]


def replacement_for(new_six: str, original_match: str) -> str:
    """Pick the new hex form (3-char or 6-char) to mirror the original match length."""
    if len(original_match) == 4:  # #abc
        short = shorten_hex(new_six)
        if short:
            return short
        return new_six  # fall back to 6-char if new colour can't shorten
    return new_six


def apply_swaps(text: str, pairs: list[tuple[str, str]]) -> tuple[str, int]:
    """Run all swaps. Returns (new_text, total_replacements)."""
    total = 0
    for old, new in pairs:
        for pat in patterns_for(old):
            def sub(m, _new=new):
                return replacement_for(_new, m.group(0))
            text, n = pat.subn(sub, text)
            total += n
    return text, total


def collect_files() -> list[Path]:
    files: list[Path] = []
    for pattern in TARGET_GLOBS:
        files.extend(sorted(REPO_ROOT.glob(pattern)))
    return [f for f in files if f.is_file()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mapping_file", nargs="?", help="Path to mapping file (lines of old=new)")
    ap.add_argument("--pair", action="append", default=[], help="Inline mapping, e.g. '#f93=#e8920a'. Repeatable.")
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    args = ap.parse_args()

    pairs: list[tuple[str, str]] = []
    if args.mapping_file:
        pairs.extend(parse_mapping_text(Path(args.mapping_file).read_text(encoding="utf-8")))
    for raw in args.pair:
        pairs.extend(parse_mapping_text(raw))

    if not pairs:
        print("No mappings provided. Pass a mapping file or --pair 'old=new'.")
        sys.exit(1)

    print("Mappings:")
    for old, new in pairs:
        print(f"  {old}  ->  {new}")
    print()

    files = collect_files()
    print(f"Scanning {len(files)} file(s)...\n")

    total_changed_files = 0
    total_replacements = 0

    for f in files:
        try:
            original = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new_text, count = apply_swaps(original, pairs)
        if count == 0:
            continue
        total_changed_files += 1
        total_replacements += count
        rel = f.relative_to(REPO_ROOT)
        print(f"  {rel}  ({count} replacement{'s' if count != 1 else ''})")
        if args.apply:
            f.write_text(new_text, encoding="utf-8")

    print()
    if args.apply:
        print(f"Applied {total_replacements} replacement(s) across {total_changed_files} file(s).")
        print("Reminder: PNG assets are binary — re-export them from Illustrator to match.")
    else:
        print(f"Dry-run: would change {total_replacements} occurrence(s) across {total_changed_files} file(s).")
        print("Re-run with --apply to write changes.")


if __name__ == "__main__":
    main()
