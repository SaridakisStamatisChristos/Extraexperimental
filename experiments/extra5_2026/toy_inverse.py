#!/usr/bin/env python3
"""Authoritative-data xorshift inverse reconstruction. Hypothetical generator, NOT deployed RNG."""
import csv,json,math,random,pathlib,collections,hashlib
P=pathlib.Path(__file__).resolve().parent
rows=list(csv.DictReader((P/'extra5_authoritative_2026.csv').open()))
lookup={int(r['draw_id']):r for r in rows}
N=math.comb(35,5); LIMIT=(1<<24)//N*N; MASK=(1<<32)-1

def rank(ticket):
    ans=0; prev=0
    for j,n in enumerate(sorted(ticket)):
        for k in range(prev+1,n):ans+=math.comb(35-k,4-j)
        prev=n
    return ans

def unrank(r):
    out=[];lo=1
    for j in range(5):
        for n in range(lo,36):
            c=math.comb(35-n,4-j) if 35-n>=4-j else 0
            if r<c:out.append(n);lo=n+1;break
            r-=c
    return out

def step96(s):
    x=s&MASK;y=(s>>32)&MASK;z=(s>>64)&MASK
    t=x^((x<<16)&MASK);t^=t>>5;t^=(t<<1)&MASK
    nz=(t^y^z)&MASK
    return y|(z<<32)|(nz<<64),nz

def step128(s):
    x=s&MASK;y=(s>>32)&MASK;z=(s>>64)&MASK;w=(s>>96)&MASK
    t=x^((x<<11)&MASK); nw=(w^(w>>19)^t^(t>>8))&MASK
    return y|(z<<32)|(w<<64)|(nw<<96),nw

def output(kind,s,k):
    fn=step96 if kind==96 else step128
    a=[]
    for _ in range(k):s,w=fn(s);a.append(w)
    return a

def basis(kind,k=4):
    cols=[output(kind,1<<i,k) for i in range(kind)]
    return [sum(1<<i for i in range(kind) if cols[i][j]>>b&1) for j in range(k) for b in range(32)]

def eliminate(rows, bits, n):
    piv={}
    for row,bit in zip(rows,bits):
        while row:
            p=row.bit_length()-1
            if p not in piv:piv[p]=(row,bit);break
            row^=piv[p][0];bit^=piv[p][1]
        else:
            if bit:raise ValueError('inconsistent')
    s=0
    for p in sorted(piv):
        row,b=piv[p]
        if (row&s).bit_count()%2!=b:s|=1<<p
    return s,len(piv)

def decode(kind,s,count=5):
    stream=b''.join(w.to_bytes(4,'big') for w in output(kind,s,20))
    out=[]
    for i in range(0,len(stream)-2,3):
        v=int.from_bytes(stream[i:i+3],'big')
        if v<LIMIT:
            out.append(unrank(v%N))
            if len(out)==count:return out
    raise ValueError('exhausted')

def reconstruct(ranks,kind=96):
    raw=b''.join(r.to_bytes(3,'big') for r in ranks)
    words=[int.from_bytes(raw[i:i+4],'big') for i in (0,4,8)]
    bits=[w>>b&1 for w in words for b in range(32)]
    s,rank_=eliminate(basis(kind,3),bits,kind)
    return s,rank_

def run():
    ids=list(range(14249,14254))
    tickets=[tuple(sorted(int(lookup[i]['n'+str(j)]) for j in range(1,6))) for i in ids]
    assert tickets[0]==(2,4,30,33,35)
    ranks=[rank(t) for t in tickets[:4]]
    assert all(unrank(r)==list(t) for r,t in zip(ranks,tickets))
    canonical,rank96=reconstruct(ranks)
    assert rank96==96 and [tuple(t) for t in decode(96,canonical)[:4]]==tickets[:4]
    prev_ranks=[rank((2,4,30,32,35))]+ranks[1:]
    old, _=reconstruct(prev_ranks)
    assert old!=canonical
    rng=random.Random(20261030)
    predictions=collections.Counter(); fifth_matches=0; unique_states=set(); samples=3000
    for _ in range(samples):
        raw=[r+N*rng.randrange(51) for r in ranks]
        s,_=reconstruct(raw)
        assert s not in unique_states or len(unique_states)<samples
        unique_states.add(s)
        d=decode(96,s)
        assert [tuple(t) for t in d[:4]]==tickets[:4]
        ticket=tuple(d[4]); predictions[ticket]+=1
        fifth_matches+=ticket==tickets[4]
    rank3=len({})
    s128,rank128=reconstruct(ranks,128)
    assert rank128==96 and [tuple(t) for t in decode(128,s128)[:4]]==tickets[:4]
    # Test rank 128 of first four output words.
    rank4=eliminate(basis(128,4),[0]*128,128)[1]
    assert rank4==128
    # Differential property: each fourth output bit can be freely selected while first 96 bits fixed.
    # Full 128x128 map is invertible: construct arbitrary fourth word and solve all 128 bits.
    fixed=output(128,s128,3)
    for v in (0,1,0xffffffff,0x12345678,0xdeadbeef):
        words=fixed+[v]
        bits=[w>>b&1 for w in words for b in range(32)]
        state,rr=eliminate(basis(128,4),bits,128)
        assert rr==128 and output(128,state,4)==words
    report={'source':'extra5_authoritative_2026.csv','corrected_training_draw_ids':ids[:4],
            'training_tickets':[list(t) for t in tickets[:4]],'retrospective_fifth_ticket':list(tickets[4]),
            'raw_aliases_per_draw':51,'no_initial_rejection_states_xorshift96':51**4,
            'xorshift96_rank':rank96,'canonical_corrected_state_hex':f'{canonical:024x}',
            'canonical_corrected_fifth_ticket':decode(96,canonical)[4],
            'old_wrong_data_state_hex':f'{old:024x}',
            'xorshift96_alias_sample_count':samples,'distinct_sampled_states':len(unique_states),
            'distinct_fifth_tickets_in_sample':len(predictions),
            'retrospective_fifth_matches_in_sample':fifth_matches,
            'xorshift128_first_three_word_rank':rank128,'xorshift128_first_four_word_rank':rank4,
            'xorshift128_all_fifth_tickets_possible_given_first_four':'PROVED under toy generator and no-rejection branch',
            'status':'retrospective toy generator reconstruction; NOT a forecast or deployed RNG identification'}
    (P/'inverse_rebuild_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':run()
