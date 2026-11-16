# 日本郵便A：取得可能性監査の再現

2026-11-11、JP-A-acquisition-v1.0。指定3文書のみ新規作成。
過去のA採点文書・参照JSON、研究コード・設定・凍結需要・過去結果・未コミット変更を保全する。

一次資料35件をGETで取得。原HTML/PDFのURL、取得UTC時刻、応答、SHA256と本文hashはSOURCE_MANIFEST.json。
PDF抽出はpdftotext -layout、HTMLはscript/styleを除いて抽出した。
東京都TDPF資料はwebツールではサイズ制限のため全文を読めなかったが、元PDFを直接取得し、
PDF p.164の走行規模推計をPNGに描画して目視した。原PDF16,643,151byteの全体hashを保存した。
NTT資料はShift_JISだったため初回UTF-8抽出で文字化けを検出し、同じ原バイトからCP932で再抽出した。
初回抽出と修正記録を保存し、独立検査で日本語原文との一致を確認した。
CBcloudのフォームは公開ページの存在/タイトルまで確認でき、動的な入力本体は未確認として残す。

保存した資料に対するオフライン再検証：

```bash
PYTHONDONTWRITEBYTECODE=1 python output/toc_delivery/a_japan_post_acquisition_20261111/build_register.py
PYTHONDONTWRITEBYTECODE=1 python output/toc_delivery/a_japan_post_acquisition_20261111/validate_acquisition.py
PYTHONDONTWRITEBYTECODE=1 python output/toc_delivery/a_japan_post_acquisition_20261111/verify_preservation.py
```

validate_acquisition.pyは出典hash、必要metadata、5種類の取得判定、Tの単位換算、
W実証の到着/出庫の境界、原データへのアクセス未確認、3段階の採否、文書リンクと字数を255項目で確認する。
これは255件の独立した実運行測定ではなく、非公開原記録の検査や提供承諾を意味しない。
日本郵便への未送信文案は件名込み931文字で、本文2000字制限を満たす。
所属・氏名・研究責任者等の角括弧は実行する研究者が記入し、記入後に字数を再確認する。

fetch_sources.pyは公開資料の取得補助の記録であり、オフライン再検証では実行しない。
ウェブ原文は更新され得るため再取得時は別の証拠ディレクトリへ保存し、既取得原本を上書きしない。
現在の35件は追加探索分を含むため、保存済みSOURCE_MANIFEST.jsonを全件の正本とする。

取得可能性はPUBLICの説明資料とUNVERIFIEDの原記録を分けて読む。
問い合わせ窓口をREQUESTABLE、個別協議の推測をNEGOTIATION_REQUIRED、無回答をUNAVAILABLEにしない。
J01の既存T参照は維持し、D/W/共通Tはnull。Level 1のTのみCONDITIONAL GO、3指標一式とLevel 2/3はHOLD。

依頼書案と計画は作成済み。フォーム送信、メール、提供申請、契約、大学への連絡、
原記録受領、S1〜S3実験、commit/pushは実施していない。
開始時47,708既存ファイルを全て再hashし、凍結8ファイルと旧成果の意図しない変更がないことを確認する。
