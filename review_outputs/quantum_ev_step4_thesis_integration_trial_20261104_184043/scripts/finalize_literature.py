from pathlib import Path
import pandas as pd,json,re,requests,urllib.parse
O=Path(__file__).resolve().parents[1];R=O.parents[1];OTHER=R/'review_outputs/quantum_ev_thesis_step3_integration_20261104_173959';old=pd.read_csv(OTHER/'LITERATURE_SELECTION_LEDGER.csv',keep_default_na=False);refs=pd.read_csv(O/'BIBLIOGRAPHY_VERIFICATION.csv',keep_default_na=False)
active=[]
claims={
'L01':('社会技術システム','歴史的転換と技術/利用/制度/インフラの関係','帆船/蒸気船の長期事例','原著要旨/枠組みの節','本研究は長期移行全体を検証しない'),
'L04':('萌芽的技術','萌芽性と不確実性を区別','概念・文献統合','原著定義/要旨','将来能力を確定値にしない'),
'L05':('政策枠組み','研究開発/イノベーションシステム/変革の三枠組み','政策の概念比較','原著要旨/導入','EV条件の因果証拠ではない'),
'L06':('他領域のモデル','水素移行をシナリオとエネルギーモデルで探索','モデルとシナリオの接続','原著要旨/方法導入','水素の数値を配送へ転用しない'),
'L11':('交通の社会技術','交通転換を多次元の相互作用として分析','MLPの交通事例適用','原著要旨','本研究で制度/市場を実証しない'),
'L13':('商用EV条件','費用と技術条件を検討','米国市場の商用車ケース','原著要旨/導入','当時の価格値を現在へ転用しない'),
'L14':('EV配送統合','経路/速度/電力量/保有費用を接続','モデル・シナリオ/分岐条件','原著要旨','接続研究が不存在とはいわない'),
'L15':('利用主体','電動カーゴバイクの性能/認知/利用を検討','事前評価','原著要旨','本研究に利用者調査はない')}
for id,(domain,claim,method,locator,limit) in claims.items():
 x=old[old.literature_id==id].iloc[0];p=O/'sources/literature'/(id+'_primary.txt');assert p.is_file();active.append(dict(reference_id=id,authors=x.authors,year=x.year,title=x.title,DOI=x.DOI.replace('https://doi.org/',''),URL=x.URL,domain=domain,target=x.target_system,method=method,supported_claim=claim,primary_source=str(p),primary_locator=locator,reading_scope='当該要旨/定義/導入の限定確認；本文全主張の査読ではない',limitation=limit,relation='2章の比較枠組み',scientific_status='CONDITIONAL',usage='CURRENT_MAIN'))
# Direct primary pages explicitly checked through web and saved source where available.
web=[('OR01','Farhi, E.; Goldstone, J.; Gutmann, S.',2014,'A Quantum Approximate Optimization Algorithm','','https://arxiv.org/abs/1411.4028','QAOAの提案','量子アルゴリズムの構成','Farhi2014.html'),('OR02','Bärtschi, A.; Eidenbenz, S.',2020,'Grover Mixers for QAOA: Shifting Complexity from Mixer Design to State Preparation','10.1109/QCE49297.2020.00020','https://arxiv.org/abs/2006.00354','Grover mixerと可行状態準備','量子アルゴリズムの提案','Bartschi2020.html'),('OR03','Hadfield, S.; Wang, Z.; O’Gorman, B.; Rieffel, E.G.; Venturelli, D.; Biswas, R.',2019,'From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz','10.3390/a12020034','https://arxiv.org/abs/1709.03489','交互演算と可行部分空間のmixer','枠組み/問題写像','Hadfield2019.html'),('OR06','Schneider, M.; Stenger, A.; Goeke, D.',2014,'The Electric Vehicle-Routing Problem with Time Windows and Recharging Stations','10.1287/trsc.2013.0490','https://pubsonline.informs.org/doi/abs/10.1287/trsc.2013.0490','E-VRPTW制約とhybrid heuristic','計算実験','Schneider2014.html'),('OR36','Palackal, L.; Poggel, B.; Wulff, M.; Ehm, H.; Lorenz, J.M.; Mendl, C.B.',2023,'Quantum-Assisted Solution Paths for the Capacitated Vehicle Routing Problem','10.1109/QCE57702.2023.00080','https://arxiv.org/abs/2304.09629','CVRP分解とQAOA/VQEの取得上の課題','定式化/計算比較','Palackal2023.html'),('OR37','Delgado, A., et al.',2022,'Simulating key properties of lithium-ion batteries with a fault-tolerant quantum computer','10.1103/PhysRevA.106.032428','https://arxiv.org/abs/2204.11890','材料エネルギーから物性評価のアルゴリズム/資源','耐故障量子計算の構成/資源推定','Delgado2022.html')]
for id,authors,year,title,doi,url,claim,method,file in web:
 p=O/'sources/literature'/file
 active.append(dict(reference_id=id,authors=authors,year=year,title=title,DOI=doi,URL=url,domain='EV経路/量子計算',target=title,method=method,supported_claim=claim,primary_source=str(p) if p.is_file() else 'evidence/PRIMARY_WEB_RESPONSE.json + web primary page',primary_locator='原著公開要旨',reading_scope='要旨/著者年/関連DOIのみ；全文読了とはしない',limitation='原著の設定を本研究の入力/実機/実運用へ一般化しない',relation='2章/3章の方法背景',scientific_status='CONDITIONAL',usage='CURRENT_MAIN'))
