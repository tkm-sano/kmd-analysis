# 小規模QAOA追加統制実験：実行前仕様

目的は支持制限・初期状態・mixer・layer・学習乱数・測定乱数を可能な限り分離すること。既存8設定では同時に条件が変わるため新規実験が必要。新実装はtrial内の厳密な順列部分空間シミュレータであり、元staged8の再実行でもQPU実験でもない。3/4顧客に限定し、大規模性能へ一般化しない。

入力選択はQAOAの成績を見ずに古典初期gapで固定：R0_001（3顧客、初期最適）、R1_001（4顧客、初期最適）、R1_020（4顧客、初期非最適の辞書順先頭）。R0に初期非最適入力はない。これは機構診断の層別選択で、156入力の確率標本ではない。

要因は支持FULL_PERMUTATION/MIRROR_ORBIT、初期BASIS_INITIAL/UNIFORM_SUPPORT、mixerPROJECTOR/GRAPH_SWAP、p=1/2の完全要因配置（16cell/input）。各cellでQAOAと、各mixer直後に完全脱位相する古典確率過程DEPHASEDを対応比較。graphはFULLでは隣接位置交換の生成グラフ、MIRRORでは対称位置pair交換グラフ。両mixerは同一指定支持の中で作用し、costは共通の有向OD秒。支持を変えた対比にはグラフ変更も含むためmixer単独の効果としない。

QAOAはexp(-i gamma C)とexp(-i beta Hmix)をp回適用。projectorのHmixは支持上の一様状態への射影。DEPHASEDは同じunitary mixerの絶対値二乗を遷移確率として用い、cost phaseは確率を変えない。それぞれ独立に同じ64目的評価上限のCOBYLAでexact expected ODを最小化。gammaは[0,8]、betaは[-pi,pi]、cost scalingはFULL費用の標準偏差、共通の平均を引く（大域位相）。厳密最適経路/目的値は学習へ渡さず評価のみ。DEPHASEDが量子計算機を必要とする主張はしない。

古典対照は(1)Step1指定greedy adjacentの同一入力保存結果を主ΔJへ利用、(2)同支持・同初期・同mixer・同p・同評価予算の独立最適化DEPHASEDを機構比較。後者はシミュレータ内の確率遷移を正確に評価する統制で、現実の古典最良手法との競争ではない。

独立学習反復数は、各cellのprimary測定rep0（8192shotsで改善解を取得したか）の取得確率を95% Wilson区間で最大半幅0.10以下に記述する精度から、ceil(1.959964^2/(4*.1^2))=97学習seed/cellとする。各fitは別optimizer-start seedを用い、測定seedは別SeedSequence。測定10rep/fit×8192shotsは既存との継続性とfit内変動確認用。97×10を独立学習としない。主推定は選択した入力/cell/アルゴリズムの乱数過程に条件付きである。fit間bootstrap10000回は補助、検定は行わない。

まず3独立学習seed/cellのpilotを実行し、正規化/可行性/直接行列作用との一致/seed再現/数値精度を確認する。pilotの予測全量wallが1800秒、process RSS2GiB以内であれば同じ事前条件の97seed本実験へ進む。pilot値を使って有利なcellを削除しない。precision failure/resource failureはHOLDとして停止し、改善の有無をgateにしない。

出力はraw sampled-bestと、両方式とも初期incumbentを保持する採用値min(initial,sampled)を別列に保存。primaryのΔJは保存greedy−raw Q、規則を揃えた保持あり値とDEPHASED差は補助。最適一致はFractionで判定、全順列を可行性検査し、float state errorは正規化/独立直接作用比較で検証。極小確率の数値誤差を実測改善へ変えない。

時間は入力/支持構築、パラメータ最適化（内数として回路/確率過程シミュレーション）、10repサンプリング、解検証、後処理を分離し、非重複total wall/CPUを記録。同一CPU affinity・1thread・逐次、最初のwarmupは別に記録。import/プロセス起動/QPU/転送は対象外で、実運用tau_totalやQPU速度とは呼ばない。H_planは未設定。

## pilot開始前の精度対象の明確化

既存JCが選択3入力ですべて厳密最適に達していることを元表で確認したため、主ΔJの正改善は定義上不可能である。この負条件を保持し、97学習seedのWilson精度対象は「primary測定rep0の最適解取得率」とする（反復数は同じ97）。改善のために入力やJCを差し替えない。初期解に対する改善、最適到達、期待目的の機構比較を併記する。

測定8192での飽和を調べるため、全fitの保存確率分布からshots=1/8/64/8192での最適取得確率・期待sampled-bestを解析的に算定する。追加の独立実験数とは数えず、同じ学習状態の測定予算感度として全cellを出す。これはpilot結果を見る前の追加固定である。

## 本実験開始前の追加診断

pilotは全96cell・3seedで数値検査PASS、97seedの見積wall約322秒で資源gate内だった。全cellを残して本実験へ進む。独立最適化DEPHASEDとの比較に加え、各QAOAの同じ学習済み角度をDEPHASEDへ与えた分布を解析的に比較する。これにより同支持/初期/mixer/layer/角度に条件付けた干渉の差を診断し、パラメータ最適化差と区別する。追加の学習反復には数えない。
