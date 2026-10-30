#!/usr/bin/env python3
"""Independent holdout evaluation. Does not import the fitter or its data."""
from pathlib import Path
import csv,hashlib,json,math
from scipy.stats import hypergeom
import numpy as np
P=Path(__file__).resolve().parent

def score(holdout,lock):
    data=list(csv.DictReader(open(holdout,newline='')))
    forecast=json.loads(Path(lock).read_text())
    assert len(data)==len(forecast['forecasts'])==5
    assert [int(r['draw_id']) for r in data]==[f['draw_id'] for f in forecast['forecasts']]
    out=[]
    for row,p in zip(data,forecast['forecasts']):
        actual=sorted(int(row[f'n{i}']) for i in range(1,6))
        predicted=sorted(p['numbers'])
        assert len(set(predicted))==5 and all(1<=x<=35 for x in predicted)
        out.append({'draw_id':int(row['draw_id']),'actual':actual,'prediction':predicted,
                    'overlap':len(set(actual)&set(predicted)),'exact':actual==predicted})
    hits=sum(x['overlap'] for x in out)
    law=np.array([hypergeom.pmf(k,35,5,5) for k in range(6)],dtype=float)
    totals=law
    for i in range(4):totals=np.convolve(totals,law)
    assert abs(totals.sum()-1)<1e-12
    return {'training_draws':599,'holdout_draws':5,'evaluation':'retrospective, separated code path',
            'lock_sha256':hashlib.sha256(Path(lock).read_bytes()).hexdigest(),
            'holdout_sha256':hashlib.sha256(Path(holdout).read_bytes()).hexdigest(),
            'outcomes':out,'total_number_matches':hits,'exact_ticket_matches':sum(x['exact'] for x in out),
            'uniform_expected_total_matches':25/7,
            'fair_lottery_one_sided_tail_probability':float(totals[hits:].sum()),
            'chance_full_ticket_probability_per_draw':1/math.comb(35,5)}
if __name__=='__main__':
    out=score(P/'holdout_5_PRIVATE.csv',P/'algorithm_forecasts_LOCK.json')
    (P/'holdout_algorithm_results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
