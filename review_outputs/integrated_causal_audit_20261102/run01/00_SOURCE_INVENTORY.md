# 証拠所在・採用版台帳 — 2026-11-02

開始時HEAD：`1b00bd7927fa1e7688e4772ac1da9db46d9bac11`。開始時tracked差分なし。既存未追跡は`docs/research/THESIS_REVISION_AUDIT.md`と`tmp_RsrchMstrDc_1026_revised.docx`の2件で、今回変更していない。新しい成果物は本run01だけ。commit/pushなし。

## 所在と正式版の判断

R=`/home/takuma/kmd-analysis`、U=`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked`、B=`/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup`、L=`同保全親/relocated`。U/L/Bは公開リポジトリの同梱資料ではない。作業木内の実在もGit追跡とは別であり、COMBINED_SOURCE_INVENTORY.csvのin_current_HEADで区別する。元SOURCE_FILES.csvのGIT_TREEは物理的な作業木所在を指し、公開追跡を意味しない。

採用はmtimeではなく採用決定・freeze・入力hash・source/設定・保存結果の連鎖で判断した。未追跡THESIS_REVISION_AUDITは探索の案内としてのみ利用し、その報告値を独立検算の正解にしなかった。新研究資料の公開・移動・復元はしていない。

|系列|採用資料と版|選定理由・非採用との区別|
|---|---|---|
|A|D10 ADOPTION_DECISION（2026-10-17）→D11 operations/候補→原R1 full_v2/古典JSON。後続RD/Q採用記録とD13 native監査も照合|PROVISIONALより正式ADOPTEDが優先。36条件は探索的仮想政策。D13成功を実配送受入に拡張しない|
|B|UNIFIED_NO_CUSTOMER_WINDOWS_V1 R0〜R5入力→staged 20261102の3familyのCONFIGURATION_FROZEN/PROTOCOL/SOURCE_SNAPSHOTと各run|8最適化設定36,800参照の範囲を採用。旧窓あり460、UNIFIED全R0〜R8の548、旧MAIN20310行、11月1日追加群を別系列に保持|
|C|T08 stage2 20261026/run02 SCENARIOS/source/energy、T09 20261029/run01部材/設定、bridge 20261030/run01|T08=簡略閉会計、T09=既知部材+未知。bridgeは条件付き質量差/軌跡感度。旧B0/B1/B2は材料主入力としない|
|道路|integrated_research_results_20261028/run02/ROAD_NETWORK_CLOSUREと元audit|修正候補不採用・追加開発打切り。最終静的PASSだけで動的受入を宣言しない|

## 主要採用資料の実ファイルSHA256

|実パス|SHA256|HEAD追跡|
|---|---|---|
|`/home/takuma/kmd-analysis/README.md`|`3c2bebd3ed15eb8a00446a0911a68e81a2a27996ed7b7eec8be3c5485260c1b4`|True|
|`/home/takuma/kmd-analysis/docs/QUANTITATIVE_GUIDE.md`|`9f011dcd1a03f0520d5257992d17434b1a456a32eb6de58c1cde7b33306dbdeb`|True|
|`/home/takuma/kmd-analysis/01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json`|`4768a0c09967a8ddf73d750d4894fc6e551c23b4e6ecd672f3af7b5b8fb5b51a`|True|
|`/home/takuma/kmd-analysis/01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json`|`b37fd532a5a7daf84f07924d954d6f8e2584f51d218506eeb14e70c53538cf78`|True|
|`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/docs/research/CPX01_D10_ADOPTION_DECISION_20261017.md`|`87731d8c211fcc0968a58198cd28447f011be1376fec32d3edf79a6268769ea2`|False|
|`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/cpx01_d11_validation_20261017/MANIFEST.json`|`b2e12226adfa1bded3d7003cb27173b7c191c2e94b14384b50086e584721f436`|False|
|`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/unified_no_windows_r0_r8_20261022/FREEZE.json`|`b0e7a5d77eb94edb1de1e6d558074ee582bf21644dfa60a1c95a4fe36261caf0`|False|
|`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/r0_r8_main_results_20261023/FREEZE.json`|`850fa763e2a0a5f506ee7c3c1dde42bedd4942c86dea9445c46cbab543fe83d6`|False|
|`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/staged_qaoa_validation_20261102/mirror_family/CONFIGURATION_FROZEN.json`|`dbc6bac9bcd5231d5ec4e42a274eecd071409b2f184eef92eaccf90677979a1d`|False|
|`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/staged_qaoa_validation_20261102/grover_depth/CONFIGURATION_FROZEN.json`|`223a539d812bdd82e03ba99fdf9ef9bd10a25ae1da469d820fe5ba98d6a3184b`|False|
|`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/staged_qaoa_validation_20261102/active_adjacent_p3/CONFIGURATION_FROZEN.json`|`d310d68ca380d515a0b7341bcbb5e85038297fccb2f88c100cf6bca766bbd75a`|False|
|`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/material_ev_stage2_20261026/run02/SCENARIOS.json`|`4ad97ae1b4dff3dab504a46d4c7b649d92aa6ecfdac8389030b94ce67ef11f98`|False|
|`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/t09_open_data_model_20261029/run01/RUN_CONFIG.json`|`2529e15e1dc69ca53798a123c1543b09161f8b1b3840c29d41f8fb0fe6c9f0f6`|False|
|`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/t08_t09_conditional_bridge_20261030/run01/INPUTS.json`|`ef7db7bcc7d4190617913b6473782c5740658771b86f7c2a58af50c2b11b3f3d`|False|

全入力・個別結果・sourceのhashはCOMBINED_SOURCE_INVENTORY.csvを参照。B_PLAN_REFERENCES.csvは各36,800参照に原JSON path/hashを保存。CSV全列・型・null・範囲はCSV_SCHEMA_AUDIT.json、検算はCHECKS/SUPPLEMENT_CHECKS、版差はB_SOURCE_BINDING_GAPSに保存。

## 調査範囲と証拠区分

README、QUANTITATIVE_GUIDE、docs/research、01_research_design、configs/CANONICAL_CONFIG_INDEX、src、scripts、review_outputs、reproducibility/release・環境記録を調査。旧計算時sourceは公開aliasではなくfreezeと当時snapshotを優先。材料文献は保存Chen本文・来歴・設定記録を読んだ。今回は新規web文献探索や文献値の外部再測定を行っていない。

過去独立記録（D11、causal_engineering_audit、native各phase、T09/bridge verification、道路CLOSURE）は既存証拠として保管し、今回の別コード検算とは区別した。ディレクトリ全ファイルの網羅的科学監査や全archive全byte照合を主張しない。

## 新成果物と再実行入口

6文書は00所在、01監査、02仕様、03実装/試行、04再現性不足、05判断。本領域内の補助CSV/JSON/コードは独立監査の追跡用。大規模実験は含まない。

軽量監査の再実行（必要な外部資料が同じ場所にありnumpyを利用できる場合）：

```bash
python -B review_outputs/integrated_causal_audit_20261102/run01/independent_audit.py
python -B review_outputs/integrated_causal_audit_20261102/run01/supplement_audit.py
python -B review_outputs/integrated_causal_audit_20261102/run01/finalize_review.py
```

これらは本レビューの生成物を更新する。凍結して保管する場合は新しいレビューコピーで実行する。科学runner再生成の代替ではない。

最終保全照合：参照入力8,383ファイル、読取り時hashからの変更0。今回実施したsubsetの保全であり全研究領域の完全保全ではない。新出力のhashはREVIEW_ARTIFACT_MANIFEST.json。
