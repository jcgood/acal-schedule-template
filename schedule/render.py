"""schedule/render.py — HTML rendering for the public and organizer schedule."""

import html as _html_module
import re

from config import (
    PLENARY_FOLDER_ID,
    GATHER_TOWN_URL, GATHER_TOWN_LIVE,
    CONF_END_DATE, CONF_END_TIME, CONF_TZ_TO_UTC_HOURS,
    CONF_PRIMARY_NAME, CONF_SECONDARY_NAME,
    ORGANIZER_EMAIL, DEFAULT_TAB,
)
from .parse import _end_time_24h


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def esc(text):
    return _html_module.escape(str(text))


def _inline_markup(text):
    """Convert *word* spans to <em>word</em> after HTML-escaping."""
    escaped = _html_module.escape(text)
    return re.sub(r'\*([^*]+)\*', r'<em>\1</em>', escaped)


def _render_room(room_str, zoom_map):
    """Return room HTML, replacing '- Zoom TBD' with a live Zoom link + copy-ID button."""
    if not room_str:
        return ''
    info = None
    for key, val in (zoom_map or {}).items():
        if room_str.startswith(key) or f'/ {key}' in room_str:
            info = val
            break
    if info:
        url        = info['url']
        meeting_id = info.get('meeting_id', '')
        if 'Zoom TBD' in room_str:
            base = room_str[:room_str.index('- Zoom TBD')].rstrip(' –-')
        else:
            base = room_str.rstrip(' –-')
        link     = f'<a href="{esc(url)}" target="_blank" rel="noopener" class="zoom-link">Zoom link</a>'
        copy_js  = (f"var t=this;navigator.clipboard.writeText('{meeting_id}');"
                    f"t.textContent='Copied!';"
                    f"setTimeout(function(){{t.textContent='Copy Meeting ID'}},1500)")
        copy_btn = f'<button class="zoom-copy-id" onclick="{esc(copy_js)}">Copy Meeting ID</button>'
        return f'{esc(base)} {link} {copy_btn}'
    return esc(room_str)


def _plenary_folder_url():
    """Return the Drive URL for the plenary session folder, or empty string."""
    if PLENARY_FOLDER_ID:
        return f'https://drive.google.com/drive/folders/{PLENARY_FOLDER_ID}'
    return ''


# ---------------------------------------------------------------------------
# Note strings
# ---------------------------------------------------------------------------

_TALKS_NOTE = (
    'Zoom links are shown next to each session room. '
    'Please use the passcode sent to registered attendees to join. '
    'If you have registered for the conference and need access to the passcodes, please '
    f'<a href="mailto:{ORGANIZER_EMAIL}" style="color:#005a9e;">email the conference organizers</a>. '
    'Remote talks to be given over Zoom are indicated with different shading.'
)


def _poster_note():
    if GATHER_TOWN_LIVE:
        return (
            f'Remote posters are hosted on gather.town. '
            f'<a href="{GATHER_TOWN_URL}" target="_blank" rel="noopener" style="color:#005a9e;">'
            f'Join the gather.town space</a> '
            f'to view them any time during the conference.'
        )
    return (
        'Remote posters will be hosted on gather.town (link TBA). '
        'You can see remote posters at the link any time during the conference.'
    )


# ---------------------------------------------------------------------------
# Talk and event renderers
# ---------------------------------------------------------------------------

def render_talk(talk, pad='', unregistered_set=None, nr_set=None):
    """Render a single talk as an indented <article> block."""
    struck     = talk.get('strikethrough', False)
    title_text = esc(talk['title'])
    if struck:
        title_text = f'<s>{title_text}</s>'
    title_html = (
        f'<a href="{esc(talk["abstract_url"])}" target="_blank" rel="noopener">'
        f'{title_text}</a>'
        if talk.get('abstract_url') and not struck
        else title_text
    )
    cls   = 'talk talk-cancelled' if struck else 'talk'
    lines = [f'{pad}<article class="{cls}">']
    if talk.get('author'):
        author_html = f'<s>{esc(talk["author"])}</s>' if struck else esc(talk['author'])
        lines.append(f'{pad}  <strong class="talk-author">{author_html}</strong>')
    remote_tag = ' <span class="remote-tag">Remote</span>' if talk.get('remote') and not struck else ''
    nr_tag = ''
    if nr_set and talk.get('unreg_key') in nr_set and not struck:
        nr_tag = ' <span class="nr-tag">NC</span>'
    lines.append(f'{pad}  <span class="talk-title">{title_html}{remote_tag}{nr_tag}</span>')
    lines.append(f'{pad}</article>')
    return '\n'.join(lines)


