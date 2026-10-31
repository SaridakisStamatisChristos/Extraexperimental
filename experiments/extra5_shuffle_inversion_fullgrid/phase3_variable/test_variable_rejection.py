"""Independent oracle and falsification checks for Phase 3B path inference."""
import random
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent / "phase3_rank"))
from math import comb
from rank_inverse import MODELS, N, combination_unrank
from variable_rejection import (threshold, generate_trace, ordinal_forms,
                                ordinal_positions, recover_bounded)

M32=(1<<32)-1

def independent_marsaglia(seed,n,gap=0,multiple=None):
    state=[(seed>>(32*k))&M32 for k in range(4)]
    cap=(1<<32)//N if multiple is None else multiple
    limit=cap*N;out=[];skips=[]
    for d in range(n):
        count=0
        while True:
            x,y,z,w=state
            t=x^(x<<11)&M32
            q=(w^(w>>19)^t^(t>>8))&M32
            state=[y,z,w,q]
            if q<limit:break
            count+=1
        out.append(combination_unrank(q%N));skips.append(count)
        for _ in range(gap):
            x,y,z,w=state;t=x^(x<<11)&M32
            q=(w^(w>>19)^t^(t>>8))&M32
            state=[y,z,w,q]
    return out,skips


def forced_first_rejection():
    """Engineer a uniformly legal nonzero initial state whose FIRST output is invalid.
    xorshift128 word formula w' = w XOR (w>>19) XOR t XOR (t>>8).
    Invert XOR-right-19 bijection instead of searching arbitrary seeds.
    """
    x=0x12345678;y=0x9abcdef0;z=0xfedcba98
    t=(x^(x<<11))&M32
    b=(M32 ^t^(t>>8))&M32
    w=b^(b>>19)  # invert y = w XOR w>>19, since 2*19>32
    seed=x|(y<<32)|(z<<64)|(w<<96)
    assert ((w^(w>>19)^t^(t>>8))&M32)==M32
    return seed

def inverse_step32(new):
    """Independent inverse for Marsaglia 4x32-bit transition."""
    y,z,w,q=new
    v=(q^w^(w>>19))&M32
    t=(v^(v>>8)^(v>>16)^(v>>24))&M32
    x=(t^(t<<11)^(t<<22))&M32
    return (x,y,z,w)


def forced_later_rejection(draw_index=14):
    """Algebraically force word at draw_index to be rejected, without a seed scan."""
    if draw_index<1:raise ValueError('must be later than first draw')
    state=(0x13579bdf,0x2468ace0,0xabcd1234,M32)
    for _ in range(draw_index+1):
        state=inverse_step32(state)
    seed=sum(x<<(32*k) for k,x in enumerate(state))
    trace,skips,_=generate_trace(MODELS['marsaglia128'],seed,draw_index+1)
    assert all(x==0 for x in skips[:draw_index]) and skips[draw_index]==1,skips
    return seed

