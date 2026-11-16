# 出典と取得範囲

確認日は2026-11-15である。一次資料の本文・要旨・著者実装を用いた。検索結果に現れた第三者要約・自動生成解説・無関係なGitHubリポジトリは判断根拠に採用していない。本文を取得できなかった部分は未確認として扱う。

|ID|資料・公開時期|確認箇所と根拠|保存・制限|
|---|---|---|---|
|L01|[Cookほか正式論文](https://pubsonline.informs.org/doi/10.1287/trsc.2022.1185)、online2022-11-08、巻号2024|Abstract/History/Acknowledgments。単一ルート、実績からの制約、公開MITコード、競技版からの改良|Web本文を閲覧した。保存したCOOK_REPORT_2021.pdfは別の2021技術報告である|
|L02|[Cook著者の方法説明](https://www.math.uwaterloo.ca/tsp/amz/code.html)、厳密な公開日未確認|Local search/Super clusters/The big picture。区域階層と制約、著者コードへのリンク|COOK_CODE.htmlを保存した。記載の短時間実験は当該機材・当該データでの結果である|
|L03|[Cook技術報告](https://www.math.uwaterloo.ca/~bico/papers/jptreport.pdf)、2021競技報告|冒頭と方法。固定された担当先の実績順を模倣する課題|PDFとpdftotextを保存した。学習側1107例の成績を独立保留評価と混同しない|
|L04|[heldstephan/jpt-amz](https://github.com/heldstephan/jpt-amz)、取得時default main|README、LICENSE.txt、model_build.sh、model_apply.sh、scripts/build_TSPLIB.py|5ファイルを保存し、Git blob SHA1と一致確認した。branch全体の論文版対応は未確定である|
|L05|[Wu論文](https://arxiv.org/abs/2205.04001)、2022-05-10版、[著者実装](https://github.com/aws-samples/amazon-sagemaker-amazon-routing-challenge-sol/blob/main/README.md)|Method Overview/Folder structure/Quick Start。PPM、rollout、論文LKH/実装OR-Tools、ローカル実行|コネクタでREADMEを閲覧・本文保存した。SageMakerを実行せず、掲載runtimeを本研究へ転用しない|
|L06|[Canoyほか2023](https://link.springer.com/article/10.1007/s10601-023-09363-2)、2023-10-11|§4.2、RD/AD、§5、実験環境。複数車両計画、201日、時系列評価、CPLEX|Webから本文を確認したが、直接取得したCANOY_2023.htmlはHTTP200のClient Challengeであり、論文原本とは扱わない|
|L07|[Canoyほか2024掲載版](https://doi.org/10.1016/j.cie.2024.109932)、2024、[前刷](https://arxiv.org/html/2201.10269v1)、2022-01-25|掲載版書誌/要旨、前刷§4–5。二段階順序生成と重み学習|CANOY_2024.pdfという保存名の内容はarXiv2022前刷である。最終版全文取得済みとは記述しない。最初に試したhtml v2/v3は404でありv1を閲覧した|
|L08|[Dieterほか](https://doi.org/10.1016/j.ejor.2023.04.043)、2023-11-16巻号|出版社Abstract/Introduction。TSPTWでの経路予測・提案の差とコスト|[大学PDF](https://ris.uni-paderborn.de/download/44383/44388/Driver_Behavior_in_last_mile_delivery_EJOR_Final.pdf)はtimeoutで未保存。詳細なコード/データ入手は未確認である|
|L09|[Sun・Arslan正式版](https://doi.org/10.1016/j.trb.2025.103172)、2025-04|正式版書誌・Abstract、前回保存済みCIRRELT2024報告の方法|直接保存は403であり、Web閲覧と前回の報告原本を区別する|
|L10|[Rashidiほか](https://www.sciencedirect.com/science/article/abs/pii/S0968090X25002827)、2025-10|§5.1、§5.2、Data availability。Cook法の比較対象利用、GLS、評価集合|Webで対象節を確認した。直接保存403。Cook実装のcommitや忠実再実行は未確認である|
|L11|[Nourmohammadiほか](https://www.sciencedirect.com/science/article/pii/S0968090X25001056)、2025-05|Abstract、Data availability。多目的CVRPTW、データ共有許可なし|原データを取得・合成していない|
|L12|[Canoy・Guns2019](https://arxiv.org/abs/1909.07893)、2019、[正式版DOI](https://doi.org/10.1007/978-3-030-30048-7_4)|Abstractと後続論文との関係|共通著者の拡張と独立追試を区別する。掲載版と前刷の引用統合は未確認である|
|L13|[大佛・田口2020](https://doi.org/10.3130/aija.85.1877)、2020-09-30公開|Abstract。実配送調査、SD/FCチーム、実経路との比較|前回閲覧原本を保全した。現行条件へ未検証の数値移転は行わない|
|L14|[Arikanほか](https://doi.org/10.1287/inte.2023.0031)、2023-09-26|Abstract。Deutsche Postの実運用、履歴由来の先行制約|原データ/原コード公開場所は今回未確認である|
|L15|[Rijalほか](https://doi.org/10.1111/poms.14051)、2023-11-01|Abstractと§7.1 Benchmark solution。逐次計画と倉庫・輸送統合の比較|当該倉庫は小売補充であり、ToC積込待機の校正に使わない|
|L16|[Xuほか](https://doi.org/10.3390/systems11080412)、2023-08-09|Abstract、問題設定。多勤務日・産業輸送の複数便と資源同期|数理構成の参考に限る|
|M01|[OpenAlex API](https://api.openalex.org/works)、2026-11-15取得|10件のDOI別書誌・著者・cited_by_count・updated_date|OPENALEX.jsonに原レスポンスと取得時刻を保存した。レコードの版を混ぜず、足し合わせない|

今回の検索は目的を限定した追加調査であり、網羅的な系統的レビューではない。査読論文、前刷、著者技術報告、コード、集計サービスを区別した。取得失敗は[ACQUISITION.json](sources/ACQUISITION.json)に残す。直接HTMLのHTTP200は本文確認を保証せず、Canoy2023のClient Challengeは明示的に除外する。

初回のCook README.md/旧master指定・LICENSE指定は404であった。その後リポジトリtreeを確認し、main上のREADMEとLICENSE.txtを取得した。失敗した推測パスを有効な公開物として挙げていない。
