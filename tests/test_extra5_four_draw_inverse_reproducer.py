import importlib.util,random,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('reproducer',Path(__file__).resolve().parents[1]/'experiments'/'extra5_four_draw_inverse_reproducer.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class StateRecovery(unittest.TestCase):
    def test_lexicographic_ranks(self):
        self.assertEqual(m.RANKS,(55817,57278,268706,23073))
        for r in (0,1,55817,57278,268706,23073,m.N-1):self.assertEqual(m.rank(m.unrank(r)),r)
    def test_96bit_inverse_random(self):
        size,rows=m.matrix('xorshift96')
        for seed in (0,1,0x92a140efbdfe8769d18dcbdc,*[random.Random(i).getrandbits(96) for i in range(10)]):
            words=m.output_words('xorshift96',seed,3)
            recovery=m.solve(rows,words,size)
            self.assertEqual(recovery,(seed,96,0))
    def test_xorshift64_canonical_branch_is_impossible(self):
        self.assertIsNone(m.seeded_fit('xorshift64'))
    def test_128bit_has_free_state(self):
        size,rows=m.matrix('xorshift128')
        seed,rank,free=m.solve(rows,m.output_words('xorshift128',123456,3),size)
        self.assertEqual((rank,free),(96,32))
        self.assertEqual(m.output_words('xorshift128',seed,3),m.output_words('xorshift128',123456,3))
    def test_exact_four_canonical(self):
        r=m.seeded_fit('xorshift96')
        self.assertEqual(r['state_hex'],'92a140efbdfe8769d18dcbdc')
        self.assertEqual(r['training_numbers'],[list(t) for t in m.DRAWS])
        self.assertEqual(r['fifth_ticket']['numbers'],[9,24,25,30,33])
    def test_four_fit_is_not_unique(self):
        r=m.run()
        self.assertEqual(r['at_least_distinct_xorshift96_seeds_with_zero_initial_rejections'],51**4)
        self.assertNotEqual(r['canonical_xorshift96']['state_hex'],r['different_raw_branch_same_four_training']['state_hex'])
        self.assertNotEqual(r['canonical_xorshift96']['fifth_ticket']['numbers'],r['different_raw_branch_same_four_training']['fifth_ticket']['numbers'])
        self.assertEqual(r['canonical_xorshift96']['training_numbers'],r['different_raw_branch_same_four_training']['training_numbers'])
    def test_sampler_boundaries(self):
        self.assertEqual(m.LIMIT,51*m.N)
        for v in (0,m.N-1,m.LIMIT-1):self.assertEqual(m.unrank(v%m.N),m.unrank((v+ m.N)%m.N))
if __name__=='__main__':unittest.main()
