#!/usr/bin/env python3
"""Exact hypergeometric calibration and yearwise pair-family falsification.

This is SECONDARY exploratory analysis prompted by the first complete audit.
Do not describe its weakest p-values as preregistered or independent discovery.
"""
import csv,json,math,hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.stats import hypergeom,binom
from scipy.signal import fftconvolve
ROOT=Path(__file__).resolve().parent
YEAR_COUNTS=(730,730,732,730,604)

def poly_power(base,exponent):
    val=np.asarray([1.],dtype=float);p=np.asarray(base,dtype=float)
    while exponent:
        if exponent&1:
            val=np.clip(fftconvolve(val,p),0,None);val/=val.sum()
        exponent//=2
        if exponent:
            p=np.clip(fftconvolve(p,p),0,None);p/=p.sum()
    return val

def exact_overlap_tail(n,total):
    pmf=hypergeom.pmf(np.arange(6),35,5,5)
    m=poly_power(pmf,n)
    return {'draws':n,'observed_hits':total,'expected_hits':n*25/35,
            'variance_per_draw':float(hypergeom.var(35,5,5)),
            'exact_p_at_least_observed':float(m[total:].sum()),
            'exact_p_at_most_observed':float(m[:total+1].sum()),
            'null_q025_hits':int(np.searchsorted(np.cumsum(m),.025)),
            'null_q975_hits':int(np.searchsorted(np.cumsum(m),.975))}

def paircounts(nums):
    n=len(nums);a=np.sort(nums,axis=1)
    cnt=np.zeros(35*35,dtype=np.int32)
    for i in range(5):
        for j in range(i+1,5):
            ids=(a[:,i]-1)*35+(a[:,j]-1)
            cnt+=np.bincount(ids,minlength=35*35).astype(np.int32)
    return cnt.reshape(35,35)

def pair_year_scan(reps=2500,seed=22022026):
    rs=list(csv.DictReader((ROOT/'extra5_2022_2026_authoritative.csv').open()))
    groups=[];out=[]
    for year,n in zip(range(2022,2027),YEAR_COUNTS):
        grp=np.array([[int(r[f'n{i}']) for i in range(1,6)] for r in rs if r['date'][:4]==str(year)],dtype=np.int16)
        assert len(grp)==n
        mx=paircounts(grp);peak=int(mx.max());idx=np.unravel_index(mx.argmax(),(35,35))
        p_raw=float(binom.sf(peak-1,n,20/(35*34)))
        out.append({'year':year,'draws':n,'most_frequent_pair':[int(idx[0]+1),int(idx[1]+1)],
                    'pair_hits':peak,'single_pair_raw_binomial_p':p_raw,
                    'bonferroni_595_pairs':min(1,p_raw*595)})
        groups.append(grp)
    observed_min=min(e['single_pair_raw_binomial_p'] for e in out)
    rng=np.random.default_rng(seed);family_count=0;values=[]
    for rep in range(reps):
        minimum=1.
        for n in YEAR_COUNTS:
            picks=np.argpartition(rng.random((n,35)),4,axis=1)[:,:5].astype(np.int16)+1
            mx=int(paircounts(picks).max())
            p=float(binom.sf(mx-1,n,20/(35*34)))
            if p<minimum:minimum=p
        values.append(minimum)
        if minimum<=observed_min:family_count+=1
    return {'yearwise_results':out,'min_raw_p_across_all_years':observed_min,
            'simultaneous_5_year_595_pairs_familywise_p':(family_count+1)/(reps+1),
            'Monte_Carlo_reps':reps,'Monte_Carlo_seed':seed,
            'interpretation':'Exploratory scan after reviewing main 5-year summaries; not a preregistered discovery.'}

def main():
    seeds=json.loads((ROOT/'seeded_generator_results.json').read_text())
    test=exact_overlap_tail(604,int(seeds['selected_test_hits']))
    val=exact_overlap_tail(730,int(seeds['selected_validation_hits']))
    both=exact_overlap_tail(1334,int(seeds['selected_validation_hits']+seeds['selected_test_hits']))
    groups=pair_year_scan(2500)
    output={'generator_validation_2025':val,'generator_test_2026':test,
            'generator_combined_2025_and_2026':both,'exploratory_pair_year_scan':groups,
            'note':'Exact overlap tails condition on a fixed selected ticket per draw, independent uniform fair-lottery outcomes. Real-world test years have already happened.'}
    (ROOT/'five_year_followup_results.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))
    return output

if __name__=='__main__':main()
