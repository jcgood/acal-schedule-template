# Conference Schedule Toolkit

A set of Python scripts for building and publishing a mobile-friendly HTML
conference schedule, with abstract PDF links, registration cross-checks, and
a PDF schedule deliverable. Originally developed for ACAL 57 / Bantoid 3
(May 2026, University at Buffalo).

## What you get

- **Live HTML schedule** on GitHub Pages — parallel tracks, collapsible sessions,
  remote/in-person tagging, live Zoom links, abstract PDF links
- **Organizer view** — highlights unregistered presenters and NC (not-confirmed) tags
- **PDF schedule** — print-ready, generated from a separate print HTML rendering;
  stable link via Google Drive
- **Abstract matching** — fuzzy-matches an abstract tracking spreadsheet to
  schedule entries, with manual override support
- **Registration checking** — cross-references presenter names/emails against
  registration CSVs with fuzzy matching

## Prerequisites

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Runtime |
| Google Cloud project | Sheets + Drive API access |
| `credentials.json` | OAuth 2.0 Desktop client (see docs/SETUP.md) |
| `gh` CLI | GitHub Pages publishing |
| `wkhtmltopdf` | PDF generation (must be in PATH) |

## Quickstart

```bash
# 1. Clone / copy this template into a new repo for your conference
git init my-conf-schedule && cd my-conf-schedule
cp -r /path/to/template/* .

# 2. Set up Python environment
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Fill in your config
cp config.example.py config.py
# Edit config.py — replace every 'FILL_IN' value

# 4. Place credentials.json in repo root (see docs/SETUP.md)

# 5. Authenticate gh CLI
gh auth login

# 6. Validate your setup
.venv/bin/python3 conf.py doctor

# 7. Build and publish
.venv/bin/python3 conf.py build
```

## Commands

```
python conf.py build          # fetch sheet → render HTML/PDF → publish to GitHub Pages + Drive
python conf.py match          # fuzzy-match abstracts → matches.csv (review before use)
python conf.py check          # cross-check presenters against registration CSVs
python conf.py roster         # generate unified presenter roster CSV
python conf.py roster --unconfirmed   # list unconfirmed presenters only
python conf.py roster --format email  # output email list by status bucket
python conf.py doctor         # validate config, credentials, and API access
```

Or use the Makefile shortcuts:

```
make build   make check   make match   make doctor
```

## Key files

| File | Purpose |
|------|---------|
| `config.py` | All conference-specific IDs and settings (not committed) |
| `config.example.py` | Template for config.py — all values are 'FILL_IN' |
| `session_folders.csv` | Maps session names to Drive folder IDs |
| `matches.csv` | Fuzzy-match output — review and adjust via overrides.csv |
| `overrides.csv` | Manual match corrections (tab, row, col, abstract_name) |
| `data/` | Input files: abstract xlsx, chair xlsx, Zoom xlsx, registration CSVs |
| `credentials.json` | OAuth client secret — gitignored, never commit |
| `token.json` | Cached OAuth token — gitignored, never commit |

## Further reading

- `docs/SETUP.md` — Google Cloud setup, Drive folder layout, Sheet structure,
  GitHub Pages repo, gh CLI authentication
- `docs/WORKFLOW.md` — The three pipelines in depth: schedule build, abstract
  matching, and presenter communication
- `data/README.md` — Expected format of every input file
