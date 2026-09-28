<a id="未commit変更の棚卸し2026-09-28"></a>

# 未変更記録変更の棚卸し（2026-09-28）

開始時HEAD/main/origin/main: `1abd765fb14575da6950432a10eccb4e635557f3`。
作業分岐: `chore/repository-consolidation-20260928`。科学実行なし。これはGit整理の記録であり、実行正本の変更ではない。

<a id="全件分類とcommit範囲"></a>

## 全件分類と変更記録範囲

既存変更49ファイル（tracked変更4・untracked45）を全件確認した。[INVENTORY.csv](INVENTORY.csv)に保存先、A–F分類、内容、由来、変更記録対象、群、SHA-256を記録。
A=研究設計・文書、B=科学コード・設定、C=正本、D=案内・まとめ・図。E（一時物）・F（由来不明）は今回の49件にない。

| Group | commit message | 内容 |
|---|---|---|
| G1 | `feat: preserve validated minimal EVRP implementation` | 最小構成の電気自動車配送経路問題実装・独立検査・単体テスト・3件の根拠登録簿 |
| G2 | `research: record battery plans and research authorities` | 研究設計・電池計画・電池根拠登録簿・タイトル・問い・仮説 |
| G3 | `docs: organize research navigation and platform evidence` | README/CURRENT/概要、navigation、アーカイブ、まとめ・図・描画出典、本棚卸し |

コンマ区切り形式はこの作業開始時点の49件を記録する。本棚卸しで追加した案内文書、INVENTORY.csv、VALIDATION.json、MANIFEST.jsonはG3の文書監査成果物として変更記録する。MANIFESTは自己参照を除く本報告3件を収録。

<a id="minimal-evrp--batteryの採否"></a>

## 最小構成の電気自動車配送経路問題 / 電池の採否

最小構成の電気自動車配送経路問題の11ファイルと根拠登録簿は既存の固定 pinsに一致する。`r24_minimal_evrp_charging_validation/20260926_v2/ARTIFACT_MANIFEST.json`の36件も一致し、検証結果と出典の対応がある。一時コードではなく、保存結果の再現・独立確認に必要な限定実装として採用する。汎用電気自動車配送経路問題本評価求解器としては扱わない。

20 kWh・reserve0.1・0.127 kWh/kmは固定参照モデル値である。10 kWと制御初期充電率はCONTROLLED_VALIDATION_CONDITIONで、実車の充電性能正本でも本実験の第0段階許可でもない。固定値は検証対象を限定する意図的な値であり、不明な一時調整値とは判定しない。メーカー公表総容量と利用可能な容量、WLTC係数と配送時実測、公開技術目標と将来性能予測を区別した記述がある。充電性能の未解決事項は未解決のまま保持する。

## 保護履歴・現行文書の境界

既存保護一覧15,096件中15,095件が一致。不一致は依頼済み案内文書入口整理1件のみ。歴史的pinsは書き換えない。今回の変更記録は、この文書差分を将来の科学admissionで自動許可するものではない。

RESEARCH_OVERVIEWの「標本抽出未開始」と一部段階文書の旧次の作業は、以前の時点の記録として残っている。最新のCURRENT_EXECUTIONは標本抽出 合格・完了・予算消費済みを示し、案内文書も現行優先を明記する。保護された概要・archive 成果物一覧をGit整理のために更新しない。古い記述を科学再実行の許可とは扱わない。

<a id="commit対象外"></a>

## 変更記録対象外

既存.gitignoreどおり、`reproducibility/outputs/traffic_simulation/**`の科学生成物、raw/processedデータ、Conda環境、cache/bytecode等は追加しない。削除もしない。出典と保存済み検証結果、説明用のcurated SVG/PNGを区別した。図は今回ユーザーが要求した共有成果物としてG3に含める。

Git管理外の科学成果物をforce-addしない。ローカルには実在するが新規clone/GitHubでは別途取得が必要なリンクが96件（重複を含む）ある。README/navigationにこの制約を明記済み。cleanとはGit上の変更なしを意味し、ローカル科学証拠や一時保存の削除を意味しない。.gitignore変更は不要。

## 検証

[VALIDATION.json](VALIDATION.json)に検査対象・件数を記録。35件の最小構成の電気自動車配送経路問題単体/保存結果検査、4件の既存CI 監査が合格。最適化・科学実行器・計算方式は起動していない。Python12件AST、JSON5件、registry4件、SVG4件を静的解析。登録簿は既存構造と保存時点の記録 SHA-256を検査し、新規データ構造は定義していない。

まとめ manifest14件、まとめ出典28件、図出典7件、電気自動車配送経路問題 manifest36件、有限回測定 manifest45件、歴史的ledger329件、保存出典 snapshot21件、概要保存時点の記録/現行ハッシュ値が一致。Markdown296リンクがローカルで実在（archive本文は保存元最上位を基準）。外部URLの再検証・見出し基準の完全検証は対象外。

状態予算2/2、標本抽出予算2/2 回呼出し・128/128 回測定、reserved0を保存成果物から確認。今回の増分はすべて0。科学履歴を変更せず、git diff --check 合格。

変更記録後は通常push → PR → CI確認 → 通常merge → 本番をfast-順方向同期する。競合・CI失敗・必要確認があればその段階で停止する。実際の変更記録 ハッシュ値・PR・同期結果はGit履歴と作業最終報告で示す。

## 段階後の書式検査

初回のcached diff検査で、未追跡だったベクトル画像の行末空白、archive計画の軽量マークアップ文書改行、棚卸しコンマ区切り形式のCRLFを検出した。ベクトル画像は整形前後の拡張マークアップ形式構造・属性値・textの一致を検査して行末空白のみ除去し、描画出典にも同じ整形を追加した。計画文書の改行は明示的brへ置換。コンマ区切り形式はLFへ統一した。科学ファイルは変更せず、まとめ 成果物一覧を更新した。コンマ区切り形式のsha256は棚卸し時点、commit_sha256は書式整形後の変更記録内容を示す。
