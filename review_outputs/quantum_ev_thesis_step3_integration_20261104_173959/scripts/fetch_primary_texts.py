from pathlib import Path
import requests,json,csv,subprocess,datetime,concurrent.futures
from lxml import html
from urllib.parse import urljoin
O=Path(__file__).resolve().parents[1];D=O/'sources/literature';log=[]
seeds={
'L01':['https://ris.utwente.nl/ws/files/6761018/Geels02technological.pdf'],
'L02':['https://www.diva-portal.org/smash/get/diva2%3A267496/FULLTEXT01.pdf'],
'L03':['https://dspace.library.uu.nl/bitstream/1874/385298/1/Functions.pdf'],
'L04':['https://arxiv.org/pdf/1503.00673'],
'L05':['https://sro.sussex.ac.uk/id/eprint/79450/1/__its-home.uscs.susx.ac.uk_home_tb263_Desktop_1-s2.0-S0048733318301987-main.pdf'],
'L06':['https://discovery.ucl.ac.uk/id/eprint/1447670/1/1-s2.0-S0016328714001232-main.pdf'],
'L07':['https://pubs.rsc.org/en/content/articlepdf/2019/ee/c8ee01157e'],
'L08':['https://spiral.imperial.ac.uk/entities/publication/7b9bf45e-50ee-4a7c-8dec-ed6bb776e9a7'],
'L09':['https://zero.lab.princeton.edu/wp-content/uploads/2026/03/Sepulveda-et-al-Firm-low-carbon-resources-Joule-2018-with-SI.pdf'],
'L11':['https://pure.manchester.ac.uk/ws/files/20381442/POST-PEER-REVIEW-PUBLISHERS.PDF'],
'L12':['https://research.tudelft.nl/en/publications/the-influence-of-financial-incentives-and-other-socio-economic-fa/'],
'L13':['https://web.cecs.pdx.edu/~maf/Journals/2012_An_Economic_and_Technological_Analysis_of_the_Key_Factors_Affecting_the_Competitiveness_of_Electric_Commercial_Vehicles.pdf'],
'L14':['https://web.cecs.pdx.edu/~maf/publications.html'],
'L15':['https://elib.dlr.de/88873/']}
def fetch(item):
 id,urls=item;result=[];queue=list(urls);seen=set();pdf=None
 for _ in range(6):
  if not queue:break
  url=queue.pop(0)
  if url in seen:continue
  seen.add(url);rec={'literature_id':id,'url':url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  try:
   r=requests.get(url,timeout=25);rec.update(http_status=r.status_code,final_url=r.url,bytes=len(r.content));r.raise_for_status()
   if r.content.startswith(b'%PDF'):
    pdf=D/(id+'_primary.pdf');pdf.write_bytes(r.content);subprocess.run(['pdftotext','-layout',str(pdf),str(D/(id+'_primary.txt'))],check=True);rec['saved']=str(pdf.relative_to(O));result.append(rec);break
   fn=D/(id+'_primary_landing.html');fn.write_text(r.text);rec['saved']=str(fn.relative_to(O));soup=html.fromstring(r.text)
   links=[]
   for a in soup.xpath('//a[@href]'):
    href=urljoin(r.url,a.get('href'));label=a.text_content().lower()
    if ('.pdf' in href.lower() or 'fulltext' in href.lower() or ('pdf' in label and 'download' not in href.lower())) and not href.endswith('#'):links.append(href)
    if id=='L14':
     context=a.getparent().text_content().lower()
     if 'methodology to evaluate the competitiveness' in context and '.pdf' in href.lower():links.insert(0,href)
   queue=links[:4]+queue
  except Exception as e:rec['error']=str(e)
  result.append(rec)
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for rr in ex.map(fetch,seeds.items()):log.extend(rr)
# Figshare preserves the author's article where publisher endpoints are unavailable.
for id,aid in [('L01',23337872),('L05',23462756)]:
 if (D/(id+'_primary.pdf')).exists():continue
 u=f'https://api.figshare.com/v2/articles/{aid}';r=requests.get(u,timeout=20)
 if r.ok:
  data=r.json();(D/(id+'_figshare.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2))
  for f in data.get('files',[]):
   if f['name'].lower().endswith('.pdf'):
    try:
     z=requests.get(f['download_url'],timeout=25);z.raise_for_status()
     if z.content.startswith(b'%PDF'):
      p=D/(id+'_primary.pdf');p.write_bytes(z.content);subprocess.run(['pdftotext','-layout',str(p),str(D/(id+'_primary.txt'))],check=True);log.append({'literature_id':id,'url':f['download_url'],'saved':str(p.relative_to(O)),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});break
    except Exception as e:log.append({'literature_id':id,'url':f['download_url'],'error':str(e)})
(D/'PRIMARY_RETRIEVAL_LOG.json').write_text(json.dumps(log,ensure_ascii=False,indent=2));print('retrieved PDFs:',[p.stem for p in D.glob('*_primary.pdf')]);print('attempts',len(log))
