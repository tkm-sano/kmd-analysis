# 実データ投入チェックリスト

## 必須ファイル
- benchmark_evidence.csv
- od_flow.csv
- translation_parameters.csv
- model_controls.csv

## 上流入力の確認
- 一次文献、レビュー、専門家判断が区別されているか
- 品質閾値が問題類型ごとに定義されているか
- 古典条件と量子条件の両方が存在するか
- 重み付け規則が事前に固定されているか

## 下流入力の確認
- 起点地域、都市、産業群の定義が固定されているか
- 流入就業者数が起点地域×都市×産業群単位で整備されているか
- 一般化交通費の構成要素が同一単位で揃っているか
- 自動車依存度の代理指標の作り方を記録しているか

## 実行前確認
- `python src/validate_inputs.py --input_dir data/actual_input` が通るか
- 出典と取得日を記録したか
- デモ値が actual_input に混入していないか
