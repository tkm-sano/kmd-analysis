# 条件Dの最終採用判定

2026-11-14。**現行Qiskitを標準として維持し、Qulacsを任意の状態計算バックエンドとして限定的採用する。QURI Partsはクロスバックエンド検証用途に限定する。Qamomileを現行Dの必須依存へ追加する利点は確認できず、標準導入は不採用とする。** モデル共有という別の要件が生じた場合は再評価できる。

本判定は、実装を差し替える試験用コードまで作成・実行した結果である。本番ファイルや本番依存を変更したという意味ではない。Qulacsの部分短縮を理由にD全体の置換を推奨しない。

## 5つの問いへの回答

|問い|確認された事実|未確認事項・限界|採用判定|
|---|---|---|---|
|1 Qulacsは状態シミュレーションを速く実行できるか|q6/8/12/16、p1/2/4で数値同等性を確認。q16,p2の状態計算中央値はQiskit166.520 ms、Qulacs55.940 ms。構築/確率/抽出込みも170.098→59.264 ms|小さな人工回路、CPU1コア、理想状態。実機、研究規模、最小依存RSSの改善は未確認|**限定的採用**：最終状態発展の任意backend|
|2 QURI PartsでPricing性能/再現性が改善するか|同じbit順・符号・XYを実装できた。q16,p2で変換1.543 ms、状態56.010 ms、総60.931 ms。現行Dの全4枝履歴はnative Qiskitと一致|Qulacs直接より変換層が増える。snapshotの品質は全案同じ。現行Qiskitより再現性が改善したという証拠はなく、同等性の証拠である|**限定的採用**：実験の接続/照合層。性能目的の必須導入は不要|
|3 QamomileはHamiltonian/ALiMに実質的利点があるか|BinaryExprから同じ式を直接構築でき、係数・定数・λ・違反energy・decodeが許容誤差内で一致。q12の一例では64状態energy評価が1.436→0.822 ms。一方、構築＋Isingは0.226→0.728 ms|ALiMは明示式を再実装しており配送専用の自動機能の実証ではない。加算順差でN6の適応的学習履歴が変わった。D/W改善なし。維持対象が増える|**不採用（現行標準への導入）**。モデル共有用途は継続調査|
|4 導入により条件D全体のD/W/Tは改善するか|2入力×3seed×9構成=54完了試験、各4枝で計216枝が全て実行可能。全構成でN6のD=0.834 km、N8のD=1.006 km、W=0。T中央値は構成/入力により変わる|Tのばらつきと計測アダプター自体の差が大きく、一貫した全体短縮をライブラリの効果として確証できない。外側監視で1試行未完了。S1〜S3/統計的有意性は未検証|**D/W改善は確認されず。全体T改善の一般的な採用推奨はしない**|
|5 何を採用し何を維持するか|Qiskitの式・tensor学習・decoder・古典完成・真RC・二重検証は維持可能。Qulacs/QURIは独立adapterとして動作した|本番への接続、Python3.12環境での再測定、実際にD/Wの差が出る検算問題は今後の作業|**Qiskit標準を維持。Qulacs optional、QURI実験用、Qamomile標準導入なし**|

上記モデル時間は `customer_unique, λc=λv=1, q12` の例であり、他条件の表も [QAMOMILE_VALIDATION](QAMOMILE_VALIDATION.md) に示す。新ライブラリを導入するだけでアルゴリズムの品質が改善するという判定はしていない。

## 全体Tの読み方

バックエンドのみの変更を比較すると、N6でQiskit adapterのT中央値2.322秒に対しQulacs3.275秒、QURI2.801秒、Qamomile併用2.362秒。N8ではそれぞれ2.928秒、2.293秒、3.383秒、2.516秒だった。Qulacsの順位は入力によって逆転する。

未変更Qiskit run自体の中央値もN6=3.276秒、N8=4.537秒で、同じ学習/標本を返すQiskit adapterとの時間差がある。従って「未変更runとの差がすべてライブラリによる効果」とは判定できない。個々の構成で観測された中央値差は実測として保存したが、少数seed・shared host・T内stage記録を含む条件での観測差である。

完了54件の他に、N6のQamomile併用で外側120秒監視による未完了1件がある。成功した同一seedの再試行だけで失敗を消していない。計画Tは未確定、未完了処理/shotsはunknown。これはQamomile固有の障害と断定する証拠でもない。詳細と3/4という実行可能試行比は [END_TO_END_COMPARISON](END_TO_END_COMPARISON.md) に明記した。

## 研究上の意味

Huangらの構成を参考に、独立CW初期列→RMP→顧客双対→量子subset/順序生成→車両/2便/バースday完成→真RC→負列追加→再RMP→整数解→独立検証までを試験用updated方式で接続した。列追加後のdualを解き直し、実際の顧客dual変化も記録した。

