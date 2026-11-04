# Step 1 最終監査

**作業上COMPLETE、総合CONDITIONAL。** Task1-1〜1-5の全成果物を保存し、Step2を開始できる評価設計を具体化した。HOLDの解消、正式採用、Step2の実行は完了条件としない。

## 入力と版

開始HEAD `1b00bd7927fa1e7688e4772ac1da9db46d9bac11`。Sの3アルゴリズム群は保存PROTOCOL.json/SOURCE_SNAPSHOTとhashで固定。主数値はPの11月2日全件CSVを元NPZ/測定/証明へ再接続。Tの11月4日統合trialは参照資料として再検査した。材料モデルはT8/run02、T9/run01、BR/run01、Controlled-DCは凍結JSONとhash保護kernel。SOURCE_MAP.mdに実在絶対パス、SOURCE_PROVENANCE.csvに10,717入力・コード・既存成果の版/hash/サイズ/時刻を保存した。

ルート統合DOCX SHA256は`53a3abac8d8e62db6442f92d850eb2f3bb58e876606a84f61f6fe3de1763f99f`。v07との抽出全文（表内含む）一致=True、バイトhash一致=False。revisedとT/THESIS_TRIALも別候補として読取。最新trialを正式版と誤認していない。AGENTS.mdは祖先とrepo内（環境・第三者ツール除外）に該当なし。evidence/AGENTS_DISCOVERY.json参照。

## 今回の独立検査

計15,944件の監査行は全PASS（元NPZ36,800経路検算など一部は1行へ集約しており、行数を試行数としない）。主検査9,586、補足5,331、履歴1,027。既存trialの検査件数を今回の検査件数に流用していない。

- Bの460元NPZ、3,680保存測定原本、36,800計画の経路/分数目的/順列/216PE/帰庫制約を照合。不一致0、保存best可行36,800。float CSVとの差最大1.82e-12秒は表示/parse精度の差で、効果判定は元Fraction。
- B規模は3/4/5/25/100/125、入力78/78/78/78/78/70。8設定×10測定repを確認。厳密参照407、未証明53（R4=21、R5=32）。53すべての元terminationはEXACT_BOUND_WITNESS_MISMATCH。単なる未保存や時間切れとは扱わず、近似値/下界で補完しない。
- 古典近似2法×460=920原経路のinput hash・目的分数・可行性・共通初期経路を検算。古典初期の上流460RESULTと時間の転記も確認。初期は3構成＋relocate/有向reversal最大3sweep。初期差と近似差・厳密参照を区別。
- T/PATH1_INPUT_SEED_STATISTICS.csvの3,680行を平均/SD/min/max/nから再集計し一致。36,800独立標本ではない。学習済みfitの10測定repである。既存group bootstrapコードも読取確認し、新規区間計算はしていない。
- 旧Aの元入力/古典/量子結果へ接続し78入力・取得64・36政策/2,808行を確認。時間窓ありの履歴として保持、定時率を今回の主指標にしていない。
- T08式からLP96.14565479871602kg、S90.6973573836391kg、差5.44829741507692kg、u境界0.877094071984104、V境界3.19315568377979Vを再現。モデル計算・proxy・仮定であり完成品の実測ではない。
- T09既知8成分を全183条件×8=1,464件で独立算術照合、完成pack全NULLを確認。B015はT09_ROW031/032、B051は103/104。既知差9.722608121107783kg/5.977891152148871kgを元行から確認。ROW183の全面対向FAILは保持。
- C古典460軌跡の保存hashを確認し、代表1軌跡の2Crr×LP/Sを凍結kernelで軽量照合。全軌跡の新規物理再計算はしていない。端点の保存電力量を対応再集計し、総和比lower=0.412579010061%、upper=0.413590411697%を確認。49点感度45,080行のPK/範囲/端点も確認。

## 横断整合性

CROSS_CONSISTENCY_AUDIT.csvの10項目はPASS/CONDITIONALで整理。旧研究にあるFAIL（地域道路受入・T09全面対向・旧主方針の残存）を今回の算術検査PASSで消去していない。

主比較はΔJ=古典近似JC−JQ、greedy adjacentを主、random swap別対照、初期補助、J*共通参照。exact Fractionに基づくεJ=0。古典は初期incumbent保持、Q主保存値はraw bestという出力規則差を明示。現行8設定の予算統制はHOLD。τtotal≤Hplanは数式を定義したがHplan数値を設定せず、32,400秒を計算締切にしない。CPU計測をQPUへ換算しない。

T08主/T09構造補完、b/deltaの部材を分離。T08の固定部材をT09へ再加算しない。同一軌跡mass置換で、総仕事の正値化・branch補正を保持。約0.413%は総電力量比、個別率平均とは別。49点やCrr条件を独立nにしない。

## 未解決と引継ぎ

HOLD_REGISTER.mdのH01〜H12：正式採用版、現行8予算、厳密53、総時間/Hplan、compiled/QPU、学習seed、raw invalid一部、材料full-cell適格性、未知BOM、量子材料改善、実道路/B→DC、末端/除外物理。既存数値の算術PASSはこれらの実証を意味しない。

既存有限cohort記述を主に、Step2ではJC対応差、中央値/SD/IQR、測定乱数・需要group感度を分離、規模/設定/欠測層を示す。T08/T09は感度・構造不確実性を主とする。新規実験優先はE1支持統制→E3時間再計測→E2証明53→E4共通モデル感度→E5保存走行条件。pilotの回数は診断用で全量実験の妥当回数を確定したものではない。詳細と実行gateはSTEP2_HANDOFF.md/候補CSV。

## 保全・境界

読取元10,717件の開始時/終了hashは全一致、Git追跡100件の開始/終了hashは全一致。広い探索対象227,795件のsize/mtime検査：変更0、欠落0。この広域検査は全バイトhash監査ではなく、環境・第三者ツール等を除外する。元データ・原稿の保全主張はhash台帳対象で保証する。

Git tracked diffは開始時と一致、trial外Git状態の追加0/除去0件。保全総合=PASS。SOURCE_PRESERVATION_CHECKS.csv、TRACKED_PRESERVATION_CHECKS.csv、EXISTING_FILE_STAT_CHECK.json、OUTSIDE_TRIAL_GIT_CHANGES.jsonに証拠を保存。

本trial以外へ書き込む処理、新規QAOA/SUMO/厳密求解、Step2統計推定・追加実験、commit/push/公開、正式原稿への反映は実施していない。全て独立したStep1 trial案であり、正式な研究成果への採用・統合は未実施。
