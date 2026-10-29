#!/usr/bin/env python3
"""EXTRA 5 100-draw fixed-protocol retrospective diagnostics (no predictive claim).

Null: independent uniform unordered 5-of-35 tickets. Deterministic Monte Carlo
calibrations for a retrospectively noticed 80-draw interval, the minimum across
all 21 such windows, and the maximum overlap deviation at lags 1..5.
"""
import argparse,csv,json,math,platform,hashlib
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.stats import hypergeom, chi2
P=Path(__file__).resolve().parent

def read_draws(path):
    rows=list(csv.DictReader(open(path,newline='',encoding='utf-8-sig')))
    ids=[int(r['draw_id']) for r in rows]
    if ids!=list(range(14256,14356)):
        raise ValueError('expected consecutive draws 14256..14355')
    X=np.zeros((100,35),dtype=np.uint8)
    for j,r in enumerate(rows):
        values=[int(r[f'n{k}']) for k in range(1,6)]
        if len(set(values))!=5 or not all(1<=v<=35 for v in values):
            raise ValueError(f'invalid draw {ids[j]}')
        X[j,np.array(values)-1]=1
    return ids,X

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',type=Path,default=P/'extra5_last100_data.csv')
    ap.add_argument('--iterations',type=int,default=20000)
    ap.add_argument('--seed',type=int,default=20261029)
    ap.add_argument('--out',type=Path,default=P/'extra5_serial_window_results.json')
    args=ap.parse_args()
    ids,X=read_draws(args.data)
    # Interval previously noticed in public cumulative-frequency snapshots.
    windows=np.stack([X[i:i+80].sum(axis=0,dtype=np.int32) for i in range(21)])
    ss=np.sum((windows-400/35)**2,axis=1)
    target_i=14268-ids[0]
    target_ss=float(ss[target_i]); min_idx=int(np.argmin(ss));min_ss=float(ss[min_idx])
    # Within-draw frequency Pearson adjusted for hypergeometric covariance.
    f=X.sum(axis=0,dtype=np.int32); expected=500/35
    uniform_stat=float(np.sum((f-expected)**2/expected)*34/30)
    unif_p=float(chi2.sf(uniform_stat,34))
    overlaps={str(lag):int(np.sum(X[:-lag]*X[lag:])) for lag in range(1,6)}
    variance=5*(5/35)*(1-5/35)*((35-5)/(35-1))
    mean=5/7
    z={str(lag):float((overlaps[str(lag)]-(100-lag)*mean)/np.sqrt((100-lag)*variance)) for lag in range(1,6)}
    maxz=max(abs(v) for v in z.values())
    lag1_hist={str(i):int(v) for i,v in sorted(Counter(np.sum(X[1:]*X[:-1],axis=1).tolist()).items())}
    lag_p=[float(hypergeom.pmf(i,35,5,5)) for i in range(6)]
    rng=np.random.default_rng(args.seed)
    low_target=low_scan=high_lags=low_full=0
    B=250
    for begin in range(0,args.iterations,B):
        b=min(B,args.iterations-begin)
        tickets=np.argpartition(rng.random((b,100,35)),5,axis=2)[:,:,:5]
        Y=np.zeros((b,100,35),dtype=np.uint8)
        Y[np.arange(b)[:,None,None],np.arange(100)[None,:,None],tickets]=1
        prefix=np.concatenate((np.zeros((b,1,35),dtype=np.int16),np.cumsum(Y,axis=1,dtype=np.int16)),axis=1)
        W=prefix[:,80:,:]-prefix[:,:21,:]
        q=np.sum((W-400/35)**2,axis=2)
        fullcounts=Y.sum(axis=1,dtype=np.int32)
        fullstat=np.sum((fullcounts-500/35)**2/(500/35),axis=1)*34/30
        low_full+=int(np.count_nonzero(fullstat<=uniform_stat+1e-10))
        low_target+=int(np.count_nonzero(q[:,target_i]<=target_ss+1e-10))
        low_scan+=int(np.count_nonzero(q.min(axis=1)<=min_ss+1e-10))
        zz=np.stack([np.abs(((Y[:,:-lag]*Y[:,lag:]).sum(axis=(1,2))-(100-lag)*mean)/np.sqrt((100-lag)*variance)) for lag in range(1,6)],axis=1)
        high_lags+=int(np.count_nonzero(zz.max(axis=1)>=maxz-1e-10))
    mc=lambda x:(x+1)/(args.iterations+1)
    result={
        'research_date':'2026-10-29','dataset':'extra5_last100_data.csv','draw_id_first':ids[0], 'draw_id_last':ids[-1],
        'dataset_canonical_sha256': hashlib.sha256(json.dumps([[int(ids[i]), *(np.flatnonzero(X[i])+1).tolist()] for i in range(100)],separators=(',',':')).encode()).hexdigest(),
        'num_draws':100,'num_80draw_windows':21,'null':'iid uniform 5-of-35 unordered subsets',
        'global_uniformity':{'statistic_chi_square_adjusted_34df':uniform_stat,'asymptotic_upper_tail_p':unif_p,'asymptotic_lower_tail_p':1-unif_p,'mc_lower_tail_p':mc(low_full),'extreme_lower':low_full,'min_count':int(f.min()),'max_count':int(f.max())},
        'window_80':{'target_draw_ids':[14268,14347],'target_std_pop':math.sqrt(target_ss/35),'target_ss':target_ss,'min_window_draw_ids':[ids[min_idx],ids[min_idx+79]],'min_window_std_pop':math.sqrt(min_ss/35),'mc_fixed_window_lower_p':mc(low_target),'mc_min_of_21_lower_p':mc(low_scan),'extreme_fixed':low_target,'extreme_min_scan':low_scan},
        'serial':{'adjacent_histogram':lag1_hist,'null_overlap_probs_k0_to_5':lag_p,'observed_sum_overlap_by_lag':overlaps,'standardized_z_by_lag':z,'max_abs_z_lags_1_to_5':maxz,'mc_familywise_max_abs_z_p':mc(high_lags),'extreme_max_abs_z':high_lags},
        'mc':{'iterations':args.iterations,'seed':args.seed,'generator':'numpy default_rng PCG64','sampler':'5 smallest iid continuous uniforms per draw, uniform without replacement','plus_one':True},
        'software':{'python':platform.python_version(),'numpy':np.__version__},
        'interpretation':'Exploratory retrospective 100-draw sample; p-values do not imply prediction; 21-window correction applies only within 100-draw archive.'}
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':
    main()
