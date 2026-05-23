# config.py — conference-specific settings
# Copy this file to config.py and fill in every 'FILL_IN' value.
# config.py is gitignored and must never be committed.

# ---------------------------------------------------------------------------
# Conference identity
# ---------------------------------------------------------------------------

CONF_PRIMARY_NAME   = 'FILL_IN'   # e.g. 'ACAL 57'    — main conference tab label
CONF_SECONDARY_NAME = 'FILL_IN'   # e.g. 'Bantoid 3'  — co-conference tab label
CONF_LOCATION       = 'FILL_IN'   # e.g. 'University at Buffalo'
CONF_DATES          = 'FILL_IN'   # e.g. 'May 20–23, 2026'  (used in print header)
ORGANIZER_EMAIL     = 'FILL_IN'   # e.g. 'acal57@buffalo.edu'  (shown in Zoom passcode note)

# Which tab opens by default: 'acal', 'banto', or 'poster'
DEFAULT_TAB = 'acal'

# ---------------------------------------------------------------------------
# Google Sheets
# ---------------------------------------------------------------------------

# The ID from your Google Sheet URL:
#   https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit
SHEET_ID = 'FILL_IN'

# Names of the three tabs in the sheet (must match exactly)
ACAL_TALKS_TAB   = 'FILL_IN'   # e.g. 'ACAL 57 Talks'
BANTO3D_TALKS_TAB = 'FILL_IN'  # e.g. 'Banto3d Talks'  (or your co-conference)
POSTER_TAB       = 'FILL_IN'   # e.g. 'Poster Session Assignments'

# ---------------------------------------------------------------------------
# Google Drive — abstract PDFs
# ---------------------------------------------------------------------------

# ID of the Drive folder containing all uploaded abstract PDFs
# (the folder your abstract managers drop files into)
DRIVE_FOLDER_ID = 'FILL_IN'

# ID of the Drive folder containing plenary speaker PDFs
# (separate from the main abstracts folder)
PLENARY_FOLDER_ID = 'FILL_IN'

# ID of the Drive folder that holds all session subfolders and the PDF schedule
PRESENTATIONS_FOLDER_ID = 'FILL_IN'

# Stable Drive file ID for the PDF schedule.
# Leave as '' on first run; the build will print the new ID after uploading.
# Paste it here so future uploads overwrite the same file (stable embed URL).
PDF_DRIVE_FILE_ID = ''

# ---------------------------------------------------------------------------
# GitHub Pages
# ---------------------------------------------------------------------------

# GitHub repo where the schedule is published (owner/repo format).
# Must have GitHub Pages enabled (Settings → Pages → Branch: main, / root).
GITHUB_REPO = 'FILL_IN'   # e.g. 'myorg/myconf-schedule'
PAGES_URL   = 'FILL_IN'   # e.g. 'https://myorg.github.io/myconf-schedule/'

# ---------------------------------------------------------------------------
# Local input files (in data/ or repo root)
# ---------------------------------------------------------------------------

# Abstract tracking spreadsheets (xlsx) — downloaded from your submission system
ACAL_XLSX    = 'FILL_IN'   # e.g. 'InternalAbstractTracking-NonAnonymous.xlsx'
BANTO3D_XLSX = 'FILL_IN'   # e.g. 'InternalAbstractTracking-NonAnonymous-Banto3d.xlsx'

# Chair/tech coordinator xlsx and Zoom room xlsx
CHAIR_XLSX = 'FILL_IN'   # e.g. 'Session-chair-planning.xlsx'
ZOOM_XLSX  = 'FILL_IN'   # e.g. 'Zoom_master.xlsx'

# Session folder mapping CSV (auto-managed; usually leave as-is)
SESSION_FOLDERS_CSV = 'session_folders.csv'

# Generated output files — do not edit these directly
MATCHES_CSV   = 'matches.csv'
OVERRIDES_CSV = 'overrides.csv'

# OAuth credential files — must be in repo root, never committed
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE       = 'token.json'

