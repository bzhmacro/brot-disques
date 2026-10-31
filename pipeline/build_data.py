import json,re,unicodedata,urllib.request,urllib.parse,time,difflib,glob,sys
sys.path.insert(0,'.')
from overrides import O,NOSPLIT
from hidden import H
def strip_acc(s): return unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode()
def norm(s):
    s=strip_acc(s).lower().replace('&',' and ')
    s=re.sub(r'^the\s+','',s.strip())
    return re.sub(r'[^a-z0-9]+','',s)
def clean_title(t):
    t=re.sub(r'\s*[\(\[][^\)\]]*(remaster|deluxe|edition|version|expanded|anniversary|mono|stereo|bonus|reissue)[^\)\]]*[\)\]]','',t,flags=re.I)
    t=re.sub(r'\s+-\s+.*(remaster|deluxe|edition|version).*$','',t,flags=re.I)
    return t
def sim(a,b):
    a,b=norm(a),norm(b)
    if not a or not b: return 0
    if a==b: return 1
    r=difflib.SequenceMatcher(None,a,b).ratio()
    if (a in b or b in a) and min(len(a),len(b))>=4:
        r=max(r,0.85 if min(len(a),len(b))/max(len(a),len(b))>=0.45 else 0.7)
    return r
CACHE={}
try: CACHE=json.load(open('dzcache.json'))
except: pass
import os
COLLECT=os.environ.get('COLLECT')
QS=[]
def dz(q):
    if COLLECT:
        QS.append(q); return []
    if q in CACHE: return CACHE[q]
    url='https://api.deezer.com/search/album?'+urllib.parse.urlencode({'q':q,'limit':25})
    for i in range(5):
        try:
            d=json.load(urllib.request.urlopen(url,timeout=20))
            if 'error' in d: time.sleep(3); continue
            CACHE[q]=d.get('data',[]); time.sleep(0.12); return CACHE[q]
        except Exception: time.sleep(3)
    return []
ALIAS={"Double Blanc":"The Beatles","Ziggy Stardust":"The Rise and Fall of Ziggy Stardust","N°1 Record":"#1 Record","Physical Graffity":"Physical Graffiti","'77":"Talking Heads: 77","Exile On Main Street":"Exile On Main St.","Selected Ambient Works 85-92":"Selected Ambient Works 85-92"}
ARTALIAS={"Chick! Chick! Chick!":"!!!","P.I.L.":"Public Image Ltd","Them":"Them","Mothers Of Invention":"The Mothers Of Invention","Fourtet":"Four Tet","Fat Boy Slim":"Fatboy Slim","Moodyman":"Moodymann","Plastikmann":"Plastikman","Mu-ziq":"µ-Ziq","Black Dog":"The Black Dog","Black Dog Productions":"The Black Dog","St Germain":"St Germain","Neu!":"NEU!","Iggy & The Stooges":"The Stooges","The Mama's & The Papa's":"The Mamas & The Papas","Monks":"The Monks","Yardbirds":"The Yardbirds","Ruts":"The Ruts","Paul Collins' Beat":"The Beat","The Sex Pistols":"Sex Pistols","Damned":"The Damned","The Stray Cats":"Stray Cats","Dogs":"Dogs","Therapy":"Therapy?","Prodigy":"The Prodigy","The Young Marble Giants":"Young Marble Giants","The Dead Kennedys":"Dead Kennedys","The Fun Boy Three":"Fun Boy Three","Les Thugs":"Thugs","Jesus Lizard":"The Jesus Lizard","2 Many DJ's":"2manydjs","Pan Sonic":"Pan Sonic","Fela Kuti & Africa 70":"Fela Kuti","Kevin Rowland & Dexys Midnight Runners":"Dexys Midnight Runners","Julie Driscoll, Brian Auger & The Trinity":"Julie Driscoll","Julie Driscoll, Brian Auger & Trinity":"Julie Driscoll","Frank Zappa & The Mothers Of Invention":"Frank Zappa","Captain Beefheart & His Magic Band":"Captain Beefheart","DJ Krush / Toshinori Kondo":"DJ Krush","Porter Ricks / Techno Animal":"Porter Ricks","Fennesz / Vainio / Zanési":"Fennesz","Snoop Doggy Dogg":"Snoop Dogg","Kurtis Mantronik":"Kurtis Mantronik","The Jimi Hendrix Experience":"Jimi Hendrix","The Soft Machine":"Soft Machine","Bruce Joyner & The Plantations":"Bruce Joyner","Nick Cave":"Nick Cave & The Bad Seeds","Scraping Foetus Off The Wheel":"Foetus","Run DMC":"Run-DMC","John Mayall & The Bluesbreakers":"John Mayall","Lee \"Scratch\" Perry":"Lee Perry","Scott Walker & The Walker Brothers":"Scott Walker","The JB's":"The J.B.'s","Fred Wesley & The JB's":"Fred Wesley","Señor Coconut Y Su Conjunto":"Señor Coconut","Chris De Luca & Peabird":"Chris De Luca"}
def split_titles(t):
    if t in NOSPLIT: return [t]
    parts=[p.strip() for p in t.split(' + ')]
    if len(parts)>1 and all(len(re.sub(r'[^A-Za-z0-9]','',p))>=2 and not re.match(r'^\(?vol',p,re.I) for p in parts): return parts
    return [t]
