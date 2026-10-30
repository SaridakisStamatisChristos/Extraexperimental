"""Small regression suite for the stand-alone 32-bit state enumerator."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
import extra5_exact_32bit_compact as x

class Exact32BitCompactTest(unittest.TestCase):
    def test_sampler_first_word_ranges(self):
        for variant,n in zip(x.SAMPLERS,(13056,13056,13230)):
            pre=list(x.first_words(variant))
            self.assertEqual(len(pre),n)
            self.assertTrue(all(x.accepted(v,variant)==x.RANKS[0] for v in pre))
    def test_full_enumeration(self):
        report=x.run()
        self.assertEqual(report['totals']['first_compatible_states'],196710)
        self.assertEqual(report['totals']['exact_2'],1)
        self.assertEqual(report['totals']['exact_3'],0)
        self.assertEqual(report['totals']['exact_4'],0)
        self.assertEqual(report['witnesses'][0]['first_word'],414935513)

if __name__=='__main__':
    unittest.main()
