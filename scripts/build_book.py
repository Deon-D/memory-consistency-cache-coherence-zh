import argparse,collections,datetime,html,json,pathlib,re,zipfile,hashlib
from xml.etree import ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'output';READER=OUT/'reader';ASSETS=READER/'assets'
READER.mkdir(parents=True,exist_ok=True);ASSETS.mkdir(exist_ok=True)
PREVIEW='--preview' in __import__('sys').argv
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
manifest=read(ROOT/'source'/'manifest.json')
glossary=read(ROOT/'glossary.json')
visuals=read(ROOT/'source'/'visuals.json')
formulas=read(ROOT/'source'/'formulas.json')
rasters=read(ROOT/'source'/'block_rasters.json') if (ROOT/'source'/'block_rasters.json').exists() else {}
pages=read(ROOT/'source'/'page_images.json')
original_only=set(read(ROOT/'source'/'original_only.json'))
chapters=[];report=[];search=[]
for meta in manifest:
    c=read(ROOT/'source'/f"{meta['id']}.json")
    tf=ROOT/'translations'/f"{meta['id']}.json"
    tr=read(tf) if tf.exists() else {}
    missing=[b['id'] for b in c['blocks'] if b['id'] not in original_only and (not isinstance(tr.get(b['id']),str) or not tr[b['id']].strip())]
    extra=sorted(set(tr)-{b['id'] for b in c['blocks']})
    report.append({'chapter':c['id'],'blocks':len(c['blocks']),'original_only':sum(b['id'] in original_only for b in c['blocks']),'translated':sum(b['id'] not in original_only for b in c['blocks'])-len(missing),'missing':missing,'extra':extra,'chinese_characters':sum(len(re.findall('[\u3400-\u9fff]',v)) for v in tr.values())})
    for b in c['blocks']:b['zh']='' if b['id'] in original_only else tr.get(b['id'],'【译文制作中】')
    chapters.append(c)
if any(x['missing'] or x['extra'] for x in report) and not PREVIEW:
    print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit('Coverage check failed; no final edition was built.')

TITLE='内存一致性与缓存一致性入门'
EN_TITLE='A Primer on Memory Consistency and Cache Coherence'
E=lambda s:html.escape(str(s),quote=True)

