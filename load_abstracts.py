"""Load abstract tracking spreadsheets into clean DataFrames."""

import pandas as pd

from config import (
    ACAL_XLSX, BANTO3D_XLSX,
    XLSX_SUBMISSION_ID_COL,
    XLSX_ABSTRACT_NAME_COL,
    XLSX_TALK_TITLE_COL,
    XLSX_MODALITY_COL,
    XLSX_AUTHOR_COLS,
)


def _combine_authors(row):
    parts = []
    for col in XLSX_AUTHOR_COLS:
        v = str(row.get(col, '') or '').strip()
        if v and v.upper() != 'NA':
            parts.append(v)
    return ', '.join(parts)


def load_acal():
    """Load ACAL abstract tracking xlsx.

    Returns a DataFrame with columns:
        submission_id, abstract_name, title, authors, modality, conference
    Includes all rows that have a Talk Title (not filtered by decision),
    so that the matcher can find the best candidate regardless of review status.
    """
    df = pd.read_excel(ACAL_XLSX)
    rename = {
        XLSX_SUBMISSION_ID_COL: 'submission_id',
        XLSX_ABSTRACT_NAME_COL: 'abstract_name',
        XLSX_TALK_TITLE_COL:    'title',
    }
    if XLSX_MODALITY_COL:
        rename[XLSX_MODALITY_COL] = 'modality'
    df = df.rename(columns=rename)
    df['authors'] = df.apply(_combine_authors, axis=1)
    df['conference'] = 'ACAL'
    if 'modality' not in df.columns:
        df['modality'] = None
    df = df[df['title'].notna() & (df['title'].str.strip() != '')].copy()
    return df[['submission_id', 'abstract_name', 'title', 'authors', 'modality', 'conference']].reset_index(drop=True)


def load_banto3d():
    """Load Banto3d abstract tracking xlsx.

    Returns same schema as load_acal(); modality column may be absent.
    """
    df = pd.read_excel(BANTO3D_XLSX)
    rename = {
        XLSX_SUBMISSION_ID_COL: 'submission_id',
        XLSX_ABSTRACT_NAME_COL: 'abstract_name',
        XLSX_TALK_TITLE_COL:    'title',
    }
    if XLSX_MODALITY_COL:
        rename[XLSX_MODALITY_COL] = 'modality'
    df = df.rename(columns=rename)
    df['authors'] = df.apply(_combine_authors, axis=1)
    df['conference'] = 'Banto3d'
    if 'modality' not in df.columns:
        df['modality'] = None
    df = df[df['title'].notna() & (df['title'].str.strip() != '')].copy()
    return df[['submission_id', 'abstract_name', 'title', 'authors', 'modality', 'conference']].reset_index(drop=True)


def load_all():
    """Return combined DataFrame from both xlsx files."""
    return pd.concat([load_acal(), load_banto3d()], ignore_index=True)
