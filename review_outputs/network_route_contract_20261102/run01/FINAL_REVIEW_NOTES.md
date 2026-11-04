# 最終独立レビューの記録

1. 元データとの一致：既存875成果物の開始hash、最終全参照hashを照合。36,800参照を全4,987候補の分類へ結合。数値・payloadSHA・主キー検査はFINAL_REVIEW_CHECKS.csv。
2. 道路版：N0/N1の差分・958無効端点を保持。新道路で旧目的値が成立するとの主張なし。N2未構築。
3. B同一性：元edge直接回収2,323と旧cache同一性HOLD2を分離。35一致／2保留、134区間中133PASS／1HOLD。距離だけの一致を経路一致と扱わない。
4. 未確定入力：partial2,662件に完全IDなし。networkblockedは完全入力にも保持。
5. 配送完了：endedを完了とせず、連続停車証拠を伴うモデル完了を定義。native監視接続HOLD。
6. B質量：主massはnull。旧B0=1,155kgは候補のみ、PEkg換算なし。
7. Cとの分離：T08/T09をB実証に転用せず、T09完成183HOLD／対向1FAILと量子材料未実証を保持。
8. 除外防止：全4,987候補・36,800参照・未保存13,249脚と制御1HOLDを残す。全候補のnetworkblockも列で保持。
9. 保全：元コード・入力・結果・FREEZE・原稿を変更せず、新レビュー領域のみ追加。FINAL_SOURCE_HASH_CHECK.csvとGIT_DIFF_FINAL.patch参照。
10. 再実行：コード、ログ、入力source/hash、raw元経路、公式資料cache、出力manifestを保存。外部保全が必要な限界を明記。地域試行や全件実験は実行していない。

## レビューで修正した事項

制御134区間のうち元edge欠落1区間が中間native距離照合台帳から落ちていた。分母134と明示HOLD1を復帰した。修正前code/CSV、修正diffをrevisionsに保存し、review_recovery.pyとfinal_review.pyを再実行して不一致0。元CSVは変更していない。

経路回収初回は同一parquet/XMLの反復hashによる遅延で中断し、hashキャッシュを適用して再実行した。初回ログを保持。科学式・保存結果・分類受入条件の変更なし。この効率修正前codeの完全snapshotは未保存で、遡及して保存済みとは主張しない。

N1の8link対は方向付きであり、順序を除くmovement対は7。この単位を両記した。追加来歴検査では欠落旧schemaにlane-mode/hash欄がないことを明示し、後期lane-routerのhash不一致と誤解しない表現にした。

すべてのFAIL/HOLDを隠さず、最終ゲートはA/BともNO-GO。これはfixture不一致があるという意味ではなく、地域道路・比較可能性・nativeイベント計測・B質量の科学受入が未成立という判断である。
