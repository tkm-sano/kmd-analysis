from pathlib import Path
import os,sys,csv,json,hashlib,subprocess,re
from fractions import Fraction as F
from docx import Document
O=Path(__file__).resolve().parents[1];R=O.parents[1];U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked')
def tab(n,rows):
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with (O/n).open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)
rows=[]
def lit(id,domain,author,year,title,url,purpose,system,method,result,metrics,lim,relation,scope='原著要旨・書誌を今回web照合',status='PASS'):
 rows.append(dict(literature_id=id,domain=domain,author=author,year=year,title=title,primary_url=url,purpose=purpose,target_system=system,method=method,main_result=result,indicators=metrics,limitations=lim,relation_to_trial=relation,verified_scope=scope,status=status))
lit('L01','社会技術','Geels',2002,'Technological transitions as evolutionary reconfiguration processes: a multi-level perspective and a case study','https://doi.org/10.1016/S0048-7333(02)00062-8','技術移行過程の説明','帆船から蒸気船','歴史事例と多層的視点','技術・利用・制度等の再構成','移行メカニズム','本配送事例の因果推定ではない','技術能力と適用条件を分ける概念的背景','著者機関原著レコード・要旨を今回照合 https://research.tue.nl/en/publications/technological-transitions-as-evolutionary-reconfiguration-process/')
lit('L02','社会技術','Schot and Steinmueller',2018,'Three frames for innovation policy: R&D, systems of innovation and transformative change','https://doi.org/10.1016/j.respol.2018.08.011','政策枠組みの区別','イノベーション政策','概念的比較','社会技術システム変革を第三の枠組みとする','政策枠組み','配送省電力の実測値は与えない','技術改善と社会的成果を直結させない','出版社検索掲載本文・書誌を照合。DOI直接open403を記録')
lit('L03','社会技術','Rotolo, Hicks and Martin',2015,'What Is an Emerging Technology?','https://arxiv.org/abs/1503.00673','萌芽的技術の定義','新技術一般','文献に基づく概念整理','五属性を提示し不確実性・曖昧性を含める','新規性・成長・一貫性・影響・不確実性','量子の性能予測ではない','条件付き分析の位置付け')
lit('L04','社会技術','Arvidsson et al.',2018,'Environmental Assessment of Emerging Technologies: Recommendations for Prospective LCA','https://doi.org/10.1111/jiec.12690','萌芽技術の環境評価','将来技術のLCA','方法論的推奨','将来条件と比較系の明示を論じる','LCAの境界・将来シナリオ','本研究はLCAを実施していない','仮定・境界の透明化の参考','出版社本文の要旨・結論を確認。全節の精読は未実施')
lit('L05','EV配送','Schneider, Stenger and Goeke',2014,'The Electric Vehicle-Routing Problem with Time Windows and Recharging Stations','https://doi.org/10.1287/trsc.2013.0490','EV固有制約を含む配送問題','容量・時間窓・充電拠点付きEV配送','VNSとタブー探索のハイブリッド','モデルとベンチマーク比較を提示','経路解品質','途中充電・時間窓ありで本Bと条件が異なる','本BがEVRP全体を解いていないことを示す比較対象','出版社原著要旨・書誌確認。個別数値は採用しない')
lit('L06','量子配送','Farhi, Goldstone and Gutmann',2014,'A Quantum Approximate Optimization Algorithm','https://arxiv.org/abs/1411.4028','組合せ最適化用近似アルゴリズム','組合せ最適化','交互量子回路','QAOAを提案','近似品質・層数','特定MaxCutの性質を配送へ移植できない','QAOAの概念上の根拠')
lit('L07','量子配送','Hadfield et al.',2019,'From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz','https://arxiv.org/abs/1709.03489','制約を持つ最適化へ枠組みを拡張','組合せ最適化','一般化された交互演算子','制約部分空間でのミキサー設計を提示','状態空間・制約保存','本B実装の実機性能ではない','支持制限・到達可能性の説明','原著要旨・著者・改訂年確認。preprint2017/掲載2019を区別')
lit('L08','量子配送','Bärtschi and Eidenbenz',2020,'Grover Mixers for QAOA: Shifting Complexity from Mixer Design to State Preparation','https://arxiv.org/abs/2006.00354','実行可能状態を使うミキサー','制約最適化・順列問題','状態準備とGrover型ミキサー','状態準備へ複雑性が移る設計','解品質・状態準備','原著の回路構成と本CPUバックエンドは異なる','支持と実装費用の区別')
lit('L09','量子配送','Palackal et al.',2023,'Quantum-Assisted Solution Paths for the Capacitated Vehicle Routing Problem','https://arxiv.org/abs/2304.09629','量子支援CVRPの障害評価','CVRPをクラスタとTSPへ分解','QAOA/VQE比較','対象実験のQAOAに解品質上の制約','解品質・可行性','分割方式・条件が本Bと異なる','実装条件を揃えず優劣を一般化しない')
lit('L10','量子材料','Delgado et al.',2022,'Simulating key properties of lithium-ion batteries with a fault-tolerant quantum computer','https://arxiv.org/abs/2204.11890','電池物性計算の量子手法と資源','結晶電池材料','qubitizationに基づく位相推定','電圧・移動度・熱安定性への計算経路と資源見積を提示','基底状態エネルギー・計算資源','対象材料・誤差仮定が本T08と異なる','量子計算から物性への候補接続。量産電池改善の実証ではない','原著要旨・著者・掲載情報を今回確認。個別資源数値は転用しない')
lit('L11','材料・EV','Chen et al.',2020,'Highly reversible oxygen redox in layered compounds enabled by surface polyanions','https://doi.org/10.1038/s41467-020-17126-3','表面改質と酸素反応の安定化','リチウム過剰正極・Li対極セル','VASP/DFTと電極実験','Fig5gの容量・保持率が条件付き参照入力の由来','容量・保持率・試験条件','実用黒鉛全電池・完成パック・量子計算機による改善ではない','T08の入力由来を限定','今回ローカル原著PDF Fig5g/p7、Methods/p9-10を確認。PDFからtrialへ再抽出')
lit('L12','材料・EV','Faraji-Niri et al.',2024,'Data of physical and electrochemical characteristics of calendered NMC622 electrodes and lithium-ion cells at pilot-plant battery manufacturing','https://doi.org/10.1016/j.dib.2023.109798','製造条件と電極特性のデータ公開','NMC622電極とLi対極セル','製造条件計画・計測','電極条件と物理・電気化学データを公開','厚さ・質量・容量','完成車パックの質量検証ではない','T09の部材・電極境界を確認','著者機関原著PDF冒頭をweb確認。2023先行公開と2024巻年を区別')
lit('L13','社会技術','Papachristos',2018,'元引用意図未同定','https://doi.org/10.1016/j.futures.2018.02.006','未確定','未確定','未確定','候補文献の存在と引用意図は別','未確定','元引用に識別子がない','新本文では依存主張を使用せず、原稿引用の同定は継続HOLD','旧報告と元原稿を照合。候補の自動採用なし','HOLD')
tab('LITERATURE_CLASSIFICATION.csv',rows)
tab('LITERATURE_EVIDENCE_MATRIX.csv',[{'literature_id':x['literature_id'],'supported_claim':x['relation_to_trial'],'primary_url':x['primary_url'],'locator':x['verified_scope'],'status':x['status'],'not_supported':x['limitations']} for x in rows])
doc=Document(O/'sources/tmp_RsrchMstrDc_1026_results_integrated.docx');existing=[]
for i in range(371,445):
 text=doc.paragraphs[i].text
 if text.strip():existing.append({'paragraph_index0':i,'original_text':text,'trial_action':'既存書誌・説明を原文保全。上記L01–L12の照合範囲外は全文未検証','status':'HOLD_FULL_BIBLIOGRAPHY_AUDIT' if text.startswith('- ') else 'SOURCE_RECORD_NOT_A_NEW_CLAIM'})
