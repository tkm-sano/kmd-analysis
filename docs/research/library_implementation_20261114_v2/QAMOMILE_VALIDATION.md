# QamomileによるHamiltonian・ALiMの検証

今回のQamomile実装は、既存Polynomialの係数を入力してspinへ変換した前回試験から進め、**配送距離・顧客双対・需要・容量・λを入力し、BinaryExprで式そのものを組み立てる**。[adapters.QamomilePolynomial](code/adapters.py)、[検査コード](code/model_validation.py)。

位置別one-hot変数は既存と同じ連番。t=0のdepotを定数1、他地点を0に固定する。容量残差hに対して明示的にλc(h+h²)、顧客ごとの訪問回数uに対してλv(u²−u)を加える。`paper_literal`は位置ごとの同じ式へ切り替える。Qamomileに配送専用のALiM自動処理があると仮定していない。OMMXの自動slack/ペナルティ化は使わない。

## 数値検証

需要を1/2/3とする非一様人工入力、容量3、非対称距離、顧客双対0.9+0.31*i。2/3顧客、slots3/4、2種類penalty、λ組(1,1)/(0.7,2.3)の12条件で全binary状態を確認した。係数は未出現項を0として比較、定数項とIsing Z/ZZも別比較。Qamomileの変数圧縮により番号が変わらないことをq/全基底energyで確認した。

|q|penalty|λc/λv|QUBO項差最大|Ising項差最大|energy差最大|全基底数|decode差|
|---:|---|---|---:|---:|---:|---:|---:|
|6|customer_unique|1.0/1.0|4.441e-16|2.220e-16|3.553e-15|64|0|
|6|customer_unique|0.7/2.3|8.882e-16|1.776e-15|7.105e-15|64|0|
|6|paper_literal|1.0/1.0|4.441e-16|4.441e-16|3.553e-15|64|0|
|6|paper_literal|0.7/2.3|8.882e-16|4.441e-16|7.105e-15|64|0|
|8|customer_unique|1.0/1.0|1.776e-15|0.000e+00|2.842e-14|256|0|
|8|customer_unique|0.7/2.3|8.882e-16|8.882e-16|2.842e-14|256|0|
|8|paper_literal|1.0/1.0|1.776e-15|0.000e+00|2.842e-14|256|0|
|8|paper_literal|0.7/2.3|1.776e-15|3.553e-15|5.684e-14|256|0|
|12|customer_unique|1.0/1.0|1.776e-15|0.000e+00|1.137e-13|4096|0|
|12|customer_unique|0.7/2.3|8.882e-16|1.421e-14|1.705e-13|4096|0|
|12|paper_literal|1.0/1.0|1.776e-15|0.000e+00|1.137e-13|4096|0|
|12|paper_literal|0.7/2.3|1.776e-15|7.105e-15|2.274e-13|4096|0|

各条件のvariable mapping、定数、項数、VALID/EMPTY/REPEATED/CAPACITY_EXCEEDED別件数と違反例energyは [model_validation_final.json](evidence/model_validation_final.json)。decodeには共通の配送decoderを保持し、独立した顧客重複/需要合計の分類と照合した。Qamomileが配送decoderを新たに提供するという結果ではない。

Pricingの部分集合で訪問しない顧客があるのは許容される。欠落は `missing_from_domain` として記録し、最終計画の全顧客exactly-onceをRMP/独立検証で確かめる。ALiM h+h²は単なる違反量ペナルティと異なり、h=−2でも正値となる。この現行仕様を変更していない。

## 構築・変換・評価時間（中央値、ms）

各1 warm-up＋7反復。同じ条件のnative Polynomial生成、Ising化と、Qamomile式構築、spin化を分けた。energy評価は同じone-hot masksを全件評価する総時間。

