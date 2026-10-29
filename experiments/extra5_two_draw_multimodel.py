#!/usr/bin/env python3
"""Diverse two-draw 5/35 models, fitted to #14249 and #14250 only.
Educational interpolation, NOT a recovered EXTRA 5 generator.
The hidden result for #14251 must not be consulted.
"""
import json
import math
from pathlib import Path

FIRST=(2,4,30,32,35)
SECOND=(2,5,9,30,33)
TARGET=14251
N=math.comb(35,5)

def rank(ticket):
    if len(ticket)!=5 or tuple(sorted(set(ticket)))!=tuple(ticket) or not all(1<=n<=35 for n in ticket):
        raise ValueError('invalid ticket')
    out=0
    previous=0
    for pos,n in enumerate(ticket):
        for v in range(previous+1,n):
            out+=math.comb(35-v,4-pos)
        previous=n
    return out

def unrank(x):
    if type(x)!=int or not 0<=x<N:raise ValueError('invalid rank')
    out=[];prior=0
    for remaining in range(5,0,-1):
        for v in range(prior+1,36):
            weight=math.comb(35-v,remaining-1)
            if x<weight:
                out.append(v);prior=v;break
            x-=weight
        else:raise AssertionError('unrank overflow')
    return tuple(out)

def ticket(numbers):
    n=tuple(sorted(numbers))
    if len(n)!=5 or len(set(n))!=5 or any(x<1 or x>35 for x in n):
        raise ValueError('invalid output ticket')
    return n

def candidates():
    x,y=rank(FIRST),rank(SECOND)
    assert (x,y)==(55817,57278)
    models=[]
    for a in (1,3,5):
        c=(y-a*x)%N
        models.append((f'affine_rank_a{a}','affine LCG',{'a':a,'c':c},unrank((a*y+c)%N),unrank((a*x+c)%N)==SECOND))
    d=math.gcd(x,N)
    if y%d==0:
        aa=((y//d)*pow(x//d,-1,N//d))%(N//d)
        models.append(('multiplicative_rank','multiplicative congruential',{'a':aa,'modulus':N},unrank(aa*y%N),unrank(aa*x%N)==SECOND))
    key=x^y
    models.append(('xor_rank_two_cycle','XOR state',{'xor_mask':key},unrank(y^key),unrank(x^key)==SECOND))
    shifts=[(v-u)%35 for u,v in zip(FIRST,SECOND)]
    proposed=[1+((v-1+s)%35) for v,s in zip(SECOND,shifts)]
    used=set();selected=[]
    for n in proposed:
        while n in used:n=1+(n%35)
        used.add(n);selected.append(n)
    check=ticket(1+((v-1+s)%35) for v,s in zip(FIRST,shifts))
    models.append(('positionwise_mod35','circular position shifts',{'shifts':shifts,'collision':'next free'},ticket(selected),check==SECOND))
    mapping=dict(zip(FIRST,SECOND))
    unused_in=[v for v in range(1,36) if v not in mapping]
    unused_out=[v for v in range(1,36) if v not in SECOND]
    mapping.update(zip(unused_in,unused_out))
    assert len(mapping)==35 and len(set(mapping.values()))==35
    models.append(('permutation_extension','permutation completion',{'completion':'remaining sorted input/output'},ticket(mapping[v] for v in SECOND),ticket(mapping[v] for v in FIRST)==SECOND))
    models.append(('fibonacci_rank','two-state modular Fibonacci',{'initial':[x,y]},unrank((x+y)%N),True))
    models.append(('constant_rank','constant-state control',{'value':y},SECOND,unrank(y)==SECOND))
    result=[]
    for name,family,parameters,pred,fit in models:
        assert fit, name
        assert ticket(pred)==pred
        result.append({'model':name,'family':family,'parameters':parameters,'fit_first_to_second':fit,'next':list(pred)})
    assert len(result)==9 and len({tuple(v['next']) for v in result})==9
    assert result[0]['next']==[2,5,15,30,34]
    return result

def report():
    models=candidates()
    return {'experiment':'extra5_two_draw_multimodel_20261029_v1',
            'training':[{'draw_id':14249,'numbers':list(FIRST)},{'draw_id':14250,'numbers':list(SECOND)}],
            'hidden_draw_id':TARGET,'hidden_result_not_consulted':True,
            'frozen_original_primary':{'model':'affine_rank_a1','numbers':[2,5,15,30,34],
              'pre_reveal_commit':'53784da5327baa669b3c5c7889c0059dcd2c1c3e'},
            'models':models,'distinct_predictions':len(models),
            'note':'These exact fits are formula construction, NOT recovered operator keys/seeds, nor verified prediction. The existing primary remains fixed.'}

if __name__=='__main__':
    dest=Path(__file__).with_name('extra5_two_draw_multimodel_predictions.json')
    dest.write_text(json.dumps(report(),indent=2)+'\n')
    print(json.dumps({'models':len(candidates()),'next':{r['model']:r['next'] for r in candidates()}},indent=2))
