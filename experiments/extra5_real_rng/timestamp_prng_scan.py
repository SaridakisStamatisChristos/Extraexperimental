#!/usr/bin/env python3
"""Falsifiable, real PRNG implementation tests for EXTRA5 time/ID reseeding.

Every model is a fully specified generator + seed function + sampler. No
frequency estimates, no hot/cold weighting, no read of holdout data. 
Select on first 400; validate on next 199; freeze 5 outputs from that model.
All hypothesis-family searches are retrospective: adjust for selection.
"""
from __future__ import annotations
import csv,datetime as dt,hashlib,itertools,json,math,random,sys
from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
ROOT=Path(__file__).resolve().parent
P=math.comb(35,5)
LIMIT24=(1<<24)//P*P
LIMIT32=(1<<32)//P*P
M32=(1<<32)-1;M64=(1<<64)-1
TZ=ZoneInfo('Europe/Athens')

def unrank(r):
    assert 0<=r<P
    out=[]; lo=1
    for j in range(5):
        for n in range(lo,36):
            count=math.comb(35-n,4-j) if 35-n>=4-j else 0
            if r<count:
                out.append(n);lo=n+1;break
            r-=count
        else:raise AssertionError
    return tuple(out)

def gen(kind,seed):
    if kind=='mt19937_python':
        rng=random.Random(seed)
        while True:yield rng.getrandbits(32)
    elif kind=='numerical_lcg32':
        x=seed&M32
        while True:
            x=(1664525*x+1013904223)&M32;yield x
    elif kind=='ansi_lcg32_fullword':
        x=seed&M32
        while True:
            x=(1103515245*x+12345)&M32;yield x
    elif kind=='msvc_rand15':
        x=seed&M32
        while True:
            x=(214013*x+2531011)&M32;yield (x>>16)&0x7fff
    elif kind=='xorshift32':
        x=seed&M32
        while True:
            x^=(x<<13)&M32;x^=x>>17;x^=(x<<5)&M32;yield x&M32
    elif kind=='xorshift64star':
        x=seed&M64
        while True:
            x^=x>>12;x^=(x<<25)&M64;x^=x>>27;x&=M64
            yield (x*2685821657736338717&M64)>>32
    elif kind=='splitmix64':
        x=seed&M64
        while True:
            x=(x+0x9e3779b97f4a7c15)&M64
            z=x;z=(z^(z>>30))*0xbf58476d1ce4e5b9&M64
            z=(z^(z>>27))*0x94d049bb133111eb&M64
            yield (z^(z>>31))>>32
    elif kind=='pcg32_fixed_stream':
        state=seed&M64;inc=1442695040888963407
        while True:
            old=state
            state=(old*6364136223846793005+inc)&M64
            xorshifted=(((old>>18)^old)>>27)&M32
            rot=old>>59
            yield ((xorshifted>>rot)|(xorshifted<<((-rot)&31)))&M32
    else:raise ValueError(kind)

def sample(kind,seed,mode):
    g=gen(kind,seed)
    if mode=='rank32_rejection':
        for _ in range(100):
            raw=next(g)
            if raw<LIMIT32:return unrank(raw%P)
        raise RuntimeError('sampling cap')
    if mode=='combinadic24':
        bytebuf=bytearray()
        for _ in range(100):
            while len(bytebuf)<3:bytebuf.extend(next(g).to_bytes(4,'big'))
            raw=int.from_bytes(bytebuf[:3],'big');del bytebuf[:3]
            if raw<LIMIT24:return unrank(raw%P)
        raise RuntimeError('sampling cap')
    if mode=='unique_mod35':
        vals=[];seen=set()
        for _ in range(100):
            n=next(g)%35+1
            if n not in seen:seen.add(n);vals.append(n)
            if len(vals)==5:return tuple(sorted(vals))
        raise RuntimeError('sampling cap')
    if mode=='fisher_yates5_modulo':
        balls=list(range(1,36))
        for i in range(5):
            j=i+next(g)%(35-i)
            balls[i],balls[j]=balls[j],balls[i]
        return tuple(sorted(balls[:5]))
    if mode=='fisher_yates5_unbiased':
        balls=list(range(1,36))
        for i in range(5):
            bound=35-i;limit=(1<<32)//bound*bound
            for _ in range(100):
                raw=next(g)
                if raw<limit:break
            else:raise RuntimeError('sampling cap')
            j=i+raw%bound;balls[i],balls[j]=balls[j],balls[i]
        return tuple(sorted(balls[:5]))
    raise ValueError(mode)

