# ToC配送研究・範囲更新と現状監査

2026-11-08。総合判定：**条件付き完了**。

動力方式を特定しない配送車両へ新研究の対象を統一し、既存の研究計画DOCX、入口、機械可読設定、実装契約へ反映した。未確定値の採択、全体ソルバー、本実験、図の実測結果は未完了である。これらはHOLDと開発タスクへ明示しており、実装済み・実証済みとは扱わない。

## 1. 作業開始時点と調査範囲

- ブランチ：`main`、HEAD：`8605d5412f6af62229a83095c35ab04c8c7dd9b1`。開始時に追跡済みファイルの差分はなく、多数の既存未追跡成果物があった。未追跡を新規作成物と見なさず保全した。
- 作業前の状態・SHA256・サイズは [BASELINE.json](BASELINE.json)。追跡・非除外の未追跡ファイルに、`01_research_design/`、`src/`、`05_src/`、`docs/research/`、`tests/fixtures/`の既存ファイルを加えた21,361件を比較対象とした。`__pycache__`、環境全体、Git内部は対象外。外部の保全領域は読取りだけを行った。
- 適用するAGENTS.mdはリポジトリ・上位ディレクトリの確認範囲では見つからなかった。commit、push、ブランチ削除、checkoutは行っていない。
- README、`docs/QUANTITATIVE_GUIDE.md`、旧設計文書、既存DOCX、公開API、調査フォルダ、保存probe、設定、既存テスト、凍結・配布マニフェストを読んだ。

|領域|確認した実体と判定|
|---|---|
|需要生成|保全領域`relocated/05_src/traffic_simulation/demand/prepare_baseline_demand.py`と旧`baseline_demand.yml`が実在。人口メッシュ按分・全国量換算・最大剰余処理を確認。世帯別Poissonの直接生成器は回復できていない|
|道路・需要|保全領域の`CUSTOMER_DEMAND_39956.csv`、`DELIVERY_POINT_SUMO_MAPPING_39956.csv`を読取り・hash記録。需要39,956行・81,859 PE・182需要グループ、道路対応39,956行を今回確認|
|経路計算|`src/kmd_quantitative/routing/solver.py`は単一車両・固定割当の旅行秒最小化。貪欲・挿入・relocate・有向反転等がある。216 PE、102秒、32,400秒等の旧条件が埋め込まれている|
|QAOA|`src/kmd_quantitative/quantum/`はハッシュ固定の旧Protocol V2と入出力アダプタ。正式保存実行は3・4顧客の理想状態ベクトル方式。後続`review_outputs`には別の保存CPU候補分析もあるが、新研究の全体ソルバーとしては未接続|
|設定|`configs/CANONICAL_CONFIG_INDEX.csv`、旧容量・時間条件、`reproducibility/environment/requirements-quickstart.lock.txt`等は旧研究の参照。新設定へ一括継承しない|
|指標・図|旧`analysis`はMethod×Battery等の保存結果を読むAPI。`review_outputs/thesis_results_interpretation_20261102/run01/scripts/make_figures.py`は旧CSVに依存。新しいD/W/Tの7図を生成するコードとして使用できない|
|テスト|既存API・凍結整合・配布・Notebook契約を確認。新研究の契約テストを別ファイルへ追加|
|再実行境界|旧`build_tables.py`、`solver_probe.py`等は実行すると旧表・probeを書き換える。今回は実行していない。保存JSON/CSVがあることと、全工程の再実行可能性を区別した|

原入力・道路生成の一部がGit非同梱であるため、ローカルで読めた事実を公開cloneだけの再現可能性とはしない。外部実体・hash・計数は [EVIDENCE.json](EVIDENCE.json)。

## 2. 再利用可否

全18項目の具体的な一覧は [ASSET_REUSE.csv](ASSET_REUSE.csv)。分類は次のとおり。

|区分|主な資産|新研究での扱い|
|---|---|---|
|A：そのまま再利用可能|先行調査の証拠台帳・出典と留保、インストール済みOR-Tools|文献根拠・ライブラリとして使用。新研究の測定結果を意味しない|
|B：変更すれば再利用可能|人口配分の数学的処理、需要・道路対応、旧貪欲／局所探索、独立検査、QAOAの構成要素、描画慣例|新しい契約と許可列に合わせて独立実装・接続し、凍結元は改変しない|
|C：新規実装が必要|住宅需要抽出、複数車両・2便・バースの連動、全体計画検証、A〜Dと補助対照、時間計測、7図|[実装仕様のT1〜T7](../../research/TOC_DELIVERY_SPEC.md)へ分解|
|D：新研究では使用しない|旧電池・材料・Controlled-DC・Method×Battery、旧結果、旧一便規模計画、保存`scale_probe.json`の結果値|履歴をそのまま保存し、新研究の入力制約・目的・測定結果へ転用しない|