CSS=r'''
:root{--paper:#fbfaf6;--panel:#f1f0e9;--ink:#1d3037;--muted:#5b6971;--line:#d8ded9;--accent:#14685e;--highlight:#d98550;--font:19px}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:90px}body{margin:0;background:var(--paper);color:var(--ink);font-family:'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',sans-serif;font-size:var(--font);line-height:1.9}body.night{--paper:#172329;--panel:#202f36;--ink:#e4e9e4;--muted:#b1bfc2;--line:#3e5159;--accent:#82cdb8;--highlight:#e7a575}a{color:var(--accent);text-underline-offset:4px}button,input,select{font:inherit}button,.button{border:1px solid var(--line);border-radius:6px;background:var(--paper);color:var(--ink);padding:5px 11px;text-decoration:none;cursor:pointer;font-size:14px;line-height:1.6}button:hover,.button:hover{border-color:var(--accent);color:var(--accent)}button:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid var(--highlight);outline-offset:3px}.primary{background:var(--accent);color:var(--paper);border-color:var(--accent);padding:12px 22px}.topbar{position:sticky;top:0;z-index:30;min-height:62px;background:var(--paper);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:9px;padding:10px 24px;font-size:14px}.brand{font-weight:700;text-decoration:none;white-space:nowrap;margin-right:auto}.controls{display:flex;align-items:center;gap:7px;flex-wrap:wrap}.navtoggle{display:none}.sidebar{position:fixed;top:64px;bottom:0;width:276px;overflow:auto;padding:26px 23px;background:var(--panel);font-size:14px;border-right:1px solid var(--line)}.sidebar h2{font-size:12px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin:0 0 15px}.sidebar a{display:block;padding:8px 0;text-decoration:none;line-height:1.6}.sidebar .active{font-weight:700;border-left:3px solid var(--accent);padding-left:12px;margin-left:-15px}.sidebar small{display:block;color:var(--muted);font-size:10px;line-height:1.5}.sidebar .navfoot{border-top:1px solid var(--line);margin-top:22px;padding-top:15px}main{margin-left:276px;padding:52px 5vw 90px;max-width:1540px}.eyebrow{font-size:12px;letter-spacing:3px;color:var(--accent);font-weight:700;text-transform:uppercase}.hero{padding:25px 0 45px;border-bottom:1px solid var(--line);margin-bottom:34px;max-width:1020px}.hero h1{font-family:'Microsoft YaHei','PingFang SC',sans-serif;font-size:clamp(30px,3.8vw,51px);font-weight:650;letter-spacing:-1px;line-height:1.35;margin:18px 0}.hero .english-title{font-family:Georgia,'Times New Roman',serif;color:var(--muted);font-size:24px;line-height:1.45;max-width:760px}.hero .meta{color:var(--muted);font-size:14px;margin:24px 0}.hero .actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}.chapter-title{margin-bottom:35px}.chapter-title h1{font-size:34px;line-height:1.5;margin:12px 0}.chapter-title .english-title{font:22px/1.5 Georgia,serif;color:var(--muted)}.chapter-title .meta{color:var(--muted);font-size:13px}.page-marker{font-size:11px;color:var(--muted);letter-spacing:1px;border-top:1px solid var(--line);padding-top:16px;margin:38px 0 14px;display:flex;justify-content:space-between}.pair{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:32px;padding:19px 0;border-bottom:1px solid var(--line);scroll-margin-top:90px}.pair>div{min-width:0}.pair .en{font-family:Georgia,'Times New Roman',serif;font-size:.95em;line-height:1.8;color:var(--muted);overflow-wrap:anywhere;white-space:pre-line}.pair .zh{line-height:1.95;overflow-wrap:anywhere;white-space:pre-line}.pair.heading{display:block;margin-top:26px;padding:17px 0;border-bottom:2px solid var(--accent)}.pair.heading .en{font-size:15px}.pair.heading .zh{font-weight:700;font-size:24px;line-height:1.6;margin-top:5px}.pair.caption{font-size:16px;background:var(--panel);padding:15px;border-radius:4px}.lang-label{font:10px/1.4 sans-serif;letter-spacing:1.5px;color:var(--muted);display:block;margin-bottom:9px}.pair.heading .lang-label{display:none}.stacked .pair{grid-template-columns:1fr;gap:18px}.zh-only .pair{grid-template-columns:1fr}.zh-only .pair .en{display:none}.en-only .pair{grid-template-columns:1fr}.en-only .pair .zh{display:none}.en-only .pair .en{color:var(--ink)}.graphic{margin:24px 0;padding:16px;background:#fff;border:1px solid var(--line);border-radius:6px;text-align:center}.graphic img{display:block;width:auto;height:auto;max-width:100%;max-height:1100px;margin:auto}.graphic figcaption{font-size:12px;color:#4d6169;margin-top:10px;line-height:1.6}.math-source{display:block;background:white;border-radius:3px;padding:6px;margin-top:10px;max-width:100%}.math-source img{display:block;max-width:100%;height:auto}.math-note{font:11px/1.5 sans-serif;color:var(--muted)}.page-original{font-size:12px;margin:15px 0 32px;color:var(--muted)}.page-original summary{cursor:pointer}.page-original img{display:block;width:100%;max-width:900px;height:auto;margin:16px auto}.chapter-nav{display:flex;justify-content:space-between;gap:25px;border-top:2px solid var(--line);padding-top:25px;margin-top:55px;font-size:15px}.chapter-nav a{max-width:48%;text-decoration:none}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 30px}.chapter-card{display:block;border-bottom:1px solid var(--line);padding:22px 0;text-decoration:none}.chapter-card strong{display:block;line-height:1.65;font-size:19px;font-weight:600}.chapter-card .number{font:12px/1.6 sans-serif;color:var(--muted);letter-spacing:2px}.chapter-card .sub{font:15px/1.5 Georgia,serif;color:var(--muted);margin-top:5px}.reading-note{padding:22px 26px;border-left:3px solid var(--accent);background:var(--panel);font-size:15px;margin:30px 0}.reading-note p{margin:0 0 10px}.reading-note p:last-child{margin:0}.section-title{font-size:23px;line-height:1.6;margin-top:35px}.local-toc{font-size:14px;margin:20px 0 35px;padding:16px 20px;background:var(--panel);border-radius:4px}.local-toc summary{cursor:pointer}.local-toc a{display:block;text-decoration:none;padding:4px 0}.local-toc .nested{padding-left:20px}.term-table{width:100%;border-collapse:collapse;font-size:15px}.term-table th{text-align:left;background:var(--panel);font-weight:600}.term-table td,.term-table th{padding:14px 12px;border-bottom:1px solid var(--line);vertical-align:top}.term-table td:first-child{font-family:Georgia,serif;width:38%}.term-table small{display:block;color:var(--muted)}.footnote{font-size:12px;color:var(--muted);margin-top:38px}.search-dialog{width:min(750px,94vw);max-height:83vh;background:var(--paper);color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:22px}.search-dialog::backdrop{background:#0008}.search-bar{display:flex;gap:10px}.search-bar input{width:100%;padding:9px 12px;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:5px;font-size:16px}.search-status{font-size:13px;color:var(--muted);padding:13px 0}.search-result{display:block;text-decoration:none;border-top:1px solid var(--line);padding:13px 0}.search-result strong{font-size:14px}.search-result p{margin:3px 0;font-size:14px;color:var(--muted);line-height:1.6}.progress{position:fixed;bottom:0;left:0;height:3px;background:var(--accent);z-index:50;width:0}.hidden{display:none!important}
@media(min-width:1700px){main{padding-right:90px}}@media(max-width:1100px){.sidebar{width:230px;padding:24px 18px}main{margin-left:230px;padding:35px 30px}.pair{gap:24px}.brand{font-size:12px}.topbar{padding:10px 16px}}@media(max-width:820px){.sidebar{display:none;width:85vw;max-width:330px;z-index:40;box-shadow:15px 0 35px #0003}.sidebar.open{display:block}.navtoggle{display:block}.brand{font-size:12px;overflow:hidden;text-overflow:ellipsis;max-width:42vw}.controls{gap:5px}.topbar{padding:9px 12px;gap:6px;flex-wrap:wrap}.controls button{font-size:12px;padding:4px 8px}main{margin:0;padding:28px 22px 70px}.pair{grid-template-columns:1fr;gap:19px;padding:22px 0}.pair .en{font-size:.91em}.pair .zh{font-size:1em}.hero{padding-top:6px}.hero h1{font-size:36px}.hero .english-title{font-size:21px}.chapter-title h1{font-size:29px}.cards{grid-template-columns:1fr}.chapter-nav{font-size:13px}.term-table{font-size:13px}.term-table th,.term-table td{padding:10px 6px}.term-table td:first-child{width:43%;overflow-wrap:anywhere}.graphic{padding:8px;margin:18px -4px}.pair.heading .zh{font-size:22px}.page-marker{margin-top:28px}}@media print{.topbar,.sidebar,.controls,.page-original,.progress{display:none}main{margin:0;padding:0}.pair{break-inside:avoid}.graphic{break-inside:avoid}body{font-size:11pt}.pair.heading{break-after:avoid}}
'''
CSS+='\n.original-only{padding:15px 0;font-family:Georgia,serif;overflow-wrap:anywhere}.original-only.caption{background:var(--panel);padding:15px}\n'
CSS+='\n.sidebar{top:var(--bar-height,64px)}html{scroll-padding-top:calc(var(--bar-height,64px) + 20px)}.pair{scroll-margin-top:calc(var(--bar-height,64px) + 20px)}\n'
(ASSETS/'reader.css').write_text(CSS,encoding='utf8')
JS=r'''
(()=>{const $=s=>document.querySelector(s);const store={get(k,d){try{return localStorage.getItem(k)||d}catch{return d}},set(k,v){try{localStorage.setItem(k,v)}catch{}}};let size=Number(store.get('book-size','19'));let mode=store.get('book-mode','parallel');function apply(){document.body.classList.remove('stacked','zh-only','en-only');if(mode!=='parallel')document.body.classList.add(mode);document.documentElement.style.setProperty('--font',size+'px');document.body.classList.toggle('night',store.get('book-night','0')==='1');const labels={parallel:'左右对照',stacked:'上下对照','zh-only':'仅中文','en-only':'仅英文'};$('#mode').textContent=labels[mode];$('#theme').textContent=document.body.classList.contains('night')?'日间':'夜间';$('#mode').setAttribute('aria-label','阅读模式：'+labels[mode]);}apply();$('#smaller').onclick=()=>{size=Math.max(15,size-1);store.set('book-size',size);apply()};$('#larger').onclick=()=>{size=Math.min(28,size+1);store.set('book-size',size);apply()};$('#mode').onclick=()=>{const modes=['parallel','stacked','zh-only','en-only'];mode=modes[(modes.indexOf(mode)+1)%4];store.set('book-mode',mode);apply()};$('#theme').onclick=()=>{store.set('book-night',document.body.classList.contains('night')?'0':'1');apply()};$('#navtoggle').onclick=()=>{const n=$('.sidebar');n.classList.toggle('open');$('#navtoggle').setAttribute('aria-expanded',n.classList.contains('open'))};document.addEventListener('click',e=>{if(window.innerWidth<=820&&!e.target.closest('.sidebar')&&!e.target.closest('#navtoggle'))$('.sidebar').classList.remove('open')});const chapter=document.body.dataset.chapter;let timer;window.addEventListener('scroll',()=>{clearTimeout(timer);timer=setTimeout(()=>{const h=document.documentElement;$('.progress').style.width=100*window.scrollY/Math.max(1,h.scrollHeight-h.clientHeight)+'%';if(chapter){const candidates=[...document.querySelectorAll('.pair')];let nearest=candidates.find(x=>x.getBoundingClientRect().bottom>85);if(nearest)store.set('book-position',chapter+'.html#'+nearest.id)}},150)},{passive:true});const resume=$('#resume');if(resume){const p=store.get('book-position','');if(p&&/^(front|ch\d\d|bio)\.html#p\d{3}b\d+$/.test(p)){resume.href=p;resume.classList.remove('hidden')}}
const dialog=$('#search-dialog'),input=$('#search-input'),results=$('#search-results'),status=$('#search-status');let loaded=false;$('#search').onclick=()=>{dialog.showModal();input.focus();if(!loaded){status.textContent='正在载入本地全文索引…';const s=document.createElement('script');s.src='assets/search.js';s.onload=()=>{loaded=true;status.textContent='输入中文、英文或协议名，搜索全书。';runSearch()};s.onerror=()=>{status.textContent='索引未能载入。请保持 assets 文件夹与阅读文件放在一起。'};document.body.append(s)}};$('#search-close').onclick=()=>dialog.close();let searchTimer;input.addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(runSearch,200)});function runSearch(){if(!loaded)return;const q=input.value.trim().toLowerCase();results.replaceChildren();if(!q){status.textContent='输入中文、英文或协议名，搜索全书。';return}const hits=window.BOOK_SEARCH.filter(x=>(x.zh+' '+x.en).toLowerCase().includes(q));status.textContent='找到 '+hits.length+' 处'+(hits.length>80?'，显示前 80 处':'');for(const x of hits.slice(0,80)){const a=document.createElement('a');a.className='search-result';a.href=x.href;const h=document.createElement('strong');h.textContent=x.chapter+' · 原书 '+x.page;const p=document.createElement('p');const t=x.zh.toLowerCase().includes(q)?x.zh:x.en;const at=t.toLowerCase().indexOf(q);p.textContent=(at>45?'…':'')+t.slice(Math.max(0,at-45),at+160)+(t.length>at+160?'…':'');a.append(h,p);a.addEventListener('click',()=>dialog.close());results.append(a)}}
})();
'''
JS+='\nnew ResizeObserver(()=>document.documentElement.style.setProperty("--bar-height",document.querySelector(".topbar").offsetHeight+"px")).observe(document.querySelector(".topbar"));\n'
(ASSETS/'reader.js').write_text(JS,encoding='utf8')

