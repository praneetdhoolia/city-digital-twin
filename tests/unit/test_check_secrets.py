"""The credential check matches every provider shape it names, and not a name.

The keys below are SYNTHETIC: the right shape, random-looking, never issued.
"""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    'check_secrets', os.path.join(os.path.dirname(__file__), '..', 'check_secrets.py'))
cs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cs)


def providers(line):
    return [p for p, pat in cs.PATTERNS if pat.search(line)]


def test_a_langsmith_key_in_a_settings_env_block_is_refused():
    line = '"CC_LANGSMITH_API_KEY": "lsv2_pt_' + 'ab12' * 8 + '_' + 'c0ffee1234' + '",'
    assert 'LangSmith' in providers(line)


def test_each_provider_shape_is_matched():
    assert providers('sk-ant-' + 'x' * 30)
    assert providers('ghp_' + 'A1' * 18)
    assert providers('AKIA' + 'ABCDEFGHIJ012345')
    assert providers('api_key = "' + 'Zq9' * 10 + '"')


def test_a_key_read_by_name_is_not_a_leak():
    """The code names its keys and reads the values from the gitignored .env."""
    assert providers("key = os.environ['TFNSW_API_KEY']") == []
    assert providers('OGD_API_KEY is read from .env') == []
