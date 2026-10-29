#!/usr/bin/env python3
"""Massive reproducible comparison against 100 published EXTRA 5 draws (80 discovery, 20 holdout).

This is NOT seed recovery and NOT a test of the lottery's proprietary production RNG.
The seeds are predetermined test vectors, generated independently of observed draw results.
All samplers aim to generate a uniform 5-subset of 1..35.
"""
import csv, hashlib, hmac, itertools, json, math, struct, time
from collections import Counter
from pathlib import Path
import numpy as np
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
from scipy.stats import hypergeom

BASE=Path(__file__).parent
DOMAIN=b'EXTRA5-BENCH-2026-10-29-v2.0|SEEDS-NOT-FITTED|'
DATA=list(csv.DictReader(open(BASE/'extra5_last100_data.csv',newline='')))
DRAWS=[(int(r['draw_id']),set(int(r[f'n{i}']) for i in range(1,6))) for r in DATA]
assert len(DRAWS)==100 and [d for d,_ in DRAWS]==list(range(14256,14356))
assert all(len(s)==5 and min(s)>=1 and max(s)<=35 for _,s in DRAWS)
TRAIN=[x[1] for x in DRAWS[:80]]
TEST=[x[1] for x in DRAWS[80:]]

def seed_bytes(family, idx, purpose='seed'):
    return hashlib.sha512(DOMAIN+family.encode()+b'|'+str(idx).encode()+b'|'+purpose.encode()).digest()

