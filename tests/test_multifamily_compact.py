import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
import extra5_multifamily_compact as m
class CompactTests(unittest.TestCase):
 def test_known_prediction(self):
  self.assertEqual(m.TRAIN,(2,4,30,32,35))
  self.assertEqual(m.decode(m.stream('aes192-cfb128',236403,64))[0],m.TRAIN)
 def test_family_independence(self):
  self.assertNotEqual(m.kdf('aes192-cfb128',24),m.kdf('cast128-cfb64',24))
 def test_prefix_consistency(self):
  for family in m.FAMILIES:
   self.assertEqual(m.stream(family,42,6),m.stream(family,42,64)[:6])
 def test_small_deterministic_replay(self):
  a=m.run(120,90,80);b=m.run(120,90,80)
  self.assertEqual(a,b)
  self.assertEqual(a['tested'],3*120+3*90+2*80)
 def test_fitted_seed_has_distinct_next(self):
  raw=m.stream('aes192-cfb128',236403,64)
  one,p=m.decode(raw);two,_=m.decode(raw,p)
  self.assertEqual(one,m.TRAIN)
  self.assertEqual(two,(4,6,19,27,31))
if __name__=='__main__':unittest.main()
