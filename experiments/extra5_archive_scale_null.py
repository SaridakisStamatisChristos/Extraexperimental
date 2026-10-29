#!/usr/bin/env python3
"""EXTRA 5: account for retrospective selection across a long lottery history.

Uniform 5-of-35, independent draws. No actual historical draws beyond the supplied
100-draw archive are loaded or invented. We use public last-draw ID ONLY as a
*conservative hypothetical scan horizon*, not a certified count of eligible draws.
"""
import argparse,csv,hashlib,json,math,platform,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent

def sample_sets(rng,b,n):
    """Rejection-resample entire 5-vector until all 5 unique: exact uniform 5-subset."""
    x=rng.integers(0,35,size=(b,n,5),dtype=np.int16)
    while True:
        bad=np.zeros((b,n),dtype=np.bool_)
        for j in range(1,5):
            for k in range(j): bad |= x[:,:,j]==x[:,:,k]
        nbad=int(bad.sum())
        if not nbad:return x
        x[bad]=rng.integers(0,35,size=(nbad,5),dtype=np.int16)

def null_fixed(rng,draws,window,threshold,replicates,batch):
    small=0
    for offset in range(0,replicates,batch):
        b=min(batch,replicates-offset)
        x=sample_sets(rng,b,window)
        j=np.repeat(np.arange(b),window*5)*35+x.reshape(-1)
        counts=np.bincount(j,minlength=b*35).reshape(b,35)
        ss=np.sum(counts*counts,axis=1)
        small+=int(np.count_nonzero(ss<=threshold))
    return small

def null_global(rng,draws,window,threshold,replicates,batch):
    small=0; hist=[]
    for offset in range(0,replicates,batch):
        b=min(batch,replicates-offset)
        x=sample_sets(rng,b,draws)
        Y=np.zeros((b,draws,35),dtype=np.uint8)
        Y[np.arange(b)[:,None,None],np.arange(draws)[None,:,None],x]=1
        counts=np.cumsum(Y,axis=1,dtype=np.int16)
        # Append zero prefix and compute all overlapping window counts.
        counts=np.concatenate([np.zeros((b,1,35),dtype=np.int16),counts],axis=1)
        W=counts[:,window:,:]-counts[:,:-window,:]
        ss=np.einsum('bti,bti->bt',W.astype(np.int32),W.astype(np.int32),optimize=True)
        m=ss.min(axis=1)
        small+=int(np.count_nonzero(m<=threshold))
        hist.extend(m.tolist())
        if (offset+batch) % 200 == 0: print(f'global {offset+batch}/{replicates}',flush=True)
    return small,np.array(hist)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--replicates',type=int,default=1000)
    parser.add_argument('--fixed-replicates',type=int,default=100000)
    parser.add_argument('--scan-horizon',type=int,default=14355)
    parser.add_argument('--seed',type=int,default=202610291)
    parser.add_argument('--out',default=str(ROOT/'extra5_archive_scale_null_results.json'))
    args=parser.parse_args()
    data=list(csv.DictReader(open(ROOT/'extra5_last100_data.csv',encoding='utf-8-sig')))
    assert len(data)==100
    ids=[int(r['draw_id']) for r in data]
    assert ids==list(range(14256,14356))
    arr=np.array([[int(r[f'n{i}']) for i in range(1,6)] for r in data])
    assert ((arr>=1)&(arr<=35)).all() and all(len(set(row))==5 for row in arr)
    # This was already selected in a previous analysis. Do NOT treat as holdout.
    W=np.zeros((21,35),dtype=np.int16)
    for i in range(21):
        W[i]=np.bincount(arr[i:i+80].reshape(-1),minlength=36)[1:]
    ss=np.sum(W.astype(np.int32)**2,axis=1)
    i=int(np.argmin(ss)); target=int(ss[i]); observed_sd=float(math.sqrt((target-160000/35)/35))
    # Fixed and global experiments seeded independently so they are reproducible.
    t=time.time()
    fixed=null_fixed(np.random.default_rng(args.seed),args.scan_horizon,80,target,args.fixed_replicates,400)
    prob=(fixed+1)/(args.fixed_replicates+1)
    exactind=1-(1-prob)**(args.scan_horizon//80)
    global_hits,minima=null_global(np.random.default_rng(args.seed+1),args.scan_horizon,80,target,args.replicates,5)
    globalp=(global_hits+1)/(args.replicates+1)
    out={
      'research_date':'2026-10-29','status':'executed simulation, exploratory look-elsewhere calibration',
      'empirical_window_from_prior_100_draw_archive':[ids[i],ids[i+79]],
      'empirical_min_80_window_appearance_sd':observed_sd,
      'sum_of_35_squared_appearance_counts_integer_threshold':target,
      'scan_horizon_hypothetical_draws':args.scan_horizon,
      'possible_overlapping_80_windows':args.scan_horizon-79,
      'disjoint_80_windows':args.scan_horizon//80,
      'fixed_80_window':{'replicates':args.fixed_replicates,'extreme_count':fixed,'plus_one_p':prob},
      'independent_disjoint_window_reference':{'windows':args.scan_horizon//80,'probability_any_extreme':exactind,
          'note':'uses simulated fixed-window p as plug-in; reference for a prespecified set of disjoint blocks, not the actual dataset'},
      'full_sliding_scan_null':{'replicates':args.replicates,'extreme_count':global_hits,'plus_one_p':globalp,
          'null_min_threshold_quantiles':np.quantile(minima,[0,0.05,0.25,0.5,0.75,0.95,1]).tolist()},
      'null_model':'independent uniformly random unordered 5-of-35 sets; each 5-vector sampled uniformly conditional on distinctness',
      'selection_limitation':'This calculates what would happen *if* 14,355 draws were eligible to be scanned. We have not obtained or audited the true earlier draws. The observed 80-window was found by post-hoc inspection. It is not a prospectively selected observation or evidence of predictive power.',
      'python':platform.python_version(),'numpy':np.__version__,'seed_fixed':args.seed,'seed_global':args.seed+1,'elapsed_seconds':time.time()-t,
      'data_sha256_normalized_csv':hashlib.sha256(('\n'.join((ROOT/'extra5_last100_data.csv').read_text(encoding='utf-8-sig').splitlines())).encode('utf-8')).hexdigest()}
    Path(args.out).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
