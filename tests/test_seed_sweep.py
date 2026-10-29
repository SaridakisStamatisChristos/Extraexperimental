"""Local deterministic regression tests for expanded synthetic seed experiment."""
import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments'))
from extra5_seed_sweep import MemoBitStream, seeded_masters, chosen_route, fixed_configs, run, exact_holdout_tail
from extra5_seeded_replay import ticket, mask
from extra5_seed_switch_protocol import SAMPLERS, routes_supported, demo_nr_key, sources_from_seed, sample_ticket
from extra5_historical_engine import RoutedBits

class Bits:
    def __init__(self):self.k=0
    def bit(self):
        self.k+=1;return self.k%2

class SeedSweepTests(unittest.TestCase):
    def test_reader_rewind_and_limit(self):
        source=Bits();r=MemoBitStream(source,[],limit=5)
        self.assertEqual([r.bit() for _ in range(3)],[1,0,1]);self.assertEqual(source.k,3)
        r.rewind();self.assertEqual([r.bit() for _ in range(3)],[1,0,1]);self.assertEqual(source.k,3)
        self.assertEqual([r.bit() for _ in range(2)],[0,1]);self.assertEqual(source.k,5)
        with self.assertRaises(ValueError):r.bit()
    def test_seed_master_policy_distinct_reproducible(self):
        ids=[14256,14257,14258]
        k=demo_nr_key()
        a=list(seeded_masters(ids,0,'fresh_fixture',k));b=list(seeded_masters(ids,0,'fresh_fixture',k))
        self.assertEqual(a,b);self.assertEqual(len(set(a)),3)
        c=list(seeded_masters(ids,0,'previous_state_fixture',k))
        self.assertNotEqual(a,c)
    def test_source_equivalence_first_two_draws(self):
        ids=[14256,14257]
        routes,plans=fixed_configs(); k=demo_nr_key()
        for seed in (0,7,19):
            for policy in ('fresh_fixture','previous_state_fixture'):
                masters=list(seeded_masters(ids,seed,policy,k))
                for schedule,route in (plans[0],plans[4],plans[16],plans[-1]):
                    for ix,sampler in enumerate(SAMPLERS):
                        try:
                            old=ticket(ids,seed,policy,route,sampler,schedule,routes,k)
                        except ValueError:
                            continue
                        new=[]
                        for j,master in enumerate(masters):
                            chosen=chosen_route(routes,seed,j,schedule,route)
                            src=MemoBitStream(RoutedBits(sources_from_seed(master),chosen,256),[])
                            new.append(sample_ticket(src,sampler))
                        self.assertEqual(old,new,(seed,policy,schedule,route,sampler))
    def test_count_and_baselines(self):
        routes,plans=fixed_configs()
        self.assertEqual(len(routes),31)
        self.assertEqual(len(plans),33)
        self.assertEqual(len(SAMPLERS),3)
        self.assertLess(exact_holdout_tail(25),exact_holdout_tail(21))
        self.assertAlmostEqual(exact_holdout_tail(0),1.0)
    def test_incorrect_seed_bounds(self):
        with self.assertRaises(ValueError):run(1,1,0,progress=False)
        with self.assertRaises(ValueError):run(-1,8,0,progress=False)

if __name__=='__main__': unittest.main()
