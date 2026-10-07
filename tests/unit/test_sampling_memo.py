"""The lift-cluster map is computed once per population and the subsample
is timed (sixteenth report, 8 October 2026).

The union-find needs the whole graph before the first keep decision, so the
sampler parsed the plans twice at every launch (74 s for the map on the
622,174-person weekday plans). The map is memoised beside its source, keyed
on the population's own bytes, so a later launch on the same bytes makes one
pass; a changed population or an older reading is never reused. The sample
is the same to the byte with or without the memo.
"""
import gzip
import json

from sample_population import (CLUSTER_MEMO_STAMP, cluster_memo_path,
                               lift_cluster_map, subsample_plans)

SEED = 20260810


def _person(identity, household=None, lift=None):
    attrs = ''.join("<attribute class='java.lang.String' name='%s'>%s</attribute>" % kv
                    for kv in (('householdId', household), ('liftHousehold', lift))
                    if kv[1] is not None)
    return ("<person id='%s'><attributes>%s</attributes><plan selected='yes'>"
            "<act type='home' x='0' y='0'/></plan></person>" % (identity, attrs))


def _population(tmp_path, name='pop.xml.gz', extra=''):
    people = _person('one', '1', '2') + _person('two', '2') + _person('three', '3')
    people += ''.join(_person('p%d' % n, str(n)) for n in range(4, 200))
    path = tmp_path / name
    with gzip.open(path, 'wt', encoding='utf-8') as fh:
        fh.write('<population>' + people + extra + '</population>')
    return path


def test_the_map_is_written_once_and_read_back(tmp_path):
    src = _population(tmp_path)
    memo = cluster_memo_path(src)
    first = lift_cluster_map(src)
    assert first == {'2': '1'}
    doc = json.loads(open(memo, encoding='utf-8').read())
    assert doc['stamp'] == CLUSTER_MEMO_STAMP and doc['clusters'] == first
    # a memo that disagrees with the parse would be read back as written:
    # prove the second call reads the memo, not the plans
    doc['clusters'] = {'2': 'memo'}
    json.dump(doc, open(memo, 'w', encoding='utf-8'))
    assert lift_cluster_map(src) == {'2': 'memo'}
    assert lift_cluster_map(src, memo=False) == {'2': '1'}


def test_a_changed_population_never_reuses_the_memo(tmp_path):
    src = _population(tmp_path)
    lift_cluster_map(src)
    _population(tmp_path, extra=_person('late', '3', '2'))     # same path, new bytes
    assert lift_cluster_map(src) == {'2': '1', '3': '1'}


def test_an_older_readings_memo_is_not_reused(tmp_path):
    src = _population(tmp_path)
    lift_cluster_map(src)
    memo = cluster_memo_path(src)
    doc = json.loads(open(memo, encoding='utf-8').read())
    doc['stamp'] = 'lift-clusters-0'
    doc['clusters'] = {'2': 'stale'}
    json.dump(doc, open(memo, 'w', encoding='utf-8'))
    assert lift_cluster_map(src) == {'2': '1'}


def test_the_sample_is_byte_identical_with_and_without_the_memo(tmp_path):
    src = _population(tmp_path)
    cold, warm = tmp_path / 'cold.xml.gz', tmp_path / 'warm.xml.gz'
    kept_cold, kept_warm = set(), set()
    subsample_plans(src, cold, 0.25, SEED, 'household', kept_ids=kept_cold)
    subsample_plans(src, warm, 0.25, SEED, 'household', kept_ids=kept_warm)
    assert kept_cold == kept_warm and kept_cold
    assert cold.read_bytes() == warm.read_bytes()
    assert ('one' in kept_cold) == ('two' in kept_cold), 'the lift pair is kept together'


def test_a_directory_that_takes_no_memo_still_samples(tmp_path, monkeypatch):
    src = _population(tmp_path)
    import sample_population as sp
    monkeypatch.setattr(sp, 'cluster_memo_path', lambda s: str(tmp_path / 'no' / 'such' / 'dir'))
    assert lift_cluster_map(src) == {'2': '1'}


def test_the_launch_records_the_subsample_seconds():
    """The card's sample block carries subsample_s (None for a warm start)."""
    import inspect
    import run_matsim
    src = inspect.getsource(run_matsim.build_config)
    assert 'subsample_s=subsample_s' in src and 'subsample_s = None' in src
