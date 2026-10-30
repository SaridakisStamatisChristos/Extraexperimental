#!/usr/bin/env python3
"""Independent regression and correctness tests for five-year EXTRA 5 archive."""
from __future__ import annotations
import csv,hashlib,itertools,json,math,sys,unittest
from pathlib import Path
import numpy as np
from scipy.stats import hypergeom
from timestamp_prng_scan import gen,sample,metadata,make_seed,asmask
from prepare_five_year import combinadic_rank
from five_year_followup import poly_power,exact_overlap_tail,paircounts
ROOT=Path(__file__).resolve().parent

class FiveYearTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT/'extra5_2022_2026_authoritative.csv').open(newline='') as f:
            cls.rows=list(csv.DictReader(f))
        cls.freeze=json.loads((ROOT/'selected_generator_PRE_EVALUATION.json').read_text())
        cls.result=json.loads((ROOT/'seeded_generator_results.json').read_text())
    def test_full_length_and_id_contiguity(self):
        self.assertEqual(len(self.rows),3526)
        self.assertEqual([int(r['draw_id']) for r in self.rows],list(range(10832,14358)))
    def test_year_counts_and_leap_year(self):
        counts=[sum(r['date'].startswith(str(y)) for r in self.rows) for y in range(2022,2027)]
        self.assertEqual(counts,[730,730,732,730,604])
    def test_cross_year_boundaries(self):
        self.assertEqual((self.rows[2191]['draw_id'],self.rows[2192]['draw_id']),('13023','13024'))
        self.assertEqual((self.rows[2921]['draw_id'],self.rows[2922]['draw_id']),('13753','13754'))
    def test_corrected_14249(self):
        r=self.rows[14249-10832]
        self.assertEqual([int(r[f's{i}']) for i in range(1,6)],[2,4,30,33,35])
    def test_numbers_are_valid_and_correctly_sorted(self):
        for r in self.rows:
            raw=[int(r[f'n{i}']) for i in range(1,6)]
            self.assertEqual(len(set(raw)),5)
            self.assertTrue(all(1<=x<=35 for x in raw))
            self.assertEqual(sorted(raw),[int(r[f's{i}']) for i in range(1,6)])
    def test_combinadic_rank_independent_enumeration(self):
        targets={(tuple(int(r[f's{i}']) for i in range(1,6))):int(r['lex_rank']) for r in self.rows}
        # Complete independent brute force oracle for all 324632 possible combinations.
        matched=0
        for rank,combo in enumerate(itertools.combinations(range(1,36),5)):
            if combo in targets:
                self.assertEqual(targets[combo],rank)
                self.assertEqual(combinadic_rank(combo),rank)
                matched+=1
        self.assertGreater(matched,3400)
    def test_frozen_source_digest(self):
        digest=hashlib.sha256((ROOT/'extra5_2022_2026_authoritative.csv').read_bytes()).hexdigest()
        self.assertEqual(digest,self.freeze['source_sha256'])
        self.assertEqual(digest,self.result['dataset_sha256'])
    def test_calendar_file_has_no_future_outcomes(self):
        with (ROOT/'evaluation_calendar_2025_2026.csv').open(newline='') as f:
            reader=csv.DictReader(f)
            self.assertEqual(reader.fieldnames,['draw_id','date','time'])
            self.assertEqual(len(list(reader)),1334)
        with (ROOT/'train_2022_2024.csv').open(newline='') as f:
            reader=csv.DictReader(f)
            self.assertEqual(len(list(reader)),2192)

    def test_selected_model_parameters_locked(self):
        self.assertEqual(self.freeze['selected_candidate'],self.result['selected'])
        self.assertEqual(self.freeze['candidate_count'],1080)
        self.assertEqual(self.freeze['selection_years'],[2022,2023,2024])
    def test_no_training_leakage_model_selection_year(self):
        self.assertEqual(self.rows[2191]['date'],'2024-12-31')
        self.assertEqual(self.rows[2192]['date'],'2025-01-01')
        self.assertEqual(self.rows[2922]['date'],'2026-01-01')
    def test_splitmix64_independent_known_vector(self):
        self.assertEqual(next(gen('splitmix64',0)),0xe220a839)
        self.assertEqual(next(gen('xorshift64star',1)),0x47e4ce4b)
    def test_prediction_vector_independent_replay(self):
        chosen=self.freeze['selected_candidate']
        forecasts=self.freeze['predictor']
        self.assertEqual(len(forecasts),1334)
        for j in [0,1,729,730,731,1333]:
            r=self.rows[2192+j]
            seed=make_seed(metadata(r),chosen['seed_rule'],chosen['seed_offset'])
            ticket=sample(chosen['generator'],seed,chosen['sampler'])
            self.assertEqual(list(ticket),forecasts[j])
    def test_exact_overlap_distribution_small_n_independent_convolution(self):
        p=hypergeom.pmf(np.arange(6),35,5,5)
        a=poly_power(p,3)
        b=np.convolve(np.convolve(p,p),p)
        self.assertTrue(np.allclose(a,b,atol=1e-10))
        self.assertAlmostEqual(a.sum(),1)
    def test_calibrated_match_pvalues(self):
        obs=self.result['selected_test_hits']
        computed=exact_overlap_tail(604,obs)
        self.assertAlmostEqual(computed['exact_p_at_least_observed'],.28740174579449923,places=8)
    def test_fixed_validation_and_test_scores_against_independent_reference(self):
        f=self.freeze['predictor']
        truth=[set(int(r[f'n{i}']) for i in range(1,6)) for r in self.rows[2192:]]
        val=sum(len(set(a)&b) for a,b in zip(f[:730],truth[:730]))
        test=sum(len(set(a)&b) for a,b in zip(f[730:],truth[730:]))
        self.assertEqual(val,538)
        self.assertEqual(test,442)
        self.assertEqual(sum(set(a)==b for a,b in zip(f,truth)),0)
    def test_pair_matrix_against_brute_force(self):
        a=np.array([[1,2,3,4,5],[1,2,6,7,8]],dtype=np.int16)
        counts=paircounts(a)
        self.assertEqual(int(counts[0,1]),2)
        self.assertEqual(int(counts[0,2]),1)
        self.assertEqual(int(counts[5,6]),1)
        self.assertEqual(int(counts[10,11]),0)

if __name__=='__main__':unittest.main()
