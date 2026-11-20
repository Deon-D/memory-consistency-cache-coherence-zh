import json,pathlib,re,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
issues=[];stats=[]
for f in sorted((ROOT/'source').glob('ch*.json')):
    c=json.loads(f.read_text(encoding='utf8'));tf=ROOT/'translations'/f.name
    if not tf.exists():continue
    tr=json.loads(tf.read_text(encoding='utf-8-sig'))
    for b in c['blocks']:
        if b['id'] not in tr:continue
        en=b['en'];zh=tr[b['id']]
        words=len(en.split());han=len(re.findall('[\u3400-\u9fff]',zh))
        if words>=65 and han<words*.75 and not re.match(r'^\[\d+\]',en):
            issues.append({'id':b['id'],'chapter':c['id'],'type':'short_translation_review','words':words,'han':han,'en':en,'zh':zh})
        if re.search('待翻译|TODO|待补|译文制作中',zh):issues.append({'id':b['id'],'type':'placeholder','zh':zh})
        if '(cid:' in zh:issues.append({'id':b['id'],'type':'unresolved_pdf_encoding','zh':zh})
        if zh==en and re.search('[A-Za-z]{3,}',en) and len(en)>100:issues.append({'id':b['id'],'type':'unchanged_english','zh':zh})
    stats.append((c['id'],len(tr),len(c['blocks'])))
(ROOT/'qa'/'translation-audit.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf8')
print('Coverage:',stats)
print('Flagged for review:',[(i['id'],i['type'],i.get('words'),i.get('han')) for i in issues])
