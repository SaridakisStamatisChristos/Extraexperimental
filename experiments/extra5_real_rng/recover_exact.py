#!/usr/bin/env python3
"""Exact bit-vector state feasibility for concrete continuous PRNGs.

NOT the operator's implementation. Tested sampler: 32bit *big-endian* PRNG
output stream, consecutive accepted 24bit chunks, uniform 5/35 rank via
rejection (< 16,556,232), lexicographic combinadic unranking.

Constraint for first K draws assumes no rejected 24-bit chunks in those draws.
Z3 library is used by ctypes; missing libz3 raises an explicit error.
No unseen holdout is read by the fit. A SAT fit is forward-checked.
"""
from __future__ import annotations
import argparse, csv, ctypes, json, math, re, time
from pathlib import Path
N=math.comb(35,5)
LIMIT=(1<<24)//N*N
MASK32=(1<<32)-1

def reads(path):
    rows=list(csv.DictReader(open(path,newline='')))
    ids=[int(r['draw_id']) for r in rows]
    assert len(rows)>=10 and ids==list(range(ids[0],ids[0]+len(rows)))
    return rows

def b32(n):return f'(_ bv{n} 32)'
def xor(*args):return f'(bvxor {" ".join(args)})' if len(args)==2 else xor(args[0],xor(*args[1:]))
def shl(a,k):return f'(bvshl {a} {b32(k)})'
def shr(a,k):return f'(bvlshr {a} {b32(k)})'

def words_prng(kind,n):
    if kind in ('nr_lcg32','ansi_lcg32','msvc_lcg32'):
        mul,inc={'nr_lcg32':(1664525,1013904223),'ansi_lcg32':(1103515245,12345),'msvc_lcg32':(214013,2531011)}[kind]
        declarations=['(declare-fun s0 () (_ BitVec 32))'];outputs=[];curr='s0'
        for i in range(n):
            name=f'w{i}';declarations.append(f'(define-fun {name} () (_ BitVec 32) (bvadd (bvmul {curr} {b32(mul)}) {b32(inc)}))');outputs.append(name);curr=name
        return declarations,outputs,['s0']
    if kind=='xorshift32':
        declarations=['(declare-fun s0 () (_ BitVec 32))'];outputs=[];curr='s0'
        for i in range(n):
            a=xor(curr,shl(curr,13)); b=xor(a,shr(a,17));c=xor(b,shl(b,5))
            name=f'w{i}';declarations.append(f'(define-fun {name} () (_ BitVec 32) {c})');outputs.append(name);curr=name
        return declarations,outputs,['s0']
    if kind=='xorshift96':
        decl=[f'(declare-fun s{i} () (_ BitVec 32))' for i in range(3)]
        state=['s0','s1','s2'];output=[]
        for i in range(n):
            x,y,z=state;t=xor(x,shl(x,16));t=xor(t,shr(t,5));t=xor(t,shl(t,1))
            name=f'w{i}';decl.append(f'(define-fun {name} () (_ BitVec 32) {xor(t,y,z)})');output.append(name);state=[y,z,name]
        return decl,output,['s0','s1','s2']
    if kind=='xorshift128':
        decl=[f'(declare-fun s{i} () (_ BitVec 32))' for i in range(4)]
        state=['s0','s1','s2','s3'];output=[]
        for i in range(n):
            x,y,z,w=state;t=xor(x,shl(x,11));out=xor(w,shr(w,19),t,shr(t,8))
            name=f'w{i}';decl.append(f'(define-fun {name} () (_ BitVec 32) {out})');output.append(name);state=[y,z,w,name]
        return decl,output,['s0','s1','s2','s3']
    raise ValueError(kind)

def raw24_expr(output,i):
    byte=3*i;w=byte//4;off=byte%4
    if off==0:return f'((_ extract 31 8) {output[w]})'
    if off==1:return f'((_ extract 23 0) {output[w]})'
    if off==2:return f'(concat ((_ extract 15 0) {output[w]}) ((_ extract 31 24) {output[w+1]}))'
    return f'(concat ((_ extract 7 0) {output[w]}) ((_ extract 31 16) {output[w+1]}))'

def parse_z3_string(s):
    if s.startswith('sat'):
        return 'sat', {k:int(v[2:],16) if v.startswith('#x') else int(v[2:],2) if v.startswith('#b') else int(v) for k,v in re.findall(r'\((s\d+)\s+(#x[0-9a-fA-F]+|#b[01]+|\d+)\)',s)}
    if s.startswith('unsat'):return 'unsat',None
    if s.startswith('unknown'):return 'unknown',None
    raise RuntimeError('unexpected Z3 text: '+s[:250])

