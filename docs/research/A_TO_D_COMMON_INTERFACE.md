# A外部参照とB/C/Qの現行評価インターフェース

2026-11-20更新。この文書は現行案内であり、研究仕様の正本ではありません。[研究仕様1〜7（凍結v1）](../frozen/配送計画最適化_評価指標と実験条件_1-7.md)と[追加運用仕様FCFS_v1](FCFS_OPERATING_POLICY_V1.md)を参照します。数式・数値・未決定事項をこの案内から新たに決定しません。更新前の案内（保全資料）は保全しています。


研究表記Qの内部識別子は既存Dを含む。保存済みのmethod_idを一括renameしない。AはPlanを持たない外部参照で、FCFS・計画の共通物理評価の対象外。

現行は `fcfs_v1.evaluation.evaluate(problem, plan)`。共通物理検証と独立FCFS検証を行い、D_kmと総積込待機W_minを返す。平均や内訳の診断欄を研究Wへ代用しない。I_dualは今回のFCFS実装では未統合である。

FCFSを満たさない計画は拒否する。旧計画の読み取り評価と、固定経路を明示的にFCFS再構築する処理は別であり、後者は新Plan・別出力に保存する。旧新の生成版を記録し、混在させない。欠測を0へ補完しない。

Plan/Problemの既存型は[共通schema記録](toc_delivery_common/COMMON_INTERFACE_SPEC.md)、有効な生成・完成経路は[運行実装対応](TOC_DELIVERY_SPEC.md)を参照する。`cargo_wait_v2.evaluation`の旧平均荷待ち・イベントAPIと `evaluate_cargo_wait_v2.py` は現行FCFS評価入口と同一ではない。

現行CLIは `scripts/analyze_dw.py --input COMMON_INPUT --plan B_PLAN.json --plan C_PLAN.json --plan D_PLAN.json --output NEW_OUTPUT`。[再現手順](REPRODUCE.md)の新規出力・同一入力条件に従う。本実験全体HOLD。
