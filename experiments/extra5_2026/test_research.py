#!/usr/bin/env python3
"""Independent verification and adversarial tests for research code; no CI."""
import csv,hashlib,itertools,json,math,random,unittest
from collections import Counter
from pathlib import Path
import numpy as np
import toy_inverse as inv
import statistical_audit as stat
import walkforward_models as walk
import prospective_control as control
from exhaustive_six import raw_fifth

P=Path(__file__).resolve().parent

class TestAuthoritativeData(unittest.TestCase):
    def test_integrity_and_no_gaps(self):
        rows,ordered,tickets=stat.load_data()
        self.assertEqual(len(rows),604)
        self.assertEqual([int(r['draw_id']) for r in rows],list(range(13754,14358)))
        self.assertEqual(list(tickets[14249-13754]),[2,4,30,33,35])
        self.assertEqual(list(ordered[14249-13754]),[35,2,4,30,33])
        self.assertEqual(stat.CSV.read_bytes(),(P/'extra5_authoritative_2026.csv').read_bytes())
        self.assertEqual(hashlib.sha256(stat.CSV.read_bytes()).hexdigest(),'5fb393513548e1c5853165eeb137c66f1a859071eaf0c4c8203f5d487289d33e')

    def test_combinadic_rank_independent_oracle(self):
        ordered=list(itertools.islice(itertools.combinations(range(1,36),5),300))
        a=np.array(ordered,dtype=np.int16)
        self.assertEqual(list(stat.ranks(a)),list(range(300)))
        self.assertEqual(inv.unrank(0),[1,2,3,4,5])
        self.assertEqual(inv.unrank(math.comb(35,5)-1),[31,32,33,34,35])
        for idx in [0,1,99,1977,65241,324631]:
            self.assertEqual(inv.rank(inv.unrank(idx)),idx)

    def test_sampler_properties(self):
        arr=stat.sample_sequences(np.random.default_rng(234),2000)
        self.assertTrue(np.all(np.diff(arr,axis=1)>0))
        self.assertTrue(np.all((arr>=1)&(arr<=35)))
        self.assertTrue(np.array_equal(stat.ranks(np.array([[1,2,3,4,5]],dtype=np.int16)),[0]))

    def test_mask_and_overlap_independent_oracle(self):
        _,_,tickets=stat.load_data()
        mask=stat.mask_of(tickets)
        self.assertEqual(int(mask.sum()),604*5)
        direct=sum(len(set(map(int,a))&set(map(int,b))) for a,b in zip(tickets,tickets[1:]))
        matrix=int((mask[1:]*mask[:-1]).sum())
        self.assertEqual(matrix,direct)
        self.assertEqual(Counter(map(tuple,tickets)).most_common(1)[0][1],2)

class TestHypotheticalGenerator(unittest.TestCase):
    def test_xorshift96_recovery(self):
        ranks=[inv.rank([int(inv.lookup[k][f'n{i}']) for i in range(1,6)]) for k in range(14249,14253)]
        for aliases in [(0,0,0,0),(50,50,50,50),(1,10,15,30),(34,2,16,50)]:
            state,r=inv.reconstruct([a+v*inv.N for a,v in zip(ranks,aliases)])
            self.assertEqual(r,96)
            self.assertEqual([tuple(x) for x in inv.decode(96,state,4)], [tuple(sorted(int(inv.lookup[k][f'n{i}']) for i in range(1,6))) for k in range(14249,14253)])
            words=inv.output(96,state,15)[3:]
            raw,rejects=raw_fifth(words)
            next_ticket=tuple(inv.unrank(raw%inv.N))
            self.assertEqual(next_ticket,tuple(inv.decode(96,state,5)[4]))

    def test_all_fifth_matching_states_replay_forward(self):
        r=json.loads((P/'exhaustive_six_results.json').read_text())
        self.assertEqual(r['raw_fits_exhaustive'],51**4)
        self.assertEqual(r['fifth_ticket_support'],math.comb(35,5))
        self.assertEqual(len(r['state_witnesses']),25)
        self.assertEqual(r['sixth_matching_states_given_first_five'],0)
        for witness in r['state_witnesses']:
            state=int(witness['state_hex'],16)
            self.assertEqual(tuple(inv.decode(96,state,6)[4]),(17,23,30,34,35))
            self.assertNotEqual(tuple(inv.decode(96,state,6)[5]),(1,6,23,26,34))

    def test_xorshift128_full_four_word_rank(self):
        rows=inv.basis(128,4)
        self.assertEqual(len(rows),128)
        state,rank=inv.eliminate(rows,[0]*128,128)
        self.assertEqual((rank,state),(128,0))

class TestForecasts(unittest.TestCase):
    def test_product_score_uniform(self):
        ticket=[2,4,30,33,35]
        self.assertAlmostEqual(walk.product_log_score(np.ones(35),ticket),-math.log(math.comb(35,5)),places=12)

    def test_product_polynomial_against_explicit_subsets(self):
        w=np.array([.9+math.sin(i)*.2 for i in range(1,36)])
        # Full independent direct enumeration of 324,632 subset products.
        brute=0.
        for selection in itertools.combinations(range(35),5):
            p=1.
            for idx in selection:p*=w[idx]
            brute+=p
        t=[1,7,15,21,35]
        independent=sum(math.log(w[i-1]) for i in t)-math.log(brute)
        self.assertAlmostEqual(walk.product_log_score(w,t),independent,places=10)

    def test_no_future_leakage(self):
        rows,_,t=stat.load_data()
        h=np.array([int(x['time'][:2]) for x in rows]); wd=np.array([0 if i%2 else 6 for i in range(len(rows))])
        rng=np.random.default_rng(100)
        altered=t.copy();altered[333:]=stat.sample_sequences(rng,len(t)-333)
        for c in walk.CONFIGS:
            before=walk.weights(t,h,wd,333,c)
            after=walk.weights(altered,h,wd,333,c)
            self.assertTrue(np.array_equal(before,after),c)

    def test_control_lock_can_be_reconstructed(self):
        record=json.loads((P/'prospective_null_control_14360_LOCK.json').read_text())
        self.assertEqual(record,control.derive())
        self.assertEqual(record['ticket'],[2,7,13,26,32])
        self.assertEqual(record['source_last_draw_id'],14357)
        with self.assertRaises(ValueError):control.derive(14357)

if __name__=='__main__':unittest.main(verbosity=2)