class VariablePathTest(unittest.TestCase):
    def test_threshold_math_and_rank(self):
        self.assertEqual(N,324632)
        self.assertEqual((1<<32)%N,85936)
        self.assertEqual((1<<64)%N,267360)
        m=MODELS['marsaglia128']
        self.assertEqual((1<<32)-threshold(m),85936)
        for bad in (0,-1,((1<<32)//N)+1):
            with self.assertRaises(ValueError):threshold(m,bad)

    def test_no_rejection_baseline(self):
        m=MODELS['xoroshiro128plus'];seed=0xabcdeeddfedcba987654321123456789
        train,skips,_=generate_trace(m,seed,175)
        self.assertEqual(sum(skips),0)
        r=recover_bounded(m,train,max_skips=0)
        self.assertEqual(r['status'],'SAT',r)
        self.assertEqual(int(r['seed'],16),seed)
        self.assertEqual(r['recovered_path'],[])

    def test_first_rejection_alias_nonidentifiability(self):
        m=MODELS['marsaglia128'];seed=forced_first_rejection()
        data,skips,_=generate_trace(m,seed,180)
        self.assertEqual(skips[0],1)
        expected,ref_skips=independent_marsaglia(seed,180)
        self.assertEqual(data,expected);self.assertEqual(skips,ref_skips)
        r=recover_bounded(m,data[:65],max_skips=1)
        self.assertEqual(r['status'],'SAT',r)
        # An alternative shifted state is indistinguishable from an initial skip.
        self.assertNotEqual(int(r['seed'],16),seed)
        self.assertEqual(r['recovered_path'],[])
        replay,_,_=generate_trace(m,int(r['seed'],16),180)
        self.assertEqual(replay,data)
        self.assertEqual(m.step(m.decode(seed))[0],m.decode(int(r['seed'],16)))
        # Explicitly pinning a one-rejection initial path restores true seed.
        r2=recover_bounded(m,data[:65],max_skips=1,minimum_skips=1)
        self.assertEqual(r2['status'],'SAT',r2)
        self.assertEqual(int(r2['seed'],16),seed)
        self.assertEqual(r2['recovered_path'],[0])

    def test_later_rejection_exact_initial_seed_and_holdout(self):
        m=MODELS['marsaglia128'];seed=forced_later_rejection(14)
        data,skips,_=generate_trace(m,seed,180)
        self.assertEqual(skips[:14],[0]*14)
        self.assertEqual(skips[14],1)
        self.assertEqual(independent_marsaglia(seed,180)[0],data)
        r=recover_bounded(m,data[:65],max_skips=1)
        self.assertEqual(r['status'],'SAT',r)
        self.assertEqual(int(r['seed'],16),seed)
        self.assertEqual(r['recovered_path'],[14])
        self.assertEqual(generate_trace(m,int(r['seed'],16),180)[0][65:],data[65:])

    def test_rejection_under_gap_2(self):
        m=MODELS['marsaglia128'];seed=forced_first_rejection()
        data,skips,_=generate_trace(m,seed,160,gap=2)
        self.assertEqual(skips[0],1)
        self.assertEqual(independent_marsaglia(seed,160,gap=2)[0],data)
        r=recover_bounded(m,data[:65],gap=2,max_skips=1,minimum_skips=1)
        self.assertEqual(r['status'],'SAT',r)
        self.assertEqual(int(r['seed'],16),seed)
        self.assertEqual(r['recovered_path'],[0])
        self.assertEqual(generate_trace(m,int(r['seed'],16),160,gap=2)[0][65:],data[65:])

    def test_wrong_path_exhaustive_rejects_planted_with_later_skip(self):
        m=MODELS['marsaglia128'];seed=forced_later_rejection(14)
        data,_,_=generate_trace(m,seed,65)
        r=recover_bounded(m,data,max_skips=0)
        self.assertEqual(r['status'],'UNSAT',r)
        self.assertTrue(r['search_complete'])

    def test_budget_unknown_not_unsat(self):
        m=MODELS['marsaglia128'];seed=forced_later_rejection(14)
        data,_,_=generate_trace(m,seed,65)
        r=recover_bounded(m,data,max_skips=1,max_paths=1)
        self.assertEqual(r['status'],'UNKNOWN',r)
        self.assertFalse(r['search_complete'])
        self.assertEqual(r['paths_tested'],1)

    def test_underdetermined_unknown(self):
        m=MODELS['xoshiro256plus'];seed=0x123456789abcdef0feedcafebeef0123456789abcdef
        data,_,_=generate_trace(m,seed,40)
        r=recover_bounded(m,data,max_skips=0)
        self.assertEqual(r['status'],'UNKNOWN',r)
        self.assertEqual(r['rank_deficient_paths'],1)

    def test_two_rejections_stress_bounded_exact_and_holdout(self):
        # Deliberately inefficient *still-uniform* rejection threshold to create
        # two observable skip events in only 68 draws; not the conventional limit.
        m=MODELS['marsaglia128'];seed=37;multiplier=13124
        data,counts,_=generate_trace(m,seed,168,accept_multiple=multiplier)
        self.assertEqual(counts[:68].count(1),2)
        self.assertEqual([i for i,c in enumerate(counts[:68]) if c],[46,50])
        self.assertEqual(data,independent_marsaglia(seed,168,multiple=multiplier)[0])
        for bound in (0,1):
            wrong=recover_bounded(m,data[:68],max_skips=bound,accept_multiple=multiplier)
            self.assertEqual(wrong['status'],'UNSAT',wrong)
            self.assertTrue(wrong['search_complete'])
        correct=recover_bounded(m,data[:68],max_skips=2,accept_multiple=multiplier)
        self.assertEqual(correct['status'],'SAT',correct)
        self.assertEqual(int(correct['seed'],16),seed)
        self.assertEqual(correct['recovered_path'],[46,50])
        self.assertEqual(generate_trace(m,int(correct['seed'],16),168,accept_multiple=multiplier)[0][68:],data[68:])

    def test_nonlinear_addition_forced_rejection(self):
        # Construct pre-transition 64-bit + output = 2**64-1.
        # This exercises the real nonlinear carry-producing output function.
        M64=(1<<64)-1
        for name in ('xoroshiro128plus','xoshiro256plus'):
            m=MODELS[name]
            first=0x123456789abcdef0
            last=(M64-first)&M64
            seed=first|(last<<64) if m.words==2 else first|(0x7777777777777777<<64)|(0xfedcba9876543210<<128)|(last<<192)
            n=170 if m.words==2 else 300
            tickets,skips,words=generate_trace(m,seed,n+100)
            self.assertEqual(skips[0],1)
            self.assertLess(words[0],threshold(m))
            # No first-word oracle. If at least one skip is assumed, recover the
            # planted original state from unordered sets and replay holdout.
            r=recover_bounded(m,tickets[:n],max_skips=1,minimum_skips=1)
            self.assertEqual(r['status'],'SAT',r)
            self.assertEqual(int(r['seed'],16),seed)
            self.assertEqual(r['recovered_path'],[0])
            self.assertEqual(generate_trace(m,int(r['seed'],16),n+100)[0][n:],tickets[n:])

    def test_ordinal_form_oracle(self):
        for m in MODELS.values():
            forms=ordinal_forms(m,41)
            seed=random.Random(761).getrandbits(m.size)
            s=m.decode(seed)
            for idx in range(41):
                s,w=m.step(s)
                for k in range(m.proved_linear_low_bits):
                    self.assertEqual(((forms[idx][k]&seed).bit_count()&1),(w>>k)&1)
        self.assertEqual(ordinal_positions(4,2,(0,2,2)),[1,4,9,12])

if __name__=='__main__':unittest.main(verbosity=2)
