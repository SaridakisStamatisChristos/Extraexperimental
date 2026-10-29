#!/usr/bin/env python3
"""EXTRA 5: deterministic, auditable comparison of toy algorithm implementations.

Not reproduction of any production lottery implementation. No seed is fitted to observations.
Source for observations: https://numerics.gr/extra-5/kliroseis-apotelesmata
Snapshot: 2026-10-29 10:32 Europe/Athens, most recent posted draw 14355.
"""
import csv, hashlib, itertools, json, math, random
from collections import Counter
from pathlib import Path
from scipy.stats import hypergeom
from sympy import nextprime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES

BASE = Path(__file__).parent
# chronological, first draw on Oct 19 and last on Oct 28
OBS = {
14336:[5,6,8,24,30],
14337:[7,9,10,15,21],
14338:[1,7,9,31,32],
14339:[5,8,18,27,32],
14340:[1,7,13,31,32],
14341:[6,7,20,26,32],
14342:[2,19,29,30,31],
14343:[9,16,29,31,34],
14344:[17,18,21,28,35],
14345:[17,19,24,25,34],
14346:[21,24,27,31,35],
14347:[1,5,10,16,28],
14348:[3,9,10,17,21],
14349:[5,6,17,22,30],
14350:[12,26,27,30,31],
14351:[6,10,17,28,31],
14352:[2,7,15,26,27],
14353:[3,5,22,24,29],
14354:[10,15,26,27,29],
14355:[4,14,15,19,27],
}
assert len(OBS)==20 and list(OBS)==list(range(14336,14356))
assert all(len(s)==5 and len(set(s))==5 and s==sorted(s) and min(s)>=1 and max(s)<=35 for s in OBS.values())
MAGIC=b'EXTRA5-2026-10-29-ALGORITHM-DEMO-V1;no-fitting;'
def seed(label, n=32):
    buf=b''; i=0
    while len(buf)<n:
        buf+=hashlib.sha256(MAGIC+label.encode()+i.to_bytes(4,'big')).digest(); i+=1
    return buf[:n]

class ByteSource:
    def __init__(self, kind):
        self.kind=kind
        self.buffer=bytearray()
        if kind=='MT19937':
            self.mt=random.Random(int.from_bytes(seed(kind),'big'))
        if kind=='SHA256-counter':
            self.key=seed(kind); self.ctr=0
        if kind in ('AES-192-CFB','DES-CFB'):
            if kind=='AES-192-CFB':
                block=Cipher(algorithms.AES(seed(kind+':key',24)),modes.CFB(seed(kind+':iv',16)))
            else:
                # EDE with three identical keys is mathematically DES; CFB64 feedback.
                k=seed(kind+':key',8)
                block=Cipher(TripleDES(k*3),modes.CFB(seed(kind+':iv',8)))
            self.encr=block.encryptor()
        if kind=='ChaCha20':
            self.encr=Cipher(algorithms.ChaCha20(seed(kind+':key'),seed(kind+':nonce',16)), mode=None).encryptor()
        if kind in ('BBS','RSA-Rabin-style'):
            def prime(label):
                u=int.from_bytes(seed(label,32),'big') | (1<<255) | 3
                p=int(nextprime(u))
                while p % 4 != 3: p=int(nextprime(p))
                return p
            p=prime(kind+':p'); q=prime(kind+':q'); assert p!=q
            self.mod=p*q
            x=int.from_bytes(seed(kind+':initial-state'),'big')%self.mod
            self.state=x*x%self.mod if kind=='BBS' else x
            self.e=65537
    def onebyte(self):
        if self.kind=='MT19937': return self.mt.getrandbits(8)
        if self.kind=='SHA256-counter':
            if not self.buffer:
                self.buffer.extend(hashlib.sha256(self.key+self.ctr.to_bytes(8,'big')).digest()); self.ctr+=1
        elif self.kind in ('AES-192-CFB','DES-CFB','ChaCha20'):
            if not self.buffer: self.buffer.extend(self.encr.update(b'\0'*4096))
        elif self.kind in ('BBS','RSA-Rabin-style'):
            byte=0
            for j in range(8):
                self.state=pow(self.state,2 if self.kind=='BBS' else self.e,self.mod)
                byte=(byte<<1)|(self.state&1)
            return byte
        return self.buffer.pop(0)
    def below(self, n):
        # unbiased mapping from an 8-bit value to n outcomes (1<=n<=35).
        limit=256-(256%n)
        while True:
            v=self.onebyte()
            if v<limit: return v%n

def draw(source, sampler):
    arr=list(range(1,36))
    if sampler=='remove':
        out=[]
        for _ in range(5): out.append(arr.pop(source.below(len(arr))))
    elif sampler=='partial-fisher-yates':
        for i in range(5):
            j=i+source.below(35-i)
            arr[i],arr[j]=arr[j],arr[i]
        out=arr[:5]
    else: raise ValueError(sampler)
    return sorted(out)

