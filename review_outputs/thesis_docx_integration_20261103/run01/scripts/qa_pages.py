from common import *
sys.path.insert(0,str(O/'rendering_tools/python'))
import fitz
from PIL import Image,ImageOps,ImageDraw
run=sys.argv[1] if len(sys.argv)>1 else 'render01';base=O/run;z=fitz.open(base/(OUT.stem+'.pdf'));pages=[];texts=[];imgs=[]
for i,p in enumerate(z):
 data=p.get_text('dict');spans=[sp for b in data['blocks'] if 'lines' in b for l in b['lines'] for sp in l['spans']];raw=p.get_text();texts.append({'page':i+1,'text':raw});overflow=[{'text':s['text'][:100],'bbox':s['bbox']} for s in spans if s['bbox'][0]<-1 or s['bbox'][2]>p.rect.width+1 or s['bbox'][1]<-1 or s['bbox'][3]>p.rect.height+1]
 imageinfo=p.get_image_info();badimages=[x['bbox'] for x in imageinfo if x['bbox'][0]<0 or x['bbox'][2]>p.rect.width+.1 or x['bbox'][1]<0 or x['bbox'][3]>p.rect.height+.1]
 pages.append({'page':i+1,'orientation':'LANDSCAPE' if p.rect.width>p.rect.height else 'PORTRAIT','text_characters':len(raw.strip()),'images':len(imageinfo),'text_outside_page':len(overflow),'images_outside_page':len(badimages),'replacement_characters':raw.count('\ufffd'),'possible_blank':len(raw.strip())<8 and not imageinfo,'overflow_detail':json.dumps(overflow,ensure_ascii=False),'automatic_status':'REVIEW' if overflow or badimages or '\ufffd' in raw else 'PASS_GEOMETRY'})
 dest=base/'pages'/f'page_{i+1:03d}.png';dest.parent.mkdir(exist_ok=True);p.get_pixmap(dpi=105,alpha=False).save(dest);imgs.append(dest)
# Labeled two-page contact sheets; every page remains available individually.
contact=base/'contact';contact.mkdir(exist_ok=True)
for i in range(0,len(imgs),2):
 canvas=Image.new('RGB',(1500,1100),'#c8c8c8');draw=ImageDraw.Draw(canvas)
 for j in range(2):
  if i+j>=len(imgs):break
  im=Image.open(imgs[i+j]);im.thumbnail((730,1050));canvas.paste(im,(j*750+(750-im.width)//2,35));draw.text((j*750+15,10),f'PAGE {i+j+1:03d}',fill='black')
 canvas.save(contact/f'spread_{i//2+1:03d}.jpg',quality=90)
table(run+'/PAGE_AUTOMATIC_QA.csv',pages);dump(run+'/PAGE_TEXT.json',texts);dump(run+'/PAGE_QA_SUMMARY.json',{'pages':len(pages),'landscape_pages':sum(x['orientation']=='LANDSCAPE' for x in pages),'blank_candidates':[x['page'] for x in pages if x['possible_blank']],'text_overflow_pages':[x['page'] for x in pages if x['text_outside_page']],'image_overflow_pages':[x['page'] for x in pages if x['images_outside_page']],'replacement_char_pages':[x['page'] for x in pages if x['replacement_characters']],'total_image_placements':sum(x['images'] for x in pages),'manual_status':'NOT_YET_ACCEPTED_BY_SCRIPT'})
print((base/'PAGE_QA_SUMMARY.json').read_text())
