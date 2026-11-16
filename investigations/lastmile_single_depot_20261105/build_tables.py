from pathlib import Path
import csv,json,hashlib,subprocess
B=Path(__file__).parent;R=B.resolve().parents[1]
K='https://wwwtb.mlit.go.jp/kanto/content/000364901.pdf';M='https://www.cao.go.jp/consumer/iinkaikouhyou/2021/doc/202108_winwin_jirei_3a.pdf';A='https://doi.org/10.1287/trsc.2022.1173';P='https://pyvrp.github.io/v0.12.0/api/pyvrp.html';G='https://github.com/tkm-sano/kmd-analysis/blob/8605d5412f6af62229a83095c35ab04c8c7dd9b1/'
def table(name,rows):
 with (B/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
rows=[]
def e(id,claim,value,unit,den,scope,year,issuer,title,url,loc,definition,limit,decision):
 rows.append(dict(claim_id=id,claim=claim,value=value,unit=unit,denominator=den,aggregation_scope=scope,target_year_region=year,issuer=issuer,source_title=title,url=url,page_table=loc,access_date='2026-11-05',confirmed_definition=definition,transfer_limitations=limit,decision=decision))
for id,claim,v,u,defn in [('E01','京浜の最近一日自動車出入',2500,'台/日','自動車出入台数；一意車両・配送便か不明'),('E02','京浜の最近一日貨物取扱量',4900,'t/日','貨物取扱量；集荷配達発送内訳なし'),('E03','京浜の利用事業者',22,'事業者','施設全体利用事業者'),('E04','京浜の取扱能力',10500,'t/日','実績取扱量と別の能力')]:e(id,claim,v,u,'施設全体・日又は施設','京浜全体','2025-03-31現在/大田区', '関東運輸局','一般トラックターミナルの現況',K,'1頁 京浜列',defn,'営業所単位の同時計画台数・先数へ換算不可','施設背景のみ採用')
e('E04b','大型トラック換算取扱能力',1050,'台分','10500t/日','京浜全体','更新年不明/大田区','日本自動車ターミナル','京浜施設案内','https://www.j-m-t.co.jp/terminal/keihin.html','概要 貨物取扱能力','台数配備でなく貨物能力の換算','配送車配備数として使わない','背景のみ')
e('E05','京浜営業所の車両台数',16,'台','関係会社含む','丸運 京浜ターミナル営業所5号棟','掲載時点不明/大田区','丸運','京浜ターミナル営業所','https://www.maruwn.co.jp/corporate/network/keihin-terminal/','詳細 車両台数','路線貨物・航空コンテナ集配を行う営業所の車両','同時出発・宅配専用・一便先数・時間不明；web本文確認、ローカル取得TLS失敗','営業所規模の参照のみ')
Y='https://www.kuronekoyamato.co.jp/ytc/customer/send/services/sameday/sales_office/tokyo.html'
for i,name,code in [('E06a','勝島','036066'),('E06b','大井埠頭','036067'),('E06c','大田山王','036086'),('E06d','戸越','036952')]:e(i,'品川平和島営業所の同住所コード '+name,code,'営業所コード','住所2-1-1','当日配送可能営業所表','2026-05/東京','ヤマト運輸','東京都当日配送可能営業所',Y,'大田区欄 '+name,'公式表の名称と住所・コード','コードごとの車群分離と担当境界不明','所在地確認のみ採用')
e('E07','同住所コードは別車群か','未確認','車群','コード別','品川平和島','2026/東京','調査者','公式コード表の適用限界',Y,'大田区欄','表に車両群定義なし','コード数から車数や営業所実体数を作らない','保留')
e('E08','松戸デリバリー同居型拠点の車両',31,'台','拠点','松戸市三ケ月1328','2020-11-06開業・発表2021/松戸','ヤマトHD（内閣府掲載）','地域共創事業紹介',M,'PDF4頁上段/スライド6','車両数と記載','日稼働・同時出発・便不明','類似拠点配備規模の参照のみ')
e('E09','松戸宅急便取扱い個数',8000,'約個/日','当該拠点の日','同居型拠点','2021資料/松戸','ヤマトHD（内閣府掲載）','地域共創事業紹介',M,'PDF4頁上段/スライド6','宅急便取扱い個数（日）','発送集荷配達内訳・配送先数不明；8000/31を便荷量にしない','荷量背景のみ')
e('E10','Amazon訓練ルート',6112,'ルート','訓練集合','実行ルート・匿名化','2018/米5都市','Merchan等/Amazon/MIT','2021 Amazon Last Mile Routing Research Challenge: Data Set',A,'§2','Seattle LA Austin Chicago Boston；評価3072とは別','一営業所全車群の網羅標本でない','海外参照採用')
for id,v,label in [('E11a',105,'P10'),('E11b',148,'平均'),('E11c',186,'P90')]:e(id,'Amazon stops '+label,v,'stop/route','6112訓練ルート','表2のNo. of stops','2018/米5都市','Merchan等','Amazonデータ論文',A,'表2', 'Station/Dropoffが区別されるstop；配送先比較は別途Dropoff集計','packageや世帯と等価でない','定義限定で採用')
e('E12','Amazon再集計でデポ除外可能','Station/Dropoff','カテゴリ','stop type','訓練データ','2018/米5都市','MIT-CAVE','Data Structures','https://raw.githubusercontent.com/MIT-CAVE/rc-cli/main/templates/data_structures.md','Definitions type; route_data.stops','各ルートでtype=Dropoffを数える','再配達試行を含み得る；住所数ではない','再集計採用')
e('E13','日本郵便試行規模',200,'約局','全国の局数','各局一部エリアの試行予定','2020-06発表/日本','日本郵便','AI配達業務支援システム試行','https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02_01.pdf','1頁 概要','約200局で2020-06〜2021-03予定','車両数でも同時計画台数でもない','業務導入の背景のみ')
e('E14','新人熟練者の配達業務時間差','67→17','平均分差','新人とベテランの業務時間差','ルート作成+配達','掲載年不明/日本郵便','オプティマインド','日本郵便事例','https://loogia.jp/cases/nihonyubin/','効果','計算時間そのものでない','出発前余裕・ソルバー秒へ流用不可','効果の定義確認のみ')
e('E15','佐川旧リリースの80個14日等','未採用','個/日等','本文直接取得不能','検索インデックスのみ','2021-10-04/日本','SGHD','Loogia導入','https://www.sg-hldgs.co.jp/newsrelease/2021/1004_4840.html','旧URL→新URLは本文欠落','web検索に本文が残るが直接open・保存HTMLに該当本文なし','転載を独立証拠にしない；80個を80先としない','保留')
e('E16','担当区域の配達順序と積込み等の準備','数十分','業務時間','積込み・伝票整理を含む','ドライバー担当エリア業務','2021/日本','SGHD','SDGs Communication Book 2021','https://www.sg-hldgs.co.jp/csr/library/pdf/CommunicationBook2021_A4.pdf','冊子16頁/PDF17頁','住所・時間指定を考慮して準備','ソルバー時間・出発前許容時間とは別','模擬方策の構造参照')
e('E17','東京都市圏の世帯受取調査','10000','対象個人','18歳以上・受取経験世帯','都市圏の個人調査','令和6年度/東京都市圏','東京都市圏交通計画協議会','第6回調査結果概要','https://www.tokyo-pt.jp/static/hp/file/special_logistics_6th/special_logistics_6th_02.pdf','PDF10頁 (5)','頻度は世帯・場所割合は直近2回19648受取の別分母','大田区営業所の一便へ換算不可','背景のみ')
for id,cl,v,u,loc,defn,lim in [('L01','基準容量',216,'PE','sources/CAPACITY_FREEZE_MANIFEST.json','ceil(431/2)；physical_calibration=false','実包数・容積・重量容量でない'),('L02','顧客作業',102,'秒/先','sources/PRIMARY_TEMPORAL_BASELINE.json','建物顧客当たり一定','PEに比例させない'),('L03','帰庫期限',32400,'秒','src/kmd_quantitative/routing/independent.py:20','出発からの相対時刻；帰庫時刻上限','現実勤務9時間と等価でない'),('L04','旧系列時間枠あり',78,'入力','probes/local_input_audit.json A_OLD_TW','4顧客・全78時間枠あり','全系列を枠なしとしない'),('L05','後発系列時間枠なし',460,'入力','probes/local_input_audit.json B_NO_CUSTOMER_WINDOWS','全顧客ready0 due32400、最大125先・単一車入力','全車群VRPでない'),('L06','主定時配達率','Σ期限内完了PE/Σ対象PE','fraction','review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py:8-10','D_i=due_i+service_i、未配達を分母保持、件数率は副','帰庫率・計画取得率と別')]:e(id,cl,v,u,'系列別固定対象','現行研究と保全入力','2026/大田区研究入力','研究者', '現行コード・原設定',G+loc if not loc.startswith(('sources','probes','review_outputs')) else loc,loc,defn,lim,'研究仮定／定義として継承')
e('T01','相談の3時間8時11時は仮例','3;8;11','時間/時刻','仮定の説明','計画開始と出発','録音日不明/相談','ユーザー提供自動文字起こし','FootTherapy日吉店','sources/transcript_excerpts.txt','01:05:03–01:05:44','仮りで、と明示','原音声未照合；運用実績でない','数値不採用')
e('T02','相談の48時間1.8倍は仮例','48;1.8','時間;倍','仮定の説明','待ち時間と距離','録音日不明/相談','ユーザー提供自動文字起こし','FootTherapy日吉店','sources/transcript_excerpts.txt','01:08:08–01:09:05','勝手なイメージと留保','効果予測・改善実績でない','数値不採用')
e('P01','PyVRP契約試験', '0.12.0','version','3顧客6順列','合成有向行列','2026-11-05/計算環境','調査者/PyVRP','契約試験と公式API',P,'ProblemData VehicleType Client Route; probes/contract.json','費用行列に道路秒、durationに道路秒、サービス別加算','静的・整数；実距離は別保存','候補採用・小規模検証済み')
e('P02','合成3000先の古典終了可行解',3000,'先','1入力1seed・上限30台','10km四方の合成有向OD','2026-11-05/計算環境','調査者','PyVRP engineering probe','probes/scale_probe.json','k30 n3000行','終了時の全先・容量・台数・時間を独立検査','大田区・量子比較・締切保証でない','古典合成実行成立のみ')
e('P03','規模と時間予算は研究計画','5/10/20/30;60/300/900','台;秒','研究系列SとF','実験提案','2026/研究','調査者','本報告計画','experiment_plan.csv','全条件','時間は端から端、車両は上限','実運用の計測値でない','主5/10;拡張20;30実態保留')
e('C01','Uchoa X系列は実装検証候補',100,'問題（Set X）','公開CVRP集合','CVRPLIB','2017/合成','CVRPLIB/Uchoa等','Set X','https://galgos.inf.puc-rio.br/cvrplib/index.php/en/instances','Set X','対称距離丸めのCVRP','大田区の比較目的値へ転用不可；今回未実行','実装検査候補')
e('E18','Amazon Dropoff再集計平均',146.9919829842932,'配送停車地点/ルート','6112訓練ルート','type=Dropoffのみ','2018/米5都市','調査者（Amazon原データ再集計）','route_data.json', 'https://amazon-last-mile-challenges.s3.us-west-2.amazonaws.com/almrrc2021/almrrc2021-data-training/model_build_inputs/route_data.json','probes/amazon_stats.py;AMAZON_REAUDIT.md','各ルートのStationを除外；P10=104中央値150P90=185','停車地点であり一意住所・包数でない','海外参照のみ採用')
e('E19','Amazon全ルートStation数',1,'Station/route','全6112ルート','原JSON全件','2018/米5都市','調査者（Amazon原データ再集計）','route_data.json','probes/amazon_stats.json','station_count_distribution','全6112でちょうど1Station','出発と帰庫を二つのデポノードとして数えない','定義確認採用')
table('evidence_ledger.csv',rows)
params=[]
def p(name,current,candidate,adopt,ids,kind,sens):params.append(dict(parameter=name,current_value=current,candidate_value=candidate,adopted_or_range=adopt,evidence_ids=ids,evidence_class=kind,sensitivity=sens))
p('対象','EV等を含む既存研究','配送計画に絞る','単一拠点静的配送・EV限定なし','T01;T02','研究上の範囲','なし')
p('車両上限','単一車固定割当','5;10;20;30','主5;10、拡張20、上限試験30；実態30は保留','E05;E08;P03','外部参照＋研究仮定','必要')
p('配送先数','3;4;5;25;100;125','500;1000;2000;3000','100先/台系列と500先固定系列','E10;E11a;E11b;E11c;E12;L05','外部参照＋研究仮定','必要')
p('容量','216PE','108;216;432','216PE基準；108/432感度','L01','研究仮定・物理校正なし','必要')
p('需要','既存B平均1.692735PE/先（重複あり）','1PE;平均1.7混合','q=1と1/2/3/4を50/35/10/5%混合；合計・各車を検査','L05;P03','研究仮定','必要')
p('サービス','102秒/先','継承','102秒/先；0/60/180秒補助感度は本解析前登録','L02','研究仮定','必要')
p('帰庫期限','32400秒','継承','32400秒；固定絶対帰庫と出発相対を別条件','L03','研究仮定','必要')
p('顧客時間枠','Aあり/Bなし','なし','主B継承でなし；Aを枠なしと読み替えない','L04;L05','入力監査実測','任意の別系列')
p('定時率','PE主・件数副','継承','due+service完了期限；帰庫は別；無時間枠可行解では率退化','L06','原定義','未配達許容は別モデル')
p('時間予算','CPX D10の仮想時間は別規約','1;5;15分','60;300;900秒端から端；実運用値とはしない','E14;E15;E16;P03','研究仮定','必要')
p('古典対照','固定割当有向TSPTW','PyVRP','0.12.0全体VRP＋局所厳密/探索','P01;C01','公式文書＋契約試験','seed反復')
p('量子部分問題','3/4先等の保存候補','4;6;8先','最初4先、6/8は追加資格確認後；実機未採用','L05;P03','研究計画','必要')
table('parameter_decisions.csv',params)
exp=[]
for series,kn in [('S',[(1,100),(5,500),(10,1000),(20,2000),(30,3000)]),('F',[(5,500),(10,500),(20,500),(30,500)])]:
 for k,n in kn:
  for demand,mean in [('unit',1),('mixture_assumption',1.7)]:
   exp.append(dict(condition=f'{series}_K{k}_N{n}_{demand}',series=series,vehicles_upper_bound=k,delivery_nodes=n,demand_PE=f'{n} exact' if mean==1 else f'{n*mean:g} nominal; realised seed sum stored',individual_demand_PE='1' if mean==1 else '1/2/3/4 proportions .50/.35/.10/.05',total_capacity_PE=216*k,nominal_load_fraction=n*mean/(216*k),balanced_service_s=102*n/k,balanced_road_wait_allowance_s=32400-102*n/k,OD_two_float64_MB=16*(n+1)**2/1e6,budget_wall_s='60;300;900',classical='B1 geographic surrogate;B2 PyVRP0.12.0 global;B3 exact/local same blocks',quantum_subproblem='4 delivery nodes first;6/8 qualification later',input_seeds='1000..1009',solver_seeds='0..4',pilot='synthetic only n100..3000 q1 S; actual Ota NOT_RUN' if series=='S' else 'NOT_RUN',quantum_hardware='none executed; simulator/device to preregister',adoption='bridge' if k==1 else ('primary provisional' if k in [5,10] else ('extension conditional' if k==20 else 'synthetic ceiling;operational scale HOLD'))))
table('experiment_plan.csv',exp)
(B/'probes/pip_freeze.txt').write_text(subprocess.check_output([str(B/'probes/venv/bin/pip'),'freeze'],text=True))
print('claims',len(rows),'params',len(params),'experiments',len(exp))
