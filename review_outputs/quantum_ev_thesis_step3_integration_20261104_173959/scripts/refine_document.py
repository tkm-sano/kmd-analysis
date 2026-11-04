from pathlib import Path
import csv,json
O=Path(__file__).resolve().parents[1]
p=O/'scripts/build_docx.py';s=p.read_text()
s=s.replace("x=tables[id];caption(x['caption'],'Table',id)","x=tables[id];cp=caption(x['caption'],'Table',id)\n if id=='2-1':cp.paragraph_format.page_break_before=True")
s=s.replace("p=para(f\"[{x['literature_id']}] {x['authors']}（{x['year']}）. {x['title']}. \")", "p=para(f\"[{x['literature_id']}] {x['authors']}（{x['year']}）. {x['title']}. {x.get('publication_details','')} \")")
p.write_text(s)
p=O/'LITERATURE_SELECTION_LEDGER.csv';rows=list(csv.DictReader(p.open()));log=[]
for x in rows:
 if x['literature_id']=='H01':continue
 src=O/x['source_json'];j=json.load(src.open())
 if j.get('http_status')!=200:
  retry=src.with_name(src.stem+'_retry.json')
  if retry.is_file() and json.load(retry.open()).get('http_status')==200:
   x['source_json']=str(retry.relative_to(O));j=json.load(retry.open());log.append(f"{x['literature_id']}: source JSON changed to successful retry")
 d=j.get('response',{})
 assert d.get('cited_by_count')==int(float(x['citation_count'])),x['literature_id']
 assert d.get('id')==x['OpenAlex_id'],x['literature_id']
 b=d.get('biblio')or{};journal=((d.get('primary_location')or{}).get('source')or{}).get('display_name','')
 detail=journal
 if b.get('volume'):detail+=', '+b['volume']
 if b.get('issue'):detail+='('+b['issue']+')'
 if b.get('first_page'):detail+=', '+b['first_page']+('–'+b['last_page'] if b.get('last_page') and b['last_page']!=b['first_page'] else '')
 x['publication_details']=detail+'.' if detail else ''
 # Author primary page uses Wei Feng, while OpenAlex expands given name differently.
 if x['literature_id']=='L13':
  x['authors']='Wei Feng; Miguel Figliozzi';x['metadata_correction']='Author byline Wei Feng in author-hosted published PDF; OpenAlex Wei Dong Feng not adopted';log.append('L13 primary byline Wei Feng used')
keys=list(dict.fromkeys(k for x in rows for k in x))
with p.open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
(O/'BIBLIOGRAPHIC_CORRECTIONS.md').write_text('# 書誌補正と照合\n\n'+'\n'.join(log)+'\n\n全26件のOpenAlex idと被引用数を保存JSONへ再照合した。巻年とオンライン公開年を区別し、巻号・ページを追加した。L14の誤取得PDFはタイトル照合で棄却し、正しい著者版へ差し替えた。REJECTEDファイルは根拠に用いない。\n')
# Make primary fetch script unambiguous on rerun.
p=O/'scripts/fetch_literature.py';s=p.read_text().replace('10.1016/j.jtrangeo.2012.01.035','10.1016/j.jtrangeo.2012.01.021').replace('max_workers=6','max_workers=1');p.write_text(s)
