#!/usr/bin/env python3
"""Z3 SMT-based shuffle-invariant state inversion from 5-of-35 outputs.

Formulates the fourth draw's (32-choice) exact index as 5 GF(2) parity
functions of an unknown 64-bit initial state, with allowed index sets inferred
without using published number order. Calls libz3 via ctypes; no pip package.

Time limits are explicit; UNKNOWN is never reported as refuted.
"""
import argparse
import csv
import ctypes as C
import json
import re
import time
from pathlib import Path

MASK64=(1<<64)-1

def step64(s,a=13,b=7,c=17):
    s^=(s<<a)&MASK64
    s^=s>>b
    s^=(s<<c)&MASK64
    return s&MASK64

def draw_mask_and_fourth(s,gap=0):
    remaining=list(range(1,36)); selected=[]; fourth=None
    for z in range(5):
        s=step64(s)
        k=s%len(remaining)
        if z==3:fourth=k
        selected.append(remaining.pop(k))
    for _ in range(gap):s=step64(s)
    return s,sum(1<<(v-1) for v in selected),fourth

def rows_for_draws(n,gap=0):
    forms=[[0]*5 for _ in range(n)]
    for bit in range(64):
        x=1<<bit
        for d in range(n):
            for k in range(5):
                x=step64(x)
                if k==3:fourth=x
            for _ in range(gap):x=step64(x)
            for k in range(5):
                if (fourth>>k)&1:forms[d][k]|=1<<bit
    return forms

class LibZ3:
    def __init__(self):
        z=self.z=C.CDLL('libz3.so.4')
        def bind(name,returns,arguments):
            f=getattr(z,name);f.restype=returns;f.argtypes=arguments;return f
        ptr=C.c_void_p;cs=C.c_char_p;ui=C.c_uint
        self.mk_config=bind('Z3_mk_config',ptr,[])
        self.del_config=bind('Z3_del_config',None,[ptr])
        self.mk_context=bind('Z3_mk_context',ptr,[ptr])
        self.del_context=bind('Z3_del_context',None,[ptr])
        self.mk_solver=bind('Z3_mk_solver',ptr,[ptr])
        self.solver_inc_ref=bind('Z3_solver_inc_ref',None,[ptr,ptr])
        self.solver_dec_ref=bind('Z3_solver_dec_ref',None,[ptr,ptr])
        self.solver_from_string=bind('Z3_solver_from_string',None,[ptr,ptr,cs])
        self.solver_check=bind('Z3_solver_check',C.c_int,[ptr,ptr])
        self.solver_get_model=bind('Z3_solver_get_model',ptr,[ptr,ptr])
        self.model_to_string=bind('Z3_model_to_string',cs,[ptr,ptr])
        self.solver_get_reason_unknown=bind('Z3_solver_get_reason_unknown',cs,[ptr,ptr])
        self.mk_params=bind('Z3_mk_params',ptr,[ptr])
        self.params_inc_ref=bind('Z3_params_inc_ref',None,[ptr,ptr])
        self.params_dec_ref=bind('Z3_params_dec_ref',None,[ptr,ptr])
        self.mk_string_symbol=bind('Z3_mk_string_symbol',ptr,[ptr,cs])
        self.params_set_uint=bind('Z3_params_set_uint',None,[ptr,ptr,ptr,ui])
        self.solver_set_params=bind('Z3_solver_set_params',None,[ptr,ptr,ptr])

    def run(self,text,timeout_ms):
        cfg=self.mk_config();ctx=self.mk_context(cfg);self.del_config(cfg)
        sol=self.mk_solver(ctx);self.solver_inc_ref(ctx,sol)
        try:
            params=self.mk_params(ctx);self.params_inc_ref(ctx,params)
            symbol=self.mk_string_symbol(ctx,b'timeout')
            self.params_set_uint(ctx,params,symbol,timeout_ms)
            self.solver_set_params(ctx,sol,params)
            self.params_dec_ref(ctx,params)
            self.solver_from_string(ctx,sol,text.encode())
            start=time.monotonic()
            status=self.solver_check(ctx,sol)
            elapsed=time.monotonic()-start
            if status==1:
                model=self.model_to_string(ctx,self.solver_get_model(ctx,sol)).decode()
                match=re.search(r'\(define-fun s \(\) \(_ BitVec 64\)\s+(#x[0-9a-fA-F]+|#b[01]+|\(_ bv\d+ 64\))',model)
                if not match:
                    match=re.search(r's\s*->\s*(#x[0-9a-fA-F]+|#b[01]+|\(_ bv\d+ 64\))',model)
                if not match: raise RuntimeError('could not parse state model: '+model)
                word=match.group(1)
                if word.startswith('#x'):seed=int(word[2:],16)
                elif word.startswith('#b'):seed=int(word[2:],2)
                else:seed=int(re.search(r'bv(\d+)',word).group(1))
                return dict(status='SAT',state=seed,elapsed_seconds=elapsed,model=model)
            if status==-1:return dict(status='UNSAT',elapsed_seconds=elapsed)
            return dict(status='UNKNOWN',reason=self.solver_get_reason_unknown(ctx,sol).decode(),elapsed_seconds=elapsed)
        finally:
            self.solver_dec_ref(ctx,sol)
            self.del_context(ctx)


