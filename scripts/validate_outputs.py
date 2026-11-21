import pathlib,json,zipfile,posixpath,re,urllib.parse
from html.parser import HTMLParser
from xml.etree import ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'output';READER=OUT/'reader'
errors=[]
class Doc(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=set();self.refs=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:
            if a['id'] in self.ids:errors.append('duplicate HTML id '+a['id'])
            self.ids.add(a['id'])
        for k in ('href','src'):
            if a.get(k):self.refs.append(a[k])
docs={p.name:Doc(p.read_text(encoding='utf8')) for p in READER.glob('*.html')}
for name,d in docs.items():
    for ref in d.refs:
        u=urllib.parse.urlsplit(ref)
        if u.scheme or u.netloc:continue
        target=u.path or name
        if not (READER/target).exists():errors.append(f'missing HTML resource {name}: {ref}')
        if u.fragment and target in docs and u.fragment not in docs[target].ids:errors.append(f'missing HTML anchor {name}: {ref}')
for f in (ROOT/'source').glob('*.json'):
    if f.stem not in {'front','bio',*[f'ch{i:02d}' for i in range(1,12)]}:continue
    source=json.loads(f.read_text(encoding='utf8'))
    for b in source['blocks']:
        if b['id'] not in docs[f.stem+'.html'].ids:errors.append('source block absent from HTML '+b['id'])
epub=OUT/'内存一致性与缓存一致性入门_第二版_中英对照.epub'
with zipfile.ZipFile(epub) as z:
    names=set(z.namelist());files={};xmlids={}
    if z.namelist()[0]!='mimetype' or z.getinfo('mimetype').compress_type!=0:errors.append('EPUB mimetype layout invalid')
    if z.read('mimetype')!=b'application/epub+zip':errors.append('EPUB mimetype invalid')
    for n in names:
        if n.endswith(('.xhtml','.opf','.xml')):
            try:root=ET.fromstring(z.read(n))
            except Exception as e:errors.append(f'XML {n}: {e}');continue
            files[n]=root;xmlids[n]={e.get('id') for e in root.iter() if e.get('id')}
    for n,root in files.items():
        for e in root.iter():
            for attr in ('href','src','full-path'):
                ref=e.get(attr)
                if not ref:continue
                u=urllib.parse.urlsplit(ref)
                if u.scheme or u.netloc:continue
                target=(posixpath.normpath(posixpath.join(posixpath.dirname(n),u.path)) if u.path else n) if attr!='full-path' else u.path
                if target not in names:errors.append(f'missing EPUB resource {n}: {ref}')
                if u.fragment and target in xmlids and u.fragment not in xmlids[target]:errors.append(f'missing EPUB anchor {n}: {ref}')
    opf=files['EPUB/package.opf'];ns={'o':'http://www.idpf.org/2007/opf'}
    itemids={i.get('id') for i in opf.findall('o:manifest/o:item',ns)}
    for i in opf.findall('o:spine/o:itemref',ns):
        if i.get('idref') not in itemids:errors.append('EPUB spine item missing '+i.get('idref'))
    declared={posixpath.normpath('EPUB/'+i.get('href')) for i in opf.findall('o:manifest/o:item',ns)}
    extra={n for n in names if n.startswith('EPUB/') and n!='EPUB/package.opf'}-declared
    if extra:errors.append('EPUB undeclared resources: '+str(extra))
v=json.loads((OUT/'validation.json').read_text(encoding='utf8'))
if v['edition']!='complete':errors.append('Final edition has not been built')
if v['total_blocks']!=v['translated_blocks']+v.get('original_only_blocks',0):errors.append('Translation coverage incomplete')
for p in READER.glob('*.html'):
    if '【译文制作中】' in p.read_text(encoding='utf8'):errors.append('Placeholder in '+p.name)
result={'html_documents':len(docs),'epub_xml_documents':len(files),'total_source_blocks':v['total_blocks'],'translated_blocks':v['translated_blocks'],'errors':errors,'passed':not errors}
(ROOT/'qa'/'output-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
if errors:raise SystemExit(1)
