from pathlib import Path
import requests,concurrent.futures,hashlib,json
B=Path(__file__).parent/'sources'
u={
'amazon_dsp.pdf':'https://m.media-amazon.com/images/G/01/DSP2/DSP_Brochure_Japanese_V1.1.pdf',
'amazon_2024_ds.html':'https://press.aboutamazon.com/jp/2024/9/amazon-opens-new-delivery-bases-in-15-locations-across-japan',
'amazon_jp_history.html':'https://www.aboutamazon.jp/news/delivery-and-logistics/amazon-logistics-five-year-journey',
'amazon_jp_process.html':'https://www.aboutamazon.jp/news/delivery-and-logistics/see-how-your-orders-reach-you-from-an-amazon-fulfilment-center',
'amazon_flex_terms.pdf':'https://m.media-amazon.com/images/G/09/FlexComm/Document/AmazonFlexJP_Revised_Terms_Conditions_20241002.pdf',
'yamato_2024.pdf':'https://www.yamato-hd.co.jp/investors/pdf/4q_setsumei_2024_03.pdf',
'yamato_history.pdf':'https://www.yamato-hd.co.jp/100th-anniversary/assets/pdf/top/429_496.pdf',
'yamato_2022.pdf':'https://www.yamato-hd.co.jp/investors/library/annualreport/pdf/j_ir2022_3_00_A3.pdf',
'amazon_area.html':'https://www.amazon.jobs/content/jp/teams/fulfillment-and-operations/area-management/japan/',
'amazon_flex_faq.html':'https://flex.amazon.co.jp/faq',
'amazon_hellowork.pdf':'https://jsite.mhlw.go.jp/tokyo-hellowork/content/contents/002226767.pdf'}
def f(kv):
 k,url=kv
 try:
  r=requests.get(url,timeout=30);(B/k).write_bytes(r.content);return dict(file=k,url=url,final_url=r.url,status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),access_date='2026-11-05')
 except Exception as e:return dict(file=k,url=url,error=str(e),access_date='2026-11-05')
rr=list(concurrent.futures.ThreadPoolExecutor(7).map(f,u.items()));(B/'manifest.json').write_text(json.dumps(rr,ensure_ascii=False,indent=2));print(json.dumps(rr,ensure_ascii=False))
