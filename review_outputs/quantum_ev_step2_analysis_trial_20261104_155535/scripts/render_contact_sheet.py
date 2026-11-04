from pathlib import Path
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parents[1];files=sorted(p for d in ['PATH1_STATISTICAL_FIGURES','QAOA_CONTROLLED_EXPERIMENT_FIGURES','PATH1_RUNTIME_FIGURES','PATH2_FIGURES'] for p in (O/d).glob('*.png'));w,h=560,390;canvas=Image.new('RGB',(w*3,h*((len(files)+2)//3)),'white');draw=ImageDraw.Draw(canvas)
for i,p in enumerate(files):
 im=Image.open(p).convert('RGB');im.thumbnail((w-12,h-30));x=(i%3)*w+(w-im.width)//2;y=(i//3)*h+25;canvas.paste(im,(x,y));draw.text(((i%3)*w+6,(i//3)*h+5),p.parent.name+'/'+p.stem,fill='black')
canvas.save(O/'evidence/FIGURE_CONTACT_SHEET.png')
