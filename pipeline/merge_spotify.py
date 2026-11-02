"""Merge spotify_cache.json (from spfetch.py) into data/albums.json.
Run from the repo root: python3 pipeline/merge_spotify.py
Rejects matches whose artist does not really match, plus a hand-checked REJECT list;
ACCEPT overrides the artist check for verified matches."""
import json, re, unicodedata
def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().replace('&', ' and ')
    s = re.sub(r'^the\s+', '', s.strip()); return re.sub(r'[^a-z0-9]+', '', s)
src = open('pipeline/build_data.py').read()
ARTALIAS = eval(src[src.index('ARTALIAS=') + 9:].split('\n')[0])
REJECT = {("Love", "Love"), ("Tomorrow", "Tomorrow"), ("Paul Collins' Beat", "The Beat"), 
          ("Marvin Gaye", "What's Going On"), ("James Brown", "Sex Machine"), ("Massive Attack", "Blue Lines"),
          ("Small Faces", "The Small Faces"), ("The Velvet Underground", "Live 1969 vol 1 & 2"),
          ("Funkadelic", "One Nation Under A Groove"), ("Johnny Thunders & The Heartbreakers", "L.A.M.F."),
          ("Dave Clarke", "Archive 1"), ("Kruder & Dorfmeister", "K&D Sessions"), ("Guru", "Jazzmatazz"),
          ("The Temptations", "Anthology"), ("The Supremes", "Anthology"), ("The Salsoul Orchestra", "Anthology"),
          ("Einstürzende Neubauten", "Strategies Against Architecture 1+2"),
          ("Lovage", "Music To Make Love To Your Old Lady By"), ("Air", "The Virgin Suicides")}
ACCEPT = {("Public Image Limited", "Public Image"), ("A Certain General", "November's Heat")}
def artist_ok(want, got):
    ws = {norm(want), norm(ARTALIAS.get(want, want))}
    for n in (g.strip() for g in got.split(',')):
        nn = norm(n)
        for w in ws:
            if not w or nn == w: return True
            if w.startswith(nn) and len(nn) >= 4: return True
            if nn.startswith(w) and nn[len(w):].startswith('and'): return True
    return False
C = json.load(open('pipeline/spotify_cache.json'))
D = json.load(open('data/albums.json'))
n = 0
def apply(artist, a):
    global n
    r = C.get(artist + '|' + a['title'])
    if not r or (artist, a['title']) in REJECT: return
    if (artist, a['title']) not in ACCEPT and not artist_ok(artist, r['artist']): return
    a['spotify'] = r['url'].split('?')[0]; a['spotify_exact'] = True; n += 1
for Y in D['years']:
    for it in Y['items']:
        for a in it['albums']: apply(it['artist'], a)
for h in D['hidden']:
    for r in h['records']:
        for a in r['albums']: apply(r['artist'], a)
json.dump(D, open('data/albums.json', 'w'), ensure_ascii=False, indent=1)
print('spotify links applied:', n)
