import datetime

DEFAULT_DURATION = datetime.timedelta(hours=2)
LINE_FOLD_LENGTH = 73


def format_datetime(dt):
    return dt.strftime('%Y%m%dT%H%M%SZ')


def escape_text(text):
    return (text.replace('\\', '\\\\')
                .replace(';', '\\;')
                .replace(',', '\\,')
                .replace('\r\n', '\\n')
                .replace('\n', '\\n'))


def fold_line(line):
    if len(line) <= LINE_FOLD_LENGTH:
        return line
    parts = [line[:LINE_FOLD_LENGTH]]
    rest = line[LINE_FOLD_LENGTH:]
    while rest:
        parts.append(' ' + rest[:LINE_FOLD_LENGTH - 1])
        rest = rest[LINE_FOLD_LENGTH - 1:]
    return '\r\n'.join(parts)


def build_calendar(events, host):
    now = format_datetime(datetime.datetime.utcnow())
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//iBlandbandet//Kalender//SV',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'X-WR-CALNAME:iBlandbandet',
    ]

    for event_id, title, starts_at, ends_at, location, latitude, longitude, description in events:
        ends_at = ends_at or (starts_at + DEFAULT_DURATION)
        lines.append('BEGIN:VEVENT')
        lines.append('UID:event-{}@{}'.format(event_id, host))
        lines.append('DTSTAMP:{}'.format(now))
        lines.append('DTSTART:{}'.format(format_datetime(starts_at)))
        lines.append('DTEND:{}'.format(format_datetime(ends_at)))
        lines.append(fold_line('SUMMARY:' + escape_text(title)))
        if location:
            lines.append(fold_line('LOCATION:' + escape_text(location)))
        if latitude is not None and longitude is not None:
            lines.append('GEO:{};{}'.format(latitude, longitude))
        if description:
            lines.append(fold_line('DESCRIPTION:' + escape_text(description)))
        lines.append('END:VEVENT')

    lines.append('END:VCALENDAR')
    return '\r\n'.join(lines) + '\r\n'
