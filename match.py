"""Match schedule entries to abstract tracking records and output matches.csv.

Usage:
    python match.py

Reads:
    - Google Sheet (ACAL_TALKS_TAB, BANTO3D_TALKS_TAB, POSTER_TAB)
    - ACAL_XLSX and BANTO3D_XLSX
    - OVERRIDES_CSV (optional, applied on top of fuzzy matches)

Writes:
    - MATCHES_CSV  (review before running the build)

Workflow:
    1. Run this script and inspect matches.csv.
    2. For any wrong or missing matches, add a row to overrides.csv with the
       correct submission_id.
    3. Re-run this script; overrides take precedence over fuzzy matches.
    4. When satisfied, run: python conf.py build
"""

import os
import csv

import pandas as pd
from rapidfuzz import fuzz, process

import auth
import parse_schedule
import load_abstracts
from config import (
    SHEET_ID, ACAL_TALKS_TAB, BANTO3D_TALKS_TAB, POSTER_TAB,
    MATCHES_CSV, OVERRIDES_CSV, MATCH_THRESHOLD,
)

OUTPUT_FIELDS = [
    'tab', 'row', 'col',
    'schedule_author', 'schedule_title', 'author_in_cell', 'strikethrough',
    'submission_id', 'abstract_name', 'conference',
    'confidence', 'xlsx_title', 'xlsx_authors',
    'notes',
]


def fuzzy_match(query_title, candidates_df, threshold=MATCH_THRESHOLD):
    """Return the best-matching row from candidates_df or None.

    Uses token_sort_ratio so minor word-order differences don't matter.
    """
    if candidates_df.empty:
        return None, 0

    titles = candidates_df['title'].tolist()
    result = process.extractOne(
        query_title,
        titles,
        scorer=fuzz.token_sort_ratio,
        processor=str.lower,
        score_cutoff=threshold,
    )
    if result is None:
        return None, 0

    matched_title, score, idx = result
    return candidates_df.iloc[idx], score


def load_overrides():
    """Return dict mapping (tab, row, col) -> abstract_name from overrides.csv."""
    overrides = {}
    if not os.path.exists(OVERRIDES_CSV):
        return overrides
    with open(OVERRIDES_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['tab'], int(row['row']), int(row['col']))
            overrides[key] = row['abstract_name'].strip()
    return overrides


def build_match_row(entry, xlsx_row, score, notes=''):
    if xlsx_row is not None:
        return {
            'tab': entry['tab'],
            'row': entry['row'],
            'col': entry['col'],
            'schedule_author': entry['author'],
            'schedule_title': entry['title'],
            'author_in_cell': entry.get('author_in_cell', True),
            'strikethrough': entry.get('strikethrough', False),
            'submission_id': xlsx_row['submission_id'],
            'abstract_name': xlsx_row['abstract_name'],
            'conference': xlsx_row['conference'],
            'confidence': round(score, 1),
            'xlsx_title': xlsx_row['title'],
            'xlsx_authors': xlsx_row['authors'],
            'notes': notes,
        }
    return {
        'tab': entry['tab'],
        'row': entry['row'],
        'col': entry['col'],
        'schedule_author': entry['author'],
        'schedule_title': entry['title'],
        'author_in_cell': entry.get('author_in_cell', True),
        'strikethrough': entry.get('strikethrough', False),
        'submission_id': '',
        'abstract_name': '',
        'conference': '',
        'confidence': 0,
        'xlsx_title': '',
        'xlsx_authors': '',
        'notes': notes or 'NO MATCH – review manually',
    }


