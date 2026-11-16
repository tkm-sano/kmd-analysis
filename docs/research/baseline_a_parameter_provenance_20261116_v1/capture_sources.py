"""Read-only public-source capture; writes exclusively into this new dossier."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, subprocess, urllib.request

OUT = Path(__file__).resolve().parent
URLS = {
 'S01': 'https://www.sagawa-exp.co.jp/customer/send/guide/beginners/',
 'S02': 'https://www.sagawa-exp.co.jp/about-csr/column/article_02.html',
 'S03a': 'https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02_01.pdf',
 'S03b': 'https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02_02.pdf',
 'S04': 'https://www.yamato-hd.co.jp/facilities/kansai-gateway/pdf/childpamphlet_jp.pdf',
 'S05': 'https://shigoto.mhlw.go.jp/Occupation/Detail?occupationId=483',
 'S09': 'https://www.j-m-t.co.jp/terminal/',
 'S12': 'https://developers.google.com/optimization/routing/cvrptw_resources',
 'S13': 'https://m.media-amazon.com/images/G/01/DSP2/DSP_Brochure_Japanese_V1.1.pdf',
 'S14': 'https://project-osrm.org/docs/v5.27.1/api/',
}

def capture(item):
 key,url=item
 rec={'id':key,'url':url,'accessed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (research source verification)'})
  with urllib.request.urlopen(req,timeout=25) as r:
   data=r.read(); rec.update(http_status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type'))
  suffix='.pdf' if data.startswith(b'%PDF') else '.html'
  path=OUT/'sources'/(key+suffix)
  with path.open('xb') as f:f.write(data)
  rec.update(file=str(path.relative_to(OUT)),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),status='RETAINED')
  if key=='S05' and not all(t.encode('utf-8') in data for t in ['宅配便配達員','営業所']):
   rec['status']='HTTP_SUCCESS_BODY_NOT_CONFIRMED_USE_WEB_VIEW'
  if suffix=='.pdf':
   dest=path.with_suffix('.txt')
   r=subprocess.run(['pdftotext','-layout',str(path),str(dest)],capture_output=True,text=True)
   rec['text_extraction_exit']=r.returncode
 except Exception as e:
  rec.update(status='RETRIEVAL_FAILED',error=type(e).__name__+': '+str(e))
 return rec

if __name__=='__main__':
 (OUT/'sources').mkdir(exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  results=list(pool.map(capture,URLS.items()))
 with (OUT/'SOURCE_ACCESS_LOG.json').open('x') as f:
  json.dump({'purpose':'source verification, not evidence of original parameter adoption','sources':results},f,ensure_ascii=False,indent=2)
 print([(r['id'],r['status']) for r in results])
