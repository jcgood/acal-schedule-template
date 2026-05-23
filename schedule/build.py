"""schedule/build.py — Orchestration: fetch data, parse, render, publish."""

import sys
from datetime import datetime, timezone, timedelta

import auth
import publish
from config import (
    SHEET_ID, DRIVE_FOLDER_ID, PLENARY_FOLDER_ID,
    MATCHES_CSV, ACAL_TALKS_TAB, BANTO3D_TALKS_TAB, POSTER_TAB,
    SESSION_FOLDERS_CSV, CHAIR_XLSX, ZOOM_XLSX,
    OUTPUT_FILE, ORGANIZER_FILE, PRINT_FILE, PDF_FILE,
    NR_TAGS_PUBLIC,
)
from .parse import (
    list_drive_folder, load_match_map, load_struck_set, fetch_grid,
    sync_session_folder_rows, load_folder_map, load_remote_cells,
    load_chair_map, load_zoom_map, load_unregistered_set,
    parse_acal, parse_banto, parse_posters,
)
from .render import build_html
from .render_print import build_print_html

# ---------------------------------------------------------------------------
# Main build entry point
# ---------------------------------------------------------------------------

def build():
    output_file = OUTPUT_FILE
    for arg in sys.argv[1:]:
        if arg.startswith('--output='):
            output_file = arg.split('=', 1)[1]
        elif arg == '--output' and sys.argv.index(arg) + 1 < len(sys.argv):
            output_file = sys.argv[sys.argv.index(arg) + 1]

    print('Authenticating…')
    gc         = auth.sheets_client()
    sheets_svc = auth.sheets_service()
    drive_svc  = auth.drive_service()

    print('Listing Drive folder for abstract PDFs…')
    abstract_url_map = list_drive_folder(drive_svc, DRIVE_FOLDER_ID)
    print(f'  {len(abstract_url_map)} files found.')
    if PLENARY_FOLDER_ID:
        plenary_map = list_drive_folder(drive_svc, PLENARY_FOLDER_ID)
        abstract_url_map.update(plenary_map)
        print(f'  {len(plenary_map)} plenary PDFs found.')

    print(f'Loading {MATCHES_CSV}…')
    match_map  = load_match_map(MATCHES_CSV, abstract_url_map)
    print(f'  {len(match_map)} abstract links resolved.')
    struck_set = load_struck_set(MATCHES_CSV)
    print(f'  {len(struck_set)} struck-through entries.')

    print(f'Fetching "{ACAL_TALKS_TAB}"…')
    acal_grid = fetch_grid(gc, SHEET_ID, ACAL_TALKS_TAB)
    print(f'  {len(acal_grid)} rows.')

    print(f'Fetching "{BANTO3D_TALKS_TAB}"…')
    banto_grid = fetch_grid(gc, SHEET_ID, BANTO3D_TALKS_TAB)
    print(f'  {len(banto_grid)} rows.')

    print(f'Fetching "{POSTER_TAB}"…')
    poster_grid = fetch_grid(gc, SHEET_ID, POSTER_TAB)
    print(f'  {len(poster_grid)} rows.')

    print(f'Syncing {SESSION_FOLDERS_CSV}…')
    sync_session_folder_rows(SESSION_FOLDERS_CSV, acal_grid, banto_grid, poster_grid)
    folder_map = load_folder_map(SESSION_FOLDERS_CSV)
    print(f'  {len(folder_map)} session folder links.')

    print(f'Loading remote cell colors for "{ACAL_TALKS_TAB}"…')
    acal_remote = load_remote_cells(sheets_svc, SHEET_ID, ACAL_TALKS_TAB)
    print(f'  {len(acal_remote)} remote-highlighted cells.')

    print(f'Loading remote cell colors for "{BANTO3D_TALKS_TAB}"…')
    banto_remote = load_remote_cells(sheets_svc, SHEET_ID, BANTO3D_TALKS_TAB)
    print(f'  {len(banto_remote)} remote-highlighted cells.')

    chair_map = load_chair_map(CHAIR_XLSX)
    print(f'  {len(chair_map)} confirmed session chair(s) loaded.')

    zoom_map = load_zoom_map(ZOOM_XLSX)
    print(f'  {len(zoom_map)} Zoom room link(s) loaded.')

    print('Parsing ACAL schedule…')
    acal_events = parse_acal(
        acal_grid, ACAL_TALKS_TAB, match_map, folder_map, struck_set, acal_remote, chair_map
    )

    print('Parsing Banto3d schedule…')
    banto_events = parse_banto(
        banto_grid, BANTO3D_TALKS_TAB, match_map, folder_map, struck_set, banto_remote, chair_map
    )

    print('Parsing poster sessions…')
    poster_sections = parse_posters(poster_grid, POSTER_TAB, match_map, struck_set, folder_map)

    unregistered_set = load_unregistered_set()

    print('Rendering HTML…')
    et   = datetime.now(timezone(timedelta(hours=-4)))
    h    = et.hour % 12 or 12
    ampm = 'AM' if et.hour < 12 else 'PM'
    last_updated = (
        f"{et.strftime('%B')} {et.day}, {et.year} at {h}:{et.strftime('%M')} {ampm} ET"
    )
    page = build_html(
        acal_events, banto_events, poster_sections, last_updated,
        zoom_map=zoom_map,
        nr_set=unregistered_set if NR_TAGS_PUBLIC else None,
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(page)

    n_acal    = sum(1 for e in acal_events   if e['type'] == 'session_block')
    n_banto   = sum(1 for e in banto_events  if e['type'] == 'session_block')
    n_slots   = sum(len(e['time_slots']) for e in acal_events if e['type'] == 'session_block')
    n_posters = sum(len(s['posters']) for s in poster_sections)
    print(f'Done → {output_file}')
    print(f'  ACAL: {n_acal} session blocks, {n_slots} talk slots')
    print(f'  Banto3d: {n_banto} session blocks')
    print(f'  Posters: {n_posters} entries')

    if unregistered_set:
        print(f'Building organizer schedule ({len(unregistered_set)} unregistered talk(s) highlighted)…')
        org_page = build_html(
            acal_events, banto_events, poster_sections, last_updated,
            zoom_map=zoom_map,
            unregistered_set=unregistered_set,
            nr_set=unregistered_set,
        )
        with open(ORGANIZER_FILE, 'w', encoding='utf-8') as f:
            f.write(org_page)
        print(f'Done → {ORGANIZER_FILE}')
    else:
        print('No registration_check.xlsx found — skipping organizer schedule.')

    print('Rendering print schedule…')
    print_page = build_print_html(
        acal_events, banto_events, poster_sections, last_updated, zoom_map=zoom_map
    )
    with open(PRINT_FILE, 'w', encoding='utf-8') as f:
        f.write(print_page)
    print(f'Done → {PRINT_FILE}')

    pdf_ok = False
    try:
        from weasyprint import HTML as WeasyprintHTML
        WeasyprintHTML(filename=PRINT_FILE).write_pdf(PDF_FILE)
        print(f'Done → {PDF_FILE}')
        pdf_ok = True
    except Exception as e:
        print(f'PDF generation failed: {e}')

    print('Publishing to GitHub Pages…')
    publish.publish()
    if unregistered_set:
        publish.publish_organizer()
    publish.publish_print_html()
    if pdf_ok:
        publish.publish_pdf()
        publish.publish_pdf_to_drive()
