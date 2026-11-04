# 図表の修正前後差分と再検証

修正はすべて今回のレビュー生成コード・画像内に限る。元CSV・研究コード・DOCXは変更していない。

```diff
- font.family = Droid Sans Fallback
+ font.family = [DejaVu Sans, Droid Sans Fallback]
- coverage ylim = (0,105)
+ coverage ylim = (0,135)
- mechanism xticks = [1,6,12,13,18,24,25,30,36]
+ mechanism xticks = [1,6,13,18,25,30,36]
- histogram annotation on bar area
+ redundant annotation removed; caption retains scope
+ svg.hashsalt = THESIS_20261102
+ SVG Date=None; PDF CreationDate=None, ModDate=None
```

元画像のhashを*_BEFORE_HASHES.jsonに残した。最終PNGを10点閲覧し、変更した3図を再度閲覧した。メタデータ固定後のPNGは全10点で同一hash、SVG/PDFを含む全30ファイルは描画再実行でbyte一致した。修正は数字・日本語の可読性と組版・再生成の安定性に関するもので、元数値・集計条件の変更ではない。
