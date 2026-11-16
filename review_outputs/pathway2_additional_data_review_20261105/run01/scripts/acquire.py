from pathlib import Path
import os,json,hashlib,concurrent.futures,datetime
import requests,subprocess
R=Path('/home/takuma/kmd-analysis');O=R/'review_outputs/pathway2_additional_data_review_20261105/run01'
requests.packages.urllib3.disable_warnings()
def fetch(item):
 name,url=item
 row=dict(source_id=name,url=url,access_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 try:
  r=requests.get(url,timeout=50,headers={'User-Agent':'Mozilla/5.0 (Academic literature verification)'})
  row.update(status_code=r.status_code,final_url=r.url,content_type=r.headers.get('Content-Type',''),bytes=len(r.content))
  ext='pdf' if r.content[:4]==b'%PDF' else ('xlsx' if r.content[:2]==b'PK' and '.xlsx' in url else 'zip' if r.content[:2]==b'PK' else 'html')
  p=O/'sources'/f'{name}.{ext}';p.write_bytes(r.content);row.update(local_path=str(p.relative_to(O)),sha256=hashlib.sha256(r.content).hexdigest(),valid_pdf=ext=='pdf')
  if ext=='pdf':
   subprocess.run(['pdftotext','-layout',str(p),str(p.with_suffix('.txt'))],check=True);row['pages']=p.with_suffix('.txt').read_text().count('\f')
 except Exception as e:row.update(error=str(e))
 return row
if __name__=='__main__':
 import csv,sys
 items=[('CHEN_AUTHOR','https://henkelmanlab.org/pubs/chen20_3411.pdf'),('CHEN_PUBLISHER','https://www.nature.com/articles/s41467-020-17126-3'),('CHEN_SI','https://static-content.springer-cdn.com/esm/art%3A10.1038%2Fs41467-020-17126-3/MediaObjects/41467_2020_17126_MOESM1_ESM.pdf'),('BATPAC_V5_MANUAL','https://publications.anl.gov/anlpubs/2022/07/176234.pdf')]
 if len(sys.argv)>1:items=json.loads(Path(sys.argv[1]).read_text())
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(fetch,items))
 dst=O/'evidence/ACQUISITION_LOG.jsonl'
 with dst.open('a') as f:
  for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n');print(json.dumps(row,ensure_ascii=False),flush=True)
