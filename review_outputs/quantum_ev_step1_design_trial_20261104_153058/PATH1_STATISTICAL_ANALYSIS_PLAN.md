# Step 2：経路1統計仕様

実施状態：既存の記述統計・cluster感度は存在する。T/PATH1_INPUT_SEED_STATISTICS.csvは3680行、input×設定ごと10測定repのn/平均/sample SD(ddof1)/min/max。T/scripts/analyze.pyで定数列SDを0とする実装を確認し、今回は元36,800行から再集計して照合した。P/B_INPUT_SEED_AGGREGATES.csvは初期差、gap、一致率、可行率をinput内平均した別表。P/statistics_tables.pyはinput→規模内等重み、25需要group bootstrap10,000回seed20261102のpercentile95%を補助感度として実行。P/CLUSTER_SENSITIVITY_INTERVALS.csv等は実在する。現行古典近似JCとの差を主にした表や、全指標の中央値/IQRは未完了。既存値の符号JQ−JinitialをΔJと誤認しない。

観測構造：group_id（25需要群）→parent_id（26親、同一groupに複数親あり）→物理input（460、規模と条件の派生）→設定8（対応あり）→fit1→measurement rep10。repには独立PCG64 streamがあるが学習条件は同じ。設定・規模を独立な無作為標本とみなさず、groupの独立性も確率標本によって立証されていない。

主推定対象は「保存された有限入力cohortについて、設定aと事前指定JCの、10測定反復にわたる平均品質差を各入力同じ重みで平均した値」。規模s別θsa=(1/Ns)Σi∈s[(1/10)Σr(JC,i−JQ,iar)]。全体は460入力等重みを補助として示し、6規模等重みの値と混同しない。JC2法は別々に出し、主はgreedy adjacent。学習予算非統制という限定を表題に付す。

実行順序（Step 2、今回は未実行）：

1. provenance/hashを固定し、(input SHA,設定,rep)PK、460×8×10、初期/近似/厳密join一対一を検査。古典近似元分数を確認し、可行性・対応が未確認の対照は差をHOLD。
2. metric仕様に沿いexact FractionでΔJを生成。JQ/Jinitial/JC/J*、exact有無、fit ID、group/parent、欠測理由、測定seed entropyを保持。
3. 各input×設定でmean/median/SD/min/max/Q25/Q75/IQR、改善/可行/最適一致を算定。SDはddof1、quantileは線形補間。mean SDとinput間SDは別列とする。
4. 規模×設定×対照ごとにinput平均差の平均・中央値・入力間SD/IQR、改善確率のinput平均と「10rep中1回以上改善したinput率」を区別して出力。全分布と全8設定を表示し有利な設定だけ選ばない。
5. gap/一致率はexact407（規模78/78/78/78/57/38）に限定。exact有無の初期目的/規模/観測特徴を比較する欠測監査を出す。53の値は代入しない。complete-caseのgapを全460へ一般化しない。
6. 設定間の比較は同じinputにおける差。異なる設定のrep番号を共通乱数によるpaired seedと自動認定しない。input内rep平均の対応で比較する。
7. fit時間は一fit一行、resource scope別の分布として示す。10rep行へ複写されたfit時間を10倍数えない。

不確実性区間：有限cohortの記述自体に標本抽出CIを強制しない。補助として二種類だけ事前宣言する。(a)固定input/fitでの測定乱数感度：input内で10repを復元抽出、設定間streamは独立に再標本化し、10,000回seed20261104、percentile95%。全8192shotsを独立最終解として数えない。10repでは尾の精度が限られると注記。(b)仮想的に同様の需要group母集団を想定したcluster感度：25 groupを25個復元抽出、同groupの全parent/input/設定/repを一緒に保持、input内平均後θを再計算、同じ再標本化重みを全対応contrastに使う。10,000回seed20261102で既存との再現可能性を保持。group交換可能性と群間独立を仮定した仮説的感度であり実配送母集団の校正済みCIではない。群が欠ける規模やexact subsetでは有効cluster数とundefined回数を報告。rep-onlyとgroup区間を無説明に合算しない。

学習乱数の区間は全入力の複数学習がないためHOLD。中央値・SD・IQRを8設定混合で一つに潰さない。検定/p値は必須とせず、量子優位の有意性や改善量を研究の合否にしない。分布・境界・負/ゼロ結果を同じ仕様で報告する。

予定出力：INPUT_CONFIG_METRICS、PAIRED_CLASSICAL_APPROX_DIFFERENCES、SCALE_CONFIG_DISTRIBUTIONS、REFERENCE_MISSINGNESS、RUNTIME_BY_SCOPE、OPTIONAL_MEASUREMENT_SENSITIVITY、OPTIONAL_GROUP_SENSITIVITY。いずれも新Step2 trialに保存しP/Tを上書きしない。

古典近似元RESULTの920経路を今回照合済みなので、同一入力・目的・制約の品質差の算定は開始可能。各法は保存された1検索seed/inputのみであり、古典側の学習/探索seed分散まで評価した比較ではない。初期incumbent保持ありの古典とraw Qの出力規則差は別条件として保持し、統制追加実験では両側同じ初期解保持規則を事前に固定する。
