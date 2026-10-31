#!/usr/bin/env python3
"""Exploratory exact SMT model of unrestricted Marsaglia xorshift128 +
5-pick multiply-high sampler from unordered sets. All initial 128 bits unknown.
No extraction order supplied. A timeout is UNKNOWN, never UNSAT.
"""
import argparse,ctypes as C,json,re,time
from pathlib import Path
def independent_transition(state):
    x,y,z,w=state
    mask=(1<<32)-1
    t=(x^((x<<11)&mask))&mask
    next_w=(w^(w>>19)^t^(t>>8))&mask
    return (y,z,w,next_w),next_w

def draw(s,gap=0):
    pool=list(range(1,36));out=[]
    for j in range(5):
        s,word=independent_transition(s)
        i=(word*(35-j))>>32
        out.append(pool.pop(i))
    for _ in range(gap):s,_=independent_transition(s)
    return s,tuple(sorted(out))

def upper_domains(ticket, bits=5):
    nums=sorted(ticket); domains=[];space=1<<32
    for j in range(5):
        high=set()
        for rank,v in enumerate(nums):
            for below in range(max(0,j-(4-rank)),min(j,rank)+1):
                index=v-1-below; remaining=35-j
                lo=(index*space+remaining-1)//remaining
                hi=((index+1)*space+remaining-1)//remaining-1
                high.update(range(lo>>(32-bits),(hi>>(32-bits))+1))
        domains.append(high)
    return domains

def formula(tickets,gap=0,pin=None,strengthen=False):
    lines=['(set-logic QF_BV)','(declare-fun s () (_ BitVec 128))','(define-fun q0 () (_ BitVec 128) s)']
    if pin is not None:lines.append(f'(assert (= s (_ bv{pin} 128)))')
    for d,nums in enumerate(tickets):
        ranks=[];values=[];domains=upper_domains(nums) if strengthen else None
        for j in range(5):
            r=f'r{d}_{j}';ranks.append(r)
            lines.append(f'(declare-fun {r} () (_ BitVec 3))')
            lines.append(f'(assert (bvult {r} (_ bv5 3)))')
            v=f'v{d}_{j}';values.append(v)
            expr=f'(_ bv{nums[-1]} 6)'
            for k in range(3,-1,-1):expr=f'(ite (= {r} (_ bv{k} 3)) (_ bv{nums[k]} 6) {expr})'
            lines.append(f'(define-fun {v} () (_ BitVec 6) {expr})')
        lines.append('(assert (distinct '+' '.join(ranks)+'))')
        for j in range(5):
            step=d*(5+gap)+j
            prev=f'q{step}'
            x=f'((_ extract 31 0) {prev})';w=f'((_ extract 127 96) {prev})'
            t=f'(bvxor {x} (bvshl {x} (_ bv11 32)))'
            out=f'(bvxor (bvxor (bvxor {w} (bvlshr {w} (_ bv19 32))) {t}) (bvlshr {t} (_ bv8 32)))'
            lines.append(f'(define-fun o{step} () (_ BitVec 32) {out})')
            lines.append(f'(define-fun q{step+1} () (_ BitVec 128) (concat o{step} ((_ extract 127 32) {prev})))')
            removed='(_ bv0 6)'
            for k in range(j):removed=f'(bvadd {removed} (ite (bvult r{d}_{k} r{d}_{j}) (_ bv1 6) (_ bv0 6)))'
            index=f'(bvsub (bvsub v{d}_{j} (_ bv1 6)) {removed})'
            observed=f'((_ extract 37 32) (bvmul ((_ zero_extend 6) o{step}) (_ bv{35-j} 38)))'
            lines.append(f'(assert (= {index} {observed}))')
            if strengthen:
                prefix=f'((_ extract 31 27) o{step})'
                lines.append('(assert (or '+' '.join(f'(= {prefix} (_ bv{v} 5))' for v in sorted(domains[j]))+'))')
        for j in range(gap):
            step=d*(5+gap)+5+j;prev=f'q{step}'
            x=f'((_ extract 31 0) {prev})';w=f'((_ extract 127 96) {prev})'
            t=f'(bvxor {x} (bvshl {x} (_ bv11 32)))'
            out=f'(bvxor (bvxor (bvxor {w} (bvlshr {w} (_ bv19 32))) {t}) (bvlshr {t} (_ bv8 32)))'
            lines.append(f'(define-fun o{step} () (_ BitVec 32) {out})')
            lines.append(f'(define-fun q{step+1} () (_ BitVec 128) (concat o{step} ((_ extract 127 32) {prev})))')
    return '\n'.join(lines)+'\n'

