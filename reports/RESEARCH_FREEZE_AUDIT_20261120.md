| 対象 | 判定 | 差異件数 | 最大影響度 |
|---|---|---:|---|
|1. 総走行距離|MATCH|0|—|
|2. 積込待機時間|MISMATCH|1|HIGH|
|3. 両立度|UNIMPLEMENTED|1|—|
|4. 研究仮説|MISMATCH|4|HIGH|
|5. ベースラインA|MISMATCH|3|LOW|
|6. ターミナル実績|MATCH|0|—|
|7. 共通実験条件|MISMATCH|7|HIGH|
|B・C・Qの比較条件|MISMATCH|6|HIGH|

# 研究仕様v1の凍結・整合性監査（2026-11-20）

**凍結PASS／監査完了（未確認を開示）／実装適合HOLD。** 差異件数は各対象に関連する差異IDの重複なし件数であり、行間では重複する。最大影響度はMISMATCHのみ。UNIMPLEMENTED/UNKNOWNは別途優先度を付す。

唯一の正本は[docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md](../docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md)。本文をUTF-8・LF・末尾改行で保存した結果、ユーザー指定の原本SHA-256 `297be6f6be2be000e627480af189bad1533a385bf269b25fc22dc4922b3de9be` と完全一致（15,688 bytes）。数式・数値・単位・暫定表記・URL・留保を一切変更せず配置した。元の添付ファイルは取得できなかったが、ユーザー返信の本文から同一hashのバイト列を確認できた。
マニフェストは全文content_utf8・固定hash・版v1・凍結日・初回検証結果を保持する。検証PASSは仕様の完全性に限り、実装適合や本実験開始許可ではない。既存仕様・設定は変更していないため旧正本指定との不一致もF09に残す。

## 調査状態と有効経路

作業ディレクトリ `/home/takuma/kmd-analysis`、ブランチ `main`、HEAD `ab79b9ddf52b604d5a162fc66c37b0fc967690d4`。開始時の28件の追跡済み未コミット変更は終了時にも内容hashがすべて一致した（PRESERVATION.json）。未追跡の旧成果も削除・上書きしない。
本依頼の唯一正本指定をAGENTSの旧正本指定より優先する。ただし既存コード・研究設定・プロトコル・READMEは変更しない。今回追加した凍結・検証・監査ファイル以外の改修、commit/push、リモート設定変更、S1〜S3再実行、量子ジョブ送信は行わない。

|入口・設定|実際の用途と上書き|監査対象としての扱い|
|---|---|---|
|scripts/analyze_dw.py:13 → evaluate_cargo_wait_v2.py:20|通常は保存計画のcargo_wait_v2評価。--model/--eventsで記録モデルを指定可能。出力は新規限定|有効な分析入口。新仕様とのW/仮説差を監査|
|cargo_wait_v2.policy:15 → configs/toc_delivery/dw_policy_20261117_v1.json|既定policyは旧平均荷待ちを固定検証。別設定を黙って採択しない|F01/F03/F09|
|common.config:39 → common_conditions_v1_1.json|固定SHA検証。from_frozenは同じ容量/ready/車両/バースを構築|共通物理条件を監査|
|cargo_wait_v2.methods.generate:11|人工12地点以下のみ、内部の旧有限仕事量B/C/Dへ接続|人工検証専用。道路本実験へ拡張しない|
|main_experiment_d.shots.run_main:124|manifest検証後HOLD。p=2/学習1000/最終10000は既存別freeze|正式全体Qは未完成|
|nkr_p2_study.study.load_case:33 / configs/nkr_p2_20261120/protocol.json|道路入力と保存B初期計画を読む局所予備研究。初期B生成時間は含まない|予備経路。正式本実験と区別|
|run_dwt.py:3 / --historical-reproduction|旧時間契約・旧A・旧DWTの履歴再現。--configや登録値を持つ|OUT_OF_SCOPE。定数の存在だけで現行違反としない|
|src/kmd_toc/dw.py:1 / analyze_dw.py:16|旧積込W分析は明示的履歴フラグ時のみ|OUT_OF_SCOPE|
|P1・nkr_study・large_n・shots/p2予備|独立した実装・符号化・計算予算の診断|結果・設定を保持し、現行Qへ無条件昇格しない|

環境変数は旧runnerのnative thread数等に使われるが、現行common.configは物理条件を環境変数から上書きしない。CLIの--model/--eventsは待機評価の対象を変え得るため、v1適合の自動保証にはならない。新正式runnerがないので、将来の実験に適用される実値・override precedenceまで確認済みとはいえない。

## 共通条件・単位・未規定選択

|規模|配送先|車両|バース|最大便数|最大配送先数相当|需要/最大容量|
|---|---:|---:|---:|---:|---:|---:|
|S1|1000|10|2|20|1200|83.333…%|
|S2|2000|20|4|40|2400|83.333…%|
|S3|4000|40|8|80|4800|83.333…%|
根拠：common_conditions_v1_1.json:27,39。1地点1配送単位なので60配送単位/便は現行では「1便当たり最大60配送先」。重量kg・容積・実荷物個数とは校正されていない（COMMON_CONDITIONS_V1.md:87）。原本の容量表記はそのまま凍結する。
積込1800秒、配送作業120秒、準備0秒、08〜20時、顧客時間窓なし、1バース同時1台は一致。容量と時間を別々に検証する。理論上の総容量充足は配送完了の証明ではない。
初便readyは `28800 + floor(3600*(2*v+1)/(2*V))` 秒（v=0,…,V−1）。決定的な等間隔区間中点配置で、確率的一様分布ではない。S1は08:03〜08:57、S2は08:01:30〜08:58:30、S3は08:00:45〜08:59:15。時間帯は一致するが分布形はF10として未規定。新たな仮定を凍結仕様へ追加しない。

## 差異一覧（修正は実施していない）

### F01 主要Wの対象・集約単位が総積込待機ではない

