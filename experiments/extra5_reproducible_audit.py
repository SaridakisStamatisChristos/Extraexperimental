#!/usr/bin/env python3
"""Reproducible descriptive audit of Greek EXTRA 5 (5 out of 35).

Usage:
    python extra5_reproducible_audit.py
    python extra5_reproducible_audit.py --draws history.csv
    python extra5_reproducible_audit.py --draws history.csv --mc 20000

Without a CSV, audit publicly published, internally reconciled cumulative
frequency snapshots. With a CSV, also run draw-level checks. The CSV must have
columns n1,n2,n3,n4,n5, with optional draw_id and date (YYYY-MM-DD); one row
per draw, chronological or sortable by draw_id/date.

Requires numpy and scipy. No network access is needed.
Results are research diagnostics, not predictions.
"""
import argparse
import csv
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import chi2, binomtest, hypergeom, norm

POOL, PICKS = 35, 5
FIN_POP_CORR = (POOL - 1) / (POOL - PICKS)  # Pearson correction: 34/30
SNAPSHOTS = {
    "2026-09-14": (14266, [1998,2028,2101,2076,2056,2045,2102,2038,1943,2080,2111,1953,2065,1998,2065,1980,2012,2032,1982,1963,2008,2062,2012,2082,2042,1996,2043,2044,2038,2007,2062,2114,2099,2033,2060]),
    "2026-10-17": (14331, [2009,2035,2113,2093,2065,2052,2109,2046,1952,2089,2120,1962,2072,2007,2072,1986,2023,2042,1991,1975,2019,2072,2022,2090,2052,2004,2053,2054,2046,2018,2069,2122,2110,2043,2068]),
    "2026-10-24": (14346, [2012,2036,2114,2094,2068,2054,2114,2048,1955,2092,2121,1962,2073,2007,2073,1989,2025,2044,1995,1976,2023,2072,2023,2093,2053,2005,2056,2056,2050,2021,2074,2126,2111,2045,2070]),
}


def uniformity_stat(counts, n):
    counts = np.asarray(counts, dtype=int)
    assert len(counts) == POOL and counts.sum() == PICKS * n
    expectation = n * PICKS / POOL
    stat = float(FIN_POP_CORR * np.sum((counts - expectation)**2 / expectation))
    return {"draws": int(n), "chi2_adjusted": round(stat, 6), "df": POOL-1,
            "upper_tail_p_asymptotic": float(chi2.sf(stat, POOL-1)),
            "lower_tail_p_asymptotic": float(chi2.cdf(stat, POOL-1)),
            "min": int(counts.min()), "max": int(counts.max()),
            "frequency_sd": float(np.std(counts, ddof=1)),
            "expected_frequency_sd": math.sqrt(n * (PICKS/POOL)*(1-PICKS/POOL))}


def mc_uniformity_lower(n, observed_stat, reps=100_000, seed=20261029, batch=500):
    """Simulate whole 5-of-35 draws: independent across draws, no replacement within."""
    rng = np.random.default_rng(seed)
    hits = 0
    for start in range(0, reps, batch):
        b = min(batch, reps-start)
        # Continuous iid keys: lowest 5 constitute a uniform 5-subset.
        selected = np.argpartition(rng.random((b,n,POOL)), kth=PICKS-1, axis=2)[:, :, :PICKS]
        offsets = (POOL*np.arange(b))[:, None, None]
        frequencies = np.bincount((selected+offsets).ravel(), minlength=b*POOL).reshape(b, POOL)
        mean = n*PICKS/POOL
        stats = FIN_POP_CORR * np.sum((frequencies-mean)**2/mean, axis=1)
        hits += int((stats<=observed_stat+1e-12).sum())
    # add-one MC correction for p-value
    return {"tail":"unusually_even", "hits":hits, "replicates":reps, "p_mc":(hits+1)/(reps+1), "seed":seed}


def snapshot_audit(reps):
    out = {"source":"foufos.gr published cumulative frequency tables", "snapshots":{}, "windows":{}, "interesting_pairs":{}}
    for dt, (n, freq) in SNAPSHOTS.items():
        assert sum(freq)==n*PICKS, (dt,"invalid totals")
        u=uniformity_stat(freq,n)
        ps = [binomtest(int(k),n,PICKS/POOL).pvalue for k in freq]
        u["smallest_individual_nominal_p"] = float(min(ps))
        u["smallest_individual_bonferroni_p"] = float(min(1,POOL*min(ps)))
        u["smallest_number"] = int(np.argmin(ps)+1)
        out["snapshots"][dt]=u
    for start,end in (("2026-09-14","2026-10-17"),("2026-10-17","2026-10-24"),("2026-09-14","2026-10-24")):
        n1, counts1 = SNAPSHOTS[start]
        n2, counts2 = SNAPSHOTS[end]
        n = n2-n1
        delta=np.asarray(counts2)-np.asarray(counts1)
        assert (delta>=0).all() and delta.sum()==PICKS*n
        u=uniformity_stat(delta,n)
        u["mc_lower_tail"] = mc_uniformity_lower(n,u["chi2_adjusted"],reps)
        u["counts_by_number"]=[int(k) for k in delta]
        out["windows"][f"{start} to {end}"]=u
    n=SNAPSHOTS["2026-10-24"][0]
    pair_p=math.comb(POOL-2,PICKS-2)/math.comb(POOL,PICKS)
    k=298
    p2=binomtest(k,n,pair_p).pvalue
    out["interesting_pairs"]["3_31"]={"observed":k,"expected":n*pair_p,"nominal_two_sided_p":p2,
              "number_of_pairs":math.comb(POOL,2),"bonferroni_p":min(1,p2*math.comb(POOL,2)),
              "note":"Pair count source is 2026-10-24 snapshot, selected after scanning all pairs."}
    return out