def render_event(event, pad='', poster_anchor='acal-poster-1', zoom_map=None):
    """Render a standalone event (plenary, break, social, etc.)."""
    lines = [f'{pad}<div class="event">']
    if event.get('time'):
        lines.append(f'{pad}  <time class="slot-time">{esc(event["time"])}</time>')
    lines.append(f'{pad}  <strong class="event-title">{esc(event["title"])}</strong>')
    details = event.get('details', [])
    url     = event.get('abstract_url')
    # Long last detail line (>40 chars) is a note, not a room.
    if details and len(details[-1]) > 40:
        note_line      = details[-1]
        render_details = details[:-1]
    else:
        note_line      = ''
        render_details = details
    for idx, line in enumerate(render_details):
        is_last = idx == len(render_details) - 1
        cls     = 'event-subtitle' if not is_last else 'event-location'
        if not is_last and idx == 0 and url:
            content = f'<a href="{esc(url)}" target="_blank" rel="noopener">{_inline_markup(line)}</a>'
        elif not is_last:
            content = _inline_markup(line)
        else:
            no_zoom = zoom_map if 'mixer' not in event.get('title', '').lower() else None
            content = _render_room(line, no_zoom)
        lines.append(f'{pad}  <span class="{cls}">{content}</span>')
    if note_line:
        lines.append(f'{pad}  <p class="event-note">{esc(note_line)}</p>')
    introducer = event.get('introducer', '')
    if introducer:
        lines.append(f'{pad}  <span class="event-introducer">Chair: {esc(introducer)}</span>')
    if 'plenary' in event.get('title', '').lower():
        folder_url = _plenary_folder_url()
        if folder_url:
            lines.append(
                f'{pad}  <a href="{esc(folder_url)}" target="_blank" rel="noopener"'
                f' class="folder-link">&#128193; Session folder</a>'
            )
    if 'poster' in event.get('title', '').lower():
        anchor = 'acal-poster-2' if '2' in event.get('title', '') else poster_anchor
        lines.append(
            f'{pad}  <a href="#{anchor}"'
            f' onclick="goToPoster(\'{anchor}\');return false;"'
            f' class="poster-tab-link">View poster schedule →</a>'
        )
    # Conference-specific: banquet directions link — update URL and location name.
    if 'banquet' in event.get('title', '').lower():
        lines.append(
            f'{pad}  <a href="https://maps.app.goo.gl/53Ja3ns4QKs3eHYcA"'
            f' target="_blank" rel="noopener" class="directions-link">&#x1F6B8; Directions from MSB</a>'
        )
    lines.append(f'{pad}</div>')
    return '\n'.join(lines)


