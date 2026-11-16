import urllib.request,concurrent.futures,json,hashlib,datetime,subprocess
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parent
class Parser(HTMLParser):
 def __init__(self): super().__init__();self.text=[];self.links=[];self.skip=0
 def handle_starttag(self,t,a):
  if t in ('script','style'): self.skip+=1
  for k,v in a:
   if k=='href' and v:self.links.append(v)
 def handle_endtag(self,t):
  if t in ('script','style'):self.skip=max(0,self.skip-1)
 def handle_data(self,d):
  if not self.skip and d.strip():self.text.append(d.strip())
SOURCES={
'mhlw_jobtag':'https://shigoto.mhlw.go.jp/Occupation/Detail?occupationId=483',
'meti_digital_index':'https://www.meti.go.jp/policy/economy/distribution/logistics_digital_service.html',
'meti_cases_v11':'https://www.meti.go.jp/policy/economy/distribution/sippers-judgment-criteria-casestudies-book_ver.1.1.pdf',
'meti_hayashi':'https://www.meti.go.jp/policy/it_policy/jinzai/Results_of_Collaborations_with_Companies_2025.pdf',
'meti_digital_mlit_mirror':'https://wwwtb.mlit.go.jp/chugoku/content/000333821.pdf',
'mlit_dx':'https://www.mlit.go.jp/seisakutokatsu/freight/content/001609016.pdf',
'mlit_dispatch':'https://wwwtb.mlit.go.jp/chugoku/content/000364956.pdf',
'maff_logitem':'https://www.maff.go.jp/j/shokusan/ryutu/attach/pdf/buturyu-603.pdf',
'mhlw_pascal':'https://jsite.mhlw.go.jp/kanagawa-roudoukyoku/content/contents/002420168.pdf',
'nihonyubin':'https://loogia.jp/cases/nihonyubin/'
}
def fetch(item):
 key,url=item;d={'id':key,'url':url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35) as resp:raw=resp.read();d.update(status=resp.status,final_url=resp.url,content_type=resp.headers.get('Content-Type'))
  ext='.pdf' if raw[:4]==b'%PDF' else '.html';p=ROOT/'sources'/(key+ext);p.write_bytes(raw)
  d.update(path=str(p.relative_to(Path.cwd())),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
  txt=p.with_suffix('.txt')
  if ext=='.pdf':subprocess.run(['pdftotext','-layout',str(p),str(txt)],check=True,capture_output=True)
  else:
   parser=Parser();parser.feed(raw.decode('utf-8',errors='replace'));txt.write_text('\n'.join(parser.text));p.with_suffix('.links.json').write_text(json.dumps(parser.links,ensure_ascii=False,indent=2))
  d.update(text_path=str(txt.relative_to(Path.cwd())),text_sha256=hashlib.sha256(txt.read_bytes()).hexdigest())
 except Exception as e:d['error']=type(e).__name__+': '+str(e)
 return d
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:rows=list(pool.map(fetch,SOURCES.items()))
 (ROOT/'SOURCE_MANIFEST.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 for row in rows:print(row['id'],row.get('status',row.get('error')),row.get('bytes',''))