tab('LITERATURE_EXISTING_BIBLIOGRAPHY.csv',existing)
# Re-extract actual immutable primary PDF, retaining location/hash.
chen=U/'review_outputs/causal_engineering_audit_20261027/run01/SOURCES/chen2020.pdf';warwick=U/'review_outputs/t09_open_data_model_20261029/run01/raw/warwick_article.pdf'
primary=[]
for src,n in [(chen,'chen2020'),(warwick,'warwick_article')]:
 dest=O/'sources'/f'{n}_primary_text.txt';subprocess.run(['pdftotext','-layout',str(src),str(dest)],check=True);primary.append({'path':str(src),'sha256':hashlib.file_digest(src.open('rb'),'sha256').hexdigest(),'bytes':src.stat().st_size,'extraction':str(dest.relative_to(O))})
tab('PRIMARY_PDF_SOURCES.csv',primary)
s=(O/'sources/chen2020_primary_text.txt').read_text();assert 'VASP' in s and '70.4%' in s and '99.0%' in s
# Independent T09 component reconstruction, not only sums.
p=R/'review_outputs/no_sumo_full_analysis_20261102/run01/C_T09_COMPONENTS_183.csv'
with p.open() as f:pack=list(csv.DictReader(f))
check=[]
for x in pack:
 v=lambda k:F(x[k]);Q=v('gross_design_Wh')/v('mean_voltage_design_V');mp=Q/v('q_reference_Ah_kg')/v('positive_utilization');mn=Q*v('NP_after_formation')/v('negative_q_Ah_kg')/(1-v('negative_unavailable_fraction'));fp=F('.96') if x['series'].startswith('A_') else F('.75');ap=v('positive_face_area_m2');an=v('negative_face_area_m2');ep=v('positive_porosity');en=v('negative_porosity')
 expected={'positive_active_kg':mp,'negative_active_kg':mn,'positive_coating_kg':mp/fp,'negative_coating_kg':mn/F('.98'),'Al_mass_kg':ap/2*v('Al_thickness_m')*2699,'Cu_mass_kg':an/2*v('Cu_thickness_m')*8960,'separator_dry_mass_kg':max(ap,an)*v('separator_areal_mass_kg_m2'),'liquid_mass_kg':(mp/fp/4458*ep/(1-ep)+mn/F('.98')/2200*en/(1-en)+max(ap,an)*F('.000025')*F('.41')+v('extra_liquid_volume_m3'))*1300}
 for k,e in expected.items():
  err=float(e)-float(x[k]);assert abs(err)<1e-8,(x['condition_id'],k,err);check.append({'row_id':x['condition_id'],'component':k,'independent_fraction_kg':str(e),'error_kg':err,'status':'PASS_ARITHMETIC_CONDITIONAL_INPUTS'})
