"""schedule/debug.py — diagnostics for schedule parsing issues.

Exposed via `python conf.py doctor` (summary) or directly:
    python -m schedule.debug breaks    # coffee/lunch break rows
"""

import re
import sys

from config import SHEET_ID, ACAL_TALKS_TAB


# ---------------------------------------------------------------------------
# Break diagnostics
# ---------------------------------------------------------------------------

def check_breaks(gc, output_file='schedule.html', *, verbose=True):
    """Compare coffee/lunch break rows in the sheet vs. rendered HTML.

    Returns (sheet_breaks, html_breaks) as lists of strings for comparison.
    gc: an authenticated gspread client.
    """
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet(ACAL_TALKS_TAB)
    rows = ws.get_all_values()

    sheet_breaks = []
    for i, row in enumerate(rows):
        col_a = row[0].strip() if row else ''
        col_b = row[1].strip() if len(row) > 1 else ''
        text = col_b.lower()
        if col_a and any(kw in text for kw in ('coffee', 'break', 'lunch')):
            sheet_breaks.append(f'Row {i + 1}: {col_a!r} | {col_b!r}')

    html_breaks = []
    try:
        with open(output_file, encoding='utf-8') as f:
            html = f.read()
        pattern = (
            r'<time class="slot-time">([^<]+)</time>\s*'
            r'<strong class="event-title">(Coffee Break|Lunch Break[^<]*)</strong>'
        )
        for m in re.finditer(pattern, html):
            html_breaks.append(f'{m.group(1)} — {m.group(2)}')
    except FileNotFoundError:
        html_breaks = [f'(file not found: {output_file})']

    if verbose:
        print(f'Coffee/lunch breaks in sheet ({len(sheet_breaks)}):')
        for b in sheet_breaks:
            print(f'  {b}')
        print()
        print(f'Coffee/lunch breaks in schedule HTML ({len(html_breaks)}):')
        for b in html_breaks:
            print(f'  {b}')
        missing = len(sheet_breaks) - len(html_breaks)
        if missing > 0:
            print(f'\nWARNING: {missing} break(s) in sheet but not found in HTML.')

    return sheet_breaks, html_breaks


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Schedule parsing diagnostics')
    sub = parser.add_subparsers(dest='check', required=True)
    bp = sub.add_parser('breaks', help='Compare break rows in sheet vs. rendered HTML')
    bp.add_argument('--output', default='schedule.html',
                    help='Path to rendered schedule.html (default: schedule.html)')
    args = parser.parse_args()

    if args.check == 'breaks':
        import auth
        gc = auth.sheets_client()
        check_breaks(gc, output_file=args.output)


if __name__ == '__main__':
    main()
