"""Set × permutation × time interaction search with full-family maxT shuffle control.

Only TRAIN labels are read in main fit. Separate evaluator reads sealed holdout
ONLY after selection lock is written. All feature definitions fixed in source.
"""
import csv, json, math, sys, hashlib
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.stats import pearsonr
ROOT=Path(__file__).resolve().parent

def read(file):
    with file.open() as f:return list(csv.DictReader(f))

def unrank_permutation(z):
    r=list(range(5));p=[]
    for i in range(5):
        d=math.factorial(4-i);a,z=divmod(z,d);p.append(r.pop(a))
    return p

@lru_cache(maxsize=None)
def set_from_rank(rank):
    if rank<0:return set()
    vals=[];lo=1
    for j in range(5):
        for v in range(lo,36):
            count=math.comb(35-v,4-j) if 0<=4-j<=35-v else 0
            if rank<count:
                vals.append(v);lo=v+1;break
            rank-=count
    assert len(vals)==5
    return set(vals)

def build(rows):
    n=len(rows)
    s={k:[] for k in (
        'sum_ge90','spread_ge25','min_le5','max_ge30','even_ge3','lex_upper',
        'adjacent_set','overlap_previous','prev_sum_ge90','prev_rank_upper',
        'sum_mod3_zero','min_odd')}
    p={k:[] for k in ('even_perm','first_rel_ge3','last_rel_ge3','first_rel_zero',
                       'last_rel_four','permutation_upper','inversions_ge5','middle_rel_ge3')}
    t={k:[] for k in ('evening','weekend','year_ge2024','first_half','ordinal_odd',
                        'mon_tue_wed','id_mod3zero','id_mod7high')}
    for row in rows:
        sort=[int(row['s'+str(i)]) for i in range(1,6)]
        mask={int(v) for v in sort};d=int(row['date_ordinal']);pid=int(row['draw_id'])
        prevsetrank=int(row['prev_set_rank']);prevsort=set_from_rank(prevsetrank)
        # overlap between sets only available as future features if previous actual set is included;
        # instead use precomputed previous-set-derived count approximation via rank equality (rare).
        S=[sum(sort)>=90,sort[-1]-sort[0]>=25,sort[0]<=5,sort[-1]>=30,
            sum(v%2==0 for v in sort)>=3,int(row['set_rank'])>=324632//2,
            any(sort[i+1]==sort[i]+1 for i in range(4)),len(mask&prevsort)>=1,
            int(row['prev_sum'])>=90,prevsetrank>=324632//2,
            sum(sort)%3==0,sort[0]%2==1]
        for k,v in zip(s,S):s[k].append(int(v))
        pi=unrank_permutation(int(row['perm_rank']))
        inversions=sum(pi[i]>pi[j] for i in range(5) for j in range(i+1,5))
        P=[inversions%2==0,pi[0]>=3,pi[4]>=3,pi[0]==0,pi[4]==4,
            int(row['perm_rank'])>=60,inversions>=5,pi[2]>=3]
        for k,v in zip(p,P):p[k].append(int(v))
        day_of_week=(d-1)%7 # Python ordinal 1 is Monday
        month=__import__('datetime').date.fromordinal(d).month
        T=[int(row['time_slot'])==1,day_of_week>=5,int(row['year'])>=2024,month<=6,
            d%2==1,day_of_week<=2,pid%3==0,pid%7>=4]
        for k,v in zip(t,T):t[k].append(int(v))
    return s,p,t

def stdcol(x):
    x=np.asarray(x,dtype=np.float64);x=x-x.mean()
    sd=np.sqrt(np.mean(x*x));return x/sd if sd>0 else x

def components(rows):
    S,P,T=build(rows)
    z_names=[]; z_cols=[]
    for sname,sv in S.items():
      for tname,tv in T.items():
        z_names.append((sname,tname));
        z_cols.append(stdcol(stdcol(sv)*stdcol(tv)))
    return z_names, np.ascontiguousarray(np.stack(z_cols,axis=1)),list(P),np.ascontiguousarray(np.stack([stdcol(v) for v in P.values()],axis=1))

def fit(reps=1000):
    rows=read(ROOT/'train_labeled.csv');names,Z,pnames,P=components(rows)
    n=len(rows);corr=Z.T@P/n
    ix,iy=np.unravel_index(np.argmax(np.abs(corr)),corr.shape)
    obs=float(abs(corr[ix,iy])); real=float(corr[ix,iy])
    rng=np.random.default_rng(20261030);mx=[]
    for rep in range(reps):
        inds=rng.permutation(n)
        maxima=float(np.max(np.abs(Z.T@P[inds])/n));mx.append(maxima)
        if (rep+1)%200==0: print('3-way null',rep+1,'/',reps,flush=True)
    p=(1+sum(v>=obs-1e-12 for v in mx))/(reps+1)
    lock={'train_n':n,'hypotheses':int(corr.size), 'feature':{'set':names[ix][0], 'time':names[ix][1], 'permutation':pnames[iy]},
          'train_correlation':real,'train_abs_correlation':obs,'maxT_null_replicates':reps,
          'maxT_exceedances':sum(v>=obs-1e-12 for v in mx),'maxT_p':p,
          'null_max_q50_q95_q99':np.quantile(mx,[.5,.95,.99]).tolist(),
          'train_sha256':hashlib.sha256((ROOT/'train_labeled.csv').read_bytes()).hexdigest()}
    (ROOT/'FROZEN_INTERACTION3D.json').write_text(json.dumps(lock,indent=2)+'\n')
    print('INTERACTION LOCK',json.dumps(lock,indent=2));return lock

def evaluate():
    lockpath=ROOT/'FROZEN_INTERACTION3D.json'
    if not lockpath.is_file():raise RuntimeError('train lock required before revealing future labels')
    lock=json.loads(lockpath.read_text());rows=read(ROOT/'sealed/future_labels.csv')
    S,P,T=build(rows);s=lock['feature']['set'];t=lock['feature']['time'];p=lock['feature']['permutation']
    z=stdcol(stdcol(S[s])*stdcol(T[t]));y=stdcol(P[p]);r=float(np.mean(z*y))
    rng=np.random.default_rng(20261031)
    null=np.array([np.mean(z*y[rng.permutation(len(y))]) for _ in range(5000)])
    pval=(1+np.count_nonzero(np.abs(null)>=abs(r)-1e-12))/(5001)
    result={'heldout_draws':len(rows),'train_frozen_feature':lock['feature'],
            'train_correlation':lock['train_correlation'],'holdout_correlation':r,
            'direction_replicated':(r*lock['train_correlation']>0),
            'holdout_two_sided_permutation_p':float(pval),'holdout_shuffle_reps':5000,
            'statement':'Not an exact ticket predictor; three-way observation-only dependence test, retrospective split.'}
    (ROOT/'interaction_evaluation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('INTERACTION TEST',json.dumps(result,indent=2))

if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('fit','evaluate'):raise SystemExit('usage: python interaction3d.py fit|evaluate')
    fit() if sys.argv[1]=='fit' else evaluate()
