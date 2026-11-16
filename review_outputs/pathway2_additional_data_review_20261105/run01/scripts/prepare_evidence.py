from pathlib import Path
from html.parser import HTMLParser
import subprocess,xml.etree.ElementTree as E,base64,shutil
O=Path(__file__).resolve().parents[1]
class Text(HTMLParser):
    def __init__(self):super().__init__();self.out=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ['script','style']:self.skip+=1
        if tag in ['p','h1','h2','h3','h4','li','tr','section'] and not self.skip:self.out.append('\n')
    def handle_endtag(self,tag):
        if tag in ['script','style']:self.skip=max(0,self.skip-1)
        if tag in ['p','h1','h2','h3','h4','li','tr','section'] and not self.skip:self.out.append('\n')
    def handle_data(self,data):
        if not self.skip:self.out.append(data)
for name in ['CHEN_PUBLISHER','CHEN_PMC','CHEN_LAB_PUBS','LMR2026_FULL','RATE2026_FULL']:
    f=O/'sources'/(name+'.html');s=Text();s.feed(f.read_text());f.with_suffix('.readable.txt').write_text(''.join(s.out))
for name in ['LMR2026_DATA','RATE2026_DATA']:
    src=O/'sources'/(name+'.html');dst=src.with_suffix('.xlsx')
    if not dst.exists() and src.exists() and src.read_bytes()[:2]==b'PK':shutil.copyfile(src,dst)
pdf=O/'sources/CHEN_AUTHOR.pdf';svg=O/'evidence/CHEN_FIG5.svg'
subprocess.run(['pdftoppm','-f','8','-l','8','-singlefile','-r','140','-png',str(pdf),str(svg.with_suffix(''))],check=True)
subprocess.run(['pdftocairo','-f','8','-l','8','-svg',str(pdf),str(svg)],check=True)
for n in E.parse(svg).getroot().iter('{http://www.w3.org/2000/svg}image'):
    name=n.attrib['id']
    (O/'evidence'/(name+'.png')).write_bytes(base64.b64decode(n.attrib['{http://www.w3.org/1999/xlink}href'].split(',')[1]))
for page,name,res in [(46,'BATPAC_CHEM_PAGE46',170),(48,'BATPAC_INPUT_PAGE48',110)]:
    subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-singlefile','-r',str(res),'-png',str(O/'sources/BATPAC_NHTSA.pdf'),str(O/'evidence'/name)],check=True)
