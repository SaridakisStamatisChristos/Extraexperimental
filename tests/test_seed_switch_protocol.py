"""Regression and falsification tests for the historical research pipeline.

No live keys, results, secrets or predictive claims; no CI.
Run: python -m unittest discover -s tests -p 'test_seed_switch_protocol.py' -v
"""
import dataclasses
import hashlib
import itertools
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"experiments"))

from extra5_historical_engine import Route, ReplayBits
from extra5_seed_switch_protocol import (
    NRKey, SeedInput, DrawSpec, demo_nr_key, allowed_routes,
    coupon_hash, seed_pipeline, expand, unrank_five, sample_ticket,
    demo_spec, draw, verify
)


class SeedPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key=demo_nr_key()

    def test_31_structural_routes(self):
        r=allowed_routes()
        self.assertEqual(len(r),31)
        self.assertEqual(len(set(r)),31)
        self.assertEqual(sum(x.operation=="m" for x in r),12)
        self.assertEqual(sum(x.operation=="xor" for x in r),11)

    def test_nr_direct_math_oracle(self):
        k=NRKey(23,11,2,(3,4,6,8,10,2,3,5,7))
        bits=[1,0,1,0,0,1,0,1]
        exponent=3
        for b,a in zip(bits,k.factors[1:]):
            if b: exponent=exponent*a%11
        self.assertEqual(k.evaluate(bytes([0b10100101])),
                         bytes([pow(2,exponent,23)]))

    def test_nr_factor_length_guard(self):
        with self.assertRaises(ValueError):
            self.key.evaluate(bytes(31))

    def test_seed_xor_and_coupon_binding(self):
        samples=SeedInput(physical=(bytes([255])*32,bytes(32)))
        self.assertEqual(samples.merged(),bytes([255])*32)
        t=seed_pipeline(7,b"coupon A",samples,self.key)
        self.assertEqual(t.mixed,bytes(255^b for b in coupon_hash(b"coupon A")))
        self.assertNotEqual(t.master,
                            seed_pipeline(7,b"coupon B",samples,self.key).master)

    def test_seed_state_branch(self):
        state=SeedInput(prior_state=bytes([7])*32)
        self.assertEqual(state.merged(),bytes([7])*32)
        self.assertNotEqual(seed_pipeline(7,b"a",state,self.key).master,
                            seed_pipeline(8,b"a",state,self.key).master)

    def test_invalid_seed_branches(self):
        cases=[SeedInput(),SeedInput(prior_state=b"bad"),
               SeedInput(physical=(bytes(32),),prior_state=bytes(32)),
               SeedInput(physical=(b"bad",))]
        for c in cases:
            with self.subTest(case=c), self.assertRaises(ValueError):c.merged()

    def test_component_domain_separation(self):
        master=bytes(64)
        self.assertNotEqual(expand(master,"aes/key",24),
                            expand(master,"des/key",24))

    def test_unrank_endpoints(self):
        self.assertEqual(unrank_five(0),(1,2,3,4,5))
        self.assertEqual(unrank_five(math.comb(35,5)-1),(31,32,33,34,35))

    def test_unrank_exhaustive_bijection(self):
        self.assertEqual(len(set(map(unrank_five,range(math.comb(35,5))))),
                         math.comb(35,5))

    def test_unrank_first_100_lexicographic(self):
        seq=itertools.combinations(range(1,36),5)
        for i in range(100):self.assertEqual(unrank_five(i),next(seq))

    def test_rejection_of_overflow_19bit_value(self):
        def bits(v):
            return [(v>>i)&1 for i in range(18,-1,-1)]
        source=ReplayBits(bits(524287)+bits(324631))
        self.assertEqual(sample_ticket(source,"combination_rank"),
                         (31,32,33,34,35))

    def test_sampler_variants(self):
        for method in ("sequential","combination_rank","distinct_rejection"):
            if method=="distinct_rejection":
                data=[(v>>i)&1 for v in range(5) for i in range(5,-1,-1)]
            else:
                data=[0]*2048
            result=sample_ticket(ReplayBits(data),method)
            self.assertEqual(len(result),5)
            self.assertEqual(len(set(result)),5)
            self.assertTrue(all(1<=x<=35 for x in result))

    def test_all_routes_reproduce_independently(self):
        for idx,route in enumerate(allowed_routes()):
            spec=demo_spec(idx,route)
            actual=draw(spec,self.key)
            self.assertTrue(verify(spec,self.key,actual),str(route))
            self.assertEqual(len(actual.numbers),5)

    def test_switch_falsifies_receipt(self):
        original=demo_spec(100,Route("m",("bbs","des")))
        changed=dataclasses.replace(original,route=Route("b",("rsa",)))
        self.assertFalse(verify(changed,self.key,draw(original,self.key)))

    def test_wrong_coupon_rejected(self):
        spec=demo_spec(100)
        self.assertFalse(verify(dataclasses.replace(spec,coupons=b"wrong"),
                                self.key,draw(spec,self.key)))

    def test_wrong_entropy_rejected(self):
        spec=demo_spec(100)
        self.assertFalse(verify(dataclasses.replace(spec,seeds=SeedInput(
            prior_state=bytes(32))),self.key,draw(spec,self.key)))

    def test_tampered_number_rejected(self):
        spec=demo_spec(100)
        r=draw(spec,self.key)
        other=(1,2,3,4,5) if r.numbers!=(1,2,3,4,5) else (1,2,3,4,6)
        self.assertFalse(verify(spec,self.key,dataclasses.replace(r,numbers=other)))

    def test_forged_digest_rejected(self):
        spec=demo_spec(100)
        r=draw(spec,self.key)
        self.assertFalse(verify(spec,self.key,dataclasses.replace(
            r,receipt_sha256="0"*64)))

    def test_invalid_route_rejected(self):
        with self.assertRaises(ValueError):
            demo_spec(100,Route("m",("aes","cast")))

    def test_block_bits_bound(self):
        with self.assertRaises(ValueError):
            dataclasses.replace(demo_spec(100),block_bits=7)


if __name__=="__main__":
    unittest.main()
