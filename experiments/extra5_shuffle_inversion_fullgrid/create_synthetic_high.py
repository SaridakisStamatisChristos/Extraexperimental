import csv
from pathlib import Path
from independent_verify import expected_allowed
ROOT=Path(__file__).resolve().parent
MASK=0xffffffff
seeds={(13,17,5):0x89ABCDEF,(5,17,13):0x9A876543,(7,9,13):0x6A5F1234}
def step(x,a,b,c):
 x^=(x<<a)&MASK;x^=x>>b;x^=(x<<c)&MASK
 return x&MASK
for (a,b,c),seed in seeds.items():
 for stride in (5,7):
  state=seed
  p=ROOT/f'synthetic_high_{a}_{b}_{c}_stride{stride}.csv'
  with p.open('w',newline='') as f:
   out=csv.writer(f);out.writerow(['index','ticket_mask','allowed_fourth_mask'])
   for d in range(60):
    remaining=list(range(1,36));chosen=[]
    for z in range(5):
     state=step(state,a,b,c)
     i=(state*len(remaining))>>32
     chosen.append(remaining.pop(i))
    for extra in range(stride-5):state=step(state,a,b,c)
    ticket=sum(1<<(x-1) for x in chosen)
    out.writerow([d,ticket,expected_allowed(ticket)])
  print(p)
