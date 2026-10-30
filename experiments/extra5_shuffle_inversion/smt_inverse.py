#!/usr/bin/env python3
"""Exact bitvector inverse-state recovery via libz3 C ABI (no z3-solver wheel).

Supported model: xoroshiro128+ old-state 64-bit addition output;
64-bit multiply-high into C(35,5) uniform unordered ticket ranks.
This is a *specified hypothesis*, not an assertion about a lottery's RNG.
"""
import ctypes, csv, json, time, re, math, argparse
from pathlib import Path
N=math.comb(35,5)
MASK=(1<<64)-1

def rol(x,k):return ((x<<k)|(x>>(64-k)))&MASK

def xoro_step(state):
    x,y=state
    out=(x+y)&MASK
    y^=x
    return (((rol(x,55)^y^(y<<14))&MASK),rol(y,36)),out

def sequence(state,n,stride=1):
    out=[]
    for t in range(n):
        for _ in range(stride):state,z=xoro_step(state)
        out.append((z*N)>>64)
    return out

def preimage(r):
    assert 0<=r<N
    low=(r*(1<<64)+N-1)//N
    high=((r+1)*(1<<64)+N-1)//N-1
    return low,high

def common_prefix(r):
    low,high=preimage(r)
    width=64-(low^high).bit_length()
    return width,low>>(64-width)

def word(x):return f'(_ bv{x & MASK} 64)'

def rot(x,n):return f'((_ rotate_left {n}) {x})'

def step_smt(a,b):
    new_b=f'(bvxor {a} {b})'
    return (f'(bvxor (bvxor {rot(a,55)} {new_b}) (bvshl {new_b} {word(14)}))',rot(new_b,36))

def smt_program(ranks,stride=1,mode='prefix',timeout=15000,fix_state=None,full_model=False):
    assert mode in ('prefix','interval','mod3')
    s=['(set-logic QF_BV)',f'(set-option :timeout {int(timeout)})', '(set-option :produce-models true)',
       '(declare-const init0 (_ BitVec 64))','(declare-const init1 (_ BitVec 64))']
    if fix_state:
        s += [f'(assert (= init0 {word(fix_state[0])}))',f'(assert (= init1 {word(fix_state[1])}))']
    aa,bb='init0','init1'
    for t,rank in enumerate(ranks):
        for step in range(stride):
            out=f'(bvadd {aa} {bb})'
            a,b=step_smt(aa,bb)
            a_var,b_var=f's{t}_{step}_0',f's{t}_{step}_1'
            s.extend([f'(declare-const {a_var} (_ BitVec 64))',f'(declare-const {b_var} (_ BitVec 64))',
                      f'(assert (= {a_var} {a}))',f'(assert (= {b_var} {b}))'])
            aa,bb=a_var,b_var
        if mode=='mod3':
            s.append(f'(assert (= ((_ extract 2 0) {out}) (_ bv{rank%8} 3)))')
        elif mode=='interval':
            lo,hi=preimage(rank)
            s.append(f'(assert (and (bvuge {out} {word(lo)}) (bvule {out} {word(hi)})))')
        else:
            bits,prefix=common_prefix(rank)
            s.append(f'(assert (= ((_ extract 63 {64-bits}) {out}) (_ bv{prefix} {bits})))')
    s.append('(check-sat)')
    if full_model:s.append('(get-value (init0 init1))')
    return '\n'.join(s)+'\n'

class LibZ3:
    def __init__(self):
        self.lib=ctypes.CDLL('libz3.so.4')
        z=self.lib
        z.Z3_mk_config.restype=ctypes.c_void_p
        z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
        z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
        z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
        z.Z3_del_context.argtypes=[ctypes.c_void_p];z.Z3_del_config.argtypes=[ctypes.c_void_p]
    def run(self,program):
        z=self.lib
        config=z.Z3_mk_config();ctx=z.Z3_mk_context(config)
        try:return z.Z3_eval_smtlib2_string(ctx,program.encode()).decode()
        finally:z.Z3_del_context(ctx);z.Z3_del_config(config)

def state_from(result):
    vals={}
    for key,v in re.findall(r'\(init([01])\s+(#x[0-9a-fA-F]+|#b[01]+|\(_ bv\d+ 64\))\)',result):
        vals[int(key)]=int(v[2:],16) if v.startswith('#x') else int(v[2:],2) if v.startswith('#b') else int(re.search(r'bv(\d+)',v).group(1))
    if len(vals)==2:return vals[0],vals[1]
    return None

def solve(ranks,stride=1,mode='prefix',timeout=10000):
    z=LibZ3()
    t=time.monotonic();out=z.run(smt_program(ranks,stride,mode,timeout,full_model=False))
    status=out.strip().splitlines()[0] if out.strip() else 'empty'
    if status=='sat':out=z.run(smt_program(ranks,stride,mode,timeout,full_model=True))
    result={'status':status,'elapsed':round(time.monotonic()-t,3),'stride':stride,'mode':mode,'constraints':len(ranks),'result_excerpt':out[:1000]}
    st=state_from(out)
    if st:
        result['recovered_state']=[hex(x) for x in st]
        result['rank_matches']=sum(a==b for a,b in zip(sequence(st,len(ranks),stride),ranks))
        result['first_rank_failure']=next((i for i,(a,b) in enumerate(zip(sequence(st,len(ranks),stride),ranks)) if a!=b),None)
    return result

def read_ranks(path):
    return [int(x['lex_rank']) for x in csv.DictReader(open(path,newline=''))]

def main():
    p=argparse.ArgumentParser();p.add_argument('--real',default='');p.add_argument('--timeout',type=int,default=12000)
    p.add_argument('--prefixes',type=int,nargs='+',default=[6,9]);p.add_argument('--strides',type=int,nargs='+',default=[1]);p.add_argument('--mode',choices=['prefix','interval','mod3'],default='prefix');p.add_argument('--output',default='')
    a=p.parse_args();r=[]
    if a.real:
        data=read_ranks(a.real)
        for stride in a.strides:
            for n in a.prefixes:
                v=solve(data[:n],stride,a.mode,a.timeout)
                r.append(dict(source='extra5',**v));print(json.dumps(r[-1]),flush=True)
    if a.output:Path(a.output).write_text(json.dumps(r,indent=2)+'\n')

if __name__=='__main__':main()