# ---------------------------------------------------------------------------
# Abstract tracking xlsx — column names
# ---------------------------------------------------------------------------
# These must match the column headers in ACAL_XLSX / BANTO3D_XLSX exactly.
# They come from your abstract submission system (EasyChair, OpenReview, etc.)

XLSX_ABSTRACT_NAME_COL    = 'Abstract Name'
XLSX_SUBMISSION_ID_COL    = 'Submission ID'
XLSX_TALK_TITLE_COL       = 'Talk Title'
XLSX_CORRESPONDING_AUTHOR = 'Corresponding Author'
XLSX_CORRESPONDING_EMAIL  = 'Corresponding Email'
# Column that records the presenter's intended modality (in-person/remote/online).
# Set to '' if your xlsx has no such column.
XLSX_MODALITY_COL  = 'Modality decision'
# All author columns to check when looking up a co-author as presenter
XLSX_AUTHOR_COLS   = ['Author 1', 'Author 2', 'Author 3', 'Author 4', 'Author 5', 'Additional Authors']

# ---------------------------------------------------------------------------
# Registration platform — column names
# ---------------------------------------------------------------------------
# These must match the column headers in your registration CSV export exactly.
# The values below match Eventbrite's default export format; update them for
# other platforms (RegFox, Cvent, etc.) or if you've customised field names.

# Glob pattern for registration CSV files.
# Files must include a MM.DD.YYYY date in the name; the most recent is used.
REGISTRATIONS_GLOB = 'Conference Registrations *.csv'

# Column(s) containing the registrant's email address.
# List multiple variants if your platform uses different names across exports.
REGISTRATION_EMAIL_COLS = [
    'Email',
]

# Column names for in-person ticket types. Each column whose value is non-empty
# (Eventbrite uses '1') signals that the registrant purchased that ticket.
REGISTRATION_INPERSON_TICKET_COLS = [
    # e.g. 'Ticket: MyConf In-person Registration--General',
    # e.g. 'Ticket: MyConf In-person Registration--Student',
]

# Column names for online/remote ticket types.
REGISTRATION_ONLINE_TICKET_COLS = [
    # e.g. 'Ticket: MyConf Online Registration',
]

# ---------------------------------------------------------------------------
# Build output filenames
# ---------------------------------------------------------------------------

OUTPUT_FILE    = 'schedule.html'
ORGANIZER_FILE = 'schedule_organizer.html'
PRINT_FILE     = 'schedule_print.html'
PDF_FILE       = 'FILL_IN'   # e.g. 'MyConf2026-schedule.pdf'

# Show NC (not-confirmed) presenter tags in the *public* schedule.
# Set False to show them only in the password-protected organizer view.
NR_TAGS_PUBLIC = True

# ---------------------------------------------------------------------------
# Virtual space (Gather.town or similar)
# ---------------------------------------------------------------------------

# Link shown on the poster tab. Leave blank ('') to hide entirely.
GATHER_TOWN_URL  = ''
# Set True while the space is open to attendees so the button turns active.
GATHER_TOWN_LIVE = False

# ---------------------------------------------------------------------------
# Session collapse
# ---------------------------------------------------------------------------

# Last date and end time of your conference (in local conference timezone).
# Sessions that have ended are auto-collapsed while the conference is in
# progress; once this timestamp passes all sessions reopen permanently.
CONF_END_DATE = 'FILL_IN'   # e.g. '2026-05-23'
CONF_END_TIME = 'FILL_IN'   # e.g. '18:30'

# Hours to add to local conference time to get UTC (positive = west of UTC).
# Common values: EDT = 4, CDT = 5, MDT = 6, PDT = 7, BST = -1, CEST = -2
CONF_TZ_TO_UTC_HOURS = 4

# ---------------------------------------------------------------------------
# Matching thresholds
# ---------------------------------------------------------------------------

# Fuzzy match confidence 0–100. Matches below this score go into matches.csv
# as unmatched (submission_id='') for manual review.
MATCH_THRESHOLD = 70

# Minimum character length of the title portion of a schedule cell for it to
# be treated as a talk entry. Filters out "Location TBD", break labels, etc.
MIN_TITLE_LENGTH = 15
