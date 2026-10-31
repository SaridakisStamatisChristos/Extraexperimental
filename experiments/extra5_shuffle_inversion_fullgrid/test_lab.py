#!/usr/bin/env python3
"""Run this without invoking any costly full-grid search. unittest -v test_lab.py"""
import csv
from ctypes.util import find_library
import hashlib
import math
import subprocess
import tempfile
import unittest
from pathlib import Path

from audit_results import ROOT, TOTAL_TRIPLES, MODELS_PER_SAMPLER, aggregate, phase_data
from independent_verify import INPUT, expected_allowed, load_masks, gen, test_all_masks, test_planted
from smt_inverse64 import step64, rows_for_draws, LibZ3

MASK32=(1<<32)-1
SEEDS={(13,17,5):0x89ABCDEF,(5,17,13):0x9A876543,(7,9,13):0x6A5F1234}


def generate_high(seed,a,b,c,gap,n):
    def transition(x):
        x^=(x<<a)&MASK32
        x^=x>>b
        x^=(x<<c)&MASK32
        return x&MASK32
    s=seed
    for _ in range(n):
        pool=list(range(1,36));chosen=[]
        for k in range(5):
            s=transition(s)
            chosen.append(pool.pop((s*len(pool))>>32))
        for _ in range(gap):s=transition(s)
        yield sum(1<<(v-1) for v in chosen)


class TestInverseLaboratory(unittest.TestCase):
    def test_combinatorics(self):
        self.assertEqual(math.comb(35,5),324632)
        self.assertEqual((31**3)*2*5,297910)

    def test_raw_dataset_identity(self):
        p=ROOT/'extra5_2022_2026_authoritative.csv'
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),'61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307')
        with p.open(newline='') as f:source=list(csv.DictReader(f))
        transformed=load_masks(INPUT/'real_unordered.csv')
        self.assertEqual(len(source),3526)
        self.assertEqual(len(transformed),len(source))
        for i,(original,model) in enumerate(zip(source,transformed)):
            self.assertEqual(int(original['draw_id']),10832+i)
            numbers=[int(original[f'n{k}']) for k in range(1,6)]
            self.assertEqual(len(set(numbers)),5)
            self.assertTrue(all(1<=v<=35 for v in numbers))
            computed=sum(1<<(x-1) for x in numbers)
            self.assertEqual(int(model['ticket_mask']),computed)

    def test_fourth_index_masks_recomputed_without_order(self):
        self.assertEqual(test_all_masks(),3886)
        for p in ROOT.glob('synthetic_high_*_stride[57].csv'):
            for row in load_masks(p):
                self.assertEqual(int(row['allowed_fourth_mask']),expected_allowed(int(row['ticket_mask'])))

    def test_six_modulo_planted_generators(self):
        self.assertEqual(len(test_planted()),6)

    def test_six_multiply_high_planted_generators(self):
        for (a,b,c),seed in SEEDS.items():
            for stride in (5,7):
                observed=[int(x['ticket_mask']) for x in load_masks(ROOT/f'synthetic_high_{a}_{b}_{c}_stride{stride}.csv')]
                self.assertEqual(observed,list(generate_high(seed,a,b,c,stride-5,60)))
                output=load_masks(ROOT/f'synthetic_high_{a}_{b}_{c}_stride{stride}_recovered.csv')
                witness=next(r for r in output if int(r['direction'])==0 and int(r['extra_gap'])==stride-5)
                self.assertEqual(int(witness['witness_seed']),seed)
                self.assertEqual(int(witness['max_exact_prefix']),60)

    def test_twelve_positive_replays(self):
        # Stronger than a single seed: compare every indicated planted witness and
        # 60 tickets to both independent Python samplers.
        for (a,b,c),seed in SEEDS.items():
            for stride in (5,7):
                for sampler in ('mod','high'):
                    path=ROOT/f'synthetic_{a}_{b}_{c}_stride{stride}_recovery.csv' if sampler=='mod' else ROOT/f'synthetic_high_{a}_{b}_{c}_stride{stride}_recovered.csv'
                    rows=load_masks(path)
                    witness=next(r for r in rows if int(r['direction'])==0 and int(r['extra_gap'])==stride-5)
                    self.assertEqual(int(witness['witness_seed']),seed)

    def test_full_modulo_grid_accounting(self):
        r=phase_data(sorted(ROOT.glob('full_*.csv')),sorted(ROOT.glob('stage2_*.csv')),'mod')
        self.assertEqual(r['total'],MODELS_PER_SAMPLER)
        self.assertEqual(r['fully_enumerated'],144440)
        self.assertEqual(r['not_fully_enumerated'],153470)
        self.assertEqual(r['primitive_models_fully_refuted'],1620)
        self.assertEqual(r['full_prefix_max'],1)

    def test_full_high_grid_accounting(self):
        r=phase_data(sorted(ROOT.glob('high_full_*.csv')),sorted(ROOT.glob('high_stage2_*.csv')),'high')
        self.assertEqual(r['total'],MODELS_PER_SAMPLER)
        self.assertEqual(r['fully_enumerated'],144440)
        self.assertEqual(r['not_fully_enumerated'],153470)
        self.assertEqual(r['primitive_models_fully_refuted'],1620)
        self.assertEqual(r['full_prefix_max'],0)

    def test_primitive_transition_periods(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'primitive.csv'
            subprocess.run([str(ROOT/'maximal_period32'),str(p)],check=True,capture_output=True,text=True)
            self.assertEqual(p.read_bytes(),(ROOT/'primitive_triples.csv').read_bytes())
            with p.open() as f:self.assertEqual(len(list(csv.DictReader(f))),324)

    def test_xorshift64_linear_form_oracle(self):
        for gap in (0,2):
            forms=rows_for_draws(40,gap)
            for seed in (1,0x89abcdef12345678,0xffffffffffffffff,0x1234abcd5678aaaa):
                s=seed
                for d in range(40):
                    for k in range(5):
                        s=step64(s)
                        if k==3:expected=s&31
                    for _ in range(gap):s=step64(s)
                    computed=sum(((seed&forms[d][k]).bit_count()&1)<<k for k in range(5))
                    self.assertEqual(computed,expected)

    @unittest.skipUnless(find_library("z3"), "optional libz3 unavailable")
    def test_smt_model_decoder(self):
        instance='(set-logic QF_BV)\n(declare-fun s () (_ BitVec 64))\n(assert (= s #x89abcdef12345678))\n'
        answer=LibZ3().run(instance,1000)
        self.assertEqual(answer['status'],'SAT')
        self.assertEqual(answer['state'],0x89abcdef12345678)

    def test_cpp_sources_recompile_clean(self):
        cpp=['shuffle_inverse32.cpp','shuffle_inverse32_8obs.cpp','shuffle_inverse32_high.cpp','shuffle_inverse32_high_8obs.cpp','maximal_period32.cpp']
        with tempfile.TemporaryDirectory() as d:
            for c in cpp:
                subprocess.run(['g++','-std=c++20','-O2','-Wall','-Wextra','-Werror',str(ROOT/c),'-o',str(Path(d)/c)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

if __name__=='__main__':unittest.main(verbosity=2)
