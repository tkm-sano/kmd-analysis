"""Bounded GET of public primary sources only. Never submits a form."""
from pathlib import Path
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import urllib.request

HERE = Path(__file__).resolve().parent
SOURCES = {
 'JP_LOOGIA': 'https://loogia.jp/cases/nihonyubin/',
 'JP_2020_RELEASE': 'https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02_01.pdf',
 'JP_2020_APPENDIX': 'https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02_02.pdf',
 'JP_2019_OPTIMIND': 'https://www.post.japanpost.jp/notification/pressrelease/2019/00_honsha/0205_01_03.pdf',
 'CB_2021_RELEASE': 'https://prtimes.jp/main/html/rd/p/000000081.000016726.html',
 'SAFIE_JP_2024': 'https://safie.co.jp/news/3661/',
 'HACOBU_JP_2024': 'https://hacobu.jp/news/12571/',
 'HACOBU_CSV_TECH': 'https://hacobu.jp/news/14674/',
 'JP_INQUIRY': 'https://www.post.japanpost.jp/question/contact-us/inquiry.html',
 'OPTIMIND_INQUIRY': 'https://www.optimind.tech/contact/',
 'HACOBU_INQUIRY': 'https://hacobu.jp/form/contact/',
 'SAFIE_INQUIRY': 'https://safie.co.jp/inquiry/',
 'JP_PDX_DATA': 'https://www.post.japanpost.jp/about/other/pdxdata.html',
 'JP_INNOVATION': 'https://www.post.japanpost.jp/about/open-innovation/',
 'JP_INNOVATION_THEME': 'https://www.post.japanpost.jp/assets/docs/about/open-innovation/theme03.pdf',
 'JP_INNOVATION_CONTACT': 'https://www.post.japanpost.jp/about/open-innovation/contact/',
 'JP_GROUP_ENV': 'https://www.japanpost.jp/sustainability/librarydata/environment/',
 'TOKYO_JP_DATA': 'https://www.tdpf-hp.metro.tokyo.lg.jp/wp-content/uploads/2024/03/TDPF%E3%82%AD%E3%83%83%E3%82%AF%E3%82%AA%E3%83%95%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88.pdf',
 'NISHIMERA_PAPER': 'https://www.jstage.jst.go.jp/article/jste/5/1/5_11/_pdf/-char/ja',
 'NISHIMERA_AUTHOR': 'https://hyokadb02.jimu.kyutech.ac.jp/html/100000644_ja.html',
 'UTOKYO_CHECK': 'https://www.u-tokyo.ac.jp/adm/uci/ja/projects/region/project_00075.html',
 'MLIT_CENSUS': 'https://www.mlit.go.jp/statistics/details/t-other-2_tk_000196.html',
 'MLIT_WAIT_SURVEY': 'https://www.mlit.go.jp/report/press/content/002011131.pdf',
 'MLIT_WAIT_DX': 'https://www.mlit.go.jp/jidosha/content/001993650.pdf',
 'NTT_JP_2026': 'https://www.ntt-east.co.jp/release/detail/20261028_02.html',
 'JP_CB_NOTICE_2026': 'https://www.post.japanpost.jp/newsrelease/pressrelease/414336381813.html',
 'JP_ROBOT_NPA': 'https://www.npa.go.jp/bureau/traffic/council/mobility/0412-3.pdf',
 'OSRM': 'https://project-osrm.org/docs/v26.5.0/http',
}


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ignored = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'):
            self.ignored += 1
        if tag in ('p','div','br','li','tr','h1','h2','h3','h4'):
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style') and self.ignored:
            self.ignored -= 1
        if tag in ('p','div','li','tr','h1','h2','h3','h4'):
            self.parts.append('\n')
    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


def fetch(item):
    sid, url = item
    rec = {'id':sid,'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'method':'GET'}
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'research-source-audit/1.0'}),timeout=30) as r:
            raw = r.read(25000001)
            if len(raw)>25000000:
                raise ValueError('25MB bounded download exceeded')
            typ=r.headers.get('Content-Type','')
            suffix='.pdf' if raw.startswith(b'%PDF') else '.html'
            rec.update(status=r.status,final_url=r.url,content_type=typ,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        p=HERE/'sources'/(sid+suffix)
        p.write_bytes(raw)
        rec['archive']=str(p)
        txt=p.with_suffix('.txt')
        if suffix=='.pdf':
            subprocess.run(['pdftotext','-layout',str(p),str(txt)],check=True,capture_output=True)
        else:
            match=re.search(r'charset=[\x27\x22]?([a-zA-Z0-9_-]+)',raw[:16384].decode('ascii',errors='ignore'),re.I)
            encoding=match.group(1) if match else 'utf-8'
            if encoding.lower().replace('-','_') in ('shift_jis','sjis'):
                encoding='cp932'
            rec['text_encoding']=encoding
            parser=PlainText();parser.feed(raw.decode(encoding))
            txt.write_text('\n'.join(line.strip() for line in ''.join(parser.parts).splitlines() if line.strip())+'\n')
        rec['text']=str(txt)
        rec['text_sha256']=hashlib.sha256(txt.read_bytes()).hexdigest()
    except Exception as exc:
        rec['error']=str(exc)
    return rec


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=5) as pool:
        records=list(pool.map(fetch,SOURCES.items()))
    (HERE/'SOURCE_MANIFEST.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    for r in records:
        print(r['id'],r.get('bytes'),r.get('error','OK'))
