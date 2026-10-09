# Configs：設定の参照入口

[CANONICAL_CONFIG_INDEX.csv](CANONICAL_CONFIG_INDEX.csv)は19の役割別参照です。需要・固定割当・OD・routing・PUBO/QAOA・SUMO・Battery/DC・統合分析・古典6規模・検証を対象とします。同じfreezeを複数の役割が参照します。設定だけでなく、入力bindingや実験計画も区別して記録しています。

正式設定は元位置に保持します。Indexのsource_path、SHA256、サイズ、using_implementation、パラメータ参照、既定値抜粋、seed方針、外部入力を確認してください。物理移動・設定値の変更・正式設定のコピーは行っていません。source freezeとauthority chainは既存のままです。Index自身は新しいfreezeではありません。

[examples/NOTEBOOK_INPUTS.json](examples/NOTEBOOK_INPUTS.json)は小規模Notebookの**入力パスを指定する設定例**です。正式実験設定ではなく、QAOAの回路・角度・seed・shots・最適化条件を上書きしません。Notebook02の既定値はgamma=0.001、beta=0.2、shots=64、seed=20261009、DO_OPTIMIZE=False。正式Protocol V2のp=1・最終4096標本等とは別です。

Notebook adapterはこの設定からdata/examplesのfixtureを選び、登録hashを検査します。入力が欠損・改変されていれば停止し、旧fixtureへ自動フォールバックしません。初期入力の値を変える場合はNotebookのメモリ上の条件変更例を使ってください。新しい入力ファイルを登録する場合は独立したDEMONSTRATIONとして来歴・hashを更新し、正式freezeを書き換えないでください。

配置後はrootで `python -B tests/test_distribution_layout.py`、`python -B notebooks/test_notebooks.py`。依存環境は[Notebook利用案内](../notebooks/README.md)。正式runnerの設定Indexに辿れても、全量OD・network・native fork・SUMO・実験入力を取得したことにはなりません。公開権利は未確定です。
