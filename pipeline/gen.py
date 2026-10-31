import json, html, sys
D = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
E = html.escape
years = D['years']; hidden = D['hidden']

n_items = sum(len(Y['items']) for Y in years)
n_alb = sum(len(it['albums']) for Y in years for it in Y['items'])
n_dz = sum(1 for Y in years for it in Y['items'] for a in it['albums'] if 'deezer' in a)
n_sp = sum(1 for Y in years for it in Y['items'] for a in it['albums'] if a.get('spotify_exact') and 'deezer' not in a)
n_exact = n_dz + n_sp
pct = round(100 * n_exact / n_alb)

ICONS = json.load(open(__import__('os').path.join(__import__('os').path.dirname(__file__), 'icons.json')))
def ico(svc):
    return f'<svg class="ic" aria-hidden="true"><use href="#i-{svc}"/></svg>'
SPRITE = '<svg width="0" height="0" style="position:absolute" aria-hidden="true">' + ''.join(
    f'<symbol id="i-{k}" viewBox="0 0 24 24"><path d="{v}"/></symbol>' for k, v in ICONS.items()) + '</svg>'
NAMES = {'deezer': 'Deezer', 'spotify': 'Spotify', 'youtube': 'YouTube'}
CLS = {'deezer': 'lk-dz', 'spotify': 'lk-sp', 'youtube': 'lk-yt'}
def lnk(svc, href, exact):
    if exact:
        return (f'<a class="lk {CLS[svc]}" data-svc="{svc}" href="{E(href)}" target="_blank" rel="noopener" '
                f'title="Ouvrir sur {NAMES[svc]}" aria-label="Ouvrir sur {NAMES[svc]}">{ico(svc)}</a>')
    return (f'<a class="lk {CLS[svc]} lk-search" data-svc="{svc}" href="{E(href)}" target="_blank" rel="noopener" '
            f'title="Rechercher sur {NAMES[svc]}" aria-label="Rechercher sur {NAMES[svc]}">{ico(svc)}<span class="srch">⌕</span></a>')
def album_links(a, artist=''):
    return (lnk('deezer', a['deezer'], True) if 'deezer' in a else lnk('deezer', deezer_search(artist, a['title']), False)) \
        + lnk('spotify', a['spotify'], bool(a.get('spotify_exact'))) + lnk('youtube', a['youtube'], False)

def deezer_search(artist, title):
    import urllib.parse
    return 'https://www.deezer.com/search/' + urllib.parse.quote((artist + ' ' + title).strip())

def fix_dz_search(a, artist):
    if 'deezer' not in a:
        a['_dzs'] = deezer_search(artist, a['title'])

def render_albums(artist, albums):
    rows = []
    for a in albums:
        lk = album_links(a, artist)
        found = 'deezer' in a or a.get('spotify_exact')
        rows.append(f'<div class="alb"><span class="alb-t">{E(a["title"])}</span>'
                    f'<span class="lks">{lk}</span>'
                    + ('' if found else '<span class="nf" title="Album introuvable en lien direct">∅</span>')
                    + '</div>')
    return ''.join(rows)

def cover(albums):
    for a in albums:
        if a.get('cover'):
            return f'<img class="cv" loading="lazy" src="{E(a["cover"])}" alt="" width="56" height="56">'
    return '<span class="cv cv-empty">◉</span>'

