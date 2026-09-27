"""`check_doc_currency.py --fix`: a drifted number (or run name) is rewritten
to its artefact's value in the document's own format, on its own line and
nowhere else; anything else is refused and left alone."""
import os
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..')))
import check_doc_currency as cdc  # noqa: E402


def _claim(pattern, cid='c', **kw):
    return dict(id=cid, doc='doc.md', pattern=pattern, **kw)


def test_the_format_the_document_used_is_kept():
    assert cdc.format_like('1,903,808', Decimal(1939239), None) == '1,939,239'
    assert cdc.format_like('579', Decimal(587), None) == '587'
    assert cdc.format_like('**6.64**', Decimal('6.67'), None) == '**6.67**'
    assert cdc.format_like('−1.5', Decimal('-2.25'), 2) == '−2.25'
    assert cdc.format_like('12', Decimal('12.5'), None) is None     # precision it lacks
    assert cdc.format_like('n/a', Decimal(3), None) is None


def test_only_the_drifted_capture_on_its_line_moves():
    text = ('Files in the manifest | 579 |\n'
            'A dated record says 579 and stays.\n'
            'Agents: 1,903,808 in the sample\n')
    claims = [(_claim(r'manifest \| (\d[\d,]*) \|', 'files'), 'number', 587),
              (_claim(r'Agents: ([\d,]+)', 'agents'), 'number', 1939239)]
    new, changes, refused = cdc.fix_document(text, claims)
    assert new == ('Files in the manifest | 587 |\n'
                   'A dated record says 579 and stays.\n'
                   'Agents: 1,939,239 in the sample\n')
    assert len(changes) == 2 and not refused
    assert any('doc.md:1 files: 579 -> 587' in c for c in changes)


def test_a_current_value_is_not_touched():
    text = 'Fit 10.65 pp\n'
    new, changes, refused = cdc.fix_document(
        text, [(_claim(r'Fit ([\d.]+) pp', decimals=2), 'number', 10.649)])
    assert new == text and not changes and not refused


def test_run_names_move_and_other_text_is_refused():
    text = 'Newest: 20260926T002526_250it_25pct\nState: running\n'
    claims = [(_claim(r'Newest: (\S+)', 'run'), 'text', '20260927T145839_250it_25pct'),
              (_claim(r'State: (\w+)', 'state'), 'text', 'stopped')]
    new, changes, refused = cdc.fix_document(text, claims)
    assert 'Newest: 20260927T145839_250it_25pct' in new
    assert 'State: running' in new
    assert len(changes) == 1 and len(refused) == 1


def test_an_unrepresentable_value_is_refused():
    text = 'Share 12 %\n'
    new, changes, refused = cdc.fix_document(
        text, [(_claim(r'Share (\d+) %'), 'number', 12.4)])
    assert new == text and not changes and len(refused) == 1
