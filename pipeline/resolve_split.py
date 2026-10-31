import json,re,unicodedata,urllib.request,urllib.parse,time,csv,sys
def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    s=s.replace('&',' and ')
    return re.sub(r'[^a-z0-9]+','',s)
def dz(q,kind='album',limit=10):
    url=f'https://api.deezer.com/search/{kind}?'+urllib.parse.urlencode({'q':q,'limit':limit})
    for i in range(4):
        try:
            d=json.load(urllib.request.urlopen(url,timeout=20))
            if 'error' in d: time.sleep(2); continue
            return d.get('data',[])
        except Exception as e: time.sleep(2)
    return []
years=json.load(open('years_ocr.json'))
csvsplit={}
for r in csv.DictReader(open('/mnt/user-data/uploads/Albums_brot/best_albums_by_year.csv')):
    csvsplit[(int(r['Year']),norm(r['Artist']+r['Album']))]=r['Artist']
out=[]
for y,d in sorted(years.items()):
    for rank,text in d['items']:
        text=text.strip()
        words=text.split()
        cands=set(norm(' '.join(words[:k])) for k in range(1,len(words)))
        guess=None;src=None
        # deezer artist search on prefixes is costly; use album search on full text
        res=dz(text.split(' + ')[0])
        for r in res:
            a=norm(r['artist']['name'])
            for k in range(1,len(words)):
                if norm(' '.join(words[:k]))==a or norm(' '.join(words[:k]))=='the'+a or 'the'+norm(' '.join(words[:k]))==a:
                    if guess is None or k>guess: guess=k;src='dz'
            if guess: break
        if guess is None:
            # artist search on first words
            for k in range(min(5,len(words)-1),0,-1):
                ar=dz(' '.join(words[:k]),'artist',3)
                if any(norm(x['name']) in (norm(' '.join(words[:k])),) or norm(x['name'])=='the'+norm(' '.join(words[:k])) for x in ar):
                    guess=k;src='dzartist';break
        c=csvsplit.get((int(y),norm(text)))
        out.append(dict(year=int(y),rank=rank,text=text,k=guess,src=src,artist=' '.join(words[:guess]) if guess else None,album=' '.join(words[guess:]) if guess else None,csv_artist=c))
        o=out[-1]; flag='' if (c is None or (o['artist'] and norm(c)==norm(o['artist']))) else '  <<CSV:'+str(c)
        print(y,rank,'|',o['artist'],'|',o['album'],src,flag,flush=True)
json.dump(out,open('split.json','w'),ensure_ascii=False,indent=1)
