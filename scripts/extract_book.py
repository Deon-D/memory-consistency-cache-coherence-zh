import json,re,collections,pathlib
import pdfplumber

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'source'
OUT.mkdir(exist_ok=True)
(ROOT/'translations').mkdir(exist_ok=True)
chapters=[
 ('front',1,22,'Front matter','卷首'),
 ('ch01',23,30,'Introduction to Consistency and Coherence','内存一致性与缓存一致性导论'),
 ('ch02',31,38,'Coherence Basics','缓存一致性基础'),
 ('ch03',39,60,'Memory Consistency Motivation and Sequential Consistency','内存一致性的动机与顺序一致性'),
 ('ch04',61,76,'Total Store Order and the x86 Memory Model','全存储顺序与 x86 内存模型'),
 ('ch05',77,112,'Relaxed Memory Consistency','宽松内存一致性'),
 ('ch06',113,128,'Coherence Protocols','缓存一致性协议'),
 ('ch07',129,172,'Snooping Coherence Protocols','监听式缓存一致性协议'),
 ('ch08',173,212,'Directory Coherence Protocols','目录式缓存一致性协议'),
 ('ch09',213,232,'Advanced Topics in Coherence','缓存一致性高级主题'),
 ('ch10',233,272,'Consistency and Coherence for Heterogeneous Systems','异构系统的内存一致性与缓存一致性'),
 ('ch11',273,294,'Specifying and Validating Memory Consistency Models and Cache Coherence','内存一致性模型与缓存一致性的规约和验证'),
 ('bio',295,296,"Authors’ Biographies",'作者简介')]

def tidy(lines):
    s=''
    for t in lines:
        if s.endswith('-') and t and t[0].islower():s=s[:-1]+t
        else:s+=(' ' if s else '')+t
    return s.replace('ﬁ','fi').replace('ﬂ','fl').replace('F irst','First')

doc=pdfplumber.open(ROOT/'primer2020_2nd_edition.pdf')
all_ch=[]
for cid,start,end,en,zh in chapters:
    chapter={'id':cid,'title_en':en,'title_zh':zh,'pdf_start':start,'pdf_end':end,'blocks':[]}
    for pn in range(start,end+1):
        p=doc.pages[pn-1]
        lines=p.extract_text_lines(x_tolerance=1,y_tolerance=3,return_chars=True)
        if pn>=12:lines=[l for l in lines if l['top']>=173]
        if not lines:continue
        # Use the ordinary prose left edge to identify first-line paragraph indents.
        regular=[l for l in lines if 10.5<=max((c['size'] for c in l['chars']),default=0)<=11.3 and len(l['text'])>55]
        base=collections.Counter(round(l['x0'],0) for l in regular).most_common(1)
        base=base[0][0] if base else min(l['x0'] for l in lines)
        groups=[];cur=[];prev=None
        for l in lines:
            txt=l['text'];size=max((c['size'] for c in l['chars']),default=10)
            heading=size>=11.8 and (size>14 or sum(c.isupper() for c in txt)>sum(c.islower() for c in txt))
            kind='heading' if heading else 'paragraph'
            if re.match(r'^(Figure|Table)\s+\d+\.',txt):kind='caption'
            l['kind']=kind
            new=not cur
            if prev:
                gap=l['top']-prev['bottom']
                new=(gap>7 or kind!=prev['kind'] or
                     (kind=='paragraph' and base+18<l['x0']<base+34 and prev['x0']<base+5) or
                     bool(re.match(r'^(?:[•●]|\[\d+\]|\d+\.\s)',txt)))
            if new and cur:groups.append(cur);cur=[]
            cur.append(l);prev=l
        if cur:groups.append(cur)
        for idx,g in enumerate(groups,1):
            text=tidy([l['text'] for l in g])
            if not text.strip():continue
            chapter['blocks'].append({'id':f'p{pn:03d}b{idx:02d}','pdf_page':pn,
                'book_page':str(pn-22) if pn>=23 else '', 'kind':g[0]['kind'],'en':text,
                'bbox':[round(min(l['x0'] for l in g),2),round(min(l['top'] for l in g),2),round(max(l['x1'] for l in g),2),round(max(l['bottom'] for l in g),2)]})
    (OUT/f'{cid}.json').write_text(json.dumps(chapter,ensure_ascii=False,indent=2),encoding='utf-8')
    all_ch.append({k:v for k,v in chapter.items() if k!='blocks'}|{'blocks':len(chapter['blocks']),'words':sum(len(b['en'].split()) for b in chapter['blocks'])})
(OUT/'manifest.json').write_text(json.dumps(all_ch,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(all_ch,ensure_ascii=False,indent=2))
