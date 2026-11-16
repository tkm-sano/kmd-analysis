# A〜D共通：固定需要v1の読込契約

この8ファイルを一体で凍結する。S1=1,000地点/10台/2バース、S2=2,000/20/4、
S3=4,000/40/8である。全地点1個は制御仮定であり、実配送の推計ではない。

読込は `from kmd_toc.frozen_demand import load_frozen_demand`、
`demand = load_frozen_demand('S1', method_id='A')` とする。B/C/Dもmethod_idだけを変える。
実行例はリポジトリルートで `PYTHONPATH=src python -B -c "from kmd_toc.frozen_demand import load_frozen_demand; d=load_frozen_demand('S1', method_id='A'); print(d.N, len(d.stops))"` である。

読込前にソース側の固定pin、設定、manifest、全payload、SHA256SUMS、件数、地域配分、
包含関係を検証する。不一致・欠損はFrozenDemandErrorで停止し、生成や自動修復をしない。
bundle_dirは完全同一の保存コピーの検証にだけ使用でき、別hashの指定はできない。
戻り値はfrozen dataclassとtupleである。経緯度は元の十進文字列を保持し、IDと地域コードも
文字列のままである。必要な数値演算は別の作業用配列で行い、元値を丸めて保存し直さない。

CSVはUTF-8・BOMなし・LF、列順はscenario_id,stop_id,building_id,chocho_code,
longitude,latitude,parcel_countである。行はstop_idのUTF-8バイト列昇順である。
同じ地点の属性は系列間で同じである。配分は元39,956地点の182町丁目構成比、
整数最大剰余法、同率は6桁コードUTF-8昇順である。各層は
SHA256(UTF8('toc-stop-rank-v1') || 0x00 || UTF8(stop_id))の32バイト昇順、
同値は地点IDのUTF-8昇順とし、共通順位先頭を非復元抽出する。需要seedは使用しない。

地点集合hashは、UTF8('toc-stop-set-v1') || 0x00 に続けて、UTF-8バイト昇順の各IDについて
4バイト符号なしbig-endian長とIDのUTF-8バイト列を連結した列のSHA-256である。
ファイルhashはファイルの全バイトを対象とする。SHA256SUMSは自身以外の7ファイルを記録する。
SHA256SUMS自身とmanifestと設定のhashは、別のfrozen_demand_pin.pyで固定する。

Aは事業者方式を参考にした規則ベース、BはVeRyPy並列Clarke–Wright、CはOR-Tools、
Dは量子研究に基づく手法である。いずれも需要の再生成・再抽出・地点削除・座標変更・
荷量変更・需要seed追加を禁止する。可能なのは訪問順・車両/便割当・時刻等の計画決定である。
容量超過や到達不能は計画側・道路側の未解決事項として記録し、需要を減らして解消しない。
車両容量や道路端点は本CSVに含まない。道路採用・全必要OD・運行条件・VRP可行性はHOLDである。
不足ODは固定stop_idの有向組合せを別工程で記録し、今回道路計算を行わない。
需要抽出と共通道路整備はA〜Dの手法固有Tの外に分け、共通準備時間として別に記録する。

旧study.json/contracts.pyの人口配分・旧単位・input_seeds・固定担当はこの需要の読込には使わない。
通常実行からfreeze_demandを呼ばない。既存v1と異なる出力は上書きせず停止する。
仕様変更はv1を残した別版の提案とし、明示的承認なく比較入力を切り替えない。
SHA-256は誤変更検知でありOSによる絶対的な書込禁止ではない。pinも含むソースの変更は
研究仕様変更としてレビューする。固定原本を書き換えるテストは行わない。

監査担当者の再現確認はリポジトリルートから
`PYTHONPATH=src python -B -m kmd_toc.freeze_demand --verify-only` とする。
元入力からメモリ内で再構築して全8ファイルのバイト一致を検査し、原本へ一切書き込まない。
初回固定専用の--freeze-v1はA〜Dから呼ばない。既存の同一v1なら照合のみで書込なし、
相違があれば停止する。出力に実行日時を含めず、実行環境・共通準備秒は別の検証報告へ保存する。
