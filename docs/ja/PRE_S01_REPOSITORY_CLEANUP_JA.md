<a id="s01開始前のrepository-cleanup記録"></a>

# S01開始前のリポジトリ cleanup記録

<a id="cleanup-summary"></a>

## Cleanup まとめ

2026年9月22日に、S01開始前の作業領域を監査した。科学的成果物の整理を目的とした大量削除は行わず、参照されていない再生成可能なPython bytecodeだけを個別に削除した。

| 項目 | 結果 |
| --- | ---: |
| 棚卸し対象ファイル | 15,443 |
| 一時保存候補 | 836 |
| 削除 | 33 |
| archive移動 | 0 |
| 保持した一時保存候補 | 803 |
| 既存ファイルの保持総数（棚卸し対象−削除） | 15,410 |
| 削除対象の論理サイズ | 746,815 バイト（約0.71 MiB） |
| SHA256一致を確認した保護対象 | 11,816 |

開始HEADは `49efad3cbba16344c911e3e26179bdbefb915c85`、分岐は `main`、作業ツリーはcleanであった。科学コードの検証済み 基準は `6ccbadbd42bdad6c95e22f7420aff6ee787c8997` である。その後の既存変更は日本語研究ガイドの追加と体裁調整である。

棚卸しはGit 付随情報、`.conda`、`.local`、`.venv`、`node_modules`、symlink先を除外した実ファイルを対象とした。依存環境を削除して容量を減らす作業は行っていない。ignored一覧もローカル監査記録へ保存した。削減量はファイル内容の合計であり、NFSの割当済みblockやGit履歴の縮小を意味しない。

## Deleted

[A分類の削除一覧](pre_s01_repository_cleanup/DELETED_FILES.csv)に保存先・理由・サイズ・SHA256を保存した。全件が既存方針でignoredの `__pycache__/*.pyc` であり、対応する `.py` の存在を確認した。tracked ファイルの削除は0件である。

10,030件のコード・軽量マークアップ文書・成果物一覧・JSON/CSV・Notebook・設定・shell スクリプト・patch等を検索した。一時保存の具体的なファイル名または保存先が見つかった候補は保持した。削除直前にも各ファイルのハッシュ値を再確認した。再帰的な削除、reset、git cleanは使用していない。Git管理外一時保存のローカル削除自体はpushされず、Gitには判断の記録が残る。

## Archived

今回のarchive移動は0件である。[ARCHIVE_MANIFEST.csv](pre_s01_repository_cleanup/ARCHIVE_MANIFEST.csv)はヘッダーのみである。過去の停止記録やpatch、成果物一覧は参照・出典・来歴を保つため元の保存先で保持した。安全に移動できるB分類は確定しなかった。

## Preserved intentionally

[保持した一時保存候補](pre_s01_repository_cleanup/PRESERVED_CACHE_CANDIDATES.csv)は803件である。このうち163件は元ソースが現作業ツリーにないためD分類として原位置で保持した。残り640件は参照がある等の保守的な除外対象である。用途不明のものを削除・移動する判断には進んでいない。

以下はC分類として保持した。

- scientific 出典、試験、Candidate A、制約なし二値二次最適化、比較 固定、乱数の種、台帳、Uniform結果。
- Structured v1〜v6、S01 停止記録、成果物一覧・ハッシュ値監査、未加工 結果、Notebook、古典計算 参照資料、道路網成果物。
- [日本語研究ガイド](VRPTW_TO_EVRP_RESEARCH_GUIDE_JA.md)を含む既存docs。
- Git stash 2件とv5の `PRESERVED_UNRELATED_WORK.tar.gz`。apply/pop/dropは行っていない。
- 大容量のCityGML ZIP（最大約544 MB）、オープンストリートマップ PBF/XML、過去の道路網比較データ。似た名前や同じサイズは不要の根拠にしていない。
- 専用台帳 `.lock`。空ファイルであっても相互排他の対象であり削除しない。

`.gitignore`は一時保存設定が既にあるため変更していない。Notebook 出力のstrip、科学的内容の変更、軽量マークアップ文書参照先の移動も行っていない。

## 再現性確認

[検証結果](pre_s01_repository_cleanup/VALIDATION_SUMMARY.json)に記録した通り、tracked files・出典・R23/R24成果物の保護対象11,816件のSHA256は前後一致した。制約なし二値二次最適化、Candidate A、固定、v4/v5/v6、Uniform 結果を含む。さらにv6の成果物 成果物一覧、実行時間 dependencies、比較 参照 authoritiesを既存ハッシュ値と照合した。

台帳は前後ともscientific 回路 **363**、回測定 **743,424**、reserved **0**である。台帳 SHA256は `7bd0ae76a1cfb79bfd00fcc8da53d140483f5ba923dd8f72549312f2d4688ef6` である。今回のscientific 回路・回測定・最適化処理 evaluations・backend/sampler 実行・台帳 increment・reservationはすべて0である。

direct-構築 22件と読取り専用 台帳回帰4件の計**26 試験 合格**を確認した。Uniform full/initial builder呼出しはいずれも0、Candidate A入力制限・状態 同一性記録・変数順序・shared body・固定・予算 projectionを検証した。計算方式・sampler・最適化処理・persistent 台帳 変更記録にはhard 実行制御を適用した。新たな状態ベクトル 標本抽出やNFS concurrency/reservation試験は行っていない。既存v6の試験成果物を再生成せず保持した。軽量リポジトリ 監査は別途4 試験を実行した。

ローカルの詳細監査は `reproducibility/outputs/traffic_simulation/r24_vrptw_structured_initial_state/20260922_pre_s01_repository_cleanup` に保存した。ここには初期Git状態、ignored一覧、候補と参照元、保護ハッシュ値一覧、テストログ、大容量上位25件が含まれる。このディレクトリは既存実行時間-出力 方針によりGit管理外である。Git管理するのは本報告と隣接成果物一覧・検証まとめのみである。

<a id="next-task"></a>

## 次の作業

次のscientific 作業は **S01：N003 WIDE × 3 反復回数 条件を統制した scientific launch** である。今回S01は開始していない。cleanup後の変更記録は科学設定を変更しないが、実行開始時にはそのHEADを記録してfresh 判定基準を改めて実施する必要がある。S02以降へ自動進行しない。
