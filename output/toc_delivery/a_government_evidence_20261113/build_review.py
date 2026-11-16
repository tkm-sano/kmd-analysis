"""Build the government-first evidence addendum; no experiment/config mutations."""
import csv
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
DOC = REPO / 'docs/research/toc_delivery_a'
MANIFEST = json.loads((ROOT / 'SOURCE_MANIFEST.json').read_text())
SOURCES = {d['id']: d for d in MANIFEST}
ROWS = []


def add(eid, source, title, publisher, tier, business, value, unit, scope,
        location, adoption, reason, *, seconds=None, n=None, v=None, p=None,
        population='', boundary='', nature='公表事例・申告値。原計測ログ・測定器・標本数は未公表',
        verified='retained_original', period='未取得', duplicate=None):
    s = SOURCES[source]
    ROWS.append(dict(
        evidence_id=eid, source_id=source, title=title, publisher=publisher,
        source_priority=tier, business=business, period=period,
        reported_value=value, reported_unit=unit, scope=scope,
        planning_stops=n, planning_vehicles=v, planning_workers=p,
        population_note=population, measurement_boundary=boundary,
        value_nature=nature, page_or_section=location, url=s['url'],
        verification_status=verified, source_path=s.get('path'),
        source_sha256=s.get('sha256'), before_time_s=seconds,
        adoption=adoption, reason=reason, duplicate_group=duplicate,
        full_A_T_s=None, used_in_existing_experiments=False,
    ))


add('G01', 'mhlw_jobtag', '職業情報提供サイトjob tag「宅配便配達員」', '厚生労働省', 1,
    '宅配便の集荷・配達', '担当区域、訪問順の決定、帰所後の再積込', '定性',
    '一般的な職業説明', 'どんな仕事？／タスク', 'GO:業務構成の根拠',
    '担当区域と訪問順・複数便の概念を支持。最大2便・角度区域・所要秒の実証ではない',
    nature='行政の職業説明。タスク実施率は作業時間ではない', verified='web_original_read_local_challenge',
    boundary='計画時間の計測なし。81.5%/98.2%はタスク実施率')
add('G02', 'mlit_dispatch', '配車計画システム（業務効率化事業の説明）', '国土交通省中国運輸局掲載', 1,
    'トラックの運行計画・乗務割・経路作成', '始業・積込先・納品先・終業、労働時間・到着時間の考慮', '定性',
    'システムの概念説明', '印刷p.18／PDF p.19、原画像確認', 'GO:工程・制約の根拠',
    '乗務割と経路を計画対象にする根拠。例示の時刻・距離を実測値にしない',
    nature='全日本トラック協会HPを出典とする行政掲載の説明図。行政独自測定ではない',
    boundary='計画作成時間の絶対値なし')
add('G03', 'meti_digital_lozi_copy', '物流効率化に資する「物流デジタルサービス」事例集', '経済産業省（取得はLOZI掲載コピー）', 1,
    '物流デジタルサービス／TMS／ラストワンマイル', '入力データ整備・地理条件・積載・時間・割当と経路', '定性',
    'サービス提供者へのヒアリング', 'p.68–87、特にp.75–76', 'CONDITIONAL GO:工程の補助根拠',
    '計画前のデータ整備も必要。Loogiaの配送時間削減を人手計画Tにしない。行政原URLとのバイト同一性は未確認',
    nature='経産省名の原資料全文コピー。行政掲載の事業者回答であり独立計測ではない',
    verified='ministry_document_third_party_copy', period='令和5年度事業、企業概要2024年1月時点',
    boundary='p.76の2時間/人・日の削減は配送時間。人手ルート作成時間ではない')
add('G04', 'maff_logitem', '判断基準の解説書（事例集）日本ロジテム・ハコベル', '農林水産省掲載', 1,
    '一般貨物・配車', '計画策定時間が半分以下', '比率のみ', '紙伝票と熟練職員による手作業からの変更',
    '事例4、印刷p.6／PDF p.7', 'GO:人手工程の根拠／絶対Tへの換算は不採用',
    '改善前の絶対時間・人数・規模なし。半減率から秒数を逆算しない',
    period='令和7年3月、v1.0。観測期間は未取得', boundary='開始終了・入力整備・検査の包含範囲不明',
    duplicate='japan_logitem_hacobell')