decades = {}
for Y in years:
    decades.setdefault(Y['year'] // 10 * 10, []).append(Y)
dec_label = {1960: 'Années 60', 1970: 'Années 70', 1980: 'Années 80', 1990: 'Années 90', 2000: 'Années 2000'}

year_chips = ''.join(f'<a class="ychip" href="#y{Y["year"]}">{Y["year"]}</a>' for Y in years)

sections = []
sn = 0
for dec, ys in decades.items():
    sn += 1
    blocks = []
    for Y in ys:
        items = []
        for it in Y['items']:
            search = (it['artist'] + ' ' + it['title']).lower()
            items.append(
                f'<li class="rec" data-q="{E(search)}">'
                f'<span class="rk">{it["rank"]:02d}</span>{cover(it["albums"])}'
                f'<div class="meta"><div class="art">{E(it["artist"])}</div>{render_albums(it["artist"], it["albums"])}</div></li>')
        blurb = ''.join(f'<p>{E(p)}</p>' for p in Y['blurb'].split('\n\n') if p.strip())
        blocks.append(
            f'<article class="year" id="y{Y["year"]}"><div class="yhead"><span class="ynum">{Y["year"]}</span>'
            f'<a class="ytop" href="#top">↑ haut</a></div>'
            f'<div class="blurb">{blurb}</div><ol class="recs">{"".join(items)}</ol></article>')
    sections.append(
        f'<section id="s{sn}"><div class="sec-num">{sn:02d}</div><h2>{dec_label[dec]} '
        f'<span class="h2y">{ys[0]["year"]}–{ys[-1]["year"]}</span></h2>{"".join(blocks)}</section>')

# hidden list
sn += 1
hid_sec = sn
hb = []
for b in hidden:
    recs = []
    for r in b['records']:
        search = (r['artist'] + ' ' + r['title']).lower()
        art = E(r['artist']) if r['artist'] else '<span class="va">Compilation</span>'
        recs.append(f'<div class="hrec" data-q="{E(search)}">{cover(r["albums"])}<div class="meta"><div class="art">{art} <span class="fmt">{E(r["format"])}</span></div>{render_albums(r["artist"], r["albums"])}</div></div>')
    hb.append(f'<li class="hblock">{"".join(recs)}<p class="hdesc">{E(b["desc"])}</p></li>')
hidden_html = (f'<section id="s{hid_sec}"><div class="sec-num">{hid_sec:02d}</div><h2>La liste cachée</h2>'
               '<p class="sec-note">« Maintenant que vous vous êtes rassasiés de ces 820 disques (en fait ils sont 882 !), il va vous rester quelques compilations à digérer. » '
               'Compils, coffrets et disques recalés, classés par ordre chronologique et non préférentiel.</p>'
               f'<ol class="hlist">{"".join(hb)}</ol></section>')

sn += 1
meth_sec = sn
method = f'''<section id="s{meth_sec}"><div class="sec-num">{meth_sec:02d}</div><h2>Méthode &amp; sources</h2>
<div class="prose sec-note">
<p>Les textes et classements sont ceux de Christophe Brault : vingt albums par année, de 1964 à 2004, chacun précédé d'un court texte de présentation, puis une « liste cachée » de compilations. Les pages ont été photographiées, passées à l'OCR, puis relues à la main : l'OCR avait fusionné le nom de l'artiste (en gras) et le titre de l'album (en italique), séparés ici à partir des photos d'origine.</p>
<p>Lorsqu'une ligne cite plusieurs disques (« A + B »), chaque album a ses propres liens. Les liens ont été résolus automatiquement : {n_dz} albums sur {n_alb} pointent directement vers la page Deezer de l'album, {n_sp} autres vers Spotify. Les boutons marqués ⌕ ouvrent une recherche (Spotify, YouTube) plutôt qu'un album précis — c'est le repli quand le disque n'est pas au catalogue ou n'a pas été trouvé. Une correspondance automatique peut se tromper d'édition (remaster, deluxe, live) : signalez-le.</p>
</div>
<div class="src">
<div><span class="tag">SRC</span>Christophe Brault, classements annuels 1964–2004 et liste cachée (photos des pages, 31 août 2022)</div>
<div><span class="tag">API</span><a href="https://developers.deezer.com/api/search" target="_blank" rel="noopener">Deezer Search API</a> — liens et pochettes</div>
<div><span class="tag">API</span>Spotify — liens directs pour une partie des albums absents de Deezer</div>
</div></section>'''

page = f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Les disques de Christophe Brault</title>
<meta name="description" content="820 albums choisis par Christophe Brault, vingt par an de 1964 à 2004, avec liens Deezer, Spotify et YouTube.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Source+Serif+4:ital,wght@0,600;0,700;1,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://www.bzhmacro.com/brand/bzh.css" onerror="this.onerror=null;this.href='assets/bzh.css';">
<link rel="stylesheet" href="assets/brault.css">
<link rel="icon" href="assets/icon.svg">
</head>
<body id="top">
<div class="site-banner">
  <span class="header-flag">💿</span>
  <div>
    <h1>Les disques de Christophe Brault</h1>
    <p>Vingt albums par an, de 1964 à 2004, à écouter sur Deezer, Spotify ou YouTube</p>
  </div>
  <div class="header-right">
    <a class="bzh-brand" href="https://www.bzhmacro.com" target="_blank" rel="noopener">
      <img src="https://www.bzhmacro.com/brand/bzhmacro-logo.png" alt="bzhmacro" onerror="this.src='assets/bzhmacro-logo.png';">
      <span class="bzh-wordmark">bzh<strong>macro</strong>.com</span>
    </a>
  </div>
</div>
<nav class="section-nav" id="snav">
{''.join(f'<a class="snav-link{" active" if i==0 else ""}" href="#s{i+1}">{dec_label[d].replace("Années ","")}</a>' for i,d in enumerate(decades))}
  <a class="snav-link" href="#s{hid_sec}">Liste cachée</a>
  <a class="snav-link" href="#s{meth_sec}">Méthode</a>
</nav>

<div class="wrap">
<header class="page-head">
  <div class="eyebrow"><span class="dot"></span>Discothèque idéale · 1964–2004</div>
  <h1>Quarante ans de disques, <em>vingt par an.</em></h1>
  <p class="sub">La sélection de Christophe Brault, année par année : un texte pour situer le millésime, puis vingt albums classés. Chaque disque renvoie vers Deezer ou Spotify quand il y est, et vers une recherche YouTube sinon.</p>
  <div class="hero-stats">
    <div class="stat"><div class="num">{len(years)}</div><div class="lbl">années, de 1964 à 2004</div></div>
    <div class="stat"><div class="num">{n_items}</div><div class="lbl">places au classement</div></div>
    <div class="stat"><div class="num">{n_alb}</div><div class="lbl">albums (certaines places en comptent deux ou trois)</div></div>
    <div class="stat"><div class="num">{pct}<small>%</small></div><div class="lbl">avec un lien direct Deezer ou Spotify</div></div>
  </div>
  <div class="controls" id="ctl">
    <input type="search" id="q" placeholder="Chercher un artiste ou un album…" aria-label="Chercher">
    <span class="lbl">Service</span>
    <button class="chip" data-pref="deezer">Deezer</button>
    <button class="chip" data-pref="spotify">Spotify</button>
    <button class="chip" data-pref="youtube">YouTube</button>
    <button class="chip on" data-pref="all">Tous</button>
    <span class="lbl" id="count"></span>
  </div>
  <div class="ychips">{year_chips}</div>
</header>
{''.join(sections)}
{hidden_html}
{method}
<footer class="site-footer">
Sélection et textes : Christophe Brault. Liens résolus automatiquement à partir des catalogues Deezer et Spotify — une édition peut différer de l'original.<br>
Derived from public sources — see method. Estimates, not official publications. Not investment advice. · <a href="https://www.bzhmacro.com">bzhmacro.com</a>
</footer>
</div>
<script>
(function(){{
  var q=document.getElementById('q'), cnt=document.getElementById('count');
  var recs=[].slice.call(document.querySelectorAll('[data-q]'));
  function filt(){{
    var v=q.value.trim().toLowerCase(), n=0;
    recs.forEach(function(r){{ var m=!v||r.dataset.q.indexOf(v)>-1; r.hidden=!m; if(m) n++; }});
    document.querySelectorAll('article.year, li.hblock').forEach(function(a){{
      a.hidden = !!v && !a.querySelector('[data-q]:not([hidden])');
    }});
    document.querySelectorAll('section').forEach(function(sec){{
      if(!sec.querySelector('article.year, li.hblock')) return;
      sec.hidden = !!v && !sec.querySelector('article.year:not([hidden]), li.hblock:not([hidden])');
    }});
    cnt.textContent = v ? n+' résultat'+(n>1?'s':'') : '';
  }}
  q.addEventListener('input',filt);
  var chips=[].slice.call(document.querySelectorAll('[data-pref]'));
  function setPref(p){{
    document.body.dataset.pref=p;
    document.querySelectorAll('.alb').forEach(function(a){{
      var ls=[].slice.call(a.querySelectorAll('.lk'));
      if(p==='all'){{ ls.forEach(function(l){{l.hidden=false;}}); return; }}
      var exact=function(svc){{ return ls.filter(function(l){{return l.dataset.svc===svc && !l.classList.contains('lk-search');}})[0]; }};
      var other = p==='deezer'?'spotify':(p==='spotify'?'deezer':null);
      var pick = (p==='youtube') ? ls.filter(function(l){{return l.dataset.svc==='youtube';}})[0]
               : (exact(p) || (other && exact(other)) || ls.filter(function(l){{return l.dataset.svc==='youtube';}})[0]);
      ls.forEach(function(l){{ l.hidden = (l!==pick); }});
    }});
    chips.forEach(function(c){{ c.classList.toggle('on',c.dataset.pref===p); }});
    try{{ localStorage.setItem('brault-pref',p); }}catch(e){{}}
  }}
  chips.forEach(function(c){{ c.addEventListener('click',function(){{ setPref(c.dataset.pref); }}); }});
  var saved='all'; try{{ saved=localStorage.getItem('brault-pref')||'all'; }}catch(e){{}}
  setPref(saved);
}})();
</script>
<script>
(function(){{
  var links=[].slice.call(document.querySelectorAll('#snav .snav-link[href^="#"]'));
  var secs=links.map(function(l){{return document.querySelector(l.getAttribute('href'));}});
  function spy(){{
    var y=window.scrollY+80,i=0;
    secs.forEach(function(s,j){{ if(s&&s.offsetTop<=y) i=j; }});
    links.forEach(function(l,j){{ l.classList.toggle('active',j===i); }});
  }}
  window.addEventListener('scroll',spy,{{passive:true}}); spy();
}})();
</script>
{SPRITE}
</body>
</html>
'''
open(OUT, 'w').write(page)
print('written', OUT, len(page), 'bytes;', n_dz, 'deezer,', n_sp, 'spotify-only,', n_alb, 'albums')
