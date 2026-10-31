#!/usr/bin/env python3
"""Independent Python oracle for the exact C++ xorshift64 unordered inverse engine."""
import csv
import itertools
import json
import random
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
MASK=(1<<64)-1

def step64(x):
    x=(x^((x<<13)&MASK))&MASK
    x=(x^(x>>7))&MASK
    return (x^((x<<17)&MASK))&MASK

def draw64(x,gap):
    remain=list(range(1,36));out=[]
    for _ in range(5):
        x=step64(x)
        out.append(remain.pop(x%len(remain)))
    for _ in range(gap):x=step64(x)
    return x,tuple(sorted(out))

def write_csv(path,sets):
    with open(path,'w',newline='') as f:
        w=csv.writer(f);w.writerow(['ticket_mask'])
        for nums in sets:w.writerow([sum(1<<(n-1) for n in nums)])

def inferred_domain(nums):
    nums=sorted(nums);out=set()
    for i,v in enumerate(nums):
        for removed_below in range(max(0,i-1),min(3,i)+1):
            out.add(v-1-removed_below)
    return out

class Inverse64BranchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.binary=Path(cls.temp.name)/'inverse64_branch'
        subprocess.run(['g++','-O3','-std=c++20','-Wall','-Wextra','-Werror',
                        str(HERE/'inverse64_branch.cpp'),'-o',str(cls.binary)],check=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def solve(self,sets,train,gap,bound=20000000):
        path=Path(self.temp.name)/'data.csv'
        write_csv(path,sets)
        p=subprocess.run([str(self.binary),str(path),str(train),str(gap),
                          str(bound),'60'],check=True,capture_output=True,text=True)
        return json.loads(p.stdout)
    def test_permutation_invariance(self):
        rng=random.Random(505)
        for _ in range(100):
            nums=tuple(sorted(rng.sample(range(1,36),5)))
            brute=set()
            for perm in itertools.permutations(nums):
                pool=list(range(1,36))
                for i,v in enumerate(perm):
                    index=pool.index(v)
                    if i==3:brute.add(index)
                    pool.pop(index)
            self.assertEqual(inferred_domain(nums),brute)
    def test_multiple_64bit_unordered_positives_and_holdout(self):
        for seed,gap in [(0x89abcdef12345678,0),(0x123456789abcdef1,2),
                         (0xfedcba9876543210,0),(0xdeadbeef1337cafe,1),
                         (0x1111111111111111,0)]:
            with self.subTest(seed=hex(seed),gap=gap):
                x=seed;sets=[]
                for _ in range(3626):
                    x,t=draw64(x,gap);sets.append(t)
                # Only training data enter inverse code. Reserved 100 are independent.
                r=self.solve(sets[:3526],3526,gap)
                self.assertEqual(r['status'],'SAT',r)
                self.assertEqual(r['rank'],64)
                self.assertEqual(r['witness_state'],seed)
                self.assertEqual(r['full_ticket_prefix'],3526)
                x=r['witness_state']
                for i,t in enumerate(sets):
                    x,pred=draw64(x,gap)
                    self.assertEqual(pred,t,msg=f'failed continuation at {i}')
    def test_random_negative_complete(self):
        rng=random.Random(20261031)
        r=self.solve([rng.sample(range(1,36),5) for _ in range(3526)],3526,0)
        self.assertEqual(r['status'],'UNSAT',r)
        self.assertEqual(int(r['selection_domain_product']),r['assignments_examined'])
    def test_bounded_unknown_is_not_unsat(self):
        x=0x89abcdef12345678;sets=[]
        for _ in range(100):x,t=draw64(x,0);sets.append(t)
        r=self.solve(sets,100,0,10000)
        self.assertEqual(r['status'],'UNKNOWN',r)
    def test_sparse_real_like_negative(self):
        rng=random.Random(137)
        sets=[rng.sample(range(1,36),5) for _ in range(3526)]
        ids=sorted(range(2,3526),key=lambda i:(len(inferred_domain(sets[i])),i))[:130]
        selected=set(ids)|{0,1}
        sparse=[sets[i] if i in selected else [] for i in range(3526)]
        r=self.solve(sparse,3526,0)
        self.assertEqual(r['status'],'UNSAT',r)
        self.assertEqual(r['observed_training_rows'],132)

if __name__=='__main__':unittest.main(verbosity=2)

# Independently coded parameterized generator oracle; this exercises both
# xorshift directions, non-default shifts, and 64-bit multiply-high sampling.
class ParameterizedXorshift64Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.binary=Path(cls.temp.name)/'inverse64_branch'
        subprocess.run(['g++','-O3','-std=c++20','-Wall','-Wextra','-Werror',
                        str(HERE/'inverse64_branch.cpp'),'-o',str(cls.binary)],check=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_unordered_recovery_configurations(self):
        specs=[(13,7,17,0,1,0),(7,9,13,0,0,2),
               (7,9,13,0,1,1),(13,7,17,1,0,0),(13,7,17,1,1,2)]
        for a,b,c,direction,high,gap in specs:
            with self.subTest(model=(a,b,c,direction,high,gap)):
                def step(x):
                    if not direction:
                        x^=(x<<a)&MASK;x^=x>>b;x^=(x<<c)&MASK
                    else:
                        x^=x>>a;x^=(x<<b)&MASK;x^=x>>c
                    return x&MASK
                def draw(x):
                    pool=list(range(1,36));numbers=[]
                    for _ in range(5):
                        x=step(x)
                        index=(x*len(pool))>>64 if high else x%len(pool)
                        numbers.append(pool.pop(index))
                    for _ in range(gap):x=step(x)
                    return x,tuple(sorted(numbers))
                seed=0xabcdef9876543210
                x=seed;sets=[]
                for _ in range(3626):
                    x,t=draw(x);sets.append(t)
                path=Path(self.temp.name)/'custom.csv'
                write_csv(path,sets[:3526])
                cmd=[str(self.binary),str(path),'3526',str(gap),'200000000',
                     '60','3526',str(a),str(b),str(c),str(direction),str(high)]
                r=json.loads(subprocess.run(cmd,check=True,capture_output=True,text=True).stdout)
                self.assertEqual(r['status'],'SAT',r)
                self.assertEqual(r['witness_state'],seed,r)
                x=r['witness_state']
                for i,expected in enumerate(sets):
                    x,actual=draw(x)
                    self.assertEqual(actual,expected,f'failed independent replay at {i}')
