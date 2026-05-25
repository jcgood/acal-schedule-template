# Workflow Guide

Three main pipelines cover the full conference schedule lifecycle.

---

## Pipeline 1: Schedule build and publish

This is the core loop. Run it whenever the Google Sheet changes.

```bash
.venv/bin/python3 conf.py build
# or: .venv/bin/python3 build_schedule_html.py
```

### What happens

1. **Fetch sheet** — reads all three tabs (talks, co-conference talks, posters)
   from Google Sheets via the API
2. **Sync session folders** — auto-corrects any stale row/col numbers in
   `session_folders.csv` by scanning the sheet for session header rows
3. **Resolve abstract links** — lists the Drive abstracts folder and plenary
   folder to build a filename→URL map; loads `matches.csv` to link each
   schedule entry to its abstract PDF
4. **Parse events** — converts raw sheet cells into structured event dicts
   (title, presenters, location, zoom link, chair, tech coordinator,
   modality, abstract URL, session folder URL)
5. **Render HTML** — generates the public schedule (`schedule.html`), the
   organizer view (`schedule_organizer.html`), and the print version
   (`schedule_print.html`)
6. **Generate PDF** — runs `wkhtmltopdf` on the print HTML to produce the
   PDF schedule
7. **Publish** — pushes all files to GitHub Pages; uploads the PDF to Drive
   (overwriting the stable file ID so embed links don't change)

### Output files

| File | URL |
|------|-----|
| `schedule.html` → `index.html` | `https://you.github.io/my-conf-schedule/` |
| `schedule_organizer.html` → `organizer.html` | `.../organizer.html` |
| `schedule_print.html` → `print.html` | `.../print.html` |
| `CONF-schedule.pdf` | `.../CONF-schedule.pdf` |
| PDF on Drive | stable `drive.google.com/file/d/<PDF_DRIVE_FILE_ID>/view` |

### First PDF upload

On the very first build, `PDF_DRIVE_FILE_ID` is empty. The build creates the
file and prints the new ID. Paste it into `config.py` so all future uploads
update the same file.

### Session auto-collapse behavior

Sessions auto-collapse in the browser when their end time has passed.
The collapse logic is conference-specific: edit the JavaScript in
`schedule/render.py` to set the correct date/time boundaries for your
conference.

### Organizer view

`schedule_organizer.html` shows NC (not confirmed) tags and highlights
presenters who appear to be unregistered. It is published to a separate URL
that you share only with the organizing committee.

---

## Pipeline 2: Abstract matching

Run this whenever the abstract tracking spreadsheet is updated or when new
PDFs are uploaded to Drive.

```bash
.venv/bin/python3 conf.py match
# or: .venv/bin/python3 match.py
```

### What happens

1. Reads the abstract tracking xlsx files (`ACAL_XLSX`, `BANTO3D_XLSX`)
   to get submission IDs, titles, and authors
2. Reads the Google Sheet schedule to get talk titles and presenter names
3. Fuzzy-matches schedule entries to abstract submissions by title
4. Writes `matches.csv` with one row per schedule entry, including a
   confidence score and the matched abstract PDF filename
5. Entries below `MATCH_THRESHOLD` are written with an empty `submission_id`
   for manual review

### Reviewing matches.csv

`matches.csv` is gitignored — it is a working file. Open it and look for:
- Low-confidence matches (score column < 85)
- Entries with empty `submission_id`
- Plenary speakers (their PDFs are not in the main xlsx)

### Fixing wrong matches with overrides.csv

Add rows to `overrides.csv` to correct mistakes:

```csv
tab,row,col,abstract_name
CONF Talks,5,2,CONF042.pdf
Poster Session Assignments,15,1,CONF107.pdf
```

- `tab`: must match the sheet tab name exactly
- `row`, `col`: 1-based row and column in the sheet
- `abstract_name`: the PDF filename in Drive (e.g. `CONF042.pdf`)

For plenary speakers (whose PDFs are not in the abstract xlsx), set
`abstract_name` directly to the filename you uploaded to the Plenaries folder
(e.g. `SpeakerLastname.pdf`).

Re-run `match.py` after editing `overrides.csv`. Then run `build` to
publish the updated links.

### Modality tracking

The ACAL abstract xlsx has a `Modality decision` column (values: In-Person,
Remote, etc.). The co-conference xlsx may not have this column. The matcher
reads it when present and writes modality to `matches.csv`. The schedule
renderer uses this to add remote/in-person tags on each entry.

---

## Pipeline 3: Registration cross-check

Run this periodically to flag unregistered or unpaid presenters.

```bash
.venv/bin/python3 conf.py check
# or: .venv/bin/python3 check_registrations.py
```

### Input files (in data/ or repo root)

| File | Columns | Purpose |
|------|---------|---------|
| `inperson_payments.csv` | `name, email, affiliation, ticket_type, paid, notes` | In-person attendees; flags unpaid |
| `cancelled.csv` | `email, name, note` | Cancellations to exclude from checks |
| Registration export CSV(s) | Name, email, affiliation | All registrants (export from your registration system) |

### What it reports

- Presenters in the schedule with no matching registration record
- Registered presenters whose `paid` field is empty or 'No'
- Registrations flagged as cancelled
- Fuzzy name/email match warnings (possible duplicates or name variants)

### NC (not confirmed) tags

Presenters identified as unregistered receive an NC tag in the organizer view.
The tag flows through from `matches.csv` (the `nc` column) to the HTML renderer.
Update the `nc` column in `matches.csv` manually after resolving cases, then
rebuild to refresh the organizer schedule.

---

## Pipeline 4: Presenter roster (planned)

```bash
.venv/bin/python3 conf.py roster
.venv/bin/python3 conf.py roster --unconfirmed
.venv/bin/python3 conf.py roster --format email
```

Generates a unified CSV of all presenters with name, email, talk/poster,
session, modality, and confirmed status. Useful as a mail-merge source.

The `--unconfirmed` flag outputs only presenters who have not registered.
The `--format email` flag outputs a plain list of email addresses grouped
by status bucket (confirmed in-person, confirmed remote, unconfirmed).

---

## Avoiding character encoding corruption

Non-ASCII characters in author names (accented letters, non-Latin scripts)
are a persistent source of data corruption. This section explains where it
goes wrong and how to prevent it.

### The root cause: Excel's CSV import

The failure mode is: abstract system exports data as UTF-8 CSV → organizer
opens it by double-clicking in Excel → Excel guesses Mac Roman or Windows-1252
→ multi-byte UTF-8 sequences are misread as two separate characters (e.g. `é`
becomes `√©`) → the xlsx is saved with the garbled text baked in → all
downstream scripts inherit the corruption.

**Never open a UTF-8 CSV by double-clicking in Excel.** Always import via
**Data → Get Data → From Text/CSV** and explicitly choose UTF-8. Or use Google
Sheets, which handles UTF-8 correctly on import.

### Preferred approach: keep abstract tracking in Google Sheets

If your abstract submission system can export to Google Sheets directly (or via
CSV import into Sheets), do that instead of maintaining a local xlsx. The
`load_abstracts.py` script already authenticates to Google via OAuth — you can
extend it to read from a Sheets tab rather than a local file, eliminating the
Excel-in-the-middle risk entirely.

### Defense-in-depth: ftfy

`ftfy` ("fixes text for you") detects and repairs the most common mojibake
patterns automatically. Add it to `requirements.txt` and apply it at the top
of `load_abstracts.py`:

```python
from ftfy import fix_text

# After reading the xlsx/csv into a DataFrame:
df = df.map(lambda x: fix_text(x) if isinstance(x, str) else x)
```

This won't fix corruption that has already propagated to downstream files, but
it will silently correct any future cases where an xlsx arrives with encoding
damage. It is safe to run unconditionally — `fix_text` is a no-op on clean text.

### Spotting corruption early

Run `conf.py doctor` and inspect author names in `matches.csv` for sequences
like `√©`, `Ã©`, `â€"`, or `â€˜` — these are reliable signs of mojibake.
Catching them in `matches.csv` (before `conf.py build`) is much cheaper than
hunting them down in a published schedule.

---

## Tips and common tasks

### Updating a single talk's abstract link

1. Find the talk in `matches.csv` (or add a row to `overrides.csv`)
2. Set `abstract_name` to the correct PDF filename
3. Run `conf.py build`

### Moving a talk to a poster (or vice versa)

When a presenter switches from a talk slot to a poster (or back):
1. Update the Google Sheet (remove from talks tab, add to poster tab)
2. Add an entry to `overrides.csv` pointing to the correct abstract PDF,
   using the new tab name and row/col
3. Remove the old entry from `matches.csv` if it still appears
4. Run `conf.py match` then `conf.py build`

The match map is keyed by `(tab_name, normalized_title)`. If the tab changes,
the old match entry no longer resolves — this is intentional.

### Adding a new session folder

1. Create a subfolder in the Drive Presentations folder
2. Add a row to `session_folders.csv`:
   ```
   Session 8A,FOLDER_ID,https://drive.google.com/drive/folders/FOLDER_ID,CONF Talks,,
   ```
3. Run `conf.py build` — row/col are auto-synced

### Rebuilding after a sheet change

Just run `conf.py build`. No manual steps needed unless abstract links
changed (in which case run `match` first).
