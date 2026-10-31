#!/usr/bin/env python3
"""Package completed experiments with a SHA256 manifest and CRC verification."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile,ZIP_DEFLATED
import json

ROOT=Path(__file__).resolve().parent
DIRECT=[
 'README.md','REPORT.md','RESEARCH_RESULTS.json','audit_console.txt','last_tests.log',
 'shuffle_inverse32.cpp','shuffle_inverse32_8obs.cpp',
 'shuffle_inverse32_high.cpp','shuffle_inverse32_high_8obs.cpp',
 'maximal_period32.cpp','independent_verify.py','audit_results.py',
 'test_lab.py','create_synthetic_high.py','smt_inverse64.py',
 'build_bundle.py','start_full_search.py','start_stage2.py',
 'start_high_full.py','start_high_stage2.py',
 'real_unordered.csv','extra5_2022_2026_authoritative.csv',
 'primitive_triples.csv','primitive_models.csv',
 'unresolved_from_seven.csv','high_unresolved_from_seven.csv',
 'high_primitive_all.csv',
 'smt_synth10.json','smt_synth35.json','smt_real35.json',
 'smt_synth10.smt2','smt_synth35.smt2','smt_real35.smt2',
 'synthetic_xorshift64_13_7_17_gap0.csv'
]
GLOBS=[
 'full_*.csv','stage2_*.csv','high_full_*.csv','high_stage2_*.csv',
 'synthetic_xorshift32_*_stride*.csv',
 'synthetic_*_stride*_recovery.csv',
 'synthetic_high_*_stride*.csv',
 'synthetic_high_*_stride*_recovered.csv'
]
files={ROOT/name for name in DIRECT}
for pattern in GLOBS:files.update(ROOT.glob(pattern))
if not all(p.is_file() for p in files):raise SystemExit('Missing required files')
manifest={p.name:{'bytes':p.stat().st_size,'sha256':sha256(p.read_bytes()).hexdigest()} for p in sorted(files)}
(ROOT/'MANIFEST.json').write_text(json.dumps({
 'project':'EXTRA5 Exact Shuffle-Invariant Inverse-State Research',
 'created':'2026-10-30',
 'status':'NO_PRODUCTION_RNG_RECOVERED',
 'files':manifest
},indent=2))
files.add(ROOT/'MANIFEST.json')
out=ROOT.parent/'EXTRA5_ShuffleInvariant_Exact_Inversion_2026_10_30.zip'
with ZipFile(out,'w',ZIP_DEFLATED,compresslevel=8) as zipout:
 for path in sorted(files):zipout.write(path,arcname='extra5_shuffle_inverse/'+path.name)
with ZipFile(out) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(files)
print('bundle',out,'files',len(files),'bytes',out.stat().st_size,'sha256',sha256(out.read_bytes()).hexdigest())
