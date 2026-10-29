#!/usr/bin/env python3
"""Fixed-parameter seed-only search for FOUR user-supplied EXTRA 5 drawings.

No production-operator seed, key, sampler, or RNG attribution is claimed.
Uses earlier fully enumerated synthetic candidate archives plus disjoint new
seed ranges. A candidate must output all four tickets *in order* from one
continuous state. The first-draw filter is lossless within the specified
synthetic sampler/stream semantics; successful prefixes are fully replayed.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys, time
from pathlib import Path
from extra5_multifamily_blind import FAMILIES
from extra5_multifamily_compact import stream,decode
from extra5_three_draw_seed_test import simple_seed_tickets,words
from extra5_one_draw_seed_fit import COMBINATIONS,LIMIT,rank_5of35

TICKETS=((2,4,30,32,35),(2,5,9,30,33),(10,18,21,25,29),(1,7,9,14,18))
IDS=(14249,14250,14251,14252)
CONTROLS=('splitmix64','xorshift64star','lcg64')
PREVIOUS_LIMITS={f:(400000 if f in FAMILIES[:3] else 80000 if f in FAMILIES[3:5] or f=='b-bbs' else 100000) for f in FAMILIES}
OLD_CONTROL_LIMIT=1000000


def exact_prefix(pred):
    n=0
    for ticket,actual in zip(pred,TICKETS):
        if tuple(ticket)!=actual:break
        n+=1
    return n


def historical_first_matches(archive):
    rows=[]
    families=archive['families']
    assert len(families)==len(FAMILIES)
    for family_rec in families:
        fam=family_rec['family']
        for item in family_rec.get('models',family_rec.get('fits',[])):
            seed=item['seed_index']
            raw=stream(fam,seed,128)
            pos=0;pred=[]
            for _ in TICKETS:
                t,pos=decode(raw,pos);pred.append(t)
            if pred[0]!=TICKETS[0]:raise AssertionError(f'archived match corrupted {fam}/{seed}')
            p=exact_prefix(pred)
            rows.append(dict(family=fam,seed=seed,tickets=[list(t) for t in pred],prefix=p,source='earlier full enumeration'))
    return rows


def historical_arithmetic_matches(archive):
    rows=[]
    sweeps=archive['additional_public_arithmetic_seed_sweeps']
    for fam in CONTROLS:
        assert sweeps[fam]['seeds_tested']==OLD_CONTROL_LIMIT
        for item in sweeps[fam]['candidates']:
            seed=item['seed_index'];pred=simple_seed_tickets(fam,seed,len(TICKETS))
            if pred[0]!=TICKETS[0]:raise AssertionError('archived arithmetic candidate not reproducible')
            rows.append(dict(family=fam,seed=seed,tickets=[list(t) for t in pred],prefix=exact_prefix(pred),source='earlier full enumeration'))
    return rows


def quick_first(fam,seed):
    """Get first ticket cheaply with a lossless fallback for rejected 24bit blocks."""
    raw=stream(fam,seed,6)
    try:
        ticket,_=decode(raw)
        return ticket,False
    except ValueError:
        # 24bit rejection may exhaust the 6-byte preview. Replay with ample bytes
        # so this class cannot be silently omitted from enumeration.
        try:
            return decode(stream(fam,seed,1024))[0],True
        except ValueError:
            return None,True  # unresolved finite-stream decode; counted separately


def sweep_cryptographic(scale=1,print_progress=False):
    if scale<1:raise ValueError('scale must >=1')
    result={}; all_rows=[]
    for fam in FAMILIES:
        limit=PREVIOUS_LIMITS[fam]
        lo,hi=limit,limit*(scale+1)
        t0=time.monotonic();hits=[];fallback=0;unresolved=0
        for seed in range(lo,hi):
            first,was_fallback=quick_first(fam,seed)
            fallback+=was_fallback
            if first is None:
                unresolved+=1;continue
            if first!=TICKETS[0]:continue
            raw=stream(fam,seed,128);pos=0;pred=[]
            for _ in TICKETS:
                t,pos=decode(raw,pos);pred.append(t)
            if pred[0]!=TICKETS[0]:raise AssertionError('prefix misdecode')
            hits.append(dict(family=fam,seed=seed,tickets=[list(t) for t in pred],prefix=exact_prefix(pred),source='new disjoint seed sweep'))
        all_rows.extend(hits)
        result[fam]={'range':[lo,hi], 'attempts':hi-lo,'first_exact':len(hits),
                     'exact_two':sum(t['prefix']>=2 for t in hits),
                     'exact_three':sum(t['prefix']>=3 for t in hits),
                     'exact_four':sum(t['prefix']>=4 for t in hits),
                     'preview_rejections_replayed':fallback,'unresolved_first_ticket_after_1024_bytes':unresolved,'seconds':round(time.monotonic()-t0,2)}
        if print_progress:print('CRYPTO',fam,result[fam],flush=True)
    return result,all_rows


def sweep_arithmetic(scale=1,print_progress=False):
    if scale<1:raise ValueError('scale must >=1')
    result={};all_rows=[];target_rank=rank_5of35(TICKETS[0]);MASK=(1<<64)-1
    for fam in CONTROLS:
        lo,hi=OLD_CONTROL_LIMIT,OLD_CONTROL_LIMIT*(scale+1)
        t0=time.monotonic();hits=[];fallback=0
        for seed in range(lo,hi):
            gen=words(fam,seed);head=next(gen)>>40
            if head<LIMIT:
                if head%COMBINATIONS!=target_rank:continue
            else:
                fallback+=1
                if simple_seed_tickets(fam,seed,1)[0]!=TICKETS[0]:continue
            pred=simple_seed_tickets(fam,seed,4)
            if pred[0]!=TICKETS[0]:raise AssertionError('control prefilter mismatch')
            hits.append(dict(family=fam,seed=seed,tickets=[list(t) for t in pred],prefix=exact_prefix(pred),source='new disjoint seed sweep'))
        all_rows.extend(hits)
        result[fam]={'range':[lo,hi],'attempts':hi-lo,'first_exact':len(hits),
                     'exact_two':sum(t['prefix']>=2 for t in hits),
                     'exact_three':sum(t['prefix']>=3 for t in hits),
                     'exact_four':sum(t['prefix']>=4 for t in hits),
                     'rejected_first_words_replayed':fallback,'seconds':round(time.monotonic()-t0,2)}
        if print_progress:print('ARITH',fam,result[fam],flush=True)
    return result,all_rows


def polynomial_congruence_obstruction():
    """Proof witness excluding ANY one-state integer polynomial modulo C(35,5)."""
    ranks=[rank_5of35(t) for t in TICKETS]
    modulus=COMBINATIONS
    d=math.gcd(ranks[2]-ranks[1],modulus)
    assert d==28
    assert ranks[1]%d==ranks[2]%d and ranks[2]%d!=ranks[3]%d
    return dict(encoding='0-indexed lexicographic 5/35 rank',ranks=ranks,modulus=modulus,
      obstruction_modulus=d,congruent_inputs=[ranks[1],ranks[2]],required_outputs=[ranks[2],ranks[3]],
      input_residues=[ranks[1]%d,ranks[2]%d],output_residues=[ranks[2]%d,ranks[3]%d],
      theorem='No integer-coefficient polynomial P on rank mod 324632 can map all four consecutive results via x_(t+1) = P(x_t) mod 324632.',
      proof='Because 57278 = 268706 (mod 28), polynomial congruence implies P(57278) = P(268706) (mod 28). But required outputs 268706 = 18 (mod 28), 23073 = 1 (mod 28). Contradiction.',
      scope='Only deterministic autonomous one-rank-state polynomial maps with integer coefficients under this encoding; not arbitrary internal-state or cryptographic generators')


def run(earlier_crypto,earlier_control,new_scale=1,progress=False):
    old=historical_first_matches(earlier_crypto)+historical_arithmetic_matches(earlier_control)
    assert len(old)==16,(len(old),'archive mismatch')
    assert all(x['prefix']==1 for x in old)
    cr,cr_rows=sweep_cryptographic(new_scale,progress)
    ar,ar_rows=sweep_arithmetic(new_scale,progress)
    all_rows=old+cr_rows+ar_rows
    attempted_old=sum(PREVIOUS_LIMITS.values())+3*OLD_CONTROL_LIMIT
    attempted_new=sum(v['attempts'] for v in cr.values())+sum(v['attempts'] for v in ar.values())
    out={'title':'Extra 5 four-draw strict seeded model search','research_date':'2026-10-29',
         'training_draws':[{'id':i,'numbers':list(t)} for i,t in zip(IDS,TICKETS)],
         'tested_families':list(FAMILIES)+list(CONTROLS),
         'synthetic_seed_ranges':{'previous_cryptographic':{k:[0,v] for k,v in PREVIOUS_LIMITS.items()},
                                  'new_cryptographic':{k:v['range'] for k,v in cr.items()},
                                  'previous_arithmetic':{k:[0,OLD_CONTROL_LIMIT] for k in CONTROLS},
                                  'new_arithmetic':{k:v['range'] for k,v in ar.items()}},
         'counts':{'archived_previous_seed_hypotheses':attempted_old,'new_executed_seed_hypotheses':attempted_new,
                   'distinct_total_seed_hypotheses':attempted_old+attempted_new,
                   'first_draw_exact':len(all_rows),'first_two_exact':sum(x['prefix']>=2 for x in all_rows),
                   'first_three_exact':sum(x['prefix']>=3 for x in all_rows),'all_four_exact':sum(x['prefix']==4 for x in all_rows)},
         'earlier_results_were_replayed_only_for_first_draw_matches':True,
         'new_cryptographic_family_results':cr,'new_arithmetic_family_results':ar,
         'all_exact_first_match_seed_candidates':all_rows,
         'fixed_polynomial_rank_model_impossibility':polynomial_congruence_obstruction(),
         'ideal_uniform_match_expectation':{'first':(attempted_old+attempted_new)/COMBINATIONS,
          'ordered_four':(attempted_old+attempted_new)/(COMBINATIONS**4)},
         'scope':'Only named synthetic seeds/initializations, fixed transformations, continuous stream and experimental bit-to-ticket decoder. Other parameterizations and hidden reseeding not tested.',
         'conclusion':'No algorithm/seed in this finite fixed-seed catalog recovered all four. The broader integer-polynomial one-state rank recurrence family is algebraically impossible given the four ranks.'}
    assert out['counts']['distinct_total_seed_hypotheses']==attempted_old+attempted_new
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--new-scale',type=int,default=1)
    p.add_argument('--crypto-archive',type=Path,default=Path(__file__).with_name('extra5_multifamily_blind_14250.json'))
    p.add_argument('--control-archive',type=Path,default=Path(__file__).with_name('extra5_three_draw_seed_test_results.json'))
    p.add_argument('--out',type=Path,default=Path(__file__).with_name('extra5_four_draw_search_results.json'))
    args=p.parse_args();t0=time.monotonic()
    old_crypto=json.loads(args.crypto_archive.read_text())
    old_control=json.loads(args.control_archive.read_text())
    result=run(old_crypto,old_control,args.new_scale,True)
    result['reproducibility']={'python':sys.version.split()[0], 'elapsed_seconds':round(time.monotonic()-t0,2),
      'crypto_archive_sha256':hashlib.sha256(args.crypto_archive.read_bytes()).hexdigest(),
      'control_archive_sha256':hashlib.sha256(args.control_archive.read_bytes()).hexdigest()}
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('FINAL',json.dumps({k:v for k,v in result['counts'].items()},indent=2),flush=True)

if __name__=='__main__':main()