- 仕様節：2, 7.4。判定：**MISMATCH**。MISMATCH影響度：HIGH。対応優先度：HIGH。
- 期待：全活動便のΣ(load_start-ready)/60を主要Wとする。
- 実際：現行policyはmean_cargo_wait_min_per_operationを主要Wとする。評価器は積込・荷卸し・その他を集計し、平均も出す。現行0待機仮定ではloading_W_minとW_total_minは数値一致するが、主要表示は平均。
- 根拠：[configs/toc_delivery/dw_policy_20261117_v1.json:7](../configs/toc_delivery/dw_policy_20261117_v1.json#L7)、[src/kmd_toc/cargo_wait_v2/evaluation.py:140](../src/kmd_toc/cargo_wait_v2/evaluation.py#L140)、[src/kmd_toc/cargo_wait_v2/evaluation.py:192](../src/kmd_toc/cargo_wait_v2/evaluation.py#L192)、[src/kmd_toc/cargo_wait_v2/evaluation.py:205](../src/kmd_toc/cargo_wait_v2/evaluation.py#L205)、[src/kmd_toc/nkr_p2_study/model.py:23](../src/kmd_toc/nkr_p2_study/model.py#L23)
- 有効経路：analyze_dw.py → evaluate_cargo_wait_v2.py → cargo_wait_v2.analysis.write_evaluation。nkr_p2_study.model.relationも平均Wを参照。
- 原因：2026-11-19の車両1日平均荷待ち方針が有効なまま。
- D/W/I_dual/H1への影響：D算定は不変。運行数が異なる計画ではWの順位・改善率・I_dual・H1が変わり得る。固定運行数内の平均差は総和差と比例しても指標の同一性を意味しない。
- 修正対象・方針（別工程）：承認された別工程でpolicy、分析出口、候補管理との対応を改訂し、総積込Wを明示。今回の正本は変更しない。
- 検証方法：活動車両数が異なる2計画で総積込Wと平均Wの順位逆転を検査し、全便の手計算と照合。
- 既存結果への影響：元計画と旧出力を保全し、新評価IDで再集計。旧平均Wを総和Wとして流用しない。

### F02 両立度の本体評価・出力が未実装

- 仕様節：3, 7.4。判定：**UNIMPLEMENTED**。MISMATCH影響度：該当なし。対応優先度：HIGH。
- 期待：Cを基準に100min((D_C-D_Q)/D_C,(W_C-W_Q)/W_C)、分母非正時は未定義と絶対差。
- 実際：現行比較器はD差、総荷待ち差、平均差のみ。I_dualとゼロ分母の統合出力がない。今回の私有テストoracleは本体実装ではない。
- 根拠：[src/kmd_toc/cargo_wait_v2/analysis.py:10](../src/kmd_toc/cargo_wait_v2/analysis.py#L10)、[src/kmd_toc/cargo_wait_v2/analysis.py:25](../src/kmd_toc/cargo_wait_v2/analysis.py#L25)、[src/kmd_toc/cargo_wait_v2/analysis.py:90](../src/kmd_toc/cargo_wait_v2/analysis.py#L90)
- 有効経路：現行分析CLI → compare_methods／write_evaluation
- 原因：旧policyの総合評価J_DWはHOLDで、新たなI_dual契約が未接続。
- D/W/I_dual/H1への影響：I_dualの正負・単位・未定義・H1同時改善を現行結果から正式出力できない。
- 修正対象・方針（別工程）：別工程で共通評価にC/Q比較と絶対差・未定義理由を追加。ソルバー目的関数を自動変更しない。
- 検証方法：正・ゼロ・負・片方不変・各分母0・欠測・入力hash不一致・A混入拒否の契約検証。
- 既存結果への影響：計画生成を変えず新評価出力のみ追加可能。旧成果の表を無断置換しない。

### F03 有効な仮説文・主要比較が旧平均WのB/C比較

- 仕様節：4, 7.4。判定：**MISMATCH**。MISMATCH影響度：HIGH。対応優先度：HIGH。
- 期待：主要比較Q対C、同じ入力・運行制約・計算時間上限でDと総積込Wを両方厳密改善。
- 実際：policyの仮説は従来手法・古典最適化と比較し平均荷待ちを両方削減する旧文。新局所DのACCEPTは一方不変を許すパレート改善でありH1の判定器ではない。
- 根拠：[configs/toc_delivery/dw_policy_20261117_v1.json:5](../configs/toc_delivery/dw_policy_20261117_v1.json#L5)、[src/kmd_toc/cargo_wait_v2/policy.py:10](../src/kmd_toc/cargo_wait_v2/policy.py#L10)、[src/kmd_toc/nkr_p2_study/model.py:22](../src/kmd_toc/nkr_p2_study/model.py#L22)、[docs/research/DW_RESEARCH_POLICY.md:13](../docs/research/DW_RESEARCH_POLICY.md#L13)
- 有効経路：現行policy読み込み／現行評価出力。局所ACCEPTは予備候補管理。
- 原因：2026-11-19の研究方針をコードで固定検証している。
- D/W/I_dual/H1への影響：仮説の対象・W・厳密性が新正本と一致しない。ACCEPT回数をH1成功数とすると誤る。
- 修正対象・方針（別工程）：別工程で新正本に基づく仮説メタデータと個別結果判定を追加。局所ACCEPTと仮説判定を分離。
- 検証方法：Dのみ改善、Wのみ改善、双方改善、不変、相反、ゼロ分母のケースをC/Q対応で検証。
- 既存結果への影響：旧予備実験の成功率・平均W仮説を新H1の結果として転載しない。

### F04 同一時間上限・期限採択の共通実行契約が未実装

- 仕様節：4, 7.4。判定：**UNIMPLEMENTED**。MISMATCH影響度：該当なし。対応優先度：HIGH。
- 期待：B/C/Qの時間上限と計時範囲を揃えTを補助記録。具体値は別途確定可能。
- 実際：現行policyは有限作業量を保持し、分析器はequal_planning_time_comparison_established=Falseを明示。共通予算・計測範囲・期限採択が未登録。
- 根拠：[configs/toc_delivery/dw_policy_20261117_v1.json:38](../configs/toc_delivery/dw_policy_20261117_v1.json#L38)、[src/kmd_toc/cargo_wait_v2/analysis.py:29](../src/kmd_toc/cargo_wait_v2/analysis.py#L29)、[docs/research/DW_RESEARCH_POLICY.md:25](../docs/research/DW_RESEARCH_POLICY.md#L25)
- 有効経路：現行分析／本実験入口。旧時間予算は履歴専用。
- 原因：同一時間の正式契約が未承認・未統合。
- D/W/I_dual/H1への影響：D/Wの記述差は算出できても、同一時間条件のH1を支持できない。
- 修正対象・方針（別工程）：別工程で共通Tと計時・全枝停止・期限可行計画採択を承認し、共通runnerへ統合。
- 検証方法：人工処理遅延と失敗枝を使い、同一開始終了点・期限後候補拒否・全枝資源集計を検証。
- 既存結果への影響：有限仕事量の旧Tを同一時間実験のTへ読み替えず、将来の結果は別ID。

### F05 正式な全体Qランナーが未完成

- 仕様節：4, 7.4。判定：**UNIMPLEMENTED**。MISMATCH影響度：該当なし。対応優先度：HIGH。
- 期待：初期計画取得から最終検証までの全体Qを共通条件で実行できる。
- 実際：run_mainは設定検証後MAIN_EXPERIMENT_HOLDを送出。予備局所Dは保存B計画から開始し、元B生成時間は未測定。
- 根拠：[src/kmd_toc/main_experiment_d/shots.py:124](../src/kmd_toc/main_experiment_d/shots.py#L124)、[src/kmd_toc/nkr_p2_study/study.py:33](../src/kmd_toc/nkr_p2_study/study.py#L33)、[docs/research/nkr_p2_20261120/AUDIT.md:47](../docs/research/nkr_p2_20261120/AUDIT.md#L47)
- 有効経路：main_experiment_dの正式run／nkr_p2_studyの予備比較
- 原因：p・shotsの凍結と全体配送計画runnerの完成は別工程。
- D/W/I_dual/H1への影響：局所改善時間を全体Tと扱えず、S1〜S3の本実験比較は未成立。
- 修正対象・方針（別工程）：別工程で初期計画取得・4枝・全停止・評価の全体Qを実装し、入力と計時をB/Cと接続。
- 検証方法：量子処理を小規模スタブにした全体時間・データ伝播検証後、別承認で実回路確認。
- 既存結果への影響：既存局所実験は診断として保全し、全体Qの本実験へ昇格しない。

### F06 Aの総時間60UとU換算の出力がない

- 仕様節：5.2, 5.4。判定：**UNIMPLEMENTED**。MISMATCH影響度：該当なし。対応優先度：MEDIUM。
- 期待：荷待ち参照総量60Uを、統計の運行と研究便の相違を明示して換算。
- 実際：external_reference(n)は60分/運行を返し、比較は平均W-60。引数U・換算仮定・総分の出力はない。
- 根拠：[src/kmd_toc/cargo_wait_v2/reference.py:7](../src/kmd_toc/cargo_wait_v2/reference.py#L7)、[src/kmd_toc/cargo_wait_v2/reference.py:22](../src/kmd_toc/cargo_wait_v2/reference.py#L22)、[src/kmd_toc/cargo_wait_v2/analysis.py:114](../src/kmd_toc/cargo_wait_v2/analysis.py#L114)
- 有効経路：現行外部参照生成と水準比較
- 原因：旧平均荷待ちモデルに合わせた参照API。
- D/W/I_dual/H1への影響：係数60自体は一致するが、総積込Wとの単位・対象差を無視した差分は不適切。I_dualへAを入れてはいけない。
- 修正対象・方針（別工程）：別工程でUと換算根拠を明示する参照APIを追加し、荷待ち参照と研究積込Wを別欄表示。
- 検証方法：U未指定は未換算、明示Uで60U、研究便数への無条件置換拒否を検証。
- 既存結果への影響：既存の60分/運行を誤値として消さず、旧参照版のまま保存。

### F07 2020年度94Uの補助参照出力がない

- 仕様節：5.3。判定：**UNIMPLEMENTED**。MISMATCH影響度：該当なし。対応優先度：LOW。
- 期待：2020年度94分/運行を2025年度60分と区別し、U換算する補助参照。
- 実際：現行reference.pyは2025年度60のみで、2020年94・年度・n315のメタデータを出力しない。
- 根拠：[src/kmd_toc/cargo_wait_v2/reference.py:1](../src/kmd_toc/cargo_wait_v2/reference.py#L1)、[src/kmd_toc/cargo_wait_v2/reference.py:7](../src/kmd_toc/cargo_wait_v2/reference.py#L7)
- 有効経路：現行外部参照API
- 原因：現行APIの参照範囲が2025年度のみ。
- D/W/I_dual/H1への影響：主比較D/W/I_dualには直接影響しないが補助参照の仕様網羅性が不足。
- 修正対象・方針（別工程）：別工程で年度・統計対象・換算Uを伴う参照欄を追加。感度実験は今回実行しない。
- 検証方法：60と94の年度分離、315を荷待ち発生運行だけの標本と断定しないことを検証。
- 既存結果への影響：旧結果を変更せず参考表の別版を追加。

### F08 A距離参照の出典URLが正本と異なる

- 仕様節：5.1。判定：**MISMATCH**。MISMATCH影響度：LOW。対応優先度：LOW。
- 期待：凍結出典https://www.mlit.go.jp/common/001102289.pdf（2015-08-25、PDF4頁）。
- 実際：DISTANCE_SOURCEはhttps://www.mlit.go.jp/common/001106397.pdf（関連する別の報告書）。係数は同じ0.58。
- 根拠：[src/kmd_toc/cargo_wait_v2/reference.py:2](../src/kmd_toc/cargo_wait_v2/reference.py#L2)、[docs/research/BASELINE_A_DESIGN.md:15](../docs/research/BASELINE_A_DESIGN.md#L15)
- 有効経路：現行external_reference出力の出典メタデータ
- 原因：先行監査が別の国交省報告書を参照している。
- D/W/I_dual/H1への影響：数値D_refの誤りを意味しない。正本に定めた資料・頁との追跡性が不一致。
- 修正対象・方針（別工程）：別工程で正本URLを主要根拠に記載し、旧関連資料の履歴は保持。
- 検証方法：出典URL、頁、0.58、幹線除外の対応を確認。
- 既存結果への影響：数値計画は変わらない。出典メタデータのみ版を区別。

### F09 既存の正本指定・評価方針が新唯一正本へ接続されていない

- 仕様節：記号, 2, 3, 4, 7.4。判定：**MISMATCH**。MISMATCH影響度：HIGH。対応優先度：HIGH。
- 期待：今回の凍結Markdownを研究仕様の唯一の正本とする。
- 実際：AGENTSと旧研究方針はDW_RESEARCH_POLICY.mdと旧policyを正本と記載し、実行時policy validatorは旧平均Wの文言・J_DW HOLDを固定する。
- 根拠：[AGENTS.md:6](../AGENTS.md#L6)、[docs/research/DW_RESEARCH_POLICY.md:19](../docs/research/DW_RESEARCH_POLICY.md#L19)、[src/kmd_toc/cargo_wait_v2/policy.py:15](../src/kmd_toc/cargo_wait_v2/policy.py#L15)
- 有効経路：人の入口文書／現行policy.load_policy。今回の依頼は旧指示に優先するがコードは未修正。
- 原因：今回は旧研究仕様・設定・プロトコルの変更が禁止されているため差異を保全。
- D/W/I_dual/H1への影響：新正本を渡しても現行policyにそのまま適用できない。旧仕様と新仕様を混ぜる危険。
- 修正対象・方針（別工程）：別工程で参照・policyの新バージョンと入口を改訂。README等もその承認工程で対応。
- 検証方法：新正本の固定hashと有効policy・評価メタデータの参照一致を検証。
- 既存結果への影響：旧仕様は履歴へ保存し、旧解析再現のために削除しない。

### F10 初便ready分布形は未規定

- 仕様節：7.2。判定：**UNKNOWN**。MISMATCH影響度：該当なし。対応優先度：MEDIUM。
- 期待：08:00〜09:00に分散。分布形は別途確定。
- 実際：実装は28800+floor(3600(2v+1)/(2V))秒の決定的な等間隔区間中点配置。確率的な一様抽出ではない。
- 根拠：[src/kmd_toc/common/config.py:46](../src/kmd_toc/common/config.py#L46)、[configs/toc_delivery/common_conditions_v1_1.json:38](../configs/toc_delivery/common_conditions_v1_1.json#L38)
- 有効経路：共通入力adapter／固定道路入力
- 原因：正本が分布形を未確定としている。
- D/W/I_dual/H1への影響：初便の競合・W・第2便時刻に影響する。時間帯の範囲は一致。
- 修正対象・方針（別工程）：実装選択として記録し、別途承認時に分布形とseed契約を確定。今回は値を変更しない。
- 検証方法：S1〜S3の実ready列を記録し全値08〜09時内・規則一致を確認。
- 既存結果への影響：変更時は既存需要ID/計画のreadyを上書きせず新条件版に分離。

### F11 統計的支持規則・需要反復・Tの具体値は未確定

- 仕様節：4, 7.4。判定：**UNKNOWN**。MISMATCH影響度：該当なし。対応優先度：HIGH。
- 期待：具体予算・試行数・統計母集団と検定は別途定義。個別H1判定と統計的支持を区別。
- 実際：policy統計支持・反復・精度はnull。旧需要は固定familyでありseed反復を独立需要としない。
- 根拠：[configs/toc_delivery/dw_policy_20261117_v1.json:36](../configs/toc_delivery/dw_policy_20261117_v1.json#L36)、[configs/toc_delivery/dw_policy_20261117_v1.json:51](../configs/toc_delivery/dw_policy_20261117_v1.json#L51)、[README.md:21](../README.md#L21)
- 有効経路：本実験設計（未開始）
- 原因：正本自体が別途確定としている設計事項。
- D/W/I_dual/H1への影響：未確定を実装違反と断定しないが、母集団H1の支持や本実験開始はできない。
- 修正対象・方針（別工程）：承認済み需要規則を保持し、別工程でM/J・精度・同時支持・Tを決定。
- 検証方法：独立需要と同一需要内seed・4枝・shotsを分離した登録と解析契約を検証。
- 既存結果への影響：旧21回案・固定需要75試行を正式な新本実験へ流用しない。

### F12 CP時刻最適化と新局所DのFCFSの位置付けが未規定

- 仕様節：7.4。判定：**UNKNOWN**。MISMATCH影響度：該当なし。対応優先度：HIGH。
- 期待：共通運行制約を適用する一方、方式固有の探索差は許容。正本にはFCFS指定がない。
- 実際：B/C完成器は開始時刻をCP-SATで選択。新局所Dは全便をFCFS再構成する。旧C保存計画にもready順と積込順の逆転がある。
- 根拠：[src/kmd_toc/termination_v1/solvers.py:19](../src/kmd_toc/termination_v1/solvers.py#L19)、[src/kmd_toc/termination_v1/solvers.py:33](../src/kmd_toc/termination_v1/solvers.py#L33)、[src/kmd_toc/d_local_design/completion.py:71](../src/kmd_toc/d_local_design/completion.py#L71)、[output/toc_delivery/non_time_variance_pilot_20261117_v1/runs/S1_C_pilot_r01/plan.json:2255](../output/toc_delivery/non_time_variance_pilot_20261117_v1/runs/S1_C_pilot_r01/plan.json#L2255)、[output/toc_delivery/non_time_variance_pilot_20261117_v1/runs/S1_C_pilot_r01/plan.json:3007](../output/toc_delivery/non_time_variance_pilot_20261117_v1/runs/S1_C_pilot_r01/plan.json#L3007)
- 有効経路：有限仕事量B/C完成器／新局所D候補完成器。どちらも正式な新本実験runnerではない。
- 原因：積込順序をアルゴリズムの探索変数とするか共通運用規則とするか未登録。
- D/W/I_dual/H1への影響：W差の因果解釈と公平性の説明に影響。FCFS相違だけで仕様違反・W改善原因と断定しない。
- 修正対象・方針（別工程）：別工程で位置付けを登録し、必要なら同じ完成規則を用いた比較を設計。今回は実装も規則も変更しない。
- 検証方法：同じ経路の異なる完成器による差を別途検証し、経路改善効果と分離。今回は追加実験なし。
- 既存結果への影響：CP結果は物理的に可行な旧計画として保持し、FCFS計画と同条件であったとは記載しない。

### F13 Qと内部Dの正式な識別対応が未登録

- 仕様節：記号, 7.4。判定：**UNKNOWN**。MISMATCH影響度：該当なし。対応優先度：MEDIUM。
- 期待：研究表記Qがハイブリッド方式を指す。旧Dとの対応を明示し旧結果を混ぜない。
- 実際：現行gatewayはB/C/Dだけを許可し、method_id=Qを拒否。旧マクロD、新局所D、main_experiment_d準備入口が共存。
- 根拠：[src/kmd_toc/cargo_wait_v2/evaluation.py:124](../src/kmd_toc/cargo_wait_v2/evaluation.py#L124)、[src/kmd_toc/cargo_wait_v2/physical.py:60](../src/kmd_toc/cargo_wait_v2/physical.py#L60)、[src/kmd_toc/termination_v1/methods.py:64](../src/kmd_toc/termination_v1/methods.py#L64)、[src/kmd_toc/main_experiment_d/shots.py:124](../src/kmd_toc/main_experiment_d/shots.py#L124)
- 有効経路：現行共通評価gatewayと保存Plan.method_id
- 原因：新仕様の記号Qに対する実験登録alias／実装version mappingがない。
- D/W/I_dual/H1への影響：表記差だけで数値誤りとはいえないが、Qの実装・入力・hashを確定できない。
- 修正対象・方針（別工程）：旧Dを一括renameせず、新実験登録にQ↔内部ID・実装版・hashを明記。
- 検証方法：旧マクロDの結果と新Q結果の混合拒否、Q aliasの共通評価への明示接続。
- 既存結果への影響：旧Dラベルと結果は保存し、再表示する場合も対応表を付す。

## 全項目チェックリスト

各要件の期待・実際・有効経路・根拠は機械可読JSONのaudit_itemsにも保存する。MATCHは追跡した実装・評価経路または資料に対する判定であり、未完成の正式Q本実験の結果を保証しない。

|ID|仕様節|確認項目|判定|実装・根拠|
|---|---|---|---|---|
|D01|1|全車両・全活動便の合計|MATCH|全trip_metricsのdistance_mをmath.fsumして/1000。 src/kmd_toc/cargo_wait_v2/physical.py:38|
|D02|1|デポ発着と配送先間|MATCH|デポを初期点に全visitのOD.legとデポ帰着を再構築。 src/kmd_toc/cargo_wait_v2/physical.py:129; src/kmd_toc/cargo_wait_v2/physical.py:152|
|D03|1|道路ODとkm単位|MATCH|共通有向OSM/OSRM、最速経路の距離mをkmへ変換。 configs/toc_delivery/common_conditions_v1_1.json:68; src/kmd_toc/cargo_wait_v2/physical.py:38|
|D04|1|未使用便・空便|MATCH|使用しない便はPlanに含めず、活動空便はEMPTY_USED_TRIPで拒否。 src/kmd_toc/cargo_wait_v2/physical.py:111; src/kmd_toc/termination_v1/solvers.py:16|
|D05|1|B/C/内部Dの共通D評価|MATCH|同一gateway・OD hash検査。人工同一計画で一致。 src/kmd_toc/cargo_wait_v2/evaluation.py:115; src/kmd_toc/cargo_wait_v2/physical.py:65|
|D06|1|距離集計値の独立検証|MATCH|保存distance_mを信用せずOD各辺から照合。 src/kmd_toc/cargo_wait_v2/physical.py:158|
|W01|2|準備完了から積込開始|MATCH|physical.loading_W_minはΣ(load_start-ready)/60。 src/kmd_toc/cargo_wait_v2/physical.py:39; src/kmd_toc/cargo_wait_v2/physical.py:168|
|W02|2|全実使用便・第1/第2便区別|MATCH|全便を集計しtrip1/trip2内訳も保持。 src/kmd_toc/cargo_wait_v2/physical.py:39|
|W03|2|第2便readyと準備0分|MATCH|previous_return+preparation_s、設定0。 src/kmd_toc/cargo_wait_v2/physical.py:104; configs/toc_delivery/common_conditions_v1_1.json:33|
|W04|2|バース排他|MATCH|半開区間で同じバースの重複と施設総同時台数を拒否。 src/kmd_toc/cargo_wait_v2/physical.py:174|
|W05|2|荷役時間との分離|MATCH|開始までを計測し、積込1800秒・作業120秒を加えない。 src/kmd_toc/cargo_wait_v2/evaluation.py:140; src/kmd_toc/cargo_wait_v2/physical.py:117|
|W06|2|行政60分の混入防止|MATCH|evaluateは参照係数を使用せずreferenceは別出力。 src/kmd_toc/cargo_wait_v2/evaluation.py:115; src/kmd_toc/cargo_wait_v2/analysis.py:86|
|W07|2|現行0待機仮定の総積込W|MATCH|積込以外0の現行モデル下ではloading_W_min=W_total_min。 src/kmd_toc/cargo_wait_v2/evaluation.py:199; configs/toc_delivery/cargo_wait_model_20261119_v2.json:3|
|W08|2|主要W表示・採択|MISMATCH|主要policyと新局所比較は平均荷待ちW configs/toc_delivery/dw_policy_20261117_v1.json:7; src/kmd_toc/nkr_p2_study/model.py:23|
|W09|2|イベント記録モード|OUT_OF_SCOPE|--model/--eventsで非ゼロ荷卸し等を評価できるが、新正本の積込Wとは別版。現行標準モデルには指定・除外なし。 scripts/evaluate_cargo_wait_v2.py:16; src/kmd_toc/cargo_wait_v2/evaluation.py:145|
|I01|3|C基準|UNIMPLEMENTED|本体のcompare_methodsにI_dual欄なし。今回の数理oracleのみ検算。 src/kmd_toc/cargo_wait_v2/analysis.py:10; src/kmd_toc/cargo_wait_v2/analysis.py:25|
|I02|3|D/W改善率を別計算し小さい方|UNIMPLEMENTED|本体のcompare_methodsにI_dual欄なし。今回の数理oracleのみ検算。 src/kmd_toc/cargo_wait_v2/analysis.py:10; src/kmd_toc/cargo_wait_v2/analysis.py:25|
|I03|3|%単位・正ゼロ負|UNIMPLEMENTED|本体のcompare_methodsにI_dual欄なし。今回の数理oracleのみ検算。 src/kmd_toc/cargo_wait_v2/analysis.py:10; src/kmd_toc/cargo_wait_v2/analysis.py:25|
|I04|3|D_C=0/W_C=0の未定義と絶対差|UNIMPLEMENTED|本体のcompare_methodsにI_dual欄なし。今回の数理oracleのみ検算。 src/kmd_toc/cargo_wait_v2/analysis.py:10; src/kmd_toc/cargo_wait_v2/analysis.py:25|
|I05|3|片方だけの改善を同時改善としない|UNIMPLEMENTED|本体のcompare_methodsにI_dual欄なし。今回の数理oracleのみ検算。 src/kmd_toc/cargo_wait_v2/analysis.py:10; src/kmd_toc/cargo_wait_v2/analysis.py:25|
|I06|3|加重和・平均改善率との分離|UNIMPLEMENTED|本体のcompare_methodsにI_dual欄なし。今回の数理oracleのみ検算。 src/kmd_toc/cargo_wait_v2/analysis.py:10; src/kmd_toc/cargo_wait_v2/analysis.py:25|
|I07|3|探索目的と評価指標の区別|MATCH|B/Cは整数単位で距離優先・待機同距離時の辞書式。量子oracleはDのみ、全体候補を別評価。 src/kmd_toc/termination_v1/solvers.py:34; scripts/large_n_20261119_v5/quantum.py:94|
|H01|4|Q対C・総積込Wの仮説|MISMATCH|有効policyはB/C比較・平均荷待ちの旧仮説 configs/toc_delivery/dw_policy_20261117_v1.json:5|
|H02|4|個別H1判定と局所ACCEPTの区別|UNIMPLEMENTED|局所ACCEPTはパレート改善であり、現行分析はstatistical_hypothesis=NOT_TESTED。 src/kmd_toc/nkr_p2_study/model.py:22; src/kmd_toc/cargo_wait_v2/analysis.py:89|
|H03|4|同一入力・運行条件|MATCH|分析比較器がproblem_hash/od_hash/model_hash一致を要求。旧9保存結果も規模内で同一hash。 src/kmd_toc/cargo_wait_v2/analysis.py:21; src/kmd_toc/cargo_wait_v2/physical.py:65|
|H04|4|同一時間条件|UNIMPLEMENTED|未登録、現行比較器はFalseを表示。 src/kmd_toc/cargo_wait_v2/analysis.py:29|
|H05|4|T補助記録|MATCH|planning_time_s引数を検証しT_program_sに格納。省略時null。 src/kmd_toc/cargo_wait_v2/evaluation.py:126; src/kmd_toc/cargo_wait_v2/evaluation.py:214|
|H06|4|反復と単一試行・統計|UNKNOWN|統計支持null・本実験未開始。旧反復を新本実験に採用しない。 configs/toc_delivery/dw_policy_20261117_v1.json:36; configs/toc_delivery/dw_policy_20261117_v1.json:51|
|A01|5|外部参照であり生成計画ではない|MATCH|role external_reference、same_observed_plan_pair=False。 src/kmd_toc/cargo_wait_v2/reference.py:10; src/kmd_toc/cargo_wait_v2/evaluation.py:124|
|A02|5.1|0.58km/個・Pとの対応|MATCH|0.58*n、one_point_one_parcel=research_assumptionを明示。 src/kmd_toc/cargo_wait_v2/reference.py:11; src/kmd_toc/cargo_wait_v2/reference.py:14|
|A03|5.1|正本の出典URL|MISMATCH|001106397.pdf src/kmd_toc/cargo_wait_v2/reference.py:2|
|A04|5.2|2025年度60分係数|MATCH|係数60と同じ2026-07-10 PDFを参照。 src/kmd_toc/cargo_wait_v2/reference.py:3; src/kmd_toc/cargo_wait_v2/reference.py:11|
|A05|5.2|60U総量・換算運行U|UNIMPLEMENTED|Uなし、60分/運行と平均差のみ。 src/kmd_toc/cargo_wait_v2/reference.py:7; src/kmd_toc/cargo_wait_v2/reference.py:22|
|A06|5.3|2020年度94・315の留保|UNIMPLEMENTED|現行参照APIに年度別補助欄なし。 src/kmd_toc/cargo_wait_v2/reference.py:7|
|A07|5.4|規模別距離580/1160/2320|MATCH|独立再計算で0.58×1000/2000/4000一致。 src/kmd_toc/cargo_wait_v2/reference.py:11|
|A08|5.4|研究便と統計運行・荷待ちの差|UNIMPLEMENTED|旧APIは車両1日平均荷待ちと60の差であり、新総積込Wとの換算比較は未実装。 src/kmd_toc/cargo_wait_v2/reference.py:22; docs/research/DW_RESEARCH_POLICY.md:29|
|A09|5.4|AをI_dual基準へ入れない|MATCH|Aはcompare_methodsに受理されず外部参照は別欄。I_dual本体自体は未実装。 src/kmd_toc/cargo_wait_v2/analysis.py:14; src/kmd_toc/cargo_wait_v2/analysis.py:86|
|A10|5|A_rule_v1・A_human_v1|OUT_OF_SCOPE|A_ruleは区域/順序/容量分割FCFS代理モデル、A_humanは人の割当順序＋プログラム完成。行政参照とは別。 configs/toc_delivery/a_human_v1_20261116.json:2; src/kmd_toc/dw.py:1; scripts/run_dwt.py:3|
|T01|6|敷地面積|MATCH|242068 m²。出典URL・頁と解釈はEXTERNAL_SOURCE_CHECKS.json参照。 docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md:158|
|T02|6|バース|MATCH|382。出典URL・頁と解釈はEXTERNAL_SOURCE_CHECKS.json参照。 docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md:158|
|T03|6|取扱能力|MATCH|10500トン/日。出典URL・頁と解釈はEXTERNAL_SOURCE_CHECKS.json参照。 docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md:158|
|T04|6|2025年度取扱量|MATCH|約5000トン/日。出典URL・頁と解釈はEXTERNAL_SOURCE_CHECKS.json参照。 docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md:158|
|T05|6|2025-03-31参考取扱量|MATCH|4900トン/日。出典URL・頁と解釈はEXTERNAL_SOURCE_CHECKS.json参照。 docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md:158|
|T06|6|出入台数|MATCH|約2500台/日。出典URL・頁と解釈はEXTERNAL_SOURCE_CHECKS.json参照。 docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md:158|
|T07|6|会社・事業者数|MATCH|22。出典URL・頁と解釈はEXTERNAL_SOURCE_CHECKS.json参照。 docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md:158|
|T08|6|単純平均|MATCH|2500/382=6.5445026178…。出典URL・頁と解釈はEXTERNAL_SOURCE_CHECKS.json参照。 docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md:158|
|T09|6.2|1バース5台・部分施設・実績非再現|MATCH|共通設定はresearch_assumption、V/berths=5、2/4/8バース。公開取扱トンからNへの換算を有効入力経路で行わない。 configs/toc_delivery/common_conditions_v1_1.json:6; configs/toc_delivery/common_conditions_v1_1.json:39; src/kmd_toc/common/adapters.py:6|
|T10|6|広範な旧資料での不適切推論の完全な不存在|OUT_OF_SCOPE|監査した有効入力・評価経路では不適切なトン→配送先換算は認めない。全履歴・全文章への一般化はしない。 configs/toc_delivery/common_conditions_v1_1.json:90; src/kmd_toc/common/adapters.py:6|
|SCALE_S1|7.1|S1規模|MATCH|設定一致、1バース5台。 configs/toc_delivery/common_conditions_v1_1.json:39|
|SCALE_S2|7.1|S2規模|MATCH|設定一致、1バース5台。 configs/toc_delivery/common_conditions_v1_1.json:39|
|SCALE_S3|7.1|S3規模|MATCH|設定一致、1バース5台。 configs/toc_delivery/common_conditions_v1_1.json:39|
|C01|7.2|デポ・地域・ToC|MATCH|東京都大田区、京浜トラックターミナル1拠点、ToC。 configs/toc_delivery/common_conditions_v1_1.json:7|
|C02|7.2|需要・便当たり上限|MATCH|1地点1配送単位、60単位/便＝現行では1便最大60配送先。kg・容積の実測容量ではない。 configs/toc_delivery/common_conditions_v1_1.json:28; docs/research/toc_delivery_common/COMMON_CONDITIONS_V1.md:87|
|C03|7.2|最大2便|MATCH|車両ごと最大2連続便。 configs/toc_delivery/common_conditions_v1_1.json:30; src/kmd_toc/cargo_wait_v2/physical.py:93|
|C04|7.2|積込30分・作業120秒|MATCH|1800秒/非空便と120秒/地点。 configs/toc_delivery/common_conditions_v1_1.json:31; src/kmd_toc/cargo_wait_v2/physical.py:117; src/kmd_toc/cargo_wait_v2/physical.py:147|
|C05|7.2|08〜20時|MATCH|初便ready以後、20時帰着期限。 configs/toc_delivery/common_conditions_v1_1.json:34; src/kmd_toc/cargo_wait_v2/physical.py:164|
|C06|7.2|帰着後準備0・第2便接続|MATCH|第2便ready=第1便帰着+0。 configs/toc_delivery/common_conditions_v1_1.json:33; src/kmd_toc/cargo_wait_v2/physical.py:104|
|C07|7.2|顧客時間窓なし|MATCH|customer_time_windows=False。 configs/toc_delivery/common_conditions_v1_1.json:13|
|C08|7.2|バース同時1台|MATCH|実バースの半開区間排他と容量の二重検査。 src/kmd_toc/cargo_wait_v2/physical.py:174|
|C09|7.2|共通道路OD|MATCH|有向OSRM同一応答のdistance/duration、同一hashを要求。 configs/toc_delivery/common_conditions_v1_1.json:68; src/kmd_toc/cargo_wait_v2/physical.py:65|
|C10|7.2|初便readyの時間帯|MATCH|決定的配置の全値が08〜09時内。 configs/toc_delivery/common_conditions_v1_1.json:38|
|C11|7.2|初便分布形|UNKNOWN|決定的な等間隔区間中点配置。新たな分布形の採択ではない。 src/kmd_toc/common/config.py:46|
|CAP01|7.3|最大容量と使用率|MATCH|V×2×60とN/(V×2×60)で独立再計算。 configs/toc_delivery/common_conditions_v1_1.json:27; configs/toc_delivery/common_conditions_v1_1.json:39|
|CAP02|7.3|容量と時間の独立検証|MATCH|CAPACITYとRETURN_DEADLINE_2000を別検証。人工容量境界・時間超過で確認。 src/kmd_toc/cargo_wait_v2/physical.py:115; src/kmd_toc/cargo_wait_v2/physical.py:164|
|BCQ01|7.4|同一需要・OD・台数・バース・運行条件|MATCH|現行APIは同一Problemから評価。旧9保存RESULTも規模内input/OD/physical hash一致。正式Qは未実行。 src/kmd_toc/cargo_wait_v2/analysis.py:21; src/kmd_toc/cargo_wait_v2/physical.py:65; src/kmd_toc/common/adapters.py:17|
|BCQ02|7.4|車両割当・訪問順序|MATCH|BはCW＋車両便CP、CはRouting＋CP。旧Dは古典割当＋マクロ順序。新局所Dは2便n件再配分・順序と外側古典初期計画。探索範囲の差は許容。 src/kmd_toc/termination_v1/methods.py:21; src/kmd_toc/termination_v1/solvers.py:17; src/kmd_toc/d_local_design/completion.py:12|
|BCQ03|7.4|Qの内部識別|UNKNOWN|現行はmethod_id D。Q直接入力は拒否。 src/kmd_toc/cargo_wait_v2/evaluation.py:124|
|BCQ04|7.4|Q全体と初期計画時間|UNIMPLEMENTED|正式runはHOLD、予備は保存B計画から開始。 src/kmd_toc/main_experiment_d/shots.py:124|
|BCQ05|7.4|共通計時開始終了・上限|UNIMPLEMENTED|common_conditionsに開始終了候補はあるが、正式全体Qへの統合と期限採択は未完了。 configs/toc_delivery/common_conditions_v1_1.json:64; src/kmd_toc/cargo_wait_v2/analysis.py:29|
|BCQ06|7.4|共通物理検証|MATCH|現行B/C/D保存計画と新局所候補はcargo_wait_v2のphysicalを利用。 src/kmd_toc/cargo_wait_v2/evaluation.py:129; src/kmd_toc/nkr_p2_study/model.py:118|
|BCQ07|7.4|共通D/W/I_dual評価|UNIMPLEMENTED|Dとloading_W診断は共通だが主要Wが平均、I_dualなし、Q aliasなし。 src/kmd_toc/cargo_wait_v2/analysis.py:25; src/kmd_toc/cargo_wait_v2/evaluation.py:205|
|BCQ08|7.4|積込順序の探索と運用規則|UNKNOWN|CP時刻最適化とFCFSの位置付けが未登録。正本にFCFS要求なし。 src/kmd_toc/termination_v1/solvers.py:19; src/kmd_toc/d_local_design/completion.py:71|
|BCQ09|7.4|正本と実行policyの対応|MISMATCH|旧平均Wのpolicyを固定検証し、新正本への参照・評価版対応なし。 src/kmd_toc/cargo_wait_v2/policy.py:15|
|OLD01|7.4|P1・旧DWT・旧停止規則|OUT_OF_SCOPE|旧runnerは履歴フラグ必須。P1の定数や旧時間予算を新仕様違反と判定しない。 scripts/run_dwt.py:3; docs/research/shots_freeze_20261120/FREEZE_SPEC.md:32|
|OLD02|7.4|n/K/R/p/shotsの状態|UNKNOWN|p2、学習1000/最終10000は既存freezeで確定。n/K/R_local・正式全体設定は未確定。 configs/p2_freeze_20261120/main_experiment_d.json:4; configs/shots_freeze_20261120/main_experiment_d.json:4; src/kmd_toc/main_experiment_d/shots.py:124|

## 公開資料の再確認

指定の5 URLはいずれも閲覧できた。PDFは指定頁のスクリーンショットも取得した。結果は[EXTERNAL_SOURCE_CHECKS.json](research_freeze_20261120/EXTERNAL_SOURCE_CHECKS.json)。
- [国交省2015資料](https://www.mlit.go.jp/common/001102289.pdf) PDF4頁：0.58 km/個、配達車距離÷取扱個数、幹線輸送除外を確認。
- [国交省2026公表PDF](https://www.mlit.go.jp/report/press/content/002011131.pdf) PDF2頁：2025年度60分、2020年度94分、2020年度の表示n=315を確認。[公表ページ](https://www.mlit.go.jp/report/press/tokatsu02_hh_000084.html)の日付は2026-07-10。315が荷待ち発生運行だけを表すとは断定しない。
- [JMT施設案内](https://www.j-m-t.co.jp/terminal/)：242068m²、382バース、取扱能力約10500トン/日、2025年度約5000トン/日、約2500台/日、バース利用会社22社を確認。
- [関東運輸局2025-03-31資料](https://wwwtb.mlit.go.jp/kanto/content/000364901.pdf) PDF1頁：4900トン/日ほかを確認。22のラベルは「ターミナル利用事業者数」であり、JMTのラベルと区別して記録。
- 2500/382=6.5445026…は単純算術。全施設の台数を個別ToCバースの処理実績としない。研究の5台/バース、N/Vは仮定。トンから配送先数や全出入車から大田区配送車への換算は有効入力経路で行われない。

## 既存結果とコード版の対応

旧non_time_variance_pilot_20261117_v1について、登録manifestと374388 bytesのSOURCE_SNAPSHOT.tar.gzを照合した。snapshot SHA-256は登録値と一致。B/C/D各規模r01の9結果はVALIDで、規模内のinput_hash/OD_hash/physical_hashが一致。全75試行を再評価したという意味ではない。
旧solvers.py/methods.py/pipeline/completion.pyの現行内容hashは登録source_hashesと一致し、archive内対応もHISTORICAL_EVIDENCE.jsonへ保存した。新正本の本実験としての適合を意味せず、保存計画の事実を旧コードへ帰属するための確認。
S1 Cの保存例：v3第2便 ready12:13:56→積込12:29:38、v2第2便 ready12:22:23→積込12:27:55。ready順の逆転は確認できるが、これ自体を新正本のFCFS違反とは呼ばない（正本はFCFS未指定）。
nkr_p2の進捗は他の既存プロセスが更新中だったため、進捗件数や結果を今回の正式採択・本実験として凍結しない。本監査はこれらのプロセスを起動・停止・変更していない。
旧総積込Wの保存計画は新正本のD/Wの再評価材料になり得るが、平均W、旧A、旧時間契約、旧仮説成功数はそのまま流用不可。新評価・新実験は別IDで、元結果を残す。

## 人工契約検証と再現

30 tests passed（TEST_RESULTS.xml）。最初のsystem Pythonにはpytestがなく実行できなかったため、既存の.conda Pythonを使用した。追加依存のインストールや既存環境の変更は行っていない。
距離は全デポ発着辺を独立合計、積込Wは全便のstart-readyを手計算。第2便ready、荷役除外、重複バース拒否、61単位の容量超過、3便拒否、容量内でも時間超過を別検証。同じ物理計画のB/C/内部Dで同じD・積込Wを確認。これは量子アルゴリズムの実行検証ではない。
I_dual正・ゼロ・負・分母0は今回専用の私有数学oracleの検算。本体にI_dualを追加したわけではなく、F02はUNIMPLEMENTEDのまま。Q識別子の拒否も現行挙動として確認。
正本本文・改行CRLF・BOM・末尾欠落・ファイル欠落、マニフェストの内容/hash/path/version/サイズ/JSON重複、および本文とmanifestの同時改変でFAILを検証。改変はすべてtmp_pathのコピーに限定。

```bash
python -B scripts/verify_research_freeze_20261120.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .conda/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_research_freeze_20261120.py tests/test_research_freeze_contracts_20261120.py
```

## 永続保護と限界

追加workflow `.github/workflows/research-freeze-v1.yml` はpush/pull_request/manualで標準ライブラリの固定hash検証を実行する。リモートへ反映・実行はしていない。既存CIは変更しない。
後続の管理者設定手順：mainのSettings → Rules/BranchesでPRレビュー必須・必須status check `frozen-spec-v1`を設定し、更新時の承認失効や最新変更への第三者承認を検討する。force pushとbranch deletionを許可せず、管理者を含むbypassの扱いを明示する。CODEOWNERSでdocs/frozen、検証script、検証tests、workflow自体の責任者を登録し、Code Owner承認を必須にする。今回はリモート設定もCODEOWNERSも変更しない。
仕様と期待hash・validator・CIを同時に変更できる権限があるとローカル検証だけでは完全強制できない。CIがpush後に失敗するだけでは既存branch変更を防げないため、必須checkとレビューをリモートで有効化する必要がある。アカウント・プランにより利用可能な保護機能は異なる。
根拠：[GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)、[CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)。
将来の仕様改訂はユーザーの明示承認を受け、v2を新規作成し、v1本文・manifest・固定hashを上書きしない。暫定値のfreezeは科学的根拠の確定を意味しない。

## 推奨順序と次工程判定

1. 新正本に対応する参照・policy・評価版の設計（F09/F01/F03）。
2. 共通評価の総積込W・C/Q対応・I_dualと個別H1判定（F02/F13）。
3. AのU換算・年度別参照・指定出典と留保（F06/F07/F08）。
4. 初便分布・積込時刻探索の位置付け・T・期限採択・統計設計の承認（F10/F12/F04/F11）。
5. 初期計画込み正式Q全体runnerの統合と別承認下の契約検証（F05）。
**次工程：設計・修正計画の検討へ進める。本実験開始はHOLD。今回の仕様凍結・監査は完了したが、実装適合PASSではない。**

## 今回の追加物と最終確認

既存の研究実装・設定・実験結果・READMEは変更していない。HEADも維持した。原本完全性PASS、追加30検証PASS。人工検算ではD=1.048km、総積込W=36.4分（平均18.2分/活動車両日）で独立合計と一致した。この数値は人工契約検証のみでS1〜S3の研究結果ではない。

追加物は凍結本文、全文manifest、独立検証script、2つの独立test、新規CI workflow、監査Markdown/JSON、およびreports/research_freeze_20261120配下の環境・コマンド・原データ検算・既存コード照合・保全・テストログ。全ファイル一覧は同ディレクトリのADDED_FILES.json、成果物hashはARTIFACT_SHA256.json。リモートの保護設定とCI実行結果は未確認で、変更・pushは行っていない。
