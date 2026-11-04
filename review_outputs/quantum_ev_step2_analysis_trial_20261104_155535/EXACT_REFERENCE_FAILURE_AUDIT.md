# 厳密参照53入力の終了理由監査

判定：原因の実装上の意味と保存数値対応は確認。新規独立証明7、残り46はHOLD。

元実装は`W/FINAL_SOURCE_SNAPSHOT/scripts/run_unified_no_windows.py`のreference()およびrun_exact_references.py。SCIPがoptimalを返し、書出しsolutionから全顧客一巡回路を抽出しても、独立目的値UとExact Dual Bound LがFractionで一致しない場合、`EXACT_BOUND_WITNESS_MISMATCH`で停止する。これはtime limitや求解不能の同義語ではない。

53件全て：R4=21/R5=32、同じSCIP10.0.3 binary SHA `a2c2342a087d66b1ccc31748db1c898bfe9d95cfc8ab791807257a5cd580ab3d`、optimal状態、timeout false。LP全有向arc・0基準索引・デポ・係数をNPZへ照合し一致。solutionヘッダの目的値は経路のFraction総和および係数annotationと一致した。一方、同実行ログのExact Primal=Exact Dualとsolution目的の差は2e-16〜5.36e-14秒、refined保存witnessとの差は1e-16〜1.7e-14秒。

boundはSCIPの緩和/探索木が与える最小化下界、witnessは入力上の可行巡回路による上界。source writerはDecimal(str(float64))をLP係数に用い、検査はFractionで行った。float許容差で等価と昇格していない。旧SOURCE/FINAL_SOURCEの停止条件は同じで、版間のその条件差が原因とは確認されなかった。異なる版のソルバを使った53群ではない。

独立SoPlex8.0.3で保存最終LPの連続緩和を再求解した。初回default toleranceでは非ゼロ残差が残るため証明として不採用。-f0/-o0で有理数双対を得て、degree/horizon/有効subtour制約と変数0..1から `L=sum(y*b)+sum(min(0,c-A^Ty))` をFractionで独立検証した。値が上界と厳密一致した場合のみ新規最適証明とした。

pilotのR4_009では整数だが複数subtour、R5_001では分数LP解を確認した。厳密mincutで有効SECを追加したpilotも、分数DFJ緩和または上限で停止した。したがって「ログ表示の丸めだけ」と断定できず、元コードは微小な未解決差を認識して停止する一方、書出し解が一巡回路であれば追加SECを打たないという限界がある。SCIP内部の有理数primalと書出し経路の不一致を完全に特定したとは主張しない。

共通特徴はevidence/EXACT_INPUT_FEATURES.csv/FEATURE_COMPARISON.csv。大規模で微小係数/近接費用が存在するが、証明済み群にも同様にあり、単一の入力特徴だけで失敗を説明できない。根拠のない原因を補完しない。

実行前仕様・段階判断はEXACT_RECHECK_PROTOCOL.md、全CLI/LP/primal/dual/資源はexperiments/exact_*。148件（既存large95＋欠測53）を独立検査し、61件で独立LP下界と巡回路の等値を得た。この61は新規7と既存54の合計であり「61新規入力」ではない。53件の大規模branch-and-boundを無条件には投入せず、必要な境界監査を完了した。
