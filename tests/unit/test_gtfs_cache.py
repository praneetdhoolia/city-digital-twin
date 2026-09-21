"""A changed city feed cannot silently reuse yesterday's extracted schedule."""
import zipfile

import pytest
import build_matsim_network as builder


def test_changed_feed_invalidates_extraction_and_removes_obsolete_tables(monkeypatch, tmp_path):
    monkeypatch.setattr(builder, 'WORK', str(tmp_path / 'work'))
    feed = tmp_path / 'feed.zip'
    with zipfile.ZipFile(feed, 'w') as z:
        z.writestr('stop_times.txt', 'old departure')
        z.writestr('obsolete.txt', 'old table')
    from pathlib import Path
    extracted = Path(builder.unpack_feed('fixture', str(feed)))
    assert (extracted / 'stop_times.txt').read_text(encoding='utf-8') == 'old departure'
    with zipfile.ZipFile(feed, 'w') as z:
        z.writestr('stop_times.txt', 'new departure')
    builder.unpack_feed('fixture', str(feed))
    assert (extracted / 'stop_times.txt').read_text(encoding='utf-8') == 'new departure'
    assert not (extracted / 'obsolete.txt').exists()


@pytest.mark.parametrize('name', ['..', '../outside', 'nested/name', ''])
def test_cache_refuses_paths_outside_its_single_feed_directory(monkeypatch, tmp_path, name):
    monkeypatch.setattr(builder, 'WORK', str(tmp_path / 'work'))
    with pytest.raises(ValueError, match='direct child'):
        builder.unpack_feed(name, str(tmp_path / 'not-read.zip'))


def test_conversion_key_tracks_projection_day_and_converter(monkeypatch, tmp_path):
    feed, converter = tmp_path / 'feed.zip', tmp_path / 'converter.jar'
    feed.write_bytes(b'unchanged feed')
    converter.write_bytes(b'converter v1')
    monkeypatch.setattr(builder.tc, 'require', lambda: ('java', str(converter)))
    monkeypatch.setattr(builder, 'CRS', 'EPSG:32601')
    monkeypatch.setattr(builder, 'GTFS_DAY_PARAM', 'all')
    original = builder.gtfs_conversion_key(str(feed))
    assert original == builder.gtfs_conversion_key(str(feed))
    monkeypatch.setattr(builder, 'CRS', 'EPSG:32602')
    projection = builder.gtfs_conversion_key(str(feed))
    assert projection != original
    monkeypatch.setattr(builder, 'GTFS_DAY_PARAM', 'weekday')
    day = builder.gtfs_conversion_key(str(feed))
    assert day != projection
    converter.write_bytes(b'converter v2')
    assert day != builder.gtfs_conversion_key(str(feed))
