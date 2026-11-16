# 行政資料を優先したA・人手Tの証拠監査（2026-11-13）

成果文書：

- `docs/research/toc_delivery_a/A_GOVERNMENT_EVIDENCE_AUDIT.md`
- `docs/research/toc_delivery_a/A_METHOD_AND_HUMAN_T_EVIDENCE_DECISION.md`
- `docs/research/toc_delivery_a/A_GOVERNMENT_EVIDENCE_REGISTER.csv`

リポジトリ直下から、保存済み原資料を使って実行する。

```bash
python -B output/toc_delivery/a_government_evidence_20261113/build_review.py
python -B output/toc_delivery/a_government_evidence_20261113/validate_review.py
```

Python標準ライブラリを使用。原資料PDFテキスト生成とページ画像にはPopplerの`pdftotext`/`pdftoppm`を使用した。独立な数値換算・原文との一致・対象規模の取り違え防止・CSV/JSON一致・既存成果保全を検査する。アルゴリズムの回帰テストや本実験ではない。

`SOURCE_MANIFEST.json`は取得URL、最終URL、UTC取得時刻、バイト数、SHA256、失敗理由を保存。既存調査から再利用した資料はその以前の取得記録と相対パスを保持する。原資料のHTTP成功と本文確認成功は区別する。厚労省job tagはローカルHTTP200でもチャレンジ画面だったため、Webツールでの原本文閲覧を`WEB_VERIFICATION_NOTES.json`に要約した。全文HTMLを保存できたという記録ではない。

経産省の複数ページは403。取得したLOZI掲載の経産省全文PDFはコピーとして分類し、経産省原URLとのバイト一致を確認したとはしない。国交省側で取得した会合資料内の経産省事例集抜粋も保存したが、これを全文PDFと同一ファイルに見せない。最新版判断基準ver1.1の未読と、農水省v1.0を実際に読んだことも分離する。

`sources/*_page*.png`は局所ページの原画像確認用。国交省ITツールp.11（PDF p.7）の7〜8時間、三浦市の本文8時間と図5〜6時間、玉野市の配車20分と受付5分の区別、配車計画システムの工程図を目視確認した。WebのPDFスクリーンショット機能は失敗したため、保存PDFをローカル描画した。OCR推計による新しい数値は生成していない。

`fetch_sources.py`は最初に調査したURL群の取得補助で、再取得は不要。後から追加取得したURLも含む完全な所在は`SOURCE_MANIFEST.json`を参照する。取得補助の再実行はマニフェストを初期集合で置き換えるため、監査の再現では上のオフライン手順を使う。ライブ再調査を行う場合は別ディレクトリへ取得する。

`PRESERVATION_BEFORE.json`の98既存ファイル（A文書、設定、共通コード、凍結需要8ファイル、既存パイプラインCSV、README/.gitignore）をハッシュ比較する。旧結果全ファイルを今回新たに走査したとの主張はしない。今回追加した文書・調査出力以外へ書き込む処理はない。実験・パイプライン全体の保全記録は従来の`ad_pipeline_20261112_route_v2/PRESERVATION_RESULT.json`等に保持する。

`ADOPTION_DECISION.json`は研究資料としての採用範囲を固定する新規ファイル。既存Aの計算係数・運行条件・ルート時間参照設定は変更しない。`full_A_human_T_s`は全規模null。行政掲載の7〜8時間は外部参照であり、S1の測定値に置換する設定ではない。

最終オフライン検査は264/264合格、保全対象98/98一致、凍結需要8/8一致。初回はG05の計測範囲欄の空欄を1件検出したため、「原PDF未確認、索引の工程名以外不明」と記入した。失敗記録は`VALIDATION_INITIAL.json`に保持した。値や研究設定の修正によって通過させたものではない。

問い合わせ、人手実験、B〜Dの監査、本実験、commit/pushは実施していない。
