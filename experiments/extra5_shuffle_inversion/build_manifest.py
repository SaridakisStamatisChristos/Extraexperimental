import hashlib,json,platform,subprocess
from pathlib import Path
p=Path(__file__).resolve().parent
tracked=sorted(v for v in p.iterdir() if v.is_file() and v.suffix in ('.py','.cpp','.sh','.md','.csv','.json'))
q={'date':'2026-10-30','dataset_sha256':'61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307',
 'python':platform.python_version(),'compiler':subprocess.run(['c++','--version'],capture_output=True,text=True).stdout.splitlines()[0],
 'files':{v.name:{'bytes':v.stat().st_size,'sha256':hashlib.sha256(v.read_bytes()).hexdigest()} for v in tracked if v.name!='MANIFEST.json'}}
(p/'MANIFEST.json').write_text(json.dumps(q,indent=2)+'\n')