def render_session_block(ev, pad='', zoom_map=None, unregistered_set=None, nr_set=None):
    """Render a session block as a collapsible <details> containing a sessions table."""
    sessions      = ev['sessions']
    time_slots    = ev.get('time_slots', [])
    session_cols  = ev.get('session_cols', [s['sheet_col'] for s in sessions])
    time_range    = ev.get('time', '')
    session_label = ev.get('session_label', '')
    n             = len(sessions)

    label_html = (
        f'<span class="session-label">{esc(session_label)}</span> '
        if session_label else ''
    )
    if n == 1:
        s = sessions[0]
        summary_inner = (
            f'{label_html}<time class="slot-time">{esc(time_range)}</time> {esc(s["name"])}'
            if time_range else f'{label_html}{esc(s["name"])}'
        )
    else:
        summary_inner = (
            f'{label_html}<time class="slot-time">{esc(time_range)}</time>'
            f' <span class="session-count">{n} parallel sessions</span>'
        )

    p2 = pad + '  '
    p4 = pad + '    '
    p6 = pad + '      '
    p8 = pad + '        '

    L = []
    L.append(f'{p2}<div class="sessions-wrap">')
    L.append(f'{p4}<table class="sessions-table">')
    L.append(f'{p6}<thead>')

    L.append(f'{p8}<tr class="session-headers-row">')
    L.append(f'{p8}  <th class="col-time"></th>')
    for s in sessions:
        inner = esc(s['name'])
        if s.get('topic'):
            inner += f'<br/><span class="session-title">{esc(s["topic"])}</span>'
        if s.get('folder_url'):
            inner += (
                f'<br/><a href="{esc(s["folder_url"])}" target="_blank" rel="noopener"'
                f' class="folder-link">&#128193; Session folder</a>'
            )
        L.append(f'{p8}  <th class="col-session">{inner}</th>')
    L.append(f'{p8}</tr>')

    if any(s.get('room') for s in sessions):
        L.append(f'{p8}<tr class="session-rooms-row">')
        L.append(f'{p8}  <td></td>')
        for s in sessions:
            L.append(f'{p8}  <td class="session-room">{_render_room(s.get("room", ""), zoom_map)}</td>')
        L.append(f'{p8}</tr>')

    if any(s.get('chair') for s in sessions):
        L.append(f'{p8}<tr class="session-chairs-row">')
        L.append(f'{p8}  <td></td>')
        for s in sessions:
            chair      = s.get('chair', '')
            chair_text = chair if (not chair or chair.lower().startswith('chair')) else f'Chair: {chair}'
            L.append(f'{p8}  <td class="session-chair">{esc(chair_text)}</td>')
        L.append(f'{p8}</tr>')

    if sessions:
        L.append(f'{p8}<tr class="session-techs-row">')
        L.append(f'{p8}  <td></td>')
        for s in sessions:
            tech       = s.get('tech', '')
            tech_clean = re.sub(
                r'^(tech\s*(coordinator)?|chair)\s*:\s*', '', tech, flags=re.IGNORECASE
            ).strip() if tech else ''
            tech_text = f'Tech Coordinator: {tech_clean if tech_clean else "TBD"}'
            tbd_cls   = ' tech-tbd' if (not tech_clean and unregistered_set is not None) else ''
            L.append(f'{p8}  <td class="session-tech{tbd_cls}">{esc(tech_text)}</td>')
        L.append(f'{p8}</tr>')

    L.append(f'{p6}</thead>')
    L.append(f'{p6}<tbody>')

    for slot in time_slots:
        slot_time = slot.get('time', '')
        L.append(f'{p8}<tr class="talk-row">')
        if slot_time:
            L.append(f'{p8}  <td class="col-time"><time>{esc(slot_time)}</time></td>')
        else:
            L.append(f'{p8}  <td class="col-time"></td>')
        for sc in session_cols:
            talk = slot['talks'].get(sc)
            if talk:
                remote_cls = ' col-talk-remote' if talk.get('remote') else ''
                unreg_cls  = ''
                if unregistered_set and talk.get('unreg_key') in unregistered_set:
                    unreg_cls = ' col-talk-unreg-remote' if talk.get('remote') else ' col-talk-unreg-inperson'
                L.append(f'{p8}  <td class="col-talk{remote_cls}{unreg_cls}">')
                L.append(render_talk(talk, pad=p8 + '    ',
                                     unregistered_set=unregistered_set, nr_set=nr_set))
                L.append(f'{p8}  </td>')
            else:
                L.append(f'{p8}  <td class="col-talk col-talk-empty"></td>')
        L.append(f'{p8}</tr>')

    L.append(f'{p6}</tbody>')
    L.append(f'{p4}</table>')
    L.append(f'{p2}</div>')

    table_html     = '\n'.join(L)
    parallel_class = ' has-parallel' if n > 1 else ''
    date_attr      = f' data-date="{ev["date"]}"' if ev.get('date') else ''
    end_24h        = _end_time_24h(time_range)
    end_attr       = f' data-end="{end_24h}"' if end_24h else ''
    lines = [f'{pad}<details class="time-slot{parallel_class}" open{date_attr}{end_attr}>']
    lines.append(f'{pad}  <summary>{summary_inner}</summary>')
    lines.append(table_html)
    lines.append(f'{pad}</details>')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Tab and poster section renderers
# ---------------------------------------------------------------------------

def render_tab_content(events, tab_id, note='', last_updated='',
                       zoom_map=None, unregistered_set=None, nr_set=None):
    poster_anchor = 'bantoid-poster' if tab_id == 'banto' else 'acal-poster-1'
    lines = [f'<div id="pane-{tab_id}" class="tab-pane">']
    if note:
        updated_suffix = (
            f' <span class="tab-note-updated">Last updated: {esc(last_updated)}</span>'
            if last_updated else ''
        )
        lines.append(f'  <p class="tab-note">{note}{updated_suffix}</p>')
    for ev in events:
        t = ev['type']
        if t == 'day':
            lines.append(f'  <h2 class="day-header">{esc(ev["text"])}</h2>')
        elif t == 'event':
            lines.append(render_event(ev, pad='  ', poster_anchor=poster_anchor, zoom_map=zoom_map))
        elif t == 'session_block':
            lines.append(render_session_block(ev, pad='  ', zoom_map=zoom_map,
                                              unregistered_set=unregistered_set, nr_set=nr_set))
    lines.append('</div>')
    return '\n'.join(lines)


