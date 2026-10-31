#!/usr/bin/env python3
"""Reproduce a specific bounded 60-draw prefix test from frozen Phase 3A ranks."""
from pathlib import Path
import sys,argparse,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent.parent / 'phase3_rank'))
from rank_inverse import MODELS,combination_unrank,N
from variable_rejection import recover_from_prefix

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ranks',type=Path,default=Path(__file__).resolve().parent.parent/'phase3_rank'/'real_first300_ranks.csv')
    p.add_argument('--gap',type=int,choices=(0,1,2),required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    raw=args.ranks.read_bytes();ranks=[int(x) for x in raw.decode().strip().split(',')]
    if len(ranks)!=300 or ranks[:2]!=[238681,229880] or not all(0<=r<N for r in ranks):raise ValueError('rank fixture mismatch')
    data=list(map(combination_unrank,ranks))
    result=recover_from_prefix(MODELS['marsaglia128'],data,60,gap=args.gap,max_prefix_skips=3)
    obj={'data_source':'first300 Phase3A GitHub source transcription, not independent canonical download',
         'data_sha256':hashlib.sha256(raw).hexdigest(),'source_git_blob':'eff4bdcb94a67bad95dd1a8e8da0e61354746d15',
         'model_result':result}
    args.output.write_text(json.dumps(obj,indent=2)+'\n');print(json.dumps(obj['model_result'],indent=2))
if __name__=='__main__':main()