def chapter_label(c):
    return (f"第 {int(c['id'][2:])} 章　" if c['id'].startswith('ch') else '')+c['title_zh']

def shell(title,body,cid=''):
    nav=''.join(f'<a class="{"active" if c["id"]==cid else ""}" href="{c["id"]}.html">{E(chapter_label(c))}</a>' for c in chapters)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)} · 中英对照</title><link rel="stylesheet" href="assets/reader.css"></head><body data-chapter="{cid}">
<header class="topbar"><button class="navtoggle" id="navtoggle" aria-expanded="false" aria-label="打开目录">目录</button><a class="brand" href="index.html">内存一致性与缓存一致性</a><div class="controls"><button id="search">全文搜索</button><button id="smaller" aria-label="减小字号">A−</button><button id="larger" aria-label="增大字号">A＋</button><button id="mode">左右对照</button><button id="theme">夜间</button></div></header>
<nav class="sidebar" aria-label="章节目录"><h2>Contents / 章节</h2><a href="index.html">阅读首页</a>{nav}<div class="navfoot"><a href="glossary.html">中英术语表与译例</a><small>第二版 · 2020<br>中文对照译本 · 2026<br>离线阅读，无需联网</small></div></nav><main>{body}</main>
<dialog class="search-dialog" id="search-dialog" aria-label="全书搜索"><div class="search-bar"><input id="search-input" aria-label="搜索全书" placeholder="搜索术语、章节或正文…"><button id="search-close">关闭</button></div><div class="search-status" id="search-status"></div><div id="search-results"></div></dialog><div class="progress" aria-hidden="true"></div><script src="assets/reader.js"></script></body></html>'''

captions={}
for c in chapters:
    for b in c['blocks']:
        m=re.match(r'^(Figure|Table)\s+(\d+\.\d+):',b['en'])
        if m:captions[(m[1],m[2])]=c['id']+'.html#'+b['id']

def text_html(s,epub=False):
    s=s.replace('Memor y','Memory').replace('Director y','Directory').replace('Mor gan','Morgan')
    s=re.sub(r'(?:\s*\.\s*){4,}', ' · ', s)
    # Escape first; only a tightly scoped set of source cross-references becomes links.
    s=E(s)
    def repl(m):
        kind='Figure' if m[1] in ('Figure','图') else 'Table'
        target=captions.get((kind,m[2]))
        if not target:return m[0]
        if epub:target=target.replace('.html#','.xhtml#')
        return f'<a href="{target}">{m[0]}</a>'
    s=re.sub(r'\b(Figure|Table)\s+(\d+\.\d+)\b|(?!)',repl,s)
    return s.replace('\n','<br />')

def is_heading(b):
    return b['kind']=='heading' or bool(re.match(r'^\d+\.\d+(?:\.\d+)?\s+[A-Z][A-Z\s,()/.-]+$',b['en']))

def chapter_body(c,epub=False):
    num=f"CHAPTER {int(c['id'][2:]):02d}" if c['id'].startswith('ch') else 'FRONT MATTER' if c['id']=='front' else 'AUTHORS'
    title_ids=[]
    if c['id'].startswith('ch'):
        for b in c['blocks'][:3]:
            normalized=b['en'].replace('Director y','Directory').replace('Memor y','Memory')
            if re.match(r'^C\s*H\s*A\s*P\s*T\s*E\s*R\s*\d+$',normalized) or normalized.lower()==c['title_en'].lower():title_ids.append(b['id'])
    title_anchors=''.join(f'<span id="{bid}"></span>' for bid in title_ids)
    page_range=f'原书第 {c["pdf_start"]-22}–{c["pdf_end"]-22} 页 · ' if c['pdf_start']>=23 else ''
    pieces=[f'<header class="chapter-title">{title_anchors}<div class="eyebrow">{num} / 中英对照</div><h1>{E(c["title_zh"])}</h1><div class="english-title" lang="en">{E(c["title_en"])}</div><p class="meta">{page_range}PDF 第 {c["pdf_start"]}–{c["pdf_end"]} 页</p></header>']
    headings=[b for b in c['blocks'] if is_heading(b) and re.match(r'^\d+\.\d+',b['en'])]
    if headings:
        links=''.join(f'<a href="#{b["id"]}" class="{"nested" if re.match(r"^\d+\.\d+\.\d+",b["en"]) else ""}">{E(b["zh"])}</a>' for b in headings)
        pieces.append(('<div class="local-toc"><p>本章目录</p>' if epub else '<details class="local-toc"><summary>本章目录</summary>')+links+('</div>' if epub else '</details>'))
    bypage=collections.defaultdict(list)
    for b in c['blocks']:bypage[b['pdf_page']].append(b)
    vmap=collections.defaultdict(list)
    for v in visuals:vmap[v['pdf_page']].append(v)
    for pn,blocks in bypage.items():
        label=f'原书第 {pn-22} 页' if pn>=23 else f'卷首 · PDF {pn}'
        pieces.append(f'<div class="page-marker" id="page-{pn}"><span>{label}</span><span>PDF {pn}</span></div>')
        inserted=set()
        for b in blocks:
            if b['id'] in title_ids:continue
            for vi,v in enumerate(vmap[pn]):
                if vi not in inserted and b['bbox'][3]>=v['bbox'][1]:
                    pieces.append(f'<figure class="graphic"><a href="assets/{v["file"]}"><img src="assets/{v["file"]}" alt="{label}的原书图表与旁注，英文标注保持原貌" /></a><figcaption>原书图表与旁注 · {label} · 可放大查看；图表保留英文原文</figcaption></figure>')
                    inserted.add(vi)
            kind='heading' if is_heading(b) else b['kind']
            source=text_html(b['en'],epub)
            if b['id'] in rasters:
                src=rasters[b['id']]
                transcript=source
                source=f'<a class="math-source" href="assets/{src}"><img src="assets/{src}" alt="本段英文图表文字或代码的原始版面" /></a>'
                if not epub:source+=f'<details class="page-original"><summary>展开可搜索的英文文字</summary>{transcript}</details>'
            if b['id'] in formulas:
                src=formulas[b['id']]
                source+=f'<a class="math-source" href="assets/{src}"><img src="assets/{src}" alt="本段英文及公式的原始版面" /></a><span class="math-note">数学符号与上下标以此原版面为准</span>'
            if b['id'] in original_only:
                pieces.append(f'<section class="original-only {kind}" id="{b["id"]}" lang="en">{source}</section>')
                if not epub:search.append({'href':c['id']+'.html#'+b['id'],'chapter':chapter_label(c),'page':str(pn-22),'en':b['en'],'zh':''})
                continue
            pieces.append(f'<section class="pair {kind}" id="{b["id"]}"><div class="en" lang="en"><span class="lang-label">ENGLISH</span>{source}</div><div class="zh" lang="zh-CN"><span class="lang-label">中文</span>{text_html(b["zh"],epub)}</div></section>')
            if not epub:search.append({'href':c['id']+'.html#'+b['id'],'chapter':chapter_label(c),'page':str(pn-22) if pn>=23 else 'PDF '+str(pn),'en':b['en'],'zh':b['zh']})
        if epub:
            pieces.append(f'<p class="page-original"><a href="source-p{pn:03d}.xhtml">查看 {label} 的完整原版面（PDF {pn}）</a></p>')
        else:
            pieces.append(f'<details class="page-original"><summary>查看 {label} 的完整原版面（PDF {pn}）</summary><a href="assets/pages/p{pn:03d}.png" target="_blank"><img loading="lazy" src="assets/pages/p{pn:03d}.png" alt="{label} 的原版面" /></a></details>')
    ci=chapters.index(c);prev=chapters[ci-1] if ci else None;nxt=chapters[ci+1] if ci+1<len(chapters) else None
    ext='xhtml' if epub else 'html'
    pieces.append('<nav class="chapter-nav">'+(f'<a href="{prev["id"]}.{ext}">← {E(chapter_label(prev))}</a>' if prev else f'<a href="index.{ext}">← 阅读首页</a>')+(f'<a href="{nxt["id"]}.{ext}">{E(chapter_label(nxt))} →</a>' if nxt else f'<a href="glossary.{ext}">术语表 →</a>')+'</nav>')
    return '\n'.join(pieces)

for c in chapters:
    (READER/(c['id']+'.html')).write_text(shell(chapter_label(c),chapter_body(c),c['id']),encoding='utf8')

policy='<ol>'+''.join('<li>'+E(s)+'</li>' for s in glossary['translation_policy'])+'</ol>'
gloss_body=f'<header class="chapter-title"><div class="eyebrow">Terminology / 翻译规范</div><h1>中英术语表与译例</h1><div class="english-title">Terminology &amp; Editorial Principles</div></header><h2 class="section-title">翻译与对照原则</h2>{policy}<h2 class="section-title">统一术语</h2><table class="term-table"><thead><tr><th>English</th><th>中文与用法</th></tr></thead><tbody>'+''.join(f'<tr><td lang="en">{E(en)}</td><td>{E(zh)}<small>{E(note)}</small></td></tr>' for en,zh,note in glossary['terms'])+'</tbody></table><h2 class="section-title">术语核对资料</h2><p class="footnote">以下资料仅用于核对术语用法，不替代或更新原著内容。核对日期：2026-11-20。</p><ul>'+''.join(f'<li><a href="{E(x["url"])}">{E(x["title"])}</a></li>' for x in glossary['sources'])+'</ul>'
(READER/'glossary.html').write_text(shell('中英术语表',gloss_body),encoding='utf8')
cards=''.join(f'<a class="chapter-card" href="{c["id"]}.html"><span class="number">{("CHAPTER "+c["id"][2:]) if c["id"].startswith("ch") else "APPENDIX"}</span><strong>{E(c["title_zh"])}</strong><div class="sub" lang="en">{E(c["title_en"])}</div></a>' for c in chapters if c['id'].startswith('ch'))
home=f'''<section class="hero"><div class="eyebrow">Computer Architecture / 计算机体系结构</div><h1>内存一致性与<br>缓存一致性入门</h1><div class="english-title" lang="en">{EN_TITLE}<br>Second Edition</div><p class="meta">Vijay Nagarajan · Daniel J. Sorin · Mark D. Hill · David A. Wood<br>2020 第二版 / 简体中文 · 英文对照</p><div class="actions"><a class="button primary" href="ch01.html">从第一章开始阅读 →</a><a class="button hidden" id="resume" href="ch01.html">继续上次阅读</a><a class="button" href="front.html#p019b01">第二版前言</a></div></section><div class="reading-note"><p><strong>11 章 · 逐段中英对照 · 原图与公式 · 可搜索全文</strong></p><p>宽屏支持左右对照，手机自动上下排列。顶部可切换阅读模式、字号与夜间主题；章节末尾和侧栏均可翻页。阅读位置保存在本设备的浏览器中。</p><p>图表及其标题、标注保留英文原文，不作翻译。每页末尾可展开原书版面；数学符号和上下标以附带的原版面为准。</p></div><h2 class="section-title">章节目录</h2><div class="cards">{cards}</div><p><a href="front.html">卷首、摘要与两版前言</a>　·　<a href="bio.html">作者简介</a>　·　<a href="glossary.html">中英术语表</a></p><p class="footnote">翻译底本：用户提供的 primer2020_2nd_edition.pdf（296 个 PDF 页面）。正文原书页码 1–274 对应 PDF 第 23–296 页。原著版权 © 2020 Morgan &amp; Claypool。此译本保留原书的时代背景及技术论断；出版信息、作者履历中的“目前”均指原书成书时。</p>'''
(READER/'index.html').write_text(shell(TITLE,home),encoding='utf8')
(ASSETS/'search.js').write_text('window.BOOK_SEARCH='+json.dumps(search,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')

EPUB_CSS='''body{font-family:serif;line-height:1.75;margin:5%;color:#202d33}h1{font-size:1.8em;line-height:1.4}a{color:#14685e}.english-title{font-size:1.1em;color:#596a70}.eyebrow,.meta,.footnote,.page-marker,.page-original,.math-note{font-size:.75em;color:#596a70}.page-marker{border-top:1px solid #bbb;margin-top:2em;padding-top:.5em}.page-marker span+span{margin-left:2em}.pair{padding:1em 0;border-bottom:1px solid #ddd}.pair .en{color:#4c5c64;font-size:.95em;margin-bottom:1em}.pair .zh{font-size:1em}.lang-label{display:block;font-family:sans-serif;font-size:.65em;letter-spacing:.1em;color:#777;margin-bottom:.5em}.pair.heading{border-bottom:2px solid #14685e;margin-top:1.5em}.pair.heading .zh{font-size:1.3em;font-weight:bold}.pair.heading .en{font-size:.85em;margin-bottom:.4em}.pair.heading .lang-label{display:none}img{max-width:100%;height:auto}.graphic{margin:1.5em 0;padding:0}.graphic figcaption{font-size:.7em;color:#596a70}.math-source{display:block;margin-top:.7em}.term-table{width:100%;border-collapse:collapse;font-size:.85em}.term-table td,.term-table th{border-bottom:1px solid #ddd;text-align:left;vertical-align:top;padding:.6em}.term-table small{display:block}.local-toc a{display:block;font-size:.8em;padding:.2em}.chapter-nav{margin-top:2em;padding-top:1em;border-top:1px solid #aaa;font-size:.8em}.chapter-nav a{display:block;margin:.6em 0}.reading-note{font-size:.85em}.chapter-card{display:block;margin:1.4em 0}.chapter-card strong{display:block}.chapter-card .number,.chapter-card .sub{font-size:.8em}.hero h1{font-size:2em}.actions{display:none}.footnote{margin-top:2em}.page-original{margin:1.5em 0}'''

def xhtml(title,body):
    # XHTML requires XML-compatible void elements.
    body=re.sub(r'<br\s*>','<br />',body)
    return f'<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="zh-CN" xml:lang="zh-CN"><head><meta charset="utf-8"/><title>{E(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head><body>{body}</body></html>'

content={}
if (ASSETS/'cover.png').exists():content['cover.xhtml']=xhtml(TITLE,'<div style="text-align:center;margin:0"><img src="assets/cover.png" alt="内存一致性与缓存一致性入门，第二版，中英文对照译本封面" /></div>')
content['index.xhtml']=xhtml(TITLE,home.replace('.html','.xhtml').replace('<br>','<br />'))
for c in chapters:content[c['id']+'.xhtml']=xhtml(chapter_label(c),chapter_body(c,True))
content['glossary.xhtml']=xhtml('中英术语表',gloss_body)
navitems=[('index.xhtml','阅读首页')]+[(c['id']+'.xhtml',chapter_label(c)) for c in chapters]+[('glossary.xhtml','术语表与译例')]
navbody='<nav epub:type="toc" id="toc"><h1>目录</h1><ol>'+''.join(f'<li><a href="{fn}">{E(label)}</a></li>' for fn,label in navitems)+'</ol></nav>'
content['nav.xhtml']=xhtml('目录',navbody)
for pn in pages:
    c=next((c for c in chapters if c['pdf_start']<=pn<=c['pdf_end']),None)
    link=(c['id']+'.xhtml'+('#page-'+str(pn) if any(b['pdf_page']==pn for b in c['blocks']) else '')) if c else 'index.xhtml'
    content[f'source-p{pn:03d}.xhtml']=xhtml(f'原 PDF 第 {pn} 页',f'<p><a href="{link}">← 返回对应译文</a></p><h1>原 PDF 第 {pn} 页</h1><img src="assets/pages/p{pn:03d}.png" alt="原 PDF 第 {pn} 页"/>')

used_assets=set(re.findall(r'(?:src|href)="(assets/[^"]+\.png)"',''.join(content.values())))
opf_items=[];spine=[]
for i,(name,data) in enumerate(content.items()):
    itemid=f'doc{i}'
    props=' properties="nav"' if name=='nav.xhtml' else ''
    opf_items.append(f'<item id="{itemid}" href="{name}" media-type="application/xhtml+xml"{props}/>')
    if name!='nav.xhtml':spine.append(f'<itemref idref="{itemid}"'+(' linear="no"' if name.startswith('source-') else '')+'/>')
for i,name in enumerate(sorted(used_assets)):
    cover_prop=' properties="cover-image"' if name=='assets/cover.png' else ''
    opf_items.append(f'<item id="img{i}" href="{name}" media-type="image/png"{cover_prop}/>')
opf_items.append('<item id="style" href="style.css" media-type="text/css"/>')
uid='urn:sha256:'+hashlib.sha256((TITLE+'2020-bilingual').encode()).hexdigest()
opf=f'''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="zh-CN"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">{uid}</dc:identifier><dc:title>{TITLE}（第二版·中英对照）</dc:title><dc:language>zh-CN</dc:language><dc:language>en</dc:language><dc:creator>Vijay Nagarajan</dc:creator><dc:creator>Daniel J. Sorin</dc:creator><dc:creator>Mark D. Hill</dc:creator><dc:creator>David A. Wood</dc:creator><dc:source>doi:10.2200/S00962ED2V01Y201910CAC049</dc:source><dc:description>全书11章中英文逐段对照，附原图、公式版面、术语表及原页定位。</dc:description><dc:rights>Original work copyright © 2020 Morgan &amp; Claypool.</dc:rights><meta property="dcterms:modified">2026-11-20T00:00:00Z</meta></metadata><manifest>{''.join(opf_items)}</manifest><spine>{''.join(spine)}</spine></package>'''
epub=OUT/'内存一致性与缓存一致性入门_第二版_中英对照.epub'
with zipfile.ZipFile(epub,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED)
    z.writestr('META-INF/container.xml','<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
    z.writestr('EPUB/package.opf',opf);z.writestr('EPUB/style.css',EPUB_CSS)
    for name,data in content.items():ET.fromstring(data);z.writestr('EPUB/'+name,data)
    for name in sorted(used_assets):z.write(READER/name,'EPUB/'+name)
ET.fromstring(opf)

validation={'edition':'preview' if PREVIEW else 'complete','source_pdf_pages':296,'chapters':report,'total_blocks':sum(x['blocks'] for x in report),'translated_blocks':sum(x['translated'] for x in report),'original_only_blocks':len(original_only),'original_page_images':len(pages),'figure_regions':len(visuals),'formula_blocks':len(formulas),'table_code_rasters':len(rasters),'epub_xhtml_documents':len(content),'terminology_entries':len(glossary['terms'])}
(OUT/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8')
with zipfile.ZipFile(OUT/'中英对照_离线阅读版.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in READER.glob('*.html'):z.write(p,'reader/'+p.name)
    for name in ('reader.css','reader.js','search.js'):z.write(ASSETS/name,'reader/assets/'+name)
    for name in sorted(used_assets):z.write(READER/name,'reader/'+name)
    z.writestr('开始阅读.txt','解压全部文件，打开 reader/index.html 即可离线阅读。\n请保留 assets 文件夹。手机和电子书阅读器可使用另行提供的 EPUB。\n')
print(json.dumps({k:v for k,v in validation.items() if k!='chapters'},ensure_ascii=False,indent=2))
print('EPUB MB:',round(epub.stat().st_size/1024/1024,2))