MASK64=(1<<64)-1
class Source:
    def __init__(self, family, idx):
        self.family=family; self.idx=idx;self.key=seed_bytes(family,idx)
        self.buf=b'';self.offset=0; self.counter=0
        self.kind=''
        if family.startswith('HASH-'):
            self.kind='HASH';self.hashname=family[5:]
        elif family.startswith('HMAC-'):
            self.kind='HMAC';self.hashname=family[5:]
        elif family.startswith('KEYED-'):
            self.kind='KEYED';self.hashname=family[6:]
        elif family.startswith('AES-') or family.startswith('DES-') or family.startswith('CHACHA') or family.startswith('CFB-') or family.startswith('ECB-') or family.startswith('CTR-'):
            self.kind='CIPHER'
            self.enc=self.make_cipher(family)
        elif family.startswith('NP-'):
            self.kind='NUMPY'
            cls={'NP-PCG64':np.random.PCG64,'NP-PCG64DXSM':np.random.PCG64DXSM,'NP-Philox':np.random.Philox,'NP-SFC64':np.random.SFC64,'NP-MT19937':np.random.MT19937}[family]
            self.bg=cls(int.from_bytes(self.key[:16],'big'))
        elif family=='PY-MT19937':
            import random
            self.kind='PY';self.mt=random.Random(int.from_bytes(self.key,'big'))
        else:
            self.kind='MATH'
            self.state=int.from_bytes(self.key[:8],'little') or 1
            self.state2=int.from_bytes(self.key[8:16],'little') or 2
            self.state3=int.from_bytes(self.key[16:24],'little') or 3
            self.state4=int.from_bytes(self.key[24:32],'little') or 4
            if family in ['MATH-BBS','MATH-RSA']:
                # Two fixed known primes make this a toy mathematical family, not a production replica.
                self.mod=1000000007*1000000087
                self.state=(self.state*self.state)%self.mod if family=='MATH-BBS' else (self.state%self.mod)
    def make_cipher(self,name):
        k=self.key
        if name=='DES-CFB64':
            c=TripleDES(k[:8]*3);mode=modes.CFB(k[8:16])
        elif name=='DES-ECB-COUNTER':
            c=TripleDES(k[:8]*3);mode=modes.ECB()
        elif name.startswith('AES-'):
            bits=int(name.split('-')[1]);key=k[:bits//8];c=algorithms.AES(key)
            mode=modes.CFB(seed_bytes(name,self.idx,'iv')[:16]) if 'CFB' in name else (modes.CTR(seed_bytes(name,self.idx,'iv')[:16]) if 'CTR' in name else modes.ECB())
        elif name=='CHACHA20':
            c=algorithms.ChaCha20(k[:32],seed_bytes(name,self.idx,'nonce')[:16]);mode=None
        elif name.startswith('CFB-'):
            alg=name[4:]
            choices={'Camellia128':(algorithms.Camellia,k[:16]),'Camellia256':(algorithms.Camellia,k[:32]),
                     'Blowfish':(algorithms.Blowfish,k[:16]),'CAST5':(algorithms.CAST5,k[:16]),
                     'IDEA':(algorithms.IDEA,k[:16]),'SEED':(algorithms.SEED,k[:16])}
            cc,kk=choices[alg];c=cc(kk);mode=modes.CFB(seed_bytes(name,self.idx,'iv')[:c.block_size//8])
        elif name.startswith('ECB-'):
            alg=name[4:]
            choices={'Camellia128':(algorithms.Camellia,k[:16]),'Camellia256':(algorithms.Camellia,k[:32]),'Blowfish':(algorithms.Blowfish,k[:16])}
            cc,kk=choices[alg];c=cc(kk);mode=modes.ECB()
        else:raise ValueError(name)
        self.block_size=c.block_size//8 if hasattr(c,"block_size") else 64
        self.is_ecb=isinstance(mode,modes.ECB)
        return Cipher(c,mode).encryptor()
    def raw64(self):
        f=self.family;x=self.state;y=self.state2;m=MASK64
        if f=='MATH-LCG32-NR':
            self.state=(1664525*(x & 0xffffffff)+1013904223)&0xffffffff;return self.state
        if f=='MATH-LCG64-MMIX':
            self.state=(6364136223846793005*x+1442695040888963407)&m;return self.state
        if f=='MATH-LCG64-PCG':
            self.state=(6364136223846793005*x+1)&m;return self.state
        if f=='MATH-SPLITMIX64':
            x=(x+0x9E3779B97F4A7C15)&m;self.state=x
            z=(x^(x>>30))*0xBF58476D1CE4E5B9&m
            z=(z^(z>>27))*0x94D049BB133111EB&m
            return z^(z>>31)
        if f=='MATH-XORSHIFT32':
            x&=0xffffffff;x^=(x<<13)&0xffffffff;x^=x>>17;x^=(x<<5)&0xffffffff
            self.state=x or 1;return x
        if f=='MATH-XORSHIFT64STAR':
            x^=x>>12;x^=(x<<25)&m;x^=x>>27;self.state=x;return(x*2685821657736338717)&m
        if f=='MATH-XORSHIFT128PLUS':
            self.state=y
            x^=(x<<23)&m;self.state2=(x^y^(x>>17)^(y>>26))&m
            return(self.state2+y)&m
        if f=='MATH-XOROSHIRO128PLUS':
            t=(x+y)&m;y^=x
            self.state=((x<<55)|(x>>9))&m^y^(y<<14)&m
            self.state2=((y<<36)|(y>>28))&m
            return t
        if f=='MATH-XOSHIRO256SS':
            z=(self.state2*5)&m;out=(((z<<7)|(z>>57))&m)*9&m
            t=(self.state2<<17)&m
            self.state3^=self.state;self.state4^=self.state2
            self.state2^=self.state3;self.state^=self.state4
            self.state3^=t
            self.state4=((self.state4<<45)|(self.state4>>19))&m
            return out
        if f=='MATH-MINSTD':
            self.state=(48271*(x%2147483647))%2147483647 or 1;return self.state
        if f=='MATH-MULBERRY32':
            self.state=(x+0x6D2B79F5)&0xffffffff;t=self.state
            t=((t^(t>>15))*(t|1))&0xffffffff
            t^=(t+((t^(t>>7))*(t|61)))&0xffffffff
            return (t^(t>>14))&0xffffffff
        if f=='MATH-BBS':
            z=0
            for _ in range(8):
                self.state=pow(self.state,2,self.mod);z=(z<<1)|(self.state&1)
            return z
        if f=='MATH-RSA':
            z=0
            for _ in range(8):
                self.state=pow(self.state,65537,self.mod);z=(z<<1)|(self.state&1)
            return z
        raise ValueError(f)
    def refill(self):
        if self.kind=='HASH':
            h=hashlib.new(self.hashname)
            h.update(self.key+self.counter.to_bytes(8,'big'))
            self.buf=h.digest(64) if self.hashname.startswith('shake_') else h.digest()
            self.counter+=1
        elif self.kind=='HMAC':
            self.buf=hmac.digest(self.key,self.counter.to_bytes(8,'big'),self.hashname);self.counter+=1
        elif self.kind=='KEYED':
            digest_size=32 if self.hashname=='blake2s' else 64
            h=getattr(hashlib,self.hashname)(key=self.key[:32 if self.hashname=='blake2s' else 64],digest_size=digest_size)
            h.update(self.counter.to_bytes(8,'big'));self.buf=h.digest();self.counter+=1
        elif self.kind=='CIPHER':
            if self.is_ecb:
                block_bytes=b''.join(i.to_bytes(self.block_size,'big') for i in range(self.counter,self.counter+256))
                self.counter+=256
            else:block_bytes=b'\0'*4096
            self.buf=self.enc.update(block_bytes)
        elif self.kind=='NUMPY':
            self.buf=self.bg.random_raw(256).tobytes()
        elif self.kind=='PY':
            self.buf=b''.join(self.mt.getrandbits(64).to_bytes(8,'little') for _ in range(256))
        else:
            self.buf=b''.join(self.raw64().to_bytes(8,'little') for _ in range(128))
        self.offset=0
    def onebyte(self):
        if self.offset>=len(self.buf):self.refill()
        v=self.buf[self.offset];self.offset+=1;return v
    def u64(self):
        return int.from_bytes(bytes(self.onebyte() for _ in range(8)),'little')
    def below(self,n):
        width=max(1,(n.bit_length()+7)//8)
        cap=1<<(8*width);limit=cap-cap%n
        while True:
            v=0
            for _ in range(width):v=(v<<8)|self.onebyte()
            if v<limit:return v%n

def unrank(rank):
    # Lexicographic combinadic unranking, all C(35,5) subsets equiprobable.
    arr=[];a=1;r=5
    for _ in range(5):
        for v in range(a,36):
            remaining=math.comb(35-v,r-1) if 35-v>=r-1 else 0
            if rank<remaining:
                arr.append(v);a=v+1;r-=1;break
            rank-=remaining
    assert len(arr)==5
    return arr

def draw(src,sampler):
    if sampler=='remove':
        arr=list(range(1,36));return sorted(arr.pop(src.below(len(arr))) for _ in range(5))
    if sampler=='with-rejection':
        out=set()
        while len(out)<5:out.add(src.below(35)+1)
        return sorted(out)
    if sampler=='reservoir':
        arr=list(range(1,6))
        for i in range(6,36):
            j=src.below(i)
            if j<5:arr[j]=i
        return sorted(arr)
    if sampler=='combinadic':
        return unrank(src.below(324632))
    if sampler=='keysort':
        return sorted(sorted(range(1,36),key=lambda n:src.u64())[:5])
    raise ValueError(sampler)

HASHES=['md5','sha1','sha224','sha256','sha384','sha512','sha3_224','sha3_256','sha3_384','sha3_512','blake2s','blake2b','shake_128','shake_256']
FAMILIES=[f'HASH-{h}' for h in HASHES]+[f'HMAC-{h}' for h in ['sha1','sha256','sha512','sha3_256']]+['KEYED-blake2s','KEYED-blake2b']
FAMILIES += [f'AES-{bits}-{mode}' for bits in [128,192,256] for mode in ['CFB','CTR','ECB-COUNTER']]
FAMILIES += ['DES-CFB64','DES-ECB-COUNTER','CHACHA20']
FAMILIES += ['CFB-Camellia128','CFB-Camellia256','CFB-Blowfish','CFB-CAST5','CFB-IDEA','CFB-SEED','ECB-Camellia128','ECB-Camellia256','ECB-Blowfish']
FAMILIES += ['NP-PCG64','NP-PCG64DXSM','NP-Philox','NP-SFC64','NP-MT19937','PY-MT19937']
FAMILIES += ['MATH-LCG32-NR','MATH-LCG64-MMIX','MATH-LCG64-PCG','MATH-SPLITMIX64','MATH-XORSHIFT32','MATH-XORSHIFT64STAR','MATH-XORSHIFT128PLUS','MATH-XOROSHIRO128PLUS','MATH-XOSHIRO256SS','MATH-MINSTD','MATH-MULBERRY32','MATH-BBS','MATH-RSA']
SAMPLERS=['remove','with-rejection','reservoir','combinadic','keysort']

def compare(pred,actual):return sum(len(set(x)&s) for x,s in zip(pred,actual))

def exact_tail(n_draws):
    pmf=hypergeom.pmf(np.arange(6),35,5,5)
    return np.convolve.reduce([pmf]*n_draws) if False else _conv(pmf,n_draws)
def _conv(pmf,n):
    v=np.array([1.])
    for _ in range(n):v=np.convolve(v,pmf)
    return np.cumsum(v[::-1])[::-1]

if __name__=='__main__':
    t0=time.time();records=[];masks=[];errors=[];family_top={};nn=0
    # 32 fixed independent initialization vectors per family; 8 for slower number-theoretic toys.
    for f in FAMILIES:
        nseed=8 if f in ['MATH-BBS','MATH-RSA'] else 32
        for ix in range(nseed):
            for sm in SAMPLERS:
                try:
                    src=Source(f,ix)
                    pred=[draw(src,sm) for _ in range(100)]
                    train=compare(pred[:80],TRAIN)
                    test=compare(pred[80:],TEST)
                    r={'family':f,'seed_index':ix,'sampler':sm,'train_hits_80':train,'holdout_hits_20':test,
                       'holdout_three_plus':sum(len(set(x)&a)>=3 for x,a in zip(pred[80:],TEST)),
                       'holdout_exact':sum(set(x)==a for x,a in zip(pred[80:],TEST))}
                    records.append(r);masks.append([sum(1<<(n-1) for n in p) for p in pred[80:]]);nn+=1
                    if (f not in family_top or train>family_top[f]['train_hits_80'] ):
                        family_top[f]=r
                except Exception as e:
                    errors.append({'family':f,'seed_index':ix,'sampler':sm,'error':str(e)[:150]})
        if len(family_top)%10==0:print('completed families',len(family_top),'models',nn,'seconds',round(time.time()-t0,1),flush=True)
    # Record selected winner by first 80 draws. tie-break independent of holdout.
    records.sort(key=lambda r:(-r['train_hits_80'],r['family'],r['seed_index'],r['sampler']))
    selected=records[0]
    tail20=exact_tail(20);tail80=exact_tail(80)
    # Number of statistical comparisons searched; exact independent-model bound is conservative
    total=len(records)
    hightrain=records[0]['train_hits_80']
    highhold=max(r['holdout_hits_20'] for r in records)
    # Absolute max holdout is diagnostic and invalid as predictive evidence because it was selected after seeing holdout.
    report={
      'data_source':'https://numerics.gr/extra-5/kliroseis-apotelesmata',
      'data_cutoff':'2026-10-28 draw #14355',
      'dataset':{'total':100,'training_draws':80,'training_range':[14256,14335], 'holdout_draws':20,'holdout_range':[14336,14355]},
      'specification':{'families_requested':len(FAMILIES),'families_successful':len(family_top),'samplers':SAMPLERS,'fixed_seeds_per_family':32,'fixed_seeds_for_BBS_and_RSA':8,'seed_domain':DOMAIN.decode(),'total_configs':total,'errors':errors[:20],'error_count':len(errors)},
      'baseline':{'expected_hits_on_80':80*25/35,'expected_hits_on_20':20*25/35,
        'sd_hits_on_20':math.sqrt(20*(5*(5/35)*(30/35)*(30/34))),
        'tail_train_selected_uncorrected':float(tail80[hightrain]),
        'tail_train_selected_bonferroni':min(1.,total*float(tail80[hightrain])),
        'tail_holdout_preselected':float(tail20[selected['holdout_hits_20']]),
        'tail_holdout_best_among_all_uncorrected':float(tail20[highhold]),
        'tail_holdout_best_among_all_bonferroni':min(1.,total*float(tail20[highhold]))},
      'best_train_selected':selected,
      'best_holdout_posthoc':sorted(records,key=lambda x:(-x['holdout_hits_20'],x['family']))[0],
      'top10_by_training':records[:10],
      'family_winners':sorted(family_top.values(),key=lambda x:(-x['train_hits_80'],x['family'])),
      'families':FAMILIES,
      'holdout_scores_summary':{'min':min(r['holdout_hits_20'] for r in records),
        'mean':sum(r['holdout_hits_20'] for r in records)/len(records),
        'max':highhold},
      'elapsed_seconds':round(time.time()-t0,1),
      'interpretation':'All seeds are independent synthetic deterministic test seeds; search scores are not evidence of production RNG use or predictive ability. Holdout selection from 80 draws is an in-sample tuning exercise; no live unseen result was predicted.'
    }
    np.savez_compressed(BASE/'extra5_mass_algorithm_holdout_masks.npz', masks=np.array(masks,dtype=np.uint64))
    with open(BASE/'extra5_mass_algorithm_scores.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['family','seed_index','sampler','train_hits_80','holdout_hits_20','holdout_three_plus','holdout_exact']);w.writeheader();w.writerows(records)
    (BASE/'extra5_mass_algorithm_results.json').write_text(json.dumps(report,indent=2))
    print('FINISHED',len(FAMILIES),'families',total,'configs, errors',len(errors),'seconds',round(time.time()-t0,1))
    print('BEST_TRAIN',selected)
    print('BEST_HOLDOUT_POSTHOC',report['best_holdout_posthoc'])
    print('BASELINE',report['baseline'])
    print('TOP10_BY_TRAIN',report['top10_by_training'])