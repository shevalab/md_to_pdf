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

# Set the document language (default is 'ru')
python3 md_to_pdf.py konsultacia.md --lang uk

# Both -l and --lang work, and can be combined with an explicit output file
python3 md_to_pdf.py konsultacia.md final.pdf -l en

# Explicit output file name
python3 md_to_pdf.py konsultacia.md output_file.pdf
```

## Language options

The script sets the `lang` attribute on the output HTML/PDF document. It only
affects the declared document language (used by readers, screen readers, and
text extraction) — it does not change fonts or text, so it is safe to set even
for documents written in other languages.

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

Any valid BCP 47 tag works, e.g. `--lang en-US`.

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
2. A styled HTML document is generated (A4 page, decent fonts/sizes) with the
   requested `lang` attribute (default `ru`).
3. Headless Chromium renders the HTML to PDF via `--print-to-pdf`.

## Script Files

| File | Purpose |
|---|---|
| `md_to_pdf.py` | The conversion script (this is the only file you need) |
| `README.md` | This explanation |

## Troubleshooting

- **`chromium not found`**: Install Chromium (`sudo apt install chromium`) or Chrome.
- **`No module named markdown_it`**: Run `pip install markdown-it-py`.
- **Cyrillic characters render as boxes**: Ensure a font like `DejaVu Sans` or `Noto Sans` is installed.
