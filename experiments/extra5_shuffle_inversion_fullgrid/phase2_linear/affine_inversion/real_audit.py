#!/usr/bin/env python3
"""Auditable necessary-parity UNSAT certificates for the canonical real EXTRA 5 record.

Recomputes all fourth-index affine-hull constraints. A contradiction is a proof
of impossibility for the SPECIFIED recurrence/sampler/gap/continuous-state model;
never evidence against other families, streams, reseeding, or production RNG.
"""
import argparse,csv,hashlib,json,time
from pathlib import Path
from recover_affine import MODELS,forms,affine_constraints,fourth_domain,replay

CANONICAL_SHA256='61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307'

def load_source(path):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=CANONICAL_SHA256:
        raise ValueError('canonical dataset SHA256 mismatch')
    with path.open(newline='') as f: rows=list(csv.DictReader(f))
    if len(rows)!=3526: raise ValueError('canonical row count mismatch')
    tickets=[]
    for d,r in enumerate(rows):
        if int(r['draw_id'])!=10832+d:raise ValueError('nonconsecutive draw id')
        nums=[int(r[f'n{i}']) for i in range(1,6)]
        if len(set(nums))!=5 or any(not 1<=x<=35 for x in nums):raise ValueError('bad combination')
        tickets.append(tuple(sorted(nums)))
    return tickets

def parity_equations(tickets,linear):
    for d,nums in enumerate(tickets):
        for mask,rhs in affine_constraints(fourth_domain(nums)):
            coeff=0
            for bit in range(5):
                if mask & (1<<bit):coeff^=linear[d][bit]
            yield (d,mask,coeff,rhs)

def check_certificate(certificate,equations):
    """Independently recompute XOR sum of source equation indices."""
    col=0;rhs=0
    for i in certificate:
        _,_,a,b=equations[i]
        col^=a;rhs^=b
    return col==0 and rhs==1

def audit(tickets,model,gap,sampler,maximum=500):
    n=min(maximum,len(tickets)); selected=tickets[:n]
    start=time.perf_counter();linears=forms(model,n,gap,sampler)
    pivots={};eqs=[];rank=0;result=None
    for d,mask,coeff,rhs in parity_equations(selected,linears):
        index=len(eqs);eqs.append((d,mask,coeff,rhs))
        x=coeff;val=rhs;support=1<<index
        while x:
            pivot=x.bit_length()-1
            if pivot not in pivots:
                pivots[pivot]=(x,val,support);rank+=1;break
            row,y,span=pivots[pivot];x^=row;val^=y;support^=span
        if x==0 and val:
            indices=[j for j in range(index+1) if (support>>j)&1]
            assert check_certificate(indices,eqs)
            result=dict(status='UNSAT',reason='XOR of necessary equations yields 0 = 1',
                first_contradicting_draw_id=10832+d,draws_used=d+1,rank_at_contradiction=rank,
                equations_processed=index+1,certificate=[{'draw_id':10832+eqs[j][0],
                    'linear_mask':eqs[j][1],'right_hand_side':eqs[j][3]} for j in indices],
                certificate_size=len(indices),certificate_xor_checked=True)
            break
    if result is None:
        result=dict(status='UNKNOWN',reason='No contradiction; no full-ticket replay or uniqueness established',
            draws_used=n,rank=rank,equations_processed=len(eqs))
    result.update(model=model.name,gap=gap,sampler=sampler,elapsed_s=round(time.perf_counter()-start,4))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--limit',type=int,default=500)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    tickets=load_source(a.source)
    output={'source_sha256':CANONICAL_SHA256,'source_draws':len(tickets),
      'audit_models': [audit(tickets,MODELS[m],gap,sampler,a.limit)
       for m in ('xorshift128','xoroshiro128_raw','xoshiro256_raw')
       for sampler in ('mod','high') for gap in (0,1,2)]}
    output_text=json.dumps(output,indent=2)
    if a.output:a.output.write_text(output_text+'\n')
    print(output_text)

if __name__=='__main__':main()