def build_smt(forms,masks,used=None):
    if used is None:used=list(range(len(masks)))
    lines=['(set-logic QF_BV)','(declare-fun s () (_ BitVec 64))']
    for d in used:
        f=forms[d]
        parts=[]
        for k in range(4,-1,-1):
            bits=[i for i in range(64) if (f[k]>>i)&1]
            tests=[f'(= ((_ extract {i} {i}) s) #b1)' for i in bits]
            parity='false' if not tests else tests[0] if len(tests)==1 else '(xor '+' '.join(tests)+')'
            parts.append(f'(ite {parity} #b1 #b0)')
        expr=parts[0]
        for part in parts[1:]:expr=f'(concat {expr} {part})'
        lines.append(f'(define-fun d{d} () (_ BitVec 5) {expr})')
        allowed=[v for v in range(32) if (masks[d]>>v)&1]
        lines.append('(assert (or '+ ' '.join(f'(= d{d} (_ bv{v} 5))' for v in allowed)+'))')
    return '\n'.join(lines)+'\n'

def read_masks(path):
    with open(path,newline='') as f:return [int(r['allowed_fourth_mask']) for r in csv.DictReader(f)]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--draws',type=int,default=35)
    ap.add_argument('--gap',type=int,default=0)
    ap.add_argument('--timeout-ms',type=int,default=15000)
    ap.add_argument('--choose',choices=['first','smallest'],default='first')
    args=ap.parse_args()
    masks=read_masks(args.input)
    n=min(len(masks),max(args.draws,80))
    forms=rows_for_draws(n,args.gap)
    ids=list(range(args.draws)) if args.choose=='first' else sorted(range(n),key=lambda d:(masks[d].bit_count(),d))[:args.draws]
    z3=LibZ3()
    smt=build_smt(forms,masks,ids)
    (Path(args.output).with_suffix('.smt2')).write_text(smt)
    result=z3.run(smt,args.timeout_ms)
    result.update(dict(draws=args.draws,gap=args.gap,selection=args.choose,indices=ids,input=args.input))
    if result['status']=='SAT':
        seed=result['state'];results=[]
        all_rows=list(csv.DictReader(open(args.input,newline='')))
        for d in range(min(len(all_rows),100)):
            seed,ticket,_=draw_mask_and_fourth(seed,args.gap)
            if ticket!=int(all_rows[d]['ticket_mask']):break
            results.append(d)
        result['exact_set_prefix']=len(results)
        result.pop('model')
    Path(args.output).write_text(json.dumps(result,indent=2))
    print({k:v for k,v in result.items() if k not in ('indices','model')})

if __name__=='__main__':main()