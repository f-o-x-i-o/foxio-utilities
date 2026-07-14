#!/usr/bin/env python3
"""Assemble ordered section fragments into one printable HTML deck.

Usage:
    python3 build.py sections/ style.css out.html

Reads every *.html file in the sections directory (sorted by filename, so
prefix them 00-, 01-, 02-... to control order — that's the whole reordering
mechanism), inlines the given stylesheet into a <style> tag (NOT a <link> —
the assembled file's location differs from the sections/ and style.css
sources, and a linked href breaks under that path mismatch), and writes the
combined HTML. Image paths inside each section (logo-badge.png, fonts/...,
assets/...) are root-relative to wherever out.html ends up, so out.html
must be written alongside fonts/, assets/, and logo-badge.png — see
SKILL.md's canonical project layout. Run export_pdf.py on the result to get
a PDF.
"""
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    sections_dir = Path(sys.argv[1])
    css_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3])

    files = sorted(sections_dir.glob('*.html'))
    if not files:
        print(f'no .html files found in {sections_dir}')
        sys.exit(1)

    body = '\n'.join(f.read_text() for f in files)
    css = css_path.read_text()
    doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
{css}
</style>
</head>
<body>
{body}
</body>
</html>
'''
    out_path.write_text(doc)
    print(f'assembled {len(files)} sections -> {out_path}')
    for f in files:
        print(f'  {f.name}')

if __name__ == '__main__':
    main()