def main():
    print("Connecting to Google Sheets...")
    gc = auth.sheets_client()
    svc = auth.sheets_service()
    spreadsheet = gc.open_by_key(SHEET_ID)

    print("Loading abstract tracking spreadsheets...")
    abstracts = load_abstracts.load_all()
    name_to_row = abstracts.set_index('abstract_name').to_dict('index')

    print("Loading overrides...")
    overrides = load_overrides()

    all_entries = []

    for tab_name, extractor in [
        (ACAL_TALKS_TAB,    lambda ws: parse_schedule.extract_talks(ws, tab_name)),
        (BANTO3D_TALKS_TAB, lambda ws: parse_schedule.extract_talks(ws, tab_name)),
        (POSTER_TAB,        lambda ws: parse_schedule.extract_posters(ws, tab_name)),
    ]:
        print(f"Parsing '{tab_name}'...")
        ws = spreadsheet.worksheet(tab_name)
        entries = extractor(ws)
        struck = parse_schedule.fetch_strikethrough_cells(svc, SHEET_ID, tab_name)
        for e in entries:
            e['strikethrough'] = (e['row'], e['col']) in struck
        struck_count = sum(1 for e in entries if e['strikethrough'])
        if struck_count:
            print(f"  {struck_count} struck-through (withdrawn) entries found.")
        all_entries += entries

    print(f"Found {len(all_entries)} schedule entries across all tabs.")

    # Pass 1: fuzzy-match every non-override entry, store results by index.
    fuzzy_results = {}  # entry_index -> (matched_row | None, score)
    for i, entry in enumerate(all_entries):
        key = (entry['tab'], entry['row'], entry['col'])
        if key in overrides:
            continue
        matched_row, score = fuzzy_match(entry['title'], abstracts)
        fuzzy_results[i] = (matched_row, score)

    # Pass 2: for each abstract, keep only the highest-confidence match.
    # Overrides are exempt — they always win regardless.
    best_idx_for_abstract = {}  # abstract_name -> entry_index with highest score
    for i, (matched_row, score) in fuzzy_results.items():
        if matched_row is not None:
            aname = matched_row['abstract_name']
            prev = best_idx_for_abstract.get(aname)
            if prev is None or score > fuzzy_results[prev][1]:
                best_idx_for_abstract[aname] = i

    results = []
    no_match_count = 0

    for i, entry in enumerate(all_entries):
        key = (entry['tab'], entry['row'], entry['col'])

        # Overrides take precedence over everything.
        if key in overrides:
            aname = overrides[key]
            if aname in name_to_row:
                xlsx_row = pd.Series(name_to_row[aname])
                xlsx_row['abstract_name'] = aname
                results.append(build_match_row(entry, xlsx_row, 100, notes='OVERRIDE'))
            else:
                minimal_row = pd.Series({
                    'submission_id': '', 'abstract_name': aname,
                    'title': '', 'authors': '', 'modality': '', 'conference': '',
                })
                results.append(build_match_row(entry, minimal_row, 100,
                                               notes=f'OVERRIDE (abstract_name={aname} not in xlsx — check xlsx)'))
            continue

        matched_row, score = fuzzy_results[i]
        if matched_row is not None:
            aname = matched_row['abstract_name']
            if best_idx_for_abstract[aname] == i:
                results.append(build_match_row(entry, matched_row, score))
            else:
                # A different entry scored higher for this abstract.
                best_entry = all_entries[best_idx_for_abstract[aname]]
                no_match_count += 1
                results.append(build_match_row(
                    entry, None, 0,
                    notes=f'DUPLICATE – {aname} better matched to row {best_entry["row"]} "{best_entry["title"][:50]}"',
                ))
        else:
            no_match_count += 1
            results.append(build_match_row(entry, None, 0))

    print(f"Matched: {len(results) - no_match_count}  |  No match: {no_match_count}")

    with open(MATCHES_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(results)

    print(f"Written to {MATCHES_CSV}")
    print()
    print("Next steps:")
    print("  1. Review matches.csv – check confidence scores and matched titles.")
    print("  2. For wrong/missing matches, add rows to overrides.csv and re-run.")
    print("  3. When satisfied, run:  python conf.py build")


if __name__ == '__main__':
    main()
