"""Model-level correctness checks; not a hidden full-state recovery claim."""
from ctypes.util import find_library
import unittest
from pathlib import Path
from exact_smt128 import draw,formula,Z3,upper_domains,independent_transition

SEED=0x8877665544332211ffeeddccbbaa9988

def gen(seed,n):
    state=tuple((seed>>(32*i))&0xffffffff for i in range(4))
    out=[]
    for _ in range(n):
        state,t=draw(state);out.append(t)
    return out

@unittest.skipUnless(find_library('z3'), 'libz3 unavailable')
class ExactFullSMTTests(unittest.TestCase):
 def test_pinned_true_state_sat(self):
    for seed in (SEED,0x112233445566778899aabbccddeeff00):
        for strengthen in (False,True):
            a=Z3().run(formula(gen(seed,4),pin=seed,strengthen=strengthen),2000)
            self.assertEqual(a['status'],'SAT',a)
            self.assertEqual(a['seed'],seed)
 def test_pinned_wrong_state_unsat(self):
    a=Z3().run(formula(gen(SEED,3),pin=SEED^0x1111111111111111),2000)
    self.assertEqual(a['status'],'UNSAT',a)
 def test_short_unpinned_witness_is_exact_but_nonunique(self):
    nums=gen(SEED,3)
    r=Z3().run(formula(nums),3000)
    self.assertEqual(r['status'],'SAT',r)
    self.assertEqual(gen(r['seed'],3),nums)
 def test_prefix_necessary_condition_complete_for_oracle(self):
    for seed in (SEED,0x112233445566778899aabbccddeeff00):
        state=tuple((seed>>(32*i))&0xffffffff for i in range(4))
        for _ in range(100):
            saved=state;state,nums=draw(state)
            domains=upper_domains(nums)
            for j in range(5):
                saved,word=independent_transition(saved)
                self.assertIn(word>>27,domains[j])
 def test_wrong_pin_rejects_with_redundant_domain_constraints(self):
    a=Z3().run(formula(gen(SEED,3),pin=SEED^123,strengthen=True),2000)
    self.assertEqual(a['status'],'UNSAT',a)
if __name__=='__main__':unittest.main(verbosity=2)
