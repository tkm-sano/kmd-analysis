# 定量研究 最終結果報告

## 最終判定と対象

**FINAL_QUANTITATIVE_STUDY_RESULT = FROZEN**。既存freezeと保存済み個別データを監査・再集計し、すべての最終ゲートをPASSした。新しいQuantum、最適化、routing、SUMO、Battery評価、trajectory生成、追加simulationは行っていない。対象はR0/R1 Candidate C / Protocol V2、同じControlled-DC/Batteryモデル、同じMethod×Battery定義による定量研究branchである。修士論文全体の完成宣言ではない。

## Authorityと検証の追跡

R0/R1のscience run完了→final-route subset→route identity→trajectory→Battery result freeze→共通matched統合分析を確認した。各上流freezeは当時点のsnapshotであり、例えばtrajectory freezeのBattery_applied=falseや過去next stageは履歴であって後続完了と矛盾しない。正確なpath/hashは[authority chain](FINAL_FREEZE_AUTHORITY_CHAIN.csv)と[全artifact manifest](FINAL_ARTIFACT_MANIFEST.csv)に保存する。

全78 planned blockを凍結済みparent_id+replicate_idで再対応し、R0/R1 PIDの1対1binding、nested membership、parent/assignment/temporal hashes、欠落・重複なしを確認した。64 included/14 excludedを保存した既存population表と一致。入力・ソース・上流freezeおよびhistorical成果物は変更しない。

## 実験事実

| Branch | full science | route available | 同一経路 | 異経路 | trajectory/Battery scope |
|---|---:|---:|---:|---:|---|
| R0 common Protocol V2 | 78/78 | 78/78 | 78 | 0 | FULL_78 |
| R1 common Protocol V2 | 78/78 | 64/78 | 59 | 5 | CONDITIONAL_64_OF_78 |
| Historical R0（contextのみ） | 旧freezeを保持 | 40/78 | 29 | 11 | primary比較から除外 |

R0は同一trajectory78件、両methodのenergy・effect・componentは全条件exact0差。R1は64件×両methodのtrajectory・Battery評価完了で、IDENTICAL59の全保存数値が一致した。全78science実行の完了と、route取得64・下流評価64を区別する。

## 共通64の中心結果

Battery effect(%)=100×(E_B0−E_Bk)/E_B0。D_R0=Classical effect−Quantum effect、D_R1も同じ符号。T=D_R1−D_R0、単位は百分率ポイント(pp)。D_R0を0と置かず両scaleの保存effectをjoinして再算出した。Wh savingについても同符号を検証した。

| Crr | 比較 | n | 保存数値からの平均T（pp、丸め前Decimal） | 中央値 | 正 / 0 / 負 |
|---|---|---:|---:|---:|---|
| CRR_LOWER_BOUND | B0_TO_B1 | 64 | -0.000248222961986721875 | 0 | 1 / 59 / 4 |
| CRR_LOWER_BOUND | B0_TO_B2 | 64 | -0.0003824303659828328125 | 0 | 1 / 59 / 4 |
| CRR_UPPER_BOUND | B0_TO_B1 | 64 | -0.000219201055817571875 | 0 | 1 / 59 / 4 |
| CRR_UPPER_BOUND | B0_TO_B2 | 64 | -0.0003377541726442796875 | 0 | 1 / 59 / 4 |

全4条件の個別256件を再集計し、保存要約に浮動小数点表示誤差内で一致。非ゼロ判定はDecimal exact差による（epsilonで0に丸めていない）。meanの上記Decimalは保存された入力桁からの値であり、元計算の無限精度を意味しない。全統計は[最終Scale要約](FINAL_SCALE_METHOD_BATTERY_SUMMARY.csv)。

route identity transitionはI→I=59、I→D=5、D→I=0、D→D=0。非ゼロ5 blockは異経路5に完全一致し、全条件で4負・1正。T<0はR1 Quantum-derived trajectoryの相対Battery削減率がClassicalより大きいことを示すが、method superiorityとはしない。

## 物理的解釈

**問題規模 → 経路選択の違い → 走行軌跡の違い → 消費energyの違い → Battery質量感度の違い**というモデルの依存関係に沿って証拠を整理した。媒介要因それぞれの独立した因果効果を識別したものではない。

[最終mechanism表](FINAL_MECHANISM_SUMMARY.csv)は5 case×4条件について両scale/methodの訪問順序、目的値とgap、trajectory path/hash、distance/duration、停止・再発進、正負加速interval、各成分とinteractionを保存する。[速度分布](FINAL_SPEED_DISTRIBUTION_SUMMARY.csv)は保存canonical samplesのみから得た20 method/scale bindings（15 distinct trajectories）の記述統計。stationaryを含む全sampleの分位点・平均・SD・最大値・速度階級度数と停止率を保存し、mean/max/sample数を既存manifestと照合した。time interpolation、trajectory再生成、energy再評価はしていない。

同一経路・同一trajectory・同一Battery/Crr modelというこのinternal controlの条件でeffectは一致する。Quantumであるため一般に一致すると解釈しない。異経路5では小さなBattery sensitivity差が生じた。全5件×全比較/Crrにおいて、translationalのabsolute saving差がrollingより大きく、rotational/aerodynamic/branch correctionのsaving差Whは0。branch correctionは分母差による微小なpp寄与を持ち得る。

