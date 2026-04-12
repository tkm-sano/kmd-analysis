# 文献レビュー手順テンプレート

## 1. 検索対象
- データベース:
- 検索日:
- 対象期間:
- 言語:
- 分野:

## 2. 検索式
- 問題類型ごとの検索式:
- 量子条件を示す語:
- 古典条件を示す語:
- 材料・表面・界面・格子・腐食などの語:

## 3. 採否基準
### 採用
- 古典条件と量子条件の比較が可能である
- 品質指標が明示されている
- 時間、計算資源、候補生成数のいずれかが読める

### 除外
- 比較条件が不明
- 品質指標が定義されていない
- 重複報告である

## 4. 抽出項目
- source_key
- industry_group_id
- problem_class
- compute_condition
- quality_metric
- quality_threshold
- budget_raw
- budget_unit
- time_hours
- quality_value
- valid_candidates
- quantum_algorithm_availability
- evidence_weight
- note

## 5. 根拠レベルの記録
- 一次文献
- レビュー
- 専門家判断

## 6. 重み付け規則
- 直接比較の有無:
- 再現可能性:
- 品質指標の明確性:
- 分野適合性:

## 7. 曖昧な値の扱い
- 欠損は補完せず空欄のまま残す
- 補助的判断を入れた場合は note に理由を書く