add('G05', 'meti_cases_v11', '判断基準取組事例集ver1.1（物流効率化法）', '経済産業省', 1,
    '一般貨物・配車', '日本ロジテムの手作業配車と時間半減（索引）', '比率のみ', 'G04と同一の事業者事例候補',
    '原PDF403、頁未検証', 'HOLD:ver1.1の原本文確認',
    '索引の内容を最新原PDFの確認済み本文としない。G04のMAFF v1.0とは版が異なり、同一性を断定しない',
    verified='indexed_only_http403', duplicate='japan_logitem_hacobell',
    boundary='原PDF未確認。計画策定時間という索引の工程名以外は不明')
add('G06', 'mlit_it_guide', '中小トラック運送業のためのITツール活用ガイドブック／協栄流通', '国土交通省', 1,
    '生協の店舗・地域宅配センターへの大型トラック輸送', '導入前7～8時間、導入後2～3時間', '時間/センター・日',
    '1センター当たりの日々の配車作業', '印刷p.10–11／PDF p.7、原画像とテキスト照合',
    'CONDITIONAL GO:全体配車の優先外部参照',
    '日次・センター単位の導入前の配車作業時間として優先採用。個人宅ToC最終配送と異なり、当該センターN/V/Pと計測境界、純粋手作業かは未取得。S1への代入不可',
    seconds=[25200, 28800], population='全社17センター、約300店舗/地域宅配センター、保有12両・傭車約450両。いずれも時間測定対象1センターの規模ではない',
    period='本文に2019年3月アンケートの記載。事例の観測日は未公表',
    boundary='配車作業という工程名のみ。1人の経過時間か複数人の合計か明示なし')
add('G07', 'mlit_agri_miura', '平成30年度農林水産物の共同輸配送方策検討業務報告書／三浦市農協', '国土交通省総合政策局物流政策課', 1,
    '農産物の出荷先市場・数量の割当と配車', '本文:人手8時間／図:配車予定作成1日5～6時間', '時間',
    '翌日分の分荷・配車。本文と図の範囲/時点の一致不明', '印刷p.51／PDF p.55、原画像で不一致確認',
    'HOLD:単一の時間値への採用／GO:割当工程の参考',
    '8時間と5～6時間を勝手に平均・統合しない。図はFAX受付・Excel入力・配車予定作成を併記。1秒は自動計算で全Tと異なる',
    population='報告書p.26は17出荷所・11委託事業者。約50市場は別の原発表。配送先数・車両数・人数の時間対象との対応不明',
    period='報告2019年3月、システム2018年4月実証運用',
    boundary='分荷（市場別品目/数量）と配車が混在。本文8時間と図5～6時間の差の説明なし',
    duplicate='miura_cybozu')
add('G08', 'mlit_tamano', '地域公共交通計画等の作成と運用の手引き・添付資料／玉野市', '国土交通省', 1,
    '乗合タクシーの予約・配車', '配車計画作成20分→5分、予約受付5分→3分', '分',
    '配車計画作成の単位未公表', '印刷p.31／PDF p.31、上段玉野市。原画像照合',
    'CONDITIONAL GO:隣接工程の外部参照',
    '改善前20分=1200秒を参考採用。予約受付と別工程。貨物ではなくN/V/P不明。下段久米南町の車両数を借用しない',
    seconds=[1200, 1200], period='自動配車導入2014年9月、効果の測定日未公表',
    boundary='受付時間は別記。計画1回/1日等の作成単位と最終検査範囲は不明')
add('G09', 'mlit172', '国土交通政策研究第172号／SWAT Mobilityヒアリング', '国土交通省国土交通政策研究所', 1,
    '名古屋市の粗大ごみ収集', '紙の人手配車に半日', '半日（原表現）', '収集ルートと配車',
    '印刷p.13／PDF p.19', 'GO:工程・負担の補助／秒への換算は不採用',
    '半日を4時間や14400秒と仮定しない。N/V/Pと勤務時間長不明',
    period='報告2023年10月、ヒアリング2022年11月', boundary='紙の人手ルート作成。秒単位の測定範囲なし')
add('G10', 'meti_hayashi', '地域企業協働プログラム事例集／林ホールディングズ', '経済産業省', 1,
    '生コンクリート輸送の配車', '毎日1～2時間（検索索引上）', '時間/日', '配車計画の作成',
    '索引上p.146、原PDF403', 'HOLD:原資料確認前の数値採用',
    '検索索引の候補として記録。原頁の図・条件を読めていないため検証済み絶対値に格上げしない',
    verified='indexed_only_http403', boundary='原資料未確認。N/V/P・入力/検査範囲不明')
