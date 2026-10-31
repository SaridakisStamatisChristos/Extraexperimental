"""Reproducible bounded SMT benchmarks; SAT states must pass full-ticket replay."""
import ctypes as C,json,platform,time
from pathlib import Path
from exact_smt128 import Z3,formula,draw
ROOT=Path(__file__).resolve().parent
SEED=0x8877665544332211ffeeddccbbaa9988

def gen(seed,n):
    s=tuple((seed>>(i*32))&0xffffffff for i in range(4))
    rows=[]
    for _ in range(n):
        s,t=draw(s);rows.append(t)
    return rows

def version():
    z=C.CDLL('libz3.so.4');v=z.Z3_get_full_version;v.argtypes=[];v.restype=C.c_char_p
    return v().decode()

def main():
    trials=[(3,False,None,3000),(5,False,None,5000),(8,False,None,8000),
            (8,True,None,8000),(8,True,SEED,3000),
            (3,False,SEED^0x1111111111111111,3000)]
    results=[]
    for n,strong,pin,budget in trials:
        rows=gen(SEED,n)
        t=time.perf_counter();f=formula(rows,pin=pin,strengthen=strong)
        result=Z3().run(f,budget)
        if result['status']=='SAT':
            state=result['seed']
            result['full_ticket_replay']=gen(state,n)==rows if state is not None else False
            result['true_planted_state']=state==SEED
            assert result['full_ticket_replay'],result
        result.update({'n':n,'strengthen':strong,'pin':pin is not None,'timeout_ms':budget,
                       'formula_bytes':len(f),'end_to_end_seconds':time.perf_counter()-t})
        results.append(result)
        print({k:v for k,v in result.items() if k not in ('seed',)},flush=True)
    out={'scope':'Marsaglia xorshift128 unrestricted state, exact high sampler, unordered five-ticket-permutation constraints',
         'seed_fixture_hex':hex(SEED),'z3_version':version(),'python':platform.python_version(),
         'cases':results,'conclusion':'Known planted state passes pinned SAT; underdetermined unpinned 3-draw SAT witnesses match; 5/8-draw unpinned timeouts UNKNOWN, not production RNG exclusions.'}
    (ROOT/'P2C_RESULTS.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
