# SUMOなし代替分析の入力監査 — 2026-11-02

本作業は道路修復を停止し、保存計画・固定OD・材料会計を用いる分析の仕様を確定する。新しい地域SUMO、道路診断・修正、経路再探索、QAOA、A/B全件評価、論文編集は実施していない。行集計は保存値の欠測・選択バイアス確認であり、新しい全件配送成果・電力量の計算ではない。

## 保存版と所在

HEADは `1b00bd7927fa1e7688e4772ac1da9db46d9bac11`。作業開始時tracked差分0。旧3レビューの成果物968件を各manifestから再ハッシュし、不一致0。レビューMD20件、D10、D03読取元、D11／B生成コードを実際に読んだ。最終状態は `PRESERVATION_FINAL.json`、全参照SHAは `SOURCE_INVENTORY.csv`、成果物SHAは `ARTIFACT_MANIFEST.json`。

R=`/home/takuma/kmd-analysis` は現作業木、U=`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked` は外部未追跡保全、B=`/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup`／L=`/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/relocated` は外部バックアップ／移設領域。外部資料を公開Git収録扱いにしない。公開Git単独で全入力が再生成できるとの主張は不可。

## 採用入力と生成経路

|系列|入力・生成経路|今回の検査|
|---|---|---|
|A|旧78NPZ→古典／QAOA原JSON→D10政策→D11 operations_2808→前回303政策＋15機構候補|全78入力hash・4需要・102秒・有限OD、取得64／未取得14。新規時刻計算は10経路40taskのみ|
|B|現行no-window460NPZ→staged 3family/8設定ALL_SEEDS・raw records→初回B_PLAN_REFERENCES→前回B_PLAN_RECOVERY_LINKS|36,800参照・4,987候補の保存値と分類を結合。新規cost検算18経路、極小3入力の参照最適値検算|
|C|T08 SCENARIOS→部材・MATERIAL_ENERGY、T09 PACK_20KWH_SENSITIVITY→bridge|T08式、保存460軌跡の加重率、T09代表4行、bridge6行を独立算術で照合|
|道路|N0／rollback／LHT／B2…B6／guard／downstreamの保存版・generation・acceptance|14ファイル12異なるSHA、履歴104資料を読取り。新規診断0|

主要入力：

- `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/docs/research/CPX01_D10_ADOPTION_DECISION_20261017.md` / SHA256 `87731d8c211fcc0968a58198cd28447f011be1376fec32d3edf79a6268769ea2`
- `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/cpx01_d11_validation_20261017/operations_2808.csv` / SHA256 `4a94031198e15cf0f734aef08384cdd0efffc2f6f2d188d1896525333e4dee98`
- `/home/takuma/kmd-analysis/review_outputs/integrated_causal_audit_20261102/run01/B_PLAN_REFERENCES.csv` / SHA256 `556cf3187be2d9aba42bc2410bb74a79d3d830c901d45e7754ee09e712c89145`
- `/home/takuma/kmd-analysis/review_outputs/network_route_contract_20261102/run01/B_PLAN_RECOVERY_LINKS.csv` / SHA256 `b768ce388e70e060f541028019b8f22c23cdd9c233a3ba73fbaa39a41dd0f7f9`
- `/home/takuma/kmd-analysis/01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json` / SHA256 `b37fd532a5a7daf84f07924d954d6f8e2584f51d218506eeb14e70c53538cf78`
- `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/material_ev_stage2_20261026/run02/SCENARIOS.json` / SHA256 `4ad97ae1b4dff3dab504a46d4c7b649d92aa6ecfdac8389030b94ce67ef11f98`
- `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/t09_open_data_model_20261029/run01/PACK_20KWH_SENSITIVITY.csv` / SHA256 `06a186109443351acbcbafccc7d82d6f28ae282760267fdfdddadbd3c1c05702`

## 構造・欠測と監査差異

`*_SCHEMAS.json` にrow数、列、NULL、指定PKの重複を保存。Aの入力不足なしは固定ODの代数計算に関する判定で、地域道路・配送成功の受入ではない。BではPK=(family,config,problem,rep)、Aは(policy,PID)。系列間でPIDや件数だけの結合をしない。

旧報告のB回復2,323＋旧cache2＋partial2,662、受入走行0、道路N0 gap563,513・N1保存collision183を保持。今回、厳密参照最適値の**407入力／欠測53入力（R4=21、R5=32欠測）**を明示した。これは旧資料の値を置換したのではなく、最適性評価の適用分母を特定したもの。保存gap欄の欠測8,310は、53入力×7設定×10=3,710と、active系列の列未保存4,600による。activeのうち407入力は今後値から導出可能だが、今回は全件補完していない。

初回B監査コードがexact値を全件で仮定してNULLで停止した。旧コード・ログを `revisions/` に保存し、欠測保持へ修正後に再検証した。科学データの矛盾ではなく監査コードの仮定誤りで、53欠測を除外・ゼロ化していない。

## 独立性と限界

AはFraction逐次式と別のmax-plus閉形式、保存OD再生CSVを照合。Bはraw JSON・NPZから18costを別算術で再計算し、R0/R1/R2各1入力では計150順列を軽量列挙して最適値一致を確認。407件の大規模証明全体を再実行したわけではない。Cは別Fraction式から代表部材と保存値の差・集計を確認した。

材料文献の保存PDF `SOURCES/chen2020.pdf` はpdftotextで新領域へ抽出し、保持試験とVASP記載を確認 (`C_LITERATURE_LOCATORS.json`)。単位Ah/kgとmAh/gは数値同一。既存入力を物性の対象車・完成pack適合へ昇格しない。

PASS＝指定された内部照合が成立、CONDITIONAL＝固定OD・質量・軌跡等の仮定、HOLD＝入力／適用証拠不足、FAIL＝既存不適合を保持。証拠分類OBSERVED等は判定とは別軸である。
