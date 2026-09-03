"""A launch refused before MATSim started leaves a status card that says why (#127).

`run_matsim.run()` used to write `_meta.json` with `status=running` before it
validated the inputs, emitted the config and checked the run stack; a missing
input file therefore left a `running` card that the next harness reconciled
as "no longer running", and the refusal's own message - the one fact that
explained the death - was lost. The card is now written after validation, and
a refusal goes through `refuse_launch`: a `failed` card whose cause quotes the
message, retired under the `aborted_` label like every other dead run.

This check drives `refuse_launch` on a temporary directory with the results
store's mirror and rename stubbed out (nothing under `results/` is touched),
and asserts the card validates against the meta contract, carries the message,
and the directory is renamed. Stdlib only, sub-second. Exit 1 on failure.
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
for sub in ('run', 'analyse', 'registry', ''):
    sys.path.insert(0, os.path.join(REPO, 'src', sub) if sub
                    else os.path.join(REPO, 'src'))
import run_matsim      # noqa: E402
import results_store   # noqa: E402
from registry import outputs  # noqa: E402

FAILS = []


def check(cond, msg):
    print(('PASS  ' if cond else 'FAIL  ') + msg)
    if not cond:
        FAILS.append(msg)


tmp = tempfile.mkdtemp(prefix='launch_refusal_')
run_dir = os.path.join(tmp, '20260903T000000_2it_1pct')
os.makedirs(run_dir)
meta = dict(status='running', scenario='S2', day='WEEKDAY', fraction=0.01,
            sample_pct=1.0, iterations=2, seed=1, threads=1, xmx='1g',
            overrides={}, controler_sha256=None, inputs_sha256=None,
            started=run_matsim._now(), ended=None, wall_s=None, rc=None,
            pid=os.getpid())
message = ('parking_prices.tsv is missing from the run inputs: '
           'cities/newcastle/scenarios/matsim/S2/WEEKDAY/parking_prices.tsv')

saved = (results_store.mirror, results_store.rename)
results_store.mirror = lambda d: None
results_store.rename = lambda a, b: None
try:
    target = run_matsim.refuse_launch(run_dir, meta, SystemExit(message))
finally:
    results_store.mirror, results_store.rename = saved

check(os.path.basename(target).startswith('aborted_'),
      'the refused directory is retired under the aborted_ label')
card_path = os.path.join(target, run_matsim.META)
check(os.path.exists(card_path), 'the status card exists in the retired directory')
card = json.load(open(card_path, encoding='utf-8')) if os.path.exists(card_path) else {}
check(card.get('status') == 'failed', 'the card says failed, not running')
check(message in (card.get('cause') or ''),
      'the cause quotes the refusal message (the missing file by name)')
check(card.get('ended') is not None, 'the card carries an end time')
errors = outputs.validate_doc('meta', card) if hasattr(outputs, 'validate_doc') else []
check(not errors, 'the card satisfies the meta contract: %s' % (errors or 'ok'))
check(not os.path.exists(run_dir), 'the original directory name is gone')

shutil.rmtree(tmp, ignore_errors=True)
if FAILS:
    print('\n%d check(s) failed' % len(FAILS))
    sys.exit(1)
print('\nALL CHECKS PASSED')
