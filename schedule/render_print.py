"""schedule/render_print.py — Print-optimized (single-column, no-JS) schedule rendering."""

import re

from config import CONF_PRIMARY_NAME, CONF_SECONDARY_NAME, CONF_LOCATION, CONF_DATES
from .render import esc, _render_room

_PRINT_HEAD = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{page_title}</title>
<style>
"""

_PRINT_CSS = """\
@page { size: letter portrait; margin: 0.75in; }
.zoom-copy-id { display: none; }
* { box-sizing: border-box; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 9.5pt; line-height: 1.4; color: #111; margin: 0; }
h1 { font-size: 17pt; margin: 0 0 3pt; color: #6A5500; }
.subtitle { font-size: 10pt; color: #555; margin: 0 0 14pt; }
h2.conf-heading { font-size: 13pt; color: #6A5500; border-bottom: 1.5pt solid #A08830;
  padding-bottom: 2pt; margin: 16pt 0 6pt; }
h3.day-heading { font-size: 10.5pt; color: #333; margin: 10pt 0 3pt; }
.event { display: flex; gap: 8pt; margin: 3pt 0; font-size: 9pt; }
.ev-time { min-width: 88pt; color: #555; flex-shrink: 0; }
.ev-body strong { font-weight: 700; }
.ev-body em { font-style: italic; }
.ev-room { color: #666; font-size: 8.5pt; }
.session-block { margin: 6pt 0 10pt; page-break-inside: avoid; }
.session-time { font-size: 9.5pt; font-weight: 700; color: #6A5500; margin: 0 0 3pt; }
.track { margin: 3pt 0 5pt 10pt; border-left: 1.5pt solid #D9C97A; padding-left: 5pt; }
.track-hdr { font-size: 8.5pt; font-weight: 700; color: #333; margin-bottom: 1pt; }
.track-hdr .room { font-weight: 400; color: #666; }
.track-hdr .chair { font-weight: 400; font-style: italic; color: #666; }
.track-hdr .topic { font-weight: 400; font-style: italic; color: #555; }
.talk-row { font-size: 8.5pt; margin: 1.5pt 0; display: flex; gap: 6pt; }
.talk-row .ttime { min-width: 66pt; color: #666; flex-shrink: 0; }
.talk-row .tcontent { }
.talk-author { font-weight: 600; }
.talk-title a { color: #005a9e; text-decoration: none; }
.talk-cancelled .talk-author, .talk-cancelled .talk-title { text-decoration: line-through; color: #999; }
.remote-tag { font-size: 7pt; background: #2B6891; color: white; padding: 0 2pt;
  border-radius: 2pt; vertical-align: middle; }
.poster-section { margin: 6pt 0; page-break-inside: avoid; }
.poster-hdr { font-size: 10pt; font-weight: 700; color: #6A5500; margin: 6pt 0 2pt; }
.poster-loc { font-size: 8.5pt; color: #666; margin: 0 0 3pt; }
.poster-timing { font-size: 8pt; color: #444; margin: 0 0 3pt; }
.poster-table { width: 100%; border-collapse: collapse; font-size: 8pt; }
.poster-table th { background: #EEE8CC; font-weight: 700; text-align: left;
  padding: 2pt 4pt; border: 0.5pt solid #CCC; }
.poster-table td { padding: 2pt 4pt; border: 0.5pt solid #DDD; vertical-align: top; }
.poster-table .num { width: 22pt; }
.poster-table .mod { width: 44pt; }
.poster-cancelled td { text-decoration: line-through; color: #999; }
.last-updated { font-size: 7pt; color: #AAA; margin-top: 12pt; text-align: right; }
"""


def _print_endash(text):
    return re.sub(r'(\d+:\d+)\s*-\s*(\d+)', r'\1–2', text)


def _build_print_event(ev, zoom_map=None):
    details  = ev.get('details', [])
    loc      = details[-1] if details and len(details[-1]) <= 40 else ''
    subtitle = details[0] if len(details) > 1 and details[0] != loc else ''
    url      = ev.get('abstract_url')
    sub_html = ''
    if subtitle:
        linked   = f'<a href="{esc(url)}">{esc(subtitle)}</a>' if url else esc(subtitle)
        sub_html = f' <em>{linked}</em>'
    no_zoom  = zoom_map if 'mixer' not in ev.get('title', '').lower() else None
    loc_html = f' <span class="ev-room">{_render_room(loc, no_zoom)}</span>' if loc else ''
    return (
        f'<div class="event">'
        f'<span class="ev-time">{esc(ev.get("time", ""))}</span>'
        f'<span class="ev-body"><strong>{esc(ev["title"])}</strong>{sub_html}{loc_html}</span>'
        f'</div>'
    )


def _build_print_session_block(ev, zoom_map=None):
    sessions      = ev['sessions']
    time_slots    = ev.get('time_slots', [])
    session_cols  = ev.get('session_cols', [s['sheet_col'] for s in sessions])
    time_range    = ev.get('time', '')
    session_label = ev.get('session_label', '')

    sess_by_col  = {s['sheet_col']: s for s in sessions}
    track_talks  = {col: [] for col in session_cols}
    for slot in time_slots:
        for col in session_cols:
            talk = slot['talks'].get(col)
            if talk:
                track_talks[col].append((slot.get('time', ''), talk))

    label_part = f'{esc(session_label)} · ' if session_label else ''
    lines = [
        '<div class="session-block">',
        f'<div class="session-time">{label_part}{esc(time_range)}</div>',
    ]
    for col in session_cols:
        sess       = sess_by_col.get(col, {})
        name       = sess.get('name', '')
        room       = sess.get('room', '')
        chair      = sess.get('chair', '')
        topic      = sess.get('topic', '')
        folder_url = sess.get('folder_url', '')
        room_html   = f' · <span class="room">{_render_room(room, zoom_map)}</span>' if room else ''
        chair_html  = f' · <span class="chair">Chair: {esc(chair)}</span>'             if chair else ''
        topic_html  = f' · <span class="topic">{esc(topic)}</span>'                    if topic else ''
        folder_html = (
            f' <a href="{esc(folder_url)}" class="folder-link">&#128193; Session folder</a>'
            if folder_url else ''
        )
        lines.append('<div class="track">')
        lines.append(f'<div class="track-hdr">{esc(name)}{room_html}{chair_html}{topic_html}{folder_html}</div>')
        for slot_time, talk in track_talks[col]:
            struck      = talk.get('strikethrough', False)
            author      = talk.get('author', '')
            title       = talk.get('title', '')
            url         = talk.get('abstract_url')
            remote      = talk.get('remote', False)
            cls         = 'talk-row talk-cancelled' if struck else 'talk-row'
            ttime_html  = f'<span class="ttime">{esc(slot_time)}</span>'
            author_html = f'<span class="talk-author">{esc(author)}</span>'
            if url and not struck:
                title_html = f'<a href="{esc(url)}" class="talk-title">{esc(title)}</a>'
            else:
                title_html = f'<span class="talk-title">{esc(title)}</span>'
            sep         = ' — ' if author and title else ''
            remote_html = ' <span class="remote-tag">R</span>' if remote and not struck else ''
            lines.append(
                f'<div class="{cls}">{ttime_html}'
                f'<span class="tcontent">{author_html}{sep}{title_html}{remote_html}</span></div>'
            )
        lines.append('</div>')
    lines.append('</div>')
    return '\n'.join(lines)


def _build_print_poster_section(section, start_num=1, num_prefix=''):
    header    = _print_endash(section.get('header', ''))
    location  = section.get('location', '')
    notes_raw = section.get('notes', '')
    lines     = ['<div class="poster-section">']
    lines.append(f'<div class="poster-hdr">{esc(header)}</div>')
    if location:
        lines.append(f'<p class="poster-loc">{esc(location)}</p>')
    if notes_raw:
        parts = [p.strip() for p in notes_raw.replace('<br/>', '\n').split('\n') if p.strip()]
        lines.append(f'<p class="poster-timing">{" ".join(esc(_print_endash(p)) for p in parts)}</p>')
    lines.append(
        '<table class="poster-table"><thead><tr>'
        '<th class="num">#</th><th class="mod">Format</th>'
        '<th>Authors</th><th>Title</th></tr></thead><tbody>'
    )
    seq = start_num
    for p in section.get('posters', []):
        struck    = p.get('strikethrough', False)
        raw_mod   = p.get('modality', '')
        is_remote = 'remote' in raw_mod.lower()
        if is_remote:
            num = 'Remote'
        else:
            num  = f'{num_prefix}{seq}'
            seq += 1
        mod        = esc('Remote' if is_remote else 'In-person')
        auth       = esc(p.get('authors', ''))
        title      = p.get('title', '')
        url        = p.get('abstract_url')
        title_html = (
            f'<a href="{esc(url)}">{esc(title)}</a>' if url and not struck else esc(title)
        )
        cls = ' class="poster-cancelled"' if struck else ''
        lines.append(f'<tr{cls}><td>{num}</td><td>{mod}</td><td>{auth}</td><td>{title_html}</td></tr>')
    lines.append('</tbody></table></div>')
    return '\n'.join(lines)


def build_print_html(acal_events, banto_events, poster_sections,
                     last_updated='', zoom_map=None):
    """Render a print-optimised, single-column schedule (no tabs, no JS)."""
    conf_title = f'{CONF_PRIMARY_NAME} / {CONF_SECONDARY_NAME}'
    parts = [_PRINT_HEAD.format(page_title=f'{conf_title} – Schedule'), _PRINT_CSS, '</style>\n</head>\n<body>']
    parts.append(f'<h1>{esc(conf_title)}</h1>')
    parts.append(
        f'<p class="subtitle">{esc(CONF_LOCATION)} &nbsp;&middot;&nbsp; {esc(CONF_DATES)}'
        f'<span class="last-updated"> &nbsp;&middot;&nbsp; Last updated: {esc(last_updated)}</span></p>'
    )

    for conf_label, events in [(CONF_SECONDARY_NAME, banto_events), (CONF_PRIMARY_NAME, acal_events)]:
        parts.append(f'<h2 class="conf-heading">{conf_label}</h2>')
        for ev in events:
            t = ev['type']
            if t == 'day':
                parts.append(f'<h3 class="day-heading">{esc(ev["text"])}</h3>')
            elif t == 'event':
                parts.append(_build_print_event(ev, zoom_map=zoom_map))
            elif t == 'session_block':
                parts.append(_build_print_session_block(ev, zoom_map=zoom_map))

    parts.append('<h2 class="conf-heading">Poster Sessions</h2>')
    _DAY_PREFIX  = {'wednesday': 'W', 'thursday': 'T', 'friday': 'F', 'saturday': 'S'}
    day_counters = {}
    for section in poster_sections:
        h      = section['header'].lower()
        prefix = next((v for k, v in _DAY_PREFIX.items() if k in h), '')
        start  = day_counters.get(prefix, 1)
        parts.append(_build_print_poster_section(section, start_num=start, num_prefix=prefix))
        inperson_count = sum(
            1 for p in section.get('posters', [])
            if 'remote' not in p.get('modality', '').lower()
        )
        day_counters[prefix] = start + inperson_count

    parts.append(f'<p class="last-updated">Last updated: {esc(last_updated)}</p>')
    parts.append('</body></html>')
    return '\n'.join(parts)
