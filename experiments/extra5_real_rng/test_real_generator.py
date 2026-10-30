#!/usr/bin/env python3
"""Independent regression/oracle checks of exact PRNG and sampler reconstructions."""
import csv,hashlib,json,math,unittest
from pathlib import Path
from recover_exact import Z3Lib,solve_prefix,forward_no_rejection,N,LIMIT
from timestamp_prng_scan import unrank,gen,make_seed,metadata,sample,future_meta
P=Path(__file__).resolve().parent
class GeneratorTests(unittest.TestCase):
    def test_ordered_rank_boundary(self):
        self.assertEqual(unrank(0),(1,2,3,4,5))
        self.assertEqual(unrank(N-1),(31,32,33,34,35))
        self.assertEqual(len({unrank(i) for i in range(1000)}),1000)
    def test_sampler_never_invalid(self):
        for kind in ['numerical_lcg32','ansi_lcg32_fullword','xorshift32','splitmix64','pcg32_fixed_stream','mt19937_python']:
            for mode in ['rank32_rejection','combinadic24','unique_mod35','fisher_yates5_modulo','fisher_yates5_unbiased']:
                for seed in (0,1,42,2123):
                    if seed==0 and kind=='xorshift32':continue
                    nums=sample(kind,seed,mode)
                    self.assertEqual(len(nums),5)
                    self.assertEqual(tuple(sorted(set(nums))),nums)
                    self.assertTrue(all(1<=n<=35 for n in nums))
    def test_known_xorshift32_vector(self):
        self.assertEqual(next(gen('xorshift32',1)),270369)
    def test_known_splitmix64_vector(self):
        self.assertEqual(next(gen('splitmix64',0)),0xe220a839)
    def test_real_training_integrity(self):
        with (P/'train_599.csv').open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),599)
        self.assertEqual([int(r['draw_id']) for r in rows],list(range(13754,14353)))
        self.assertEqual(hashlib.sha256((P/'train_599.csv').read_bytes()).hexdigest(),'cc2e3da23f5edab6f310f68a1204c00aa0113dcd38660b2e732346ce5cf9b8e4')
        self.assertEqual(len(set(tuple(int(r[f'n{i}']) for i in range(1,6)) for r in rows)),599)
    def test_lock_integrity_and_separation(self):
        lock=json.loads((P/'algorithm_forecasts_LOCK.json').read_text())
        self.assertEqual(lock['train_sha256'],hashlib.sha256((P/'train_599.csv').read_bytes()).hexdigest())
        self.assertEqual([r['draw_id'] for r in lock['forecasts']],list(range(14353,14358)))
        with (P/'train_599.csv').open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(future_meta(rows[-1]),[{k:r[k] for k in ('draw_id','date','time')} for r in [{'draw_id':str(x['draw_id']),'date':x['date'],'time':x['time']} for x in lock['forecasts']]])
        chosen=lock['chosen_algorithm']
        for p in lock['forecasts']:
            meta=metadata({'draw_id':p['draw_id'],'date':p['date'],'time':p['time']})
            seed=make_seed(meta,chosen['seed_type'],chosen['seed_offset'])
            self.assertEqual(seed,int(p['seed']))
            self.assertEqual(list(sample(chosen['prng'],seed,chosen['sampler'])),p['numbers'])
    def test_smt_recovers_real_synthetic_state(self):
        solver=Z3Lib()
        for kind,seed in [('nr_lcg32',(12345,)),('ansi_lcg32',(12345,)),('msvc_lcg32',(12345,)),('xorshift32',(12345,)),('xorshift128',(12345,6789,9876,54321))]:
            # All first four raw24 values must be accepted for the no-rejection branch.
            raw=forward_no_rejection(kind,seed,4)
            self.assertTrue(all(v<LIMIT for v in raw))
            result=solve_prefix(solver,kind,[r%N for r in raw],4,timeout_ms=10000)
            self.assertEqual(result['result'],'sat',(kind,result))
            self.assertEqual([r%N for r in result['raw24']],[r%N for r in raw])
    def test_solver_negative_certificates(self):
        results=json.loads((P/'exact_state_results.json').read_text())
        self.assertEqual(results['training_draws'],599)
        for kind in ['nr_lcg32','ansi_lcg32','msvc_lcg32','xorshift32']:
            self.assertEqual(results['families'][kind][0]['result'],'unsat')
        # unknown is *not* an elimination.
        self.assertEqual(results['families']['xorshift128'][-1]['result'],'unknown')
    def test_exhaustive_branch_negative_cert(self):
        result=json.loads((P/'exact_xorshift96_first_six_results.json').read_text())
        self.assertEqual(result['raw_fits_exhaustive'],51**4)
        self.assertEqual(result['sixth_matching_states_given_first_five'],0)
        self.assertEqual(result['fifth_matching_states'],26)
    def test_multiple_search_adjustment(self):
        report=json.loads((P/'timestamp_scan_results.json').read_text())
        self.assertEqual(report['family_count'],1080)
        self.assertGreater(report['selection_null_calibration']['p_max_corrected'],.05)
        self.assertEqual(report['selection_winner']['exact_validation199'],0)
        self.assertEqual(report['selection_winner']['hits_validation199'],140)
    def test_holdout_independent_math(self):
        report=json.loads((P/'holdout_algorithm_results.json').read_text())
        self.assertEqual(sum(x['overlap'] for x in report['outcomes']),2)
        self.assertEqual(report['exact_ticket_matches'],0)
        self.assertEqual(report['lock_sha256'],hashlib.sha256((P/'algorithm_forecasts_LOCK.json').read_bytes()).hexdigest())
        self.assertAlmostEqual(report['uniform_expected_total_matches'],25/7,places=10)

if __name__=='__main__':unittest.main(verbosity=2)
