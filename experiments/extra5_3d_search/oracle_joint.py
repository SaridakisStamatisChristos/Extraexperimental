"""Independent pure-Python oracle for the entire 20,160-configuration PRNG library.

No C++ calls/shared code. Independently reconstruct seeding, output recurrences,
combination rank / Fisher-Yates selection, and permutation sampling.
"""
import csv, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MASK=(1<<64)-1; M32=(1<<32)-1; N=324632
LIMIT=(1<<32)//N*N

def rotl(x,n):return ((x<<n)|(x>>(64-n)))&MASK

def splitmix_step(s):
  s=(s+0x9e3779b97f4a7c15)&MASK
  z=s;z=((z^(z>>30))*0xbf58476d1ce4e5b9)&MASK
  z=((z^(z>>27))*0x94d049bb133111eb)&MASK
  return s,(z^(z>>31))&MASK

class RandomWords:
  def __init__(self,kind,seed):
    self.kind=kind;self.seed=seed&MASK;self.state=self.seed
    if kind=='xorshift64star' and self.state==0:self.state=0x9e3779b97f4a7c15
    if kind=='xorshift32':
      self.state=self.state&M32
      if self.state==0:self.state=0x9e3779b9
    if kind=='jsf32':
      self.abcd=[]
      for _ in range(4):
        self.state,v=splitmix_step(self.state);self.abcd.append(v&M32)
      for _ in range(20):self.word()
    if kind=='xoroshiro128plus':
      self.state,self.a=splitmix_step(self.state)
      self.state,self.b=splitmix_step(self.state)
    elif kind=='xoshiro256starstar':
      self.arr=[]
      for i in range(4):
        self.state,z=splitmix_step(self.state);self.arr.append(z)
  def word(self):
    if self.kind=='splitmix64':
      self.state,v=splitmix_step(self.state)
      return v>>32
    if self.kind=='xorshift64star':
      s=self.state;s^=s>>12;s^=(s<<25)&MASK;s^=s>>27
      self.state=s&MASK
      return (self.state*2685821657736338717&MASK)>>32
    if self.kind=='lcg64high':
      self.state=(self.state*6364136223846793005+1442695040888963407)&MASK
      return self.state>>32
    if self.kind=='xorshift32':
      x=self.state;x^=(x<<13)&M32;x^=x>>17;x^=(x<<5)&M32
      self.state=x&M32
      return self.state
    if self.kind=='jsf32':
      a,b,c,d=self.abcd
      e=(a-(((b<<27)|(b>>(32-27)))&M32))&M32
      a=(b^(((c<<17)|(c>>(32-17)))&M32))&M32
      b=(c+d)&M32
      c=(d+e)&M32
      d=(e+a)&M32
      self.abcd=[a,b,c,d]
      return d
    if self.kind=='pcg32':
      old=self.state;self.state=(old*6364136223846793005+1442695040888963407)&MASK
      x=(((old>>18)^old)>>27)&M32;rot=old>>59
      return ((x>>rot)|(x<<((-rot)&31)))&M32
    if self.kind=='xoroshiro128plus':
      s0=self.a;s1=self.b;res=(s0+s1)&MASK
      s1^=s0
      self.a=(rotl(s0,55)^s1^(s1<<14))&MASK
      self.b=rotl(s1,36)
      return (res>>32)&M32
    if self.kind=='xoshiro256starstar':
      a,b,c,d=self.arr
      res=(rotl((b*5)&MASK,7)*9)&MASK
      t=(b<<17)&MASK
      c^=a;d^=b;b^=c;a^=d;c^=t;d=rotl(d,45)
      self.arr=[a&MASK,b&MASK,c&MASK,d&MASK]
      return res>>32
    raise ValueError(self.kind)

def choose(n,k):
  from math import comb
  return comb(n,k) if 0<=k<=n else 0

def fromrank(rank):
  nums=[];lo=1
  for j in range(5):
    for value in range(lo,36):
      c=choose(35-value,4-j)
      if rank<c:
        nums.append(value);lo=value+1;break
      rank-=c
  assert len(nums)==5
  return nums

