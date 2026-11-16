from pathlib import Path
import requests,concurrent.futures,json,hashlib
B=Path(__file__).parent/'sources'
urls={
'kanto.pdf':'https://wwwtb.mlit.go.jp/kanto/content/000364901.pdf',
'matsudo.pdf':'https://www.cao.go.jp/consumer/iinkaikouhyou/2021/doc/202108_winwin_jirei_3a.pdf',
'pt.html':'https://www.tokyo-pt.jp/special_logistics_6th',
'amazon_schema.md':'https://raw.githubusercontent.com/MIT-CAVE/rc-cli/main/templates/data_structures.md',
'amazon_listing.xml':'https://amazon-last-mile-challenges.s3.us-west-2.amazonaws.com/?list-type=2',
'pyvrp_api.html':'https://pyvrp.github.io/v0.12.0/api/pyvrp.html',
'pyvrp_model.html':'https://pyvrp.github.io/v0.12.0/api/model.html',
'sg.html':'https://www.sg-hldgs.co.jp/newsrelease/2021/1004_4840.html',
'loogia.html':'https://loogia.jp/cases/nihonyubin/',
'jmt.html':'https://www.j-m-t.co.jp/terminal/keihin.html',
'yamato_codes.html':'https://www.kuronekoyamato.co.jp/ytc/customer/send/services/sameday/sales_office/tokyo.html',
'amazon_paper.html':'https://pubsonline.informs.org/doi/10.1287/trsc.2022.1173',
'jp.pdf':'https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02_01.pdf',
'jp_appendix.pdf':'https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02_02.pdf'}
def fetch(kv):
 k,u=kv
 try:
  r=requests.get(u,timeout=40); p=B/k;p.write_bytes(r.content)
  return dict(file=k,url=u,status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),access_date='2026-11-05',final_url=r.url)
 except Exception as e:return dict(file=k,url=u,error=str(e))
rows=list(concurrent.futures.ThreadPoolExecutor(8).map(fetch,urls.items()))
(B/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print(json.dumps(rows,ensure_ascii=False,indent=2))
