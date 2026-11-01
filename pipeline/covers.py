"""Fill missing covers in data/albums.json.
1) Albums with a direct Spotify link: Spotify oEmbed thumbnail (no auth).
2) Otherwise: MusicBrainz release-group search -> Cover Art Archive front image.
Run from repo root: python3 pipeline/covers.py   (cache: pipeline/covers_cache.json)"""
import json, os, re, time, difflib, unicodedata, urllib.request, urllib.parse, urllib.error
UA = {'User-Agent': 'brault-disques/1.0 (https://brault.bzhmacro.com)'}
CP = 'pipeline/covers_cache.json'
C = json.load(open(CP)) if os.path.exists(CP) else {}
def get(url, timeout=20):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().replace('&', ' and ')
    s = re.sub(r'^the\s+', '', s.strip()); return re.sub(r'[^a-z0-9]+', '', s)
def sim(a, b):
    a, b = norm(a), norm(b)
    if not a or not b: return 0
    if a == b: return 1
    r = difflib.SequenceMatcher(None, a, b).ratio()
    if (a in b or b in a) and min(len(a), len(b)) >= 4: r = max(r, 0.85)
    return r
def spotify_cover(url):
    try:
        d = json.load(get('https://open.spotify.com/oembed?url=' + urllib.parse.quote(url, safe=':/')))
        return d.get('thumbnail_url')
    except Exception: return None