def read_draws(path):
    draws=[]
    with open(path,newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        needed=[f"n{i}" for i in range(1,PICKS+1)]
        if not set(needed).issubset(reader.fieldnames or []):
            raise ValueError("CSV must have columns n1,n2,n3,n4,n5")
        for row in reader:
            nums=tuple(sorted(int(row[key]) for key in needed))
            if len(set(nums))!=PICKS or not all(1<=x<=POOL for x in nums):
                raise ValueError(f"Invalid draw: {row}")
            draws.append({"numbers":nums,"date":row.get("date", ""),"draw_id":row.get("draw_id","")})
    if not draws: raise ValueError("Empty draw archive")
    if all(d["draw_id"] and str(d["draw_id"]).isdigit() for d in draws):
        draws.sort(key=lambda d:int(d["draw_id"]))
        ids=[int(d["draw_id"]) for d in draws]
        if len(set(ids)) !=len(ids): raise ValueError("Duplicate draw_id values")
    elif all(d["date"] for d in draws):
        # Date alone cannot distinguish the two daily draws, so preserve file ordering within date.
        draws.sort(key=lambda d:d["date"])
    return draws


def draw_level_audit(draws):
    n=len(draws)
    mat=np.zeros((n,POOL),dtype=np.uint8)
    for i,d in enumerate(draws): mat[i,np.array(d["numbers"])-1]=1
    freq=mat.sum(axis=0).astype(int)
    out={"N":n,"uniformity":uniformity_stat(freq,n),"draw_id_gaps":[],"number_counts":freq.tolist()}
    if all(str(d["draw_id"]).isdigit() for d in draws):
        ids=np.array([int(d["draw_id"]) for d in draws]); out["draw_id_gaps"]=(ids[1:]-ids[:-1]-1)[(ids[1:]-ids[:-1])>1].tolist()
    allpairs=list(itertools.combinations(range(POOL),2))
    paircounts=np.array([int(np.dot(mat[:,i].astype(int),mat[:,j].astype(int))) for i,j in allpairs])
    pair_p=math.comb(POOL-2,PICKS-2)/math.comb(POOL,PICKS)
    pair_ps=np.array([binomtest(int(k),n,pair_p).pvalue for k in paircounts])
    maxid=int(np.argmin(pair_ps))
    out["pairs"]={"smallest_nominal_p":float(pair_ps[maxid]),"bonferroni_p":float(min(1,len(pair_ps)*pair_ps[maxid])),
                  "pair":[x+1 for x in allpairs[maxid]],"observed":int(paircounts[maxid]),"expected":n*pair_p}
    if n>1:
        obs_overlap=np.sum(mat[:-1] * mat[1:],axis=1).astype(int)
        counts=np.bincount(obs_overlap,minlength=6)
        expected=np.array([math.comb(PICKS,k)*math.comb(POOL-PICKS,PICKS-k)/math.comb(POOL,PICKS) for k in range(PICKS+1)])*(n-1)
        # Group 3,4,5: expected counts for upper bins too small individually.
        expgrp=np.r_[expected[:3],expected[3:].sum()]
        obsgrp=np.r_[counts[:3],counts[3:].sum()]
        chi=float(np.sum((obsgrp-expgrp)**2/expgrp))
        out["consecutive_draw_overlap"]={"observed":counts.tolist(),"expected":expected.tolist(),
                  "chi2_grouped":chi,"p_asymptotic":float(chi2.sf(chi,3))}
    sums=np.array([sum(d["numbers"]) for d in draws])
    sd_single=math.sqrt(PICKS*(POOL**2-1)/12*(POOL-PICKS)/(POOL-1))
    z=(sums.mean()-90)/(sd_single/math.sqrt(n))
    out["number_sum"]={"observed_mean":float(sums.mean()),"expected_mean":90,
                         "two_sided_p":float(2*norm.sf(abs(z)))}
    # Pre-defined disjoint 80-draw windows, not selected by posthoc extremes.
    windows=[]
    for start in range(0,n-79,80):
        s=mat[start:start+80].sum(axis=0)
        w=uniformity_stat(s,80)
        windows.append({"start_record":start+1,"end_record":start+80,
                        "lower_p":w["lower_tail_p_asymptotic"],"upper_p":w["upper_tail_p_asymptotic"]})
    for tail in ("lower_p","upper_p"):
        m=len(windows)
        for w in windows: w[tail+"_bonferroni"] = min(1, m*w[tail])
    out["nonoverlap_80_draw_windows"]=windows
    return out


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--draws",type=Path,help="Chronological CSV (n1..n5, optionally draw_id/date)")
    a.add_argument("--mc",type=int,default=100_000,help="Simulation replicates for aggregate snapshot windows")
    a.add_argument("--output",type=Path,default=Path("extra5_audit_results.json"))
    args=a.parse_args()
    if args.mc<1000: a.error("--mc must be at least 1000")
    result={"model":"Independent uniform five-element subsets of {1,...,35}",
            "aggregate_analysis":snapshot_audit(args.mc)}
    if args.draws: result["draw_level_analysis"]=draw_level_audit(read_draws(args.draws))
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Audit written: {args.output}")
    print("Full-history uniformity:",result["aggregate_analysis"]["snapshots"]["2026-10-24"]["upper_tail_p_asymptotic"])
    print("Recent 80-draw window lower-tail MC:",result["aggregate_analysis"]["windows"]["2026-09-14 to 2026-10-24"]["mc_lower_tail"]["p_mc"])

if __name__=="__main__":main()