def metadata(row):
    day=dt.date.fromisoformat(row['date'])
    hour,minute=map(int,row['time'].split(':'))
    sec=int(dt.datetime(day.year,day.month,day.day,hour,minute,tzinfo=TZ).timestamp())
    return {'id':int(row['draw_id']),'second':sec,'minute':sec//60,
            'hour':sec//3600,'day':day.toordinal(),'yyyymmdd':day.year*10000+day.month*100+day.day,
            'yyyymmddhh':(day.year*10000+day.month*100+day.day)*100+hour}

def seedspecs():
    ss=[('draw_id',0),('epoch_second_xor_draw_id',0),('epoch_second_plus_draw_id',0),('yyyymmdd',0),('yyyymmddhh',0)]
    ss += [('epoch_second',v) for v in [-3600,-120,-60,-1,0,1,60,120,3600]]
    ss += [('epoch_minute',v) for v in [-60,-1,0,1,60]]
    ss += [('epoch_hour',v) for v in [-1,0,1]]
    ss += [('ordinal_day',v) for v in [-1,0,1]]
    ss += [('draw_id_shift',v) for v in [-1,1]]
    return ss

def make_seed(m,stype,delta):
    return {
      'draw_id':m['id'],
      'epoch_second_xor_draw_id':m['second']^m['id'],
      'epoch_second_plus_draw_id':m['second']+m['id'],
      'yyyymmdd':m['yyyymmdd'],
      'yyyymmddhh':m['yyyymmddhh'],
      'epoch_second':m['second']+delta,
      'epoch_minute':m['minute']+delta,
      'epoch_hour':m['hour']+delta,
      'ordinal_day':m['day']+delta,
      'draw_id_shift':m['id']+delta,
    }[stype]

def asmask(t):
    m=0
    for n in t:m|=1<<(n-1)
    return m

def future_meta(last,count=5):
    day=dt.date.fromisoformat(last['date']);time=last['time'];draw=int(last['draw_id'])
    result=[]
    for _ in range(count):
        if time=='15:00':time='19:00'
        else:day+=dt.timedelta(days=1);time='15:00'
        draw+=1
        result.append({'draw_id':str(draw),'date':day.isoformat(),'time':time})
    return result

