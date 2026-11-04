# 入力・実装監査

事前固定 `FROZEN_PROTOCOL.json` と旧4レビューを継承。旧成果1047ファイルをmanifest SHAで照合した。既存OD、計画、政策、seed、FREEZEの変更なし。今回の依頼による全件算術実行は、旧タスク固有の全件禁止表記を歴史記録として保持したうえで実行した。

## 元データと生成経路

|対象|実入力・実装|出力・行数|
|---|---|---|
|A|旧78NPZ、古典/QAOA原JSON、D10/D11 operations_2808。新run_a.py|政策2,808、古典対照2,808、成功64の機構4arm9,216、task59,328|
|B|現行R0…R5 460NPZ、3family raw JSON・8設定、SeedSequence対応台帳。新run_b.py|36,800参照、3680 fit資源、407/53の460参照台帳|
|C T08|SCENARIOS、MATERIAL_ENERGY、旧trajectory manifestsとgzip速度。凍結evaluate|4,464全行、744 dataset/method軌跡参照、465固有速度ファイル|
|C T09|PACK_20KWH_SENSITIVITY、T09_MASS_BOUNDARIES|183行、完成mass NULL183、対向FAIL1|
|C bridge|DC_MASS_RESPONSE、固定旧460速度|25,760全行、1200/1400kgの既存感度probe|

主要起点：

- `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/cpx01_d11_validation_20261017/operations_2808.csv` — SHA256 `4a94031198e15cf0f734aef08384cdd0efffc2f6f2d188d1896525333e4dee98`
- `/home/takuma/kmd-analysis/review_outputs/integrated_causal_audit_20261102/run01/B_PLAN_REFERENCES.csv` — SHA256 `556cf3187be2d9aba42bc2410bb74a79d3d830c901d45e7754ee09e712c89145`
- `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/staged_qaoa_validation_20261102/mirror_family/MANIFEST.json` — SHA256 `0e07e9ea0d18fdcf40e6e5caebb5669fd24c0dfcfd5589f7312c7e7a7a330750`
- `/home/takuma/kmd-analysis/01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json` — SHA256 `b37fd532a5a7daf84f07924d954d6f8e2584f51d218506eeb14e70c53538cf78`
- `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/material_ev_stage2_20261026/run02/SCENARIOS.json` — SHA256 `4ad97ae1b4dff3dab504a46d4c7b649d92aa6ecfdac8389030b94ce67ef11f98`
- `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/t09_open_data_model_20261029/run01/PACK_20KWH_SENSITIVITY.csv` — SHA256 `06a186109443351acbcbafccc7d82d6f28ae282760267fdfdddadbd3c1c05702`
- `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/t08_t09_conditional_bridge_20261030/run01/DC_MASS_RESPONSE.csv` — SHA256 `e59287f730cca43ed2b82e408588dce2d94681b33339b1a0cefb887898b2b2de`

`SOURCE_AND_OUTPUT_HASHES.csv` は実パス・role・SHA・所在を保存。外部Uの未追跡コピーとB/Lの保全資料は公開Git収録扱いにしない。`INPUT_LEDGER.csv` と `PARENT_GROUP_MAPPING.csv` は78/460物理入力と26親→25元需要groupを保持。原入力を再生成していない。

## 指標・単位・欠測

Aは秒、需要PE、率fraction、差ppを別列。完了期限due_start+102、デポdue32400を独立に扱う。Bのobjective_fractionは原有理数、OD_time_sはNPZ脚和。両者のserialization照合許容1e-7秒を、最適値一致の許容には使わない。最適値一致は原有理数で厳密比較する。距離はOD mでnative走行距離ではない。

Bの厳密参照407、未確定53は前回と一致。53入力×8×10=4,240参照はgap/最適一致nullで保持する。全460で評価する取得・初期解差等と分母を分けた。hardware qubit・compiled depth/gates、未保存CPU/RSSは推定で埋めずreasonを付す。原CSVのgap未保存と参照値不存在も区別する。

Cはkg・Wh・%と原設計条件単位を保持。主材料比較のgross20kWh／usable18kWh、T08とT09会計差、Crr両境界、unknown BOMを継承。Cのinput_sha256は速度hashまたは材料CSVのhash、集計行は入力ledger／元結果表hashである。`input_sha_scope` を見て物理入力SHAと区別する。

全CSVの実row数、列、NULL、PKは `DATA_SCHEMA_AUDIT.json`。task PKはscope/condition/problem/arm/task、Bはproblem/config/measurement_rep。親・rep・条件を独立問題として増やさない。保存結果・モデル派生・実世界未検証を別状態で記録する。

## 独立実装

primary AはDecimal逐次、独立AはFraction max-plus。primary Bはraw有理数＋NPZ脚和、独立Bはfsumの別手順と参照分母。primary Cは元の凍結kernelを呼び出し、独立Cはmass線形係数を使った別vector式と部材Fraction式。primary関数を検証コードからimportしていない。主出力14CSVは全件再実行してbyte SHA一致を確認した。
