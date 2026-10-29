#!/usr/bin/env python3
"""Reproduce the locked multi-family seed search for EXTRA 5 #14249 -> #14250.

Synthetic public seed derivation, toy BBS/RSA parameters and sampler are not
Allwyn technical parameters. This must never query #14250's actual result.
"""
import argparse,hashlib,json,math
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
from cryptography.hazmat.decrepit.ciphers.algorithms import CAST5,TripleDES
from extra5_historical_engine import BBS,RSAParity,mixer_m,mixer_b
from extra5_one_draw_seed_fit import COMBINATIONS,LIMIT,unrank_5of35,rank_5of35

TRAIN=(2,4,30,32,35)
DOMAIN=b'EXTRA5-MULTI-FAMILY-BLIND-20261029-v1|PUBLIC-SYNTHETIC|'
FAMILIES=('aes192-cfb128','des-cfb64','cast128-cfb64','bbs-parity-toy','rsa-parity-toy','xor-aes192-des','m-aes192-bbs','b-bbs')

def kdf(family,i):
    return hashlib.sha512(DOMAIN+family.encode()+b'|'+i.to_bytes(8,'big')).digest()

def unit(d,N):
    for i in range(64):
        v=2+(int.from_bytes(hashlib.sha256(d+i.to_bytes(2,'big')).digest(),'big')%(N-3))
        if math.gcd(v,N)==1:return v
    raise ValueError('no coprime synthetic seed')

def bitstream(family,d,n):
    if family=='bbs':s=BBS(383,503,unit(d+b'/bbs',383*503))
    else:s=RSAParity(397,401,17,unit(d+b'/rsa',397*401))
    return bytes(sum(s.bit()<<(7-j) for j in range(8)) for _ in range(n))

def cipher(name,d,n):
    if name=='aes':alg,key,iv=algorithms.AES,d[:24],d[24:40]
    elif name=='des':alg,key,iv=TripleDES,d[:8]*3,d[8:16]
    else:alg,key,iv=CAST5,d[:16],d[16:24]
    return Cipher(alg(key),modes.CFB(iv)).encryptor().update(bytes(n))

def bits(buf):return [b>>j&1 for b in buf for j in range(7,-1,-1)]
def packed(v):return bytes(sum(v[i+j]<<(7-j) for j in range(8)) for i in range(0,len(v),8))

def stream(family,i,n):
    d=kdf(family,i)
    if family=='aes192-cfb128':return cipher('aes',d,n)
    if family=='des-cfb64':return cipher('des',d,n)
    if family=='cast128-cfb64':return cipher('cast',d,n)
    if family=='bbs-parity-toy':return bitstream('bbs',d,n)
    if family=='rsa-parity-toy':return bitstream('rsa',d,n)
    if family=='xor-aes192-des':
        x=cipher('aes',hashlib.sha512(d+b'|aes').digest(),n)
        y=cipher('des',hashlib.sha512(d+b'|des').digest(),n)
        return bytes(a^b for a,b in zip(x,y))
    # The fixed M/B mixing block is 256 bits. To obtain a SHORT preview,
    # compute only its main-loop prefix, never the short block's end wrap.
    full=((n+31)//32)*32 if n>31 else (n*8+2+7)//8
    x=bits(cipher('aes',hashlib.sha512(d+b'|aes').digest(),full)) if family=='m-aes192-bbs' else bits(bitstream('bbs',d,full))
    y=bits(bitstream('bbs',hashlib.sha512(d+b'|bbs').digest(),full)) if family=='m-aes192-bbs' else x
    if n<=31:
        regs=x[:2];out=[]
        for j in range(2,n*8+2):
            v=y[j];out.append(regs[v]);regs[v]=x[j]
        return packed(out)
    out=[]
    for off in range(0,len(x),256):
        xx=x[off:off+256]; yy=y[off:off+256]
        out+=mixer_m(xx,yy) if family=='m-aes192-bbs' else mixer_b(xx)
    return packed(out)[:n]

def decode(raw,pos=0):
    while pos+3<=len(raw):
        v=int.from_bytes(raw[pos:pos+3],'big');pos+=3
        if v<LIMIT:return unrank_5of35(v%COMBINATIONS),pos
    raise ValueError('insufficient fixed preview')

def selection(m):
    value=f"{m['family']}|{m['seed_index']}".encode()
    return hashlib.sha256(DOMAIN+b'FIXED-SELECTION|'+value).hexdigest()

def run(cipher_seeds=400000,math_seeds=80000,mixed_seeds=100000):
    counts={f:cipher_seeds if f in FAMILIES[:3] else math_seeds if f in FAMILIES[3:5] or f=='b-bbs' else mixed_seeds for f in FAMILIES}
    results=[];matches=[]
    for family in FAMILIES:
        found=[];failed=0
        for seed in range(counts[family]):
            try:first,_=decode(stream(family,seed,6))
            except ValueError:failed+=1;continue
            if first==TRAIN:
                raw=stream(family,seed,64)
                one,pos=decode(raw);two,_=decode(raw,pos)
                assert one==TRAIN
                item={'family':family,'seed_index':seed,'fit':list(one),'hidden_next_prediction':list(two)}
                found.append(item);matches.append(item)
        results.append({'family':family,'tested':counts[family],'exceptions':failed,'fits':found})
    chosen=min(matches,key=selection) if matches else None
    return {'training':{'draw_id':14249,'numbers':list(TRAIN)},'hidden_draw_id':14250,
            'hidden_result_accessed':False,'domain':DOMAIN.decode(),
            'tested':sum(counts.values()),'first_draw_exact_fits':len(matches),
            'decode_failures':sum(r['exceptions'] for r in results),
            'results_by_family':results,'selection':'minimum SHA256(DOMAIN + FIXED-SELECTION| + family|seed)',
            'chosen':chosen,'primary_prediction':chosen['hidden_next_prediction'] if chosen else None,
            'note':'Research models with synthetic public seeds; not actual lottery keys or proof of prediction.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cipher-seeds',type=int,default=400000);p.add_argument('--math-seeds',type=int,default=80000);p.add_argument('--mixed-seeds',type=int,default=100000);p.add_argument('--out',type=Path,default=Path(__file__).with_name('extra5_multifamily_blind_compact_results.json'))
    a=p.parse_args();r=run(a.cipher_seeds,a.math_seeds,a.mixed_seeds);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'tested':r['tested'],'first_draw_exact_fits':r['first_draw_exact_fits'],'primary_prediction':r['primary_prediction'],'chosen':r['chosen']},indent=2))
