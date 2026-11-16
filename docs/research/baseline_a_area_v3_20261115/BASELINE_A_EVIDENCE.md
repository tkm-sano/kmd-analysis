# 公開資料による業務・実績の証拠台帳

追加調査日は2026-11-15である。利用者の指示により公開資料だけを使用し、事業者への連絡は行っていない。既存の[証拠台帳v2](../baseline_a_redesign_20261113_v2/BASELINE_A_EVIDENCE.md)と[訪問順データ監査](../baseline_a_sequence_validation_20261114_v1/DATA_AUDIT.json)を保全し、今回の判定へ参照する。新規原本・hash・取得失敗は[sources/SOURCES.json](sources/SOURCES.json)、[追加取得記録](sources/ADDITIONAL_SOURCES.json)、[Modena取得記録](sources/MODENA_HEADER_ACQUISITION.json)に保存した。本文閲覧だけの資料をローカル原本保存済みと表示しない。

## 業務の一次資料

|主体・資料・公開日|該当箇所・確認した業務|数値の性質・本研究への適用と採否|
|---|---|---|
|佐川急便 [集荷から配送までの流れ](https://www.sagawa-exp.co.jp/customer/send/guide/beginners/)、公開日未確認|STEP4/7。担当エリア、エリア仕分け、担当ドライバーによる積込|定性的な公式業務説明である。区域配送構成の参考とするが、営業所担当圏と車両担当区域を同一視しない。角度分割・FCFS・最大2便を裏付けない|
|佐川急便 [ラストワンマイルを担うセールスドライバーの業務負担低減](https://www.sagawa-exp.co.jp/about-csr/column/article_02.html)、2024-04-01|本文のスマート集配・夜積み。担当者の積込時の順序判断、AIによる提示、夜勤者の積込|公式説明である。人手とシステム双方の存在を確認する。荷台6区画を容量60の根拠にしない。全便を朝に1800秒積むモデルとの一致は未確認である|
|日本郵便 [AI配達業務支援の試行](https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02.html)、2020-06-15|[本文](https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02_01.pdf)p1、[別紙](https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02_02.pdf)pp1–2。積込・順序提示・配送情報管理|約200局の一部へ試行予定という計画であり、その数を計画規模や観測済み実績にしない。具体的な数式・順序アルゴリズムは未確認である|
|ヤマト [もっと知りたい！宅急便](https://www.yamato-hd.co.jp/facilities/kansai-gateway/pdf/childpamphlet_jp.pdf)、表紙2026.2|PDF pp5–6。着営業所の配達エリア別仕分け、届け先情報からのルート自動設定・携帯端末|教育用の公式業務説明である。区域・末端拠点という構成を採用する。現在の実務をすべて人手最近隣と説明することはできない|
|厚労省 [job tag 宅配便配達員](https://shigoto.mhlw.go.jp/Occupation/Detail?occupationId=483)、公開日未確認|「どんな仕事？」。区域ごとの割当、概略の順序判断、帰所後に荷物があれば再積込|公的職業説明である。複数便の構成は支持するが、上限2便、便容量60、当該拠点の実施頻度は未確認である。前回直接保存HTMLはアクセス対策画面のため本文原本の扱いにしない|
|積運 [業務紹介](https://recruit.sekiun.co.jp/interview/works/)、公開日未確認|京浜トラックターミナルを掲げる事業者。管理者の概略ルートと担当者の変更、区単位の担当、他車分の補完|2tロング、平均7〜8件、企業・病院・学校中心との業務説明である。地元資料だがB2B中心であり、研究ToCの距離・件数校正には不採用である|

上記の詳細な原本記録は前版台帳とそのsourcesに残す。対象事業者の区域境界、需要による区域変更条件、誰が何時に車両別割当を決めるか、現在の具体的順序計算、便の実頻度、当該ToCバース予約・優先度は未確認である。

## 定量資料と追加候補

|ID・主体|資料・URL・公開日・該当箇所|確認した事実・値の性質|適用範囲と採否|
|---|---|---|---|
|Q01 Amazon/MIT|[公開データ](https://registry.opendata.aws/amazon-last-mile-challenges/)、2021 challenge、[論文](https://doi.org/10.1287/trsc.2022.1173)、[schema](https://github.com/MIT-CAVE/rc-cli/blob/main/templates/data_structures.md)。route/actual/travel-time項目|2018年米国の配送先集合・zone・実績順・履歴平均の移動時間である。今回校正32/検証26。行列は実運行経過秒の観測値ではない|訪問順成分の外部校正・独立検証に採用する。対象ToC拠点の全車両D/W/Tの校正としては不採用である。公式3072に対し原本3052の差の理由は未確認である|
|Q02 SGシステム/JILS|[平成28年度次世代物流システム構築事業報告書](https://www.logistics.or.jp/jils_news/05_IoT.pdf)、2017-03-15。PDF pp31–32、東京の図はp32（印刷31）|大田区大森北/南/西/東のクリーニング店22件を配達すると仮定し、不慣れな運転者の地図走行と別担当者の宅配ナビ走行を比較した。東京の地図121分/23km、ナビ94分/16km。模擬走行の測定である。本文には最寄り地点の検索について説明がある|地域と近隣選択の類例として採用する。ToCの通常一日実績、全車両総D、計画Tではない。23kmや16kmをN/22や車両数で倍率換算しない。原本と[図の確認画像](sources/SGS_TOKYO_PAGE32.png)を保存した。報告書の今後の効果試算と先行実証を区別する|
|Q03 佐川急便|[セールスドライバーの歩数検証](https://www.sagawa-exp.co.jp/about-csr/column/article_33.html)、2025-02-06。観測2025-01-10、検証条件・結果|都内1名のトラック13km/日、郊外1名148km/日は当日測定。都内通常約20km/日という説明とは別である。集荷を含む|都市の参照値として残すが、地点数・便数・区域が不明でありToC専用校正・全車両Dの検証へ転用しない|
|Q04 日本郵便担当者/オプティマインド|[導入事例](https://loogia.jp/cases/nihonyubin/)、2021年時点、厳密な公開日未確認。導入前課題・利用状況|個別の紙地図順序作成で熟練5〜10分、新人30〜60分、支援後新人10〜15分との公開インタビューである|補足的な人手時間の記述に限る。N/V/同時人数/測定分布がなく、S1〜S3の全体T_human参照には不採用である。プログラム秒へ換算しない|
|Q05 国交省|[荷待ち改善事例集](https://www.mlit.go.jp/jidosha/content/001487579.pdf)、厳密な刊行日未確認。PDF pp258–259（印刷234–235）|静岡の紙製品/古紙、製造工場・倉庫運行の積込待ち平均140→97分。行政掲載の事例値である|荷待ちと作業の区別に参照する。末端ToC拠点のreadyと一致せず、Wへの校正は不採用である|
|Q06 大阪労働局|[ベストプラクティス企業との意見交換](https://jsite.mhlw.go.jp/osaka-roudoukyoku/content/contents/002484671.pdf)、2025-12-05、会合2025-11-11。PDF p2の締切/予約、p6の効果|鴻池運輸・ダイキンの物流で、荷物の出荷締切、帰庫車両と荷物の準備、予約管理等を扱う。積込時間平均50分短縮と拘束時間48分短縮の説明は積込待ちの観測時間そのものではない|FCFS以外の運用もあり得るという業務上の参考である。ToC配送のバース待ち分布・AのWへ使わない|
|Q07 ヤマト総研|[納品待機時間短縮スキーム](https://www.yamato-hd.co.jp/news/h29/h29_28_01news.html)、2017-06-29。§2–3|先着順の納品に待機が生じ、予約・RFID・優先入庫のスキームを説明し、ライオンとの実証開始予定を公表した。定性的説明・実証計画である|納品先の入庫/荷卸であり、当該ToC営業所の出発積込とは異なる。FCFSの普遍的根拠や対象Wの校正には不採用である|
|Q08 Vraniほか|[Delivering data](https://pmc.ncbi.nlm.nih.gov/articles/PMC12206052/)、2025-06-07、doi:10.1016/j.dib.2025.111762。Abstract/Specifications/Methods、[Zenodo](https://zenodo.org/records/15310106)|Athensの3PL医薬品配送9日、60〜85地点。実注文を取得する一方、距離km・時間分の全対行列はAPIで生成した。時間窓や作業条件も記載される|実要求を使うVRP資料だが、実走行arc・積込ready/start/endを今回確認した公開項目から得られない。ToC全体の実績照合・D/W/T校正には不採用である。生成行列を実走行距離と呼ばない|
|Q09 Masola/TRACE|[Modena GPS dataset](https://zenodo.org/records/21717592)、2026-07-31。Description/Files、[orders CSVヘッダ](https://zenodo.org/records/21717592/files/orders_export%20%289%29.csv?download=1)|Modenaの配送車両位置・荷物・時間窓との説明、CSV2件を確認した。API/先頭の直接取得は403、previewは列本文なしであった。追加のWeb取得ではorders CSVのヘッダを閲覧でき、出発/到着座標、車両ID、Delivered_at、時間窓等を確認した。一方、GPS CSVはWeb取得容量上限で本文未取得である|ordersの閲覧ヘッダには明示的なload_ready/load_start/load_endは見当たらず、Delivered_atやcreatedAtをそれらと同一視できない。GPS列・ライセンス詳細・積込準備時刻の定義は未確認である。データ一式に列が存在しないと断定せず、GPS滞在をWと見なさない。今回の校正には未使用である|
|Q10 経産省|[regular_report_wholesaler.pdf](https://www.meti.go.jp/policy/economy/distribution/regular_report_wholesaler.pdf)、公開日・本文タイトル未確認|報告書の候補として検索したが直接取得403で本文未確認である|検索抜粋の待ち/作業数値を実測値として採用しない。未取得として記録する|

## 計算規則の分類

|規則・主張|分類|根拠と限界|
|---|---|---|
|区域別仕分け・担当配送の業務構成|EVIDENCED|佐川・ヤマト・job tagの説明である。具体的境界と車両数は未確認である|
|座標から地理的区域を作る研究方針|SUPPORTED_INFERENCE|区域業務を近似する理由はあるが、実区域との一致は未検証である|
|角度同数分割と開始0度|ASSUMPTION|再現用規則である。事業者採用の証拠はない|
|負荷proxyによる最大V回の境界移動|ASSUMPTION|研究規則である。実務の再割当条件は未確認である|
|座標の最長軸中央値分割、葉6/12/24|ASSUMPTION|新しい研究候補である。公開zoneとの一致も改善も確認できていない|
|区域優先倍率1.5/3/無制限|ASSUMPTION|研究候補である。今回の自動区域候補は採用を支持されなかった|
|人/システムが訪問順を作成する業務|EVIDENCED|複数の公式説明がある。事業者・時点により自動化の範囲が異なる|
|近い次地点を選ぶことの合理性|SUPPORTED_INFERENCE|Q02の模擬走行は類例であるが、通常の対象ToC業務とは異なる|
|対象ToCの有向道路距離最近隣そのもの|ASSUMPTION|米国時間行列の検証は対象の道路距離検証ではない|
|帰所し再積込する業務構成|EVIDENCED|job tagの職業説明である|
|容量60・最大2便・作業120秒・積込1800秒・勤務枠|ASSUMPTION|共通の研究条件である。公開実績による校正ではない|
|有限バースの資源制約|SUPPORTED_INFERENCE|物理資源をモデル化する理由はある。当該ToC拠点の共用状態は未確認である|
|ready順FCFS・最早空きバース|ASSUMPTION|対象施設の運用資料は未取得である。納品予約の他業務事例はFCFSを立証しない|
|A全体が京浜・大田区ToCの実績を代表するという主張|UNSUPPORTED|適格な対象全体D/W/Tの照合が不足している|

## 未取得項目と校正可否

対象または適格な国内類似ToC拠点について、同一需要・割当・便に対応する全車両D、readyから積込開始までのW、一括計画工程が明示された人手Tは未取得である。適格な校正/独立検証の件数は各指標0である。Amazonの訪問順成分は32/26であり、この0件という全体D/W/Tの状態と混同しない。異業務の資料を合成して単一事業者のD/W/Tにしていない。

不足をコード実行・任意倍率・任意許容幅で補わない。今回の検索範囲で得られなかったという結論であり、世界の公開資料に存在しないと証明したものではない。
