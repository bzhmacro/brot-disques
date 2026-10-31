import json,urllib.request,urllib.parse,time,os,sys
Q=json.load(open('queries.json',encoding='utf-8'))
C=json.load(open('dzcache_gb.json',encoding='utf-8')) if os.path.exists('dzcache_gb.json') else {}
t0=time.time()
for q in Q:
    if q in C: continue
    if time.time()-t0>150: break
    url='https://api.deezer.com/search/album?'+urllib.parse.urlencode({'q':q,'limit':25})
    try:
        d=json.load(urllib.request.urlopen(url,timeout=20))
        if 'error' in d: time.sleep(5); continue
        C[q]=[dict(title=r['title'],link=r['link'],cover_medium=r.get('cover_medium'),artist=dict(name=r['artist']['name'])) for r in d.get('data',[])]
    except Exception as e: time.sleep(2)
    time.sleep(0.11)
json.dump(C,open('dzcache_gb.json','w',encoding='utf-8'),ensure_ascii=False)
print(len(C),'/',len(Q))
