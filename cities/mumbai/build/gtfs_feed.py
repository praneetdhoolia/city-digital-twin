"""The one GTFS table writer of this city's three feed builders.

`build_baseline_transit_feed.py`, `build_suburban_timetable_feed.py` and
`build_regional_bus_feed.py` each carried their own copy of the same three
steps - a table serialised with LF line ends, rows appended to a table the
incoming feed already holds (its columns widened to the rows'), and the feed
zipped with fixed entry headers so two builds of the same content hash the
same. One copy here; the bytes are the ones the copies wrote.
"""
import csv
import io
import zipfile


def table(items, fields):
    """A GTFS table's bytes: `fields` as the header, one row per item, LF ends."""
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(items)
    return out.getvalue().encode('utf-8')


def append_table(content, name, additions):
    """Append `additions` to the table `content[name]` holds, widening its
    columns to any key the additions carry; `content` is {name: bytes}."""
    reader = csv.DictReader(io.StringIO(content[name].decode('utf-8-sig')))
    fields = list(reader.fieldnames)
    existing = list(reader)
    for row in additions:
        for key in row:
            if key not in fields:
                fields.append(key)
    content[name] = table(existing + additions, fields)


def write_feed(path, content):
    """Zip {name: bytes} at `path`, entries in name order with the fixed
    header zipfile gives a bare ZipInfo, deflated: byte-identical per content."""
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(content.items()):
            entry = zipfile.ZipInfo(name)
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
