#!/usr/bin/env python3
"""Exact exhaustive 51^4 initial-rejection-free xorshift96 inverse audit.

Hypothetical xorshift96 (3x32 state), big-endian output words, continuous
24-bit rejection/combinadic decoder. Neither deployed RNG nor a prediction.
"""
from __future__ import annotations
import collections,hashlib,json,random,time
from pathlib import Path
from toy_inverse import P, lookup, N, LIMIT,rank,reconstruct,output,decode

IDS=list(range(14249,14257))
TICKETS=[tuple(sorted(int(lookup[i]['n'+str(j)]) for j in range(1,6))) for i in IDS]
RANKS=[rank(t) for t in TICKETS[:4]]
assert TICKETS[0]==(2,4,30,33,35)
assert (1<<24)//N==51


def raw_fifth(words):
    """Decode first accepted future raw24; inspect up to 48 bytes if necessary."""
    b=b''.join(w.to_bytes(4,'big') for w in words)
    for pos in range(0,len(b)-2,3):
        raw=int.from_bytes(b[pos:pos+3],'big')
        if raw<LIMIT:return raw,pos//3
    raise AssertionError('unexpected 48-byte rejection run')


def run():
    began=time.monotonic()
    base,_=reconstruct(RANKS)
    base_words=output(96,base,15)[3:]
    delta=[]
    for idx in range(4):
        branches=[]
        for alias in range(51):
            target=RANKS.copy();target[idx]+=alias*N
            state,_=reconstruct(target)
            words=output(96,state,15)[3:]
            branches.append(tuple(w^baseword for w,baseword in zip(words,base_words)))
        delta.append(branches)
    counts=[0]*N
    rejects=collections.Counter()
    matching=[]
    # Deliberately enumerate ALL 51^4 legal four-draw raw-word transcripts.
    for i,a in enumerate(delta[0]):
      for j,b in enumerate(delta[1]):
        ab=[x^y^z for x,y,z in zip(base_words,a,b)]
        for k,c in enumerate(delta[2]):
          abc=[x^y for x,y in zip(ab,c)]
          for l,d in enumerate(delta[3]):
            w0=abc[0]^d[0]
            raw=w0>>8
            depth=0
            if raw>=LIMIT:
                w1=abc[1]^d[1]
                raw=((w0&255)<<16)|(w1>>16)
                depth=1
                if raw>=LIMIT:
                    w2=abc[2]^d[2]
                    raw=((w1&65535)<<8)|(w2>>24)
                    depth=2
                    if raw>=LIMIT:
                        raw=w2&0xffffff
                        depth=3
                        if raw>=LIMIT:
                            raw,depth=raw_fifth([x^y for x,y in zip(abc,d)])
            r=raw%N
            counts[r]+=1;rejects[depth]+=1
            # Only need state recovery/forward verification for fifth-draw matches.
            if r==rank(TICKETS[4]):
                raw_four=[RANKS[q]+N*v for q,v in enumerate((i,j,k,l))]
                state,_=reconstruct(raw_four)
                got=[tuple(t) for t in decode(96,state,count=8)]
                assert got[:5]==TICKETS[:5], (raw_four,state,got[:5],TICKETS[:5])
                matching.append({'aliases':[i,j,k,l], 'state_hex':f'{state:024x}',
                                 'sixth_matches':got[5]==TICKETS[5],
                                 'sixth_ticket':list(got[5]),
                                 'seventh_matches':got[6]==TICKETS[6]})
    assert sum(counts)==51**4
    assert sum(rejects.values())==51**4
    assert len(set(x['state_hex'] for x in matching))==len(matching)
    # Independent forward decode randomized across all depths, with deterministic seed.
    rng=random.Random(240101)
    checked=0
    for _ in range(600):
        aliases=[rng.randrange(51) for _ in range(4)]
        raw_four=[r+a*N for r,a in zip(RANKS,aliases)]
        state,_=reconstruct(raw_four)
        forward=[tuple(t) for t in decode(96,state,count=6)]
        assert forward[:4]==TICKETS[:4]
        checked+=1
    out={
      'model':'toy xorshift96, continuous big-endian 32-bit output, 24-bit rejection modulo lexicographic combinadic',
      'dataset':'extra5_authoritative_2026.csv',
      'dataset_sha256':hashlib.sha256((P/'extra5_authoritative_2026.csv').read_bytes()).hexdigest(),
      'first_train_id':IDS[0], 'last_train_id':IDS[3],
      'train_tickets':[list(x) for x in TICKETS[:4]],
      'raw_fits_exhaustive':51**4,
      'fifth_ticket_support':sum(bool(c) for c in counts),
      'fifth_ticket_min_multiplicity':min(counts),
      'fifth_ticket_max_multiplicity':max(counts),
      'fifth_rejection_counts':dict(sorted(rejects.items())),
      'known_fifth_id':IDS[4], 'known_fifth_ticket':list(TICKETS[4]),
      'fifth_matching_states':len(matching),
      'sixth_id':IDS[5], 'sixth_actual_ticket':list(TICKETS[5]),
      'sixth_matching_states_given_first_five':sum(m['sixth_matches'] for m in matching),
      'seventh_id':IDS[6], 'seventh_actual_ticket':list(TICKETS[6]),
      'seventh_matching_states_given_first_six':sum(m['sixth_matches'] and m['seventh_matches'] for m in matching),
      'state_witnesses':matching,
      'forward_check_sample':checked,
      'elapsed_seconds':round(time.monotonic()-began,3),
      'status':'RETROSPECTIVE; toy generator; fixed zero-rejection first four branch only; not physical RNG identification',
    }
    target=P/'exhaustive_six_results.json'
    target.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='state_witnesses'},indent=2))
    return out
if __name__=='__main__':run()
