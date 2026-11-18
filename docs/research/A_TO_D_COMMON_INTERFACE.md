# A〜Dの二目的分析インターフェース

2026-11-17の最新研究判断に基づく。正本は[二目的研究方針](DW_RESEARCH_POLICY.md)と[現行設定](../../configs/toc_delivery/dw_policy_20261117_v1.json)。旧本文は[変更前の保存版](../audits/dw_policy_20261117_v1/before/docs/research/A_TO_D_COMMON_INTERFACE.md)に保全する。

生の実行契約・ソルバー・保存形式は履歴再現のため保全する。新しい分析契約は`configs/toc_delivery/dw_policy_20261117_v1.json`、実装は`src/kmd_toc/dw.py`。

分析へ採用する品質値は、入力VALID・実行NORMAL・計画VALID・二重検証VALIDATED・adoptable=trueを満たす同じ計画のD[km]とW[分]のみ。Tや旧Jの値・欠損・大小を採否、支配、平均差、順位に利用しない。失敗の品質はnullとし、全試行の状態を残す。

読み取り時に登録lock、run一覧、保存ソースsnapshot、凍結入力／ODのhash、結果ID・物理条件・設定hash、保存計画hashを照合する。出力は元データから独立した新しいディレクトリに保存し、既存出力があれば拒否する。

`compare_objectives`は2要素(D,W)を受け取り、絶対差、正の基準に対する相対差、二次元支配を返す。3要素の呼出しは現行契約で拒否する。旧の3要素契約は保存版に残す。運行モデル内の秒単位時刻は削除しない。
