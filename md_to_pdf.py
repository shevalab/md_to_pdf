#!/usr/bin/env python3
"""Convert a Markdown file to PDF.

Uses markdown-it-py to render Markdown to HTML, then headless Chromium
to print the HTML to PDF. Handles Cyrillic/special characters well.

Usage:
    python3 md_to_pdf.py <input.md> [output.pdf] [-l en]

If output.pdf is omitted, the output file is <input with .pdf extension>.
Language defaults to 'ru'; use --lang to set the document language.
"""

import argparse
import sys
from pathlib import Path

CSS = """
@page {
    size: A4;
    margin: 18mm 16mm;
}
body {
    font-family: "DejaVu Sans", "Noto Sans", sans-serif;
    font-size: 11pt;
    line-height: 1.45;
    color: #1a1a1a;
}
h1 {
    font-size: 17pt;
    border-bottom: 2px solid #333;
    padding-bottom: 6px;
}
h2 {
    font-size: 13.5pt;
    margin-top: 22px;
}
h1, h2 {
    page-break-after: avoid;
}
a {
    color: #1a4d8f;
    text-decoration: none;
    word-break: break-all;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
    font-size: 9.5pt;
}
th, td {
    border: 1px solid #999;
    padding: 6px 8px;
    vertical-align: top;
}
th {
    background: #f0f0f0;
}
tr, .block {
    page-break-inside: avoid;
}
ul, ol {
    padding-left: 22px;
}
li {
    margin-bottom: 4px;
}
hr {
    border: none;
    border-top: 1px solid #999;
    margin: 18px 0;
}
"""


def md_to_html(md_text: str) -> str:
    from markdown_it import MarkdownIt
    md = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable("table")
    return md.render(md_text)


def render_html(title: str, md_text: str, lang: str = "ru") -> str:
    body = md_to_html(md_text)
    lang = "".join(c for c in lang if c.isalnum() or c == "-") or "ru"
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


def find_chromium() -> str:
    import shutil
    for name in ("chromium", "google-chrome", "google-chrome-stable", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    return "chromium"


def html_to_pdf(html: str, out_pdf: Path) -> None:
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8") as f:
        f.write(html)
        f.flush()
        subprocess.run(
            [
                find_chromium(),
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                f"--print-to-pdf={out_pdf}",
                f"file://{f.name}",
            ],
            check=True,
            capture_output=True,
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Path to the input .md file")
    parser.add_argument("output", nargs="?", help="Path to the output .pdf file")
    parser.add_argument(
        "-l",
        "--lang",
        default="ru",
        help="Language code for the HTML lang attribute (default: ru)",
    )
    args = parser.parse_args(argv)

    md_path = Path(args.input)
    if not md_path.exists():
        parser.error(f"input file not found: {md_path}")
    out_path = Path(args.output) if args.output else md_path.with_suffix(".pdf")

    md_text = md_path.read_text(encoding="utf-8")
    title = md_path.stem

    html_to_pdf(render_html(title, md_text, args.lang), out_path)
    print(f"OK: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())