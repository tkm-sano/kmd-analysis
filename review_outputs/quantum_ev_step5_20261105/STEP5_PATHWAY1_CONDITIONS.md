# 経路1の成立条件

必要な接続をA〜Eに分ける。いずれかの段階だけをもって量子技術の運用寄与としない。ΔJの符号は候補−greedyである。

| 条件 | 証拠 | 適用範囲と判断 | 未検証事項 |
| --- | --- | --- | --- |
| A 改善解の存在 | mirror支持460でJ*_S=J_initial、J_greedy≤J_initialを照合 | 指定mirrorの2^floor(n/2)支持では改善候補がない（CONDITIONAL） | 全順列や別mixerへの一般化は不可。activeは3点grid全t0であり全active支持の最小証明ではない |
| B 改善解の取得 | Bの差分布、診断3入力の9,312fit/93,120測定 | 支持内存在と有限予算での取得を区別。診断は主greedyが既に最適 | Grover大規模の悪化原因は角度・予算・初期・測定等に分解し切れない |
| C 時間的成立 | CPU工程記録9,603、固定例Q34.643ms/脱位相35.014ms | CPUでの限定scope測定。greedy12.142msは1出力、Qは10測定 | 全工程τ_total・H_plan・QPU総性能HOLD |
| D 計画採用 | 全36,800保存best可行、容量/帰庫条件をNPZ再検算 | モデル上の可行性は確認。greedyfallbackなら採用後差0の条件式 | 現実の採用イベント・出発遅延・道路受入未検証 |
| E 成果への反映 | 帰庫差=ΔJ、最後の顧客差=ΔJ−帰路差、余裕最小7435.748秒 | 保存Bの共通上限遵守差0ポイント。実定時率には置換しない | 契約期限と実行交通・顧客別時刻の運用検証HOLD |

## 支持不存在と取得失敗の区別

`/home/takuma/kmd-analysis/review_outputs/quantum_ev_step2_analysis_trial_20261104_155535/PATH1_SUPPORT_AUDIT.csv` はmatching-chain独立DPにより460入力全てで支持内最良値=初期値を示す。`data/B_PLAN_GAPS_36800.csv` の初期値/主対照対応から J_greedy≤J_initial が成立するので、この特定支持内ではJ_candidate<J_greedyを満たす解がない。測定shotsや同じ支持内の学習を増やしても不存在を補うことはできない。これは支持の制約に関する結論である。activeのt0選択を、その広い全到達空間での不可能性証明へ置換しない。

Grover全順列支持のAは全問題の最適参照と主greedyを比較して、支持最小がgreedyより小さい入力でのみ成立を確認できる。監査後414参照は再列挙234、保存DP78、独立有理LP61、保存MIP等値のみ41であり、外部証明未了41を区別する。残る46はJ*未証明である。Bの差と可行性は460全件で利用できるが、46のglobal gapを推定補完しない。参照の有無と「改善解が存在しない」を同義にしない。

診断R1_020のfull/基底/graphでは最適取得p1=58/97、p2=78/97、条件付きWilson95%は49.8〜69.0%、71.4〜87.1%である。初期状態等の条件を伴う取得能力の結果である。greedyは診断入力で最適のため、最適取得確率の差をgreedy超えと解釈しない。旧10測定を97独立学習と混ぜない。

## 単一原因への帰属を避ける

mirrorはAの不成立を指定支持で確認できる。一方Groverの大規模悪化は、全支持であることだけでは角度最適化・有限shots・初期状態・各backendの精度/予算・出力規則を統制したことにならず、単一原因を確定できない。旧greedyと8設定の予算・初期解保持の差も残る。CPU模擬結果からQPU優劣、量子優位性、量子一般の不可能性を主張しない。

根拠はStep2 `PATH1_PAIRED_COMPARISONS.csv`、`PATH1_SUPPORT_AUDIT.csv`、`EXACT_REFERENCE_STATUS.csv`、`QAOA_CONTROLLED_EXPERIMENT_REPORT.md`、`PATH1_RUNTIME_PROTOCOL.md` とStep4 P1-01〜14である。
