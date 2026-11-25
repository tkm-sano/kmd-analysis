# 統計解析範囲の正式Freeze・MDE廃止・J評価方針更新

**統計解析範囲はFROZEN。MDE・検定・検出力設計はSUPERSEDED。正式Jと本実験全体はHOLD。** ユーザー指定のRQと最終Freeze文言を[FREEZE_SPEC.md](FREEZE_SPEC.md)にそのまま記録し、固定SHA-256で保護した。最適化・需要・運行・量子設定は変更せず、本実験を実行していない。

## 依頼への回答

| 項目 | 決定・実装・検証 |
|---|---|
| 1. 今回FREEZEした事項 | D［km］・総積込W［分］の絶対値・ばらつき・改善量/率・両立改善。S1〜S3別、A対B/C/D・B対D・C対Dの5組。J、平均、標本SD(ddof=1)、中央値、Q1/Q3/IQR、最小最大。Tukey箱ひげ・平均±1SD。Aは整合性確認済みの参照点/線。 |
| 2. SUPERSEDED | MDE、MDE必要数、α=.05の仮説検定設計、80%検出力、Cohen's d等の検出力標本数、主要6検定、Holm、仮説検定・有意性判定。SEM/95%CIの主要結果バーも不採用。旧計算・入力・結果・文書は削除/書換なし。[変更台帳](TRANSITIONS.json)。 |
| 3. HOLD | 正式な独立外側J、MCSE許容値、J選定の資源上限、SESOIの数値根拠、失敗/欠測の推定対象、現行の有効反復・対応設計、Aの各指標の比較整合性、本実験全体。暫定J30は採用しない。 |
| 4. MCSE導入 | 独立外側単位でs/√J、対応差は差のSD/√J。独立2群の平均差はsqrt(sX²/JX+sY²/JY)。根拠不明・J<2ならnull。内部prefix・資源・失敗欠測資料へ分離し、主要バーに使用しない。 |
| 5. 学術的根拠 | [文献確認表](LITERATURE.md)と[参照URL・確認範囲](SOURCES.json)。Cumming: SD/SEの役割、Bartz-Beielstein: 最適化の記述統計、Krzywinski/Altman・NIST: 箱とIQR、Morris: MC誤差と反復数設計。文献の一般事項と今回の研究判断を区別。指定Springer書誌とNature全文直接取得の未確認を明記。 |
| 6. 変更ファイル | 下表。既存案内7件に現行方針を追記し、旧本文全体を保持。既存CLI1件に新統計への分岐を追加。新規設定・パッケージ・CLI・テスト・文書・CI整合検査を追加。 |
| 7. テスト | 新規35 PASS、関連回帰114 PASS、旧時点案内hash固定の1件は今回の承認更新と衝突するため対象外。新しい開始時点の223保護ファイルと旧source pin26件はすべて一致。合成データで主要8図×PNG/PDF、内部4図×PNG/PDFを生成。 |
| 8. 正式Jへの残作業 | 外側単位と変動対象を明記し、現行条件の適格な予備試行を取得。対応/独立2群/C参照を事前登録し、失敗欠測の扱いを確定。精度と費用を検討後、Jの選定前にMCSE許容精度・資源制約を固定し、安定性・改善SD/MCSE・費用を評価してJを別途Freeze。p値/検出力で調整しない。 |

## 実装と適用範囲

| ファイル | 変更理由 |
|---|---|
| `configs/statistical_scope_20261121_v1/policy.json` | 新版FROZEN設定。MDE等SUPERSEDED、J/精度基準/SESOIはnull/HOLD。ユーザー指定RQと文言を保存。 |
| `src/kmd_toc/descriptive_v1/statistics.py` | 記述統計、type 7四分位、Tukey、直接差、改善率、C基準I_dual、MCSE。欠測0補完・検定なし。 |
| `src/kmd_toc/descriptive_v1/analysis.py` | 規模別・方式別集計、5比較、A整合性ゲート、外側/内部/再試行の分離、根拠付きの対応のみ。 |
| `src/kmd_toc/descriptive_v1/inputs.py` | 保存計画・入力・証跡SHAと条件版を確認し、既存評価器でD/Wを読み取り専用再計算。旧版/勤務版を混在させない。 |
| `src/kmd_toc/descriptive_v1/plots.py` | 箱ひげと実観測点、平均±SD、A参照線。MCSEはinternal/の別図。 |
| `src/kmd_toc/descriptive_v1/pipeline.py`, `policy.py`, `__init__.py` | 新規出力だけを許可し、入力・解析コードhash/環境、CSV/JSON、内部J資料を保存。固定policy/specの改変を拒否。 |
| `scripts/analyze_descriptive_v1.py`, `scripts/analyze_dw.py` | 現行統計CLIを追加。後者への今回差分は新統計分岐6行のみ。通常FCFS評価・明示履歴解析は維持。 |
| `scripts/statistical_scope_20261121_v1/audit_and_demo.py` | 既存適格性資料の読み取り専用監査と、明示的合成算術fixtureによる図表検証。 |
| `scripts/statistical_scope_20261121_v1/finalize_audit.py` | 作業前後の差分、保護hash、HEAD、案内原文、旧source pinを確認・記録。 |
| `scripts/verify_statistical_scope_v1.py`, `.github/workflows/statistical-scope-v1.yml` | 固定hashによる統計仕様・設定の整合検査。CIはローカル検証のみ。リモート実行していない。 |
| `tests/descriptive_v1/test_statistics.py`, `test_figures.py` | 定義・境界値・不正な対応の拒否・保存計画再評価・版混在拒否・実SDバー・保全等35件。 |
| `AGENTS.md`, `README.md`, `DWT_STATISTICAL_PROTOCOL.md`, `DWT_SAMPLE_SIZE_PIPELINE.md`, `DWT_7_FIGURES_SPEC.md`, `DW_RESEARCH_POLICY.md`, `REPRODUCE.md` | 現行統計案内を先頭に追加。後半の旧本文を履歴として保持。変更前の全内容をbefore/へ保存。 |
| 本ディレクトリの文書・台帳 | 正式仕様、根拠、変更履歴、実行・テスト・保全・Freeze seal。過去のdated報告を上書きしない。 |

