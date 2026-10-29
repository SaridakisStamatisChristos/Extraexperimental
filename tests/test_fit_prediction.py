import csv
import json
import sys
import unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments'))
import extra5_walkforward_fit as w
import extra5_exact_fit_counterexample as p

class TestFit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ids,cls.X=w.load_data(ROOT/'experiments/extra5_last100_data.csv')
    def test_no_leak_selection(self):
        _,_,_,rows=w.holdout_rows(self.X,2)
        for rr in rows.values():
            for r in rr:
                self.assertEqual(r['prefix_count'],r['target_index']-1)
    def test_each_pred_is_a_valid_ticket(self):
        for model in w.MODELS:
            for h in (1,2):
                p0=w.predict(self.X[:65],model,h)
                self.assertAlmostEqual(p0.sum(),5,places=6)
                self.assertTrue(np.all(p0>=0) and np.all(p0<=1))
                self.assertEqual(len(set(w.top_ticket(p0))),5)
    def test_100_full_history_valid(self):
        self.assertEqual(self.ids,list(range(14256,14356)))
        self.assertTrue(np.all(self.X.sum(axis=1)==5))
    def test_interp_all_historical(self):
        ys=[p.rank_combination((self.X[i].nonzero()[0]+1).tolist()) for i in range(100)]
        weights=p.barycentric_weights(self.ids)
        for x,y in zip(self.ids,ys):self.assertEqual(y,p.interpolate(self.ids,ys,weights,x))
    def test_any_next_possible(self):
        ys=[p.rank_combination((self.X[i].nonzero()[0]+1).tolist()) for i in range(100)]
        weights=p.barycentric_weights(self.ids)
        for target in ([1,2,3,4,5],[31,32,33,34,35],[2,11,13,14,35]):
            z=p.make_fit(self.ids,ys,weights,14357,p.rank_combination(target))
            self.assertEqual(z['next_ticket'],target)
    def test_rank_roundtrip_all(self):
        for k in range(p.TOTAL):
            self.assertEqual(p.rank_combination(p.unrank_combination(k)),k)
    def test_adaptive_null_exact(self):
        from scipy.stats import hypergeom
        dist=np.array([1.]);pmf=hypergeom.pmf(np.arange(6),35,5,5)
        for _ in range(40):dist=np.convolve(dist,pmf)
        self.assertAlmostEqual(dist.sum(),1,places=12)
        self.assertAlmostEqual(sum(np.arange(len(dist))*dist),40*25/35,places=10)

if __name__=='__main__':unittest.main()
