"""Positive/negative controls and independent algebra checks for Phase 2.

No real lottery label is used to infer a generator or state.
"""
import itertools
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from inverse_linear import MODELS, ticket, fourth_domain, forms, recover_known_fourth, replay, solve_equations

SEEDS=(0x0123456789abcdef112233445566778899aabbccddeeff0013579bdf2468ace1,
       0xabcdef9876543210ffeeddccbbaa99887766554433221100deadbeefcafef00d)


def independent_transition(name,state):
    w32=(1<<32)-1;w64=(1<<64)-1
    def rol(x,k):return ((x<<k)|(x>>(64-k)))&w64
    if name=='xorshift128':
        a,b,c,d=state
        z=(a^(a<<11))&w32
        next_d=(d^(d>>19)^z^(z>>8))&w32
        return (b,c,d,next_d),next_d
    if name=='xoroshiro128_raw':
        a,b=state;v=b^a
        first=(rol(a,24)^v^(v<<16))&w64
        second=rol(v,37)
        return (first,second),first
    if name=='xoshiro256_raw':
        a,b,c,d=state
        x=(b<<17)&w64
        c^=a;d^=b;b^=c;a^=d;c^=x;d=rol(d,45)
        return (a,b,c,d),a
    raise ValueError(name)


def independent_ticket(model,words,gap,sampler):
    available=list(range(1,36));numbers=[];indices=[]
    for z in range(5):
        words,out=independent_transition(model.name,words)
        i=out%len(available) if sampler=='mod' else (out*len(available))//(1<<model.bits)
        indices.append(i);numbers.append(available.pop(i))
    for _ in range(gap):words,_=independent_transition(model.name,words)
    return words,tuple(sorted(numbers)),tuple(indices)


class ExactLinearInverseTests(unittest.TestCase):
    def test_recovery_with_known_extraction_index_and_holdout(self):
        # 3 model cores x 2 sampler choices x 2 gaps x 2 seeds = 24 controls.
        for model in MODELS.values():
            for sampler in ('mod','high'):
                for gap in (0,2):
                    for seed in SEEDS:
                        seed%=1<<model.size
                        if seed==0:seed=1
                        with self.subTest(model=model.name,sampler=sampler,gap=gap,seed=seed):
                            words=model.from_integer(seed)
                            train=[];oracle=[];holdout=[]
                            for i in range(210):
                                words,nums,indices=independent_ticket(model,words,gap,sampler)
                                if i<160:
                                    train.append(nums);oracle.append((i,indices[3]))
                                else:holdout.append(nums)
                            result=recover_known_fourth(model,oracle,gap,sampler)
                            self.assertEqual((result.status,result.rank,len(result.nullspace)),('SAT',model.size,0))
                            self.assertEqual(result.seed,seed)
                            # Strict held-back comparison, independent implementation.
                            words=model.from_integer(result.seed)
                            for expected in train+holdout:
                                words,actual,_=independent_ticket(model,words,gap,sampler)
                                self.assertEqual(actual,expected)
                            self.assertTrue(replay(model,result.seed,train+holdout,gap,sampler))

    def test_rank_deficient_affine_state_space(self):
        for model in MODELS.values():
            seed=SEEDS[0]%(1<<model.size)
            words=model.from_integer(seed);obs=[]
            for i in range(8):
                words,ticket_set,indices=independent_ticket(model,words,0,'mod')
                obs.append((i,indices[3]))
            result=recover_known_fourth(model,obs)
            self.assertEqual(result.status,'SAT')
            self.assertLess(result.rank,model.size)
            delta=result.seed^seed
            # Difference between original and particular solution is a null vector.
            basis={};
            for b in result.nullspace:
                q=b
                while q:
                    high=q.bit_length()-1
                    if high not in basis:basis[high]=q;break
                    q^=basis[high]
            while delta:
                p=delta.bit_length()-1
                self.assertIn(p,basis)
                delta^=basis[p]
            self.assertEqual(delta,0)

    def test_fourth_domain_enumeration_exact(self):
        rng=random.Random(102931)
        for _ in range(18):
            nums=tuple(rng.sample(range(1,36),5))
            brute=set()
            for perm in itertools.permutations(nums):
                remain=list(range(1,36))
                for i,n in enumerate(perm):
                    p=remain.index(n)
                    if i==3:brute.add(p)
                    remain.pop(p)
            self.assertEqual(fourth_domain(nums),brute)

    def test_forms_match_independent_recurrence(self):
        for model in MODELS.values():
            for sampler in ('mod','high'):
                for gap in (0,2):
                    seed=SEEDS[1] % (1<<model.size)
                    ff=forms(model,25,gap,sampler)
                    words=model.from_integer(seed)
                    for j in range(25):
                        words,_,indices=independent_ticket(model,words,gap,sampler)
                        calculated=sum(((seed&ff[j][k]).bit_count()&1)<<k for k in range(5))
                        self.assertEqual(calculated,indices[3])

    def test_conflicting_equations_prove_unsat(self):
        for width in (128,256):
            eq=[(1<<k,(k%2)) for k in range(width)]
            yes=solve_equations(eq,width)
            self.assertEqual((yes.status,yes.rank),('SAT',width))
            no=solve_equations(eq+[(1<<42,0 if 42%2 else 1)],width)
            self.assertEqual(no.status,'UNSAT')
            self.assertEqual(no.conflicting_row,width)

    def test_implicit_order_never_assumed(self):
        model=MODELS['xorshift128']
        seed=SEEDS[0]%(1<<model.size)
        words=model.from_integer(seed)
        for _ in range(20):
            words,nums,actual=ticket(model,words)
            self.assertIn(actual[3],fourth_domain(nums))

    def test_wrong_generator_state_equations_rejected(self):
        generated=MODELS['xorshift128'];other=MODELS['xoroshiro128_raw']
        words=generated.from_integer(SEEDS[0]%(1<<generated.size));oracle=[]
        for i in range(110):
            words,_,idx=independent_ticket(generated,words,0,'mod')
            oracle.append((i,idx[3]))
        r=recover_known_fourth(other,oracle)
        self.assertEqual(r.status,'UNSAT')

if __name__=='__main__':unittest.main(verbosity=2)
