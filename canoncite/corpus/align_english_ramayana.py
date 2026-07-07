import json, re, unicodedata
from difflib import SequenceMatcher
from collections import Counter

ROOT="/Volumes/Data/Pralia-labs/shastra - Scripture RAG/canoncite/data/corpora/ramayana"
ASH=ROOT+"/raw/english/AshuVj_Valmiki_Ramayan_Shlokas.json"
CORP=ROOT+"/corpus_index.jsonl"
SCR="/private/tmp/claude-501/-Volumes-Data-Pralia-labs/f2322f97-e15c-411c-8505-2cca93e883bf/scratchpad"

def sig(s):
    if not s: return ''
    s=unicodedata.normalize('NFD',s.lower())
    s=''.join(c for c in s if not unicodedata.combining(c))
    s=re.sub(r'[^a-z]','',s).replace('h','')
    s=re.sub(r'[mn]','n',s); s=re.sub(r'(.)\1+',r'\1',s)
    return s
kmap={'Bala Kanda':1,'Ayodhya Kanda':2,'Aranya Kanda':3,'Kishkindha Kanda':4,
      'Sundara Kanda':5,'Yuddha Kanda':6,'Uttara Kanda':7}

ours_by_k={k:[] for k in range(1,8)}; ours_all=[]
with open(CORP) as f:
    for line in f:
        e=json.loads(line)
        rec={'id':e['id'],'k':e['kanda'],'sig':sig(e['transliteration'])}
        ours_by_k[e['kanda']].append(rec); ours_all.append(rec)
ash_by_k={k:[] for k in range(1,8)}
for e in json.load(open(ASH)):
    k=kmap[e['kanda']]
    ash_by_k[k].append({'sig':sig(e.get('transliteration','')),
                        'en':(e.get('explanation') or '').strip(),
                        'aid':f"{k}.{e['sarga']}.{e['shloka']}"})
for k in ash_by_k: ash_by_k[k].sort(key=lambda r:(int(r['aid'].split('.')[1]),int(r['aid'].split('.')[2])))

def ratio(a,b):
    if not a or not b: return 0.0
    return SequenceMatcher(None,a,b).ratio()

MATCH=0.86; HIGH=0.97
results={}; conf_ct=Counter()

for k in range(1,8):
    A=ours_by_k[k]; B=ash_by_k[k]
    # global signature uniqueness within kanda
    ca=Counter(a['sig'] for a in A); cb=Counter(b['sig'] for b in B)
    bidx={}
    for jj,b in enumerate(B):
        if cb[b['sig']]==1: bidx[b['sig']]=jj
    # anchors: unique-unique exact, monotonic in j
    raw=[]
    for ii,a in enumerate(A):
        s=a['sig']
        if s and ca[s]==1 and s in bidx:
            raw.append((ii,bidx[s]))
    # enforce strictly increasing j (longest increasing subsequence by j, simple greedy)
    anchors=[]; lastj=-1
    for ii,jj in raw:
        if jj>lastj:
            anchors.append((ii,jj)); lastj=jj
    # emit anchors (high)
    for ii,jj in anchors:
        if B[jj]['en']:
            results[A[ii]['id']]=(B[jj]['en'],B[jj]['aid'],'high',1.0)
            conf_ct['high']+=1
    # gap fill
    sent=[(-1,-1)]+anchors+[(len(A),len(B))]
    for (i0,j0),(i1,j1) in zip(sent,sent[1:]):
        gA=range(i0+1,i1); gB=list(range(j0+1,j1))
        if not gB: continue
        ptr=0
        for ii in gA:
            sa=A[ii]['sig']
            best=-1; bestr=0.0
            for t in range(ptr,len(gB)):
                jj=gB[t]; r=ratio(sa,B[jj]['sig'])
                if r>bestr: bestr=r; best=t
                if r>=0.999: break
            if best>=0 and bestr>=MATCH:
                jj=gB[best]
                if B[jj]['en'] and A[ii]['id'] not in results:
                    c='high' if bestr>=HIGH else 'medium'
                    results[A[ii]['id']]=(B[jj]['en'],B[jj]['aid'],c,round(bestr,3))
                    conf_ct[c]+=1
                ptr=best+1

SRC_URL="https://raw.githubusercontent.com/AshuVj/Valmiki_Ramayan_Dataset/main/data/Valmiki_Ramayan_Shlokas.json"
out=ROOT+"/text_en_supplement.jsonl"
ids_sorted=sorted(results, key=lambda x:tuple(int(p) for p in x.split('.')))
with open(out,'w') as f:
    for oid in ids_sorted:
        en,aid,conf,r=results[oid]
        row={"id":oid,"text_en":en,"translation_source":"IITK","source_url":SRC_URL,
             "align_confidence":conf,"iitk_id":aid,"align_ratio":r,
             "translation_provenance":"IIT-Kanpur GitaSupersite (valmiki.iitk.ac.in) running English translation, via MIT-licensed mirror AshuVj/Valmiki_Ramayan_Dataset; aligned to Baroda Critical Edition id by verse-content matching"}
        f.write(json.dumps(row,ensure_ascii=False)+"\n")

kid_total=Counter(r['k'] for r in ours_all)
covk=Counter(int(o.split('.')[0]) for o in results)
kn={1:'Bala',2:'Ayodhya',3:'Aranya',4:'Kishkindha',5:'Sundara',6:'Yuddha',7:'Uttara'}
print("TOTAL:",len(ours_all)," aligned:",len(results),f"{100*len(results)/len(ours_all):.1f}%")
print("high:",conf_ct['high']," medium:",conf_ct['medium'])
for k in range(1,8):
    print(f"  {k} {kn[k]:11s} {covk[k]}/{kid_total[k]} = {100*covk[k]/kid_total[k]:.1f}%")
json.dump({"total":len(ours_all),"aligned":len(results),"high":conf_ct['high'],"medium":conf_ct['medium'],
           "per_kanda":{k:[covk[k],kid_total[k]] for k in range(1,8)}}, open(SCR+"/stats.json","w"))