class Z3Lib:
    def __init__(self):
        self.lib=ctypes.CDLL('libz3.so.4')
        for name,args,restype in [('Z3_mk_config',[],ctypes.c_void_p),('Z3_mk_context',[ctypes.c_void_p],ctypes.c_void_p),('Z3_eval_smtlib2_string',[ctypes.c_void_p,ctypes.c_char_p],ctypes.c_char_p),('Z3_del_context',[ctypes.c_void_p],None),('Z3_del_config',[ctypes.c_void_p],None)]:
            fn=getattr(self.lib,name);fn.argtypes=args;fn.restype=restype
    def query(self,s,values_query):
        cfg=self.lib.Z3_mk_config();ctx=self.lib.Z3_mk_context(cfg)
        try:
            res=self.lib.Z3_eval_smtlib2_string(ctx,s.encode())
            if res is None:raise RuntimeError('Z3 returned null')
            status=res.decode().strip()
            if status.startswith('sat'):
                values=self.lib.Z3_eval_smtlib2_string(ctx,values_query.encode())
                return parse_z3_string('sat\n'+values.decode())
            return parse_z3_string(status)
        finally:
            self.lib.Z3_del_context(ctx);self.lib.Z3_del_config(cfg)

def word_step(kind,state):
    if kind in ('nr_lcg32','ansi_lcg32','msvc_lcg32'):
        a,c={'nr_lcg32':(1664525,1013904223),'ansi_lcg32':(1103515245,12345),'msvc_lcg32':(214013,2531011)}[kind]
        x=(a*state[0]+c)&MASK32
        return [x],x
    if kind=='xorshift32':
        x=state[0];x^=(x<<13)&MASK32;x^=x>>17;x^=(x<<5)&MASK32;x&=MASK32
        return [x],x
    if kind=='xorshift96':
        x,y,z=state;t=x^((x<<16)&MASK32);t^=t>>5;t^=(t<<1)&MASK32
        z2=(t^y^z)&MASK32
        return [y,z,z2],z2
    x,y,z,w=state;t=x^((x<<11)&MASK32);nw=(w^(w>>19)^t^(t>>8))&MASK32
    return [y,z,w,nw],nw

def forward_no_rejection(kind,state,n):
    curr=state;words=[]
    while len(words)*4 < 3*n:
        curr,w=word_step(kind,curr)
        words.append(w)
    raw=b''.join(w.to_bytes(4,'big') for w in words)
    got=[int.from_bytes(raw[3*i:3*i+3],'big') for i in range(n)]
    return got

def solve_prefix(lib,kind,ranks,k,timeout_ms=12000):
    nwords=(3*k+3)//4
    decl,words,states=words_prng(kind,nwords)
    lines=['(set-logic QF_BV)',f'(set-option :timeout {timeout_ms})']+decl
    for i,r in enumerate(ranks[:k]):
        term=raw24_expr(words,i)
        # Exact accepted raw aliases, not an approximate modulo constraint.
        alts=[f'(= {term} (_ bv{r+j*N} 24))' for j in range(51)]
        lines.append('(assert (or '+' '.join(alts)+'))')
    lines+=['(check-sat)']
    start=time.monotonic()
    verdict,values=lib.query('\n'.join(lines),'(get-value ('+' '.join(states)+'))')
    duration=time.monotonic()-start
    if verdict=='sat':
        seed=tuple(values[v] for v in states)
        raw=forward_no_rejection(kind,seed,k)
        assert len(raw)==k and all(v<LIMIT and v%N==r for v,r in zip(raw,ranks[:k])),(kind,k,seed,raw)
        return {'result':verdict,'seconds':round(duration,3),'state':list(seed),'raw24':raw}
    return {'result':verdict,'seconds':round(duration,3)}

def run(train,timeout_ms=12000):
    rows=reads(train)
    ranks=[int(row['lex_rank']) for row in rows]
    assert len(ranks)==599
    out={'dataset':Path(train).name,'training_draws':len(rows),'first_id':int(rows[0]['draw_id']),'last_id':int(rows[-1]['draw_id']),'sampler':'fixed big-endian continuous 24bit rejection/combinadic; zero rejected chunks for probed prefix','families':{},'solver':'native libz3.so.4 using exact QF_BV constraints','timeout_ms':timeout_ms}
    z=Z3Lib()
    for kind in ['nr_lcg32','ansi_lcg32','msvc_lcg32','xorshift32','xorshift96','xorshift128']:
        measurements=[]
        for k in [4,6,8,10,12]:
            ans=solve_prefix(z,kind,ranks,k,timeout_ms)
            ans['k']=k;measurements.append(ans)
            print(kind,k,ans['result'],ans['seconds'],flush=True)
            if ans['result'] in ('unsat','unknown'):break
        out['families'][kind]=measurements
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--train',required=True);ap.add_argument('--out',required=True);ap.add_argument('--timeout-ms',type=int,default=12000)
    a=ap.parse_args();report=run(a.train,a.timeout_ms)
    Path(a.out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
