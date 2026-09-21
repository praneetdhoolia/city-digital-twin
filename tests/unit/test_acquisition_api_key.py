"""A registered API key reaches the request and never the record (9.207).

The second city's acquisition adapter sends the key a catalogue entry names
(`api_key_env`) as a query parameter read from the environment or `.env`,
refuses with the reason when it is absent, and strips it from the final URL
the provenance keeps.
"""
import importlib.util
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))


@pytest.fixture
def adapter():
    # the adapter only touches the city at request time; loading it leaves
    # the framework's `city` module (and the suite's active city) alone.
    # It imports `requests`, which the offline CI image does not carry.
    pytest.importorskip('requests')
    spec = importlib.util.spec_from_file_location(
        'acquire_sources', os.path.join(ROOT, 'cities', 'mumbai', 'extract', 'acquire_sources.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_key_comes_from_the_environment_as_the_named_parameter(adapter, monkeypatch):
    monkeypatch.setenv('OGD_API_KEY', 'k-123')
    entry = dict(api_key_env='OGD_API_KEY', api_key_param='api-key')
    assert adapter.api_key_params(entry) == {'api-key': 'k-123'}
    assert adapter.api_key_params(dict()) is None


def test_a_missing_key_refuses_with_the_registration_reason(adapter, monkeypatch, tmp_path):
    monkeypatch.delenv('OGD_API_KEY', raising=False)
    monkeypatch.setattr(adapter.city, 'REPO', str(tmp_path))       # no .env here
    entry = dict(api_key_env='OGD_API_KEY', api_key_registration='a free account at the publisher')
    with pytest.raises(ValueError, match='needs OGD_API_KEY.*free account'):
        adapter.api_key_params(entry)


def test_the_key_is_read_from_the_repository_env_file(adapter, monkeypatch, tmp_path):
    monkeypatch.delenv('OGD_API_KEY', raising=False)
    monkeypatch.setattr(adapter.city, 'REPO', str(tmp_path))
    (tmp_path / '.env').write_text('OTHER=1\nOGD_API_KEY="from-file"\n', encoding='utf-8')
    assert adapter.api_key_params(dict(api_key_env='OGD_API_KEY')) == {'api-key': 'from-file'}


def test_the_final_url_in_the_record_carries_no_key(adapter):
    url = 'https://api.data.gov.in/resource/abc?format=csv&api-key=secret&limit=2000'
    assert adapter.without_api_key(url, {'api-key': 'secret'}) == \
        'https://api.data.gov.in/resource/abc?format=csv&limit=2000'
    assert adapter.without_api_key(url, None) == url