def render_poster_section(section, pad='', unregistered_set=None, nr_set=None,
                          start_num=1, num_prefix=''):
    p2 = pad + '  '
    p4 = pad + '    '
    p6 = pad + '      '

    header_lower = section['header'].lower()
    if 'bantoid' in header_lower:
        section_id = 'bantoid-poster'
    else:
        m = re.search(r'session\s+(\d+)', header_lower)
        section_id = f'acal-poster-{m.group(1)}' if m else 'acal-poster'

    def _endash(text):
        return re.sub(r'(\d+:\d+)\s*-\s*(\d+)', r'\1–\2', text)

    # Conference-specific: maps day names to calendar dates; update for your event.
    _CONF_DAY_DATES = {'wednesday': 'May 20', 'thursday': 'May 21',
                       'friday': 'May 22', 'saturday': 'May 23'}

    lines      = [f'{pad}<section class="poster-session">']
    folder_url = section.get('folder_url')
    folder_badge = (
        f'<a href="{esc(folder_url)}" target="_blank" rel="noopener"'
        f' class="folder-link">&#128193; Session folder</a>'
        if folder_url else ''
    )
    raw_header = _endash(section['header'])
    if ': ' in raw_header:
        name_part, daytime_part = raw_header.split(': ', 1)
        daytime_part = re.sub(
            r'^(Wednesday|Thursday|Friday|Saturday)(,)',
            lambda mo: f'{mo.group(1)}, {_CONF_DAY_DATES[mo.group(1).lower()]}{mo.group(2)}',
            daytime_part, flags=re.IGNORECASE)
        header_html = f'{esc(name_part)}<br/><span class="poster-session-time">{esc(daytime_part)}</span>'
    else:
        header_html = esc(raw_header)
    if folder_badge:
        header_html += f'<br/>{folder_badge}'
    lines.append(f'{p2}<h2 class="poster-session-header" id="{section_id}">{header_html}</h2>')

    location = section.get('location', '')
    if location:
        lines.append(f'{p2}<p class="poster-location">{esc(location)}</p>')

    raw_notes = section.get('notes', '')
    if raw_notes:
        note_parts   = [p.strip() for p in raw_notes.replace('<br/>', '\n').split('\n')]
        note_parts   = [p for p in note_parts if p]
        adhere_parts = [p for p in note_parts if p.lower().startswith('please adhere')]
        main_parts   = [p for p in note_parts if not p.lower().startswith('please adhere')]
        notes_html   = '<br/>'.join(esc(_endash(p)) for p in main_parts)
        if adhere_parts:
            notes_html += f'<br/><em class="poster-timing-note">{esc(_endash(adhere_parts[0]))}</em>'
        lines.append(f'{p2}<p class="poster-timing">{notes_html}</p>')

    lines.append(f'{p2}<table class="poster-table">')
    lines.append(f'{p4}<thead>')
    lines.append(f'{p6}<tr>')
    lines.append(f'{p6}  <th>#</th>')
    lines.append(f'{p6}  <th>Authors</th>')
    lines.append(f'{p6}  <th>Title</th>')
    lines.append(f'{p6}</tr>')
    lines.append(f'{p4}</thead>')
    lines.append(f'{p4}<tbody>')

    seq = start_num
    for p in section['posters']:
        struck     = p.get('strikethrough', False)
        title_text = esc(p['title'])
        if struck:
            title_text = f'<s>{title_text}</s>'
        title_html = (
            f'<a href="{esc(p["abstract_url"])}" target="_blank" rel="noopener">'
            f'{title_text}</a>'
            if p.get('abstract_url') and not struck
            else title_text
        )
        is_remote       = 'remote' in p.get('modality', '').lower()
        mod_class       = ' remote' if is_remote else ''
        cancelled_class = ' poster-cancelled' if struck else ''
        unreg_cls       = ''
        if unregistered_set and p.get('unreg_key') in unregistered_set:
            unreg_cls = ' poster-unreg-remote' if mod_class else ' poster-unreg-inperson'
        lines.append(f'{p6}<tr class="poster-row{mod_class}{cancelled_class}{unreg_cls}">')
        if is_remote:
            num_display = 'Remote'
        else:
            num_display = f'{num_prefix}{seq}'
            seq += 1
        lines.append(f'{p6}  <td class="poster-num">{num_display}</td>')
        authors_html = f'<s>{esc(p["authors"])}</s>' if struck else esc(p['authors'])
        lines.append(f'{p6}  <td class="poster-authors">{authors_html}</td>')
        poster_nr_tag = ''
        if nr_set and p.get('unreg_key') in nr_set and not struck:
            poster_nr_tag = ' <span class="nr-tag">NC</span>'
        lines.append(f'{p6}  <td class="poster-title">{title_html}{poster_nr_tag}</td>')
        lines.append(f'{p6}</tr>')

    lines.append(f'{p4}</tbody>')
    lines.append(f'{p2}</table>')
    lines.append(f'{pad}</section>')
    return '\n'.join(lines)


def render_poster_tab(sections, last_updated='', unregistered_set=None, nr_set=None):
    lines = ['<div id="pane-poster" class="tab-pane">']
    updated_suffix = (
        f' <span class="tab-note-updated">Last updated: {esc(last_updated)}</span>'
        if last_updated else ''
    )
    lines.append(f'  <p class="tab-note">{_poster_note()}{updated_suffix}</p>')
    _DAY_PREFIX  = {'wednesday': 'W', 'thursday': 'T', 'friday': 'F', 'saturday': 'S'}
    day_counters = {}
    for s in sections:
        h      = s['header'].lower()
        prefix = next((v for k, v in _DAY_PREFIX.items() if k in h), '')
        start  = day_counters.get(prefix, 1)
        lines.append(render_poster_section(
            s, pad='  ', unregistered_set=unregistered_set, nr_set=nr_set,
            start_num=start, num_prefix=prefix,
        ))
        inperson_count = sum(
            1 for p in s['posters'] if 'remote' not in p.get('modality', '').lower()
        )
        day_counters[prefix] = start + inperson_count
    lines.append('</div>')
    return '\n'.join(lines)


