#!/usr/bin/env python3
"""Exact affine-hull constraint extraction for unordered 5/35 tickets.
When every admissible fourth index has the same parity against an index mask,
that parity is a genuine linear equation in the initial state for a GF(2)-linear
PRNG that emits linear word bits and consumes precisely five words per ticket.
Does not use actual extraction order, planted indices, or hidden state.
"""
from pathlib import Path
import sys,time,csv,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inverse_linear import MODELS,forms,solve_equations,ticket,replay
from affine import fourth_domain, affine_constraints

def recover(tickets,model,gap=0,sampler='high',limit=None):
    """Returns witness or UNKNOWN (nullspace remaining) or UNSAT (provable contradiction).
    SAT only after independent complete ticket replay. A rank-complete solution
    is unique within exactly the model's state space.
    """
    n=len(tickets) if limit is None else min(limit,len(tickets))
    if n<1:raise ValueError('need some tickets')
    started=time.monotonic()
    lin=forms(model,n,gap,sampler)
    equations=[];informative=0
    for d,nums in enumerate(tickets[:n]):
        rules=affine_constraints(fourth_domain(nums))
        if rules:informative+=1
        for mask,rhs in rules:
            row=0
            for bit in range(5):
                if mask&(1<<bit):row^=lin[d][bit]
            equations.append((row,rhs))
    result=solve_equations(equations,model.size)
    outcome={'model':model.name,'sampler':sampler,'gap':gap,'observed_tickets':n,
        'affine_informative_tickets':informative,'total_parity_equations':len(equations),
        'rank':result.rank,'nullity':model.size-result.rank,'seconds':round(time.monotonic()-started,6)}
    if result.status=='UNSAT':
        outcome.update(status='UNSAT',reason='inconsistent necessary GF(2) equations',conflicting_row=result.conflicting_row)
    elif result.rank < model.size:
        outcome.update(status='UNKNOWN',reason='linear system has nonzero nullspace; full ticket search not performed')
    else:
        ok=replay(model,result.seed,tickets[:n],gap,sampler)
        outcome.update(status='SAT' if ok else 'UNSAT',recovered_seed=f'0x{result.seed:0{model.size//4}x}',
            reason='unique state fully replayed' if ok else 'unique parity-compatible state fails full ticket replay')
    return outcome

def synthetic(seed,n,model,gap,sampler):
    state=model.from_integer(seed);data=[]
    for _ in range(n):
        state,vals,_=ticket(model,state,gap,sampler)
        data.append(vals)
    return data

def csv_tickets(path):
    with open(path,newline='') as f:
        for row in csv.DictReader(f):
            mask=int(row['ticket_mask']);
            if mask==0:yield None
            else:yield tuple(i+1 for i in range(35) if mask&(1<<i))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',choices=list(MODELS),default='xorshift128')
    p.add_argument('--seed',type=lambda s:int(s,0),default=0x8877665544332211ffeeddccbbaa9988)
    p.add_argument('--n',type=int,default=600);p.add_argument('--gap',type=int,default=0)
    p.add_argument('--sampler',choices=['mod','high'],default='high')
    args=p.parse_args();m=MODELS[args.model]
    t=synthetic(args.seed,args.n+100,m,args.gap,args.sampler)
    result=recover(t[:args.n],m,args.gap,args.sampler)
    if result['status']=='SAT':
        seed=int(result['recovered_seed'],16)
        result['planted_seed_exact']=seed==args.seed
        result['full_train_and_holdout_replay']=replay(m,seed,t,args.gap,args.sampler)
    print(json.dumps(result))
