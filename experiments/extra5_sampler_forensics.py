#!/usr/bin/env python3
"""EXTRA 5: reproducible tests of candidate bitstream-to-five-integers mappings.

Source of published aggregate counts (35 values, 14,353 draws):
https://numerics.gr/extra-5/statistika-arithmoi
https://numbers.gr/extra-5

These tests evaluate mapping mechanisms, NOT the identity or security of the
internal CSPRNG or its seeds. Runs entirely offline using Python standard library.
"""
from collections import defaultdict
from math import comb, erfc, sqrt
import csv
import json
from pathlib import Path

N = 14353
FREQUENCIES = [
    2012,2038,2116,2094,2070,2056,2116,2048,1956,2094,2121,1963,
    2073,2007,2074,1989,2028,2044,1995,1976,2024,2074,2023,2094,
    2053,2007,2058,2058,2052,2024,2076,2126,2111,2045,2070,
]
PICKS, POOL = 5, 35
assert len(FREQUENCIES) == POOL
assert sum(FREQUENCIES) == N*PICKS


def weighted_group_distribution(bits: int) -> dict:
    """Exact K=number of 'high modulo probability' labels selected per draw.

    A b-bit unsigned uniform RNG result x is converted to (x % 35)+1,
    repeated candidates rejected until 5 distinct labels have been selected.
    The first r=2**b % 35 labels receive q+1 preimages, others q.
    Conditional-on-acceptance selection of the next distinct label is
    proportional to its remaining weight (Plackett-Luce sampling).
    """
    q, r = divmod(1 << bits, POOL)
    state = {(0, 0): 1.0}  # (selected high, selected low)
    for _ in range(PICKS):
        nxt = defaultdict(float)
        for (h, l), p in state.items():
            H, L = (q+1)*(r-h), q*(POOL-r-l)
            if H: nxt[(h+1,l)] += p*H/(H+L)
            if L: nxt[(h,l+1)] += p*L/(H+L)
        state = dict(nxt)
    dist = [0.0]*(PICKS+1)
    for (h,_),p in state.items(): dist[h] += p
    mu = sum(i*p for i,p in enumerate(dist))
    var = sum((i-mu)**2*p for i,p in enumerate(dist))
    return {"bit_width":bits,"q":q,"remainder":r,
            "per_draw_high_count_probabilities":dist,
            "mean_high_per_draw":mu,"var_high_per_draw":var}


def test_width(bits):
    model = weighted_group_distribution(bits)
    r = model['remainder']
    count = sum(FREQUENCIES[:r])
    expected = N*model['mean_high_per_draw']
    standard_error = sqrt(N*model['var_high_per_draw'])
    z = (count-expected)/standard_error
    # large-N normal approximation to the sum of independent per-draw counts
    p_two_sided = erfc(abs(z)/sqrt(2))
    fair_mean = N*PICKS*r/POOL
    fair_var = N*PICKS*(r/POOL)*(1-r/POOL)*((POOL-PICKS)/(POOL-1))
    fair_z = (count-fair_mean)/sqrt(fair_var)
    return {**model,"observed_high_total":count,
            "expected_high_under_candidate":expected,
            "expected_high_under_uniform":fair_mean,
            "candidate_z":z,"candidate_two_sided_p_approx":p_two_sided,
            "uniform_z_for_same_group":fair_z}


def main():
    results = {"source":"Published number frequencies (numerics.gr / numbers.gr)",
               "date_note":"14,353-draw published snapshot, latest results around 2026-10-27; source may update",
               "draws":N,"total_appearances":sum(FREQUENCIES),
               "possible_unordered_outcomes":comb(POOL,PICKS),
               "number_counts":dict(zip(range(1,POOL+1),FREQUENCIES)),
               "hypothesis":"Unbiased uniformly distributed b-bit words, modulo 35, then reject duplicates until five distinct numbers",
               "candidate_tests":[test_width(bits) for bits in (8,10,16,32)]}
    out = Path(__file__).resolve().parent / 'extra5_sampler_forensics_results.json'
    out.write_text(json.dumps(results,indent=2,ensure_ascii=False))
    print('draws=',N,'appearances=',sum(FREQUENCIES),'possible subsets=',comb(POOL,PICKS))
    for d in results['candidate_tests']:
        print(f"{d['bit_width']:2} bits | remainder={d['remainder']:2} | observed={d['observed_high_total']:5} | expected={d['expected_high_under_candidate']:.2f} | z={d['candidate_z']:+.3f} | p={d['candidate_two_sided_p_approx']:.3g} | ideal_z={d['uniform_z_for_same_group']:+.3f}")
    print(out)

if __name__ == '__main__': main()