def _poster_location_map(acal_events, banto_events):
    """Scan schedule events to build a poster-section-id → location map."""
    loc_map = {}
    for events, is_banto in [(banto_events, True), (acal_events, False)]:
        for ev in events:
            if ev['type'] != 'event' or 'poster' not in ev.get('title', '').lower():
                continue
            details = ev.get('details', [])
            loc     = next((d for d in reversed(details) if d and len(d) <= 40), '')
            if not loc:
                continue
            title = ev.get('title', '').lower()
            if is_banto or 'bantoid' in title:
                loc_map['bantoid-poster'] = loc
            else:
                m = re.search(r'(\d+)', title)
                key = f'acal-poster-{m.group(1)}' if m else 'acal-poster'
                loc_map[key] = loc
    return loc_map


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS = """\
*, *::before, *::after { box-sizing: border-box; }

body {
  font-family: 'Open Sans', system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.5;
  margin: 0;
  padding: 0;
  color: #222;
  background: #EEDD9D;
}

/* ---- CSS-only tab switching (radio button trick) ---- */
.tab-wrapper > input[type="radio"] { display: none; }

.tab-nav {
  display: flex;
  border-bottom: 2px solid #A08830;
  position: sticky;
  top: 0;
  background: #EEDD9D;
  z-index: 10;
  padding: 0 0.5rem;
  gap: 0.25rem;
  font-family: 'Bungee', cursive;
}

.tab-nav label {
  padding: 0.6rem 1rem;
  cursor: pointer;
  border: 2px solid transparent;
  border-bottom: none;
  border-radius: 4px 4px 0 0;
  color: #111;
  white-space: nowrap;
  margin-bottom: -2px;
}
.tab-nav label:hover { background: #D9C97A; }

.tab-pane { display: none; padding: 1rem 0.75rem; max-width: 1200px; margin: 0 auto; }

#tab-acal:checked   ~ .tab-nav label[for="tab-acal"],
#tab-banto:checked  ~ .tab-nav label[for="tab-banto"],
#tab-poster:checked ~ .tab-nav label[for="tab-poster"] {
  border-color: #A08830;
  border-bottom-color: #EEDD9D;
  color: #111;
  background: #EEDD9D;
}

#tab-acal:checked   ~ #pane-acal,
#tab-banto:checked  ~ #pane-banto,
#tab-poster:checked ~ #pane-poster { display: block; }

/* ---- Day headers ---- */
.day-header {
  font-size: 1.25rem;
  font-weight: 700;
  font-family: 'Bungee', cursive;
  color: #111;
  margin: 1.5rem 0 0.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 2px solid #111;
}

/* ---- Standalone events (plenaries, breaks, etc.) ---- */
.event {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0.45rem 0.75rem;
  background: #D9C97A;
  border-radius: 4px;
  margin: 0.4rem 0;
}

.slot-time {
  font-size: 0.875rem;
  font-weight: 700;
  color: #111;
  white-space: nowrap;
}

.event-title      { font-weight: 600; font-size: 1rem; }
.event-subtitle   { font-style: italic; color: #111; font-size: 0.9rem; }
.event-subtitle a { color: #005a9e; }
.event-introducer { font-size: 0.875rem; color: #111; }
.event-location   { font-size: 0.875rem; color: #111; }
.event-note       { font-size: 0.85rem; color: #111; margin: 0.2em 0 0; }
.zoom-link,
.zoom-copy-id {
  display: inline-block;
  margin-left: 0.35rem;
  font-size: 0.7rem;
  line-height: 1;
  font-weight: 700;
  padding: 0.15rem 0.3rem;
  border-radius: 3px;
  background: #2B6891;
  color: #fff;
  vertical-align: middle;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border: none;
  cursor: pointer;
  text-decoration: none;
  font-family: inherit;
}
.zoom-link:hover,
.zoom-copy-id:hover { background: #245778; }

/* ---- Collapsible time slots ---- */
details.time-slot {
  margin: 0.5rem 0;
  border: 1px solid #A08830;
  border-radius: 6px;
  overflow: hidden;
}

details.time-slot > summary {
  list-style: none;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  cursor: pointer;
  background: #D9C97A;
  font-weight: 600;
  user-select: none;
  flex-wrap: wrap;
}
details.time-slot > summary::-webkit-details-marker { display: none; }

details.time-slot > summary::before {
  content: "▶";
  font-size: 0.7rem;
  color: #111;
  flex-shrink: 0;
  transition: transform 0.15s;
}
details.time-slot[open] > summary::before { transform: rotate(90deg); }

details.time-slot > summary .slot-time     { color: #111; }
details.time-slot > summary .session-label { font-weight: 700; color: #111; }
details.time-slot > summary .session-count { color: #111; font-weight: 400; font-size: 0.9rem; }

/* ---- Sessions table with horizontal scroll ---- */
.sessions-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  padding: 0.5rem;
}

.sessions-table {
  border-collapse: separate;
  border-spacing: 8px 0;
  width: 100%;
}

.sessions-table .col-time {
  width: 5rem;
  padding: 0.35rem 0.5rem;
  vertical-align: top;
  color: #111;
  font-size: 0.875rem;
  font-weight: 700;
  white-space: nowrap;
  border: none;
}

.sessions-table .col-session {
  min-width: 200px;
  padding: 0.5rem 0.6rem;
  font-weight: 700;
  font-size: 1rem;
  color: #111;
  background: #C8B45E;
  border: 1px solid #A08830;
  border-bottom: none;
  border-radius: 6px 6px 0 0;
  text-align: left;
  vertical-align: top;
}
.sessions-table .col-session a {
  color: inherit;
  font-weight: 700;
  text-decoration: none;
}
.sessions-table .col-session a:hover { text-decoration: underline; }

.sessions-table .session-title {
  font-weight: 700;
  font-size: 1rem;
  color: #111;
}

/* Session/poster folder link badge */
.folder-link {
  display: inline-block;
  align-self: flex-start;
  margin-top: 0.35rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: #5a3e00;
  background: rgba(0,0,0,0.10);
  border-radius: 4px;
  padding: 0.1em 0.45em;
  text-decoration: none;
  letter-spacing: 0.01em;
}
.folder-link:hover {
  background: rgba(0,0,0,0.20);
  text-decoration: none;
}

.directions-link {
  display: inline-block;
  align-self: flex-start;
  margin-top: 0.3rem;
  font-size: 0.82rem;
  line-height: 1;
  font-weight: 700;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  background: #2B6891;
  color: #fff;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  text-decoration: none;
}
.directions-link:hover { background: #245778; text-decoration: none; }

/* Sub-header rows (room, chair, tech) */
.sessions-table .session-rooms-row  td:not(:first-child),
.sessions-table .session-chairs-row td:not(:first-child),
.sessions-table .session-techs-row  td:not(:first-child) {
  font-size: 0.875rem;
  padding: 0.15rem 0.6rem;
  background: #D9C97A;
  border-top: none;
  border-bottom: none;
  border-left: 1px solid #A08830;
  border-right: 1px solid #A08830;
}
.sessions-table .session-rooms-row  td:not(:first-child) { color: #222; }
.sessions-table .session-chairs-row td:not(:first-child) { color: #222; }
.sessions-table .session-techs-row  td:not(:first-child) { color: #222; }
.sessions-table .session-techs-row td.session-tech.tech-tbd { background: #ff69b4; color: #fff; font-weight: 600; }
.sessions-table .session-rooms-row  td:first-child,
.sessions-table .session-chairs-row td:first-child,
.sessions-table .session-techs-row  td:first-child { border: none; }

/* Talk cells */
.sessions-table .col-talk {
  min-width: 200px;
  padding: 0.35rem 0.6rem;
  vertical-align: top;
  border-top: none;
  border-bottom: none;
  border-left: 1px solid #A08830;
  border-right: 1px solid #A08830;
}

.sessions-table tbody tr:last-child .col-talk {
  border-bottom: 1px solid #A08830;
  border-radius: 0 0 6px 6px;
}

.sessions-table .col-talk-empty  { background: #EEDD9D; }
.sessions-table .col-talk-remote { background: #BBA040; }
.sessions-table .col-talk-unreg-inperson { background: #aed6f1; }
.sessions-table .col-talk-unreg-remote   { background: #1a5276; color: #fff; }
.sessions-table .col-talk-unreg-remote .talk-author,
.sessions-table .col-talk-unreg-remote .talk-title,
.sessions-table .col-talk-unreg-remote a { color: #d6eaf8; }

.sessions-table .talk-row:not(:first-child) td {
  border-top: 1px solid #C8B45E;
}

.sessions-table .talk {
  margin: 0;
  padding: 0;
  border-top: none;
  font-size: 0.88rem;
}

/* ---- Talk entries ---- */
.talk {
  display: flex;
  flex-direction: column;
  margin: 0.4rem 0;
  padding: 0.35rem 0;
  border-top: 1px solid #C8B45E;
  font-size: 0.9rem;
}
.talk:first-of-type { border-top: none; }

.talk-author {
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: 0.15rem;
}
.talk-title           { color: #222; line-height: 1.4; }
.talk-title a         { color: #005a9e; text-decoration: underline; }
.talk-title a:visited { color: #5a189a; }

.remote-tag {
  display: inline-block;
  margin-left: 0.35rem;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.05rem 0.3rem;
  border-radius: 3px;
  background: #6A5500;
  color: #fff;
  vertical-align: middle;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.nr-tag {
  display: inline-block;
  margin-left: 0.35rem;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.05rem 0.3rem;
  border-radius: 3px;
  background: #f0e8cc;
  color: #6A5500;
  border: 1.5px solid #6A5500;
  vertical-align: middle;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* ---- Poster table ---- */
.poster-session { margin: 1rem 0 2rem; }

.poster-session-header {
  font-size: 1.1rem;
  font-weight: 700;
  color: #111;
  margin: 1rem 0 0.5rem;
  padding-bottom: 0.2rem;
  border-bottom: 1px solid #A08830;
}
.poster-session-time {
  font-family: 'Bungee', cursive;
}
.poster-session-header a { color: inherit; text-decoration: none; }
.poster-session-header a:hover { text-decoration: underline; }
.poster-location {
  font-size: 1rem;
  color: #444;
  margin: 0.1rem 0 0.3rem;
}
.poster-timing {
  font-size: 0.88rem;
  color: #222;
  margin: 0.1rem 0 0.6rem;
  line-height: 1.5;
}
.poster-timing-note {
  font-style: italic;
  color: #111;
}

.poster-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}
.poster-table th {
  text-align: left;
  padding: 0.4rem 0.5rem;
  background: #C8B45E;
  border-bottom: 2px solid #111;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.poster-table td {
  padding: 0.4rem 0.5rem;
  vertical-align: top;
  border-bottom: 1px solid #C8B45E;
}
.poster-table tr:last-child td { border-bottom: none; }

.poster-num     { white-space: nowrap; font-weight: 600; color: #222; width: 3.5rem; }
.poster-authors { width: 30%; color: #222; }
.poster-title a         { color: #005a9e; text-decoration: underline; }
.poster-title a:visited { color: #5a189a; }
.poster-row.remote               { background: #BBA040; }
.poster-row.poster-unreg-inperson { background: #aed6f1; }
.poster-row.poster-unreg-remote   { background: #1a5276; color: #fff; }
.poster-row.poster-unreg-remote td { color: #d6eaf8; }
.poster-row.poster-unreg-remote a  { color: #d6eaf8; }

/* ---- Tab intro note ---- */
.tab-note {
  margin: 0.75rem 0 1rem;
  padding: 0.6rem 0.9rem;
  background: #D9C97A;
  border-left: 3px solid #111;
  border-radius: 0 4px 4px 0;
  font-size: 0.9rem;
  color: #222;
  line-height: 1.5;
}

/* ---- Narrow-display scroll hint ---- */
@media (max-width: 700px) {
  details.time-slot.has-parallel[open] > summary::after {
    content: "Scroll right for more sessions →";
    display: block;
    width: 100%;
    font-size: 0.75rem;
    font-weight: 400;
    color: #111;
    margin-top: 0.2rem;
  }
}

/* ---- Poster-tab navigation link inside event blocks ---- */
.poster-tab-link {
  display: inline-block;
  margin-top: 0.25rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #005a9e;
  cursor: pointer;
  text-decoration: underline;
}
.poster-tab-link:hover { color: #003d6b; }

/* ---- Cancelled / withdrawn entries ---- */
.talk-cancelled { opacity: 0.5; }
.talk-cancelled .talk-author,
.talk-cancelled .talk-title { color: #444; }
.poster-cancelled td { opacity: 0.5; color: #444; }

.tab-note-updated {
  display: block;
  font-size: 0.8em;
  color: #111;
  margin-top: 0.3em;
}

@media (max-width: 600px) {
  .poster-table thead { display: none; }
  .poster-table tr {
    display: block;
    margin-bottom: 0.75rem;
    border: 1px solid #A08830;
    border-radius: 4px;
    padding: 0.5rem;
  }
  .poster-table td    { display: block; border: none; padding: 0.1rem 0; }
  .poster-num         { font-size: 0.8rem; }
  .poster-authors     { font-size: 0.85rem; }
}
"""


