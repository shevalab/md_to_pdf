#!/usr/bin/env python3
"""Convert a Markdown file to PDF.

Uses markdown-it-py to render Markdown to HTML, then headless Chromium
to print the HTML to PDF. Handles Cyrillic/special characters well.

Usage:
    python3 md_to_pdf.py <input.md> [output.pdf] [-l en]

If output.pdf is omitted, the output file is <input with .pdf extension>.
The language is auto-detected ('he' for Hebrew documents, otherwise 'ru');
use --lang to set it explicitly. Right-to-left documents (Hebrew) are laid out
RTL automatically; use --dir to force the direction.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple

DEFAULT_LANG = "ru"

# Languages advertised by --lang; any other BCP 47 tag is accepted as well.
LANGUAGES = {
    "ru": "Russian",
    "uk": "Ukrainian",
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "kk": "Kazakh",
    "be": "Belarusian",
    "zh": "Chinese",
    "he": "Hebrew",
}

# Languages written right-to-left. Matched on the primary subtag of the tag,
# so regional variants such as "he-IL" are recognised too. "iw" is the
# deprecated ISO code for Hebrew and is still seen in the wild.
RTL_LANGUAGES = {"he", "iw"}

# Language names accepted in place of a code, e.g. --lang Hebrew or --lang iw.
LANGUAGE_ALIASES = {name.lower(): code for code, name in LANGUAGES.items()}
LANGUAGE_ALIASES.update({"iw": "he", "hebrew": "he"})

# Unicode ranges used to guess the direction/language from the document text.
RTL_CHAR_RANGES = (
    (0x0590, 0x05FF),  # Hebrew
    (0x0600, 0x06FF),  # Arabic
    (0x0700, 0x074F),  # Syriac
    (0x0750, 0x077F),  # Arabic Supplement
    (0x0780, 0x07BF),  # Thaana
    (0x07C0, 0x07FF),  # NKo
    (0xFB1D, 0xFB4F),  # Hebrew presentation forms
    (0xFB50, 0xFDFF),  # Arabic presentation forms A
    (0xFE70, 0xFEFF),  # Arabic presentation forms B
)
HEBREW_CHAR_RANGES = ((0x0590, 0x05FF), (0xFB1D, 0xFB4F))

CSS = """
@page {
    size: A4;
    margin: 18mm 16mm;
}
body {
    font-family: "DejaVu Sans", "Noto Sans", "Noto Sans Hebrew", sans-serif;
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

# Appended to CSS for right-to-left documents. Direction and alignment are set
# explicitly (not just inherited from the dir attribute) so the PDF comes out
# right-aligned in every renderer, with list markers in the right-hand gutter.
RTL_CSS = """
body, h1, h2, h3, h4, h5, h6, p, li, blockquote, th, td {
    direction: rtl;
    text-align: right;
}
ul, ol {
    direction: rtl;
    padding-left: 0;
    padding-right: 22px;
}
table {
    direction: rtl;
}
/* Code stays left-to-right even inside RTL documents. */
pre, code {
    direction: ltr;
    text-align: left;
}
"""


def md_to_html(md_text: str) -> str:
    from markdown_it import MarkdownIt
    md = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable("table")
    return md.render(md_text)


def normalize_lang(lang: str) -> str:
    """Reduce a user-supplied language tag to a safe value for the lang attribute."""
    cleaned = "".join(
        c for c in lang.replace("_", "-") if c.isalnum() or c == "-"
    ).strip("-")
    if not cleaned:
        return DEFAULT_LANG
    return LANGUAGE_ALIASES.get(cleaned.lower(), cleaned)


def text_direction(lang: str) -> str:
    """Return 'rtl' for right-to-left languages, 'ltr' otherwise.

    Only the primary subtag is inspected, so 'he-IL' counts as Hebrew.
    """
    primary = normalize_lang(lang).split("-")[0].lower()
    return "rtl" if primary in RTL_LANGUAGES else "ltr"


def scan_scripts(md_text: str) -> Tuple[int, int, int, Optional[str]]:
    """Count RTL/Hebrew/LTR letters and note the first strong direction."""
    rtl = ltr = hebrew = 0
    first_strong = None
    for ch in md_text:
        code = ord(ch)
        if any(lo <= code <= hi for lo, hi in RTL_CHAR_RANGES):
            rtl += 1
            if any(lo <= code <= hi for lo, hi in HEBREW_CHAR_RANGES):
                hebrew += 1
            is_rtl = True
        elif ch.isalpha():
            ltr += 1
            is_rtl = False
        else:
            continue
        if first_strong is None:
            first_strong = "rtl" if is_rtl else "ltr"
    return rtl, ltr, hebrew, first_strong


def detect_rtl(md_text: str) -> bool:
    """Decide from the document text whether it reads right-to-left.

    True when the first strong character is RTL or when the text holds more
    RTL than LTR letters, so predominantly Hebrew documents render RTL even
    when no --lang/--dir is given.
    """
    rtl, ltr, _hebrew, first_strong = scan_scripts(md_text)
    return rtl > 0 and (first_strong == "rtl" or rtl > ltr)


def detect_lang(md_text: str) -> Optional[str]:
    """Guess the language code from the document text; None when unsure.

    Only Hebrew is recognised: RTL documents are declared as Hebrew unless the
    caller states another language.
    """
    _rtl, _ltr, hebrew, _first_strong = scan_scripts(md_text)
    return "he" if hebrew and detect_rtl(md_text) else None


def resolve_direction(direction: str, lang: str, md_text: str) -> str:
    """Turn the --dir setting ('auto' | 'ltr' | 'rtl') into a concrete value."""
    if direction in ("ltr", "rtl"):
        return direction
    if text_direction(lang) == "rtl" or detect_rtl(md_text):
        return "rtl"
    return "ltr"


def render_html(
    title: str,
    md_text: str,
    lang: Optional[str] = None,
    direction: str = "auto",
) -> str:
    body = md_to_html(md_text)
    if lang is None:
        lang = detect_lang(md_text) or DEFAULT_LANG
    lang = normalize_lang(lang)
    direction = resolve_direction(direction, lang, md_text)
    css = CSS + (RTL_CSS if direction == "rtl" else "")
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{direction}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body dir="{direction}">
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
        default=None,
        help=(
            "Language code for the HTML lang attribute. Known codes: "
            f"{', '.join(LANGUAGES)}; any BCP 47 tag works, e.g. en-US. "
            "Auto-detected when omitted ('he' for Hebrew documents, "
            f"otherwise '{DEFAULT_LANG}')"
        ),
    )
    parser.add_argument(
        "-d",
        "--dir",
        choices=("auto", "ltr", "rtl"),
        default="auto",
        help=(
            "Text direction: 'auto' (default) follows --lang and the document "
            "text, so Hebrew documents are laid out right-to-left"
        ),
    )
    args = parser.parse_args(argv)

    md_path = Path(args.input)
    if not md_path.exists():
        parser.error(f"input file not found: {md_path}")
    out_path = Path(args.output) if args.output else md_path.with_suffix(".pdf")

    md_text = md_path.read_text(encoding="utf-8")
    title = md_path.stem

    html_to_pdf(
        render_html(title, md_text, args.lang, args.dir),
        out_path,
    )
    print(f"OK: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())