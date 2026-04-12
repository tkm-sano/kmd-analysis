# モデル仕様（簡略）

1. 材料探索性能
   search_performance_index = 
   0.4*search_space_score + 0.35*evaluation_accuracy_score + 0.25*engineering_validity_score

2. 軽量化率
   lambda_rate = intercept + slope * search_performance_index
   ただし上限 lambda_max と採用率 adoption_rate を掛ける

3. 燃費改善率
   fuel_efficiency_gain = alpha * lambda_rate

4. 単位距離当たり燃料費・電力費
   unit_cost = energy_price * baseline_energy_intensity * (1 - fuel_efficiency_gain)

5. 都市流動更新
   beta は負のコスト弾力性として保持する
   simulated_inflow = base_inflow * exp(beta * relative_cost_change) * condition_multiplier
