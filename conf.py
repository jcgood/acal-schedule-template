#!/usr/bin/env python3
"""conf.py — unified CLI for conference schedule tooling.

Usage:
    python conf.py build          # fetch sheet → render → publish
    python conf.py match          # fuzzy-match abstracts → matches.csv
    python conf.py check          # cross-check presenters against registrations
    python conf.py roster         # generate presenter roster CSV
    python conf.py roster --unconfirmed   # list unconfirmed presenters only
    python conf.py roster --format email  # output email list by status bucket
    python conf.py doctor         # validate config, check credentials, verify API access
"""

import argparse
import os
import subprocess
import sys


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def cmd_build(args):
    from schedule.build import build
    build()


def cmd_match(args):
    import match
    match.main()


def cmd_check(args):
    import check_registrations
    check_registrations.main()


def cmd_roster(args):
    import roster
    roster.main(
        unconfirmed_only=args.unconfirmed,
        output_format=args.format,
        conference=args.conference,
    )


def cmd_doctor(args):
    _run_doctor()


# ---------------------------------------------------------------------------
# Doctor: validate setup before first build
# ---------------------------------------------------------------------------

_REQUIRED_CONFIG_KEYS = [
    'SHEET_ID',
    'ACAL_TALKS_TAB',
    'BANTO3D_TALKS_TAB',
    'POSTER_TAB',
    'DRIVE_FOLDER_ID',
    'PLENARY_FOLDER_ID',
    'ACAL_XLSX',
    'BANTO3D_XLSX',
]


def _check(label, ok, detail=''):
    icon = 'PASS' if ok else 'FAIL'
    line = f'  [{icon}] {label}'
    if detail:
        line += f' — {detail}'
    print(line)
    return ok


def _run_doctor():
    print('Running conf.py doctor…\n')
    all_ok = True

    # 1. config.py present and filled in
    config_ok = os.path.exists('config.py')
    all_ok &= _check('config.py exists', config_ok)
    if config_ok:
        try:
            import importlib
            cfg = importlib.import_module('config')
            for key in _REQUIRED_CONFIG_KEYS:
                val = getattr(cfg, key, None)
                filled = val is not None and val != 'FILL_IN' and val != ''
                ok = _check(f'config.{key} is set', filled,
                            f'(current value: {val!r})' if not filled else '')
                all_ok &= ok
        except Exception as e:
            all_ok &= _check('config.py importable', False, str(e))

    # 2. credentials.json present
    creds_ok = os.path.exists('credentials.json')
    all_ok &= _check('credentials.json exists', creds_ok,
                     'download from Google Cloud Console → APIs & Services → Credentials'
                     if not creds_ok else '')

    # 3. Abstract xlsx files present
    for key in ('ACAL_XLSX', 'BANTO3D_XLSX'):
        try:
            import config as cfg_mod
            path = getattr(cfg_mod, key, 'FILL_IN')
            if path and path != 'FILL_IN':
                ok = os.path.exists(path)
                all_ok &= _check(f'{key} file exists ({path})', ok)
        except Exception:
            pass

    # 4. Google Sheets API access
    if config_ok and creds_ok:
        try:
            import auth
            import config as cfg_mod
            gc = auth.sheets_client()
            gc.open_by_key(cfg_mod.SHEET_ID)
            all_ok &= _check('Google Sheets API: can open sheet', True)
        except Exception as e:
            all_ok &= _check('Google Sheets API: can open sheet', False, str(e))
    else:
        print('  [SKIP] Google Sheets API check (config or credentials missing)')

    # 5. Google Drive API access
    if config_ok and creds_ok:
        try:
            import auth
            import config as cfg_mod
            drive_svc = auth.drive_service()
            drive_svc.files().list(
                q=f"'{cfg_mod.DRIVE_FOLDER_ID}' in parents",
                pageSize=1,
                fields='files(id)',
            ).execute()
            all_ok &= _check('Google Drive API: can list abstract folder', True)
        except Exception as e:
            all_ok &= _check('Google Drive API: can list abstract folder', False, str(e))
    else:
        print('  [SKIP] Google Drive API check (config or credentials missing)')

    # 6. gh CLI present and authenticated
    try:
        result = subprocess.run(
            ['gh', 'auth', 'status'],
            capture_output=True, text=True,
        )
        ok = result.returncode == 0
        detail = result.stdout.strip().split('\n')[0] if ok else result.stderr.strip().split('\n')[0]
        all_ok &= _check('gh CLI: authenticated', ok, detail)
    except FileNotFoundError:
        all_ok &= _check('gh CLI: installed', False,
                         'install with: brew install gh  (then: gh auth login)')

    # 7. wkhtmltopdf present (needed for PDF export)
    try:
        result = subprocess.run(
            ['wkhtmltopdf', '--version'],
            capture_output=True, text=True,
        )
        ok = result.returncode == 0
        detail = result.stdout.strip() if ok else 'not found'
        all_ok &= _check('wkhtmltopdf: installed', ok,
                         detail if ok else 'install with: brew install --cask wkhtmltopdf')
    except FileNotFoundError:
        all_ok &= _check('wkhtmltopdf: installed', False,
                         'install with: brew install --cask wkhtmltopdf')

    print()
    if all_ok:
        print('All checks passed. You are ready to run: python conf.py build')
    else:
        print('Some checks failed. Fix the issues above before running the build.')
        sys.exit(1)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser():
    parser = argparse.ArgumentParser(
        prog='conf.py',
        description='Conference schedule tooling — one command for every task',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Examples:\n'
            '  python conf.py doctor              # verify setup before first run\n'
            '  python conf.py build               # fetch → render → publish\n'
            '  python conf.py match               # fuzzy-match abstracts\n'
            '  python conf.py check               # cross-check registrations\n'
            '  python conf.py roster              # write roster.csv\n'
            '  python conf.py roster --unconfirmed\n'
            '  python conf.py roster --format email --conference banto\n'
        ),
    )
    sub = parser.add_subparsers(dest='command', required=True, metavar='COMMAND')

    sub.add_parser('build',
                   help='Fetch sheet → render → publish to GitHub Pages + Drive')

    sub.add_parser('match',
                   help='Fuzzy-match abstracts → matches.csv (review before use)')

    sub.add_parser('check',
                   help='Cross-check presenters against registration CSVs')

    roster_p = sub.add_parser('roster',
                               help='Generate presenter roster CSV or email lists')
    roster_p.add_argument('--unconfirmed', action='store_true',
                           help='Print unconfirmed presenters only (no CSV written)')
    roster_p.add_argument('--format', choices=['csv', 'email'], default='csv',
                           help='Output format: csv (default) or email list')
    roster_p.add_argument('--conference', choices=['all', 'acal', 'banto'], default='all',
                           help='Filter by conference (default: all)')

    sub.add_parser('doctor',
                   help='Validate config, check credentials, verify API access')

    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()

    dispatch = {
        'build':  cmd_build,
        'match':  cmd_match,
        'check':  cmd_check,
        'roster': cmd_roster,
        'doctor': cmd_doctor,
    }
    dispatch[args.command](args)


if __name__ == '__main__':
    main()
