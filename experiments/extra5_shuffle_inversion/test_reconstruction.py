#!/usr/bin/env python3
"""Independent regressions for the shuffle-invariant exact-state algorithm."""
import unittest,random,itertools,subprocess,json,hashlib,csv,math
from pathlib import Path
from inverse_unordered_sampler import fourth_indices,make_tickets,xorshift32_step,compute_masks
from inverse_linear import load,ticket_rank,unrank
from smt_inverse import preimage,common_prefix,sequence,xoro_step
BASE=Path(__file__).resolve().parent
EXE=BASE/'unordered_attack'

PLANTS=[
('xorshift32_13_17_5',0x89abcdef,5,1),('xorshift32_13_17_5',0x89abcdef,7,1),
('xorshift32_5_17_13',0x9a876543,5,1),('xorshift32_5_17_13',0x9a876543,7,1),
('xorshift32_7_9_13',0x6a5f1234,5,1),('xorshift32_7_9_13',0x6a5f1234,7,1),
('xorshift32_13_17_5',0x89abcdef,5,0x9E3779BB),
('xorshift32_5_17_13',0x9a876543,7,0x85EBCA6B),
('xorshift32_7_9_13',0x6a5f1234,6,0x2545F491)]

def independent_tickets(name,seed,steps,count,mult=1):
    state=seed;out=[]
    for _ in range(count):
        pool=list(range(1,36));numbers=[]
        for i in range(steps):
            state,v=xorshift32_step(state,name)
            if i<5:numbers.append(pool.pop(((v*mult)&0xffffffff)%len(pool)))
        out.append(tuple(sorted(numbers)))
    return out

def call(family,seed,stride,mult,input_path,limit=60):
    args=family.split('_')[1:]
    p=subprocess.run([str(EXE),str(input_path),*args,str(stride),'12',str(limit),str(mult)],
                     check=True,capture_output=True,text=True,timeout=12)
    return json.loads(p.stdout)

class ReconstructionTests(unittest.TestCase):
    def test_archive_integrity(self):
        dat=(BASE/'extra5_2022_2026_authoritative.csv').read_bytes()
        self.assertEqual(hashlib.sha256(dat).hexdigest(),'61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307')
        draws=load(BASE/'extra5_2022_2026_authoritative.csv')
        self.assertEqual(len(draws),3526)
        self.assertEqual((draws[0]['draw_id'],draws[-1]['draw_id']),('10832','14357'))

    def test_combinatorial_sampler_exactness(self):
        rng=random.Random(444)
        for _ in range(100):
            ticket=sorted(rng.sample(range(1,36),5))
            reference=set()
            for chosen_fourth in ticket:
                others=set(ticket)-{chosen_fourth}
                for previous_three in itertools.combinations(others,3):
                    idx=chosen_fourth-1-sum(v<chosen_fourth for v in previous_three)
                    reference.add(idx)
            self.assertEqual(fourth_indices(ticket),tuple(sorted(reference)))
            self.assertTrue(4<=len(reference)<=9)

    def test_bitmask_projection_matches_direct_generator(self):
        rng=random.Random(2808)
        for name in ['xorshift32_13_17_5','xorshift32_5_17_13','xorshift32_7_9_13']:
            for stride in [5,7,8]:
                masks=compute_masks(name,stride,8)
                for _ in range(6):
                    seed=rng.randrange(1,1<<32)
                    state=seed
                    for t in range(8):
                        for j in range(stride):
                            state,v=xorshift32_step(state,name)
                            if j==3:
                                prediction=sum(((masks[t][b]&seed).bit_count()&1)<<b for b in range(5))
                                self.assertEqual(v&31,prediction)

    def test_scrambler_five_bits_inversion(self):
        for mult in (1,3,5,7,9,0x9E3779BB,0x85EBCA6B,0x2545F491,0xFFFFFFFF):
            inv=next(k for k in range(1,32,2) if ((k*mult)&31)==1)
            for raw in range(32):
                observed=(raw*mult)&31
                self.assertEqual((observed*inv)&31,raw)

    def test_nine_synthetic_full_state_recoveries(self):
        for family,seed,stride,mul in PLANTS:
            with self.subTest(family=family,stride=stride,mul=mul):
                filename=(f'synthetic_star_{family}_stride{stride}_mul{mul}.csv' if mul!=1
                          else f'synthetic_{family}_stride{stride}.csv')
                target=BASE/filename
                actual=call(family,seed,stride,mul,target)
                self.assertTrue(actual['exhaustive'])
                self.assertEqual(actual['recovered_states'],[seed])
                self.assertEqual(actual['states_matching_all_tickets'],1)
                expected=independent_tickets(family,seed,stride,60,mul)
                recorded=[]
                with target.open(newline='') as h:
                    for row in csv.DictReader(h):
                        mask=int(row['ticket_mask'])
                        recorded.append(tuple(i+1 for i in range(35) if mask&(1<<i)))
                self.assertEqual(expected,recorded)

    def test_synthetic_continuation_independent_of_training(self):
        family,seed,stride,mul=PLANTS[0]
        src=BASE/f'synthetic_{family}_stride{stride}.csv'
        r=call(family,seed,stride,mul,src)
        self.assertEqual(r['recovered_states'],[seed])
        seq=independent_tickets(family,seed,stride,61)
        self.assertEqual(len(seq[12:]),49)
        self.assertNotEqual(seq[12],seq[11])

    def test_real_negative_controls(self):
        for fam,stride,mul in [('xorshift32_13_17_5',5,1),('xorshift32_5_17_13',7,1),
                               ('xorshift32_7_9_13',5,1),('xorshift32_13_17_5',5,0x9E3779BB)]:
            with self.subTest(fam=fam,stride=stride,mul=mul):
                r=call(fam,0,stride,mul,BASE/'real_unordered.csv',3526)
                self.assertTrue(r['exhaustive'])
                self.assertEqual(r['states_matching_all_tickets'],0)

    def test_systematic_grid_evidence(self):
        records=[]
        for i in range(1,13,2):
            p=BASE/f'grid_results_{i}_{i+1}.json'
            dat=json.loads(p.read_text())
            self.assertEqual(dat['summary']['total'],1152)
            records+=dat['results']
        self.assertEqual(len(records),6912)
        self.assertEqual(len({(r['family'],r['stride']) for r in records}),6912)
        self.assertTrue(all(r.get('exhaustive') and not r['states_matching_all_tickets'] for r in records))

    def test_star_evidence(self):
        x=json.loads((BASE/'star_sweep_results.json').read_text())
        self.assertEqual(x['summary']['trials'],900)
        self.assertEqual(x['summary']['exhaustive'],900)
        self.assertTrue(all(r.get('exhaustive') and r['states_matching_all_tickets']==0 for r in x['results']))

    def test_smt_interval_preimage_exact(self):
        N=math.comb(35,5)
        for r in [0,1,103,238681,324631]:
            low,high=preimage(r)
            self.assertEqual((low*N)>>64,r)
            self.assertEqual((high*N)>>64,r)
            if low>0:self.assertLess(((low-1)*N)>>64,r)
            if high<(1<<64)-1:self.assertGreater(((high+1)*N)>>64,r)
            k,p=common_prefix(r)
            self.assertEqual(low>>(64-k),p)
            self.assertEqual(high>>(64-k),p)

if __name__=='__main__':unittest.main(verbosity=2)