KIND=['BBS','RSA-Rabin-style','DES-CFB','AES-192-CFB','ChaCha20','SHA256-counter','MT19937']
SAMPLER=['remove','partial-fisher-yates']
rows=[]; scores=[]; predictions={}
actual=[set(x) for x in OBS.values()]
for kind in KIND:
    for sampler in SAMPLER:
        # distinct sampling schemes share PRNG initialization per algorithm.
        rng=ByteSource(kind)
        preds=[draw(rng,sampler) for _ in OBS]
        predictions[f'{kind}/{sampler}']=preds
        matches=[len(set(p)&a) for p,a in zip(preds,actual)]
        hits=sum(matches)
        scores.append({'algorithm':kind,'sampler':sampler,'total_matches':hits,
                'mean_matches_per_draw':hits/20,
                'draws_with_3_or_more':sum(m>=3 for m in matches),
                'draws_with_4_or_more':sum(m>=4 for m in matches),
                'exact_5_of_5':sum(m==5 for m in matches),
                'max_match_in_one_draw':max(matches)})
        for number,obs,pred,m in zip(OBS, OBS.values(),preds,matches):
            rows.append({'draw_id':number,'algorithm':kind,'sampler':sampler,
                      'actual':' '.join(map(str,obs)),'simulated':' '.join(map(str,pred)),
                      'matches':m})
# Exact null for a fixed, predeclared sequence independently compared with 20 fair draws.
pmf=hypergeom.pmf(list(range(6)),35,5,5)
dist=[1.0]
for _ in range(20):
    new=[0.0]*(len(dist)+5)
    for i,pr in enumerate(dist):
        for k,pk in enumerate(pmf): new[i+k]+=pr*pk
    dist=new
for item in scores:
    obs=item['total_matches']
    item['one_sided_p_uncorrected']=sum(dist[obs:])
    item['bonferroni_p_for_14_predeclared_models']=min(1.,14*item['one_sided_p_uncorrected'])
scores.sort(key=lambda x:(-x['total_matches'],x['algorithm'],x['sampler']))

# Observed draw-level summaries. Note 20 is too small for stable uniformity inference.
counts=Counter(itertools.chain.from_iterable(OBS.values()))
lag_overlaps=[len(a&b) for a,b in zip(actual,actual[1:])]
observed={
    'draws':20, 'unique_numbers_seen':len(counts),
    'frequencies':{str(n):counts[n] for n in range(1,36)},
    'average_numbers_per_draw':5,
    'consecutive_draw_overlap_total':sum(lag_overlaps),
    'consecutive_draw_overlap_mean':sum(lag_overlaps)/19,
    'expected_consecutive_draw_overlap_total':19*25/35,
    'largest_frequency':max(counts.values()),
    'min_frequency':min(counts.get(n,0) for n in range(1,36)),
    'draws_with_repeated_previous_3_or_more':sum(x>=3 for x in lag_overlaps),
}
result={'date_snapshot':'2026-10-29 10:32 Europe/Athens',
    'source':'https://numerics.gr/extra-5/kliroseis-apotelesmata',
    'algorithm_specification':'illustrative variants, not actual OPAP generator or seeds',
    'seed_derivation': 'SHA256 counter expansion using ASCII domain '+MAGIC.decode(),
    'sampling':'rejection sampling of 8-bit bytes to unbiased range 0..n-1; 5 choices without replacement',
    'notes':'BBS and RSA outputs generated one least-significant bit per update; DES via equal-key TripleDES equivalent in CFB64; AES192 CFB128; ChaCha20 is 64-bit counter 64-bit nonce OpenSSL convention; no calibration to draw outputs',
    'theoretical_expected_matches_per_20_draws':20*25/35,
    'theoretical_sd_matches_per_20_draws':math.sqrt(20*5*(5/35)*(30/35)*(30/34)),
    'null_hit_probability_3_or_more_per_draw':sum(pmf[3:]),
    'observed':observed,'comparison':scores,
    'draws_actual':[{ 'draw_id':n,'numbers':seq} for n,seq in OBS.items()],
}
with (BASE/'extra5_last20_model_comparisons.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['draw_id','algorithm','sampler','actual','simulated','matches']); w.writeheader();w.writerows(rows)
with (BASE/'extra5_last20_data.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['draw_id','n1','n2','n3','n4','n5']);w.writerows([[n]+v for n,v in OBS.items()])
(BASE/'extra5_last20_simulation_results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
print('Observed:',observed)
print('Null mean',result['theoretical_expected_matches_per_20_draws'],'SD',result['theoretical_sd_matches_per_20_draws'])
for r in scores:print(r)
print('BEST PREDICTIONS')
best=scores[0];best_name=f"{best['algorithm']}/{best['sampler']}"
for n,obs,pred in zip(OBS,OBS.values(),predictions[best_name]):print(n,obs,pred,len(set(obs)&set(pred)))