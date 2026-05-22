"""
promote.py — Copy repaired SVGs to NSG-coach-helper Web_Palette.

Source:      elemental-netball/repaired/*.svg
Destination: NSG-coach-helper/colour-temp-position-logic/Web_Palette/

Naming: files already prefixed with EN_ copy as-is; others get EN_ prepended.

Usage:
    python src/promote.py               # copy all target bibs
    python src/promote.py --dry-run     # list what would be copied
    python src/promote.py --check       # diff repaired/ vs Web_Palette (stale/missing)
    python src/promote.py Blue_GA_Ice.svg  # promote specific file(s)
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REPAIRED_DIR = REPO_ROOT / "repaired"
WEB_PALETTE = REPO_ROOT.parent / "NSG-coach-helper" / "colour-temp-position-logic" / "Web_Palette"

# Bibs the app actually loads (BIB dict in colour_temp_interactive.html)
TARGET_BIBS = {
    "Blue_GA_Ice.svg",
    "Blue_GD_Fire.svg",
    "Green_C_Fire.svg",
    "Green_C_Ice.svg",
    "Orange_GA_Fire.svg",
    "Orange_GD_Ice.svg",
    "Purple_GK_Fire.svg",
    "Purple_GS_Ice.svg",
    "Red_GK_Ice.svg",
    "Red_GS_Fire.svg",
    "Teal_WA_Ice.svg",
    "Teal_WD_Fire.svg",
    "Yellow_WA_Fire.svg",
    "Yellow_WD_Ice.svg",
}


def dest_name(src_name: str) -> str:
    """Return the Web_Palette filename for a repaired source filename."""
    if src_name.startswith("EN_"):
        return src_name
    return f"EN_{src_name}"


def cmd_check():
    """Report which repaired assets are stale or missing in Web_Palette."""
    if not WEB_PALETTE.exists():
        print(f"Web_Palette not found: {WEB_PALETTE}")
        sys.exit(1)

    all_clean = True
    for src_name in sorted(TARGET_BIBS):
        src = REPAIRED_DIR / src_name
        dst = WEB_PALETTE / dest_name(src_name)

        if not src.exists():
            print(f"  MISSING from repaired/: {src_name}")
            all_clean = False
        elif not dst.exists():
            print(f"  NOT IN Web_Palette:    {dest_name(src_name)}")
            all_clean = False
        elif src.stat().st_mtime > dst.stat().st_mtime:
            print(f"  STALE in Web_Palette:  {dest_name(src_name)}")
            all_clean = False
        else:
            print(f"  ok  {dest_name(src_name)}")

    if all_clean:
        print("\nAll targets are up to date.")


def cmd_promote(files: list[str], dry_run: bool):
    if not WEB_PALETTE.exists():
        print(f"Web_Palette not found: {WEB_PALETTE}")
        sys.exit(1)

    if files:
        targets = [Path(f).name for f in files]
    else:
        targets = sorted(TARGET_BIBS)

    copied = 0
    skipped = 0
    errors = 0

    for src_name in targets:
        src = REPAIRED_DIR / src_name
        dst = WEB_PALETTE / dest_name(src_name)

        if not src.exists():
            print(f"  SKIP (not in repaired/): {src_name}")
            skipped += 1
            continue

        action = "copy" if not dst.exists() else "overwrite"
        print(f"  {action}: {src_name} -> {dst.name}")
        if not dry_run:
            shutil.copy2(src, dst)
        copied += 1

    label = "would copy" if dry_run else "copied"
    print(f"\n{label} {copied} file(s). {skipped} skipped. {errors} errors.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help="Specific repaired SVG filenames to promote")
    parser.add_argument("--dry-run", action="store_true", help="List what would be copied without writing")
    parser.add_argument("--check", action="store_true", help="Compare repaired/ vs Web_Palette and report status")
    args = parser.parse_args()

    if args.check:
        cmd_check()
    else:
        cmd_promote(args.files, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
