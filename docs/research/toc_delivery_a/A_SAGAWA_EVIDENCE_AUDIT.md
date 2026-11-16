# 佐川急便・従来人手配送計画の一次資料監査

2026-11-12。版：`Sagawa-manual-A-20261112-v1.0`。最新の改善前限定指示を優先する。
証拠は`output/toc_delivery/a_sagawa_relative_20261112/`に保存。
ディレクトリ名は直前の相対値調査で作成された履歴であり、現行の採用対象は改善前人手計画である。

## 1. 確認範囲と取得方法

README、11/8研究計画の既存抽出監査、A採用・参照値・適合性評価・日本郵便取得計画・公開資料限定方針、現行共通条件v1.1を確認。
最新指示を旧DOCXの代理A、日本郵便A、指標別混成参照、直前の相対値案より優先する。
共通条件・研究計画本体・README・アルゴリズム・凍結需要・既存結果は変更しない。
`WORK_PLAN.md`に着手前計画と追加指示による変更を保存した。

|資料ID|一次資料・確認箇所|確認結果|
|---|---|---|
|OPTIMIND_RELEASE|[2021-10-04共同発表](https://www.optimind.tech/news/ルート最適化システム「loogia」を佐川急便で導入を/)、検証条件・結果|人手の順序決定、期間、個数、指標境界。改善前の絶対値や生ログは見つからない|
|OPTIMIND_CHART|[結果画像](https://www.optimind.tech/wp-content/uploads/cms/png2.jpg)|9個の削減量ラベル。before/after絶対値・百分率・軸はない|
|OPTIMIND_OPERATION_IMAGE|[運用イメージ](https://www.optimind.tech/wp-content/uploads/cms/png1.jpg)|8:30出社/9:30出庫、1件目/80件目。Tの境界・実住所・道路経路ではない|
|PRTIMES_RELEASE/CHART/OPERATION|[同社配信の原リリース](https://prtimes.jp/main/html/rd/p/000000012.000034529.html)、結果・運用画像|別配信先でも同じ表・イメージ。独立した実測ではない|
|SAGAWA_DISTANCE|[2025年歩数検証](https://www.sagawa-exp.co.jp/about-csr/column/article_33.html)、内容・実測値|13kmの観測は保存。人手導入前とは未確認|
|KANTO_CASE|[指定PDF](https://wwwtb.mlit.go.jp/kanto/jidou_koutu/kamotu/kamotu_kyougikai/date/kanagawa/12/4.pdf#page=60)、第60/61ページ|別の拠点間輸送、26分等の改善前平均。W/Tの取り違えを排除|
|MLIT_CASE_REPRINT|[国交省再録](https://www.mlit.go.jp/jidosha/content/001487579.pdf#page=338)、第338/339ページ・印刷314/315|上記事例を別PDFの画像と本文で照合。新たな母集団ではない|
|LOOGIA_CASE_INDEX|[導入事例一覧](https://loogia.jp/cases/)、佐川急便へのリンク|独立の詳細ケースではなく、上記公式発表へ誘導|
|SG_RELEASE_REDIRECT / SAGAWA_RELEASE_SHELL|[SGの旧URL](https://www.sg-hldgs.co.jp/newsrelease/2021/1004_4840.html)、[佐川の旧URL](https://www2.sagawa-exp.co.jp/newsrelease/detail/2021/1004_1749.html)|今回のGETでは前者はニュース画面、後者はJS案内。HTTP200だけで本文を取得済みとしない|
|SG_UTOKYO_FIELD / UTOKYO_PROJECT|[SG実証報告](https://www.sg-hldgs.co.jp/hikyakulabo/archive/detail/202203_02.html)、[東大](https://www.u-tokyo.ac.jp/adm/uci/ja/projects/region/project_00075.html)|実績利用は確認できるが、2018学内/2019シミュレーション/2020横須賀はLoogia8月実証と別。改善前D/W/Tの穴埋めにはならない|
|PALTAC_REPORT|[同社統合報告2023](https://www.paltac.co.jp/tomorrow/pdf/backnumber_2023.pdf)、待機削減記事|佐川との提携記載だけではPALTAC全体の入荷待機を佐川人手ToCと同定できない。不採用|

公開GETのみ実施。ログイン、フォーム送信、連絡、非公開記録の取得はしていない。
原本URL・リダイレクト後URL・取得日時・バイト数・SHA256は`SOURCE_MANIFEST.json`。
権利表示を保持する。公開閲覧できることを、運行生データのオープンライセンスや自由な再配布許諾とは見なさない。
PDFの生成日時を計測日と見なさず、正確な対象日・母集団・取得装置の不足は残す。

## 2. 原図読取と照合

1. 保存した結果JPEGを原寸で視認。行はルート組み/配送業務/走行距離、列は担当/代走/新人・応援。
2. 分・kmのラベルを転記。数値軸・分母・before/after系列がないことを確認。矢印の画素長による推定は行わない。
3. PR TIMESの原配信画像を別途取得・視認し、9ラベルを照合。過去監査の保存JPEG・転記とも一致する。
4. KANTO_CASEの第60/61ページを`pdftoppm`でPNG化して視認。図中文字を含め26分・積込180/229分等を転記。
5. 同じ事例の再録PDF第338ページ画像と、第339ページの`pdftotext`による本文を照合。
6. 時間の合計は別の算術表現で再計算し、合わない部分も結果として保存する。

別配信・再録との照合は**抽出の安定性**の確認であり、別研究者による追試や独立した運行実測ではない。
画像表の数値は公表ラベルの転記で、軸からの推定値ではない。原資料の丸め幅・標本誤差は未公表。
OCRは環境に実行器がなく、追加取得も完了しなかったため使用していない。OCR成功として記録しない。
本文抽出の初回はbs4がなく失敗したため、標準ライブラリHTMLParserに切り替えた。原資料の補完や加工はしていない。

## 3. 行政図表の整合しない箇所

出庫16:35→翌8:15=940分。表示された運転4欄340分、待ち4欄144分、荷扱い4欄501分の和は985分。
差は45分。荷積み待ち26+積込180=206分も、木更津17:00→20:00の180分と一致しない。
鴨川の荷卸し待ち20+荷卸し37=57分は、6:45→7:05の20分と一致しない。
集計対象の違い・平均処理・重複などが解消していないため、整合する秒単位の便ログへ変換しない。
26分二欄の単純合計52分も、研究Wとして採用しない。
再録の検索用テキストには運転2時間20分を12時間20分とする誤読もあるが、原画像では2時間20分。
検索紹介文や自動抽出だけを確定根拠にしない。

## 4. 調査限界と再現手順

探索語・範囲・取得失敗と再試行は`SEARCH_LOG.md`に保存する。
検索で見つからないことを不存在・提供不可と断定しない。
小さい差分表を高精度化しても、記載されていない分母・実経路・積込時刻は復元できない。
本調査では大規模配送計算や新しい人手計画の作成を実行していない。

```bash
python -B output/toc_delivery/a_sagawa_relative_20261112/validate_manual_baseline.py
```

原本hash、リンク、JSON/CSV/文書、単位換算、逆算拒否、誤ったA採用の排除、旧文書本文・既存成果の保全を検査する。
結果は`VALIDATION_RESULTS.json`と`PRESERVATION_RESULT.json`。これは証拠と採用判断の監査であり、未取得の運行値の検証ではない。
