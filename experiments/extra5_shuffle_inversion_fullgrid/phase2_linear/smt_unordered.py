"""Measured SAT/SMT diagnostic, NOT a production RNG attribution.

Uses libz3 through ctypes; unknown/timeouts retain UNKNOWN status.
Outputs are raw linear xorshift128/xoroshiro128/xoshiro256 projections.
"""
from __future__ import annotations
import ctypes as C
import json
import re
import time
from inverse_linear import forms, fourth_domain, MODELS

class Solver:
    def __init__(self):
        z=self.z=C.CDLL('libz3.so.4');ptr=C.c_void_p;string=C.c_char_p;u=C.c_uint
        def bind(name,restype,args):
            fun=getattr(z,name);fun.restype=restype;fun.argtypes=args;return fun
        self.mc=bind('Z3_mk_config',ptr,[])
        self.dc=bind('Z3_del_config',None,[ptr])
        self.mctx=bind('Z3_mk_context',ptr,[ptr])
        self.dctx=bind('Z3_del_context',None,[ptr])
        self.ms=bind('Z3_mk_solver',ptr,[ptr])
        self.inc=bind('Z3_solver_inc_ref',None,[ptr,ptr])
        self.dec=bind('Z3_solver_dec_ref',None,[ptr,ptr])
        self.fromstr=bind('Z3_solver_from_string',None,[ptr,ptr,string])
        self.check=bind('Z3_solver_check',C.c_int,[ptr,ptr])
        self.getmodel=bind('Z3_solver_get_model',ptr,[ptr,ptr])
        self.modelstr=bind('Z3_model_to_string',string,[ptr,ptr])
        self.reason=bind('Z3_solver_get_reason_unknown',string,[ptr,ptr])
        self.mparams=bind('Z3_mk_params',ptr,[ptr]);self.pinc=bind('Z3_params_inc_ref',None,[ptr,ptr]);self.pdec=bind('Z3_params_dec_ref',None,[ptr,ptr]);self.msy=bind('Z3_mk_string_symbol',ptr,[ptr,string]);self.paramu=bind('Z3_params_set_uint',None,[ptr,ptr,ptr,u]);self.setp=bind('Z3_solver_set_params',None,[ptr,ptr,ptr])
    def run(self,source,timeout_ms):
        c=self.mc();ctx=self.mctx(c);self.dc(c)
        solver=self.ms(ctx);self.inc(ctx,solver)
        try:
            params=self.mparams(ctx);self.pinc(ctx,params)
            self.paramu(ctx,params,self.msy(ctx,b'timeout'),timeout_ms)
            self.setp(ctx,solver,params);self.pdec(ctx,params)
            self.fromstr(ctx,solver,source.encode())
            t=time.perf_counter();stat=self.check(ctx,solver);elapsed=time.perf_counter()-t
            if stat==1:
                model=self.modelstr(ctx,self.getmodel(ctx,solver)).decode()
                pat=r'\(define-fun s \(\) \(_ BitVec (\d+)\)\s+(#x[0-9a-fA-F]+|#b[01]+|\(_ bv\d+ \d+\))'
                m=re.search(pat,model)
                if not m:raise RuntimeError('cannot parse state '+model[:1000])
                val=m.group(2)
                seed=int(val[2:],16) if val.startswith('#x') else int(val[2:],2) if val.startswith('#b') else int(re.search(r'bv(\d+)',val).group(1))
                return {'status':'SAT','seed':seed,'seconds':elapsed}
            if stat==-1:return {'status':'UNSAT','seconds':elapsed}
            return {'status':'UNKNOWN','reason':self.reason(ctx,solver).decode(),'seconds':elapsed}
        finally:
            self.dec(ctx,solver);self.dctx(ctx)


def build_formula(model,tickets,indices,gap=0,sampler='mod'):
    selected=list(indices)
    ff=forms(model,max(selected)+1,gap,sampler)
    width=model.size
    lines=['(set-logic QF_BV)',f'(declare-fun s () (_ BitVec {width}))']
    for d in selected:
        parts=[]
        for k in range(4,-1,-1):
            bits=[i for i in range(width) if (ff[d][k]>>i)&1]
            preds=[f'(= ((_ extract {b} {b}) s) #b1)' for b in bits]
            parity='false' if not preds else preds[0] if len(preds)==1 else '(xor '+' '.join(preds)+')'
            parts.append(f'(ite {parity} #b1 #b0)')
        idx=parts[0]
        for p in parts[1:]:idx=f'(concat {idx} {p})'
        domain=sorted(fourth_domain(tickets[d]))
        lines.append(f'(define-fun d{d} () (_ BitVec 5) {idx})')
        lines.append('(assert (or '+' '.join(f'(= d{d} (_ bv{v} 5))' for v in domain)+'))')
    return '\n'.join(lines)+'\n'


def selected_domains(tickets,count):
    return sorted(range(len(tickets)),key=lambda i:(len(fourth_domain(tickets[i])),i))[:count]
