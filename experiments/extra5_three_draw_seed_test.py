#!/usr/bin/env python3
"""Strictly match three consecutive EXTRA 5 outputs from continuous seeded toy PRNGs.
No actual operator RNG keys, seed policy, sampling map or state is available.
"""
import argparse
import json
import math
from pathlib import Path
from extra5_multifamily_compact import stream, decode
from extra5_one_draw_seed_fit import rank_5of35, unrank_5of35, COMBINATIONS, LIMIT

TICKETS=((2,4,30,32,35),(2,5,9,30,33),(10,18,21,25,29))
N=COMBINATIONS
MASK=(1<<64)-1

def replay_historical(archive):
    """The earlier complete 1.64M search had only five first-draw fits.
    Replay every such seed for all THREE draws using the same initial state.
    """
    assert archive.get("tested",archive.get("total_attempted"))==1640000
    fits=[]
    for f in archive["families"]:
        for m in f.get("models",f.get("fits",[])):
            seed=m["seed_index"]
            raw=stream(f["family"],seed,128)
            pos=0
            produced=[]
            for _ in range(3):
                ticket,pos=decode(raw,pos)
                produced.append(ticket)
            expected_second=m.get("second_ticket_pre_reveal",m.get("hidden_next_prediction"))
            assert produced[0]==TICKETS[0] and list(produced[1])==expected_second
            prefix=0
            for a,b in zip(produced,TICKETS):
                if a!=b:break
                prefix+=1
            fits.append({"family":f["family"],"seed_index":seed,
                         "tickets":[list(t) for t in produced],"exact_prefix":prefix})
    assert len(fits)==5
    return fits

def words(kind,index):
    x=index & MASK
    if kind=="splitmix64":
        while True:
            x=(x+0x9e3779b97f4a7c15)&MASK
            z=x
            z=((z^(z>>30))*0xbf58476d1ce4e5b9)&MASK
            z=((z^(z>>27))*0x94d049bb133111eb)&MASK
            yield z^(z>>31)
    elif kind=="xorshift64star":
        if x==0:x=1  # Zero remapped; index 0 duplicates index 1.
        while True:
            x^=x>>12
            x^=(x<<25)&MASK
            x^=x>>27
            yield (x*2685821657736338717)&MASK
    elif kind=="lcg64":
        while True:
            x=(x*6364136223846793005+1442695040888963407)&MASK
            yield x
    else:raise ValueError(kind)

def tickets(kind,index,count=3):
    g=words(kind,index)
    remain=b""
    out=[]
    for _ in range(count):
        while True:
            while len(remain)<3:
                remain+=next(g).to_bytes(8,"big")
            val=int.from_bytes(remain[:3],"big")
            remain=remain[3:]
            if val<LIMIT:
                out.append(unrank_5of35(val%N))
                break
    return tuple(out)

def sweep(num_seeds):
    if not 1<=num_seeds<=10000000:raise ValueError("bad seed range")
    expected_rank=rank_5of35(TICKETS[0])
    out={}
    for name in ("splitmix64","xorshift64star","lcg64"):
        found=[]
        for seed in range(num_seeds):
            high24=next(words(name,seed))>>40
            if high24<LIMIT and high24%N!=expected_rank:
                continue
            seq=tickets(name,seed)
            if seq[0]!=TICKETS[0]:continue
            prefix=0
            for a,b in zip(seq,TICKETS):
                if a!=b:break
                prefix+=1
            found.append({"seed_index":seed,"tickets":[list(t) for t in seq],
                          "exact_prefix":prefix})
        out[name]={"tested":num_seeds,"first_exact":len(found),
                   "two_exact":sum(c["exact_prefix"]>=2 for c in found),
                   "three_exact":sum(c["exact_prefix"]==3 for c in found),
                   "candidates":found}
    return out

def solve_three():
    """Exact coefficient interpolation, not discovery of a secret PRNG seed."""
    x,y,z=map(rank_5of35,TICKETS)
    if math.gcd((y-x)%N,N)!=1:raise ValueError("non-unique affine fit")
    inv=pow((y-x)%N,-1,N)
    a=((z-y)*inv)%N
    c=(y-a*x)%N
    b=((z-y)-(y*y-x*x))*inv%N
    c2=(y-x*x-b*x)%N
    assert (a*x+c)%N==y and (a*y+c)%N==z
    assert (x*x+b*x+c2)%N==y and (y*y+b*y+c2)%N==z
    return {"ranks":[x,y,z],
            "affine":{"seed_x0":x,"a":a,"c":c,
                      "gcd_a_N":math.gcd(a,N),
                      "draw14252":list(unrank_5of35((a*z+c)%N))},
            "quadratic":{"seed_x0":x,"a":1,"b":b,"c":c2,
                         "draw14252":list(unrank_5of35((z*z+b*z+c2)%N))}}

def run(archive,num_seeds):
    old=replay_historical(archive)
    new=sweep(num_seeds)
    exact=sum(c["exact_prefix"]==3 for c in old)+sum(v["three_exact"] for v in new.values())
    return {"experiment":"EXTRA5-three-draw-seed-test-v1",
            "training":[{"draw_id":i,"numbers":list(t)} for i,t in zip((14249,14250,14251),TICKETS)],
            "historical_family_attempts_reused":1640000,
            "historical_first_draw_fits_replayed":old,
            "arithmetic_seed_sweeps":new,
            "total_attempts":1640000+3*num_seeds,
            "total_exact_three_seed_only":exact,
            "algebraically_fitted_three_draw_models":solve_three(),
            "uniform_ideal_expected_three_matches":(1640000+3*num_seeds)/(N**3),
            "caveat":"All seed-only candidates use synthetic public initialization and a hypothetical 5/35 mapper. Fitting extra recurrence coefficients is not recovery of a physical-entropy or cryptographic operator seed; no #14252 target was consulted."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--control-seeds",type=int,default=1000000)
    p.add_argument("--archive",type=Path,default=Path(__file__).with_name("extra5_multifamily_blind_14250.json"))
    p.add_argument("--out",type=Path,default=Path(__file__).with_name("extra5_three_draw_seed_test_results.json"))
    a=p.parse_args()
    result=run(json.loads(a.archive.read_text()),a.control_seeds)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"seed_only_exact_three":result["total_exact_three_seed_only"],
                      "attempts":result["total_attempts"],
                      "first_hits_by_control":{k:v["first_exact"] for k,v in result["arithmetic_seed_sweeps"].items()},
                      "coefficient_fits":result["algebraically_fitted_three_draw_models"]},indent=2))

if __name__=="__main__":main()