ALIAS = {  # (artist, title) -> (MusicBrainz artist, MusicBrainz title)
 ("John Mayall & The Bluesbreakers", "Featuring Eric Clapton"): ("John Mayall", "Blues Breakers With Eric Clapton"),
 ("The Soft Machine", "Soft Machine Volume 2"): ("Soft Machine", "Volume Two"),
 ("The Velvet Underground", "Live 1969 vol 1 & 2"): ("The Velvet Underground", "1969: The Velvet Underground Live"),
 ("LL Cool J", "I Love My Radio"): ("LL Cool J", "Radio"),
 ("LL Cool J", "B.A.D."): ("LL Cool J", "Bigger and Deffer"),
 ("The Justified Ancients Of Mumu", "Who Killed The Jams?"): ("The Justified Ancients of Mu Mu", "Who Killed the JAMs?"),
 ("808 State", "New Build"): ("808 State", "Newbuild"),
 ("808 State", "90"): ("808 State", "Ninety"),
 ("Jeff Mills", "Waveform Transmissions Vol 1"): ("Jeff Mills", "Waveform Transmission"),
 ("Arrested Development", "5 Years, 3 Months & 2 Days"): ("Arrested Development", "3 Years, 5 Months & 2 Days in the Life Of"),
 ("United Future Organization", "U.F.O."): ("United Future Organization", "United Future Organization"),
 ("Bandulu", "Anti Matters"): ("Bandulu", "Antimatters"),
 ("Carl Craig", "6.9 The Sound Of Music"): ("69", "The Sound of Music"),
 ("Superdiscount", "Superdiscount"): ("Étienne de Crécy", "Super Discount"),
 ("Coldcut", "JDJ 70 Minutes Of Madness"): ("Coldcut", "70 Minutes of Madness"),
 ("Basic Channel", "Basic Channel"): ("Basic Channel", "BCD"),
 ("Moodyman", "Your Silent Introduction"): ("Moodymann", "Silentintroduction"),
 ("Pole", "Cd 1"): ("Pole", "1"),
 ("Pole", "Pole 2"): ("Pole", "2"),
 ("DJ Krush / Toshinori Kondo", "Ki-Oku"): ("DJ Krush", "Ki-Oku"),
 ("Porter Ricks / Techno Animal", "Symbiotics"): ("Techno Animal", "Symbiotics"),
 ("Kit Clayton", "Nek Salanet"): ("Kit Clayton", "Nek Sankofa"),
 ("Rubin Steiner", "Lo Fi Nu Jazz n°2"): ("Rubin Steiner", "Lo-Fi Nu Jazz Vol. 2"),
 ("Set Fire To Flames", "Sings Reign Rebuilders"): ("Set Fire to Flames", "Sings Reign Rebuilder"),
 ("2 Many DJ's", "As Heard On Radio Soulwax Pt 2"): ("2manydjs", "As Heard on Radio Soulwax, Pt. 2"),
 ("The Woodentops", "Straight Eight Bushwalker"): ("The Woodentops", "Giant"),
 ("The Hollies", "30th Anniversary Collection 63-93"): ("The Hollies", "30th Anniversary Collection"),
 ("Einstürzende Neubauten", "Strategies Against Architecture 1+2"): ("Einstürzende Neubauten", "Strategies Against Architecture 80-83"),
 ("Kurtis Blow", "Presents The History Of Rap Vol.1 + Vol.2 + Vol.3"): ("", "Kurtis Blow Presents: The History of Rap"),
 ("", "Headz (A Soundtrack Of Beathead Jams... Abstract Musical Science)"): ("", "Headz"),
 ("", "Nuggets: Original Artyfacts From The First Psychedelic Era 1965-68"): ("", "Nuggets: Original Artyfacts From the First Psychedelic Era"),
 ("", "Nuggets II: Original Artyfacts From The British Empire & Beyond 1964-69"): ("", "Nuggets II: Original Artyfacts From the British Empire and Beyond"),
 ("", "OHM: The Early Gurus Of Electronic Music: 1948-1980"): ("", "OHM: The Early Gurus of Electronic Music"),
 ("", "Story Of Jamaican Music: Tougher Than Tough"): ("", "Tougher Than Tough: The Story of Jamaican Music"),
 ("", "Inflight Entertainment: 19 New Ways To Fly Around The World Of Easy Listening"): ("", "Inflight Entertainment"),
 ("James Brown", "Foundations Of Funk: A Brand New Bag 64-69"): ("James Brown", "Foundations of Funk: A Brand New Bag: 1964-1969"),
 ("James Brown", "Make It Funky: The Big Payback 71-75"): ("James Brown", "Make It Funky: The Big Payback: 1971-1975"),
 ("Machine Soul", "An Odyssey Into Electronic Dance Music"): ("", "Machine Soul: An Odyssey Into Electronic Dance Music"),
 ("", "Disco Not Disco Compiled By Joey Negro & Sean P. (Vol.1+2)"): ("", "Disco Not Disco"),
 ("", "House Nation «Classic House Anthems» Vol.1 + Vol.2"): ("", "House Nation"),
}
def mb_cover(artist, title):
    artist, title = ALIAS.get((artist, title), (artist, title))
    t = re.sub(r'\s*\+\s*(\(|Vol).*$', '', title, flags=re.I)
    t = re.sub(r'\(?\bVol\.?\s*\d[^)]*\)?', '', t, flags=re.I).strip(' :-')
    q = f'releasegroup:"{t}"' + (f' AND artist:"{artist}"' if artist else '')
    d = None
    for _ in range(4):
        time.sleep(1.2)
        try:
            d = json.load(get('https://musicbrainz.org/ws/2/release-group/?' + urllib.parse.urlencode({'query': q, 'fmt': 'json', 'limit': 10}))); break
        except Exception: time.sleep(3)
    if d is None: return None
    for rg in d.get('release-groups', []):
        an = ' '.join(c.get('name', '') + ' ' + c.get('artist', {}).get('name', '') for c in rg.get('artist-credit', []) if isinstance(c, dict))
        if sim(t, rg['title']) < 0.8: continue
        if artist and max(sim(artist, an), sim(artist, rg['artist-credit'][0]['name'])) < 0.8 and norm(artist) not in norm(an): continue
        u = f"https://coverartarchive.org/release-group/{rg['id']}/front-250"
        try:
            req = urllib.request.Request(u, headers=UA, method='HEAD')
            class NoRedir(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *a, **k): return None
            urllib.request.build_opener(NoRedir).open(req, timeout=20)
            return u
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 307): return u
        except Exception: pass
    return None
D = json.load(open('data/albums.json'))
recs = [(it['artist'], it) for Y in D['years'] for it in Y['items']] + [(r['artist'], r) for H in D['hidden'] for r in H['records']]
found = 0; todo = 0
for artist, it in recs:
    if any(a.get('cover') for a in it['albums']): continue
    todo += 1
    for a in it['albums']:
        k = artist + '|' + a['title']
        if k not in C:
            c = spotify_cover(a['spotify']) if a.get('spotify_exact') else None
            C[k] = c or mb_cover(artist, a['title'])
            json.dump(C, open(CP, 'w'), ensure_ascii=False, indent=0)
        if C[k]:
            a['cover'] = C[k]; found += 1; break
json.dump(D, open('data/albums.json', 'w'), ensure_ascii=False, indent=1)
print(f'records missing a cover: {todo}; filled: {found}')