直接運用energy差はQ−C（Wh）、saving interactionはC−Q saving（Wh）であり、別指標。B0/B1/B2いずれのdirect差でも全5非ゼロcaseで|direct|>|saving interaction|、IDENTICAL59では0=0。Whとppを直接比較しない。

## 感度分析

保存LOO276件（共通64×4条件=256、nonzero5×4条件=20）を個別に再検証した。

| scope | Crr | 比較 | 最大case除外時 mean T (pp) | magnitude低下率(%) | 全LOO負符号維持 |
|---|---|---|---:|---:|---|
| COMMON_MATCHED | CRR_LOWER_BOUND | B0_TO_B1 | -9.32183861178e-05 | 62.4457039 | YES |
| COMMON_MATCHED | CRR_LOWER_BOUND | B0_TO_B2 | -0.000143655267452 | 62.4362289 | YES |
| COMMON_MATCHED | CRR_UPPER_BOUND | B0_TO_B1 | -8.67435673653e-05 | 60.4273953 | YES |
| COMMON_MATCHED | CRR_UPPER_BOUND | B0_TO_B2 | -0.000133585093742 | 60.4490175 | YES |
| NONZERO_5 | CRR_LOWER_BOUND | B0_TO_B1 | -0.00146818958135 | 53.7906122 | YES |
| NONZERO_5 | CRR_LOWER_BOUND | B0_TO_B2 | -0.00226257046238 | 53.7789535 | YES |
| NONZERO_5 | CRR_UPPER_BOUND | B0_TO_B1 | -0.001366211186 | 51.3071465 | YES |
| NONZERO_5 | CRR_UPPER_BOUND | B0_TO_B2 | -0.00210396522644 | 51.333752 | YES |

最大影響block：`PROPOSED-OTA-B2C-2026-01-01-002002_V002|replicate_id=0`、R1 PID `P_507cf93a31b95e6873fde136f5837b9b589c90453296db2312410c54c6e5e24d`。全条件で同じcaseである。詳細full mean・LOO min/maxは[感度再検証](FINAL_SENSITIVITY_VERIFICATION.csv)。

符号は安定していてもmagnitudeは安定していない。共通64の最大case除外では約60–62%低下、nonzero5内では約51–54%低下。平均値のみで結論せず、個別5件・中央値・符号patternを既存case表とともに評価する。LOOはseed反復による頑健性の証拠ではない。

## 研究上の示唆

1. 共通protocolのR0で全78のrouteが一致したことはMethod×Batteryのexact-zero internal controlを与える。
2. R1では取得可能64の5件にroute divergenceと小さなBattery effect差が集中した。
3. direct energy差の方がsaving interactionより大きく、mass sensitivity差は主に並進運動成分に対応する。
4. 観測された量的関係は少数caseへの感度が大きく、一般化は限定する。

実験事実・物理的解釈・示唆の区別と個別根拠は[結論―証拠対応表](FINAL_RESULT_SUMMARY.csv)に明示した。historical R0（40/78・同一29・異経路11）とcommon-protocol R0（78/78・同一78）は別authority。encoding/protocol選択とstochastic realizationが観測結果に影響し得る方法論上のcontextだが、primary matched comparisonに混ぜずScale effectとも呼ばない。

## 識別判定と主張限界

- PROTOCOL_CHANGE_CONFOUNDING = **RESOLVED**
- COMMON_PROTOCOL_MATCHED_SCALE_X_METHOD_X_BATTERY = **CALCULATED**
- FULL_POPULATION_SCALE_X_METHOD_X_BATTERY = **NOT_IDENTIFIABLE_WITHOUT_IMPUTATION**
- CAUSAL_PURE_SCALE_EFFECT = **NOT_ESTABLISHED**

共通protocolの変更交絡は解消しているが、1 science seed/PID・共通乱数なし・非ランダムなR1取得subset・nested customer task変更・parent/group依存が残る。未取得14を含むR1全78の効果、母集団全体Scale効果、純粋因果的Scale効果、Quantum優位性、一般的な大規模拡張性、実運用保証は主張できない。imputationはしていない。詳細は[識別可能性と限界](FINAL_IDENTIFIABILITY_AND_LIMITATIONS.md)。

## 最終freezeと次段階

FINAL_QUANTITATIVE_RESULT_FREEZE.jsonを最終結果authorityとし、FINAL_INTEGRITY_VERIFICATION.jsonが全入力・上流保護ファイル・出力（freeze自身を含む）のSHA-256を検証する。hash循環を避け、manifestは上流とcore成果物、freezeはmanifest/core成果物、integrityはfreezeとgit記録を含む全最終出力を参照し、integrity自身のみself-hashから除外する。

**NEXT_STAGE = SYNTHESIZE_FUTURE_MOBILITY_SYSTEM_SCENARIO_AXES — PLANNED_NOT_EXECUTED**

次段階は既存文献から技術・制度・インフラ等の軸を整理し、Scale×Routing Method×Batteryを将来配送システム全体へ位置づけ、発展段階・分岐経路の仮説と専門家インタビュー設計につなげる。今回その作業は開始していない。定量研究の実行・分析完了と修士論文全体の完成は区別する。
