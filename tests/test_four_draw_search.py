"""Checks independent of post-search winner selection."""
import unittest,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
from extra5_four_draw_search import TICKETS,CONTROLS,FAMILIES,quick_first,exact_prefix,polynomial_congruence_obstruction
from extra5_one_draw_seed_fit import rank_5of35,unrank_5of35
from extra5_multifamily_compact import stream,decode
from extra5_three_draw_seed_test import simple_seed_tickets,words

class FourDrawTests(unittest.TestCase):
    def test_four_ranks(self):
        self.assertEqual([rank_5of35(t) for t in TICKETS],[55817,57278,268706,23073])
    def test_polynomial_impossibility(self):
        obs=polynomial_congruence_obstruction()
        self.assertEqual(obs['obstruction_modulus'],28)
        self.assertEqual(obs['input_residues'],[18,18])
        self.assertEqual(obs['output_residues'],[18,1])
        for a,b,c in [(0,1,1),(1,1461,0),(194124,204866,0),(1,81029,315056)]:
            p=lambda v:(a*v*v+b*v+c)%obs['modulus']
            self.assertEqual(p(obs['congruent_inputs'][0])%28,p(obs['congruent_inputs'][1])%28)
    def test_four_prefix_semantics(self):
        self.assertEqual(exact_prefix(TICKETS),4)
        self.assertEqual(exact_prefix((TICKETS[0],TICKETS[2],TICKETS[1],TICKETS[3])),1)
    def test_crypto_preview_all_11_families_samples(self):
        for fam in FAMILIES:
            for seed in (0,1,123,500001):
                v,_=quick_first(fam,seed)
                full=decode(stream(fam,seed,128))[0]
                self.assertEqual(v,full,(fam,seed))
    def test_arithmetic_quick_prefilter(self):
        mask=(1<<64)-1
        for fam in CONTROLS:
            for seed in (0,1,5,12345,1000001):
                v=next(words(fam,seed))>>40
                full=simple_seed_tickets(fam,seed,1)[0]
                if v<((1<<24)//math.comb(35,5)*math.comb(35,5)):
                    self.assertEqual(v%math.comb(35,5),rank_5of35(full))
    def test_unrank_roundtrip_samples(self):
        for rank in (0,55817,57278,268706,23073,math.comb(35,5)-1):
            self.assertEqual(rank_5of35(unrank_5of35(rank)),rank)

if __name__=='__main__':unittest.main()
