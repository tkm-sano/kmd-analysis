# A資料適合性監査の再現

条件AD-common-20261111-v1.1、A-external-reference-v1.1、採点A-applicability-v1.0。
対象12資料×3指標。点数は本監査の判断で、原データの性能値ではない。

リポジトリルートで次を順に実行する。Python標準ライブラリのみを使う。

```bash
PYTHONDONTWRITEBYTECODE=1 python output/toc_delivery/a_applicability_20261111/inspect_workbooks.py
PYTHONDONTWRITEBYTECODE=1 python output/toc_delivery/a_applicability_20261111/audit_small_data.py
PYTHONDONTWRITEBYTECODE=1 python output/toc_delivery/a_applicability_20261111/build_assessment.py
PYTHONDONTWRITEBYTECODE=1 python output/toc_delivery/a_applicability_20261111/assemble_report.py
PYTHONDONTWRITEBYTECODE=1 python output/toc_delivery/a_applicability_20261111/validate_assessment.py
PYTHONDONTWRITEBYTECODE=1 python output/toc_delivery/a_applicability_20261111/verify_preservation.py
```

新JSON/Markdown生成は本監査の2文書のみを書き直す。既存のA文書/参照JSONを更新する処理は含まない。
旧監査の23項目を含む参照検査を読み込み、新しいE11原資料hashを加えた24項目を実施する。
検証出力は本ディレクトリへ向け、旧証拠出力を変更しない。
最終検証では採点/素点/感度/必須条件/Markdown一致・出典hash・図表の本文との照合・小データ構造を296項目で確認。
これは296件の配送実験や独立した原観測ではない。共通Tの実測でもない。

sources/には国交省PDF3本と抽出文、目視したPDF4ページ、Amazon原論文と台帳/スキーマ、
LaDe原カード/論文、著者GitHubのコネクタ応答、Zenodoメタデータ/配布原ZIP・Excelなどを保持した。
DOWNLOAD_LOG.json、DATA_DOWNLOAD_LOG.jsonは直接取得URL/日時・成否・hashを記録する。
GitHubはコネクタのUTF-8応答を保存したもので、*.txtのhashを元リポジトリのGit blob hashとは呼ばない。
sources内の全保存物のSHA256はA_APPLICABILITY_ASSESSMENT.json.source_artifacts。
取得済みZIP/Excel3本はZenodo公開MD5とも一致する。

工場CSVのコネクタは本文が空だったため、既知のraw URLから最大65536byteのみ直接取得した。
QUEUE_PARTIAL_METADATA.jsonのhashは**先頭部分のhash**であり全量のhashではない。
GB18030で読めた完結247行だけを使用し、全量統計や代表平均を出していない。
openpyxlは利用環境に未導入だったため、インストールせずZIP/XMLへ切り替えた。
Delivering Data論文本文の取得timeoutとブラウザ認証は記録に残し、成功扱いしていない。
補助コードの旧Zenodo IDとREADMEのID差を記録し、第三者ダウンロード/分析コードは実行していない。

保全対象は開始時にhashを記録した47643ファイル。変更を許した既存ファイルはAの3文書と参照JSONのみ。
新規は適合性評価のMD/JSONと本証拠ディレクトリ。
凍結需要・A〜Dアルゴリズム・共通設定・過去実験・README/.gitignoreの既存変更は保全する。
S1〜S3最適化、OD大量生成、実績の創作、commit/push、外部への連絡は行わない。