add('G11', 'mhlw_pascal', '荷主・トラック運送事業者等の協議会資料／敷島製パン', '厚生労働省神奈川労働局掲載', 1,
    'パンの店舗配送', '配送距離225km/日削減、店舗作業142店×5分=710分/日削減', 'km/日、分/日',
    '運行・荷役作業の改善', 'PDF内の配車アプリ導入・コース見直し・作業時間削減の各図',
    'GO:経験・土地勘に依存する配車の根拠／T数値は不採用',
    '710分は店舗作業時間の削減。人手計画Tの削減でも改善前Tでもない',
    period='2025年10月16日資料', boundary='運行距離と店舗作業。人手計画開始終了の時間はない')
add('G12', 'chusho_hisano', '2022年版中小企業白書／ヒサノ', '中小企業庁', 1,
    '精密機器・中重量物の輸送', '車・荷物・稼働日・経路を分析し配車システムの要件定義（索引）', '定性',
    '要件定義・業務分析', '第2部第3章第2節、原ページ403', 'HOLD:原本文確認／定性的探索記録のみ',
    '省庁資料でも原本文を取得していない内容を数値・確定工程の根拠に追加しない',
    verified='indexed_only_http403', boundary='人手計画Tの絶対値は未確認')
add('Q01', 'smrj_billing', '省力化事例／運輸・配車入力から請求確定', '中小企業基盤整備機構（独立行政法人）', None,
    '運送業の事務処理', '4時間→2時間', '時間', '配車入力から請求金額確定まで',
    'PDF p.1', '不採用:Tの範囲不一致',
    '中小機構は中小企業庁そのものではない。請求処理を含む時間を計画作成Tにしない',
    boundary='配車入力～請求金額確定。入力境界・請求確定までの時間')
add('O01', 'sagawa_operations', 'セールスドライバーの歩数検証', '佐川急便', 2,
    '都市/郊外の担当コースにおける集配', '都市部のトラック実走13km、通常平均約20kmの説明', 'km/車両・日',
    '別日の1担当者の集配', '検証条件・検証結果・Aさんの場合', 'GO:担当区域の業務根拠／T校正は不採用',
    '固定された担当区域/ルートの説明は参考。13と20を2020年人手計画の実測レンジにしない。W/Tなし',
    period='検証2025年1月10日、公表2025年2月6日', boundary='走行実績/歩数。計画作成時間は未公表')
add('V01', 'nihonyubin', '日本郵便Loogia導入事例・担当者インタビュー', 'オプティマインド', 3,
    'ゆうパック配送', '熟練5～10分／新人30～60分', '分/人手ルート作成（便/日の単位は不明）',
    '各ドライバーの紙地図によるルート作成', '導入前の課題／ご利用方法',
    'CONDITIONAL GO:個別ルート作成の既存参照を維持',
    '熟練300～600秒、新人1800～3600秒。全車両割当・便/バース調整・検査の全Tではない。経験条件をA1/A2/A3と対応づけない',
    boundary='ルート作成。担当先数、車両/便単位、全計画の同時開始終了、準備・検査の包含不明')
add('V02', 'suwa', '諏訪梱包運輸LYNA導入事例・担当者インタビュー', 'ライナロジクス', 3,
    '潤滑油をSS・工場等へ配送', '導入前2時間30分～3時間（工程の詳細談）', '分/日',
    'オーダー確定後の重量/配送先確認から運転者への指示可能状態', '導入前の課題・具体的効果',
    'CONDITIONAL GO:N/V付きの全体工程の外部参照',
    '150～180分を採用候補。別の概括120～180分と混ぜない。ToC限定で除外しないがPとバース工程不明。線形換算の根拠なし',
    seconds=[9000, 10800], n=[100, 150], v=[6, 7], period='掲載2025年1月28日、観測期間未公表',
    boundary='重量/場所確認→配車→指示可能。注文確定前の準備不可という説明。バース調整・共通検査の包含不明')
