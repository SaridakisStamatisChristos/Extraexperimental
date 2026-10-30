#!/usr/bin/env python3
"""Create immutable model-selection/forecast evidence without touching holdout."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
src=P/'timestamp_scan_results.json'
result=json.loads(src.read_text())
assert result['selection_count']+result['validation_count']==599
assert [f['draw_id'] for f in result['forecasts']]==list(range(14353,14358))
assert result['dataset_sha256']==hashlib.sha256((P/'train_599.csv').read_bytes()).hexdigest()
lock={'protocol':'2026-10-30 source-controlled timestamp/ID PRNG search; retrospectively separated five holdout draws',
 'train_file':'train_599.csv','train_sha256':result['dataset_sha256'],
 'fitter_sha256':hashlib.sha256((P/'timestamp_prng_scan.py').read_bytes()).hexdigest(),
 'full_scan_results_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
 'chosen_algorithm':result['selection_winner'],
 'forecasts':result['forecasts'],
 'holdout_was_not_read_by_fitter':True,
 'model_caveat':'Best searched time-seeded toy PRNG; 199-draw validation fails to show advantage; not identified lottery RNG'}
text=json.dumps(lock,sort_keys=True,indent=2)+'\n'
out=P/'algorithm_forecasts_LOCK.json'
if out.exists():
 assert out.read_text()==text,'Refusing to rewrite immutable lock'
else:out.write_text(text)
print('LOCKED',out,'sha256',hashlib.sha256(out.read_bytes()).hexdigest())
for item in lock['forecasts']:print(item['draw_id'],item['numbers'])
