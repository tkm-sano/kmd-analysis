# 検索と採否の記録

実施日：2026年11月11日。日本語・英語のウェブ検索と原文閲覧を行った。検索結果の発見経路を記録するものであり、網羅的な系統的レビューの検索式・件数を示すものではない。以下は実際に用いた主要検索語である。

| 段階 | 検索・閲覧内容 | 結果と処理 |
|---|---|---|
| 起点 | ユーザー指定6文献のURL・DOIを最初に閲覧 | S01–S06。J-STAGEからS02のPDFへ進み、アイシン全冊PDFの該当論文を特定した |
| 国内の計画業務 | 自動配車 計画作成時間 コープ 導入 事例 | 国土交通省のスーパーレックス事例S07等を発見 |
| 国内ToC | site:optimind.tech コープ 配送 計画 時間／site:nec.com コープ 配送 計画 時間 自動 | 企業公式事例の探索。検索結果に現れたNECの保守部品配送等はスコープとの距離から深掘りしなかった |
| 国内ToCの追加探索 | site:optimind.tech コープ 時間／site:kuronekoyamato.co.jp 配送計画 時間／配送 ルート最適化 コープ 立案 時間 オプティマインド | 佐川急便・オプティマインド共同発表S08、コープさっぽろ公式事例S15を発見・原文確認 |
| 配送事業者の公式ページ探索 | site:sagawa-exp.co.jp Loogia 2021 ルート | 採用の根拠は同じ共同発表を載せたオプティマインドの公式原文とした |
| 現場の時間制約 | 国内検索からOKIの『物流のCO2削減に貢献する配送ルート最適化技術』へ | S14で業務制約による最長10分の設定を原文確認 |
| 公的資料の書誌確認 | site:mlit.go.jp 物流DX導入事例集 2022 | [国土交通白書2025](https://www.mlit.go.jp/hakusyo/mlit/r06/hakusho/r07/html/n1212000.html)の末尾資料一覧に令和4年3月の記載を確認。事例の主要根拠はS07原文p.17である |
| 古典構成法 | Clarke Wright 1964 scheduling vehicles central depot pdf computing time／Scheduling of Vehicles Clarke Wright minutes | S09の出版社抄録と大学掲載の原著本文を確認。秒・分の性能は採用せず、迅速な構成に関する議論を採用 |
| 局所探索 | Hybrid genetic search for the CVRP 2022 time／Hybrid genetic search for the CVRP Vidal pdf | S10の出版社情報と著者公開v2を確認。コードの入手・実行・変更はしなかった |
| 動的配送 | dynamic vehicle routing real time optimization 30 seconds Pillac Gendreau 2013 pdf | 動的VRP総説を文献発見に利用。総説経由の数値は最終証拠にしなかった |
| 即日配送 | Same-day deliveries in omnichannel retail pdf | S06の大学リポジトリから出版社版PDFを取得。§6.6の翌日・即日比較を確認 |
| 動的配送の原著 | The same-day delivery problem for online purchases pdf computation／The Same-Day Delivery Problem decision epoch CPU | Vocciaらの出版社抄録とResearchGateの著者公開稿を確認。最終版本文の入手・照合に至らず、最終15件には含めなかった |
| 動的配送の関連研究 | The Dynamic Dispatch Waves Problem for Same-Day Delivery 2018 DOI | S11の2018年の正式書誌と大学掲載2017年著者稿を確認。別の2018年資料は講演スライドであり、原著本文とは扱わなかった |
| 量子比較 | quantum vehicle routing classical benchmark time seconds | S12、S13等を発見。S04–S05の関連研究も参照 |
| 商用量子の書誌更新 | Performance of Commercial Quantum Annealing Solvers DOI | 2023年プレプリントに加えて、題名を変更した2025年AIP Advancesの出版社版S13を発見し、後者を採用 |

## 原文の取得と照合

指定MDPIのDOIは一部の取得経路ではエラーとなったが、出版社HTMLの閲覧と公式配信 `mdpi-res.com` のPDF取得に成功した。S06は出版社サイトの代わりに著者所属大学のリポジトリにある出版社版を用いた。S12は出版社HTML・PDFをともに確認した。S13はDOIの書誌情報とINSPIRΕ収録の出版社版PDFで確認した。

S09の大学URLは、ブラウザから原著本文を閲覧できた一方、ローカル取得では認証ページを返した。`sources/S09.html` は取得に失敗したHTMLであり、原著PDFではない。確認した内容は `sources/S09_browser_verification.md` に要約した。URL内の1962という文字列は書誌年と一致せず、出版社書誌の1964年を採用した。

主要表の数値は、S02 PDF2ページ、S03 PDF51ページ、S04 PDF39ページ、S12 PDF11ページ、S13出版社版PDF8ページの画像で照合した。S06の§6.6もPDF18ページで確認した。確認画像は `verification/` にある。S02は抽出テキストの日本語が文字化けするため画像の確認を優先した。

## 発見したが主要論拠にしなかった資料・情報

| 資料・情報 | 採用しなかった理由 |
|---|---|
| 一般ニュース、SaaS比較、物流解説、個人GitHubの量子比較 | 発行主体の原文や学術原著を優先した。検索要約のみの時間短縮値は転載しなかった |
| 西濃運輸の実証開始発表 | 主に配送業務時間の目標値であり、計画計算時間の実測とは区別した |
| 経済産業省の日本ロジテム事例、NECの保守部品配送事例 | 関連候補は得られたが、最終報告では対象を広げ過ぎず、原文を深く確認した15件に絞った |
| Bodin（1983）のClarke–Wright実装 | 出版社抄録には計算時間があるが、本文を確認しなかったため最終報告に数値は採用しなかった |
| Pillacらの動的VRP総説 | 文献発見に利用。一次研究S11および実用例S08を最終証拠にした |
| Vocciaらの即日配送研究 | 著者の2015年公開稿と発表済み論文を混同しないため最終証拠一覧から外した。公開稿に見えた数値も採用していない |
| Sinnoらの2023年プレプリント | 2025年の出版社版に置き換えた。旧稿の要約値を最終版の表へ混在させない |
| S04の制約違反例を含むFeasibility表記 | 原文内の整合性上の問題を証拠一覧に明記し、成功率の根拠にしなかった |
| S02の『精度63%向上』 | 掲載された距離2値からの単純な短縮率と厳密には一致しない。距離の実数値を優先し、この百分率を引用用の数値根拠にしなかった |
| 重ね合わせからの一般的高速化、少数点からの将来線形スケーリング | 本調査で配送問題の速度優位として確認された結果ではないため、期待と区別した |

## 未実施

Google Scholarの直接検索、契約データベースの網羅検索、全被引用文献の追跡、実運用ログの照会、担当者への連絡・聞き取り、アルゴリズムの実装・実行・追試、シミュレーション、研究用データ・コードの変更は実施していない。取得エラーの詳細は `download_log_*.json` に残した。取得失敗と原文未確認を、根拠が存在しないことと同一視していない。
