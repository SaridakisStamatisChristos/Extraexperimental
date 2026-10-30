"""Third-stage scoring: opens sealed labels only after fitted models and predictions exist."""
import csv,json,hashlib
from pathlib import Path
from scipy.stats import binomtest
R=Path(__file__).resolve().parent
lock=R/'FROZEN_JOINT3D_models.csv'; predictions=R/'FROZEN_JOINT3D_future.csv'
assert lock.is_file() and predictions.is_file(), 'models and future tickets must be frozen before scoring'
with (R/'sealed/future_labels.csv').open() as f: actual={int(x['draw_id']):x for x in csv.DictReader(f)}
with predictions.open() as f: pred=list(csv.DictReader(f))
from collections import defaultdict
arms=defaultdict(list)
for r in pred:
    draw=actual[int(r['draw_id'])]
    generated={int(r[f'n{i}']) for i in range(1,6)}
    real={int(draw[f'n{i}']) for i in range(1,6)}
    n=len(generated&real);sameperm=int(r['pred_perm_rank'])==int(draw['perm_rank'])
    assert len(generated)==5
    arms[r['objective']].append({'year':int(draw['year']),'draw_id':int(r['draw_id']),
                                'number_hits':n,'permutation_match':sameperm})
p4=151/324632
summary=[]
for objective,rows in arms.items():
  years=[]
  for y in (2025,2026):
    a=[r for r in rows if r['year']==y]
    years.append({'year':y,'draws':len(a),'number_matches':sum(r['number_hits'] for r in a),
     'four_plus':sum(r['number_hits']>=4 for r in a),'five_exact':sum(r['number_hits']==5 for r in a),
     'permutation_exact':sum(r['permutation_match'] for r in a),
     'joint_four_plus_perm':sum(r['number_hits']>=4 and r['permutation_match'] for r in a),
     'four_plus_draws':[r['draw_id'] for r in a if r['number_hits']>=4]})
  rare=sum(y['four_plus'] for y in years);nh=sum(y['number_matches'] for y in years);perm=sum(y['permutation_exact'] for y in years);j=sum(y['joint_four_plus_perm'] for y in years)
  summary.append({'objective':objective,'yearly':years,'combined_four_plus':rare,'combined_number_hits':nh,
    'combined_perm_correct':perm,'combined_joint_four_plus_correct_perm':j,
    'expected_number_hits':1334*25/35,'expected_four_plus':1334*p4,
    'one_sided_four_plus_p':binomtest(rare,1334,p4,alternative='greater').pvalue,
    'one_sided_permutation_p':binomtest(perm,1334,1/120,alternative='greater').pvalue,
    'one_sided_joint_p':binomtest(j,1334,p4/120,alternative='greater').pvalue})
report={'models_sha256':hashlib.sha256(lock.read_bytes()).hexdigest(),
        'frozen_forecasts_sha256':hashlib.sha256(predictions.read_bytes()).hexdigest(),
        'forecast_contract':'one-step ahead: previous known actual outcome may influence seed, NO current outcome used',
        'development_years':'2022-2024','evaluation_years':'2025-2026','globally_blind':False,
        'results':summary}
(R/'joint_evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
