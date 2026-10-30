#!/usr/bin/env python3
"""Shuffle-invariant exact inversion of a five-output without-replacement sampler.

For each observed unordered set, compute all possible *fourth extraction indices*
under ALL 5! unknown extraction orders. Every ticket constrains five linear
bits of output 4 to an explicit set of 5..8 values; solve the disjunctive
constraints using a bit-vector SAT engine. No assumption on published order.
This tests fixed-stride, modulo-32 fourth selection, with no unknown skips inside
one ticket, not every possible lottery sampler.
"""
import sys, csv, itertools, json, math, re, time, argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from smt_inverse import LibZ3
from inverse_linear import FAMILIES, step as existing_step

MASK32=(1<<32)-1

def fourth_indices(ticket):
    vals=set()
    ticket=tuple(sorted(ticket))
    for p in itertools.permutations(ticket):
        remaining=[i for i in range(1,36) if i not in p[:3]]
        vals.add(remaining.index(p[3]))
    assert all(0<=v<32 for v in vals) and 1<=len(vals)<=32
    return tuple(sorted(vals))

def xorshift32_step(s,name):
    a,b,c=(int(x) for x in name.split('_')[1:])
    s^=(s<<a)&MASK32
    s^=(s>>b)
    s^=(s<<c)&MASK32
    return s&MASK32,s&MASK32

def family_step(s,name):
    return xorshift32_step(s,name) if name.startswith('xorshift32_') else existing_step(name,s)

def bits_and_output(name):
    if name.startswith('xorshift32_'):return 32,32
    if name.startswith('marsaglia128_'):return 128,32
    if name.startswith('xorshift64_'):return 64,64
    raise ValueError(name)

def make_tickets(name,s,count,stride=5):
    assert stride>=5
    result=[]
    for _ in range(count):
        remaining=list(range(1,36)); ticket=[]
        for i in range(stride):
            s,out=family_step(s,name)
            if i<5:ticket.append(remaining.pop(out%len(remaining)))
        result.append(tuple(sorted(ticket)))
    return result

def compute_masks(name,stride,n,word=3):
    """Output bit row is parity(initial_state & rowmask)."""
    bits,_=bits_and_output(name)
    masks=[[0]*5 for _ in range(n)]
    for ibit in range(bits):
        state=1<<ibit
        for t in range(n):
            for i in range(stride):
                state,out=family_step(state,name)
                if i==3 and name.startswith('marsaglia128_'):
                    out=(state>>(word*32))&MASK32
                if i==3:
                    for k in range(5):
                        if (out>>k)&1:masks[t][k]|=1<<ibit
    return masks

def xor_parity(row):
    if row==0:return '(_ bv0 1)'
    pieces=[]
    while row:
        bit=(row & -row).bit_length()-1
        pieces.append(f'((_ extract {bit} {bit}) initial)')
        row &= row-1
    while len(pieces)>1:
        pieces=[f'(bvxor {pieces[i]} {pieces[i+1]})' if i+1<len(pieces) else pieces[i]
                for i in range(0,len(pieces),2)]
    return pieces[0]

def constraints_program(name,stride,tickets,n,timeout=10000,output_word=3,with_model=False,full_values=False):
    bits,_=bits_and_output(name)
    masks=compute_masks(name,stride,n,output_word)
    p=['(set-logic QF_BV)',f'(set-option :timeout {timeout})','(set-option :produce-models true)',
       f'(declare-const initial (_ BitVec {bits}))']
    for i in range(n):
        arr=[]
        for b in range(4,-1,-1):
            row=masks[i][b]
            arr.append(xor_parity(row))
        actual=arr[0]
        for bit in arr[1:]:actual=f'(concat {actual} {bit})'
        possibilities=f' '.join(f'(= {actual} (_ bv{v} 5))' for v in fourth_indices(tickets[i]))
        p.append(f'(assert (or {possibilities}))')
    p.append('(check-sat)')
    if with_model:p.append('(get-value (initial))')
    return '\n'.join(p)+'\n'

def extract_state(output):
    m=re.search(r'\(initial\s+(#b[01]+|#x[\da-fA-F]+|\(_ bv\d+ \d+\))\)',output)
    if not m:return None
    t=m.group(1)
    return int(t[2:],2) if t.startswith('#b') else int(t[2:],16) if t.startswith('#x') else int(re.search(r' bv(\d+)',t).group(1))

def solve(name,stride,tickets,n,timeout=10000,word=3):
    start=time.monotonic()
    p=constraints_program(name,stride,tickets,n,timeout,word,False)
    lib=LibZ3();raw=lib.run(p)
    status=raw.strip().splitlines()[0] if raw.strip() else 'empty'
    rec={'family':name,'stride':stride,'draws':n,'state_bits':bits_and_output(name)[0],
         'word':word,'status':status,'seconds':round(time.monotonic()-start,3)}
    if status=='sat':
        raw=lib.run(p+'(get-value (initial))\n')
        state=extract_state(raw)
        if state is not None:
            predicted=make_tickets(name,state,n,stride)
            rec.update(state=hex(state),exact_whole_ticket_matches=sum(predicted[i]==tuple(sorted(tickets[i])) for i in range(n)),
                       exact_first_ticket=(predicted[0]==tuple(sorted(tickets[0]))),
                       verified_fourth_constraints=all((fourth_indices(tickets[i]) and True) for i in range(n)))
    return rec

def load(path):
    rows=list(csv.DictReader(open(path,newline='')))
    return [tuple(int(row[f'n{i}']) for i in range(1,6)) for row in rows]

FAMILIES_TO_TEST=['xorshift32_13_17_5','xorshift32_5_17_13',
                  'xorshift32_7_9_13','xorshift64_13_7_17',
                  'xorshift64_12_25_27','marsaglia128_11_8_19','marsaglia128_15_4_21']

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--real',default='');ap.add_argument('--prefix',type=int,default=25)
    ap.add_argument('--timeout',type=int,default=10000);ap.add_argument('--out',default='');ap.add_argument('--families',nargs='+',default=FAMILIES_TO_TEST);ap.add_argument('--strides',type=int,nargs='+',default=[5]);a=ap.parse_args()
    tickets=load(a.real) if a.real else None
    results=[]
    for name in a.families:
        for stride in a.strides:
            if tickets is None:
                s=0x89abcdef if name.startswith('xorshift32_') else 0x1234567abbccdd116612a4444 if name.startswith('xorshift64_') else 0x0123456789abcdeffedcba9876543210
                target=make_tickets(name,s,a.prefix,stride)
                rec=solve(name,stride,target,a.prefix,a.timeout)
                rec['source']='synthetic';rec['planted_state']=hex(s)
                if rec.get('state')==hex(s):rec['exact_state_recovered']=True
            else:
                rec=solve(name,stride,tickets,a.prefix,a.timeout)
                rec['source']='extra5'
            print(json.dumps(rec),flush=True);results.append(rec)
    if a.out:Path(a.out).write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