|q|penalty|λc/λv|native構築|native Ising|Qamomile構築|Qamomile Ising|native評価|Qamomile評価|native/Qam項数|
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
|6|customer_unique|1.0/1.0|0.0824|0.0071|0.1978|0.0597|0.0599|0.0428|15/15|
|6|customer_unique|0.7/2.3|0.0817|0.0070|0.2014|0.0600|0.0595|0.0427|15/15|
|6|paper_literal|1.0/1.0|0.0926|0.0070|0.2150|0.0730|0.0592|0.0495|19/19|
|6|paper_literal|0.7/2.3|0.0910|0.0070|0.2197|0.0731|0.0596|0.0493|19/19|
|8|customer_unique|1.0/1.0|0.1227|0.0113|0.3227|0.1055|0.1694|0.1144|28/28|
|8|customer_unique|0.7/2.3|0.1223|0.0113|0.3254|0.1052|0.1678|0.1144|28/28|
|8|paper_literal|1.0/1.0|0.1367|0.0111|0.3505|0.1282|0.1748|0.1324|34/34|
|8|paper_literal|0.7/2.3|0.1369|0.0111|0.3476|0.1237|0.1746|0.1353|34/34|
|12|customer_unique|1.0/1.0|0.2029|0.0231|0.5175|0.2104|1.4355|0.8220|58/58|
|12|customer_unique|0.7/2.3|0.2022|0.0228|0.5130|0.2109|1.4377|0.8386|58/58|
|12|paper_literal|1.0/1.0|0.2298|0.0232|0.5617|0.2383|1.4894|0.9270|67/67|
|12|paper_literal|0.7/2.3|0.2285|0.0231|0.5633|0.2380|1.4668|0.9218|67/67|

モデル検証プロセスのVmHWMは163328 KiB（共通import込み）。条件ごとの最小構成メモリ優位は未確認。全反復の生時間・評価状態数をJSONへ保存した。

同じ式の異なる加算順序によりfloat値はbit単位では一致しない。COBYLAがほぼ同点の候補を比較するときは、この小差でも後続角・nfev・経路集合が変わり得る。固定角の状態同等性と、適応的最適化履歴の完全再現を区別する。

全体試験で実際に使った容量60・q12のN6/N8マクロPricingも、事後に全4096状態ずつ照合した。QUBO係数差は最大5.69e−14、Ising係数差は最大2.85e−14、energy差は最大1.82e−12で、同じ許容誤差を満たした。[実容量の照合結果](evidence/actual_capacity_model_audit.json)。未変更runとのN6全4枝の学習履歴はQamomileで異なったが、Qiskit/Qulacs/QURIの履歴は全入力/seedで一致した。数学的同等性を履歴のbit単位一致と混同しない。

## 変更量と判定

本番の変更ファイルは0。候補は `QamomilePolynomial` とbackend選択を独立ファイルへ実装した。既存の短い定式化を単純に消して依存を置換できるわけではなく、変数/定数/λ/decoder/版の契約を維持する必要がある。独立検証コードの非空・非コメント行数は [implementation_size.json](evidence/implementation_size.json) に保存する。行数は本番移行工数の見積りではない。

標準Qamomile QAOAのX mixer/plus初期状態、FQAOAの粒子数保存を現行位置別exact XYへそのまま置換しない。本比較はQamomileの明示モデル構築＋既存ALiMの同式再実装である。配送制約を自動生成してくれる利点や、より良いALiM調整は実証していない。モデル共有の用途は残るが、現行の簡潔なPolynomialに対する速度・品質の実質的な導入利点は別途採否で判定する。

前回環境のprotobuf6.33.6は既存OR-Tools9.14の要求<6.32と衝突した。今回は隔離環境のprotobufだけ6.31.1へ合わせ、OR-Toolsを既存Dと同じ9.14.6206に固定した。Qiskit/NumPy/SciPyも前回と同版。初期resolver失敗、9.15試行、最終解決ログをすべて保存し、本番環境と前回venvは変更していない。[freeze](evidence/requirements.lock.txt)、[導入手順](evidence/install_reproduce.sh)。
