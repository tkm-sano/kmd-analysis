# 依存関係と検証範囲

|範囲|必要なもの|今回の扱い|
|---|---|---|
|CORE|Python3.12.3、numpy2.3.1、pandas2.2.3、scipy1.16.0、highspy1.15.1、正式source・小規模fixture・保存集計|軽量API検証。凍結ソースの必要部分への接続を含む|
|NOTEBOOK|CORE、qiskit2.1.1、nbformat5.10.4、nbclient0.10.2、ipykernel6.30.1と推移依存|6冊の既定セル。教材回路のためQiskitはquickstartに含む|
|QUANTUM_OPTIONAL|正式Protocolの専用環境、worker/QPY等|本番最適化・実機・高負荷シミュレーションは未復元|
|SUMO_OPTIONAL|SUMO/native fork、専用router、道路ネットワーク、全OD、worker設定|保存軌跡APIはSUMO不要。全量運行は対象外|
|FULL_RESEARCH|元のanalysis/qgpu/native環境、大容量入力と全量証拠|既存requirements-analysis.txtとRelease Manifestを保持。quickstartとの同一環境化はしない|

[quickstart lock](requirements-quickstart.lock.txt)はNOTEBOOKまでの実測解決版です。既存analysis定義（Hayate保存参照: `reproducibility/environment/requirements-analysis.txt`、公開ツリー非同梱）のnumpy/scipy等とは用途が異なるため上書きしません。これは正式研究環境の完全復元ではありません。OS、ネイティブライブラリ、配布物の永続保存は別途必要です。

外部ライブラリはpipで取得し、ソースをこのリポジトリへ再配布しません。インストール成功はライセンス互換性・自作コードの公開権限確認とは別です。
