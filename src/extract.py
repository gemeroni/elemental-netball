"""
Extract text and structure from an existing PDF using pdfplumber.
Returns a dict ready to pass into a Jinja2 template.
"""

import re
from pathlib import Path

import pdfplumber


def extract(pdf_path: str | Path) -> dict:
    pdf_path = Path(pdf_path)
    result = {
        "source_file": pdf_path.name,
        "pages": [],
        "raw_text": "",
    }

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_data = {
                "page_number": page.page_number,
                "text": page.extract_text() or "",
                "tables": [],
                "words": [],
            }

            # Extract tables if present
            tables = page.extract_tables()
            for table in tables:
                cleaned = [
                    [cell.strip() if cell else "" for cell in row]
                    for row in table
                    if any(cell for cell in row)
                ]
                if cleaned:
                    page_data["tables"].append(cleaned)

            # Word-level data for layout analysis (font size heuristics)
            words = page.extract_words(extra_attrs=["size", "fontname"])
            for w in words:
                page_data["words"].append({
                    "text": w["text"],
                    "x0": round(w["x0"], 1),
                    "top": round(w["top"], 1),
                    "size": round(w.get("size", 0), 1),
                    "font": w.get("fontname", ""),
                })

            result["pages"].append(page_data)
            result["raw_text"] += page_data["text"] + "\n"

    result["structure"] = _infer_structure(result)
    return result


def _infer_structure(extracted: dict) -> dict:
    """
    Heuristic pass: identify headings (large font), body text, and tables.
    Groups lines into logical blocks by font size thresholds.
    """
    structure = {"headings": [], "body_blocks": [], "tables": []}

    for page in extracted["pages"]:
        # Collect tables straight through
        structure["tables"].extend(page["tables"])

        if not page["words"]:
            continue

        sizes = [w["size"] for w in page["words"] if w["size"] > 0]
        if not sizes:
            continue

        median_size = sorted(sizes)[len(sizes) // 2]
        heading_threshold = median_size * 1.4

        current_block: list[str] = []
        current_top = None

        for word in page["words"]:
            if word["size"] >= heading_threshold:
                if current_block:
                    structure["body_blocks"].append(" ".join(current_block))
                    current_block = []
                structure["headings"].append(word["text"])
            else:
                # Group words on the same line (within 2pt vertical tolerance)
                if current_top is None or abs(word["top"] - current_top) <= 2:
                    current_block.append(word["text"])
                else:
                    if current_block:
                        structure["body_blocks"].append(" ".join(current_block))
                    current_block = [word["text"]]
                current_top = word["top"]

        if current_block:
            structure["body_blocks"].append(" ".join(current_block))

    return structure


def extract_fixture_draw(pdf_path: str | Path) -> list[dict]:
    """
    Specialised extractor for competition fixture draws.
    Looks for round/date/team patterns and returns a list of fixtures.
    """
    extracted = extract(pdf_path)
    fixtures = []

    round_pattern = re.compile(r"round\s*(\d+)", re.IGNORECASE)
    date_pattern = re.compile(
        r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\w+\s+\d{1,2}\s+\w+\s+\d{4})"
    )

    current_round = None
    current_date = None

    for line in extracted["raw_text"].splitlines():
        line = line.strip()
        if not line:
            continue

        round_match = round_pattern.search(line)
        if round_match:
            current_round = int(round_match.group(1))
            continue

        date_match = date_pattern.search(line)
        if date_match:
            current_date = date_match.group(0)
            continue

        # Try to detect "Team A vs Team B" or "Team A d Team B"
        vs_match = re.match(r"(.+?)\s+(?:vs?\.?|def\.?|d)\s+(.+)", line, re.IGNORECASE)
        if vs_match:
            fixtures.append({
                "round": current_round,
                "date": current_date,
                "home": vs_match.group(1).strip(),
                "away": vs_match.group(2).strip(),
            })

    return fixtures


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: python extract.py <path/to/file.pdf>")
        sys.exit(1)
    data = extract(sys.argv[1])
    print(json.dumps(data["structure"], indent=2))
