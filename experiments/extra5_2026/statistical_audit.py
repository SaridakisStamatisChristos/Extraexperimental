#!/usr/bin/env python3
"""Predeclared simulation-calibrated EXTRA5 2026 generator fingerprints.

Null: independent uniformly sampled five-element subsets of 1..35.
Observe unordered sets; optionally test recorded order *conditionally* on sets.
This cannot identify a secure RNG, the RNG seed, or the sampler implementation.
"""
from __future__ import annotations
import csv,hashlib,json,math
from collections import Counter
from datetime import date
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
CSV=HERE/'extra5_authoritative_2026.csv'
N=math.comb(35,5)
COMB=np.asarray([[math.comb(i,j) if i>=j else 0 for j in range(6)] for i in range(36)], dtype=np.int64)

def load_data(path=CSV):
    with path.open(newline='',encoding='utf8') as handle:
        r=list(csv.DictReader(handle))
    ids=[int(row['draw_id']) for row in r]
    assert ids==list(range(13754,14358)) and len(r)==604
    ordered=np.array([[int(row[f'n{i}']) for i in range(1,6)] for row in r],dtype=np.int16)
    sorted_=np.sort(ordered,axis=1)
    assert all(np.array_equal(sorted_[i],[int(r[i][f's{j}']) for j in range(1,6)]) for i in range(len(r)))
    assert np.all((1<=sorted_)&(sorted_<=35)) and np.all(np.diff(sorted_,axis=1)>0)
    return r,ordered,sorted_

def ranks(sorted_nums):
    ans=np.full(len(sorted_nums),N-1,dtype=np.int64)
    for j in range(5):ans-=COMB[35-sorted_nums[:,j],5-j]
    return ans

def sample_sequences(rng,n):
    # Selecting the five smallest i.i.d. continuous keys yields exact random
    # unordered subsets except for floating-point tie probability (negligible).
    keys=rng.random((n,35))
    return np.sort(np.argpartition(keys,5,axis=1)[:,:5]+1,axis=1).astype(np.int16)

def mask_of(tickets):
    n=len(tickets)
    m=np.zeros((n,35),dtype=np.int8)
    m[np.arange(n)[:,None],tickets-1]=1
    return m

def position_stat(ordered):
    counts=np.zeros((5,35),dtype=np.int32)
    for j in range(5):counts[j]=np.bincount(ordered[:,j]-1,minlength=35)
    return float(np.sum((counts-ordered.shape[0]/35)**2/(ordered.shape[0]/35)))

