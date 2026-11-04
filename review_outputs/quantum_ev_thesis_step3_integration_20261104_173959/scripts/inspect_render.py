from pathlib import Path
import sys,json,re
from PIL import Image,ImageOps,ImageDraw
O=Path(__file__).resolve().parents[1];sys.path.insert(0,'/home/takuma/kmd-analysis/review_outputs/thesis_docx_integration_20261103/run01/rendering_tools/python')
import fitz
pdf=fitz.open(O/'render/THESIS_UPDATED_STEP3.pdf');records=[]
for i,page in enumerate(pdf):
 pix=page.get_pixmap(matrix=fitz.Matrix(1,1));pix.save(str(O/f'render/page_{i+1:03}.png'))
 blocks=page.get_text('dict')['blocks'];txt=page.get_text(sort=True);(O/f'render/page_{i+1:03}.txt').write_text(txt)
 outside=[]
 for b in blocks:
  if b['bbox'][0]<-1 or b['bbox'][2]>page.rect.width+1 or b['bbox'][1]<-1 or b['bbox'][3]>page.rect.height+1:outside.append(b['bbox'])
 records.append(dict(page=i+1,width=page.rect.width,height=page.rect.height,text_chars=len(txt),replacement_chars=txt.count('\ufffd'),out_of_page_blocks=outside,images=len(page.get_images())))
for start in range(0,len(pdf),8):
 sheet=Image.new('RGB',(1200,900),'#ddd');d=ImageDraw.Draw(sheet)
 for offset in range(min(8,len(pdf)-start)):
  im=Image.open(O/f'render/page_{start+offset+1:03}.png');im.thumbnail((285,420));x=(offset%4)*300;y=(offset//4)*450
  sheet.paste(im,(x,y+22));d.text((x+5,y+3),str(start+offset+1),fill='black')
 sheet.save(O/f'render/contact_{start+1:03}.jpg',quality=90)
(O/'RENDER_AUDIT.json').write_text(json.dumps(dict(pages=len(pdf),records=records),indent=2));print('pages',len(pdf))
