# data/

Place all input data files here (or in the repo root, per your preference).
Update the paths in `config.py` if you move them.

None of these files are committed to the repository (they contain
personally identifying information or are gitignored output files).

---

## Required files

### Abstract tracking spreadsheets (xlsx)

Exported from your abstract submission system (e.g. OpenReview, EasyChair).
Configured via `ACAL_XLSX` and `BANTO3D_XLSX` in `config.py`.

Expected columns (exact names may vary — check `match.py`):
- Submission ID (numeric, used to derive the PDF filename, e.g. `CONF042.pdf`)
- Title
- Authors / presenter name
- Modality decision (In-Person / Remote — main conference only)

### Session chair spreadsheet (xlsx)

Configured via `CHAIR_XLSX` in `config.py`.

One row per session. Expected columns:
- Session ID (e.g. `1A`, `2B`)
- Chair name
- Tech coordinator name

### Zoom master spreadsheet (xlsx)

Configured via `ZOOM_XLSX` in `config.py`.

Maps session IDs to Zoom meeting URLs and passcodes.

### Registration export CSV(s)

From your registration system (e.g. Eventbrite, custom form).
Used by `check_registrations.py`.

Expected columns (flexible — the checker uses fuzzy name/email matching):
- Name
- Email
- Affiliation

Place any number of registration CSV exports here; the checker reads all
of them and deduplicates.

---

## Generated / manually maintained files

### matches.csv (gitignored)

Output of `match.py`. One row per schedule entry that was matched to an
abstract PDF. Review this file and fix errors via `overrides.csv`.

Key columns: `tab`, `row`, `col`, `schedule_title`, `abstract_name`,
`submission_id`, `nc`, `strikethrough`, `score`, `modality`

### overrides.csv

Manual corrections to the fuzzy matcher. Committed to the repo.

Columns: `tab`, `row`, `col`, `abstract_name`

Add a row here whenever the matcher gets something wrong. For plenaries
(not in the abstract xlsx), set `abstract_name` directly to the uploaded
PDF filename.

### inperson_payments.csv

Tracks in-person attendees and payment status. Manually maintained.

Columns: `name, email, affiliation, ticket_type, paid, notes`

- `paid`: `Yes` / `No` / empty
- `notes`: free text (e.g. "invoice sent", "comp registration")

### cancelled.csv

Confirmed cancellations. Manually maintained.

Columns: `email, name, note`

Entries here are excluded from the "unregistered" check.

### manual_confirmations.csv

Presenters confirmed via email or other out-of-band method (i.e., they did
not register through the registration system but have confirmed attendance).

Columns: `name, email, note`

The registration checker treats these as confirmed.

---

## session_folders.csv (repo root, committed)

Maps each session name to its Google Drive folder ID.
Auto-synced on each build run (row/col columns are updated automatically).

Columns: `session, folder_id, url, tab, row, col`

You must fill in `session`, `folder_id`, and `url` manually when creating
a new session. The `tab`, `row`, and `col` columns are populated automatically.