# ---------------------------------------------------------------------------
# Full page builder
# ---------------------------------------------------------------------------

def build_html(acal_events, banto_events, poster_sections, last_updated='',
               zoom_map=None, unregistered_set=None, nr_set=None):
    """Render the full tabbed HTML schedule page."""
    loc_map = _poster_location_map(acal_events, banto_events)
    for s in poster_sections:
        h   = s['header'].lower()
        if 'bantoid' in h:
            sid = 'bantoid-poster'
        else:
            m   = re.search(r'session\s+(\d+)', h)
            sid = f'acal-poster-{m.group(1)}' if m else 'acal-poster'
        s['location'] = loc_map.get(sid, '')

    acal_pane   = render_tab_content(acal_events,  'acal',  note=_TALKS_NOTE,
                                     last_updated=last_updated, zoom_map=zoom_map,
                                     unregistered_set=unregistered_set, nr_set=nr_set)
    banto_pane  = render_tab_content(banto_events, 'banto', note=_TALKS_NOTE,
                                     last_updated=last_updated, zoom_map=zoom_map,
                                     unregistered_set=unregistered_set, nr_set=nr_set)
    poster_pane = render_poster_tab(poster_sections, last_updated=last_updated,
                                    unregistered_set=unregistered_set, nr_set=nr_set)

    # Pre-compute conference end date/time parts for the collapse JS.
    _d = CONF_END_DATE.split('-')
    _t = CONF_END_TIME.split(':')
    _conf_end_year  = int(_d[0])
    _conf_end_month = int(_d[1]) - 1   # JS months are 0-indexed
    _conf_end_day   = int(_d[2])
    _conf_end_hour  = int(_t[0])
    _conf_end_min   = int(_t[1])

    # Conference-specific JavaScript: update the tab IDs, hash mappings, and
    # default tab to match your conference. Collapse timing comes from config.
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{CONF_PRIMARY_NAME} / {CONF_SECONDARY_NAME} Schedule</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bungee&family=Open+Sans:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
{CSS}  </style>
</head>
<body>
  <div class="tab-wrapper">
    <input type="radio" id="tab-acal"   name="schedule-tab">
    <input type="radio" id="tab-banto"  name="schedule-tab" checked>
    <input type="radio" id="tab-poster" name="schedule-tab">
    <nav class="tab-nav">
      <label for="tab-banto">{CONF_SECONDARY_NAME}</label>
      <label for="tab-acal">{CONF_PRIMARY_NAME}</label>
      <label for="tab-poster">Posters</label>
    </nav>
{banto_pane}
{acal_pane}
{poster_pane}
  </div>
