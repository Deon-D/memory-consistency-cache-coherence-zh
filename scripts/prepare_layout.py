import pathlib,json,re,collections
import pdfplumber
from PIL import Image,ImageOps,ImageDraw
ROOT=pathlib.Path(__file__).resolve().parents[1]
ASSETS=ROOT/'output'/'reader'/'assets'
(ASSETS/'formulas').mkdir(exist_ok=True)
(ASSETS/'blocks').mkdir(exist_ok=True)
doc=pdfplumber.open(ROOT/'primer2020_2nd_edition.pdf')
formulas={};rasters={}
for f in sorted((ROOT/'source').glob('ch*.json')):
    chapter=json.loads(f.read_text(encoding='utf8'))
    for b in chapter['blocks']:
        p=doc.pages[b['pdf_page']-1];box=b['bbox']
        cs=[c for c in p.chars if c['x0']>=box[0]-1 and c['x1']<=box[2]+1 and c['top']>=box[1]-1 and c['bottom']<=box[3]+1]
        math=[c for c in cs if 'MT2' in c['fontname']]
        tablechars=[c for c in cs if any(k in c['fontname'] for k in ('TimesNewRoman','LMMono','NimbusRom'))]
        tablecells=[r for r in p.rects if 5<r['height']<120 and r['width']>10 and r['top']<box[3] and r['bottom']>box[1] and r['x0']<box[2] and r['x1']>box[0]]
        if math:
            name=f"formulas/{b['id']}.png"
            if not (ASSETS/name).exists():p.crop((box[0]-3,box[1]-3,box[2]+3,box[3]+3)).to_image(resolution=180,antialias=True).save(ASSETS/name)
            formulas[b['id']]=name
        elif len(tablechars)>max(2,len(cs)*.6) or len(tablecells)>=3:
            name=f"blocks/{b['id']}.png"
            p.crop((box[0]-3,box[1]-3,box[2]+3,box[3]+3)).to_image(resolution=180,antialias=True).save(ASSETS/name)
            rasters[b['id']]=name
(ROOT/'source'/'formulas.json').write_text(json.dumps(formulas,indent=2),encoding='utf8')
(ROOT/'source'/'block_rasters.json').write_text(json.dumps(rasters,indent=2),encoding='utf8')
files=sorted((ASSETS/'figures').glob('*.png'))
sample=files[::max(1,len(files)//24)][:24]
sheet=Image.new('RGB',(1200,6*260),'#eeeeee');dr=ImageDraw.Draw(sheet)
for i,f in enumerate(sample):
    im=Image.open(f).convert('RGB');im.thumbnail((280,225))
    x=(i%4)*300+(300-im.width)//2;y=(i//4)*260+25
    sheet.paste(im,(x,y));dr.text(((i%4)*300+10,(i//4)*260+6),f.name,fill='black')
(ROOT/'qa').mkdir(exist_ok=True)
sheet.save(ROOT/'qa'/'figure-contact-sheet.jpg')
print('Formula blocks:',len(formulas),'Table/code blocks:',len(rasters))
