"""Generate the declared ordinal assessment; no optimizer or distance inference."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DOCS = ROOT / 'docs/research/toc_delivery_a'
AXES = ['definition', 'empirical_support', 'reproducibility', 'toc_similarity', 'scale_transfer']
WEIGHTS = dict(zip(AXES, [30, 25, 20, 15, 10]))


def absent(reason):
    return {'levels': dict.fromkeys(AXES, 0), 'reasons': dict.fromkeys(AXES, reason),
            'availability': 'not_obtained_in_reviewed_material', 'value': None, 'unit': None,
            'external_role': 'none', 'external_status': 'HOLD', 'absolute_observed_quantity': False,
            'minimum_metric_class_match': False, 'operator_origin_supported': False,
            'data_reuse_cleared_for_this_scope': None}


def related(levels, reasons, availability, value, unit, role, *, absolute=False, match=False, origin=True, reuse=None):
    return {'levels': dict(zip(AXES, levels)), 'reasons': dict(zip(AXES, reasons)),
            'availability': availability, 'value': value, 'unit': unit, 'external_role': role,
            'external_status': 'CONDITIONAL GO' if role in ('primary_external', 'general_context', 'relative_change_only') else 'HOLD',
            'absolute_observed_quantity': absolute, 'minimum_metric_class_match': match,
            'operator_origin_supported': origin, 'data_reuse_cleared_for_this_scope': reuse}


def main():
    candidates = []
    def add(eid, name, urls, locator, facts, nonzero):
        metrics = {m: absent(f'{name}の確認範囲には{m}の適合値・必要イベントがない。資料の一般的信頼性は加点しない。') for m in ('D', 'T', 'W')}
        metrics.update(nonzero)
        candidates.append({'evidence_id': eid, 'name': name, 'urls': urls, 'locator': locator,
                           'verified_facts': facts, 'metrics': metrics})
    add('E05', '佐川急便・都市担当者の日走行', ['https://www.sagawa-exp.co.jp/about-csr/column/article_33.html'],
        '検証結果：実測値、Aさんの場合。旧証拠SAGAWA_DISTANCE.txt。',
        ['2025-01-10の単日、都市13km、郊外148km。徒歩距離と別。', '配送先数・便数・距離計測器・集荷比率は未取得。'],
        {'D': related([3,2,1,3,1], ['トラックの日走行kmで加算可能だが全車両計画の境界ではない。','事業者が単日実測と報告、距離原ログ・装置なし。','本文と単位を照合可能、原観測を追試不可。','宅配系の都市集配、商業施設・集荷も混在。','車両・日の単位は分かるが配送先数・便数がなく移送未検証。'], 'operator_reported_absolute', 13, 'km/observed_vehicle_day', 'primary_external', absolute=True, match=True)})
    add('E07', '日本郵便・紙地図ルート作成', ['https://loogia.jp/cases/nihonyubin/'],
        '導入前の課題、現在の利用、2021年時点注記。旧証拠JP_CASE.txt。',
        ['熟練者5〜10分、新人30分〜1時間程度。担当者インタビュー。','22局は試行範囲、標本数・台数ではない。67→17分は計画と配達を合わせた経験層間の差。'],
        {'T': related([2,2,1,4,0], ['ルート作成の人の作業時間で、共通入力〜最終検証の全体Tではない。','担当者の概数報告、独立の時計ログなし。','分秒換算は検証可能、日付・標本・計測境界なし。','ゆうパックの宅配業務。時間帯指定は研究条件と異なる。','仕事量、並行作業、車両数がなく全体wall時間へ換算不可。'], 'operator_reported_range', {'experienced':[300,600], 'novice':[1800,3600]}, 's/driver_route_preparation', 'primary_external', absolute=True, match=True)})
    delta_reasons = ['営業所発着距離/訪問順作成に関する削減量のみ。絶対基準値を回復できない。','2020年8月14日間80個の実地検証という公式共同発表。','定義と区分別差分図は確認可、対応原ログ・絶対値なし。','宅配に近いが時間指定あり。80個≠80一意地点。','全車両・便数・地域密度がなくS1〜S3への換算未検証。']
    add('E06', '佐川急便・Loogia実地検証', ['https://www.optimind.tech/news/ルート最適化システム「loogia」を佐川急便で導入を/'],
        'これまでの取組実績1、指標定義、検証結果画像。旧証拠SAGAWA_CHART.jpg。',
        ['担当/代走/新人応援の順で距離削減10/9/11km、ルート組み短縮10/15/30分。','配送業務短縮30/60/60分はTにしない。'],
        {'D': related([1,3,2,3,0],delta_reasons,'reported_difference_only',[10,9,11],'km reduction','relative_change_only'),
         'T': related([1,3,2,3,0],delta_reasons,'reported_difference_only',[600,900,1800],'s reduction in route preparation','relative_change_only')})
    add('E11', '国交省・2025年度拘束時間調査', ['https://www.mlit.go.jp/report/press/content/002011131.pdf'],
        '2026-07-10公表、PDF p.2の2025年度棒グラフ。MLIT_SURVEY_2026_p2.pngを目視。',
        ['一般貨物実運送、2025-11-25〜12-24調査、2025年4〜8月通常期の代表的1日。n=1032。','荷待ち60分、荷役48分、附帯14分。合計122分を純待機にしない。'],
        {'W': related([1,3,2,1,0], ['荷役と分離した荷待ちだが全運行の複数集配先を含み得る。自拠点積込ready基準ではない。','国の期間・標本数を明記した調査報告。連続時計の原ログではない。','図表と集計単位を照合可能、回答個票・ToC抽出なし。','一般貨物全般で宅配専用ではない。','バース数、積込回数、到着分布、readyイベントがなく換算不能。'], 'published_survey_average',60,'min/general_freight_operation','general_context',absolute=True,match=True)})
    add('E12', '国交省施設DX・川西倉庫', ['https://www.mlit.go.jp/seisakutokatsu/freight/content/001995027.pdf'],
        '誌面p.20/PDF p.21、事例7。MLIT_FACILITY_DX_p21.pngを目視。',
        ['荷待ち時間30%軽減という報告。対象件数・絶対平均・測定期間・バース数は確認箇所に記載なし。','同資料大和ハウスp.15の画面例は測定条件がなく、実績値として採らない。'],
        {'W': related([1,2,1,1,0], ['荷待ちの改善率であり研究Wの絶対分数ではない。','行政事例集に事業者の効果を報告、測定設計は不明。','30%の記載は照合可能、分母・原ログなし。','営業倉庫でToC向け積込かは未確認。','車両、バース、期間、before/after絶対値不明。'], 'reported_relative_reduction',30,'percent reduction','relative_change_only')})
    add('E13', '国交省・荷待ち客観把握DX調査', ['https://www.mlit.go.jp/jidosha/content/001993650.pdf'],
        '2025-03、誌面p.11〜12/PDF pp.12〜13。MLIT_OBJECTIVE_DX_2025_p13.pngを目視。',
        ['事例④は滋賀工場〜大田区デポの機械部品幹線輸送。受付後平均70分、最大438分。','早着後の手待ちを分割休息に使用と明記。事例③の宅配貨物も主に幹線。','84/219/99分は荷役、66時間/月は日報・勤怠事務でTではない。'],
        {'W': related([1,3,2,0,0], ['受付後時間には分割休息が混在。積込ready〜startへ分離できない。','DX運行記録と現場確認・ヒアリングによる事例。','報告図と平均/最大値を確認、原イベント・標本数未取得。','機械部品の拠点間幹線でToCラストマイルではない。','受付≠ready、荷卸し/積込の切分け、台数・バース・到着条件不足。'], 'reported_receipt_after_time_including_rest',{'mean':70,'max':438},'min/receipt_after_interval','general_context',absolute=True,match=False)})
    add('E14', 'Amazon米国Last Mile Challenge', ['https://registry.opendata.aws/amazon-last-mile-challenges/','https://raw.githubusercontent.com/MIT-CAVE/rc-cli/main/templates/data_structures.md'],
        '公開台帳、著者論文、amazon_schema.txtのData Field Definitionsとmodel_score_timings。',
        ['2018年米国5都市9184ルート。実訪問順、匿名化座標、秒の移動時間行列。道路距離行列なし。','departure_time_utc≠loading start/ready。planned_service_time_seconds≠planning time。','14030/3920のtimingはスキーマのExampleでありAmazon実務計画作成実績ではない。CC BY-NC 4.0。','全データ結合・匿名化誤差・地図対応・車両日/閉路終端の検証は未実施。'],
        {'D': related([1,0,3,4,0], ['実訪問順と座標は距離再構成の材料。現状の道路D実績値はない。','公開された実訪問順は実績だが、それ自体は走行距離の実測ではない。','一次論文・公式スキーマ・公開配布。全レコード検査未実施なので4ではない。','実務の宅配ラストマイル。時間窓・容積容量など条件差あり。','同一station/dayのNは将来集計可能だが台数/2便/バースへの対応は未検証。'], 'reconstruction_material_only',None,None,'development_only',reuse=True)})
    add('E15', 'Cainiao LaDe', ['https://huggingface.co/datasets/Cainiao-AI/LaDe','https://arxiv.org/html/2306.10675v3'],
        'LADE_CARD.mdのtrajectory例/項目表、論文§3・§4.5。',
        ['配達完了/引受時刻、courier_id、20秒軌跡とroad-networkの提供記載。courierと車両は同義と確認できない。','カード例のlat/lngは3.95e6/3.05e6で緯経度度として読めない。座標変換の根拠未取得。','カードはApache-2.0、論文本文はCC BY-NC 4.0と記載。利用条件の整合未確認。','引受≠積込ready、delivery_time≠計画完了、欠測・モード・拠点発着の確認未完。'],
        {'D': related([1,0,1,2,0], ['軌跡は距離候補だが道路車両距離・閉路・座標単位が未確定。','軌跡を合計した道路車両実績Dは今回取得していない。','原カードと論文は確認。座標/権利表記差と欠測が再計算を阻む。','配達員のラストマイルで車種・宅配車両の同一性未確認。','配達員数を車両数に置換できず、便/バース/走行区分未確認。'], 'reconstruction_material_with_unresolved_crs_and_terms',None,None,'development_only',reuse=False)})
    add('E16', 'Delivering Data・医薬品3PL', ['https://zenodo.org/records/15310106','https://github.com/annavrani/Delivering-Data'],
        'Zenodo API記述、data.zipの全ファイル一覧、9日全距離行列とorders.xlsx。',
        ['ZIPのMD5を配布元と照合。実ファイルでは9日63〜84注文、距離はkm、時間は分のAPI推計。','距離行列は有向・欠損なし・対角0。ただし実際の車両別訪問順ファイルを確認できない。','行列だけでは各車経路の合計Dは求まらない。新たな最適化出力は事業者実績にならない。','公開READMEのDOIは15310106、ダウンロード補助コードは14967221を指定。補助コード未実行。CC BY 4.0。'],
        {'D': related([1,0,3,1,0], ['道路由来km行列という材料はあるが実運行の訪問順なし。','APIのペア距離は実車の計画総距離の実測値ではない。','配布hash・全9距離行列のID/数値を点検。経路/道路版/原住所なし。','医薬品配送で純ToCは未確認。重量/容積/時間窓あり。','9日を結合・複製しても同一日の1000/2000/4000地点実績にならない。'], 'od_input_only_no_observed_route',None,None,'development_only',reuse=True)})
    add('E17', 'Hss-477工場トラック待ちCSV', ['https://github.com/Hss-477/Logistics-Dataset'],
        'README、倉庫/貨物先頭6行、queuing_info先頭65536byte/完結247行のみ。',
        ['queue_start_time/calling_time/entry_time等を確認。先頭行queuing_time=1.916666667はcalling−queue_startの分に一致。','同先頭行entry−queue_start=4.15分。呼出しと積込開始を同一にできない。','247行に129plan_no、queue_type2/3あり。行を独立した便として足すと重複する恐れ。','工場・鋼材、実事業者の帰属/収集方法/再利用ライセンス未確認。全量監査未実施。'],
        {'W': related([1,0,1,0,0], ['列名は待ちを示すがready/積込開始の対応が未確定。','実在事業者・測定手順・実測/生成の来歴を裏付けられない。','先頭算術は検証、列辞書/全量/権利不足。公開GitHubだけでは実績認定できない。','鋼材工場でToC配送ではない。','複数queue_type/便/倉庫の切分けとバース定義なし。'], 'unverified_queue_events_prefix_only',None,None,'development_only',origin=False,reuse=False)})
    add('E18', 'URBANE Barcelona RFID', ['https://zenodo.org/records/18417198','https://recerca.uoc.edu/documentos/697b971a645ef261d1be6df6'],
        'Zenodo v1/2026-01-29。両Excelを取得してMD5照合、ZIP/XML全シートを点検。',
        ['週別4シートとraw1シート。raw1421行にTEST1行、倉庫到着/compartment/配達状態イベント。','shipmentId/eventIdとtimestamp/位置はあるが、専用vehicle_id/trip/berth/ready/load_start列なし。','Pallet Has Arrived→Real Start of Deliveryは荷物到着から配送開始。積込待機と計画時間を分離できない。','位置とイベントのみで車両別道路Dは確定しない。CC BY 4.0。'],
        {'D': related([1,0,2,2,0], ['位置・イベントは材料になるが車両走行経路の境界がない。','車両別道路距離の実測/集計は取得できない。','原Excelの列/イベントを独立点検。モード/車両連結・地図対応未確認。','都市ラストマイルの実証だが一般配送車の同一性は未確認。','件数を車両・便・バースへ接続する識別子が不足。'], 'parcel_event_material_only',None,None,'development_only',reuse=True)})
    add('E10', 'ロンコ・ジャパン/OKI店舗配送', ['https://www.oki.com/global/ja/technologies/otr/assets_c/uploads/otr241_r05.pdf'],
        '印刷pp.32〜34、旧証拠OKI_RONCO.txt。',
        ['約50店舗/15台前後、代表荷量948は容器数。224km/5.1%は推計差分。','最長10分は計算予算であり、実測Tではない。店舗分割配送で純ToCではない。'],
        {'D': related([1,1,2,0,1], ['距離削減の推計差分であり事業者の同一需要の総D実測ではない。','実証主体の技術報告だが採点対象の224kmは代表荷量でのモデル推計なので実測報告に加点しない。','図/推計手順を確認、車両別経路原ログなし。','店舗配送・分割訪問で本研究ToCと異なる。','店舗数/台数の概数はあるが便数・密度・容器と需要単位が違う。'], 'estimated_difference_only',{'reduction_km':224,'reduction_percent':5.1},'estimated km reduction','none')})

    for c in candidates:
        for metric, rec in c['metrics'].items():
            rec['score_100'] = sum(WEIGHTS[a] * rec['levels'][a] / 4 for a in AXES)
            rec['score_display'] = f"{rec['score_100']:.1f}"
            rec['common_definition_matched'] = False
            rec['scale_transfer_validated'] = False
            rec['can_populate_S1_S2_S3'] = False
            rec['same_condition_status'] = 'HOLD'
            # Sensitivity to one weight changed by ±5 points; remaining weights rescaled.
            trial = [rec['score_100']]
            for axis in AXES:
                for delta in (-5, 5):
                    altered = {a: (WEIGHTS[a]+delta if a == axis else WEIGHTS[a]*(100-WEIGHTS[axis]-delta)/(100-WEIGHTS[axis])) for a in AXES}
                    trial.append(sum(altered[a]*rec['levels'][a]/4 for a in AXES))
            rec['weight_sensitivity_range'] = [round(min(trial),2),round(max(trial),2)]
    artifacts = {}
    for p in sorted((HERE/'sources').iterdir()):
        if p.is_file():
            artifacts[str(p.relative_to(ROOT))] = {'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
    data = {'assessment_version':'A-applicability-v1.0','date':'2026-11-11','conditions_version':'AD-common-20261111-v1.1',
            'score_interpretation':'declared ordinal evidence suitability, not a probability, performance score, or automatic adoption threshold',
            'axes':AXES,'weights':WEIGHTS,'levels':[0,1,2,3,4],'missing_metric_score_is_not_observed_zero':True,
            'no_aggregate_score_across_metrics':True,'joint_observation':False,'candidates':candidates,
            'source_artifacts':artifacts,'all_same_condition_results_missing':True,
            'unchanged_conditions':{'loading_s':1800,'customer_service_s':120,'return_preparation_s':0},
            'scope':'public source/schema/small file audit only; no reconstruction, optimization or scale calibration'}
    (DOCS/'A_APPLICABILITY_ASSESSMENT.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    table = ['|資料|D /100|T /100|W /100|現在の利用範囲|','|---|---:|---:|---:|---|']
    for c in candidates:
        roles = {'E05':'Dの単日外部参照','E07':'人のルート作成時間の外部参照','E06':'D/Tの短縮差分のみ','E11':'一般貨物の荷待ち背景値','E12':'W関連の改善率のみ','E13':'休息混在の受付後時間。計測方法の背景','E14':'D再構成の候補。値は未取得','E15':'座標・利用条件確認までHOLD','E16':'OD入力。事業者の実績経路なし','E17':'来歴・イベント対応・利用条件未確認','E18':'荷物イベント。車両別経路なし','E10':'ToCのD/T実績として不採用'}
        table.append('|'+c['evidence_id']+' '+c['name']+'|'+'|'.join(c['metrics'][m]['score_display'] for m in ('D','T','W'))+'|'+roles[c['evidence_id']]+'|')
    (HERE/'SCORE_TABLE.md').write_text('\n'.join(table)+'\n')
    details=[]
    for c in candidates:
        details += [f"### {c['evidence_id']} {c['name']}",'', '出典：'+ '、'.join(f'[一次資料{i+1}]({u})' for i,u in enumerate(c['urls']))+'。確認箇所：'+c['locator'],'']
        details += ['- '+f for f in c['verified_facts']]+['']
        for metric,rec in c['metrics'].items():
            if not any(rec['levels'].values()):
                continue
            details += [f"{metric}：**{rec['score_display']}/100**。観点順の素点は`"+','.join(str(rec['levels'][a]) for a in AXES)+'`。', '', '|観点|素点 /4|判断根拠|','|---|---:|---|']
            labels=['定義','実績','再検証','ToC類似性','規模換算']
            details += [f"|{label}|{rec['levels'][a]}|{rec['reasons'][a]}|" for a,label in zip(AXES,labels)]
            details += ['', '未取得・無関係の指標欄は全観点0。現在の実績値利用と、将来の再構成可能性は別判定とする。','']
    (HERE/'SCORE_DETAILS.md').write_text('\n'.join(details)+'\n')
    print('\n'.join(table))


if __name__ == '__main__':
    main()
