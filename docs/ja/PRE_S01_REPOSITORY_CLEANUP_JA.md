# S01開始前のrepository cleanup記録

## Cleanup summary

2026年9月22日に、S01開始前の作業領域を監査した。科学的成果物の整理を目的とした大量削除は行わず、参照されていない再生成可能なPython bytecodeだけを個別に削除した。

| 項目 | 結果 |
| --- | ---: |
| 棚卸し対象ファイル | 15,443 |
| cache候補 | 836 |
| 削除 | 33 |
| archive移動 | 0 |
| 保持したcache候補 | 803 |
| 既存ファイルの保持総数（棚卸し対象−削除） | 15,410 |
| 削除対象の論理サイズ | 746,815 bytes（約0.71 MiB） |
| SHA256一致を確認した保護対象 | 11,816 |

開始HEADは `49efad3cbba16344c911e3e26179bdbefb915c85`、branchは `main`、作業ツリーはcleanであった。科学コードのvalidated baselineは `6ccbadbd42bdad6c95e22f7420aff6ee787c8997` である。その後の既存変更は日本語研究ガイドの追加と体裁調整である。

棚卸しはGit metadata、`.conda`、`.local`、`.venv`、`node_modules`、symlink先を除外した実ファイルを対象とした。依存環境を削除して容量を減らす作業は行っていない。ignored一覧もローカル監査記録へ保存した。削減量はファイル内容の合計であり、NFSの割当済みblockやGit履歴の縮小を意味しない。

## Deleted

[A分類の削除一覧](pre_s01_repository_cleanup/DELETED_FILES.csv)にpath・理由・サイズ・SHA256を保存した。全件が既存policyでignoredの `__pycache__/*.pyc` であり、対応する `.py` の存在を確認した。tracked fileの削除は0件である。

10,030件のコード・Markdown・manifest・JSON/CSV・Notebook・設定・shell script・patch等を検索した。cacheの具体的なファイル名またはpathが見つかった候補は保持した。削除直前にも各ファイルのhashを再確認した。再帰的な削除、reset、git cleanは使用していない。Git管理外cacheのローカル削除自体はpushされず、Gitには判断の記録が残る。

## Archived

今回のarchive移動は0件である。[ARCHIVE_MANIFEST.csv](pre_s01_repository_cleanup/ARCHIVE_MANIFEST.csv)はヘッダーのみである。過去のSTOP記録やpatch、manifestは参照・provenanceを保つため元のpathで保持した。安全に移動できるB分類は確定しなかった。

## Preserved intentionally

[保持したcache候補](pre_s01_repository_cleanup/PRESERVED_CACHE_CANDIDATES.csv)は803件である。このうち163件は元ソースが現作業ツリーにないためD分類として原位置で保持した。残り640件は参照がある等の保守的な除外対象である。用途不明のものを削除・移動する判断には進んでいない。

以下はC分類として保持した。

- scientific source、tests、Candidate A、QUBO、comparison freeze、seed、ledger、Uniform結果。
- Structured v1〜v6、S01 STOP記録、manifest・hash監査、raw results、Notebook、classical references、road-network成果物。
- [日本語研究ガイド](VRPTW_TO_EVRP_RESEARCH_GUIDE_JA.md)を含む既存docs。
- Git stash 2件とv5の `PRESERVED_UNRELATED_WORK.tar.gz`。apply/pop/dropは行っていない。
- 大容量のCityGML ZIP（最大約544 MB）、OSM PBF/XML、過去のroad-network比較データ。似た名前や同じサイズは不要の根拠にしていない。
- 専用ledger `.lock`。空ファイルであっても相互排他の対象であり削除しない。

`.gitignore`はcache設定が既にあるため変更していない。Notebook outputのstrip、科学的内容の変更、Markdown参照先の移動も行っていない。

## Reproducibility check

[検証結果](pre_s01_repository_cleanup/VALIDATION_SUMMARY.json)に記録した通り、tracked files・source・R23/R24成果物の保護対象11,816件のSHA256は前後一致した。QUBO、Candidate A、freeze、v4/v5/v6、Uniform resultsを含む。さらにv6のartifact manifest、runtime dependencies、comparison reference authoritiesを既存hashと照合した。

ledgerは前後ともscientific circuits **363**、shots **743,424**、reserved **0**である。ledger SHA256は `7bd0ae76a1cfb79bfd00fcc8da53d140483f5ba923dd8f72549312f2d4688ef6` である。今回のscientific circuits・shots・optimizer evaluations・backend/sampler execution・ledger increment・reservationはすべて0である。

direct-build 22件とread-only ledger回帰4件の計**26 tests PASS**を確認した。Uniform full/initial builder呼出しはいずれも0、Candidate A入力制限・state identity記録・variable order・shared body・freeze・budget projectionを検証した。backend・sampler・optimizer・persistent ledger commitにはhard guardを適用した。新たなstatevector samplingやNFS concurrency/reservation試験は行っていない。既存v6の試験成果物を再生成せず保持した。軽量repository auditは別途4 testsを実行した。

ローカルの詳細監査は `reproducibility/outputs/traffic_simulation/r24_vrptw_structured_initial_state/20260922_pre_s01_repository_cleanup` に保存した。ここには初期Git状態、ignored一覧、候補と参照元、保護hash一覧、テストログ、大容量上位25件が含まれる。このdirectoryは既存runtime-output policyによりGit管理外である。Git管理するのは本報告と隣接manifest・検証summaryのみである。

## Next task

次のscientific taskは **S01：N003 WIDE × 3 repetitions controlled scientific launch** である。今回S01は開始していない。cleanup後のcommitは科学設定を変更しないが、実行開始時にはそのHEADを記録してfresh gateを改めて実施する必要がある。S02以降へ自動進行しない。
