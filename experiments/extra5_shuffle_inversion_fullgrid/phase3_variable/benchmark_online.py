#!/usr/bin/env python3
"""Reproduce exactly the Phase 3C bounded-prefix tests; no full-library search."""
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path
from rank_inverse import MODELS, combination_unrank, N
from online_path_solver import recover_online


def run(prefix=60, max_skips=4, gaps=(0,1,2), out=None):
    path=Path(__file__).resolve().parent.parent/'phase3_rank'/'real_first300_ranks.csv'
    raw=path.read_bytes()
    ranks=[int(x) for x in raw.decode().strip().split(',')]
    if len(ranks)!=300 or ranks[:2]!=[238681,229880] or any(not 0<=x<N for x in ranks):
        raise ValueError('rank fixture mismatch')
    tickets=[combination_unrank(r) for r in ranks]
    results=[]
    for gap in gaps:
        ans=recover_online(MODELS['marsaglia128'],tickets,prefix_length=prefix,
                           gap=gap,max_prefix_skips=max_skips)
        results.append(ans)
        print(f'gap={gap} status={ans["status"]} counted={ans["pruned_leaf_path_multiplicity"]}/'
              f'{ans["total_prefix_paths"]} nodes={ans["nodes_visited"]} seconds={ans["elapsed_seconds"]}',flush=True)
        if out is not None:
            obj={'version':'phase3c-1','python':sys.version,'platform':platform.platform(),
                 'data':'preserved first300 from Phase3A; ranks cross-checked with GitHub main blob eff4bdcb94a67bad95dd1a8e8da0e61354746d15',
                 'fixture_sha256':hashlib.sha256(raw).hexdigest(),'results':results}
            Path(out).write_text(json.dumps(obj,indent=2)+'\n')
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--prefix',type=int,default=60)
    p.add_argument('--max-skips',type=int,default=4)
    p.add_argument('--gaps',type=int,nargs='+',default=[0,1,2])
    p.add_argument('--output',default='PHASE3C_RESULTS.json')
    args=p.parse_args()
    run(args.prefix,args.max_skips,args.gaps,args.output)