<script>
var TAB_HASHES = {{'tab-acal': '#acal', 'tab-banto': '#banto', 'tab-poster': '#poster'}};
var HASH_TABS  = {{'#acal': 'tab-acal', '#banto': 'tab-banto', '#poster': 'tab-poster'}};

function switchTab(tabId, push) {{
  var el = document.getElementById(tabId);
  if (!el) return;
  el.checked = true;
  var hash = TAB_HASHES[tabId] || '';
  if (push) {{
    history.pushState({{tab: tabId}}, '', hash || location.pathname);
  }} else {{
    history.replaceState({{tab: tabId}}, '', hash || location.pathname);
  }}
}}

function goToPoster(anchor) {{
  switchTab('tab-poster', true);
  var el = document.getElementById(anchor);
  if (!el) return;
  var nav = document.querySelector('.tab-nav');
  el.style.scrollMarginTop = (nav ? nav.offsetHeight : 0) + 'px';
  void el.getBoundingClientRect();
  el.scrollIntoView({{behavior: 'smooth', block: 'start'}});
}}

document.querySelectorAll('.tab-nav label').forEach(function(label) {{
  label.addEventListener('click', function(e) {{
    var tabId = label.getAttribute('for');
    if (tabId && TAB_HASHES[tabId]) {{
      e.preventDefault();
      switchTab(tabId, true);
    }}
  }});
}});

