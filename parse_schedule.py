"""Parse visual schedule worksheets to extract talk entries.

The schedule tabs use a layout where each talk occupies one cell containing:
    Author Name(s)\nTitle of Talk

Column A holds time slots; columns B onward hold parallel session talks.
Header/metadata rows (room names, chairs, session labels) do not contain \n,
so the newline test reliably identifies talk cells.
"""

from config import MIN_TITLE_LENGTH


def fetch_strikethrough_cells(svc, spreadsheet_id, tab_name):
    """Return set of (row, col) 1-indexed tuples that have strikethrough formatting.

    Uses the Sheets API directly since gspread's get_all_values() does not
    return formatting information.
    """
    result = svc.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=[tab_name],
        includeGridData=True,
        fields='sheets.data.rowData.values.userEnteredFormat.textFormat.strikethrough',
    ).execute()

    struck = set()
    for sheet in result.get('sheets', []):
        for grid_data in sheet.get('data', []):
            for row_idx, row_data in enumerate(grid_data.get('rowData', [])):
                for col_idx, cell in enumerate(row_data.get('values', [])):
                    tf = cell.get('userEnteredFormat', {}).get('textFormat', {})
                    if tf.get('strikethrough', False):
                        struck.add((row_idx + 1, col_idx + 1))  # 1-indexed
    return struck


def extract_talks(worksheet, tab_name):
    """Return a list of talk dicts from a visual-schedule worksheet.

    Each dict has:
        tab       – worksheet name
        row       – 1-indexed row in the sheet (for gspread updates)
        col       – 1-indexed column in the sheet
        author    – text before the first newline in the cell
        title     – text after the first newline (may contain further newlines)
        cell_text – full original cell text
    """
    all_values = worksheet.get_all_values()
    talks = []

    for row_idx, row in enumerate(all_values):
        for col_idx, cell in enumerate(row):
            if col_idx == 0:
                # Column A contains time slots, not talks
                continue
            cell = cell.strip()
            if '\n' not in cell:
                continue
            first_nl = cell.index('\n')
            author = cell[:first_nl].strip()
            title = cell[first_nl + 1:].strip()
            if len(title) < MIN_TITLE_LENGTH or not author:
                continue
            talks.append({
                'tab': tab_name,
                'row': row_idx + 1,   # gspread is 1-indexed
                'col': col_idx + 1,
                'author': author,
                'title': title,
                'cell_text': cell,
                'author_in_cell': True,
            })

    return talks


def extract_posters(worksheet, tab_name):
    """Return poster entries from the Poster Session Assignments worksheet.

    Tries table format first (looks for a header row with 'title' and 'author'
    columns). Falls back to the visual-schedule parser if no table header found.
    """
    all_values = worksheet.get_all_values()
    if not all_values:
        return []

    # Try to find a header row in the first 10 rows
    header_idx = None
    headers = []
    for i, row in enumerate(all_values[:10]):
        row_lower = [c.lower().strip() for c in row]
        if any('title' in c for c in row_lower) and any('author' in c for c in row_lower):
            header_idx = i
            headers = row_lower
            break

    if header_idx is not None:
        title_col = next((i for i, h in enumerate(headers) if 'title' in h), None)
        author_col = next((i for i, h in enumerate(headers) if 'author' in h), None)
        posters = []
        for row_idx, row in enumerate(all_values[header_idx + 1:], start=header_idx + 2):
            title = row[title_col].strip() if title_col is not None and title_col < len(row) else ''
            author = row[author_col].strip() if author_col is not None and author_col < len(row) else ''
            if len(title) < MIN_TITLE_LENGTH:
                continue
            posters.append({
                'tab': tab_name,
                'row': row_idx,
                'col': (title_col or 0) + 1,
                'author': author,
                'title': title,
                'cell_text': title,  # title column only; author is in a separate column
                'author_in_cell': False,
            })
        return posters

    # Poster tab uses the same visual format as the talk tabs
    return extract_talks(worksheet, tab_name)
