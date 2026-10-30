"""Score only after frozen prediction files exist. No retraining or future label reuse."""
import csv,json,hashlib
from pathlib import Path
from scipy.stats import binomtest
R=Path(__file__).resolve().parent
lock=R/'FROZEN_AFFINE3D_models.csv'; preds=R/'FROZEN_AFFINE3D_future.csv'
assert lock.exists() and preds.exists(), 'must lock training models before opening holdout'
with (R/'sealed/future_labels.csv').open() as f:
  actual={int(x['draw_id']):x for x in csv.DictReader(f)}
with preds.open() as f: data=list(csv.DictReader(f))
from collections import defaultdict
per=defaultdict(list)
for item in data:
  key=item['x_axis']+'/'+item['t_axis']; truth=actual[int(item['draw_id'])]
  per[key].append((int(truth['year']), int(item['predicted_perm_rank'])==int(truth['perm_rank'])))
result=[]
for key, rows in per.items():
  k25=sum(ok for year,ok in rows if year==2025);k26=sum(ok for year,ok in rows if year==2026);k=k25+k26
  result.append({'model':key,'2025_exact_permutation':k25,'2026_exact_permutation':k26,
    'combined_exact_permutation':k,'expected_combined':len(rows)/120,
    'binomial_one_sided_p':binomtest(k,len(rows),1/120,alternative='greater').pvalue,
    'relative_to_baseline':k/(len(rows)/120)})
result.sort(key=lambda r:r['combined_exact_permutation'],reverse=True)
summary={'frozen_models_sha256':hashlib.sha256(lock.read_bytes()).hexdigest(),
    'frozen_predictions_sha256':hashlib.sha256(preds.read_bytes()).hexdigest(),
    'holdout_draws':1334,'description':'Retrospective execution-time split; 2025/2026 already used in older research, NOT untouched globally',
    'current_set_models': 'conditional order reconstruction only, current set unknown before draw',
    'previous_*_models':'one-step-ahead order forecasts using previously revealed outcomes',
    'results':result}
(R/'evaluation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