## 既存資料の適格性監査

正本1〜7、FCFS、最終I_dual選択、勤務版、README/AGENTS、旧統計プロトコル・標本設計、旧MDE/統計予備出力・コード、n/K/RのALL54/REPORT/VERIFICATION、POSTPROCESS_SOURCE_HASHESを確認した。対象の正本・履歴パスは見つかっており、移設していない。主な矛盾は旧検定/Holm/検出力/J30案、旧SEM/CI図表、旧平均W・旧RQの現行への混入である。対応は新仕様への優先順位とSUPERSEDED台帳で明示し、過去記録を改変していない。

最新の読み取り専用監査は `output/statistical_scope_20261121_v1/verified_v4/current_audit/`。今回確認した保存資料から現行のJ評価に採用できる外側反復は**0件**。リポジトリ外を含む全記録に試行が存在しないという断定ではない。

| 保存資料 | 件数・意味 | 今回の扱い |
|---|---|---|
| `stat_conditions_pilot_20261120_v2/OBSERVATIONS.json` | C15件・D15件、各規模5件の旧実行。既存適格性監査は全30件False、CURRENT表のC/Dは各0。 | 旧FCFS不適合、Dの旧shots/旧構成などが残る。最終選択実装が追加されても過去計画の適格性は回復しない。旧監査は根拠付き履歴として引用。 |
| `nkr_p2_20261120_v1/ALL54.csv` | 54条件表の6条件完了。4内部枝の記述平均・旧W。 | 6独立外側試行へ読み替えない。現行最終実計画の反復分布へ流用しない。54条件の再実行なし。 |
| `duty_break_20261121_v1/replay_verified_v2` | B/C/旧Dの固定経路9件のモデル可行性再生。 | 新たな確率的外側試行ではない。実停車可能性は未確認。新しいDの性能反復と混同しない。 |

現行監査出力は18統計セルで有効J=0、5比較×3規模×2指標=30スロットを維持するが性能値は空。AもP/U・荷待ち範囲等の整合が未承認で比較HOLD。架空のA分布・SD・便数換算を作っていない。

## 計算・図表検証と限界

合成算術fixtureは `output/statistical_scope_20261121_v1/verified_v4/synthetic_fixture/`。3規模×3方式×6行の54行であって、54条件の配送実験ではない。値・合成設計証跡をコードで明示し、全図に `STATISTICS FIXTURE ONLY - NOT DELIVERY RESULTS` を表示した。このfixtureの独立性・対応宣言を実データの証拠として用いない。

既知値[1,2,3]の平均2・標本SD1・MCSE1/√3、ゼロ/1標本、観測SD0、四分位補間・境界・外れ値、対応差SD、独立2群MCSE、I_dualの正負/ゼロ分母/厳密両立割合、A監査・参照差、seedのみの対応拒否、完全RNG重複時MCSE抑止、内部枝/再試行/欠測分離、保存FCFS/勤務版計画の再評価、版混在拒否を検証した。

Matplotlibの実際のerrorbar引数を検査し、yerr=標本SD、上下端=平均±SD、MCSE不使用を確認。箱は同じ定義のQ1/Q3/中央値/ひげ/外れ値を使用し、ノッチCIなし。D平均±SDとI_dual箱を目視確認した。統計処理のテスト成功は、配送手法の優位・独立外側試行の十分性・新条件の実運行可行性を示さない。

初期テストのPYTHONPATH未設定による収集失敗、CLI表示にHOLD状態が含まれない1件を修正し、最終35件PASSを保存した。数式を変えてテストに合わせてはいない。旧時点の案内hash固定テスト1件は履歴を維持したまま除外理由を記録し、新しい開始時点の保全テストと監査で代替した。

## Jを確定する最小の次工程

1. 現行のD入口・n/K/R/停止条件・共通計時等、既存HOLDを別作業で解決する。今回の統計Freezeで採用済みとしない。
2. 1規模1固定問題に対する確率的実行の外側単位、全RNG生成、B-D/C-Dの共有要因と対応表、固定Cなら別途決定論証明を事前登録する。内部4枝を独立数へ入れない。
3. 現行条件の小規模予備反復を別途実施する。登録順で平均・SD・分布・改善量・I_dual・MCSE・資源・失敗欠測を確認する。今回その反復を開始していない。
4. 予備精度と費用を検討し、正式Jの選定前に許容精度・資源制約・不可行/欠損の扱いを固定する。外部根拠のないSESOIを導入しない。
5. 規模別に判断根拠を保存し、正式Jを別途承認・Freezeする。本実験全体はそれまでHOLD。

再現手順は[INPUT_AND_REPRODUCE.md](INPUT_AND_REPRODUCE.md)、hash・差分・環境とテストは[VERIFICATION.md](VERIFICATION.md)、正式Freeze証跡は[FREEZE_SEAL.json](FREEZE_SEAL.json)。
