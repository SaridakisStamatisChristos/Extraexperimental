#!/usr/bin/env python3
"""Adversarial and independent verification of EXTRA 5 599/5 experiment."""
import csv,hashlib,itertools,json,math,random,tempfile,unittest
from pathlib import Path
import numpy as np
import forecast, challengers, evaluate

HERE=Path(__file__).resolve().parent
class TestExtra5Holdout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train=forecast.load_train(HERE/'train_599.csv')
        cls.lock=json.loads((HERE/'predictions_LOCK.json').read_text())
        cls.challengers=json.loads((HERE/'challengers_LOCK.json').read_text())
    def test_partitions_are_correct(self):
        self.assertEqual(len(self.train),599)
        self.assertEqual(self.train[0].id,13754)
        self.assertEqual(self.train[-1].id,14352)
    def test_wrong_training_length_rejected(self):
        text=(HERE/'train_599.csv').read_text().splitlines()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'in.csv';p.write_text('\n'.join(text[:-1])+'\n')
            with self.assertRaises(ValueError):forecast.load_train(p)
    def test_next_schedule_known(self):
        self.assertEqual(forecast.next_schedule(self.train[-1]),[
            (14353,'2026-10-27','19:00'), (14354,'2026-10-28','15:00'),
            (14355,'2026-10-28','19:00'), (14356,'2026-10-29','15:00'),
            (14357,'2026-10-29','19:00')])
    def test_train_dataset_hash_stays_pinned(self):
        self.assertEqual(hashlib.sha256((HERE/'train_599.csv').read_bytes()).hexdigest(),
            'cc2e3da23f5edab6f310f68a1204c00aa0113dcd38660b2e732346ce5cf9b8e4')
        self.assertEqual(self.lock['train_sha256'],self.challengers['train_sha256'])
    def test_e5_matches_independent_bruteforce(self):
        rng=random.Random(20261030)
        for _ in range(40):
            size=rng.randrange(5,12)
            w=[rng.uniform(.01,4) for i in range(size)]
            calc=forecast.symmetric5(np.array(w))
            ref=math.fsum(math.prod(c) for c in itertools.combinations(w,5))
            self.assertAlmostEqual(calc,ref,places=8)
    def test_product_probability_normalizes_independently(self):
        w=np.array([.7,2.1,1.2,4.,.45,1.3,2.5]+[0.]*28)
        total=sum(math.prod(w[i] for i in comb) for comb in itertools.combinations(range(7),5))
        self.assertAlmostEqual(total,forecast.symmetric5(w))
        self.assertAlmostEqual(sum(math.prod(w[i] for i in c)/total for c in itertools.combinations(range(7),5)),1.)
    def test_inclusion_marginals_and_order(self):
        w=np.linspace(.2,3.5,35)
        m=forecast.odds_marginals(w)
        self.assertAlmostEqual(float(m.sum()),5.,places=10)
        self.assertTrue(all(a<b for a,b in zip(m,m[1:])))
    def test_training_weights_constant_uniform(self):
        d=self.train[505]
        w=forecast.prior_weights(self.train,505,d.date,d.time,('uniform',0,0))
        self.assertTrue(np.all(w==1))
        self.assertAlmostEqual(forecast.log_probability(w,d.numbers),-math.log(math.comb(35,5)))
    def test_all_model_weights_positive_and_finite(self):
        for model in forecast.MODELS:
            d=self.train[544]
            w=forecast.prior_weights(self.train,544,d.date,d.time,model)
            self.assertTrue(np.all(w>0) and np.all(np.isfinite(w)),str(model))
    def test_no_lookahead_and_validation_future_invariant(self):
        index=430;d=self.train[index]
        modified=list(self.train)
        for k in range(index,len(modified)):
            old=modified[k]
            modified[k]=forecast.Draw(old.id,old.date,old.time,(1,2,3,4,5))
        for model in forecast.MODELS:
            a=forecast.prior_weights(self.train,index,d.date,d.time,model)
            b=forecast.prior_weights(modified,index,d.date,d.time,model)
            self.assertTrue(np.array_equal(a,b),str(model))
    def test_random_sampler_is_exact_for_uniform(self):
        weights=np.ones(35)
        # uniform ticket inclusion frequencies across 1200 independent seeds
        all_samples=[forecast.product_weight_sample(weights,k) for k in range(1200)]
        self.assertTrue(all(len(set(x))==5 and all(1<=i<=35 for i in x) for x in all_samples))
        freq=[sum(i in x for x in all_samples) for i in range(1,36)]
        self.assertLess(max(abs(x-1200/7) for x in freq),60)
    def test_empirical_challenger_only_uses_training(self):
        recalculated=challengers.build(HERE/'train_599.csv')
        self.assertEqual(recalculated,self.challengers)
    def test_lock_sha_and_results_reproduced_independently(self):
        res=evaluate.evaluate(HERE/'holdout_5_PRIVATE.csv',HERE/'predictions_LOCK.json',HERE/'challengers_LOCK.json')
        saved=json.loads((HERE/'holdout_results.json').read_text())
        self.assertEqual(res,saved)
        self.assertEqual(res['comparison']['evidence_gated_primary']['primary_total_hits'],3)
        self.assertEqual(res['comparison']['best_training_logscore']['primary_total_hits'],4)
    def test_uniform_hit_pmf_vs_direct_combinatorics(self):
        distribution=evaluate.hit_distribution()
        self.assertAlmostEqual(sum(distribution),1.)
        self.assertAlmostEqual(sum(k*p for k,p in enumerate(distribution)),5*5/35)
        self.assertAlmostEqual(evaluate.tail_n5_at_least(0),1.)
        self.assertAlmostEqual(evaluate.tail_n5_at_least(26),0.)
        self.assertAlmostEqual(evaluate.tail_n5_at_least(4),0.4946880758533767,places=12)
    def test_hard_lock_overwrite_refused(self):
        import subprocess,sys
        result=subprocess.run([sys.executable,str(HERE/'forecast.py'),'--train',str(HERE/'train_599.csv'),'--lock',str(HERE/'predictions_LOCK.json')],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('REFUSE',result.stderr+result.stdout)

if __name__=='__main__':unittest.main(verbosity=2)