class Z3:
 def __init__(self):
    z=C.CDLL('libz3.so.4');self.z=z;ptr=C.c_void_p;cs=C.c_char_p;uint=C.c_uint
    def bind(name,ret,args):
        f=getattr(z,name);f.restype=ret;f.argtypes=args;return f
    self.mk_config=bind('Z3_mk_config',ptr,[]);self.del_config=bind('Z3_del_config',None,[ptr]);self.mk_ctx=bind('Z3_mk_context',ptr,[ptr]);self.del_ctx=bind('Z3_del_context',None,[ptr]);self.mk_solver=bind('Z3_mk_solver',ptr,[ptr]);self.inc=bind('Z3_solver_inc_ref',None,[ptr,ptr]);self.dec=bind('Z3_solver_dec_ref',None,[ptr,ptr]);self.fromstr=bind('Z3_solver_from_string',None,[ptr,ptr,cs]);self.check=bind('Z3_solver_check',C.c_int,[ptr,ptr]);self.getmodel=bind('Z3_solver_get_model',ptr,[ptr,ptr]);self.modelstr=bind('Z3_model_to_string',cs,[ptr,ptr]);self.reason=bind('Z3_solver_get_reason_unknown',cs,[ptr,ptr]);self.mk_params=bind('Z3_mk_params',ptr,[ptr]);self.pinc=bind('Z3_params_inc_ref',None,[ptr,ptr]);self.pdec=bind('Z3_params_dec_ref',None,[ptr,ptr]);self.sym=bind('Z3_mk_string_symbol',ptr,[ptr,cs]);self.setuint=bind('Z3_params_set_uint',None,[ptr,ptr,ptr,uint]);self.setparams=bind('Z3_solver_set_params',None,[ptr,ptr,ptr])
 def run(self,formula,timeout):
    c=self.mk_config();ctx=self.mk_ctx(c);self.del_config(c);solver=self.mk_solver(ctx);self.inc(ctx,solver)
    try:
        p=self.mk_params(ctx);self.pinc(ctx,p);self.setuint(ctx,p,self.sym(ctx,b'timeout'),timeout);self.setparams(ctx,solver,p);self.pdec(ctx,p)
        self.fromstr(ctx,solver,formula.encode());t=time.perf_counter();status=self.check(ctx,solver);elapsed=time.perf_counter()-t
        if status==-1:return {'status':'UNSAT','seconds':elapsed}
        if status==0:return {'status':'UNKNOWN','seconds':elapsed,'reason':self.reason(ctx,solver).decode()}
        model=self.modelstr(ctx,self.getmodel(ctx,solver)).decode();m=re.search(r'\bs\s*->\s*(#x[0-9a-fA-F]+|#b[01]+|\(_ bv\d+ 128\))',model)
        if not m:return {'status':'SAT','seconds':elapsed,'seed':None,'parse_error':model[:200]}
        val=m.group(1);seed=int(val[2:],16) if val.startswith('#x') else int(val[2:],2) if val.startswith('#b') else int(re.search(r'bv(\d+)',val).group(1))
        return {'status':'SAT','seconds':elapsed,'seed':seed}
    finally:
        self.dec(ctx,solver);self.del_ctx(ctx)

def main():
    p=argparse.ArgumentParser();p.add_argument('--n',type=int,default=8);p.add_argument('--timeout',type=int,default=10000);p.add_argument('--pin',action='store_true');p.add_argument('--strengthen',action='store_true');p.add_argument('--seed',type=lambda s:int(s,0),default=0x8877665544332211ffeeddccbbaa9988)
    a=p.parse_args();s=tuple((a.seed>>(32*i))&0xffffffff for i in range(4))
    tickets=[]
    for _ in range(a.n):s,vals=draw(s);tickets.append(vals)
    source=formula(tickets,pin=a.seed if a.pin else None,strengthen=a.strengthen)
    print('formula size',len(source),'bytes',a.n,'draws, pin',a.pin,flush=True)
    res=Z3().run(source,a.timeout)
    if res['status']=='SAT' and res['seed'] is not None:
        ss=tuple((res['seed']>>(32*i))&0xffffffff for i in range(4))
        matches=0
        for vals in tickets:
            ss,actual=draw(ss)
            if vals!=actual:break
            matches+=1
        res['exact_full_tickets']=matches
        res['correct_initial_state']=res['seed']==a.seed
    print(res,flush=True)
if __name__=='__main__':main()
