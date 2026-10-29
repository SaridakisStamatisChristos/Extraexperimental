"""Local regression tests for EXTRA5 seeded replay (no CI).
All inputs are synthetic, not real lottery seeds.
"""
import csv
import hashlib
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments'))
from extra5_historical_engine import Route
from extra5_seed_switch_protocol import demo_nr_key, routes_supported
from extra5_seeded_replay import D, BudgetBits, mask, ticket

class SeededReplayTests(unittest.TestCase):
    def test_source_data(self):
        with (ROOT/'experiments'/'extra5_last100_data.csv').open(newline='') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),100)
        self.assertEqual([int(x['draw_id']) for x in rows],list(range(14256,14356)))
        self.assertEqual(tuple(int(rows[-1][f'n{i}']) for i in range(1,6)),(4,14,15,19,27))
    def test_mask(self):
        self.assertEqual(mask([1,2,35]),(1<<0)|(1<<1)|(1<<34))
    def test_domain_is_experimental(self):
        self.assertIn(b'NOT-OPERATOR-SEEDS',D)
    def test_replay_is_deterministic(self):
        routes=routes_supported()
        p=('fixed',Route('xor',('bbs','aes')))
        for policy in ('fresh_fixture','previous_state_fixture'):
            a=ticket([14256,14257],2,policy,p[1],'combination_rank',p[0],routes,demo_nr_key())
            b=ticket([14256,14257],2,policy,p[1],'combination_rank',p[0],routes,demo_nr_key())
            self.assertEqual(a,b)
            self.assertTrue(all(len(set(x))==5 and all(1<=v<=35 for v in x) for x in a))
    def test_switch_routes(self):
        routes=routes_supported()
        for schedule in ('fixed','round_robin','hash_switch'):
            x=ticket([14256],2,'fresh_fixture',routes[0],'combination_rank',schedule,routes,demo_nr_key())
            self.assertEqual(len(x[0]),5)
    def test_budget_protects_against_endless_rejection(self):
        class AllZero:
            def bit(self):return 0
        b=BudgetBits(AllZero())
        for _ in range(1024):self.assertEqual(b.bit(),0)
        with self.assertRaisesRegex(ValueError,'1024'):b.bit()
    def test_seed_index_changes_output(self):
        routes=routes_supported()
        x=ticket([14256,14257,14258],0,'fresh_fixture',routes[0],'combination_rank','fixed',routes,demo_nr_key())
        y=ticket([14256,14257,14258],3,'fresh_fixture',routes[0],'combination_rank','fixed',routes,demo_nr_key())
        self.assertNotEqual(x,y)

if __name__=='__main__':unittest.main()
