#!/usr/bin/env python3
"""Render a foxio-deck-html slide deck to PDF via headless Chromium.

Usage:
    python3 export_pdf.py deck.html [output.pdf]

Requires: pip install playwright --break-system-packages -q && playwright install chromium
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    html_path = Path(sys.argv[1]).resolve()
    out_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else html_path.with_suffix('.pdf')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f'file://{html_path}', wait_until='networkidle', timeout=15000)
        # The deck's own @page{size:1920px 1080px;margin:0} rule drives the
        # page box — prefer_css_page_size lets it win over Playwright's default.
        page.pdf(path=str(out_path), print_background=True, prefer_css_page_size=True)
        browser.close()

    print(f'wrote {out_path}')

if __name__ == '__main__':
    main()