window.addEventListener('popstate', function(e) {{
  var tabId = (e.state && e.state.tab) || HASH_TABS[location.hash] || 'tab-banto';
  var el = document.getElementById(tabId);
  if (el) el.checked = true;
}});

// Default tab and session auto-collapse.
// Conference-specific: update defaultTab, and set CONF_END_DATE / CONF_END_TIME /
// CONF_TZ_TO_UTC_HOURS in config.py — the values below are baked in at build time.
(function() {{
  var TZ_OFFSET_MS = {CONF_TZ_TO_UTC_HOURS} * 60 * 60 * 1000;
  var defaultTab = 'tab-{DEFAULT_TAB}';  // Set DEFAULT_TAB in config.py

  switchTab(HASH_TABS[location.hash] || defaultTab, false);

  // Auto-collapse any session whose end time has passed, on any conference day.
  // Once CONF_END_UTC passes the conference is over and all sessions stay open.
  var CONF_END_UTC = Date.UTC({_conf_end_year}, {_conf_end_month}, {_conf_end_day}, {_conf_end_hour}, {_conf_end_min}) + TZ_OFFSET_MS;
  var nowMs = Date.now();
  if (nowMs >= CONF_END_UTC) return;
  document.querySelectorAll('details.time-slot[data-date][data-end]').forEach(function(el) {{
    var d = el.dataset.date.split('-');
    var t = el.dataset.end.split(':');
    var endUTC = Date.UTC(+d[0], +d[1] - 1, +d[2], +t[0], +t[1]) + TZ_OFFSET_MS;
    if (endUTC < nowMs) el.removeAttribute('open');
  }});
}})();
</script>
</body>
</html>"""
