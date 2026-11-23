#!/usr/bin/env python3
"""Build docs/index.html from src/dashboard.html with the Thmanyah fonts
embedded inside the page (the font license allows web use only when the
font is packaged into the product, so the raw font files are never
committed to the repository).

Usage: python3 scripts/build_page.py [path/to/thmanyah typeface]
"""
import base64
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = os.path.expanduser("~/Downloads/Thmanyah-Font-Family/thmanyah typeface")
FONTS = [  # (css family, weight, file)
    ("TS", 500, "thmanyahsans/woff2/thmanyahsans-Medium.woff2"),
    ("TS", 700, "thmanyahsans/woff2/thmanyahsans-Bold.woff2"),
    ("TD", 900, "thmanyahserifdisplay/woff2/thmanyahserifdisplay-Black.woff2"),
]


def main():
    font_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    css = []
    for family, weight, rel in FONTS:
        with open(os.path.join(font_dir, rel), "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        css.append('@font-face{font-family:"%s";font-weight:%d;font-display:swap;'
                   'src:url(data:font/woff2;base64,%s) format("woff2")}' % (family, weight, b64))
    with open(os.path.join(ROOT, "src", "dashboard.html"), encoding="utf-8") as f:
        page = f.read().replace("/*FONTS*/", "\n".join(css))
    out = os.path.join(ROOT, "docs", "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote %s (%d KB)" % (out, os.path.getsize(out) // 1024))


if __name__ == "__main__":
    main()
