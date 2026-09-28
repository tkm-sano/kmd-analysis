<a id="tokyo-traffic-simulation-processed-data"></a>

# 東京交通シミュレーションの加工データ

このディレクトリには、再生成可能な交通シミュレーション専用の加工データを保存する。生成ファイルは版管理対象外とし、この説明とディレクトリ構成のみを管理する。

- `calibration/`：道路網の要素に対応付けた観測値と較正対象。
- `demand/`：旅客・貨物・出発地到着地間の需要の加工データ。
- `driver_behavior/`：根拠を記録した運転技能・運転傾向のパラメーター条件。
- `road_network/`：対象範囲の切出しと正規化を行った道路網の中間データ。
- `sumo_inputs/`：生成したスーモの道路網・経路・追加ファイル・設定。
- `traffic_profiles/`：時間帯別の交通量・速度・車種構成。
- `validation/`：実行結果の検証に使う参照表。

取得した原資料は`03_data/raw/traffic_simulation/`、実行成果物は`reproducibility/outputs/traffic_simulation/`に保存する。`06_outputs/traffic_simulation/`には確認済みの最終成果物のみを置く。
