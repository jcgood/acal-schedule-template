"""publish.py — push schedule files to GitHub Pages and Google Drive.

Pushes the following files to the GitHub Pages repo via the Contents API:
  index.html       ← schedule.html
  organizer.html   ← schedule_organizer.html  (if present)
  print.html       ← schedule_print.html
  <PDF_FILE>       ← PDF schedule

Also uploads the PDF to a stable Google Drive file ID so the embed URL
never changes.

Requires `gh` CLI to be authenticated (gh auth login).

Usage:
    python publish.py      # push index.html only
    python conf.py build   # full build + publish pipeline
"""

import base64
import json
import subprocess
import urllib.request
import urllib.error

from config import (
    GITHUB_REPO, PAGES_URL,
    OUTPUT_FILE, ORGANIZER_FILE, PRINT_FILE, PDF_FILE,
    PRESENTATIONS_FOLDER_ID, PDF_DRIVE_FILE_ID,
)

# Derive published URLs from PAGES_URL so there is one place to update.
_base = PAGES_URL.rstrip('/')
ORGANIZER_PAGES_URL = f'{_base}/organizer.html'
PRINT_HTML_URL      = f'{_base}/print.html'
PDF_URL             = f'{_base}/{PDF_FILE}'


# ---------------------------------------------------------------------------
# GitHub Contents API helpers
# ---------------------------------------------------------------------------

def _get_token():
    result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _github_api(method, path, token, data=None):
    url = f'https://api.github.com{path}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code


def _push_file(local_path, remote_path, commit_msg, token):
    with open(local_path, 'rb') as f:
        content = base64.b64encode(f.read()).decode()

    data, status = _github_api('GET', f'/repos/{GITHUB_REPO}/contents/{remote_path}', token)
    sha = data.get('sha') if status == 200 else None

    payload = {'message': commit_msg, 'content': content}
    if sha:
        payload['sha'] = sha

    _, status = _github_api('PUT', f'/repos/{GITHUB_REPO}/contents/{remote_path}', token, payload)
    if status not in (200, 201):
        print(f'Error pushing {remote_path}: HTTP {status}')
        return False
    return True


# ---------------------------------------------------------------------------
# Public publish functions (called from schedule/build.py)
# ---------------------------------------------------------------------------

def publish():
    token = _get_token()
    if _push_file(OUTPUT_FILE, 'index.html', 'Update schedule', token):
        print(f'Published: {PAGES_URL}')


def publish_organizer():
    token = _get_token()
    if _push_file(ORGANIZER_FILE, 'organizer.html', 'Update organizer schedule', token):
        print(f'Published: {ORGANIZER_PAGES_URL}')


def publish_print_html():
    token = _get_token()
    if _push_file(PRINT_FILE, 'print.html', 'Update print schedule', token):
        print(f'Published: {PRINT_HTML_URL}')


def publish_pdf():
    token = _get_token()
    if _push_file(PDF_FILE, PDF_FILE, 'Update schedule PDF', token):
        print(f'Published: {PDF_URL}')


def publish_pdf_to_drive():
    """Upload or update the PDF schedule in Drive, keeping a stable file ID."""
    import auth
    from googleapiclient.http import MediaFileUpload

    svc   = auth.drive_service()
    media = MediaFileUpload(PDF_FILE, mimetype='application/pdf', resumable=False)

    if PDF_DRIVE_FILE_ID:
        svc.files().update(fileId=PDF_DRIVE_FILE_ID, media_body=media).execute()
        url = f'https://drive.google.com/file/d/{PDF_DRIVE_FILE_ID}/view'
        print(f'Published to Drive: {url}')
    else:
        meta = {'name': PDF_FILE, 'parents': [PRESENTATIONS_FOLDER_ID]}
        f = svc.files().create(body=meta, media_body=media, fields='id').execute()
        file_id = f['id']
        url = f'https://drive.google.com/file/d/{file_id}/view'
        print(f'Created Drive PDF: {url}')
        print(f"  → Add to config.py: PDF_DRIVE_FILE_ID = '{file_id}'")


if __name__ == '__main__':
    publish()
