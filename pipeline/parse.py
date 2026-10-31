import glob,os,re,json
out={}
for f in glob.glob('ocr/*/*/markdown.md'):
    img=os.path.basename(os.path.dirname(f)); t=open(f).read()
    out[img]=t
json.dump(out,open('ocr_raw.json','w'),ensure_ascii=False,indent=1)
years={}
for img,t in sorted(out.items()):
    lines=[l.strip() for l in t.split('\n') if l.strip()]
    m=re.match(r'#?\s*(\d{4})$',lines[0])
    if not m: continue
    y=int(m.group(1)); blurb=[];items=[]
    for l in lines[1:]:
        mm=re.match(r'^[-*]?\s*(\d{1,2})[\.\)]?\s+(.*)$',l)
        if mm and int(mm.group(1))<=25 and len(l)<150: items.append((int(mm.group(1)),mm.group(2)))
        elif not items: blurb.append(l)
        else: print('EXTRA',y,l)
    years[y]=dict(img=img,blurb='\n\n'.join(blurb),items=items)
    print(y,img,len(items),[i[0] for i in items] if len(items)!=20 else '')
json.dump(years,open('years_ocr.json','w'),ensure_ascii=False,indent=1)
