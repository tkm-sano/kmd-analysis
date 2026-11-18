# 二目的研究のCPU並列実行方針

2026-11-17の最新研究判断に基づく。正本は[二目的研究方針](DW_RESEARCH_POLICY.md)と[現行設定](../../configs/toc_delivery/dw_policy_20261117_v1.json)。旧本文は[変更前の保存版](../audits/dw_policy_20261117_v1/before/docs/research/CPU_PARALLEL_EXECUTION.md)に保全する。

B/C/Dと古典置換対照の内部4プロセス並列マルチスタートを継承する。各枝1物理コア・native solver1thread。手法間・外側試行間は逐次。割当不足を黙って逐次へ落とさない。CPU数の変更は全手法共通の明示設定と新登録で行う。

有限作業量の条件は`configs/toc_delivery/termination_rules_20261116_v1.json`を継承する。旧`dwt_balance_v1_4_cpu_parallel.json`の時間予算・T正規化は履歴であり、通常の新規研究の既定にはしない。通常実行に時間上限を復活させない。今回の修正は新しい実験の実行を許可しない。

全枝のseed、PID、affinity、成功／失敗、D/W、実行ログ、量子処理・shotsを保存する。未選択枝の処理を隠さず、内部枝を外側試行数・独立需要数へ加算しない。T_programの計時境界は履歴・実行管理情報として保持するが、RQ、性能比較、旧J、図、必要品質反復数に使わない。

旧逐次設定と結果は保全する。単コア再現には`--historical-serial-reproduction`等の履歴指定を用いる。旧三目的CLIの再現にも`--historical-reproduction`を明示する。新規実験を旧APIの互換経路へ流さない。
