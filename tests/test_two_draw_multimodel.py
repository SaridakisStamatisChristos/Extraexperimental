"""Deterministic checks for the two-draw hypothesis bank. No target outcome."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
from extra5_two_draw_multimodel import FIRST,SECOND,TARGET,N,rank,unrank,candidates,report
class TwoDrawModels(unittest.TestCase):
    def test_known_ranks(self):
        self.assertEqual(rank(FIRST),55817)
        self.assertEqual(rank(SECOND),57278)
    def test_exhaustive_rank_roundtrip(self):
        for i in range(N):self.assertEqual(rank(unrank(i)),i)
    def test_fit(self):
        self.assertTrue(all(r['fit_first_to_second'] for r in candidates()))
    def test_diversity(self):
        self.assertEqual(len(candidates()),9)
        self.assertEqual(len({tuple(r['next']) for r in candidates()}),9)
    def test_prior_primary_preserved(self):
        self.assertEqual(candidates()[0]['next'],[2,5,15,30,34])
    def test_not_using_hidden_target(self):
        self.assertEqual(TARGET,14251)
        self.assertTrue(report()['hidden_result_not_consulted'])
if __name__=='__main__':unittest.main()
