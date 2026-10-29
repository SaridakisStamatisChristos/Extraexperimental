from pathlib import Path
import sys, json, unittest, math
E=Path(__file__).resolve().parents[1]/'experiments';sys.path.insert(0,str(E))
from extra5_two_draw_replay import FIRST, SECOND, N, affine_fit, evaluate
from extra5_one_draw_seed_fit import rank_5of35, unrank_5of35
class TestReplay(unittest.TestCase):
    def test_lex_ranks(self):
        self.assertEqual(N,324632)
        self.assertEqual(rank_5of35(FIRST),55817)
        self.assertEqual(rank_5of35(SECOND),57278)
    def test_affine_models_exact_two(self):
        for a in (1,3,5):
            m=affine_fit(a)
            self.assertEqual((a*m['first_rank']+m['c'])%N,m['second_rank'])
            self.assertEqual(unrank_5of35(m['second_rank']),SECOND)
    def test_target_disagreement(self):
        self.assertEqual(affine_fit(1)['next_numbers'],[2,5,15,30,34])
        self.assertEqual(len({tuple(affine_fit(a)['next_numbers']) for a in (1,3,5)}),3)
    def test_search_archive(self):
        archive=json.loads((E/'extra5_multifamily_blind_14250.json').read_text())
        d=evaluate(archive)
        self.assertEqual(d['exact_both_draws'],0)
        self.assertEqual([x['second_hits'] for x in d['replayed_seed_candidates']],[0,0,1,1,1])
    def test_archive_corruption_rejected(self):
        archive=json.loads((E/'extra5_multifamily_blind_14250.json').read_text())
        archive['total_first_draw_exact_fits']=10
        with self.assertRaises(ValueError): evaluate(archive)
if __name__=='__main__':unittest.main()
