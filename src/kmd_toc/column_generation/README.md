# Huang CG＋AOA：小規模独立参照実装

本パッケージはarXiv:2503.17051v1を参照した独立実装である。著者コードの移植ではない。研究規模の時刻付き日列、車両台数、最大2便、バース、勤務制約は未実装である。人工CVRPの距離単一目的だけを検証する。研究のRQ・仮説・共通入力を変更しない。

## モジュール契約

|モジュール|入力→出力|根拠・変更・ライブラリ|seed・エラー・検証・期待結果|
|---|---|---|---|
|models.py|不変距離/需要/容量→Instance、Route、全列|原著式(5),(13),(14)。NumPy/itertools。人工fixtureを独立定義|乱数なし。不正値はValueError、列挙は8顧客以内。容量・有向距離・全列テスト|
|master.py|列集合/LP型→LP/双対、整数分割解|式(7)–(12)。SciPy HiGHS。分割LPも別モードで提供|乱数なし。求解/双対不整合はRuntimeError。c−Aᵀπ、強双対、一度配送を検査|
|aoa.py|Instance/双対/AOAConfig→Qiskit標本/列/ログ|式(13),(17)–(20)。Qiskit/NumPy/SciPy。literal/補正を分離|solver_seedのみ。qubit上限21。不整合は例外。基底値・XY・Qiskit/tensor一致・復号を検査|
|reduction.py|人工問題/双対/顧客又は連続区間→縮小問題と展開写像|原著にない独自拡張。距離/荷量/双対を保存するマクロ変換|乱数なし。不正/重複/容量超過区間はValueError。展開距離と被約費用が一致することを検査|
|runner.py|人工問題/価格付け方式/有限上限→CG全履歴/整数解|原著図1。全列挙oracleをAOAの診断にのみ使用|AOA seedを反復ごとに記録。負列のみ追加。未取得停止と証明を区別するテスト|
|experiment.py|版固定JSON/新しい出力先→実験台帳/JSON/CSV|独立人工実験の構成。原著の未公開設定を補足する|seedは設定に記録。排他的作成、例外をFAILUREへ保存して停止。S需要/ODの入口なし|

## 原著との差

- paper_literalは式(18)/(19)の表示どおり、位置ごとの重複項を使う。fixed_depot=Falseは式(20)の範囲どおりt=0も混ぜる。この組合せの固定拠点違反を測定する。
- customer_uniqueは式(13)の顧客再訪禁止に対応する添字への補正案である。fixed_depot=Trueはt=0を定数代入し、ミキサーから除く補正案である。いずれも著者確認済みの修正とは呼ばない。
- 初期状態は全位置拠点のone-hot基底とする独自設定である。ALiMは許容容量内にも非零値を持ち、全制約を保証しない。
- XYは位置ブロックの行列指数で厳密に構成する。通常のXミキサーへ置換しない。
- 訓練はone-hot部分空間のテンソルで正確に状態発展させ、1000shotsの標本期待値をCOBYLAへ渡す。最終状態はQiskit Statevectorで実行し、テンソルとの忠実度/漏出を検査後、独立4096shotsを採る。圧縮は古典シミュレーションのメモリ削減であり量子ビット削減ではない。
- 内部拠点帰着を含む可行walkは、拠点間で分割して列にする。自由車両数の原著規模参照では距離/双対和が保存されるが、車両日列・バース双対がある研究版への自動適用は不可である。
- 原著はCBC/Qamomile/QURI Partsであり、本実装はHiGHS/Qiskitである。最終整数解は限定列集合上の最適解と表示する。

## 再実行

Python 3.12.11の新規venvを用い、reproducibility/environment/huang_cg_aoa_v1/requirements.lock.txtを導入する。既存の凍結環境へインストールしない。

~~~bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /path/to/independent/venv/bin/python -m pytest tests/toc_cg -q -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /path/to/independent/venv/bin/python scripts/run_huang_reference.py --output /new/run/directory
~~~

同じ出力ファイルが存在すると排他的作成で停止する。需要の生成/抽出やS1〜S3の配送計画は実行しない。時間は実測環境依存であり、他環境で同じ秒数になる保証はない。回路深さは論理ゲート深さと、取得した場合のrz/sx/x/cx分解深さを区別する。全結合の分解値は実機のルーティング済み深さではない。

完全な原著数値再現、研究規模適用、量子優位性は本パッケージの検証結果から主張できない。
