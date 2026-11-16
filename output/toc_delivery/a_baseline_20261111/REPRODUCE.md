# A採用判断の検証

採用文書はdocs/research/toc_delivery_a/以下の3 Markdownと参照値JSON。
公式原資料はsources/、取得時刻・URL・SHA256はSOURCE_MANIFEST.json。
ブラウザで読めても直接取得に失敗した丸運は原HTML保存済みとは扱わない。

リポジトリルートで、研究実験を呼ばずに検査する。

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  output/toc_delivery/a_baseline_20261111/validate_reference.py
```

出典本文の値と日付、分→秒の換算、欠測null、S1〜S3へ外挿していないこと、
共同観察でないことを23項目で確認する。事業者の測定原ログの再検証ではない。

原HTML/PDFは直接取得。HTMLは標準ライブラリHTMLParserでscript/styleを除き
テキストを抽出、PDFは`pdftotext -layout`を使用した。佐川2021年の結果画像は
目視で短縮量のみと確認し、D/T絶対値には採用しなかった。JP_CHART.jpgは
担当者写真であり、数値の証拠ではない。証拠の目的を取り違えないこと。

検証時の基準は現行共通v1.1（積込1800秒、作業120秒、準備0秒）。
事業者の参照で設定を変更しない。旧研究計画の代理Aを実績として扱わない。

PRESERVATION_BEFORE/AFTER.jsonは今回開始時に存在した同一ファイル群のhashを
比較する。新規A文書と本証拠ディレクトリだけを追加し、既存コード・設定・
凍結需要・保存結果・README等のユーザー変更は保全する。終了状態と追加差分は
GIT_STATUS_AFTER.txt、TASK_ADDITIONS.patch、FINAL_REVIEW.jsonに保存する。

S1〜S3最適化、Aの代理アルゴリズム、需要生成、事業者への連絡、commit/pushは
この作業にも再現手順にも含めない。
