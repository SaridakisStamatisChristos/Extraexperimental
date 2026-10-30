"""Independent cross-language verification: all 20,160 configurations × 2 calendars."""
import csv,json,hashlib
from pathlib import Path
from oracle_joint import generate
R=Path(__file__).resolve().parent
with (R/'train_labeled.csv').open() as f: tr=list(csv.DictReader(f))
with (R/'future_features_only.csv').open() as f: fu=list(csv.DictReader(f))
metas={int(r['draw_id']):r for r in [tr[1],fu[0]]}
mismatches=[];pergen={};cases=0
with (R/'all_20160_config_smoke.csv').open() as f:
 for row in csv.DictReader(f):
  config={k:row[k] for k in ('gen','seed_rule','offset','sampler','permutation')}
  nums,p=generate(metas[int(row['draw_id'])],config)
  expected=([int(row['n'+str(i)]) for i in range(1,6)],int(row['pred_perm_rank']))
  if (nums,p)!=expected and len(mismatches)<6:
    mismatches.append({'config':config,'id':row['draw_id'],'python':(nums,p),'C++':expected})
  pergen[row['gen']]=pergen.get(row['gen'],0)+1
  cases+=1
out={'cases':cases,'distinct_generators':len(pergen),'per_generator':pergen,'mismatches':len(mismatches),'first_mismatches':mismatches,
     'fixture_sha256':hashlib.sha256((R/'all_20160_config_smoke.csv').read_bytes()).hexdigest()}
(R/'full_library_oracle.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
assert cases==40320 and len(pergen)==8 and not mismatches