add('V03', 'ctc_trivalue', 'TriValueとのOptyLiner共同実証結果', '伊藤忠テクノソリューションズ（共同開発者）', None,
    '家具・家電等の宅配と現地作業の計画', '熟練手組3時間', '時間/配送計画',
    '実証の宅配92件・車両10台', '実証実験の条件／配送計画作成時間',
    'CONDITIONAL GO:工程・規模差の反証参照',
    '共同当事者の公式実証発表。事業者自身の単独公表/インタビューとは分類を分ける。熟練なら全計画5～10分という一般化を否定',
    seconds=[10800, 10800], n=[92, 92], v=[10, 10],
    period='実証2025年4月2～5日、公表2025年6月12日', boundary='現地作業を含む計画。人数、入力準備・最終検査の境界不明')
add('P01', 'visser', 'Visser & Scheltes (1989)配送計画に関する原論文', '原著学術論文', 4,
    '配送ルート・労働条件の研究', '表の31/78時間は運行時間', '時間', '配送の稼働時間',
    '原著Table 2, p.51／保存PDF p.6', '不採用:運行時間でありTではない',
    '学術論文であっても指標の定義が異なればTの係数へ使わない', boundary='operation time。計画作成のwall時間ではない',
    nature='学術原著の運行結果。人手計画Tの実測値としては不適合')


def main():
    DOC.mkdir(parents=True, exist_ok=True)
    (ROOT / 'EVIDENCE.json').write_text(json.dumps(ROWS, ensure_ascii=False, indent=2) + '\n')
    fields = list(ROWS[0])
    with (ROOT / 'EVIDENCE.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in ROWS:
            writer.writerow({k: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x for k, x in row.items()})
    (DOC / 'A_GOVERNMENT_EVIDENCE_REGISTER.csv').write_bytes((ROOT / 'EVIDENCE.csv').read_bytes())
    decision = {
        'version': 'A-government-evidence-20261113-v1',
        'date_jst': '2026-11-13',
        'source_priority': ['ministry_published_case_or_measurement', 'operator_published_case_or_measurement',
                            'official_case_with_operator_interview', 'academic_observation', 'research_assumption'],
        'priority_requires_scope_match': True,
        'planning_method_support': ['G01', 'G02', 'G04', 'O01'],
        'preferred_government_fleet_planning_external_reference': {
            'evidence_id': 'G06', 'before_time_s': [25200, 28800],
            'unit': 'reported planning work time / center / day',
            'wall_time_vs_person_time_verified': False,
            'target_center_N_V_P': None,
            'status': 'CONDITIONAL GO:external_reference_only',
        },
        'adjacent_dispatch_external_reference': {'evidence_id': 'G08', 'before_time_s': 1200,
                                                  'status': 'CONDITIONAL GO:adjacent_process_only'},
        'individual_route_reference_config': 'configs/toc_delivery/a_human_route_time_reference_v1.json',
        'individual_route_reference_replaced': False,
        'full_A_human_T_s': {'S1': None, 'S2': None, 'S3': None},
        'full_A_human_T_status': 'HOLD:unmeasured_and_not_empirically_calibrated',
        'miura_conflicting_values_merged': False,
        'research_rules_or_coefficients_modified': False,
        'applied_to_existing_experiments': False,
    }
    (ROOT / 'ADOPTION_DECISION.json').write_text(json.dumps(decision, ensure_ascii=False, indent=2) + '\n')
    web = {
        'capture_kind': 'analyst_paraphrase_of_web_tool_original_not_complete_HTML',
        'mhlw_jobtag': {
            'url': SOURCES['mhlw_jobtag']['url'],
            'section': 'どんな仕事？、タスク',
            'confirmed': ['担当区域内で集配し、区域ごとに仕事を割り振る場合が多い',
                          '大まかな配達順を考慮し、ルートを決めて積み込む',
                          '配達後に営業所へ戻り、次の荷物があれば積み込む業務例'],
            'not_confirmed': ['最大2便', '計画時間の絶対秒数', '最適な区域分割の具体規則'],
            'local_HTTP200_is_challenge': True,
        },
        'meti_cases_v11': {'url': SOURCES['meti_cases_v11']['url'], 'verification': 'search_index_only; original403'},
        'meti_hayashi': {'url': SOURCES['meti_hayashi']['url'], 'verification': 'search_index_only; original403'},
        'chusho_hisano': {'url': SOURCES['chusho_hisano']['url'], 'verification': 'search_index_only; original403'},
    }
    (ROOT / 'WEB_VERIFICATION_NOTES.json').write_text(json.dumps(web, ensure_ascii=False, indent=2) + '\n')
    print('Wrote', len(ROWS), 'evidence rows and adoption decision; existing configs untouched')


if __name__ == '__main__':
    main()