通常DWTの量子受理対象は元tripの全macro順列であり、集合変更は0。updatedでは集合変更を受理できるが、この性質はQiskitでも実現できる。全4枝の集合変更tuple数の中央値はN6で130、N8で145（枝間重複を含む）となった。負RC完成列の追加とdual更新も起きたが、最終D/Wの改善には至らなかった。これは「表現力と接続の実装確認」であり、量子優位の実証ではない。

容量2・1バースの別契約では3便が必要となり、最終D4.2 km/W2分、最大2便/台とバースピーク1を全backendで検証した。一方、通常共通条件のN6/N8では容量60と2便上限が最適解を制限せず、Wも0だった。D/Wトレードオフや拘束の厳しい運行での性能は未検証である。

全域Pricingの非負証明、全顧客の同時量子最適化、S1〜S3のスケール性能は主張しない。計算はすべてCPUの状態ベクトル/tensorシミュレーションであり、実機量子計算の高速化とは呼ばない。正式仮説の支持/棄却・統計的有意性の判定も行っていない。

## ソースコード・公式根拠

- 既存実装: [aoa.py](../../../src/kmd_toc/column_generation/aoa.py) の `Polynomial` / `PricingAOA.run`、[dwt/methods.py](../../../src/kmd_toc/dwt/methods.py) のmacro受理、[parallel.py](../../../src/kmd_toc/dwt/parallel.py) の4枝/親T、[vehicle_day/master.py](../../../src/kmd_toc/vehicle_day/master.py) の全資源RC。
- 作成した実装: [adapters.py](code/adapters.py)（Qulacs直接、QURI変換、Qamomile直接式、共通sampler）、[cg_trial.py](code/cg_trial.py)（新dualと真RCを持つ有限CG）、[trial_driver.py](code/trial_driver.py)（通常4枝へのプロセス限定接続）、[test_contracts.py](code/test_contracts.py)（同等性と制約の独立検算）。
- [Huangら2025](https://arxiv.org/html/2503.17051v1) はALiM/QamomileとQURI Partsを用いた小規模CVRPを報告。配送の2便/バース問題や最新SDK比較の性能保証として扱わない。
- [Qulacs公式](https://github.com/qulacs/qulacs)、[QURI Parts 0.28.0のQulacs変換](https://github.com/QunaSys/quri-sdk/blob/v0.28.0/quri-parts/packages/qulacs/quri_parts/qulacs/circuit/__init__.py)、[Qamomile 0.15.2のBinaryModel](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/qamomile/optimization/binary_model/model.py)、[標準QAOA回路](https://github.com/Jij-Inc/Qamomile/blob/v0.15.2/qamomile/circuit/algorithm/qaoa.py)。標準X mixerやFQAOAへ無断変更して同等比較としていない。

## 本番へ導入する場合の変更対象と次の検証

|対象|必要な変更・維持事項|
|---|---|
|`column_generation/aoa.py`|最終回路/状態発展をoptional backendへ分離する。native Polynomial・圧縮tensor学習・decodeを維持。全体phase/bit順/XY exactをgolden testにする|
|`vehicle_day/pricing.py`, `pipeline/hybrid.py`, `dwt/methods.py`|SDK切替と、subset/dual更新というアルゴリズム切替を別configにする。代理RCと完成day真RCの検証を維持|
|`dwt/setup.py`, `worker.py`, `parallel.py`, `experiment.py`|全枝のversion/seed/PID/affinity/失敗/時間/shotsを保持し、変換/状態/抽出を分離計測。共通準備と親/子の出力時間も切り分ける|
|新しい環境lock/config|既存版を保全し、Qulacs0.6.14/QURI0.28.0をoptionalに固定。既存Python3.12.11で再検証。今回のPython3.11.15の時間と過去結果を混ぜない|
|次の小規模比較|容量・2便・バースとWが実際に拘束する同一入力で、backend-only/CG-domain-onlyを分ける。classical-controlを用い、stage記録IOと探索時間を分離して十分なpaired反復を設計する|

Qamomileの標準導入を再検討するのは、モデル共有/複数定式化の管理という具体的要件が生じ、構築費・float再現性・依存増を含めた利点が確認された場合。今回のenergy評価の部分短縮だけで全面移行しない。

## 成果と保全

36バックエンド条件（12回路設定×3構成、各warm-up1＋測定7）、15 Pricing snapshot、54完了全体試験、容量/2便/バースの接続契約、107件の回帰/契約テストを保存した。前回の40測定は再利用し、再測定の時間集計へは混ぜていない。[実行環境](evidence/requirements.lock.txt)、[再現手順](evidence/install_reproduce.sh)、[条件](evidence/protocol.json)、[生ログ](evidence/logs/)、[保全確認](evidence/preservation_check.json)。

既存成果・実装・設定・依存定義・READMEなど237ファイルのhashは一致し、本番変更は0。S1〜S3、既存の凍結需要生成、本実験の書換え、commit/pushは実施していない。
