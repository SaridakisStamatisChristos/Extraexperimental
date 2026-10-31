"""Independent differential and adversarial tests of online GF(2) pruning."""
import random
import unittest
from math import comb
from online_path_solver import recover_online,candidate_from_pivots,count_allocations
from variable_rejection import recover_bounded,recover_from_prefix,generate_trace
from rank_inverse import MODELS
from test_variable_rejection import forced_later_rejection, forced_first_rejection

class OnlineSolverTests(unittest.TestCase):
    def test_stars_bars_exact_enumeration(self):
        from itertools import combinations_with_replacement
        for n in range(1,7):
            for k in range(5):
                manual=sum(sum(1 for _ in combinations_with_replacement(range(n),j)) for j in range(k+1))
                self.assertEqual(count_allocations(n,k),manual)

    def test_zero_rejection_cross_model_and_holdout(self):
        seeds={'marsaglia128':0x123456789abcdef0fedcba9876543211,
               'xoroshiro128plus':0x9876543210012345abcdef0123456789,
               'xoshiro256plus':0xcafedeadbeef123456789abcd112233489abcdef01234567823334445556666}
        for name,seed in seeds.items():
            m=MODELS[name]
            n=65 if name=='marsaglia128' else 155 if name=='xoroshiro128plus' else 280
            data,skips,_=generate_trace(m,seed,n+30)
            self.assertEqual(sum(skips),0)
            ans=recover_online(m,data[:n],prefix_length=n,max_prefix_skips=0)
            self.assertEqual(ans['status'],'SAT',ans)
            self.assertEqual(int(ans['witness']['seed'],16),seed)
            # Independent reference algorithm agrees on witness.
            baseline=recover_bounded(m,data[:n],max_skips=0)
            self.assertEqual(baseline['status'],'SAT')
            self.assertEqual(int(baseline['seed'],16),seed)
            replay,_,_=generate_trace(m,seed,n+30)
            self.assertEqual(replay[n:],data[n:])

    def test_late_rejection_and_full_replay(self):
        m=MODELS['marsaglia128'];seed=forced_later_rejection(14)
        data,counts,_=generate_trace(m,seed,175)
        self.assertEqual(counts[14],1)
        online=recover_online(m,data[:70],prefix_length=60,max_prefix_skips=1)
        oracle=recover_from_prefix(m,data[:70],prefix_length=60,max_prefix_skips=1)
        self.assertEqual(online['status'],oracle['status'])
        self.assertEqual(int(online['witness']['seed'],16),seed)
        self.assertEqual(online['witness']['recovered_prefix_skip_counts'][14],1)
        self.assertEqual(online['witness']['full_ticket_replay'],70)

    def test_alias_earliest_seed_is_not_unique(self):
        m=MODELS['marsaglia128'];seed=forced_first_rejection()
        data,counts,_=generate_trace(m,seed,180)
        self.assertEqual(counts[0],1)
        online=recover_online(m,data[:80],prefix_length=65,max_prefix_skips=1)
        self.assertEqual(online['status'],'SAT')
        self.assertNotEqual(int(online['witness']['seed'],16),seed)
        self.assertEqual(online['witness']['prefix_rejections'],0)

    def test_wrong_model_complete_and_path_count(self):
        m=MODELS['marsaglia128'];seed=forced_later_rejection(14)
        data,_,_=generate_trace(m,seed,150)
        online=recover_online(m,data[:60],prefix_length=60,max_prefix_skips=0)
        oracle=recover_from_prefix(m,data[:60],prefix_length=60,max_prefix_skips=0)
        self.assertEqual(online['status'],oracle['status'])
        self.assertEqual(online['status'],'UNSAT')
        self.assertEqual(online['pruned_leaf_path_multiplicity'],1)

    def test_rank_deficiency_unknown(self):
        m=MODELS['xoshiro256plus'];seed=0x33445566778899
        data,_,_=generate_trace(m,seed,45)
        ans=recover_online(m,data,prefix_length=45,max_prefix_skips=0)
        self.assertEqual(ans['status'],'UNKNOWN')
        self.assertTrue(ans['search_complete'])
        self.assertEqual(ans['rank_deficient_terminal_paths'],1)

    def test_budget_cannot_falsely_claim_unsat(self):
        m=MODELS['marsaglia128'];seed=forced_later_rejection(14)
        data,_,_=generate_trace(m,seed,75)
        result=recover_online(m,data,prefix_length=60,max_prefix_skips=2,max_nodes=1)
        self.assertEqual(result['status'],'UNKNOWN',result)
        self.assertFalse(result['search_complete'])
        self.assertTrue(result['budget_exceeded'])

    def test_mutated_ticket_rejected(self):
        m=MODELS['marsaglia128'];seed=0x897654321abcdef001244334532111aa
        data,_,_=generate_trace(m,seed,75)
        changed=list(data)
        changed[20]=tuple(x for x in range(1,36) if x not in changed[20])[:5]
        bad=recover_online(m,changed[:65],max_prefix_skips=0)
        self.assertEqual(bad['status'],'UNSAT',bad)

    def test_rank_zero_not_committed_as_unsat(self):
        m=MODELS['xoroshiro128plus'];seed=0x12345
        data,_,_=generate_trace(m,seed,10)
        for k in (0,1):
            ans=recover_online(m,data,prefix_length=10,max_prefix_skips=k)
            self.assertEqual(ans['status'],'UNKNOWN')
            self.assertGreater(ans['rank_deficient_terminal_paths'],0)

if __name__=='__main__':unittest.main(verbosity=2)