def audit(train_path,calibration=1000):
    rows=list(csv.DictReader(open(train_path,newline='')))
    assert len(rows)==599
    assert [int(r['draw_id']) for r in rows]==list(range(13754,14353))
    times=[metadata(r) for r in rows];actual=[tuple(int(r[f's{i}']) for i in range(1,6)) for r in rows]
    labels=np.asarray([asmask(t) for t in actual],dtype=np.uint64)
    gens=['numerical_lcg32','ansi_lcg32_fullword','msvc_rand15','xorshift32','xorshift64star','splitmix64','pcg32_fixed_stream','mt19937_python']
    samplers=['rank32_rejection','combinadic24','unique_mod35','fisher_yates5_modulo','fisher_yates5_unbiased']
    configs=[];predictions=[];matches=[]
    for prng in gens:
      for sname,offset in seedspecs():
       seedlist=[make_seed(m,sname,offset) for m in times]
       for sampler in samplers:
        masks=[];maxcost=0
        for seed in seedlist:
            try:ticket=sample(prng,seed,sampler)
            except RuntimeError:
                ticket=() ;maxcost+=1
            masks.append(asmask(ticket))
        if maxcost:
            # Reject configurations that cannot safely produce five numbers.
            continue
        pm=np.asarray(masks,dtype=np.uint64)
        overlaps=np.bitwise_count(np.bitwise_and(labels,pm)).astype(np.uint8)
        hit400=int(overlaps[:400].sum());hit199=int(overlaps[400:].sum())
        exact400=int((pm[:400]==labels[:400]).sum())
        exact199=int((pm[400:]==labels[400:]).sum())
        configurations={'prng':prng,'seed_type':sname,'seed_offset':offset,'sampler':sampler,
                      'hits_select400':hit400,'hits_validation199':hit199,
                      'exact_select400':exact400,'exact_validation199':exact199,
                      'hits_full599':hit400+hit199,
                      'exact_full599':exact400+exact199}
        configs.append(configurations);predictions.append(pm)
    if not configs:raise RuntimeError('no models')
    predictions=np.stack(predictions)
    # Selection metric is explicitly first-400 total hits, ties deterministic by stable iteration order.
    scores=np.asarray([c['hits_select400'] for c in configs])
    winner=int(scores.argmax());selected=configs[winner]
    rng=np.random.default_rng(20261030)
    maxima=[];validation=[]
    for rep in range(calibration):
        rand_index=np.argpartition(rng.random((400,35)),4,axis=1)[:,:5]
        bits=np.left_shift(np.uint64(1),rand_index.astype(np.uint64))
        randmask=np.bitwise_or.reduce(bits,axis=1)
        hits=np.bitwise_count(np.bitwise_and(predictions[:,:400],randmask)).sum(axis=1)
        maxima.append(int(hits.max()))
    pmax=(1+sum(n>=int(scores[winner]) for n in maxima))/(calibration+1)
    # Place in validation records WITHOUT letting validation choose the winner.
    last=rows[-1];forecast_rows=future_meta(last)
    forecasts=[]
    for row in forecast_rows:
        m=metadata(row);seed=make_seed(m,selected['seed_type'],selected['seed_offset'])
        ticket=sample(selected['prng'],seed,selected['sampler'])
        forecasts.append({'draw_id':int(row['draw_id']),'date':row['date'],'time':row['time'],
                          'numbers':list(ticket),'seed':str(seed)})
    result={'source':Path(train_path).name,'dataset_sha256':hashlib.sha256(Path(train_path).read_bytes()).hexdigest(),
      'selection_count':400,'validation_count':199,'test_count':5,'family_count':len(configs),
      'selection_rule':'max first-400 sum of five-number overlaps; stable enumeration ties; only train data',
      'selection_winner':selected,'selection_null_calibration':{
       'repetitions':calibration,'generator_seed':20261030,
       'p_max_corrected':pmax,'null_max_hits_mean':float(np.mean(maxima)),
       'null_max_hits_95pct':float(np.quantile(maxima,.95)),
       'observed_max_hits':int(scores[winner])},
      'validation_uniform_expected_hits':199*25/35,
      'validation_expected_exact':199/P,
      'full_uniform_expected_hits':599*25/35,
      'top_selection_candidates':sorted(configs,key=lambda x:x['hits_select400'],reverse=True)[:12],
      'max_exact_any_config':max(x['exact_full599'] for x in configs),
      'num_models_with_two_or_more_exact':sum(x['exact_full599']>=2 for x in configs),
      'max_hits_full599_posthoc':max(x['hits_full599'] for x in configs),
      'forecasts':forecasts,
      'conclusion':'family selection is exploratory; a seed-derived model is not recovered production RNG without repeatable validation'}
    return result

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--train',default=str(ROOT/'train_599.csv'))
    ap.add_argument('--out',default=str(ROOT/'timestamp_scan_results.json'))
    ap.add_argument('--calibration',type=int,default=1000)
    a=ap.parse_args();result=audit(a.train,a.calibration)
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['top_selection_candidates']},indent=2))
