"""Regression checks for three-known-draw synthetic seed and coefficient experiments."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"experiments"))
from extra5_three_draw_seed_test import TICKETS,replay_historical,sweep,solve_three,tickets
from extra5_one_draw_seed_fit import rank_5of35,unrank_5of35
ROOT=Path(__file__).resolve().parents[1]/"experiments"

class ThreeDrawSeedChecks(unittest.TestCase):
    def test_known_combinations(self):
        self.assertEqual([rank_5of35(t) for t in TICKETS],[55817,57278,268706])
        for t in TICKETS:self.assertEqual(unrank_5of35(rank_5of35(t)),t)

    def test_prior_seed_replays(self):
        a=json.loads((ROOT/"extra5_multifamily_blind_14250.json").read_text())
        v=replay_historical(a)
        self.assertEqual(len(v),5)
        self.assertTrue(all(c["exact_prefix"]==1 for c in v))

    def test_algebraic_three_draw_fit(self):
        v=solve_three()
        self.assertEqual((v["affine"]["a"],v["affine"]["c"]),(194124,204866))
        self.assertEqual((v["quadratic"]["b"],v["quadratic"]["c"]),(81029,315056))
        self.assertEqual(v["affine"]["draw14252"],[13,16,21,26,32])
        self.assertEqual(v["quadratic"]["draw14252"],[3,12,17,18,33])
        self.assertEqual(v["affine"]["gcd_a_N"],28)

    def test_prefilter_matches_direct_execution(self):
        r=sweep(5000)
        for family,data in r.items():
            slow=[s for s in range(5000) if tickets(family,s,1)[0]==TICKETS[0]]
            self.assertEqual([x["seed_index"] for x in data["candidates"]],slow)

    def test_million_seed_checkpoint(self):
        p=json.loads((ROOT/"extra5_three_draw_seed_test_results.json").read_text())
        self.assertEqual(p["total_attempts"],4640000)
        self.assertEqual(p["total_exact_three_seed_only"],0)
        self.assertEqual({k:v["first_exact"] for k,v in p["arithmetic_seed_sweeps"].items()},
                         {"splitmix64":3,"xorshift64star":2,"lcg64":6})

if __name__=="__main__":unittest.main()
