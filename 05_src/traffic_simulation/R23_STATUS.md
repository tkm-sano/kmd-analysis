<a id="r23-current-authority"></a>

# R23の現行正本

| 項目 | 現在の状態 |
|---|---|
| R23 | `R23_CLOSED_WITH_DOCUMENTED_LIMITATIONS` |
| コード監査 | `CODE_AUDIT_PASS_WITH_LIMITATIONS` |
| 再現性 | `RESULT_REPRODUCED_WITH_LIMITATIONS` |
| 来歴が明確な実行 | `R23_PROVENANCE_CLEAN_RUN_PASSED` |
| 未解決の重大・主要課題 | 0 / 0 |
| R24 | [現行研究設計](CURRENT_RESEARCH_DESIGN.md)を参照。判定段階A〜Dと経路計算の互換性は限界付きで受入済み |

本ファイルをR23の唯一の現行索引とする。R24と統合した現行設計は[現行研究設計](CURRENT_RESEARCH_DESIGN.md)で管理する。段階計画、次の作業、研究画面からは、R23についてのみ本書を参照する。科学的定義は正本仕様に保持し、過去の文書で現在の状態を上書きしない。

<a id="final-scientific-evidence"></a>

## 最終的な科学的根拠

厳密な最適経路の復元は**3/3**。最適化処理が成功を報告したのは**2/3**。順位01は`success=false`、`nfev=300`で、目的関数の評価回数上限に達した。これらは異なる結果として区別する。

現在の再現性の正本は、来歴が完全な実行である。過去の順位02・03の来歴は強い推定のままで、書き換えていない。参照先： [来歴が明確な実行の結果](../../reproducibility/archive/traffic_simulation/r23/provenance/r23_n5_provenance_clean_run_and_formal_benchmark/20260913_v1/CLEAN_RUN_RESULTS.md)、[起動時の記録一覧](../../reproducibility/archive/traffic_simulation/r23/provenance/r23_n5_provenance_clean_run_and_formal_benchmark/20260913_v1/CLEAN_RUN_MANIFEST.json)、[厳密参照解の検証](../../reproducibility/archive/traffic_simulation/r23/provenance/r23_n5_provenance_clean_run_and_formal_benchmark/20260913_v1/EXACT_REFERENCE_VALIDATION.md),と[実行の原記録](../../reproducibility/archive/traffic_simulation/r23/provenance/r23_n5_provenance_clean_run_and_formal_benchmark/20260913_v1/clean_runs/).

<a id="formal-implementation-benchmark"></a>

## 正式実装の性能評価

顧客数5・順位01の固定した目的関数評価負荷を対象とし、出力の同等性は合格。

| 評価指標 | 基準方式 | 第4版 | 観測された基準方式／第4版の比率 |
|---|---:|---:|---:|
| 実行時間 | 1106.778772 秒 | 21.575394 秒 | 51.2982倍 |
| 処理の最大実メモリー使用量 | 211,405,768 キビバイト | 675,432 キビバイト | 312.9934倍 |

**単一の処理負荷で、各実装につき有効な実行は1回。** 負荷条件と反復回数の限界は残る。一般的な規模拡大への適用可能性や実行時間保証を示すものではなく、量子実機と古典実機を比較したものでもない。 [測定値と固定済み手順](../../reproducibility/archive/traffic_simulation/r23/audits/r23_n5_full_formal_benchmark_and_closure_review/20260913_v1/README.md).

<a id="remaining-limitations-and-closure"></a>

## 残る限界と完了判定

| 限界 | 重大度 | 保持済みの根拠 |
|---|---|---|
| B2のハッシュ値不一致6件。派生成果物の不一致であり、科学的数値への影響は確認されていない | 中程度 | [B2の評価](../../reproducibility/archive/traffic_simulation/r23/audits/r23_n5_full_formal_benchmark_and_closure_review/20260913_v1/B2_SHA_CLOSURE_ASSESSMENT.md)、[不一致一覧](../../reproducibility/archive/traffic_simulation/r23/intermediate/r23_repository_rebaseline/20260913_v2/b2_sha_impact_assessment.json) |
| 顧客数5での反復回数が1回であることとシステム負荷 | 中程度 | [性能評価条件](../../reproducibility/archive/traffic_simulation/r23/audits/r23_n5_full_formal_benchmark_and_closure_review/20260913_v1/SYSTEM_CONDITIONS.md) |
| 過去の来歴と小規模問題の選定 | 限界を記録済み。最終再評価を参照 | [確認事項の再評価](../../reproducibility/archive/traffic_simulation/r23/audits/r23_n5_full_formal_benchmark_and_closure_review/20260913_v1/FINDINGS_REASSESSMENT.md) |

[受理済みの正式完了判定](../../reproducibility/outputs/traffic_simulation/r23_formal_closure/20260913_v1/R23_FORMAL_CLOSURE.md)と[元の限界登録簿](../../reproducibility/outputs/traffic_simulation/r23_formal_closure/20260913_v1/R23_LIMITATIONS_REGISTER.md) は元のバイト列を保持している。科学的根拠の独立再現、完全な実行来歴、経路と最適化処理の正しい意味付け、未解決の重大・主要課題が0件であることに基づき、進行を妨げない限界を記録して完了とする。

<a id="authority-paths"></a>

## 正本の参照先

- [経路計算の基準の正本仕様](specifications/ROUTING_BASELINE_CANONICAL.md)
- [R23の正本仕様](specifications/R23_REDUCED_PROBLEM_CANONICAL.md)
- [段階計画](R23_ROADMAP.md)と[次の作業](R23_NEXT_STEPS.md)
- [保管先の最上位と移動対応表](../../reproducibility/archive/traffic_simulation/r23/README.md)

保管記録の本文には元の保存先とハッシュ値を保持する。旧保存先の解決には`ARCHIVE_MANIFEST.csv`または`resolve_archived_path.py`を使う。廃止済み出力領域に対して過去の生成器を実行してはならない。
