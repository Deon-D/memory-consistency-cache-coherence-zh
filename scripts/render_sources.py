import pathlib,json,re
import pdfplumber

ROOT=pathlib.Path(__file__).resolve().parents[1]
ASSETS=ROOT/'output'/'reader'/'assets'
(ASSETS/'pages').mkdir(parents=True,exist_ok=True)
(ASSETS/'figures').mkdir(exist_ok=True)
doc=pdfplumber.open(ROOT/'primer2020_2nd_edition.pdf')
visuals=[];pages=[];fonts=set()
for pn,p in enumerate(doc.pages,1):
    if pn in (2,4):continue
    lines=p.extract_text_lines(x_tolerance=1,return_chars=False)
    crop=p.cropbox
    # Keep the actual book page, removing only its PDF production margins.
    target=ASSETS/'pages'/f'p{pn:03d}.png'
    if not target.exists():p.crop(crop).to_image(resolution=144,antialias=True).save(target)
    pages.append(pn)
    fonts.update(c['fontname'] for c in p.chars)
    if pn<23:continue
    objects=[]
    for o in p.rects+p.curves+p.lines+p.images:
        if o['bottom']<174 or o['top']>715:continue
        if o['width']<1 and o['height']>500 and any(abs(o['x0']-x)<3 for x in (262.77,674.22)):continue
        if pn in (23,31,39,61,77,113,129,173,213,233,273) and o['bottom']<325:continue
        objects.append(o)
    objects.sort(key=lambda o:o['top'])
    groups=[]
    for o in objects:
        if groups and o['top']<=max(x['bottom'] for x in groups[-1])+22:groups[-1].append(o)
        else:groups.append([o])
    # A figure can contain disconnected subpanels. Keep all page geometry together
    # so that inter-panel labels and complete captions cannot be cut away.
    if groups:groups=[[o for g in groups for o in g]]
    for n,g in enumerate(groups,1):
        top=min(x['top'] for x in g);bottom=max(x['bottom'] for x in g)
        left=min(x['x0'] for x in g);right=max(x['x1'] for x in g)
        if right-left<30 or bottom-top<8:continue
        # Include table captions and labels adjacent to diagram geometry.
        if pn in (23,31,39,61,77,113,129,173,213,233,273) and bottom<290:continue
        candidates=[l for l in lines if l['top']>=top-55 and l['bottom']<=bottom+55 and l['top']>=174]
        for l in candidates:
            top=min(top,l['top']);bottom=max(bottom,l['bottom']);left=min(left,l['x0']);right=max(right,l['x1'])
        box=(max(crop[0],left-8),max(173,top-6),min(crop[2],right+8),min(724,bottom+6))
        name=f'figures/p{pn:03d}-full.png'
        p.crop(box).to_image(resolution=180,antialias=True).save(ASSETS/name)
        visuals.append({'pdf_page':pn,'file':name,'bbox':list(box)})
    if pn%40==0:print('Rendered',pn,flush=True)
(ROOT/'source'/'visuals.json').write_text(json.dumps(visuals,ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'source'/'page_images.json').write_text(json.dumps(pages),encoding='utf8')
(ROOT/'source'/'fonts.json').write_text(json.dumps(sorted(fonts),indent=2),encoding='utf8')
print('Done:',len(pages),'source pages;',len(visuals),'figure regions')
