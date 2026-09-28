# 未commit変更の棚卸し（2026-09-28）

開始時HEAD/main/origin/main: `1abd765fb14575da6950432a10eccb4e635557f3`。
作業branch: `chore/repository-consolidation-20260928`。科学実行なし。これはGit整理の記録であり、実行authorityの変更ではない。

## 全件分類とcommit範囲

既存変更49ファイル（tracked変更4・untracked45）を全件確認した。[INVENTORY.csv](INVENTORY.csv)にpath、A–F分類、内容、由来、commit対象、group、SHA-256を記録。
A=研究設計・文書、B=科学コード・設定、C=authority、D=案内・summary・図。E（一時物）・F（由来不明）は今回の49件にない。

| Group | commit message | 内容 |
|---|---|---|
| G1 | `feat: preserve validated minimal EVRP implementation` | Minimal EVRP実装・独立検査・単体テスト・3件の根拠registry |
| G2 | `research: record battery plans and research authorities` | 研究設計・Battery計画・Battery根拠registry・タイトル・問い・仮説 |
| G3 | `docs: organize research navigation and platform evidence` | README/CURRENT/概要、navigation、アーカイブ、summary・図・描画source、本棚卸し |

CSVはこの作業開始時点の49件を記録する。本棚卸しで追加したREADME、INVENTORY.csv、VALIDATION.json、MANIFEST.jsonはG3の文書監査成果物としてcommitする。MANIFESTは自己参照を除く本報告3件を収録。

## Minimal EVRP / Batteryの採否

Minimal EVRPの11ファイルと根拠registryは既存のfreeze pinsに一致する。`r24_minimal_evrp_charging_validation/20260926_v2/ARTIFACT_MANIFEST.json`の36件も一致し、検証結果とsourceの対応がある。一時コードではなく、保存結果の再現・独立確認に必要な限定実装として採用する。汎用EVRP本評価solverとしては扱わない。

20 kWh・reserve0.1・0.127 kWh/kmは固定参照モデル値である。10 kWと制御初期SOCはCONTROLLED_VALIDATION_CONDITIONで、実車の充電性能authorityでもMain S0許可でもない。固定値は検証対象を限定する意図的な値であり、不明な一時調整値とは判定しない。メーカー公表総容量とusable容量、WLTC係数と配送時実測、公開技術目標と将来性能予測を区別した記述がある。充電性能の未解決事項は未解決のまま保持する。

## 保護履歴・現行文書の境界

既存保護一覧15,096件中15,095件が一致。不一致は依頼済みREADME入口整理1件のみ。歴史的pinsは書き換えない。今回のcommitは、この文書差分を将来の科学admissionで自動許可するものではない。

RESEARCH_OVERVIEWの「sampling未開始」と一部段階文書の旧next taskは、以前の時点の記録として残っている。最新のCURRENT_EXECUTIONはsampling PASS / COMPLETE・予算消費済みを示し、READMEもCURRENT優先を明記する。保護された概要・archive manifestをGit整理のために更新しない。古い記述を科学再実行の許可とは扱わない。

## commit対象外

既存.gitignoreどおり、`reproducibility/outputs/traffic_simulation/**`の科学生成物、raw/processedデータ、Conda環境、cache/bytecode等は追加しない。削除もしない。sourceと保存済み検証結果、説明用のcurated SVG/PNGを区別した。図は今回ユーザーが要求した共有成果物としてG3に含める。

Git管理外の科学成果物をforce-addしない。ローカルには実在するが新規clone/GitHubでは別途取得が必要なリンクが96件（重複を含む）ある。README/navigationにこの制約を明記済み。cleanとはGit上の変更なしを意味し、ローカル科学証拠やcacheの削除を意味しない。.gitignore変更は不要。

## 検証

[VALIDATION.json](VALIDATION.json)に検査対象・件数を記録。35件のMinimal EVRP単体/保存結果検査、4件の既存CI auditがPASS。最適化・科学runner・backendは起動していない。Python12件AST、JSON5件、registry4件、SVG4件を静的解析。registryは既存構造とsnapshot SHA-256を検査し、新規schemaは定義していない。

summary manifest14件、summary出典28件、図出典7件、EVRP manifest36件、finite-shot manifest45件、歴史的ledger329件、保存source snapshot21件、概要snapshot/現行hashが一致。Markdown296リンクがローカルで実在（archive本文は保存元rootを基準）。外部URLの再検証・見出しanchorの完全検証は対象外。

state予算2/2、sampling予算2/2 calls・128/128 shots、reserved0を保存成果物から確認。今回の増分はすべて0。科学履歴を変更せず、git diff --check PASS。

commit後は通常push → PR → CI確認 → 通常merge → mainをfast-forward同期する。競合・CI失敗・必要reviewがあればその段階で停止する。実際のcommit hash・PR・同期結果はGit履歴と作業最終報告で示す。

## stage後の書式検査

初回のcached diff検査で、未追跡だったSVGの行末空白、archive計画のMarkdown改行、棚卸しCSVのCRLFを検出した。SVGは整形前後のXML構造・属性値・textの一致を検査して行末空白のみ除去し、描画sourceにも同じ整形を追加した。計画文書の改行は明示的brへ置換。CSVはLFへ統一した。科学ファイルは変更せず、summary manifestを更新した。CSVのsha256は棚卸し時点、commit_sha256は書式整形後のcommit内容を示す。
