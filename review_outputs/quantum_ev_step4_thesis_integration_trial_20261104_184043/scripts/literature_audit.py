from pathlib import Path
import re,json,time,concurrent.futures,urllib.parse
import requests,pandas as pd
from docx import Document
O=Path(__file__).resolve().parents[1];R=O.parents[1];OTHER=R/'review_outputs/quantum_ev_thesis_step3_integration_20261104_173959';P=OTHER/'sources/literature';D=Document(O/'sources/BASELINE_THESIS.docx');dest=O/'sources/literature';dest.mkdir(exist_ok=True)
# Bibliographic units from all original references, not only selected new citations.
units=[];cur=[]
for i in range(371,445):
 t=D.paragraphs[i].text
 if t.startswith('- ') or re.match(r'^(Chen,|Faraji-Niri,|Robinson,|IPCC\.|Schot,|Geels,|Rotolo,|Arvidsson,|Palackal,|Delgado,|Field,)',t):
  if cur:units.append(cur)
  cur=[(i,t)]
 elif cur:cur.append((i,t))
if cur:units.append(cur)
refs=[]
for j,u in enumerate(units,1):
 text=' '.join(x[1] for x in u);urls=re.findall(r'https?://[^\s。]+',text);doi=next((x.split('doi.org/')[1].rstrip('；;，,') for x in urls if 'doi.org/' in x),'');refs.append(dict(reference_id=f'OR{j:02d}',original_indices=';'.join(str(x[0]) for x in u),original_text=text,DOI=doi,URL=urls[0] if urls else '',metadata_status='HOLD',claim_support_status='HOLD_NOT_FULLTEXT_VERIFIED',usage='原書誌は保存付録へ保全；主論証での利用は別審査'))
# IPCC and Papachristos are reviewed separately rather than pretending malformed original groups are clean citations.
refs.append(dict(reference_id='PAPA_HOLD',original_indices='9;444;900',original_text='Papachristos（2018）元引用意図不明',DOI='',URL='https://discovery.ucl.ac.uk/id/eprint/10058753/',metadata_status='HOLD_ORIGINAL_INTENT',claim_support_status='HOLD',usage='原稿保全のみ；新本文の根拠引用から除外'))
def fetch(x):
 if not x['DOI']:return x
 key=re.sub('[^a-zA-Z0-9]','_',x['DOI']);f=dest/(key+'.crossref.json')
 try:
  r=requests.get('https://api.crossref.org/works/'+urllib.parse.quote(x['DOI'],safe=''),headers={'User-Agent':'KMD-thesis-trial/1.0 bibliographic-verification'},timeout=18);r.raise_for_status();j=r.json();f.write_text(json.dumps(j,ensure_ascii=False,indent=2));m=j['message'];x.update(metadata_status='PASS_REGISTRY_METADATA_ONLY',registry_title=';'.join(m.get('title',[])),registry_authors=';'.join(' '.join([a.get('given',''),a.get('family','')]).strip() for a in m.get('author',[])),registry_year=json.dumps(m.get('published',{}).get('date-parts',[])),registry_DOI=m.get('DOI',''),metadata_source=str(f),registry_URL='https://api.crossref.org/works/'+urllib.parse.quote(x['DOI'],safe=''))
 except Exception as e:x.update(metadata_status='HOLD_FETCH_FAILED',metadata_error=str(e))
 return x
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:refs=list(ex.map(fetch,refs))
pd.DataFrame(refs).to_csv(O/'BIBLIOGRAPHY_VERIFICATION.csv',index=False)
# Copy and inspect actual primary texts; never use old adoption labels as verification.
selected=['L01','L04','L05','L06','L09','L11','L13','L14','L15'];reads=[]
for id in selected:
 p=P/(id+'_primary.txt')
 if p.is_file():
  text=p.read_text();(dest/p.name).write_text(text);reads.append(dict(id=id,source=str(p),characters=len(text),opening=text[:1800],keywords=[line[:280] for line in text.splitlines() if any(s in line.lower() for s in ['abstract','verification','validation','uncertainty','socio-technical','resource','vehicle'])][:16]))
(O/'evidence/PRIMARY_READING_EXTRACTS.json').write_text(json.dumps(reads,ensure_ascii=False,indent=2))
# New live first-party pages: preserve HTTP source, with extraction scope noted later.
urls={'Schneider2014':'https://pubsonline.informs.org/doi/abs/10.1287/trsc.2013.0490','Palackal2023':'https://arxiv.org/abs/2304.09629','Delgado2022':'https://arxiv.org/abs/2204.11890','Farhi2014':'https://arxiv.org/abs/1411.4028','Hadfield2019':'https://arxiv.org/abs/1709.03489','Bartschi2020':'https://arxiv.org/abs/2006.00354','Papachristos2019_candidate':'https://discovery.ucl.ac.uk/id/eprint/10058753/'}
logs=[]
def page(kv):
 k,url=kv
 try:
  r=requests.get(url,timeout=18);r.raise_for_status();f=dest/(k+'.html');f.write_text(r.text);return dict(id=k,url=url,status=r.status_code,path=str(f),scope='publisher/author-archive page; abstract scope only')
 except Exception as e:return dict(id=k,url=url,status='HOLD_HTTP',error=str(e),scope='web tool read may exist separately')
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:logs=list(ex.map(page,urls.items()))
(O/'evidence/LITERATURE_RETRIEVAL_LOG.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2));print('Original units',len(refs),'metadata status',pd.DataFrame(refs).metadata_status.value_counts().to_dict());print('Primary extracts',len(reads))
