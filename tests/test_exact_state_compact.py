"""Regression tests for the four-draw exact first-output-state search."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
from extra5_exact_state_compact import N,RANKS,first_words,sample,fmix,unmix,experiment

class TestStateSearch(unittest.TestCase):
    def test_ranks(self):
        self.assertEqual((N,RANKS),(324632,(55817,57278,268706,23073)))
    def test_fmix_bijection(self):
        for v in (0,1,0xffffffff,0x12345678):
            self.assertEqual(unmix(fmix(v)),v)
    def test_complete_preimages(self):
        for m,count in [('high24',13056),('low24',13056),('full32',13230)]:
            words=list(first_words(m))
            self.assertEqual(len(words),count)
            self.assertEqual(len(set(words)),count)
            self.assertTrue(all(sample(w,m)==RANKS[0] for w in words))
    def test_all_results(self):
        x=experiment()
        self.assertEqual(len(x['results']),15)
        self.assertEqual(x['aggregate'],{'first_output_states':196710,'two':1,'three':0,'four':0})
        witnesses=[r for r in x['results'] if r['two']>0]
        self.assertEqual(len(witnesses),1)
        self.assertEqual((witnesses[0]['family'],witnesses[0]['mapping']),('splitmix32_fmix','full32'))
        self.assertEqual(witnesses[0]['two_draw_witnesses'],[{'first_accepted_word':414935513,'next_two_ranks':[216364,59123]}])
if __name__=='__main__':unittest.main()
