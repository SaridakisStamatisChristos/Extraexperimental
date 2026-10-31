#!/usr/bin/env python3
"""Independent model-specific regression controls for rank-based state inversion."""
from itertools import combinations
from math import comb
import random
import unittest

from rank_inverse import MODELS,N,combination_rank,combination_unrank,generate,recover,low_forms,solve,rotl

MASK=(1<<64)-1

def reference_words(which, seed, count):
    """Implementation intentionally independent of production generator functions."""
    w=32 if which=='marsaglia128' else 64
    state=[(seed>>(i*w))&((1<<w)-1) for i in range(4 if which!='xoroshiro128plus' else 2)]
    out=[]
    for _ in range(count):
        if which=='marsaglia128':
            v=((state[0]<<11)^state[0])&0xffffffff
            z=(state[3]^(state[3]>>19)^v^(v>>8))&0xffffffff
            state=state[1:]+[z];out.append(z)
        elif which=='xoroshiro128plus':
            p,q=state
            out.append((p+q)&MASK)
            z=p^q
            state=[(((p<<24)|(p>>(64-24)))^z^(z<<16))&MASK, ((z<<37)|(z>>(64-37)))&MASK]
        elif which=='xoshiro256plus':
            a,b,c,d=state
            out.append((a+d)&MASK)
            t=(b<<17)&MASK
            state=[(a^d^b)&MASK,(b^c^a)&MASK,(c^a^t)&MASK,((d^b)<<45 | (d^b)>>(64-45))&MASK]
        else:raise AssertionError(which)
    return out

class TestCombinationRankInverse(unittest.TestCase):
    def test_population_and_lex_rank_exhaustive(self):
        self.assertEqual(N,324632)
        self.assertEqual(N%8,0)
        self.assertNotEqual(N%16,0)
        for r,ticket in enumerate(combinations(range(1,36),5)):
            self.assertEqual(combination_rank(ticket),r)
            self.assertEqual(combination_unrank(r),ticket)
        # Verified first canonical row recorded by project's authoritative CSV
        self.assertEqual(combination_rank((30,34,21,15,8)),238681)

    def test_invalid_input(self):
        for x in [(1,1,2,3,4),(0,1,2,3,4),(1,2,3,4,36),(1,2,3,4)]:
            with self.assertRaises(ValueError):combination_rank(x)
        for x in [-1,N]:
            with self.assertRaises(ValueError):combination_unrank(x)

    def test_independent_forward_implementations(self):
        seed128=0x99887766554433221100ffeeddccbbaa
        seed256=int('123456789abcdef0fedcba9876543210cafebabedeadbeef0123456789abcdef',16)
        for name,m in MODELS.items():
            for seed in (1,seed128 if m.size==128 else seed256):
                s=m.decode(seed)
                words=[]
                for _ in range(36):
                    s,w=m.step(s);words.append(w)
                self.assertEqual(words,reference_words(name,seed,36))
                actual=list(generate(m,seed,36))
                expected=[combination_unrank(w%N) for w in words]
                self.assertEqual(actual,expected)

    def test_exact_lowbit_projection_under_addition(self):
        for name,m in MODELS.items():
            f=low_forms(m,45,0)
            rng=random.Random(947)
            for seed in [1,(1<<m.size)-1,*[rng.getrandbits(m.size) for _ in range(3)]]:
                s=m.decode(seed)
                for d in range(45):
                    s,w=m.step(s)
                    for k in range(m.proved_linear_low_bits):
                        self.assertEqual((seed&f[d][k]).bit_count()&1,(w>>k)&1)

    def test_unrestricted_synthetic_recovery_with_holdout(self):
        seeds128=(1,0x123456789abcdef0fedcba9876543210,0x99887766554433221100ffeeddccbbaa)
        seeds256=(1,int('123456789abcdef0fedcba9876543210cafebabedeadbeef0123456789abcdef',16),
                  int('a185aa00003918cafedcba98765432100112233445566778899aabbccddeeff',16))
        counts={128:200,256:335}
        for name,m in MODELS.items():
            for gap in (0,2):
                for seed in seeds128 if m.size==128 else seeds256:
                    with self.subTest(model=name,gap=gap,seed=seed):
                        train_count=counts[m.size]
                        all_data=list(generate(m,seed,train_count+100,gap))
                        result=recover(m,all_data[:train_count],gap)
                        self.assertEqual(result['status'],'SAT',result)
                        self.assertEqual(int(result['recovered_seed'],16),seed)
                        self.assertTrue(result['full_ticket_replay'])
                        self.assertEqual(list(generate(m,seed,len(all_data),gap)),all_data)
                        oracle_words=reference_words(name,seed,len(all_data)*(1+gap))
                        independently_expected=[combination_unrank(oracle_words[d*(1+gap)]%N)
                                                for d in range(len(all_data))]
                        self.assertEqual(independently_expected,all_data)
                        # No extraction indices or seed supplied to recover.

    def test_nullspace_and_wrong_sampler_falsifier(self):
        m=MODELS['xoroshiro128plus'];seed=0x123456789abcdef0fedcba9876543210
        actual=list(generate(m,seed,205))
        self.assertEqual(recover(m,actual[:32])['status'],'UNKNOWN')
        mutated=actual.copy()
        old=combination_rank(mutated[170]);mutated[170]=combination_unrank(old^1)
        self.assertEqual(recover(m,mutated)['status'],'UNSAT')
        # Wrong fixed gap is a different, falsified model.
        self.assertEqual(recover(m,actual,gap=1)['status'],'UNSAT')

    def test_rejection_not_silently_linearized(self):
        m=MODELS['marsaglia128']
        with self.assertRaises(NotImplementedError):
            recover(m,[(1,2,3,4,5)],rejection=True)
        self.assertEqual(((1<<32)%N),85936)
        self.assertEqual(((1<<64)%N),267360)

if __name__=='__main__':unittest.main(verbosity=2)
