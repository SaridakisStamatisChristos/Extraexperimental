import subprocess,pathlib,json,time
r=pathlib.Path(__file__).parent
chunks=[(0,5000),(5000,5000),(10000,5000),(15000,5000),(20000,5000),(25000,4791)]
procs=[]
for off,n in chunks:
 log=(r/f'high8run_{off:05d}.log').open('w')
 cmd=[str(r/'shuffle_inverse32_high_8obs'),str(r/'real_unordered.csv'),str(r/f'high_stage2_{off:05d}.csv'),str(n),'4','100','100',str(off),'1',str(r/'high_unresolved_from_seven.csv')]
 p=subprocess.Popen(cmd,cwd=r,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 procs.append({'offset':off,'triples':n,'pid':p.pid})
(r/'high_stage2_processes.json').write_text(json.dumps({'launch_unix':time.time(),'processes':procs},indent=2))
print(procs)
