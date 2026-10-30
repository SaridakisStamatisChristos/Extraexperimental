"""Prepare independent chronological experiment on 3D set/order/time variables."""
import csv, datetime as dt, hashlib, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'extra5_2022_2026_authoritative.csv'
if not SRC.exists():SRC=Path('/mnt/data/extra5_five_year/extra5_2022_2026_authoritative.csv')
assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307'

def p_rank(p):
    remaining=list(range(5)); rank=0
    for j,x in enumerate(p):
        pos=remaining.index(x);rank+=pos*math.factorial(4-j);remaining.pop(pos)
    return rank

def p_unrank(rank):
    remaining=list(range(5));out=[]
    for j in range(5):
        d=math.factorial(4-j);q,rank=divmod(rank,d);out.append(remaining.pop(q))
    return out

def main():
    assert all(p_rank(p_unrank(i))==i for i in range(120))
    rows=list(csv.DictReader(SRC.open()))
    assert len(rows)==3526
    out=[]
    for k,row in enumerate(rows):
        nums=[int(row['n'+str(i)]) for i in range(1,6)]
        sortednums=sorted(nums)
        perm=tuple(sortednums.index(x) for x in nums)
        day=dt.date.fromisoformat(row['date'])
        res={
            'draw_id':int(row['draw_id']), 'year':day.year, 'date_ordinal':day.toordinal(),
            'time_slot':0 if row['time']=='15:00' else 1,
            'set_rank':int(row['lex_rank']), 'sum':sum(nums), 'min':min(nums),
            'max':max(nums), 'even_count':sum(x%2==0 for x in nums),
            'perm_rank':p_rank(perm), 'perm_parity':sum(perm[i]>perm[j] for i in range(5) for j in range(i+1,5))%2,
            'n1':nums[0],'n2':nums[1],'n3':nums[2],'n4':nums[3],'n5':nums[4],
            's1':sortednums[0],'s2':sortednums[1],'s3':sortednums[2],'s4':sortednums[3],'s5':sortednums[4],
            'prev_set_rank':int(rows[k-1]['lex_rank']) if k else -1,
            'prev_perm_rank':out[k-1]['perm_rank'] if k else -1,
            'prev_sum':out[k-1]['sum'] if k else -1,
            'prev2_set_rank':out[k-2]['set_rank'] if k>1 else -1,
        }
        assert len(set(nums))==5 and all(1<=v<=35 for v in nums)
        assert res['draw_id']==10832+k
        out.append(res)
    train=out[:2192]; test=out[2192:]
    cols=list(out[0]);features=[c for c in cols if c not in ['perm_rank','perm_parity','n1','n2','n3','n4','n5']]
    # Current-set-dependent models require realized current set: these are conditional shuffle models,
    # not usable to predict lottery numbers before the draw.
    for name,record,headers in [
     ('train_labeled.csv',train,cols),
     ('future_features_only.csv',test,features),
     ('sealed/future_labels.csv',test,cols),
    ]:
        with (ROOT/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=headers);w.writeheader();w.writerows([{c:r[c] for c in headers} for r in record])
    with (ROOT/'source_manifest.json').open('w') as f:
        json.dump({'data_source':str(SRC),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
                   'train_rows':2192,'heldout_rows':1334,'current_set_feature_is_post_draw':True,
                   'all_hidden_outcome_columns': ['perm_rank','perm_parity','n1','n2','n3','n4','n5']},f,indent=2)
    print('prepare OK train',len(train),'holdout',len(test),'p distinct',len(set(r['perm_rank'] for r in out)))

if __name__ == "__main__":
    main()