def seed(meta,rule,off):
  prev=int(meta['prev_set_rank']);prev2=int(meta['prev2_set_rank'])
  i=int(meta['draw_id'])
  minute=(int(meta['date_ordinal'])-719163)*1440+(1140 if int(meta['time_slot']) else 900)
  pid=int(meta['prev_perm_rank'])&MASK
  pre=(prev&MASK);prev2&=MASK
  day=int(meta['date_ordinal']);slot=int(meta['time_slot'])
  if rule=='prev_set':x=pre
  elif rule=='prev_perm':x=pid
  elif rule=='prev_set_perm':x=(pre*120+pid)&MASK
  elif rule=='id_xor_prev_set':x=i^pre
  elif rule=='minute_xor_prev_set':x=minute^pre
  elif rule=='id_xor_prev_perm':x=i^pid
  elif rule=='minute_xor_prev_perm':x=minute^pid
  elif rule=='mixed_joint_id':
    _,x=splitmix_step((i^((pre<<17)&MASK)^((pid<<51)&MASK))&MASK)
  elif rule=='mixed_joint_minute':
    _,x=splitmix_step((minute+pre*0x9e3779b97f4a7c15+pid)&MASK)
  elif rule=='mixed_lag2_id':
    _,x=splitmix_step((pre^((prev2<<1)&MASK)^i)&MASK)
  elif rule=='prevsum_xor_minute':x=int(meta['prev_sum'])^minute
  elif rule=='day_slot_prev_set':x=((day<<1)^slot^pre)&MASK
  elif rule=='drawid_control':x=i
  elif rule=='minute_control':x=minute
  else:raise ValueError(rule)
  return (x+int(off))&MASK

def generate(meta,config):
  kind=config['gen'];sampler=config['sampler'];s=seed(meta,config['seed_rule'],config['offset']);prng=RandomWords(kind,s)
  if sampler in ('rank32_rejection','rank24_rejection'):
    lim=LIMIT if sampler=='rank32_rejection' else (1<<24)//N*N
    for _ in range(128):
      raw=prng.word()
      if sampler=='rank24_rejection':raw>>=8
      if raw<lim:
        nums=fromrank(raw%N);break
    else:raise ValueError('rank rejection cap')
  elif sampler=='distinct_mod':
    seen=set()
    for _ in range(128):
      seen.add(1+prng.word()%35)
      if len(seen)==5:break
    nums=sorted(seen)
    assert len(nums)==5
  elif sampler in ('fisher_mod','fisher_high'):
    a=list(range(1,36))
    for j in range(5):
      raw=prng.word()
      delta=raw%(35-j) if sampler=='fisher_mod' else (raw*(35-j))>>32
      a[j],a[j+delta]=a[j+delta],a[j]
    nums=sorted(a[:5])
  else:raise ValueError(sampler)
  pm=config['permutation']
  if pm=='sorted_control':p=0
  elif pm=='separate_stream_rank':
    separate_seed=s^0x5045524d53485546
    _,separate_seed=splitmix_step(separate_seed&MASK)
    rr=RandomWords(kind,separate_seed)
    for _ in range(128):
      val=rr.word()
      if val<((1<<32)//120*120):p=val%120;break
    else:raise ValueError('separate rejection cap')
  elif pm=='same_stream_rank':
    for _ in range(128):
      val=prng.word()
      if val<((1<<32)//120*120):p=val%120;break
    else:raise ValueError('same rejection cap')
  elif pm=='same_stream_fisher':
    a=list(range(5))
    for j in range(5):
      delta=prng.word()%(5-j)
      a[j],a[j+delta]=a[j+delta],a[j]
    remaining=list(range(5));p=0
    facts=[24,6,2,1,1]
    for j,value in enumerate(a):
      k=remaining.index(value)
      p+=k*facts[j]
      remaining.pop(k)
  else:raise ValueError(pm)
  return nums,p

def main():
  with (ROOT/'FROZEN_JOINT3D_models.csv').open() as f:conf={r['objective']:r for r in csv.DictReader(f)}
  with (ROOT/'future_features_only.csv').open() as f:meta={int(r['draw_id']):r for r in csv.DictReader(f)}
  with (ROOT/'FROZEN_JOINT3D_future.csv').open() as f:rows=list(csv.DictReader(f))
  mismatches=[]
  for r in rows:
    nums,p=generate(meta[int(r['draw_id'])],conf[r['objective']])
    expected=[int(r[f'n{i}']) for i in range(1,6)]
    if nums!=expected or p!=int(r['pred_perm_rank']):
      mismatches.append({'draw_id':r['draw_id'],'model':r['objective'],'oracle':(nums,p),'cpp':(expected,r['pred_perm_rank'])})
  report={'models':list(conf),'cases':len(rows),'mismatches':len(mismatches),'first_three':mismatches[:3]}
  (ROOT/'independent_oracle.json').write_text(json.dumps(report,indent=2)+'\n')
  print(report)
  if mismatches:raise AssertionError('Independent generator replay differs from C++')

if __name__=='__main__':main()