def stats(tickets,hours,weekend):
    n=len(tickets)
    m=mask_of(tickets)
    cnt=m.sum(axis=0)
    mu=n/7
    # 5-of-35 marginal indicator p=1/7, each count variance n*6/49.
    single_z=np.max(np.abs(cnt-mu))/math.sqrt(n*6/49)
    freq_chi=np.sum((cnt-mu)**2/mu)
    # Each unordered pair is counted once for each ticket.
    joint=np.zeros((35,35),dtype=np.int16)
    for i in range(4):
        for j in range(i+1,5):
            np.add.at(joint,(tickets[:,i]-1,tickets[:,j]-1),1)
    max_pair=float(np.max(joint))
    overlaps={}
    for lag in (1,2,3,7,14,30):
        overlaps[f'lag{lag}_mean_overlap']=float((m[lag:]*m[:-lag]).sum()/(n-lag))
    adj=float(np.sum(np.diff(tickets,axis=1)==1))
    repeat_pairs=sum(v*(v-1)//2 for v in Counter(map(tuple,tickets)).values())
    rr=np.sort(ranks(tickets))
    u=(rr+0.5)/N
    ks=float(max(np.max(np.arange(1,n+1)/n-u),np.max(u-np.arange(n)/n)))
    day=m[hours==0].sum(axis=0)
    night=m[hours==1].sum(axis=0)
    tod=float(np.sum((day-night)**2/(day+night+1e-8)))
    wd=m[weekend==0].sum(axis=0)
    we=m[weekend==1].sum(axis=0)
    weekend_totals=np.array([np.sum(weekend==0),np.sum(weekend==1)])*5
    day_expected=cnt*weekend_totals[0]/sum(weekend_totals)
    night_expected=cnt*weekend_totals[1]/sum(weekend_totals)
    wk=float(np.sum((wd-day_expected)**2/(day_expected+1e-8)+(we-night_expected)**2/(night_expected+1e-8)))
    return {'frequency_chi':float(freq_chi),'max_marginal_z':float(single_z),
            'max_pair_count':max_pair,'adjacent_values':adj,'ticket_rank_ks':ks,
            'duplicate_pairs':float(repeat_pairs),'time_of_day_chi':tod,'weekend_chi':wk,
            'mean_ticket_sum':float(np.mean(tickets.sum(axis=1))),**overlaps}

# All statistics will be included in one one-sided maxT test except for
# centered mean_ticket_sum and overlaps (two-sided); no fishing by dropping tests.
TWO_SIDED={'mean_ticket_sum',*(f'lag{lag}_mean_overlap' for lag in (1,2,3,7,14,30))}

def audit(calibration=700,null_runs=3000,order_runs=4000,seed=20261030):
    rows,ordered,draws=load_data()
    dates=[date.fromisoformat(row['date']) for row in rows]
    hours=np.array([0 if row['time']=='15:00' else 1 for row in rows],dtype=np.int8)
    weekend=np.array([int(d.weekday()>=5) for d in dates],dtype=np.int8)
    rng=np.random.default_rng(seed)
    observed=stats(draws,hours,weekend)
    keys=list(observed)
    def sample_stat():return stats(sample_sequences(rng,len(draws)),hours,weekend)
    cal=np.array([[s[k] for k in keys] for s in (sample_stat() for _ in range(calibration))],dtype=float)
    mu=cal.mean(axis=0);sd=cal.std(axis=0,ddof=1)
    assert np.all(sd>0)
    def z(v):
        zz=(v-mu)/sd
        zz[np.array([k in TWO_SIDED for k in keys])]=np.abs(zz[np.array([k in TWO_SIDED for k in keys])])
        return zz
    observed_vec=np.array([observed[k] for k in keys])
    observed_z=z(observed_vec)
    maxima=[];marginal=np.zeros(len(keys),dtype=np.int64)
    for _ in range(null_runs):
        run=sample_stat()
        v=z(np.array([run[k] for k in keys]))
        maxima.append(float(np.max(v)))
        marginal+=(v>=observed_z)
    maxima=np.array(maxima)
    global_p=(1+np.sum(maxima>=np.max(observed_z)))/(null_runs+1)
    adjusted={k:float((1+np.sum(maxima>=v))/(null_runs+1)) for k,v in zip(keys,observed_z)}
    unadj={k:float((1+c)/(null_runs+1)) for k,c in zip(keys,marginal)}

    pos_obs=position_stat(ordered)
    greater=0
    for _ in range(order_runs):
        perm=rng.random(ordered.shape).argsort(axis=1)
        ordered_shuffle=np.take_along_axis(ordered,perm,axis=1)
        greater+=position_stat(ordered_shuffle)>=pos_obs
    p_order=(greater+1)/(order_runs+1)
    report={
      'experiment':'EXTRA5-2026-FULL-SEQUENCE-NULL-AUDIT-v1',
      'dataset_sha256':hashlib.sha256(CSV.read_bytes()).hexdigest(),
      'draws':len(draws),'observed_range':[int(rows[0]['draw_id']),int(rows[-1]['draw_id'])],
      'null_hypothesis':'independent uniform five-element subsets of 1..35, with conditional position permutations',
      'sample_seed':seed,'calibration_runs':calibration,'null_runs':null_runs,'position_permutation_runs':order_runs,
      'metric_names_predeclared':keys,
      'observed_metrics':{k:round(float(observed[k]),9) for k in keys},
      'null_calibration_mean':dict(zip(keys,mu.tolist())),
      'null_calibration_sd':dict(zip(keys,sd.tolist())),
      'standardized_deviations':dict(zip(keys,observed_z.tolist())),
      'individual_tail_p':unadj,'global_maxT_p_value':float(global_p),
      'familywise_adjusted_p':adjusted,
      'recorded_order_position_chi_square':pos_obs,
      'conditional_position_permutation_p':p_order,
      'supports_predictive_edge':False,
      'caveats':[
        'Exploratory 2026 data already inspected during previous research; cannot be labeled untouched holdout.',
        'Simulated maxT calibrates this predeclared battery but does not prove independence, secure RNG, or absence of subtle bias.',
        'Correct positional interpretation of n1..n5 remains unverified against primary raw extraction records.',
        'Multiple statistical hypotheses require familywise or preregistered correction; nominal isolated p-values are not discoveries.'
      ]
    }
    (HERE/'statistical_audit_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'draws':len(draws),'global_maxT_p_value':global_p,
         'min_individual_p':min(unadj.values()),'min_familywise_adjusted_p':min(adjusted.values()),
         'position_permutation_p':p_order,
         'most_extreme_metric':max(keys,key=lambda k: observed_z[keys.index(k)]),
         'observed_metrics':report['observed_metrics']},indent=2))
    return report
if __name__=='__main__':audit()