chen=R/'review_outputs/quantum_ev_conditions_full_trial_20261104_125659/sources/chen2020_primary_text.txt'
active.append(dict(reference_id='OR28',authors='Chen, Q.; Pei, Y.; Chen, H.; Song, Y.; Zhen, L.; Xu, C.-Y.; Xiao, P.; Henkelman, G.',year=2020,title='Highly reversible oxygen redox in layered compounds enabled by surface polyanions',DOI='10.1038/s41467-020-17126-3',URL='https://www.nature.com/articles/s41467-020-17126-3',domain='材料参考',target='層状正極',method='電極実験/DFT',supported_claim='100cycle容量/保持率の報告と本研究逆算を分離',primary_source=str(chen),primary_locator='Fig5g対応本文604–609行',reading_scope='直接報告箇所の確認',limitation='逆算入力の主分析採用HOLD；実用初回値/量子機改善ではない',relation='2.3/5.5参考例',scientific_status='CONDITIONAL',usage='CURRENT_REFERENCE_ONLY'))
for id in ['OR24','OR25','OR30','OR38','OR31']:
 x=refs[refs.reference_id==id].iloc[0];active.append(dict(reference_id=id,authors=x.get('registry_authors','') or x.original_text.split('(')[0],year=2007 if id=='OR38' else 2023 if id=='OR31' else 2013 if id=='OR25' else 2008,title=x.get('registry_title','') or 'Climate Change 2023: Synthesis Report',DOI=x.DOI,URL=x.URL,domain='保存された方法/背景引用',target='元原稿の議論',method='書誌照合',supported_claim='原著の新しい実質的主張へ帰属させない',primary_source=x.get('metadata_source',''),primary_locator='Crossref書誌/原稿引用箇所',reading_scope='書誌照合；全文未確認HOLD',limitation='内容根拠としての再保証をしない',relation='原説明の保全と確認範囲の表示',scientific_status='HOLD',usage='METADATA_NOTICE_ONLY'))
mat=pd.DataFrame(active);mat.to_csv(O/'LITERATURE_EVIDENCE_MATRIX.csv',index=False)
# Differentiate registered identity from checked claim support for each original reference.
for i,x in refs.iterrows():
 match=mat[mat.reference_id==x.reference_id]
 if len(match):
  a=match.iloc[0];refs.loc[i,'claim_support_status']=a.scientific_status;refs.loc[i,'usage']=a.usage;refs.loc[i,'checked_claim']=a.supported_claim;refs.loc[i,'primary_locator']=a.primary_locator
  if a.usage in ['CURRENT_MAIN','CURRENT_REFERENCE_ONLY']:refs.loc[i,'metadata_status']='PASS_PRIMARY_IDENTITY_WITH_SCOPE'
 if x.reference_id=='OR29':refs.loc[i,'DOI']='10.1016/j.dib.2023.109798';refs.loc[i,'metadata_status']='HOLD_METADATA_LINK_IN_ORIGINAL_P443';refs.loc[i,'usage']='保存引用；主論証に用いない'
refs.to_csv(O/'BIBLIOGRAPHY_VERIFICATION.csv',index=False)
# Complete separate citation audit includes newly introduced sources, without pretending original 39 includes them.
ca=refs.copy();ca['origin']='original bibliography/ambiguous citation';add=[]
for a in active:
 if a['reference_id'].startswith('L'):add.append(dict(reference_id=a['reference_id'],original_text=a['title'],DOI=a['DOI'],URL=a['URL'],metadata_status='PASS_PRIMARY_IDENTITY_WITH_SCOPE',claim_support_status=a['scientific_status'],usage=a['usage'],checked_claim=a['supported_claim'],primary_locator=a['primary_locator'],origin='verified prior retrieval reused after readback'))
pd.concat([ca,pd.DataFrame(add)],ignore_index=True).to_csv(O/'CITATION_AUDIT.csv',index=False)
# Keep original Papachristos intent HOLD even after finding a strong candidate.
(O/'evidence/PAPACHRISTOS_CANDIDATES.json').write_text(json.dumps([dict(year=2018,title='A mechanism based transition research methodology: Bridging analytical approaches',DOI='10.1016/j.futures.2018.02.006',URL='https://discovery.ucl.ac.uk/id/eprint/10044052/',source='UCL record + author-posted SSRN abstract',matching='語義は近いが元の引用意図を証明しない'),dict(year=2019,title='System dynamics modelling and simulation for sociotechnical transitions research',DOI='10.1016/j.eist.2018.10.001',URL='https://discovery.ucl.ac.uk/id/eprint/10058753/',source='UCL公開書誌/要旨',matching='DOI年2018と巻年2019を区別')],ensure_ascii=False,indent=2))
# Plain references used by new main text. Full author list is retained where verified; et al. is disclosed.
lines=['# 現行本文の参考文献']
for a in active:
 if a['usage']=='METADATA_NOTICE_ONLY':continue
 lines.append(f"[{a['reference_id']}] {a['authors']} ({a['year']}). {a['title']}. "+('https://doi.org/'+a['DOI'] if a['DOI'] else a['URL']))
lines+=['# 書誌確認に限定した保存引用','以下は本文で確認範囲を示すために言及する。原著の実質的な新主張の根拠には用いない。']
for a in active:
 if a['usage']=='METADATA_NOTICE_ONLY':lines.append(f"[{a['reference_id']};内容HOLD] {a['authors']} ({a['year']}). {a['title']}. {a['URL']}")
(O/'drafts/08_references.md').write_text('\n\n'.join(lines)+'\n')
print('Literature matrix',len(active),'citation audit',len(ca)+len(add))
