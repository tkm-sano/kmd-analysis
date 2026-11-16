# 因果経路2・限定Level2検証 run01

結論はFINAL_REPORT_JA.md、計算条件はRUN_CONFIG.json、数値確認はevidence/NUMERICAL_CHECKS.csv、独立した保存後監査はevidence/SERIALIZED_AUDIT.csvにある。原データを新しく読み直し、旧T08関数と凍結DC核を参照する。旧成果物・論文は書き換えない。

リポジトリルートで以下を順に実行する。

```bash
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python review_outputs/pathway2_level2_validation_20261105/run01/scripts/validate.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python review_outputs/pathway2_level2_validation_20261105/run01/scripts/report.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python review_outputs/pathway2_level2_validation_20261105/run01/scripts/audit.py
```

完全再現にはRUN_CONFIG.json記載の旧成果物、旧T09参照、保存軌跡アーカイブ、凍結コード、sourcesのPDF/xlsxが必要である。外部取得は不要である。環境のバージョンはevidence/ENVIRONMENT.json、原著・SI・元xlsxのURLはevidence/PRIMARY_SOURCE_CATALOG.csvに記録する。別出力への再実行は環境変数LEVEL2_OUTPUTに新しい空ディレクトリの絶対パスを与え、3スクリプトに共通指定する。設定を変更する場合は別のJSONへ複製し、LEVEL2_CONFIGにその絶対パスを与える。元成果物を変更しない。

今回の数値は公開近縁全電池の記録と仮想20kWh設計の算術検算である。実用LP/S完成パック・実車DCはHOLDである。17質量条件、境界18行、3軌跡/2Crr/4質量のDC24行であり、大規模再計算ではない。図はfigures、放電生抽出と部材単位検算はevidenceにある。
