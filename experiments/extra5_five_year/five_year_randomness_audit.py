#!/usr/bin/env python3
"""Reproducible Monte Carlo / conditional-permutation audit of 3,526 EXTRA 5 draws.

The tests are descriptive. No historical reconstruction is declared from null
p-values. Uses the complete user-authoritative five-year archive.
"""
from __future__ import annotations
import csv,json,math,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.stats import hypergeom,poisson
ROOT=Path(__file__).resolve().parent
N=35;K=5;P=math.comb(35,5)
SEED=20261030
LAGS=[1,2,3,7,14,30]
YEAR_COUNTS=[730,730,732,730,604]

def read_data():
    path=ROOT/'extra5_2022_2026_authoritative.csv'; rows=list(csv.DictReader(path.open()))
    nums=np.array([[int(r[f'n{i}']) for i in range(1,6)] for r in rows],dtype=np.int16)
    ranks=np.array([int(r['lex_rank']) for r in rows],dtype=np.int64)
    return rows,nums,ranks

def setmatrix(nums):
    n=len(nums);x=np.zeros((n,35),dtype=np.int16)
    x[np.repeat(np.arange(n),5),nums.ravel()-1]=1
    return x

def stats(nums,ranks):
    n=len(nums);x=setmatrix(nums)
    count=x.sum(axis=0).astype(float);expected=n*5/35
    pairs=x.T@x;pairmax=int(np.triu(pairs,k=1).max())
    serial=[float(np.bitwise_and((x[:-lag]>0),(x[lag:]>0)).sum(axis=1).mean()) for lag in LAGS]
    years=np.array_split(x,[],axis=0) if False else []
    start=0;year_stat=0
    for size in YEAR_COUNTS:
        c=x[start:start+size].sum(axis=0).astype(float)
        year_stat+=float(np.sum((c-size/7)**2/(size/7)))
        start+=size
    rankbins=np.bincount(np.minimum(ranks*10//P,9),minlength=10)
    uniq,cts=np.unique(ranks,return_counts=True)
    repeats=int(np.sum(cts*(cts-1)//2))
    # Four adjacent positions in each sorted ticket, count consecutive integer pairs.
    adjacent=int(np.sum(np.diff(np.sort(nums,axis=1),axis=1)==1))
    return {'chisq35':float(np.sum((count-expected)**2/expected)),
            'max_number_deviation':float(np.max(np.abs(count-expected))),
            'max_pair_occurrence':pairmax,
            'serial_overlap_by_lag':dict(zip(map(str,LAGS),serial)),
            'year_frequency_chisq':year_stat,
            'rank_decile_chisq':float(np.sum((rankbins-n/10)**2/(n/10))),
            'repeated_ticket_pairs':repeats,
            'adjacent_pairs':adjacent,
            'number_min_count':int(count.min()),'number_max_count':int(count.max()),
            'max_pair_expected':n*20/(35*34),
            'top_ten_number_counts':sorted([(i+1,int(v)) for i,v in enumerate(count)],key=lambda t:-t[1])[:10]}

def two_sided_mc(stat,sims,center):
    return (1+int(np.count_nonzero(abs(sims-center)>=abs(stat-center))))/(len(sims)+1)

def upper_mc(stat,sims):
    return (1+int(np.count_nonzero(sims>=stat)))/(len(sims)+1)

def main(reps=1000,order_reps=1000):
    rows,nums,ranks=read_data();n=len(nums)
    assert n==3526 and np.all((nums>=1)&(nums<=35))
    obs=stats(nums,ranks)
    rng=np.random.default_rng(SEED)
    suite=['chisq35','max_number_deviation','max_pair_occurrence','year_frequency_chisq','rank_decile_chisq','repeated_ticket_pairs','adjacent_pairs']
    samples={key:[] for key in suite}
    maxserial=[]
    expected_overlap=25/35
    observed_serial_max=max(abs(obs['serial_overlap_by_lag'][str(l)]-expected_overlap)*math.sqrt(n-l) for l in LAGS)
    for r in range(reps):
        # Each simulated ticket is selected uniformly without replacement.
        pick=np.argpartition(rng.random((n,35)),4,axis=1)[:,:5].astype(np.int16)+1
        # Uniform rank is used only for marginal rank and birthday tests. It is
        # independent of pick, which affects no reported marginal null statistic.
        fair_rank=rng.integers(P,size=n,dtype=np.int64)
        s=stats(pick,fair_rank)
        for k in suite:samples[k].append(s[k])
        maxserial.append(max(abs(s['serial_overlap_by_lag'][str(l)]-expected_overlap)*math.sqrt(n-l) for l in LAGS))
    tests={}
    for k in suite:
        arr=np.asarray(samples[k]); value=obs[k]
        if k=='repeated_ticket_pairs':
            p=two_sided_mc(value,arr,float(arr.mean()))
        elif k=='adjacent_pairs':
            p=two_sided_mc(value,arr,float(arr.mean()))
        else:p=upper_mc(value,arr)
        tests[k]={'observed':value,'null_mean':float(arr.mean()),'null_q05':float(np.quantile(arr,.05)),
                  'null_q95':float(np.quantile(arr,.95)),'p_two_sided_or_upper_as_defined':p,
                  'tail':'two-sided about simulated mean' if k in ('repeated_ticket_pairs','adjacent_pairs') else 'upper'}
    tests['max_serial_overlap_across_lags']={'observed':observed_serial_max,'null_mean':float(np.mean(maxserial)),
                                                'p_upper':upper_mc(observed_serial_max,np.asarray(maxserial)),
                                                'lags':LAGS,'observed_raw':obs['serial_overlap_by_lag']}
    # Conservatively account for the total number of tested summary families.
    num_families=len(tests)+2
    for t in tests.values():
        p=t.get('p_upper',t.get('p_two_sided_or_upper_as_defined'))
        t['bonferroni_adjusted_p_over_all_families']=min(1.0,p*num_families)
    # Within-draw exchangeability test of recorded *column* order, not verified actual order.
    # Stat: sum across 5 columns and 35 labels of (position_count - overall_count/5)^2 / (overall_count/5).
    x=setmatrix(nums);total=x.sum(axis=0)
    def posstat(mat):
        c=np.zeros((5,35),dtype=np.int32)
        for j in range(5):np.add.at(c[j],mat[:,j]-1,1)
        e=total[None,:]/5
        return float(np.sum((c-e)**2/e))
    obs_pos=posstat(nums)
    pos_dist=[]
    for r in range(order_reps):
        shuffled=np.take_along_axis(nums,np.argsort(rng.random(nums.shape),axis=1),axis=1)
        pos_dist.append(posstat(shuffled))
    tests['position_conditional_permutation']={'observed':obs_pos,'null_mean':float(np.mean(pos_dist)),
      'p_upper':upper_mc(obs_pos,np.asarray(pos_dist)),
      'bonferroni_adjusted_p_over_all_families':min(1,upper_mc(obs_pos,np.asarray(pos_dist))*num_families),
      'interpretation':'tests workbook column ordering, not independently verified mechanical extraction order'}
    # Paired afternoon/evening conditional random sign swaps, null robust to per-day ticket patterns.
    diff=x[0::2]-x[1::2]
    observed_d=diff.sum(axis=0)
    def pair_st(vec):return float(np.sum(vec.astype(float)**2 / np.maximum(total.astype(float),1)))
    obs_day=pair_st(observed_d)
    pm=[]
    for r in range(order_reps):
        s=rng.choice(np.array([-1,1]),size=len(diff));pm.append(pair_st((diff*s[:,None]).sum(axis=0)))
    tests['afternoon_evening_paired_permutation']={'observed':obs_day,'null_mean':float(np.mean(pm)),
        'p_upper':upper_mc(obs_day,np.asarray(pm)),
        'bonferroni_adjusted_p_over_all_families':min(1,upper_mc(obs_day,np.asarray(pm))*num_families)}
    result={
      'dataset':'extra5_2022_2026_authoritative.csv','dataset_sha256':hashlib.sha256((ROOT/'extra5_2022_2026_authoritative.csv').read_bytes()).hexdigest(),
      'draw_count':n,'numbers_observed':n*5,'calibration_replicates':reps,
      'permutation_replicates':order_reps,'seed':SEED,
      'test_method':'uniform 5-without-replacement Monte Carlo; familywise Bonferroni across 10 prespecified summary families; paired and column permutation conditional tests',
      'observed':obs,'tests':tests,
      'interpretation':'A failure to reject tested nulls does not identify a production RNG or certify cryptographic randomness. Statistical associations are not predictive evidence.'}
    (ROOT/'five_year_randomness_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'observed':obs,'tests':tests},indent=2))
    return result

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--reps',type=int,default=1000);a.add_argument('--order-reps',type=int,default=1000)
    args=a.parse_args();main(args.reps,args.order_reps)
