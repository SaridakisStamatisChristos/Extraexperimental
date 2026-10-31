#!/usr/bin/env python3
"""Historical exact model-specific bounded skip audit on first 300 frozen ranks.

The input is the previously committed 300-rank transcription of GitHub blob
`eff4bdcb94a67bad95dd1a8e8da0e61354746d15`, not a new independent
canonical CSV download. Repo checkout required for full SHA-256 source audit.
"""
from pathlib import Path
import argparse,json,time,hashlib
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent / "phase3_rank"))
from rank_inverse import MODELS,combination_unrank,N
from variable_rejection import recover_bounded

def main():
 p=argparse.ArgumentParser();p.add_argument('--ranks',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--max-skips',type=int,default=1)
 p.add_argument('--max-paths',type=int,default=None)
 a=p.parse_args()
 raw=a.ranks.read_text().strip();ranks=[int(x) for x in raw.split(',') if x.strip()]
 if len(ranks)!=300 or not all(0<=v<N for v in ranks):raise ValueError('expected exactly 300 ranks in 0..N-1')
 if ranks[0]!=238681 or ranks[1]!=229880:raise ValueError('first ranks mismatch')
 tickets=list(map(combination_unrank,ranks)); results=[]
 for name in MODELS:
  m=MODELS[name]
  for gap in (0,1,2):
   res=recover_bounded(m,tickets,gap=gap,max_skips=a.max_skips,max_paths=a.max_paths)
   results.append({key:val for key,val in res.items() if key!='seconds'} | {'seconds':res['seconds']})
   print(f'{name} gap={gap}: {res["status"]}, {res["paths_tested"]}/{res["total_bounded_paths"]} paths, rankdef={res.get("rank_deficient_paths",0)}, {res["seconds"]}s',flush=True)
 obj={'source':'phase3_rank/real_first300_ranks.csv (GitHub transcription)','source_sha256':hashlib.sha256(a.ranks.read_bytes()).hexdigest(),
      'source_blob_sha':'eff4bdcb94a67bad95dd1a8e8da0e61354746d15',
      'source_provenance_limitation':'300 ranks provided in prior Phase 3A artifact; full canonical CSV not independently checked here',
      'draw_ids':'10832..11131','models':results,
      'overall_scope':'single-word lex-rank uniform rejection with <= max-skips, one persistent state and fixed gap; no reseed'}
 a.output.write_text(json.dumps(obj,indent=2)+'\n')
if __name__=='__main__':main()
