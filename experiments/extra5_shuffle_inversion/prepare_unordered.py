#!/usr/bin/env python3
import sys,csv,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from inverse_unordered_sampler import fourth_indices,make_tickets,load,xorshift32_step

def export(tickets,path):
    with open(path,'w',newline='') as f:
        w=csv.writer(f);w.writerow(['index','ticket_mask','allowed_fourth_mask'])
        for i,nums in enumerate(tickets):
            word=0
            for v in nums:word|=1<<(v-1)
            allowed=sum(1<<v for v in fourth_indices(nums))
            w.writerow([i,word,allowed])

if __name__=='__main__':
    out=Path(__file__).parent
    export(load(str(out/'extra5_2022_2026_authoritative.csv')),out/'real_unordered.csv')
    for name,seed in [('xorshift32_13_17_5',0x89abcdef),('xorshift32_5_17_13',0x9a876543),('xorshift32_7_9_13',0x6a5f1234)]:
        for stride in (5,7):
            tickets=make_tickets(name,seed,60,stride)
            export(tickets,out/f'synthetic_{name}_stride{stride}.csv')
            print(name,stride,seed,tickets[:2])
    for name,seed,mult,stride in [
        ('xorshift32_13_17_5',0x89abcdef,0x9E3779BB,5),
        ('xorshift32_5_17_13',0x9a876543,0x85EBCA6B,7),
        ('xorshift32_7_9_13',0x6a5f1234,0x2545F491,6),
    ]:
        s=seed;tickets=[]
        for t in range(60):
            remain=list(range(1,36));chosen=[]
            for k in range(stride):
                s,word=xorshift32_step(s,name)
                if k<5:chosen.append(remain.pop(((word*mult)&0xffffffff)%len(remain)))
            tickets.append(tuple(sorted(chosen)))
        export(tickets,out/f'synthetic_star_{name}_stride{stride}_mul{mult}.csv')
        print('STAR',name,seed,mult,stride,tickets[:2])
