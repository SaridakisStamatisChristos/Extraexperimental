#!/usr/bin/env python3
"""Reproduce the bounded 40-case EXTRA 5 xorshift64 falsification grid.

This script intentionally does not modify historical CSVs or prediction locks.
The user supplies the checksum-verified sparse input produced by
prepare_real_subset.py. Each reported UNSAT must have a complete enumeration.
"""
import argparse
import itertools
import json
import subprocess
from pathlib import Path

def run(binary: Path, input_csv: Path, train: int = 3526):
    results = []
    for (a,b,c), direction, sampler, gap in itertools.product(
        ((13,7,17),(7,9,13)), (0,1), ('mod','high'), range(5)):
        cmd=[str(binary),str(input_csv),str(train),str(gap),
             '200000000','60',str(train),str(a),str(b),str(c),
             str(direction),'1' if sampler=='high' else '0']
        item=json.loads(subprocess.run(cmd, check=True,
                        capture_output=True, text=True).stdout)
        item['hypothesis']={'shift_a':a,'shift_b':b,'shift_c':c,
                            'direction':direction,'sampler':sampler,
                            'gap':gap}
        results.append(item)
    return results

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--binary',type=Path,required=True)
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    results=run(args.binary.resolve(),args.input.resolve())
    args.output.write_text(json.dumps(results, indent=2)+'\n')
    statuses={s:sum(r['status']==s for r in results)
              for s in ('SAT','UNSAT','UNKNOWN','SURVIVING')}
    print(json.dumps({'models':len(results),'statuses':statuses,
                      'rank63_count':sum(r['rank']==63 for r in results),
                      'all_fully_enumerated':all(
                          r['assignments_examined']==int(r['selection_domain_product'])
                          for r in results)},indent=2))

if __name__=='__main__':
    main()
