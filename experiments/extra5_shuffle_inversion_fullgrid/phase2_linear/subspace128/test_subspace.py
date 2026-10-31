"""Independent exact negative/positive controls for the restricted 128-state model."""
import csv,json,subprocess,tempfile,unittest,random
from pathlib import Path
from benchmark_subspace import generate,write,run,ref_draw
ROOT=Path(__file__).resolve().parent
SEED=0x123456789abcdef0

class SubspaceInversionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory()
  cls.bin=Path(cls.tmp.name)/'inverse128_subspace'
  subprocess.run(['g++','-O3','-std=c++20','-Wall','-Wextra','-Werror',str(ROOT/'inverse128_subspace.cpp'),'-o',str(cls.bin)],check=True,capture_output=True)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_planted_unordered_modulo_and_high(self):
  for sampler in ('mod','high'):
   for gap in (0,2):
    with self.subTest(sampler=sampler,gap=gap):
     items=list(generate(SEED,gap,sampler,600))
     path=Path(self.tmp.name)/'synthetic.csv';write(path,items[:500])
     r=run(self.bin,path,500,gap,sampler=='high')
     self.assertEqual(r['status'],'SAT',r)
     self.assertEqual(r['rank'],64)
     self.assertEqual(r['witness_state'],SEED)
     self.assertEqual(list(generate(r['witness_state'],gap,sampler,600)),items)
 def test_random_128_state_not_in_subspace_is_refuted(self):
  # Negative control: upper two initial words are not zero, so a subspace solver
  # must not silently claim it has recovered a general 128-bit state.
  state=(0x87654321,0xfedcba98,0x11223344,0x55667788)
  items=[]
  for i in range(500):
   state,t=ref_draw(state,0,'mod');items.append(t)
  path=Path(self.tmp.name)/'out_of_subspace.csv';write(path,items)
  r=run(self.bin,path,500,0,False)
  self.assertEqual((r['status'],r['rank']),('UNSAT',64),r)
 def test_truncated_budget_reports_unknown_not_unsat(self):
  path=Path(self.tmp.name)/'planted.csv';write(path,list(generate(SEED,0,'mod',500)))
  r=run(self.bin,path,500,0,False,budget=10)
  self.assertEqual(r['status'],'UNKNOWN',r)
  self.assertEqual(r['assignments_examined'],11)
 def test_modified_ticket_is_detected(self):
  tickets=list(generate(SEED,0,'high',500));first=set(tickets[0]);replacement=next(v for v in range(1,36) if v not in first)
  tickets[0]=tuple(sorted((first-{min(first)})|{replacement}))
  path=Path(self.tmp.name)/'altered.csv';write(path,tickets)
  r=run(self.bin,path,500,0,True)
  self.assertEqual(r['status'],'UNSAT',r)
if __name__=='__main__':unittest.main(verbosity=2)
