import subprocess, pathlib, time, json
root=pathlib.Path(__file__).parent
input_path=str(root/'real_unordered.csv')
chunks=[(0,5000),(5000,5000),(10000,5000),(15000,5000),(20000,5000),(25000,4791)]
procs=[]
for off,n in chunks:
    log=open(root/f'run_{off:05d}.log','w')
    argv=[str(root/'shuffle_inverse32'),input_path,str(root/f'full_{off:05d}.csv'),str(n),'4','100','100',str(off),'1']
    p=subprocess.Popen(argv,cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    procs.append({'offset':off,'triples':n,'pid':p.pid,'argv':argv})
(root/'full_search_processes.json').write_text(json.dumps({'launch_unix':time.time(),'processes':procs},indent=2))
print(json.dumps(procs,indent=2))
