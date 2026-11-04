from common import *
sys.path.insert(0,str(O/'rendering_tools/python'))
import fitz
run='render08'; pdf=fitz.open(O/run/(OUT.stem+'.pdf'))
assert len(pdf)==88
reviews=[];numbers=[]
for p in range(1,89):
 name=f'page_{p:03d}.png'; final=O/run/'pages'/name
 if p<=14: prior='render02'
 elif p<=44: prior='render07'
 else: prior=run
 viewed=O/prior/'pages'/name
 assert sha(final)==sha(viewed)
 method='ACTUALLY_VIEWED_FINAL08_CONTACT_SHEET' if prior==run else f'VIEWED_{prior.upper()}_AND_FINAL08_BYTE_IDENTICAL'
 reviews.append({'page':p,'status':'PASS','method':method,'final_image':str(final),'final_image_sha256':sha(final),'previously_viewed_image':str(viewed),'contact_sheet':str(O/prior/'contact'/f'spread_{(p+1)//2:03d}.jpg'),'scope':'目視：欠落・文字化け・図表/数式・ページ外配置・表分割。原履歴・固定図ページの余白は構成上保持。'})
 page=pdf[p-1];footer=page.get_text('text',clip=fitz.Rect(0,page.rect.height-65,page.rect.width,page.rect.height)).strip()
 numbers.append({'pdf_page':p,'footer':footer,'expected':p,'status':'PASS' if footer==str(p) else 'FAIL'})
assert all(x['status']=='PASS' for x in numbers),numbers
assert sha(OUT)==js(O/run/'RENDER_RUN.json')['DOCX_sha256']
table('VISUAL_PAGE_REVIEW.csv',reviews);table('PAGE_NUMBER_CHECKS.csv',numbers)
dump('FINAL_RENDER_SELECTION.json',{'run':run})
dump('VISUAL_ACCEPTANCE.json',{'accepted_pages':88,'render':run,'pages_1_14':'render02で実際に目視した画像とのSHA一致を確認','pages_15_44':'render07で実際に目視した画像とのSHA一致を確認','pages_45_88':'render08の全22見開き画像を実際に目視確認','native_MS_Word_tested':False,'remaining_layout_notes':'付録C導入74頁・最終88頁は章導入/末尾に伴う余白。旧英語パス折返し等は全面推敲へ。'})
print(json.dumps({'accepted_pages':88,'continuous_page_numbers':88,'DOCX_sha256':sha(OUT)},ensure_ascii=False))
