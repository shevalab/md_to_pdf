# Markdown → PDF Converter

This folder contains `md_to_pdf.py` — a reusable script for converting Markdown files to PDF with proper Cyrillic (and other Unicode) support.

## Prerequisites

| Dependency | Install (Debian/Ubuntu) |
|---|---|
| Python 3.8+ | system package |
| `markdown-it-py` | `pip install markdown-it-py` |
| `chromium` or `google-chrome` | `sudo apt install chromium` |

The script auto-detects whichever of `chromium`, `google-chrome`, or `chrome` is available on `PATH`.

## Usage

```bash
# Basic usage — output file will be named after input with .pdf extension
python3 md_to_pdf.py konsultacia.md
# → produces konsultacia.pdf

# Set the document language (auto-detected by default: 'he' for Hebrew, else 'ru')
python3 md_to_pdf.py konsultacia.md --lang uk

# Hebrew Markdown needs no flags — language and right-to-left layout are detected
python3 md_to_pdf.py sefer.md

# Force the direction if detection guesses wrong
python3 md_to_pdf.py sefer.md --dir rtl
python3 md_to_pdf.py report.md --dir ltr

# Both -l and --lang work, and can be combined with an explicit output file
python3 md_to_pdf.py konsultacia.md final.pdf -l en

# Explicit output file name
python3 md_to_pdf.py konsultacia.md output_file.pdf
```

## Language options

The script sets the `lang` attribute on the output HTML/PDF document, plus a
matching `dir` attribute. For left-to-right languages this only affects the
declared document language (used by readers, screen readers, and text
extraction) — it does not change fonts or text, so it is safe to set even for
documents written in other languages. Right-to-left languages additionally flip
the text direction, as described below.

| `--lang` | Language |
|---|---|
| `ru` | Russian (**default**) |
| `uk` | Ukrainian |
| `en` | English |
| `de` | German |
| `fr` | French |
| `es` | Spanish |
| `it` | Italian |
| `pt` | Portuguese |
| `pl` | Polish |
| `kk` | Kazakh |
| `be` | Belarusian |
| `zh` | Chinese |
| `he` | Hebrew (**right-to-left**) |
| `Hebrew`, `iw` | accepted aliases for `he` |

Any valid BCP 47 tag works, e.g. `--lang en-US` or `--lang he-IL`. When
`--lang` is omitted it is auto-detected: `he` for documents detected as
right-to-left, otherwise `ru`.

## Direction options (`--dir`)

| `--dir` | Behaviour |
|---|---|
| `auto` | **default** — RTL when the language is `he`/`iw`, or when the document text is detected as RTL |
| `ltr` | force left-to-right layout |
| `rtl` | force right-to-left layout |

Detection (used by `auto`) inspects the letters of the document: it chooses RTL
when the first strong character is right-to-left or when the text contains more
RTL than LTR letters. A Hebrew document therefore converts correctly even with
no flags and even when it opens with a Latin acronym, while an English document
that merely quotes a few Hebrew words stays left-to-right.

For RTL documents the generated HTML gets `lang`/`dir="rtl"` **and** explicit
`direction: rtl; text-align: right` CSS, so text is right-aligned, list bullets
and numbers sit in the right-hand margin, and table columns run right-to-left.
Code blocks (`pre`/`code`) deliberately stay left-to-right.

## Examples

```bash
# Convert a document in the current folder
python3 md_to_pdf.py ./some_doc.md

# Convert and save to a different directory
python3 md_to_pdf.py ./docs/readme.md /tmp/readme.pdf

# In a script / cron job — omit second arg for default output name
python3 md_to_pdf.py /path/to/report.md
```

## How It Works

1. Markdown is parsed to HTML using `markdown-it-py`.
2. The language and text direction are taken from `--lang`/`--dir`, falling back
   to content detection (Hebrew documents become `lang="he" dir="rtl"`).
3. A styled HTML document is generated (A4 page, decent fonts/sizes); RTL
   documents additionally get explicit right-to-left CSS.
4. Headless Chromium renders the HTML to PDF via `--print-to-pdf`.

## Script Files

| File | Purpose |
|---|---|
| `md_to_pdf.py` | The conversion script (this is the only file you need) |
| `README.md` | This explanation |

## Troubleshooting

- **`chromium not found`**: Install Chromium (`sudo apt install chromium`) or Chrome.
- **`No module named markdown_it`**: Run `pip install markdown-it-py`.
- **Cyrillic characters render as boxes**: Ensure a font like `DejaVu Sans` or `Noto Sans` is installed.
- **Hebrew characters render as boxes**: Ensure a Hebrew font such as `DejaVu Sans`
  (already covers Hebrew) or `Noto Sans Hebrew` is installed
  (`sudo apt install fonts-noto-hebrew`).