`scale_probe.json`は100/500/1,000/2,000/3,000先の合成座標・一便・PyVRP試験である。大田区道路、2便、バース待機、量子比較を扱っていない。S3の4,000先を実行した記録でもない。新S1〜S3の成立や量子優位の根拠にはならない。

## 3. 既存需要と新しい需要の区別

旧式は保存設定・コード・ガイドに基づく`5,031,470,000 / 123,802,000 / 365 × 736,652 ≈ 82,023.204937 PE/日`。2020年人口メッシュを行政界面積で按分し、2024年大田区人口へ補正した記録がある。これは今回の一次統計全セルの再確認ではない。

旧世帯別仕様は`lambda_h=82023×r_h/Σr_h`、`N_h,d~Poisson(lambda_h)`、seed20260829。384,353合成世帯→正需要73,547レコード・82,246 PE→建物対応73,200レコード・81,859 PE→39,956集約配送地点という保存記録である。39,956行と81,859 PEは今回需要CSVでも確認した。世帯・注文・PE・停車地点を同じ件数として扱わない。Poisson原生成器と全行順・乱数環境が未回復のため、seedだけの完全再生成を主張しない。

新研究は地域人口比`P_g/ΣP_k`で所定総数Nを最大剰余配分する。全国量からNやPEを再推定せず、旧Poisson標本も黙って流用しない。人口の候補一次資料には[大田区「世帯と人口」](https://www.city.ota.tokyo.jp/kuseijoho/suuji/jinkou/setai_jinkou/index.html)と[東京都の町丁別人口統計](https://www.toukei.metro.tokyo.lg.jp/juukiy/jy-index.htm)があるが、基準日・表・境界との対応は未採択である。旧56区画の定義と新しい人口区画とのクロスウォークも今回同定できず、H02にした。182需要グループを56区画へ読み替えない。

Nの元計画表記は顧客数、一方で作業時間・平均件数は訪問単位の説明を含む。個人顧客と同一建物集約地点は一致するとは限らないためH01にした。整数配分コードはこの判断を代行しない。

## 4. 実際の変更

|ファイル|変更内容|
|---|---|
|`README.md`|新研究の入口・RQ・状態・参照先を22行追加。旧本文はバイト単位で完全に保持|
|`research_plan_toc_three_objectives_faceted_20261108.docx`|既存計画の21段落・セルを更新。配送車両表記、三目的RQ、人口配分、HOLD、対照、時間境界を整合。元の未確定運行値を採用値から候補へ変更|
|`docs/research/TOC_DELIVERY_SPEC.md`|計画書に付随する実装契約・HOLD・開発順序・テスト・完了条件|
|`configs/toc_delivery/study.json`|S1〜S3と採択範囲、未決定のnull、未採択候補値、D/W/T、7図の契約|
|`src/kmd_toc/__init__.py`、`contracts.py`|旧研究をimportしない設定検査・実行HOLDゲート・整数配分・三目的の数値比較。全体ソルバーではない|
|`tests/test_toc_contracts.py`|設定混入拒否、整数配分、三目的、依存分離の9契約テスト|
|本監査フォルダ|開始状態・旧計画の保全、段落差分、証拠・資産一覧、テスト・動作確認・保全検証記録|

旧計画の完全コピーは [source_plan_original.docx](source_plan_original.docx)。これは変更前入力の監査保存であり、新しい計画書の重複採択ではない。段落ごとの差分は [DOCX_CHANGES.json](DOCX_CHANGES.json)。DOCXパッケージでは`word/document.xml`だけを変更し、画像7枚・書式・その他パーツのバイトを保持した。再ページ組みの描画検査は行っていない。

新研究から除外した項目は、EV固有運行、電池容量、SOC、充電設備・時間・計画、航続距離、電池劣化・重量、電力量・消費エネルギー、電池材料性能変化、その他動力方式依存の入力・制約・評価・感度分析である。元DOCXに存在した「EV台数」「中途充電なし」を除去した。元DOCXになかった項目も、新設定・計算依存へ追加していない。機械設定は許可した項目だけを受け付け、未知のネスト項目も拒否する。

## 5. 新仕様と意思決定

正式な入出力契約は [実装仕様](../../research/TOC_DELIVERY_SPEC.md) と [設定](../../../configs/toc_delivery/study.json)。範囲・RQ・三目的を統一し、顧客割当→訪問順→帰着→準備→第2便積込可能→バース積込の接続を定義した。第1・第2便の待機を分け、全車両・全便の距離、採用計画が利用可能になるまでの時間を記録する。

H01〜H09は、Nの意味、人口・境界・56区画対応、PE・容量、住宅・道路OD、運行時間、サービス単位・空便、予算・反復・T境界、量子部分問題・古典対照、図の表示規則を対象とする。216 PE、102秒、積込20分、7:00は**HOLD_NOT_ADOPTED**候補であり、実行値はnull。勤務終了と準備時間は候補値も創作していない。

推奨順序は、H01〜H04解消・需要入力→独立計画検証→小規模の2便・バース連動とA→B/C→Dと同一意思決定の古典対照→S1/S2/S3の段階試験→反復・7図。必要なテストと完了条件は仕様T0〜T7に記録した。今回、大規模シミュレーション・本実験は実行していない。

## 6. 検証結果と限界

- 新契約：9テストPASS。人口0・同率・小数・入力順・厳密な合計N、不正値、未知設定項目、D/W/Tの優越・基準0、旧処理の非importを検査した。56区画を使うテストは架空の算術fixtureであり、大田区の56区画を確認した結果ではない。
- 既存関連API・凍結整合：40テストPASS。routing6、quantum core5、formal7、simulation6、battery/energy7、analysis8、runtime integrity1。
- 既存Notebook：6冊の既定セルPASS、依存38件のhash不変。オプション最適化・全量科学計算は実行していない。
- OR-Tools 9.12.4544：Routing管理器とCP-SATの2区間・順序・排他の小例PASS。[公式拠点資源制約](https://developers.google.com/optimization/routing/cvrptw_resources)、[公式スケジューリング例](https://developers.google.com/optimization/scheduling/job_shop)も参照した。新研究のモデル完成を意味しない。
- 保全検証：21,361既存ファイルを比較し、変更はREADMEと新研究DOCXのみ。残り21,359件は同一hash。旧README本文も同一hash。新研究の設定・契約コード・仕様・DOCXのスコープ検査PASS。追跡差分の`git diff --check`もPASS。

既存の`verify_quickstart.py`は、最初の配布テストでFAILとなった。原因は作業開始前からある配布マニフェストとの不一致4件（`.github/workflows/ci.yml`、`.gitignore`、`README.md`、`docs/QUANTITATIVE_GUIDE.md`）。開始時hashでも全4件の不一致を確認した。READMEは今回入口追加でさらに更新したが、既存の科学結果・配布履歴を書き換えて一致させることはしていない。配布テストは6件中5件PASS・1件FAIL。全既存チェックがPASSしたとは報告しない。残りのチェックは個別に実行した。

記録は [TEST_RESULTS.json](TEST_RESULTS.json)、[QUICKSTART_FAILURE.txt](QUICKSTART_FAILURE.txt)、[ORTOOLS_SMOKE.json](ORTOOLS_SMOKE.json)、[VALIDATION.json](VALIDATION.json)。保全・スコープ再検査は `python -B docs/audits/toc_scope_20261108/verify.py`、新契約は `python -B tests/test_toc_contracts.py`。保全検査は既存ファイルを読むだけで、過去の生成器やソルバーを呼ばない。

## 7. git diffと成果保全

追跡済み差分は`README.md`の22行追加だけ。新仕様・設定・コード・テスト・監査記録は新規ファイルであり、通常の`git diff --stat`には現れない。元から未追跡だったDOCXの変更は段落差分で確認する。今回のファイル一覧は [CHANGESET.json](CHANGESET.json)。開始時の多数の未追跡ファイルを今回作成したものとして列挙しない。

旧研究の凍結原実装・保存結果・材料評価・Controlled-DC・QAOAの成果は変更・削除していない。branchとHEADは作業前と同じ。新研究の結果は存在せず、代理値や模式図を実測値として生成していない。