tab('T09_INDEPENDENT_COMPONENT_CHECKS.csv',check)
# Evidence-based review of complete earlier reference updates; not treating older HOLD as current by default.
(O/'LITERATURE_REVIEW_TRIAL.md').write_text('''# 先行研究の体系化（trial提案）

本整理は、既存原稿の文献を入口に行った対象を限定した根拠照合である。検索データベースを網羅する系統的レビューではない。2026年11月4日に著者公開原著、出版社、著者機関の記録を確認した。検索語はsources/web_verification_*.jsonに保存した。主張の照合範囲を表のverified_scopeに限定し、要旨確認を全文精読としない。

## 社会技術システムと萌芽的技術

Geels（2002）の社会技術的移行、Schot and Steinmueller（2018）の政策枠組み、Rotolo et al.（2015）の萌芽的技術の定義を、技術能力と利用条件を区別する背景とする。Arvidsson et al.（2018）は将来条件を明示する方法論上の参照である。本研究は移行全体やLCAの実証を行っていない。各一次URLと照合範囲はL01–L04である。

## EV配送の運用と経路最適化

Schneider et al.（2014）は容量・時間窓・充電拠点を含むEV配送問題を扱う（L05）。本系列Bは固定した顧客割当と車両数の下の訪問順問題であり、途中充電を含まない。この差は簡略化した研究境界である。既存の総移動時間は道路OD時間であり、電力量目的やサービス完了時間の最適化ではない。

## 量子最適化と材料計算

QAOAの基礎とミキサー・状態準備の関係はL06–L08、配送応用の比較はL09に対応する。Palackal et al.の分割方式と本Bの全顧客を保持した支持制限は異なる。Delgado et al.（L10）は電池物性計算と資源見積の経路を示すが、対象材料も精度条件も本T08の参照入力とは異なる。

Chen et al.（L11）の原著はVASP/DFTと電極実験であり、量子計算機による性能改善の証拠として用いない。LP/S200の参照比容量は同図の保持率から研究上逆算した入力である。Faraji-Niri et al.（L12）の電極データは完成パック検証ではない。部材質量と完成品性能の境界を越えて引用しない。

## 未同定引用と版の照合

11月2日のLITERATURE_VERIFICATION.csvでは複数背景文献がHOLDであった。一方、11月3日のREFERENCE_UPDATES.jsonでは7背景文献とFaraji-Niri DOIの同定が進んでいる。古いHOLDをそのまま最新とせず、今回L01–L12の範囲で再確認した。Papachristos（2018）は引用意図が未確定でありL13=HOLDを維持する。新本文はこの未同定引用に依存させない。旧文献一覧全体の精読・引用妥当性は未完了であり、LITERATURE_EXISTING_BIBLIOGRAPHY.csvに範囲を残した。
''')
(O/'RESEARCH_GAP.md').write_text('''# 研究上の位置付け（trial提案）

先行研究は、社会技術的移行の説明、EV配送の制約付き最適化、量子アルゴリズムの解品質、材料物性計算を、それぞれ異なる対象・指標・境界で扱う。本trialが検討する問いは、計算の技術的能力が、固定した配送計画または電池設計へ反映され、運用上の差に伝達される際にどこで制約・相殺・未接続が生じるかである。

経路1では保存された同一入力に対する古典初期解・厳密参照・支持内最適値を分け、品質改善条件と時間内の計画取得条件を分ける。経路2では材料入力、既知部材、未知部材差、車両質量、固定速度DCを接続し、相殺境界を示す。この二経路を三層へ対応付けることを学術的貢献候補とする。

これは本監査対象文献と保存データの比較から得た位置付けであり、世界初・文献不存在・新規の量子優位の主張ではない。社会制度・採用行動を観測していないため、社会技術システム全体の移行説明へ一般化しない。
''')
print('literature',len(rows),'independent T09 checks',len(check),'existing bibliography paragraphs',len(existing))
