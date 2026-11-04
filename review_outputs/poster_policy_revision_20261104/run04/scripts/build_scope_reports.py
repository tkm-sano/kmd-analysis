from pathlib import Path
import csv,html
from review_content import CONDITIONS
R=Path(__file__).resolve().parents[1];O=R/'reports'
def write(stem,title,headers,rows,prefix=''):
 with (O/(stem+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:w=csv.writer(f);w.writerow(headers);w.writerows(rows)
 h=lambda s:html.escape(str(s))
 text='<table><tr>'+''.join('<th>'+h(v)+'</th>' for v in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+h(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</table>'
 (O/(stem+'.html')).write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>'+h(title)+'</title><style>body{font-family:system-ui,sans-serif;margin:30px;line-height:1.7;color:#17232d}table{border-collapse:collapse}td,th{border:1px solid #b9c6cf;padding:10px;vertical-align:top;text-align:left}th{background:#edf3f7}h1{color:#143653}</style><body><a href="../README.html">成果物一覧</a><h1>'+h(title)+'</h1>'+prefix+text+'</body></html>')
causal=[
 ('K01','配送完了→定時配達率','新しい成果ノードから除外する。旧結果・記録は保全する。','最新研究方針。新ポスターにこの主要指標を置かない。','対象範囲の決定'),
 ('K02','出発余裕→定時性','旧指標に依存する接続を削除する。現在の固定ODのJに出発余裕を追加しない。','時間不変OD・顧客時間窓なしでは出発余裕はJを定義する変数ではない。実運用一般で無意味と主張しない。','B：モデル前提'),
 ('K03','計画取得→採用','許容計算時間を、入力確定・更新から採用判断までの時間枠として新たに定義する。','T判断−T入力と、前処理・候補取得・検証・通信・統合等の全工程を照合する必要がある。出発余裕の名称だけの置換ではない。','C：時刻・全工程の対応は未測定'),
 ('K04','候補のJ・制約検証→実運用の採用','保存候補の算術検証と全体統合・採用を分離する。','前者は保存データでAとして確認し、後者はCとして残す。','A／Cを分離'),
 ('K05','計画品質→実走行DC','現在Bから速度・DCへの未検証の接続として残す。','現行460計画入力と旧460速度は別系列である。Jの差からDCの差を推定しない。','C：未検証'),
 ('K06','材料評価→材料選択・設計','量子評価情報が実際に有用で採用される接続を条件候補とする。','Chenは古典研究由来のモデル入力であり、対象の量子改善を示さない。R2/R7は量子材料評価の方法・資源の先行研究である。','B：文献からの条件候補／C：対象での利用'),
 ('K07','材料比容量→電池・車両質量','容量一定・平均セル電圧等を固定した①と、部材別②を分離する。','①の固定34kg推計を②の完成パックへ流用しない。②ではbとδの定義からb−δを扱う。','A：保存計算／B：会計式'),
 ('K08','質量→走行DC','速度、転がり抵抗、空力、効率、勾配、回生、補機、積載等を修飾条件として扱う。','今回Aは同一保存速度・平坦・回生と補機除外・積載0等に限定する。別の走行条件・実車へ普遍係数で外挿しない。','A：固定条件／B：条件付き解釈／C：実車'),
 ('K09','計画採用判断と電池設計採用判断','共通する分析上の段階として整理する。','配送では候補検証と統合、材料では評価情報の利用と工学試験であり、同じ実務手順や基準とは仮定しない。','B：分析枠組み'),
 ('K10','技術能力→適用判断→成果','技術と関与主体・判断の区別[4]、将来構成の予見・前提の省察[3]に用いる。','STSの移行過程やRRI全過程、社会的価値を実証したとはしない。実際の接続はABC台帳を参照する。','B：限定的な理論使用')]
write('10_CAUSAL_MODEL_REVIEW','因果モデルの削除・再定義・修飾条件',['ID','見直す関係','改稿での扱い','論理と根拠','確認状態'],causal)
verification={
 'C01':'改善候補を含む分割・選択規則を定義し、同一制約の全体目的と統合費用を検証する。',
 'C02':'入力更新と採用判断の時刻、通信・待機を含む全工程の範囲を揃えて記録する。',
 'C03':'状態準備、符号化、雑音、コンパイル資源・誤り制御を確認する。',
 'C04':'対象の量子物性評価の精度・費用と古典対照を確認し、情報が選択・設計判断に有用か検討する。',
 'C05':'全構成部材と完成質量、対象の出力・寿命・安全要件を資料・試験で確認する。',
 'C06':'採用計画から速度への対応と、回生・補機・勾配・積載を含む対象EVの校正・計量範囲を確認する。'}
rows=[(v[0],v[1],v[3],v[4],verification[v[0]],v[5]) for v in CONDITIONS if v[2]=='C']
write('05_UNVERIFIED_CONNECTIONS','未検証接続と今後の確認内容',['条件ID','経路','未検証の内容','根拠・現状','必要な確認','過剰解釈を防ぐ留保'],rows,'<p>以下の検証を今回実施したという意味ではない。面接・RIQ・M1を工程として追加していない。</p>')
requirements=[
 ('1','対象資料・生成原本の確認','現行run03のPPTX・生成コード・本文、配送と材料のCSV、方法・結果・考察原稿、一次資料を確認した。','00_SOURCE_INVENTORY.csv; baseline; sources'),
 ('2','原本保全・指示','祖先・repo内でAGENTS.mdは未確認である。原本1940ファイルのhashを再照合する。','evidence/ORIGINAL_PRESERVATION.csv'),
 ('3','タイトル・問い・目的','指定タイトルと問いを採用した。目的・方法は条件候補・制約・未検証接続の特定として統合した。','poster.pptx; 03_RESEARCH_STRUCTURE'),
 ('4','配送指標','ΔJ、相対差、実行可能性、最適性参照、工程時間、探索支持を区別した。未保存の実機資源はHOLDである。','09_NUMERIC_AUDIT; TIME_SCOPE_AUDIT; GLOBAL_REFERENCE_COVERAGE'),
 ('5','配送の結果・方式','3群8設定と、GM2設定だけの結果表、7改善入力と規模別結果を区別した。実機ではない。','SETTING_SCOPE_AUDIT; B_IMPROVING_INPUTS'),
 ('6','材料の入力・二モデル','Chenは入力出典、R2/R7は量子評価の先行研究として扱う。①簡略推計と②部材別183設計を分離した。','08_REFERENCES; C_COMPONENT_BOUNDARIES; 06_REVIEW_REPORT'),
 ('7','削減率・伝達比','5.67%・0.478%・0.413%と各LP分母、有限差分の比、走行条件を確認した。普遍係数や量子効果としない。','C_MASS_DC_RECONCILIATION; 09_NUMERIC_AUDIT'),
 ('8','成立・消失条件','支持内改善解の必要条件とb−δの代数的符号境界だけに強い論理用語を用い、適用範囲を限定した。','04_CONDITIONS; 06_REVIEW_REPORT'),
 ('9','考察・統合','配送の計画品質と材料の固定速度DCは異なる到達段階である。共通の適用判断の枠組みにABC接続を整理した。','07_CONNECTIONS_ABC; 07_COMMON_FRAMEWORK'),
 ('10','因果モデル','旧指標・出発余裕を復活させず、許容計算時間と走行条件の修飾を再検討した。','10_CAUSAL_MODEL_REVIEW'),
 ('11','理論の使用範囲','STSは技術・判断の区別、RRIは予見・前提の省察に限定した。','poster_text.txt; 08_REFERENCES'),
 ('12','デザイン・表示','二段組・青茶色を維持し、A/B/C・二モデル・境界を表示した。実PPTX描画と文字・余白を確認する。','render/FINAL_VALIDATION.json; poster_preview.png'),
 ('13','未実証性能','対象量子材料改善、完成パックの出力・寿命・安全性、実車性能は未実証として示した。','poster_text.txt; 05_UNVERIFIED_CONNECTIONS'),
 ('14','作業範囲','新しい科学実験、commit・push・PR作成は行わない。棄却済みの方法は再導入しない。','BUILD_AND_REVIEW.txt; FINAL_GIT_STATUS.txt')]
write('11_REQUIREMENT_COVERAGE','今回依頼の要件対応',['No.','要件','確認内容','成果物・根拠'],requirements,'<p>この表は研究全体の因果実証が完了したという意味ではない。未検証事項を残したまま、改稿の要件に対応する。</p>')
print('Scope, causal review and unverified-connection reports generated.')
