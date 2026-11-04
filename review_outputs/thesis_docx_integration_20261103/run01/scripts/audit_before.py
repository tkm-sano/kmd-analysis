from common import *
from docx import Document
start=time.monotonic();assert not OUT.exists(),'Target already exists; do not overwrite a preexisting user file'
pins={}
def pin(p,role):
 p=Path(p);pins[str(p)]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'role':role}
pin(SRC,'ORIGINAL_DOCX_NEVER_WRITE');assert sha(SRC)=='ea25f2cc71368669a691ebe1e7643a25f30f288c00ce34cd66ed0590d95b3da3'
for base,manifest in [(P,'SHA256_MANIFEST.csv'),(F,'ARTIFACT_MANIFEST.json')]:
 rr=rows(base/manifest) if manifest.endswith('.csv') else js(base/manifest)
 for x in rr:
  p=base/x['path'];assert sha(p)==x['sha256'],str(p);pin(p,'FROZEN_REVIEW_OR_ANALYSIS_INPUT')
 pin(base/manifest,'PREVIOUS_MANIFEST')
pin(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json','FROZEN_DC_SPEC')
x=structure(SRC);dump('DOCX_STRUCTURE_BEFORE.json',x);table('SOURCE_HASHES_BEFORE.csv',list(pins.values()));d=Document(SRC);table('DOCX_PARAGRAPHS_BEFORE.csv',[{'index0':i,'style':p.style.name,'text':p.text,'OMML':''.join(p._p.xpath('.//m:t/text()'))} for i,p in enumerate(d.paragraphs)])
mp=rows(P/'DOCX_INSERTION_MAPPING.csv');audit=[]
for i,m in enumerate(mp,1):
 starti=int(m['paragraph_index0_start']);actual=d.paragraphs[starti].text;ok=actual.startswith(m['exact_anchor']);assert ok
 audit.append({'integration_id':f'I{i:02d}',**m,'actual_anchor':actual,'anchor_matches':ok,'status':'PASS_ANCHOR_NOT_YET_EDITED'})
table('INSERTION_PLAN_AUDIT.csv',audit)
dump('INITIAL_GIT_STATE.json',{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'status':subprocess.check_output(['git','status','--short'],cwd=R,text=True),'diff':subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R,text=True)})
md('01_DOCX_STRUCTURE_AUDIT.md',f'''# 編集前のDOCX構造監査

原文書SHA256 `{x['sha256']}`。本文610段落・全XML段落{x['all_paragraphs']}、表8、埋込み画像0、OMML数式67、脚注・巻末注参照0。章見出しの一部はnormal styleであり、3節以降にHeading1/2がある。番号は文字列で、本文内にTOC/REF/SEQフィールドはない。目次は存在しないため今回も新規目次は作らず、章見出しの階層を整備する。既存の数式がpython-docxの本文テキストに現れないことを欠落とみなさない。

ブックマーク29、ハイパーリンク53。名前・関係先・原段落はJSON/CSVに保存した。参考文献は原段落334〜397、付録は398〜609である。既存参考文献を削除せず、確認できた不足項目のみ別途追加する。

A4・1セクション、上下左右25.4mm。header1.xmlは空の段落で、フッター・ページ番号は存在しない。既存セクション設定・ヘッダーを保持し、統合版にページ番号PAGEフィールドをフッターへ新規追加する。原文のNormalはArial11ptである。既存の段落・文字書式は非対象部分で維持し、新規段落は既存BodyText/Headingスタイルに従う。

保全方式はpython-docx/lxmlによるXML要素の移動・挿入である。段落全体のtext再代入を既存数式・リンクのある段落へ行わない。更新対象の旧本文・旧表は要素ごと付録Bへ移動し、各移動元を記録する。67数式、53リンク、29ブックマークと既存8表の内容を終了時に独立照合する。

32反映箇所の先頭アンカーを実DOCXと照合し、32/32で一致した。対応表の機械的な全文置換はせず、維持する節と付録へ移す節を編集仕様で分ける。原文はLibreOffice24.2.7.2で読み取り変換でき、参考レンダリングは47ページである。Microsoft Wordでの実機表示は別条件であり、今回の検証環境と区別する。
''')
print(json.dumps({'pinned_files':len(pins),'insertion_anchors':len(audit),'before':{k:x[k] for k in ['body_paragraphs','tables','OMML_equations','footnote_refs','hyperlinks','bookmark_count']}}))
