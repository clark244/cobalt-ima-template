#!/usr/bin/env python3
"""Bundle index.html + styles.css into a single, portable HTML file.

The working copy keeps CSS in styles.css (linked) so index.html stays short and
editable. But a linked relative stylesheet doesn't travel well — emailing the
.html alone, or printing to PDF from a sandboxed context, loses the styles. This
script inlines styles.css back into a <style> block so the output is one
self-contained file with no external assets (except the CDN fonts).

Usage:
    python3 bundle.py                      # -> dist/ima-bundled.html
    python3 bundle.py path/to/output.html  # custom output path

Run it from the repo root. It does not modify index.html or styles.css.

NOTE ON THE PDF BUTTON: the "Download PDF" button does NOT fetch a sibling file.
The PDF export of the final Google Doc is embedded in index.html as base64
(PDF_B64 / PDF_NAME), so it survives bundling intact and needs nothing attached.
This docstring previously described an older sibling-file convention.

NOTE ON SIZE: the bundle carries both the embedded PDF (in index.html) and the
cover banner (a data URI in styles.css), so a bundled file in the 1-2 MB range
is expected, not a mistake.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"
CSS = ROOT / "styles.css"
# Matches the stylesheet link with or without a ?v= cache-busting query.
LINK_RE = re.compile(r'<link rel="stylesheet" href="styles\.css(?:\?[^"]*)?">')


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "ima-bundled.html"

    if not HTML.exists() or not CSS.exists():
        print(f"error: expected {HTML.name} and {CSS.name} next to this script", file=sys.stderr)
        return 1

    html = HTML.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    matches = LINK_RE.findall(html)
    if len(matches) != 1:
        print(f"error: found {len(matches)} stylesheet links in {HTML.name}; expected exactly one\n"
              f'       (looking for <link rel="stylesheet" href="styles.css"> with optional ?v= query)',
              file=sys.stderr)
        return 1

    bundled = LINK_RE.sub(f"<style>\n{css}\n</style>", html, count=1)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(bundled, encoding="utf-8")
    kb = out.stat().st_size / 1024
    print(f"wrote {out} ({kb:.0f} KB, single-file, portable)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
