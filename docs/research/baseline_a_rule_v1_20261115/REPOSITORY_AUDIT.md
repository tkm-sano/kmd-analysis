# リポジトリ監査

参照資料は [統合設計v0.1](../BASELINE_A_DESIGN.md)、2026-11-15。作業HEADは `8605d5412f6af62229a83095c35ab04c8c7dd9b1` で一致した。checkout/reset/commit/pushはしない。開始時にREADME/.gitignoreが変更済みで、A関連コード・設定・結果を含む多数の未追跡資産がある。HEADだけでは実行状態を同定できないため、`INITIAL_GIT_STATUS.txt` と `PRESERVATION_BEFORE.json` を保存した。既存READMEは研究全体の案内として読み、変更しない。AGENTS.mdのB/C/D並列契約を採用するが、今回B/C/Dの実行はしない。

最初の広範なdocs再帰一覧取得はNFSメタデータ待ちとなり、自分の読取プロセスを停止した。全リポジトリの完全ハッシュを取得したとは主張しない。保全対象を既存kmd_tocコード・関連設定/テスト、既知の設計資料、過去結果の最上位集計、凍結需要全体、S1〜S3 Route入力全体へ限定してハッシュを保存した。新規ファイル以外はこの取得まで変更していない。保全範囲はJSON内の全パスで確認できる。

## 設計書・実物・今回の扱い

|対象|①統合設計v0.1|②実ファイル/コード/ログ|③今回の扱い|
|---|---|---|---|
|Aの役割|仮定付き代理計画、最終方式未確定|過去A-area/Cook報告は代表性FAIL・主比較不可と記録|旧判定は保全。今回の計算方式の採否と、対象実績未検証を別判定|
|初期区域|角度順・0度・同数分割|construction._angular_orderは東0度、反時計回り、半径二乗、stop_id tie。入力tuple順で車両index|同式を新コードへ明示実装し、IDはNFC・衝突拒否を追加|
|負荷調整|地点ごとのproxy二乗和、最大V移動|_balanceは `120+(ceil(t0j)+ceil(tj0))/2`、delta最小候補を選ぶ。訪問順生成前|旧proxyを呼ばず、毎候補の全スケジュール(O,H)に置換。最初の厳密改善|
|隣接境界|有限境界移動|旧_balanceは各区域の両端から左右双方へ候補を作る。端点と対応境界を限定していない|対応する円環境界の端点のみ。0度跨ぎ列と空区域の隣接を確定|
|訪問順・便|道路距離NN→容量60分割|A2は同順。area_programは校正選択NNまたは自動区域優先、旧proxy調整も共有|NNのみ、割当が変わるたび再順序化・再分割。交換interface追加|
|全体時刻|FCFS・最大2便・準備0・arc切上げ|A2/area_programは全first/reloadイベントをheapで接続|保持し、全候補で全体を再計算。独立FCFS再構成を追加|
|空便・非稼働|最大2便|common.scope.unused_vehicles_allowed=true、validate_planは空の使用便を拒否|全台必須としない。非稼働L=0、帰着null|
|道路|Route版、旧文言不整合あり|common JSONはsame_table_response。登録manifestはtable_distances_used=false・同Route object|新設定のconditions_referenceで物理v1.1と道路Route manifestの正本関係を整理。旧ファイル不変|
|共通完成|各手法候補から完成|pipeline/completion.complete_routesはCP-SATでroute pool選択、車両/便/積込開始を最適化。assembleは選ばれたstartを保持してバース彩色|A_rule_v1は完成器を使わずFCFS。生成された便内部順序は完成器で変更されないが、車両所属等は変更し得る|
|DWT内のA|Aを独立条件として扱う|dwt/methods.generateのmethod=Aは旧A2の便候補をcompleteへ渡すため、FCFSのみのA2とは異なり得る|旧DWTのA経路へ新Aを自動接続しない。正式比較への未解決事項|
|検証|共通+独立|common.validationはOD.legで全時刻/D/W。program_validationはDecimalで別実装、生成器helper不使用。ただしFCFS規則そのものは検査しない|両物理検証を維持し、新rule_validationで別のイベントアルゴリズムによりFCFS・O/H・全帰着も照合|
|T|読込/hashから二重検証まで|program/area_programは同境界。ライブラリ準備は別記。旧DWT設定はA除外・Tref60秒を持つ|T_input/planning/validation/attemptを分解。正式Trefは未確定のまま|
|Cook|順序の追加候補。大田区接続未実装|著者commitはdc4ebc0aa091d4d1eb7dc7d9b9b2d8f8c19664ce。BUILD.jsonはmake -j1成功。external CLIはpath/precedenceと1% merge|著者コードと既存score・逆転率・有向辺・再進入・閉路時間比を保全。今回再学習/再採点しない|

## 実在する入力・処理・結果

`configs/toc_delivery/common_conditions_v1_1.json` のsha256は `bbb15417a4eee5072f8118056c90ab422d792b4cedc35a6a06bf6bc0497fe8d2`。容量60、最大2、1800/120/0秒、28800〜72000、S1=1000/10/2、S2=2000/20/4、S3=4000/40/8で依頼条件に一致した。frozen_demand_v1.jsonのmanifest pinは `9e1b0ba8afed05f9fbae6ff725489a3e0d602bf8b1e9f19e5b9e8a6a8eada776`。原本は `03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/MANIFEST.json`（大文字）。実需個票ではなく凍結合成需要でS1⊂S2⊂S3。

実ODは `output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/{S1,S2,S3}/od/manifest.json`。a_provisional_program_v2.jsonの全input/OD file pinを新版設定にコピーし、実行時に確認する。manifest hashは順に `c508951f20035a93dce8eadc7965442fb60dfeff0cea6ed4d61962ba0b137c30`、`3de697376510522dab96a7dad8db6bb7e273e5c0b10eba62f5789d4fc0f1db77`、`57a0e40037cb15baf1da2e284d8399f89f0ebe20ff506c58ee20a1391dbca2f5`。正確な最終文字列と全ピンは新版JSONを参照（転記表より機械照合を優先）。道路は保存manifest上の関東OSM 2026-07-16・OSRM5.27.1 static car・有向・fallbackなしで、原本やODの再生成はしない。

現行入口 `scripts/run_a_area_program.py` はモデルhash確認、登録入力読込、area_program.execute、共通/独立検証、出力を行う。`scripts/run_cook_transfer_study.py` は外部Amazon履歴の選択、著者コードの学習/推論、採点、再集計の別試験。対象モデル/データ/時間を混ぜない。

既存A-area選択結果は `output/toc_delivery/a_area_v3_20261115_selected_checks02/SUMMARY.json`。D/WはS1=551.1398/422.45、S2=965.1498/883.8167、S3=1722.4391/1588.4667で、各2回の確認であった。未採択自動区域候補は別診断。Cook結果は `output/toc_delivery/a_cook_transfer_20261115_finalized01`、独立監査は `a_cook_transfer_20261115_validation01`。過去にFAILとされた項目も数値も変更しない。

B/C/Dの契約は `AGENTS.md`、`docs/research/CPU_PARALLEL_EXECUTION.md`、`configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json`、`src/kmd_toc/dwt/{methods,parallel,worker}.py` を照合した。入力Problem・出力Plan、四枝×1コア/native1thread、全枝停止/選択/再検証までの親wall、未選択枝/quantum量も保存する。Aのために制約を緩和しない。比較上の差と未接続部分は [EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md) に分離した。
