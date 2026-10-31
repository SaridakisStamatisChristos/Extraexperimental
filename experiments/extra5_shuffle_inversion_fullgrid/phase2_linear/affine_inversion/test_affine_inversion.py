#!/usr/bin/env python3
"""Independent planted-state, all-combination, mutation and completeness tests."""
import itertools,random,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inverse_linear import MODELS
from affine import fourth_domain,affine_constraints,census
from recover_affine import recover
from real_audit import audit,check_certificate

M32=(1<<32)-1;M64=(1<<64)-1

def rol(v,n):return ((v<<n)|(v>>(64-n)))&M64

def oracle_step(name,s):
    if name=='xorshift128':
        x,y,z,w=s;t=(x^(x<<11))&M32
        w=(w^(w>>19)^t^(t>>8))&M32
        return (y,z,s[3],w),w
    if name=='xoroshiro128_raw':
        a,b=s;v=a^b;c=(rol(a,24)^v^(v<<16))&M64;d=rol(v,37)
        return (c,d),c
    if name=='xoshiro256_raw':
        a,b,c,d=s;t=(b<<17)&M64
        c^=a;d^=b;b^=c;a^=d;c^=t;d=rol(d,45)
        return (a,b,c,d),a
    raise AssertionError('unknown model')

def oracle_tickets(model,seed,n,gap,sampler):
    state=model.from_integer(seed);output=[]
    for _ in range(n):
        pool=list(range(1,36));selected=[]
        for i in range(5):
            state,word=oracle_step(model.name,state)
            k=word%len(pool) if sampler=='mod' else (word*len(pool))//(1<<model.bits)
            selected.append(pool.pop(k))
        for _ in range(gap):state,_=oracle_step(model.name,state)
        output.append(tuple(sorted(selected)))
    return output

class AffineRecoveryTests(unittest.TestCase):
    def test_exhaustive_affine_census(self):
        counts,_,_=census()
        self.assertEqual(dict(counts),{0:181456,1:120868,2:20853,3:1424,4:31})
        self.assertEqual(sum(counts.values()),324632)

    def test_independent_permutation_oracle(self):
        rng=random.Random(105491);tickets=[tuple(rng.sample(range(1,36),5)) for _ in range(1000)]
        for ticket in tickets:
            vals=set()
            for perm in itertools.permutations(ticket):
                remaining=list(range(1,36))
                for j,x in enumerate(perm):
                    idx=remaining.index(x)
                    if j==3:vals.add(idx)
                    remaining.pop(idx)
            self.assertEqual(vals,set(fourth_domain(ticket)))
            for mask,rhs in affine_constraints(fourth_domain(ticket)):
                self.assertTrue(all(((v&mask).bit_count()&1)==rhs for v in vals))

    def test_unrestricted_state_recovery_with_true_independent_holdouts(self):
        seeds=[0x8877665544332211ffeeddccbbaa9988,
               0x13579bdf2468ace0011223344556677889abcdef01234567fedcba9876543210]
        count=0
        for name,m in MODELS.items():
            for sampler in ('mod','high'):
                for gap in (0,2):
                    for seed in seeds:
                        seed%=1<<m.size
                        with self.subTest(model=name,sampler=sampler,gap=gap,seed=seed):
                            seq=oracle_tickets(m,seed,1100,gap,sampler)
                            r=recover(seq[:1000],m,gap,sampler)
                            self.assertEqual((r['status'],r['rank'],r['nullity']),('SAT',m.size,0),r)
                            self.assertEqual(int(r['recovered_seed'],16),seed)
                            self.assertEqual(oracle_tickets(m,int(r['recovered_seed'],16),1100,gap,sampler),seq)
                            count+=1
        self.assertEqual(count,24)

    def test_incomplete_rank_is_unknown(self):
        m=MODELS['xorshift128'];tickets=oracle_tickets(m,123456,6,0,'high')
        r=recover(tickets,m,0,'high')
        self.assertEqual(r['status'],'UNKNOWN');self.assertLess(r['rank'],128)

    def test_mutation_refuted_by_equation_contradiction(self):
        m=MODELS['xorshift128'];seq=oracle_tickets(m,0x12345678aabbccdd9922113344556677,1000,0,'high')
        corrupted=seq.copy();corrupted[0]=tuple(sorted(set(range(1,36))-set(seq[0])))[:5]
        r=recover(corrupted,m,0,'high')
        self.assertEqual(r['status'],'UNSAT')
        self.assertEqual(r['reason'],'inconsistent necessary GF(2) equations')

    def test_wrong_gap_and_sampler_are_only_conditional_refutations(self):
        m=MODELS['xorshift128'];seq=oracle_tickets(m,0x13245678aabbccdd9922113344556677,900,2,'mod')
        self.assertEqual(recover(seq,m,0,'mod')['status'],'UNSAT')
        self.assertEqual(recover(seq,m,2,'high')['status'],'UNSAT')

    def test_certificate_recomputed_against_equations(self):
        m=MODELS['xorshift128'];seq=oracle_tickets(m,0x13245678aabbccdd9922113344556677,500,2,'mod')
        r=audit(seq,m,0,'mod',500)
        self.assertEqual(r['status'],'UNSAT');self.assertTrue(r['certificate_xor_checked'])
        self.assertGreater(r['certificate_size'],1)

if __name__=='__main__':unittest.main(verbosity=2)
