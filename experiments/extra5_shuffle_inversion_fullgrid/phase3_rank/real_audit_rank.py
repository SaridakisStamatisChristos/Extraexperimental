#!/usr/bin/env python3
"""Local independent rank-only historical check. Source: first 300 lex ranks
from GitHub canonical 5-year CSV, blob eff4bdcb94a67bad95dd1a8e8da0e61354746d15.
Not a source checksum verification; full CSV must be independently downloaded
and SHA256-checked to certify its provenance on a later environment.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from rank_inverse import MODELS,low_forms,solve,N

def contradiction_certificate(equations, dimension):
    """Recompute exact GF(2) dependence, independently of rank_inverse.solve.
    Certificate is a 0=1 XOR of explicitly identified equations.
    """
    pivots={}
    for idx,(coeff,rhs) in enumerate(equations):
        x,v=coeff,rhs
        used=1<<idx
        while x:
            p=x.bit_length()-1
            if p not in pivots:
                pivots[p]=(x,v,used);break
            a,b,dep=pivots[p]
            x^=a;v^=b;used^=dep
        else:
            if v:
                ids=[i for i in range(idx+1) if (used>>i)&1]
                check_lhs=0;check_rhs=0
                for i in ids:
                    a,b=equations[i];check_lhs^=a;check_rhs^=b
                assert check_lhs==0 and check_rhs==1
                return {'contradiction_equation':idx,
                        'certificate_row_ids':ids,
                        'certificate_size':len(ids),
                        'checked_xor_coefficients':0,
                        'checked_xor_rhs':1}
    return None

def audit(ranks,model,gap):
    f=low_forms(model,len(ranks),gap)
    eq=[]
    for d,r in enumerate(ranks):
        if not 0<=r<N:raise ValueError('invalid rank')
        for k in range(model.proved_linear_low_bits):
            eq.append((f[d][k],(r>>k)&1))
            x=solve(eq,model.size)
            if x['status']=='UNSAT':
                certificate=contradiction_certificate(eq,model.size)
                assert certificate is not None
                return dict(model=model.name,sampler='one_word_combination_rank_modulo',gap=gap,
                            status='UNSAT',first_failing_draw=10832+d,first_failing_zero_based_index=d,
                            rank=x['rank'],equations=len(eq),
                            certificate=certificate,
                            reason='contradictory GF(2) necessary equations')
    return dict(model=model.name,sampler='one_word_combination_rank_modulo',gap=gap,
                status='UNKNOWN',rank=x['rank'],equations=len(eq))

def read_canonical(path):
    content=path.read_bytes()
    expected='61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307'
    observed=hashlib.sha256(content).hexdigest()
    if observed!=expected:raise ValueError(f'canonical dataset hash mismatch: {observed}')
    with path.open(newline='') as f:rows=list(csv.DictReader(f))
    if len(rows)!=3526:raise ValueError('wrong canonical draw count')
    from rank_inverse import combination_rank
    ranks=[]
    for i,row in enumerate(rows):
        if int(row['draw_id'])!=10832+i:raise ValueError('nonconsecutive draw ID')
        values=[int(row[f'n{k}']) for k in range(1,6)]
        rank=combination_rank(values)
        if rank!=int(row['lex_rank']):raise ValueError('stored lex rank does not match independent rank')
        ranks.append(rank)
    return ranks

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=Path(__file__).with_name('real_first300_ranks.csv'))
 p.add_argument('--canonical',type=Path,help='full original canonical CSV with SHA256 validation')
 p.add_argument('--output',type=Path,default=Path(__file__).with_name('REAL_LOCAL_AUDIT.json'))
 args=p.parse_args();ranks=read_canonical(args.canonical) if args.canonical else [int(x) for x in args.input.read_text().strip().split(',')]
 if args.canonical is None:assert len(ranks)==300
 results=[audit(ranks,m,g) for m in MODELS.values() for g in (0,1,2)]
 data={'input':str(args.canonical) if args.canonical else 'first_300_lex_ranks_from_GitHub_canonical_CSV','github_blob':'eff4bdcb94a67bad95dd1a8e8da0e61354746d15',
       'note':'Full canonical CSV SHA256 validation performed' if args.canonical else 'local fixture transcription compared against GitHub results; requires full canonical CSV SHA check later',
       'results':results}
 args.output.write_text(json.dumps(data,indent=2)+'\n')
 for item in results:print(item)