def resolve(artist,title):
    a=ARTALIAS.get(artist,artist); t=ALIAS.get(title,title)
    tq=re.sub(r'[\(\)]',' ',t)
    qs=([f'artist:"{a}" album:"{tq}"', f'{a} {tq}'] if a else [tq]) 
    best=None
    for q in qs:
        for r in dz(q):
            ra=norm(r['artist']['name'])
            asim=max(sim(a,r['artist']['name']),sim(artist,r['artist']['name'])) if a else 1
            if a and len(norm(a))>=3 and (ra.startswith(norm(a)) or norm(a).startswith(ra)) and len(ra)>=3: asim=max(asim,0.9)
            if a and asim<0.85: continue
            ct=clean_title(r['title'])
            ts=max(sim(t,ct),sim(title,ct),sim(artist+' '+t,ct) if a else 0)
            if len(norm(t))>=4 and norm(ct).startswith(norm(t)): ts=max(ts,0.8)
            if not a and r['artist']['name'].lower() not in ('various artists','artistes divers','multi-interprètes'): ts-=0.1
            sc=ts+0.3*asim - (0.05 if re.search(r'live|deluxe|remaster|edition|remix|redux',r['title'],re.I) and not re.search('live',t,re.I) else 0)
            if best is None or sc>best[0]: best=(sc,ts,r)
        if best and best[1]>=0.9: break
    if best and best[1]>=(0.72 if a else 0.85):
        r=best[2]
        return dict(deezer=r['link'],cover=r.get('cover_medium'),dz_title=r['title'],dz_artist=r['artist']['name'],conf=round(best[1],2))
    return None
def links(artist,title):
    q=(artist+' '+title).strip()
    return dict(spotify='https://open.spotify.com/search/'+urllib.parse.quote(q),youtube='https://www.youtube.com/results?search_query='+urllib.parse.quote(q+' full album'))
SP={tuple(l.strip().split('|')[:2]):l.strip().split('|')[2] for l in open('spotify_hits.txt') if l.strip()}
DENY={("Paul Collins' Beat","The Beat"),("Venetian Snares","Venetian Snares"),("Prince","Parade"),("X-101","X-101")}
def mk(artist,title):
    albums=[]
    for t in split_titles(title):
        d=dict(title=t); d.update(links(artist,t)); r=None if (artist,t) in DENY else resolve(artist,t)
        if r: d.update(r)
        if (artist,t) in SP: d['spotify']='https://open.spotify.com/album/'+SP[(artist,t)]; d['spotify_exact']=True
        albums.append(d)
    return albums
split={(o['year'],o['rank']):o for o in json.load(open('split.json'))}
yo=json.load(open('years_ocr.json'))
years=[]
for y,d in yo.items():
    items=[]
    for rank,text in d['items']:
        o=split[(int(y),rank)]
        a,t=O.get((int(y),rank),(o['artist'],o['album']))
        a=a.replace('&amp;','&');t=t.replace('&amp;','&')
        if a=="!!!": a="Chick! Chick! Chick!"
        items.append(dict(rank=rank,artist=a,title=t))
    years.append(dict(year=int(y),image=d['img'],blurb=d['blurb'].replace('&amp;','&'),items=items))
for f in sorted(glob.glob('manual/19*.txt')):
    L=open(f).read().strip().split('\n'); y=int(L[0].split()[1]); bl=L[1][6:]
    items=[dict(rank=i+1,artist=l.split(' | ')[0],title=l.split(' | ')[1]) for i,l in enumerate(L[2:])]
    years.append(dict(year=y,image=None,blurb=bl,items=items))
years.sort(key=lambda x:x['year'])
n=0;miss=0
for Y in years:
    for it in Y['items']:
        it['albums']=mk(it['artist'],it['title']); n+=len(it['albums']); miss+=sum('deezer' not in a for a in it['albums'])
    print(Y['year'],flush=True)
    json.dump(CACHE,open('dzcache.json','w'))
hidden=[]
for recs,desc in H:
    hidden.append(dict(desc=desc,records=[dict(artist=a,title=t,format=f,albums=mk(a,t)) for a,t,f in recs]))
json.dump(CACHE,open('dzcache.json','w'))
json.dump(dict(years=years,hidden=hidden),open('data.json','w'),ensure_ascii=False,indent=1)
print('albums',n,'missing',miss)
if COLLECT: json.dump(sorted(set(QS)),open('queries.json','w'),ensure_ascii=False)
