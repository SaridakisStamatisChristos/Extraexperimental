"""Tests of exact 5-of-35 combinatorial target and predictor replay."""
import math,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'experiments'))
from extra5_180_probability import N, WEIGHTS, exact_tail

class ExactTargetTests(unittest.TestCase):
    def test_one_draw_multiplicities(self):
        self.assertEqual(N,324632)
        self.assertEqual(WEIGHTS,[142506,137025,40600,4350,150,1])
        self.assertEqual(sum(WEIGHTS),N)
    def test_one_draw_exact_ticket(self):
        p,n,d=exact_tail(1,5)
        self.assertEqual((n,d),(1,324632))
    def test_requested_target(self):
        p,_,_=exact_tail(40,180)
        self.assertTrue(2.4e-165 < float(p) < 2.5e-165)
    def test_monotonicity(self):
        self.assertGreater(exact_tail(40,35)[0],exact_tail(40,48)[0])
        self.assertGreater(exact_tail(40,48)[0],exact_tail(40,180)[0])

if __name__=='__main__':unittest.main()
